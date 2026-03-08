#*TO*#
__pgm__ = "importtest.py"
__version__ = "0.0.0"
__date__ = "01/01/1970 00:00"

"""
Test de détection des critères sur le fichier importtest.csv.

OBJECTIF :
- Lire refs/importtest.csv (25000 lignes)
- Appliquer detall pour détecter les critères
- Comparer avec la colonne 'attendu'
- Générer un fichier de résultat avec colonnes supplémentaires

COLONNES EN ENTRÉE :
- id : Identifiant de la ligne
- test : Expression à tester
- attendu : Nombre de critères attendus
- oripathologies : Pathologies de référence (séparées par ,)

COLONNES EN SORTIE (ajoutées) :
- nb_detall : Nombre de critères détectés par detall
- detecte : Pathologies détectées (uniquement si nb_detall ≠ attendu)

Usage :
    python importtest.py
    python importtest.py --verbose
    python importtest.py --limit 100
"""

import os
import sys
import csv
import json
import time
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from tqdm import tqdm

# Import de detall
try:
    from detall import charger_references, detecter_tout
    DETALL_DISPONIBLE = True
except ImportError as e:
    print(f"[ERREUR] Impossible d'importer detall: {e}")
    DETALL_DISPONIBLE = False
    sys.exit(1)


def formater_criteres(criteres: List[dict]) -> str:
    """
    Formate la liste des critères détectés en chaîne lisible.
    Format : tag [adj1, adj2], tag2, ...
    """
    parties = []
    for c in criteres:
        c_type = c.get('type', '')
        if c_type == 'tag':
            tag = c.get('canonique', c.get('detecte', '?'))
            adjs = c.get('adjectifs', [])
            if adjs:
                adjs_str = ', '.join(
                    a.get('canonique', str(a)) if isinstance(a, dict) else str(a)
                    for a in adjs
                )
                parties.append(f"{tag} [{adjs_str}]")
            else:
                parties.append(tag)
        elif c_type == 'meme':
            cible = c.get('cible', '?')
            parties.append(f"même:{cible}")
        elif c_type == 'age':
            label = c.get('label', '?')
            parties.append(f"âge:{label}")
        elif c_type == 'sexe':
            label = c.get('label', '?')
            parties.append(f"sexe:{label}")
        elif c_type == 'count':
            parties.append("COUNT")
        elif c_type == 'angle':
            label = c.get('label', c.get('detecte', '?'))
            parties.append(f"angle:{label}")
    
    return ', '.join(parties)


def compter_criteres_significatifs(criteres: List[dict]) -> int:
    """
    Compte les critères significatifs (hors count).
    On compte les tags, meme, angles, age, sexe comme critères.
    Seul 'count' (qui est un modificateur, pas un critère) est exclu.
    """
    count = 0
    for c in criteres:
        c_type = c.get('type', '')
        # On compte tous les critères sauf 'count' qui est un modificateur
        if c_type in ('tag', 'meme', 'angle', 'age', 'sexe'):
            count += 1
    return count


def lire_fichier_entree(chemin: Path) -> Tuple[List[dict], List[str]]:
    """
    Lit le fichier d'entrée CSV.
    
    Returns:
        Tuple (lignes, commentaires)
    """
    lignes = []
    commentaires = []
    
    encodages = ['utf-8-sig', 'utf-8', 'windows-1252']
    
    for encodage in encodages:
        try:
            with open(chemin, 'r', encoding=encodage, newline='') as f:
                # Lire toutes les lignes
                contenu = f.read()
                
            # Détecter le séparateur (tab ou point-virgule)
            premiere_ligne = contenu.split('\n')[0]
            if '\t' in premiere_ligne:
                sep = '\t'
            else:
                sep = ';'
            
            # Parser avec csv
            reader = csv.DictReader(
                contenu.splitlines(),
                delimiter=sep
            )
            
            for row in reader:
                # Ignorer les lignes vides ou commentaires
                first_val = list(row.values())[0] if row else ''
                if first_val and str(first_val).strip().startswith('#'):
                    commentaires.append(row)
                    continue
                
                # Convertir en dict propre
                ligne = {
                    'id': row.get('id', '').strip(),
                    'test': row.get('test', '').strip(),
                    'attendu': row.get('attendu', '0').strip(),
                    'oripathologies': row.get('oripathologies', '').strip()
                }
                
                if ligne['test']:  # Ignorer lignes sans test
                    lignes.append(ligne)
            
            print(f"  Encodage: {encodage}, Séparateur: {'TAB' if sep == '\\t' else ';'}")
            break
            
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            print(f"[ERREUR] Lecture avec {encodage}: {e}")
            continue
    
    return lignes, commentaires


def ecrire_fichier_sortie(chemin: Path, lignes: List[dict], stats: dict):
    """
    Écrit le fichier de sortie CSV (UTF-8-SIG, séparateur ;).
    """
    with open(chemin, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        
        # Entêtes
        writer.writerow(['id', 'test', 'attendu', 'oripathologies', 'nb_detall', 'detecte'])
        
        # Lignes
        for ligne in lignes:
            writer.writerow([
                ligne['id'],
                ligne['test'],
                ligne['attendu'],
                ligne['oripathologies'],
                ligne['nb_detall'],
                ligne.get('detecte', '')  # Vide si pas de différence
            ])
    
    print(f"✓ Fichier écrit: {os.path.abspath(chemin)}")


def main():
    """Point d'entrée principal."""
    print(f"╔════════════════════════════════════════════════════════════════")
    print(f"║ {__pgm__} V{__version__} - {__date__}")
    print(f"║ Test de détection sur importtest.csv (detall uniquement)")
    print(f"╚════════════════════════════════════════════════════════════════")
    print()
    
    parser = argparse.ArgumentParser(description="Test detall sur importtest.csv")
    parser.add_argument('--verbose', '-v', action='store_true', help='Affichage détaillé')
    parser.add_argument('--debug', '-d', action='store_true', help='Mode debug')
    parser.add_argument('--limit', '-l', type=int, default=0, help='Limiter à N lignes (0=tout)')
    parser.add_argument('--input', '-i', type=str, default='refs/importtest.csv', help='Fichier d\'entrée')
    parser.add_argument('--output', '-o', type=str, default='', help='Fichier de sortie (auto si vide)')
    
    args = parser.parse_args()
    
    # Trouver le fichier d'entrée
    script_dir = Path(__file__).parent
    
    # Chemins possibles
    chemins_possibles = [
        Path(args.input),
        script_dir / args.input,
        script_dir / "refs" / "importtest.csv",
        Path("c:/g/refs/importtest.csv"),
        Path("c:/cx/refs/importtest.csv"),
    ]
    
    fichier_entree = None
    for chemin in chemins_possibles:
        if chemin.exists():
            fichier_entree = chemin
            break
    
    if not fichier_entree:
        print(f"[ERREUR] Fichier introuvable: {args.input}")
        print("  Chemins testés:")
        for c in chemins_possibles:
            print(f"    - {c}")
        return 1
    
    print(f"Fichier d'entrée : {os.path.abspath(fichier_entree)}")
    
    # Fichier de sortie
    if args.output:
        fichier_sortie = Path(args.output)
    else:
        fichier_sortie = fichier_entree.parent / f"{fichier_entree.stem}_result.csv"
    
    print(f"Fichier de sortie: {os.path.abspath(fichier_sortie)}")
    print()
    
    # Charger les références detall
    print("Chargement des références detall...")
    start_load = time.time()
    references = charger_references(verbose=True, debug=args.debug)
    print(f"  → Chargé en {time.time() - start_load:.2f}s")
    print()
    
    # Lire le fichier d'entrée
    print("Lecture du fichier d'entrée...")
    lignes, commentaires = lire_fichier_entree(fichier_entree)
    print(f"  → {len(lignes)} lignes à traiter")
    
    if args.limit > 0:
        lignes = lignes[:args.limit]
        print(f"  → Limité à {len(lignes)} lignes (--limit)")
    
    print()
    
    # Statistiques
    stats = {
        'total': len(lignes),
        'ok': 0,
        'diff': 0,
        'erreurs': 0,
        'temps_total': 0
    }
    
    # Traitement
    print("Traitement avec detall...")
    print("-" * 70)
    
    start_time = time.time()
    
    for ligne in tqdm(lignes, desc="Détection", unit="ligne", 
                      bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]'):
        try:
            # Détecter avec detall
            resultat = detecter_tout(
                ligne['test'],
                references,
                verbose=False,
                debug=args.debug
            )
            
            # Compter les critères significatifs (pathologies)
            nb_detecte = compter_criteres_significatifs(resultat['criteres'])
            ligne['nb_detall'] = nb_detecte
            
            # Comparer avec attendu
            try:
                attendu = int(ligne['attendu'])
            except ValueError:
                attendu = 0
            
            if nb_detecte != attendu:
                # Différence : ajouter la colonne detecte
                ligne['detecte'] = formater_criteres(resultat['criteres'])
                stats['diff'] += 1
                
                if args.verbose:
                    tqdm.write(f"  [DIFF] id={ligne['id']}: attendu={attendu}, détecté={nb_detecte}")
                    tqdm.write(f"         test: {ligne['test']}")
                    tqdm.write(f"         détecté: {ligne['detecte']}")
            else:
                ligne['detecte'] = ''
                stats['ok'] += 1
            
        except Exception as e:
            ligne['nb_detall'] = -1
            ligne['detecte'] = f"ERREUR: {str(e)}"
            stats['erreurs'] += 1
            if args.verbose:
                tqdm.write(f"  [ERREUR] id={ligne['id']}: {e}")
    
    stats['temps_total'] = time.time() - start_time
    
    print("-" * 70)
    print()
    
    # Écrire le fichier de sortie
    ecrire_fichier_sortie(fichier_sortie, lignes, stats)
    print()
    
    # Résumé
    print("═" * 70)
    print("RÉSUMÉ")
    print("═" * 70)
    print(f"  Total traité    : {stats['total']:,} lignes")
    print(f"  OK (=attendu)   : {stats['ok']:,} ({100*stats['ok']/stats['total']:.1f}%)")
    print(f"  Différences     : {stats['diff']:,} ({100*stats['diff']/stats['total']:.1f}%)")
    print(f"  Erreurs         : {stats['erreurs']:,}")
    print(f"  Temps total     : {stats['temps_total']:.1f}s")
    print(f"  Temps/ligne     : {1000*stats['temps_total']/stats['total']:.2f}ms")
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
