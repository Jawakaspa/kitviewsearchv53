# detiabrut.py V1.0.3 - 05/01/2026 20:26:46
__pgm__ = "detiabrut.py"
__version__ = "1.0.3"
__date__ = "05/01/2026 20:26:46"

"""
Module de détection IA avec options de configuration des référentiels.

VERSION CONFIGURABLE de detia.py permettant d'activer/désactiver sélectivement
les référentiels injectés dans le prompt IA et le post-traitement.

BUT : Mesurer l'importance de chaque référentiel en comparant les résultats
      avec/sans leur utilisation.

RÉFÉRENTIELS DISPONIBLES :
    tags     : Liste des tags pathologiques dans le prompt IA
    adjs     : Liste des adjectifs dans le prompt IA
    ages     : Patterns âge/sexe dans le prompt IA
    angles   : Seuils ANB/SNA/SNB dans le prompt IA
    mapping  : Post-traitement détecté → canonique

SYNTAXE CLI :
    +xxx     : Active le référentiel xxx
    -xxx     : Désactive le référentiel xxx
    all      : Active tous les référentiels (par défaut, équivalent à detia.py)
    none     : Désactive tous les référentiels (IA brute sans aide)

PAR DÉFAUT : Tout est DÉSACTIVÉ (comportement = none = IA brute)

EXEMPLES :
    python detiabrut.py "bruxisme sévère"                    # Tout désactivé (défaut=none)
    python detiabrut.py "bruxisme sévère" none               # Tout désactivé (explicite)
    python detiabrut.py "bruxisme sévère" all                # Tout actif (= detia.py)
    python detiabrut.py "bruxisme sévère" +tags              # Brut + tags seul
    python detiabrut.py "bruxisme sévère" +adjs +mapping     # Brut + adjs + mapping
    python detiabrut.py "grincement" all -tags               # Tout sauf tags
    python detiabrut.py tests.csv sonnet                     # Batch mode brut
    python detiabrut.py tests.csv all sonnet                 # Batch mode tout actif

SIGNATURE JSON :
    Le champ "auteur" indique la configuration :
    - "openai/gpt-4o"                    → mode all (tout activé)
    - "openai/gpt-4o [none]"             → mode none (tout désactivé)
    - "openai/gpt-4o [-tags,-mapping]"   → tags et mapping désactivés
    - "openai/gpt-4o [none,+mapping]"    → brut sauf mapping
"""

import os
import sys
import json
import csv
import argparse
from pathlib import Path
from typing import Dict, List, Set, Optional

# Import depuis detia.py
try:
    from detia import (
        charger_references,
        charger_langues_actives,
        charger_modeles_ia,
        get_modeles_ia,
        _get_model_config,
        _construire_auteur,
        _appeler_openai_direct,
        _appeler_eden_ai,
        _mapper_vers_canonique,
        standardise,
        supprimer_motsvides,
        MOTSVIDES_DISPONIBLE,
        DEFAULT_MODEL,
        DEFAULT_LANGUE,
        trouver_fichier_batch,
        _identifier_argument
    )
    DETIA_DISPONIBLE = True
except ImportError as e:
    print(f"[ERREUR] Impossible d'importer detia.py: {e}")
    DETIA_DISPONIBLE = False
    sys.exit(1)

# =============================================================================
# CONSTANTES - RÉFÉRENTIELS DISPONIBLES
# =============================================================================

REFERENTIELS_DISPONIBLES = {'tags', 'adjs', 'ages', 'angles', 'mapping'}

# Raccourcis
RACCOURCI_ALL = 'all'    # Active tout
RACCOURCI_NONE = 'none'  # Désactive tout

# Compatibilité avec ancienne syntaxe
RACCOURCI_DETIA = 'detia'  # Alias de all
RACCOURCI_BRUT = 'brut'    # Alias de none


def parse_options(args: List[str]) -> tuple[Set[str], List[str]]:
    """
    Parse les arguments pour extraire la configuration des référentiels.
    
    Syntaxe:
        +xxx     : Active xxx
        -xxx     : Désactive xxx
        all      : Active tout (point de départ)
        none     : Désactive tout (point de départ)
    
    Returns:
        (referentiels_actifs, autres_args)
    """
    # Par défaut, tout est DÉSACTIVÉ (none) pour ne pas faire doublon avec detia
    actifs = set()
    autres = []
    
    for arg in args:
        arg_lower = arg.lower()
        
        # Raccourcis globaux
        if arg_lower in (RACCOURCI_ALL, RACCOURCI_DETIA):
            actifs = REFERENTIELS_DISPONIBLES.copy()
            continue
        
        if arg_lower in (RACCOURCI_NONE, RACCOURCI_BRUT):
            actifs = set()
            continue
        
        # Activation explicite +xxx
        if arg_lower.startswith('+') and arg_lower[1:] in REFERENTIELS_DISPONIBLES:
            actifs.add(arg_lower[1:])
            continue
        
        # Désactivation -xxx
        if arg_lower.startswith('-') and arg_lower[1:] in REFERENTIELS_DISPONIBLES:
            actifs.discard(arg_lower[1:])
            continue
        
        # Ancienne syntaxe : nom seul = désactivation (compatibilité)
        if arg_lower in REFERENTIELS_DISPONIBLES:
            actifs.discard(arg_lower)
            continue
        
        # Autre argument (question, moteur, langue, fichier)
        autres.append(arg)
    
    return actifs, autres


def formater_signature_auteur(auteur_base: str, actifs: Set[str]) -> str:
    """
    Formate la signature auteur avec la configuration des référentiels.
    
    Args:
        auteur_base: Ex: "openai/gpt-4o"
        actifs: Set des référentiels actifs
    
    Returns:
        Ex: "openai/gpt-4o [-tags,-mapping]" ou "openai/gpt-4o [none]"
    """
    # Tout actif → pas de suffixe
    if actifs == REFERENTIELS_DISPONIBLES:
        return auteur_base
    
    # Rien actif → [none]
    if not actifs:
        return f"{auteur_base} [none]"
    
    # Calculer ce qui est désactivé
    desactives = REFERENTIELS_DISPONIBLES - actifs
    
    # Si plus de la moitié est désactivé, partir de none et ajouter les +
    if len(desactives) > len(actifs):
        actifs_str = ','.join(f"+{r}" for r in sorted(actifs))
        return f"{auteur_base} [none,{actifs_str}]"
    
    # Sinon, lister ce qui est désactivé
    desactives_str = ','.join(f"-{r}" for r in sorted(desactives))
    return f"{auteur_base} [{desactives_str}]"


def get_config_cli_string(actifs: Set[str]) -> str:
    """
    Génère la chaîne CLI équivalente à la configuration.
    
    Returns:
        Ex: "all", "none", "-tags -mapping", "none +mapping"
    """
    if actifs == REFERENTIELS_DISPONIBLES:
        return "all"
    
    if not actifs:
        return "none"
    
    desactives = REFERENTIELS_DISPONIBLES - actifs
    
    # Si plus de la moitié est désactivé, partir de none
    if len(desactives) > len(actifs):
        return "none " + " ".join(f"+{r}" for r in sorted(actifs))
    
    # Sinon, lister les désactivations
    return " ".join(f"-{r}" for r in sorted(desactives))


# =============================================================================
# CONSTRUCTION DU PROMPT SYSTÈME CONFIGURABLE
# =============================================================================

def _construire_prompt_systeme_brut(references: dict, actifs: Set[str]) -> str:
    """
    Construit le prompt système en fonction des référentiels actifs.
    
    Args:
        references: Dictionnaire des références chargées
        actifs: Set des référentiels ACTIFS
    """
    # Section TAGS
    # FIX V2 : clé corrigée 'tags_liste' → 'liste_tags' (bug: ne chargeait jamais les tags)
    if 'tags' in actifs and references.get('liste_tags'):
        categories = references.get('categories_tags', {})  # V2
        if categories:
            tags_liste = '\n'.join(
                f"- {t} ({categories[t]})" if t in categories else f"- {t}"
                for t in references['liste_tags'][:800]
            )
        else:
            tags_liste = '\n'.join(f"- {t}" for t in references['liste_tags'][:800])
        section_tags = f"""=== TAGS PATHOLOGIQUES ===
{tags_liste}
"""
    else:
        section_tags = """=== TAGS PATHOLOGIQUES ===
(Utilise tes connaissances générales en orthodontie pour détecter les pathologies)
"""
    
    # Section ADJECTIFS
    # FIX V2 : clé corrigée 'adjs_liste' → 'liste_adjs'
    if 'adjs' in actifs and references.get('liste_adjs'):
        adjs_liste = '\n'.join(f"- {a}" for a in references['liste_adjs'][:200])
        section_adjs = f"""=== ADJECTIFS ===
{adjs_liste}
"""
    else:
        section_adjs = """=== ADJECTIFS ===
(Utilise tes connaissances générales pour détecter les adjectifs qualificatifs)
"""
    
    # Section ANGLES
    if 'angles' in actifs:
        section_angles = """=== ANGLES CÉPHALOMÉTRIQUES ===
| Angle | Condition | Seuil | Tag résultant |
|-------|-----------|-------|---------------|
| ANB   | BETWEEN   | 0-4   | classe i squelettique |
| ANB   | >         | 4     | classe ii squelettique |
| ANB   | <         | 0     | classe iii squelettique |
"""
    else:
        section_angles = """=== ANGLES CÉPHALOMÉTRIQUES ===
(Angles non pris en charge dans ce mode)
"""
    
    # Section AGES
    if 'ages' in actifs:
        section_ages = """=== CRITÈRES D'ÂGE ET SEXE ===
IMPORTANT - Règles pour l'âge :
- "{n} ans", "de {n} ans", "âgé de {n} ans" → âge EXACT, operateur "="
- "moins de {n} ans", "de moins de {n} ans", "inférieur à {n} ans" → operateur "<"
- "plus de {n} ans", "de plus de {n} ans", "supérieur à {n} ans" → operateur ">"
- "entre {n} et {n} ans", "compris entre {n} et {n}" → operateur "BETWEEN" avec valeur et valeur2

ATTENTION - RÈGLE CRITIQUE :
Quand la question contient DEUX conditions d'âge SÉPARÉES reliées par "et", tu DOIS retourner DEUX critères d'âge distincts, JAMAIS un BETWEEN.
- "supérieur à 17 et inférieur à 23" → DEUX critères : {"operateur": ">", "valeur": 17} ET {"operateur": "<", "valeur": 23}
- "plus de 20 ans et moins de 23 ans" → DEUX critères : {"operateur": ">", "valeur": 20} ET {"operateur": "<", "valeur": 23}
- "entre 13 et 16" → UN critère BETWEEN (formulation explicite "entre...et...")
Le BETWEEN est réservé UNIQUEMENT aux formulations "entre X et Y" ou "compris entre X et Y".

Exemples :
- "14 ans" ou "de 14 ans" → {"type": "age", "detecte": "14 ans", "operateur": "=", "valeur": 14}
- "moins de 30 ans" → {"type": "age", "detecte": "moins de 30 ans", "operateur": "<", "valeur": 30}
- "plus de 18 ans" → {"type": "age", "detecte": "plus de 18 ans", "operateur": ">", "valeur": 18}
- "supérieur à 17 ans" → {"type": "age", "detecte": "supérieur à 17 ans", "operateur": ">", "valeur": 17}
- "inférieur à 23 ans" → {"type": "age", "detecte": "inférieur à 23 ans", "operateur": "<", "valeur": 23}
- "entre 10 et 15 ans" → {"type": "age", "detecte": "entre 10 et 15 ans", "operateur": "BETWEEN", "valeur": 10, "valeur2": 15}
- "supérieur à 17 et inférieur à 23" → DEUX critères age séparés (> 17) et (< 23), PAS un BETWEEN
- "enfants" → operateur "<", valeur 12
- "adolescents" → operateur "BETWEEN", valeur 12, valeur2 18
- "adultes" → operateur ">=", valeur 18

Sexe :
- femme/fille/femmes/patiente/patientes → "F"
- homme/garçon/hommes/patient/patients → "M"
"""
    else:
        section_ages = """=== CRITÈRES D'ÂGE ET SEXE ===
(Critères âge/sexe non pris en charge dans ce mode)
"""
    
    return f"""Tu es un analyseur de requêtes orthodontiques. Tu dois IDENTIFIER les termes présents dans la question.

=== MISSION ===
1. Détecter les TAGS (pathologies) de la liste ci-dessous
2. Détecter les ADJECTIFS qualifiant ces tags
3. Détecter les critères d'ÂGE et de SEXE
4. Détecter les demandes de COMPTAGE (combien, nombre de)
5. Détecter les ANGLES céphalométriques (ANB, SNA, SNB)

{section_tags}
{section_adjs}
{section_angles}
{section_ages}
=== COMPTAGE ===
- "combien", "nombre de" → listcount = "COUNT"
- Sinon → listcount = "LIST"

=== FORMAT DE SORTIE (JSON strict) ===
{{
    "langue": "fr",
    "listcount": "COUNT" ou "LIST",
    "criteres": [
        {{"type": "tag", "detecte": "terme", "adjectifs": ["adj1"]}},
        {{"type": "age", "detecte": "...", "operateur": "<", "valeur": 30}},
        {{"type": "sexe", "detecte": "...", "valeur": "M|F"}}
    ],
    "residu": "mots non reconnus"
}}

RÈGLES: Retourne UNIQUEMENT du JSON valide.
CLASSE 2 : "classe 2" seul = classification d'ANGLE (rapport molaire dentaire).
"classe 2 squelettique" = classification de Ballard (rapport osseux, ANB).
JAMAIS utiliser "classe ii squelettique" sauf si "squelettique" est ÉCRIT dans la question
ou si c'est un critère d'angle céphalométrique (ANB > 4)."""


def _construire_prompt_utilisateur(question: str) -> str:
    """Construit le prompt utilisateur."""
    return f'Analyse cette question et retourne le JSON: "{question}"'


# =============================================================================
# MAPPING VERS CANONIQUE CONFIGURABLE
# =============================================================================

def _mapper_vers_canonique_brut(resultat_ia: dict, references: dict, actifs: Set[str], debug: bool = False) -> list:
    """
    Mappe les résultats IA vers les formes canoniques si mapping actif.
    
    Si mapping désactivé, utilise title() pour la présentation.
    """
    tags_map = references.get('tags_map', {}) if 'mapping' in actifs else {}
    adjs_map = references.get('adjs_map', {}) if 'mapping' in actifs else {}
    categories = references.get('categories_tags', {}) if 'mapping' in actifs else {}  # V2
    criteres_enrichis = []
    
    for critere in resultat_ia.get('criteres', []):
        c_type = critere.get('type', '')
        
        if c_type == 'tag':
            detecte = critere.get('detecte', '').lower().strip()
            
            # Mapping ou title()
            if tags_map:
                canontag = tags_map.get(standardise(detecte), detecte.title())
            else:
                canontag = detecte.title()
            
            canon_std = standardise(canontag) if canontag else detecte
            cat = categories.get(canon_std, '')  # V2
            
            adjectifs_enrichis = []
            for adj in critere.get('adjectifs', []):
                adj_str = adj if isinstance(adj, str) else str(adj)
                adj_lower = adj_str.lower().strip()
                
                if adjs_map:
                    canonadj = adjs_map.get(standardise(adj_lower), adj_lower.title())
                else:
                    canonadj = adj_lower.title()
                
                adjectifs_enrichis.append({
                    'detecte': adj_str,
                    'canonique': canonadj,
                    'sql': {'colonne': 'canonadjs', 'operateur': '=', 'valeur': canonadj}
                })
            
            criteres_enrichis.append({
                'type': 'tag',
                'detecte': detecte,
                'canonique': canontag,
                'label': canontag,
                'cat': cat,  # V2
                'adjectifs': adjectifs_enrichis,
                'sql': {'colonne': 'canontags', 'operateur': '=', 'valeur': canontag}
            })
        
        elif c_type == 'angle':
            tag_resultat = critere.get('tag_resultat', '')
            if tags_map:
                canontag = tags_map.get(standardise(tag_resultat.lower()), tag_resultat.title())
            else:
                canontag = tag_resultat.title()
            canon_std = standardise(canontag) if canontag else ''
            cat = categories.get(canon_std, '')  # V2
            criteres_enrichis.append({
                'type': 'tag',
                'detecte': critere.get('detecte', ''),
                'canonique': canontag,
                'label': canontag,
                'cat': cat,  # V2
                'adjectifs': [],
                'source': 'angle',
                'sql': {'colonne': 'canontags', 'operateur': '=', 'valeur': canontag}
            })
        
        elif c_type == 'age':
            criteres_enrichis.append({
                'type': 'age',
                'detecte': critere.get('detecte', ''),
                'label': f"Âge {critere.get('operateur', '<')} {critere.get('valeur', 0)}",
                'sql': {'colonne': 'age', 'operateur': critere.get('operateur', '<'), 'valeur': critere.get('valeur', 0)}
            })
        
        elif c_type == 'sexe':
            valeur = critere.get('valeur', '').upper()
            criteres_enrichis.append({
                'type': 'sexe',
                'detecte': critere.get('detecte', ''),
                'label': 'Masculin' if valeur == 'M' else 'Féminin',
                'sql': {'colonne': 'sexe', 'operateur': '=', 'valeur': valeur}
            })
        
        elif c_type == 'count':
            criteres_enrichis.append({
                'type': 'count',
                'detecte': critere.get('detecte', ''),
                'label': 'Comptage demandé'
            })
        else:
            criteres_enrichis.append(critere)
    
    return criteres_enrichis


# =============================================================================
# FONCTION DE DÉTECTION PRINCIPALE
# =============================================================================

def detecter_tout_brut(question: str, references: dict, model: str = DEFAULT_MODEL,
                       actifs: Set[str] = None, verbose: bool = False, debug: bool = False) -> dict:
    """
    Détecte tous les critères via IA avec configuration des référentiels.
    
    Args:
        question: Question à analyser
        references: Dictionnaire des références
        model: Modèle IA à utiliser
        actifs: Set des référentiels actifs (none par défaut)
        verbose: Affichage modéré
        debug: Affichage complet
    
    Returns:
        Dictionnaire de résultat enrichi
    """
    import time
    
    if actifs is None:
        actifs = set()
    
    question_std = standardise(question)
    
    # Construction du prompt
    prompt_systeme = _construire_prompt_systeme_brut(references, actifs)
    prompt_utilisateur = _construire_prompt_utilisateur(question)
    
    if debug:
        print(f"[DEBUG] Prompt système ({len(prompt_systeme)} chars)")
        print(f"[DEBUG] Référentiels actifs: {sorted(actifs)}")
    
    # Appel IA
    model_config = _get_model_config(model)
    via = model_config['via']
    model_complet = model_config['model']
    
    try:
        if via == 'openai':
            if verbose:
                print(f"  → Appel OpenAI ({model_complet})...", end=" ", flush=True)
            resultat_ia, latency_ms = _appeler_openai_direct(
                prompt_systeme, prompt_utilisateur, model_complet, debug
            )
            if verbose:
                print(f"OK ({latency_ms:.0f}ms)")
        else:
            if verbose:
                print(f"  → Appel Eden AI ({model_complet})...", end=" ", flush=True)
            resultat_ia, latency_ms = _appeler_eden_ai(
                prompt_systeme, prompt_utilisateur, model_complet, debug
            )
            if verbose:
                print(f"OK ({latency_ms:.0f}ms)")
    except Exception as e:
        return {
            'auteur': formater_signature_auteur(_construire_auteur(model_complet, via), actifs),
            'langue': references.get('langue', 'fr'),
            'listcount': 'LIST',
            'criteres': [],
            'residu': question,
            'question_originale': question,
            'question_standardisee': question_std,
            'ia_erreur': str(e),
            'ia_moteur': model,
            'ia_model': model_complet,
            'ia_via': via,
            'ia_latency_ms': 0,
            'referentiels_actifs': sorted(actifs)
        }
    
    # Mapping vers canonique
    criteres_enrichis = _mapper_vers_canonique_brut(resultat_ia, references, actifs, debug)
    
    # Calcul du résidu
    mots_utilises = set()
    for c in criteres_enrichis:
        detecte = c.get('detecte', '')
        for mot in detecte.lower().split():
            mots_utilises.add(standardise(mot))
        for adj in c.get('adjectifs', []):
            adj_det = adj.get('detecte', '') if isinstance(adj, dict) else str(adj)
            for mot in adj_det.lower().split():
                mots_utilises.add(standardise(mot))
    
    mots_question = question_std.split()
    residu_mots = [m for m in mots_question if standardise(m) not in mots_utilises]
    residu = ' '.join(residu_mots)
    
    auteur_base = _construire_auteur(model_complet, via)
    
    return {
        'auteur': formater_signature_auteur(auteur_base, actifs),
        'langue': resultat_ia.get('langue', references.get('langue', 'fr')),
        'listcount': resultat_ia.get('listcount', 'LIST'),
        'criteres': criteres_enrichis,
        'residu': residu,
        'question_originale': question,
        'question_standardisee': question_std,
        'ia_moteur': model,
        'ia_model': model_complet,
        'ia_via': via,
        'ia_latency_ms': latency_ms,
        'referentiels_actifs': sorted(actifs)
    }


# =============================================================================
# TRAITEMENT BATCH
# =============================================================================

def traiter_fichier_batch_brut(fichier_entree: str, references: dict, model: str = DEFAULT_MODEL,
                                actifs: Set[str] = None, verbose: bool = False, debug: bool = False,
                                delay: float = 0):
    """Traite un fichier CSV en mode batch."""
    import time
    
    if actifs is None:
        actifs = set()
    
    chemin_entree = Path(fichier_entree)
    nom_base = chemin_entree.stem
    module_name = Path(__pgm__).stem  # 'detiabrut'
    fichier_sortie = chemin_entree.parent / f"{nom_base}{module_name}.csv"
    
    print(f"Fichier d'entrée : {os.path.abspath(fichier_entree)}")
    print(f"Fichier de sortie: {os.path.abspath(fichier_sortie)}")
    print(f"Modèle IA       : {model}")
    print(f"Configuration   : {get_config_cli_string(actifs)}")
    if delay > 0:
        print(f"Délai inter-req : {delay}s")
    print()
    
    lignes_entree = []
    col_indices = {}  # indices des colonnes résultat/commentaire
    commentaires = []
    
    for encodage in ["utf-8-sig", "utf-8", "windows-1252"]:
        try:
            with open(fichier_entree, 'r', encoding=encodage, newline='') as f:
                for row in csv.reader(f, delimiter=';'):
                    if not row:
                        continue
                    if (row[0] or '').strip().startswith('#'):
                        commentaires.append(row)
                    elif 'question' in (row[0] or '').lower():
                        # Capturer les indices des colonnes résultat et commentaire
                        for _ci, _cn in enumerate(row):
                            _cn_low = (_cn or '').strip().lower()
                            if _cn_low in ('résultat', 'resultat'):
                                col_indices['resultat'] = _ci
                            elif _cn_low == 'commentaire':
                                col_indices['commentaire'] = _ci
                    else:
                        lignes_entree.append(row)
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    if not lignes_entree:
        print("[ERREUR] Aucune ligne")
        return 0, None
    
    print(f"{len(lignes_entree)} question(s)")
    print("-" * 70)
    
    resultats = []
    total_latency = 0
    
    for i, row in enumerate(lignes_entree, 1):
        question = next((c.strip() for c in row if c and '?' in c), (row[0] or '').strip())
        # Extraire résultat et commentaire si présents
        _idx_res = col_indices.get('resultat', -1)
        _idx_comm = col_indices.get('commentaire', -1)
        _val_resultat = (row[_idx_res] or '').strip() if 0 <= _idx_res < len(row) else ''
        _val_commentaire = (row[_idx_comm] or '').strip() if 0 <= _idx_comm < len(row) else ''
        if not question:
            continue
        
        if delay > 0 and i > 1:
            time.sleep(delay)
        
        print(f"  [{i}/{len(lignes_entree)}] {question[:60]}...", end=" ", flush=True)
        
        resultat = detecter_tout_brut(question, references, model=model,
                                       actifs=actifs, verbose=False, debug=debug)
        latency = resultat.get('ia_latency_ms', 0)
        total_latency += latency
        
        # Construire les lignes du résumé pour le CSV
        lignes_resume = []
        if resultat['criteres']:
            for j, c in enumerate(resultat['criteres'], 1):
                type_c = c.get('type', '?')
                label = c.get('label', c.get('canonique', '?'))
                extra = ''
                if type_c == 'tag':
                    adjs_c = c.get('adjectifs', [])
                    if adjs_c:
                        adjs_str = ', '.join(a.get('canonique', str(a)) if isinstance(a, dict) else str(a) for a in adjs_c)
                        extra = f" [{adjs_str}]"
                lignes_resume.append(f"[{type_c}] {label}{extra}")
        lignes_resume.append(f"Résidu: '{resultat['residu']}'")
        lignes_resume.append(f"{latency:.0f}ms")
        
        resultats.append({
            'question': question,
            'resultat': _val_resultat,
            'commentaire': _val_commentaire,
            'lignes': lignes_resume
        })
        print(f"✓ {latency:.0f}ms")
        
        # Mini-résumé pour chaque question
        print(f"        \"{question}\"")
        if resultat['criteres']:
            for j, c in enumerate(resultat['criteres'], 1):
                type_c = c.get('type', '?')
                label = c.get('label', c.get('canonique', '?'))
                extra = ''
                if type_c == 'tag':
                    adjs_c = c.get('adjectifs', [])
                    if adjs_c:
                        adjs_str = ', '.join(a.get('canonique', str(a)) if isinstance(a, dict) else str(a) for a in adjs_c)
                        extra = f" [{adjs_str}]"
                print(f"        {j}. [{type_c}] {label}{extra}")
        else:
            print(f"        (aucun critère)")
        print(f"        Résidu: '{resultat['residu']}'")
        print()
    
    # Déterminer le nombre max de colonnes L
    max_l = max((len(r['lignes']) for r in resultats), default=0)
    entete_l = ['question', 'résultat', 'commentaire'] + [f'L{i+1}' for i in range(max_l)]
    
    with open(fichier_sortie, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow([f'# Généré par detiabrut.py V{__version__} avec {model} [{get_config_cli_string(actifs)}]'] + [''] * (len(entete_l) - 1))
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
    print(f"✓ {len(resultats)} lignes → {os.path.abspath(fichier_sortie)}")
    if resultats:
        print(f"  Latence moyenne: {total_latency/len(resultats):.0f}ms")
    
    return len(resultats), fichier_sortie


# =============================================================================
# AFFICHAGE AIDE
# =============================================================================

def afficher_aide():
    """Affiche l'aide avec la nouvelle syntaxe."""
    print()
    print("RÉFÉRENTIELS DISPONIBLES :")
    print("─" * 60)
    descriptions = {
        'tags': "Liste des tags pathologiques dans le prompt IA",
        'adjs': "Liste des adjectifs dans le prompt IA", 
        'ages': "Patterns âge/sexe dans le prompt IA",
        'angles': "Seuils ANB/SNA/SNB dans le prompt IA",
        'mapping': "Post-traitement détecté → canonique"
    }
    for ref in sorted(REFERENTIELS_DISPONIBLES):
        print(f"  {ref:10} : {descriptions.get(ref, '')}")
    
    print()
    print("SYNTAXE :")
    print("─" * 60)
    print("  +xxx       Active le référentiel xxx")
    print("  -xxx       Désactive le référentiel xxx")
    print("  all        Active tous les référentiels (= detia.py)")
    print("  none       Désactive tous les référentiels (défaut)")
    print()
    print("  Note: Par défaut, tous les référentiels sont DÉSACTIVÉS (none)")
    
    print()
    print("EXEMPLES :")
    print("─" * 60)
    print(f'  python {__pgm__} "bruxisme sévère"                   # Tout désactivé (défaut)')
    print(f'  python {__pgm__} "bruxisme sévère" all               # Tout actif (= detia.py)')
    print(f'  python {__pgm__} "bruxisme sévère" none              # Tout désactivé (explicite)')
    print(f'  python {__pgm__} "grincement" +tags                  # Brut + tags seul')
    print(f'  python {__pgm__} "bruxisme important" +adjs          # Brut + adjectifs seul')
    print(f'  python {__pgm__} "bruxisme" all -tags -mapping       # Tout sauf tags/mapping')
    print(f'  python {__pgm__} "bruxisme" +mapping                 # Brut + mapping seul')
    print(f'  python {__pgm__} tests.csv sonnet                    # Batch mode brut')
    print(f'  python {__pgm__} tests.csv all sonnet                # Batch mode tout actif')
    print()
    print("TESTS DISCRIMINANTS :")
    print("─" * 60)
    print('  "grincement sévère"           → Grincement, Sévère    (défaut=none)')
    print('  "grincement sévère" all       → bruxisme, sévère      (mapping actif)')
    print('  "extraction dentaire" +tags   → avulsion              (IA + tags)')
    print('  "béance importante" +adjs     → béance, sévère        (important → sévère)')
    print()


# =============================================================================
# POINT D'ENTRÉE CLI
# =============================================================================

def main():
    """Point d'entrée CLI."""
    print(f"╔════════════════════════════════════════════════════════════════")
    print(f"║ {__pgm__} V{__version__} - {__date__}")
    print(f"║ Détection IA configurable (+/- référentiels)")
    print(f"╚════════════════════════════════════════════════════════════════")
    
    parser = argparse.ArgumentParser(
        description="Détecte les critères orthodontiques via IA avec configuration",
        add_help=False
    )
    parser.add_argument('args', nargs='*', help='Question/fichier, +/-options, moteur')
    parser.add_argument('-v', '--verbose', action='store_true', help='Affichage modéré')
    parser.add_argument('-d', '--debug', action='store_true', help='Affichage complet')
    parser.add_argument('-l', '--list', action='store_true', help='Liste les moteurs')
    parser.add_argument('-h', '--help', action='store_true', help="Affiche l'aide")
    parser.add_argument('--delay', type=float, default=0, help='Délai en secondes entre requêtes')
    
    args = parser.parse_args()
    
    # Liste des moteurs
    if args.list:
        print()
        print("Moteurs IA disponibles:")
        for moteur, config in sorted(get_modeles_ia().items()):
            if config.get('via'):
                status = "✓" if config.get('actif') else "✗"
                print(f"  {status} {moteur:15} via {config['via']}")
        print(f"\nLangues: {', '.join(charger_langues_actives())}")
        return 0
    
    # Pas d'arguments ou aide demandée → afficher aide
    if not args.args or args.help:
        afficher_aide()
        return 0
    
    # Parser les options +/- et extraire les autres arguments
    actifs, autres_args = parse_options(args.args)
    
    # Identifier les autres arguments (question, moteur, langue, fichier)
    question = None
    moteur = DEFAULT_MODEL
    langue = DEFAULT_LANGUE
    
    modeles_ia = get_modeles_ia()
    langues = charger_langues_actives()
    
    for arg in autres_args:
        arg_lower = arg.lower()
        
        if arg_lower in modeles_ia:
            moteur = arg_lower
        elif arg_lower in langues:
            langue = arg_lower
        elif arg.lower().endswith('.csv'):
            question = arg
        elif question is None:
            question = arg
    
    # Vérifier qu'on a une question
    if question is None:
        print("[ERREUR] Aucune question ou fichier spécifié")
        afficher_aide()
        return 1
    
    # Vérifier les clés API
    model_config = _get_model_config(moteur)
    via = model_config['via']
    if via == 'openai' and not os.environ.get('OPENAI_API_KEY'):
        print("[ERREUR] Variable OPENAI_API_KEY non définie")
        return 1
    if via == 'eden' and not os.environ.get('EDENAI_API_KEY'):
        print("[ERREUR] Variable EDENAI_API_KEY non définie")
        return 1
    
    # Afficher la configuration
    print()
    print(f"Moteur : {moteur}")
    print(f"Langue : {langue}")
    
    config_str = get_config_cli_string(actifs)
    if config_str == "all":
        print(f"Mode   : ALL (tous les référentiels actifs)")
    elif config_str == "none":
        print(f"Mode   : NONE (IA brute sans aide)")
    else:
        print(f"Config : {config_str}")
    
    print()
    
    # Charger les références
    print("Chargement des références...")
    references = charger_references(langue=langue, verbose=True, debug=args.debug)
    print()
    
    # Mode batch ou question unique
    if question.lower().endswith('.csv'):
        fichier_batch = trouver_fichier_batch(question)
        if not fichier_batch:
            print(f"[ERREUR] Fichier non trouvé : {question}")
            return 1
        print(f"Mode BATCH - {fichier_batch.absolute()}")
        print("-" * 70)
        nb, _ = traiter_fichier_batch_brut(str(fichier_batch), references, 
                                           model=moteur, actifs=actifs,
                                           verbose=args.verbose, debug=args.debug,
                                           delay=args.delay)
        return 0 if nb > 0 else 1
    
    # Question unique
    print(f'Question: "{question}"')
    print()
    
    resultat = detecter_tout_brut(question, references, model=moteur,
                                   actifs=actifs, verbose=args.verbose, debug=args.debug)
    
    # Affichage du résumé
    print()
    print("═" * 70)
    print("RÉSUMÉ")
    print("═" * 70)
    print(f"Auteur      : {resultat['auteur']}")
    print(f"Mode        : {resultat['listcount']}")
    print(f"Nb critères : {len(resultat['criteres'])}")
    print(f"Latence     : {resultat.get('ia_latency_ms', 0):.1f}ms")
    
    for i, c in enumerate(resultat['criteres'], 1):
        label = c.get('label', c.get('canonique', '?'))
        cat = c.get('cat', '')
        adjs = c.get('adjectifs', [])
        adjs_str = f" [{', '.join(a.get('canonique', '') if isinstance(a, dict) else str(a) for a in adjs)}]" if adjs else ""
        cat_str = f" ({cat})" if cat else ""
        print(f"  {i}. [{c.get('type', '?')}] {label}{cat_str}{adjs_str}")
    
    print(f"\nRésidu: '{resultat['residu']}'")
    
    if 'ia_erreur' in resultat:
        print(f"\n⚠ Erreur: {resultat['ia_erreur']}")
    
    # Affichage JSON
    print()
    print("═" * 70)
    print("RÉSULTAT (JSON)")
    print("═" * 70)
    print(json.dumps(resultat, indent=2, ensure_ascii=False))
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
