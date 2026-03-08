# detangles.py V1.0.10 - 14/01/2026 17:23:12
__pgm__ = "detangles.py"
__version__ = "1.0.10"
__date__ = "14/01/2026 17:23:12"

"""
Module de détection des angles céphalométriques dans une question en langage naturel.

Ce module analyse une question pour détecter des angles céphalométriques (ANB, SNA, SNB)
et la mesure AO-BO (Wits Appraisal) pour les convertir en tags orthodontiques qualifiés.

CHANGEMENTS V1.1.1 (14/01/2026) :
- CORRECTIF : Évaluation intelligente étendue à TOUS les patterns (>, <, BETWEEN)
  * Avant : seulement les patterns d'égalité (BETWEEN) déclenchaient l'évaluation
  * Maintenant : "SNA > 84" → 84 ∈ [80,86] → "maxillaire normopositionné"
- AMÉLIORATION : Le label affiche l'opérateur original (ex: "SNA > 84°" au lieu de "SNA = 84°")

CHANGEMENTS V1.1.0 (13/01/2026) :
- AJOUT : Détection de la mesure AO-BO (Wits Appraisal) - Jacobson 1975
  * Patterns : "ao bo", "aobo", "wits", "longueur ao bo"
  * Unité : millimètres (mm) - c'est une longueur, pas un angle
  * Seuils : Classe I (-1 à 1 mm), Classe II (> 1 mm), Classe III (< -1 mm)
- AJOUT : 'aobo' dans SEUILS_CLINIQUES pour l'évaluation intelligente
- MODIF : _identifier_type_angle() reconnaît maintenant 'aobo', 'ao bo', 'wits'
- MODIF : Préservation du signe négatif dans standardise() fallback

CHANGEMENTS V1.0.7 (08/01/2026) :
- AJOUT : Évaluation intelligente pour les patterns d'égalité (ANB = X)
  * Quand l'utilisateur écrit "ANB = 0", la valeur est testée contre TOUS les seuils
  * ANB = 0 → 0 < 2 → Classe III squelettique (et non pas rejeté)
  * Fonctionne pour ANB, SNA, SNB avec leurs seuils cliniques respectifs
- AJOUT : Dictionnaire SEUILS_CLINIQUES avec les classifications orthodontiques
- AJOUT : Fonction _evaluer_egalite_clinique() pour l'évaluation intelligente
- AJOUT : Détection du type d'angle (anb/sna/snb) dans le pattern matché

CHANGEMENTS V1.0.6 (17/12/2025) :
- Suppression de 'position' dans les critères (usage interne uniquement)
- Suppression de 'adjectifs_possibles' (non utilisé en sortie)
- Valeurs SQL en forme canonique (avec accents) au lieu de standardisée

POSITION DANS LA CHAÎNE DE DÉTECTION :
    detall.py
      ├── detcount.py      → LIST/COUNT
      ├── detangles.py     → Angles céphalo → tags qualifiés ◄ CE MODULE
      ├── dettags.py       → Tags + adjectifs
      └── detage.py        → Âge/sexe

detangles.py est appelé AVANT dettags.py car :
1. Les angles céphalo sont logiquement des tags (pathologies/caractéristiques)
2. Ils doivent être détectés en priorité avec leurs patterns spécifiques
3. Les résultats alimentent la même structure de tags que dettags.py

LOGIQUE DE DÉTECTION (Option A - clinique) :
- L'utilisateur écrit "ANB > 5" → capture de la valeur 5
- Vérification clinique : 5 > 4 (seuil de Classe II) → vrai
- Résultat : Tag "classe ii squelettique"

FORMAT DE SORTIE JSON :
{
    "criteres": [
        {
            "type": "tag",
            "detecte": "anb > 5",
            "canonique": "classe ii squelettique",
            "label": "Classe II squelettique",
            "sql": {"colonne": "canontags", "operateur": "=", "valeur": "classe ii squelettique"}
        }
    ],
    "residu": "patients avec un angle"
}

Usage en import :
    from detangles import charger_patterns_angles, detecter_angles
    patterns_angles = charger_patterns_angles('refs/angles.csv')
    resultat = detecter_angles(question, patterns_angles, verbose=True)

Usage CLI unitaire :
    python detangles.py "patients avec ANB > 4°" [--verbose] [--debug]

Usage CLI batch :
    python detangles.py tests/testsanglesin.csv [--verbose] [--debug]
    # Sortie automatique : tests/testsanglesout.csv
"""

import re
import csv
import argparse
import sys
import os
import json
from pathlib import Path

# Import de standardise (doit être dans le même répertoire ou PYTHONPATH)
try:
    from standardise import standardise
except ImportError:
    # Fallback si standardise.py n'est pas disponible
    import unicodedata
    def standardise(texte):
        """Version simplifiée de standardise si le module n'est pas disponible."""
        if texte is None or texte == "":
            return ""
        texte = texte.lower()
        texte = unicodedata.normalize('NFD', texte)
        texte = ''.join(char for char in texte if unicodedata.category(char) != 'Mn')
        # Supprimer ° et "degré(s)"
        texte = texte.replace('°', ' ')
        texte = re.sub(r'\bdegres?\b', ' ', texte)
        # Supprimer ponctuation SAUF le "-" devant un chiffre (signe négatif)
        for char in ".!_?":
            texte = texte.replace(char, " ")
        # Remplacer "-" par espace SAUF si suivi d'un chiffre (signe négatif)
        texte = re.sub(r'-(?!\d)', ' ', texte)
        texte = re.sub(r'\s+', ' ', texte)
        return texte.strip()


# ═══════════════════════════════════════════════════════════════════════════════
# SEUILS CLINIQUES V1.0.7 - Évaluation intelligente des patterns d'égalité
# ═══════════════════════════════════════════════════════════════════════════════
# Ces seuils sont utilisés quand l'utilisateur écrit "ANB = X" pour déterminer
# automatiquement la classification orthodontique basée sur la valeur X.

SEUILS_CLINIQUES = {
    'anb': {
        # ANB : Relation maxillo-mandibulaire (moyenne 3° ± 1°)
        'classifications': [
            {'condition': lambda v: v < 2, 'tag': 'classe iii squelettique', 'label': 'Classe III squelettique'},
            {'condition': lambda v: 2 <= v <= 4, 'tag': 'classe i squelettique', 'label': 'Classe I squelettique'},
            {'condition': lambda v: v > 4, 'tag': 'classe ii squelettique', 'label': 'Classe II squelettique'},
        ]
    },
    'sna': {
        # SNA : Position maxillaire (moyenne 83° ± 3°)
        'classifications': [
            {'condition': lambda v: v < 80, 'tag': 'rétrognathie maxillaire', 'label': 'Rétrognathie maxillaire'},
            {'condition': lambda v: 80 <= v <= 86, 'tag': 'maxillaire normopositionné', 'label': 'Position maxillaire normale'},
            {'condition': lambda v: v > 86, 'tag': 'prognathisme maxillaire', 'label': 'Prognathisme maxillaire'},
        ]
    },
    'snb': {
        # SNB : Position mandibulaire (moyenne 80° ± 3°)
        'classifications': [
            {'condition': lambda v: v < 77, 'tag': 'rétrognathie mandibulaire', 'label': 'Rétrognathie mandibulaire'},
            {'condition': lambda v: 77 <= v <= 83, 'tag': 'mandibule normopositionnée', 'label': 'Position mandibulaire normale'},
            {'condition': lambda v: v > 83, 'tag': 'prognathie mandibulaire', 'label': 'Prognathie mandibulaire'},
        ]
    },
    'aobo': {
        # AO-BO (Wits Appraisal) : Relation sagittale des bases osseuses - Jacobson 1975
        # Valeurs en mm : Femmes -1 à 0 mm / Hommes 0 à +1 mm
        # Moyenne simplifiée : entre -1 et 1 mm pour Classe I
        'classifications': [
            {'condition': lambda v: v < -1, 'tag': 'classe iii squelettique', 'label': 'Classe III squelettique (Wits)'},
            {'condition': lambda v: -1 <= v <= 1, 'tag': 'classe i squelettique', 'label': 'Classe I squelettique (Wits)'},
            {'condition': lambda v: v > 1, 'tag': 'classe ii squelettique', 'label': 'Classe II squelettique (Wits)'},
        ]
    }
}


def _identifier_type_angle(texte_matche):
    """
    Identifie le type d'angle (anb, sna, snb, aobo) dans le texte matché.
    
    Args:
        texte_matche: Texte capturé par le pattern (ex: "anb = 0", "ao bo moins de 3")
        
    Returns:
        str ou None: 'anb', 'sna', 'snb', 'aobo' ou None si non identifié
    """
    texte_lower = texte_matche.lower()
    if 'anb' in texte_lower:
        return 'anb'
    elif 'sna' in texte_lower:
        return 'sna'
    elif 'snb' in texte_lower:
        return 'snb'
    elif 'aobo' in texte_lower or 'ao bo' in texte_lower or 'wits' in texte_lower:
        return 'aobo'
    return None


def _evaluer_egalite_clinique(valeur, type_angle, verbose=False, debug=False):
    """
    Évalue une valeur d'angle contre les seuils cliniques pour déterminer
    automatiquement la classification orthodontique.
    
    Cette fonction est utilisée quand l'utilisateur écrit "ANB = X" :
    au lieu de rejeter le pattern si X n'est pas dans la plage attendue,
    on détermine quelle classification correspond à la valeur X.
    
    Args:
        valeur: Valeur numérique de l'angle (ex: 0, 5, -2)
        type_angle: Type d'angle ('anb', 'sna', 'snb')
        verbose: Afficher les résultats
        debug: Afficher les détails
        
    Returns:
        dict ou None: {'tag': str, 'label': str} si classification trouvée, None sinon
    """
    if type_angle not in SEUILS_CLINIQUES:
        if debug:
            print(f"[DEBUG] _evaluer_egalite_clinique: Type d'angle inconnu: {type_angle}")
        return None
    
    classifications = SEUILS_CLINIQUES[type_angle]['classifications']
    
    for classif in classifications:
        if classif['condition'](valeur):
            if debug:
                print(f"[DEBUG] _evaluer_egalite_clinique: {type_angle.upper()} = {valeur} → {classif['tag']}")
            return {'tag': classif['tag'], 'label': classif['label']}
    
    if debug:
        print(f"[DEBUG] _evaluer_egalite_clinique: Aucune classification pour {type_angle} = {valeur}")
    return None


def _est_pattern_egalite(operateur, expression_norm):
    """
    Détermine si un pattern est un pattern d'égalité simple (ANB = X).
    
    Args:
        operateur: Opérateur du pattern (BETWEEN, >, <, etc.)
        expression_norm: Expression normalisée du pattern
        
    Returns:
        bool: True si c'est un pattern d'égalité
    """
    # Un pattern d'égalité a généralement BETWEEN comme opérateur
    # mais représente "anb = {n}" ou "anb={n}"
    if operateur != 'BETWEEN':
        return False
    
    # Vérifier que c'est une expression d'égalité simple
    # (contient "=" mais pas ">" ou "<")
    return '=' in expression_norm and '>' not in expression_norm and '<' not in expression_norm


def _build_angle_regex(expression):
    r"""
    Transforme une expression du CSV en regex.
    
    Règles :
    - Standardise l'expression
    - Échappe tous les caractères spéciaux SAUF |
    - Remplace {n} par des groupes capturants pour nombres (entiers ou décimaux)
    - Remplace {1}, {2} par des références aux groupes
    - Remplace les espaces par \s*
    
    Args:
        expression: Expression du CSV (ex: "anb > {n}")
        
    Returns:
        Regex compilable (string)
    """
    # Standardiser
    expr_norm = standardise(expression)
    
    # Échapper caractère par caractère, sauf | et espaces
    result = []
    i = 0
    while i < len(expr_norm):
        char = expr_norm[i]
        if char == '|':
            result.append('|')
        elif char == ' ':
            result.append(' ')
        elif char in r'\^$.*+?{}[]()':
            result.append('\\' + char)
        else:
            result.append(char)
        i += 1
    p = ''.join(result)
    
    # Remplacer \{n\} par des groupes capturants pour nombres (entiers ou décimaux avec . ou ,)
    p = re.sub(r'\\{n\\}', r'(-?\\d+(?:[.,]\\d+)?)', p)
    
    # Remplacer \{1\}, \{2\} par des références (si utilisés dans les patterns)
    p = re.sub(r'\\{(\d+)\\}', r'\\\\\\1', p)
    
    # Autoriser zéro ou plusieurs espaces entre les tokens
    p = p.replace(" ", r"\s*")
    
    return p


def _compter_mots(texte):
    """Compte le nombre de mots dans un texte normalisé."""
    if not texte:
        return 0
    return len(texte.split())


def _parse_seuil(seuil_str):
    """
    Parse une valeur de seuil depuis le CSV.
    
    Args:
        seuil_str: String comme "4", "0,4", "{1},{2}", "80,84"
        
    Returns:
        - Pour un seuil simple : float
        - Pour BETWEEN : tuple (min, max) ou ('ref', 1, 2) si références
        - None si vide
    """
    if not seuil_str or not seuil_str.strip():
        return None
    
    seuil_str = seuil_str.strip()
    
    # Vérifier si c'est une référence {1},{2}
    if '{' in seuil_str:
        # Extraire les références
        refs = re.findall(r'\{(\d+)\}', seuil_str)
        if len(refs) == 2:
            return ('ref', int(refs[0]), int(refs[1]))
        elif len(refs) == 1:
            return ('ref', int(refs[0]))
        return None
    
    # Vérifier si c'est une plage "min,max"
    if ',' in seuil_str:
        parts = seuil_str.split(',')
        if len(parts) == 2:
            try:
                return (float(parts[0].strip()), float(parts[1].strip()))
            except ValueError:
                return None
    
    # Seuil simple
    try:
        return float(seuil_str.replace(',', '.'))
    except ValueError:
        return None


def evaluer_condition(valeur_capturee, operateur, seuil, valeurs_capturees=None):
    """
    Évalue si la valeur capturée satisfait la condition clinique.
    
    La logique est CLINIQUE : on vérifie si la valeur de l'utilisateur
    correspond à la classification orthodontique.
    
    Exemple : ANB > 5 avec seuil 4 → on vérifie 5 > 4 → vrai → Classe II
    
    Args:
        valeur_capturee: Valeur numérique extraite de la question
        operateur: '>', '<', '>=', '<=', '=', 'BETWEEN'
        seuil: Valeur(s) de référence (float ou tuple)
        valeurs_capturees: Liste complète des valeurs (pour références {1}, {2})
        
    Returns:
        bool: True si la condition est satisfaite
    """
    if valeur_capturee is None:
        return False
    
    # Gérer les références pour BETWEEN avec {1}, {2}
    if isinstance(seuil, tuple) and len(seuil) >= 2:
        if seuil[0] == 'ref':
            # Les seuils sont les valeurs capturées elles-mêmes
            if valeurs_capturees and len(valeurs_capturees) >= 2:
                seuil = (valeurs_capturees[0], valeurs_capturees[1])
            else:
                return False
    
    if operateur == '>':
        return valeur_capturee > seuil
    elif operateur == '<':
        return valeur_capturee < seuil
    elif operateur == '>=':
        return valeur_capturee >= seuil
    elif operateur == '<=':
        return valeur_capturee <= seuil
    elif operateur == '=' or operateur == '':
        # Pour '=' sur un angle, on vérifie si dans la plage normale
        if isinstance(seuil, tuple):
            return seuil[0] <= valeur_capturee <= seuil[1]
        return valeur_capturee == seuil
    elif operateur == 'BETWEEN':
        if isinstance(seuil, tuple) and len(seuil) >= 2:
            if seuil[0] == 'ref':
                # Déjà géré au-dessus
                return False
            return seuil[0] <= valeur_capturee <= seuil[1]
        return False
    
    return False


def charger_patterns_angles(fichier_csv, verbose=False, debug=False):
    """
    Charge les patterns d'angles depuis angles.csv
    
    Format CSV : expression;operateur;seuil;tag_canonique;adjectifs_possibles;label
    
    Args:
        fichier_csv: Chemin vers angles.csv
        verbose: Afficher les informations de chargement
        debug: Afficher les détails complets
        
    Returns:
        Liste de dicts, chaque dict contenant :
        {
            'patterns': [{'regex': str, 'expression': str, 'expression_norm': str, 'nb_mots': int}, ...],
            'operateur': str,
            'seuil': float ou tuple,
            'tag_canonique': str,
            'adjectifs_possibles': list,
            'label': str,
            'expression_complete': str
        }
    """
    patterns_par_ligne = []
    
    if not os.path.exists(fichier_csv):
        print(f"[ERREUR] Fichier patterns introuvable: {os.path.abspath(fichier_csv)}")
        return patterns_par_ligne
    
    if debug:
        print(f"[DEBUG] detangles: Chargement depuis {os.path.abspath(fichier_csv)}")
    
    # Essayer différents encodages
    encodages = ["utf-8-sig", "utf-8", "windows-1252", "iso-8859-1"]
    
    for encodage in encodages:
        try:
            with open(fichier_csv, 'r', encoding=encodage, newline='') as f:
                reader = csv.reader(f, delimiter=';')
                ligne_num = 0
                lignes_valides = 0
                
                for row in reader:
                    ligne_num += 1
                    
                    # Ignorer lignes vides ou commentaires
                    if not row or (row[0] or '').strip().startswith('#'):
                        continue
                    
                    # Ignorer la ligne d'en-tête
                    if ligne_num <= 2 and 'expression' in (row[0] or '').lower():
                        continue
                    
                    # Format : expression;operateur;seuil;tag_canonique;adjectifs_possibles;label
                    if len(row) < 6:
                        if debug:
                            print(f"[DEBUG] Ligne {ligne_num} ignorée (moins de 6 colonnes): {row}")
                        continue
                    
                    expression_brute = (row[0] or '').strip()
                    operateur = (row[1] or '').strip().upper()
                    seuil_str = (row[2] or '').strip()
                    tag_canonique = (row[3] or '').strip().lower()
                    adjectifs_str = (row[4] or '').strip()
                    label = (row[5] or '').strip()
                    
                    if not expression_brute:
                        continue
                    
                    # Parser le seuil
                    seuil = _parse_seuil(seuil_str)
                    
                    # Parser les adjectifs possibles
                    adjectifs_possibles = []
                    if adjectifs_str:
                        adjectifs_possibles = [a.strip() for a in adjectifs_str.split(',') if a.strip()]
                    
                    # Exploser les patterns sur |
                    alternatives = expression_brute.split('|')
                    patterns_ligne = []
                    
                    for alt in alternatives:
                        alt = alt.strip()
                        if not alt:
                            continue
                        
                        try:
                            # Construire la regex
                            pattern_regex = _build_angle_regex(alt)
                            alt_norm = standardise(alt)
                            nb_mots = _compter_mots(alt_norm)
                            
                            patterns_ligne.append({
                                'regex': pattern_regex,
                                'expression': alt,
                                'expression_norm': alt_norm,
                                'nb_mots': nb_mots
                            })
                            
                        except Exception as e:
                            if debug:
                                print(f"[DEBUG] Erreur pattern '{alt}': {e}")
                            continue
                    
                    if patterns_ligne:
                        # Trier les patterns de cette ligne par nb_mots décroissant
                        patterns_ligne.sort(key=lambda x: x['nb_mots'], reverse=True)
                        
                        patterns_par_ligne.append({
                            'patterns': patterns_ligne,
                            'operateur': operateur,
                            'seuil': seuil,
                            'tag_canonique': tag_canonique,
                            'adjectifs_possibles': adjectifs_possibles,
                            'label': label,
                            'expression_complete': expression_brute
                        })
                        lignes_valides += 1
                        
                        if debug and lignes_valides <= 5:
                            print(f"[DEBUG] Ligne {ligne_num}: {len(patterns_ligne)} patterns, tag='{tag_canonique}'")
                            print(f"  Premier pattern: '{patterns_ligne[0]['expression']}' ({patterns_ligne[0]['nb_mots']} mots)")
                
                if verbose or debug:
                    print(f"✓ {lignes_valides} lignes de patterns chargées depuis {os.path.abspath(fichier_csv)}")
                
                return patterns_par_ligne
                
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            if debug:
                print(f"[DEBUG] Erreur encodage {encodage}: {e}")
            continue
    
    print(f"[ERREUR] Impossible de lire {os.path.abspath(fichier_csv)}")
    return patterns_par_ligne


def _construire_label_final(label_template, valeurs_capturees):
    """
    Remplace les placeholders dans le label par les valeurs capturées.
    
    Args:
        label_template: Label avec placeholders (ex: "Classe I squelettique (ANB {1}° à {2}°)")
        valeurs_capturees: Liste des valeurs capturées [2, 4]
        
    Returns:
        Label final (ex: "Classe I squelettique (ANB 2° à 4°)")
    """
    if not valeurs_capturees:
        return label_template
    
    label_final = label_template
    
    # Remplacer {1}, {2}, etc.
    for i, val in enumerate(valeurs_capturees, 1):
        label_final = label_final.replace(f'{{{i}}}', str(int(val) if val == int(val) else val))
    
    # Remplacer {n} génériques
    for val in valeurs_capturees:
        label_final = label_final.replace('{n}', str(int(val) if val == int(val) else val), 1)
    
    return label_final


def detecter_angles(question, patterns_angles, verbose=False, debug=False):
    """
    Détecte les angles céphalométriques dans une question.
    
    Cette fonction analyse la question et retourne des critères de type 'tag'
    au format JSON unifié.
    
    Args:
        question: Texte de la question en langage naturel
        patterns_angles: Liste de patterns (retournée par charger_patterns_angles)
        verbose: Afficher les résultats intermédiaires
        debug: Afficher tous les détails
        
    Returns:
        dict: {
            'criteres': [
                {
                    'type': 'tag',
                    'detecte': str,
                    'canonique': str,
                    'label': str,
                    'sql': {'colonne': 'canontags', 'operateur': '=', 'valeur': str}
                },
                ...
            ],
            'residu': 'texte restant',
            'question_standardisee': str
        }
    """
    question_norm = standardise(question)
    mots_question = question_norm.split()
    mots_utilises = set()
    criteres_detectes = []
    
    if debug:
        print(f"[DEBUG] detangles: Question originale: '{question}'")
        print(f"[DEBUG] detangles: Question normalisée: '{question_norm}'")
        print(f"[DEBUG] detangles: Mots: {mots_question}")
    
    # Collecter tous les patterns avec leur ligne parente, triés par nb_mots décroissant
    tous_patterns = []
    for ligne_data in patterns_angles:
        for pattern_info in ligne_data['patterns']:
            tous_patterns.append({
                'pattern_info': pattern_info,
                'ligne_data': ligne_data
            })
    
    # Trier par nombre de mots décroissant (patterns les plus longs d'abord)
    tous_patterns.sort(key=lambda x: x['pattern_info']['nb_mots'], reverse=True)
    
    if debug:
        print(f"[DEBUG] detangles: {len(tous_patterns)} patterns à tester (triés par longueur)")
    
    # Lignes déjà matchées (pour éviter de matcher plusieurs patterns de la même ligne)
    lignes_matchees = set()
    
    for item in tous_patterns:
        pattern_info = item['pattern_info']
        ligne_data = item['ligne_data']
        
        # Si cette ligne a déjà été matchée, passer
        ligne_id = id(ligne_data)
        if ligne_id in lignes_matchees:
            continue
        
        regex = pattern_info['regex']
        
        # Chercher le pattern dans la question
        try:
            match = re.search(regex, question_norm, re.IGNORECASE)
        except re.error as e:
            if debug:
                print(f"[DEBUG] Erreur regex '{regex}': {e}")
            continue
        
        if match:
            texte_matche = match.group(0)
            mots_matche = texte_matche.split()
            
            # Vérifier que les mots ne sont pas déjà utilisés
            if any(mot in mots_utilises for mot in mots_matche if mot):
                continue
            
            # Capturer les valeurs numériques (gérer virgule décimale)
            valeurs_capturees = []
            for g in match.groups():
                if g:
                    try:
                        valeurs_capturees.append(float(g.replace(',', '.')))
                    except ValueError:
                        pass
            
            if debug:
                print(f"[DEBUG] Match trouvé: '{texte_matche}', valeurs: {valeurs_capturees}")
                print(f"[DEBUG]   Opérateur: {ligne_data['operateur']}, Seuil: {ligne_data['seuil']}")
            
            # Évaluer la condition clinique
            tag_override = None  # V1.0.7 : Pour évaluation intelligente des égalités
            label_override = None
            
            if ligne_data['operateur'] and ligne_data['seuil'] is not None:
                # Pattern avec condition numérique
                if not valeurs_capturees:
                    if debug:
                        print(f"[DEBUG]   → Pas de valeur capturée, skip")
                    continue
                
                valeur_principale = valeurs_capturees[0]
                condition_ok = evaluer_condition(
                    valeur_principale,
                    ligne_data['operateur'],
                    ligne_data['seuil'],
                    valeurs_capturees
                )
                
                if not condition_ok:
                    # V1.1.1 : Évaluation intelligente pour TOUS les patterns d'angles
                    # Quand l'utilisateur écrit "SNA > 84", on évalue 84 contre les seuils cliniques
                    # pour déterminer la classification (84 ∈ [80,86] → maxillaire normopositionné)
                    type_angle = _identifier_type_angle(texte_matche)
                    
                    if type_angle:
                        # Tenter l'évaluation clinique intelligente
                        classif = _evaluer_egalite_clinique(valeur_principale, type_angle, verbose, debug)
                        
                        if classif:
                            # Classification trouvée via évaluation intelligente
                            tag_override = classif['tag']
                            # V1.1.0 : Utiliser mm pour AO-BO (longueur), ° pour les angles
                            unite = 'mm' if type_angle == 'aobo' else '°'
                            valeur_affichee = int(valeur_principale) if valeur_principale == int(valeur_principale) else valeur_principale
                            # Afficher l'opérateur original dans le label
                            op_display = ligne_data['operateur'] if ligne_data['operateur'] in ('>', '<', '>=', '<=') else '='
                            label_override = f"{classif['label']} ({type_angle.upper()} {op_display} {valeur_affichee}{unite})"
                            if debug:
                                print(f"[DEBUG]   → Évaluation intelligente: {type_angle.upper()} {op_display} {valeur_principale} → {tag_override}")
                        else:
                            if debug:
                                print(f"[DEBUG]   → Condition non satisfaite et pas de classification: {valeur_principale} {ligne_data['operateur']} {ligne_data['seuil']}")
                            continue
                    else:
                        if debug:
                            print(f"[DEBUG]   → Condition non satisfaite: {valeur_principale} {ligne_data['operateur']} {ligne_data['seuil']}")
                        continue
                else:
                    if debug:
                        print(f"[DEBUG]   → Condition satisfaite!")
            
            # Construire le label final
            if label_override:
                label_final = label_override
            else:
                label_final = _construire_label_final(ligne_data['label'], valeurs_capturees)
            
            # Trouver la position dans la question originale (approximatif)
            pos_debut = question_norm.find(texte_matche)
            pos_fin = pos_debut + len(texte_matche) if pos_debut >= 0 else -1
            
            # V1.0.7 : Utiliser tag_override si défini (évaluation intelligente)
            tag_final = tag_override if tag_override else ligne_data['tag_canonique']
            
            # Créer le critère (SANS position - usage interne uniquement)
            # La valeur SQL est la forme canonique du tag
            critere = {
                'type': 'tag',
                'detecte': texte_matche,
                'canonique': tag_final,
                'label': label_final,
                'sql': {
                    'colonne': 'canontags',
                    'operateur': '=',
                    'valeur': tag_final  # Forme canonique pour SQL
                }
            }
            
            # Note: Les angles n'ont pas d'adjectifs associés
            
            criteres_detectes.append(critere)
            
            # Marquer les mots comme utilisés
            for mot in mots_matche:
                if mot:
                    mots_utilises.add(mot)
            
            # Marquer cette ligne comme matchée
            lignes_matchees.add(ligne_id)
            
            if verbose or debug:
                print(f"  ✓ Détecté: '{texte_matche}' → {tag_final} ({label_final})")
    
    # Calculer le résidu
    residu = ' '.join([m for m in mots_question if m not in mots_utilises])
    
    if debug:
        print(f"[DEBUG] detangles: {len(criteres_detectes)} critère(s) détecté(s)")
        print(f"[DEBUG] detangles: Résidu: '{residu}'")
    
    return {
        'criteres': criteres_detectes,
        'residu': residu,
        'question_standardisee': question_norm
    }


def identifier_angles(residu, patterns_angles, filtres, verbose=False, debug=False):
    """
    Wrapper de compatibilité avec signature standard.
    
    SIGNATURE STANDARD pour tous les modules detXXX :
        identifier_XXX(residu, data, filtres, verbose=False, debug=False) -> (filtres, residu)
    
    Args:
        residu: Texte restant après détections précédentes
        patterns_angles: Liste de patterns (retournée par charger_patterns_angles)
        filtres: Dict à enrichir {'listcount': ..., 'criteres': [...]}
        verbose: Mode verbose (résultats intermédiaires)
        debug: Mode debug (tous les détails)
        
    Returns:
        Tuple (filtres, residu)
        - filtres['criteres'] est enrichi avec les critères détectés
        - residu contient les mots non matchés
    """
    if debug:
        print(f"[DEBUG] identifier_angles: Analyse du résidu: '{residu}'")
    
    # Appeler la fonction de détection
    resultat = detecter_angles(residu, patterns_angles, verbose=verbose, debug=debug)
    
    # Enrichir filtres['criteres'] avec les nouveaux critères
    if 'criteres' not in filtres:
        filtres['criteres'] = []
    
    for critere in resultat['criteres']:
        filtres['criteres'].append(critere)
    
    if verbose or debug:
        print(f"[DEBUG] identifier_angles: {len(resultat['criteres'])} critère(s) ajouté(s)")
    
    # Retourner filtres enrichi + nouveau résidu
    return filtres, resultat['residu']


def traiter_fichier_batch(fichier_entree, patterns_angles, verbose=False, debug=False):
    """
    Traite un fichier de test batch et génère [nom_entrée]detangles.csv.
    
    Format d'entrée : CSV avec colonne 'question'
    Format de sortie : question;L1;L2;...;Ln (résumé transposé)
    """
    # Déterminer le fichier de sortie
    chemin_entree = Path(fichier_entree)
    nom_base = chemin_entree.stem
    module_name = Path(__pgm__).stem  # 'detangles'
    fichier_sortie = chemin_entree.parent / f"{nom_base}{module_name}.csv"
    
    if verbose or debug:
        print(f"Fichier d'entrée : {os.path.abspath(fichier_entree)}")
        print(f"Fichier de sortie: {os.path.abspath(fichier_sortie)}")
        print()
    
    # Lire le fichier d'entrée
    lignes_entree = []
    col_indices = {}  # indices des colonnes résultat/commentaire
    commentaires = []
    
    encodages = ["utf-8-sig", "utf-8", "windows-1252"]
    contenu_lu = False
    
    for encodage in encodages:
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
                        continue  # Ignorer l'en-tête
                    lignes_entree.append(row)
            contenu_lu = True
            break
        except (UnicodeDecodeError, UnicodeError):
            continue
    
    if not contenu_lu:
        print(f"[ERREUR] Impossible de lire {fichier_entree}")
        return 0, None
    
    # Traiter chaque ligne
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
        
        # Détecter avec le nouveau format
        resultat = detecter_angles(question, patterns_angles, verbose=verbose, debug=debug)
        
        # Extraire les labels
        labels = [c['label'] for c in resultat['criteres']]
        canoniques = [c['canonique'] for c in resultat['criteres']]
        nb_criteres = len(labels)
        sorties_labels = ', '.join(labels)
        sorties_canoniques = ', '.join(canoniques)
        
        # Construire les lignes du résumé pour le CSV
        lignes_resume = []
        if resultat['criteres']:
            for j, c in enumerate(resultat['criteres'], 1):
                label = c.get('label', '?')
                canon = c.get('canonique', '')
                lignes_resume.append(f"[angle] {label} → {canon}")
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
                label = c.get('label', '?')
                canon = c.get('canonique', '')
                print(f"        {j}. [angle] {label} → {canon}")
        else:
            print(f"        (aucun angle)")
        print(f"        Résidu: '{resultat['residu']}'")
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
    
    print(f"✓ {len(resultats)} lignes traitées → {os.path.abspath(fichier_sortie)}")
    
    return len(resultats), fichier_sortie


def main():
    """Point d'entrée CLI."""
    print(f"╔════════════════════════════════════════════════════════════════")
    print(f"║ {__pgm__} V{__version__} - {__date__}")
    print(f"║ Détection des angles céphalométriques dans une question")
    print(f"╚════════════════════════════════════════════════════════════════")
    print()
    
    parser = argparse.ArgumentParser(
        description="Détecte les angles céphalométriques (ANB, SNA, SNB) dans une question"
    )
    parser.add_argument('question', help='Question en langage naturel OU fichier xxxin.csv')
    parser.add_argument('-v', '--verbose', action='store_true', help='Affichage modéré (résultats)')
    parser.add_argument('-d', '--debug', action='store_true', help='Affichage complet (tout)')
    parser.add_argument('--patterns', default='refs/angles.csv', help='Chemin vers angles.csv')
    
    args = parser.parse_args()
    
    # Déterminer si c'est un fichier batch ou une question unitaire
    fichier_batch = None
    if args.question.endswith('.csv'):
        # C'est censé être un fichier batch - chercher le fichier
        chemins_possibles = [
            args.question,                                    # Tel quel
            Path("tests") / args.question,                    # Dans tests/
            Path("tests") / Path(args.question).name,         # Nom seul dans tests/
            Path(__file__).parent / "tests" / args.question,  # Relatif au script
            Path("c:/g/tests") / Path(args.question).name,    # Chemin absolu Windows
        ]
        
        for chemin in chemins_possibles:
            if Path(chemin).exists():
                fichier_batch = str(chemin)
                break
        
        # Si fichier .csv non trouvé, c'est une erreur (pas une question)
        if fichier_batch is None:
            print(f"[ERREUR] Fichier batch introuvable: {args.question}")
            print(f"  Chemins testés:")
            for chemin in chemins_possibles:
                print(f"    - {os.path.abspath(chemin)}")
            return 1
    
    est_fichier_batch = fichier_batch is not None
    
    # Chercher le fichier patterns
    patterns_path = args.patterns
    if not os.path.exists(patterns_path):
        # Essayer des chemins alternatifs
        chemins_alternatifs = [
            Path(__file__).parent / "refs" / "angles.csv",
            Path("c:/g/refs/angles.csv"),
            Path("refs/angles.csv"),
        ]
        for chemin in chemins_alternatifs:
            if chemin.exists():
                patterns_path = str(chemin)
                break
    
    print(f"Fichier angles.csv: {os.path.abspath(patterns_path)}")
    print()
    
    # Charger les patterns
    patterns_angles = charger_patterns_angles(patterns_path, verbose=args.verbose, debug=args.debug)
    
    if not patterns_angles:
        print()
        print("[ERREUR] Aucun pattern chargé depuis angles.csv")
        return 1
    
    print()
    
    if est_fichier_batch:
        # Mode batch
        print(f"Mode BATCH - Traitement de {os.path.abspath(fichier_batch)}")
        print("-" * 70)
        nb_lignes, fichier_sortie = traiter_fichier_batch(
            fichier_batch, 
            patterns_angles, 
            verbose=args.verbose, 
            debug=args.debug
        )
        return 0 if nb_lignes > 0 else 1
    
    else:
        # Mode unitaire - sortie JSON
        print(f"Question: \"{args.question}\"")
        print()
        
        # Détecter les angles
        resultat = detecter_angles(
            args.question,
            patterns_angles,
            verbose=args.verbose,
            debug=args.debug
        )
        
        # Affichage résumé
        print()
        print(f"{len(resultat['criteres'])} angle(s) détecté(s) :")
        for i, c in enumerate(resultat['criteres'], 1):
            print(f"  {i}. '{c['detecte']}' → {c['canonique']}")
        
        print()
        print(f"Résidu : '{resultat['residu']}'")
        
        # Afficher le résultat en JSON formaté
        print()
        print("═" * 70)
        print("RÉSULTAT (JSON)")
        print("═" * 70)
        print(json.dumps(resultat, indent=2, ensure_ascii=False))
        
        return 0


if __name__ == '__main__':
    sys.exit(main())
