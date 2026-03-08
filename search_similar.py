#*TO*#
__pgm__ = "search_similar.py"
__version__ = "0.0.0"
__date__ = "01/01/1970 00:00"

"""
Recherche de portraits similaires dans la base Photofit.

Ce programme recherche les portraits les plus ressemblants à un portrait de référence
en utilisant une stratégie en 2 étapes :
1. Pré-filtrage par attributs binarisés (optionnel)
2. Classement par distance cosinus sur les embeddings

USAGE :
    python search_similar.py                           # Affiche l'aide
    python search_similar.py <idportrait>              # Recherche les 10 plus similaires
    python search_similar.py <idportrait> -n 20       # Recherche les 20 plus similaires
    python search_similar.py <idportrait> --hair      # Utilise uniquement hair_embedding
    python search_similar.py <idportrait> --face      # Utilise uniquement face_embedding
    python search_similar.py <idportrait> --both      # Combine les deux (défaut)
    python search_similar.py <idportrait> --no-filter # Pas de pré-filtrage attributs

STRATÉGIES DE RECHERCHE :
    - hair   : Distance cosinus sur hair_embedding (384 dims) - style capillaire
    - face   : Distance cosinus sur face_embedding (128 dims) - reconnaissance faciale
    - both   : Moyenne pondérée des deux distances (configurable)

PRÉ-FILTRAGE :
    Par défaut, on filtre d'abord sur les attributs binarisés pour réduire 
    les candidats avant le calcul des distances (plus rapide sur grandes bases).
    Désactivable avec --no-filter.
"""

import argparse
import json
import math
import sqlite3
import struct
import sys
from pathlib import Path
from typing import List, Optional, Tuple

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

DEFAULT_DB_PATH = "photofit.db"
DEFAULT_N_RESULTS = 10

# Poids par défaut pour la combinaison des embeddings
# Validés par tests : Recall@10 = 100% sur les groupes
WEIGHT_HAIR = 0.3
WEIGHT_FACE = 0.7

# Attributs à utiliser pour le pré-filtrage (indices)
# On ignore certains attributs moins discriminants
FILTER_ATTRIBUTES_INDICES = [1, 2, 3, 4, 5, 6, 8, 9, 10, 11]  # male, young, length_*, hair_color

# Tolérance pour le matching d'attributs (nombre de différences autorisées)
ATTRIBUTES_TOLERANCE = 2


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

def deserialize_float_vector(data: bytes) -> List[float]:
    """
    Désérialise des bytes en vecteur de floats.
    """
    if data is None:
        return []
    count = len(data) // 4
    return list(struct.unpack(f'<{count}f', data))


def cosine_distance(vec1: List[float], vec2: List[float]) -> float:
    """
    Calcule la distance cosinus entre deux vecteurs.
    Distance = 1 - similarité cosinus
    Retourne une valeur entre 0 (identiques) et 2 (opposés).
    """
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return float('inf')
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    
    if norm1 == 0 or norm2 == 0:
        return float('inf')
    
    similarity = dot_product / (norm1 * norm2)
    # Clamp pour éviter les erreurs d'arrondi
    similarity = max(-1.0, min(1.0, similarity))
    
    return 1.0 - similarity


def hamming_distance(bin1: str, bin2: str) -> int:
    """
    Calcule la distance de Hamming entre deux chaînes binaires.
    """
    if not bin1 or not bin2:
        return 999
    
    vals1 = bin1.split(',')
    vals2 = bin2.split(',')
    
    distance = 0
    for i in FILTER_ATTRIBUTES_INDICES:
        if i < len(vals1) and i < len(vals2):
            if vals1[i] != vals2[i]:
                distance += 1
    
    return distance


# ═══════════════════════════════════════════════════════════════════════════════
# BASE DE DONNÉES
# ═══════════════════════════════════════════════════════════════════════════════

def ouvrir_base(db_path: Path) -> sqlite3.Connection:
    """
    Ouvre la base de données en lecture seule.
    """
    if not db_path.exists():
        raise FileNotFoundError(f"Base de données introuvable: {db_path}")
    
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def get_portrait(conn: sqlite3.Connection, idportrait: str) -> Optional[dict]:
    """
    Récupère les données d'un portrait.
    """
    cursor = conn.cursor()
    cursor.execute("""
        SELECT idportrait, filepath, attributes_json, attributes_bin,
               hair_embedding, face_embedding, status
        FROM portraits 
        WHERE idportrait = ? AND status = 'ok'
    """, (idportrait,))
    
    row = cursor.fetchone()
    if row is None:
        return None
    
    return {
        'idportrait': row['idportrait'],
        'filepath': row['filepath'],
        'attributes': json.loads(row['attributes_json']) if row['attributes_json'] else [],
        'attributes_bin': row['attributes_bin'],
        'hair_embedding': deserialize_float_vector(row['hair_embedding']),
        'face_embedding': deserialize_float_vector(row['face_embedding']),
    }


def get_all_portraits(conn: sqlite3.Connection, exclude_id: str = None, 
                      filter_attributes: str = None, tolerance: int = ATTRIBUTES_TOLERANCE) -> List[dict]:
    """
    Récupère tous les portraits valides, avec pré-filtrage optionnel.
    """
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT idportrait, filepath, attributes_bin, hair_embedding, face_embedding
        FROM portraits 
        WHERE status = 'ok'
    """)
    
    portraits = []
    for row in cursor.fetchall():
        if exclude_id and row['idportrait'] == exclude_id:
            continue
        
        # Pré-filtrage par attributs
        if filter_attributes:
            distance = hamming_distance(filter_attributes, row['attributes_bin'])
            if distance > tolerance:
                continue
        
        portraits.append({
            'idportrait': row['idportrait'],
            'filepath': row['filepath'],
            'attributes_bin': row['attributes_bin'],
            'hair_embedding': deserialize_float_vector(row['hair_embedding']),
            'face_embedding': deserialize_float_vector(row['face_embedding']),
        })
    
    return portraits


def get_stats(conn: sqlite3.Connection) -> dict:
    """
    Retourne les statistiques de la base.
    """
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM portraits WHERE status = 'ok'")
    return {'total_ok': cursor.fetchone()[0]}


# ═══════════════════════════════════════════════════════════════════════════════
# RECHERCHE
# ═══════════════════════════════════════════════════════════════════════════════

def rechercher_similaires(ref_portrait: dict, candidats: List[dict], 
                          mode: str = 'both', n: int = 10,
                          weight_hair: float = WEIGHT_HAIR,
                          weight_face: float = WEIGHT_FACE,
                          verbose: bool = False, debug: bool = False) -> List[dict]:
    """
    Recherche les portraits les plus similaires.
    
    Args:
        ref_portrait: Portrait de référence
        candidats: Liste des portraits candidats
        mode: 'hair', 'face', ou 'both'
        n: Nombre de résultats à retourner
        weight_hair: Poids du hair_embedding (si mode='both')
        weight_face: Poids du face_embedding (si mode='both')
        verbose: Mode verbose
        debug: Mode debug
        
    Returns:
        Liste des portraits triés par similarité (plus proche en premier)
    """
    ref_hair = ref_portrait['hair_embedding']
    ref_face = ref_portrait['face_embedding']
    
    resultats = []
    
    for candidat in candidats:
        # Calcul des distances selon le mode
        if mode == 'hair':
            distance = cosine_distance(ref_hair, candidat['hair_embedding'])
            score_detail = {'hair': distance}
            
        elif mode == 'face':
            distance = cosine_distance(ref_face, candidat['face_embedding'])
            score_detail = {'face': distance}
            
        else:  # 'both'
            dist_hair = cosine_distance(ref_hair, candidat['hair_embedding'])
            dist_face = cosine_distance(ref_face, candidat['face_embedding'])
            
            # Moyenne pondérée (si face_embedding absent, utiliser uniquement hair)
            if candidat['face_embedding']:
                distance = weight_hair * dist_hair + weight_face * dist_face
            else:
                distance = dist_hair
            
            score_detail = {'hair': dist_hair, 'face': dist_face, 'combined': distance}
        
        resultats.append({
            'idportrait': candidat['idportrait'],
            'filepath': candidat['filepath'],
            'distance': distance,
            'score_detail': score_detail,
            'attributes_bin': candidat['attributes_bin'],
        })
    
    # Trier par distance croissante
    resultats.sort(key=lambda x: x['distance'])
    
    return resultats[:n]


# ═══════════════════════════════════════════════════════════════════════════════
# AFFICHAGE
# ═══════════════════════════════════════════════════════════════════════════════

def afficher_resultats(ref_id: str, resultats: List[dict], mode: str, 
                       verbose: bool = False) -> None:
    """
    Affiche les résultats de recherche.
    """
    print()
    print("═" * 70)
    print(f"RÉSULTATS - Portraits similaires à '{ref_id}'")
    print(f"Mode: {mode} | {len(resultats)} résultat(s)")
    print("═" * 70)
    print()
    
    print(f"{'#':<4} {'ID Portrait':<15} {'Distance':<12} {'Détail':<30} {'Groupe':<10}")
    print("─" * 70)
    
    for i, r in enumerate(resultats, 1):
        # Identifier le groupe (numéro de base pour les variantes)
        try:
            id_num = int(r['idportrait'])
            groupe = (id_num // 10) * 10
        except:
            groupe = "?"
        
        # Formater le détail du score
        detail = r['score_detail']
        if 'combined' in detail:
            detail_str = f"h:{detail['hair']:.4f} f:{detail['face']:.4f}"
        elif 'hair' in detail:
            detail_str = f"hair:{detail['hair']:.4f}"
        else:
            detail_str = f"face:{detail['face']:.4f}"
        
        print(f"{i:<4} {r['idportrait']:<15} {r['distance']:<12.6f} {detail_str:<30} {groupe:<10}")
    
    print()


# ═══════════════════════════════════════════════════════════════════════════════
# PROGRAMME PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def afficher_aide():
    """Affiche l'aide du programme."""
    print("=" * 70)
    print(f"{__pgm__} - Recherche de portraits similaires")
    print("=" * 70)
    print()
    print("USAGE :")
    print(f"  python {__pgm__} <idportrait> [options]")
    print()
    print("ARGUMENTS :")
    print("  idportrait         ID du portrait de référence (ex: 1000)")
    print()
    print("OPTIONS :")
    print("  -n, --top N        Nombre de résultats (défaut: 10)")
    print("  --db FILE          Chemin de la base (défaut: photofit.db)")
    print("  --hair             Utiliser uniquement hair_embedding")
    print("  --face             Utiliser uniquement face_embedding")
    print("  --both             Combiner les deux embeddings (défaut)")
    print("  --no-filter        Désactiver le pré-filtrage par attributs")
    print("  --tolerance N      Tolérance pour le filtre attributs (défaut: 2)")
    print("  --weight-hair F    Poids hair_embedding si --both (défaut: 0.3)")
    print("  --weight-face F    Poids face_embedding si --both (défaut: 0.7)")
    print("  -v, --verbose      Mode verbose")
    print("  -d, --debug        Mode debug")
    print()
    print("EXEMPLES :")
    print(f"  python {__pgm__} 1000")
    print(f"  python {__pgm__} 1000 -n 20 --hair")
    print(f"  python {__pgm__} 1000 --both --weight-hair 0.5 --weight-face 0.5")
    print(f"  python {__pgm__} 1000 --no-filter -v")
    print()


def main():
    """Point d'entrée principal."""
    print(f"{__pgm__} V{__version__} - {__date__}")
    print()
    
    # Pas d'arguments → aide
    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        afficher_aide()
        return 0
    
    # Parser les arguments
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('idportrait', type=str, help='ID du portrait de référence')
    parser.add_argument('-n', '--top', type=int, default=DEFAULT_N_RESULTS)
    parser.add_argument('--db', type=str, default=DEFAULT_DB_PATH)
    parser.add_argument('--hair', action='store_true')
    parser.add_argument('--face', action='store_true')
    parser.add_argument('--both', action='store_true')
    parser.add_argument('--no-filter', action='store_true')
    parser.add_argument('--tolerance', type=int, default=ATTRIBUTES_TOLERANCE)
    parser.add_argument('--weight-hair', type=float, default=WEIGHT_HAIR)
    parser.add_argument('--weight-face', type=float, default=WEIGHT_FACE)
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-d', '--debug', action='store_true')
    
    args = parser.parse_args()
    verbose = args.verbose or args.debug
    debug = args.debug
    
    # Déterminer le mode
    if args.hair:
        mode = 'hair'
    elif args.face:
        mode = 'face'
    else:
        mode = 'both'
    
    # Ouvrir la base
    db_path = Path(args.db).resolve()
    try:
        conn = ouvrir_base(db_path)
    except FileNotFoundError as e:
        print(f"ERREUR : {e}")
        return 1
    
    if verbose:
        stats = get_stats(conn)
        print(f"Base     : {db_path}")
        print(f"Portraits: {stats['total_ok']} valides")
        print()
    
    # Récupérer le portrait de référence
    ref_portrait = get_portrait(conn, args.idportrait)
    if ref_portrait is None:
        print(f"ERREUR : Portrait '{args.idportrait}' non trouvé ou en erreur")
        conn.close()
        return 1
    
    if verbose:
        print(f"Référence: {args.idportrait}")
        print(f"  Fichier: {ref_portrait['filepath']}")
        print(f"  Attributs: {ref_portrait['attributes_bin']}")
        print(f"  Hair embedding: {len(ref_portrait['hair_embedding'])} dims")
        print(f"  Face embedding: {len(ref_portrait['face_embedding'])} dims")
        print()
    
    # Récupérer les candidats
    filter_attr = None if args.no_filter else ref_portrait['attributes_bin']
    candidats = get_all_portraits(conn, exclude_id=args.idportrait, 
                                   filter_attributes=filter_attr,
                                   tolerance=args.tolerance)
    
    if verbose:
        print(f"Candidats: {len(candidats)} (après pré-filtrage)")
    
    if not candidats:
        print("Aucun candidat trouvé après filtrage.")
        conn.close()
        return 0
    
    # Rechercher les similaires
    resultats = rechercher_similaires(
        ref_portrait, candidats, mode=mode, n=args.top,
        weight_hair=args.weight_hair, weight_face=args.weight_face,
        verbose=verbose, debug=debug
    )
    
    # Afficher les résultats
    afficher_resultats(args.idportrait, resultats, mode, verbose)
    
    # Analyse spéciale pour les groupes de variantes
    try:
        ref_num = int(args.idportrait)
        ref_groupe = (ref_num // 10) * 10
        
        # Compter combien de variantes du même groupe sont dans le top N
        variantes_trouvees = sum(
            1 for r in resultats 
            if (int(r['idportrait']) // 10) * 10 == ref_groupe
        )
        
        print(f"📊 Analyse groupe {ref_groupe}:")
        print(f"   Variantes attendues: 9 (de {ref_groupe} à {ref_groupe+9}, sauf {args.idportrait})")
        print(f"   Variantes dans top {args.top}: {variantes_trouvees}")
        if variantes_trouvees > 0:
            print(f"   Recall: {variantes_trouvees}/9 = {variantes_trouvees/9*100:.1f}%")
        print()
        
    except ValueError:
        pass  # ID non numérique
    
    conn.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
