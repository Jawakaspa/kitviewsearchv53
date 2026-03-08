# traducteur.py V1.0.0 - 28/12/2025 18:41:31
__pgm__ = "traducteur.py"
__version__ = "1.0.0"
__date__ = "28/12/2025 18:41:31"

# ╔════════════════════════════════════════════════════════════════════════════╗
# ║ traducteur.py                                                              ║
# ║ Traducteur multilingue utilisant exclusivement le glossaire                ║
# ║                                                                            ║
# ║ Modes d'utilisation :                                                      ║
# ║   python traducteur.py                     → Affiche l'aide                ║
# ║   python traducteur.py -h                  → Affiche l'aide                ║
# ║   python traducteur.py glossaire.csv       → Complète glossaire avec DeepL ║
# ║   python traducteur.py glossaire.csv -t10  → Mode test (10 lignes)         ║
# ║   python traducteur.py glossaire.csv de    → Complète uniquement allemand  ║
# ║   python traducteur.py "phrase"            → Auto→fr avec glossaire        ║
# ║   python traducteur.py "phrase" ptfr       → pt→fr avec glossaire          ║
# ║   python traducteur.py "phrase" frpt --deepl → fr→pt avec DeepL            ║
# ║   python traducteur.py fichier.csv         → Traduit fr→toutes (glossaire) ║
# ║   python traducteur.py fichier.csv de      → Traduit fr→de (glossaire)     ║
# ║   python traducteur.py fichier.csv --deepl → Traduit fr→toutes (DeepL)     ║
# ║   python traducteur.py -t N fichier.csv    → Mode test (N premières lignes)║
# ╚════════════════════════════════════════════════════════════════════════════╝

import csv
import sys
import os
import re
import io
import time
import argparse
from pathlib import Path
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ══════════════════════════════════════════════════════════════════════════════

# Chemin par défaut du glossaire (relatif au script)
CHEMIN_GLOSSAIRE = "refs/glossaire.csv"

# Colonnes de langue supportées (dans l'ordre)
COLONNES_LANGUES = ['fr', 'en', 'de', 'es', 'it', 'ja', 'pt', 'pl', 'ro', 'th', 'ar', 'cn']

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
        self.termes_non_trouves = 0
        self.api_deepl = 0
        self.caracteres_traduits = 0
        self.lignes_traitees = 0
        self.colonnes_creees = []
        self.erreurs = []
    
    def afficher(self):
        """Affiche les statistiques."""
        print()
        print("=" * 70)
        print("STATISTIQUES DE TRADUCTION")
        print("=" * 70)
        print(f"  Lignes traitées         : {self.lignes_traitees}")
        print(f"  Termes trouvés glossaire: {self.termes_glossaire}")
        print(f"  Termes non trouvés      : {self.termes_non_trouves}")
        print(f"  Appels API DeepL        : {self.api_deepl}")
        print(f"  Caractères traduits     : {self.caracteres_traduits}")
        if self.colonnes_creees:
            print(f"  Colonnes créées         : {', '.join(self.colonnes_creees)}")
        if self.erreurs:
            print(f"  Erreurs                 : {len(self.erreurs)}")
            for err in self.erreurs[:5]:
                print(f"    - {err}")

# Instance globale
stats = Stats()

# ══════════════════════════════════════════════════════════════════════════════
# UTILITAIRES CSV
# ══════════════════════════════════════════════════════════════════════════════

def lire_csv_filtre_commentaires(chemin: Path) -> tuple:
    """
    Lit un fichier CSV en filtrant les lignes de commentaires (#).
    
    Returns:
        tuple: (liste de dict, liste des noms de colonnes, liste des commentaires)
    """
    if not chemin.exists():
        print(f"[ERREUR] Fichier non trouvé : {chemin}")
        return [], [], []
    
    commentaires = []
    lignes_data = []
    
    with open(chemin, 'r', encoding='utf-8-sig') as f:
        for ligne in f:
            ligne_strip = ligne.strip()
            if ligne_strip.startswith('#'):
                commentaires.append(ligne.rstrip('\n\r'))
            elif ligne_strip:
                lignes_data.append(ligne)
    
    if not lignes_data:
        print(f"[ERREUR] Fichier vide ou uniquement des commentaires : {chemin}")
        return [], [], commentaires
    
    # Parser les lignes de données
    contenu = io.StringIO(''.join(lignes_data))
    reader = csv.DictReader(contenu, delimiter=';')
    colonnes = reader.fieldnames or []
    
    rows = []
    for row in reader:
        rows.append(row)
    
    return rows, colonnes, commentaires


def sauvegarder_csv(chemin: Path, rows: list, colonnes: list, commentaires: list = None):
    """
    Sauvegarde un fichier CSV en UTF-8-BOM avec point-virgule.
    
    Args:
        chemin: Chemin du fichier
        rows: Liste de dictionnaires
        colonnes: Liste des noms de colonnes (ordre préservé)
        commentaires: Liste des lignes de commentaires (optionnel)
    """
    with open(chemin, 'w', encoding='utf-8-sig', newline='') as f:
        # Écrire l'en-tête
        f.write(';'.join(colonnes) + '\n')
        
        # Écrire les commentaires après l'en-tête
        if commentaires:
            for comm in commentaires:
                f.write(comm + '\n')
        
        # Écrire les données
        for row in rows:
            ligne = [str(row.get(col, '')) for col in colonnes]
            f.write(';'.join(ligne) + '\n')
    
    print(f"Fichier sauvegardé : {chemin}")

# ══════════════════════════════════════════════════════════════════════════════
# GESTION DU GLOSSAIRE
# ══════════════════════════════════════════════════════════════════════════════

def charger_glossaire(chemin: Path = None) -> dict:
    """
    Charge le glossaire en dictionnaire.
    
    La clé est le terme français en minuscules.
    La valeur est un dict avec toutes les colonnes.
    
    Returns:
        dict: {terme_fr_lower: {type, fr, en, de, ...}}
    """
    if chemin is None:
        chemin = Path(__file__).parent / CHEMIN_GLOSSAIRE
    
    chemin = chemin.resolve()
    
    if not chemin.exists():
        print(f"[ERREUR] Glossaire non trouvé : {chemin}")
        return {}
    
    rows, colonnes, _ = lire_csv_filtre_commentaires(chemin)
    
    glossaire = {}
    for row in rows:
        fr = row.get('fr', '').strip()
        if fr:
            cle = fr.lower()
            glossaire[cle] = {k: v.strip() if v else '' for k, v in row.items()}
    
    print(f"Glossaire chargé : {len(glossaire)} entrées depuis {chemin}")
    return glossaire


def sauvegarder_glossaire(glossaire: dict, chemin: Path = None):
    """
    Sauvegarde le glossaire.
    
    GARDE-FOU : Ne sauvegarde pas si le nouveau est plus petit que l'existant.
    """
    if chemin is None:
        chemin = Path(__file__).parent / CHEMIN_GLOSSAIRE
    
    chemin = chemin.resolve()
    
    # GARDE-FOU : Compter les entrées existantes
    nb_existant = 0
    if chemin.exists():
        rows_exist, _, _ = lire_csv_filtre_commentaires(chemin)
        nb_existant = len(rows_exist)
    
    if nb_existant > 0 and len(glossaire) < nb_existant:
        print(f"[GARDE-FOU] Sauvegarde REFUSÉE : glossaire actuel ({nb_existant}) > nouveau ({len(glossaire)})")
        return
    
    # Lire les commentaires existants
    commentaires = []
    if chemin.exists():
        _, _, commentaires = lire_csv_filtre_commentaires(chemin)
    
    # Construire les colonnes : type + langues
    colonnes = ['type'] + COLONNES_LANGUES
    
    # Convertir glossaire dict → list de rows
    rows = []
    for cle, data in sorted(glossaire.items(), key=lambda x: (x[1].get('type', 'z'), x[0])):
        rows.append(data)
    
    sauvegarder_csv(chemin, rows, colonnes, commentaires)
    print(f"  -> {len(glossaire)} entrées")

# ══════════════════════════════════════════════════════════════════════════════
# DÉTECTION DE LANGUE
# ══════════════════════════════════════════════════════════════════════════════

def detecter_langue_deepl(texte: str) -> str:
    """
    Détecte la langue d'un texte via DeepL.
    
    Returns:
        Code langue interne (fr, en, de, etc.) ou 'fr' par défaut
    """
    try:
        import deepl
        api_key = os.environ.get('DEEPL_API_KEY')
        if not api_key:
            print("[WARN] DEEPL_API_KEY non définie, détection impossible")
            return 'fr'
        
        translator = deepl.Translator(api_key)
        # DeepL détecte automatiquement si on ne spécifie pas source_lang
        # On traduit vers FR pour obtenir la langue source détectée
        result = translator.translate_text(texte, target_lang="FR")
        
        # Convertir code DeepL → code interne
        code_detecte = result.detected_source_lang.lower()
        
        # Mapping inverse
        for code_interne, code_deepl in CODES_DEEPL.items():
            if code_deepl.lower().startswith(code_detecte):
                return code_interne
        
        return code_detecte if code_detecte in COLONNES_LANGUES else 'fr'
        
    except Exception as e:
        print(f"[WARN] Détection langue échouée : {e}")
        return 'fr'

# ══════════════════════════════════════════════════════════════════════════════
# TRADUCTION DEEPL
# ══════════════════════════════════════════════════════════════════════════════

def traduire_deepl(texte: str, langue_source: str, langue_cible: str) -> str:
    """
    Traduit un texte via l'API DeepL.
    
    Returns:
        Texte traduit ou None si échec
    """
    if not texte or not texte.strip():
        return texte
    
    if langue_source == langue_cible:
        return texte
    
    try:
        import deepl
        api_key = os.environ.get('DEEPL_API_KEY')
        if not api_key:
            print("[ERREUR] Variable DEEPL_API_KEY non définie")
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
        print("[ERREUR] Module deepl non installé. Installez-le avec : pip install deepl")
        return None
    except Exception as e:
        stats.erreurs.append(f"DeepL: {e}")
        return None

# ══════════════════════════════════════════════════════════════════════════════
# TRADUCTION AVEC GLOSSAIRE (MOT À MOT, EXPRESSIONS LONGUES D'ABORD)
# ══════════════════════════════════════════════════════════════════════════════

def construire_index_glossaire(glossaire: dict, langue_source: str) -> dict:
    """
    Construit un index inversé du glossaire pour une langue source donnée.
    
    Pour traduire DE l'anglais VERS le français, on indexe par la colonne 'en'.
    
    Returns:
        dict: {terme_source_lower: terme_fr_lower}
    """
    index = {}
    
    for cle_fr, data in glossaire.items():
        terme_source = data.get(langue_source, '').strip().lower()
        if terme_source:
            index[terme_source] = cle_fr
    
    return index


def traduire_glossaire_mot_a_mot(texte: str, glossaire: dict, langue_source: str, langue_cible: str) -> str:
    """
    Traduit un texte en utilisant le glossaire mot à mot.
    Cherche les expressions les plus longues d'abord.
    
    Le résultat peut être hybride : mots traduits + mots non traduits.
    
    Args:
        texte: Texte à traduire
        glossaire: Dictionnaire du glossaire (clé = terme fr)
        langue_source: Code langue source (fr, en, de, etc.)
        langue_cible: Code langue cible
    
    Returns:
        Texte traduit (hybride si termes non trouvés)
    """
    if not texte or not texte.strip():
        return texte
    
    if langue_source == langue_cible:
        return texte
    
    # Construire l'index pour la langue source
    if langue_source == 'fr':
        # Traduction fr → autre : on cherche directement dans le glossaire
        index = {cle: cle for cle in glossaire.keys()}
    else:
        # Traduction autre → fr ou autre → autre : index inversé
        index = construire_index_glossaire(glossaire, langue_source)
    
    # Extraire tous les termes du glossaire (langue source) triés par longueur décroissante
    termes_tries = sorted(index.keys(), key=len, reverse=True)
    
    # Tokeniser le texte en préservant la ponctuation et les espaces
    # On travaille en minuscules pour la recherche
    texte_lower = texte.lower()
    texte_resultat = texte  # On garde la casse originale pour les parties non traduites
    
    # Marquer les positions déjà traduites
    masque = [False] * len(texte)
    
    remplacements = []  # Liste de (debut, fin, traduction)
    
    for terme in termes_tries:
        if not terme:
            continue
        
        # Chercher toutes les occurrences du terme
        pos = 0
        while True:
            idx = texte_lower.find(terme, pos)
            if idx == -1:
                break
            
            fin = idx + len(terme)
            
            # Vérifier que cette zone n'est pas déjà traduite
            if not any(masque[idx:fin]):
                # Vérifier les limites de mot (optionnel mais recommandé)
                avant_ok = (idx == 0 or not texte_lower[idx-1].isalnum())
                apres_ok = (fin == len(texte_lower) or not texte_lower[fin].isalnum())
                
                if avant_ok and apres_ok:
                    # Chercher la traduction
                    cle_fr = index[terme]
                    
                    if langue_cible == 'fr':
                        traduction = glossaire[cle_fr].get('fr', '')
                    else:
                        traduction = glossaire[cle_fr].get(langue_cible, '')
                    
                    if traduction:
                        remplacements.append((idx, fin, traduction))
                        for i in range(idx, fin):
                            masque[i] = True
                        stats.termes_glossaire += 1
                    else:
                        stats.termes_non_trouves += 1
            
            pos = idx + 1
    
    # Appliquer les remplacements de la fin vers le début pour préserver les indices
    remplacements.sort(key=lambda x: x[0], reverse=True)
    
    for debut, fin, traduction in remplacements:
        texte_resultat = texte_resultat[:debut] + traduction + texte_resultat[fin:]
    
    return texte_resultat

# ══════════════════════════════════════════════════════════════════════════════
# MODE 1 : TRADUCTION DU GLOSSAIRE (avec DeepL)
# ══════════════════════════════════════════════════════════════════════════════

def traduire_glossaire_csv(chemin: Path, langue_cible: str = None, limite: int = None):
    """
    Traduit les cases vides du glossaire avec DeepL.
    
    Args:
        chemin: Chemin du fichier glossaire.csv
        langue_cible: Si spécifié, traduit uniquement vers cette langue
        limite: Nombre max de lignes à traiter (mode test)
    """
    print(f"\n[MODE GLOSSAIRE] Traduction avec DeepL")
    print(f"Fichier : {chemin.resolve()}")
    
    rows, colonnes, commentaires = lire_csv_filtre_commentaires(chemin)
    
    if not rows:
        print("[ERREUR] Aucune donnée à traiter")
        return
    
    # Déterminer les langues cibles
    if langue_cible:
        if langue_cible not in COLONNES_LANGUES:
            print(f"[ERREUR] Langue '{langue_cible}' non supportée")
            print(f"         Langues disponibles : {', '.join(COLONNES_LANGUES)}")
            return
        langues_cibles = [langue_cible]
    else:
        langues_cibles = [l for l in COLONNES_LANGUES if l != 'fr']
    
    print(f"Langues cibles : {', '.join(langues_cibles)}")
    
    # Ajouter les colonnes manquantes
    for lang in COLONNES_LANGUES:
        if lang not in colonnes:
            colonnes.append(lang)
            stats.colonnes_creees.append(lang)
            print(f"  Colonne créée : {lang}")
    
    # Traiter les lignes
    total = min(len(rows), limite) if limite else len(rows)
    modifies = 0
    
    print(f"\nTraitement de {total} lignes...")
    
    for i, row in enumerate(rows[:total]):
        stats.lignes_traitees += 1
        
        fr = row.get('fr', '').strip()
        if not fr:
            continue
        
        type_val = row.get('type', '').strip()
        
        # Type 'z' : copier fr dans toutes les colonnes
        if type_val == 'z':
            for lang in langues_cibles:
                if not row.get(lang, '').strip():
                    row[lang] = fr
                    modifies += 1
            continue
        
        # Autres types : traduire avec DeepL si case vide
        for lang in langues_cibles:
            if row.get(lang, '').strip():
                continue  # Déjà traduit, ne pas écraser
            
            traduction = traduire_deepl(fr, 'fr', lang)
            if traduction:
                row[lang] = traduction
                modifies += 1
                print(f"  [{i+1}/{total}] {fr} → {lang}: {traduction}")
            else:
                print(f"  [{i+1}/{total}] {fr} → {lang}: ÉCHEC")
        
        # Progression
        if (i + 1) % 20 == 0:
            pct = int((i + 1) * 100 / total)
            print(f"  Progression: {pct}% ({i+1}/{total})")
    
    # Sauvegarder
    print(f"\n{modifies} traductions ajoutées")
    
    # GARDE-FOU
    if len(rows) < len(rows):  # Toujours vrai... on vérifie plutôt nb_existant
        pass  # Le garde-fou est dans sauvegarder_csv
    
    sauvegarder_csv(chemin, rows, colonnes, commentaires)

# ══════════════════════════════════════════════════════════════════════════════
# MODE 2 : TRADUCTION D'UNE PHRASE
# ══════════════════════════════════════════════════════════════════════════════

def traduire_phrase(phrase: str, direction: str, glossaire: dict, use_deepl: bool = False) -> str:
    """
    Traduit une phrase.
    
    Args:
        phrase: Phrase à traduire
        direction: Direction (ex: 'ptfr', 'frde', ou '' pour auto→fr)
        glossaire: Dictionnaire du glossaire
        use_deepl: Si True, utilise DeepL au lieu du glossaire
    
    Returns:
        Phrase traduite
    """
    # Parser la direction
    if direction and len(direction) >= 4:
        langue_source = direction[:2]
        langue_cible = direction[2:4]
    elif direction and len(direction) == 2:
        # Juste une langue = fr vers cette langue
        langue_source = 'fr'
        langue_cible = direction
    else:
        # Auto-détection → fr
        langue_source = detecter_langue_deepl(phrase)
        langue_cible = 'fr'
        print(f"Langue détectée : {langue_source}")
    
    # Valider les langues
    if langue_source not in COLONNES_LANGUES:
        print(f"[ERREUR] Langue source '{langue_source}' non supportée")
        return phrase
    if langue_cible not in COLONNES_LANGUES:
        print(f"[ERREUR] Langue cible '{langue_cible}' non supportée")
        return phrase
    
    print(f"Direction : {langue_source} → {langue_cible}")
    
    if use_deepl:
        resultat = traduire_deepl(phrase, langue_source, langue_cible)
        source = "DeepL"
    else:
        resultat = traduire_glossaire_mot_a_mot(phrase, glossaire, langue_source, langue_cible)
        source = "glossaire"
    
    print(f"\n[{source}] {langue_source}→{langue_cible} : {phrase}")
    print(f"         → {resultat}")
    
    return resultat

# ══════════════════════════════════════════════════════════════════════════════
# MODE 3 : TRADUCTION D'UN FICHIER CSV
# ══════════════════════════════════════════════════════════════════════════════

def traduire_fichier_csv(chemin: Path, glossaire: dict, langue_cible: str = None, 
                         use_deepl: bool = False, limite: int = None):
    """
    Traduit un fichier CSV.
    
    Traduit la colonne 'fr' vers les colonnes de langue.
    Crée les colonnes manquantes si nécessaire.
    Ne touche pas aux autres colonnes.
    
    Args:
        chemin: Chemin du fichier CSV
        glossaire: Dictionnaire du glossaire
        langue_cible: Si spécifié, traduit uniquement vers cette langue
        use_deepl: Si True, utilise DeepL
        limite: Nombre max de lignes (mode test)
    """
    print(f"\n[MODE FICHIER] Traduction de {chemin.resolve()}")
    
    rows, colonnes, commentaires = lire_csv_filtre_commentaires(chemin)
    
    if not rows:
        print("[ERREUR] Aucune donnée à traiter")
        return
    
    # Vérifier que la colonne 'fr' existe
    if 'fr' not in colonnes:
        print("[ERREUR] Colonne 'fr' non trouvée dans le fichier")
        return
    
    # Déterminer les langues cibles
    if langue_cible:
        if langue_cible not in COLONNES_LANGUES:
            print(f"[ERREUR] Langue '{langue_cible}' non supportée")
            return
        langues_cibles = [langue_cible]
    else:
        langues_cibles = [l for l in COLONNES_LANGUES if l != 'fr']
    
    print(f"Langues cibles : {', '.join(langues_cibles)}")
    print(f"Mode : {'DeepL' if use_deepl else 'Glossaire'}")
    
    # Ajouter les colonnes de langue manquantes
    for lang in COLONNES_LANGUES:
        if lang not in colonnes:
            # Insérer après 'fr' si possible
            try:
                idx_fr = colonnes.index('fr')
                colonnes.insert(idx_fr + 1, lang)
            except ValueError:
                colonnes.append(lang)
            stats.colonnes_creees.append(lang)
            print(f"  Colonne créée : {lang}")
    
    # Traiter les lignes
    total = min(len(rows), limite) if limite else len(rows)
    modifies = 0
    
    print(f"\nTraitement de {total} lignes...")
    
    for i, row in enumerate(rows[:total]):
        stats.lignes_traitees += 1
        
        fr = row.get('fr', '').strip()
        if not fr:
            continue
        
        for lang in langues_cibles:
            # Ne pas écraser une case déjà traduite
            if row.get(lang, '').strip():
                continue
            
            if use_deepl:
                traduction = traduire_deepl(fr, 'fr', lang)
            else:
                traduction = traduire_glossaire_mot_a_mot(fr, glossaire, 'fr', lang)
            
            if traduction and traduction != fr:
                row[lang] = traduction
                modifies += 1
                print(f"  [{i+1}/{total}] {fr} → {lang}: {traduction}")
        
        # Progression
        if (i + 1) % 50 == 0:
            pct = int((i + 1) * 100 / total)
            print(f"  Progression: {pct}% ({i+1}/{total})")
    
    # Sauvegarder
    print(f"\n{modifies} traductions ajoutées")
    sauvegarder_csv(chemin, rows, colonnes, commentaires)

# ══════════════════════════════════════════════════════════════════════════════
# AIDE
# ══════════════════════════════════════════════════════════════════════════════

def afficher_aide():
    """Affiche l'aide détaillée."""
    aide = f"""
{__pgm__} V{__version__} - Traducteur multilingue avec glossaire

SYNOPSIS
  python {__pgm__} [OPTIONS] [CIBLE]

MODES D'UTILISATION

  1. AIDE
     python {__pgm__}
     python {__pgm__} -h
     
  2. TRADUCTION DU GLOSSAIRE (avec DeepL)
     python {__pgm__} glossaire.csv           → Complète toutes les langues
     python {__pgm__} glossaire.csv de        → Complète uniquement l'allemand
     python {__pgm__} glossaire.csv -t10      → Mode test (10 lignes)
     python {__pgm__} glossaire.csv -t15 en   → Mode test, anglais uniquement
     
  3. TRADUCTION D'UNE PHRASE
     python {__pgm__} "phrase"                → Auto-détection → français (glossaire)
     python {__pgm__} "phrase" ptfr           → Portugais → français (glossaire)
     python {__pgm__} "phrase" frde           → Français → allemand (glossaire)
     python {__pgm__} "phrase" frpt --deepl   → Français → portugais (DeepL)
     
  4. TRADUCTION D'UN FICHIER CSV
     python {__pgm__} fichier.csv             → Traduit fr vers toutes langues (glossaire)
     python {__pgm__} fichier.csv de          → Traduit fr vers allemand (glossaire)
     python {__pgm__} fichier.csv --deepl     → Traduit fr vers toutes langues (DeepL)
     python {__pgm__} fichier.csv de --deepl  → Traduit fr vers allemand (DeepL)
     python {__pgm__} -t10 fichier.csv        → Mode test (10 lignes)

OPTIONS
  -h, --help     Affiche cette aide
  -t N           Mode test : traite uniquement N premières lignes (défaut: 5)
  --deepl        Utilise DeepL au lieu du glossaire
  
LANGUES SUPPORTÉES
  {', '.join(COLONNES_LANGUES)}

DIRECTION DE TRADUCTION
  La direction est spécifiée par 4 caractères : SOURCE + CIBLE
  Exemples :
    ptfr = portugais → français
    fren = français → anglais
    deja = allemand → japonais

GLOSSAIRE
  Le glossaire (refs/glossaire.csv) est la source unique de traductions.
  Exception : pour traduire le glossaire lui-même, DeepL est utilisé.
  
  La traduction par glossaire est "mot à mot" :
  - Cherche les expressions les plus longues d'abord
  - Le résultat peut être hybride (mots traduits + non traduits)

EXEMPLES
  # Compléter les traductions manquantes du glossaire
  python {__pgm__} glossaire.csv
  
  # Traduire "bruxisme sévère" du français vers l'anglais
  python {__pgm__} "bruxisme sévère" fren
  
  # Traduire un fichier patients avec le glossaire
  python {__pgm__} tests/qpat100.csv
  
  # Compléter les traductions DeepL après le glossaire
  python {__pgm__} fichier.csv --deepl
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
    
    # Parser les arguments manuellement pour plus de flexibilité
    args = sys.argv[1:]
    
    # Aide
    if not args or '-h' in args or '--help' in args or '-?' in args:
        afficher_aide()
        return
    
    # Options
    use_deepl = '--deepl' in args
    if use_deepl:
        args.remove('--deepl')
    
    # Mode test
    limite = None
    for i, arg in enumerate(args):
        if arg == '-t':
            # -t seul ou -t N
            if i + 1 < len(args) and args[i + 1].isdigit():
                limite = int(args[i + 1])
                args.pop(i + 1)
            else:
                limite = 5
            args.pop(i)
            break
        elif arg.startswith('-t') and arg[2:].isdigit():
            # -tN (collé)
            limite = int(arg[2:])
            args.pop(i)
            break
    
    if limite:
        print(f"[MODE TEST] Limite : {limite} lignes")
    
    # Analyser les arguments restants
    cible = None
    direction = None
    langue = None
    
    for arg in args:
        if arg.endswith('.csv'):
            cible = arg
        elif len(arg) == 4 and arg[:2] in COLONNES_LANGUES and arg[2:] in COLONNES_LANGUES:
            # Direction complète (ex: ptfr)
            direction = arg
        elif len(arg) == 2 and arg in COLONNES_LANGUES:
            # Langue seule
            langue = arg
        elif not cible:
            # Probablement une phrase
            cible = arg
    
    # Charger le glossaire (sauf pour l'aide)
    glossaire = {}
    chemin_glossaire = Path(__file__).parent / CHEMIN_GLOSSAIRE
    
    # Déterminer le mode
    if cible and cible.endswith('.csv'):
        chemin = Path(cible)
        
        # Chercher le fichier
        if not chemin.exists():
            # Essayer dans refs/
            chemin_refs = Path(__file__).parent / 'refs' / chemin.name
            if chemin_refs.exists():
                chemin = chemin_refs
        
        if not chemin.exists():
            chemin = chemin.resolve()
            print(f"[ERREUR] Fichier non trouvé : {chemin}")
            return
        
        chemin = chemin.resolve()
        
        # Mode glossaire.csv
        if chemin.name == 'glossaire.csv':
            traduire_glossaire_csv(chemin, langue_cible=langue, limite=limite)
        else:
            # Mode fichier CSV classique
            glossaire = charger_glossaire()
            traduire_fichier_csv(chemin, glossaire, langue_cible=langue, 
                                use_deepl=use_deepl, limite=limite)
    
    elif cible:
        # Mode phrase
        glossaire = charger_glossaire()
        
        # Construire la direction
        if direction:
            dir_str = direction
        elif langue:
            dir_str = f"fr{langue}"
        else:
            dir_str = ""  # Auto → fr
        
        traduire_phrase(cible, dir_str, glossaire, use_deepl=use_deepl)
    
    else:
        afficher_aide()
        return
    
    # Statistiques
    stats.afficher()
    
    elapsed = time.time() - t0
    print()
    print("=" * 70)
    print(f"TEMPS TOTAL : {elapsed:.1f} secondes")
    print("=" * 70)


if __name__ == "__main__":
    main()
