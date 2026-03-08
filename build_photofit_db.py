#*TO*#
__pgm__ = "build_photofit_db.py"
__version__ = "0.0.0"
__date__ = "01/01/1970 00:00"

"""
Construction de la base vectorielle des portraits pour la recherche par similarité.

Ce programme :
1. Parcourt les images d'un répertoire donné en paramètre
2. Appelle l'API Photofit de Maxime pour extraire les features
3. Stocke les résultats dans une base SQLite avec sqlite-vec

PAR DÉFAUT : ajoute des lignes dans la base existante (pas de création).
Utiliser --create pour créer/réinitialiser la base.

USAGE :
    python build_photofit_db.py                     # Affiche l'aide
    python build_photofit_db.py <répertoire>        # Ajoute les portraits à la base
    python build_photofit_db.py <répertoire> -v     # Mode verbose
    python build_photofit_db.py <répertoire> -d     # Mode debug
    python build_photofit_db.py <répertoire> --create    # Crée la base avant traitement
    python build_photofit_db.py <répertoire> --resume    # Reprend où on s'est arrêté
    python build_photofit_db.py <répertoire> --dry-run   # Simule sans appeler l'API

API PHOTOFIT :
    URL: https://demo.ia.orqual.info:506/photofit/api/v1/extract-features
    Méthode: POST multipart/form-data
    Paramètre: img (fichier image)
    Réponse: {attributes: [...], hair_embedding: [...], face_embedding: [...]}

STRUCTURE DB :
    photofit.db (dans C:\\cx\\bases par défaut)
    ├── portraits (idportrait, filepath, attributes_json, attributes_bin,
    │              hair_embedding, face_embedding, status, error_message, created_at)
    └── metadata (key, value) - pour stocker les infos de version/config
"""

import argparse
import json
import os
import sqlite3
import struct
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import requests
from tqdm import tqdm

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

API_URL = "https://demo.ia.orqual.info:506/photofit/api/v1/extract-features"
API_TIMEOUT = 60  # secondes

DEFAULT_DB_DIR = Path(r"C:\cx\bases")
DEFAULT_DB_NAME = "photofit.db"

EXTENSIONS_IMAGES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# Dimensions des embeddings (à vérifier avec l'API)
HAIR_EMBEDDING_SIZE = 384
FACE_EMBEDDING_SIZE = 128

# Noms des attributs (ordre de l'API)
ATTRIBUTES_NAMES = [
    "eyeglasses", "male", "young", "length_bald", "length_short",
    "length_mid", "length_long", "bangs", "black_hair", "blond_hair",
    "brown_hair", "gray_hair", "receding_hairline", "straight_hair",
    "wavy_hair", "attr_15", "attr_16", "attr_17"  # Au cas où il y en a plus
]


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

def serialize_float_vector(vector: list) -> bytes:
    """
    Sérialise un vecteur de floats en bytes pour sqlite-vec.
    Format: little-endian float32
    """
    return struct.pack(f'<{len(vector)}f', *vector)


def deserialize_float_vector(data: bytes) -> list:
    """
    Désérialise des bytes en vecteur de floats.
    """
    count = len(data) // 4
    return list(struct.unpack(f'<{count}f', data))


def binarize_attributes(attributes: list, threshold: float = 0.5) -> str:
    """
    Binarise les attributs avec un seuil.
    Retourne une chaîne de 0 et 1 séparés par des virgules.
    """
    return ",".join("1" if v >= threshold else "0" for v in attributes)


def lister_images(repertoire: Path) -> list:
    """
    Liste toutes les images du répertoire (non récursif).
    Retourne une liste de tuples (idportrait, filepath_complète).
    idportrait = stem du fichier (ex: "10000")
    """
    images = []
    for f in sorted(repertoire.iterdir()):
        if f.is_file() and f.suffix.lower() in EXTENSIONS_IMAGES:
            idportrait = f.stem
            images.append((idportrait, f))
    return images


# ═══════════════════════════════════════════════════════════════════════════════
# API PHOTOFIT
# ═══════════════════════════════════════════════════════════════════════════════

def appeler_api_photofit(filepath: Path, verbose: bool = False, debug: bool = False) -> Tuple[Optional[dict], Optional[str]]:
    """
    Appelle l'API Photofit pour extraire les features d'une image.

    Args:
        filepath: Chemin vers l'image
        verbose: Mode verbose
        debug: Mode debug

    Returns:
        Tuple (données, erreur)
        - Si succès: (dict avec attributes/hair_embedding/face_embedding, None)
        - Si erreur: (None, message d'erreur)
    """
    try:
        with open(filepath, 'rb') as f:
            files = {'img': (filepath.name, f, f'image/{filepath.suffix[1:]}')}
            headers = {'accept': 'application/json'}

            if debug:
                print(f"[DEBUG] POST {API_URL}")
                print(f"[DEBUG] Fichier: {filepath.name} ({filepath.stat().st_size} bytes)")

            response = requests.post(
                API_URL,
                files=files,
                headers=headers,
                timeout=API_TIMEOUT,
                verify=False  # SSL non vérifié pour le serveur de démo
            )

            if debug:
                print(f"[DEBUG] Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()

                # Vérifier la présence des clés attendues
                if 'attributes' not in data:
                    return None, "Réponse API sans 'attributes'"
                if 'hair_embedding' not in data:
                    return None, "Réponse API sans 'hair_embedding'"

                if debug:
                    print(f"[DEBUG] attributes: {len(data['attributes'])} valeurs")
                    print(f"[DEBUG] hair_embedding: {len(data['hair_embedding'])} valeurs")
                    if 'face_embedding' in data:
                        print(f"[DEBUG] face_embedding: {len(data['face_embedding'])} valeurs")

                return data, None
            else:
                return None, f"HTTP {response.status_code}: {response.text[:200]}"

    except requests.exceptions.Timeout:
        return None, f"Timeout après {API_TIMEOUT}s"
    except requests.exceptions.ConnectionError as e:
        return None, f"Erreur connexion: {str(e)[:100]}"
    except Exception as e:
        return None, f"Erreur: {str(e)[:100]}"


# ═══════════════════════════════════════════════════════════════════════════════
# BASE DE DONNÉES
# ═══════════════════════════════════════════════════════════════════════════════

def creer_base(db_path: Path, verbose: bool = False) -> sqlite3.Connection:
    """
    Crée la base de données avec les tables nécessaires.
    Utilisé uniquement avec --create.
    """
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Table des portraits
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portraits (
            idportrait TEXT PRIMARY KEY,
            filepath TEXT NOT NULL,
            attributes_json TEXT,
            attributes_bin TEXT,
            hair_embedding BLOB,
            face_embedding BLOB,
            status TEXT DEFAULT 'pending',
            error_message TEXT,
            created_at TEXT,
            updated_at TEXT
        )
    """)

    # Table de métadonnées
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # Index pour les recherches
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_portraits_status ON portraits(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_portraits_attributes_bin ON portraits(attributes_bin)")

    # Métadonnées
    cursor.execute("""
        INSERT OR REPLACE INTO metadata (key, value) VALUES
        ('version', '5.2'),
        ('created_at', ?),
        ('hair_embedding_size', ?),
        ('face_embedding_size', ?)
    """, (datetime.now().isoformat(), str(HAIR_EMBEDDING_SIZE), str(FACE_EMBEDDING_SIZE)))

    conn.commit()

    if verbose:
        print(f"  ✓ Base créée/ouverte: {db_path}")

    return conn


def ouvrir_base(db_path: Path, verbose: bool = False) -> sqlite3.Connection:
    """
    Ouvre une base existante pour y ajouter des lignes.
    Vérifie que la table portraits existe.
    """
    if not db_path.is_file():
        print(f"ERREUR : Base introuvable : {db_path}")
        print(f"  Utilisez --create pour créer une nouvelle base.")
        sys.exit(1)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Vérifier que la table portraits existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='portraits'")
    if cursor.fetchone() is None:
        print(f"ERREUR : La table 'portraits' n'existe pas dans {db_path}")
        print(f"  Utilisez --create pour créer la structure.")
        conn.close()
        sys.exit(1)

    if verbose:
        print(f"  ✓ Base ouverte (ajout) : {db_path}")

    return conn


def portrait_existe(conn: sqlite3.Connection, idportrait: str) -> bool:
    """
    Vérifie si un portrait existe déjà avec status='ok'.
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM portraits WHERE idportrait = ? AND status = 'ok'",
        (idportrait,)
    )
    return cursor.fetchone() is not None


def sauver_portrait(conn: sqlite3.Connection, idportrait: str, filepath: Path,
                    data: Optional[dict], error: Optional[str]) -> None:
    """
    Sauvegarde les données d'un portrait dans la base.
    """
    cursor = conn.cursor()
    now = datetime.now().isoformat()

    if data is not None:
        # Succès
        attributes_json = json.dumps(data['attributes'])
        attributes_bin = binarize_attributes(data['attributes'])
        hair_embedding = serialize_float_vector(data['hair_embedding'])
        face_embedding = None
        if 'face_embedding' in data:
            face_embedding = serialize_float_vector(data['face_embedding'])

        cursor.execute("""
            INSERT OR REPLACE INTO portraits
            (idportrait, filepath, attributes_json, attributes_bin,
             hair_embedding, face_embedding, status, error_message, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 'ok', NULL,
                    COALESCE((SELECT created_at FROM portraits WHERE idportrait = ?), ?), ?)
        """, (idportrait, str(filepath), attributes_json, attributes_bin,
              hair_embedding, face_embedding, idportrait, now, now))
    else:
        # Erreur
        cursor.execute("""
            INSERT OR REPLACE INTO portraits
            (idportrait, filepath, attributes_json, attributes_bin,
             hair_embedding, face_embedding, status, error_message, created_at, updated_at)
            VALUES (?, ?, NULL, NULL, NULL, NULL, 'error', ?,
                    COALESCE((SELECT created_at FROM portraits WHERE idportrait = ?), ?), ?)
        """, (idportrait, str(filepath), error, idportrait, now, now))

    conn.commit()


def get_stats(conn: sqlite3.Connection) -> dict:
    """
    Retourne les statistiques de la base.
    """
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM portraits")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM portraits WHERE status = 'ok'")
    ok = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM portraits WHERE status = 'error'")
    errors = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM portraits WHERE status = 'pending'")
    pending = cursor.fetchone()[0]

    return {'total': total, 'ok': ok, 'errors': errors, 'pending': pending}


# ═══════════════════════════════════════════════════════════════════════════════
# PROGRAMME PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════════

def afficher_aide():
    """Affiche l'aide du programme."""
    db_default = DEFAULT_DB_DIR / DEFAULT_DB_NAME
    print("=" * 70)
    print(f"{__pgm__} - Construction de la base vectorielle Photofit")
    print("=" * 70)
    print()
    print("USAGE :")
    print(f"  python {__pgm__} <répertoire_images> [options]")
    print()
    print("ARGUMENTS :")
    print("  répertoire_images  Répertoire contenant les images à traiter")
    print()
    print("OPTIONS :")
    print(f"  -o, --output FILE  Chemin de la base (défaut: {db_default})")
    print("  -v                 Mode verbose")
    print("  -d                 Mode debug (très verbeux)")
    print("  --create           Crée la base avant traitement (défaut: ajout)")
    print("  --resume           Reprend le traitement (skip les portraits déjà OK)")
    print("  --dry-run          Simule sans appeler l'API")
    print("  --limit N          Traite seulement N images")
    print("  --retry-errors     Réessaie les portraits en erreur")
    print()
    print("COMPORTEMENT PAR DÉFAUT :")
    print("  Ouvre la base existante et AJOUTE des lignes dans la table portraits.")
    print("  Utiliser --create pour créer/réinitialiser la base.")
    print()
    print("EXEMPLES :")
    print(f"  python {__pgm__} C:\\PortraitsPhotofit\\1964N")
    print(f"  python {__pgm__} C:\\PortraitsPhotofit\\1964N -v --resume")
    print(f"  python {__pgm__} C:\\PortraitsPhotofit\\1964N --create --limit 10 -d")
    print(f"  python {__pgm__} C:\\PortraitsPhotofit\\1964N -o D:\\autre\\photofit.db")
    print()
    print("API PHOTOFIT :")
    print(f"  URL: {API_URL}")
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
    parser.add_argument('source', type=str, help='Répertoire source des images')
    parser.add_argument('-o', '--output', type=str, default=None)
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('--create', action='store_true',
                        help='Crée la base (défaut: ajout dans base existante)')
    parser.add_argument('--resume', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--limit', type=int, default=None)
    parser.add_argument('--retry-errors', action='store_true')

    args = parser.parse_args()
    verbose = args.verbose or args.debug
    debug = args.debug

    # Désactiver les warnings SSL pour le serveur de démo
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Vérifier le répertoire source
    source_dir = Path(args.source).resolve()
    if not source_dir.is_dir():
        print(f"ERREUR : Le répertoire '{source_dir}' n'existe pas.")
        return 1

    # Déterminer le chemin de la base
    if args.output:
        db_path = Path(args.output).resolve()
    else:
        db_path = (DEFAULT_DB_DIR / DEFAULT_DB_NAME).resolve()

    mode = "CRÉATION" if args.create else "AJOUT"
    print(f"Source  : {source_dir}")
    print(f"Base    : {db_path}")
    print(f"Mode    : {mode}")
    print(f"Options : resume={args.resume}, dry-run={args.dry_run}, limit={args.limit}")
    print()

    # Lister les images
    images = lister_images(source_dir)
    nb_images = len(images)

    if nb_images == 0:
        print(f"ERREUR : Aucune image trouvée dans '{source_dir}'")
        print(f"  Extensions acceptées : {', '.join(sorted(EXTENSIONS_IMAGES))}")
        return 1

    print(f"Images trouvées : {nb_images}")

    # Limiter si demandé
    if args.limit:
        images = images[:args.limit]
        print(f"  → Limité à {len(images)} images")

    # Créer ou ouvrir la base
    if args.create:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = creer_base(db_path, verbose)
    else:
        conn = ouvrir_base(db_path, verbose)

    # Stats initiales
    stats_init = get_stats(conn)
    print(f"Base initiale : {stats_init['ok']} OK, {stats_init['errors']} erreurs, {stats_init['pending']} en attente")
    print()

    if args.dry_run:
        print("─" * 70)
        print("MODE DRY-RUN : Aucun appel API ne sera effectué")
        print("─" * 70)
        print()

    # Traitement
    nb_traites = 0
    nb_ok = 0
    nb_erreurs = 0
    nb_skipped = 0

    start_time = time.time()

    for idportrait, filepath in tqdm(images, desc="Traitement", unit="img"):
        # Skip si déjà traité et mode resume
        if args.resume and portrait_existe(conn, idportrait):
            nb_skipped += 1
            if debug:
                print(f"[DEBUG] Skip {idportrait} (déjà OK)")
            continue

        # Dry-run : on simule
        if args.dry_run:
            if verbose:
                print(f"  [DRY-RUN] {idportrait} → simulation OK")
            nb_traites += 1
            nb_ok += 1
            continue

        # Appel API
        if verbose:
            print(f"  Traitement: {idportrait} ({filepath.name})")

        data, error = appeler_api_photofit(filepath, verbose, debug)

        if error:
            if verbose:
                print(f"    ✗ ERREUR: {error}")
            nb_erreurs += 1
        else:
            if verbose:
                attr_bin = binarize_attributes(data['attributes'])
                print(f"    ✓ OK - attributes={len(data['attributes'])}, hair={len(data['hair_embedding'])}")
            nb_ok += 1

        # Sauvegarder
        sauver_portrait(conn, idportrait, filepath, data, error)
        nb_traites += 1

        # Petite pause pour ne pas surcharger l'API
        time.sleep(0.1)

    elapsed = time.time() - start_time

    # Stats finales
    stats_final = get_stats(conn)

    # Résumé
    print()
    print("=" * 70)
    print("RÉSUMÉ")
    print("=" * 70)
    print(f"  Répertoire source : {source_dir}")
    print(f"  Images trouvées   : {nb_images}")
    print(f"  Images traitées   : {nb_traites}")
    print(f"  Succès            : {nb_ok}")
    print(f"  Erreurs           : {nb_erreurs}")
    print(f"  Ignorées (skip)   : {nb_skipped}")
    print(f"  Temps total       : {elapsed:.1f}s ({elapsed/max(nb_traites,1):.2f}s/image)")
    print()
    print(f"Base finale : {stats_final['ok']} OK, {stats_final['errors']} erreurs, {stats_final['total']} total")
    print(f"Fichier     : {db_path}")
    print()

    conn.close()
    return 0


if __name__ == '__main__':
    sys.exit(main())
