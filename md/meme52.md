# Techerche par similarité (Même X)

<!-- PRESENTATION_META
titre_court: "Recherche par Similarité"
sous_titre: "Fonctionnalité 'Même X que Patient' - Documentation technique V5.2"
duree_estimee: "30min"
niveau: "avancé"
audience: "Développeurs backend/frontend, architectes"
fichiers_concernes: "detmeme.py, trouveid.py, jsonsql.py, meme.js, main.js, web24.html, web24.css"
emoji_principal: "🔍"
-->

---

<!-- SLIDE
id: "vue-ensemble"
titre: "Vue d'ensemble fonctionnelle"
template: "titre-section"
emoji: "🎯"
timing: "3min"
transition: "slide"
-->

## 1. Vue d'ensemble fonctionnelle

<!-- KEY: La recherche par similarité permet de trouver des patients partageant des caractéristiques communes avec un patient de référence -->

### Objectif de la fonctionnalité

La fonctionnalité **"Même X que Patient"** permet aux praticiens de rechercher des patients présentant des caractéristiques identiques ou similaires à un patient de référence. C'est un outil puissant pour :

- **Études comparatives** : Comparer des cas cliniques similaires
- **Recherche de cas analogues** : Trouver des patients avec le même profil pathologique
- **Constitution de cohortes** : Regrouper des patients par caractéristiques communes

### Cas d'usage typiques en orthodontie

1. **Recherche par pathologie** : "Même béance antérieure que Guillaume Moulin" → Tous les patients avec la même pathologie
2. **Recherche par profil** : "Même sexe et même âge que Marie Durand" → Patients du même groupe démographique
3. **Recherche par portrait** : "Même portrait que id 123" → Patients avec un visage ressemblant (V5.2 : via analyse IA)

### Expérience utilisateur cible

L'utilisateur peut :

- **Cliquer directement** sur les attributs d'une fiche patient pour construire une recherche
- **Taper en langage naturel** une requête de similarité
- **Combiner plusieurs critères** pour affiner la recherche
- Le **patient de référence** est mis en évidence visuellement (fond jaune)
- Les **critères actifs** sont signalés en rouge

---

<!-- SLIDE
id: "syntaxes-supportees"
titre: "Syntaxes de requêtes"
template: "tableau"
emoji: "📝"
timing: "3min"
transition: "fade"
-->

## 2. Syntaxes supportées

<!-- KEY: Le parser accepte de nombreuses variantes syntaxiques en langage naturel français -->

<!-- QUESTION: Quelle syntaxe préférez-vous pour vos recherches quotidiennes ? -->

Le module `detmeme.py` (V1.0.7) analyse les requêtes en langage naturel et reconnaît les formats suivants :

<!-- TABLE
titre: "Formats de requêtes supportés"
colonnes_cles: "Format,Exemple"
style: "large"
-->

| Format              | Exemple                                              | Description                            |
| ------------------- | ---------------------------------------------------- | -------------------------------------- |
| Critère simple      | `même portrait que Guillaume Moulin`                 | Un seul critère, référence par nom     |
| Critères avec "et"  | `même portrait et même prénom que Guillaume Moulin`  | Plusieurs critères liés par "et même"  |
| Critères sans "et"  | `même portrait même prénom que Guillaume Moulin`     | Variante sans connecteur explicite     |
| Liste avec virgules | `même portrait, prénom, nom que Guillaume Moulin`    | Liste de critères séparés par virgules |
| Pluriel français    | `mêmes portrait, prénom et nom que Guillaume Moulin` | Support du pluriel "mêmes"             |
| Référence par ID    | `même portrait que id 123`                           | Référence par identifiant numérique    |
| Critère spécifique  | `même béance antérieure gauche que id 123`           | Pathologie complète comme critère      |

<!-- /TABLE -->

### Synonymes reconnus

Le fichier `communb.csv` (format vertical) définit les synonymes acceptés :

- **Pour "même"** : `identique`, `similaire`, `commun`, `semblable`, `pareil`...
- **Pour "que"** : `comme`, `de`, `du`...

### Chargement des synonymes

Le module supporte deux formats de configuration avec ordre de priorité :

1. **communb.csv** (nouveau format vertical) : `section;parametre;valeur;description`
2. **commun.csv** (ancien format horizontal) : colonnes `meme` et `que`
3. **Valeurs par défaut** : fallback si aucun fichier trouvé

---

<!-- SLIDE
id: "criteres-similarite"
titre: "Critères de similarité"
template: "tableau"
emoji: "📊"
timing: "4min"
transition: "slide"
-->

## 3. Critères de similarité disponibles

<!-- KEY: 7 critères de similarité : portrait, sexe, age (±3 ans), nom, prénom, tag (1 mot), pathologie (plusieurs mots) -->

<!-- TABLE
titre: "Mapping critères → colonnes SQL"
colonnes_cles: "Critère,Cible,Comportement"
style: "large"
-->

| Critère      | Cible SQL     | Comportement                                | Exemple SQL généré                                          |
| ------------ | ------------- | ------------------------------------------- | ----------------------------------------------------------- |
| `portrait`   | `idportrait`  | **Actuellement** : correspondance exacte ⚠️ | `WHERE p.idportrait = '12'`                                 |
| `sexe`       | `sexe`        | Correspondance exacte                       | `WHERE p.sexe = 'M'`                                        |
| `age`        | `age`         | Tolérance ±3 ans                            | `WHERE p.age BETWEEN 32 AND 38`                             |
| `nom`        | `nom`         | Insensible à la casse                       | `WHERE LOWER(p.nom) = LOWER('Dupont')`                      |
| `prenom`     | `prenom`      | Insensible à la casse                       | `WHERE LOWER(p.prenom) = LOWER('Jean')`                     |
| `tag`        | `pathologies` | 1 mot = tag seul                            | `JOIN ... WHERE pa.pathologie LIKE 'beance%'`               |
| `pathologie` | `pathologies` | Multi-mots = pathologie complète            | `JOIN ... WHERE pa.pathologie = 'beance anterieure gauche'` |

<!-- /TABLE -->

### Distinction tag vs pathologie

La distinction est automatique basée sur le nombre de mots :

<!-- CODE
langage: "python"
titre: "Logique de distinction tag/pathologie"
executable: "false"
-->

```python
# Dans detmeme.py, lignes 574-577
mots = contenu_norm.split()
if len(mots) == 1:
    cible_code = 'tag'      # Ex: "béance" → tag
else:
    cible_code = 'pathologie'  # Ex: "béance antérieure" → pathologie
```

<!-- /CODE -->

---

<!-- SLIDE
id: "critere-portrait-placeholder"
titre: "Critère Portrait - État actuel (Placeholder)"
template: "alerte"
emoji: "⚠️"
timing: "4min"
transition: "zoom"
-->

## 4. Critère "Même portrait" - État actuel

<!-- KEY: PLACEHOLDER ! La recherche portrait compare actuellement uniquement l'ID, pas la ressemblance visuelle -->

### ⚠️ Implémentation placeholder actuelle

**ATTENTION** : Le critère "même portrait" est actuellement un **placeholder** qui ne recherche PAS les visages ressemblants mais simplement les patients ayant **le même idportrait**.

<!-- CODE
langage: "sql"
titre: "SQL généré actuellement pour 'même portrait'"
executable: "false"
-->

```sql
-- COMPORTEMENT ACTUEL (placeholder)
-- Recherche uniquement les patients avec le MÊME idportrait
SELECT DISTINCT p.id, p.prenom, p.nom, ...
FROM patients p
WHERE p.idportrait = ? AND p.id != ?
-- Params: ['12', 2]

-- En pratique : retourne 0 résultat dans la plupart des cas
-- car chaque patient a généralement un idportrait unique
```

<!-- /CODE -->

### Pourquoi ce placeholder ?

L'implémentation d'une vraie recherche de visages similaires nécessite :

1. **Extraction de caractéristiques faciales** : Analyse des traits du visage
2. **Calcul d'embeddings** : Vecteurs représentant le visage
3. **Recherche vectorielle** : Trouver les vecteurs les plus proches
4. **Infrastructure** : Base de données vectorielle (sqlite-vec)

Cette fonctionnalité est prévue dans la **V5.2** grâce à l'API Photofit développée par Maxime.

---

<!-- SLIDE
id: "api-photofit"
titre: "API Photofit - Intégration prévue (V5.2)"
template: "titre-section"
emoji: "🤖"
timing: "5min"
transition: "slide"
-->

## 5. API Photofit - Recherche de portraits similaires (V5.2)

<!-- KEY: L'API de Maxime permettra une vraie recherche de ressemblance faciale via attributs + embeddings -->

### 5.1 Présentation de l'API

L'API Photofit, développée par **Maxime**, permet d'analyser des portraits et d'en extraire des vecteurs de caractéristiques pour la recherche de similitude.

**URL du service** : `https://demo.ia.orqual.info:506/photofit`

### 5.2 Endpoints disponibles

<!-- TABLE
titre: "Endpoints de l'API Photofit"
colonnes_cles: "Endpoint,Méthode,Description"
style: "large"
-->

| Endpoint                      | Méthode | Description                                    |
| ----------------------------- | ------- | ---------------------------------------------- |
| `/api/v1/attributes-names`    | GET     | Liste des 15 attributs faciaux                 |
| `/api/v1/extra-features`      | POST    | Analyse d'un portrait → attributs + embeddings |
| `/api/v1/hair-embedding-size` | GET     | Taille du vecteur cheveux (384)                |

<!-- /TABLE -->

### 5.3 Attributs faciaux détectés

L'API analyse **15 attributs** binaires (probabilité 0-1) :

<!-- TABLE
titre: "Attributs faciaux Photofit"
colonnes_cles: "Catégorie,Attributs"
style: "compact"
-->

| Catégorie            | Attributs                                                  |
| -------------------- | ---------------------------------------------------------- |
| **Genre/Âge**        | `male`, `young`                                            |
| **Accessoires**      | `eyeglasses`                                               |
| **Longueur cheveux** | `length_bald`, `length_short`, `length_mid`, `length_long` |
| **Couleur cheveux**  | `black_hair`, `blond_hair`, `brown_hair`, `gray_hair`      |
| **Style cheveux**    | `bangs`, `receding_hairline`, `straight_hair`, `wavy_hair` |

<!-- /TABLE -->

### 5.4 Vecteurs d'embeddings

L'API retourne trois types de vecteurs :

<!-- CODE
langage: "json"
titre: "Structure de réponse de l'API Photofit"
executable: "false"
-->

```json
{
    "attributes": [0.12, 0.98, 0.03, ...],   // 15 floats (probabilités attributs)
    "hair-embedding": [0.234, -0.567, ...],  // 384 floats (embedding cheveux)
    "face-embedding": [0.123, 0.456, ...]    // 128 floats (embedding facial)
}
```

<!-- /CODE -->

| Vecteur          | Dimension | Usage                                    |
| ---------------- | --------- | ---------------------------------------- |
| `attributes`     | 15        | Pré-filtrage rapide (binarisé à 0.5)     |
| `hair-embedding` | 384       | Similarité capillaire (distance cosinus) |
| `face-embedding` | 128       | Reconnaissance faciale (V3)              |

---

<!-- SLIDE
id: "strategie-recherche-portrait"
titre: "Stratégie de recherche portrait (V5.2)"
template: "schema"
emoji: "🎯"
timing: "4min"
transition: "fade"
-->

### 5.5 Stratégie de recherche portrait

<!-- KEY: Filtrage en 2 étapes : attributs binarisés puis k-NN sur embeddings cheveux -->

<!-- DIAGRAM
type: "flux"
titre: "Pipeline de recherche portrait V5.2"
legende: "Approche en entonnoir : attributs → embeddings"
-->

```
┌─────────────────────────────────────────────────────────────────────────┐
│                   RECHERCHE "MÊME PORTRAIT" V5.2                           │
└─────────────────────────────────────────────────────────────────────────┘

    Portrait du patient de référence
                    │
                    ▼
    ┌───────────────────────────────────────┐
    │           API Photofit                 │
    │    POST /api/v1/extra-features        │
    │  → attributes[15] + hair_emb[384]     │
    └───────────────────────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────────────┐
    │       ÉTAPE 1 : PRÉ-FILTRAGE          │
    │        (Attributs binarisés)           │
    │                                        │
    │  • Binarisation avec seuil 0.5        │
    │  • Filtrage SQL sur attributs          │
    │  • Ex: male=1 AND young=0 AND ...     │
    │                                        │
    │  → Réduit de ~25000 à ~500 candidats  │
    └───────────────────────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────────────┐
    │        ÉTAPE 2 : CLASSEMENT           │
    │       (Embeddings cheveux)             │
    │                                        │
    │  • Distance cosinus entre embeddings  │
    │  • Tri par proximité                   │
    │  • Sélection des k plus proches        │
    │                                        │
    │  → Retourne les 20 plus ressemblants  │
    └───────────────────────────────────────┘
                    │
                    ▼
              Résultats classés
         par score de ressemblance
```

<!-- /DIAGRAM -->

### 5.6 Roadmap d'implémentation

<!-- TABLE
titre: "Versions prévues pour le critère portrait"
colonnes_cles: "Version,Fonctionnalité"
style: "large"
-->

| Version         | Fonctionnalité             | Description                                    |
| --------------- | -------------------------- | ---------------------------------------------- |
| **V1** (actuel) | Placeholder                | Comparaison `idportrait` exact uniquement      |
| **V5.2.1**      | Attributs + Hair embedding | Filtrage attributs puis k-NN cheveux           |
| **V5.2.2**      | Pondération configurable   | Interface pour ajuster poids attributs/cheveux |
| **V5.2.3**      | Face embedding             | Ajout de l'embedding facial (128 dims)         |

<!-- /TABLE -->

---

<!-- SLIDE
id: "architecture-technique"
titre: "Architecture technique"
template: "titre-section"
emoji: "🏗️"
timing: "2min"
transition: "zoom"
-->

## 6. Architecture technique

<!-- KEY: Pipeline en 6 étapes : Question → detmeme → trouveid → jsonsql → lancesql → Résultats -->

---

<!-- SLIDE
id: "pipeline-traitement"
titre: "Pipeline de traitement"
template: "schema"
emoji: "🔄"
timing: "4min"
transition: "slide"
-->

### 6.1 Pipeline de traitement

<!-- DIAGRAM
type: "flux"
titre: "Pipeline complet de la recherche par similarité"
legende: "Chaque étape enrichit les données pour l'étape suivante"
-->

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         PIPELINE "MÊME X"                                │
└─────────────────────────────────────────────────────────────────────────┘

    Question utilisateur
    "même portrait et même âge que Guillaume Moulin"
                    │
                    ▼
    ┌───────────────────────────────────────┐
    │           detmeme.py V1.0.7           │
    │       (Parsing syntaxe "même")        │
    │  • Détecte les critères de similarité │
    │  • Extrait la référence (nom ou ID)   │
    │  • Support critères multiples V2.0    │
    └───────────────────────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────────────┐
    │  JSON intermédiaire avec reference:   │
    │  {                                    │
    │    "type": "nom",                     │
    │    "valeur": "Guillaume Moulin"       │
    │  }                                    │
    └───────────────────────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────────────┐
    │          trouveid.py V1.0.1           │
    │    (Résolution nom → ID + données)    │
    │  • Recherche dans la base patients    │
    │  • Récupère toutes les données        │
    └───────────────────────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────────────┐
    │   JSON enrichi avec reference_id +    │
    │   reference_patient (toutes données)  │
    └───────────────────────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────────────┐
    │          jsonsql.py V1.0.7            │
    │        (Génération SQL)               │
    │  • Construit les clauses WHERE        │
    │  • Gère les JOINs pour pathologies    │
    │  • Exclut le patient de référence     │
    └───────────────────────────────────────┘
                    │
                    ▼
    ┌───────────────────────────────────────┐
    │          lancesql.py                  │
    │        (Exécution SQL)                │
    └───────────────────────────────────────┘
                    │
                    ▼
              Résultats
      (patients similaires, sans le patient de référence)
```

<!-- /DIAGRAM -->

---

<!-- SLIDE
id: "format-json-intermediaire"
titre: "Format JSON intermédiaire"
template: "code"
emoji: "📄"
timing: "4min"
transition: "fade"
-->

### 6.2 Format JSON intermédiaire

<!-- KEY: Le JSON passe par 2 états : après detmeme (sans ID) puis après trouveid (avec toutes les données) -->

#### Sortie de detmeme.py (avant enrichissement)

<!-- CODE
langage: "json"
titre: "JSON produit par detmeme.py"
executable: "false"
-->

```json
{
    "criteres": [
        {
            "type": "meme",
            "detecte": "même portrait",
            "cible": "portrait",
            "label": "Même portrait",
            "valeur": null
        },
        {
            "type": "meme",
            "detecte": "même bruxisme nocturne",
            "cible": "pathologie",
            "label": "Même pathologie",
            "valeur": "bruxisme nocturne"
        }
    ],
    "reference": {
        "type": "nom",
        "valeur": "Guillaume Moulin",
        "id": null
    },
    "residu": ""
}
```

<!-- /CODE -->

#### Sortie de trouveid.py (après enrichissement)

<!-- CODE
langage: "json"
titre: "JSON enrichi par trouveid.py"
executable: "false"
-->

```json
{
    "criteres": [
        {
            "type": "meme",
            "detecte": "même portrait",
            "cible": "portrait",
            "label": "Même portrait",
            "valeur": null,
            "reference_id": 2,
            "reference_patient": {
                "id": 2,
                "prenom": "Guillaume",
                "nom": "Moulin",
                "sexe": "M",
                "age": 19,
                "canontags": "beance,bruxisme,diabete",
                "canonadjs": "anterieure|gauche|moderee",
                "idportrait": "2",
                "oripathologies": "Béance Antérieure Gauche Modérée,Bruxisme,Diabète"
            }
        }
    ],
    "reference": {
        "type": "nom",
        "valeur": "Guillaume Moulin",
        "id": null
    }
}
```

<!-- /CODE -->

---

<!-- SLIDE
id: "generation-sql"
titre: "Génération SQL"
template: "code"
emoji: "🗃️"
timing: "5min"
transition: "slide"
-->

### 6.3 Génération SQL

<!-- KEY: jsonsql.py génère des clauses SQL adaptées à chaque type de critère, avec exclusion automatique du patient de référence -->

#### Exemples de SQL généré par critère

<!-- CODE
langage: "sql"
titre: "SQL pour 'même sexe'"
executable: "false"
-->

```sql
-- Critère: même sexe que Guillaume Moulin (ID 2, sexe='M')
SELECT DISTINCT p.id, p.prenom, p.nom, p.sexe, p.age, 
       p.idportrait, p.oripathologies, p.canontags, p.canonadjs
FROM patients p
WHERE (p.sexe = ? AND p.id != ?)
ORDER BY p.id
-- Params: ['M', 2]
```

<!-- /CODE -->

<!-- CODE
langage: "sql"
titre: "SQL pour 'même âge' (tolérance ±3 ans)"
executable: "false"
-->

```sql
-- Critère: même âge que Guillaume Moulin (ID 2, age=19)
-- Tolérance: TOLERANCE_AGE_DEFAUT = 3 (jsonsql.py ligne 94)
SELECT DISTINCT p.id, p.prenom, p.nom, p.sexe, p.age, ...
FROM patients p
WHERE (p.age BETWEEN ? AND ? AND p.id != ?)
ORDER BY p.id
-- Params: [16, 22, 2]
```

<!-- /CODE -->

<!-- CODE
langage: "sql"
titre: "SQL pour 'même pathologie' (avec JOIN)"
executable: "false"
-->

```sql
-- Critère: même pathologie (béance antérieure gauche modérée)
SELECT DISTINCT p.id, p.prenom, p.nom, ...
FROM patients p
    JOIN patients_pathologies pp1 ON p.id = pp1.patient_id
    JOIN pathologies pa1 ON pp1.pathologie_id = pa1.id
WHERE (pa1.pathologie = ? AND p.id != ?)
ORDER BY p.id
-- Params: ['beance anterieure gauche moderee', 2]
```

<!-- /CODE -->

<!-- CODE
langage: "sql"
titre: "SQL pour 'même portrait' (PLACEHOLDER actuel)"
executable: "false"
-->

```sql
-- PLACEHOLDER : Comparaison idportrait exact (sera remplacé en V5.2)
SELECT DISTINCT p.id, p.prenom, p.nom, ...
FROM patients p
WHERE (p.idportrait = ? AND p.id != ?)
ORDER BY p.id
-- Params: ['12', 2]
```

<!-- /CODE -->

---

<!-- SLIDE
id: "interface-utilisateur"
titre: "Interface utilisateur"
template: "titre-section"
emoji: "🖥️"
timing: "2min"
transition: "zoom"
-->

## 7. Interface utilisateur

<!-- KEY: L'interface permet de construire visuellement une recherche par clics successifs sur les attributs patients -->

---

<!-- SLIDE
id: "affichage-fiches"
titre: "Affichage des fiches patients"
template: "2colonnes"
emoji: "🎴"
timing: "3min"
transition: "slide"
-->

### 7.1 Affichage des fiches patients

<!-- KEY: Les badges utilisent deux styles : light (fond clair) pour Prénom/Sexe, dark (fond sombre) pour Nom/Âge -->

#### Structure des badges

| Élément             | Style CSS           | Apparence                       |
| ------------------- | ------------------- | ------------------------------- |
| Prénom              | `.info-badge-light` | Noir sur fond clair (#e8eaf6)   |
| Nom                 | `.info-badge-dark`  | Blanc sur fond sombre (#37474f) |
| Sexe                | `.info-badge-light` | Noir sur fond clair             |
| Âge                 | `.info-badge-dark`  | Blanc sur fond sombre           |
| Tag seul            | `.patho-tag-dark`   | Blanc sur fond sombre           |
| Pathologie complète | `.patho-full-light` | Noir sur fond clair             |

#### Groupement des pathologies

Les pathologies sont groupées par **tag parent** :

```
Béance (tag)
├── Béance Antérieure Gauche (pathologie)
└── Béance Latérale Modérée (pathologie)

Bruxisme (tag seul, sans pathologies dérivées)
```

---

<!-- SLIDE
id: "etats-visuels"
titre: "États visuels"
template: "tableau"
emoji: "🎨"
timing: "3min"
transition: "fade"
-->

### 7.2 États visuels

<!-- KEY: Fond jaune = patient de référence, bordure rouge = critère actif, cursor pointer = élément cliquable -->

<!-- TABLE
titre: "États visuels des éléments"
colonnes_cles: "État,Classe CSS,Style"
style: "large"
-->

| État                 | Classe CSS                      | Style appliqué                               |
| -------------------- | ------------------------------- | -------------------------------------------- |
| Patient de référence | `.reference-patient`            | Fond `#fff9c4` (jaune), bordure `#ffc107`    |
| Critère actif        | `.meme-active`                  | Texte `#d32f2f` (rouge), `font-weight: bold` |
| Tag actif            | `.patho-tag-dark.meme-active`   | Fond `#d32f2f` (rouge)                       |
| Pathologie active    | `.patho-full-light.meme-active` | Fond `#ffebee`, bordure rouge                |
| Élément cliquable    | `.meme-clickable`               | `cursor: pointer`, hover avec scale(1.03)    |
| Portrait cliquable   | `.meme-portrait-clickable`      | Bordure orange au hover                      |
| Portrait référence   | `.meme-portrait-reference`      | Bordure rouge permanente                     |
| Élément désactivé    | `.meme-disabled`                | `opacity: 0.5`, `cursor: not-allowed`        |

<!-- /TABLE -->

#### Mode sombre

En mode sombre (`[data-theme="dark"]`), le patient de référence utilise :

```css
[data-theme="dark"] .reference-patient {
    background-color: rgba(255, 193, 7, 0.15) !important;
    border-color: #ffc107 !important;
}
```

---

<!-- SLIDE
id: "logique-javascript"
titre: "Logique d'interaction JavaScript"
template: "code"
emoji: "⚙️"
timing: "5min"
transition: "slide"
-->

### 7.3 Logique d'interaction JavaScript (meme.js)

<!-- KEY: Code extrait dans meme.js : memeState gère l'état, handleMemeClick traite les clics -->

#### Architecture modulaire

Depuis la V2.4.0, le code JavaScript "même" a été extrait dans un module dédié :

```javascript
// main.js - ligne 44
// Modules externes requis (charger AVANT main.js) :
// - utils.js, voice.js, illustrations.js, search.js, i18n.js, meme.js
```

#### Objet memeState (gestion de l'état)

<!-- CODE
langage: "javascript"
titre: "Structure de memeState (meme.js)"
executable: "false"
-->

```javascript
const memeState = {
    referenceId: null,           // ID du patient de référence
    referenceName: '',           // Nom complet pour affichage
    criteres: [],                // [{type: 'portrait', value: null}, ...]

    reset() { /* Réinitialise tout */ },
    hasCritere(type, value = null) { /* Vérifie si critère actif */ },
    addCritere(type, value = null) { /* Ajoute un critère */ },
    removeCritere(type, value = null) { /* Retire un critère */ },
    toggleCritere(type, value = null) { /* Ajoute ou retire */ },
    isReference(patientId) { /* Vérifie si c'est la référence */ },
    hasReference() { /* Vérifie s'il y a une référence */ }
};
```

<!-- /CODE -->

#### Fonctions d'interaction (main.js)

Les fonctions suivantes dans main.js orchestrent les clics :

<!-- CODE
langage: "javascript"
titre: "Fonctions clés dans main.js"
executable: "false"
-->

```javascript
// Ligne 2507-2578 : Rendu des tags/pathologies avec gestion meme
const tagClickable = isMemeClickable(patientId, 'tag');
const tagActive = isMemeActive(patientId, 'tag', tag);

// Ligne 2636-2641 : Portrait cliquable pour "même portrait"
makePortraitMemeClickable(photoContainer, patientId, patientFullName);

// Ligne 2691-2724 : Badges prénom/nom/sexe/âge cliquables
makeMemeClickable(prenomSpan, patientId, patientFullName, 'prenom', null, 'Même prénom');
makeMemeClickable(nomSpan, patientId, patientFullName, 'nom', null, 'Même nom');
makeMemeClickable(sexeSpan, patientId, patientFullName, 'sexe', null, 'Même sexe');
makeMemeClickable(ageSpan, patientId, patientFullName, 'age', null, 'Même âge (±3 ans)');
```

<!-- /CODE -->

#### Fonction handleMemeClick (traitement des clics)

<!-- CODE
langage: "javascript"
titre: "Logique de handleMemeClick"
executable: "false"
-->

```javascript
function handleMemeClick(patientId, patientName, critereType, critereValue = null) {
    // CAS 1 : Clic sur un AUTRE patient → changement de référence
    if (memeState.hasReference() && !memeState.isReference(patientId)) {
        memeState.reset();
        memeState.referenceId = patientId;
        memeState.referenceName = patientName;
        memeState.addCritere(critereType, critereValue);
    }
    // CAS 2 : Premier clic ou même patient → toggle critère
    else {
        if (!memeState.hasReference()) {
            memeState.referenceId = patientId;
            memeState.referenceName = patientName;
        }

        // Désélection automatique du tag si pathologie sélectionnée
        if (critereType === 'pathologie' && critereValue) {
            const tag = critereValue.split(/\s+/)[0];
            if (memeState.hasCritere('tag', tag)) {
                memeState.removeCritere('tag', tag);
            }
        }

        memeState.toggleCritere(critereType, critereValue);
    }

    // Si plus de critères → retour à la recherche initiale
    if (memeState.criteres.length === 0) {
        memeState.reset();
        searchPatients(lastSearchQuery);
        return;
    }

    // Génère et exécute la nouvelle recherche
    const questions = generateMemeQuestion();
    searchPatients(questions.technical);
}
```

<!-- /CODE -->

---

<!-- SLIDE
id: "ajout-suppression-criteres"
titre: "Ajout et suppression de critères"
template: "code"
emoji: "➕➖"
timing: "4min"
transition: "fade"
-->

### 7.4 Ajout et suppression de critères

<!-- KEY: Les critères sont gérés via memeState dans meme.js, avec toggle automatique et désélection intelligente -->

#### Mécanisme de toggle

Le clic sur un élément déjà actif le **désélectionne** :

<!-- CODE
langage: "javascript"
titre: "Logique toggle dans memeState"
executable: "false"
-->

```javascript
// Dans memeState (meme.js)
toggleCritere(type, value = null) {
    if (this.hasCritere(type, value)) {
        this.removeCritere(type, value);  // Déjà actif → retirer
    } else {
        this.addCritere(type, value);      // Non actif → ajouter
    }
}
```

<!-- /CODE -->

#### Désélection automatique tag/pathologie

Quand l'utilisateur sélectionne une **pathologie complète**, le **tag parent** est automatiquement désélectionné pour éviter les doublons :

<!-- CODE
langage: "javascript"
titre: "Désélection automatique"
executable: "false"
-->

```javascript
// Dans handleMemeClick
if (critereType === 'pathologie' && critereValue) {
    const tag = critereValue.split(/\s+/)[0];  // "béance antérieure" → "béance"
    if (memeState.hasCritere('tag', tag)) {
        memeState.removeCritere('tag', tag);   // Retire le tag parent
    }
}
```

<!-- /CODE -->

#### Retour à la recherche initiale

Quand **tous les critères** sont retirés, le système revient automatiquement à la recherche d'origine :

```javascript
if (memeState.criteres.length === 0) {
    memeState.reset();
    searchPatients(lastSearchQuery);  // Relance la recherche initiale
    return;
}
```

---

<!-- SLIDE
id: "fichiers-impliques"
titre: "Fichiers impliqués"
template: "tableau"
emoji: "📁"
timing: "2min"
transition: "fade"
-->

## 8. Fichiers impliqués

<!-- KEY: 6 fichiers principaux : 3 backend (parsing, résolution, SQL), 3 frontend (JS module, JS principal, CSS) -->

<!-- TABLE
titre: "Récapitulatif des fichiers"
colonnes_cles: "Fichier,Version,Rôle"
style: "large"
-->

| Fichier       | Version | Rôle                          | Fonctions clés                          |
| ------------- | ------- | ----------------------------- | --------------------------------------- |
| `detmeme.py`  | V1.0.7  | Parser syntaxe "même X que"   | `detecter_meme()`, `identifier_meme()`  |
| `trouveid.py` | V1.0.1  | Résolution nom → ID + données | `enrichir_avec_reference()`             |
| `jsonsql.py`  | V1.0.7  | Génération SQL                | `_generer_clause_meme()`                |
| `meme.js`     | V2.0.0  | État et logique JS "même"     | `memeState`, `handleMemeClick()`        |
| `main.js`     | V2.4.0  | Rendu patients + clics        | `makeMemeClickable()`, `isMemeActive()` |
| `web24.css`   | V1.0.0  | Styles visuels                | `.meme-*`, `.reference-patient`         |

<!-- /TABLE -->

### Dépendances

```
communb.csv (refs/)          ← Format vertical section;parametre;valeur
    └── Synonymes "même" et "que"

commun.csv (refs/)           ← Format horizontal (fallback)
    └── Synonymes "même" et "que"

standardise.py
    └── Normalisation texte (accents, casse)
```

---

<!-- SLIDE
id: "tests-validation"
titre: "Tests et validation"
template: "synthese"
emoji: "✅"
timing: "3min"
transition: "slide"
-->

## 9. Tests et validation

<!-- KEY: Tests batch via fichiers testsmemein.csv → testsmemeout.csv, validation manuelle de l'interface -->

### Fichiers de test

Le module `detmeme.py` supporte l'exécution batch :

```bash
python detmeme.py tests/testsmemein.csv --verbose
```

Génère automatiquement `tests/testsmemeout.csv` avec les colonnes :

- `question` : Question d'entrée
- `nb_criteres` : Nombre de critères détectés
- `cibles` : Liste des cibles (portrait, sexe, age...)
- `valeurs` : Valeurs spécifiques (tags/pathologies)
- `labels` : Labels affichables
- `reference` : Référence extraite (nom ou id:N)
- `residu` : Texte non parsé

### Cas de tests critiques

<!-- TABLE
titre: "Cas de tests essentiels"
colonnes_cles: "Cas,Question,Attendu"
style: "compact"
-->

| #   | Question test                                    | Résultat attendu                            |
| --- | ------------------------------------------------ | ------------------------------------------- |
| 1   | `même portrait que Guillaume Moulin`             | cible=portrait, ref=Guillaume Moulin        |
| 2   | `même âge et même sexe que id 123`               | cibles=[age,sexe], ref=id:123               |
| 3   | `mêmes portrait, nom, prénom que Jean Dupont`    | cibles=[portrait,nom,prenom]                |
| 4   | `même béance antérieure que Marie`               | cible=pathologie, valeur=béance antérieure  |
| 5   | `même bruxisme que Paul`                         | cible=tag, valeur=bruxisme                  |
| 6   | `même portrait et même âge que Guillaume Moulin` | cibles=[portrait,age], ref=Guillaume Moulin |

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

## 10. Limitations connues et évolutions futures

<!-- KEY: Limitations actuelles : placeholder portrait, 1 seul patient de référence, pas de combinaisons OR -->

### Limitations actuelles (V5.1)

- **⚠️ Portrait = placeholder** : Compare uniquement l'idportrait, pas la ressemblance
- **Patient de référence unique** : Impossible de comparer à plusieurs patients simultanément
- **Critères en AND** : Tous les critères sont combinés en ET logique (pas de OU)
- **Première pathologie** : Pour "même pathologie", seule la première pathologie du patient de référence est utilisée
- **Recherche séquentielle** : La résolution du nom parcourt tous les patients

### Évolutions prévues

| Version    | Fonctionnalité            | Description                                       |
| ---------- | ------------------------- | ------------------------------------------------- |
| **V5.2.1** | 🖼️ Recherche portrait IA | Intégration API Photofit (Maxime)                 |
| **V5.2.2** | ⚖️ Pondération            | Interface pour ajuster poids attributs/embeddings |
| **V5.2.3** | 👤 Face embedding         | Ajout reconnaissance faciale                      |
| V7         | Multiple références       | "Même X que Patient1 ou Patient2"                 |
| V7         | Critères OR               | "Même âge ou même sexe que..."                    |

### Améliorations UX envisagées

- **Auto-complétion** des noms de patients dans la barre de recherche
- **Preview** du patient de référence au survol
- **Score de ressemblance** affiché pour le critère portrait
- **Export** de la cohorte trouvée en CSV

---

<!-- SLIDE
id: "annexes"
titre: "Annexes techniques"
template: "titre-section"
emoji: "📎"
timing: "1min"
transition: "fade"
-->

## Annexes

<!-- NO_SLIDE -->

### A. Constantes importantes

```python
# jsonsql.py - Tolérance pour "même âge"
TOLERANCE_AGE_DEFAUT = 3  # ±3 ans

# detmeme.py - Cibles reconnues
CIBLES_MEME = {
    'tag': ('tag', 'Même tag'),
    'tags': ('tag', 'Même tag'),
    'pathologie': ('pathologie', 'Même pathologie'),
    'pathologies': ('pathologie', 'Même pathologie'),
    'portrait': ('portrait', 'Même portrait'),
    'portraits': ('portrait', 'Même portrait'),
    'photo': ('portrait', 'Même photo'),
    'photos': ('portrait', 'Même photo'),
    'sexe': ('sexe', 'Même sexe'),
    'genre': ('sexe', 'Même genre'),
    'age': ('age', 'Même âge'),
    'nom': ('nom', 'Même nom'),
    'prenom': ('prenom', 'Même prénom'),
}

# detmeme.py - Synonymes par défaut
SYNONYMES_MEME_DEFAUT = ['meme', 'memes', 'identique', 'identiques', 
                         'similaire', 'similaires', 'commun', 'communs', 
                         'semblable', 'semblables']
SYNONYMES_QUE_DEFAUT = ['que', 'comme', 'de', 'du']
```

### B. Couleurs CSS

```css
/* Patient de référence */
--meme-reference-bg: #fff9c4;
--meme-reference-border: #ffc107;

/* Critère actif */
--meme-active-color: #d32f2f;
--meme-active-bg: #ffebee;

/* Hover sur élément cliquable */
--meme-hover-bg: rgba(59, 157, 216, 0.28);
```

### C. API Photofit - Référence rapide

```
Base URL: https://demo.ia.orqual.info:506/photofit
Swagger:  https://demo.ia.orqual.info:506/photofit/docs

GET  /api/v1/attributes-names    → Liste des 15 attributs
GET  /api/v1/hair-embedding-size → Taille embedding (384)
POST /api/v1/extra-features      → Analyse portrait (img en POST)
     → Retourne: attributes[15], hair-embedding[384], face-embedding[128]
```

<!-- /NO_SLIDE -->

---

**Document généré le 30/01/2026** | KITVIEW Search V5.2 | Fonctionnalité "Même X"
