#*TO*#
__pgm__ = "photofit_upload.py"
__version__ = "0.0.0"
__date__ = "01/01/1970 00:00"

"""
Module de recherche par image uploadée et gestion des prospects.

Ce module permet de :
1. Envoyer une image à l'API Photofit pour extraire les embeddings
2. Rechercher les portraits similaires dans photofit.db ET prospects.db
3. Gérer la base prospects.db (création, sauvegarde, listage)

ARCHITECTURE :
    Image uploadée
      │
      ▼
    extraire_features() → API Photofit → embeddings (hair_384 + face_128)
      │
      ▼
    rechercher_par_image() → cosine distance pondérée vs photofit.db + prospects.db
      │
      ▼
    Résultats triés par score (0-100), filtrés par score_min

PROSPECTS :
    prospects.db (dans bases/) - Base séparée pour les prospects
    bases/prospects/ - Photos des prospects

USAGE CLI :
    python photofit_upload.py                          # Affiche l'aide
    python photofit_upload.py search <image>           # Recherche similaires
    python photofit_upload.py search <image> -v        # Mode verbose
    python photofit_upload.py search <image> -d        # Mode debug
    python photofit_upload.py list                     # Liste les prospects
    python photofit_upload.py list -v                  # Liste détaillée
    python photofit_upload.py stats                    # Stats photofit.db + prospects.db

USAGE EN IMPORT :
    from photofit_upload import (
        extraire_features,
        rechercher_par_image,
        sauver_prospect,
        lister_prospects,
        supprimer_prospect,
        get_prospect_by_id,
        creer_base_prospects
    )

CONFIG :
    Lit les paramètres depuis communb.csv (section 'bases') :
    - photofit_max_results, photofit_weight_hair, photofit_weight_face
    - photofit_distance_max, photofit_score_min
"""

import argparse
import csv
import io
import json
import math
import os
import shutil
import sqlite3
import struct
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import requests


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

API_URL = "https://demo.ia.orqual.info:506/photofit/api/v1/extract-features"
API_TIMEOUT = 60  # secondes

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_PHOTOFIT_DB = SCRIPT_DIR / "bases" / "photofit.db"
DEFAULT_PROSPECTS_DB = SCRIPT_DIR / "bases" / "prospects.db"
DEFAULT_PROSPECTS_PHOTOS = SCRIPT_DIR / "bases" / "prospects"

EXTENSIONS_IMAGES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

# Valeurs par défaut (overridées par communb.csv)
DEFAULT_CONFIG = {
    'photofit_db': 'bases/photofit.db',
    'max_results': 20,
    'weight_hair': 0.3,
    'weight_face': 0.7,
    'distance_max': 0.5,
    'score_min': 30,
    'seuil': 1000,
}


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION COMMUNB.CSV
# ═══════════════════════════════════════════════════════════════════════════════

_config_cache = None


def lire_config(debug: bool = False) -> dict:
    """
    Lit les paramètres Photofit depuis communb.csv (section 'bases').
    Cache le résultat pour ne lire qu'une seule fois.
    """
    global _config_cache
    if _config_cache is not None:
        return _config_cache

    config = dict(DEFAULT_CONFIG)

    candidates = [
        SCRIPT_DIR / 'refs' / 'communb.csv',
        SCRIPT_DIR / 'communb.csv',
    ]

    communb_path = None
    for candidate in candidates:
        if candidate.exists():
            communb_path = candidate
            break

    if communb_path is None:
        if debug:
            print(f"[DEBUG] photofit_upload: communb.csv introuvable, valeurs par défaut")
        _config_cache = config
        return config

    if debug:
        print(f"[DEBUG] photofit_upload: Lecture config depuis {communb_path}")

    try:
        with open(communb_path, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(
                (row for row in f if not row.startswith('#')),
                delimiter=';'
            )
            for row in reader:
                section = row.get('section', '').strip()
                parametre = row.get('parametre', '').strip()
                valeur = row.get('valeur', '').strip()

                if section != 'bases':
                    continue

                if parametre == 'photofit':
                    config['photofit_db'] = valeur
                elif parametre == 'photofit_max_results':
                    config['max_results'] = int(valeur)
                elif parametre == 'photofit_weight_hair':
                    config['weight_hair'] = float(valeur)
                elif parametre == 'photofit_weight_face':
                    config['weight_face'] = float(valeur)
                elif parametre == 'photofit_seuil':
                    config['seuil'] = int(valeur)
                elif parametre == 'photofit_distance_max':
                    config['distance_max'] = float(valeur)
                elif parametre == 'photofit_score_min':
                    config['score_min'] = int(valeur)
    except Exception as e:
        if debug:
            print(f"[DEBUG] photofit_upload: Erreur lecture communb.csv : {e}")

    if debug:
        print(f"[DEBUG] photofit_upload: Config = {config}")

    _config_cache = config
    return config


# ═══════════════════════════════════════════════════════════════════════════════
# FONCTIONS UTILITAIRES
# ═══════════════════════════════════════════════════════════════════════════════

def _deserialize_float_vector(data: bytes) -> List[float]:
    """Désérialise des bytes en vecteur de floats."""
    if data is None:
        return []
    count = len(data) // 4
    return list(struct.unpack(f'<{count}f', data))


def _serialize_float_vector(vector: list) -> bytes:
    """Sérialise un vecteur de floats en bytes (little-endian float32)."""
    return struct.pack(f'<{len(vector)}f', *vector)


def _cosine_distance(vec1: List[float], vec2: List[float]) -> float:
    """Distance cosinus entre deux vecteurs (0 = identiques, 2 = opposés)."""
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


def _distance_to_score(distance: float, distance_max: float) -> int:
    """
    Convertit une distance cosinus pondérée en score de ressemblance 0-100.
    """
    if distance_max <= 0:
        return 0
    score = 100.0 * (1.0 - distance / distance_max)
    return max(0, min(100, round(score)))


def _binarize_attributes(attributes: list, threshold: float = 0.5) -> str:
    """Binarise les attributs avec un seuil."""
    return ",".join("1" if v >= threshold else "0" for v in attributes)


# ═══════════════════════════════════════════════════════════════════════════════
# API PHOTOFIT - EXTRACTION DES FEATURES
# ═══════════════════════════════════════════════════════════════════════════════

def extraire_features(
    image_bytes: bytes,
    filename: str,
    verbose: bool = False,
    debug: bool = False
) -> Tuple[Optional[dict], Optional[str]]:
    """
    Appelle l'API Photofit pour extraire les features d'une image.

    Args:
        image_bytes: Contenu binaire de l'image
        filename: Nom du fichier (pour le Content-Type)
        verbose: Mode verbose
        debug: Mode debug

    Returns:
        Tuple (données, erreur)
        - Si succès: (dict avec attributes/hair_embedding/face_embedding, None)
        - Si erreur: (None, message d'erreur)
    """
    # Désactiver les warnings SSL
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # Déterminer le content-type
    ext = Path(filename).suffix.lower().lstrip('.')
    if ext == 'jpg':
        ext = 'jpeg'
    content_type = f'image/{ext}'

    try:
        files = {'img': (filename, image_bytes, content_type)}
        headers = {'accept': 'application/json'}

        if debug:
            print(f"[DEBUG] photofit_upload: POST {API_URL}")
            print(f"[DEBUG] photofit_upload: Fichier: {filename} ({len(image_bytes)} bytes, {content_type})")

        start = time.time()
        response = requests.post(
            API_URL,
            files=files,
            headers=headers,
            timeout=API_TIMEOUT,
            verify=False
        )
        elapsed = time.time() - start

        if debug:
            print(f"[DEBUG] photofit_upload: Status: {response.status_code} ({elapsed:.2f}s)")

        if response.status_code == 200:
            data = response.json()

            if 'attributes' not in data:
                return None, "Réponse API sans 'attributes'"
            if 'hair_embedding' not in data:
                return None, "Réponse API sans 'hair_embedding'"

            if verbose:
                print(f"  ✓ Features extraites en {elapsed:.2f}s")
                print(f"    attributes: {len(data['attributes'])} valeurs")
                print(f"    hair_embedding: {len(data['hair_embedding'])} dims")
                if 'face_embedding' in data:
                    print(f"    face_embedding: {len(data['face_embedding'])} dims")

            return data, None
        else:
            return None, f"HTTP {response.status_code}: {response.text[:200]}"

    except requests.exceptions.Timeout:
        return None, f"Timeout après {API_TIMEOUT}s"
    except requests.exceptions.ConnectionError as e:
        return None, f"Erreur connexion API Photofit: {str(e)[:100]}"
    except Exception as e:
        return None, f"Erreur: {str(e)[:100]}"


# ═══════════════════════════════════════════════════════════════════════════════
# RECHERCHE PAR IMAGE
# ═══════════════════════════════════════════════════════════════════════════════

def _rechercher_dans_base(
    db_path: Path,
    ref_hair: List[float],
    ref_face: List[float],
    config: dict,
    source: str = "photofit",
    debug: bool = False
) -> List[dict]:
    """
    Recherche les portraits similaires dans une base donnée.

    Args:
        db_path: Chemin vers la base SQLite
        ref_hair: hair_embedding de référence
        ref_face: face_embedding de référence
        config: Configuration (weight_hair, weight_face, distance_max)
        source: 'photofit' ou 'prospect' (pour le tag dans les résultats)
        debug: Mode debug

    Returns:
        Liste de dicts triés par distance croissante
    """
    if not db_path.exists():
        if debug:
            print(f"[DEBUG] photofit_upload: Base introuvable : {db_path}")
        return []

    weight_hair = config['weight_hair']
    weight_face = config['weight_face']
    distance_max = config['distance_max']

    # Déterminer la requête SQL selon la base (photofit vs prospects)
    if source == "prospect":
        sql = """
            SELECT id, prenom, nom, sexe, age, tags, photo_filename,
                   hair_embedding, face_embedding
            FROM prospects
        """
    else:
        sql = """
            SELECT idportrait, hair_embedding, face_embedding
            FROM portraits
            WHERE status = 'ok'
        """

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql)

        resultats = []
        for row in cursor.fetchall():
            cand_hair = _deserialize_float_vector(row['hair_embedding'])
            cand_face = _deserialize_float_vector(row['face_embedding'])

            dist_hair = _cosine_distance(ref_hair, cand_hair)
            dist_face = _cosine_distance(ref_face, cand_face)

            if cand_face:
                distance = weight_hair * dist_hair + weight_face * dist_face
            else:
                distance = dist_hair

            score = _distance_to_score(distance, distance_max)

            if source == "prospect":
                resultats.append({
                    'idportrait': f"prospect_{row['id']}",
                    'source': 'prospect',
                    'prospect_id': row['id'],
                    'prenom': row['prenom'],
                    'nom': row['nom'],
                    'sexe': row['sexe'] or '',
                    'age': row['age'],
                    'tags': row['tags'] or '',
                    'photo_filename': row['photo_filename'],
                    'distance': distance,
                    'score': score,
                })
            else:
                resultats.append({
                    'idportrait': str(row['idportrait']),
                    'source': 'photofit',
                    'distance': distance,
                    'score': score,
                })

        conn.close()

        if debug:
            print(f"[DEBUG] photofit_upload: {len(resultats)} candidats dans {source} ({db_path.name})")

        return resultats

    except Exception as e:
        if debug:
            print(f"[DEBUG] photofit_upload: Erreur recherche {source} : {e}")
        return []


def rechercher_par_image(
    hair_embedding: List[float],
    face_embedding: List[float],
    config: Optional[dict] = None,
    photofit_db: Optional[Path] = None,
    prospects_db: Optional[Path] = None,
    verbose: bool = False,
    debug: bool = False
) -> List[dict]:
    """
    Recherche les portraits similaires dans photofit.db ET prospects.db.

    Fusionne les résultats, trie par score décroissant, filtre par score_min,
    limite à max_results.

    Args:
        hair_embedding: Vecteur hair (384 dims) de l'image uploadée
        face_embedding: Vecteur face (128 dims) de l'image uploadée
        config: Configuration (depuis communb.csv). Si None, lecture auto.
        photofit_db: Chemin photofit.db (override). Si None, depuis config.
        prospects_db: Chemin prospects.db (override). Si None, défaut.
        verbose: Mode verbose
        debug: Mode debug

    Returns:
        Liste de dicts triés par score décroissant, filtrés par score_min.
        Chaque dict contient: idportrait, source, score, distance, [prospect_info...]
    """
    if config is None:
        config = lire_config(debug=debug)

    # Résoudre les chemins
    if photofit_db is None:
        photofit_db = (SCRIPT_DIR / config['photofit_db']).resolve()
    if prospects_db is None:
        prospects_db = DEFAULT_PROSPECTS_DB

    max_results = config['max_results']
    score_min = config['score_min']

    if verbose:
        print(f"  Recherche dans photofit.db : {photofit_db}")
        print(f"  Recherche dans prospects.db : {prospects_db}")
        print(f"  Poids : hair={config['weight_hair']}, face={config['weight_face']}")
        print(f"  Score min : {score_min}, Max résultats : {max_results}")

    # Rechercher dans les deux bases
    resultats_photofit = _rechercher_dans_base(
        photofit_db, hair_embedding, face_embedding, config,
        source="photofit", debug=debug
    )

    resultats_prospects = _rechercher_dans_base(
        prospects_db, hair_embedding, face_embedding, config,
        source="prospect", debug=debug
    )

    # Fusionner
    tous_resultats = resultats_photofit + resultats_prospects

    # Filtrer par score_min
    tous_resultats = [r for r in tous_resultats if r['score'] >= score_min]

    # Trier par score décroissant
    tous_resultats.sort(key=lambda x: -x['score'])

    # Limiter
    tous_resultats = tous_resultats[:max_results]

    if verbose:
        nb_photofit = sum(1 for r in tous_resultats if r['source'] == 'photofit')
        nb_prospects = sum(1 for r in tous_resultats if r['source'] == 'prospect')
        print(f"  Résultats : {len(tous_resultats)} total "
              f"({nb_photofit} patients, {nb_prospects} prospects)")

    return tous_resultats


# ═══════════════════════════════════════════════════════════════════════════════
# BASE PROSPECTS
# ═══════════════════════════════════════════════════════════════════════════════

def creer_base_prospects(db_path: Optional[Path] = None, verbose: bool = False) -> Path:
    """
    Crée la base prospects.db si elle n'existe pas.
    Crée aussi le répertoire bases/prospects/ pour les photos.

    Returns:
        Chemin de la base créée
    """
    if db_path is None:
        db_path = DEFAULT_PROSPECTS_DB

    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Créer le répertoire photos
    photos_dir = DEFAULT_PROSPECTS_PHOTOS
    photos_dir.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prospects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            prenom TEXT NOT NULL,
            nom TEXT NOT NULL,
            sexe TEXT DEFAULT '',
            age REAL,
            tags TEXT DEFAULT 'prospect',
            photo_filename TEXT NOT NULL,
            hair_embedding BLOB,
            face_embedding BLOB,
            attributes_json TEXT,
            attributes_bin TEXT,
            created_at TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    cursor.execute("""
        INSERT OR REPLACE INTO metadata (key, value) VALUES
        ('version', '1.0'),
        ('created_at', ?)
    """, (datetime.now().isoformat(),))

    conn.commit()
    conn.close()

    if verbose:
        print(f"  ✓ Base prospects : {db_path}")
        print(f"  ✓ Photos prospects : {photos_dir}")

    return db_path


def sauver_prospect(
    prenom: str,
    nom: str,
    photo_bytes: bytes,
    photo_filename: str,
    features: dict,
    sexe: str = "",
    age: Optional[float] = None,
    tags: str = "prospect",
    db_path: Optional[Path] = None,
    photos_dir: Optional[Path] = None,
    verbose: bool = False,
    debug: bool = False
) -> dict:
    """
    Sauvegarde un prospect dans prospects.db et sa photo dans bases/prospects/.

    Args:
        prenom: Prénom du prospect
        nom: Nom du prospect
        photo_bytes: Contenu binaire de la photo
        photo_filename: Nom original du fichier
        features: Réponse de l'API Photofit (attributes, hair_embedding, face_embedding)
        sexe: Sexe (M/F, optionnel)
        age: Âge (optionnel)
        tags: Tags séparés par virgules (défaut: 'prospect')
        db_path: Chemin prospects.db (défaut: bases/prospects.db)
        photos_dir: Répertoire photos (défaut: bases/prospects/)
        verbose: Mode verbose
        debug: Mode debug

    Returns:
        dict avec id, prenom, nom, photo_filename, photo_url
    """
    if db_path is None:
        db_path = DEFAULT_PROSPECTS_DB
    if photos_dir is None:
        photos_dir = DEFAULT_PROSPECTS_PHOTOS

    # S'assurer que la base existe
    creer_base_prospects(db_path, verbose=False)

    # Générer un nom de fichier unique pour la photo
    ext = Path(photo_filename).suffix.lower()
    if ext not in EXTENSIONS_IMAGES:
        ext = '.jpg'
    unique_filename = f"{uuid.uuid4().hex[:12]}{ext}"

    # Sauvegarder la photo
    photo_path = photos_dir / unique_filename
    photo_path.write_bytes(photo_bytes)

    if verbose:
        print(f"  ✓ Photo sauvegardée : {photo_path}")

    # Préparer les embeddings
    hair_embedding = _serialize_float_vector(features['hair_embedding'])
    face_embedding = None
    if 'face_embedding' in features:
        face_embedding = _serialize_float_vector(features['face_embedding'])

    attributes_json = json.dumps(features.get('attributes', []))
    attributes_bin = _binarize_attributes(features.get('attributes', []))

    now = datetime.now().isoformat()

    # Insérer dans la base
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO prospects
        (prenom, nom, sexe, age, tags, photo_filename,
         hair_embedding, face_embedding, attributes_json, attributes_bin, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (prenom, nom, sexe, age, tags, unique_filename,
          hair_embedding, face_embedding, attributes_json, attributes_bin, now))

    prospect_id = cursor.lastrowid
    conn.commit()
    conn.close()

    if verbose:
        print(f"  ✓ Prospect #{prospect_id} sauvegardé : {prenom} {nom}")

    return {
        'id': prospect_id,
        'prenom': prenom,
        'nom': nom,
        'sexe': sexe,
        'age': age,
        'tags': tags,
        'photo_filename': unique_filename,
        'photo_url': f"/photofit/prospects/photos/{unique_filename}",
    }


def lister_prospects(
    db_path: Optional[Path] = None,
    verbose: bool = False
) -> List[dict]:
    """
    Liste tous les prospects enregistrés.
    """
    if db_path is None:
        db_path = DEFAULT_PROSPECTS_DB

    if not db_path.exists():
        return []

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, prenom, nom, sexe, age, tags, photo_filename, created_at
        FROM prospects
        ORDER BY created_at DESC
    """)

    prospects = []
    for row in cursor.fetchall():
        prospect = dict(row)
        prospect['photo_url'] = f"/photofit/prospects/photos/{row['photo_filename']}"
        prospects.append(prospect)

    conn.close()

    if verbose:
        print(f"  {len(prospects)} prospect(s) dans {db_path}")

    return prospects


def supprimer_prospect(
    prospect_id: int,
    db_path: Optional[Path] = None,
    photos_dir: Optional[Path] = None,
    verbose: bool = False,
    debug: bool = False
) -> dict:
    """
    Supprime un prospect par son ID (base + photo).

    Args:
        prospect_id: ID du prospect à supprimer
        db_path: Chemin prospects.db (défaut: bases/prospects.db)
        photos_dir: Répertoire photos (défaut: bases/prospects/)
        verbose: Mode verbose
        debug: Mode debug

    Returns:
        dict avec success, id, photo_deleted
    """
    if db_path is None:
        db_path = DEFAULT_PROSPECTS_DB
    if photos_dir is None:
        photos_dir = DEFAULT_PROSPECTS_PHOTOS

    if not db_path.exists():
        return {'success': False, 'error': 'Base prospects inexistante'}

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Récupérer le nom du fichier photo avant suppression
    cursor.execute("SELECT photo_filename FROM prospects WHERE id = ?", (prospect_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {'success': False, 'error': f'Prospect #{prospect_id} introuvable'}

    photo_filename = row[0]

    # Supprimer de la base
    cursor.execute("DELETE FROM prospects WHERE id = ?", (prospect_id,))
    conn.commit()
    conn.close()

    # Supprimer la photo sur disque
    photo_deleted = False
    if photo_filename:
        photo_path = photos_dir / photo_filename
        if photo_path.exists():
            photo_path.unlink()
            photo_deleted = True
            if verbose:
                print(f"  ✓ Photo supprimée : {photo_path}")

    if verbose:
        print(f"  ✓ Prospect #{prospect_id} supprimé")

    return {'success': True, 'id': prospect_id, 'photo_deleted': photo_deleted}


def get_prospect_by_id(
    prospect_id: int,
    db_path: Optional[Path] = None,
    debug: bool = False
) -> Optional[dict]:
    """
    Récupère un prospect par son ID avec ses embeddings désérialisés.

    Utilisé pour la recherche par prospect (évite de rappeler l'API Photofit).

    Args:
        prospect_id: ID du prospect
        db_path: Chemin prospects.db (défaut: bases/prospects.db)
        debug: Mode debug

    Returns:
        dict avec id, prenom, nom, sexe, age, tags, photo_url,
        hair_embedding (list[float]), face_embedding (list[float]),
        attributes (list[float]) — ou None si introuvable
    """
    if db_path is None:
        db_path = DEFAULT_PROSPECTS_DB

    if not db_path.exists():
        if debug:
            print(f"[DEBUG] photofit_upload: prospects.db introuvable : {db_path}")
        return None

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, prenom, nom, sexe, age, tags, photo_filename,
               hair_embedding, face_embedding, attributes_json
        FROM prospects WHERE id = ?
    """, (prospect_id,))

    row = cursor.fetchone()
    conn.close()

    if not row:
        if debug:
            print(f"[DEBUG] photofit_upload: Prospect #{prospect_id} introuvable")
        return None

    result = {
        'id': row['id'],
        'prenom': row['prenom'],
        'nom': row['nom'],
        'sexe': row['sexe'] or '',
        'age': row['age'],
        'tags': row['tags'] or '',
        'photo_filename': row['photo_filename'],
        'photo_url': f"/photofit/prospects/photos/{row['photo_filename']}",
        'hair_embedding': _deserialize_float_vector(row['hair_embedding']),
        'face_embedding': _deserialize_float_vector(row['face_embedding']) if row['face_embedding'] else [],
        'attributes': json.loads(row['attributes_json']) if row['attributes_json'] else [],
    }

    if debug:
        print(f"[DEBUG] photofit_upload: Prospect #{prospect_id} trouvé : "
              f"{result['prenom']} {result['nom']}")

    return result


def get_stats_prospects(db_path: Optional[Path] = None) -> dict:
    """Retourne les statistiques de la base prospects."""
    if db_path is None:
        db_path = DEFAULT_PROSPECTS_DB

    if not db_path.exists():
        return {'total': 0, 'exists': False}

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM prospects")
    total = cursor.fetchone()[0]
    conn.close()

    return {'total': total, 'exists': True, 'db_path': str(db_path)}


def enrichir_avec_patients(
    resultats: List[dict],
    base_path: Path,
    portraits_cache: dict,
    debug: bool = False
) -> List[dict]:
    """
    Enrichit les résultats photofit avec les infos patients depuis baseN.db.

    Pour chaque résultat source='photofit', recherche le patient correspondant
    via idportrait et ajoute nom, prénom, âge, sexe, pathologies, portrait URL.

    Pour les résultats source='prospect', construit l'URL de la photo prospect.

    Args:
        resultats: Liste de dicts issus de rechercher_par_image()
        base_path: Chemin vers la baseN.db active
        portraits_cache: Dict {idportrait: url} depuis PORTRAITS_CACHE
        debug: Mode debug

    Returns:
        Liste enrichie avec les infos patients/prospects
    """
    if not resultats:
        return resultats

    # Collecter les idportrait des résultats photofit
    ids_photofit = [r['idportrait'] for r in resultats if r['source'] == 'photofit']

    # Requête batch pour les patients
    patients_map = {}
    if ids_photofit and base_path.exists():
        try:
            conn = sqlite3.connect(str(base_path))
            conn.row_factory = sqlite3.Row

            # Préparer la requête avec placeholders
            placeholders = ','.join('?' * len(ids_photofit))
            cursor = conn.cursor()
            cursor.execute(f"""
                SELECT id, prenom, nom, sexe, age, idportrait, canontags, oripathologies
                FROM patients
                WHERE idportrait IN ({placeholders})
            """, ids_photofit)

            for row in cursor.fetchall():
                patients_map[str(row['idportrait'])] = dict(row)

            conn.close()

            if debug:
                print(f"[DEBUG] photofit_upload: {len(patients_map)} patients trouvés "
                      f"sur {len(ids_photofit)} idportrait")

        except Exception as e:
            if debug:
                print(f"[DEBUG] photofit_upload: Erreur enrichissement patients : {e}")

    # Enrichir chaque résultat
    for r in resultats:
        if r['source'] == 'photofit':
            idp = r['idportrait']

            # URL portrait depuis le cache
            r['portrait'] = portraits_cache.get(idp, '')

            # Infos patient depuis la base
            patient = patients_map.get(idp, {})
            r['prenom'] = patient.get('prenom', '')
            r['nom'] = patient.get('nom', '')
            r['sexe'] = patient.get('sexe', '')
            r['age'] = patient.get('age', None)
            r['canontags'] = patient.get('canontags', '')
            r['oripathologies'] = patient.get('oripathologies', '')
            r['patient_id'] = patient.get('id', None)

        elif r['source'] == 'prospect':
            # L'URL photo est déjà construite, ajouter le portrait
            r['portrait'] = r.get('photo_url',
                                   f"/photofit/prospects/photos/{r.get('photo_filename', '')}")

    return resultats


# ═══════════════════════════════════════════════════════════════════════════════
# PROGRAMME PRINCIPAL (CLI)
# ═══════════════════════════════════════════════════════════════════════════════

def afficher_aide():
    """Affiche l'aide du programme."""
    print("=" * 70)
    print(f"{__pgm__} - Recherche par image et gestion des prospects")
    print("=" * 70)
    print()
    print("USAGE :")
    print(f"  python {__pgm__} search <image>         Recherche portraits similaires")
    print(f"  python {__pgm__} list                   Liste les prospects")
    print(f"  python {__pgm__} delete <id>            Supprime un prospect par ID")
    print(f"  python {__pgm__} stats                  Stats des bases")
    print()
    print("OPTIONS :")
    print("  -v                Mode verbose")
    print("  -d                Mode debug (très verbeux)")
    print("  -n N              Nombre max de résultats (défaut: 20)")
    print("  --db FILE         Chemin photofit.db (override)")
    print()
    print("EXEMPLES :")
    print(f"  python {__pgm__} search photo.jpg")
    print(f"  python {__pgm__} search photo.jpg -v -n 10")
    print(f"  python {__pgm__} list -v")
    print(f"  python {__pgm__} stats")
    print()


def main():
    """Point d'entrée principal."""
    print(f"{__pgm__} V{__version__} - {__date__}")
    print()

    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        afficher_aide()
        return 0

    commande = sys.argv[1]

    # Parser commun
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('commande', type=str)
    parser.add_argument('image', type=str, nargs='?', default=None)
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-n', '--top', type=int, default=None)
    parser.add_argument('--db', type=str, default=None)

    args = parser.parse_args()
    verbose = args.verbose or args.debug
    debug = args.debug

    if commande == 'search':
        if not args.image:
            print("ERREUR : Chemin de l'image requis")
            print(f"  python {__pgm__} search <image>")
            return 1

        image_path = Path(args.image).resolve()
        if not image_path.is_file():
            print(f"ERREUR : Image introuvable : {image_path}")
            return 1

        print(f"Image : {image_path}")
        print()

        # Lire l'image
        image_bytes = image_path.read_bytes()

        # Extraire les features
        print("Extraction des features via API Photofit...")
        features, error = extraire_features(image_bytes, image_path.name, verbose, debug)

        if error:
            print(f"ERREUR : {error}")
            return 1

        # Lire la config
        config = lire_config(debug=debug)
        if args.top:
            config['max_results'] = args.top

        # Rechercher
        print("Recherche des portraits similaires...")
        resultats = rechercher_par_image(
            hair_embedding=features['hair_embedding'],
            face_embedding=features.get('face_embedding', []),
            config=config,
            verbose=verbose,
            debug=debug
        )

        # Affichage
        print()
        print("═" * 70)
        print(f"RÉSULTATS - {len(resultats)} portrait(s) similaire(s)")
        print("═" * 70)
        print()
        print(f"{'#':<4} {'ID':<20} {'Source':<12} {'Score':<8} {'Distance':<12}")
        print("─" * 70)

        for i, r in enumerate(resultats, 1):
            source = r['source']
            label = r['idportrait']
            if source == 'prospect':
                label = f"{r.get('prenom', '')} {r.get('nom', '')}"
            print(f"{i:<4} {label:<20} {source:<12} {r['score']:<8} {r['distance']:<12.6f}")

        print()
        return 0

    elif commande == 'list':
        prospects = lister_prospects(verbose=verbose)
        if not prospects:
            print("Aucun prospect enregistré.")
            return 0

        print(f"{'#':<4} {'Prénom':<15} {'Nom':<15} {'Âge':<6} {'Tags':<20} {'Date':<20}")
        print("─" * 80)
        for p in prospects:
            age_str = f"{p['age']:.0f}" if p.get('age') else ""
            print(f"{p['id']:<4} {p['prenom']:<15} {p['nom']:<15} "
                  f"{age_str:<6} {p.get('tags', ''):<20} {p.get('created_at', '')[:19]:<20}")
        print()
        return 0

    elif commande == 'delete':
        if not args.image:
            print("ERREUR : ID du prospect requis")
            print(f"  python {__pgm__} delete <id>")
            return 1

        try:
            prospect_id = int(args.image)
        except ValueError:
            print(f"ERREUR : ID invalide : {args.image}")
            return 1

        result = supprimer_prospect(prospect_id, verbose=verbose, debug=debug)
        if result['success']:
            print(f"✓ Prospect #{prospect_id} supprimé")
            return 0
        else:
            print(f"ERREUR : {result.get('error', 'Erreur inconnue')}")
            return 1

    elif commande == 'stats':
        config = lire_config(debug=debug)
        photofit_db = (SCRIPT_DIR / config['photofit_db']).resolve()

        print(f"photofit.db : {photofit_db}")
        if photofit_db.exists():
            conn = sqlite3.connect(str(photofit_db))
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM portraits WHERE status = 'ok'")
            total = cursor.fetchone()[0]
            conn.close()
            print(f"  Portraits OK : {total}")
        else:
            print("  (introuvable)")

        stats_p = get_stats_prospects()
        print(f"prospects.db : {DEFAULT_PROSPECTS_DB}")
        if stats_p['exists']:
            print(f"  Prospects : {stats_p['total']}")
        else:
            print("  (non créée)")

        print()
        return 0

    else:
        print(f"Commande inconnue : '{commande}'")
        afficher_aide()
        return 1


if __name__ == '__main__':
    sys.exit(main())
