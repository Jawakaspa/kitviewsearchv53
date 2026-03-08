#*TO*#
__pgm__ = "detall.py"
__version__ = "0.0.0"
__date__ = "01/01/1970 00:00"

"""
Module orchestrateur de détection pour le système de recherche multilingue.

Ce module coordonne tous les modules de détection pour analyser une question
en langage naturel et produire un JSON unifié exploitable par jsonsql.py.

CHANGEMENTS V5.2 (16/02/2026) :
- NOUVEAU : Intégration de detid.py pour la recherche par identifiant (id XXX)
- Pipeline : detcount → detmeme → detid → detangles → dettags → detage → motsvides

CHANGEMENTS V5.1.1 (21/01/2026) :
- FIX CRITIQUE : Propagation de 'reference' de detmeme vers le JSON de sortie

CHANGEMENTS V5.1 (13/01/2026) :
- NOUVEAU : Intégration de detmeme.py pour les similarités (même X)

PIPELINE DE DÉTECTION :
    Question
      │
      ▼
    ┌─────────────────┐
    │  1. detcount    │  → LIST/COUNT
    └────────┬────────┘
             │
      ▼
    ┌─────────────────┐
    │ 1.5 detmeme     │  → Similarités (même X)
    └────────┬────────┘
             │
      ▼
    ┌─────────────────┐
    │ 1.6 detid       │  → Identifiant patient (id XXX)  ◄ NOUVEAU V5.2
    └────────┬────────┘
             │
      ▼
    ┌─────────────────┐
    │  2. detangles   │  → Angles céphalométriques
    └────────┬────────┘
             │
      ▼
    ┌─────────────────┐
    │  3. dettags     │  → Tags + adjectifs
    └────────┬────────┘
             │
      ▼
    ┌─────────────────┐
    │  4. detage      │  → Âge et sexe
    └────────┬────────┘
             │
      ▼
    ┌─────────────────┐
    │  5. motsvides   │  → Nettoyage résidu
    └────────┬────────┘
             │
             ▼
         JSON unifié

FORMAT DE SORTIE JSON :
{
    "auteur": "cx",
    "langue": "fr",
    "listcount": "LIST" | "COUNT",
    "criteres": [
        {"type": "count", ...},
        {"type": "meme", "cible": "pathologie", "label": "Même pathologie", ...},
        {"type": "id", "detecte": "id 10122", "label": "Patient ID 10122", ...},
        {"type": "tag", "canonique": "béance", "adjectifs": [...], ...},
        {"type": "age", "sql": {...}, ...},
        {"type": "sexe", "sql": {...}, ...}
    ],
    "residu": "texte restant non reconnu",
    "question_originale": "...",
    "question_standardisee": "..."
}

Usage en import :
    from detall import charger_references, detecter_tout
    refs = charger_references(verbose=True)
    resultat = detecter_tout(question, refs, verbose=True)

Usage CLI unitaire :
    python detall.py "patients avec béance antérieure de moins de 30 ans"
    python detall.py "id 10122 avec béance" -d

Usage CLI batch :
    python detall.py tests/testsdetallin.csv
"""

import os
import sys
import csv
import json
import re
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Import de standardise
try:
    from standardise import standardise
except ImportError:
    import unicodedata
    def standardise(texte):
        """Version simplifiée de standardise si le module n'est pas disponible."""
        if texte is None or texte == "":
            return ""
        texte = texte.lower()
        texte = unicodedata.normalize('NFD', texte)
        texte = ''.join(char for char in texte if unicodedata.category(char) != 'Mn')
        for char in ".!-_?":
            texte = texte.replace(char, " ")
        texte = re.sub(r'\s+', ' ', texte)
        return texte.strip()


# =============================================================================
# IMPORTS DES MODULES DE DÉTECTION
# =============================================================================

# detcount - Détection LIST/COUNT
try:
    from detcount import charger_patterns_count, detecter_count
    DETCOUNT_DISPONIBLE = True
except ImportError:
    DETCOUNT_DISPONIBLE = False
    def charger_patterns_count(*args, **kwargs): return []
    def detecter_count(q, p, **kw): return {'listcount': 'LIST', 'criteres': [], 'residu': q}

# detmeme - Détection des similarités (même X) - V5.1
try:
    from detmeme import charger_patterns_meme, detecter_meme
    DETMEME_DISPONIBLE = True
except ImportError:
    DETMEME_DISPONIBLE = False
    def charger_patterns_meme(*args, **kwargs): return {'synonymes_meme': [], 'synonymes_que': [], 'cibles': {}}
    def detecter_meme(q, p, **kw): return {'criteres': [], 'residu': q}

# detid - Détection des identifiants patients (id XXX) - NOUVEAU V5.2
try:
    from detid import detecter_id
    DETID_DISPONIBLE = True
except ImportError:
    DETID_DISPONIBLE = False
    def detecter_id(q, **kw): return {'criteres': [], 'residu': q}

# detangles - Détection des angles céphalométriques
try:
    from detangles import charger_patterns_angles, detecter_angles
    DETANGLES_DISPONIBLE = True
except ImportError:
    DETANGLES_DISPONIBLE = False
    def charger_patterns_angles(*args, **kwargs): return []
    def detecter_angles(q, p, **kw): return {'criteres': [], 'residu': q, 'question_standardisee': q}

# dettags - Détection des tags (V3 avec adjectifs intégrés)
try:
    from dettags import charger_tags, detecter_tags
    DETTAGS_DISPONIBLE = True
except ImportError:
    DETTAGS_DISPONIBLE = False
    def charger_tags(*args, **kwargs): return [], {}
    def detecter_tags(q, t, a, **kw): return {'criteres': [], 'residu': q, 'question_standardisee': q}

# detage - Détection âge/sexe
try:
    from detage import charger_patterns_ages, detecter_age
    DETAGE_DISPONIBLE = True
except ImportError:
    DETAGE_DISPONIBLE = False
    def charger_patterns_ages(*args, **kwargs): return []
    def detecter_age(q, p, **kw): return {'criteres': [], 'residu': q}

# motsvides - Suppression des mots vides
try:
    from motsvides import supprimer_motsvides
    MOTSVIDES_DISPONIBLE = True
except ImportError:
    MOTSVIDES_DISPONIBLE = False
    def supprimer_motsvides(texte, **kw): return {'residu': texte, 'mots_supprimes': []}


def charger_references(verbose=False, debug=False) -> dict:
    """
    Charge tous les fichiers de référence nécessaires aux détections.
    
    Args:
        verbose: Mode verbose
        debug: Mode debug
    
    Returns:
        dict avec:
        {
            'patterns_count': [...],
            'patterns_meme': {...},
            'patterns_angles': [...],
            'tags_data': {...},
            'adjs_data': {...},
            'patterns_ages': [...]
        }
    """
    script_dir = Path(__file__).parent
    
    # Chemins vers fichiers de référence
    communb_path = script_dir / "refs" / "communb.csv"
    commun_path = script_dir / "refs" / "commun.csv"
    angles_path = script_dir / "refs" / "angles.csv"
    tags_path = script_dir / "refs" / "tags.csv"
    adjectifs_path = script_dir / "refs" / "adjectifs.csv"
    ages_path = script_dir / "refs" / "ages.csv"
    
    # Alternatives: c:/g/refs/ ou c:/cx/refs/
    alt_refs_list = [Path("c:/g/refs"), Path("c:/cx/refs")]
    for alt_refs in alt_refs_list:
        if not communb_path.exists() and (alt_refs / "communb.csv").exists():
            communb_path = alt_refs / "communb.csv"
        if not commun_path.exists() and (alt_refs / "commun.csv").exists():
            commun_path = alt_refs / "commun.csv"
        if not angles_path.exists() and (alt_refs / "angles.csv").exists():
            angles_path = alt_refs / "angles.csv"
        if not tags_path.exists() and (alt_refs / "tags.csv").exists():
            tags_path = alt_refs / "tags.csv"
        if not adjectifs_path.exists() and (alt_refs / "adjectifs.csv").exists():
            adjectifs_path = alt_refs / "adjectifs.csv"
        if not ages_path.exists() and (alt_refs / "ages.csv").exists():
            ages_path = alt_refs / "ages.csv"
    
    config_path = communb_path if communb_path.exists() else commun_path
    
    references = {
        'patterns_count': [],
        'patterns_meme': {},
        'patterns_angles': [],
        'tags_data': {},
        'adjs_data': {},
        'patterns_ages': []
    }
    
    # 1. Charger patterns COUNT
    if DETCOUNT_DISPONIBLE and config_path.exists():
        references['patterns_count'] = charger_patterns_count(str(config_path), verbose=verbose, debug=debug)
        if verbose:
            print(f"  ✓ {len(references['patterns_count'])} mot(s) COUNT")
    elif verbose:
        print(f"  ⚠ detcount non disponible ou fichier config introuvable")
    
    # 1.5 Charger synonymes meme/que
    if DETMEME_DISPONIBLE:
        references['patterns_meme'] = charger_patterns_meme(None, verbose=verbose, debug=debug)
        if verbose:
            nb_meme = len(references['patterns_meme'].get('synonymes_meme', []))
            nb_que = len(references['patterns_meme'].get('synonymes_que', []))
            print(f"  ✓ {nb_meme} synonyme(s) 'même', {nb_que} synonyme(s) 'que'")
    elif verbose:
        print(f"  ⚠ detmeme non disponible")
    
    # 1.6 detid : pas de chargement nécessaire (pas de CSV)
    if verbose:
        if DETID_DISPONIBLE:
            print(f"  ✓ detid disponible (pas de référentiel à charger)")
        else:
            print(f"  ⚠ detid non disponible")
    
    # 2. Charger angles.csv
    if DETANGLES_DISPONIBLE and angles_path.exists():
        references['patterns_angles'] = charger_patterns_angles(str(angles_path), verbose=verbose, debug=debug)
        if verbose:
            print(f"  ✓ {len(references['patterns_angles'])} pattern(s) angles")
    elif verbose:
        print(f"  ⚠ detangles non disponible ou angles.csv introuvable")
    
    # 3. Charger tags.csv et adjectifs.csv
    if DETTAGS_DISPONIBLE:
        if tags_path.exists():
            adjs_path_str = str(adjectifs_path) if adjectifs_path.exists() else None
            references['tags_data'], references['adjs_data'] = charger_tags(
                str(tags_path), adjs_path_str,
                verbose=verbose, debug=debug
            )
            if verbose:
                nb_tags = len(references['tags_data'].get('tags', {}))
                nb_lookup = len(references['tags_data'].get('lookup', []))
                nb_adjs = len(references['adjs_data'].get('adjectifs', {})) if references['adjs_data'] else 0
                print(f"  ✓ {nb_tags} tag(s), {nb_lookup} entrées lookup, {nb_adjs} adjectif(s)")
        elif verbose:
            print(f"  ⚠ tags.csv introuvable à {tags_path}")
    elif verbose:
        print(f"  ⚠ dettags non disponible")
    
    # 4. Charger ages.csv
    if DETAGE_DISPONIBLE and ages_path.exists():
        references['patterns_ages'] = charger_patterns_ages(str(ages_path), verbose=verbose, debug=debug)
        if verbose:
            print(f"  ✓ {len(references['patterns_ages'])} pattern(s) âge")
    elif verbose:
        print(f"  ⚠ detage non disponible ou ages.csv introuvable")
    
    return references


def detecter_tout(question: str, references: dict, verbose=False, debug=False) -> dict:
    """
    Orchestre tous les modules de détection sur une question.
    
    Pipeline V5.2 :
        Question → detcount → detmeme → detid → detangles → dettags → detage → motsvides → JSON
    """
    question_originale = question
    
    if debug:
        print(f"[DEBUG] detall: Question brute: '{question}'")
    
    question_norm = standardise(question)
    question_norm = re.sub(r'[,;]+', ' ', question_norm)
    question_norm = re.sub(r'\s+', ' ', question_norm).strip()
    
    if debug:
        print(f"[DEBUG] detall: Question standardisée: '{question_norm}'")
    
    resultat = {
        'auteur': 'cx',
        'langue': 'fr',
        'listcount': 'LIST',
        'criteres': [],
        'residu': question_norm,
        'question_originale': question_originale,
        'question_standardisee': question_norm
    }
    
    residu = question_norm
    
    # =========================================================================
    # ÉTAPE 1 : detcount - Détection LIST/COUNT
    # =========================================================================
    if debug:
        print()
        print(f"[DEBUG] detall: === ÉTAPE 1 : detcount ===")
    
    if DETCOUNT_DISPONIBLE and references['patterns_count']:
        resultat_count = detecter_count(
            residu, references['patterns_count'],
            verbose=verbose, debug=debug
        )
        resultat['listcount'] = resultat_count['listcount']
        resultat['criteres'].extend(resultat_count['criteres'])
        residu = resultat_count['residu']
        
        if debug:
            print(f"[DEBUG] detall: Listcount = {resultat['listcount']}")
            print(f"[DEBUG] detall: Résidu après count: '{residu}'")
    
    # =========================================================================
    # ÉTAPE 1.5 : detmeme - Détection des similarités (même X) - V5.1
    # =========================================================================
    if debug:
        print()
        print(f"[DEBUG] detall: === ÉTAPE 1.5 : detmeme (V5.1) ===")
    
    if DETMEME_DISPONIBLE and references['patterns_meme']:
        resultat_meme = detecter_meme(
            residu, references['patterns_meme'],
            verbose=verbose, debug=debug
        )
        resultat['criteres'].extend(resultat_meme['criteres'])
        residu = resultat_meme['residu']
        
        if resultat_meme.get('reference'):
            resultat['reference'] = resultat_meme['reference']
        
        if debug:
            nb_meme = len(resultat_meme['criteres'])
            print(f"[DEBUG] detall: {nb_meme} critère(s) 'même' détecté(s)")
            if resultat_meme.get('reference'):
                print(f"[DEBUG] detall: Référence: {resultat_meme['reference']}")
            print(f"[DEBUG] detall: Résidu après meme: '{residu}'")
    
    # =========================================================================
    # ÉTAPE 1.6 : detid - Détection des identifiants patients - NOUVEAU V5.2
    # =========================================================================
    if debug:
        print()
        print(f"[DEBUG] detall: === ÉTAPE 1.6 : detid ===")
    
    if DETID_DISPONIBLE:
        resultat_id = detecter_id(
            residu,
            verbose=verbose,
            debug=debug
        )
        resultat['criteres'].extend(resultat_id['criteres'])
        residu = resultat_id['residu']
        
        if debug:
            nb_id = len(resultat_id['criteres'])
            print(f"[DEBUG] detall: {nb_id} identifiant(s) détecté(s)")
            print(f"[DEBUG] detall: Résidu après id: '{residu}'")
    
    # =========================================================================
    # ÉTAPE 2 : detangles - Détection des angles céphalométriques
    # =========================================================================
    if debug:
        print()
        print(f"[DEBUG] detall: === ÉTAPE 2 : detangles ===")
    
    if DETANGLES_DISPONIBLE and references['patterns_angles']:
        resultat_angles = detecter_angles(
            residu, references['patterns_angles'],
            verbose=verbose, debug=debug
        )
        resultat['criteres'].extend(resultat_angles['criteres'])
        residu = resultat_angles['residu']
        
        if debug:
            nb_angles = len(resultat_angles['criteres'])
            print(f"[DEBUG] detall: {nb_angles} angle(s) détecté(s)")
            print(f"[DEBUG] detall: Résidu après angles: '{residu}'")
    
    # =========================================================================
    # ÉTAPE 3 : dettags - Détection des tags + adjectifs
    # =========================================================================
    if debug:
        print()
        print(f"[DEBUG] detall: === ÉTAPE 3 : dettags ===")
    
    if DETTAGS_DISPONIBLE and references['tags_data']:
        resultat_tags = detecter_tags(
            residu, references['tags_data'], references['adjs_data'],
            verbose=verbose, debug=debug
        )
        resultat['criteres'].extend(resultat_tags['criteres'])
        residu = resultat_tags['residu']
        
        if debug:
            nb_tags = len(resultat_tags['criteres'])
            print(f"[DEBUG] detall: {nb_tags} tag(s) détecté(s)")
            print(f"[DEBUG] detall: Résidu après tags: '{residu}'")
    
    # =========================================================================
    # ÉTAPE 4 : detage - Détection âge/sexe
    # =========================================================================
    if debug:
        print()
        print(f"[DEBUG] detall: === ÉTAPE 4 : detage ===")
    
    if DETAGE_DISPONIBLE and references['patterns_ages']:
        resultat_age = detecter_age(
            residu, references['patterns_ages'],
            verbose=verbose, debug=debug
        )
        resultat['criteres'].extend(resultat_age['criteres'])
        residu = resultat_age['residu']
        
        if debug:
            nb_age = len([c for c in resultat_age['criteres'] if c.get('type') == 'age'])
            nb_sexe = len([c for c in resultat_age['criteres'] if c.get('type') == 'sexe'])
            print(f"[DEBUG] detall: {nb_age} critère(s) âge, {nb_sexe} critère(s) sexe")
            print(f"[DEBUG] detall: Résidu après ages: '{residu}'")
    
    # =========================================================================
    # ÉTAPE 5 : motsvides - Nettoyage final du résidu
    # =========================================================================
    if debug:
        print()
        print(f"[DEBUG] detall: === ÉTAPE 5 : motsvides ===")
    
    if MOTSVIDES_DISPONIBLE and residu.strip():
        resultat_motsvides = supprimer_motsvides(
            residu, verbose=verbose, debug=debug
        )
        residu = resultat_motsvides['residu']
        
        if debug:
            nb_supprimes = len(resultat_motsvides.get('mots_supprimes', []))
            print(f"[DEBUG] detall: {nb_supprimes} mot(s) vide(s) supprimé(s)")
            print(f"[DEBUG] detall: Résidu final: '{residu}'")
    
    resultat['residu'] = residu
    
    return resultat


def identifier_tout(question: str, references: dict, verbose=False, debug=False) -> Tuple[dict, str]:
    """Wrapper de compatibilité avec l'ancienne signature."""
    resultat = detecter_tout(question, references, verbose=verbose, debug=debug)
    
    pathologies = []
    for critere in resultat['criteres']:
        if critere.get('type') == 'tag':
            pathologies.append(critere.get('canonique', critere.get('label', '')))
    
    filtres = {
        'listcount': resultat['listcount'],
        'pathologies': pathologies,
        'criteres': resultat['criteres']
    }
    
    return filtres, resultat['residu']


def trouver_fichier_batch(nom_fichier):
    """Cherche un fichier batch dans plusieurs répertoires possibles."""
    chemin = Path(nom_fichier)
    if chemin.exists():
        return chemin
    
    repertoires = [Path('.'), Path('tests'), Path('c:/g/tests'), Path('c:/g')]
    nom_seul = Path(nom_fichier).name
    
    for rep in repertoires:
        chemin_candidat = rep / nom_seul
        if chemin_candidat.exists():
            return chemin_candidat
    
    return None


def traiter_fichier_batch(fichier_entree: str, references: dict, verbose=False, debug=False):
    """Traite un fichier batch et génère [nom_entrée]detall.csv."""
    chemin_entree = Path(fichier_entree)
    if not chemin_entree.exists():
        chemin_entree = trouver_fichier_batch(fichier_entree)
        if not chemin_entree:
            print(f"[ERREUR] Fichier introuvable: {fichier_entree}")
            return 0, None
    
    nom_base = chemin_entree.stem
    module_name = Path(__pgm__).stem  # 'detall'
    fichier_sortie = chemin_entree.parent / f"{nom_base}{module_name}.csv"
    
    print(f"Fichier d'entrée : {os.path.abspath(str(chemin_entree))}")
    print(f"Fichier de sortie: {os.path.abspath(str(fichier_sortie))}")
    print()
    
    lignes_entree = []
    col_indices = {}  # indices des colonnes résultat/commentaire
    commentaires = []
    
    for encodage in ["utf-8-sig", "utf-8", "windows-1252"]:
        try:
            with open(str(chemin_entree), 'r', encoding=encodage, newline='') as f:
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
        print(f"[ERREUR] Aucune ligne à traiter")
        return 0, None
    
    print(f"{len(lignes_entree)} question(s) à traiter")
    print("-" * 70)
    
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
        
        resultat = detecter_tout(question, references, verbose=verbose, debug=debug)
        
        nb_meme = len([c for c in resultat['criteres'] if c.get('type') == 'meme'])
        nb_id = len([c for c in resultat['criteres'] if c.get('type') == 'id'])
        nb_tags = len([c for c in resultat['criteres'] if c.get('type') == 'tag'])
        nb_age = len([c for c in resultat['criteres'] if c.get('type') == 'age'])
        nb_sexe = len([c for c in resultat['criteres'] if c.get('type') == 'sexe'])
        
        # Construire les lignes du résumé pour le CSV
        lignes_resume = []
        if resultat['criteres']:
            for j, c in enumerate(resultat['criteres'], 1):
                type_c = c.get('type', '?')
                label = c.get('label', c.get('canonique', '?'))
                extra = ''
                if type_c == 'tag':
                    adjs = c.get('adjectifs', [])
                    if adjs:
                        adjs_str = ', '.join(a.get('canonique', str(a)) if isinstance(a, dict) else str(a) for a in adjs)
                        extra = f" [{adjs_str}]"
                lignes_resume.append(f"[{type_c}] {label}{extra}")
        lignes_resume.append(f"Résidu: '{resultat['residu']}'")
        
        resultats.append({
            'question': question,
            'resultat': _val_resultat,
            'commentaire': _val_commentaire,
            'lignes': lignes_resume
        })
        
        # Mini-résumé pour chaque question (toujours affiché)
        print(f"  [{i+1}/{len(lignes_entree)}] \"{question}\"")
        if resultat['criteres']:
            for j, c in enumerate(resultat['criteres'], 1):
                type_c = c.get('type', '?')
                label = c.get('label', c.get('canonique', '?'))
                extra = ''
                if type_c == 'tag':
                    adjs = c.get('adjectifs', [])
                    if adjs:
                        adjs_str = ', '.join(a.get('canonique', str(a)) if isinstance(a, dict) else str(a) for a in adjs)
                        extra = f" [{adjs_str}]"
                print(f"        {j}. [{type_c}] {label}{extra}")
        else:
            print(f"        (aucun critère)")
        print(f"        Résidu: '{resultat['residu']}'")
        print()
    
    # Déterminer le nombre max de colonnes L
    max_l = max((len(r['lignes']) for r in resultats), default=0)
    entete_l = ['question', 'résultat', 'commentaire'] + [f'L{i+1}' for i in range(max_l)]
    
    with open(str(fichier_sortie), 'w', encoding='utf-8-sig', newline='') as f:
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
    print(f"✓ {len(resultats)} lignes traitées → {os.path.abspath(str(fichier_sortie))}")
    
    return len(resultats), fichier_sortie


def main():
    """Point d'entrée CLI."""
    print(f"╔════════════════════════════════════════════════════════════════")
    print(f"║ {__pgm__} V{__version__} - {__date__}")
    print(f"║ Orchestrateur de détection (analyse langage naturel)")
    print(f"║ V5.2 : Intégration detid (identifiants patients)")
    print(f"╚════════════════════════════════════════════════════════════════")
    print()
    
    # Sans argument → afficher l'aide
    if len(sys.argv) < 2 or (len(sys.argv) == 2 and sys.argv[1] in ('-h', '--help')):
        print("Usage:")
        print('  python detall.py "<question>"          Analyse une question')
        print("  python detall.py tests/testallin.csv   Traite un fichier batch")
        print()
        print("Options:")
        print("  -v, --verbose   Affichage modéré (résultats)")
        print("  -d, --debug     Affichage complet (tout)")
        print()
        print("Exemples:")
        print('  python detall.py "bruxisme sévère femme de 30 ans"')
        print('  python detall.py "id 10122" -v')
        print('  python detall.py "même portrait que id 10122 Guillaume" -d')
        print("  python detall.py tests/testallin.csv -v")
        return 0

    parser = argparse.ArgumentParser(
        description="Analyse une question en langage naturel et détecte les critères de recherche"
    )
    parser.add_argument('question', help='Question en langage naturel OU fichier xxxin.csv')
    parser.add_argument('-v', '--verbose', action='store_true', help='Affichage modéré')
    parser.add_argument('-d', '--debug', action='store_true', help='Affichage complet')
    
    args = parser.parse_args()
    
    print("Modules de détection:")
    print(f"  detcount:  {'✓' if DETCOUNT_DISPONIBLE else '✗'}")
    print(f"  detmeme:   {'✓' if DETMEME_DISPONIBLE else '✗'} (V5.1)")
    print(f"  detid:     {'✓' if DETID_DISPONIBLE else '✗'} (V5.2)")
    print(f"  detangles: {'✓' if DETANGLES_DISPONIBLE else '✗'}")
    print(f"  dettags:   {'✓' if DETTAGS_DISPONIBLE else '✗'}")
    print(f"  detage:    {'✓' if DETAGE_DISPONIBLE else '✗'}")
    print(f"  motsvides: {'✓' if MOTSVIDES_DISPONIBLE else '✗'}")
    print()
    
    print("Chargement des références...")
    references = charger_references(verbose=True, debug=args.debug)
    print()
    
    est_fichier_batch = args.question.endswith('.csv')
    
    if est_fichier_batch:
        print(f"Mode BATCH - Traitement de {args.question}")
        print("-" * 70)
        nb_lignes, _ = traiter_fichier_batch(
            args.question, references,
            verbose=args.verbose, debug=args.debug
        )
        return 0 if nb_lignes > 0 else 1
    
    else:
        print(f"Question: \"{args.question}\"")
        print()
        
        resultat = detecter_tout(
            args.question, references,
            verbose=args.verbose, debug=args.debug
        )
        
        print()
        print("═" * 70)
        print("RÉSUMÉ")
        print("═" * 70)
        print(f"Mode: {resultat['listcount']}")
        print(f"Nb critères: {len(resultat['criteres'])}")
        
        for i, c in enumerate(resultat['criteres'], 1):
            type_c = c.get('type', '?')
            label = c.get('label', c.get('canonique', '?'))
            print(f"  {i}. [{type_c}] {label}")
        
        print(f"\nRésidu: '{resultat['residu']}'")
        
        print()
        print("═" * 70)
        print("JSON COMPLET")
        print("═" * 70)
        print(json.dumps(resultat, indent=2, ensure_ascii=False))
        
        return 0


if __name__ == '__main__':
    sys.exit(main())
