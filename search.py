# search.py V1.0.29 - 28/01/2026 18:50:00
__pgm__ = "search.py"
__version__ = "1.0.29"
__date__ = "28/01/2026 18:50:00"

"""
Module de recherche multilingue utilisant trouve.py.

CHANGEMENTS V1.0.29 (28/01/2026) :
- FIX PAGINATION : Tous les appels à rechercher() passent maintenant limit et offset
- Permet la pagination côté serveur (LIMIT/OFFSET SQL)

CHANGEMENTS V1.0.28 (09/01/2026) :
- NOUVEAUX MODES : 'purstandard' et 'puria' sans fallback automatique
  * purstandard : detall.py uniquement, aucun fallback IA ni DeepL
  * puria : detia.py uniquement, aucun fallback DeepL
  * Utiles pour les tests CLI et le debug
- Ajout dans ia.csv pour sélection depuis l'interface web
- MODES_VALIDES étendu à ['standard', 'ia', 'purstandard', 'puria']

CHANGEMENTS V1.0.27 (08/01/2026) :
- RETOUR GLOSSAIRE PRIORITAIRE : Utilise traduire() au lieu de deepl_traduire()
  * traduire() passe par glossaire.csv en PRIORITÉ pour les termes médicaux
  * DeepL utilisé uniquement pour le résidu (mots non trouvés dans glossaire)
  * Corrige le bug "offener Biss" traduit en "occlusion ouverte" au lieu de "béance"
- modulelangue = 'glossaire' quand termes trouvés dans glossaire
- modulelangue = 'deepl' quand DeepL utilisé pour traduction
- modulelangue = 'glossaire+deepl' quand les deux sont utilisés

CHANGEMENTS V1.0.26 (07/01/2026) :
- FIX : Utilisation de deepl_traduire() DIRECTEMENT au lieu de traduire()
  * traduire() utilisait le glossaire en priorité, donnant des traductions partielles
  * deepl_traduire() traduit la question ENTIÈRE via DeepL
- Import ajouté : deepl_traduire depuis traduire.py
- modulelangue = 'deepl_direct' quand traduction complète réussie

CHANGEMENTS V1.0.25 (07/01/2026) :
- OPTION A : Traduction complète via DeepL pour langues non-FR
  * Remplace la résolution glossaire partielle par traduction DeepL complète
  * Les mots courants (di, ai, dei, etc.) sont maintenant traduits
- NOUVEAU CHAMP : 'question_technique_fr' = question envoyée à trouve.py
- AFFICHAGE CLI : Ajout ligne "Question tech FR" pour debug
- FIX : resolution_provider reflète maintenant le vrai fournisseur (traduire_deepl, traduire_glossaire)

CHANGEMENTS V1.1.1 (05/01/2026) :
- FIX : Ajout "(no deepl)" dans le parcours quand la clé API DeepL est absente
- FIX : Ajout "deepl:échec" dans le parcours quand la traduction échoue
- AMÉLIORATION : Logs de debug plus explicites sur les raisons d'échec d'escalade

CHANGEMENTS V1.1.0 (05/01/2026) :
- RENOMMAGE : "rapide" → "standard" partout (modes, logs, API)
- NOUVEAU CHAMP : 'parcours_detection' trace les escalades :
  - "standard" : Résultat direct
  - "standard→ia" : Fallback IA (standardia)
  - "standard→deepl→standard" : Traduction puis standard (standarddeepl)
  - "standard→ia→deepl→ia" : Traduction après IA (iadeepl)
  - "ia" : Mode IA forcé direct
  - "ia→deepl→ia" : Mode IA forcé avec traduction (iadeepl)
- ESCALADE MODE IA : Le mode IA forcé escalade aussi vers DeepL si 0 résultats
- LOGS ENRICHIS : Affichage du parcours complet avec résultats intermédiaires

CHANGEMENTS V1.0.20 (05/01/2026) :
- FIX BUG RATING : Correction TypeError dans update_rating() quand type_probleme
  ou commentaire est None (cas du pouce vers le haut sans dropdown)
- Conversion explicite des valeurs None en chaînes vides avec "or ''"

CHANGEMENTS V1.0.19 (05/01/2026) :
- Suppression des modes "compare" et "union" (fonctions supprimées de trouve.py)
- Modes disponibles : "standard" et "ia" uniquement

CHANGEMENTS V1.0.15 (05/01/2026) :
- ROUTAGE INTELLIGENT avec fallback automatique :
  1. Recherche STANDARD (detall) en premier
  2. Si 0 résultat → fallback vers IA (detia) + emoji 🤖
  3. Si toujours 0 résultat → traduction DeepL + nouvelle recherche + emoji 🌐
- INDICATEURS DE ROUTAGE : Nouveau champ 'indicateurs_routage' avec emojis
  - 🤖 = Fallback IA utilisé
  - 🌐 = Traduction DeepL utilisée
  - 🤖🌐 = Les deux (IA après traduction)
- Champ 'question_affichee' = question + emojis pour affichage UI

ARCHITECTURE :
    Question (any lang) → search.py → trouve.py → Résultats traduits
                              ↓
                        - Détection langue (deepl si auto)
                        - Résolution sémantique question → français (via glossaire.csv)
                        - Appel trouve.rechercher() [STANDARD]
                        - Si 0 résultat → fallback IA
                        - Si toujours 0 → traduction DeepL + retry
                        - Traduction résultats → langue sortie

MODES DE DÉTECTION (via trouve.py) :
    - "standard" : detall.py (patterns, tags, adjectifs)
    - "ia" : detia.py (Claude via Eden AI)

RÉFÉRENTIELS UTILISÉS :
    - glossaire.csv : résolution sémantique multilingue
    - tags.csv : tags orthodontiques avec patterns (pts) et adjectifs autorisés (as)
    - adjectifs.csv : adjectifs avec formes accordées et patterns (pas)
    - pathoori.csv : traductions pathologies patients
    - messages.csv : messages UI multilingues

LANGUES NATIVES (traductions pré-enregistrées) :
    fr, en, de, es, it, pt, pl, ro, th, ar, cn, ja

FORMAT DE SORTIE :
{
    "auteur": "cx|eden/...|cxgti",
    "question_originale": "歯軋り",
    "question_resolue": "bruxisme",
    "question_affichee": "bruxisme 🤖",  # Question + emojis routage
    "indicateurs_routage": "🤖",  # Emojis seuls
    "parcours_detection": "standard→ia",  # Trace des escalades
    "lang": "ja",
    "response_lang": "ja",
    "nb_patients": 42,
    "patients": [...],
    "message": "42 患者 見つかりました 条件 歯軋り",
    "description_filtres": "歯軋り",
    "temps_ms": 125,
    "mots_non_resolus": ["xxx", "yyy"],
    ...
}

Usage en import :
    from search import search
    resultat = search("歯軋り", db_path, lang="auto", mode_detection="standard")
    resultat = search("bruxisme", db_path, mode_detection="ia", model="gpt4o")

Usage CLI :
    python search.py base100.db "bruxisme" --lang=fr
    python search.py base100.db "歯軋り" --lang=ja --mode=ia
"""

import sys
import os
from pathlib import Path

# =============================================================================
# AJOUT DU RÉPERTOIRE DU SCRIPT AU PATH (AVANT les imports locaux)
# =============================================================================
SCRIPT_DIR = Path(__file__).parent.resolve()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

# Détection automatique de la racine (répertoire du script)
RACINE = str(SCRIPT_DIR)
BASES_DIR = SCRIPT_DIR / "bases"
REFS_DIR = SCRIPT_DIR / "refs"
LOGS_DIR = SCRIPT_DIR / "logs"
TESTS_DIR = SCRIPT_DIR / "tests"
LOG_FILE = str(LOGS_DIR / "logrecherche.csv")

import csv
import json
import io
import unicodedata
import re
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

# =============================================================================
# CONSTANTES EMOJIS ROUTAGE
# =============================================================================
EMOJI_IA = "🤖"
EMOJI_TRADUCTION = "🌐"

# =============================================================================
# IMPORTS DES MODULES LOCAUX
# =============================================================================

# Import du module de traduction multi-fournisseurs
try:
    from traduire import (
        traduire, detecter_langue, est_langue_native, 
        get_fallback_langue, LANGUES_NATIVES,
        deepl_traduire  # NOUVEAU V1.0.26 : Import direct pour traduction complète
    )
    TRADUIRE_DISPONIBLE = True
except ImportError as e:
    TRADUIRE_DISPONIBLE = False
    LANGUES_NATIVES = ['fr', 'en', 'de', 'es', 'it', 'pt', 'pl', 'ro', 'th', 'ar', 'cn', 'ja']

# Import de standardise
try:
    from standardise import standardise
    STANDARDISE_DISPONIBLE = True
except ImportError:
    STANDARDISE_DISPONIBLE = False
    def standardise(texte):
        """Version simplifiée de standardise."""
        if texte is None or texte == "":
            return ""
        texte = texte.lower()
        texte = unicodedata.normalize('NFD', texte)
        texte = ''.join(char for char in texte if unicodedata.category(char) != 'Mn')
        for char in ".!-_?":
            texte = texte.replace(char, " ")
        texte = re.sub(r'\s+', ' ', texte)
        return texte.strip()

# Import de trouve.py - CRITIQUE
try:
    from trouve import rechercher
    TROUVE_DISPONIBLE = True
except ImportError as e:
    TROUVE_DISPONIBLE = False
    print(f"[ERREUR] Impossible d'importer trouve.py: {e}")
    print(f"[DEBUG] sys.path = {sys.path[:3]}...")
    print(f"[DEBUG] Fichiers dans {SCRIPT_DIR}: {[f.name for f in SCRIPT_DIR.glob('*.py')][:10]}")


# =============================================================================
# CONFIGURATION
# =============================================================================

DEEPL_API_KEY_ENV = os.environ.get('DEEPL_API_KEY', '')

# Modes de détection valides
# - standard : detall.py avec fallback IA puis DeepL si 0 résultat
# - ia : detia.py avec fallback DeepL si 0 résultat
# - purstandard : detall.py UNIQUEMENT, aucun fallback
# - puria : detia.py UNIQUEMENT, aucun fallback DeepL
MODES_VALIDES = ['standard', 'ia', 'purstandard', 'puria']

# Modèle IA par défaut
DEFAULT_MODEL = 'sonnet'

# Colonnes de langues dans glossaire.csv
COLONNES_LANGUES = ['en', 'de', 'es', 'it', 'ja', 'pt', 'pl', 'ro', 'th', 'ar', 'cn']

# Langues CJK (sans séparateurs de mots) - nécessitent une détection par sous-chaînes
LANGUES_CJK = ['ja', 'cn', 'th']

# En-tête du fichier de log V1.1.0 (avec nouvelles colonnes)
LOG_HEADER = [
    'module', 'timestamp', 'temps_ms', 'languesaisie', 'langueutilisee',
    'modulelangue', 'questionoriginale', 'question', 'filtres', 'sql', 'tri',
    'base', 'mode', 'nb_patients', 'pathologies', 'ages', 'residu', 'erreur',
    'session_id', 'ip_utilisateur', 'rating', 'type_probleme', 'commentaire'
]


# =============================================================================
# CACHE GLOBAL DES DICTIONNAIRES DE RÉSOLUTION SÉMANTIQUE (LAZY LOADING)
# =============================================================================

# Cache: {lang_code: [(expression_normalisee, terme_francais, expression_originale), ...]}
# Trié par longueur décroissante de expression_normalisee
_DICO_RESOLUTION_CACHE: Dict[str, List[Tuple[str, str, str]]] = {}

# Cache du glossaire brut (chargé une seule fois)
_GLOSSAIRE_BRUT_CACHE: Optional[List[Dict[str, str]]] = None

# Cache des termes français du glossaire
_GLOSSAIRE_FR_CACHE: Optional[set] = None

# Cache des langues valides
_LANGUES_CACHE: Optional[List[str]] = None

# Cache des modèles valides
_MODELES_CACHE: Optional[Dict[str, dict]] = None


def _normaliser_pour_comparaison(texte: str) -> str:
    """
    Normalise un texte pour la comparaison : minuscules + suppression accents.
    """
    if not texte:
        return ""
    texte = texte.lower()
    texte = unicodedata.normalize('NFD', texte)
    texte = ''.join(char for char in texte if unicodedata.category(char) != 'Mn')
    return texte.strip()


def _charger_glossaire_brut(glossaire_path: Path = None, verbose: bool = False) -> List[Dict[str, str]]:
    """Charge le glossaire brut une seule fois."""
    global _GLOSSAIRE_BRUT_CACHE
    
    if _GLOSSAIRE_BRUT_CACHE is not None:
        return _GLOSSAIRE_BRUT_CACHE
    
    if glossaire_path is None:
        glossaire_path = REFS_DIR / "glossaire.csv"
    
    if not glossaire_path.exists():
        if verbose:
            print(f"[DEBUG] _charger_glossaire_brut: glossaire.csv introuvable à {glossaire_path}")
        _GLOSSAIRE_BRUT_CACHE = []
        return []
    
    rows = []
    try:
        with open(glossaire_path, 'r', encoding='utf-8-sig') as f:
            lignes = [line for line in f if not line.strip().startswith('#')]
        
        if not lignes:
            _GLOSSAIRE_BRUT_CACHE = []
            return []
        
        lignes_io = io.StringIO(''.join(lignes))
        reader = csv.DictReader(lignes_io, delimiter=';')
        
        for row in reader:
            rows.append(dict(row))
        
        if verbose:
            print(f"[DEBUG] _charger_glossaire_brut: {len(rows)} lignes chargées")
        
        _GLOSSAIRE_BRUT_CACHE = rows
        return rows
        
    except Exception as e:
        if verbose:
            print(f"[DEBUG] _charger_glossaire_brut: Erreur {e}")
        _GLOSSAIRE_BRUT_CACHE = []
        return []


def _construire_dico_resolution(lang: str, verbose: bool = False) -> List[Tuple[str, str, str]]:
    """
    Construit le dictionnaire de résolution pour une langue donnée.
    """
    global _DICO_RESOLUTION_CACHE
    
    if lang in _DICO_RESOLUTION_CACHE:
        return _DICO_RESOLUTION_CACHE[lang]
    
    glossaire = _charger_glossaire_brut(verbose=verbose)
    
    if not glossaire:
        _DICO_RESOLUTION_CACHE[lang] = []
        return []
    
    entries = []
    
    for row in glossaire:
        terme_fr = row.get('fr', '').strip()
        if not terme_fr:
            continue
        
        terme_lang = row.get(lang, '').strip()
        if not terme_lang:
            continue
        
        variantes = [v.strip() for v in terme_lang.split(',') if v.strip()]
        
        for variante in variantes:
            variante_norm = _normaliser_pour_comparaison(variante)
            if variante_norm:
                entries.append((variante_norm, terme_fr, variante))
    
    entries.sort(key=lambda x: len(x[0]), reverse=True)
    
    if verbose:
        print(f"[DEBUG] _construire_dico_resolution({lang}): {len(entries)} entrées")
    
    _DICO_RESOLUTION_CACHE[lang] = entries
    return entries


def resoudre_question_semantique(question: str, lang: str, verbose: bool = False) -> Tuple[str, List[str]]:
    """
    Résout une question d'une langue vers le français via glossaire.csv.
    """
    if lang == 'fr':
        return question, []
    
    dico = _construire_dico_resolution(lang, verbose)
    
    if not dico:
        if verbose:
            print(f"[DEBUG] resoudre_question_semantique: Pas de dico pour {lang}")
        return question, [question] if question.strip() else []
    
    question_norm = _normaliser_pour_comparaison(question)
    question_travail = question_norm
    
    est_cjk = lang in LANGUES_CJK
    
    resolutions = []
    positions_resolues = []
    
    for (expr_norm, terme_fr, expr_orig) in dico:
        pos = 0
        while True:
            idx = question_travail.find(expr_norm, pos)
            if idx == -1:
                break
            
            fin = idx + len(expr_norm)
            
            chevauchement = False
            for (debut_existant, fin_existant) in positions_resolues:
                if not (fin <= debut_existant or idx >= fin_existant):
                    chevauchement = True
                    break
            
            if chevauchement:
                pos = fin
                continue
            
            if est_cjk:
                avant_ok = True
                apres_ok = True
            else:
                avant_ok = (idx == 0 or not question_travail[idx-1].isalnum())
                apres_ok = (fin == len(question_travail) or not question_travail[fin].isalnum())
            
            if avant_ok and apres_ok:
                positions_resolues.append((idx, fin))
                resolutions.append((idx, fin, terme_fr))
                if verbose:
                    print(f"[DEBUG]   Résolu: '{expr_orig}' → '{terme_fr}' à position {idx}")
            
            pos = fin
    
    if not resolutions:
        if est_cjk:
            return question, [question] if question.strip() else []
        else:
            mots = question.split()
            return question, mots
    
    resolutions.sort(key=lambda x: x[0])
    
    result_parts = []
    mots_non_resolus = []
    last_end = 0
    
    for (debut, fin, terme_fr) in resolutions:
        if debut > last_end:
            texte_avant = question_norm[last_end:debut].strip()
            if texte_avant:
                result_parts.append(texte_avant)
                if est_cjk:
                    if texte_avant:
                        mots_non_resolus.append(texte_avant)
                else:
                    for mot in texte_avant.split():
                        if mot and len(mot) > 1:
                            mots_non_resolus.append(mot)
        
        result_parts.append(terme_fr)
        last_end = fin
    
    if last_end < len(question_norm):
        texte_apres = question_norm[last_end:].strip()
        if texte_apres:
            result_parts.append(texte_apres)
            if est_cjk:
                mots_non_resolus.append(texte_apres)
            else:
                for mot in texte_apres.split():
                    if mot and len(mot) > 1:
                        mots_non_resolus.append(mot)
    
    question_resolue = ' '.join(result_parts)
    
    if verbose:
        print(f"[DEBUG] resoudre_question_semantique: Résultat = '{question_resolue}'")
        print(f"[DEBUG]   Mots non résolus: {mots_non_resolus}")
    
    return question_resolue, mots_non_resolus


# =============================================================================
# GESTION DU CHUTIER (MOTS NON RÉSOLUS)
# =============================================================================

def _maj_chutier(lang: str, mots_non_resolus: List[str], verbose: bool = False) -> None:
    """Crée ou met à jour le fichier chutier.csv avec les mots non résolus."""
    if not mots_non_resolus:
        return
    
    chutier_path = REFS_DIR / "chutier.csv"
    chutier_data = {}
    
    if chutier_path.exists():
        try:
            with open(chutier_path, 'r', encoding='utf-8-sig') as f:
                lignes = [line for line in f if not line.strip().startswith('#')]
            
            if lignes:
                lignes_io = io.StringIO(''.join(lignes))
                reader = csv.DictReader(lignes_io, delimiter=';')
                
                for row in reader:
                    langue = row.get('langue', '').strip()
                    mot = row.get('mot', '').strip()
                    nb = int(row.get('nb', '0'))
                    if langue and mot:
                        chutier_data[(langue, mot)] = nb
        except Exception as e:
            if verbose:
                print(f"[DEBUG] _maj_chutier: Erreur lecture chutier.csv: {e}")
    
    mots_traites = []
    for mot in mots_non_resolus:
        mot = mot.strip().lower()
        if mot:
            cle = (lang, mot)
            if cle in chutier_data:
                chutier_data[cle] += 1
            else:
                chutier_data[cle] = 1
            mots_traites.append(mot)
    
    try:
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        with open(chutier_path, 'w', encoding='utf-8-sig', newline='') as f:
            f.write(f"# chutier.csv - Créé par {__pgm__} - {timestamp}\n")
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['langue', 'mot', 'nb'])
            
            donnees_triees = sorted(chutier_data.items(), key=lambda x: (x[0][0], -x[1]))
            
            for (langue, mot), nb in donnees_triees:
                writer.writerow([langue, mot, nb])
        
        if verbose or mots_traites:
            print(f"chutier màj & {', '.join(mots_traites)}")
            
    except Exception as e:
        if verbose:
            print(f"[DEBUG] _maj_chutier: Erreur écriture chutier.csv: {e}")


# =============================================================================
# CHARGEMENT DES LANGUES ET MODÈLES DEPUIS COMMUN.CSV
# =============================================================================

def charger_langues(commun_path: str = None, verbose: bool = False) -> List[str]:
    """Charge les langues depuis la colonne 'langues' de commun.csv."""
    if commun_path is None:
        commun_path = REFS_DIR / "commun.csv"
    else:
        commun_path = Path(commun_path)
    
    if not commun_path.exists():
        if verbose:
            print(f"[DEBUG] charger_langues: commun.csv introuvable, fallback")
        return ['fr', 'en', 'de', 'es', 'it', 'pt', 'pl', 'ro', 'th', 'ar', 'cn', 'ja']
    
    langues = set()
    
    try:
        with open(commun_path, 'r', encoding='utf-8-sig') as f:
            lignes = [line for line in f if not line.strip().startswith('#')]
        
        if not lignes:
            return ['fr']
        
        lignes_io = io.StringIO(''.join(lignes))
        reader = csv.DictReader(lignes_io, delimiter=';')
        
        for row in reader:
            lang = row.get('langues', '').strip().lower()
            if lang:
                langues.add(lang)
        
        if verbose:
            print(f"[DEBUG] charger_langues: {len(langues)} langues chargées")
        
        return sorted(list(langues)) if langues else ['fr']
        
    except Exception as e:
        if verbose:
            print(f"[DEBUG] charger_langues: Erreur {e}")
        return ['fr']


def charger_modeles(commun_path: str = None, verbose: bool = False) -> Dict[str, dict]:
    """Charge les modèles IA depuis ia.csv."""
    refs_dir = REFS_DIR
    ia_path = refs_dir / "ia.csv"
    
    default_modeles = {
        'standard': {'via': '', 'complet': '', 'actif': True},
        'sonnet': {'via': 'eden', 'complet': 'anthropic/claude-3-7-sonnet-20250219', 'actif': True},
        'gpt4omini': {'via': 'openai', 'complet': 'gpt-4o-mini', 'actif': True},
    }
    
    if not ia_path.exists():
        return default_modeles
    
    modeles = {'standard': {'via': '', 'complet': '', 'actif': True}}
    
    try:
        with open(ia_path, 'r', encoding='utf-8-sig') as f:
            lignes = [line for line in f if not line.strip().startswith('#')]
        
        if not lignes:
            return default_modeles
        
        lignes_io = io.StringIO(''.join(lignes))
        reader = csv.DictReader(lignes_io, delimiter=';')
        
        for row in reader:
            court = row.get('court', row.get('moteur', '')).strip().lower()
            # Mapper 'rapide' vers 'standard' pour rétrocompatibilité ia.csv
            if court == 'rapide':
                court = 'standard'
            if not court or court == 'standard':
                continue
            
            actif = row.get('actif', 'O').strip().upper() == 'O'
            
            modeles[court] = {
                'via': row.get('via', '').strip().lower(),
                'complet': row.get('complet', '').strip(),
                'actif': actif,
            }
        
        if verbose:
            print(f"[DEBUG] charger_modeles: {len(modeles)} modèles chargés")
        
        return modeles
        
    except Exception as e:
        if verbose:
            print(f"[DEBUG] charger_modeles: Erreur {e}")
        return default_modeles


def charger_glossaire_fr(glossaire_path: Path = None, verbose: bool = False) -> set:
    """Charge les termes français du glossaire pour détection langue."""
    if glossaire_path is None:
        glossaire_path = REFS_DIR / "glossaire.csv"
    
    if not glossaire_path.exists():
        if verbose:
            print(f"[DEBUG] charger_glossaire_fr: glossaire.csv introuvable")
        return set()
    
    termes_fr = set()
    
    try:
        with open(glossaire_path, 'r', encoding='utf-8-sig') as f:
            lignes = [line for line in f if not line.strip().startswith('#')]
        
        if not lignes:
            return set()
        
        lignes_io = io.StringIO(''.join(lignes))
        reader = csv.DictReader(lignes_io, delimiter=';')
        
        for row in reader:
            terme_fr = row.get('fr', '').strip().lower()
            if terme_fr:
                termes_fr.add(terme_fr)
        
        if verbose:
            print(f"[DEBUG] charger_glossaire_fr: {len(termes_fr)} termes français chargés")
        
        return termes_fr
        
    except Exception as e:
        if verbose:
            print(f"[DEBUG] charger_glossaire_fr: Erreur {e}")
        return set()


def get_glossaire_fr() -> set:
    """Retourne l'ensemble des termes français du glossaire (avec cache)."""
    global _GLOSSAIRE_FR_CACHE
    if _GLOSSAIRE_FR_CACHE is None:
        _GLOSSAIRE_FR_CACHE = charger_glossaire_fr()
    return _GLOSSAIRE_FR_CACHE


def est_terme_glossaire_fr(question: str) -> bool:
    """Vérifie si la question est un terme français du glossaire."""
    glossaire_fr = get_glossaire_fr()
    return question.lower().strip() in glossaire_fr


def get_langues_valides() -> List[str]:
    """Retourne la liste des langues valides (avec cache)."""
    global _LANGUES_CACHE
    if _LANGUES_CACHE is None:
        _LANGUES_CACHE = charger_langues()
    return _LANGUES_CACHE


def get_modeles_valides() -> Dict[str, dict]:
    """Retourne le dictionnaire des modèles valides (avec cache)."""
    global _MODELES_CACHE
    if _MODELES_CACHE is None:
        _MODELES_CACHE = charger_modeles()
    return _MODELES_CACHE


# =============================================================================
# GESTION DES LOGS V1.1.0
# =============================================================================

def _init_log_file():
    """Initialise le fichier de logs s'il n'existe pas."""
    try:
        if not os.path.exists(LOGS_DIR):
            os.makedirs(LOGS_DIR, exist_ok=True)
            print(f"[INFO] Répertoire logs créé : {LOGS_DIR}")
        
        if not os.path.exists(LOG_FILE):
            timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
            with open(LOG_FILE, 'w', encoding='utf-8-sig', newline='') as f:
                f.write(f"# logrecherche.csv V1.1.0 - {timestamp}\n")
                writer = csv.writer(f, delimiter=';')
                writer.writerow(LOG_HEADER)
            print(f"[INFO] Fichier log créé : {LOG_FILE}")
        else:
            _migrate_log_file_if_needed()
    except PermissionError as e:
        print(f"[ERREUR] Permission refusée pour créer le fichier de logs: {e}")
    except Exception as e:
        print(f"[ERREUR] Impossible d'initialiser le fichier de logs: {e}")


def _migrate_log_file_if_needed():
    """Migre le fichier de log si nécessaire."""
    try:
        with open(LOG_FILE, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
        
        if not lines:
            return
        
        header_idx = -1
        for i, line in enumerate(lines):
            if not line.strip().startswith('#'):
                header_idx = i
                break
        
        if header_idx == -1:
            return
        
        current_header = lines[header_idx].strip().split(';')
        if 'session_id' not in current_header:
            new_columns = ['session_id', 'ip_utilisateur', 'rating', 'type_probleme', 'commentaire']
            new_header = current_header + new_columns
            lines[header_idx] = ';'.join(new_header) + '\n'
            
            with open(LOG_FILE, 'w', encoding='utf-8-sig', newline='') as f:
                f.writelines(lines)
            
            print(f"[INFO] logrecherche.csv migré vers V1.1.0")
    
    except Exception as e:
        print(f"[WARNING] Erreur migration log: {e}")


def _log_recherche(question_originale: str, question_fr: str, base: str, mode: str,
                   nb_patients: int, temps_ms: int, pathologies: List[str],
                   ages: List[str], residu: str, filtres: dict, sql: str,
                   languesaisie: str, langueutilisee: str, modulelangue: str,
                   erreur: str = "", session_id: str = "", ip_utilisateur: str = "",
                   indicateurs_routage: str = ""):
    """Ajoute une ligne au fichier de logs."""
    _init_log_file()
    
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    pathologies_str = ", ".join(pathologies) if pathologies else ""
    ages_str = ", ".join(ages) if ages else ""
    filtres_json = json.dumps(filtres, ensure_ascii=False) if filtres else ""
    
    # Ajouter indicateurs au mode si présents
    mode_complet = f"{mode} {indicateurs_routage}".strip() if indicateurs_routage else mode
    
    log_row = [
        __pgm__,
        timestamp,
        temps_ms,
        languesaisie,
        langueutilisee,
        modulelangue,
        question_originale,
        question_fr,
        filtres_json,
        sql,
        '',  # tri
        base,
        mode_complet,
        nb_patients,
        pathologies_str,
        ages_str,
        residu,
        erreur,
        session_id,
        ip_utilisateur,
        '',  # rating
        '',  # type_probleme
        ''   # commentaire
    ]
    
    try:
        with open(LOG_FILE, 'a', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(log_row)
    except Exception as e:
        print(f"[ERREUR] Erreur écriture log: {e}")


def update_rating(session_id: str, rating: str, type_probleme: str = "", 
                  commentaire: str = "") -> bool:
    """Met à jour le rating d'une recherche via son session_id."""
    if not session_id:
        return False
    
    try:
        with open(LOG_FILE, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
        
        if not lines:
            return False
        
        header_idx = -1
        for i, line in enumerate(lines):
            if not line.strip().startswith('#'):
                header_idx = i
                break
        
        if header_idx == -1:
            return False
        
        header = lines[header_idx].strip().split(';')
        
        try:
            session_col = header.index('session_id')
            rating_col = header.index('rating')
            type_col = header.index('type_probleme')
            comment_col = header.index('commentaire')
        except ValueError:
            return False
        
        found = False
        for i in range(header_idx + 1, len(lines)):
            cols = lines[i].strip().split(';')
            if len(cols) > session_col and cols[session_col] == session_id:
                while len(cols) <= comment_col:
                    cols.append('')
                
                cols[rating_col] = rating or ''
                cols[type_col] = type_probleme or ''
                cols[comment_col] = commentaire or ''
                lines[i] = ';'.join(cols) + '\n'
                found = True
                break
        
        if found:
            with open(LOG_FILE, 'w', encoding='utf-8-sig', newline='') as f:
                f.writelines(lines)
        
        return found
        
    except Exception as e:
        print(f"[WARNING] Erreur update_rating: {e}")
        return False


# =============================================================================
# CHARGEMENT DES RÉFÉRENCES MULTILINGUES
# =============================================================================

def charger_pathologies_multilingues(pathoori_path: str, verbose: bool = False) -> dict:
    """Charge les traductions de pathologies depuis pathoori.csv."""
    mapping = {}
    
    try:
        with open(pathoori_path, 'r', encoding='utf-8-sig') as f:
            lignes = [line for line in f if not line.strip().startswith('#')]
        
        if not lignes:
            return mapping
        
        lignes_io = io.StringIO(''.join(lignes))
        reader = csv.DictReader(lignes_io, delimiter=';')
        
        for ligne in reader:
            pathofr = ligne.get('pathofr', '').strip()
            if not pathofr:
                continue
            
            pathofr_std = standardise(pathofr)
            
            mapping[pathofr_std] = {
                'fr': pathofr,
                'en': ligne.get('en', '').strip(),
                'de': ligne.get('de', '').strip(),
                'es': ligne.get('es', '').strip(),
                'it': ligne.get('it', '').strip(),
                'pt': ligne.get('pt', '').strip(),
                'pl': ligne.get('pl', '').strip(),
                'ro': ligne.get('ro', '').strip(),
                'th': ligne.get('th', '').strip(),
                'ar': ligne.get('ar', '').strip(),
                'cn': ligne.get('cn', '').strip(),
                'ja': ligne.get('ja', '').strip()
            }
        
        if verbose:
            print(f"[DEBUG] search: {len(mapping)} pathologies multilingues chargées")
        
        return mapping
        
    except Exception as e:
        if verbose:
            print(f"[DEBUG] search: ERREUR chargement pathoori.csv: {e}")
        return {}


def charger_messages_multilingues(messages_path: str, verbose: bool = False) -> dict:
    """Charge les messages traduits depuis messages.csv."""
    messages = {}
    
    try:
        with open(messages_path, 'r', encoding='utf-8-sig') as f:
            lignes = [line for line in f if not line.strip().startswith('#')]
        
        if not lignes:
            return messages
        
        lignes_io = io.StringIO(''.join(lignes))
        reader = csv.DictReader(lignes_io, delimiter=';')
        
        for ligne in reader:
            usage = ligne.get('usage', '').strip()
            if not usage:
                continue
            
            messages[usage] = {
                'fr': ligne.get('fr', '').strip(),
                'en': ligne.get('en', '').strip(),
                'de': ligne.get('de', '').strip(),
                'es': ligne.get('es', '').strip(),
                'it': ligne.get('it', '').strip(),
                'pt': ligne.get('pt', '').strip(),
                'pl': ligne.get('pl', '').strip(),
                'ro': ligne.get('ro', '').strip(),
                'th': ligne.get('th', '').strip(),
                'ar': ligne.get('ar', '').strip(),
                'cn': ligne.get('cn', '').strip(),
                'ja': ligne.get('ja', '').strip()
            }
        
        if verbose:
            print(f"[DEBUG] search: {len(messages)} messages chargés")
        
        return messages
        
    except Exception as e:
        if verbose:
            print(f"[DEBUG] search: ERREUR chargement messages.csv: {e}")
        return {}


# =============================================================================
# TRADUCTION DES PATHOLOGIES
# =============================================================================

def traduire_pathologie(patho_fr: str, mapping_patho: dict, lang: str, 
                        verbose: bool = False) -> str:
    """Traduit une pathologie française vers la langue cible."""
    if lang == 'fr' or not mapping_patho:
        return patho_fr
    
    patho_std = standardise(patho_fr)
    
    if patho_std in mapping_patho:
        trad = mapping_patho[patho_std].get(lang, '')
        if trad:
            if ',' in trad:
                trad = trad.split(',')[0].strip()
            if verbose:
                print(f"[DEBUG] search: Pathologie '{patho_fr}' → '{trad}'")
            return trad
    
    return patho_fr


def traduire_pathologies_patient(patho_str: str, mapping_patho: dict, lang: str,
                                  verbose: bool = False) -> str:
    """Traduit la liste de pathologies d'un patient."""
    if not patho_str or lang == 'fr':
        return patho_str
    
    pathologies_list = [p.strip() for p in patho_str.split(',') if p.strip()]
    pathologies_trad = []
    
    for patho_fr in pathologies_list:
        trad = traduire_pathologie(patho_fr, mapping_patho, lang, verbose)
        pathologies_trad.append(trad)
    
    return ', '.join(pathologies_trad)


def traduire_description_filtres(description_fr: str, mapping_patho: dict, lang: str,
                                  verbose: bool = False) -> str:
    """Traduit la description des filtres."""
    if not description_fr or lang == 'fr':
        return description_fr
    
    parties = description_fr.split(' + ')
    parties_traduites = []
    
    for partie in parties:
        sous_parties = [p.strip() for p in partie.split(', ') if p.strip()]
        sous_parties_trad = []
        
        for terme in sous_parties:
            terme_trad = traduire_pathologie(terme, mapping_patho, lang, verbose=False)
            sous_parties_trad.append(terme_trad)
        
        parties_traduites.append(', '.join(sous_parties_trad))
    
    resultat = ' + '.join(parties_traduites)
    
    if verbose and resultat != description_fr:
        print(f"[DEBUG] search: Filtres '{description_fr}' → '{resultat}'")
    
    return resultat


# =============================================================================
# TRADUCTION DES MESSAGES
# =============================================================================

def get_message(messages: dict, usage: str, lang: str, nb: int = 0, 
                filtre: str = '', verbose: bool = False) -> str:
    """Récupère un message traduit avec substitutions."""
    if usage not in messages:
        return f"{nb} patients trouvés"
    
    msg_dict = messages[usage]
    msg = msg_dict.get(lang, '')
    
    if not msg:
        msg = msg_dict.get('fr', f"{nb} patients trouvés")
    
    msg = msg.replace('xx', str(nb))
    msg = msg.replace('{ff}', filtre)
    
    return msg


def get_unit_year(messages: dict, lang: str) -> str:
    """Récupère l'unité d'année traduite."""
    if 'unit_year' in messages:
        unit = messages['unit_year'].get(lang, '')
        if unit:
            return unit
    
    units = {
        'fr': 'ans', 'en': 'years', 'de': 'Jahre', 'es': 'años',
        'it': 'anni', 'pt': 'anos', 'pl': 'lat', 'ro': 'ani',
        'th': 'ปี', 'ar': 'سنة', 'cn': '岁', 'ja': '歳'
    }
    return units.get(lang, 'ans')


# =============================================================================
# CONSTRUCTION DE LA DESCRIPTION DES FILTRES
# =============================================================================

def _construire_description_filtres(resultats: dict) -> str:
    """Construit la description des filtres appliqués."""
    parties = []
    
    criteres = resultats.get('criteres_detectes', [])
    if criteres:
        for critere in criteres:
            if isinstance(critere, dict):
                valeur = critere.get('valeur', critere.get('terme', ''))
                if valeur:
                    parties.append(valeur)
            elif isinstance(critere, str):
                parties.append(critere)
    
    if not parties:
        pathologies = resultats.get('pathologies', [])
        if pathologies:
            parties.extend(pathologies)
        
        ages = resultats.get('ages', [])
        if ages:
            parties.extend(ages)
    
    return ' + '.join(parties) if parties else ''


# =============================================================================
# TRADUCTION DEEPL (FALLBACK)
# =============================================================================

def _traduire_question_deepl(question: str, lang_source: str, api_key: str = None, 
                              verbose: bool = False) -> Tuple[str, bool]:
    """
    Traduit une question vers le français via DeepL API.
    
    Returns:
        Tuple (question_traduite, succes)
    """
    if not TRADUIRE_DISPONIBLE:
        if verbose:
            print(f"[DEBUG] _traduire_question_deepl: Module traduire non disponible")
        return question, False
    
    deepl_key = api_key or DEEPL_API_KEY_ENV
    if not deepl_key:
        if verbose:
            print(f"[DEBUG] _traduire_question_deepl: Pas de clé DeepL")
        return question, False
    
    try:
        question_traduite = traduire(
            texte=question,
            source=lang_source,
            target='fr',
            api_key=deepl_key,
            verbose=verbose
        )
        
        if question_traduite and question_traduite != question:
            if verbose:
                print(f"[DEBUG] Traduction DeepL: '{question}' → '{question_traduite}'")
            return question_traduite, True
        
        return question, False
        
    except Exception as e:
        if verbose:
            print(f"[DEBUG] _traduire_question_deepl: Erreur {e}")
        return question, False


# =============================================================================
# FONCTION PRINCIPALE : search() AVEC ROUTAGE INTELLIGENT
# =============================================================================

def search(
    question: str, 
    base_path: str, 
    lang: Optional[str] = None,
    mode_detection: str = 'standard',
    model: str = None,
    verbose: bool = False,
    mapping_patho: Optional[dict] = None,
    messages: Optional[dict] = None,
    response_lang: Optional[str] = None,
    limit: int = 100, 
    offset: int = 0,
    api_key: str = None,
    session_id: str = None,
    ip_utilisateur: str = None
) -> dict:
    """
    Point d'entrée multilingue pour rechercher des patients.
    
    ROUTAGE INTELLIGENT V1.1.0:
    Mode STANDARD (défaut):
      1. Recherche STANDARD (detall) en premier
      2. Si 0 résultat → fallback vers IA (detia) + emoji 🤖
      3. Si toujours 0 résultat → traduction DeepL + nouvelle recherche + emoji 🌐
    
    Mode IA (forcé):
      1. Recherche IA directe
      2. Si 0 résultat → traduction DeepL + nouvelle recherche IA + emoji 🌐
    
    PARCOURS DE DÉTECTION:
      - "standard" : Résultat standard direct
      - "standard→ia" : Fallback IA après échec standard
      - "standard→deepl→standard" : Traduction puis standard
      - "standard→ia→deepl→standard" : Traduction après échecs, puis standard OK
      - "standard→ia→deepl→ia" : Traduction après échecs, puis IA OK
      - "ia" : Mode IA forcé direct
      - "ia→deepl→ia" : Mode IA forcé avec traduction
    """
    start_time = datetime.now()
    base_name = os.path.basename(base_path)
    
    # Clé API : paramètre > variable d'environnement
    deepl_key = api_key or DEEPL_API_KEY_ENV
    
    # Variables pour les logs et le routage
    languesaisie = lang if lang else 'Auto'
    langueutilisee = ''
    modulelangue = ''
    question_resolue = question
    mots_non_resolus = []
    indicateurs_routage = ""  # Emojis de routage
    mode_effectif = mode_detection  # Mode réellement utilisé
    parcours_detection = []  # Liste des étapes du parcours
    
    # Valeurs par défaut pour session_id et IP
    session_id = session_id or ''
    ip_utilisateur = ip_utilisateur or ''
    
    if verbose:
        print(f"[DEBUG] search: Lang demandée: {lang}, Mode détection: {mode_detection}")
        if model:
            print(f"[DEBUG] search: Modèle IA: {model}")
        print(f"[DEBUG] search: DeepL API: {'✓' if deepl_key else '✗'}")
    
    # ═══════════════════════════════════════════════════════════════
    # VÉRIFICATION TROUVE.PY
    # ═══════════════════════════════════════════════════════════════
    
    if not TROUVE_DISPONIBLE:
        elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        return {
            'erreur': "Module trouve.py non disponible",
            'nb_patients': 0,
            'patients': [],
            'lang': lang or 'fr',
            'response_lang': response_lang or 'fr',
            'temps_ms': elapsed_ms,
            'indicateurs_routage': '',
            'question_affichee': question
        }
    
    # ═══════════════════════════════════════════════════════════════
    # VÉRIFICATION ET RÉSOLUTION DU CHEMIN DE LA BASE
    # ═══════════════════════════════════════════════════════════════
    
    base_path_resolved = Path(base_path)
    if not base_path_resolved.exists():
        base_in_bases = BASES_DIR / base_path_resolved.name
        if base_in_bases.exists():
            base_path = str(base_in_bases)
            base_path_resolved = base_in_bases
            if verbose:
                print(f"[DEBUG] search: Base trouvée dans bases/: {base_path}")
        else:
            elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            return {
                'erreur': f"Base introuvable: {base_path}",
                'nb_patients': 0,
                'patients': [],
                'lang': lang or 'fr',
                'response_lang': response_lang or 'fr',
                'temps_ms': elapsed_ms,
                'indicateurs_routage': '',
                'question_affichee': question
            }
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 0 : PRÉ-DÉTECTION PATTERN 'id XXX' → Forcer FR
    # Si la question contient "id XXX" (pattern technique detid.py),
    # c'est une requête par identifiant qui ne doit PAS être traduite.
    # "id" seul est interprété comme Latin/Danois par DeepL → corruption.
    # ═══════════════════════════════════════════════════════════════
    
    _PATTERN_ID_TECHNIQUE = re.compile(r'\bid\s+[a-zA-Z0-9]+', re.IGNORECASE)
    if _PATTERN_ID_TECHNIQUE.search(question):
        lang = 'fr'
        modulelangue = 'id_technique'
        if verbose:
            print(f"[DEBUG] search: Pattern 'id XXX' détecté → forcé fr (pas de traduction)")
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 1 : DÉTECTION LANGUE
    # ═══════════════════════════════════════════════════════════════
    
    detecte_via_glossaire = False
    
    if lang is None or lang.lower() == 'auto':
        if est_terme_glossaire_fr(question):
            lang = 'fr'
            modulelangue = 'glossaire_fr'
            detecte_via_glossaire = True
        elif TRADUIRE_DISPONIBLE:
            lang = detecter_langue(question, deepl_key, verbose)
            modulelangue = 'deepl' if deepl_key else 'heuristique'
        else:
            lang = 'fr'
            modulelangue = 'fallback'
    
    lang = lang.lower()
    langueutilisee = lang
    
    if verbose:
        suffix_glossaire = ", dans glossaire fr" if detecte_via_glossaire else ""
        print(f"[DEBUG] search: Question: '{question}' Lang: {lang}{suffix_glossaire}")
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 2 : DÉTERMINER LANGUE DE RÉPONSE
    # ═══════════════════════════════════════════════════════════════
    
    if response_lang == 'fr':
        output_lang = 'fr'
    else:
        output_lang = lang
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 3 : TRADUCTION QUESTION → FRANÇAIS (V1.0.27 : Glossaire prioritaire)
    # ═══════════════════════════════════════════════════════════════
    
    question_technique_fr = question  # Question envoyée à trouve.py
    
    if lang == 'fr':
        question_resolue = question
        question_technique_fr = question
        mots_non_resolus = []
    else:
        # V1.0.27 : GLOSSAIRE PRIORITAIRE, DeepL en fallback
        # traduire() cherche d'abord dans glossaire.csv les termes médicaux,
        # puis utilise DeepL uniquement pour traduire le résidu.
        # Cela évite que DeepL traduise "offener Biss" en "occlusion ouverte"
        # au lieu de conserver "béance" du glossaire.
        if TRADUIRE_DISPONIBLE:
            if verbose:
                print(f"[DEBUG] search: Traduction {lang} → fr via glossaire + DeepL fallback...")
            
            # Appel à traduire() qui utilise glossaire en priorité
            question_traduite, fournisseur = traduire(
                texte=question,
                source_lang=lang,
                target_lang='fr',
                api_key=deepl_key,
                verbose=verbose
            )
            
            if question_traduite and question_traduite != question:
                question_resolue = question_traduite
                question_technique_fr = question_traduite
                modulelangue = fournisseur  # 'glossaire', 'deepl' ou 'none'
                mots_non_resolus = []
                
                if verbose:
                    print(f"[DEBUG] search: Traduction via {fournisseur}: '{question_traduite}'")
            else:
                # Aucune traduction effectuée - garder la question originale
                if verbose:
                    print(f"[DEBUG] search: Pas de traduction possible, question inchangée")
                question_resolue = question
                question_technique_fr = question
                modulelangue = 'none'
                mots_non_resolus = []
        else:
            # Module traduire non disponible → résolution glossaire seul
            question_resolue, mots_non_resolus = resoudre_question_semantique(
                question, lang, verbose
            )
            question_technique_fr = question_resolue
            modulelangue = 'glossaire_resolution'
        
        if verbose:
            print(f"[DEBUG] search: Question technique FR: '{question_technique_fr}'")
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 4 : CHARGER RÉFÉRENCES SI NON FOURNIES
    # ═══════════════════════════════════════════════════════════════
    
    script_dir = Path(__file__).parent
    refs_dir = script_dir / "refs"
    
    if mapping_patho is None:
        pathoori_path = refs_dir / "pathoori.csv"
        if pathoori_path.exists():
            mapping_patho = charger_pathologies_multilingues(str(pathoori_path), verbose)
        else:
            mapping_patho = {}
    
    if messages is None:
        messages_path = refs_dir / "messages.csv"
        if messages_path.exists():
            messages = charger_messages_multilingues(str(messages_path), verbose)
        else:
            messages = {}
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 5 : RECHERCHE AVEC ROUTAGE INTELLIGENT
    # ═══════════════════════════════════════════════════════════════
    
    resultats = None
    question_pour_recherche = question_resolue
    
    try:
        if mode_detection == 'puria':
            # ═══════════════════════════════════════════════════════════
            # MODE PURIA : IA PURE SANS AUCUN FALLBACK
            # ═══════════════════════════════════════════════════════════
            
            parcours_detection.append(f"puria:{0}")
            if verbose:
                print(f"[DEBUG] search: 🤖 Mode PURIA (IA sans fallback)...")
            
            resultats = rechercher(
                question_pour_recherche, base_path,
                mode='ia', include_details=True, verbose=verbose, debug=False, model=model,
                limit=limit, offset=offset
            )
            
            nb_resultats = resultats.get('nb', 0)
            parcours_detection[-1] = f"puria:{nb_resultats}"
            mode_effectif = 'puria'
            
            if verbose:
                print(f"[DEBUG] search: 🤖 puria: {nb_resultats} résultat(s) (pas de fallback)")
        
        elif mode_detection == 'ia':
            # ═══════════════════════════════════════════════════════════
            # MODE IA FORCÉ (avec escalade DeepL possible)
            # ═══════════════════════════════════════════════════════════
            
            # ÉTAPE 5.1 : Recherche IA directe
            parcours_detection.append(f"ia:{0}")  # Placeholder, sera mis à jour
            if verbose:
                print(f"[DEBUG] search: 🤖 Mode IA forcé...")
            
            resultats = rechercher(
                question_pour_recherche, base_path,
                mode='ia', include_details=True, verbose=verbose, debug=False, model=model,
                limit=limit, offset=offset
            )
            
            nb_resultats = resultats.get('nb', 0)
            parcours_detection[-1] = f"ia:{nb_resultats}"
            
            if verbose:
                print(f"[DEBUG] search: 🤖 ia: {nb_resultats} résultat(s)")
            
            if nb_resultats > 0:
                mode_effectif = 'ia'
            else:
                # ÉTAPE 5.2 : Si 0 résultat ET langue != fr → fallback traduction DeepL
                if lang != 'fr':
                    if deepl_key:
                        if verbose:
                            print(f"[DEBUG] search: 🤖 ia: 0 → 🌐 fallback traduction DeepL")
                        
                        question_traduite, traduction_ok = _traduire_question_deepl(
                            question, lang, deepl_key, verbose
                        )
                        
                        if traduction_ok and question_traduite != question_resolue:
                            parcours_detection.append("deepl")
                            
                            # Réessayer en mode IA avec la question traduite
                            if verbose:
                                print(f"[DEBUG] search: Nouvelle recherche IA avec '{question_traduite}'")
                            
                            resultats_trad_ia = rechercher(
                                question_traduite, base_path,
                                mode='ia', include_details=True, verbose=verbose, debug=False, model=model,
                                limit=limit, offset=offset
                            )
                            
                            nb_trad_ia = resultats_trad_ia.get('nb', 0)
                            parcours_detection.append(f"ia:{nb_trad_ia}")
                            
                            if verbose:
                                print(f"[DEBUG] search: 🤖 ia (après deepl): {nb_trad_ia} résultat(s)")
                            
                            if nb_trad_ia > 0:
                                resultats = resultats_trad_ia
                                question_resolue = question_traduite
                                indicateurs_routage = EMOJI_TRADUCTION
                                mode_effectif = 'ia (iadeepl)'
                            else:
                                # Garder les résultats même si 0
                                indicateurs_routage = EMOJI_TRADUCTION
                                question_resolue = question_traduite
                                mode_effectif = 'ia (iadeepl)'
                        else:
                            # Traduction échouée ou identique
                            if verbose:
                                print(f"[DEBUG] search: 🌐 Traduction DeepL échouée ou identique")
                            parcours_detection.append("deepl:échec")
                            mode_effectif = 'ia'
                    else:
                        # Pas de clé DeepL → indiquer dans le parcours
                        if verbose:
                            print(f"[DEBUG] search: ⚠️ Pas de clé DeepL, escalade impossible")
                        parcours_detection.append("(no deepl)")
                        mode_effectif = 'ia'
                else:
                    mode_effectif = 'ia'
        
        elif mode_detection == 'purstandard':
            # ═══════════════════════════════════════════════════════════
            # MODE PURSTANDARD : STANDARD PUR SANS AUCUN FALLBACK
            # ═══════════════════════════════════════════════════════════
            
            parcours_detection.append(f"purstandard:{0}")
            if verbose:
                print(f"[DEBUG] search: 🔎 Mode PURSTANDARD (standard sans fallback)...")
            
            resultats = rechercher(
                question_pour_recherche, base_path,
                mode='standard', include_details=True, verbose=verbose, debug=False,
                limit=limit, offset=offset
            )
            
            nb_resultats = resultats.get('nb', 0)
            parcours_detection[-1] = f"purstandard:{nb_resultats}"
            mode_effectif = 'purstandard'
            
            if verbose:
                print(f"[DEBUG] search: 🔎 purstandard: {nb_resultats} résultat(s) (pas de fallback)")
        
        else:
            # ═══════════════════════════════════════════════════════════
            # MODE STANDARD (avec escalades automatiques)
            # ═══════════════════════════════════════════════════════════
            
            # ÉTAPE 5.1 : Recherche STANDARD
            parcours_detection.append(f"standard:{0}")  # Placeholder
            if verbose:
                print(f"[DEBUG] search: 🔎 Tentative STANDARD...")
            
            resultats = rechercher(
                question_pour_recherche, base_path,
                mode='standard', include_details=True, verbose=verbose, debug=False,
                limit=limit, offset=offset
            )
            
            nb_resultats = resultats.get('nb', 0)
            parcours_detection[-1] = f"standard:{nb_resultats}"
            
            if verbose:
                print(f"[DEBUG] search: 🔎 standard: {nb_resultats} résultat(s)")
            
            # ÉTAPE 5.2 : Si 0 résultat → fallback IA
            if nb_resultats == 0:
                if verbose:
                    print(f"[DEBUG] search: 🔎 standard: 0 → 🤖 fallback IA")
                
                resultats_ia = rechercher(
                    question_pour_recherche, base_path,
                    mode='ia', include_details=True, verbose=verbose, debug=False, model=model,
                    limit=limit, offset=offset
                )
                
                nb_ia = resultats_ia.get('nb', 0)
                parcours_detection.append(f"ia:{nb_ia}")
                
                if verbose:
                    print(f"[DEBUG] search: 🤖 ia: {nb_ia} résultat(s)")
                
                if nb_ia > 0:
                    # IA a trouvé des résultats → standardia
                    resultats = resultats_ia
                    indicateurs_routage = EMOJI_IA
                    mode_effectif = 'ia (standardia)'
                else:
                    # Toujours 0 → garder les résultats IA mais noter le fallback
                    resultats = resultats_ia
                    indicateurs_routage = EMOJI_IA
                    mode_effectif = 'ia (standardia)'
                
                # ÉTAPE 5.3 : Si toujours 0 résultat ET langue != fr → fallback traduction DeepL
                if nb_ia == 0 and lang != 'fr':
                    if deepl_key:
                        if verbose:
                            print(f"[DEBUG] search: 🤖 ia: 0 → 🌐 fallback traduction DeepL")
                        
                        question_traduite, traduction_ok = _traduire_question_deepl(
                            question, lang, deepl_key, verbose
                        )
                        
                        if traduction_ok and question_traduite != question_resolue:
                            parcours_detection.append("deepl")
                            
                            # Réessayer avec la question traduite
                            if verbose:
                                print(f"[DEBUG] search: Nouvelle recherche avec '{question_traduite}'")
                            
                            # D'abord en mode standard
                            resultats_trad = rechercher(
                                question_traduite, base_path,
                                mode='standard', include_details=True, verbose=verbose, debug=False,
                                limit=limit, offset=offset
                            )
                            
                            nb_trad = resultats_trad.get('nb', 0)
                            parcours_detection.append(f"standard:{nb_trad}")
                            
                            if verbose:
                                print(f"[DEBUG] search: 🔎 standard (après deepl): {nb_trad} résultat(s)")
                            
                                
                            if nb_trad > 0:
                                # standarddeepl : traduction → standard OK
                                resultats = resultats_trad
                                question_resolue = question_traduite
                                indicateurs_routage = EMOJI_TRADUCTION
                                mode_effectif = 'standard (standarddeepl)'
                            else:
                                # Essayer en mode IA après traduction
                                resultats_trad_ia = rechercher(
                                    question_traduite, base_path,
                                    mode='ia', include_details=True, verbose=verbose, debug=False, model=model,
                                    limit=limit, offset=offset
                                )
                                
                                nb_trad_ia = resultats_trad_ia.get('nb', 0)
                                parcours_detection.append(f"ia:{nb_trad_ia}")
                                
                                if verbose:
                                    print(f"[DEBUG] search: 🤖 ia (après deepl): {nb_trad_ia} résultat(s)")
                                
                                if nb_trad_ia > 0:
                                    # iadeepl : traduction → IA OK
                                    resultats = resultats_trad_ia
                                    question_resolue = question_traduite
                                    indicateurs_routage = f"{EMOJI_IA}{EMOJI_TRADUCTION}"
                                    mode_effectif = 'ia (iadeepl)'
                                else:
                                    # Aucun résultat même après traduction
                                    indicateurs_routage = f"{EMOJI_IA}{EMOJI_TRADUCTION}"
                                    question_resolue = question_traduite
                                    mode_effectif = 'ia (iadeepl)'
                        else:
                            # Traduction échouée ou identique
                            if verbose:
                                print(f"[DEBUG] search: 🌐 Traduction DeepL échouée ou identique")
                            parcours_detection.append("deepl:échec")
                    else:
                        # Pas de clé DeepL → indiquer dans le parcours
                        if verbose:
                            print(f"[DEBUG] search: ⚠️ Pas de clé DeepL, escalade impossible")
                        parcours_detection.append("(no deepl)")
        
    except Exception as e:
        if verbose:
            print(f"[DEBUG] search: ERREUR trouve: {e}")
        elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        erreur = str(e)
        
        _log_recherche(
            question_originale=question,
            question_fr=question_resolue,
            base=base_name,
            mode=mode_effectif,
            nb_patients=0,
            temps_ms=elapsed_ms,
            pathologies=[],
            ages=[],
            residu='',
            filtres={},
            sql='',
            languesaisie=languesaisie,
            langueutilisee=langueutilisee,
            modulelangue=modulelangue,
            erreur=erreur,
            session_id=session_id,
            ip_utilisateur=ip_utilisateur,
            indicateurs_routage=indicateurs_routage
        )
        
        return {
            'erreur': erreur,
            'nb_patients': 0,
            'patients': [],
            'lang': lang,
            'response_lang': output_lang,
            'temps_ms': elapsed_ms,
            'indicateurs_routage': indicateurs_routage,
            'question_affichee': f"{question} {indicateurs_routage}".strip()
        }
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 6 : MISE À JOUR DU CHUTIER (MOTS NON RÉSOLUS)
    # ═══════════════════════════════════════════════════════════════
    
    if mots_non_resolus and lang != 'fr':
        _maj_chutier(lang, mots_non_resolus, verbose)
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 7 : TRADUIRE PATHOLOGIES DES PATIENTS
    # ═══════════════════════════════════════════════════════════════
    
    unit_year = get_unit_year(messages, output_lang)
    
    if output_lang != 'fr' and resultats.get('patients') and mapping_patho:
        for patient in resultats['patients']:
            if patient.get('pathologies'):
                patient['pathologies'] = traduire_pathologies_patient(
                    patient['pathologies'], mapping_patho, output_lang, verbose=False
                )
            if patient.get('oripathologies'):
                patient['oripathologies'] = traduire_pathologies_patient(
                    patient['oripathologies'], mapping_patho, output_lang, verbose=False
                )
            patient['unit_year'] = unit_year
    else:
        for patient in resultats.get('patients', []):
            patient['unit_year'] = unit_year
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 8 : CONSTRUIRE DESCRIPTION FILTRES ET TRADUIRE
    # ═══════════════════════════════════════════════════════════════
    
    description_filtres_fr = _construire_description_filtres(resultats)
    
    if output_lang != 'fr' and description_filtres_fr:
        description_filtres_traduite = traduire_description_filtres(
            description_filtres_fr, mapping_patho, output_lang, verbose
        )
    else:
        description_filtres_traduite = description_filtres_fr
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 9 : GÉNÉRER MESSAGE DANS LA LANGUE DE RÉPONSE
    # ═══════════════════════════════════════════════════════════════
    
    nb_patients = resultats.get('nb', 0)
    
    if nb_patients == 0:
        usage = 'final_none'
    elif nb_patients == 1:
        usage = 'final_exact'
    else:
        usage = 'final_multiple'
    
    message_traduit = get_message(
        messages, usage, output_lang, nb_patients, 
        description_filtres_traduite, verbose
    )
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 10 : CONSTRUIRE RÉSULTAT FINAL
    # ═══════════════════════════════════════════════════════════════
    
    elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)
    
    # Construire la question affichée avec emojis
    question_affichee = f"{question} {indicateurs_routage}".strip() if indicateurs_routage else question
    
    resultat_final = {
        # Métadonnées auteur/mode
        'auteur': resultats.get('auteur', 'cx'),
        'mode_detection': mode_effectif,
        'model': model,
        
        # Métadonnées linguistiques
        'lang': lang,
        'lang_detectee': lang,
        'response_lang': output_lang,
        'question_originale': question,
        'question_resolue': question_resolue if lang != 'fr' or question_resolue != question else None,
        'question_technique_fr': question_technique_fr,  # NOUVEAU V1.0.25 : Question envoyée à trouve.py
        'resolution_provider': modulelangue if lang != 'fr' else None,
        'mots_non_resolus': mots_non_resolus if mots_non_resolus else None,
        
        # NOUVEAUX CHAMPS V1.0.15 : Indicateurs de routage
        'indicateurs_routage': indicateurs_routage,
        'question_affichee': question_affichee,
        
        # NOUVEAU CHAMP V1.1.0 : Parcours de détection
        'parcours_detection': '→'.join(parcours_detection) if parcours_detection else mode_effectif,
        
        # Résultats
        'nb_patients': nb_patients,
        'nb_returned': len(resultats.get('patients', [])),
        'patients': resultats.get('patients', []),
        
        # Description et message
        'message': message_traduit,
        'description_filtres': description_filtres_traduite,
        'description_filtres_fr': description_filtres_fr,
        
        # Temps et métadonnées techniques
        'temps_ms': elapsed_ms,
        'unit_year': unit_year,
        
        # Détails de détection (si disponibles)
        'criteres_detectes': resultats.get('criteres_detectes', []),
        'portrait_scores': resultats.get('portrait_scores', None),  # PHOTOFIT V5.2
        'sql': resultats.get('sql', ''),
        'sql_params': resultats.get('sql_params', []),
        'json_detection': resultats.get('json_detection', {}),
        'filtres': resultats.get('filtres', {})
    }
    
    # Logging
    _log_recherche(
        question_originale=question,
        question_fr=question_resolue,
        base=base_name,
        mode=mode_effectif,
        nb_patients=nb_patients,
        temps_ms=elapsed_ms,
        pathologies=resultats.get('pathologies', []),
        ages=resultats.get('ages', []),
        residu=resultats.get('residu', ''),
        filtres=resultats.get('filtres', {}),
        sql=resultats.get('sql', ''),
        languesaisie=languesaisie,
        langueutilisee=langueutilisee,
        modulelangue=modulelangue,
        session_id=session_id,
        ip_utilisateur=ip_utilisateur,
        indicateurs_routage=indicateurs_routage
    )
    
    return resultat_final


# =============================================================================
# AFFICHAGE DES RÉSULTATS CLI
# =============================================================================

def _trouver_fichier(nom_fichier: str) -> Optional[Path]:
    """Cherche un fichier dans plusieurs répertoires possibles."""
    chemin = Path(nom_fichier)
    if chemin.exists():
        return chemin
    for rep in [TESTS_DIR, Path('tests'), SCRIPT_DIR / 'tests']:
        candidat = rep / chemin.name
        if candidat.exists():
            return candidat
    return None


def _traiter_fichier_batch(base_path: str, fichier_csv: str, mode_detection: str,
                           model: str, verbose: bool, api_key: str,
                           lang_cli: str = 'fr') -> int:
    """
    Traite un fichier CSV de questions en batch.
    Génère [nom_entrée]search.csv avec résumé transposé.
    
    Args:
        lang_cli: Langue spécifiée en CLI. Forcée pour toutes les questions sauf
                  si le CSV a une colonne 'lang' ET que lang_cli vaut 'auto'.
    """
    fichier_path = _trouver_fichier(fichier_csv)
    if not fichier_path:
        print(f"ERREUR : Fichier {fichier_csv} introuvable")
        print(f"  Chemins testés:")
        for c in [fichier_csv, str(TESTS_DIR / Path(fichier_csv).name)]:
            print(f"    - {os.path.abspath(c)}")
        return 0
    
    # Fichier de sortie
    module_name = Path(__pgm__).stem  # 'search'
    fichier_sortie = fichier_path.parent / f"{fichier_path.stem}{module_name}.csv"
    
    print(f"Fichier d'entrée : {fichier_path.resolve()}")
    print(f"Fichier de sortie: {fichier_sortie.resolve()}")
    print()
    
    try:
        with open(fichier_path, 'r', encoding='utf-8-sig') as f:
            lignes = [line for line in f if not line.strip().startswith('#')]
        
        # Récupérer les commentaires séparément
        commentaires = []
        with open(fichier_path, 'r', encoding='utf-8-sig') as f:
            for line in f:
                if line.strip().startswith('#'):
                    commentaires.append(line.strip())
                else:
                    break
        
        if not lignes:
            print("Fichier vide ou seulement des commentaires")
            return 0
        
        lignes_io = io.StringIO(''.join(lignes))
        reader = csv.DictReader(lignes_io, delimiter=';')
        
        questions = []
        for row in reader:
            question = row.get('question', '').strip()
            # Langue : CLI a priorité, sinon colonne CSV, sinon 'fr'
            if lang_cli != 'auto':
                lang = lang_cli
            else:
                lang = row.get('lang', 'fr').strip() or 'fr'
            # Extraire résultat et commentaire si présents
            _val_resultat = row.get('résultat', row.get('resultat', '')).strip()
            _val_commentaire = row.get('commentaire', '').strip()
            if question:
                questions.append({'question': question, 'lang': lang,
                                  'resultat': _val_resultat, 'commentaire': _val_commentaire})
        
        if not questions:
            print("Aucune question trouvée dans le fichier")
            return 0
        
        print(f"{len(questions)} question(s) à traiter")
        print("-" * 70)
        
        resultats = []
        
        for i, q in enumerate(questions, 1):
            resultat = search(
                question=q['question'],
                base_path=base_path,
                lang=q['lang'],
                mode_detection=mode_detection,
                model=model,
                verbose=verbose,
                api_key=api_key
            )
            
            nb = resultat.get('nb_patients', 0)
            temps = resultat.get('temps_ms', 0)
            indicateurs = resultat.get('indicateurs_routage', '')
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
            lignes_resume.append(f"→ {nb} patient(s) en {temps}ms")
            if indicateurs:
                lignes_resume.append(f"Routage: {indicateurs}")
            if resultat.get('erreur'):
                lignes_resume.append(f"⚠ {resultat['erreur']}")
            
            # Ajouter JSON détection et SQL
            json_det = resultat.get('json_detection', {})
            if json_det:
                json_compact = json.dumps(json_det, ensure_ascii=False, separators=(',', ':')).replace('\n', ' ').replace('\r', '')
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
                'question': q['question'],
                'resultat': q.get('resultat', ''),
                'commentaire': q.get('commentaire', ''),
                'lignes': lignes_resume
            })
            
            # Mini-résumé (toujours affiché)
            print(f"  [{i}/{len(questions)}] \"{q['question']}\"")
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
            print(f"        → {nb} patient(s) en {temps}ms")
            if indicateurs:
                print(f"        Routage: {indicateurs}")
            if resultat.get('sql'):
                print(f"        SQL: {resultat['sql']}")
            if resultat.get('erreur'):
                print(f"        ⚠ {resultat['erreur']}")
            print()
        
        # Écrire le fichier de sortie
        max_l = max((len(r['lignes']) for r in resultats), default=0)
        entete_l = ['question', 'résultat', 'commentaire'] + [f'L{i+1}' for i in range(max_l)]
        
        with open(fichier_sortie, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            for comm in commentaires:
                row_comm = [comm] + [''] * (len(entete_l) - 1)
                writer.writerow(row_comm)
            writer.writerow(entete_l)
            for res in resultats:
                row = [res['question'], res.get('resultat', ''), res.get('commentaire', '')] + res['lignes']
                while len(row) < len(entete_l):
                    row.append('')
                writer.writerow(row)
        
        print("-" * 70)
        print(f"✓ {len(questions)} lignes traitées → {os.path.abspath(str(fichier_sortie))}")
        
        return len(questions)
        
    except Exception as e:
        print(f"ERREUR lecture fichier: {e}")
        return 0


def _parser_arguments_flexibles(args: list) -> dict:
    """Parse les arguments CLI de manière flexible."""
    resultat = {
        'lang': 'fr',
        'response_lang': 'same',
        'mode': 'standard',
        'model': None,
        'limit': 100,
        'verbose': False,
        'api_key': None
    }
    
    langues = get_langues_valides()
    modeles = get_modeles_valides()
    modeles_actifs = [m for m, c in modeles.items() if c.get('actif', False) and m != 'standard']
    
    for arg in args:
        arg_lower = arg.lower()
        
        if arg.startswith('--lang='):
            resultat['lang'] = arg.split('=')[1].lower()
        elif arg.startswith('--mode='):
            resultat['mode'] = arg.split('=')[1].lower()
        elif arg.startswith('--model='):
            resultat['model'] = arg.split('=')[1].lower()
        elif arg.startswith('--response='):
            resultat['response_lang'] = arg.split('=')[1].lower()
        elif arg.startswith('--limit='):
            resultat['limit'] = int(arg.split('=')[1])
        elif arg.startswith('--api-key='):
            resultat['api_key'] = arg.split('=')[1]
        elif arg in ('-v', '--verbose'):
            resultat['verbose'] = True
        elif arg_lower in MODES_VALIDES:
            resultat['mode'] = arg_lower
        elif arg_lower in langues:
            resultat['lang'] = arg_lower
        elif arg_lower in modeles_actifs:
            resultat['model'] = arg_lower
            if resultat['mode'] == 'standard':
                resultat['mode'] = 'ia'
    
    return resultat


# =============================================================================
# POINT D'ENTRÉE CLI
# =============================================================================

def main():
    """Interface en ligne de commande."""
    print(f"╔════════════════════════════════════════════════════════════════")
    print(f"║ {__pgm__} V{__version__} - {__date__}")
    print(f"║ Recherche multilingue avec routage intelligent")
    print(f"║ Fallback: standard → IA {EMOJI_IA} → traduction DeepL {EMOJI_TRADUCTION}")
    print(f"╚════════════════════════════════════════════════════════════════")
    print()
    
    langues = get_langues_valides()
    modeles = get_modeles_valides()
    
    if len(sys.argv) < 2:
        modeles_actifs = [m for m, c in modeles.items() if c.get('actif', False) and m != 'standard']
        print("Usage:")
        print(f"  python {__pgm__} <base.db> \"question\" [options]")
        print(f"  python {__pgm__} \"question\" <base.db> [options]")
        print(f"  python {__pgm__} <base.db> <fichier.csv> [options]")
        print()
        print("Arguments (ordre libre) :")
        print(f"  *.db     Base SQLite (cherche aussi dans bases/)")
        print(f"  *.csv    Fichier batch (cherche aussi dans tests/)")
        print(f"  \"...\"    Question en langage naturel")
        print(f"  Mode   : {', '.join(MODES_VALIDES)}")
        if modeles_actifs:
            print(f"  Modèle : {', '.join(modeles_actifs)}")
        print()
        print("Options :")
        print("  --lang=XX        Langue (défaut: fr)")
        print("  --response=XX    Langue réponse: same (défaut) ou fr")
        print("  --mode=XX        Mode de détection")
        print("  --model=XX       Modèle IA")
        print("  --limit=N        Max résultats (défaut: 100)")
        print("  --api-key=XXX    Clé API DeepL")
        print("  -v, --verbose    Mode verbose")
        print("  -d, --debug      Mode debug")
        print()
        print("Exemples :")
        print(f"  python {__pgm__} base1964.db \"bruxisme\"")
        print(f"  python {__pgm__} \"bruxisme\" base1964.db")
        print(f"  python {__pgm__} base1964.db quentin.csv")
        print(f"  python {__pgm__} base1964.db \"Tiefbiss\" --lang=de")
        print(f"  python {__pgm__} base1964.db \"bruxisme\" ia")
        print()
        print(f"Langues supportées : {', '.join(langues)}")
        print(f"Module traduire    : {'✓ Disponible' if TRADUIRE_DISPONIBLE else '✗ Non disponible'}")
        print(f"Module trouve      : {'✓ Disponible' if TROUVE_DISPONIBLE else '✗ Non disponible'}")
        print(f"Logs               : {LOG_FILE}")
        return 1
    
    # ═══════════════════════════════════════════════════════════════
    # PARSER FLEXIBLE : détecter .db, .csv, question dans n'importe quel ordre
    # ═══════════════════════════════════════════════════════════════
    
    # Parser les options (--xxx, -v, modes, langues, modèles)
    options = _parser_arguments_flexibles(sys.argv[1:])
    
    # Construire les sets pour identifier les mots-clés connus
    modeles_actifs = {m.lower() for m, c in modeles.items() if c.get('actif', False) and m != 'standard'}
    modes_set = {m.lower() for m in MODES_VALIDES}
    langues_set = {l.lower() for l in langues}
    mots_cles = modeles_actifs | modes_set | langues_set
    
    # Détecter base (.db) et question/fichier parmi les args positionnels
    base_path = None
    question_or_file = None
    
    for arg in sys.argv[1:]:
        # Ignorer les options --xxx et -v/-d
        if arg.startswith('-'):
            continue
        # Ignorer les mots-clés reconnus (mode, langue, modèle)
        if arg.lower() in mots_cles:
            continue
        # Détecter la base
        if arg.endswith('.db'):
            base_path = arg
        # Détecter le fichier CSV ou la question
        elif question_or_file is None:
            question_or_file = arg
    
    lang = options['lang']
    response_lang = options['response_lang']
    mode_detection = options['mode']
    model = options['model']
    limit = options['limit']
    api_key = options['api_key']
    verbose = options['verbose']
    
    # Vérifications
    if not base_path:
        print("ERREUR : Aucune base .db spécifiée")
        print(f"  Exemple: python {__pgm__} base1964.db \"bruxisme\"")
        return 1
    
    if not question_or_file:
        print("ERREUR : Aucune question ou fichier CSV spécifié")
        print(f"  Exemple: python {__pgm__} base1964.db \"bruxisme\"")
        return 1
    
    # Résoudre le chemin de la base (.db → chercher dans bases/)
    if not os.path.exists(base_path):
        base_in_bases = os.path.join(RACINE, "bases", base_path)
        if os.path.exists(base_in_bases):
            base_path = base_in_bases
        else:
            print(f"ERREUR : Base {os.path.abspath(base_path)} introuvable")
            return 1
    
    print(f"Base: {os.path.abspath(base_path)}")
    
    # ═══════════════════════════════════════════════════════════════
    # MODE BATCH (CSV)
    # ═══════════════════════════════════════════════════════════════
    
    if question_or_file.endswith('.csv'):
        print(f"Mode: BATCH")
        if mode_detection != 'standard':
            print(f"Mode détection: {mode_detection}")
        if model:
            print(f"Modèle IA: {model}")
        print()
        
        nb_lignes = _traiter_fichier_batch(
            base_path, question_or_file, mode_detection, model, verbose, api_key,
            lang_cli=lang
        )
        return 0 if nb_lignes > 0 else 1
    
    # ═══════════════════════════════════════════════════════════════
    # MODE UNITAIRE (question)
    # ═══════════════════════════════════════════════════════════════
    
    else:
        question = question_or_file
        
        print(f"Question: {question}")
        if lang != 'fr':
            print(f"Langue: {lang}")
        print(f"Mode détection: {mode_detection}")
        if model:
            print(f"Modèle IA: {model}")
        print()
        
        resultats = search(
            question=question,
            base_path=base_path,
            lang=lang,
            mode_detection=mode_detection,
            model=model,
            verbose=verbose,
            response_lang=response_lang,
            limit=limit,
            api_key=api_key
        )
        
        print()
        print("═" * 70)
        print(f"Question affichée  : {resultats.get('question_affichee', question)}")
        if resultats.get('parcours_detection'):
            print(f"Parcours détection : {resultats['parcours_detection']}")
        if resultats.get('indicateurs_routage'):
            print(f"Routage            : {resultats['indicateurs_routage']}")
        print(f"Question originale : {resultats.get('question_originale', question)}")
        # TOUJOURS afficher la question technique FR envoyée à trouve.py
        question_tech = resultats.get('question_technique_fr', resultats.get('question_originale', question))
        print(f"Question tech FR   : {question_tech}")
        if resultats.get('question_resolue') and resultats.get('question_resolue') != question:
            print(f"Résolution via     : {resultats.get('resolution_provider', '?')}")
        if resultats.get('mots_non_resolus'):
            print(f"Mots non résolus   : {', '.join(resultats['mots_non_resolus'])}")
        print(f"Auteur             : {resultats.get('auteur', '?')}")
        print(f"Mode effectif      : {resultats.get('mode_detection', '?')}")
        print(f"Langue question    : {resultats.get('lang', '?')}")
        print(f"Langue réponse     : {resultats.get('response_lang', '?')}")
        print("═" * 70)
        print(f"Message: {resultats.get('message', '')}")
        print(f"Description: {resultats.get('description_filtres', '')}")
        print()
        
        if resultats.get('erreur'):
            print(f"ERREUR: {resultats['erreur']}")
            return 1
        
        if resultats.get('patients'):
            print(f"Patients ({len(resultats['patients'])} sur {resultats.get('nb_patients', 0)}):")
            unit = resultats.get('unit_year', 'ans')
            for i, p in enumerate(resultats['patients'][:10], 1):
                sexe = p.get('sexe', '?')
                age = int(p.get('age', 0))
                prenom = p.get('oriprenom', p.get('prenom', ''))
                nom = p.get('orinom', p.get('nom', ''))
                pathos = p.get('oripathologies', p.get('pathologies', ''))
                print(f"  {i}. {prenom} {nom}, {sexe}, {age} {unit} - {pathos}")
            
            if len(resultats['patients']) > 10:
                print(f"  ... et {len(resultats['patients']) - 10} autres")
        
        print()
        print(f"⏱️  Temps: {resultats.get('temps_ms', 0)}ms")
        print(f"📝 Log: {LOG_FILE}")
        
        return 0


if __name__ == "__main__":
    sys.exit(main())
