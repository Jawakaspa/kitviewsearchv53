# detia.py V1.0.30 - 28/01/2026 14:55:26
__pgm__ = "detia.py"
__version__ = "1.0.30"
__date__ = "28/01/2026 14:55:26"

"""
Module de détection des critères orthodontiques par Intelligence Artificielle.

CHANGEMENTS V1.0.30 (28/01/2026) :
- FIX CRITIQUE : Intégration de detmeme.py en PRÉ-TRAITEMENT
  * Avant : Les critères "même X" n'étaient pas détectés en mode IA
  * Après : detmeme.py est appelé AVANT l'envoi à l'IA
  * Pipeline : detmeme → IA → mapping → motsvides
- La référence patient est propagée dans le JSON de sortie
- Alignement avec le pipeline de detall.py

ARCHITECTURE V4 - NOUVELLE STRUCTURE :
- Charge directement tags.csv (colonnes: t;gn;as;pts)
- Charge directement adjectifs.csv (colonnes: a;f;mp;fp;pas)
- Génère en mémoire les structures de recherche (plus de syntags/synadjs.csv)
- Les patterns (pts/pas) sont des synonymes unidirectionnels

V1.0.26 - AMÉLIORATIONS :
- Ajout des synonymes importants dans le prompt IA (tong e, rétrusion, spacing, etc.)
- Ajout des angles SNA et SNB (pas seulement ANB) dans le prompt
- Meilleure détection des angles céphalométriques

FICHIERS UTILISÉS :
- tags.csv       : Tags avec patterns (t;gn;as;pts;cat) - V2 avec catégories
- adjectifs.csv  : Adjectifs avec patterns (a;f;mp;fp;pas)
- ages.csv       : Patterns âge/sexe
- angles.csv     : Seuils angles céphalométriques
- ia.csv         : Configuration des moteurs IA
- commun.csv     : Langues actives
- communb.csv    : Synonymes pour detmeme (format vertical)

Usage CLI :
    python detia.py "bruxisme sévère"
    python detia.py "bruxisme" gpt51mini
    python detia.py "bruxisme" gpt4o
    python detia.py "même portrait que Guillaume Moulin" gpt4o
    python detia.py tests.csv gpt51mini
    python detia.py -l
"""

import os
import sys
import json
import csv
import re
import io
import time
import argparse
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Import de standardise
try:
    from standardise import standardise
except ImportError:
    import unicodedata
    def standardise(texte):
        if texte is None or texte == "":
            return ""
        texte = texte.lower()
        texte = unicodedata.normalize('NFD', texte)
        texte = ''.join(char for char in texte if unicodedata.category(char) != 'Mn')
        for char in ".!-_?":
            texte = texte.replace(char, " ")
        texte = re.sub(r'\s+', ' ', texte)
        return texte.strip()

# Import de motsvides
try:
    from motsvides import supprimer_motsvides
    MOTSVIDES_DISPONIBLE = True
except ImportError:
    MOTSVIDES_DISPONIBLE = False
    def supprimer_motsvides(texte, **kw): 
        return {'residu': texte, 'mots_supprimes': []}

# ═══════════════════════════════════════════════════════════════════════════
# NOUVEAU V1.0.30 : Import de detmeme pour pré-traitement des similarités
# ═══════════════════════════════════════════════════════════════════════════
try:
    from detmeme import charger_patterns_meme, detecter_meme
    DETMEME_DISPONIBLE = True
except ImportError:
    DETMEME_DISPONIBLE = False
    def charger_patterns_meme(*args, **kwargs): 
        return {'synonymes_meme': [], 'synonymes_que': [], 'cibles': {}}
    def detecter_meme(q, p, **kw): 
        return {'criteres': [], 'reference': None, 'residu': q}

# Configuration
DEFAULT_MODEL = "gpt41mini"
DEFAULT_LANGUE = "fr"
EDEN_AI_URL = "https://api.edenai.run/v2/text/chat"
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

_LANGUES_CACHE = None
_MODELES_IA_CACHE = None
_PATTERNS_MEME_CACHE = None  # NOUVEAU V1.0.30

MODEL_SIMPLE_NAMES = {
    "gpt-4o": "gpt-4o",
    "gpt-4o-mini": "gpt-4o-mini",
    "anthropic/claude-3-7-sonnet-20250219": "claude-sonnet-3.7",
}

SUPPORTED_MODELS = {
    "anthropic/claude-3-7-sonnet-20250219": "anthropic/claude-3-7-sonnet-20250219",
    "claude-sonnet": "anthropic/claude-3-7-sonnet-20250219",
    "gpt-4o": "openai/gpt-4o",
    "gpt-4o-mini": "openai/gpt-4o-mini",
}


def charger_langues_actives(refs_dir: Path = None) -> List[str]:
    global _LANGUES_CACHE
    if _LANGUES_CACHE is not None:
        return _LANGUES_CACHE
    
    if refs_dir is None:
        script_dir = Path(__file__).parent
        refs_local = script_dir / "refs"
        refs_alt = Path("c:/g/refs")
        refs_dir = refs_local if refs_local.exists() else refs_alt
    
    commun_path = refs_dir / "commun.csv"
    langues = []
    
    if commun_path.exists():
        try:
            with open(commun_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(
                    (line for line in f if line.strip() and not line.strip().startswith('#')),
                    delimiter=';'
                )
                for row in reader:
                    langue = (row.get('langues') or '').strip().lower()
                    if langue and langue not in langues:
                        langues.append(langue)
        except Exception:
            pass
    
    _LANGUES_CACHE = langues if langues else ['fr', 'en', 'ja']
    return _LANGUES_CACHE


def charger_modeles_ia(refs_dir: Path = None, verbose: bool = False, debug: bool = False) -> dict:
    if refs_dir is None:
        refs_dir = Path(__file__).parent / "refs"
    
    ia_path = refs_dir / "ia.csv"
    
    default_config = {
        'gpt41mini': {'via': 'openai', 'complet': 'gpt-4.1-mini', 'actif': True},
        'gpt4o': {'via': 'openai', 'complet': 'gpt-4o', 'actif': True},
        'sonnet': {'via': 'eden', 'complet': 'anthropic/claude-3-7-sonnet-20250219', 'actif': True},
    }
    
    if not ia_path.exists():
        return default_config
    
    modeles = {}
    try:
        with open(ia_path, 'r', encoding='utf-8-sig') as f:
            lignes = [line for line in f if not line.strip().startswith('#')]
        
        if lignes:
            reader = csv.DictReader(io.StringIO(''.join(lignes)), delimiter=';')
            for row in reader:
                moteur = row.get('moteur', row.get('court', '')).strip().lower()
                if moteur:
                    modeles[moteur] = {
                        'via': row.get('via', '').strip().lower(),
                        'complet': row.get('complet', '').strip(),
                        'actif': row.get('actif', 'O').strip().upper() == 'O',
                        'cout': row.get('cout', '').strip(),
                        'notes': row.get('notes', '').strip()
                    }
    except Exception:
        pass
    
    return modeles if modeles else default_config


def get_modeles_ia() -> dict:
    global _MODELES_IA_CACHE
    if _MODELES_IA_CACHE is None:
        _MODELES_IA_CACHE = charger_modeles_ia()
    return _MODELES_IA_CACHE


# ═══════════════════════════════════════════════════════════════════════════
# NOUVEAU V1.0.30 : Chargement des patterns pour detmeme
# ═══════════════════════════════════════════════════════════════════════════

def get_patterns_meme(refs_dir: Path = None, verbose: bool = False, debug: bool = False) -> dict:
    """Charge les patterns pour detmeme (avec cache)."""
    global _PATTERNS_MEME_CACHE
    
    if _PATTERNS_MEME_CACHE is not None:
        return _PATTERNS_MEME_CACHE
    
    if not DETMEME_DISPONIBLE:
        _PATTERNS_MEME_CACHE = {'synonymes_meme': [], 'synonymes_que': [], 'cibles': {}}
        return _PATTERNS_MEME_CACHE
    
    if refs_dir is None:
        script_dir = Path(__file__).parent
        refs_local = script_dir / "refs"
        refs_alt = Path("c:/g/refs")
        refs_dir = refs_local if refs_local.exists() else refs_alt
    
    # Chercher communb.csv puis commun.csv
    communb_path = refs_dir / "communb.csv"
    commun_path = refs_dir / "commun.csv"
    config_path = str(communb_path) if communb_path.exists() else str(commun_path) if commun_path.exists() else None
    
    _PATTERNS_MEME_CACHE = charger_patterns_meme(config_path, verbose=verbose, debug=debug)
    
    if verbose:
        nb_syn = len(_PATTERNS_MEME_CACHE.get('synonymes_meme', []))
        print(f"  detmeme: {nb_syn} synonymes 'même' chargés")
    
    return _PATTERNS_MEME_CACHE


def _get_model_config(model_name: str) -> dict:
    modeles = get_modeles_ia()
    if model_name.lower() in modeles:
        config = modeles[model_name.lower()]
        return {'via': config['via'], 'model': config['complet']}
    if model_name.startswith('gpt-'):
        return {'via': 'openai', 'model': model_name}
    if '/' in model_name:
        return {'via': 'eden', 'model': model_name}
    return {'via': 'eden', 'model': 'anthropic/claude-3-7-sonnet-20250219'}


def _construire_auteur(model: str, via: str) -> str:
    simple_name = MODEL_SIMPLE_NAMES.get(model, model.split('/')[-1] if '/' in model else model)
    return f"{via}/{simple_name}"


def _charger_tags_csv(chemin: Path, verbose: bool = False, debug: bool = False) -> Tuple[List[str], Dict[str, str], Dict[str, str], Dict[str, str]]:
    """Charge tags.csv (t;gn;as;pts[;cat]) et génère liste + mapping + synonymes + catégories.
    
    Returns:
        (liste_stdtag, mapping, synonymes_importants, categories)
        - synonymes_importants: dict {pattern_original: tag_canonique} pour le prompt IA
        - categories: dict {canon_std: cat} pour enrichir le prompt (V2)
    """
    liste_stdtag = []
    mapping = {}
    synonymes_importants = {}
    categories = {}
    
    if not chemin.exists():
        return liste_stdtag, mapping, synonymes_importants, categories
    
    for encodage in ["utf-8-sig", "utf-8", "windows-1252"]:
        try:
            with open(chemin, 'r', encoding=encodage, newline='') as f:
                lignes = [line for line in f if line.strip() and not line.strip().startswith('#')]
            
            reader = csv.DictReader(io.StringIO(''.join(lignes)), delimiter=';')
            vus = set()
            
            for row in reader:
                canon = (row.get('t') or '').strip()
                if not canon:
                    continue
                
                canon_std = standardise(canon)
                cat = (row.get('cat') or '').strip().lower()  # V2 : catégorie (optionnel)
                
                if canon_std not in vus:
                    vus.add(canon_std)
                    liste_stdtag.append(canon_std)
                    mapping[canon_std] = canon
                    if cat:
                        categories[canon_std] = cat
                
                pts_raw = row.get('pts', '')
                if pts_raw:
                    for pattern in pts_raw.split(','):
                        pattern = pattern.strip()
                        if pattern:
                            pattern_std = standardise(pattern)
                            if pattern_std and pattern_std not in mapping:
                                mapping[pattern_std] = canon
                                synonymes_importants[pattern_std] = canon_std
            
            if verbose:
                if categories:
                    cats_count = {}
                    for c in categories.values():
                        cats_count[c] = cats_count.get(c, 0) + 1
                    cats_str = ', '.join(f"{c}={n}" for c, n in sorted(cats_count.items()))
                    print(f"  tags.csv: {len(liste_stdtag)} tags, {len(synonymes_importants)} synonymes, catégories: {cats_str}")
                else:
                    print(f"  tags.csv: {len(liste_stdtag)} tags, {len(synonymes_importants)} synonymes")
            
            return liste_stdtag, mapping, synonymes_importants, categories
            
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    return liste_stdtag, mapping, synonymes_importants, categories


def _charger_adjectifs_csv(chemin: Path, verbose: bool = False, debug: bool = False) -> Tuple[List[str], Dict[str, str]]:
    """Charge adjectifs.csv (a;f;mp;fp;pas) et génère liste + mapping."""
    liste_stdadj = []
    mapping = {}
    
    if not chemin.exists():
        return liste_stdadj, mapping
    
    for encodage in ["utf-8-sig", "utf-8", "windows-1252"]:
        try:
            with open(chemin, 'r', encoding=encodage, newline='') as f:
                lignes = [line for line in f if line.strip() and not line.strip().startswith('#')]
            
            reader = csv.DictReader(io.StringIO(''.join(lignes)), delimiter=';')
            vus = set()
            
            for row in reader:
                canon = (row.get('a') or '').strip()
                if not canon:
                    continue
                
                canon_std = standardise(canon)
                
                if canon_std not in vus:
                    vus.add(canon_std)
                    liste_stdadj.append(canon_std)
                    mapping[canon_std] = canon
                
                for col in ['f', 'mp', 'fp']:
                    forme = (row.get(col) or '').strip()
                    if forme:
                        forme_std = standardise(forme)
                        if forme_std and forme_std not in mapping:
                            mapping[forme_std] = canon
                
                pas_raw = row.get('pas', '')
                if pas_raw:
                    for pattern in pas_raw.split(','):
                        pattern = pattern.strip()
                        if pattern:
                            pattern_std = standardise(pattern)
                            if pattern_std and pattern_std not in mapping:
                                mapping[pattern_std] = canon
            
            if verbose:
                print(f"  adjectifs.csv: {len(liste_stdadj)} adjectifs")
            
            return liste_stdadj, mapping
            
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    return liste_stdadj, mapping


def charger_references(langue: str = DEFAULT_LANGUE, verbose: bool = False, debug: bool = False) -> dict:
    """Charge toutes les références nécessaires depuis les fichiers CSV."""
    script_dir = Path(__file__).parent
    refs_local = script_dir / "refs"
    refs_alt = Path("c:/g/refs")
    refs_dir = refs_local if refs_local.exists() else refs_alt
    
    if verbose:
        print(f"Chargement depuis: {refs_dir}")
    
    tags_path = refs_dir / "tags.csv"
    adjs_path = refs_dir / "adjectifs.csv"
    
    liste_tags, tags_map, synonymes_tags, categories_tags = _charger_tags_csv(tags_path, verbose, debug)
    liste_adjs, adjs_map = _charger_adjectifs_csv(adjs_path, verbose, debug)
    
    # NOUVEAU V1.0.30 : Charger les patterns pour detmeme
    patterns_meme = get_patterns_meme(refs_dir, verbose, debug)
    
    return {
        'langue': langue,
        'liste_tags': liste_tags,
        'tags_map': tags_map,
        'synonymes_tags': synonymes_tags,
        'categories_tags': categories_tags,  # V2 : catégories des tags
        'liste_adjs': liste_adjs,
        'adjs_map': adjs_map,
        'patterns_meme': patterns_meme  # NOUVEAU V1.0.30
    }


def _construire_prompt_systeme(references: dict) -> str:
    """Construit le prompt système pour l'IA."""
    # V2 : enrichir les tags avec leur catégorie si disponible
    categories = references.get('categories_tags', {})
    if categories:
        tags_liste = '\n'.join(
            f"- {t} ({categories[t]})" if t in categories else f"- {t}"
            for t in references.get('liste_tags', [])[:100]
        )
    else:
        tags_liste = '\n'.join(f"- {t}" for t in references.get('liste_tags', [])[:100])
    adjs_liste = '\n'.join(f"- {a}" for a in references.get('liste_adjs', [])[:50])
    
    synonymes = references.get('synonymes_tags', {})
    tags_map = references.get('tags_map', {})
    
    synonymes_filtres = []
    
    synonymes_prioritaires = [
        ('tongue thrust', 'interposition linguale'),
        ('tong e', 'interposition linguale'),
        ('tongue', 'interposition linguale'),
        ('retrusion', 'retroalveolie'),
        ('spacing', 'diasteme'),
        ('open bite', 'beance'),
        ('openbite', 'beance'),
        ('deep bite', 'supraclusion'),
        ('overbite', 'supraclusion'),
        ('cross bite', 'occlusion croisee'),
        ('crossbite', 'occlusion croisee'),
        ('underbite', 'prognathisme mandibulaire'),
        ('overjet', 'surplomb'),
        ('protrusion', 'proalveolie'),
        ('crowding', 'encombrement'),
        ('impaction', 'inclusion'),
        ('impacted', 'inclusion'),
        ('thumb sucking', 'succion du pouce'),
        ('bruxism', 'bruxisme'),
        ('grinding', 'bruxisme'),
        ('teeth grinding', 'bruxisme'),
        ('apnea', 'apnee'),
        ('sleep apnea', 'apnee du sommeil'),
        ('snoring', 'ronflement'),
        ('tmj', 'atm'),
        ('temporomandibular', 'atm'),
        ('jaw pain', 'douleur atm'),
        ('clicking', 'claquement atm'),
        ('malocclusion', 'malocclusion'),
        ('fil', 'arc'),
        ('grincement', 'bruxisme'),
        ('grince des dents', 'bruxisme'),
        ('prognathisme mandibulaire', 'classe iii d\'angle'),
        ('mandibule en avant', 'classe iii d\'angle'),
        ('extraction', 'avulsion'),
        ('extraction dentaire', 'avulsion'),
    ]
    
    for pattern, canon in synonymes_prioritaires:
        if pattern in synonymes or any(pattern in k for k in synonymes.keys()):
            synonymes_filtres.append(f"  {pattern} → {canon}")
    
    count = 0
    for pattern, canon in sorted(synonymes.items()):
        if count >= 50:
            break
        if pattern != canon and len(pattern) > 3 and len(pattern) <= 25:
            ligne = f"  {pattern} → {canon}"
            if ligne not in synonymes_filtres:
                synonymes_filtres.append(ligne)
                count += 1
    
    synonymes_str = '\n'.join(synonymes_filtres[:60]) if synonymes_filtres else "(aucun synonyme chargé)"
    
    return f"""Tu es un analyseur de requêtes orthodontiques. Tu dois IDENTIFIER les termes présents dans la question.

=== MISSION ===
1. Détecter les TAGS (pathologies) de la liste ci-dessous
2. Détecter les ADJECTIFS qualifiant ces tags
3. Détecter les critères d'ÂGE et de SEXE
4. Détecter les demandes de COMPTAGE (combien, nombre de)
5. Détecter les ANGLES céphalométriques (ANB, SNA, SNB)

=== TAGS PATHOLOGIQUES ===
{tags_liste}

=== SYNONYMES IMPORTANTS ===
Quand tu détectes ces termes, utilise le tag canonique correspondant :
{synonymes_str}

=== ADJECTIFS ===
{adjs_liste}

=== ANGLES CÉPHALOMÉTRIQUES ===
IMPORTANT: Convertis les valeurs d'angles en tags pathologiques.

| Angle | Condition | Valeur | Tag résultant |
|-------|-----------|--------|---------------|
| ANB   | =         | 0 à 4  | classe i squelettique |
| ANB   | >         | 4      | classe ii squelettique |
| ANB   | <         | 0      | classe iii squelettique |
| SNA   | =         | 79-85  | position maxillaire normale |
| SNA   | >         | 85     | prognathisme maxillaire |
| SNA   | <         | 79     | rétrognathisme maxillaire |
| SNB   | =         | 77-83  | position mandibulaire normale |
| SNB   | >         | 83     | prognathisme mandibulaire |
| SNB   | <         | 77     | rétrognathisme mandibulaire |

Exemples:
- "SNA = 84" → position maxillaire normale
- "SNA > 85" ou "SNA supérieur à 85" → prognathisme maxillaire
- "SNB de 81" → position mandibulaire normale (car 77 <= 81 <= 83)
- "SNB < 77" ou "SNB moins de 77" → rétrognathisme mandibulaire

=== CRITÈRES D'ÂGE ET SEXE ===
IMPORTANT - Règles pour l'âge :
- "{{n}} ans", "de {{n}} ans", "âgé de {{n}} ans" → âge EXACT, operateur "="
- "moins de {{n}} ans", "de moins de {{n}} ans", "inférieur à {{n}} ans" → operateur "<"
- "plus de {{n}} ans", "de plus de {{n}} ans", "supérieur à {{n}} ans" → operateur ">"
- "entre {{n}} et {{n}} ans", "compris entre {{n}} et {{n}}" → operateur "BETWEEN" avec valeur et valeur2

ATTENTION - RÈGLE CRITIQUE :
Quand la question contient DEUX conditions d'âge SÉPARÉES reliées par "et", tu DOIS retourner DEUX critères d'âge distincts, JAMAIS un BETWEEN.
- "supérieur à 17 et inférieur à 23" → DEUX critères : {{"operateur": ">", "valeur": 17}} ET {{"operateur": "<", "valeur": 23}}
- "plus de 20 ans et moins de 23 ans" → DEUX critères : {{"operateur": ">", "valeur": 20}} ET {{"operateur": "<", "valeur": 23}}
- "entre 13 et 16" → UN critère BETWEEN (formulation explicite "entre...et...")
Le BETWEEN est réservé UNIQUEMENT aux formulations "entre X et Y" ou "compris entre X et Y".

Exemples :
- "14 ans" ou "de 14 ans" → {{"type": "age", "detecte": "14 ans", "operateur": "=", "valeur": 14}}
- "moins de 30 ans" → {{"type": "age", "detecte": "moins de 30 ans", "operateur": "<", "valeur": 30}}
- "plus de 18 ans" → {{"type": "age", "detecte": "plus de 18 ans", "operateur": ">", "valeur": 18}}
- "supérieur à 17 ans" → {{"type": "age", "detecte": "supérieur à 17 ans", "operateur": ">", "valeur": 17}}
- "inférieur à 23 ans" → {{"type": "age", "detecte": "inférieur à 23 ans", "operateur": "<", "valeur": 23}}
- "entre 10 et 15 ans" → {{"type": "age", "detecte": "entre 10 et 15 ans", "operateur": "BETWEEN", "valeur": 10, "valeur2": 15}}
- "supérieur à 17 et inférieur à 23" → DEUX critères age séparés (> 17) et (< 23), PAS un BETWEEN
- "enfants" → operateur "<", valeur 12
- "adolescents" → operateur "BETWEEN", valeur 12, valeur2 18
- "adultes" → operateur ">=", valeur 18

Sexe :
- femme/fille/femmes/patiente/patientes → "F"
- homme/garçon/hommes/patient/patients → "M"

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

RÈGLES IMPORTANTES:
- Retourne UNIQUEMENT du JSON valide.
- Pour les angles, génère un critère de type "tag" avec le tag résultant.
- Utilise les synonymes pour mapper vers les tags canoniques.
- CLASSE 2 : "classe 2" seul = classification d'ANGLE (rapport molaire dentaire).
  "classe 2 squelettique" = classification de Ballard (rapport osseux, ANB).
  JAMAIS utiliser "classe ii squelettique" sauf si "squelettique" est ÉCRIT dans la question
  ou si c'est un critère d'angle céphalométrique (ANB > 4)."""


def _construire_prompt_utilisateur(question: str) -> str:
    return f'Analyse cette question et retourne le JSON: "{question}"'


def _mapper_vers_canonique(resultat_ia: dict, references: dict, debug: bool = False) -> list:
    tags_map = references.get('tags_map', {})
    adjs_map = references.get('adjs_map', {})
    categories = references.get('categories_tags', {})  # V2
    criteres_enrichis = []
    
    for critere in resultat_ia.get('criteres', []):
        c_type = critere.get('type', '')
        
        if c_type == 'tag':
            detecte = critere.get('detecte', '').lower().strip()
            canontag = tags_map.get(detecte, detecte.title())
            canon_std = standardise(canontag) if canontag else detecte
            cat = categories.get(canon_std, '')  # V2 : catégorie
            
            adjectifs_enrichis = []
            for adj in critere.get('adjectifs', []):
                adj_lower = adj.lower().strip() if isinstance(adj, str) else ''
                canonadj = adjs_map.get(adj_lower, adj_lower)
                adjectifs_enrichis.append({
                    'detecte': adj, 'canonique': canonadj,
                    'sql': {'colonne': 'canonadjs', 'operateur': '=', 'valeur': canonadj}
                })
            
            criteres_enrichis.append({
                'type': 'tag', 'detecte': detecte, 'canonique': canontag, 'label': canontag,
                'cat': cat,  # V2
                'adjectifs': adjectifs_enrichis,
                'sql': {'colonne': 'canontags', 'operateur': '=', 'valeur': canontag}
            })
        
        elif c_type == 'angle':
            tag_resultat = critere.get('tag_resultat', '')
            canontag = tags_map.get(tag_resultat.lower(), tag_resultat.title())
            canon_std = standardise(canontag) if canontag else ''
            cat = categories.get(canon_std, '')  # V2
            criteres_enrichis.append({
                'type': 'tag', 'detecte': critere.get('detecte', ''), 'canonique': canontag,
                'label': canontag, 'cat': cat, 'adjectifs': [], 'source': 'angle',
                'sql': {'colonne': 'canontags', 'operateur': '=', 'valeur': canontag}
            })
        
        elif c_type == 'age':
            operateur = critere.get('operateur', '<')
            valeur = critere.get('valeur', 0)
            
            if operateur == 'BETWEEN':
                valeur2 = critere.get('valeur2', valeur)
                criteres_enrichis.append({
                    'type': 'age', 'detecte': critere.get('detecte', ''),
                    'label': f"entre {valeur} et {valeur2} ans",
                    'sql': {'colonne': 'age', 'operateur': 'BETWEEN', 'valeur': [valeur, valeur2]}
                })
            else:
                criteres_enrichis.append({
                    'type': 'age', 'detecte': critere.get('detecte', ''),
                    'label': f"Âge {operateur} {valeur}",
                    'sql': {'colonne': 'age', 'operateur': operateur, 'valeur': valeur}
                })
        
        elif c_type == 'sexe':
            valeur = critere.get('valeur', '').upper()
            criteres_enrichis.append({
                'type': 'sexe', 'detecte': critere.get('detecte', ''),
                'label': 'Masculin' if valeur == 'M' else 'Féminin',
                'sql': {'colonne': 'sexe', 'operateur': '=', 'valeur': valeur}
            })
        
        elif c_type == 'count':
            criteres_enrichis.append({'type': 'count', 'detecte': critere.get('detecte', ''), 'label': 'Comptage demandé'})
        else:
            criteres_enrichis.append(critere)
    
    return criteres_enrichis


def _appeler_openai_direct(prompt_systeme: str, prompt_utilisateur: str, model: str, debug: bool = False, max_retries: int = 5) -> Tuple[dict, float]:
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("Clé API OpenAI non trouvée. Configurez OPENAI_API_KEY")
    
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": prompt_systeme}, {"role": "user", "content": prompt_utilisateur}],
        "temperature": 0.1, "max_tokens": 2000
    }
    
    start_time = time.time()
    last_error = None
    
    for attempt in range(max_retries):
        try:
            response = requests.post(OPENAI_API_URL, headers=headers, json=payload, timeout=60)
            latency_ms = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                generated_text = data['choices'][0]['message']['content'].strip()
                
                if debug:
                    print(f"\n[DEBUG] Réponse brute: {generated_text[:500]}")
                
                if generated_text.startswith('```json'):
                    generated_text = generated_text[7:]
                if generated_text.startswith('```'):
                    generated_text = generated_text[3:]
                if generated_text.endswith('```'):
                    generated_text = generated_text[:-3]
                
                try:
                    return json.loads(generated_text.strip()), latency_ms
                except json.JSONDecodeError as e:
                    return {"langue": "fr", "listcount": "LIST", "criteres": [], "residu": "", "erreur_parsing": str(e)}, latency_ms
            
            elif response.status_code == 429:
                wait_time = 2 ** attempt
                if debug:
                    print(f"[DEBUG] Rate limit, attente {wait_time}s")
                time.sleep(wait_time)
                last_error = "Rate limit"
                continue
            
            elif response.status_code >= 500:
                wait_time = 2 ** attempt
                if debug:
                    print(f"[DEBUG] Erreur serveur {response.status_code}, attente {wait_time}s")
                time.sleep(wait_time)
                last_error = f"Erreur serveur {response.status_code}"
                continue
            
            else:
                return {"langue": "fr", "listcount": "LIST", "criteres": [], "residu": "", 
                        "erreur": f"API {response.status_code}"}, latency_ms
        
        except requests.exceptions.RequestException as e:
            last_error = str(e)
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            return {"langue": "fr", "listcount": "LIST", "criteres": [], "residu": "", "erreur": str(e)}, (time.time() - start_time) * 1000
    
    return {"langue": "fr", "listcount": "LIST", "criteres": [], "residu": "", 
            "erreur": f"Échec après {max_retries} tentatives: {last_error}"}, (time.time() - start_time) * 1000


def _appeler_eden_ai(prompt_systeme: str, prompt_utilisateur: str, model: str, debug: bool = False) -> Tuple[dict, float]:
    api_key = os.environ.get('EDENAI_API_KEY')
    if not api_key:
        raise ValueError("Clé API Eden AI non trouvée. Configurez EDENAI_API_KEY")
    
    model_id = SUPPORTED_MODELS.get(model, model)
    provider = model_id.split('/')[0] if '/' in model_id else model_id
    model_name = model_id.split('/', 1)[1] if '/' in model_id else model_id
    
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    payload = {
        "providers": provider, "text": prompt_utilisateur, "chatbot_global_action": prompt_systeme,
        "previous_history": [], "temperature": 0.1, "max_tokens": 2000, "settings": {provider: model_name}
    }
    
    start_time = time.time()
    try:
        response = requests.post(EDEN_AI_URL, headers=headers, json=payload, timeout=60)
        latency_ms = (time.time() - start_time) * 1000
        
        if response.status_code != 200:
            raise ValueError(f"Erreur API: {response.status_code}")
        
        data = response.json()
        generated_text = data.get(provider, {}).get('generated_text', '')
        if not generated_text:
            for key in data:
                if isinstance(data[key], dict) and 'generated_text' in data[key]:
                    generated_text = data[key]['generated_text']
                    break
        
        generated_text = generated_text.strip()
        if generated_text.startswith('```json'):
            generated_text = generated_text[7:]
        if generated_text.startswith('```'):
            generated_text = generated_text[3:]
        if generated_text.endswith('```'):
            generated_text = generated_text[:-3]
        
        try:
            return json.loads(generated_text.strip()), latency_ms
        except json.JSONDecodeError as e:
            return {"langue": "fr", "listcount": "LIST", "criteres": [], "residu": "", "erreur_parsing": str(e)}, latency_ms
    
    except requests.exceptions.RequestException as e:
        return {"langue": "fr", "listcount": "LIST", "criteres": [], "residu": "", "erreur": str(e)}, (time.time() - start_time) * 1000


def detecter_tout(question: str, references: dict, model: str = DEFAULT_MODEL, verbose: bool = False, debug: bool = False) -> dict:
    """
    Analyse une question via IA et retourne les critères détectés.
    
    NOUVEAU V1.0.30 : Pré-traitement par detmeme.py pour les critères "même X"
    Pipeline : detmeme → IA → mapping → motsvides
    """
    question_originale = question
    question_std = standardise(question)
    
    model_config = _get_model_config(model)
    via = model_config['via']
    model_id = model_config['model']
    
    # ═══════════════════════════════════════════════════════════════════════════
    # NOUVEAU V1.0.30 : PRÉ-TRAITEMENT PAR DETMEME
    # ═══════════════════════════════════════════════════════════════════════════
    criteres_meme = []
    reference_meme = None
    question_pour_ia = question  # Question à envoyer à l'IA (après extraction des "même")
    
    if DETMEME_DISPONIBLE:
        patterns_meme = references.get('patterns_meme', get_patterns_meme())
        
        if patterns_meme and patterns_meme.get('synonymes_meme'):
            if verbose:
                print(f"  → Pré-traitement detmeme...", end=" ", flush=True)
            
            resultat_meme = detecter_meme(
                question,
                patterns_meme,
                verbose=False,
                debug=debug
            )
            
            criteres_meme = resultat_meme.get('criteres', [])
            reference_meme = resultat_meme.get('reference')
            question_pour_ia = resultat_meme.get('residu', question)
            
            if verbose:
                if criteres_meme:
                    print(f"{len(criteres_meme)} critère(s) 'même' détecté(s)")
                else:
                    print(f"aucun critère 'même'")
            
            if debug and criteres_meme:
                print(f"[DEBUG] detia: Critères 'même' détectés: {criteres_meme}")
                print(f"[DEBUG] detia: Référence: {reference_meme}")
                print(f"[DEBUG] detia: Question résiduelle pour IA: '{question_pour_ia}'")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # APPEL À L'IA (sur la question résiduelle)
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Si la question résiduelle est vide ou très courte après detmeme, pas besoin d'appeler l'IA
    question_pour_ia_clean = question_pour_ia.strip()
    
    if len(question_pour_ia_clean) < 3 and criteres_meme:
        # Tout a été consommé par detmeme, pas besoin d'appeler l'IA
        if verbose:
            print(f"  → Question consommée par detmeme, pas d'appel IA")
        
        resultat_ia = {"langue": "fr", "listcount": "LIST", "criteres": [], "residu": ""}
        latency_ms = 0
        criteres_ia = []
    else:
        # Appeler l'IA sur la question résiduelle
        prompt_systeme = _construire_prompt_systeme(references)
        prompt_utilisateur = _construire_prompt_utilisateur(question_pour_ia)
        
        if verbose:
            print(f"  → Appel {'OpenAI' if via == 'openai' else 'Eden AI'} ({model_id})...", end=" ", flush=True)
        
        if via == 'openai':
            resultat_ia, latency_ms = _appeler_openai_direct(prompt_systeme, prompt_utilisateur, model_id, debug)
        else:
            resultat_ia, latency_ms = _appeler_eden_ai(prompt_systeme, prompt_utilisateur, model_id, debug)
        
        if verbose:
            print(f"OK ({latency_ms:.0f}ms)")
        
        criteres_ia = _mapper_vers_canonique(resultat_ia, references, debug)
    
    # ═══════════════════════════════════════════════════════════════════════════
    # FUSION DES CRITÈRES : meme + IA
    # ═══════════════════════════════════════════════════════════════════════════
    
    # Les critères "même" viennent en premier (comme dans detall.py)
    criteres_fusionnes = criteres_meme + criteres_ia
    
    listcount = resultat_ia.get("listcount", "LIST")
    if listcount == "COUNT" and not any(c.get("type") == "count" for c in criteres_fusionnes):
        criteres_fusionnes.insert(0, {"type": "count", "detecte": "combien", "label": "Comptage demandé"})
    
    # ═══════════════════════════════════════════════════════════════════════════
    # CONSTRUCTION DU RÉSULTAT FINAL
    # ═══════════════════════════════════════════════════════════════════════════
    
    resultat = {
        "auteur": _construire_auteur(model_id, via),
        "langue": resultat_ia.get("langue", references.get('langue', 'fr')),
        "listcount": listcount,
        "criteres": criteres_fusionnes,
        "residu": resultat_ia.get("residu", ""),
        "question_originale": question_originale,
        "question_standardisee": question_std,
        "ia_moteur": model, 
        "ia_model": model_id, 
        "ia_via": via,
        "ia_latency_ms": round(latency_ms, 1)
    }
    
    # NOUVEAU V1.0.30 : Propager la référence pour les critères "même"
    if reference_meme:
        resultat["reference"] = reference_meme
    
    if "erreur" in resultat_ia:
        resultat["ia_erreur"] = resultat_ia["erreur"]
    if "erreur_parsing" in resultat_ia:
        resultat["ia_erreur_parsing"] = resultat_ia["erreur_parsing"]
    
    # Nettoyage du résidu par motsvides
    if MOTSVIDES_DISPONIBLE and resultat["residu"]:
        res_mv = supprimer_motsvides(resultat["residu"], verbose=False, debug=debug)
        resultat["residu"] = res_mv.get('residu', resultat["residu"])
    
    return resultat


def traiter_fichier_batch(fichier_entree: str, references: dict, model: str = DEFAULT_MODEL, 
                          verbose: bool = False, debug: bool = False, delay: float = 0) -> Tuple[int, Optional[Path]]:
    """
    Traite un fichier batch.
    
    Args:
        delay: Délai en secondes entre chaque requête (0 = pas de délai)
    """
    chemin_entree = Path(fichier_entree)
    nom_base = chemin_entree.stem
    module_name = Path(__pgm__).stem  # 'detia'
    fichier_sortie = chemin_entree.parent / f"{nom_base}{module_name}.csv"
    
    print(f"Fichier d'entrée : {os.path.abspath(fichier_entree)}")
    print(f"Fichier de sortie: {os.path.abspath(fichier_sortie)}")
    print(f"Modèle IA       : {model}")
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
        
        resultat = detecter_tout(question, references, model=model, verbose=False, debug=debug)
        latency = resultat.get('ia_latency_ms', 0)
        
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
        lignes_resume.append(f"{latency:.0f}ms")
        
        resultats.append({
            'question': question,
            'resultat': _val_resultat,
            'commentaire': _val_commentaire,
            'lignes': lignes_resume
        })
        total_latency += latency
        print(f"✓ {latency:.0f}ms")
        
        # Mini-résumé pour chaque question
        print(f"        \"{question}\"")
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
    
    with open(fichier_sortie, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow([f'# Généré par detia.py V{__version__} avec {model}'] + [''] * (len(entete_l) - 1))
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


def trouver_fichier_batch(nom_fichier: str) -> Optional[Path]:
    chemin = Path(nom_fichier)
    if chemin.exists():
        return chemin
    for rep in [Path('.'), Path('tests'), Path('c:/g/tests'), Path('c:/g')]:
        candidat = rep / Path(nom_fichier).name
        if candidat.exists():
            return candidat
    return None


def _identifier_argument(arg: str) -> str:
    arg_lower = arg.lower().strip()
    if arg_lower.endswith('.csv'):
        return 'fichier'
    if arg_lower in get_modeles_ia():
        return 'moteur'
    if arg_lower in charger_langues_actives():
        return 'langue'
    return 'question'


def main():
    print(f"╔════════════════════════════════════════════════════════════════")
    print(f"║ {__pgm__} V{__version__} - {__date__}")
    print(f"║ Détection par IA (V4 - tags.csv + adjectifs.csv)")
    print(f"║ V1.0.30 : Intégration detmeme (similarités)")
    print(f"╚════════════════════════════════════════════════════════════════")
    print()
    
    # Afficher les modules disponibles
    print("Modules:")
    print(f"  detmeme:   {'✓' if DETMEME_DISPONIBLE else '✗'} (V1.0.30)")
    print(f"  motsvides: {'✓' if MOTSVIDES_DISPONIBLE else '✗'}")
    print()
    
    parser = argparse.ArgumentParser(description="Détecte les critères orthodontiques via IA")
    parser.add_argument('args', nargs='*', help='Question/fichier, moteur et/ou langue')
    parser.add_argument('-v', '--verbose', action='store_true', help='Affichage modéré')
    parser.add_argument('-d', '--debug', action='store_true', help='Affichage complet')
    parser.add_argument('-l', '--list', action='store_true', help='Liste les moteurs')
    parser.add_argument('--delay', type=float, default=0, help='Délai en secondes entre requêtes (ex: --delay 2)')
    
    args = parser.parse_args()
    
    if args.list:
        print("Moteurs IA disponibles:")
        for moteur, config in sorted(get_modeles_ia().items()):
            if config.get('via'):
                status = "✓" if config.get('actif') else "✗"
                print(f"  {status} {moteur:15} via {config['via']}")
        print(f"\nLangues: {', '.join(charger_langues_actives())}")
        return 0
    
    question, moteur, langue = None, DEFAULT_MODEL, DEFAULT_LANGUE
    for arg in args.args:
        nature = _identifier_argument(arg)
        if nature == 'moteur':
            moteur = arg.lower()
        elif nature == 'langue':
            langue = arg.lower()
        elif question is None:
            question = arg
    
    if question is None:
        parser.print_help()
        return 1
    
    model_config = _get_model_config(moteur)
    via = model_config['via']
    if via == 'openai' and not os.environ.get('OPENAI_API_KEY'):
        print("[ERREUR] Variable OPENAI_API_KEY non définie")
        return 1
    if via == 'eden' and not os.environ.get('EDENAI_API_KEY'):
        print("[ERREUR] Variable EDENAI_API_KEY non définie")
        return 1
    
    print(f"Moteur : {moteur}")
    print(f"Langue : {langue}")
    print()
    print("Chargement des références (V4 + detmeme)...")
    references = charger_references(langue=langue, verbose=True, debug=args.debug)
    print()
    
    if question.lower().endswith('.csv'):
        fichier_batch = trouver_fichier_batch(question)
        if not fichier_batch:
            print(f"[ERREUR] Fichier non trouvé : {question}")
            return 1
        print(f"Mode BATCH - {fichier_batch.absolute()}")
        print("-" * 70)
        nb, _ = traiter_fichier_batch(str(fichier_batch), references, model=moteur, 
                                       verbose=args.verbose, debug=args.debug, delay=args.delay)
        return 0 if nb > 0 else 1
    
    print(f'Question: "{question}"')
    print()
    
    resultat = detecter_tout(question, references, model=moteur, verbose=args.verbose, debug=args.debug)
    
    print()
    print("═" * 70)
    print("RÉSUMÉ")
    print("═" * 70)
    print(f"Auteur      : {resultat['auteur']}")
    print(f"Mode        : {resultat['listcount']}")
    print(f"Nb critères : {len(resultat['criteres'])}")
    print(f"Latence IA  : {resultat.get('ia_latency_ms', 0)}ms")
    
    for i, c in enumerate(resultat['criteres'], 1):
        c_type = c.get('type', '?')
        if c_type == 'meme':
            cible = c.get('cible', '?')
            label = c.get('label', '?')
            print(f"  {i}. [meme] {label} (cible: {cible})")
        else:
            label = c.get('label', c.get('canonique', '?'))
            adjs = c.get('adjectifs', [])
            adjs_str = f" [{', '.join(a.get('canonique', '') if isinstance(a, dict) else str(a) for a in adjs)}]" if adjs else ""
            print(f"  {i}. [{c_type}] {label}{adjs_str}")
    
    # NOUVEAU V1.0.30 : Afficher la référence si présente
    if resultat.get('reference'):
        ref = resultat['reference']
        if ref.get('type') == 'id':
            print(f"\nRéférence   : ID {ref.get('id')}")
        else:
            print(f"\nRéférence   : {ref.get('valeur', '?')}")
    
    print(f"\nRésidu      : '{resultat['residu']}'")
    
    if 'ia_erreur' in resultat:
        print(f"\n⚠ Erreur: {resultat['ia_erreur']}")
    
    print()
    print("═" * 70)
    print("RÉSULTAT (JSON)")
    print("═" * 70)
    print(json.dumps(resultat, indent=2, ensure_ascii=False))
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
