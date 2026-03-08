#*TO*#
__pgm__ = "test_photofit.py"
__version__ = "0.0.0"
__date__ = "01/01/1970 00:00"

"""
Tests et validation du système Photofit.

Ce programme valide que le système de recherche de portraits similaires
fonctionne correctement en vérifiant que les variantes d'une même photo
sont bien retrouvées.

LOGIQUE DE TEST :
    Les photos sont organisées par groupes de 10 :
    - 1000 = original, 1001-1009 = variantes de 1000
    - 1010 = original, 1011-1019 = variantes de 1010
    - etc.
    
    Pour chaque original (1000, 1010, 1020...), on vérifie que ses 9 variantes
    sont retrouvées dans le top-N des résultats de recherche.

MÉTRIQUES :
    - Recall@N : % de variantes retrouvées dans le top N
    - MRR : Mean Reciprocal Rank (position moyenne inverse)
    - MAP : Mean Average Precision

USAGE :
    python test_photofit.py                      # Affiche l'aide
    python test_photofit.py --db photofit.db    # Lance les tests
    python test_photofit.py --db photofit.db -v # Mode verbose
    python test_photofit.py --db photofit.db --mode hair  # Teste uniquement hair
    python test_photofit.py --db photofit.db --limit 10   # Teste 10 groupes seulement
"""

import argparse
import json
import math
import sqlite3
import struct
import sys
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional

from tqdm import tqdm

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_DB_PATH = "photofit.db"
DEFAULT_TOP_N = 20  # Top N pour calculer le recall
GROUP_SIZE = 10     # Taille d'un groupe (1 original + 9 variantes)

WEIGHT_HAIR = 0.7
WEIGHT_FACE = 0.3


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES (copiées de search_similar.py)
# ═══════════════════════════════════════════════════════════════════════════════

def deserialize_float_vector(data: bytes) -> List[float]:
    """Désérialise des bytes en vecteur de floats."""
    if data is None:
        return []
    count = len(data) // 4
    return list(struct.unpack(f'<{count}f', data))


def cosine_distance(vec1: List[float], vec2: List[float]) -> float:
    """Calcule la distance cosinus entre deux vecteurs."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return float('inf')
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    
    if norm1 == 0 or norm2 == 0:
        return float('inf')
    
    similarity = dot_product / (norm1 * norm2)
    similarity = max(-1.0, min(1.0, similarity))
    
    return 1.0 - similarity


# ═══════════════════════════════════════════════════════════════════════════════
# BASE DE DONNÉES
# ═══════════════════════════════════════════════════════════════════════════════

def ouvrir_base(db_path: Path) -> sqlite3.Connection:
    """Ouvre la base de données."""
    if not db_path.exists():
        raise FileNotFoundError(f"Base de données introuvable: {db_path}")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def get_all_portraits(conn: sqlite3.Connection) -> Dict[str, dict]:
    """Récupère tous les portraits valides, indexés par idportrait."""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT idportrait, filepath, attributes_bin, hair_embedding, face_embedding
        FROM portraits 
        WHERE status = 'ok'
    """)
    
    portraits = {}
    for row in cursor.fetchall():
        portraits[row['idportrait']] = {
            'idportrait': row['idportrait'],
            'filepath': row['filepath'],
            'attributes_bin': row['attributes_bin'],
            'hair_embedding': deserialize_float_vector(row['hair_embedding']),
            'face_embedding': deserialize_float_vector(row['face_embedding']),
        }
    
    return portraits


def identifier_groupes(portraits: Dict[str, dict]) -> List[dict]:
    """
    Identifie les groupes de variantes (original + 9 variantes).
    
    Returns:
        Liste de dicts {base: 1000, original: '1000', variantes: ['1001', ...]}
    """
    # Extraire tous les IDs numériques
    ids_numeriques = []
    for idp in portraits.keys():
        try:
            ids_numeriques.append(int(idp))
        except ValueError:
            continue
    
    # Identifier les bases (multiples de 10)
    bases = set(id_num // GROUP_SIZE * GROUP_SIZE for id_num in ids_numeriques)
    
    groupes = []
    for base in sorted(bases):
        original = str(base)
        variantes = [str(base + i) for i in range(1, GROUP_SIZE)]
        
        # Vérifier que l'original existe
        if original not in portraits:
            continue
        
        # Filtrer les variantes existantes
        variantes_existantes = [v for v in variantes if v in portraits]
        
        if variantes_existantes:  # Au moins une variante
            groupes.append({
                'base': base,
                'original': original,
                'variantes': variantes_existantes,
                'nb_variantes': len(variantes_existantes)
            })
    
    return groupes


# ═══════════════════════════════════════════════════════════════════════════════
# RECHERCHE
# ═══════════════════════════════════════════════════════════════════════════════

def rechercher_top_n(ref_portrait: dict, tous_portraits: Dict[str, dict], 
                     exclude_id: str, mode: str, n: int) -> List[Tuple[str, float]]:
    """
    Recherche les top N portraits les plus similaires.
    
    Returns:
        Liste de tuples (idportrait, distance) triés par distance croissante
    """
    ref_hair = ref_portrait['hair_embedding']
    ref_face = ref_portrait['face_embedding']
    
    resultats = []
    
    for idp, portrait in tous_portraits.items():
        if idp == exclude_id:
            continue
        
        if mode == 'hair':
            distance = cosine_distance(ref_hair, portrait['hair_embedding'])
        elif mode == 'face':
            distance = cosine_distance(ref_face, portrait['face_embedding'])
        else:  # 'both'
            dist_hair = cosine_distance(ref_hair, portrait['hair_embedding'])
            dist_face = cosine_distance(ref_face, portrait['face_embedding'])
            if portrait['face_embedding']:
                distance = WEIGHT_HAIR * dist_hair + WEIGHT_FACE * dist_face
            else:
                distance = dist_hair
        
        resultats.append((idp, distance))
    
    resultats.sort(key=lambda x: x[1])
    return resultats[:n]


# ═══════════════════════════════════════════════════════════════════════════════
# MÉTRIQUES
# ═══════════════════════════════════════════════════════════════════════════════

def calculer_recall_at_n(resultats: List[Tuple[str, float]], 
                         variantes_attendues: List[str], n: int) -> float:
    """
    Calcule le Recall@N : % de variantes attendues présentes dans le top N.
    """
    top_n_ids = set(r[0] for r in resultats[:n])
    variantes_trouvees = len(set(variantes_attendues) & top_n_ids)
    return variantes_trouvees / len(variantes_attendues) if variantes_attendues else 0.0


def calculer_mrr(resultats: List[Tuple[str, float]], 
                 variantes_attendues: List[str]) -> float:
    """
    Calcule le Mean Reciprocal Rank (MRR).
    MRR = moyenne de 1/rang pour chaque variante trouvée.
    """
    resultats_ids = [r[0] for r in resultats]
    reciprocal_ranks = []
    
    for var in variantes_attendues:
        try:
            rang = resultats_ids.index(var) + 1  # rang commence à 1
            reciprocal_ranks.append(1.0 / rang)
        except ValueError:
            reciprocal_ranks.append(0.0)  # Non trouvé
    
    return sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0


def calculer_precision_at_k(resultats: List[Tuple[str, float]], 
                            variantes_attendues: List[str], k: int) -> float:
    """
    Calcule la Precision@k : parmi les k premiers résultats, combien sont pertinents.
    """
    top_k_ids = set(r[0] for r in resultats[:k])
    pertinents = len(set(variantes_attendues) & top_k_ids)
    return pertinents / k if k > 0 else 0.0


# ═══════════════════════════════════════════════════════════════════════════════
# TESTS
# ═══════════════════════════════════════════════════════════════════════════════

def tester_groupe(groupe: dict, tous_portraits: Dict[str, dict], 
                  mode: str, top_n: int, verbose: bool = False) -> dict:
    """
    Teste un groupe (original + variantes).
    
    Returns:
        Dict avec les métriques du groupe
    """
    original = groupe['original']
    variantes = groupe['variantes']
    
    ref_portrait = tous_portraits[original]
    
    # Rechercher
    resultats = rechercher_top_n(ref_portrait, tous_portraits, original, mode, top_n * 2)
    
    # Calculer les métriques
    recall_10 = calculer_recall_at_n(resultats, variantes, 10)
    recall_20 = calculer_recall_at_n(resultats, variantes, 20)
    mrr = calculer_mrr(resultats, variantes)
    precision_10 = calculer_precision_at_k(resultats, variantes, 10)
    
    # Identifier les variantes trouvées et leurs rangs
    resultats_ids = [r[0] for r in resultats]
    variantes_rangs = {}
    for var in variantes:
        try:
            variantes_rangs[var] = resultats_ids.index(var) + 1
        except ValueError:
            variantes_rangs[var] = None
    
    return {
        'base': groupe['base'],
        'original': original,
        'nb_variantes': len(variantes),
        'recall@10': recall_10,
        'recall@20': recall_20,
        'mrr': mrr,
        'precision@10': precision_10,
        'variantes_rangs': variantes_rangs,
    }


def lancer_tests(conn: sqlite3.Connection, mode: str, top_n: int,
                 limit: Optional[int] = None, verbose: bool = False, 
                 debug: bool = False) -> dict:
    """
    Lance les tests sur tous les groupes.
    
    Returns:
        Dict avec les métriques globales
    """
    print("Chargement des portraits...")
    tous_portraits = get_all_portraits(conn)
    print(f"  → {len(tous_portraits)} portraits chargés")
    
    print("Identification des groupes...")
    groupes = identifier_groupes(tous_portraits)
    print(f"  → {len(groupes)} groupes identifiés")
    
    if limit:
        groupes = groupes[:limit]
        print(f"  → Limité à {len(groupes)} groupes")
    
    print()
    print(f"Lancement des tests (mode={mode}, top_n={top_n})...")
    print()
    
    resultats_groupes = []
    
    for groupe in tqdm(groupes, desc="Test groupes", unit="grp"):
        resultat = tester_groupe(groupe, tous_portraits, mode, top_n, verbose)
        resultats_groupes.append(resultat)
        
        if debug:
            print(f"\n[DEBUG] Groupe {groupe['base']}:")
            print(f"  Recall@10: {resultat['recall@10']:.2%}")
            print(f"  Rangs: {resultat['variantes_rangs']}")
    
    # Agrégation des métriques
    nb_groupes = len(resultats_groupes)
    
    metrics = {
        'mode': mode,
        'top_n': top_n,
        'nb_groupes': nb_groupes,
        'nb_portraits': len(tous_portraits),
        
        'recall@10_mean': sum(r['recall@10'] for r in resultats_groupes) / nb_groupes,
        'recall@20_mean': sum(r['recall@20'] for r in resultats_groupes) / nb_groupes,
        'mrr_mean': sum(r['mrr'] for r in resultats_groupes) / nb_groupes,
        'precision@10_mean': sum(r['precision@10'] for r in resultats_groupes) / nb_groupes,
        
        'recall@10_min': min(r['recall@10'] for r in resultats_groupes),
        'recall@10_max': max(r['recall@10'] for r in resultats_groupes),
        
        'groupes_parfaits_10': sum(1 for r in resultats_groupes if r['recall@10'] == 1.0),
        'groupes_parfaits_20': sum(1 for r in resultats_groupes if r['recall@20'] == 1.0),
        
        'resultats_detail': resultats_groupes,
    }
    
    return metrics


# ═══════════════════════════════════════════════════════════════════════════════
# AFFICHAGE
# ═══════════════════════════════════════════════════════════════════════════════

def afficher_resultats(metrics: dict) -> None:
    """Affiche les résultats des tests."""
    print()
    print("═" * 70)
    print("RÉSULTATS DES TESTS PHOTOFIT")
    print("═" * 70)
    print()
    
    print(f"Configuration:")
    print(f"  Mode embedding : {metrics['mode']}")
    print(f"  Groupes testés : {metrics['nb_groupes']}")
    print(f"  Portraits total: {metrics['nb_portraits']}")
    print()
    
    print("Métriques globales:")
    print(f"  ┌{'─'*50}┐")
    print(f"  │ {'Recall@10 (moyen)':<30} {metrics['recall@10_mean']:>15.2%} │")
    print(f"  │ {'Recall@20 (moyen)':<30} {metrics['recall@20_mean']:>15.2%} │")
    print(f"  │ {'MRR (moyen)':<30} {metrics['mrr_mean']:>15.4f} │")
    print(f"  │ {'Precision@10 (moyenne)':<30} {metrics['precision@10_mean']:>15.2%} │")
    print(f"  ├{'─'*50}┤")
    print(f"  │ {'Recall@10 (min)':<30} {metrics['recall@10_min']:>15.2%} │")
    print(f"  │ {'Recall@10 (max)':<30} {metrics['recall@10_max']:>15.2%} │")
    print(f"  ├{'─'*50}┤")
    print(f"  │ {'Groupes parfaits @10':<30} {metrics['groupes_parfaits_10']:>12}/{metrics['nb_groupes']:<2} │")
    print(f"  │ {'Groupes parfaits @20':<30} {metrics['groupes_parfaits_20']:>12}/{metrics['nb_groupes']:<2} │")
    print(f"  └{'─'*50}┘")
    print()
    
    # Interprétation
    recall_10 = metrics['recall@10_mean']
    print("Interprétation:")
    if recall_10 >= 0.9:
        print("  ✅ EXCELLENT - Le système retrouve très bien les variantes")
    elif recall_10 >= 0.7:
        print("  ✓ BON - Le système fonctionne correctement")
    elif recall_10 >= 0.5:
        print("  ⚠ MOYEN - Des améliorations sont nécessaires")
    else:
        print("  ✗ INSUFFISANT - Le système ne fonctionne pas correctement")
    print()


def afficher_pires_groupes(metrics: dict, n: int = 5) -> None:
    """Affiche les groupes avec le plus mauvais recall."""
    resultats = metrics['resultats_detail']
    pires = sorted(resultats, key=lambda x: x['recall@10'])[:n]
    
    print(f"Les {n} pires groupes (Recall@10):")
    print("─" * 50)
    for r in pires:
        print(f"  Groupe {r['base']}: Recall@10={r['recall@10']:.2%}")
        manquants = [v for v, rang in r['variantes_rangs'].items() if rang is None or rang > 10]
        if manquants:
            print(f"    Manquants dans top 10: {', '.join(manquants)}")
    print()


# ═══════════════════════════════════════════════════════════════════════════════
# PROGRAMME PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def afficher_aide():
    """Affiche l'aide du programme."""
    print("=" * 70)
    print(f"{__pgm__} - Tests et validation du système Photofit")
    print("=" * 70)
    print()
    print("USAGE :")
    print(f"  python {__pgm__} [options]")
    print()
    print("OPTIONS :")
    print("  --db FILE          Chemin de la base (défaut: photofit.db)")
    print("  --mode MODE        Mode de recherche: hair, face, both (défaut: both)")
    print("  --top N            Top N pour le recall (défaut: 20)")
    print("  --limit N          Nombre de groupes à tester (défaut: tous)")
    print("  --show-worst N     Affiche les N pires groupes (défaut: 5)")
    print("  -v, --verbose      Mode verbose")
    print("  -d, --debug        Mode debug")
    print()
    print("EXEMPLES :")
    print(f"  python {__pgm__} --db photofit.db")
    print(f"  python {__pgm__} --db photofit.db --mode hair -v")
    print(f"  python {__pgm__} --db photofit.db --limit 10 --show-worst 3")
    print()


def main():
    """Point d'entrée principal."""
    print(f"{__pgm__} V{__version__} - {__date__}")
    print()
    
    # Pas d'arguments spécifiques → aide
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        afficher_aide()
        return 0
    
    # Parser les arguments
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--db', type=str, default=DEFAULT_DB_PATH)
    parser.add_argument('--mode', type=str, default='both', choices=['hair', 'face', 'both'])
    parser.add_argument('--top', type=int, default=DEFAULT_TOP_N)
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--show-worst', type=int, default=5)
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-d', '--debug', action='store_true')
    
    args = parser.parse_args()
    verbose = args.verbose or args.debug
    debug = args.debug
    
    # Ouvrir la base
    db_path = Path(args.db).resolve()
    try:
        conn = ouvrir_base(db_path)
    except FileNotFoundError as e:
        print(f"ERREUR : {e}")
        return 1
    
    print(f"Base: {db_path}")
    print()
    
    # Lancer les tests
    start_time = time.time()
    metrics = lancer_tests(conn, args.mode, args.top, args.limit, verbose, debug)
    elapsed = time.time() - start_time
    
    # Afficher les résultats
    afficher_resultats(metrics)
    
    if args.show_worst > 0:
        afficher_pires_groupes(metrics, args.show_worst)
    
    print(f"Temps d'exécution: {elapsed:.1f}s")
    print()
    
    conn.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
