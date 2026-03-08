# Prompt_photofit_continuation.md

## Objet

Ce prompt permet de **continuer le développement** du service Photofit Upload (recherche par portrait) dans une nouvelle conversation. Il résume tout ce qui a été fait, l'état actuel, et les fichiers en jeu.

---

## Contexte général

Le projet est une application de recherche multilingue sur 25 000+ patients orthodontiques. Le service **Photofit Upload** permet de :
1. **Uploader ou photographier** un portrait (mobile PWA)
2. Appeler l'**API Photofit** pour extraire les embeddings faciaux (hair_384 + face_128)
3. Chercher les **portraits similaires** dans photofit.db (patients existants) + prospects.db (prospects ajoutés)
4. Afficher les résultats avec scores de similarité
5. Optionnellement **sauvegarder comme prospect** dans une base séparée

## Architecture Option A : base prospects séparée

Décision clé : on ne touche **jamais** aux baseN.db ni à portraits.csv. Les prospects vont dans :
- `bases/prospects.db` — table `prospects` (id, prenom, nom, sexe, age, tags, photo_filename, embeddings)
- `bases/prospects/` — photos des prospects (UUID.jpg)

Un script `integrer_prospects.py` (non encore créé) permettra ultérieurement de fusionner les prospects validés dans une baseN.db.

---

## Fichiers créés et leur état actuel

### Backend

| Fichier | Version | Rôle |
|---|---|---|
| `photofit_upload.py` | v0.0.0 | Module cœur : API Photofit, recherche cosine, gestion prospects. CLI + import. |
| `server.py` | v1.2.0 (3562 lignes) | 3 endpoints ajoutés + mount statique + init lifespan |

#### Endpoints ajoutés à server.py

| Endpoint | Rôle |
|---|---|
| `POST /photofit/search-by-image` | Upload image → features → recherche → résultats enrichis. Params: `img`, `base`, `score_min` (override), `max_results` (override) |
| `POST /photofit/save-prospect` | Sauvegarde prospect. Params: `img`, `prenom`, `nom`, `sexe`, `age`, `tags`, `hair_embedding` (JSON), `face_embedding` (JSON), `attributes` (JSON) |
| `GET /photofit/prospects` | Liste des prospects |
| `GET /photofit/prospects/photos/{filename}` | Mount statique `bases/prospects/` |

#### Fonctions de photofit_upload.py

| Fonction | Signature |
|---|---|
| `extraire_features(image_bytes, filename, verbose, debug)` | → `(data_dict, error_string)` |
| `rechercher_par_image(hair_emb, face_emb, config, photofit_db, prospects_db, verbose, debug)` | → `[{idportrait, source, score, distance, ...}]` |
| `enrichir_avec_patients(resultats, base_path, portraits_cache, debug)` | → résultats enrichis avec nom/prenom/age/pathologies/portrait_url |
| `sauver_prospect(prenom, nom, photo_bytes, photo_filename, features, sexe, age, tags, ...)` | → `{id, prenom, nom, photo_url, ...}` |
| `lister_prospects(db_path)` | → `[{id, prenom, nom, ...}]` |
| `creer_base_prospects(db_path)` | → Path |
| `get_stats_prospects(db_path)` | → `{total, exists}` |
| `lire_config(debug)` | → dict depuis communb.csv |

### Frontend

| Fichier | Emplacement | Rôle |
|---|---|---|
| `photofit30.html` | `ihm/` | Page principale |
| `photofit30.css` | `ihm/css/` | Styles dédiés (thème jour/nuit, responsive) |
| `photofit30_main.js` | `ihm/js/` | Logique : upload, compression JPEG, API, cards, prospect form, modal |
| `manifest_photofit.json` | `ihm/` | PWA manifest |
| `sw_photofit.js` | `ihm/js/` | Service worker minimal (cerbere range les .js dans js/) |

#### Configuration JS (photofit30_main.js)

```javascript
const CONFIG = {
    MAX_RESULTS: 3,         // Envoyé au serveur (override communb.csv)
    SCORE_MIN: 1,           // Envoyé au serveur (override communb.csv)
    JPEG_QUALITY: 0.85,     // Compression canvas → JPEG
    JPEG_MAX_SIZE: 1200,    // Dimension max en pixels
    COMPRESS_THRESHOLD: 200,// Ko : skip compression si JPEG et < ce seuil
    DEFAULT_BASE: 'base1964.db',
};
```

#### Flux JS
1. Upload (file/camera/drag-drop) → `handleFile()`
2. Si JPEG et < 200 Ko → skip compression (re-encoder gonfle). Sinon canvas → JPEG 85%, max 1200px → `compressImage()`
3. POST `/photofit/search-by-image` avec `score_min=1`, `max_results=3` → `launchSearch()`
4. Affichage : photo référence (jaune) + grille de cards → `showResults()` + `buildCard()`
5. Checkbox "💾 Ajouter prospect" → formulaire inline → POST `/photofit/save-prospect` → `saveProspect()`
6. Les embeddings sont passés depuis `STATE.lastResponse` (évite de rappeler l'API)

### Algorithme de similarité

- Distance cosinus pondérée : `0.3 * dist_hair + 0.7 * dist_face`
- Score : `100 * (1 - distance / 0.5)`, clamped [0, 100]
- Config communb.csv : `photofit_weight_hair=0.3`, `photofit_weight_face=0.7`, `photofit_distance_max=0.5`
- Override page photofit30 : `score_min=1`, `max_results=3`

### API Photofit externe

- URL : `https://demo.ia.orqual.info:506/photofit/api/v1/extract-features`
- POST multipart/form-data, champ `img`
- SSL non vérifié (`verify=False`)
- Timeout : 60s
- Réponse : `{attributes: [16 floats], hair_embedding: [384 floats], face_embedding: [128 floats]}`

### Structures de données

#### photofit.db — table `portraits`
```
idportrait TEXT PK, filepath TEXT, attributes_json TEXT, attributes_bin TEXT,
hair_embedding BLOB (384 float32), face_embedding BLOB (128 float32),
status TEXT, error_message TEXT, created_at TEXT, updated_at TEXT
```

#### prospects.db — table `prospects`
```
id INTEGER PK AUTO, prenom TEXT, nom TEXT, sexe TEXT, age REAL,
tags TEXT DEFAULT 'prospect', photo_filename TEXT,
hair_embedding BLOB, face_embedding BLOB, attributes_json TEXT,
attributes_bin TEXT, created_at TEXT
```

---

## Tests effectués et validés

1. ✅ CLI `photofit_upload.py search <image> -v` — fonctionne
2. ✅ CLI `photofit_upload.py stats` — fonctionne
3. ✅ Endpoint `POST /photofit/search-by-image` via curl — fonctionne
4. ✅ Photo d'un patient existant (Audrey) → score 100 + similaires
5. ✅ Photo inconnue (PNG) → résultats avec scores faibles (47 max)
6. ✅ Sauvegarde prospect (#1 Thierry Oberlé) — fonctionne
7. ✅ Re-recherche → retrouve le prospect sauvegardé (1 résultat prospect)
8. ✅ Frontend photofit30.html : upload, cards, prospect form — fonctionnel
9. ✅ Service worker corrigé (sw_photofit.js au lieu de sw.js)
10. 🔧 Compression JPEG côté client — vient d'être ajoutée, à tester
11. 🔧 Overrides score_min/max_results côté serveur — vient d'être ajouté, à tester

---

## Ce qui reste à faire / évolutions possibles

- [ ] Tester la compression JPEG (gain de temps sur les PNG)
- [ ] Tester les overrides score_min=1 / max_results=3 (PhotoCVTO doit maintenant trouver des résultats)
- [ ] `integrer_prospects.py` — batch pour fusionner prospects → baseN.db
- [ ] Slider de score côté front (réglage dynamique du seuil)
- [ ] Historique des recherches par image
- [ ] Lien depuis simple30.html vers photofit30.html
- [ ] [Vos prochaines fonctionnalités ici]

---

## Fichiers à joindre en PJ pour la prochaine conversation

**Obligatoires :**
- `Prompt_contexte0502.md` (conventions projet)
- `Prompt_photofit_continuation.md` (ce fichier)
- `photofit_upload.py` (module backend)
- `server.py` (v1.2.0 avec les endpoints)
- `photofit30.html` (page frontend)
- `photofit30.css` (dans ihm/css/)
- `photofit30_main.js` (dans ihm/js/)

**Selon les besoins :**
- `communb.csv` (si modification config)
- `build_photofit_db.py` (si modification algo)
- `jsonsql.py` (si modification recherche)
- `simple30.html` + `chat30.css` (si intégration cross-page)
- `manifest_photofit.json` + `sw_photofit.js` (si modification PWA)
