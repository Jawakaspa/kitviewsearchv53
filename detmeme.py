# detmeme.py V1.0.8 - 04/02/2026 16:10:00
__pgm__ = "detmeme.py"
__version__ = "1.0.8"
__date__ = "04/02/2026 16:10:00"

"""
Module de détection des expressions "même X" dans une question en langage naturel.

Ce module analyse une question pour détecter des demandes de similarité
(même tag, même pathologie, même portrait, même sexe, même âge, même nom, même prénom).

CHANGEMENTS V1.0.8 (04/02/2026) :
- FIX CRITIQUE : Ajout d'une vérification préalable de la présence d'un synonyme de "même"
- Avant : "système de bielles" → référence "bielles" (FAUX POSITIF)
- Après : "système de bielles" → pas de détection (correct)
- La référence n'est extraite que s'il y a effectivement un "même" dans la question

CHANGEMENTS V1.0.7 (25/01/2026) :
- CORRECTION BUG CRITIQUE : Les critères multiples sont maintenant correctement séparés
- Nouvelle stratégie : recherche de TOUTES les occurrences de "meme X" dans la chaîne
- Support des séparateurs : "et meme", ", meme", " meme" (juxtaposition)
- Chaque "meme X" génère un critère distinct

CHANGEMENTS V1.0.5 (21/01/2026) :
- Support de communb.csv (format vertical section;parametre;valeur)
- Fallback vers commun.csv (ancien format horizontal) si communb absent
- Priorité de recherche : communb.csv → commun.csv → valeurs par défaut

NOUVEAUTÉS V2.0.0 :
    - Support des critères multiples : "même X et même Y et même Z que Nom"
    - Extraction du nom du patient de référence
    - Support des tags/pathologies spécifiques : "même béance", "même bruxisme nocturne"
    - Nouveau format de sortie avec 'reference' et 'valeur' dans critères

CHANGEMENTS V1.0.9 (15/02/2026) :
    - Support des identifiants alphanumériques dans "que id XXX"
    - Avant : seuls les identifiants numériques (\\d+) étaient capturés
    - Après : "que id ABC123" fonctionne aussi ([a-zA-Z0-9]+)

FICHIER DE RÉFÉRENCE :
    communb.csv (format vertical) - section;parametre;valeur;description
    - synonymes;meme;valeurs... → synonymes de "même"
    - synonymes;que;valeurs... → synonymes de "que"

CIBLES DÉTECTÉES :
    - tag → colonne canontags (+ valeur spécifique si fournie)
    - pathologie → colonnes canontags + canonadjs (+ valeur spécifique si fournie)
    - portrait → colonne idportrait
    - sexe → colonne sexe
    - age → colonne age (BETWEEN age±3)
    - nom → colonne nom
    - prenom → colonne prenom

FORMAT DE SORTIE JSON V2.0 :
{
    "criteres": [
        {
            "type": "meme",
            "detecte": "même portrait",
            "cible": "portrait",
            "label": "Même portrait",
            "valeur": null
        },
        {
            "type": "meme",
            "detecte": "même bruxisme nocturne",
            "cible": "pathologie",
            "label": "Même pathologie",
            "valeur": "bruxisme nocturne"
        }
    ],
    "reference": {
        "type": "nom",           // "nom" ou "id"
        "valeur": "Guillaume Moulin",
        "id": null              // Si type="id", contient l'ID numérique
    },
    "residu": "texte restant après détection"
}

Usage en import (depuis detall.py) :
    from detmeme import charger_patterns_meme, detecter_meme
    patterns_meme = charger_patterns_meme('refs/commun.csv')
    resultat = detecter_meme(question, patterns_meme, verbose=True)

Usage CLI unitaire :
    python detmeme.py "même portrait et même prénom que Guillaume Moulin"

Usage CLI batch :
    python detmeme.py tests/testsmemein.csv
"""

import re
import csv
import argparse
import sys
import os
import json
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
# CIBLES DE SIMILARITÉ
# =============================================================================

# Mapping des mots-clés vers les cibles
# Format: mot_cle_standardisé → (cible, label)
CIBLES_MEME = {
    'tag': ('tag', 'Même tag'),
    'tags': ('tag', 'Même tag'),
    'pathologie': ('pathologie', 'Même pathologie'),
    'pathologies': ('pathologie', 'Même pathologie'),
    'portrait': ('portrait', 'Même portrait'),
    'portraits': ('portrait', 'Même portrait'),
    'photo': ('portrait', 'Même photo'),
    'photos': ('portrait', 'Même photo'),
    'sexe': ('sexe', 'Même sexe'),
    'genre': ('sexe', 'Même genre'),
    'age': ('age', 'Même âge'),
    'ages': ('age', 'Même âge'),
    'tranche d age': ('age', 'Même tranche d\'âge'),
    'nom': ('nom', 'Même nom'),
    'noms': ('nom', 'Même nom'),
    'nom de famille': ('nom', 'Même nom de famille'),
    'prenom': ('prenom', 'Même prénom'),
    'prenoms': ('prenom', 'Même prénom'),
}

# Synonymes par défaut si communb.csv non disponible
SYNONYMES_MEME_DEFAUT = ['meme', 'memes', 'identique', 'identiques', 'similaire', 'similaires', 'commun', 'communs', 'semblable', 'semblables']
SYNONYMES_QUE_DEFAUT = ['que', 'comme', 'de', 'du']


def _charger_synonymes_communb(fichier_csv: str, verbose=False, debug=False) -> Tuple[List[str], List[str]]:
    """
    Charge les synonymes de 'même' et 'que' depuis communb.csv (format vertical).
    
    Format communb.csv :
        section;parametre;valeur;description
        synonymes;meme;commun,semblable,...;Description
        synonymes;que;pareil,identique a,...;Description
    
    Args:
        fichier_csv: Chemin vers communb.csv
        verbose: Mode verbose
        debug: Mode debug
        
    Returns:
        Tuple (synonymes_meme, synonymes_que) ou (None, None) si format incorrect
    """
    synonymes_meme = []
    synonymes_que = []
    
    if not os.path.exists(fichier_csv):
        if debug:
            print(f"[DEBUG] detmeme: {fichier_csv} introuvable")
        return None, None
    
    encodages = ["utf-8-sig", "utf-8", "windows-1252", "iso-8859-1"]
    
    for encodage in encodages:
        try:
            with open(fichier_csv, 'r', encoding=encodage, newline='') as f:
                reader = csv.DictReader(
                    (line for line in f if not line.strip().startswith('#')),
                    delimiter=';'
                )
                
                # Vérifier si c'est le format vertical
                if not all(col in (reader.fieldnames or []) for col in ['section', 'parametre', 'valeur']):
                    if debug:
                        print(f"[DEBUG] detmeme: {fichier_csv} n'est pas au format vertical")
                    return None, None
                
                for row in reader:
                    section = (row.get('section') or '').strip().lower()
                    parametre = (row.get('parametre') or '').strip().lower()
                    valeur = (row.get('valeur') or '').strip()
                    
                    if section != 'synonymes':
                        continue
                    
                    if parametre == 'meme' and valeur:
                        for mot in valeur.split(','):
                            mot_std = standardise(mot.strip())
                            if mot_std and mot_std not in synonymes_meme:
                                synonymes_meme.append(mot_std)
                    
                    elif parametre == 'que' and valeur:
                        for mot in valeur.split(','):
                            mot_std = standardise(mot.strip())
                            if mot_std and mot_std not in synonymes_que:
                                synonymes_que.append(mot_std)
                
                # Ajouter les mots de base
                for mot in ['meme', 'memes']:
                    if mot not in synonymes_meme:
                        synonymes_meme.append(mot)
                
                for mot in ['que', 'comme', 'de']:
                    if mot not in synonymes_que:
                        synonymes_que.append(mot)
                
                # Trier par nombre de mots décroissant
                synonymes_meme.sort(key=lambda x: (-len(x.split()), x))
                synonymes_que.sort(key=lambda x: (-len(x.split()), x))
                
                if debug:
                    print(f"[DEBUG] detmeme: Chargé depuis {fichier_csv} (format vertical)")
                
                return synonymes_meme, synonymes_que
                
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            if debug:
                print(f"[DEBUG] detmeme: Erreur lecture {encodage}: {e}")
            continue
    
    return None, None


def _charger_synonymes_commun(fichier_csv: str, verbose=False, debug=False) -> Tuple[List[str], List[str]]:
    """
    Charge les synonymes de 'même' et 'que' depuis commun.csv.
    
    Args:
        fichier_csv: Chemin vers commun.csv
        verbose: Mode verbose
        debug: Mode debug
        
    Returns:
        Tuple (synonymes_meme, synonymes_que) triés par nb_mots décroissant
    """
    synonymes_meme = []
    synonymes_que = []
    
    if not os.path.exists(fichier_csv):
        if debug:
            print(f"[DEBUG] detmeme: commun.csv introuvable, utilisation des synonymes par défaut")
        return SYNONYMES_MEME_DEFAUT.copy(), SYNONYMES_QUE_DEFAUT.copy()
    
    encodages = ["utf-8-sig", "utf-8", "windows-1252", "iso-8859-1"]
    
    for encodage in encodages:
        try:
            with open(fichier_csv, 'r', encoding=encodage, newline='') as f:
                reader = csv.DictReader(
                    (line for line in f if not line.strip().startswith('#')),
                    delimiter=';'
                )
                
                if 'meme' not in reader.fieldnames or 'que' not in reader.fieldnames:
                    if debug:
                        print(f"[DEBUG] detmeme: Colonnes 'meme' ou 'que' absentes dans commun.csv")
                    continue
                
                seen_meme = set()
                seen_que = set()
                
                for row in reader:
                    # Colonne 'meme'
                    meme_val = (row.get('meme') or '').strip()
                    if meme_val:
                        meme_std = standardise(meme_val)
                        if meme_std and meme_std not in seen_meme:
                            seen_meme.add(meme_std)
                            synonymes_meme.append(meme_std)
                    
                    # Colonne 'que'
                    que_val = (row.get('que') or '').strip()
                    if que_val:
                        que_std = standardise(que_val)
                        if que_std and que_std not in seen_que:
                            seen_que.add(que_std)
                            synonymes_que.append(que_std)
                
                # Ajouter les mots de base s'ils ne sont pas déjà présents
                for mot in ['meme', 'memes']:
                    if mot not in seen_meme:
                        synonymes_meme.append(mot)
                
                for mot in ['que', 'comme', 'de']:
                    if mot not in seen_que:
                        synonymes_que.append(mot)
                
                # Trier par nombre de mots décroissant (expressions longues d'abord)
                synonymes_meme.sort(key=lambda x: (-len(x.split()), x))
                synonymes_que.sort(key=lambda x: (-len(x.split()), x))
                
                if verbose or debug:
                    print(f"  ✓ {len(synonymes_meme)} synonyme(s) 'même', {len(synonymes_que)} synonyme(s) 'que'")
                
                return synonymes_meme, synonymes_que
                
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            if debug:
                print(f"[DEBUG] detmeme: Erreur lecture {encodage}: {e}")
            continue
    
    # Fallback
    return SYNONYMES_MEME_DEFAUT.copy(), SYNONYMES_QUE_DEFAUT.copy()


def charger_patterns_meme(fichier_csv: str = None, verbose=False, debug=False) -> dict:
    """
    Charge les patterns de détection "même X" depuis communb.csv ou commun.csv.
    
    Ordre de recherche :
    1. communb.csv (format vertical section;parametre;valeur)
    2. commun.csv (ancien format horizontal)
    3. Valeurs par défaut
    
    Args:
        fichier_csv: Chemin vers le fichier (optionnel, cherche automatiquement)
        verbose: Afficher les informations de chargement
        debug: Afficher les détails complets
        
    Returns:
        Dict avec :
        {
            'synonymes_meme': [...],  # Synonymes de "même" triés
            'synonymes_que': [...],   # Synonymes de "que" triés
            'cibles': {...}           # Mapping mot-clé → (cible, label)
        }
    """
    script_dir = Path(__file__).parent
    synonymes_meme = None
    synonymes_que = None
    
    # 1. Chercher communb.csv (nouveau format vertical)
    chemins_communb = [
        script_dir / "refs" / "communb.csv",
        Path("refs/communb.csv"),
        Path("c:/g/refs/communb.csv"),
        Path("c:/cx/refs/communb.csv"),
    ]
    
    for chemin in chemins_communb:
        if chemin.exists():
            synonymes_meme, synonymes_que = _charger_synonymes_communb(str(chemin), verbose, debug)
            if synonymes_meme is not None:
                if verbose:
                    print(f"  ✓ Patterns 'même' chargés ({len(synonymes_meme)} synonymes meme, {len(synonymes_que)} synonymes que)")
                break
    
    # 2. Si pas trouvé, chercher commun.csv (ancien format horizontal)
    if synonymes_meme is None:
        chemins_commun = [
            script_dir / "refs" / "commun.csv",
            Path("refs/commun.csv"),
            Path("c:/g/refs/commun.csv"),
            Path("c:/cx/refs/commun.csv"),
        ]
        
        for chemin in chemins_commun:
            if chemin.exists():
                if debug:
                    print(f"[DEBUG] detmeme: Fallback vers {chemin}")
                synonymes_meme, synonymes_que = _charger_synonymes_commun(str(chemin), verbose, debug)
                if synonymes_meme:
                    if verbose:
                        print(f"  ✓ Patterns 'même' chargés ({len(synonymes_meme)} synonymes meme, {len(synonymes_que)} synonymes que)")
                    break
    
    # 3. Valeurs par défaut
    if not synonymes_meme:
        if debug:
            print(f"[DEBUG] detmeme: Aucun fichier trouvé, utilisation des valeurs par défaut")
        synonymes_meme = SYNONYMES_MEME_DEFAUT.copy()
        synonymes_que = SYNONYMES_QUE_DEFAUT.copy()
        if verbose:
            print(f"  ✓ Patterns 'même' par défaut ({len(synonymes_meme)} synonymes meme, {len(synonymes_que)} synonymes que)")
    
    return {
        'synonymes_meme': synonymes_meme,
        'synonymes_que': synonymes_que,
        'cibles': CIBLES_MEME.copy()
    }


def _convertir_id_reference(identifiant_str):
    """
    Convertit un identifiant de référence en int si purement numérique,
    sinon le garde en string.
    
    Args:
        identifiant_str: Identifiant capturé (ex: "10122", "abc123")
        
    Returns:
        int ou str
    """
    try:
        return int(identifiant_str)
    except (ValueError, TypeError):
        return identifiant_str


def detecter_meme(question: str, patterns_meme: dict, verbose=False, debug=False) -> dict:
    """
    Détecte les expressions "même X" dans une question.
    
    V2.1 - FORMATS SUPPORTÉS :
    1. "même portrait et même prénom que Guillaume Moulin"     (avec "et même")
    2. "même portrait même prénom que Guillaume Moulin"        (sans "et")
    3. "même portrait, prénom, nom que Guillaume Moulin"       (liste avec virgules)
    4. "mêmes portrait, prénom et nom que Guillaume Moulin"    (pluriel + liste)
    5. "même béance antérieure gauche que id 123"              (pathologie spécifique)
    6. "même portrait que id ABC123"                           (id alphanumérique)
    
    Args:
        question: Texte de la question en langage naturel
        patterns_meme: Dict retourné par charger_patterns_meme()
        verbose: Afficher les résultats intermédiaires
        debug: Afficher tous les détails
        
    Returns:
        dict: {
            'criteres': [{type, detecte, cible, label, valeur}, ...],
            'reference': {type: 'nom'|'id', valeur: str, id: int|str|None},
            'residu': 'texte restant'
        }
    """
    question_norm = standardise(question)
    
    if debug:
        print(f"[DEBUG] detmeme: Question normalisée: '{question_norm}'")
    
    synonymes_meme = patterns_meme.get('synonymes_meme', SYNONYMES_MEME_DEFAUT)
    synonymes_que = patterns_meme.get('synonymes_que', SYNONYMES_QUE_DEFAUT)
    cibles = patterns_meme.get('cibles', CIBLES_MEME)
    
    criteres = []
    reference = None
    residu = question_norm
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 0 (V1.0.8) : Vérifier s'il y a un synonyme de "même" dans la question
    # Si non, retourner directement sans rien détecter
    # Ceci évite les faux positifs comme "système de bielles" 
    # où "de bielles" serait interprété comme une référence patient
    # ═══════════════════════════════════════════════════════════════
    
    contient_meme = False
    for syn_meme in synonymes_meme:
        # Chercher le synonyme comme mot entier
        pattern_check = re.compile(r'\b' + re.escape(syn_meme) + r's?\b', re.IGNORECASE)
        if pattern_check.search(question_norm):
            contient_meme = True
            if debug:
                print(f"[DEBUG] detmeme: Synonyme 'même' trouvé: '{syn_meme}'")
            break
    
    if not contient_meme:
        if debug:
            print(f"[DEBUG] detmeme: Aucun synonyme de 'même' trouvé, sortie rapide")
        return {
            'criteres': [],
            'reference': None,
            'residu': question_norm
        }
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 1 : Extraire la référence (après "que")
    # Format : "... que Nom Prénom" ou "... que id 123" ou "... que id ABC123"
    # V1.0.9 : Support identifiants alphanumériques ([a-zA-Z0-9]+)
    # ═══════════════════════════════════════════════════════════════
    
    synonymes_que_tries = sorted(synonymes_que, key=lambda x: -len(x))
    
    for syn_que in synonymes_que_tries:
        # Cas 1 : "que id XXX" (alphanumérique)
        pattern_id = re.compile(
            r'\b' + re.escape(syn_que) + r'\s+id\s+([a-z0-9]+)\b',
            re.IGNORECASE
        )
        match_id = pattern_id.search(residu)
        if match_id:
            id_brut = match_id.group(1)
            id_val = _convertir_id_reference(id_brut)
            reference = {
                'type': 'id',
                'valeur': f"id {id_brut}",
                'id': id_val
            }
            residu = residu[:match_id.start()].strip()
            if debug:
                print(f"[DEBUG] detmeme: Référence ID trouvée: {reference}")
            break
        
        # Cas 2 : "que Nom Prénom"
        pattern_nom = re.compile(
            r'\b' + re.escape(syn_que) + r'\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ\s\-\']+)$',
            re.IGNORECASE
        )
        match_nom = pattern_nom.search(residu)
        if match_nom:
            nom_complet = match_nom.group(1).strip()
            reference = {
                'type': 'nom',
                'valeur': nom_complet,
                'id': None
            }
            residu = residu[:match_nom.start()].strip()
            if debug:
                print(f"[DEBUG] detmeme: Référence NOM trouvée: {reference}")
            break
    
    if verbose and reference:
        ref_str = reference['valeur'] if reference['type'] == 'nom' else f"id {reference['id']}"
        print(f"  ✓ Référence: {ref_str}")
    
    # ═══════════════════════════════════════════════════════════════
    # ÉTAPE 2 : Détecter et parser les critères
    # V1.0.7 : Trouver TOUTES les occurrences de "meme X" individuellement
    # Supporte : "et meme", ", meme", " meme" (juxtaposition)
    # ═══════════════════════════════════════════════════════════════
    
    if debug:
        print(f"[DEBUG] detmeme: Résidu après référence: '{residu}'")
    
    # Liste des cibles connues (triées par longueur décroissante)
    cibles_triees = sorted(cibles.keys(), key=lambda x: (-len(x.split()), -len(x), x))
    
    # ═══════════════════════════════════════════════════════════════
    # STRATÉGIE V1.0.7 : Trouver toutes les positions de synonymes "meme"
    # puis extraire le contenu de chaque occurrence
    # ═══════════════════════════════════════════════════════════════
    
    # Construire un pattern qui trouve "meme + contenu" en s'arrêtant au prochain "meme" ou fin
    # On utilise un lookahead pour s'arrêter avant le prochain synonyme
    
    # D'abord, construire l'alternance des synonymes (triés par longueur décroissante)
    synonymes_tries = sorted(synonymes_meme, key=lambda x: -len(x))
    synonymes_pattern = '|'.join(re.escape(s) for s in synonymes_tries)
    
    if debug:
        print(f"[DEBUG] detmeme: Synonymes pattern: ({synonymes_pattern[:50]}...)")
    
    # Pattern pour capturer chaque "meme X" individuellement
    # - Commence par un synonyme de "meme"
    # - Suivi d'un ou plusieurs mots
    # - S'arrête AVANT : prochain "meme", "et meme", ", meme", ou fin de chaîne
    # 
    # Approche : trouver tous les "meme" puis extraire ce qui suit jusqu'au prochain délimiteur
    
    # Pattern pour trouver le début de chaque critère "meme"
    pattern_debut = re.compile(
        r'(?:^|(?:,\s*)|(?:\s+et\s+)|(?:\s+))(' + synonymes_pattern + r')s?\s+',
        re.IGNORECASE
    )
    
    # Trouver toutes les positions de début
    matches_debut = list(pattern_debut.finditer(residu))
    
    if debug:
        print(f"[DEBUG] detmeme: {len(matches_debut)} occurrence(s) de 'meme' trouvée(s)")
        for m in matches_debut:
            print(f"[DEBUG] detmeme:   Position {m.start()}: '{m.group()}'")
    
    if matches_debut:
        # Pour chaque match, extraire le contenu jusqu'au prochain match ou fin
        for i, match in enumerate(matches_debut):
            # Début du contenu = fin du match actuel
            debut_contenu = match.end()
            
            # Fin du contenu = début du prochain match ou fin de la chaîne
            if i + 1 < len(matches_debut):
                # Trouver où commence le prochain "meme" (avant le séparateur)
                prochain_match = matches_debut[i + 1]
                fin_contenu = prochain_match.start()
            else:
                fin_contenu = len(residu)
            
            # Extraire le contenu
            contenu_brut = residu[debut_contenu:fin_contenu].strip()
            
            # Nettoyer : enlever les séparateurs de fin ("et", ",")
            contenu = re.sub(r'\s*,\s*$', '', contenu_brut)
            contenu = re.sub(r'\s+et\s*$', '', contenu, flags=re.IGNORECASE)
            contenu = contenu.strip()
            
            if debug:
                print(f"[DEBUG] detmeme: Critère {i+1}: '{match.group(1)}' + '{contenu}'")
            
            if not contenu:
                continue
            
            contenu_norm = standardise(contenu)
            texte_complet = f"{match.group(1)} {contenu}"
            
            # Chercher si c'est une cible connue
            cible_trouvee = False
            for cible_mot in cibles_triees:
                if contenu_norm == cible_mot or contenu_norm == cible_mot + 's':
                    cible_code, label = cibles[cible_mot]
                    critere = {
                        'type': 'meme',
                        'detecte': texte_complet.strip(),
                        'cible': cible_code,
                        'label': label,
                        'valeur': None
                    }
                    criteres.append(critere)
                    cible_trouvee = True
                    if verbose:
                        print(f"  ✓ Critère: '{texte_complet}' → {cible_code}")
                    break
            
            # Si pas une cible connue, c'est un tag ou pathologie spécifique
            if not cible_trouvee:
                mots = contenu_norm.split()
                if len(mots) == 1:
                    cible_code = 'tag'
                else:
                    cible_code = 'pathologie'
                
                critere = {
                    'type': 'meme',
                    'detecte': texte_complet.strip(),
                    'cible': cible_code,
                    'label': f'Même {contenu_norm}',
                    'valeur': contenu_norm
                }
                criteres.append(critere)
                if verbose:
                    print(f"  ✓ Critère spécifique: '{texte_complet}' → {cible_code} = '{contenu_norm}'")
        
        # Tout a été traité, résidu vide
        residu = ''
    
    # Si aucun critère trouvé avec la méthode ci-dessus, fallback sur l'ancienne méthode
    if not criteres and residu:
        if debug:
            print(f"[DEBUG] detmeme: Fallback - aucun critère trouvé avec la méthode V1.0.7")
        # Séparer par " et " d'abord
        parties = re.split(r'\s+et\s+', residu, flags=re.IGNORECASE)
        
        residu_final = []
        
        for partie in parties:
            partie = partie.strip()
            if not partie:
                continue
            
            critere_trouve = False
            
            for syn_meme in synonymes_meme:
                if critere_trouve:
                    break
                
                # Chercher "syn_meme + cible" dans cette partie
                for cible_mot in cibles_triees:
                    cible_code, label = cibles[cible_mot]
                    pattern_str = r'\b' + re.escape(syn_meme) + r's?\s+' + re.escape(cible_mot) + r's?\b'
                    
                    try:
                        pattern = re.compile(pattern_str, re.IGNORECASE)
                        match = pattern.search(partie)
                        
                        if match:
                            critere = {
                                'type': 'meme',
                                'detecte': match.group(0),
                                'cible': cible_code,
                                'label': label,
                                'valeur': None
                            }
                            criteres.append(critere)
                            critere_trouve = True
                            if verbose:
                                print(f"  ✓ Critère: '{match.group(0)}' → {cible_code}")
                            break
                    except re.error:
                        pass
                
                # Si pas de cible connue, chercher tag/pathologie spécifique
                if not critere_trouve:
                    pattern_spec = re.compile(
                        r'\b' + re.escape(syn_meme) + r's?\s+([a-zàâäéèêëïîôùûüç]+(?:\s+[a-zàâäéèêëïîôùûüç]+)*)',
                        re.IGNORECASE
                    )
                    match_spec = pattern_spec.search(partie)
                    
                    if match_spec:
                        valeur = match_spec.group(1).strip().lower()
                        mots = valeur.split()
                        
                        if len(mots) == 1:
                            cible_code = 'tag'
                        else:
                            cible_code = 'pathologie'
                        
                        critere = {
                            'type': 'meme',
                            'detecte': match_spec.group(0),
                            'cible': cible_code,
                            'label': f'Même {valeur}',
                            'valeur': valeur
                        }
                        criteres.append(critere)
                        critere_trouve = True
                        if verbose:
                            print(f"  ✓ Critère spécifique: '{match_spec.group(0)}' → {cible_code} = '{valeur}'")
            
            if not critere_trouve and partie:
                residu_final.append(partie)
        
        residu = ' '.join(residu_final).strip()
    
    if debug:
        print(f"[DEBUG] detmeme: {len(criteres)} critère(s) détecté(s)")
        print(f"[DEBUG] detmeme: Référence: {reference}")
        print(f"[DEBUG] detmeme: Résidu: '{residu}'")
    
    return {
        'criteres': criteres,
        'reference': reference,
        'residu': residu
    }


def identifier_meme(residu: str, patterns_meme: dict, filtres: dict, verbose=False, debug=False) -> Tuple[dict, str]:
    """
    Wrapper de compatibilité avec l'ancienne signature.
    
    SIGNATURE STANDARD pour tous les modules identXXX/detXXX :
        identifier_XXX(residu, data, filtres, verbose=False, debug=False) -> (filtres, residu)
    
    V2.0 : Ajoute aussi la référence dans filtres si présente
    
    Args:
        residu: Texte à analyser
        patterns_meme: Dict retourné par charger_patterns_meme()
        filtres: Dict à enrichir {'criteres': [...], 'reference': ...}
        verbose: Mode verbose
        debug: Mode debug
        
    Returns:
        Tuple (filtres, residu)
    """
    if debug:
        print(f"[DEBUG] identifier_meme: Analyse du résidu: '{residu}'")
    
    resultat = detecter_meme(residu, patterns_meme, verbose=verbose, debug=debug)
    
    # Ajouter les critères détectés
    for critere in resultat['criteres']:
        filtres['criteres'].append(critere)
    
    # V2.0 : Ajouter la référence si présente
    if resultat.get('reference'):
        filtres['reference_meme'] = resultat['reference']
    
    return filtres, resultat['residu']


def traiter_fichier_batch(fichier_entree: str, patterns_meme: dict, verbose=False, debug=False):
    """
    Traite un fichier de test batch (xxxin.csv) et génère xxxout.csv.
    """
    chemin_entree = Path(fichier_entree)
    nom_base = chemin_entree.stem
    
    if nom_base.endswith('in'):
        nom_sortie = nom_base[:-2] + 'out'
    else:
        nom_sortie = nom_base + '_out'
    
    fichier_sortie = chemin_entree.parent / f"{nom_sortie}.csv"
    
    print(f"Fichier d'entrée : {os.path.abspath(fichier_entree)}")
    print(f"Fichier de sortie: {os.path.abspath(fichier_sortie)}")
    print()
    
    lignes_entree = []
    col_indices = {}  # indices des colonnes résultat/commentaire
    commentaires = []
    
    encodages = ["utf-8-sig", "utf-8", "windows-1252"]
    
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
        if not question:
            continue
        # Extraire résultat et commentaire si présents
        _idx_res = col_indices.get('resultat', -1)
        _idx_comm = col_indices.get('commentaire', -1)
        _val_resultat = (row[_idx_res] or '').strip() if 0 <= _idx_res < len(row) else ''
        _val_commentaire = (row[_idx_comm] or '').strip() if 0 <= _idx_comm < len(row) else ''
        
        resultat = detecter_meme(question, patterns_meme, verbose=verbose, debug=debug)
        
        cibles = [c['cible'] for c in resultat['criteres']]
        labels = [c['label'] for c in resultat['criteres']]
        valeurs = [c.get('valeur') or '' for c in resultat['criteres']]
        
        # V2.0 : Extraire la référence
        ref = resultat.get('reference')
        ref_str = ''
        if ref:
            if ref['type'] == 'id':
                ref_str = f"id:{ref['id']}"
            else:
                ref_str = ref['valeur']
        
        resultats.append({
            'question': question,
            'resultat': _val_resultat,
            'commentaire': _val_commentaire,
            'nb_criteres': len(cibles),
            'cibles': ', '.join(cibles),
            'valeurs': ', '.join(valeurs),
            'labels': ', '.join(labels),
            'reference': ref_str,
            'residu': resultat['residu']
        })
        
        # Mini-résumé pour chaque question (toujours affiché)
        print(f"  [{i+1}/{len(lignes_entree)}] \"{question}\"")
        if resultat['criteres']:
            for j, c in enumerate(resultat['criteres'], 1):
                cible = c.get('cible', '?')
                label = c.get('label', '?')
                val = c.get('valeur', '')
                val_str = f" = {val}" if val else ''
                print(f"        {j}. [meme] {label}{val_str}")
        else:
            print(f"        (aucun critère 'même')")
        if ref_str:
            print(f"        Référence: {ref_str}")
        print(f"        Résidu: '{resultat['residu']}'")
        print()
    
    with open(fichier_sortie, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        
        for comm in commentaires:
            while len(comm) < 9:
                comm.append('')
            writer.writerow(comm)
        
        # V2.0 : Nouvelles colonnes
        writer.writerow(['question', 'résultat', 'commentaire', 'nb_criteres', 'cibles', 'valeurs', 'labels', 'reference', 'residu'])
        
        for res in resultats:
            writer.writerow([
                res['question'],
                res.get('resultat', ''),
                res.get('commentaire', ''),
                res['nb_criteres'],
                res['cibles'],
                res['valeurs'],
                res['labels'],
                res['reference'],
                res['residu']
            ])
    
    print("-" * 70)
    print(f"✓ {len(resultats)} lignes traitées → {os.path.abspath(fichier_sortie)}")
    
    return len(resultats), fichier_sortie


def main():
    """Point d'entrée CLI."""
    print(f"╔════════════════════════════════════════════════════════════════")
    print(f"║ {__pgm__} V{__version__} - {__date__}")
    print(f"║ Détection des expressions 'même X' (similarités)")
    print(f"║ V2.0 : Support critères multiples + référence patient")
    print(f"║ V1.0.9 : Support identifiants alphanumériques")
    print(f"║ Synonymes chargés depuis commun.csv")
    print(f"╚════════════════════════════════════════════════════════════════")
    print()
    
    parser = argparse.ArgumentParser(
        description="Détecte les expressions 'même X' dans une question"
    )
    parser.add_argument('question', help='Question en langage naturel OU fichier xxxin.csv')
    parser.add_argument('-v', '--verbose', action='store_true', help='Affichage modéré')
    parser.add_argument('-d', '--debug', action='store_true', help='Affichage complet')
    parser.add_argument('--commun', default=None, help='Chemin vers commun.csv')
    
    args = parser.parse_args()
    
    # Charger les patterns
    print("Chargement des patterns...")
    patterns_meme = charger_patterns_meme(args.commun, verbose=True, debug=args.debug)
    print()
    
    # Déterminer si c'est un fichier batch
    est_fichier_batch = args.question.endswith('.csv') and os.path.exists(args.question)
    
    if est_fichier_batch:
        print(f"Mode BATCH - Traitement de {args.question}")
        print("-" * 70)
        nb_lignes, _ = traiter_fichier_batch(
            args.question,
            patterns_meme,
            verbose=args.verbose,
            debug=args.debug
        )
        return 0 if nb_lignes > 0 else 1
    
    else:
        print(f"Question: \"{args.question}\"")
        print()
        
        resultat = detecter_meme(
            args.question,
            patterns_meme,
            verbose=args.verbose,
            debug=args.debug
        )
        
        print()
        print("═" * 70)
        print("RÉSUMÉ")
        print("═" * 70)
        print(f"Nb critères : {len(resultat['criteres'])}")
        
        for i, c in enumerate(resultat['criteres'], 1):
            valeur_str = f" = '{c['valeur']}'" if c.get('valeur') else ""
            print(f"  {i}. [{c['cible']}{valeur_str}] {c['label']} (détecté: '{c['detecte']}')")
        
        # V2.0 : Afficher la référence
        ref = resultat.get('reference')
        if ref:
            if ref['type'] == 'id':
                print(f"\nRéférence : ID {ref['id']}")
            else:
                print(f"\nRéférence : {ref['valeur']}")
        else:
            print(f"\nRéférence : (non détectée)")
        
        print(f"Résidu    : '{resultat['residu']}'")
        
        print()
        print("═" * 70)
        print("RÉSULTAT (JSON)")
        print("═" * 70)
        print(json.dumps(resultat, indent=2, ensure_ascii=False))
        
        return 0


if __name__ == '__main__':
    sys.exit(main())
