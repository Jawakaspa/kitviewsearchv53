# conv_importphoto — Synthèse de conversation

## 13/02/2026 — Échange 1 : Cadrage du projet

### Question
Thierry souhaite créer un service de recherche par image uploadée (ou caméra mobile).
Photo → API Photofit → embeddings → recherche similaires dans photofit.db → affichage cards.
PWA confirmé.

### Fichiers fournis
- `build_photofit_db.py`, `simple30.html`, `chat30.css`, `communb.csv`

### Questions posées
API Photofit, structure photofit.db, front existant, portraits

---

## 13/02/2026 — Échange 2 : Architecture complète

### Fichiers fournis
- `server.py`, `search.py`, `search_similar.py`, `trouve.py`, `detmeme.py`
- `detall.py`, `trouveid.py`, `jsonsql.py`, `portraits.csv`

### Analyse
Pipeline existant "même portrait que X" : detmeme → trouveid → jsonsql/_rechercher_portraits_similaires
Nouveau : la référence est une photo uploadée, pas un idportrait existant.

### Architecture proposée et validée : Option A (base prospects séparée)
- `prospects.db` : base séparée pour les prospects (jamais toucher baseN.db ni portraits.csv)
- `bases/prospects/` : photos des prospects
- Script batch `integrer_prospects.py` ultérieur pour fusionner si souhaité

---

## 13/02/2026 — Échange 3 : Décisions finales

### Réponses Thierry
- Photos : conservées dans `bases/prospects/`
- Cards : infos patient complètes (comme simple30)
- Preview : géré côté front (FileReader)
- Prospects retrouvés : badge "Prospect" pour les distinguer

### 2 cas d'usage confirmés
1. **Simple** : prospect arrive, photo → recherche similaires. Pas de sauvegarde.
2. **Enrichissement** : checkbox → formulaire (prénom, nom, âge opt, tag "prospect") → sauvegarde dans prospects.db

---

## 17/02/2026 — Échange 4 : Livraison backend (étapes 1 + 2)

### Fichiers livrés

#### `photofit_upload.py` — Module backend principal
- `extraire_features()` : appel API Photofit → embeddings
- `rechercher_par_image()` : cosine distance pondérée vs photofit.db + prospects.db
- `enrichir_avec_patients()` : ajoute nom, âge, pathologies, URL portrait
- `sauver_prospect()` : INSERT prospects.db + photo dans bases/prospects/
- `lister_prospects()`, `creer_base_prospects()`, `get_stats_prospects()`
- `lire_config()` : lit communb.csv section bases
- CLI : `search <image>`, `list`, `stats`

#### `Prompt_server_photofit.py` — Ajouts à server.py (6 blocs)
1. IMPORT photofit_upload
2. Variable PROSPECTS_PHOTOS_DIR
3. LIFESPAN : init prospects.db + répertoire photos
4. Modèle Pydantic ProspectSaveRequest
5. Mount statique `/photofit/prospects/photos/`
6. 3 endpoints :
   - `POST /photofit/search-by-image` : image → features → recherche → résultats enrichis
   - `POST /photofit/save-prospect` : formulaire + embeddings → INSERT
   - `GET /photofit/prospects` : liste des prospects

#### `Prompt_photofit_upload.md` — Prompt de recréation complet

### Prochaine étape
Étape 3 : Front `photofit30.html` (page PWA avec upload, caméra, cards résultats)

---

## 17/02/2026 — Échange 5 : Livraison frontend (étape 3)

### Décisions
- Seuil score : 1 (override communb.csv, hardcodé côté JS)
- Max résultats : 3 (override communb.csv, hardcodé côté JS)
- Temps API pas un problème pour l'instant (effet "deep search")

### Fichiers livrés

#### `photofit30.html` (170 lignes)
Page principale. Structure :
- Header : Logo (clic → retour simple30) | "Portrait Search" | sélecteur base | 🔍🌙
- Zone upload : drag & drop + bouton fichier + bouton 📷 caméra (mobile only)
- Zone loading : spinner + texte dynamique
- Zone résultats : photo référence (jaune) + grille de cards + form prospect
- Modal photo plein écran

#### `photofit30.css` (777 lignes)
CSS dédié, autonome (pas d'import de chat30.css). Reprend les mêmes variables CSS.
- Thème jour/nuit complet
- Responsive (mobile, tablette, desktop)
- Cards patients avec score-badge (vert/orange/rouge selon score)
- Badge "PROSPECT" violet pour distinguer les prospects
- Form prospect avec animation slideDown
- Upload zone avec effet drag-over

#### `photofit30_main.js` (519 lignes)
Toute la logique JS en un seul fichier :
- Upload (fichier, caméra, drag & drop) + validation type/taille
- POST /photofit/search-by-image → filtrage client (score≥1, max 3)
- Construction des cards (photo, nom, âge, sexe, pathologies/tags, score)
- Formulaire prospect (checkbox toggle → form inline → POST /photofit/save-prospect)
- Modal photo plein écran (clic portrait)
- Thème jour/nuit (localStorage)
- Sélecteur base (GET /bases, exclut prospects.db et photofit.db)
- Preview local via FileReader (pas de base64 serveur)

#### `manifest_photofit.json` + `sw_photofit.js`
PWA : manifest pour "Add to Home Screen" + service worker minimal (cache assets, network-first pour API)

### Placement des fichiers

```
ihm/
├── photofit30.html
├── manifest_photofit.json
├── sw_photofit.js
├── css/
│   └── photofit30.css
└── js/
    └── photofit30_main.js
```

### Test
Accès : http://localhost:8000/ihm/photofit30.html

---

## 17/02/2026 — Échange 6 : Corrections + compression + prompt continuation

### Problème identifié
Le `score_min` et `max_results` de communb.csv étaient appliqués côté serveur AVANT que le front ne puisse filtrer. Résultat : PhotoCVTO (score max 47) retournait 0 résultats quand communb avait score_min=50.

### Corrections apportées

#### server.py (v1.2.0 → 3562 lignes)
- Ajout params `score_min` et `max_results` en `Form(None)` au endpoint search-by-image
- Construction d'un `config_override` quand ces params sont fournis
- Passage de l'override à `photofit_rechercher(config=config_override)`

#### photofit30_main.js
- **Compression JPEG côté client** : canvas → JPEG 85%, max 1200px avant upload
  - Fallback sur fichier original si compression échoue
  - Log console : `Compression: 718 Ko → 85 Ko`
- Envoi `score_min=1` et `max_results=3` dans le FormData au serveur
- Suppression du filtrage client (le serveur fait tout)
- Ajout `registerServiceWorker()` → `/ihm/sw_photofit.js`

### Livraison
- `server.py` mis à jour
- `photofit30_main.js` mis à jour
- `Prompt_photofit_continuation.md` — prompt complet pour continuer dans une nouvelle conversation
