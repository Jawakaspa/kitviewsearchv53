# conv_fichePhotofit.md — Synthèse de conversation

**Projet** : KITVIEW Search V5.2
**Sujet** : Création de la documentation technique Photofit (intégration API Maxime → simple30)

---

## Échange 1 — 11/02/2026 ~15h15

**Question Thierry** : Demande de création d'un document technique `photofit.md` couvrant l'intégration de la fonctionnalité Photofit, depuis l'API de Maxime jusqu'à l'IHM simple30. Fourniture d'une capture d'écran montrant "même portrait que Richard Fernandez" (13 résultats, 2299ms, base03200.db).

**Réponse Claude** : Recherche dans l'historique des conversations pour comprendre le contexte existant (detmeme.py, trouveid.py, jsonsql.py, pipeline V5.1). Identification de 4 points manquants avant de rédiger :
1. Specs de l'API de Maxime (endpoints, format réponse)
2. Fichier simple30.html (différences avec web24)
3. Concept "photofit" (classification morphologique ? portrait-robot ?)
4. Périmètre du document (API Maxime seule ou pipeline complet ?)

---

## Échange 2 — 11/02/2026 ~16h00

**Réponses Thierry** :
- **API Maxime** : Swagger disponible à `https://demo.ia.orqual.info:506/photofit/docs`
- **simple30.html** : Fourni en PJ — version simplifiée de chat30 (ex web24), sans page paramètres, recherche compatible
- **Photofit = classification morphologique faciale** (confirmé)
- **Périmètre** : End-to-end complet incluant la base vectorielle
- **Stratégie de test hybride** :
  - `idportrait < 1000` → match exact (V5.1)
  - `idportrait 1000-2599` → API Photofit sur 160 photos × 10 dégradations = 1600 photos test
  - `idportrait ≥ 10000` → photos réelles fournies
- **nc=fichePhotofit** : Nom de la conversation

**Réponse Claude** : Tentative d'accès au Swagger (bloqué par proxy réseau). Début de création du document photofit.md — fichier tronqué à la section 9.

---

## Échange 3 — 11/02/2026 ~16h15

**Thierry** : Fournit la capture d'écran du Swagger Photofit montrant les vrais endpoints :
- **Groupe "default"** : `GET /`, `HEAD /`, `GET /version`, `GET /api/v1/attributes-names`, `GET /api/v1/hair-embedding-size`, `GET /api/v1/face-embedding-size`
- **Groupe "v1"** : `POST /api/v1/extract-features` (body: `img` en multipart/form-data, required)
- Rappel nc=fichePhotofit

**Réponse Claude** : Recréation complète du document `photofit.md` (10 sections) avec :
- Les vrais endpoints issus du Swagger
- Architecture en 2 phases (batch indexation via API + recherche KNN locale)
- Stratégie de test hybride 3 plages
- Pipeline V5.1 vs V5.2 comparé
- Intégration dans l'architecture existante (couche 4c)
- Flux end-to-end en 9 étapes
- Structure proposée de `photofit_client.py`
- Questions ouvertes pour Maxime

---

## Fichiers produits

| Fichier | Description |
|---------|-------------|
| `photofit.md` | Documentation technique complète (format slides-ready) — 10 sections |
| `conv_fichePhotofit.md` | Ce fichier de synthèse |

## Fichiers en entrée

| Fichier | Provenance |
|---------|-----------|
| `simple30.html` | PJ fournie par Thierry (V1.0.0) |
| Capture écran simple30 | "même portrait que Richard Fernandez" — 13 résultats |
| Capture écran Swagger | Endpoints API Photofit (demo.ia.orqual.info:506) |
| `meme.md` | Document projet existant (documentation V5.1 "Même X") |
| `Prompt_contexte0502.md` | Contexte projet |
| `Prompt_MD_to_Slides_Ready.md` | Format slides-ready |

## Points en suspens

1. **Réponses de Maxime** : 7 questions ouvertes (dimensions vecteurs, format JSON exact, attributs, auth, rate limits, formats image, robustesse)
2. **Choix base vectorielle** : FAISS vs ChromaDB vs SQLite+numpy
3. **Calibration seuils** : threshold et pondération face/hair à valider sur les 1600 photos test
4. **Développement** : photofit_client.py à implémenter
