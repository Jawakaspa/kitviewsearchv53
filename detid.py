#*TO*#
__pgm__ = "detid.py"
__version__ = "0.0.0"
__date__ = "01/01/1970 00:00"

"""
Module de détection des identifiants patients dans une question en langage naturel.

Ce module analyse une question pour détecter un identifiant patient explicite
(pattern "id XXX") et retourne un critère structuré SANS exécuter de requête SQL.

ARCHITECTURE :
- Module de DÉTECTION uniquement (chaînes de caractères)
- Retourne des structures de données (critères avec labels)
- Aucun accès à la base de données
- 1 question = au plus 1 identifiant détecté
- La recherche par identifiant retourne toujours 0 ou 1 résultat

DÉTECTION :
    Pattern : "id XXX" où XXX est alphanumérique
    - Au début : "id 10122 avec béance"
    - Au milieu : "patients id 10122 de moins de 30 ans"
    - Alphanumérique : "id ABC123"
    - Insensible à la casse : "ID 10122" = "id 10122"

POSITION DANS LE PIPELINE detall.py :
    detcount → detmeme → **detid** → detangles → dettags → detage → motsvides

    Placé APRÈS detmeme pour que "même portrait que id 10122" soit traité
    par detmeme (extraction de la référence), et AVANT les autres détecteurs
    pour que le numéro d'ID ne soit pas interprété comme un âge ou autre.

FORMAT DE SORTIE JSON :
{
    "criteres": [
        {
            "type": "id",
            "detecte": "id 10122",
            "label": "Patient ID 10122",
            "sql": {"colonne": "id", "operateur": "=", "valeur": 10122}
        }
    ],
    "residu": "texte restant après extraction"
}

INTÉGRATION AVEC LA SIMILARITÉ :
    "même portrait que id 10122" → Traité par detmeme (pas par detid)
    "id 10122"                  → Traité par detid
    "id 10122 avec béance"      → detid extrait l'ID, dettags détecte béance
                                   → jsonsql génère : WHERE p.id = 10122
                                     AND pathologie = 'beance'
                                   → Résultat : 0 ou 1 patient

Usage en import (depuis detall.py ou detia.py) :
    from detid import detecter_id
    resultat = detecter_id(question, verbose=True)

Usage CLI unitaire :
    python detid.py "id 10122"
    python detid.py "id 10122 avec béance" -v
    python detid.py "patients id ABC123 femme" -d

Usage CLI batch :
    python detid.py tests/testsidin.csv
    python detid.py tests/testsidin.csv -v
    # Sortie automatique : tests/testsidout.csv
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


# =============================================================================
# PATTERN DE DÉTECTION
# =============================================================================

# Pattern : "id" en tant que mot entier suivi d'un identifiant alphanumérique
# \b assure que "id" est un mot complet (pas "kid", "identifiant", etc.)
# [a-z0-9]+ capture l'identifiant (lowercase après standardise)
PATTERN_ID = re.compile(r'\bid\s+([a-z0-9]+)')


def _convertir_valeur_id(identifiant_str):
    """
    Convertit l'identifiant en int si possible, sinon garde en string.
    
    La colonne patients.id est INTEGER PRIMARY KEY, donc les identifiants
    numériques doivent être passés en int pour la comparaison SQL.
    Les identifiants alphanumériques restent en string (retourneront 0 résultat
    sur la colonne id INTEGER, mais le code reste robuste).
    
    Args:
        identifiant_str: Identifiant sous forme de chaîne
        
    Returns:
        int ou str selon le contenu
    """
    try:
        return int(identifiant_str)
    except (ValueError, TypeError):
        return identifiant_str


def detecter_id(question, verbose=False, debug=False):
    """
    Détecte un identifiant patient dans une question.
    
    Cherche le pattern "id XXX" où XXX est alphanumérique.
    Retourne au plus 1 critère (un seul identifiant par question).
    
    Args:
        question: Texte de la question en langage naturel
        verbose: Afficher les résultats intermédiaires
        debug: Afficher tous les détails
        
    Returns:
        dict: {
            'criteres': [
                {
                    'type': 'id',
                    'detecte': 'id 10122',
                    'label': 'Patient ID 10122',
                    'sql': {'colonne': 'id', 'operateur': '=', 'valeur': 10122}
                }
            ],
            'residu': 'texte restant'
        }
    """
    question_norm = standardise(question)
    
    if debug:
        print(f"[DEBUG] detid: Question normalisée: '{question_norm}'")
    
    match = PATTERN_ID.search(question_norm)
    
    if not match:
        if debug:
            print(f"[DEBUG] detid: Aucun pattern 'id XXX' trouvé")
        return {
            'criteres': [],
            'residu': question_norm
        }
    
    identifiant_str = match.group(1)
    texte_matche = match.group(0)
    identifiant_val = _convertir_valeur_id(identifiant_str)
    
    if debug:
        print(f"[DEBUG] detid: Match trouvé: '{texte_matche}' → identifiant='{identifiant_str}' (type={type(identifiant_val).__name__})")
    
    critere = {
        'type': 'id',
        'detecte': texte_matche,
        'label': f'Patient ID {identifiant_str}',
        'sql': {
            'colonne': 'id',
            'operateur': '=',
            'valeur': identifiant_val
        }
    }
    
    # Calculer le résidu : retirer le texte matché de la question
    avant = question_norm[:match.start()]
    apres = question_norm[match.end():]
    residu = (avant + ' ' + apres).strip()
    residu = re.sub(r'\s+', ' ', residu)
    
    if verbose or debug:
        print(f"  ✓ Détecté: '{texte_matche}' → ID {identifiant_str}")
    
    if debug:
        print(f"[DEBUG] detid: Résidu: '{residu}'")
    
    return {
        'criteres': [critere],
        'residu': residu
    }


def identifier_id(residu, filtres, verbose=False, debug=False):
    """
    Wrapper de compatibilité avec la signature standard des modules det*.
    
    SIGNATURE STANDARD :
        identifier_XXX(residu, [data,] filtres, verbose, debug) -> (filtres, residu)
    
    Note : detid n'a pas besoin de données externes (pas de CSV),
    donc la signature n'a pas de paramètre 'data'.
    
    Args:
        residu: Texte restant après détections précédentes
        filtres: Dict à enrichir {'listcount': ..., 'criteres': [...]}
        verbose: Mode verbose
        debug: Mode debug
        
    Returns:
        Tuple (filtres, residu)
    """
    if debug:
        print(f"[DEBUG] identifier_id: Analyse du résidu: '{residu}'")
    
    resultat = detecter_id(residu, verbose=verbose, debug=debug)
    
    for critere in resultat['criteres']:
        filtres['criteres'].append(critere)
    
    if verbose or debug:
        nb = len(resultat['criteres'])
        print(f"[DEBUG] identifier_id: {nb} critère(s) ajouté(s)")
    
    return filtres, resultat['residu']


def traiter_fichier_batch(fichier_entree, verbose=False, debug=False):
    """
    Traite un fichier de test batch et génère [nom_entrée]detid.csv.
    
    Format d'entrée : CSV avec colonne 'question'
    Format de sortie : question;L1;L2;...;Ln (résumé transposé)
    """
    chemin_entree = Path(fichier_entree)
    nom_base = chemin_entree.stem
    module_name = Path(__pgm__).stem  # 'detid'
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
        print(f"[ERREUR] Impossible de lire {os.path.abspath(fichier_entree)}")
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
        
        resultat = detecter_id(question, verbose=verbose, debug=debug)
        
        # Construire les lignes du résumé pour le CSV
        lignes_resume = []
        if resultat['criteres']:
            for j, c in enumerate(resultat['criteres'], 1):
                label = c.get('label', '?')
                lignes_resume.append(f"[id] {label}")
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
                print(f"        {j}. [id] {label}")
        else:
            print(f"        (aucun identifiant)")
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
    print(f"║ Détection des identifiants patients (pattern 'id XXX')")
    print(f"╚════════════════════════════════════════════════════════════════")
    print()
    
    parser = argparse.ArgumentParser(
        description="Détecte un identifiant patient dans une question en langage naturel",
        add_help=False
    )
    parser.add_argument('question', nargs='?', default=None,
                        help='Question en langage naturel OU fichier xxxin.csv')
    parser.add_argument('-v', '--verbose', action='store_true', help='Affichage modéré')
    parser.add_argument('-d', '--debug', action='store_true', help='Affichage complet')
    parser.add_argument('-h', '--help', action='store_true', help="Affiche l'aide")
    
    args = parser.parse_args()
    
    # Pas d'argument ou aide → afficher l'aide
    if args.question is None or args.help:
        print("Usage:")
        print(f"  python {__pgm__} \"<question>\"          Analyse une question")
        print(f"  python {__pgm__} tests/testsidin.csv   Traite un fichier batch")
        print()
        print("Options:")
        print("  -v, --verbose   Affichage modéré (résultats)")
        print("  -d, --debug     Affichage complet (tout)")
        print()
        print("Exemples:")
        print(f'  python {__pgm__} "id 10122"')
        print(f'  python {__pgm__} "id 10122 avec béance" -v')
        print(f'  python {__pgm__} "patients id ABC123 femme" -d')
        print(f'  python {__pgm__} tests/testsidin.csv -v')
        print()
        print("Pattern détecté : 'id XXX' où XXX est alphanumérique")
        print("Retourne toujours 0 ou 1 résultat (identifiant unique)")
        return 0
    
    # Déterminer si c'est un fichier batch ou une question unitaire
    fichier_batch = None
    if args.question.endswith('.csv'):
        chemins_possibles = [
            args.question,
            Path("tests") / args.question,
            Path("tests") / Path(args.question).name,
            Path(__file__).parent / "tests" / args.question,
            Path("c:/g/tests") / Path(args.question).name,
        ]
        
        for chemin in chemins_possibles:
            if Path(chemin).exists():
                fichier_batch = str(chemin)
                break
        
        if fichier_batch is None:
            print(f"[ERREUR] Fichier batch introuvable: {args.question}")
            print(f"  Chemins testés:")
            for chemin in chemins_possibles:
                print(f"    - {os.path.abspath(chemin)}")
            return 1
    
    print()
    
    if fichier_batch:
        # Mode batch
        print(f"Mode BATCH - Traitement de {os.path.abspath(fichier_batch)}")
        print("-" * 70)
        nb_lignes, fichier_sortie = traiter_fichier_batch(
            fichier_batch,
            verbose=args.verbose,
            debug=args.debug
        )
        return 0 if nb_lignes > 0 else 1
    
    else:
        # Mode unitaire - sortie JSON
        print(f"Question: \"{args.question}\"")
        print()
        
        resultat = detecter_id(
            args.question,
            verbose=args.verbose,
            debug=args.debug
        )
        
        print()
        print("═" * 70)
        print("RÉSULTAT (JSON)")
        print("═" * 70)
        print(json.dumps(resultat, indent=2, ensure_ascii=False))
        
        return 0


if __name__ == '__main__':
    sys.exit(main())
