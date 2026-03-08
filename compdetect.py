# compdetect.py V1.0.1 - 13/12/2025 21:44:39
__pgm__ = "compdetect.py"
__version__ = "1.0.1"
__date__ = "13/12/2025 21:44:39"

"""
Programme de comparaison des résultats de détection entre detall.py et detia.py.

Ce programme analyse les fichiers CSV de sortie générés par les deux pipelines
et produit un rapport détaillé des différences pour évaluer objectivement
la qualité de détection de l'approche IA vs l'approche traditionnelle.

ENTRÉES :
- fichier_detall.csv : Sortie de detall.py (ex: questionspats100_out.csv)
- fichier_detia.csv  : Sortie de detia.py (ex: questionspats100_out_ia.csv)

SORTIE :
- Rapport console avec statistiques
- Fichier CSV de comparaison ligne par ligne (optionnel: --output)

MÉTRIQUES CALCULÉES :
- Concordance nb_criteres
- Concordance tags (en ignorant la casse et les accents)
- Concordance adjectifs
- Concordance ages
- Différences de résidu

Usage :
    python compdetect.py questionspats100_out.csv questionspats100_out_ia.csv
    python compdetect.py questionspats100_out.csv questionspats100_out_ia.csv --output comparaison.csv
"""

import csv
import sys
import argparse
import unicodedata
import re
from pathlib import Path
from collections import Counter


def normaliser_texte(texte: str) -> str:
    """
    Normalise un texte pour comparaison :
    - Minuscules
    - Suppression des accents
    - Suppression des % (format SQL LIKE)
    - Normalisation des espaces
    """
    if not texte:
        return ""
    
    texte = texte.lower().strip()
    
    # Supprimer les % du format SQL LIKE
    texte = texte.replace('%', '')
    
    # Supprimer les accents
    texte = unicodedata.normalize('NFD', texte)
    texte = ''.join(char for char in texte if unicodedata.category(char) != 'Mn')
    
    # Normaliser les espaces
    texte = re.sub(r'\s+', ' ', texte)
    
    return texte.strip()


def parser_liste(valeur: str) -> set:
    """
    Parse une liste CSV (séparateur virgule) en ensemble normalisé.
    """
    if not valeur or valeur.strip() == '':
        return set()
    
    elements = [normaliser_texte(e.strip()) for e in valeur.split(',')]
    return set(e for e in elements if e)


def lire_csv_sortie(fichier: str) -> list:
    """
    Lit un fichier CSV de sortie (detall ou detia).
    Retourne une liste de dictionnaires avec les colonnes normalisées.
    """
    lignes = []
    
    encodages = ["utf-8-sig", "utf-8", "windows-1252"]
    
    for encodage in encodages:
        try:
            with open(fichier, 'r', encoding=encodage, newline='') as f:
                reader = csv.DictReader(
                    (row for row in f if not row.startswith('#')),
                    delimiter=';'
                )
                
                for row in reader:
                    # Ignorer les lignes d'entête ou vides
                    if not row.get('question'):
                        continue
                    
                    lignes.append({
                        'question': row.get('question', ''),
                        'listcount': row.get('listcount', 'LIST'),
                        'nb_criteres': int(row.get('nb_criteres', 0) or 0),
                        'tags': row.get('tags', ''),
                        'adjectifs': row.get('adjectifs', ''),
                        'ages': row.get('ages', ''),
                        'residu': row.get('residu', ''),
                        'latency_ms': float(row.get('latency_ms', 0) or 0)
                    })
            
            return lignes
            
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            print(f"[ERREUR] Lecture {fichier}: {e}")
            return []
    
    return lignes


def comparer_ligne(ligne_detall: dict, ligne_detia: dict) -> dict:
    """
    Compare une ligne de detall avec une ligne de detia.
    Retourne un dictionnaire avec les métriques de comparaison.
    """
    # Parser les listes en ensembles normalisés
    tags_detall = parser_liste(ligne_detall['tags'])
    tags_detia = parser_liste(ligne_detia['tags'])
    
    adjs_detall = parser_liste(ligne_detall['adjectifs'])
    adjs_detia = parser_liste(ligne_detia['adjectifs'])
    
    ages_detall = parser_liste(ligne_detall['ages'])
    ages_detia = parser_liste(ligne_detia['ages'])
    
    # Calculer les métriques
    tags_communs = tags_detall & tags_detia
    tags_only_detall = tags_detall - tags_detia
    tags_only_detia = tags_detia - tags_detall
    
    adjs_communs = adjs_detall & adjs_detia
    adjs_only_detall = adjs_detall - adjs_detia
    adjs_only_detia = adjs_detia - adjs_detall
    
    ages_communs = ages_detall & ages_detia
    ages_only_detall = ages_detall - ages_detia
    ages_only_detia = ages_detia - ages_detall
    
    # Score de concordance tags (Jaccard)
    if tags_detall or tags_detia:
        tags_jaccard = len(tags_communs) / len(tags_detall | tags_detia)
    else:
        tags_jaccard = 1.0  # Accord si les deux sont vides
    
    # Concordance exacte
    tags_exact = (tags_detall == tags_detia)
    nb_criteres_exact = (ligne_detall['nb_criteres'] == ligne_detia['nb_criteres'])
    listcount_exact = (ligne_detall['listcount'] == ligne_detia['listcount'])
    
    return {
        'question_detall': ligne_detall['question'],
        'question_detia': ligne_detia['question'],
        
        'listcount_detall': ligne_detall['listcount'],
        'listcount_detia': ligne_detia['listcount'],
        'listcount_match': listcount_exact,
        
        'nb_criteres_detall': ligne_detall['nb_criteres'],
        'nb_criteres_detia': ligne_detia['nb_criteres'],
        'nb_criteres_match': nb_criteres_exact,
        'nb_criteres_diff': ligne_detia['nb_criteres'] - ligne_detall['nb_criteres'],
        
        'tags_detall': ligne_detall['tags'],
        'tags_detia': ligne_detia['tags'],
        'tags_match': tags_exact,
        'tags_jaccard': tags_jaccard,
        'tags_communs': ', '.join(sorted(tags_communs)),
        'tags_only_detall': ', '.join(sorted(tags_only_detall)),
        'tags_only_detia': ', '.join(sorted(tags_only_detia)),
        
        'adjs_detall': ligne_detall['adjectifs'],
        'adjs_detia': ligne_detia['adjectifs'],
        'adjs_communs': ', '.join(sorted(adjs_communs)),
        'adjs_only_detall': ', '.join(sorted(adjs_only_detall)),
        'adjs_only_detia': ', '.join(sorted(adjs_only_detia)),
        
        'ages_detall': ligne_detall['ages'],
        'ages_detia': ligne_detia['ages'],
        'ages_communs': ', '.join(sorted(ages_communs)),
        'ages_only_detall': ', '.join(sorted(ages_only_detall)),
        'ages_only_detia': ', '.join(sorted(ages_only_detia)),
        
        'residu_detall': ligne_detall['residu'],
        'residu_detia': ligne_detia['residu'],
        
        'latency_ms': ligne_detia['latency_ms']
    }


def generer_rapport(comparaisons: list) -> dict:
    """
    Génère un rapport statistique à partir des comparaisons.
    """
    total = len(comparaisons)
    
    if total == 0:
        return {'total': 0}
    
    # Comptages
    listcount_ok = sum(1 for c in comparaisons if c['listcount_match'])
    nb_criteres_ok = sum(1 for c in comparaisons if c['nb_criteres_match'])
    tags_exact_ok = sum(1 for c in comparaisons if c['tags_match'])
    
    # Jaccard moyen pour les tags
    tags_jaccard_moy = sum(c['tags_jaccard'] for c in comparaisons) / total
    
    # Comptage des différences
    detall_plus = sum(1 for c in comparaisons if c['nb_criteres_diff'] < 0)  # detall trouve plus
    detia_plus = sum(1 for c in comparaisons if c['nb_criteres_diff'] > 0)   # detia trouve plus
    
    # Tags uniques trouvés
    all_tags_only_detall = Counter()
    all_tags_only_detia = Counter()
    
    for c in comparaisons:
        for tag in c['tags_only_detall'].split(', '):
            if tag.strip():
                all_tags_only_detall[tag.strip()] += 1
        for tag in c['tags_only_detia'].split(', '):
            if tag.strip():
                all_tags_only_detia[tag.strip()] += 1
    
    # Latence
    latencies = [c['latency_ms'] for c in comparaisons if c['latency_ms'] > 0]
    latency_moy = sum(latencies) / len(latencies) if latencies else 0
    latency_min = min(latencies) if latencies else 0
    latency_max = max(latencies) if latencies else 0
    
    return {
        'total': total,
        'listcount_ok': listcount_ok,
        'listcount_pct': 100 * listcount_ok / total,
        'nb_criteres_ok': nb_criteres_ok,
        'nb_criteres_pct': 100 * nb_criteres_ok / total,
        'tags_exact_ok': tags_exact_ok,
        'tags_exact_pct': 100 * tags_exact_ok / total,
        'tags_jaccard_moy': tags_jaccard_moy,
        'detall_plus': detall_plus,
        'detia_plus': detia_plus,
        'egalite': total - detall_plus - detia_plus,
        'tags_only_detall': all_tags_only_detall.most_common(10),
        'tags_only_detia': all_tags_only_detia.most_common(10),
        'latency_moy': latency_moy,
        'latency_min': latency_min,
        'latency_max': latency_max
    }


def afficher_rapport(rapport: dict, comparaisons: list):
    """
    Affiche le rapport de comparaison en console.
    """
    print()
    print("=" * 80)
    print("RAPPORT DE COMPARAISON DETALL vs DETIA")
    print("=" * 80)
    print()
    
    print(f"Nombre de questions comparées : {rapport['total']}")
    print()
    
    print("─" * 80)
    print("CONCORDANCES GLOBALES")
    print("─" * 80)
    print(f"  listcount (LIST/COUNT)     : {rapport['listcount_ok']:3d}/{rapport['total']} ({rapport['listcount_pct']:.1f}%)")
    print(f"  nb_criteres (exact)        : {rapport['nb_criteres_ok']:3d}/{rapport['total']} ({rapport['nb_criteres_pct']:.1f}%)")
    print(f"  tags (concordance exacte)  : {rapport['tags_exact_ok']:3d}/{rapport['total']} ({rapport['tags_exact_pct']:.1f}%)")
    print(f"  tags (Jaccard moyen)       : {rapport['tags_jaccard_moy']:.1%}")
    print()
    
    print("─" * 80)
    print("DISTRIBUTION NB_CRITERES")
    print("─" * 80)
    print(f"  detall trouve plus  : {rapport['detall_plus']:3d} questions")
    print(f"  detia trouve plus   : {rapport['detia_plus']:3d} questions")
    print(f"  Égalité             : {rapport['egalite']:3d} questions")
    print()
    
    print("─" * 80)
    print("TAGS DÉTECTÉS UNIQUEMENT PAR DETALL (top 10)")
    print("─" * 80)
    if rapport['tags_only_detall']:
        for tag, count in rapport['tags_only_detall']:
            print(f"  {tag:40s} : {count} fois")
    else:
        print("  (aucun)")
    print()
    
    print("─" * 80)
    print("TAGS DÉTECTÉS UNIQUEMENT PAR DETIA (top 10)")
    print("─" * 80)
    if rapport['tags_only_detia']:
        for tag, count in rapport['tags_only_detia']:
            print(f"  {tag:40s} : {count} fois")
    else:
        print("  (aucun)")
    print()
    
    print("─" * 80)
    print("LATENCE IA (detia)")
    print("─" * 80)
    print(f"  Moyenne : {rapport['latency_moy']:.0f} ms")
    print(f"  Min     : {rapport['latency_min']:.0f} ms")
    print(f"  Max     : {rapport['latency_max']:.0f} ms")
    print()
    
    # Exemples de divergences
    print("─" * 80)
    print("EXEMPLES DE DIVERGENCES (5 premiers)")
    print("─" * 80)
    
    divergences = [c for c in comparaisons if not c['tags_match']][:5]
    
    for i, c in enumerate(divergences, 1):
        print(f"\n  [{i}] Question (detia): {c['question_detia'][:60]}...")
        print(f"      detall tags: {c['tags_detall'] or '(vide)'}")
        print(f"      detia tags : {c['tags_detia'] or '(vide)'}")
        if c['tags_only_detall']:
            print(f"      → Manque detia: {c['tags_only_detall']}")
        if c['tags_only_detia']:
            print(f"      → Extra detia : {c['tags_only_detia']}")
    
    print()
    print("=" * 80)


def ecrire_csv_comparaison(comparaisons: list, fichier_sortie: str):
    """
    Écrit le fichier CSV de comparaison détaillée.
    """
    colonnes = [
        'question_detia',
        'listcount_match', 'listcount_detall', 'listcount_detia',
        'nb_criteres_match', 'nb_criteres_detall', 'nb_criteres_detia', 'nb_criteres_diff',
        'tags_match', 'tags_jaccard',
        'tags_detall', 'tags_detia',
        'tags_communs', 'tags_only_detall', 'tags_only_detia',
        'adjs_detall', 'adjs_detia',
        'ages_detall', 'ages_detia',
        'residu_detall', 'residu_detia',
        'latency_ms'
    ]
    
    with open(fichier_sortie, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=colonnes, delimiter=';', extrasaction='ignore')
        writer.writeheader()
        writer.writerows(comparaisons)
    
    print(f"✓ Comparaison détaillée écrite dans : {fichier_sortie}")


def main():
    """Point d'entrée CLI."""
    print(f"╔════════════════════════════════════════════════════════════════")
    print(f"║ {__pgm__} V{__version__} - {__date__}")
    print(f"║ Comparaison des résultats detall.py vs detia.py")
    print(f"╚════════════════════════════════════════════════════════════════")
    print()
    
    parser = argparse.ArgumentParser(
        description="Compare les fichiers de sortie de detall.py et detia.py"
    )
    parser.add_argument('fichier_detall', help='Fichier CSV sortie de detall.py')
    parser.add_argument('fichier_detia', help='Fichier CSV sortie de detia.py')
    parser.add_argument('--output', '-o', help='Fichier CSV de comparaison détaillée (optionnel)')
    
    args = parser.parse_args()
    
    # Vérifier les fichiers (avec recherche dans tests/)
    def trouver_fichier(nom):
        """Cherche un fichier dans plusieurs répertoires."""
        chemin = Path(nom)
        if chemin.exists():
            return chemin
        # Chercher dans tests/
        for rep in [Path('tests'), Path('c:/g/tests'), Path('c:/cx/tests')]:
            candidat = rep / chemin.name
            if candidat.exists():
                return candidat
        return None
    
    fichier_detall = trouver_fichier(args.fichier_detall)
    fichier_detia = trouver_fichier(args.fichier_detia)
    
    if not fichier_detall:
        print(f"[ERREUR] Fichier introuvable : {args.fichier_detall}")
        return 1
    
    if not fichier_detia:
        print(f"[ERREUR] Fichier introuvable : {args.fichier_detia}")
        return 1
    
    print(f"Fichier detall : {fichier_detall}")
    print(f"Fichier detia  : {fichier_detia}")
    print()
    
    # Lire les fichiers
    print("Lecture des fichiers...")
    lignes_detall = lire_csv_sortie(str(fichier_detall))
    lignes_detia = lire_csv_sortie(str(fichier_detia))
    
    print(f"  detall : {len(lignes_detall)} lignes")
    print(f"  detia  : {len(lignes_detia)} lignes")
    
    # Vérifier la correspondance
    if len(lignes_detall) != len(lignes_detia):
        print(f"\n[ATTENTION] Nombre de lignes différent !")
    
    # Comparer ligne par ligne
    print("\nComparaison en cours...")
    
    comparaisons = []
    nb_lignes = min(len(lignes_detall), len(lignes_detia))
    
    for i in range(nb_lignes):
        comp = comparer_ligne(lignes_detall[i], lignes_detia[i])
        comparaisons.append(comp)
    
    # Générer et afficher le rapport
    rapport = generer_rapport(comparaisons)
    afficher_rapport(rapport, comparaisons)
    
    # Écrire le CSV si demandé
    if args.output:
        ecrire_csv_comparaison(comparaisons, args.output)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
