# Intégration Photofit dans KITVIEW Search

<!-- PRESENTATION_META
titre_court: "Intégration Photofit"
sous_titre: "De l'API d'extraction de features faciales à l'IHM simple30 — Documentation technique V5.2"
duree_estimee: "30min"
niveau: "avancé"
audience: "Développeurs backend/frontend, architectes, Maxime"
fichiers_concernes: "detmeme.py, trouveid.py, jsonsql.py, photofit_client.py, simple30.html, simple30_meme.js"
emoji_principal: "🧬"
-->

**Version** : 1.0.0
**Date** : 11/02/2026
**Auteur** : Documentation technique KITVIEW Search V5.2
**Audience** : Développeurs, architectes logiciel, équipe Maxime

---

<!-- NO_SLIDE -->

## Table des matières

1. [Contexte et objectif](#1-contexte-et-objectif)

2. [Concept Photofit](#2-concept-photofit)

3. [API Photofit de Maxime — Swagger](#3-api-photofit-de-maxime--swagger)

4. [Base vectorielle et calcul de similarité](#4-base-vectorielle-et-calcul-de-similarité)

5. [Pipeline de recherche "même portrait"](#5-pipeline-de-recherche-même-portrait)

6. [Stratégie de test hybride](#6-stratégie-de-test-hybride)

7. [Intégration côté serveur](#7-intégration-côté-serveur)

8. [Interface utilisateur (simple30)](#8-interface-utilisateur-simple30)

9. [Flux end-to-end illustré](#9-flux-end-to-end-illustré)

10. [Limitations et évolutions](#10-limitations-et-évolutions)
    
    <!-- /NO_SLIDE -->

---

<!-- SLIDE
id: "contexte"
titre: "Contexte et objectif"
template: "titre-section"
emoji: "🎯"
timing: "3min"
transition: "slide"
-->

## 1. Contexte et objectif

<!-- KEY: Photofit remplace la correspondance exacte d'idportrait par une similarité morphologique IA via l'API de Maxime -->

### Problème initial (V5.1)

Dans la V5.1 de KITVIEW Search, la recherche "même portrait" repose sur une **correspondance exacte** de la colonne `idportrait` dans la table `patients`. Deux patients ont le "même portrait" si et seulement si leur `idportrait` est identique.

Cette approche est limitée :

- L'`idportrait` est un identifiant statique attribué manuellement ou par classification simple
- Aucune **gradation** de similarité : c'est soit identique, soit différent
- Pas de prise en compte des **nuances morphologiques** entre types faciaux proches
- Impossible de chercher "les patients qui **ressemblent** à Richard Fernandez"

### Objectif V5.2

Intégrer l'API **Photofit** développée par Maxime (Orqual) pour :

- **Extraire des features** (embeddings visage + cheveux) depuis les photos patients via un modèle IA
- **Calculer une similarité vectorielle** entre patients basée sur ces embeddings
- **Remplacer progressivement** la correspondance exacte par une recherche par similarité
- **Afficher un score de correspondance** dans l'interface utilisateur

### Priorité stratégique

L'intégration Photofit est la **priorité n°1** de la V5.2, comme annoncé dans la roadmap :

> *"D'abord remplacer la recherche de portraits similaires en intégrant les développements de Maxime."*

---

<!-- SLIDE
id: "concept-photofit"
titre: "Concept Photofit"
template: "2colonnes"
emoji: "🧬"
timing: "4min"
transition: "fade"
-->

## 2. Concept Photofit

<!-- KEY: Photofit extrait deux types d'embeddings (visage + cheveux) et des attributs nommés à partir d'une photo -->

<!-- QUESTION: Comment classifier objectivement un visage pour la recherche orthodontique ? -->

### Classification morphologique faciale

En orthodontie, les praticiens classifient les visages selon plusieurs axes :

- **Type facial vertical** : dolichocéphale (long), brachycéphale (court), mésocéphale (moyen)
- **Profil sagittal** : convexe (Classe II), droit (Classe I), concave (Classe III)
- **Symétrie** : symétrique vs asymétrique

Photofit automatise cette classification en utilisant un modèle de deep learning (CNN) qui extrait des **vecteurs d'embedding** capturant les caractéristiques morphologiques du visage et des cheveux séparément.

### Deux vecteurs complémentaires

Le modèle produit :

1. **Face embedding** : vecteur capturant la morphologie faciale (forme du visage, mâchoire, profil)
2. **Hair embedding** : vecteur capturant les caractéristiques capillaires (utile pour le portrait-robot complet)
3. **Attributs nommés** : liste de caractéristiques faciales identifiées (endpoint `/attributes-names`)

### Portrait-robot vs photo réelle

Le terme "photofit" (portrait-robot) reflète le concept : au lieu de comparer des photos pixel par pixel, le système compare des **représentations abstraites** (vecteurs) qui capturent les caractéristiques morphologiques pertinentes pour l'orthodontie.

Visuellement dans l'IHM, chaque patient affiche une **image de profil stylisée** correspondant à sa catégorie morphologique.

---

<!-- SLIDE
id: "api-photofit-swagger"
titre: "API Photofit — Swagger"
template: "tableau"
emoji: "🔌"
timing: "5min"
transition: "slide"
-->

## 3. API Photofit de Maxime — Swagger

<!-- KEY: 7 endpoints : health check, version, attributs, dimensions embeddings (face + hair), et le POST central extract-features -->

### Point d'accès

<!-- TABLE
titre: "Informations API Photofit"
colonnes_cles: "Paramètre,Valeur"
style: "compact"
-->

| Paramètre                 | Valeur                                          |
| ------------------------- | ----------------------------------------------- |
| **URL base**              | `https://demo.ia.orqual.info:506/photofit`      |
| **Documentation Swagger** | `https://demo.ia.orqual.info:506/photofit/docs` |
| **Framework**             | FastAPI (Python)                                |
| **Développeur**           | Maxime (équipe Orqual)                          |
| **Versioning**            | API v1                                          |

<!-- /TABLE -->

### Endpoints — Groupe "default"

<!-- TABLE
titre: "Endpoints du groupe default"
colonnes_cles: "Méthode,Endpoint,Description"
style: "large"
-->

| Méthode  | Endpoint                      | Nom Swagger          | Description                                        |
| -------- | ----------------------------- | -------------------- | -------------------------------------------------- |
| **GET**  | `/`                           | Get                  | Health check — vérifie que le service est actif    |
| **HEAD** | `/`                           | Get                  | Idem, sans body (monitoring)                       |
| **GET**  | `/version`                    | Version              | Retourne la version de l'API                       |
| **GET**  | `/api/v1/attributes-names`    | Get Attributes Names | Liste les noms des attributs faciaux détectables   |
| **GET**  | `/api/v1/hair-embedding-size` | Get Hair Dim         | Retourne la dimension du vecteur embedding cheveux |
| **GET**  | `/api/v1/face-embedding-size` | Get Face Dim         | Retourne la dimension du vecteur embedding visage  |

<!-- /TABLE -->

### Endpoint principal — Groupe "v1"

<!-- TABLE
titre: "Endpoint d'extraction de features"
colonnes_cles: "Paramètre,Valeur"
style: "large"
-->

| Paramètre          | Valeur                                                 |
| ------------------ | ------------------------------------------------------ |
| **Méthode**        | `POST`                                                 |
| **Endpoint**       | `/api/v1/extract-features`                             |
| **Nom Swagger**    | Extract Features                                       |
| **Content-Type**   | `multipart/form-data`                                  |
| **Body**           | `img` *(required)* — `string($binary)` — fichier image |
| **Paramètres URL** | Aucun                                                  |
| **Réponse**        | Embeddings face + hair + attributs                     |

<!-- /TABLE -->

### Architecture de l'API

<!-- DIAGRAM
type: "architecture"
titre: "Vue d'ensemble de l'API Photofit"
legende: "1 endpoint principal (extract-features) + 4 endpoints de métadonnées"
-->

```
┌──────────────────────────────────────────────────────────────────────────┐
│                   API PHOTOFIT (FastAPI)                                  │
│                   demo.ia.orqual.info:506/photofit                       │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  GROUPE "default" — Métadonnées & santé                                  │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │  GET  /                       → Health check                     │    │
│  │  HEAD /                       → Health check (sans body)         │    │
│  │  GET  /version                → Version API                      │    │
│  │  GET  /api/v1/attributes-names → Noms des attributs faciaux      │    │
│  │  GET  /api/v1/hair-embedding-size → Dimension vecteur cheveux    │    │
│  │  GET  /api/v1/face-embedding-size → Dimension vecteur visage     │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  GROUPE "v1" — Extraction de features ★ ENDPOINT CLÉ                    │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │  POST /api/v1/extract-features                                   │    │
│  │       Content-Type: multipart/form-data                          │    │
│  │       Body: img (string/$binary, required) ← photo du patient    │    │
│  │                                                                  │    │
│  │       Retour attendu :                                           │    │
│  │       {                                                          │    │
│  │           "face_embedding": [float × N],  // dim → face-emb-size │    │
│  │           "hair_embedding": [float × M],  // dim → hair-emb-size │    │
│  │           "attributes": { nom: valeur, ... }                     │    │
│  │       }                                                          │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

<!-- /DIAGRAM -->

### Appels aux endpoints de métadonnées

<!-- CODE
langage: "python"
titre: "Récupération des métadonnées API"
executable: "false"
-->

```python
import httpx

BASE = "https://demo.ia.orqual.info:506/photofit"

async def get_api_metadata():
    """Récupère les métadonnées de l'API Photofit."""
    async with httpx.AsyncClient(verify=False) as client:
        # Version de l'API
        version = (await client.get(f"{BASE}/version")).json()

        # Noms des attributs faciaux détectables
        attributes = (await client.get(f"{BASE}/api/v1/attributes-names")).json()

        # Dimensions des vecteurs d'embedding
        face_dim = (await client.get(f"{BASE}/api/v1/face-embedding-size")).json()
        hair_dim = (await client.get(f"{BASE}/api/v1/hair-embedding-size")).json()

    return {
        "version": version,
        "attributes": attributes,
        "face_embedding_dim": face_dim,
        "hair_embedding_dim": hair_dim
    }
```

<!-- /CODE -->

### Appel à extract-features

<!-- CODE
langage: "python"
titre: "Extraction de features depuis une photo patient"
executable: "false"
-->

```python
async def extraire_features(image_path: str) -> dict:
    """
    Envoie une photo à POST /api/v1/extract-features.

    Le paramètre 'img' est envoyé en multipart/form-data.
    Retour attendu (structure à confirmer avec Maxime) :
    {
        "face_embedding": [0.12, -0.34, 0.56, ...],   # N floats
        "hair_embedding": [0.45, 0.23, -0.67, ...],   # M floats
        "attributes": {
            "face_shape": "oval",
            "jaw_type": "square",
            ...
        }
    }
    """
    async with httpx.AsyncClient(verify=False, timeout=10.0) as client:
        with open(image_path, "rb") as f:
            response = await client.post(
                f"{BASE}/api/v1/extract-features",
                files={"img": ("photo.jpg", f, "image/jpeg")}
            )
        response.raise_for_status()
    return response.json()
```

<!-- /CODE -->

---

<!-- SLIDE
id: "base-vectorielle"
titre: "Base vectorielle et similarité"
template: "schema"
emoji: "📐"
timing: "4min"
transition: "zoom"
-->

## 4. Base vectorielle et calcul de similarité

<!-- KEY: Les embeddings face+hair sont stockés localement ; la similarité est calculée par distance cosinus côté KITVIEW, sans appel réseau -->

<!-- QUESTION: Pourquoi séparer les embeddings visage et cheveux ? -->

### Principe

L'API Photofit **ne stocke pas** les embeddings et **ne gère pas** la recherche de similarité. Elle extrait uniquement les features d'une image. C'est à KITVIEW Search de :

1. **Indexer** les embeddings de tous les patients (batch offline via `extract-features`)
2. **Stocker** les vecteurs dans une base vectorielle locale
3. **Calculer** la similarité entre le patient de référence et les patients indexés (KNN)

### Workflow d'indexation (batch offline)

<!-- DIAGRAM
type: "flux"
titre: "Indexation des embeddings patients"
legende: "Batch exécuté une fois puis mis à jour incrémentalement"
-->

```
┌──────────────────────────────────────────────────────────────────────────┐
│                INDEXATION BATCH (offline)                                 │
└──────────────────────────────────────────────────────────────────────────┘

  Pour chaque patient ayant une photo :

  ┌────────────┐     POST /api/v1/extract-features  ┌────────────────┐
  │  Photo     │ ──────────────────────────────────▶ │  API Photofit  │
  │  patient   │     files: {img: photo.jpg}         │  (Maxime)      │
  │  ID: 1042  │                                     └───────┬────────┘
  └────────────┘                                             │
                                                             ▼
                                                   ┌─────────────────────┐
                                                   │ Réponse JSON :      │
                                                   │  face_emb: [N dim]  │
                                                   │  hair_emb: [M dim]  │
                                                   │  attributes: {...}  │
                                                   └─────────┬───────────┘
                                                             │
                                                             ▼
                                                   ┌─────────────────────┐
                                                   │ Base vectorielle    │
                                                   │ locale              │
                                                   │                     │
                                                   │ ID: 1042            │
                                                   │ face: [0.12, ...]   │
                                                   │ hair: [0.45, ...]   │
                                                   │ attrs: {shape:oval} │
                                                   └─────────────────────┘
```

<!-- /DIAGRAM -->

### Workflow de recherche (online, sans appel réseau)

<!-- DIAGRAM
type: "flux"
titre: "Recherche de portraits similaires — calcul local"
legende: "Aucun appel à l'API Photofit en temps réel"
-->

```
  "même portrait que Richard Fernandez"
        │
        ▼
  ┌──────────────────────────────────────┐
  │  trouveid.py → idportrait = 1042    │
  │  Récupère embedding du patient 1042  │
  │  depuis la base vectorielle locale   │
  └───────────────┬──────────────────────┘
                  │
                  ▼
  ┌──────────────────────────────────────┐
  │  Recherche KNN (K Nearest Neighbors) │
  │                                      │
  │  Similarité cosinus :                │
  │  sim(A,B) = (A·B) / (||A|| × ||B||) │
  │                                      │
  │  Score composite :                   │
  │  score = α × sim_face + β × sim_hair │
  │  (ex: α=0.8, β=0.2)                 │
  └───────────────┬──────────────────────┘
                  │
                  ▼
  ┌──────────────────────────────────────┐
  │  Résultats triés par score :         │
  │  ID 1089 → 94%                       │
  │  ID 1156 → 87%                       │
  │  ID 1203 → 72%                       │
  │  ...                                 │
  └──────────────────────────────────────┘
```

<!-- /DIAGRAM -->

### Pondération face / hair

<!-- CODE
langage: "python"
titre: "Calcul de similarité pondérée face + hair"
executable: "false"
-->

```python
import numpy as np

def similarite_cosinus(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Distance cosinus entre deux vecteurs."""
    dot = np.dot(vec_a, vec_b)
    norm = np.linalg.norm(vec_a) * np.linalg.norm(vec_b)
    return float(dot / norm) if norm > 0 else 0.0

def similarite_photofit(
    patient_ref: dict,
    patient_cible: dict,
    poids_face: float = 0.8,
    poids_hair: float = 0.2
) -> float:
    """
    Score de similarité composite face + cheveux.
    Pondération par défaut : 80% visage, 20% cheveux.
    """
    sim_face = similarite_cosinus(
        np.array(patient_ref["face_embedding"]),
        np.array(patient_cible["face_embedding"])
    )
    sim_hair = similarite_cosinus(
        np.array(patient_ref["hair_embedding"]),
        np.array(patient_cible["hair_embedding"])
    )
    return poids_face * sim_face + poids_hair * sim_hair
```

<!-- /CODE -->

### Technologies de stockage vectoriel envisagées

<!-- TABLE
titre: "Options de base vectorielle"
colonnes_cles: "Technologie,Type"
style: "large"
-->

| Technologie        | Type                 | Avantages                       | Inconvénients                   |
| ------------------ | -------------------- | ------------------------------- | ------------------------------- |
| **FAISS** (Meta)   | Bibliothèque Python  | Ultra-rapide, pas de serveur    | En mémoire, persistance à gérer |
| **ChromaDB**       | Base embarquée       | Simple, Python natif            | Limité en très gros volumes     |
| **SQLite + numpy** | Fichier local        | Cohérent avec l'archi existante | Moins optimisé pour KNN massif  |
| **pgvector**       | Extension PostgreSQL | Intégré à une BDD relationnelle | Nécessite PostgreSQL            |

<!-- /TABLE -->

---

<!-- SLIDE
id: "pipeline-meme-portrait"
titre: "Pipeline 'même portrait'"
template: "schema"
emoji: "🔄"
timing: "5min"
transition: "slide"
-->

## 5. Pipeline de recherche "même portrait"

<!-- KEY: V5.1 = match exact sur idportrait | V5.2 = KNN local sur embeddings extraits par Photofit API -->

### Comparaison V5.1 vs V5.2

<!-- DIAGRAM
type: "comparaison"
titre: "Évolution du pipeline portrait"
legende: "V5.1 = match exact | V5.2 = similarité vectorielle via embeddings Photofit"
-->

```
═══════════════════════════════════════════════════════════════════════
  V5.1 — CORRESPONDANCE EXACTE (idportrait identique)
═══════════════════════════════════════════════════════════════════════

  "même portrait que Richard Fernandez"
        │
        ▼
  ┌─────────────┐    ┌────────────┐    ┌──────────────┐    ┌──────────┐
  │  detmeme.py │───▶│ trouveid.py│───▶│  jsonsql.py  │───▶│ lancesql │
  │  cible=     │    │ idportrait │    │ WHERE p.id   │    │          │
  │  portrait   │    │ = '5'      │    │ portrait='5' │    │ Résultats│
  └─────────────┘    └────────────┘    └──────────────┘    └──────────┘

  SQL : WHERE p.idportrait = '5' AND p.id != 5


═══════════════════════════════════════════════════════════════════════
  V5.2 — SIMILARITÉ VECTORIELLE (embeddings Photofit)
═══════════════════════════════════════════════════════════════════════

  "même portrait que Richard Fernandez"
        │
        ▼
  ┌─────────────┐    ┌────────────┐    ┌────────────────┐    ┌──────────┐
  │  detmeme.py │───▶│ trouveid.py│───▶│ photofit_      │───▶│ jsonsql  │
  │  cible=     │    │ idportrait │    │ client.py      │    │ WHERE id │
  │  portrait   │    │ = 1042     │    │                │    │ IN (...)  │
  └─────────────┘    └────────────┘    │ KNN local sur  │    └──────────┘
                                       │ base vecto.    │         │
                                       └────────────────┘         ▼
                                            │               ┌──────────┐
                                            ▼               │ Résultats│
                                    IDs similaires          │ + scores │
                                    + scores                └──────────┘
                                    [1089:94%,
                                     1156:87%, ...]

  SQL : WHERE p.idportrait IN (1042, 1089, 1156, ...) AND p.id != 5
```

<!-- /DIAGRAM -->

### Détail des étapes V5.2

1. **detmeme.py** : Détecte le pattern "même portrait que X" → `cible = "portrait"`
2. **trouveid.py** : Résout "Richard Fernandez" → `id = 5`, récupère `idportrait = 1042`
3. **photofit_client.py** (nouveau) : Recherche KNN dans la base vectorielle locale → liste d'IDs similaires avec scores
4. **jsonsql.py** : Génère `WHERE p.idportrait IN (1042, 1089, 1156, ...)` au lieu de `WHERE p.idportrait = '5'`
5. **lancesql.py** : Exécute la requête SQL
6. **Résultats** : Patients triés par score de similarité décroissant

---

<!-- SLIDE
id: "strategie-test-hybride"
titre: "Stratégie de test hybride"
template: "tableau"
emoji: "🧪"
timing: "4min"
transition: "fade"
-->

## 6. Stratégie de test hybride

<!-- KEY: 3 plages d'idportrait : <1000 (match exact), 1000-2599 (Photofit sur 1600 photos test dégradées), ≥10000 (photos réelles) -->

<!-- QUESTION: Comment tester la similarité IA sans disposer de toutes les photos réelles ? -->

Pour permettre un développement et des tests progressifs, KITVIEW Search V5.2 adopte une **stratégie hybride** basée sur la plage de l'`idportrait`.

### Trois plages de fonctionnement

<!-- TABLE
titre: "Stratégie hybride par plage d'idportrait"
colonnes_cles: "Plage,Mode,Source"
style: "large"
-->

| Plage idportrait | Mode                | Source photos             | Méthode de similarité               | Volume         |
| ---------------- | ------------------- | ------------------------- | ----------------------------------- | -------------- |
| **< 1000**       | Match exact         | Pas de photo réelle       | `idportrait` identique (V5.1)       | Base existante |
| **1000 — 2599**  | Photofit test       | 160 photos test dégradées | Similarité vectorielle (embeddings) | 1 600 photos   |
| **≥ 10000**      | Photofit production | Photos réelles fournies   | Similarité vectorielle (embeddings) | Variable       |

<!-- /TABLE -->

### Détail de la plage de test (1000-2599)

Les 160 photos originales sont chacune déclinées en **10 variantes dégradées**, produisant 1 600 photos au total :

<!-- DIAGRAM
type: "flux"
titre: "Génération des 1600 photos de test"
legende: "160 photos originales × 10 variantes de dégradation = 1600 photos indexées"
-->

```
  160 photos originales (IDs 1000-1159)
  ┌───────────────────────────────────────────────────────────┐
  │  ID 1000        ID 1001        ID 1002   ...   ID 1159   │
  │  📷 photo_0     📷 photo_1     📷 photo_2      📷 photo_159│
  └───────────────────────────┬───────────────────────────────┘
                              │
                              ▼  × 10 variantes par photo
  ┌───────────────────────────────────────────────────────────┐
  │  Variante 0 : Original (sans dégradation)                 │
  │  Variante 1 : Rotation légère (±5°)                       │
  │  Variante 2 : Changement luminosité (+/-)                 │
  │  Variante 3 : Flou gaussien                               │
  │  Variante 4 : Bruit aléatoire                             │
  │  Variante 5 : Recadrage (zoom/décalage)                   │
  │  Variante 6 : Compression JPEG forte                      │
  │  Variante 7 : Changement de contraste                     │
  │  Variante 8 : Miroir horizontal                           │
  │  Variante 9 : Combinaison de dégradations                 │
  └───────────────────────────┬───────────────────────────────┘
                              │
                              ▼
  ┌───────────────────────────────────────────────────────────┐
  │  1 600 photos indexées via POST /api/v1/extract-features  │
  │  → 1 600 paires (face_embedding, hair_embedding)          │
  │  → Stockées dans la base vectorielle locale               │
  └───────────────────────────────────────────────────────────┘
```

<!-- /DIAGRAM -->

### Objectif de la dégradation

Les photos dégradées permettent de tester la **robustesse** du modèle Photofit :

- Le modèle doit retrouver les variantes d'une même personne avec un score élevé (>0.8)
- Les photos de personnes différentes doivent avoir un score bas (<0.5)
- Les seuils de similarité sont calibrés sur ces données de test avant le passage en production

### Logique de routage dans le code

<!-- CODE
langage: "python"
titre: "Routage hybride selon l'idportrait"
executable: "false"
-->

```python
# Constantes de routage
SEUIL_EXACT = 1000          # En dessous : match exact V5.1
SEUIL_TEST_MIN = 1000       # Début plage test Photofit
SEUIL_TEST_MAX = 2599       # Fin plage test Photofit
SEUIL_PRODUCTION = 10000    # Au-dessus : photos réelles Photofit

def determiner_mode_portrait(idportrait: int) -> str:
    """Détermine le mode de recherche selon l'idportrait."""
    if idportrait < SEUIL_EXACT:
        return "exact"         # V5.1 : WHERE idportrait = X
    elif SEUIL_TEST_MIN <= idportrait <= SEUIL_TEST_MAX:
        return "photofit_test" # Similarité sur photos dégradées
    elif idportrait >= SEUIL_PRODUCTION:
        return "photofit_prod" # Similarité sur photos réelles
    else:
        return "exact"         # Fallback sécurité (plage 2600-9999)
```

<!-- /CODE -->

---

<!-- SLIDE
id: "integration-serveur"
titre: "Intégration côté serveur"
template: "schema"
emoji: "⚙️"
timing: "5min"
transition: "slide"
-->

## 7. Intégration côté serveur

<!-- KEY: Nouveau module photofit_client.py ; API Photofit appelée en batch (indexation) mais jamais en temps réel (recherche = KNN local) -->

### Deux usages distincts de l'API

<!-- TABLE
titre: "Batch vs Online — quand appeler l'API"
colonnes_cles: "Contexte,Quand,Endpoint"
style: "large"
-->

| Contexte             | Quand                                | Fréquence              | Endpoint utilisé                           |
| -------------------- | ------------------------------------ | ---------------------- | ------------------------------------------ |
| **Indexation batch** | Ajout/mise à jour de photos patients | Ponctuel (cron/manuel) | `POST /api/v1/extract-features`            |
| **Recherche online** | Requête "même portrait que..."       | Chaque recherche       | **Aucun** (KNN local sur base vectorielle) |

<!-- /TABLE -->

Point clé : l'API Photofit n'est **pas appelée en temps réel** lors d'une recherche. Les embeddings sont pré-calculés et stockés localement. La recherche de similarité (KNN) se fait côté KITVIEW sans latence réseau.

### Point d'insertion dans l'architecture

<!-- DIAGRAM
type: "architecture"
titre: "Position de Photofit dans les couches serveur"
legende: "Nouveau module photofit_client.py entre trouveid et jsonsql"
-->

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        KITVIEW Search V5.2                               │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Couche 1 — API (server.py / FastAPI)                                    │
│       │                                                                  │
│       ▼                                                                  │
│  Couche 2 — Orchestration (search.py)                                    │
│       │                                                                  │
│       ▼                                                                  │
│  Couche 3 — Recherche (trouve.py)                                        │
│       │                                                                  │
│       ▼                                                                  │
│  Couche 4a — Détection (detall.py → detmeme.py → ...)                    │
│       │                                                                  │
│       ▼                                                                  │
│  Couche 4b — Résolution identité (trouveid.py)                           │
│       │         Récupère id, idportrait, données patient                  │
│       ▼                                                                  │
│  ┌────────────────────────────────────────────────────────────────┐      │
│  │  Couche 4c — PHOTOFIT (NOUVEAU)                                │      │
│  │  photofit_client.py                                            │      │
│  │                                                                │      │
│  │  SI cible == "portrait" ET idportrait >= 1000 :                │      │
│  │     → Recherche KNN dans base vectorielle locale               │      │
│  │     → Retourne liste d'IDs similaires + scores                 │      │
│  │  SINON :                                                       │      │
│  │     → Correspondance exacte (V5.1)                             │      │
│  │                                                                │      │
│  │  FALLBACK : si base vectorielle absente/erreur                 │      │
│  │     → Correspondance exacte + log warning                     │      │
│  └────────────────────────────────────────────────────────────────┘      │
│       │                                                                  │
│       ▼                                                                  │
│  Couche 5 — Génération SQL (jsonsql.py)                                  │
│       │      WHERE p.idportrait IN (...) au lieu de = X                  │
│       ▼                                                                  │
│  Couche 6 — Exécution (lancesql.py)                                      │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

<!-- /DIAGRAM -->

### Structure de photofit_client.py

<!-- CODE
langage: "python"
titre: "photofit_client.py — structure proposée"
executable: "false"
-->

```python
#*TO*#
__pgm__ = "photofit_client.py"
__version__ = "0.0.0"
__date__ = "01/01/1970 00:00"

"""
Client Photofit (Orqual / Maxime).
Phase 1 (batch) : Appel POST /api/v1/extract-features → indexation embeddings.
Phase 2 (online) : Recherche KNN locale sur les embeddings pré-calculés.
"""

import httpx
import numpy as np
import os

PHOTOFIT_BASE = os.getenv(
    "PHOTOFIT_API_URL",
    "https://demo.ia.orqual.info:506/photofit"
)
PHOTOFIT_TIMEOUT = 10  # secondes

SEUIL_EXACT = 1000
SEUIL_TEST_MAX = 2599
SEUIL_PRODUCTION = 10000


# ═══════════════════════════════════════════════════
#  PHASE 1 : INDEXATION (batch offline)
# ═══════════════════════════════════════════════════

async def extraire_features(image_path: str) -> dict:
    """Appelle POST /api/v1/extract-features pour une photo."""
    async with httpx.AsyncClient(verify=False, timeout=PHOTOFIT_TIMEOUT) as client:
        with open(image_path, "rb") as f:
            response = await client.post(
                f"{PHOTOFIT_BASE}/api/v1/extract-features",
                files={"img": ("photo.jpg", f, "image/jpeg")}
            )
        response.raise_for_status()
    return response.json()


async def indexer_patients(photos: dict, db_path: str):
    """
    Indexe toutes les photos patients via l'API.
    photos = {idportrait: chemin_photo, ...}
    """
    for idportrait, photo_path in photos.items():
        features = await extraire_features(photo_path)
        stocker_embedding(
            db_path=db_path,
            idportrait=idportrait,
            face_emb=features["face_embedding"],
            hair_emb=features["hair_embedding"],
            attributes=features.get("attributes", {})
        )


# ═══════════════════════════════════════════════════
#  PHASE 2 : RECHERCHE (online — aucun appel réseau)
# ═══════════════════════════════════════════════════

def chercher_portraits_similaires(
    idportrait: int,
    db_path: str,
    top_k: int = 20,
    threshold: float = 0.5,
    poids_face: float = 0.8,
    poids_hair: float = 0.2
) -> dict:
    """
    Recherche les portraits similaires — 100% local.
    """
    mode = determiner_mode_portrait(idportrait)

    if mode == "exact":
        return {
            "mode": "exact",
            "portraits": [{"idportrait": idportrait, "score": 1.0}]
        }

    ref_emb = charger_embedding(db_path, idportrait)
    if ref_emb is None:
        return {
            "mode": "exact_fallback",
            "portraits": [{"idportrait": idportrait, "score": 1.0}]
        }

    tous_emb = charger_tous_embeddings(db_path)
    scores = []
    for id_cible, emb_cible in tous_emb.items():
        if id_cible == idportrait:
            continue
        sim = (
            poids_face * similarite_cosinus(ref_emb["face"], emb_cible["face"])
            + poids_hair * similarite_cosinus(ref_emb["hair"], emb_cible["hair"])
        )
        if sim >= threshold:
            scores.append({"idportrait": id_cible, "score": round(sim, 4)})

    scores.sort(key=lambda x: x["score"], reverse=True)
    return {"mode": mode, "portraits": scores[:top_k]}
```

<!-- /CODE -->

### Modification de jsonsql.py

<!-- CODE
langage: "python"
titre: "Nouvelle clause SQL pour similarité portrait (jsonsql.py)"
executable: "false"
-->

```python
def _generer_clause_meme_portrait(self, critere: dict) -> tuple:
    """Génère la clause SQL pour le critère 'même portrait'."""

    photofit = critere.get("photofit_result", {})
    mode = photofit.get("mode", "exact")
    portraits = photofit.get("portraits", [])

    if mode in ("exact", "exact_fallback"):
        # V5.1 : correspondance exacte
        idp = critere["reference_patient"]["idportrait"]
        return "p.idportrait = ?", [idp]
    else:
        # V5.2 : liste de portraits similaires
        ids = [p["idportrait"] for p in portraits]
        placeholders = ", ".join(["?"] * len(ids))
        return f"p.idportrait IN ({placeholders})", ids
```

<!-- /CODE -->

---

<!-- SLIDE
id: "interface-simple30"
titre: "Interface simple30"
template: "2colonnes"
emoji: "🖥️"
timing: "4min"
transition: "zoom"
-->

## 8. Interface utilisateur (simple30)

<!-- KEY: simple30 = version épurée (7 JS dédiés, aucun partage avec chat30), recherche "même portrait" avec fond jaune stabilo et scores -->

### Architecture frontend simple30

L'IHM `simple30.html` (V1.0.0, 11/02/2026) est une version simplifiée de `chat30.html`. Fichiers 100% dédiés :

<!-- TABLE
titre: "Fichiers JavaScript dédiés simple30"
colonnes_cles: "Fichier,Rôle"
style: "large"
-->

| Fichier                     | Rôle                                                                  |
| --------------------------- | --------------------------------------------------------------------- |
| `simple30_utils.js`         | Utilitaires (debounce, addDebugLog, constantes DEBUG)                 |
| `simple30_voice.js`         | Reconnaissance vocale (micro)                                         |
| `simple30_illustrations.js` | Gestion images patients et filigrane                                  |
| `simple30_search.js`        | Module recherche API (appels serveur)                                 |
| `simple30_i18n.js`          | Internationalisation (12 langues)                                     |
| `simple30_meme.js`          | Logique "même que" (memeState, handleMemeClick, generateMemeQuestion) |
| `simple30_main.js`          | Code principal, initialisation, événements                            |

<!-- /TABLE -->

### Simplifications vs chat30

| Élément                   | chat30       | simple30         |
| ------------------------- | ------------ | ---------------- |
| Checkbox toolbar toggle   | ✅            | ❌ Supprimé       |
| Mode Démo (switch + ring) | ✅            | ❌ Supprimé       |
| Bouton Analyse (📊)       | ✅            | ❌ Supprimé       |
| Bouton Paramètres (⚙️)    | ✅            | ❌ Supprimé       |
| Page paramètres           | ✅ webparams  | ❌ Aucune         |
| Mode SC                   | Configurable | Fixé (masqué)    |
| Recherche patients        | ✅            | ✅ **Compatible** |

Header résultant : `☰ Logo Search [base] [langue] [→fr] [détection] ? 🌙`

### Illustration de la capture d'écran

La capture montre la requête **"même portrait que Richard Fernandez"** sur `base03200.db` en mode `standard` :

- **13 patients trouvés** en **2299 ms**
- **Patient de référence** (Richard Fernandez, ID 5, ♂ 15 ans) : fond **jaune stabilo** dégradé `#ffff00 → #ffeb3b`, bordure dorée `#ffc107`
- **Badge rouge 100%** sur le patient de référence (recouvrement pathologique)
- **Scores décroissants** : 75% (Mariama Bouzid, ♀ 7 ans), 59% (Roger Laporte, ♂ 14 ans), 56% (Pierre Bernard, ♂ 18 ans), 53%, 49%, 49%, 49%, 46%, 36%...
- Chaque carte : portrait circulaire stylisé, prénom (badge clair) / nom (badge sombre), sexe/âge, pathologies groupées par tag parent

### Score affiché

Les **pourcentages** visibles (100%, 75%, 59%...) sont le **taux de recouvrement pathologique** — combien de pathologies le patient partage avec le patient de référence. Ce score est **indépendant** de la similarité morphologique Photofit.

Avec la V5.2, un **second score** (similarité portrait) pourra être ajouté ou combiné au score pathologique.

### CSS patient de référence (inline simple30.html)

<!-- CODE
langage: "css"
titre: "Style jaune stabilo — override inline"
executable: "false"
-->

```css
.patient-card.reference-patient {
    background: linear-gradient(135deg, #ffff00 0%, #ffeb3b 100%) !important;
    border: 3px solid #ffc107 !important;
    box-shadow: 0 4px 15px rgba(255, 235, 59, 0.5) !important;
}

[data-theme="dark"] .patient-card.reference-patient {
    background: linear-gradient(135deg, #ffff00 0%, #fdd835 100%) !important;
    border: 3px solid #ffb300 !important;
}
```

<!-- /CODE -->

---

<!-- SLIDE
id: "flux-end-to-end"
titre: "Flux end-to-end"
template: "schema"
emoji: "🔀"
timing: "4min"
transition: "slide"
-->

## 9. Flux end-to-end illustré

<!-- KEY: 9 étapes du clic utilisateur à l'affichage ; l'API Photofit n'est appelée qu'en indexation batch, jamais en recherche -->

### Scénario : "même portrait que Richard Fernandez" (V5.2)

<!-- DIAGRAM
type: "sequence"
titre: "Flux end-to-end de la recherche par portrait similaire"
legende: "Du navigateur au résultat affiché — 9 étapes"
-->

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ NAVIGATEUR│     │ SERVER   │     │ DÉTECTION│     │ PHOTOFIT │     │ BASE     │
│ simple30  │     │ .py      │     │ pipeline │     │ CLIENT   │     │ SQLite   │
└─────┬────┘     └─────┬────┘     └─────┬────┘     └─────┬────┘     └─────┬────┘
      │                │                │                │                │
  ①   │  POST /api/    │                │                │                │
      │  search?q=     │                │                │                │
      │  "même portrait│                │                │                │
      │  que Richard   │                │                │                │
      │  Fernandez"    │                │                │                │
      │───────────────▶│                │                │                │
      │                │                │                │                │
  ②   │                │  search()      │                │                │
      │                │───────────────▶│                │                │
      │                │                │                │                │
  ③   │                │                │  detmeme.py    │                │
      │                │                │  → cible=      │                │
      │                │                │    portrait    │                │
      │                │                │  → ref=Richard │                │
      │                │                │    Fernandez   │                │
      │                │                │                │                │
  ④   │                │                │  trouveid.py   │                │
      │                │                │  → id=5        │                │
      │                │                │  → idportrait= │                │
      │                │                │    1042        │                │
      │                │                │                │                │
  ⑤   │                │                │  idportrait    │                │
      │                │                │  1042 >= 1000  │                │
      │                │                │  → mode=       │                │
      │                │                │  photofit_test │                │
      │                │                │───────────────▶│                │
      │                │                │                │  KNN local     │
      │                │                │                │  cosinus(face  │
      │                │                │                │  + hair)       │
      │                │                │  IDs similaires│                │
      │                │                │  + scores      │                │
      │                │                │◀───────────────│                │
      │                │                │                │                │
  ⑥   │                │                │  jsonsql.py    │                │
      │                │                │  WHERE idp     │                │
      │                │                │  IN (1042,     │                │
      │                │                │  1089,1156,..) │                │
      │                │                │────────────────────────────────▶│
      │                │                │                │                │
  ⑦   │                │                │  13 patients   │                │
      │                │                │◀───────────────────────────────│
      │                │                │                │                │
  ⑧   │  JSON résultats│                │                │                │
      │  + scores patho│                │                │                │
      │  + scores photo│                │                │                │
      │◀───────────────│                │                │                │
      │                │                │                │                │
  ⑨   │  Affichage :   │                │                │                │
      │  • Réf en jaune│                │                │                │
      │  • Scores %    │                │                │                │
      │  • Tri par     │                │                │                │
      │    similarité  │                │                │                │
```

<!-- /DIAGRAM -->

### Temps de réponse attendus

<!-- TABLE
titre: "Décomposition des temps V5.2"
colonnes_cles: "Étape,Temps"
style: "compact"
-->

| Étape                       | Temps estimé | Commentaire                    |
| --------------------------- | ------------ | ------------------------------ |
| detmeme.py                  | < 5 ms       | Pattern matching algorithmique |
| trouveid.py                 | < 50 ms      | Requête SQL simple             |
| photofit_client (KNN local) | < 100 ms     | Calcul vectoriel en mémoire    |
| jsonsql.py                  | < 5 ms       | Construction de la requête     |
| lancesql.py                 | < 500 ms     | Dépend de la taille de la base |
| **Total cible**             | **< 700 ms** | **vs 2299 ms actuel**          |

<!-- /TABLE -->

---

<!-- SLIDE
id: "limitations-evolutions"
titre: "Limitations et évolutions"
template: "2colonnes"
emoji: "🚀"
timing: "3min"
transition: "zoom"
-->

## 10. Limitations et évolutions

<!-- KEY: Dépendance API Maxime pour l'indexation uniquement ; seuils et pondérations à calibrer sur les 1600 photos test -->

### Limitations actuelles

- **API Maxime** : Dépendance sur `demo.ia.orqual.info:506` pour l'indexation (pas pour la recherche)
- **Qualité des photos** : L'angle et la qualité impactent directement la qualité de l'embedding
- **Calibration** : Le `threshold` (0.5) et la pondération face/hair (80/20) sont des estimations initiales
- **Plage 2600-9999** : Non définie — fallback silencieux sur match exact
- **Pas de re-indexation auto** : Si l'API évolue, les anciens embeddings ne sont pas mis à jour
- **Format de réponse** : La structure JSON exacte de `extract-features` reste à confirmer

### Roadmap Photofit

<!-- TABLE
titre: "Évolutions prévues"
colonnes_cles: "Version,Fonctionnalité"
style: "large"
-->

| Version | Fonctionnalité     | Description                                                     |
| ------- | ------------------ | --------------------------------------------------------------- |
| V5.2.0  | Indexation batch   | Script d'indexation des 1600 photos test via `extract-features` |
| V5.2.0  | KNN local          | Recherche de similarité dans base vectorielle FAISS/ChromaDB    |
| V5.2.0  | Routage hybride    | 3 plages d'idportrait (<1000, 1000-2599, ≥10000)                |
| V5.2.1  | Score combiné      | Affichage score portrait + score pathologique dans l'IHM        |
| V5.2.1  | Calibration seuils | Tests sur les 1600 photos dégradées                             |
| V5.2.2  | Photos réelles     | Passage en production (≥10000)                                  |
| V5.3    | Re-indexation auto | Détection changement version API → re-indexation                |
| V5.3    | Attributs nommés   | Exploitation des `attributes` (endpoint `/attributes-names`)    |

<!-- /TABLE -->

### ---

<!-- SLIDE
id: "annexes"
titre: "Annexes"
template: "titre-section"
emoji: "📎"
timing: "1min"
transition: "fade"
-->

## Annexes

<!-- NO_SLIDE -->

### A. Variables d'environnement

```python
PHOTOFIT_API_URL = "https://demo.ia.orqual.info:506/photofit"
PHOTOFIT_DB_PATH = "bases/photofit_embeddings.db"
PHOTOFIT_POIDS_FACE = 0.8
PHOTOFIT_POIDS_HAIR = 0.2
PHOTOFIT_THRESHOLD = 0.5
PHOTOFIT_TOP_K = 20
```

### B. Récapitulatif endpoints Swagger

| Méthode  | Endpoint                       | Description                           |
| -------- | ------------------------------ | ------------------------------------- |
| GET      | `/`                            | Health check                          |
| HEAD     | `/`                            | Health check (sans body)              |
| GET      | `/version`                     | Version de l'API                      |
| GET      | `/api/v1/attributes-names`     | Noms des attributs faciaux            |
| GET      | `/api/v1/hair-embedding-size`  | Dimension vecteur cheveux             |
| GET      | `/api/v1/face-embedding-size`  | Dimension vecteur visage              |
| **POST** | **`/api/v1/extract-features`** | **Extraction features (img: binary)** |

### C. Structure table patients (rappel)

```sql
CREATE TABLE patients (
    id INTEGER PRIMARY KEY,
    canontags TEXT, canonadjs TEXT,
    sexe TEXT, age DECIMAL(5,3), datenaissance DATE,
    prenom TEXT, nom TEXT,
    idportrait TEXT,          -- Clé pour le routage photofit
    oripathologies TEXT, pathologies TEXT
);
```

### D. CSS patient de référence (rappel)

```css
.patient-card.reference-patient {
    background: linear-gradient(135deg, #ffff00 0%, #ffeb3b 100%) !important;
    border: 3px solid #ffc107 !important;
    box-shadow: 0 4px 15px rgba(255, 235, 59, 0.5) !important;
}
```

<!-- /NO_SLIDE -->

---

**Document généré le 11/02/2026** | KITVIEW Search V5.2 | Intégration Photofit
