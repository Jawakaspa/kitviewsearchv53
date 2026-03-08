# traduis.py V1.0.11 - 26/12/2025 20:09:20
__pgm__ = "traduis.py"
__version__ = "1.0.11"
__date__ = "26/12/2025 20:09:20"

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║ traduis.py                                                                  ║
# ║ Gestion centralisée des traductions via glossaire.csv                       ║
# ║                                                                             ║
# ║ Modes d'utilisation :                                                       ║
# ║   python traduis.py                    → Vérifie et complète le glossaire   ║
# ║   python traduis.py "phrase"           → Traduit une phrase                 ║
# ║   python traduis.py fichier.csv        → Traduit un fichier CSV             ║
# ║   python traduis.py --only ja "phrase" → Traduit seulement vers japonais    ║
# ║   python traduis.py -r "phrase"        → Reverse: traduit vers le français  ║
# ║   python traduis.py -t fichier.csv     → Mode test (5 premières lignes)     ║
# ║   python traduis.py -h                 → Affiche l'aide                     ║
# ║                                                                             ║
# ║ Le glossaire est le référentiel central de toutes les traductions.          ║
# ╚════════════════════════════════════════════════════════════════════════════╝

import csv
import sys
import os
import json
import time
import argparse
from datetime import datetime
from pathlib import Path

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

# Chemins par défaut (relatifs au script)
CHEMIN_GLOSSAIRE = "refs/glossaire.csv"
CHEMIN_COMMUN = "refs/commun.csv"
FICHIER_LAST_TEST = ".traduis_last_test"

# Délai de sécurité pour le mode test (en secondes)
DELAI_SECURITE_TEST = 5 * 60  # 5 minutes

# Mapping codes langue internes → codes DeepL
CODES_DEEPL = {
    "fr": "FR",
    "en": "EN-GB",
    "de": "DE",
    "es": "ES",
    "it": "IT",
    "pt": "PT-PT",
    "pl": "PL",
    "ro": "RO",
    "ja": "JA",
    "ar": "AR",
    "cn": "ZH-HANS",
    "th": "TH"
}

# ══════════════════════════════════════════════════════════════════════════════
# STATISTIQUES
# ══════════════════════════════════════════════════════════════════════════════

class Stats:
    """Collecte les statistiques de traduction."""
    
    def __init__(self):
        self.termes_glossaire = 0
        self.termes_nouveaux = 0
        self.api_deepl = 0
        self.api_mymemory = 0
        self.api_libretranslate = 0
        self.caracteres_traduits = 0
        self.erreurs = []
    
    def afficher(self):
        """Affiche les statistiques."""
        print()
        print("=" * 70)
        print("STATISTIQUES DE TRADUCTION")
        print("=" * 70)
        print(f"  Termes depuis glossaire : {self.termes_glossaire}")
        print(f"  Termes nouveaux traduits : {self.termes_nouveaux}")
        print(f"  API DeepL : {self.api_deepl}")
        print(f"  API MyMemory : {self.api_mymemory}")
        print(f"  API LibreTranslate : {self.api_libretranslate}")
        print(f"  Caractères traduits : {self.caracteres_traduits}")
        if self.erreurs:
            print(f"  Erreurs : {len(self.erreurs)}")
            for err in self.erreurs[:5]:
                print(f"    - {err}")

# Instance globale
stats = Stats()

# ══════════════════════════════════════════════════════════════════════════════
# GESTION DU MODE TEST (SÉCURITÉ 5 MINUTES)
# ══════════════════════════════════════════════════════════════════════════════

def get_chemin_last_test() -> Path:
    """Retourne le chemin du fichier de timestamp du dernier test."""
    return Path(__file__).parent / FICHIER_LAST_TEST


def lire_dernier_test() -> float:
    """Lit le timestamp du dernier test. Retourne 0 si inexistant."""
    chemin = get_chemin_last_test()
    if chemin.exists():
        try:
            return float(chemin.read_text().strip())
        except:
            pass
    return 0


def ecrire_dernier_test():
    """Écrit le timestamp actuel comme dernier test."""
    chemin = get_chemin_last_test()
    chemin.write_text(str(time.time()))


def verifier_securite_test(force_test: bool) -> bool:
    """
    Vérifie si le mode test doit être forcé.
    
    Args:
        force_test: True si l'utilisateur a demandé -t
    
    Returns:
        True si le mode test doit être activé
    """
    if force_test:
        ecrire_dernier_test()
        return True
    
    dernier = lire_dernier_test()
    maintenant = time.time()
    
    if maintenant - dernier > DELAI_SECURITE_TEST:
        print("[SÉCURITÉ] Plus de 5 minutes sans test → Mode test forcé")
        print("           Utilisez -t explicitement pour confirmer les gros traitements")
        ecrire_dernier_test()
        return True
    
    return False

# ══════════════════════════════════════════════════════════════════════════════
# CHARGEMENT DES LANGUES
# ══════════════════════════════════════════════════════════════════════════════

def charger_langues(chemin: str = None) -> list:
    """
    Charge les langues actives depuis commun.csv.
    Retourne une liste de codes langue (ex: ['fr', 'en', 'ja', 'de']).
    
    IMPORTANT: Pas de fallback - si commun.csv est absent, erreur fatale.
    
    Note: Les lignes de commentaires (commençant par #) sont filtrées avant lecture.
    """
    if chemin is None:
        chemin = Path(__file__).parent / CHEMIN_COMMUN
    else:
        chemin = Path(chemin)
    
    chemin_absolu = chemin.resolve()
    
    if not chemin_absolu.exists():
        print(f"[ERREUR FATALE] Fichier non trouvé : {chemin_absolu}")
        print("                Le fichier commun.csv est obligatoire.")
        sys.exit(1)
    
    langues = []
    try:
        with open(chemin_absolu, 'r', encoding='utf-8-sig') as f:
            # Filtrer les lignes de commentaires AVANT DictReader
            lignes = []
            for ligne in f:
                ligne_strip = ligne.strip()
                # Garder les lignes non vides qui ne sont pas des commentaires
                if ligne_strip and not ligne_strip.startswith('#'):
                    lignes.append(ligne)
            
            if not lignes:
                print(f"[ERREUR FATALE] Fichier vide ou uniquement des commentaires : {chemin_absolu}")
                sys.exit(1)
            
            # Créer un DictReader à partir des lignes filtrées
            import io
            contenu_filtre = io.StringIO(''.join(lignes))
            reader = csv.DictReader(contenu_filtre, delimiter=';')
            
            for row in reader:
                lang = row.get('langues', '').strip()
                if lang:
                    # Éviter les doublons
                    if lang not in langues:
                        langues.append(lang)
                        
    except Exception as e:
        print(f"[ERREUR FATALE] Lecture de {chemin_absolu} : {e}")
        sys.exit(1)
    
    if not langues:
        print(f"[ERREUR FATALE] Aucune langue trouvée dans {chemin_absolu}")
        print("                Vérifiez que la colonne 'langues' existe et contient des valeurs.")
        sys.exit(1)
    
    return langues

# ══════════════════════════════════════════════════════════════════════════════
# GESTION DU GLOSSAIRE
# ══════════════════════════════════════════════════════════════════════════════

def charger_glossaire(chemin: str = None) -> dict:
    """
    Charge le glossaire en dictionnaire.
    
    Retourne:
        dict avec clé = terme français (minuscule), valeur = dict des traductions
        Exemple: {'avec': {'type': 'p', 'fr': 'avec', 'en': 'with', 'de': 'mit', ...}}
    
    Note: Les lignes de commentaires (commençant par #) sont filtrées avant lecture.
    """
    if chemin is None:
        chemin = Path(__file__).parent / CHEMIN_GLOSSAIRE
    else:
        chemin = Path(chemin)
    
    glossaire = {}
    chemin_absolu = chemin.resolve()
    
    if not chemin_absolu.exists():
        print(f"[INFO] Glossaire non trouvé, création : {chemin_absolu}")
        return glossaire
    
    try:
        with open(chemin_absolu, 'r', encoding='utf-8-sig') as f:
            # Filtrer les lignes de commentaires AVANT DictReader
            lignes = []
            for ligne in f:
                ligne_strip = ligne.strip()
                # Garder les lignes non vides qui ne sont pas des commentaires
                if ligne_strip and not ligne_strip.startswith('#'):
                    lignes.append(ligne)
            
            if not lignes:
                print(f"[INFO] Glossaire vide ou uniquement des commentaires : {chemin_absolu}")
                return glossaire
            
            # Créer un DictReader à partir des lignes filtrées
            import io
            contenu_filtre = io.StringIO(''.join(lignes))
            reader = csv.DictReader(contenu_filtre, delimiter=';')
            
            for row in reader:
                fr = row.get('fr', '').strip()
                if fr:
                    cle = fr.lower()
                    glossaire[cle] = {k: v.strip() for k, v in row.items()}
                    
    except Exception as e:
        print(f"[ERREUR] Lecture du glossaire : {e}")
    
    return glossaire


def sauvegarder_glossaire(glossaire: dict, chemin: str = None, langues: list = None):
    """
    Sauvegarde le glossaire dans le fichier CSV.
    Préserve les commentaires existants.
    
    GARDE-FOU : Ne sauvegarde pas si le nouveau glossaire est plus petit que l'existant.
    """
    if chemin is None:
        chemin = Path(__file__).parent / CHEMIN_GLOSSAIRE
    else:
        chemin = Path(chemin)
    
    chemin_absolu = chemin.resolve()
    chemin_absolu.parent.mkdir(parents=True, exist_ok=True)
    
    # GARDE-FOU : Compter les entrées existantes avant d'écraser
    nb_existant = 0
    if chemin_absolu.exists():
        try:
            with open(chemin_absolu, 'r', encoding='utf-8-sig') as f:
                for line in f:
                    line_strip = line.strip()
                    # Compter les lignes non vides, non commentaires, non en-tête
                    if line_strip and not line_strip.startswith('#') and not line_strip.startswith('type;'):
                        nb_existant += 1
        except:
            pass
    
    # GARDE-FOU : Refuser d'écraser si le nouveau est plus petit
    if nb_existant > 0 and len(glossaire) < nb_existant:
        print(f"[GARDE-FOU] Sauvegarde REFUSÉE : le glossaire actuel ({nb_existant} entrées) ")
        print(f"            serait remplacé par un plus petit ({len(glossaire)} entrées)")
        print(f"            Fichier préservé : {chemin_absolu}")
        return
    
    # Déterminer les colonnes
    if langues is None:
        langues = charger_langues()
    
    colonnes = ['type', 'fr'] + [l for l in langues if l != 'fr']
    
    # Lire les commentaires existants
    commentaires = []
    if chemin_absolu.exists():
        try:
            with open(chemin_absolu, 'r', encoding='utf-8-sig') as f:
                for line in f:
                    if line.strip().startswith('#'):
                        commentaires.append(line.rstrip('\n\r'))
                    elif line.strip() and not line.startswith('type;'):
                        break
        except:
            pass
    
    try:
        with open(chemin_absolu, 'w', encoding='utf-8-sig', newline='') as f:
            # Écrire l'en-tête
            f.write(';'.join(colonnes) + '\n')
            
            # Écrire les commentaires
            for comm in commentaires:
                f.write(comm + '\n')
            
            # Écrire les données triées par type puis par terme français
            ordre_types = {'p': 0, 'c': 1, 'o': 2, 'a': 3, 'z': 4, 'm': 5}
            
            def cle_tri(item):
                type_val = item[1].get('type', 'z')
                ordre = ordre_types.get(type_val, 10)  # Types date en dernier
                return (ordre, item[0])
            
            for cle, data in sorted(glossaire.items(), key=cle_tri):
                if data.get('type', '').startswith('#'):
                    continue
                ligne = [data.get(col, '') for col in colonnes]
                f.write(';'.join(ligne) + '\n')
        
        print(f"Glossaire sauvegardé : {chemin_absolu}")
        print(f"  -> {len(glossaire)} entrées")
        
    except Exception as e:
        print(f"[ERREUR] Sauvegarde du glossaire : {e}")

# ══════════════════════════════════════════════════════════════════════════════
# DÉTECTION DE LANGUE
# ══════════════════════════════════════════════════════════════════════════════

def detecter_langue(texte: str) -> str:
    """
    Détecte la langue d'un texte.
    Utilise l'API de détection ou des heuristiques simples.
    
    Returns:
        Code langue détecté (ex: 'en', 'de', 'ja') ou 'fr' par défaut
    """
    if not texte or not texte.strip():
        return 'fr'
    
    # Essayer avec langdetect si disponible
    try:
        from langdetect import detect
        lang = detect(texte)
        # Normaliser certains codes
        if lang == 'zh-cn' or lang == 'zh-tw':
            return 'cn'
        return lang
    except ImportError:
        pass
    except:
        pass
    
    # Heuristiques simples basées sur les caractères
    texte_lower = texte.lower()
    
    # Japonais (hiragana, katakana, kanji)
    if any('\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff' or '\u4e00' <= c <= '\u9fff' for c in texte):
        # Distinguer japonais et chinois
        if any('\u3040' <= c <= '\u309f' or '\u30a0' <= c <= '\u30ff' for c in texte):
            return 'ja'
        return 'cn'
    
    # Arabe
    if any('\u0600' <= c <= '\u06ff' for c in texte):
        return 'ar'
    
    # Thaï
    if any('\u0e00' <= c <= '\u0e7f' for c in texte):
        return 'th'
    
    # Mots clés pour langues européennes
    mots_anglais = {'the', 'is', 'are', 'was', 'were', 'have', 'has', 'with', 'for', 'and', 'that'}
    mots_allemands = {'der', 'die', 'das', 'und', 'ist', 'sind', 'mit', 'für', 'ein', 'eine'}
    mots_espagnols = {'el', 'la', 'los', 'las', 'es', 'son', 'con', 'para', 'que', 'una'}
    mots_italiens = {'il', 'la', 'le', 'è', 'sono', 'con', 'per', 'che', 'una', 'gli'}
    mots_portugais = {'o', 'a', 'os', 'as', 'é', 'são', 'com', 'para', 'que', 'uma'}
    
    mots = set(texte_lower.split())
    
    scores = {
        'en': len(mots & mots_anglais),
        'de': len(mots & mots_allemands),
        'es': len(mots & mots_espagnols),
        'it': len(mots & mots_italiens),
        'pt': len(mots & mots_portugais),
    }
    
    meilleur = max(scores, key=scores.get)
    if scores[meilleur] > 0:
        return meilleur
    
    # Par défaut français
    return 'fr'

# ══════════════════════════════════════════════════════════════════════════════
# SERVICES DE TRADUCTION
# ══════════════════════════════════════════════════════════════════════════════

def traduire_deepl(texte: str, langue_source: str, langue_cible: str) -> str:
    """Traduit via l'API DeepL."""
    try:
        import deepl
        api_key = os.environ.get('DEEPL_API_KEY')
        if not api_key:
            return None
        
        translator = deepl.Translator(api_key)
        code_source = CODES_DEEPL.get(langue_source, langue_source.upper())
        code_cible = CODES_DEEPL.get(langue_cible, langue_cible.upper())
        
        result = translator.translate_text(
            texte,
            source_lang=code_source,
            target_lang=code_cible
        )
        
        stats.api_deepl += 1
        stats.caracteres_traduits += len(texte)
        return result.text
        
    except ImportError:
        return None
    except Exception as e:
        stats.erreurs.append(f"DeepL: {e}")
        return None


def traduire_mymemory(texte: str, langue_source: str, langue_cible: str) -> str:
    """Traduit via l'API MyMemory (gratuit)."""
    try:
        import requests
        
        url = "https://api.mymemory.translated.net/get"
        params = {
            'q': texte,
            'langpair': f"{langue_source}|{langue_cible}"
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('responseStatus') == 200:
                traduction = data['responseData']['translatedText']
                stats.api_mymemory += 1
                stats.caracteres_traduits += len(texte)
                return traduction
        return None
        
    except Exception as e:
        stats.erreurs.append(f"MyMemory: {e}")
        return None


def traduire_libretranslate(texte: str, langue_source: str, langue_cible: str) -> str:
    """Traduit via LibreTranslate (fallback)."""
    try:
        import requests
        
        url = "https://libretranslate.com/translate"
        payload = {
            'q': texte,
            'source': langue_source,
            'target': langue_cible,
            'format': 'text'
        }
        
        response = requests.post(url, json=payload, timeout=10)
        if response.status_code == 200:
            data = response.json()
            traduction = data.get('translatedText')
            if traduction:
                stats.api_libretranslate += 1
                stats.caracteres_traduits += len(texte)
                return traduction
        return None
        
    except Exception as e:
        stats.erreurs.append(f"LibreTranslate: {e}")
        return None


def traduire_terme(terme: str, langue_cible: str, langue_source: str = 'fr', 
                   glossaire: dict = None) -> str:
    """
    Traduit un terme via le glossaire puis les APIs en cascade.
    
    Args:
        terme: Texte à traduire
        langue_cible: Code langue cible (en, de, ja, etc.)
        langue_source: Code langue source (défaut: fr)
        glossaire: Dictionnaire du glossaire (optionnel)
    
    Returns:
        Traduction ou None si échec
    """
    if not terme or langue_cible == langue_source:
        return terme
    
    # 1. Chercher dans le glossaire
    if glossaire:
        cle = terme.lower()
        if cle in glossaire:
            trad = glossaire[cle].get(langue_cible, '').strip()
            if trad:
                stats.termes_glossaire += 1
                return trad
    
    # 2. Cascade API : DeepL → MyMemory → LibreTranslate
    result = traduire_deepl(terme, langue_source, langue_cible)
    if result:
        return result
    
    result = traduire_mymemory(terme, langue_source, langue_cible)
    if result:
        return result
    
    result = traduire_libretranslate(terme, langue_source, langue_cible)
    if result:
        return result
    
    # Échec total
    stats.erreurs.append(f"Traduction échouée: '{terme}' ({langue_source}→{langue_cible})")
    return None

# ══════════════════════════════════════════════════════════════════════════════
# FONCTIONS PRINCIPALES
# ══════════════════════════════════════════════════════════════════════════════

def verifier_glossaire(glossaire: dict, langues: list) -> dict:
    """
    Vérifie et complète les traductions manquantes dans le glossaire.
    NE JAMAIS écraser une case déjà traduite.
    
    Args:
        glossaire: Dictionnaire du glossaire
        langues: Liste des codes langue
    
    Returns:
        Glossaire mis à jour
    """
    print()
    print("Vérification des traductions manquantes...")
    
    total = len(glossaire)
    traites = 0
    modifies = 0
    
    for cle, data in glossaire.items():
        traites += 1
        type_val = data.get('type', '')
        fr = data.get('fr', '')
        
        if not fr:
            continue
        
        # Type 'z' : ne pas traduire, copier la valeur fr
        if type_val == 'z':
            for lang in langues:
                if lang != 'fr' and not data.get(lang, '').strip():
                    data[lang] = fr
                    modifies += 1
            continue
        
        # Autres types : traduire si manquant (case vide)
        for lang in langues:
            if lang == 'fr':
                continue
            
            # IMPORTANT: Ne jamais écraser une case déjà traduite
            existing = data.get(lang, '').strip()
            if existing:
                stats.termes_glossaire += 1
                continue
            
            # Case vide → traduire
            traduction = traduire_terme(fr, lang, 'fr', glossaire)
            if traduction:
                data[lang] = traduction
                modifies += 1
                stats.termes_nouveaux += 1
                print(f"  [{traites}/{total}] {fr} → {lang}: {traduction}")
            else:
                print(f"  [{traites}/{total}] {fr} → {lang}: ÉCHEC")
        
        # Barre de progression simple
        if traites % 50 == 0:
            pct = int(traites * 100 / total)
            print(f"  Progression: {pct}% ({traites}/{total})")
    
    print(f"\nVérification terminée: {modifies} traductions ajoutées")
    return glossaire


def traduire_phrase_unique(phrase: str, langue_cible: str, glossaire: dict, 
                           langue_source: str = 'fr', reverse: bool = False) -> dict:
    """
    Traduit une phrase vers une langue cible unique.
    
    Args:
        phrase: Phrase à traduire
        langue_cible: Code langue cible
        glossaire: Dictionnaire du glossaire
        langue_source: Code langue source
        reverse: Si True, traduit vers le français
    
    Returns:
        Dict avec la traduction et métadonnées
    """
    phrase_clean = phrase.strip()
    
    # Mode reverse : traduire vers le français
    if reverse:
        if langue_source == 'fr':
            # Détection automatique
            langue_source = detecter_langue(phrase_clean)
        langue_cible = 'fr'
    
    # Si source = cible, retourner tel quel
    if langue_source == langue_cible:
        return {
            'langue_source': langue_source,
            'langue_cible': langue_cible,
            'original': phrase_clean,
            'traduction': phrase_clean,
            'source': 'copie'
        }
    
    # Chercher dans le glossaire
    cle = phrase_clean.lower()
    if cle in glossaire:
        trad = glossaire[cle].get(langue_cible, '').strip()
        if trad:
            stats.termes_glossaire += 1
            return {
                'langue_source': langue_source,
                'langue_cible': langue_cible,
                'original': phrase_clean,
                'traduction': trad,
                'source': 'glossaire'
            }
    
    # Traduire via API
    traduction = traduire_terme(phrase_clean, langue_cible, langue_source, glossaire)
    
    if traduction:
        # Ajouter au glossaire si traduction réussie
        if cle not in glossaire:
            glossaire[cle] = {
                'type': datetime.now().strftime('%d%m%Y'),
                'fr': phrase_clean if langue_source == 'fr' else '',
                langue_cible: traduction
            }
            if langue_source != 'fr':
                glossaire[cle][langue_source] = phrase_clean
            stats.termes_nouveaux += 1
        elif not glossaire[cle].get(langue_cible, '').strip():
            glossaire[cle][langue_cible] = traduction
    
    return {
        'langue_source': langue_source,
        'langue_cible': langue_cible,
        'original': phrase_clean,
        'traduction': traduction or phrase_clean,
        'source': 'api' if traduction else 'echec'
    }


def afficher_traduction(result: dict):
    """Affiche une traduction au format standard."""
    src = result['langue_source']
    tgt = result['langue_cible']
    orig = result['original']
    trad = result['traduction']
    print(f"{src}->{tgt} : {orig} -> {trad}")


def traduire_fichier(chemin_entree: str, glossaire: dict, langues: list,
                     langue_unique: str = None, reverse: bool = False,
                     langue_reverse: str = None, mode_test: bool = False) -> list:
    """
    Traduit un fichier CSV.
    
    Détection automatique du type de fichier :
    - syntags.csv (colonnes stdtag;canontag) : traduit stdtag, garde canontag tel quel
    - tagsadjs.csv (colonnes canon;...;synonymes;...;adjs) : traduit canon/synonymes/adjs, ajoute frcanon/fradjs
    - Autre : mode générique (cherche colonne 'fr' ou première colonne texte)
    
    Args:
        chemin_entree: Chemin du fichier CSV d'entrée
        glossaire: Dictionnaire du glossaire
        langues: Liste des codes langue
        langue_unique: Si spécifié, traduit vers cette langue uniquement
        reverse: Mode reverse (vers le français)
        langue_reverse: Langue source pour le reverse
        mode_test: Si True, limite à 5 lignes
    
    Returns:
        Liste des chemins des fichiers créés
    """
    chemin_in = Path(chemin_entree)
    
    # Si le fichier n'existe pas, essayer dans refs/ (sauf si déjà dans refs/)
    if not chemin_in.exists():
        chemin_str = str(chemin_entree)
        # Éviter la boucle : ne pas chercher refs/refs/...
        if not chemin_str.startswith('refs/') and not chemin_str.startswith('refs\\'):
            chemin_refs = Path(__file__).parent / 'refs' / chemin_in.name
            if chemin_refs.exists():
                print(f"[INFO] Fichier trouvé dans refs/ : {chemin_refs.resolve()}")
                chemin_in = chemin_refs
    
    chemin_in = chemin_in.resolve()
    
    if not chemin_in.exists():
        print(f"[ERREUR] Fichier non trouvé : {chemin_in}")
        return []
    
    print(f"\nTraduction du fichier : {chemin_in}")
    
    # Déterminer les langues cibles
    if reverse:
        langues_cibles = ['fr']
    elif langue_unique:
        langues_cibles = [langue_unique]
    else:
        langues_cibles = [l for l in langues if l != 'fr']
    
    fichiers_crees = []
    
    try:
        # Lire le fichier d'entrée (avec filtrage des commentaires)
        with open(chemin_in, 'r', encoding='utf-8-sig') as f:
            lignes_brutes = []
            commentaires = []
            for ligne in f:
                ligne_strip = ligne.strip()
                if ligne_strip.startswith('#'):
                    commentaires.append(ligne.rstrip('\n\r'))
                elif ligne_strip:
                    lignes_brutes.append(ligne)
            
            if not lignes_brutes:
                print(f"[ERREUR] Fichier vide ou uniquement des commentaires")
                return []
            
            import io
            contenu_filtre = io.StringIO(''.join(lignes_brutes))
            reader = csv.DictReader(contenu_filtre, delimiter=';')
            colonnes_entree = reader.fieldnames
            lignes = list(reader)
        
        # Détecter le type de fichier
        mode_fichier = detecter_mode_fichier(colonnes_entree)
        print(f"  Mode détecté : {mode_fichier}")
        
        # Mode test : limiter à 5 lignes
        if mode_test:
            lignes = lignes[:5]
            print(f"[MODE TEST] Limité à {len(lignes)} lignes")
        
        # Traiter chaque langue cible
        for lang_cible in langues_cibles:
            print(f"\n  Traduction vers : {lang_cible}")
            
            # Nom du fichier de sortie : préfixé par la langue SANS underscore
            nom_sortie = f"{lang_cible}{chemin_in.name}"
            chemin_out = chemin_in.parent / nom_sortie
            
            # Traiter selon le mode
            if mode_fichier == 'syntags':
                lignes_sortie, colonnes_sortie = traduire_mode_syntags(
                    lignes, lang_cible, glossaire, commentaires
                )
            elif mode_fichier == 'synadjs':
                lignes_sortie, colonnes_sortie = traduire_mode_synadjs(
                    lignes, lang_cible, glossaire, commentaires
                )
            elif mode_fichier == 'tagsadjs':
                lignes_sortie, colonnes_sortie = traduire_mode_tagsadjs(
                    lignes, colonnes_entree, lang_cible, glossaire, commentaires
                )
            else:
                lignes_sortie, colonnes_sortie = traduire_mode_generique(
                    lignes, colonnes_entree, lang_cible, glossaire, reverse, langue_reverse
                )
            
            # Écrire le fichier de sortie
            with open(chemin_out, 'w', encoding='utf-8-sig', newline='') as f:
                # Écrire les commentaires d'en-tête
                for comm in commentaires:
                    # Adapter le commentaire pour la nouvelle langue
                    if '# Langue:' in comm:
                        f.write(f"# Langue: {lang_cible}\n")
                    elif 'généré par' in comm.lower():
                        f.write(comm.replace(chemin_in.name, nom_sortie) + '\n')
                    else:
                        f.write(comm + '\n')
                
                writer = csv.DictWriter(f, fieldnames=colonnes_sortie, delimiter=';')
                writer.writeheader()
                writer.writerows(lignes_sortie)
            
            print(f"  Fichier créé : {chemin_out}")
            print(f"    -> {len(lignes_sortie)} lignes")
            fichiers_crees.append(str(chemin_out))
        
        return fichiers_crees
        
    except Exception as e:
        print(f"[ERREUR] Traitement du fichier : {e}")
        import traceback
        traceback.print_exc()
        return []


def detecter_mode_fichier(colonnes: list) -> str:
    """
    Détecte le mode de traduction selon les colonnes du fichier.
    
    Returns:
        'syntags' : fichier syntags.csv (stdtag;canontag)
        'synadjs' : fichier synadjs.csv (stdadj;canonadj;canontag)
        'tagsadjs' : fichier tagsadjs.csv (canon;type;...;synonymes;...;adjs)
        'generique' : autre fichier
    """
    if colonnes is None:
        return 'generique'
    
    cols = [c.lower() if c else '' for c in colonnes]
    
    # Mode synadjs : colonnes stdadj, canonadj, canontag
    if 'stdadj' in cols and 'canonadj' in cols:
        return 'synadjs'
    
    # Mode syntags : colonnes stdtag et canontag
    if 'stdtag' in cols and 'canontag' in cols:
        return 'syntags'
    
    # Mode tagsadjs : colonnes canon, synonymes, adjs
    if 'canon' in cols and 'synonymes' in cols:
        return 'tagsadjs'
    
    return 'generique'


def traduire_mode_syntags(lignes: list, lang_cible: str, glossaire: dict, 
                          commentaires: list) -> tuple:
    """
    Traduit un fichier syntags.csv.
    
    - Traduit la colonne stdtag vers la langue cible
    - Garde canontag tel quel (en français, pour la jointure)
    
    Returns:
        (lignes_sortie, colonnes_sortie)
    """
    colonnes_sortie = ['stdtag', 'canontag']
    lignes_sortie = []
    
    for row in lignes:
        stdtag_fr = row.get('stdtag', '').strip()
        canontag = row.get('canontag', '').strip()
        
        if not stdtag_fr:
            continue
        
        # Traduire stdtag
        stdtag_traduit = traduire_terme(stdtag_fr, lang_cible, 'fr', glossaire)
        if not stdtag_traduit:
            stdtag_traduit = stdtag_fr  # Fallback : garder l'original
        
        lignes_sortie.append({
            'stdtag': stdtag_traduit,
            'canontag': canontag  # Garder en français
        })
        
        # Afficher
        if stdtag_traduit != stdtag_fr:
            print(f"    fr->{lang_cible} : {stdtag_fr} -> {stdtag_traduit}")
        else:
            stats.termes_glossaire += 1
    
    return lignes_sortie, colonnes_sortie


def traduire_mode_synadjs(lignes: list, lang_cible: str, glossaire: dict, 
                          commentaires: list) -> tuple:
    """
    Traduit un fichier synadjs.csv.
    
    IMPORTANT: stdadj est sans accents (normalisé), canonadj a les accents.
    On utilise canonadj pour chercher la traduction (car le glossaire a les accents),
    puis on normalise le résultat (suppression des accents) pour stdadj.
    
    - Traduit via canonadj (avec accents) -> normalise pour stdadj (sans accents)
    - Garde canonadj et canontag tels quels (en français, pour la jointure)
    
    Returns:
        (lignes_sortie, colonnes_sortie)
    """
    colonnes_sortie = ['stdadj', 'canonadj', 'canontag']
    lignes_sortie = []
    
    for row in lignes:
        stdadj_fr = row.get('stdadj', '').strip()
        canonadj = row.get('canonadj', '').strip()
        canontag = row.get('canontag', '').strip()
        
        if not stdadj_fr:
            continue
        
        # Traduire via canonadj (qui a les accents) pour obtenir une traduction correcte
        # Exemple: canonadj="sévère" -> traduction="schwer" (correct)
        #          au lieu de stdadj="severe" -> traduction="ernst" (incorrect)
        if canonadj:
            canonadj_traduit = traduire_terme(canonadj, lang_cible, 'fr', glossaire)
        else:
            canonadj_traduit = None
        
        if canonadj_traduit:
            # Normaliser la traduction (supprimer les accents) pour stdadj
            stdadj_traduit = normaliser_texte(canonadj_traduit)
        else:
            # Fallback : garder l'original
            stdadj_traduit = stdadj_fr
        
        lignes_sortie.append({
            'stdadj': stdadj_traduit,
            'canonadj': canonadj,  # Garder en français
            'canontag': canontag   # Garder en français
        })
        
        # Afficher
        if stdadj_traduit != stdadj_fr:
            print(f"    fr->{lang_cible} : {stdadj_fr} ({canonadj}) -> {stdadj_traduit}")
        else:
            stats.termes_glossaire += 1
    
    return lignes_sortie, colonnes_sortie


def normaliser_texte(texte: str) -> str:
    """
    Normalise un texte en supprimant les accents et en mettant en minuscules.
    
    Exemple: "Sévère" -> "severe", "différé" -> "differe"
    """
    import unicodedata
    
    if not texte:
        return texte
    
    # Décomposer les caractères accentués (é -> e + accent)
    texte_decompose = unicodedata.normalize('NFD', texte)
    
    # Supprimer les marques diacritiques (accents)
    texte_sans_accents = ''.join(
        c for c in texte_decompose 
        if unicodedata.category(c) != 'Mn'  # Mn = Mark, Nonspacing (accents)
    )
    
    # Mettre en minuscules
    return texte_sans_accents.lower()


def traduire_mode_tagsadjs(lignes: list, colonnes_entree: list, lang_cible: str, 
                           glossaire: dict, commentaires: list) -> tuple:
    """
    Traduit un fichier tagsadjs.csv.
    
    - Traduit les colonnes canon, synonymes, adjs
    - Ajoute frcanon et fradjs comme références au français
    - Garde les autres colonnes telles quelles
    
    Returns:
        (lignes_sortie, colonnes_sortie)
    """
    # Construire les colonnes de sortie
    # Garder toutes les colonnes existantes + ajouter frcanon, fradjs à la fin
    colonnes_sortie = list(colonnes_entree)
    if 'frcanon' not in colonnes_sortie:
        colonnes_sortie.append('frcanon')
    if 'fradjs' not in colonnes_sortie:
        colonnes_sortie.append('fradjs')
    
    lignes_sortie = []
    
    for row in lignes:
        nouvelle_ligne = {}
        
        # Sauvegarder les valeurs françaises originales
        canon_fr = row.get('canon', '').strip()
        synonymes_fr = row.get('synonymes', '').strip()
        adjs_fr = row.get('adjs', '').strip()
        
        # Copier toutes les colonnes
        for col in colonnes_entree:
            nouvelle_ligne[col] = row.get(col, '')
        
        # Traduire canon
        if canon_fr:
            canon_traduit = traduire_terme(canon_fr, lang_cible, 'fr', glossaire)
            if canon_traduit:
                nouvelle_ligne['canon'] = canon_traduit
                if canon_traduit != canon_fr:
                    print(f"    canon: {canon_fr} -> {canon_traduit}")
        
        # Traduire synonymes (liste séparée par virgules)
        if synonymes_fr:
            synonymes_traduits = []
            for syn in synonymes_fr.split(','):
                syn = syn.strip()
                if syn:
                    syn_traduit = traduire_terme(syn, lang_cible, 'fr', glossaire)
                    synonymes_traduits.append(syn_traduit if syn_traduit else syn)
            nouvelle_ligne['synonymes'] = ','.join(synonymes_traduits)
        
        # Traduire adjs (liste séparée par virgules)
        if adjs_fr:
            adjs_traduits = []
            for adj in adjs_fr.split(','):
                adj = adj.strip()
                if adj:
                    adj_traduit = traduire_terme(adj, lang_cible, 'fr', glossaire)
                    adjs_traduits.append(adj_traduit if adj_traduit else adj)
            nouvelle_ligne['adjs'] = ','.join(adjs_traduits)
        
        # Ajouter les références françaises
        nouvelle_ligne['frcanon'] = canon_fr
        nouvelle_ligne['fradjs'] = adjs_fr
        
        lignes_sortie.append(nouvelle_ligne)
    
    return lignes_sortie, colonnes_sortie


def traduire_mode_generique(lignes: list, colonnes_entree: list, lang_cible: str,
                            glossaire: dict, reverse: bool, langue_reverse: str) -> tuple:
    """
    Traduit un fichier CSV générique.
    
    - Cherche la colonne 'fr' ou la première colonne texte
    - Produit un fichier avec colonnes : langue_source, langue_cible, original, traduction
    
    Returns:
        (lignes_sortie, colonnes_sortie)
    """
    colonnes_sortie = ['langue_source', 'langue_cible', 'original', 'traduction']
    colonnes_ignorees = [c for c in colonnes_entree if c and c.startswith('X')]
    colonnes_a_traduire = [c for c in colonnes_entree if c and not c.startswith('X')]
    
    lignes_sortie = []
    
    for row in lignes:
        # Trouver la colonne source
        if reverse:
            langue_source = langue_reverse
            texte_source = None
            
            if langue_source and langue_source in row:
                texte_source = row[langue_source].strip()
            else:
                for col in colonnes_a_traduire:
                    val = row.get(col, '').strip()
                    if val:
                        texte_source = val
                        langue_source = detecter_langue(val)
                        break
        else:
            langue_source = 'fr'
            # Chercher colonne 'fr' ou première colonne texte
            if 'fr' in row:
                texte_source = row.get('fr', '').strip()
            else:
                texte_source = None
                for col in colonnes_a_traduire:
                    val = row.get(col, '').strip()
                    if val:
                        texte_source = val
                        break
        
        if not texte_source:
            continue
        
        # Traduire
        traduction = traduire_terme(texte_source, lang_cible, langue_source, glossaire)
        if not traduction:
            traduction = texte_source
        
        lignes_sortie.append({
            'langue_source': langue_source,
            'langue_cible': lang_cible,
            'original': texte_source,
            'traduction': traduction
        })
        
        # Afficher
        print(f"    {langue_source}->{lang_cible} : {texte_source} -> {traduction}")
    
    return lignes_sortie, colonnes_sortie

# ══════════════════════════════════════════════════════════════════════════════
# AIDE
# ══════════════════════════════════════════════════════════════════════════════

def afficher_aide(langues: list):
    """Affiche l'aide détaillée."""
    aide = f"""
{__pgm__} - Traducteur multilingue avec glossaire centralisé

SYNOPSIS
  python {__pgm__} [OPTIONS] [TEXTE|FICHIER.csv]

OPTIONS
  (aucune)           Mode vérification : complète les traductions manquantes du glossaire
  "phrase"           Traduit la phrase vers toutes les langues actives
  fichier.csv        Traduit toutes les colonnes texte du fichier CSV
  --only <lang>      Traduit uniquement vers la langue spécifiée (ex: --only ja)
  -r [lang]          Reverse : traduit vers le français
                     Si lang spécifiée : traduit depuis cette langue
                     Sinon : détection automatique de la langue source
  -t                 Mode test : limite aux 5 premières lignes
  -? ou -h           Affiche cette aide

LANGUES DISPONIBLES
  {', '.join(langues)}
  (lues depuis refs/commun.csv)

GLOSSAIRE
  Le fichier refs/glossaire.csv stocke toutes les traductions connues.
  Avant toute traduction API, le programme cherche d'abord dans le glossaire.
  Les nouvelles traductions sont automatiquement ajoutées au glossaire.
  Les cases déjà traduites ne sont JAMAIS écrasées.

  Types de termes dans le glossaire :
    p = permanent (mots fondamentaux)
    c = courant
    o = orthodontie
    a = appareils
    z = ne pas traduire (copier tel quel)
    m = manuel (ajouté manuellement)
    jjmmaaaa = date d'ajout automatique (temporaire)

SÉCURITÉ
  Si aucun test (-t) n'a été effectué depuis plus de 5 minutes,
  le mode test est automatiquement forcé pour éviter les gros traitements accidentels.

FICHIERS DE SORTIE
  Pour un fichier CSV, le résultat est préfixé par la langue cible :
    toto.csv traduit en japonais → ja_toto.csv
    toto.csv traduit en allemand → de_toto.csv

  Les colonnes dont l'en-tête commence par X sont ignorées.

FORMAT D'AFFICHAGE
  Chaque traduction est affichée au format :
    langue_source->langue_cible : phrase_originale -> phrase_traduite

EXEMPLES
  python {__pgm__} "bonjour le monde"
      → Traduit vers toutes les langues
      → fr->en : bonjour le monde -> hello world

  python {__pgm__} --only ja "bonjour"
      → Traduit uniquement vers le japonais

  python {__pgm__} -r "hello world"
      → Détecte l'anglais, traduit vers le français
      → en->fr : hello world -> bonjour le monde

  python {__pgm__} -r en "hello"
      → Force la langue source anglais, traduit vers le français

  python {__pgm__} patients.csv
      → Génère en_patients.csv, ja_patients.csv, de_patients.csv, etc.

  python {__pgm__} -t gros_fichier.csv
      → Mode test sur 5 lignes seulement
"""
    print(aide)

# ══════════════════════════════════════════════════════════════════════════════
# POINT D'ENTRÉE
# ══════════════════════════════════════════════════════════════════════════════

def main():
    """Point d'entrée principal."""
    print(f"{__pgm__} V{__version__} - {__date__}")
    print(f"Chemin : {Path(__file__).resolve()}")
    
    t0 = time.time()
    
    # Charger les langues (OBLIGATOIRE - pas de fallback)
    langues = charger_langues()
    print(f"Langues actives : {', '.join(langues)}")
    
    # Parser les arguments
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('texte_ou_fichier', nargs='?', default=None)
    parser.add_argument('--only', dest='only_lang', default=None)
    parser.add_argument('-r', '--reverse', dest='reverse', nargs='?', const='', default=None)
    parser.add_argument('-t', '--test', action='store_true')
    parser.add_argument('-h', '-?', '--help', action='store_true', dest='aide')
    
    # Gérer les arguments manuellement pour plus de flexibilité
    args_list = sys.argv[1:]
    
    # Vérifier -? ou -h en premier
    if '-?' in args_list or '-h' in args_list or '--help' in args_list:
        afficher_aide(langues)
        return
    
    # Parser
    try:
        args, reste = parser.parse_known_args()
    except:
        args = parser.parse_args([])
        reste = args_list
    
    # Récupérer le texte ou fichier si dans le reste
    texte_ou_fichier = args.texte_ou_fichier
    if not texte_ou_fichier and reste:
        # Chercher le premier argument qui n'est pas une option
        for r in reste:
            if not r.startswith('-'):
                texte_ou_fichier = r
                break
    
    # Charger le glossaire
    glossaire = charger_glossaire()
    print(f"Glossaire chargé : {len(glossaire)} entrées")
    
    # Vérifier la sécurité du mode test
    mode_test = verifier_securite_test(args.test)
    
    # Mode vérification (sans argument)
    if not texte_ou_fichier:
        print("\n[MODE VÉRIFICATION]")
        glossaire = verifier_glossaire(glossaire, langues)
        sauvegarder_glossaire(glossaire, langues=langues)
    
    # Mode fichier CSV
    elif texte_ou_fichier.endswith('.csv'):
        print(f"\n[MODE FICHIER]")
        
        # Déterminer les options
        langue_unique = args.only_lang
        reverse = args.reverse is not None
        langue_reverse = args.reverse if args.reverse else None
        
        # Valider la langue unique
        if langue_unique and langue_unique not in langues:
            print(f"[ERREUR] Langue '{langue_unique}' non disponible")
            print(f"         Langues disponibles : {', '.join(langues)}")
            sys.exit(1)
        
        fichiers = traduire_fichier(
            texte_ou_fichier, glossaire, langues,
            langue_unique=langue_unique,
            reverse=reverse,
            langue_reverse=langue_reverse,
            mode_test=mode_test
        )
        
        sauvegarder_glossaire(glossaire, langues=langues)
        
        if fichiers:
            print(f"\n{len(fichiers)} fichier(s) créé(s)")
    
    # Mode phrase
    else:
        print(f"\n[MODE PHRASE]")
        phrase = texte_ou_fichier
        
        # Déterminer les options
        langue_unique = args.only_lang
        reverse = args.reverse is not None
        langue_reverse = args.reverse if args.reverse else None
        
        # Valider la langue unique
        if langue_unique and langue_unique not in langues:
            print(f"[ERREUR] Langue '{langue_unique}' non disponible")
            print(f"         Langues disponibles : {', '.join(langues)}")
            sys.exit(1)
        
        # Déterminer les langues cibles
        if reverse:
            langues_cibles = ['fr']
            langue_source = langue_reverse if langue_reverse else detecter_langue(phrase)
        elif langue_unique:
            langues_cibles = [langue_unique]
            langue_source = 'fr'
        else:
            langues_cibles = [l for l in langues if l != 'fr']
            langue_source = 'fr'
        
        print(f"Phrase : {phrase}")
        print()
        
        for lang_cible in langues_cibles:
            result = traduire_phrase_unique(
                phrase, lang_cible, glossaire,
                langue_source=langue_source,
                reverse=reverse
            )
            afficher_traduction(result)
        
        sauvegarder_glossaire(glossaire, langues=langues)
    
    # Statistiques
    stats.afficher()
    
    elapsed = time.time() - t0
    print()
    print("=" * 70)
    print(f"TEMPS TOTAL : {elapsed:.1f} secondes")
    print("=" * 70)


if __name__ == "__main__":
    main()
