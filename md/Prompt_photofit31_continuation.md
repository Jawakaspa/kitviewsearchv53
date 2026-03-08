# Prompt_photofit31_continuation.md

## Objet

Prompt de continuation pour le développement du service Photofit Upload v31 (recherche par portrait). Résume l'état actuel après la migration v30 → v31.

---

## Contexte général

Application de recherche multilingue sur 25 000+ patients orthodontiques. Le service **Photofit Upload** permet de :
1. **Uploader ou photographier** un portrait (mobile PWA ou desktop)
2. Appeler l'**API Photofit** pour extraire les embeddings faciaux (hair_384 + face_128)
3. Chercher les **portraits similaires** dans photofit.db + prospects.db
4. Afficher les résultats enrichis : **prénom, nom, sexe, âge, pathologies**
5. **Sauvegarder comme prospect** / **Supprimer un prospect**
6. **Rechercher via un prospect existant** (pas d'appel API → instantané)
7. **Lister tous les prospects** dans un panneau latéral

## Architecture : base prospects séparée

- `bases/prospects.db` — table `prospects`
- `bases/prospects/` — photos des prospects (UUID.jpg)
- On ne touche **jamais** aux baseN.db ni à portraits.csv

---

## Fichiers et conventions de nommage v31

### Convention com_ (fichiers communs)

Les fichiers partagés entre photofit31.html et pwa31.html sont préfixés `com_` :
- `com_photofit.css` → `ihm/css/`
- `com_photofit.js` → `ihm/js/`

### Backend

| Fichier | Version | Rôle |
|---|---|---|
| `photofit_upload.py` | v31 | Module cœur + 2 nouvelles fonctions |
| `server.py` | v31 | +2 endpoints (DELETE + search-by-prospect-id) |

#### Endpoints photofit complets

| Endpoint | Rôle |
|---|---|
| `POST /photofit/search-by-image` | Upload image → features → recherche → résultats enrichis |
| `POST /photofit/search-by-prospect-id` | **NOUVEAU** Recherche via prospect existant (0ms API) |
| `POST /photofit/save-prospect` | Sauvegarde prospect |
| `GET /photofit/prospects` | Liste des prospects |
| `DELETE /photofit/prospects/{id}` | **NOUVEAU** Supprime prospect + photo |
| `GET /photofit/prospects/photos/{filename}` | Mount statique photos |

#### Nouvelles fonctions photofit_upload.py

| Fonction | Rôle |
|---|---|
| `supprimer_prospect(prospect_id, ...)` | Supprime prospect de la DB + photo du disque |
| `get_prospect_by_id(prospect_id, ...)` | Récupère prospect avec embeddings désérialisés |

### Frontend

| Fichier | Emplacement | Rôle |
|---|---|---|
| `photofit31.html` | `ihm/` | Version desktop (sans PWA) |
| `pwa31.html` | `ihm/` | Version PWA installable (caméra mobile) |
| `simple31.html` | `ihm/` | Search + icône 📷 vers photofit31 |
| `com_photofit.css` | `ihm/css/` | Styles partagés photofit31/pwa31 |
| `com_photofit.js` | `ihm/js/` | Logique partagée photofit31/pwa31 |
| `manifest_pwa31.json` | `ihm/` | Manifest PWA |
| `sw_photofit.js` | `ihm/js/` | Service worker (inchangé) |

---

## Fonctionnalités v31 (ajouts par rapport à v30)

### 1. Suppression de prospect (✕)
- Bouton ✕ sur chaque card prospect (apparaît au hover / toujours visible mobile)
- Animation fade-out à la suppression
- Confirmation avant suppression
- DELETE /photofit/prospects/{id} côté serveur

### 2. Infos patient enrichies
- Prénom, Nom, Sexe (♂/♀), Âge, ID affiché sur chaque card
- Pathologies affichées en tags (jusqu'à 8, puis +N)

### 3. Panneau liste prospects (📋)
- Bouton 📋 dans le header avec badge compteur
- Panneau slide-in depuis la droite
- Chaque prospect : photo, nom, méta, bouton 🔍 (rechercher) et ✕ (supprimer)
- Clic 🔍 → recherche par prospect (pas d'appel API Photofit)

### 4. Recherche par prospect existant
- POST /photofit/search-by-prospect-id
- Utilise les embeddings stockés → 0ms API
- Affiche le prospect comme photo référence (jaune)
- Cache le formulaire "sauver prospect" (déjà sauvé)

### 5. Icône caméra sur simple31
- 📷 ajouté entre ❓ et 🌙 dans le header
- Lien vers /ihm/photofit31.html

### 6. Toast notifications
- Remplace les alert() par des toasts élégants (success/error/info)
- Auto-disparition après 3s

### 7. PWA séparée
- photofit31.html = desktop (pas de SW)
- pwa31.html = PWA installable (manifest + SW)
- Différencié par `window.PHOTOFIT_PWA = true/false`

---

## Algorithme de similarité (inchangé)

- Distance cosinus pondérée : `0.3 * dist_hair + 0.7 * dist_face`
- Score : `100 * (1 - distance / 0.5)`, clamped [0, 100]
- Config communb.csv : `photofit_weight_hair=0.3`, `photofit_weight_face=0.7`
- Override JS : `score_min=1`, `max_results=3`

---

## Ce qui reste à faire

- [ ] Tester DELETE prospect end-to-end
- [ ] Tester search-by-prospect-id end-to-end
- [ ] Déployer sur kitviewsearch53 (privé)
- [ ] `integrer_prospects.py` — batch fusion prospects → baseN.db
- [ ] Slider de score côté front
- [ ] Historique des recherches par image

---

## Fichiers à joindre en PJ

**Obligatoires :**
- `Prompt_contexte0502.md`
- `Prompt_photofit31_continuation.md` (ce fichier)
- `photofit_upload.py`
- `server.py`
- `photofit31.html`
- `pwa31.html`
- `com_photofit.css`
- `com_photofit.js`

**Selon les besoins :**
- `simple31.html` (si modification header/navigation)
- `communb.csv` (si modification config)
- `manifest_pwa31.json` + `sw_photofit.js` (si modification PWA)
