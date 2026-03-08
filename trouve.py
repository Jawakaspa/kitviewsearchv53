# trouve.py V1.0.20 - 28/01/2026 18:15:00
__pgm__ = "trouve.py"
__version__ = "1.0.20"
__date__ = "28/01/2026 18:15:00"

"""
Orchestrateur complet du pipeline de recherche patients.

CHANGEMENTS V1.0.20 (28/01/2026) :
- NOUVEAU : Support de limit et offset pour la pagination
- rechercher() accepte maintenant limit: int et offset: int
- Retourne nb_patients (total) et nb_patients_retournes (limité)

CHANGEMENTS V5.1 (13/01/2026) :
- NOUVEAU : Intégration de trouveid.py pour enrichir les critères "meme"
- Pipeline : detall → trouveid (si critères meme) → jsonsql → lancesql

CHANGEMENTS V1.0.18 (09/01/2026) :
- FIX CRITIQUE GARDEFOU : Le gardefou s'active désormais correctement
  * Avant : Dépendait de syntags.csv (obsolète) → gardefou ignoré si absent
  * Après : Le gardefou bloque par défaut quand aucun critère de filtrage détecté
- NETTOYAGE : Suppression de toutes les références à syntags.csv (obsolète)
- Filtrage des critères "count"/"list" qui ne sont pas des vrais filtres

PIPELINE V5.1 :
    Question
      │
      ▼
    ┌─────────────────┐
    │  detall.py      │  → JSON avec critères (dont "meme")
    └────────┬────────┘
             │
      ▼
    ┌─────────────────┐
    │ trouveid.py     │  → Enrichit critères "meme" avec patient référence ◄ NOUVEAU
    └────────┬────────┘
             │
      ▼
    ┌─────────────────┐
    │  jsonsql.py     │  → Génère SQL (gère critères "meme")
    └────────┬────────┘
             │
      ▼
    ┌─────────────────┐
    │  lancesql.py    │  → Exécute SQL
    └────────┬────────┘
             │
             ▼
         Résultats

Usage CLI :
    python trouve.py base1000.db "patients avec même pathologie que Jean Dupont"
    python trouve.py base1000.db "même âge que Hélène Joly" --verbose
"""

import json
import sys
import os
import time
import csv
import io
from pathlib import Path
from typing import Optional, Union, Dict, List
from datetime import datetime

# Imports des modules du pipeline
try:
    from jsonsql import generer_sql
except ImportError:
    generer_sql = None

try:
    from lancesql import executer_sql
except ImportError:
    executer_sql = None

# Import de trouveid - NOUVEAU V5.1
try:
    from trouveid import enrichir_avec_reference
    TROUVEID_DISPONIBLE = True
except ImportError:
    TROUVEID_DISPONIBLE = False
    def enrichir_avec_reference(json_det, db, **kw): return json_det

# Import du garde-fou
try:
    from gardefou import verifier_intention_tous
    GARDEFOU_DISPONIBLE = True
except ImportError:
    GARDEFOU_DISPONIBLE = False
    verifier_intention_tous = None


# =============================================================================
# CHARGEMENT DES MODÈLES DEPUIS ia.csv
# =============================================================================

def charger_modeles_ia(refs_dir: Path = None, verbose: bool = False) -> Dict[str, dict]:
    """
    Charge les modèles IA depuis refs/ia.csv.
    
    Returns:
        dict: {nom_court: {"via": "openai|eden", "complet": "...", "actif": True/False}}
    """
    if refs_dir is None:
        refs_dir = Path(__file__).parent / "refs"
    
    ia_path = refs_dir / "ia.csv"
    
    if not ia_path.exists():
        if verbose:
            print(f"[DEBUG] trouve: ia.csv introuvable, utilisation config par défaut")
        # Config par défaut si fichier absent
        return {
            'standard': {'via': '', 'complet': '', 'actif': True},
            'sonnet': {'via': 'eden', 'complet': 'anthropic/claude-3-7-sonnet-20250219', 'actif': True},
            'gpt4omini': {'via': 'openai', 'complet': 'gpt-4o-mini', 'actif': True},
        }
    
    modeles = {}
    
    try:
        with open(ia_path, 'r', encoding='utf-8-sig') as f:
            lignes = [line for line in f if not line.strip().startswith('#')]
        
        if not lignes:
            return {}
        
        lignes_io = io.StringIO(''.join(lignes))
        reader = csv.DictReader(lignes_io, delimiter=';')
        
        for row in reader:
            court = row.get('court', '').strip().lower()
            if not court:
                continue
            
            actif = row.get('actif', 'O').strip().upper() == 'O'
            
            modeles[court] = {
                'via': row.get('via', '').strip().lower(),
                'complet': row.get('complet', '').strip(),
                'actif': actif,
                'cout': row.get('cout', '').strip(),
                'notes': row.get('notes', '').strip()
            }
        
        if verbose:
            actifs = sum(1 for m in modeles.values() if m['actif'])
            print(f"[DEBUG] trouve: {len(modeles)} modèles chargés ({actifs} actifs)")
        
        return modeles
        
    except Exception as e:
        if verbose:
            print(f"[DEBUG] trouve: Erreur chargement ia.csv: {e}")
        return {}


# Cache global des modèles
_MODELES_IA_CACHE = None

# Seuil pour déclencher le garde-fou (% de la base retourné)
SEUIL_GARDEFOU_POURCENTAGE = 80  # Si >80% de la base retournée, vérifier


def get_modeles_ia() -> Dict[str, dict]:
    """Retourne les modèles IA (avec cache)."""
    global _MODELES_IA_CACHE
    if _MODELES_IA_CACHE is None:
        _MODELES_IA_CACHE = charger_modeles_ia()
    return _MODELES_IA_CACHE


def get_modele_defaut() -> str:
    """Retourne le premier modèle IA actif (hors standard)."""
    modeles = get_modeles_ia()
    for court, config in modeles.items():
        if court != 'standard' and config.get('actif', False):
            return court
    return 'sonnet'  # Fallback


# =============================================================================
# CHARGEMENT DYNAMIQUE DES MODULES DE DÉTECTION
# =============================================================================

def _charger_module_detection(mode: str):
    """
    Charge dynamiquement le module de détection approprié.
    """
    if mode == "ia":
        try:
            from detia import charger_references, detecter_tout
            return "detia", charger_references, detecter_tout
        except ImportError as e:
            print(f"[ERREUR] Impossible de charger detia.py: {e}")
            return None, None, None
    else:
        try:
            from detall import charger_references, detecter_tout
            return "detall", charger_references, detecter_tout
        except ImportError as e:
            print(f"[ERREUR] Impossible de charger detall.py: {e}")
            return None, None, None


# =============================================================================
# FONCTION PRINCIPALE : rechercher()
# =============================================================================

def rechercher(
    question: str,
    db_path: Union[str, Path],
    mode: str = "standard",
    model: str = None,
    references: dict = None,
    include_details: bool = True,
    limit: int = None,
    offset: int = 0,
    verbose: bool = False,
    debug: bool = False
) -> dict:
    """
    Recherche des patients correspondant à une question en langage naturel.
    
    Modes supportés :
    - 'standard' : détection locale via detall.py
    - 'ia' : détection IA via detia.py
    
    Args:
        limit: Nombre maximum de patients à retourner (None = tous)
        offset: Décalage pour la pagination (défaut: 0)
    
    NOUVEAU V5.1 : Support des critères "meme" (similarités)
    Si des critères de type "meme" sont détectés, trouveid.py est appelé
    pour identifier le patient de référence et enrichir le JSON.
    """
    temps_debut = time.perf_counter()
    
    # Vérifier la base
    db_path = Path(db_path)
    if not db_path.exists():
        script_dir = Path(__file__).parent
        base_in_bases = script_dir / "bases" / db_path.name
        if base_in_bases.exists():
            db_path = base_in_bases
        else:
            return {
                "question": question,
                "nb": 0,
                "ids": [],
                "patients": [],
                "erreur": f"Base introuvable: {db_path}",
                "temps_total_ms": 0
            }
    
    # Charger le module de détection
    module_name, charger_refs, detecter = _charger_module_detection(mode)
    if not detecter:
        return {
            "question": question,
            "nb": 0,
            "ids": [],
            "patients": [],
            "erreur": f"Module de détection '{mode}' non disponible",
            "temps_total_ms": 0
        }
    
    # Charger les références si pas fournies
    if references is None:
        if verbose:
            print(f"  Chargement des références ({module_name})...")
        try:
            references = charger_refs(verbose=verbose, debug=debug)
        except Exception as e:
            return {
                "question": question,
                "nb": 0,
                "ids": [],
                "patients": [],
                "erreur": f"Erreur chargement références: {e}",
                "temps_total_ms": 0
            }
    
    # === ÉTAPE 1 : Détection ===
    temps_detection_debut = time.perf_counter()
    
    if verbose:
        print(f"  Détection ({module_name})...")
        if model and mode == "ia":
            print(f"  Modèle IA: {model}")
    
    try:
        if mode == "ia" and model:
            json_detection = detecter(question, references, model=model, verbose=verbose, debug=debug)
        else:
            json_detection = detecter(question, references, verbose=verbose, debug=debug)
    except Exception as e:
        return {
            "question": question,
            "nb": 0,
            "ids": [],
            "patients": [],
            "erreur": f"Erreur détection: {e}",
            "temps_total_ms": 0
        }
    
    temps_detection = (time.perf_counter() - temps_detection_debut) * 1000
    
    if debug:
        print(f"[DEBUG] trouve: JSON détection (avant trouveid):")
        print(json.dumps(json_detection, indent=2, ensure_ascii=False))
    
    # === ÉTAPE 1.5 : Enrichissement des critères "meme" (NOUVEAU V5.1) ===
    criteres_meme = [c for c in json_detection.get('criteres', []) if c.get('type') == 'meme']
    
    if criteres_meme and TROUVEID_DISPONIBLE:
        temps_trouveid_debut = time.perf_counter()
        
        if verbose:
            print(f"  Identification patient de référence (trouveid)...")
            print(f"    {len(criteres_meme)} critère(s) 'même' à enrichir")
        
        try:
            json_detection = enrichir_avec_reference(
                json_detection,
                db_path,
                verbose=verbose,
                debug=debug
            )
            
            temps_trouveid = (time.perf_counter() - temps_trouveid_debut) * 1000
            
            if debug:
                print(f"[DEBUG] trouve: JSON après trouveid:")
                print(json.dumps(json_detection, indent=2, ensure_ascii=False))
                print(f"[DEBUG] trouve: Temps trouveid: {temps_trouveid:.2f}ms")
            
            # Vérifier si tous les critères ont un reference_id
            for c in json_detection.get('criteres', []):
                if c.get('type') == 'meme':
                    if c.get('reference_id') is None:
                        if verbose:
                            print(f"    ⚠ Patient non trouvé: {c.get('reference_erreur', 'inconnu')}")
                    else:
                        ref_patient = c.get('reference_patient', {})
                        ref_nom = f"{ref_patient.get('prenom', '')} {ref_patient.get('nom', '')}".strip()
                        if verbose:
                            print(f"    ✓ Référence trouvée: {ref_nom} (ID {c['reference_id']})")
                        
        except Exception as e:
            if verbose:
                print(f"    ⚠ Erreur trouveid: {e}")
            # Continuer sans enrichissement
    
    # === ÉTAPE 2 : Génération SQL ===
    temps_sql_debut = time.perf_counter()
    
    if verbose:
        print(f"  Génération SQL...")
    
    try:
        # V1.0.20 : D'abord générer SQL pour COUNT (total), puis pour LIST (avec limit/offset)
        
        # 1. Requête COUNT pour avoir le nombre total
        json_count = json_detection.copy()
        json_count['listcount'] = 'COUNT'
        sql_dict_count = generer_sql(json_count, verbose=verbose, debug=debug)
        
        # 2. Requête LIST avec limit/offset
        sql_dict = generer_sql(json_detection, limit=limit, offset=offset, verbose=verbose, debug=debug)
        
    except Exception as e:
        return {
            "question": question,
            "nb": 0,
            "ids": [],
            "patients": [],
            "json_detection": json_detection,
            "erreur": f"Erreur génération SQL: {e}",
            "temps_detection_ms": round(temps_detection, 2),
            "temps_total_ms": 0
        }
    
    # === ÉTAPE 3 : Exécution SQL ===
    if verbose:
        print(f"  Exécution SQL...")
    
    try:
        # V1.0.20 : Exécuter COUNT d'abord pour avoir le total
        resultat_count = executer_sql(
            sql_dict_count, 
            db_path, 
            include_details=False,
            verbose=verbose, 
            debug=debug
        )
        nb_total = resultat_count.get('nb', 0)
        
        # Puis exécuter LIST avec limit/offset
        resultat_sql = executer_sql(
            sql_dict, 
            db_path, 
            include_details=include_details,
            verbose=verbose, 
            debug=debug
        )
        # Injecter le total dans resultat_sql
        resultat_sql['nb_total'] = nb_total
        
    except Exception as e:
        return {
            "question": question,
            "nb": 0,
            "ids": [],
            "patients": [],
            "json_detection": json_detection,
            "sql": sql_dict.get('sql', ''),
            "erreur": f"Erreur exécution SQL: {e}",
            "temps_detection_ms": round(temps_detection, 2),
            "temps_total_ms": 0
        }
    
    temps_sql = (time.perf_counter() - temps_sql_debut) * 1000
    temps_total = (time.perf_counter() - temps_debut) * 1000
    
    # === ÉTAPE 4 : GARDE-FOU - Vérification intention "tous les patients" ===
    # FIX V1.0.18 : Le gardefou s'active correctement sans dépendance externe
    
    nb_resultats = resultat_sql.get('nb', 0)
    criteres_detectes = json_detection.get('criteres', [])
    
    # Filtrer les critères de type "count"/"list" qui ne sont pas des vrais filtres
    # NOUVEAU V5.1 : Les critères "meme" SONT des filtres valides
    criteres_filtrage = [c for c in criteres_detectes if c.get('type') not in ('count', 'list')]
    
    # Déclencher le garde-fou si :
    # - Aucun critère de FILTRAGE détecté (tags, ages, angles, sexe, meme)
    # - Beaucoup de résultats (> 100)
    if GARDEFOU_DISPONIBLE and len(criteres_filtrage) == 0 and nb_resultats > 100:
        if verbose:
            print(f"  Vérification garde-fou (aucun critère de filtrage, {nb_resultats} résultats)...")
        
        # Appeler le gardefou sans syntags (liste vide)
        verdict = verifier_intention_tous(
            question, 
            [],  # Pas de syntags, le gardefou fonctionne quand même
            verbose=verbose, 
            debug=debug
        )
        
        if not verdict['intention_tous']:
            # Bloquer et retourner un message d'erreur
            if verbose:
                print(f"  ⚠️  Garde-fou activé: {verdict['raison']}")
            
            return {
                "question": question,
                "nb": 0,
                "ids": [],
                "patients": [],
                "criteres_detectes": [],
                "mode": mode,
                "model": model if mode == "ia" else None,
                "auteur": json_detection.get('auteur', 'cx' if mode == 'standard' else 'eden'),
                "gardefou": True,
                "gardefou_raison": verdict['raison'],
                "gardefou_message": verdict['message'],
                "gardefou_suggestions": verdict.get('suggestions', []),
                "temps_detection_ms": round(temps_detection, 2),
                "temps_sql_ms": round(temps_sql, 2),
                "temps_total_ms": round(temps_total, 2)
            }
    
    # === Construction du résultat final ===
    # V1.0.20 : nb_patients = total, nb_patients_retournes = après limit/offset
    nb_retournes = resultat_sql.get('nb', 0)
    nb_total = resultat_sql.get('nb_total', nb_retournes)
    
    resultat = {
        "question": question,
        "nb_patients": nb_total,  # Total sans limit
        "nb_patients_retournes": nb_retournes,  # Retournés avec limit
        "nb": nb_total,  # Rétrocompatibilité
        "ids": resultat_sql.get('ids', []),
        "patients": resultat_sql.get('patients', []) if include_details else [],
        "listcount": json_detection.get('listcount', 'LIST'),
        "criteres_detectes": json_detection.get('criteres', []),
        "residu": json_detection.get('residu', ''),
        "mode": mode,
        "model": model if mode == "ia" else None,
        "auteur": json_detection.get('auteur', 'cx' if mode == 'standard' else 'eden'),
        "temps_detection_ms": round(temps_detection, 2),
        "temps_sql_ms": round(temps_sql, 2),
        "temps_total_ms": round(temps_total, 2)
    }
    
    # === PHOTOFIT V5.2 : Propager portrait_scores pour badges de similarité ===
    if sql_dict.get('portrait_scores'):
        resultat['portrait_scores'] = sql_dict['portrait_scores']
        if debug:
            print(f"  [DEBUG] portrait_scores: {len(sql_dict['portrait_scores'])} portraits avec scores")
    
    if resultat_sql.get('erreur'):
        resultat['erreur_sql'] = resultat_sql['erreur']
    
    # Toujours retourner le SQL et le JSON de détection (utile pour batch/CSV)
    resultat['sql'] = sql_dict.get('sql', '')
    resultat['sql_params'] = sql_dict.get('params', [])
    resultat['json_detection'] = json_detection
    
    if verbose:
        print(f"  ✓ {resultat['nb']} résultat(s) en {temps_total:.1f}ms")
    
    return resultat


# =============================================================================
# MODE BATCH
# =============================================================================

def _trouver_fichier(nom_fichier):
    """Cherche un fichier dans plusieurs répertoires possibles."""
    chemin = Path(nom_fichier)
    if chemin.exists():
        return chemin
    script_dir = Path(__file__).parent
    for rep in [Path('tests'), script_dir / 'tests']:
        candidat = rep / chemin.name
        if candidat.exists():
            return candidat
    return None


def traiter_fichier_batch(fichier_entree, db_path, mode='standard', model=None,
                          verbose=False, debug=False):
    """
    Traite un fichier CSV de questions en batch.
    
    Format d'entrée : CSV avec colonne 'question'
    Format de sortie : question;nb_patients;nb_criteres;mode;temps_ms;residu;erreur
    """
    chemin_entree = Path(fichier_entree)
    nom_base = chemin_entree.stem
    module_name = Path(__pgm__).stem  # 'trouve'
    fichier_sortie = chemin_entree.parent / f"{nom_base}{module_name}.csv"
    
    print(f"Fichier d'entrée : {os.path.abspath(fichier_entree)}")
    print(f"Fichier de sortie: {os.path.abspath(fichier_sortie)}")
    print(f"Base             : {os.path.abspath(str(db_path))}")
    print(f"Mode             : {mode}")
    if model:
        print(f"Modèle IA        : {model}")
    print()
    
    # Lire le fichier d'entrée
    lignes_entree = []
    col_indices = {}  # indices des colonnes résultat/commentaire
    commentaires = []
    
    for encodage in ["utf-8-sig", "utf-8", "windows-1252"]:
        try:
            with open(fichier_entree, 'r', encoding=encodage, newline='') as f:
                reader = csv.reader(f, delimiter=';')
                for row in reader:
                    if not row:
                        continue
                    if (row[0] or '').strip().startswith('#'):
                        commentaires.append(row)
                        continue
                    if 'question' in (row[0] or '').lower():
                        # Capturer les indices des colonnes résultat et commentaire
                        for _ci, _cn in enumerate(row):
                            _cn_low = (_cn or '').strip().lower()
                            if _cn_low in ('résultat', 'resultat'):
                                col_indices['resultat'] = _ci
                            elif _cn_low == 'commentaire':
                                col_indices['commentaire'] = _ci
                        continue
                    lignes_entree.append(row)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    if not lignes_entree:
        print("[ERREUR] Aucune ligne à traiter")
        return 0, None
    
    print(f"{len(lignes_entree)} question(s) à traiter")
    print("-" * 70)
    
    # Charger les références une seule fois
    module_name, charger_refs, detecter = _charger_module_detection(mode)
    references = None
    if charger_refs:
        references = charger_refs(verbose=False, debug=False)
    
    resultats = []
    
    for i, row in enumerate(lignes_entree):
        question = (row[0] or '').strip()
        # Extraire résultat et commentaire si présents
        _idx_res = col_indices.get('resultat', -1)
        _idx_comm = col_indices.get('commentaire', -1)
        _val_resultat = (row[_idx_res] or '').strip() if 0 <= _idx_res < len(row) else ''
        _val_commentaire = (row[_idx_comm] or '').strip() if 0 <= _idx_comm < len(row) else ''
        if not question:
            continue
        
        resultat = rechercher(
            question=question, db_path=db_path, mode=mode, model=model,
            references=references, include_details=True,
            verbose=False, debug=debug
        )
        
        nb = resultat.get('nb', 0)
        temps = resultat.get('temps_total_ms', 0)
        criteres = resultat.get('criteres_detectes', [])
        
        # Construire les lignes du résumé pour le CSV
        lignes_resume = []
        if criteres:
            for j, c in enumerate(criteres, 1):
                type_c = c.get('type', '?')
                label = c.get('label', c.get('canonique', '?'))
                extra = ''
                if type_c == 'tag':
                    adjs = c.get('adjectifs', [])
                    if adjs:
                        adjs_str = ', '.join(a.get('canonique', str(a)) if isinstance(a, dict) else str(a) for a in adjs)
                        extra = f" [{adjs_str}]"
                elif type_c == 'meme':
                    ref_id = c.get('reference_id', '?')
                    extra = f" (ref_id={ref_id})"
                lignes_resume.append(f"[{type_c}] {label}{extra}")
        lignes_resume.append(f"→ {nb} patient(s) en {temps:.0f}ms")
        
        if resultat.get('erreur'):
            lignes_resume.append(f"⚠ {resultat['erreur']}")
        if resultat.get('gardefou'):
            lignes_resume.append(f"⚠ Garde-fou: {resultat.get('gardefou_raison', '?')}")
        
        # Ajouter JSON détection et SQL
        json_det = resultat.get('json_detection', {})
        if json_det:
            # Résumé compact du JSON de détection
            json_compact = json.dumps(json_det, ensure_ascii=False, separators=(',', ':')).replace('\n', ' ').replace('\r', '')
            # Tronquer si trop long pour le CSV
            if len(json_compact) > 500:
                json_compact = json_compact[:497] + '...'
            lignes_resume.append(f"JSON: {json_compact}")
        
        sql_txt = resultat.get('sql', '').replace('\n', ' ').replace('\r', '')
        if sql_txt:
            sql_params = resultat.get('sql_params', [])
            sql_ligne = f"SQL: {sql_txt}"
            if sql_params:
                sql_ligne += f" | params={sql_params}"
            lignes_resume.append(sql_ligne)
        
        resultats.append({
            'question': question,
            'resultat': _val_resultat,
            'commentaire': _val_commentaire,
            'lignes': lignes_resume
        })
        
        # Mini-résumé (toujours affiché)
        print(f"  [{i+1}/{len(lignes_entree)}] \"{question}\"")
        if criteres:
            for j, c in enumerate(criteres, 1):
                type_c = c.get('type', '?')
                label = c.get('label', c.get('canonique', '?'))
                extra = ''
                if type_c == 'tag':
                    adjs = c.get('adjectifs', [])
                    if adjs:
                        adjs_str = ', '.join(a.get('canonique', str(a)) if isinstance(a, dict) else str(a) for a in adjs)
                        extra = f" [{adjs_str}]"
                elif type_c == 'meme':
                    ref_id = c.get('reference_id', '?')
                    extra = f" (ref_id={ref_id})"
                print(f"        {j}. [{type_c}] {label}{extra}")
        else:
            print(f"        (aucun critère)")
        print(f"        → {nb} patient(s) en {temps:.0f}ms")
        if resultat.get('sql'):
            print(f"        SQL: {resultat['sql']}")
        if resultat.get('erreur'):
            print(f"        ⚠ {resultat['erreur']}")
        if resultat.get('gardefou'):
            print(f"        ⚠ Garde-fou: {resultat.get('gardefou_raison', '?')}")
        print()
    
    # Déterminer le nombre max de colonnes L
    max_l = max((len(r['lignes']) for r in resultats), default=0)
    entete_l = ['question', 'résultat', 'commentaire'] + [f'L{i+1}' for i in range(max_l)]
    
    # Écrire le fichier de sortie
    with open(fichier_sortie, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        for comm in commentaires:
            while len(comm) < len(entete_l):
                comm.append('')
            writer.writerow(comm)
        writer.writerow(entete_l)
        for res in resultats:
            row = [res['question'], res.get('resultat', ''), res.get('commentaire', '')] + res['lignes']
            while len(row) < len(entete_l):
                row.append('')
            writer.writerow(row)
    
    print("-" * 70)
    print(f"✓ {len(resultats)} lignes traitées → {os.path.abspath(fichier_sortie)}")
    
    return len(resultats), fichier_sortie


# =============================================================================
# POINT D'ENTRÉE CLI
# =============================================================================

def main():
    """Point d'entrée CLI."""
    print(f"╔════════════════════════════════════════════════════════════════")
    print(f"║ {__pgm__} V{__version__} - {__date__}")
    print(f"║ Recherche de patients en langage naturel")
    print(f"║ V5.1 : Support des similarités (même X que patient)")
    print(f"╚════════════════════════════════════════════════════════════════")
    print()
    
    # Afficher la disponibilité des modules
    print("Modules du pipeline:")
    print(f"  jsonsql:   {'✓' if generer_sql else '✗'}")
    print(f"  lancesql:  {'✓' if executer_sql else '✗'}")
    print(f"  trouveid:  {'✓' if TROUVEID_DISPONIBLE else '✗'} (V5.1)")
    print(f"  gardefou:  {'✓' if GARDEFOU_DISPONIBLE else '✗'}")
    print()
    
    # Charger les modèles IA
    modeles_ia = get_modeles_ia()
    modeles_courts = [m for m, c in modeles_ia.items() if c.get('actif', False)]
    
    args_list = sys.argv[1:]
    
    # Options booléennes
    verbose = '--verbose' in args_list or '-v' in args_list
    debug = '--debug' in args_list or '-d' in args_list
    no_details = '--no-details' in args_list
    
    args_list = [a for a in args_list if a not in (
        '--verbose', '-v', '--debug', '-d', '--no-details'
    )]
    
    # Détecter mode et modèle
    mode = 'standard'
    model = None
    
    if 'ia' in args_list:
        mode = 'ia'
        args_list.remove('ia')
    if 'standard' in args_list:
        mode = 'standard'
        args_list.remove('standard')
    # Compatibilité avec ancien nom 'rapide'
    if 'rapide' in args_list:
        mode = 'standard'
        args_list.remove('rapide')
    
    # Détecter le modèle (nom court depuis ia.csv)
    for m in modeles_courts:
        if m in args_list and m != 'standard':
            model = m
            args_list.remove(m)
            if mode == 'standard':
                mode = 'ia'  # Si on spécifie un modèle, c'est mode IA
            break
    
    # Détecter base et question
    database = None
    question = None
    
    for arg in args_list:
        if arg.endswith('.db'):
            database = arg
        else:
            question = arg
    
    if not database or not question:
        print("Usage:")
        print(f"  python {__pgm__} <base.db> \"<question>\" [options]")
        print(f"  python {__pgm__} <base.db> <fichier.csv> [options]")
        print()
        print("Options:")
        print("  -v, --verbose    Affichage détaillé")
        print("  -d, --debug      Affichage de débogage")
        print("  --no-details     Ne pas inclure les détails patients")
        print("  standard         Mode détection locale (défaut)")
        print("  ia               Mode détection IA")
        print()
        print("Exemples:")
        print(f'  python {__pgm__} base1000.db "patients avec béance de moins de 30 ans"')
        print(f'  python {__pgm__} base1000.db "même pathologie que Jean Dupont" -v')
        print(f'  python {__pgm__} base1000.db quentin.csv')
        return 1
    
    # Résoudre le chemin de la base
    if not os.path.exists(database):
        script_dir = Path(__file__).parent
        base_in_bases = script_dir / "bases" / database
        if base_in_bases.exists():
            database = str(base_in_bases)
        else:
            print(f"[ERREUR] Base introuvable: {os.path.abspath(database)}")
            return 1
    
    # Mode batch (CSV) ou unitaire
    if question.endswith('.csv'):
        fichier_batch = _trouver_fichier(question)
        if not fichier_batch:
            print(f"[ERREUR] Fichier introuvable: {question}")
            return 1
        print(f"Mode BATCH - Traitement de {fichier_batch.name}")
        print("-" * 70)
        nb, _ = traiter_fichier_batch(
            str(fichier_batch), database, mode=mode, model=model,
            verbose=verbose, debug=debug
        )
        return 0 if nb > 0 else 1
    
    # Exécuter la recherche
    resultat = rechercher(
        question=question,
        db_path=database,
        mode=mode,
        model=model,
        include_details=not no_details,
        verbose=verbose,
        debug=debug
    )
    
    # Afficher le résultat
    print()
    print("═" * 70)
    print("RÉSULTAT")
    print("═" * 70)
    
    if resultat.get('erreur'):
        print(f"ERREUR: {resultat['erreur']}")
    elif resultat.get('gardefou'):
        print(f"GARDE-FOU ACTIVÉ")
        print(f"  Raison: {resultat.get('gardefou_raison', '?')}")
        print(f"  Message: {resultat.get('gardefou_message', '?')}")
    else:
        print(f"Nombre de résultats: {resultat['nb']}")
        print(f"Mode: {resultat['mode']}")
        print(f"Temps total: {resultat['temps_total_ms']:.1f}ms")
        
        if resultat.get('criteres_detectes'):
            print(f"\nCritères détectés:")
            for c in resultat['criteres_detectes']:
                type_c = c.get('type', '?')
                if type_c == 'meme':
                    cible = c.get('cible', '?')
                    ref_id = c.get('reference_id', '?')
                    print(f"  - [meme] {c.get('label', '?')} (ref_id={ref_id})")
                else:
                    print(f"  - [{type_c}] {c.get('label', c.get('canonique', '?'))}")
        
        if resultat['nb'] > 0 and resultat['nb'] <= 10:
            print(f"\nPatients trouvés:")
            for p in resultat.get('patients', [])[:10]:
                if isinstance(p, dict):
                    print(f"  ID {p.get('id', '?')}: {p.get('prenom', '')} {p.get('nom', '')}")
                else:
                    print(f"  ID {p}")
    
    if debug:
        print()
        print("═" * 70)
        print("JSON COMPLET")
        print("═" * 70)
        print(json.dumps(resultat, indent=2, ensure_ascii=False))
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
