# detlang.py V1.0.2 - 11/12/2025 17:44:46
__pgm__ = "detlang.py"
__version__ = "1.0.2"
__date__ = "11/12/2025 17:44:46"

"""
detlang.py - Détection automatique de la langue d'une question utilisateur

Ce programme détecte la langue d'une question en utilisant plusieurs approches :
1. Détection par script Unicode (thaï, arabe, chinois) - prioritaire
2. Score de langue sélectionnée par l'utilisateur (select)
3. Score par termes métier (tags/adjectifs de tags.csv)
4. Score par vocabulaire discriminant (discriminants.csv)
5. Score par caractères accentués (discriminants.csv)
6. Fallback DeepL si résultat non satisfaisant

Usage CLI:
    python detlang.py "question" [langue_selectionnee] [--verbose]
    
    langue_selectionnee: fr (défaut), en, de, th, etc. ou "auto" pour désactiver
"""

import csv
import json
import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import Optional

# ============================================================================
# CONSTANTES ET CONFIGURATION
# ============================================================================

# Répertoire des fichiers de référence
REFS_DIR = Path(__file__).parent / "refs"

# Fichiers de configuration
FICHIER_COMMUN = REFS_DIR / "commun.csv"
FICHIER_TAGS = REFS_DIR / "tags.csv"
FICHIER_DISCRIMINANTS = REFS_DIR / "discriminants.csv"

# Langue par défaut
LANGUE_DEFAUT = "fr"

# Score pour la langue sélectionnée
SCORE_SELECT = 3

# Score DeepL (langue détectée avec certitude)
SCORE_DEEPL = 5

# Plages Unicode pour détection directe
UNICODE_RANGES = {
    "th": (0x0E00, 0x0E7F),   # Thaï
    "ar": (0x0600, 0x06FF),   # Arabe
    "cn": (0x4E00, 0x9FFF),   # Chinois (CJK)
}

# ============================================================================
# VARIABLES GLOBALES (CACHE)
# ============================================================================

_vocabulaire_metier: dict[str, set[str]] = {}
_vocabulaire_discriminant: dict[str, set[str]] = {}
_accents_discriminants: dict[str, set[str]] = {}
_langues_actives: list[str] = []
_config: dict[str, int] = {"ecartlang": 2, "seuillang": 5}
_cache_charge: bool = False


# ============================================================================
# FONCTIONS DE CHARGEMENT
# ============================================================================

def charger_config() -> tuple[list[str], dict[str, int]]:
    """
    Charge la configuration depuis commun.csv.
    
    Returns:
        Tuple (langues_actives, config avec ecartlang et seuillang)
    """
    langues = []
    config = {"ecartlang": 2, "seuillang": 5}
    
    if not FICHIER_COMMUN.exists():
        print(f"[ERREUR] Fichier non trouvé : {FICHIER_COMMUN.absolute()}")
        return [LANGUE_DEFAUT], config
    
    with open(FICHIER_COMMUN, "r", encoding="utf-8-sig", newline="") as f:
        lignes = [ligne for ligne in f if not ligne.strip().startswith("#")]
    
    reader = csv.DictReader(lignes, delimiter=";")
    
    for row in reader:
        # Langues actives
        langue = row.get("langues", "").strip()
        if langue and langue not in langues:
            langues.append(langue)
        
        # Configuration (première ligne non vide)
        if "ecartlang" in row and row["ecartlang"].strip():
            try:
                config["ecartlang"] = int(row["ecartlang"].strip())
            except ValueError:
                pass
        if "seuillang" in row and row["seuillang"].strip():
            try:
                config["seuillang"] = int(row["seuillang"].strip())
            except ValueError:
                pass
    
    return langues if langues else [LANGUE_DEFAUT], config


def charger_vocabulaire_metier(langues: list[str]) -> dict[str, set[str]]:
    """
    Charge le vocabulaire métier depuis tags.csv.
    
    Args:
        langues: Liste des codes langues actives
        
    Returns:
        Dictionnaire {langue: set de termes standardisés}
    """
    vocabulaire: dict[str, set[str]] = {lang: set() for lang in langues}
    
    if not FICHIER_TAGS.exists():
        print(f"[ERREUR] Fichier non trouvé : {FICHIER_TAGS.absolute()}")
        return vocabulaire
    
    with open(FICHIER_TAGS, "r", encoding="utf-8-sig", newline="") as f:
        lignes = [ligne for ligne in f if not ligne.strip().startswith("#")]
    
    reader = csv.DictReader(lignes, delimiter=";")
    
    for row in reader:
        for lang in langues:
            # Colonnes standardisées : std{lang}tags et std{lang}adjs
            col_tags = f"std{lang}tags"
            col_adjs = f"std{lang}adjs"
            
            # Extraire les tags
            if col_tags in row and row[col_tags]:
                termes = row[col_tags].split(",")
                for terme in termes:
                    terme = terme.strip()
                    if terme:
                        vocabulaire[lang].add(terme)
            
            # Extraire les adjectifs (séparateur | pour les groupes)
            if col_adjs in row and row[col_adjs]:
                groupes = row[col_adjs].split(",")
                for groupe in groupes:
                    adjs = groupe.split("|")
                    for adj in adjs:
                        adj = adj.strip()
                        if adj:
                            vocabulaire[lang].add(adj)
    
    return vocabulaire


def charger_discriminants(langues: list[str]) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """
    Charge les discriminants depuis discriminants.csv.
    
    Args:
        langues: Liste des codes langues actives
        
    Returns:
        Tuple (vocabulaire_discriminant, accents_discriminants)
    """
    vocabulaire: dict[str, set[str]] = {lang: set() for lang in langues}
    accents: dict[str, set[str]] = {lang: set() for lang in langues}
    
    if not FICHIER_DISCRIMINANTS.exists():
        print(f"[ERREUR] Fichier non trouvé : {FICHIER_DISCRIMINANTS.absolute()}")
        return vocabulaire, accents
    
    with open(FICHIER_DISCRIMINANTS, "r", encoding="utf-8-sig", newline="") as f:
        lignes = [ligne for ligne in f if not ligne.strip().startswith("#")]
    
    reader = csv.DictReader(lignes, delimiter=";")
    
    for row in reader:
        type_ligne = row.get("type", "").strip().lower()
        
        if type_ligne == "vocabulaire":
            for lang in langues:
                if lang in row and row[lang]:
                    mots = row[lang].split(",")
                    for mot in mots:
                        mot = mot.strip()
                        if mot:
                            vocabulaire[lang].add(mot.lower())
        
        elif type_ligne == "accent":
            for lang in langues:
                if lang in row and row[lang]:
                    chars = row[lang].split(",")
                    for char in chars:
                        char = char.strip()
                        if char:
                            accents[lang].add(char)
    
    return vocabulaire, accents


def charger_vocabulaire() -> None:
    """
    Charge tous les vocabulaires en mémoire (cache global).
    À appeler une seule fois au démarrage de l'application.
    """
    global _vocabulaire_metier, _vocabulaire_discriminant, _accents_discriminants
    global _langues_actives, _config, _cache_charge
    
    if _cache_charge:
        return
    
    _langues_actives, _config = charger_config()
    _vocabulaire_metier = charger_vocabulaire_metier(_langues_actives)
    _vocabulaire_discriminant, _accents_discriminants = charger_discriminants(_langues_actives)
    _cache_charge = True


# ============================================================================
# FONCTIONS DE STANDARDISATION
# ============================================================================

def standardiser(texte: str) -> str:
    """
    Standardise un texte : minuscules, suppression des accents.
    
    Args:
        texte: Texte à standardiser
        
    Returns:
        Texte standardisé
    """
    texte = texte.lower()
    # Décomposition Unicode puis suppression des diacritiques
    texte = unicodedata.normalize("NFD", texte)
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")
    return texte


# ============================================================================
# FONCTIONS DE DÉTECTION
# ============================================================================

def detecter_unicode(question: str) -> Optional[str]:
    """
    Détecte la langue par plages Unicode (thaï, arabe, chinois).
    
    Args:
        question: Question utilisateur
        
    Returns:
        Code langue si détecté, None sinon
    """
    for char in question:
        code = ord(char)
        for lang, (debut, fin) in UNICODE_RANGES.items():
            if debut <= code <= fin:
                return lang
    return None


def calculer_score_select(langue_selectionnee: str, langues: list[str]) -> dict[str, int]:
    """
    Calcule le score pour la langue sélectionnée.
    
    Args:
        langue_selectionnee: Code langue sélectionné ou "auto"
        langues: Liste des langues actives
        
    Returns:
        Dictionnaire {langue: score}
    """
    scores = {lang: 0 for lang in langues}
    
    if langue_selectionnee != "auto" and langue_selectionnee in langues:
        scores[langue_selectionnee] = SCORE_SELECT
    
    return scores


def calculer_score_metier(question_std: str, langues: list[str]) -> dict[str, int]:
    """
    Calcule le score par termes métier (tags.csv).
    
    Args:
        question_std: Question standardisée
        langues: Liste des langues actives
        
    Returns:
        Dictionnaire {langue: score}
    """
    scores = {lang: 0 for lang in langues}
    mots_question = set(question_std.split())
    
    for lang in langues:
        if lang in _vocabulaire_metier:
            for terme in _vocabulaire_metier[lang]:
                # Vérifier si le terme (qui peut contenir des espaces) est dans la question
                if terme in question_std:
                    scores[lang] += 1
    
    return scores


def calculer_score_vocabulaire(question_orig: str, langues: list[str]) -> dict[str, int]:
    """
    Calcule le score par vocabulaire discriminant.
    
    Args:
        question_orig: Question originale (avec accents)
        langues: Liste des langues actives
        
    Returns:
        Dictionnaire {langue: score}
    """
    scores = {lang: 0 for lang in langues}
    question_lower = question_orig.lower()
    mots_question = re.findall(r'\b\w+\b', question_lower)
    
    for lang in langues:
        if lang in _vocabulaire_discriminant:
            for mot in mots_question:
                if mot in _vocabulaire_discriminant[lang]:
                    scores[lang] += 1
    
    return scores


def calculer_score_accent(question_orig: str, langues: list[str]) -> dict[str, int]:
    """
    Calcule le score par caractères accentués discriminants.
    
    Args:
        question_orig: Question originale (avec accents)
        langues: Liste des langues actives
        
    Returns:
        Dictionnaire {langue: score}
    """
    scores = {lang: 0 for lang in langues}
    
    for lang in langues:
        if lang in _accents_discriminants:
            for char in question_orig:
                if char in _accents_discriminants[lang]:
                    scores[lang] += 1
    
    return scores


def appeler_deepl(question: str) -> Optional[str]:
    """
    Appelle l'API DeepL pour détecter la langue.
    
    Args:
        question: Question originale
        
    Returns:
        Code langue détecté ou None si erreur
    """
    api_key = os.environ.get("DEEPL_API_KEY")
    if not api_key:
        return None
    
    try:
        import urllib.request
        import urllib.parse
        
        # Utiliser l'endpoint de traduction pour obtenir la langue source
        url = "https://api-free.deepl.com/v2/translate"
        data = urllib.parse.urlencode({
            "auth_key": api_key,
            "text": question,
            "target_lang": "EN"  # Langue cible arbitraire
        }).encode()
        
        req = urllib.request.Request(url, data=data, method="POST")
        
        with urllib.request.urlopen(req, timeout=5) as response:
            result = json.loads(response.read().decode())
            if "translations" in result and result["translations"]:
                lang_detectee = result["translations"][0].get("detected_source_language", "").lower()
                # Normaliser les codes (DeepL utilise parfois des codes différents)
                if lang_detectee == "zh":
                    lang_detectee = "cn"
                return lang_detectee
    except Exception as e:
        print(f"[DEBUG] Erreur DeepL : {e}")
    
    return None


# ============================================================================
# FONCTION PRINCIPALE DE DÉTECTION
# ============================================================================

def detecter_langue(question: str, langue_selectionnee: str = "fr", verbose: bool = False) -> dict:
    """
    Détecte la langue d'une question.
    
    Args:
        question: La question utilisateur
        langue_selectionnee: Langue présélectionnée (défaut: "fr", ou "auto")
        verbose: Afficher les détails
        
    Returns:
        dict avec langue_detectee, score, scores_all, methode, etc.
    """
    # Charger le cache si nécessaire
    charger_vocabulaire()
    
    langues = _langues_actives
    ecart_min = _config["ecartlang"]
    seuil_min = _config["seuillang"]
    
    # Résultat par défaut
    resultat = {
        "langue_detectee": LANGUE_DEFAUT,
        "score": 0,
        "scores_all": {lang: 0 for lang in langues},
        "methode": "defaut",
        "question_originale": question,
        "question_standardisee": ""
    }
    
    # Question vide
    if not question or not question.strip():
        return resultat
    
    question = question.strip()
    
    # 1. Détection par Unicode (prioritaire)
    lang_unicode = detecter_unicode(question)
    if lang_unicode:
        resultat["langue_detectee"] = lang_unicode
        resultat["score"] = 10
        resultat["scores_all"] = {lang: (10 if lang == lang_unicode else 0) for lang in langues}
        resultat["methode"] = "unicode"
        resultat["question_originale"] = question
        if verbose:
            print(f"[DEBUG] Détection Unicode : {lang_unicode}")
        return resultat
    
    # Standardiser la question
    question_std = standardiser(question)
    resultat["question_standardisee"] = question_std
    
    # 2. Calculer tous les scores
    scores_select = calculer_score_select(langue_selectionnee, langues)
    scores_metier = calculer_score_metier(question_std, langues)
    scores_vocabulaire = calculer_score_vocabulaire(question, langues)
    scores_accent = calculer_score_accent(question, langues)
    
    if verbose:
        print(f"[DEBUG] Scores select : {scores_select}")
        print(f"[DEBUG] Scores métier : {scores_metier}")
        print(f"[DEBUG] Scores vocabulaire : {scores_vocabulaire}")
        print(f"[DEBUG] Scores accent : {scores_accent}")
    
    # 3. Calculer les scores totaux
    scores_totaux = {lang: 0 for lang in langues}
    for lang in langues:
        scores_totaux[lang] = (
            scores_select.get(lang, 0) +
            scores_metier.get(lang, 0) +
            scores_vocabulaire.get(lang, 0) +
            scores_accent.get(lang, 0)
        )
    
    if verbose:
        print(f"[DEBUG] Scores totaux : {scores_totaux}")
    
    # 4. Déterminer la méthode dominante
    methodes = []
    score_max = max(scores_totaux.values())
    
    if score_max > 0:
        # Identifier les contributions
        lang_gagnante = max(scores_totaux, key=lambda k: (scores_totaux[k], k == LANGUE_DEFAUT))
        
        if scores_select.get(lang_gagnante, 0) > 0:
            methodes.append("select")
        if scores_metier.get(lang_gagnante, 0) > 0:
            methodes.append("terme")
        if scores_vocabulaire.get(lang_gagnante, 0) > 0:
            methodes.append("vocabulaire")
        if scores_accent.get(lang_gagnante, 0) > 0:
            methodes.append("accent")
    
    # 5. Vérifier si résultat fiable
    scores_tries = sorted(scores_totaux.values(), reverse=True)
    meilleur_score = scores_tries[0] if scores_tries else 0
    second_score = scores_tries[1] if len(scores_tries) > 1 else 0
    ecart = meilleur_score - second_score
    
    besoin_deepl = (meilleur_score < seuil_min) or (ecart < ecart_min and meilleur_score > 0)
    
    if verbose:
        print(f"[DEBUG] Meilleur score : {meilleur_score}, Écart : {ecart}")
        print(f"[DEBUG] Seuil : {seuil_min}, Écart min : {ecart_min}")
        print(f"[DEBUG] Besoin DeepL : {besoin_deepl}")
    
    # 6. Appeler DeepL si nécessaire
    if besoin_deepl:
        lang_deepl = appeler_deepl(question)
        if lang_deepl:
            if verbose:
                print(f"[DEBUG] DeepL détecte : {lang_deepl}")
            
            # Ajouter le score DeepL
            if lang_deepl in scores_totaux:
                scores_totaux[lang_deepl] += SCORE_DEEPL
            else:
                scores_totaux[lang_deepl] = SCORE_DEEPL
            
            methodes.append("deepl")
    
    # 7. Déterminer la langue finale
    if all(s == 0 for s in scores_totaux.values()):
        # Aucun score -> défaut
        resultat["langue_detectee"] = LANGUE_DEFAUT
        resultat["score"] = 0
        resultat["methode"] = "defaut"
    else:
        # Langue avec meilleur score (priorité FR si égalité)
        lang_finale = LANGUE_DEFAUT
        score_final = scores_totaux.get(LANGUE_DEFAUT, 0)
        
        for lang, score in scores_totaux.items():
            if score > score_final:
                lang_finale = lang
                score_final = score
        
        resultat["langue_detectee"] = lang_finale
        resultat["score"] = score_final
        
        # Déterminer la méthode affichée
        if len(methodes) == 1 or (ecart >= ecart_min and meilleur_score >= seuil_min):
            resultat["methode"] = methodes[0] if methodes else "defaut"
        else:
            resultat["methode"] = ", ".join(methodes) if methodes else "defaut"
    
    resultat["scores_all"] = scores_totaux
    resultat["question_originale"] = question
    
    return resultat


# ============================================================================
# INTERFACE CLI
# ============================================================================

def main():
    """Point d'entrée principal."""
    print(f"{__pgm__} V{__version__} - {__date__}")
    
    # Parser les arguments
    args = sys.argv[1:]
    verbose = "--verbose" in args or "-v" in args
    args = [a for a in args if a not in ("--verbose", "-v")]
    
    if not args:
        print("Usage: python detlang.py \"question\" [langue_selectionnee] [--verbose]")
        print("  langue_selectionnee: fr (défaut), en, de, th, etc. ou 'auto'")
        sys.exit(1)
    
    question = args[0]
    langue_selectionnee = args[1] if len(args) > 1 else "fr"
    
    # Détecter la langue
    resultat = detecter_langue(question, langue_selectionnee, verbose)
    
    # Afficher le résultat JSON
    print(json.dumps(resultat, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
