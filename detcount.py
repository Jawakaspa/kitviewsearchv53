# detcount.py V1.0.1 - 21/01/2026 18:12:57
__pgm__ = "detcount.py"
__version__ = "1.0.1"
__date__ = "21/01/2026 18:12:57"

"""
Module de détection LIST/COUNT dans une question en langage naturel.

Ce module analyse une question pour détecter si elle demande un comptage (COUNT)
ou une liste (LIST) et retourne le résidu après retrait du mot détecté.

CHANGEMENTS V1.0.1 (21/01/2026) :
- Support de communb.csv (format vertical section;parametre;valeur)
- Fallback vers commun.csv (ancien format horizontal)
- Lecture de synonymes;combien;valeurs... dans le format vertical

ARCHITECTURE :
- Module de DÉTECTION uniquement (chaînes de caractères)
- Retourne un dict avec 'listcount', 'criteres', 'residu'
- Aucun accès à la base de données

NOUVEAU FORMAT DE SORTIE :
{
    "listcount": "COUNT" ou "LIST",
    "criteres": [
        {
            "type": "count",
            "detecte": "combien",
            "label": "Comptage demandé"
        }
    ] ou [],
    "residu": "texte restant"
}

Usage en import (depuis cherche.py ou detall.py) :
    from detcount import charger_patterns_count, detecter_count
    patterns_count = charger_patterns_count('refs/commun.csv')
    resultat = detecter_count(question, patterns_count, verbose=True)

Usage CLI unitaire :
    python detcount.py "combien de femmes de moins de 39 ans" [--verbose] [--debug]

Usage CLI batch :
    python detcount.py tests/testscountin.csv [--verbose] [--debug]
    # Sortie automatique : tests/testscountout.csv
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


def _charger_patterns_communb(fichier_csv, verbose=False, debug=False):
    """
    Charge les mots-clés COUNT depuis communb.csv (format vertical).
    
    Format : synonymes;combien;mot1,mot2,...;description
    """
    patterns = []
    
    if not os.path.exists(fichier_csv):
        return None
    
    encodages = ["utf-8-sig", "utf-8", "windows-1252", "iso-8859-1"]
    
    for encodage in encodages:
        try:
            with open(fichier_csv, 'r', encoding=encodage, newline='') as f:
                reader = csv.DictReader(
                    (line for line in f if not line.strip().startswith('#')),
                    delimiter=';'
                )
                
                # Vérifier format vertical
                if not all(col in (reader.fieldnames or []) for col in ['section', 'parametre', 'valeur']):
                    return None
                
                for row in reader:
                    section = (row.get('section') or '').strip().lower()
                    parametre = (row.get('parametre') or '').strip().lower()
                    valeur = (row.get('valeur') or '').strip()
                    
                    if section == 'synonymes' and parametre == 'combien' and valeur:
                        # Splitter par virgule
                        for mot_brut in valeur.split(','):
                            mot_brut = mot_brut.strip()
                            if not mot_brut:
                                continue
                            
                            mot_norm = standardise(mot_brut)
                            if not mot_norm:
                                continue
                            
                            # Éviter les doublons
                            if any(p['mot'] == mot_norm for p in patterns):
                                continue
                            
                            nb_mots = len(mot_norm.split())
                            patterns.append({
                                'mot': mot_norm,
                                'mot_brut': mot_brut,
                                'nb_mots': nb_mots
                            })
                            
                            if debug:
                                print(f"[DEBUG] detcount: '{mot_brut}' → '{mot_norm}' ({nb_mots} mot(s))")
                
                # Trier par nb_mots décroissant
                patterns.sort(key=lambda x: x['nb_mots'], reverse=True)
                
                if verbose or debug:
                    print(f"✓ {len(patterns)} mot(s) COUNT chargé(s) depuis {os.path.basename(fichier_csv)} (format vertical)")
                
                return patterns
                
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            if debug:
                print(f"[DEBUG] Erreur: {e}")
            continue
    
    return None


def charger_patterns_count(fichier_csv, verbose=False, debug=False):
    """
    Charge les mots-clés COUNT depuis communb.csv ou commun.csv.
    
    Ordre de recherche :
    1. communb.csv (format vertical section;parametre;valeur)
    2. commun.csv (ancien format horizontal)
    
    Args:
        fichier_csv: Chemin vers le fichier de config
        verbose: Afficher les informations de chargement
        debug: Afficher les détails complets
        
    Returns:
        Liste de dicts triée par nb_mots décroissant
    """
    patterns = None
    script_dir = Path(__file__).parent
    
    # 1. Essayer communb.csv d'abord
    chemins_communb = [
        script_dir / "refs" / "communb.csv",
        Path("refs/communb.csv"),
        Path("c:/g/refs/communb.csv"),
        Path("c:/cx/refs/communb.csv"),
    ]
    
    for chemin in chemins_communb:
        if chemin.exists():
            patterns = _charger_patterns_communb(str(chemin), verbose, debug)
            if patterns is not None:
                return patterns
    
    # 2. Fallback vers commun.csv (ancien format)
    if patterns is None:
        patterns = _charger_patterns_commun_ancien(fichier_csv, verbose, debug)
    
    return patterns or []


def _charger_patterns_commun_ancien(fichier_csv, verbose=False, debug=False):
    """
    Charge les mots-clés COUNT depuis commun.csv (colonne 'combien')
    
    Format CSV : combien;devant;langues (première colonne = mot-clé COUNT)
    
    Args:
        fichier_csv: Chemin vers commun.csv
        verbose: Afficher les informations de chargement
        debug: Afficher les détails complets
        
    Returns:
        Liste de dicts, chaque dict contenant :
        {
            'mot': str,           # Mot normalisé
            'mot_brut': str,      # Mot original
            'nb_mots': int        # Nombre de mots (pour tri)
        }
        Liste triée par nb_mots décroissant (expressions les plus longues d'abord)
    """
    patterns = []
    
    if not os.path.exists(fichier_csv):
        print(f"[ERREUR] Fichier patterns introuvable: {os.path.abspath(fichier_csv)}")
        return patterns
    
    if debug:
        print(f"[DEBUG] detcount: Chargement depuis {os.path.abspath(fichier_csv)}")
    
    # Essayer différents encodages
    encodages = ["utf-8-sig", "utf-8", "windows-1252", "iso-8859-1"]
    
    for encodage in encodages:
        try:
            with open(fichier_csv, 'r', encoding=encodage, newline='') as f:
                reader = csv.reader(f, delimiter=';')
                ligne_num = 0
                mots_valides = 0
                
                for row in reader:
                    ligne_num += 1
                    
                    # Ignorer lignes vides ou commentaires
                    if not row or (row[0] or '').strip().startswith('#'):
                        continue
                    
                    # Ignorer l'en-tête
                    if ligne_num <= 2 and 'combien' in (row[0] or '').lower():
                        continue
                    
                    # Première colonne = mot-clé COUNT
                    mot_brut = (row[0] or '').strip()
                    
                    if not mot_brut:
                        continue
                    
                    # Normaliser le mot
                    mot_norm = standardise(mot_brut)
                    
                    if not mot_norm:
                        continue
                    
                    # Éviter les doublons
                    if any(p['mot'] == mot_norm for p in patterns):
                        if debug:
                            print(f"[DEBUG] Ligne {ligne_num}: '{mot_brut}' déjà présent (ignoré)")
                        continue
                    
                    # Compter les mots
                    nb_mots = len(mot_norm.split())
                    
                    patterns.append({
                        'mot': mot_norm,
                        'mot_brut': mot_brut,
                        'nb_mots': nb_mots
                    })
                    mots_valides += 1
                    
                    if debug:
                        print(f"[DEBUG] Ligne {ligne_num}: '{mot_brut}' → '{mot_norm}' ({nb_mots} mot(s))")
                
                # Trier par nb_mots décroissant (expressions les plus longues d'abord)
                patterns.sort(key=lambda x: x['nb_mots'], reverse=True)
                
                if verbose or debug:
                    print(f"✓ {mots_valides} mot(s) COUNT chargé(s) depuis {os.path.abspath(fichier_csv)}")
                
                return patterns
                
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            if debug:
                print(f"[DEBUG] Erreur encodage {encodage}: {e}")
            continue
    
    print(f"[ERREUR] Impossible de lire {os.path.abspath(fichier_csv)}")
    return patterns


def detecter_count(question, patterns_count, verbose=False, debug=False):
    """
    Détecte si la question demande un comptage (COUNT) ou une liste (LIST).
    
    Cette fonction analyse la question et retourne le résultat de détection
    au NOUVEAU FORMAT JSON unifié.
    
    Args:
        question: Texte de la question en langage naturel
        patterns_count: Liste de patterns (retournée par charger_patterns_count)
        verbose: Afficher les résultats intermédiaires
        debug: Afficher tous les détails
        
    Returns:
        dict: {
            'listcount': 'COUNT' ou 'LIST',
            'criteres': [
                {
                    'type': 'count',
                    'detecte': str,
                    'label': 'Comptage demandé'
                }
            ] ou [],
            'residu': 'texte restant'
        }
    """
    question_norm = standardise(question)
    
    if debug:
        print(f"[DEBUG] detcount: Question normalisée: '{question_norm}'")
    
    listcount = 'LIST'
    criteres = []
    residu = question_norm
    
    # Chercher un mot COUNT dans la question
    # Les patterns sont triés par nb_mots décroissant (expressions longues d'abord)
    for pattern in patterns_count:
        mot = pattern['mot']
        
        # Chercher le mot dans la question
        # On utilise une regex pour s'assurer que c'est un mot complet
        # ou une expression complète (pas une sous-chaîne)
        regex = r'\b' + re.escape(mot) + r'\b'
        
        match = re.search(regex, question_norm)
        
        if match:
            listcount = 'COUNT'
            
            # Créer le critère au nouveau format
            criteres.append({
                'type': 'count',
                'detecte': mot,
                'label': 'Comptage demandé'
            })
            
            # Retirer le mot de la question
            residu = re.sub(regex, ' ', question_norm)
            # Nettoyer les espaces multiples
            residu = re.sub(r'\s+', ' ', residu).strip()
            
            if verbose or debug:
                print(f"  ✓ Détecté: '{mot}' → listcount=COUNT")
            
            break  # Un seul mot COUNT suffit
    
    if not criteres and debug:
        print(f"[DEBUG] detcount: Aucun mot COUNT trouvé → listcount=LIST")
    
    if debug:
        print(f"[DEBUG] detcount: Résidu: '{residu}'")
    
    return {
        'listcount': listcount,
        'criteres': criteres,
        'residu': residu
    }


def identifier_count(residu, patterns_count, filtres, verbose=False, debug=False):
    """
    Wrapper de compatibilité avec l'ancienne signature.
    
    SIGNATURE STANDARD pour tous les modules identXXX/detXXX :
        identifier_XXX(residu, data, filtres, verbose=False, debug=False) -> (filtres, residu)
    
    Args:
        residu: Texte à analyser
        patterns_count: Liste de patterns (retournée par charger_patterns_count)
        filtres: Dict à enrichir {'listcount': ..., 'criteres': [...]}
        verbose: Mode verbose
        debug: Mode debug
        
    Returns:
        Tuple (filtres, residu)
        - filtres['listcount'] mis à jour
        - filtres['criteres'] enrichi avec le critère count si détecté
    """
    if debug:
        print(f"[DEBUG] identifier_count: Analyse du résidu: '{residu}'")
    
    # Appeler la fonction de détection
    resultat = detecter_count(residu, patterns_count, verbose=verbose, debug=debug)
    
    # Mettre à jour filtres['listcount']
    filtres['listcount'] = resultat['listcount']
    
    # Ajouter les critères détectés
    for critere in resultat['criteres']:
        filtres['criteres'].append(critere)
    
    if verbose or debug:
        print(f"[DEBUG] identifier_count: listcount={resultat['listcount']}")
    
    # Retourner filtres enrichi + nouveau résidu
    return filtres, resultat['residu']


def traiter_fichier_batch(fichier_entree, patterns_count, verbose=False, debug=False):
    """
    Traite un fichier de test batch et génère [nom_entrée]detcount.csv.
    
    Format d'entrée : CSV avec colonne 'question'
    Format de sortie : question;L1;L2;...;Ln (résumé transposé)
    """
    # Déterminer le fichier de sortie
    chemin_entree = Path(fichier_entree)
    nom_base = chemin_entree.stem
    module_name = Path(__pgm__).stem  # 'detcount'
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
        resultat = detecter_count(question, patterns_count, verbose=verbose, debug=debug)
        
        # Résultat : 1 si COUNT, 0 si LIST
        resultat_num = 1 if resultat['listcount'] == 'COUNT' else 0
        sorties = resultat['listcount']
        
        # Construire les lignes du résumé pour le CSV
        lignes_resume = [f"→ {sorties}", f"Résidu: '{resultat['residu']}'"]
        
        resultats.append({
            'question': question,
            'resultat': _val_resultat,
            'commentaire': _val_commentaire,
            'lignes': lignes_resume
        })
        
        # Mini-résumé pour chaque question (toujours affiché)
        print(f"  [{i+1}/{len(lignes_entree)}] \"{question}\"")
        print(f"        → {sorties}")
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
    print(f"║ Détection LIST/COUNT dans une question")
    print(f"╚════════════════════════════════════════════════════════════════")
    print()
    
    parser = argparse.ArgumentParser(
        description="Détecte si une question demande un comptage (COUNT) ou une liste (LIST)"
    )
    parser.add_argument('question', help='Question en langage naturel OU fichier xxxin.csv')
    parser.add_argument('-v', '--verbose', action='store_true', help='Affichage modéré (résultats)')
    parser.add_argument('-d', '--debug', action='store_true', help='Affichage complet (tout)')
    parser.add_argument('--patterns', default='refs/commun.csv', help='Chemin vers commun.csv')
    
    args = parser.parse_args()
    
    # Déterminer si c'est un fichier batch ou une question unitaire
    est_fichier_batch = args.question.endswith('.csv') and os.path.exists(args.question)
    
    # Chercher le fichier patterns
    patterns_path = args.patterns
    if not os.path.exists(patterns_path):
        # Essayer des chemins alternatifs
        chemins_alternatifs = [
            Path(__file__).parent / "refs" / "commun.csv",
            Path("c:/g/refs/commun.csv"),
            Path("refs/commun.csv"),
        ]
        for chemin in chemins_alternatifs:
            if chemin.exists():
                patterns_path = str(chemin)
                break
    
    print(f"Fichier commun.csv: {os.path.abspath(patterns_path)}")
    print()
    
    # Charger les patterns
    patterns_count = charger_patterns_count(patterns_path, verbose=args.verbose, debug=args.debug)
    
    if not patterns_count:
        print()
        print("[ERREUR] Aucun pattern chargé depuis commun.csv")
        return 1
    
    print()
    
    if est_fichier_batch:
        # Mode batch
        print(f"Mode BATCH - Traitement de {args.question}")
        print("-" * 70)
        nb_lignes, fichier_sortie = traiter_fichier_batch(
            args.question, 
            patterns_count, 
            verbose=args.verbose, 
            debug=args.debug
        )
        return 0 if nb_lignes > 0 else 1
    
    else:
        # Mode unitaire - sortie JSON
        print(f"Question: \"{args.question}\"")
        print()
        
        # Détecter
        resultat = detecter_count(
            args.question,
            patterns_count,
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
