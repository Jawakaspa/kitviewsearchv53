# Prompt_photofit_upload.md

## Objet

Ce prompt permet de recréer les fichiers backend du service **Photofit Upload** :
recherche de portraits similaires à partir d'une image uploadée et gestion des prospects.

---

## Fichiers à créer

### 1. `photofit_upload.py` (module backend principal)

Module Python importable ET utilisable en CLI.

### 2. Ajouts à `server.py` (endpoints FastAPI)

3 endpoints + 1 mount static + 1 init lifespan.

---

## Fichiers à joindre en PJ

- `Prompt_contexte0502.md` (conventions projet)
- `communb.csv` (configuration, section `bases` pour les paramètres Photofit)
- `build_photofit_db.py` (pour référence API Photofit et structure photofit.db)
- `jsonsql.py` (pour référence : `_rechercher_portraits_similaires`, `_cosine_distance`)
- `search_similar.py` (pour référence : algorithme de recherche)
- `server.py` (pour l'intégration des endpoints)
- `portraits.csv` (mapping idportrait → URL)

---

## Spécifications de `photofit_upload.py`

### Fonctions exportées

| Fonction | Rôle |
|---|---|
| `extraire_features(image_bytes, filename, verbose, debug)` | Appel API Photofit → `(data, error)` |
| `rechercher_par_image(hair_emb, face_emb, config, ...)` | Cosine vs photofit.db + prospects.db → liste triée |
| `enrichir_avec_patients(resultats, base_path, portraits_cache)` | Enrichit les résultats avec infos patients/prospects |
| `sauver_prospect(prenom, nom, photo_bytes, photo_filename, features, ...)` | INSERT prospects.db + sauvegarde photo |
| `lister_prospects(db_path)` | SELECT * FROM prospects |
| `creer_base_prospects(db_path)` | CREATE TABLE IF NOT EXISTS |
| `get_stats_prospects(db_path)` | COUNT prospects |
| `lire_config(debug)` | Lit communb.csv section bases |

### API Photofit

- URL : `https://demo.ia.orqual.info:506/photofit/api/v1/extract-features`
- Méthode : POST multipart/form-data, champ `img`
- Réponse : `{attributes: [float...], hair_embedding: [384 floats], face_embedding: [128 floats]}`
- SSL non vérifié (`verify=False`)
- Timeout : 60s

### Structure prospects.db

```sql
CREATE TABLE prospects (
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
);

CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT
);
```

### Algorithme de similarité

- Distance cosinus pondérée : `weight_hair * dist_hair + weight_face * dist_face`
- Conversion distance → score : `score = 100 * (1 - distance / distance_max)`
- Filtrage : score ≥ score_min (30)
- Tri : score décroissant
- Limite : max_results (20)
- Recherche dans photofit.db ET prospects.db, fusion des résultats

### Stockage photos prospects

- Répertoire : `bases/prospects/`
- Nom de fichier : UUID hex (12 chars) + extension originale
- Servies par FastAPI static mount sur `/photofit/prospects/photos/`

### CLI

```
python photofit_upload.py                      # Aide
python photofit_upload.py search <image>       # Recherche
python photofit_upload.py search <image> -v    # Verbose
python photofit_upload.py search <image> -d    # Debug
python photofit_upload.py list                 # Prospects
python photofit_upload.py stats                # Stats
```

---

## Spécifications des endpoints server.py

### `POST /photofit/search-by-image`

- Input : `multipart/form-data` avec `img` (fichier) + `base` (string, défaut "base1000.db")
- Process : extraire_features → rechercher_par_image → enrichir_avec_patients
- Output :
```json
{
    "resultats": [
        {
            "idportrait": "1234",
            "source": "photofit",
            "score": 85,
            "distance": 0.075,
            "portrait": "https://...",
            "prenom": "Jean",
            "nom": "Dupont",
            "sexe": "M",
            "age": 25,
            "canontags": "beance,bruxisme",
            "oripathologies": "Béance,Bruxisme"
        }
    ],
    "nb_resultats": 15,
    "temps_ms": 2300,
    "temps_api_ms": 1800,
    "hair_embedding": [...],
    "face_embedding": [...],
    "attributes": [...]
}
```
- Erreurs : 400 (format invalide, trop gros), 502 (API Photofit), 503 (module absent)
- Limite image : 10 Mo max

### `POST /photofit/save-prospect`

- Input : `multipart/form-data` avec `img` + `prenom` + `nom` + `sexe` + `age` + `tags` + embeddings en JSON stringifié
- Les embeddings proviennent de la réponse search-by-image (évite de rappeler l'API)
- Output : `{success: true, prospect: {id, prenom, nom, photo_url, ...}}`

### `GET /photofit/prospects`

- Output : `{prospects: [...], total: N}`

### Mount statique

```python
app.mount("/photofit/prospects/photos",
          StaticFiles(directory="bases/prospects"),
          name="prospects_photos")
```

---

## Architecture des résultats

Chaque résultat contient un champ `source` :
- `"photofit"` : portrait existant dans la base patients → enrichi avec nom, âge, pathologies, URL portrait
- `"prospect"` : prospect de prospects.db → contient directement prenom, nom, age, tags, photo_url + badge "Prospect" côté front

---

## Tests (TDD)

À tester :
1. `_cosine_distance` : vecteurs identiques → 0, orthogonaux → 1
2. `_distance_to_score` : distance=0 → 100, distance=distance_max → 0
3. `_binarize_attributes` : seuil 0.5
4. `creer_base_prospects` : vérifie que la table existe après création
5. `sauver_prospect` + `lister_prospects` : round-trip
6. `rechercher_par_image` : avec une base de test contenant des embeddings connus
