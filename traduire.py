# traduire.py V1.0.6 - 09/01/2026 20:30:29
__pgm__ = "traduire.py"
__version__ = "1.0.6"
__date__ = "09/01/2026 20:30:29"

"""
Module de traduction multilingue pour Kitview Search.

NOUVEAUTÉS v1.0.6 :
- FIX CRITIQUE : charger_glossaire() utilise maintenant _normaliser_pour_recherche()
  au lieu de standardise() pour préserver les caractères CJK (japonais, chinois, etc.)
  * standardise() utilisait NFD qui décomposait les hiragana (ぎ → き + dakuten)
  * Résultat : 歯ぎしり n'était pas trouvé dans le glossaire, seulement 歯
  * Maintenant : 歯ぎしり → bruxisme fonctionne correctement

NOUVEAUTÉS v1.0.5 :
- LANGUES DYNAMIQUES : La liste des langues est maintenant lue depuis commun.csv
  * Colonne 'langues' de refs/commun.csv
  * Plus de liste hardcodée dans le code
  * Fonction get_langues_glossaire() avec cache
  * Fallback vers liste par défaut si commun.csv introuvable
  * Cohérence garantie avec le reste du système KITVIEW

NOUVEAUTÉS v1.0.4 :
- FIX CRITIQUE : charger_glossaire() réécrit pour supporter le format MULTICOLONNE
  * Ancien format attendu : synonyme;original;langue (3 colonnes)
  * Nouveau format supporté : type;fr;en;de;es;it;ja;pt;pl;ro;th;ar;cn
  * Détection automatique de l'en-tête pour mapper les colonnes
  * Support des synonymes multiples séparés par virgule
  * Permet au glossaire de traduire 歯ぎしり → bruxisme SANS DeepL

NOUVEAUTÉS v1.0.3 :
- FIX RENDER : Logging détaillé des erreurs DeepL (type + message + clé API preview)
  * Visible dans les logs serveur et F12 via réponses JSON
  * Permet de diagnostiquer pourquoi DeepL échoue sur Render
- FALLBACK FR : Si DeepL échoue ET texte en script latin → retourne 'fr' au lieu de 'unknown'
  * Évite le message "Langue détectée: UNKNOWN" dans l'interface
  * Le français est la langue par défaut pour les textes latins sans pathologie détectée

NOUVEAUTÉS v1.0.16 :
- FIX BUG AMBIGUÏTÉ FR/EN : En cas d'ambiguïté glossaire (même score pour FR et EN),
  DeepL est maintenant utilisé pour trancher au lieu de préférer FR par défaut
- Affecte les termes techniques identiques en FR/EN (ex: "linguo-version")
- detecter_langue_glossaire() retourne maintenant un flag 'ambiguite' (6ème élément)
- detecter_langue() utilise DeepL pour trancher si ambiguïté détectée

NOUVEAUTÉS v1.3.0 :
- DÉTECTION UNICODE : Pré-filtre rapide pour scripts non-latins
  * Japonais : Hiragana (3040-309F), Katakana (30A0-30FF), Kanji (CJK)
  * Chinois : CJK Unifié (4E00-9FFF) sans kana
  * Thaï : Thai (0E00-0E7F)
  * Arabe : Arabic (0600-06FF)
  * Distinction JA/CN : présence de kana = japonais certain
- Nouvelle fonction : detecter_langue_unicode(texte, verbose) -> (langue, confiance, details)
- Support du japonais (ja) ajouté aux 12 langues

NOUVEAUTÉS v1.2.2 :
- Compatibilité COMPLÈTE avec suche.py :
  * traduire(texte, source_lang, target_lang, api_key, verbose) -> (texte, fournisseur)
  * detecter_langue(question, api_key, verbose) -> str
  * est_langue_native(lang) -> bool
  * get_fallback_langue(lang) -> str
  * LANGUES_NATIVES (alias de LANGUES_GLOSSAIRE)

NOUVEAUTÉS v1.2.1 :
- Correction du chargement glossaire dans detecter_langue()

NOUVEAUTÉS v1.2.0 :
- PRIORITÉ AU GLOSSAIRE : glossaire.csv utilisé en premier pour détection + traduction
- DeepL uniquement en FALLBACK si aucune pathologie trouvée dans le glossaire
- Timing détaillé en mode verbose (chaque étape chronométrée)
- Support langue imposée (évite détection si spécifiée)

ARCHITECTURE v1.3.0 :
0. [UNICODE] Pré-détection par caractères (rapide, scripts non-latins)
1. [GLOSSAIRE] Chercher des pathologies dans toutes les langues du glossaire
2. [GLOSSAIRE] Si trouvé → langue détectée + pathologies traduites en FR
3. [GLOSSAIRE] Traduire le résidu via le glossaire si possible
4. [DEEPL] Si aucune pathologie trouvée → DeepL traduit tout
5. [POST] Extraire les pathologies dans le texte FR final

LANGUES GÉRÉES PAR LE GLOSSAIRE :
fr, en, de, es, it, pt, pl, ro, th, ar, cn, ja (12 langues)

Usage en import :
    from traduire import charger_glossaire, traduire_question, detecter_langue_unicode
    glossaire = charger_glossaire('refs/glossaire.csv')
    question_fr, langue_detectee, pathologies = traduire_question(question, glossaire)

Usage CLI unitaire :
    python traduire.py "Schiene bei Frauen unter 30" [--verbose] [--debug]
    python traduire.py "歯列矯正の患者" [--verbose]  # Japonais

Usage CLI batch :
    python traduire.py testsmulticomplets.csv [--verbose] [--debug]
"""

import re
import csv
import argparse
import sys
import os
import time
import unicodedata
from pathlib import Path

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

# Import DeepL (optionnel)
try:
    import deepl
    DEEPL_DISPONIBLE = True
except ImportError:
    DEEPL_DISPONIBLE = False

# ============================================================================
# CHARGEMENT DYNAMIQUE DES LANGUES DEPUIS commun.csv
# ============================================================================

# Langues par défaut (fallback si commun.csv introuvable)
_LANGUES_DEFAUT = ['fr', 'en', 'de', 'es', 'it', 'pt', 'pl', 'ro', 'th', 'ar', 'cn', 'ja']

# Cache des langues chargées
_LANGUES_CACHE = None


def charger_langues_depuis_commun(commun_path=None, verbose=False):
    """
    Charge la liste des langues depuis la colonne 'langues' de commun.csv.
    
    V1.0.5 : Les langues ne sont plus hardcodées mais lues depuis commun.csv
    pour garantir la cohérence avec le reste du système.
    
    Args:
        commun_path: Chemin vers commun.csv (auto-détecté si None)
        verbose: Afficher les messages de debug
        
    Returns:
        list: Liste des codes langues ['fr', 'en', 'de', ...]
    """
    global _LANGUES_CACHE
    
    # Retourner le cache si déjà chargé
    if _LANGUES_CACHE is not None:
        return _LANGUES_CACHE
    
    # Chemins possibles pour commun.csv
    if commun_path is None:
        chemins = [
            Path(__file__).parent / "refs" / "commun.csv",
            Path("refs/commun.csv"),
            Path("c:/g/refs/commun.csv"),
            Path("/app/refs/commun.csv"),  # Render
        ]
    else:
        chemins = [Path(commun_path)]
    
    # Chercher le fichier
    fichier_trouve = None
    for chemin in chemins:
        if chemin.exists():
            fichier_trouve = chemin
            break
    
    if not fichier_trouve:
        if verbose:
            print(f"  [LANGUES] commun.csv non trouvé, utilisation des langues par défaut")
        _LANGUES_CACHE = _LANGUES_DEFAUT.copy()
        return _LANGUES_CACHE
    
    # Lire la colonne 'langues'
    langues = []
    try:
        for encodage in ['utf-8-sig', 'utf-8', 'windows-1252']:
            try:
                with open(fichier_trouve, 'r', encoding=encodage, newline='') as f:
                    reader = csv.reader(f, delimiter=';')
                    col_langues = None
                    
                    for row in reader:
                        if not row:
                            continue
                        
                        # Ignorer les commentaires
                        if (row[0] or '').strip().startswith('#'):
                            continue
                        
                        # Détecter l'en-tête
                        if col_langues is None:
                            for idx, col in enumerate(row):
                                if col.strip().lower() == 'langues':
                                    col_langues = idx
                                    break
                            continue
                        
                        # Extraire la langue de cette ligne
                        if col_langues is not None and col_langues < len(row):
                            lang = (row[col_langues] or '').strip().lower()
                            if lang and lang not in langues:
                                langues.append(lang)
                
                break  # Encodage trouvé
            except UnicodeDecodeError:
                continue
        
        if langues:
            if verbose:
                print(f"  [LANGUES] {len(langues)} langues chargées depuis {fichier_trouve}: {', '.join(langues)}")
            _LANGUES_CACHE = langues
            return langues
        else:
            if verbose:
                print(f"  [LANGUES] Colonne 'langues' vide dans commun.csv, utilisation des langues par défaut")
            _LANGUES_CACHE = _LANGUES_DEFAUT.copy()
            return _LANGUES_CACHE
            
    except Exception as e:
        if verbose:
            print(f"  [LANGUES] Erreur lecture commun.csv: {e}, utilisation des langues par défaut")
        _LANGUES_CACHE = _LANGUES_DEFAUT.copy()
        return _LANGUES_CACHE


def get_langues_glossaire():
    """
    Retourne la liste des langues supportées par le glossaire.
    Charge depuis commun.csv si pas encore fait.
    """
    return charger_langues_depuis_commun()


def reset_langues_cache():
    """Réinitialise le cache des langues (utile pour les tests)."""
    global _LANGUES_CACHE
    _LANGUES_CACHE = None


# Chargement initial des langues (lazy - sera fait au premier appel)
# Pour compatibilité, on garde LANGUES_GLOSSAIRE comme variable mais elle pointe vers la fonction
def _get_langues_glossaire_compat():
    """Wrapper pour compatibilité avec l'ancien code qui utilisait LANGUES_GLOSSAIRE."""
    return charger_langues_depuis_commun()

# LANGUES_GLOSSAIRE est maintenant une propriété dynamique
# Pour les imports directs, on garde une valeur par défaut qui sera mise à jour
LANGUES_GLOSSAIRE = _LANGUES_DEFAUT.copy()

# Alias pour compatibilité avec suche.py
LANGUES_NATIVES = LANGUES_GLOSSAIRE


def est_langue_native(lang):
    """
    Vérifie si une langue est supportée nativement par le glossaire.
    Fonction de compatibilité pour suche.py.
    """
    if not lang:
        return False
    langues = get_langues_glossaire()
    return lang.lower() in langues


def get_fallback_langue(lang):
    """
    Retourne une langue de fallback si la langue n'est pas native.
    Fonction de compatibilité pour suche.py.
    
    Stratégie :
    - Si langue native → retourne la même
    - Sinon → retourne 'en' (anglais comme lingua franca)
    """
    if not lang:
        return 'fr'
    langues = get_langues_glossaire()
    if lang.lower() in langues:
        return lang.lower()
    return 'en'

# Clé API DeepL
DEEPL_API_KEY = os.environ.get('DEEPL_API_KEY', '')


# ============================================================================
# DÉTECTION DE LANGUE PAR CARACTÈRES UNICODE
# ============================================================================

def detecter_langue_unicode(texte, verbose=False):
    """
    Détecte la langue d'un texte par analyse des caractères Unicode.
    
    Cette fonction est un pré-filtre rapide avant le glossaire/DeepL.
    Elle détecte les scripts non-latins avec haute confiance.
    
    Plages Unicode utilisées :
    - Japonais : Hiragana (3040-309F), Katakana (30A0-30FF)
    - Chinois  : CJK Unifié (4E00-9FFF) - partagé avec japonais
    - Thaï     : Thai (0E00-0E7F)
    - Arabe    : Arabic (0600-06FF), Arabic Extended (0750-077F)
    - Cyrillique : Cyrillic (0400-04FF) - pour futur support russe
    - Grec     : Greek (0370-03FF) - pour futur support grec
    
    Stratégie de distinction Japonais/Chinois :
    - Présence de Hiragana ou Katakana → Japonais (ces syllabaires sont exclusifs au japonais)
    - Uniquement des CJK sans kana → Chinois
    
    Returns:
        tuple: (langue_detectee, confiance, details)
            - langue_detectee: code langue ('ja', 'cn', 'th', 'ar', None)
            - confiance: float 0.0-1.0
            - details: dict avec compteurs par type de caractère
    """
    if not texte or not texte.strip():
        return None, 0.0, {}
    
    # Compteurs par type de caractère
    counts = {
        'hiragana': 0,      # Japonais uniquement
        'katakana': 0,      # Japonais uniquement
        'cjk': 0,           # Chinois/Japonais (kanji)
        'thai': 0,          # Thaï
        'arabic': 0,        # Arabe
        'cyrillic': 0,      # Russe (futur)
        'greek': 0,         # Grec (futur)
        'latin': 0,         # Langues européennes
        'other': 0          # Autres
    }
    
    total_alpha = 0
    
    for char in texte:
        code = ord(char)
        
        # Ignorer espaces et ponctuation
        if char.isspace() or not char.isalpha():
            continue
        
        total_alpha += 1
        
        # Hiragana (japonais exclusif)
        if 0x3040 <= code <= 0x309F:
            counts['hiragana'] += 1
        # Katakana (japonais exclusif)
        elif 0x30A0 <= code <= 0x30FF:
            counts['katakana'] += 1
        # Katakana étendu
        elif 0x31F0 <= code <= 0x31FF:
            counts['katakana'] += 1
        # CJK Unifié (kanji japonais / hanzi chinois)
        elif 0x4E00 <= code <= 0x9FFF:
            counts['cjk'] += 1
        # CJK Extension A
        elif 0x3400 <= code <= 0x4DBF:
            counts['cjk'] += 1
        # Thaï
        elif 0x0E00 <= code <= 0x0E7F:
            counts['thai'] += 1
        # Arabe
        elif 0x0600 <= code <= 0x06FF:
            counts['arabic'] += 1
        # Arabe étendu
        elif 0x0750 <= code <= 0x077F:
            counts['arabic'] += 1
        # Cyrillique
        elif 0x0400 <= code <= 0x04FF:
            counts['cyrillic'] += 1
        # Grec
        elif 0x0370 <= code <= 0x03FF:
            counts['greek'] += 1
        # Latin (inclut les accents)
        elif (0x0041 <= code <= 0x007A) or (0x00C0 <= code <= 0x024F):
            counts['latin'] += 1
        else:
            counts['other'] += 1
    
    if total_alpha == 0:
        return None, 0.0, counts
    
    # Calcul des ratios
    ratio_hiragana = counts['hiragana'] / total_alpha
    ratio_katakana = counts['katakana'] / total_alpha
    ratio_kana = ratio_hiragana + ratio_katakana
    ratio_cjk = counts['cjk'] / total_alpha
    ratio_thai = counts['thai'] / total_alpha
    ratio_arabic = counts['arabic'] / total_alpha
    ratio_cyrillic = counts['cyrillic'] / total_alpha
    ratio_latin = counts['latin'] / total_alpha
    
    # Décision avec seuils
    SEUIL_DETECTION = 0.15  # 15% minimum pour détecter
    
    # JAPONAIS : présence de kana = japonais certain
    if ratio_kana > 0.05 or (ratio_kana > 0 and ratio_cjk > 0):
        # Même quelques kana suffisent car ils sont exclusifs au japonais
        confiance = min(1.0, ratio_kana + ratio_cjk * 0.8)
        if verbose:
            print(f"  [UNICODE] Japonais détecté (kana={ratio_kana:.0%}, cjk={ratio_cjk:.0%}) → confiance={confiance:.0%}")
        return 'ja', confiance, counts
    
    # CHINOIS : CJK sans kana
    if ratio_cjk > SEUIL_DETECTION:
        confiance = min(1.0, ratio_cjk)
        if verbose:
            print(f"  [UNICODE] Chinois détecté (cjk={ratio_cjk:.0%}) → confiance={confiance:.0%}")
        return 'cn', confiance, counts
    
    # THAÏ
    if ratio_thai > SEUIL_DETECTION:
        confiance = min(1.0, ratio_thai)
        if verbose:
            print(f"  [UNICODE] Thaï détecté ({ratio_thai:.0%}) → confiance={confiance:.0%}")
        return 'th', confiance, counts
    
    # ARABE
    if ratio_arabic > SEUIL_DETECTION:
        confiance = min(1.0, ratio_arabic)
        if verbose:
            print(f"  [UNICODE] Arabe détecté ({ratio_arabic:.0%}) → confiance={confiance:.0%}")
        return 'ar', confiance, counts
    
    # CYRILLIQUE (futur support russe)
    if ratio_cyrillic > SEUIL_DETECTION:
        confiance = min(1.0, ratio_cyrillic)
        if verbose:
            print(f"  [UNICODE] Cyrillique détecté ({ratio_cyrillic:.0%}) → confiance={confiance:.0%}")
        return 'ru', confiance, counts  # Russe par défaut pour cyrillique
    
    # Pas de script non-latin détecté
    if verbose and ratio_latin > 0.5:
        print(f"  [UNICODE] Script latin ({ratio_latin:.0%}) - détection par glossaire/DeepL nécessaire")
    
    return None, 0.0, counts


def _normaliser_pour_recherche(texte):
    """
    Normalise un texte pour la recherche dans le glossaire.
    
    V1.0.6 : CRITIQUE - Utilisé aussi dans charger_glossaire() pour préserver
    les caractères CJK lors du chargement du glossaire.
    
    V1.0.4 : Préserve les caractères CJK (Japonais, Chinois, Thaï, Arabe)
    - Ne pas utiliser NFD qui décompose les caractères japonais (ex: ぎ → き + dakuten)
    - Minuscules uniquement pour les caractères latins
    - Espaces normalisés
    """
    if not texte:
        return ""
    
    resultat = []
    for char in texte:
        code = ord(char)
        
        # Caractères CJK et autres scripts non-latins : préserver tels quels
        if (0x3040 <= code <= 0x30FF or   # Hiragana + Katakana
            0x4E00 <= code <= 0x9FFF or   # CJK Unifié
            0x3400 <= code <= 0x4DBF or   # CJK Extension A
            0x0E00 <= code <= 0x0E7F or   # Thaï
            0x0600 <= code <= 0x06FF or   # Arabe
            0x0750 <= code <= 0x077F):    # Arabe étendu
            resultat.append(char)
        elif char.isspace():
            resultat.append(' ')
        elif char.isalpha():
            # Caractères latins : minuscules + suppression accents
            char_lower = char.lower()
            # Normalisation NFC pour les accents latins
            char_norm = unicodedata.normalize('NFD', char_lower)
            char_sans_accent = ''.join(c for c in char_norm if unicodedata.category(c) != 'Mn')
            resultat.append(char_sans_accent)
        elif char.isdigit():
            resultat.append(char)
        elif char in '.,;:!?-_\'':
            resultat.append(' ')  # Remplacer ponctuation par espace
        # Ignorer les autres caractères
    
    # Nettoyer les espaces multiples
    texte_resultat = ''.join(resultat)
    texte_resultat = re.sub(r'\s+', ' ', texte_resultat)
    return texte_resultat.strip()


def charger_glossaire(csv_path, verbose=False, debug=False):
    """
    Charge le glossaire multilingue depuis glossaire.csv.
    
    V1.0.5 : Utilise get_langues_glossaire() pour obtenir la liste des langues
    depuis commun.csv au lieu d'une liste hardcodée.
    
    V1.0.4 : Support du format MULTICOLONNE (utilisé par KITVIEW)
    Format CSV attendu : type;fr;en;de;es;it;ja;pt;pl;ro;th;ar;cn
    Où chaque colonne contient les traductions dans la langue correspondante.
    
    Returns:
        dict: Glossaire organisé par langue {lang: {synonyme_norm: {original, synonyme_brut, nb_mots}}}
    """
    t0 = time.time()
    
    # Charger les langues depuis commun.csv
    langues_supportees = get_langues_glossaire()
    
    glossaire = {lang: {} for lang in langues_supportees}
    
    if not os.path.exists(csv_path):
        print(f"[ERREUR] Fichier introuvable: {os.path.abspath(csv_path)}")
        return glossaire
    
    encodages = ['utf-8-sig', 'utf-8', 'windows-1252', 'iso-8859-1']
    stats = {lang: 0 for lang in langues_supportees}
    doublons = 0
    
    # Mapping des indices de colonnes vers les codes langues
    # Format attendu : type;fr;en;de;es;it;ja;pt;pl;ro;th;ar;cn
    COL_MAPPING = {
        1: 'fr',   # Colonne 1 = français (référence)
        2: 'en',   # Colonne 2 = anglais
        3: 'de',   # Colonne 3 = allemand
        4: 'es',   # Colonne 4 = espagnol
        5: 'it',   # Colonne 5 = italien
        6: 'ja',   # Colonne 6 = japonais
        7: 'pt',   # Colonne 7 = portugais
        8: 'pl',   # Colonne 8 = polonais
        9: 'ro',   # Colonne 9 = roumain
        10: 'th',  # Colonne 10 = thaï
        11: 'ar',  # Colonne 11 = arabe
        12: 'cn',  # Colonne 12 = chinois
    }
    
    for encodage in encodages:
        try:
            with open(csv_path, 'r', encoding=encodage, newline='') as f:
                reader = csv.reader(f, delimiter=';')
                ligne_num = 0
                header_detected = False
                col_mapping = COL_MAPPING.copy()
                
                for row in reader:
                    ligne_num += 1
                    
                    # Ignorer lignes vides et commentaires
                    if not row or (row[0] or '').strip().startswith('#'):
                        continue
                    
                    # Détecter l'en-tête et ajuster le mapping
                    first_cell = (row[0] or '').strip().lower()
                    if not header_detected and (first_cell in ['type', 'original', 'standard', 'synonyme'] or 'fr' in [c.lower().strip() for c in row[:5]]):
                        # C'est une ligne d'en-tête, construire le mapping dynamique
                        header_detected = True
                        col_mapping = {}
                        for idx, col_name in enumerate(row):
                            col_name_clean = col_name.strip().lower()
                            if col_name_clean in langues_supportees:
                                col_mapping[idx] = col_name_clean
                        if debug:
                            print(f"  [DEBUG] En-tête détecté: {col_mapping}")
                        continue
                    
                    # Ignorer les lignes trop courtes
                    if len(row) < 3:
                        continue
                    
                    # Extraire le terme français (référence) - généralement colonne 1 ou celle nommée 'fr'
                    terme_fr = None
                    idx_fr = None
                    for idx, lang in col_mapping.items():
                        if lang == 'fr' and idx < len(row):
                            terme_fr = (row[idx] or '').strip()
                            idx_fr = idx
                            break
                    
                    # Fallback : colonne 1 si pas de mapping explicite
                    if not terme_fr and len(row) > 1:
                        terme_fr = (row[1] or '').strip()
                        idx_fr = 1
                    
                    if not terme_fr:
                        continue
                    
                    # Traiter chaque colonne de langue
                    for idx, lang in col_mapping.items():
                        if idx >= len(row) or idx == idx_fr:
                            continue
                        
                        terme_lang = (row[idx] or '').strip()
                        if not terme_lang:
                            continue
                        
                        # Gérer les synonymes multiples séparés par virgule
                        variantes = [v.strip() for v in terme_lang.split(',') if v.strip()]
                        
                        for variante in variantes:
                            # V1.0.6 : Utiliser _normaliser_pour_recherche() au lieu de standardise()
                            # pour préserver les caractères CJK (japonais, chinois, etc.)
                            synonyme_norm = _normaliser_pour_recherche(variante)
                            if not synonyme_norm:
                                continue
                            
                            nb_mots = len(synonyme_norm.split()) if ' ' in synonyme_norm else 1
                            
                            # Vérifier doublon
                            if synonyme_norm in glossaire[lang]:
                                doublons += 1
                                if debug:
                                    print(f"  [DEBUG] Doublon ignoré: '{variante}' ({lang})")
                                continue
                            
                            glossaire[lang][synonyme_norm] = {
                                'original': terme_fr,  # Le terme français de référence
                                'synonyme_brut': variante,
                                'nb_mots': nb_mots
                            }
                            stats[lang] += 1
                    
                    # Ajouter aussi les synonymes français (pour auto-détection FR)
                    if terme_fr and idx_fr is not None:
                        synonyme_norm_fr = _normaliser_pour_recherche(terme_fr)
                        if synonyme_norm_fr and synonyme_norm_fr not in glossaire['fr']:
                            glossaire['fr'][synonyme_norm_fr] = {
                                'original': terme_fr,
                                'synonyme_brut': terme_fr,
                                'nb_mots': len(synonyme_norm_fr.split()) if ' ' in synonyme_norm_fr else 1
                            }
                            stats['fr'] += 1
            
            break  # Encodage trouvé, sortir de la boucle
            
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    elapsed = int((time.time() - t0) * 1000)
    
    if verbose or debug:
        total = sum(stats.values())
        print(f"  [TIMING] Glossaire: {total} synonymes chargés en {elapsed} ms")
        if doublons > 0:
            print(f"  [INFO] {doublons} doublon(s) ignoré(s)")
        if debug:
            for lang in langues_supportees:
                if stats[lang] > 0:
                    print(f"    - {lang}: {stats[lang]}")
    
    return glossaire


def detecter_pathologies_langue(texte, glossaire_langue, verbose=False, debug=False):
    """
    Détecte les pathologies dans un texte pour UNE langue donnée.
    Utilise l'algorithme n-grammes (termes les plus longs d'abord).
    
    V1.0.4 : Utilise _normaliser_pour_recherche() au lieu de standardise()
    pour préserver les caractères japonais/chinois.
    
    Pour les langues CJK (sans espaces), utilise la recherche par sous-chaîne.
    
    Returns:
        tuple: (pathologies_fr, positions, residu)
            - pathologies_fr: Liste des termes français (original)
            - positions: Dict {position_debut: pathologie_fr} pour reconstruction
            - residu: Texte avec les pathologies retirées
    """
    texte_norm = _normaliser_pour_recherche(texte)
    
    # Détecter si c'est une langue CJK (sans espaces)
    # En comptant les caractères CJK vs latins
    nb_cjk = sum(1 for c in texte_norm if ord(c) > 0x2E00)
    nb_latin = sum(1 for c in texte_norm if c.isascii() and c.isalpha())
    est_cjk = nb_cjk > nb_latin
    
    if est_cjk:
        # Mode CJK : recherche par sous-chaîne (pas de split par espaces)
        return _detecter_pathologies_cjk(texte_norm, glossaire_langue, verbose, debug)
    else:
        # Mode latin : recherche par mots
        return _detecter_pathologies_latin(texte_norm, glossaire_langue, verbose, debug)


def _detecter_pathologies_cjk(texte_norm, glossaire_langue, verbose=False, debug=False):
    """
    Détection pour langues CJK (japonais, chinois) : recherche par sous-chaîne.
    """
    pathologies_fr = []
    positions_utilisees = []  # Liste de (debut, fin)
    originals_vus = set()
    
    # Trier par longueur décroissante (termes les plus longs d'abord)
    synonymes_tries = sorted(
        glossaire_langue.items(),
        key=lambda x: len(x[0]),
        reverse=True
    )
    
    for synonyme_norm, info in synonymes_tries:
        # Normaliser le synonyme aussi
        synonyme_norm_clean = _normaliser_pour_recherche(synonyme_norm)
        if not synonyme_norm_clean:
            continue
        
        # Chercher dans le texte
        pos = 0
        while True:
            idx = texte_norm.find(synonyme_norm_clean, pos)
            if idx == -1:
                break
            
            fin = idx + len(synonyme_norm_clean)
            
            # Vérifier chevauchement avec positions déjà utilisées
            chevauchement = False
            for (d, f) in positions_utilisees:
                if not (fin <= d or idx >= f):
                    chevauchement = True
                    break
            
            if not chevauchement:
                original = info['original']
                if original not in originals_vus:
                    originals_vus.add(original)
                    pathologies_fr.append(original)
                    positions_utilisees.append((idx, fin))
                    if debug:
                        print(f"    [MATCH CJK] '{synonyme_norm_clean}' → '{original}' (pos {idx})")
            
            pos = idx + 1
    
    # Calculer le résidu (parties non matchées)
    positions_utilisees.sort()
    residu_parts = []
    last_end = 0
    for (d, f) in positions_utilisees:
        if d > last_end:
            residu_parts.append(texte_norm[last_end:d])
        last_end = f
    if last_end < len(texte_norm):
        residu_parts.append(texte_norm[last_end:])
    
    residu = ''.join(residu_parts).strip()
    
    return pathologies_fr, {i: p for i, (p, _) in enumerate(zip(pathologies_fr, positions_utilisees))}, residu


def _detecter_pathologies_latin(texte_norm, glossaire_langue, verbose=False, debug=False):
    """
    Détection pour langues latines : recherche par mots séparés par espaces.
    """
    mots_texte = texte_norm.split()
    
    # Trier par nombre de mots décroissant
    synonymes_tries = sorted(
        glossaire_langue.items(),
        key=lambda x: x[1]['nb_mots'],
        reverse=True
    )
    
    pathologies_fr = []
    positions = {}
    mots_utilises = [False] * len(mots_texte)
    originals_vus = set()
    
    for synonyme_norm, info in synonymes_tries:
        # Normaliser le synonyme
        synonyme_norm_clean = _normaliser_pour_recherche(synonyme_norm)
        mots_synonyme = synonyme_norm_clean.split()
        nb_mots_syn = len(mots_synonyme)
        
        if nb_mots_syn == 0:
            continue
        
        # Chercher le synonyme dans le texte
        for i in range(len(mots_texte) - nb_mots_syn + 1):
            # Vérifier si tous les mots correspondent et ne sont pas utilisés
            match = True
            for j, mot_syn in enumerate(mots_synonyme):
                if mots_texte[i + j] != mot_syn or mots_utilises[i + j]:
                    match = False
                    break
            
            if match:
                original = info['original']
                
                # Dédoublonnage
                if original in originals_vus:
                    continue
                
                originals_vus.add(original)
                pathologies_fr.append(original)
                positions[i] = original
                
                # Marquer les mots comme utilisés
                for j in range(nb_mots_syn):
                    mots_utilises[i + j] = True
                
                if debug:
                    print(f"    [MATCH] '{synonyme_norm_clean}' → '{original}' (pos {i})")
                
                break  # Passer au synonyme suivant
    
    # Calculer le résidu
    mots_restants = [mot for i, mot in enumerate(mots_texte) if not mots_utilises[i]]
    residu = ' '.join(mots_restants)
    
    return pathologies_fr, positions, residu


def detecter_langue_glossaire(texte, glossaire, verbose=False, debug=False):
    """
    Détecte la langue en cherchant des pathologies dans TOUTES les langues.
    
    Returns:
        tuple: (langue, pathologies_fr, positions, residu, score, ambiguite)
            - ambiguite: True si plusieurs langues ont le même score
            ou (None, [], {}, texte, 0, False) si rien trouvé
    """
    t0 = time.time()
    
    langues_supportees = get_langues_glossaire()
    
    if verbose:
        print(f"  [GLOSSAIRE] Recherche dans {len(langues_supportees)} langues...")
    
    meilleur_score = 0
    meilleure_langue = None
    meilleures_pathos = []
    meilleures_positions = {}
    meilleur_residu = texte
    langues_candidates = []
    
    for langue in langues_supportees:
        glossaire_langue = glossaire.get(langue, {})
        if not glossaire_langue:
            continue
        
        pathologies, positions, residu = detecter_pathologies_langue(
            texte, glossaire_langue, verbose=False, debug=debug
        )
        
        score = len(pathologies)
        
        if score > 0:
            langues_candidates.append((langue, score, pathologies))
            
            if score > meilleur_score:
                meilleur_score = score
                meilleure_langue = langue
                meilleures_pathos = pathologies
                meilleures_positions = positions
                meilleur_residu = residu
    
    elapsed = int((time.time() - t0) * 1000)
    
    # Vérifier les ambiguïtés
    ambiguite = False
    if meilleur_score > 0:
        langues_meme_score = [l for l, s, _ in langues_candidates if s == meilleur_score]
        
        if len(langues_meme_score) > 1:
            ambiguite = True  # SIGNAL D'AMBIGUÏTÉ pour detecter_langue()
            if verbose:
                print(f"  [GLOSSAIRE] Ambiguïté: {langues_meme_score} (score={meilleur_score}) - {elapsed} ms")
            # En cas d'ambiguïté, on préfère dans l'ordre: fr, en, de, es...
            # MAIS on signale l'ambiguïté pour que detecter_langue() puisse utiliser DeepL
            for lang_pref in langues_supportees:
                if lang_pref in langues_meme_score:
                    meilleure_langue = lang_pref
                    # Recalculer pour cette langue
                    meilleures_pathos, meilleures_positions, meilleur_residu = detecter_pathologies_langue(
                        texte, glossaire.get(lang_pref, {}), verbose=False, debug=debug
                    )
                    break
            if verbose:
                print(f"  [GLOSSAIRE] → Choix provisoire: {meilleure_langue} (ambiguïté signalée)")
        else:
            if verbose:
                print(f"  [GLOSSAIRE] Langue détectée: {meilleure_langue} ({meilleur_score} patho) - {elapsed} ms")
    else:
        if verbose:
            print(f"  [GLOSSAIRE] Aucune pathologie trouvée - {elapsed} ms")
    
    return meilleure_langue, meilleures_pathos, meilleures_positions, meilleur_residu, meilleur_score, ambiguite


def deepl_traduire(texte, source_lang=None, verbose=False, debug=False):
    """
    Traduit un texte vers le français via DeepL (FALLBACK).
    
    Returns:
        tuple: (texte_traduit_fr, langue_detectee, temps_ms)
    """
    t0 = time.time()
    
    if not texte or not texte.strip():
        return texte, 'unknown', 0
    
    if not DEEPL_DISPONIBLE:
        if verbose:
            print("  [DEEPL] ✗ Module non installé")
        return texte, 'unknown', 0
    
    if not DEEPL_API_KEY:
        if verbose:
            print("  [DEEPL] ✗ Clé API non configurée")
        return texte, 'unknown', 0
    
    try:
        translator = deepl.Translator(DEEPL_API_KEY)
        
        kwargs = {'target_lang': 'FR'}
        if source_lang and source_lang.lower() not in ['auto', 'unknown', '']:
            kwargs['source_lang'] = source_lang.upper()
            if verbose:
                print(f"  [DEEPL] Traduction {source_lang.upper()} → FR...")
        else:
            if verbose:
                print(f"  [DEEPL] Traduction (auto) → FR...")
        
        result = translator.translate_text(texte, **kwargs)
        
        langue_detectee = result.detected_source_lang.lower()
        texte_traduit = result.text
        
        elapsed = int((time.time() - t0) * 1000)
        
        if verbose:
            print(f"  [DEEPL] ✓ Langue: {langue_detectee} - {elapsed} ms")
        
        if debug:
            print(f"  [DEBUG] '{texte}' → '{texte_traduit}'")
        
        return texte_traduit, langue_detectee, elapsed
        
    except Exception as e:
        elapsed = int((time.time() - t0) * 1000)
        # V1.0.3 : Logging détaillé pour diagnostic (visible en F12)
        error_type = type(e).__name__
        error_msg = str(e)
        print(f"  [DEEPL] ✗ ERREUR {error_type}: {error_msg} - {elapsed} ms")
        # Afficher les premiers caractères de la clé pour debug (sans exposer toute la clé)
        key_preview = DEEPL_API_KEY[:8] + "..." if DEEPL_API_KEY else "(vide)"
        print(f"  [DEEPL] Clé API: {key_preview}, Longueur: {len(DEEPL_API_KEY) if DEEPL_API_KEY else 0}")
        return texte, 'unknown', elapsed


def traduire_question(question, glossaire, langue_source=None, verbose=False, debug=False):
    """
    Traduit une question vers le français.
    
    STRATÉGIE v1.3.0 (avec détection Unicode) :
    0. [NOUVEAU] Pré-détection Unicode pour scripts non-latins (ja, cn, th, ar)
    1. Si langue_source imposée → chercher dans cette langue du glossaire
    2. Sinon → chercher dans TOUTES les langues du glossaire
    3. Si pathologies trouvées → traduction via glossaire + DeepL pour résidu
    4. Si rien trouvé → DeepL traduit tout (fallback)
    5. Post-traitement : extraire pathologies dans le texte FR final
    
    Returns:
        tuple: (question_fr, langue_detectee, pathologies_extraites)
    """
    t0_total = time.time()
    
    if verbose:
        print(f"\n  ╔══ TRADUCTION ══════════════════════════════════════")
        print(f"  ║ Question: '{question}'")
        if langue_source and langue_source.lower() not in ['auto', '']:
            print(f"  ║ Langue imposée: {langue_source}")
        print(f"  ╚═════════════════════════════════════════════════════")
    
    # ÉTAPE 0 : Pré-détection Unicode (pour scripts non-latins)
    langue_unicode = None
    if not langue_source or langue_source.lower() in ['auto', '']:
        langue_unicode, confiance_unicode, _ = detecter_langue_unicode(question, verbose=verbose)
        if langue_unicode and confiance_unicode >= 0.5:
            # Haute confiance Unicode → utiliser comme indice pour le glossaire
            if verbose:
                print(f"  [UNICODE] Pré-détection: {langue_unicode} (confiance={confiance_unicode:.0%})")
    
    # ÉTAPE 1 : Chercher dans le glossaire
    if langue_source and langue_source.lower() not in ['auto', 'unknown', '']:
        # Langue imposée → chercher uniquement dans cette langue
        langue_imposee = langue_source.lower()
        glossaire_langue = glossaire.get(langue_imposee, {})
        
        if glossaire_langue:
            pathologies, positions, residu = detecter_pathologies_langue(
                question, glossaire_langue, verbose=verbose, debug=debug
            )
            if pathologies:
                langue_detectee = langue_imposee
                score = len(pathologies)
                if verbose:
                    print(f"  [GLOSSAIRE] {score} pathologie(s) trouvée(s) en {langue_imposee}")
            else:
                langue_detectee = None
                score = 0
        else:
            langue_detectee = None
            pathologies = []
            positions = {}
            residu = question
            score = 0
    elif langue_unicode and langue_unicode in glossaire:
        # Unicode a détecté une langue → chercher d'abord dans cette langue
        glossaire_langue = glossaire.get(langue_unicode, {})
        pathologies, positions, residu = detecter_pathologies_langue(
            question, glossaire_langue, verbose=verbose, debug=debug
        )
        if pathologies:
            langue_detectee = langue_unicode
            score = len(pathologies)
            if verbose:
                print(f"  [GLOSSAIRE] {score} pathologie(s) en {langue_unicode} (via Unicode)")
        else:
            # Pas de pathologies dans la langue Unicode → chercher partout
            langue_detectee, pathologies, positions, residu, score, _ = detecter_langue_glossaire(
                question, glossaire, verbose=verbose, debug=debug
            )
            # Si toujours rien mais Unicode avait trouvé quelque chose, garder la langue Unicode
            if not langue_detectee and langue_unicode:
                langue_detectee = langue_unicode
    else:
        # Auto-détection → chercher dans toutes les langues
        langue_detectee, pathologies, positions, residu, score, _ = detecter_langue_glossaire(
            question, glossaire, verbose=verbose, debug=debug
        )
    
    # ÉTAPE 2 : Traitement selon résultat glossaire
    if langue_detectee and score > 0:
        # Pathologies trouvées via glossaire
        if langue_detectee == 'fr':
            # Déjà en français
            if verbose:
                print(f"  [RÉSULTAT] Question déjà en français")
            elapsed_total = int((time.time() - t0_total) * 1000)
            if verbose:
                print(f"  [TOTAL] {elapsed_total} ms")
            return question, 'fr', pathologies
        
        # Langue étrangère : traduire le résidu
        if residu.strip():
            if verbose:
                print(f"  [RÉSIDU] À traduire: '{residu}'")
            residu_fr, _, _ = deepl_traduire(residu, source_lang=langue_detectee, verbose=verbose, debug=debug)
        else:
            residu_fr = ''
        
        # Reconstruire la question FR
        # On met les pathologies dans l'ordre naturel avec le résidu
        if residu_fr.strip():
            # Insérer les pathologies à leurs positions relatives
            question_fr = residu_fr
            # Ajouter les pathologies de façon lisible
            pathos_str = ' '.join(pathologies)
            # Heuristique : si résidu commence par verbe/pronom, mettre pathos à la fin
            premiers_mots = residu_fr.lower().split()[:2]
            mots_debut = ['je', 'tu', 'il', 'elle', 'nous', 'vous', 'ils', 'elles', 
                         'qui', 'quel', 'quelle', 'quels', 'quelles', 'combien',
                         'trouve', 'cherche', 'montre', 'affiche', 'récupère']
            if premiers_mots and premiers_mots[0] in mots_debut:
                question_fr = f"{residu_fr} {pathos_str}"
            else:
                question_fr = f"{pathos_str} {residu_fr}"
        else:
            question_fr = ' '.join(pathologies)
        
        if verbose:
            print(f"  [RÉSULTAT] '{question_fr}'")
            print(f"  [PATHOS] {pathologies}")
        
        elapsed_total = int((time.time() - t0_total) * 1000)
        if verbose:
            print(f"  [TOTAL] {elapsed_total} ms")
        
        return question_fr, langue_detectee, pathologies
    
    # ÉTAPE 3 : Fallback DeepL (aucune pathologie trouvée)
    if verbose:
        print(f"  [FALLBACK] DeepL pour traduction complète")
    
    question_fr, langue_deepl, temps_deepl = deepl_traduire(
        question, 
        source_lang=langue_source if langue_source and langue_source.lower() not in ['auto', ''] else None,
        verbose=verbose, 
        debug=debug
    )
    
    # Post-traitement : extraire pathologies dans le texte FR traduit
    pathologies_fr = []
    glossaire_fr = glossaire.get('fr', {})
    if glossaire_fr:
        pathologies_fr, _, _ = detecter_pathologies_langue(
            question_fr, glossaire_fr, verbose=False, debug=debug
        )
        if verbose and pathologies_fr:
            print(f"  [POST] Pathologies FR détectées: {pathologies_fr}")
    
    elapsed_total = int((time.time() - t0_total) * 1000)
    
    if verbose:
        print(f"  [RÉSULTAT] '{question_fr}' (via DeepL)")
        print(f"  [TOTAL] {elapsed_total} ms")
    
    return question_fr, langue_deepl, pathologies_fr


# ============================================================================
# FONCTIONS LEGACY (compatibilité avec teste.py)
# ============================================================================

def detecter_langue(question, api_key=None, verbose=False):
    """
    Fonction de compatibilité pour suche.py ET teste.py.
    
    Signatures acceptées :
    - detecter_langue(question, api_key, verbose)  # suche.py
    - detecter_langue(question, glossaire, verbose, debug)  # teste.py (glossaire=None)
    
    Stratégie de détection (ordre de priorité) :
    1. [UNICODE] Détection par caractères (rapide, haute confiance pour scripts non-latins)
    2. [GLOSSAIRE] Détection par pathologies médicales connues
    3. [DEEPL] Fallback via API DeepL
    
    Returns:
        str: Code langue détecté ('en', 'de', 'fr', 'ja', 'cn', 'th', 'ar', etc.) ou 'unknown'
    """
    # ÉTAPE 1 : Détection Unicode (pré-filtre rapide)
    langue_unicode, confiance, _ = detecter_langue_unicode(question, verbose=verbose)
    
    if langue_unicode and confiance >= 0.3:
        # Haute confiance : on fait confiance à Unicode
        if verbose:
            print(f"  [DÉTECTION] Unicode → {langue_unicode} (confiance={confiance:.0%})")
        return langue_unicode
    
    # ÉTAPE 2 : Charger le glossaire
    glossaire = None
    chemins = [
        Path(__file__).parent / "refs" / "glossaire.csv",
        Path("c:/g/refs/glossaire.csv"),
        Path("refs/glossaire.csv"),
    ]
    for chemin in chemins:
        if chemin.exists():
            glossaire = charger_glossaire(str(chemin), verbose=False, debug=False)
            break
    if not glossaire:
        glossaire = {lang: {} for lang in get_langues_glossaire()}
    
    # ÉTAPE 3 : Détection par glossaire (pathologies médicales)
    langue_glossaire, _, _, _, score, ambiguite = detecter_langue_glossaire(question, glossaire, verbose=verbose, debug=False)
    
    if langue_glossaire:
        # NOUVEAU : En cas d'ambiguïté, utiliser DeepL pour trancher
        if ambiguite:
            if verbose:
                print(f"  [DÉTECTION] Glossaire → {langue_glossaire} (score={score}) MAIS ambiguïté détectée")
                print(f"  [DÉTECTION] Utilisation de DeepL pour trancher...")
            _, langue_deepl, _ = deepl_traduire(question, verbose=verbose, debug=False)
            if langue_deepl and langue_deepl != 'unknown':
                if verbose:
                    print(f"  [DÉTECTION] DeepL tranche l'ambiguïté → {langue_deepl}")
                return langue_deepl
            # Si DeepL échoue, on garde le choix glossaire
            if verbose:
                print(f"  [DÉTECTION] DeepL échec, on garde → {langue_glossaire}")
        else:
            if verbose:
                print(f"  [DÉTECTION] Glossaire → {langue_glossaire} (score={score})")
        return langue_glossaire
    
    # ÉTAPE 4 : Si Unicode a trouvé quelque chose avec confiance faible, l'utiliser
    if langue_unicode and confiance > 0:
        if verbose:
            print(f"  [DÉTECTION] Unicode (confiance faible) → {langue_unicode}")
        return langue_unicode
    
    # ÉTAPE 5 : Fallback DeepL
    _, langue_deepl, _ = deepl_traduire(question, verbose=verbose, debug=False)
    if langue_deepl != 'unknown':
        if verbose:
            print(f"  [DÉTECTION] DeepL → {langue_deepl}")
        return langue_deepl
    
    # V1.0.3 : FALLBACK FR pour scripts latins quand DeepL échoue
    # Si Unicode n'a détecté aucun script non-latin → c'est probablement du français ou une langue européenne
    if langue_unicode is None:
        if verbose:
            print(f"  [DÉTECTION] Fallback FR (script latin, DeepL indisponible)")
        return 'fr'
    
    return 'unknown'


def traduire(texte, source_lang, target_lang='fr', api_key=None, verbose=False):
    """
    Fonction de compatibilité pour suche.py.
    
    Signature attendue par suche.py :
        traduire(texte, source_lang, target_lang, api_key, verbose) -> (texte_traduit, fournisseur)
    
    Args:
        texte: Texte à traduire
        source_lang: Langue source ('auto', 'en', 'de', 'tr', etc.)
        target_lang: Langue cible (défaut 'fr')
        api_key: Clé API DeepL (non utilisée, on utilise la variable d'environnement)
        verbose: Mode verbose
        
    Returns:
        tuple: (texte_traduit, fournisseur) où fournisseur = 'glossaire', 'deepl' ou 'none'
    """
    # Charger le glossaire si nécessaire
    glossaire = None
    chemins = [
        Path(__file__).parent / "refs" / "glossaire.csv",
        Path("c:/g/refs/glossaire.csv"),
        Path("refs/glossaire.csv"),
    ]
    for chemin in chemins:
        if chemin.exists():
            glossaire = charger_glossaire(str(chemin), verbose=False, debug=False)
            break
    if not glossaire:
        glossaire = {lang: {} for lang in get_langues_glossaire()}
    
    # Si target n'est pas français, on doit utiliser DeepL directement
    if target_lang.lower() != 'fr':
        texte_traduit, langue_detectee, temps = deepl_traduire(
            texte, source_lang=source_lang, verbose=verbose, debug=False
        )
        fournisseur = 'deepl' if langue_detectee != 'unknown' else 'none'
        return texte_traduit, fournisseur
    
    # Traduction vers le français via notre système
    question_fr, langue_detectee, pathologies = traduire_question(
        texte, glossaire, 
        langue_source=source_lang if source_lang and source_lang.lower() not in ['auto', ''] else None,
        verbose=verbose, debug=False
    )
    
    # Déterminer le fournisseur
    if pathologies:
        fournisseur = 'glossaire'
    elif question_fr != texte:
        fournisseur = 'deepl'
    else:
        fournisseur = 'none'
    
    return question_fr, fournisseur


# ============================================================================
# TRAITEMENT BATCH
# ============================================================================

def traiter_fichier_batch(fichier_entree, glossaire, verbose=False, debug=False):
    """Traite un fichier batch CSV."""
    t0 = time.time()
    
    if 'in.csv' in fichier_entree:
        fichier_sortie = fichier_entree.replace('in.csv', 'out.csv')
    else:
        base, ext = os.path.splitext(fichier_entree)
        fichier_sortie = base + '_out' + ext
    
    print(f"Fichier d'entrée  : {os.path.abspath(fichier_entree)}")
    print(f"Fichier de sortie : {os.path.abspath(fichier_sortie)}")
    print()
    
    lignes_entree = []
    commentaires = []
    format_detecte = None
    header_row = None
    
    for encodage in ['utf-8-sig', 'utf-8', 'windows-1252']:
        try:
            with open(fichier_entree, 'r', encoding=encodage, newline='') as f:
                reader = csv.reader(f, delimiter=';')
                for row in reader:
                    if not row:
                        continue
                    if (row[0] or '').strip().startswith('#'):
                        commentaires.append(row)
                        continue
                    
                    col0 = (row[0] or '').strip().lower()
                    if header_row is None and ('langue' in col0 or 'question' in col0):
                        header_row = row
                        if col0 == 'langue' or (len(row) > 1 and 'question' in (row[1] or '').lower()):
                            format_detecte = 'langue_question'
                        else:
                            format_detecte = 'question_seule'
                        continue
                    
                    lignes_entree.append(row)
            break
        except UnicodeDecodeError:
            continue
    
    if format_detecte is None and lignes_entree:
        first_col = (lignes_entree[0][0] or '').strip().lower()
        if first_col in ['auto'] + get_langues_glossaire():
            format_detecte = 'langue_question'
        else:
            format_detecte = 'question_seule'
    
    print(f"Format            : {format_detecte}")
    print(f"Lignes à traiter  : {len(lignes_entree)}")
    print("-" * 70)
    
    resultats = []
    
    for i, row in enumerate(lignes_entree):
        if format_detecte == 'langue_question':
            langue_demandee = (row[0] or '').strip()
            question = (row[1] or '').strip() if len(row) > 1 else ''
        else:
            langue_demandee = 'Auto'
            question = (row[0] or '').strip()
        
        if not question:
            continue
        
        langue_source = None
        if langue_demandee.lower() not in ['auto', '']:
            langue_source = langue_demandee
        
        question_fr, langue_detectee, pathologies = traduire_question(
            question, glossaire, 
            langue_source=langue_source,
            verbose=verbose, debug=debug
        )
        
        resultats.append({
            'langue_demandee': langue_demandee,
            'question': question,
            'langue_detectee': langue_detectee,
            'question_fr': question_fr,
            'pathologies': ', '.join(pathologies) if pathologies else ''
        })
        
        if verbose:
            q_short = question[:40] + '...' if len(question) > 40 else question
            fr_short = question_fr[:40] + '...' if len(question_fr) > 40 else question_fr
            print(f"  {i+1}. [{langue_detectee}] {q_short}")
            print(f"       → {fr_short}")
    
    print("-" * 70)
    
    with open(fichier_sortie, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        
        for comm in commentaires:
            writer.writerow(comm)
        
        writer.writerow(['langue_demandee', 'question', 'langue_detectee', 'question_fr', 'pathologies'])
        
        for res in resultats:
            writer.writerow([
                res['langue_demandee'],
                res['question'], 
                res['langue_detectee'], 
                res['question_fr'],
                res['pathologies']
            ])
    
    elapsed_total = int((time.time() - t0) * 1000)
    avg = elapsed_total // len(resultats) if resultats else 0
    print(f"✓ {len(resultats)} lignes → {os.path.abspath(fichier_sortie)}")
    print(f"  Temps: {elapsed_total} ms ({avg} ms/ligne)")
    
    return len(resultats), fichier_sortie


def main():
    """Point d'entrée CLI."""
    print(f"╔════════════════════════════════════════════════════════════════")
    print(f"║ {__pgm__} V{__version__} - {__date__}")
    print(f"║ Traduction multilingue - GLOSSAIRE prioritaire, DeepL fallback")
    print(f"╚════════════════════════════════════════════════════════════════")
    print()
    
    parser = argparse.ArgumentParser(
        description="Traduit une question vers le français avec gestion des termes médicaux"
    )
    parser.add_argument('question', help='Question à traduire OU fichier .csv')
    parser.add_argument('--verbose', action='store_true', help='Affichage avec timing')
    parser.add_argument('--debug', action='store_true', help='Affichage complet')
    parser.add_argument('--csv', default='refs/glossaire.csv', help='Chemin vers glossaire.csv')
    
    args = parser.parse_args()
    
    csv_path = args.csv
    if not os.path.exists(csv_path):
        chemins_alternatifs = [
            Path(__file__).parent / "refs" / "glossaire.csv",
            Path("c:/g/refs/glossaire.csv"),
            Path("refs/glossaire.csv"),
        ]
        for chemin in chemins_alternatifs:
            if chemin.exists():
                csv_path = str(chemin)
                break
    
    print(f"Fichier glossaire: {os.path.abspath(csv_path)}")
    
    if DEEPL_DISPONIBLE and DEEPL_API_KEY:
        print(f"DeepL: ✓ Disponible (fallback)")
    elif DEEPL_DISPONIBLE:
        print(f"DeepL: ⚠ Clé API manquante")
    else:
        print(f"DeepL: ✗ Non installé")
    print()
    
    glossaire = charger_glossaire(csv_path, verbose=args.verbose, debug=args.debug)
    
    total_synonymes = sum(len(g) for g in glossaire.values())
    if total_synonymes == 0:
        print("[ERREUR] Glossaire vide")
        return 1
    
    print()
    
    est_fichier_batch = args.question.endswith('.csv')
    
    if est_fichier_batch:
        print(f"Mode BATCH")
        print("-" * 70)
        
        fichier_batch = Path(args.question)
        if not fichier_batch.exists():
            for rep in [Path('.'), Path('tests'), Path('c:/g/tests')]:
                candidat = rep / fichier_batch.name
                if candidat.exists():
                    fichier_batch = candidat
                    break
        
        if not fichier_batch.exists():
            print(f"[ERREUR] Fichier non trouvé: {args.question}")
            return 1
        
        nb_lignes, _ = traiter_fichier_batch(
            str(fichier_batch), glossaire, 
            verbose=args.verbose, debug=args.debug
        )
        return 0 if nb_lignes > 0 else 1
    
    else:
        print(f"Question: \"{args.question}\"")
        print()
        
        question_fr, langue, pathologies = traduire_question(
            args.question, glossaire,
            langue_source=None,
            verbose=args.verbose, debug=args.debug
        )
        
        print()
        print("═" * 70)
        print("RÉSULTAT")
        print("═" * 70)
        print(f"Langue détectée   : {langue}")
        print(f"Question FR       : {question_fr}")
        if pathologies:
            print(f"Pathologies       : {', '.join(pathologies)}")
        else:
            print(f"Pathologies       : (aucune)")
        
        return 0


if __name__ == '__main__':
    sys.exit(main())
