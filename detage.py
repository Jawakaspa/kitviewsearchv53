# detage.py V1.0.5 - 20/12/2025 16:18:33
__pgm__ = "detage.py"
__version__ = "1.0.5"
__date__ = "20/12/2025 16:18:33"

"""
Module de détection des critères d'âge dans une question en langage naturel.

Ce module analyse une question pour détecter des critères d'âge (opérateurs, valeurs, sexe)
et retourne des critères structurés avec labels SANS exécuter de requête SQL.

MIGRATION depuis identages.py V1.0.1 :
- Renommage identages.py → detage.py
- Nouveau format JSON unifié pour les critères
- SÉPARATION des critères sexe et âge (un critère par détection)
- Structure sql: {colonne, operateur, valeur} au lieu de conditions: [...]

ARCHITECTURE :
- Module de DÉTECTION uniquement (chaînes de caractères)
- Retourne des structures de données (critères avec labels)
- Aucun accès à la base de données
- 1 détection = possiblement 2 critères séparés (1 sexe + 1 âge)

NOUVEAU FORMAT DE SORTIE :
{
    "criteres": [
        {
            "type": "sexe",
            "detecte": "femme",
            "label": "Femme",
            "sql": {"colonne": "sexe", "operateur": "=", "valeur": "F"}
        },
        {
            "type": "age",
            "detecte": "moins de 39 ans",
            "label": "Moins de 39 ans",
            "sql": {"colonne": "age", "operateur": "<", "valeur": 39}
        }
    ],
    "residu": "texte restant"
}

Usage en import (depuis cherche.py ou detall.py) :
    from detage import charger_patterns_ages, detecter_age
    patterns_ages = charger_patterns_ages('refs/ages.csv')
    resultat = detecter_age(question, patterns_ages, verbose=True)

Usage CLI unitaire :
    python detage.py "Femme de moins de 39 ans" [--verbose] [--debug]

Usage CLI batch :
    python detage.py tests/testsagesin.csv [--verbose] [--debug]
    # Sortie automatique : tests/testsagesout.csv
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
        for char in ".!-_?":
            texte = texte.replace(char, " ")
        texte = re.sub(r'\s+', ' ', texte)
        return texte.strip()


def _build_age_regex(expression):
    r"""
    Transforme une expression du CSV en regex.
    
    Règles :
    - Remplace {n} par un placeholder AVANT standardisation
    - Standardise l'expression
    - Échappe tous les caractères spéciaux SAUF |
    - Remplace le placeholder par des groupes capturants (\d+)
    - Remplace les espaces par \s+
    
    Note: Le placeholder permet de distinguer {1}, {2} des valeurs littérales.
    Cette logique est aussi utilisée par angles.py.
    
    Args:
        expression: Expression du CSV (ex: "moins de {n} ans")
        
    Returns:
        Regex compilable (string)
    """
    # Remplacer {n} par un placeholder AVANT standardisation
    PLACEHOLDER = "XNUMX"
    expr_avec_placeholder = expression.replace("{n}", PLACEHOLDER)
    
    # Standardiser
    expr_norm = standardise(expr_avec_placeholder)
    
    # Échapper caractère par caractère, sauf |
    result = []
    for char in expr_norm:
        if char == '|':
            result.append('|')
        elif char in r'\^$.*+?{}[]()':
            result.append('\\' + char)
        else:
            result.append(char)
    p = ''.join(result)
    
    # Remplacer le placeholder par des groupes capturants
    p = p.replace(PLACEHOLDER.lower(), r'(\d+)')
    
    # Autoriser plusieurs espaces
    p = p.replace(" ", r"\s+")
    
    return p


def _compter_mots(texte):
    """Compte le nombre de mots dans un texte normalisé."""
    if not texte:
        return 0
    return len(texte.split())


def charger_patterns_ages(fichier_csv, verbose=False, debug=False):
    """
    Charge les patterns d'âge depuis ages.csv
    
    Format CSV : expression;operateur;valeur_sql;sexe;label
    
    Args:
        fichier_csv: Chemin vers ages.csv
        verbose: Afficher les informations de chargement
        debug: Afficher les détails complets
        
    Returns:
        Liste de dicts, chaque dict contenant :
        {
            'patterns': [(regex, expression_brute, nb_mots), ...],  # triés par nb_mots décroissant
            'operateur': str,
            'valeur_template': str,
            'sexe': str ('M', 'F', ou ''),
            'label': str,
            'expression_complete': str  # expression brute complète de la ligne
        }
    """
    patterns_par_ligne = []
    
    if not os.path.exists(fichier_csv):
        print(f"[ERREUR] Fichier patterns introuvable: {os.path.abspath(fichier_csv)}")
        return patterns_par_ligne
    
    if debug:
        print(f"[DEBUG] detage: Chargement depuis {os.path.abspath(fichier_csv)}")
    
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
                    
                    # Format : expression;operateur;valeur_sql;sexe;label
                    if len(row) < 5:
                        if debug:
                            print(f"[DEBUG] Ligne {ligne_num} ignorée (moins de 5 colonnes)")
                        continue
                    
                    expression_brute = (row[0] or '').strip()
                    operateur = (row[1] or '').strip().upper()
                    valeur_template = (row[2] or '').strip()
                    sexe = (row[3] or '').strip().upper()
                    label = (row[4] or '').strip()
                    
                    if not expression_brute:
                        continue
                    
                    # Exploser les patterns sur |
                    alternatives = expression_brute.split('|')
                    patterns_ligne = []
                    
                    for alt in alternatives:
                        alt = alt.strip()
                        if not alt:
                            continue
                        
                        try:
                            # Construire la regex
                            pattern_regex = _build_age_regex(alt)
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
                            'valeur_template': valeur_template,
                            'sexe': sexe if sexe in ('M', 'F') else '',
                            'label': label,
                            'expression_complete': expression_brute
                        })
                        lignes_valides += 1
                        
                        if debug and lignes_valides <= 5:
                            print(f"[DEBUG] Ligne {ligne_num}: {len(patterns_ligne)} patterns, label='{label}'")
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
    Remplace les {n} dans le label par les valeurs capturées.
    
    Args:
        label_template: Label avec placeholders (ex: "Moins de {n} ans")
        valeurs_capturees: Liste des valeurs capturées [39] ou [20, 30]
        
    Returns:
        Label final (ex: "Moins de 39 ans")
    """
    if not valeurs_capturees:
        return label_template
    
    label_final = label_template
    for val in valeurs_capturees:
        label_final = label_final.replace('{n}', str(val), 1)
    
    return label_final


def _construire_criteres_separes(operateur, valeur_template, sexe, valeurs_capturees, texte_matche, label_template, debug=False):
    """
    Construit la liste des critères SÉPARÉS (un par type) au nouveau format.
    
    CHANGEMENT MAJEUR : Au lieu de retourner un seul critère avec conditions: [...],
    on retourne plusieurs critères séparés avec sql: {...} chacun.
    
    Args:
        operateur: Opérateur SQL (>=, <=, <, >, =, BETWEEN, ou vide)
        valeur_template: Template de valeur (ex: "{1}", "BETWEEN {1} AND {2}", "18")
        sexe: 'M', 'F', ou ''
        valeurs_capturees: Liste des valeurs numériques capturées
        texte_matche: Texte détecté dans la question
        label_template: Template de label
        debug: Mode debug
        
    Returns:
        Liste de critères au nouveau format [{'type': ..., 'detecte': ..., 'label': ..., 'sql': {...}}, ...]
    """
    criteres = []
    label_final = _construire_label_final(label_template, valeurs_capturees)
    
    # Critère de sexe si présent
    # Label = "Masculin"/"Féminin" (genre) pour éviter confusion avec le label âge
    if sexe in ('M', 'F'):
        label_sexe = 'Masculin' if sexe == 'M' else 'Féminin'
        criteres.append({
            'type': 'sexe',
            'detecte': texte_matche,
            'label': label_sexe,
            'sql': {
                'colonne': 'sexe',
                'operateur': '=',
                'valeur': sexe
            }
        })
    
    # Critère d'âge si opérateur présent
    if operateur:
        if operateur == 'BETWEEN':
            # Cas BETWEEN : besoin de 2 valeurs
            if len(valeurs_capturees) >= 2:
                val1, val2 = valeurs_capturees[0], valeurs_capturees[1]
            elif len(valeurs_capturees) == 1:
                # Patterns comme "environ {n} ans" avec formule
                val1 = valeurs_capturees[0]
                # Parser le template pour extraire les offsets
                # Ex: "BETWEEN {1}-2 AND {1}+2"
                if '-' in valeur_template or '+' in valeur_template:
                    # Extraire les bornes
                    match_bornes = re.search(r'BETWEEN\s+\{1\}([+-]\d+)?\s+AND\s+\{1\}([+-]\d+)?', valeur_template)
                    if match_bornes:
                        offset1 = int(match_bornes.group(1) or 0)
                        offset2 = int(match_bornes.group(2) or 0)
                        val1 = valeurs_capturees[0] + offset1
                        val2 = valeurs_capturees[0] + offset2
                    else:
                        val2 = val1
                else:
                    val2 = val1
            else:
                # Valeurs fixes dans le template (ex: "BETWEEN 12 AND 18")
                match_fixed = re.search(r'BETWEEN\s+(\d+)\s+AND\s+(\d+)', valeur_template)
                if match_fixed:
                    val1, val2 = int(match_fixed.group(1)), int(match_fixed.group(2))
                else:
                    return criteres
            
            criteres.append({
                'type': 'age',
                'detecte': texte_matche,
                'label': label_final,
                'sql': {
                    'colonne': 'age',
                    'operateur': 'BETWEEN',
                    'valeur': [val1, val2]  # Liste pour BETWEEN
                }
            })
            
        elif operateur in ('>=', '<=', '<', '>', '='):
            # Cas opérateur simple
            if valeurs_capturees:
                valeur = valeurs_capturees[0]
            elif valeur_template.isdigit():
                valeur = int(valeur_template)
            else:
                # Template avec {1} sans valeur capturée
                return criteres
            
            criteres.append({
                'type': 'age',
                'detecte': texte_matche,
                'label': label_final,
                'sql': {
                    'colonne': 'age',
                    'operateur': operateur,
                    'valeur': valeur
                }
            })
    
    # Si ni sexe ni âge, mais label présent (ex: "tous", "toutes")
    # On crée un critère générique
    if not criteres and label_final:
        # Cas spécial : uniquement sexe sans âge (ex: "de sexe feminin")
        if sexe in ('M', 'F'):
            label_sexe = 'Masculin' if sexe == 'M' else 'Féminin'
            criteres.append({
                'type': 'sexe',
                'detecte': texte_matche,
                'label': label_sexe,
                'sql': {
                    'colonne': 'sexe',
                    'operateur': '=',
                    'valeur': sexe
                }
            })
    
    return criteres


def detecter_age(question, patterns_ages, verbose=False, debug=False):
    """
    Détecte les critères d'âge et sexe dans une question.
    
    Cette fonction analyse la question et retourne des critères SÉPARÉS
    au nouveau format JSON unifié.
    
    Args:
        question: Texte de la question en langage naturel
        patterns_ages: Liste de patterns (retournée par charger_patterns_ages)
        verbose: Afficher les résultats intermédiaires
        debug: Afficher tous les détails
        
    Returns:
        dict: {
            'criteres': [
                {
                    'type': 'sexe' ou 'age',
                    'detecte': str,
                    'label': str,
                    'sql': {'colonne': str, 'operateur': str, 'valeur': ...}
                },
                ...
            ],
            'residu': 'texte restant'
        }
    """
    question_norm = standardise(question)
    mots_question = question_norm.split()
    plages_utilisees = []  # Liste de tuples (start, end) des zones déjà matchées
    criteres_detectes = []
    
    if debug:
        print(f"[DEBUG] detage: Question normalisée: '{question_norm}'")
        print(f"[DEBUG] detage: Mots: {mots_question}")
    
    # Collecter tous les patterns avec leur ligne parente, triés par nb_mots décroissant
    tous_patterns = []
    for ligne_data in patterns_ages:
        for pattern_info in ligne_data['patterns']:
            tous_patterns.append({
                'pattern_info': pattern_info,
                'ligne_data': ligne_data
            })
    
    # Trier par nombre de mots décroissant (patterns les plus longs d'abord)
    tous_patterns.sort(key=lambda x: x['pattern_info']['nb_mots'], reverse=True)
    
    if debug:
        print(f"[DEBUG] detage: {len(tous_patterns)} patterns à tester (triés par longueur)")
    
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
        expression_norm = pattern_info['expression_norm']
        mots_pattern = expression_norm.split()
        
        # Vérifier si tous les mots du pattern sont disponibles
        # (pour patterns sans {n})
        if '{n}' not in pattern_info['expression'].lower() and '\\d+' not in regex:
            # Pattern sans nombre : vérifier que les mots existent dans la question
            if not all(mot in mots_question for mot in mots_pattern):
                continue
        
        # Chercher le pattern dans la question
        try:
            match = re.search(regex, question_norm, re.IGNORECASE)
        except re.error as e:
            if debug:
                print(f"[DEBUG] Erreur regex '{regex}': {e}")
            continue
        
        if match:
            texte_matche = match.group(0)
            match_start = match.start()
            match_end = match.end()
            
            # Vérifier que la plage ne chevauche pas une plage déjà utilisée
            chevauchement = False
            for (us, ue) in plages_utilisees:
                if match_start < ue and match_end > us:
                    chevauchement = True
                    break
            if chevauchement:
                continue
            
            # Capturer les valeurs numériques
            valeurs_capturees = [int(g) for g in match.groups() if g and g.isdigit()]
            
            # Construire les critères SÉPARÉS au nouveau format
            nouveaux_criteres = _construire_criteres_separes(
                ligne_data['operateur'],
                ligne_data['valeur_template'],
                ligne_data['sexe'],
                valeurs_capturees,
                texte_matche,
                ligne_data['label'],
                debug=debug
            )
            
            if nouveaux_criteres:
                criteres_detectes.extend(nouveaux_criteres)
                
                # Marquer la plage de caractères comme utilisée
                plages_utilisees.append((match_start, match_end))
                
                # Marquer cette ligne comme matchée
                lignes_matchees.add(ligne_id)
                
                if verbose or debug:
                    for c in nouveaux_criteres:
                        print(f"  ✓ Détecté: '{texte_matche}' → Type: {c['type']}, Label: '{c['label']}'")
    
    # Calculer le résidu : mots dont la position n'est couverte par aucune plage utilisée
    residu_mots = []
    pos = 0
    for mot in mots_question:
        mot_start = question_norm.index(mot, pos)
        mot_end = mot_start + len(mot)
        pos = mot_end
        # Vérifier si ce mot est couvert par une plage utilisée
        couvert = False
        for (us, ue) in plages_utilisees:
            if mot_start >= us and mot_end <= ue:
                couvert = True
                break
        if not couvert:
            residu_mots.append(mot)
    residu = ' '.join(residu_mots)
    
    if debug:
        print(f"[DEBUG] detage: {len(criteres_detectes)} critère(s) détecté(s)")
        print(f"[DEBUG] detage: Résidu: '{residu}'")
    
    # POST-TRAITEMENT : Gérer les conflits d'âge implicite/explicite
    # Si on a un âge EXPLICITE (avec nombre capturé comme "moins de 25 ans")
    # ET un âge IMPLICITE (mot genré comme "femmes" → >= 18 ou "filles" → < 12)
    # → On garde uniquement le sexe du mot genré, on ignore son âge implicite
    
    criteres_age = [c for c in criteres_detectes if c['type'] == 'age']
    
    if len(criteres_age) >= 2:
        # Identifier les âges explicites (avec nombre dans 'detecte') vs implicites
        ages_explicites = []
        ages_implicites = []
        
        for c in criteres_age:
            detecte = c.get('detecte', '')
            # Un âge est explicite s'il contient un nombre
            if any(char.isdigit() for char in detecte):
                ages_explicites.append(c)
            else:
                ages_implicites.append(c)
        
        # S'il y a au moins un âge explicite ET au moins un âge implicite
        # → supprimer les âges implicites
        if ages_explicites and ages_implicites:
            if debug:
                print(f"[DEBUG] detage: Conflit détecté - {len(ages_explicites)} âge(s) explicite(s), {len(ages_implicites)} âge(s) implicite(s)")
                for c in ages_implicites:
                    print(f"[DEBUG] detage: Suppression âge implicite: '{c['detecte']}' → {c['sql']}")
            
            # Reconstruire la liste sans les âges implicites
            criteres_detectes = [c for c in criteres_detectes if c not in ages_implicites]
            
            if verbose or debug:
                print(f"  ⚠ Âge(s) implicite(s) ignoré(s) car âge explicite présent")
    
    return {
        'criteres': criteres_detectes,
        'residu': residu
    }


def identifier_ages(residu, patterns_ages, filtres, verbose=False, debug=False):
    """
    Wrapper de compatibilité avec l'ancienne signature.
    
    SIGNATURE STANDARD pour tous les modules identXXX/detXXX :
        identifier_XXX(residu, data, filtres, verbose=False, debug=False) -> (filtres, residu)
    
    Args:
        residu: Texte restant après détections précédentes
        patterns_ages: Liste de patterns (retournée par charger_patterns_ages)
        filtres: Dict à enrichir {'listcount': ..., 'pathologies': [], 'criteres': [...]}
        verbose: Mode verbose (résultats intermédiaires)
        debug: Mode debug (tous les détails)
        
    Returns:
        Tuple (filtres, residu)
        - filtres['criteres'] est enrichi avec les critères détectés
        - residu contient les mots non matchés
    """
    if debug:
        print(f"[DEBUG] identifier_ages: Analyse du résidu: '{residu}'")
    
    # Appeler la fonction de détection avec le nouveau format
    resultat = detecter_age(residu, patterns_ages, verbose=verbose, debug=debug)
    
    # Enrichir filtres['criteres'] avec les nouveaux critères
    for critere in resultat['criteres']:
        filtres['criteres'].append(critere)
    
    if verbose or debug:
        print(f"[DEBUG] identifier_ages: {len(resultat['criteres'])} critère(s) ajouté(s)")
    
    # Retourner filtres enrichi + nouveau résidu
    return filtres, resultat['residu']


def traiter_fichier_batch(fichier_entree, patterns_ages, verbose=False, debug=False):
    """
    Traite un fichier de test batch et génère [nom_entrée]detage.csv.
    
    Format d'entrée : CSV avec colonne 'question'
    Format de sortie : question;L1;L2;...;Ln (résumé transposé)
    """
    # Déterminer le fichier de sortie
    chemin_entree = Path(fichier_entree)
    nom_base = chemin_entree.stem
    module_name = Path(__pgm__).stem  # 'detage'
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
        resultat = detecter_age(question, patterns_ages, verbose=verbose, debug=debug)
        
        # Extraire les labels
        labels = [c['label'] for c in resultat['criteres']]
        nb_criteres = len(labels)
        sorties = ', '.join(labels)
        
        # Construire les lignes du résumé pour le CSV
        lignes_resume = []
        if resultat['criteres']:
            for j, c in enumerate(resultat['criteres'], 1):
                type_c = c.get('type', '?')
                label = c.get('label', '?')
                lignes_resume.append(f"[{type_c}] {label}")
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
                label = c.get('label', '?')
                print(f"        {j}. [{type_c}] {label}")
        else:
            print(f"        (aucun critère)")
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
    print(f"║ Détection des critères d'âge dans une question")
    print(f"╚════════════════════════════════════════════════════════════════")
    print()
    
    parser = argparse.ArgumentParser(
        description="Détecte les critères d'âge dans une question en langage naturel"
    )
    parser.add_argument('question', help='Question en langage naturel OU fichier xxxin.csv')
    parser.add_argument('-v', '--verbose', action='store_true', help='Affichage modéré (résultats)')
    parser.add_argument('-d', '--debug', action='store_true', help='Affichage complet (tout)')
    parser.add_argument('--patterns', default='refs/ages.csv', help='Chemin vers ages.csv')
    
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
            Path(__file__).parent / "refs" / "ages.csv",
            Path("c:/g/refs/ages.csv"),
            Path("refs/ages.csv"),
        ]
        for chemin in chemins_alternatifs:
            if chemin.exists():
                patterns_path = str(chemin)
                break
    
    print(f"Fichier ages.csv: {os.path.abspath(patterns_path)}")
    print()
    
    # Charger les patterns
    patterns_ages = charger_patterns_ages(patterns_path, verbose=args.verbose, debug=args.debug)
    
    if not patterns_ages:
        print()
        print("[ERREUR] Aucun pattern chargé depuis ages.csv")
        return 1
    
    print()
    
    if est_fichier_batch:
        # Mode batch
        print(f"Mode BATCH - Traitement de {os.path.abspath(fichier_batch)}")
        print("-" * 70)
        nb_lignes, fichier_sortie = traiter_fichier_batch(
            fichier_batch, 
            patterns_ages, 
            verbose=args.verbose, 
            debug=args.debug
        )
        return 0 if nb_lignes > 0 else 1
    
    else:
        # Mode unitaire - sortie JSON
        print(f"Question: \"{args.question}\"")
        print()
        
        # Détecter les critères
        resultat = detecter_age(
            args.question,
            patterns_ages,
            verbose=args.verbose,
            debug=args.debug
        )
        
        # Afficher le résultat en JSON formaté
        print()
        print("═" * 70)
        print("RÉSULTAT (JSON)")
        print("═" * 70)
        print(json.dumps(resultat, indent=2, ensure_ascii=False))
        
        return 0


if __name__ == '__main__':
    sys.exit(main())
