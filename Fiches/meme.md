# Système de recherche par similarité (Même X)

<!-- PRESENTATION_META
titre_court: "Recherche par Similarité"
sous_titre: "Fonctionnalité 'Même X que Patient' - Documentation technique V5"
duree_estimee: "25min"
niveau: "avancé"
audience: "Développeurs backend/frontend, architectes"
fichiers_concernes: "detmeme.py, trouveid.py, jsonsql.py, web24.html, web24.css"
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
3. **Recherche par portrait** : "Même portrait que id 123" → Patients avec la même photo de profil/classification

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

Le module `detmeme.py` (V1.0.3) analyse les requêtes en langage naturel et reconnaît les formats suivants :

<!-- TABLE
titre: "Formats de requêtes supportés"
colonnes_cles: "Format,Exemple"
style: "large"
-->

| Format | Exemple | Description |
|--------|---------|-------------|
| Critère simple | `même portrait que Guillaume Moulin` | Un seul critère, référence par nom |
| Critères avec "et" | `même portrait et même prénom que Guillaume Moulin` | Plusieurs critères liés par "et même" |
| Critères sans "et" | `même portrait même prénom que Guillaume Moulin` | Variante sans connecteur explicite |
| Liste avec virgules | `même portrait, prénom, nom que Guillaume Moulin` | Liste de critères séparés par virgules |
| Pluriel français | `mêmes portrait, prénom et nom que Guillaume Moulin` | Support du pluriel "mêmes" |
| Référence par ID | `même portrait que id 123` | Référence par identifiant numérique |
| Critère spécifique | `même béance antérieure gauche que id 123` | Pathologie complète comme critère |

<!-- /TABLE -->

### Synonymes reconnus

Le fichier `commun.csv` définit les synonymes acceptés :

- **Pour "même"** : `identique`, `similaire`, `commun`, `semblable`, `pareil`...
- **Pour "que"** : `comme`, `de`, `du`...

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

| Critère | Cible SQL | Comportement | Exemple SQL généré |
|---------|-----------|--------------|-------------------|
| `portrait` | `idportrait` | Correspondance exacte | `WHERE p.idportrait = '12'` |
| `sexe` | `sexe` | Correspondance exacte | `WHERE p.sexe = 'M'` |
| `age` | `age` | Tolérance ±3 ans | `WHERE p.age BETWEEN 32 AND 38` |
| `nom` | `nom` | Insensible à la casse | `WHERE LOWER(p.nom) = LOWER('Dupont')` |
| `prenom` | `prenom` | Insensible à la casse | `WHERE LOWER(p.prenom) = LOWER('Jean')` |
| `tag` | `pathologies` | 1 mot = tag seul | `JOIN ... WHERE pa.pathologie LIKE 'beance%'` |
| `pathologie` | `pathologies` | Multi-mots = pathologie complète | `JOIN ... WHERE pa.pathologie = 'beance anterieure gauche'` |

<!-- /TABLE -->

### Distinction tag vs pathologie

La distinction est automatique basée sur le nombre de mots :

<!-- CODE
langage: "python"
titre: "Logique de distinction tag/pathologie"
executable: "false"
-->

```python
# Dans detmeme.py, ligne 428-433
mots = elem_norm.split()
if len(mots) == 1:
    cible_code = 'tag'      # Ex: "béance" → tag
    label = f'Même {elem_norm}'
else:
    cible_code = 'pathologie'  # Ex: "béance antérieure" → pathologie
    label = f'Même {elem_norm}'
```

<!-- /CODE -->

---

<!-- SLIDE
id: "architecture-technique"
titre: "Architecture technique"
template: "titre-section"
emoji: "🏗️"
timing: "2min"
transition: "zoom"
-->

## 4. Architecture technique

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

### 4.1 Pipeline de traitement

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
    │           detmeme.py V1.0.3           │
    │       (Parsing syntaxe "même")        │
    │  • Détecte les critères de similarité │
    │  • Extrait la référence (nom ou ID)   │
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

### 4.2 Format JSON intermédiaire

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

### 4.3 Génération SQL

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
titre: "SQL pour 'même tag' (LIKE avec préfixe)"
executable: "false"
-->

```sql
-- Critère: même tag 'béance' (recherche toutes pathologies commençant par ce tag)
SELECT DISTINCT p.id, p.prenom, p.nom, ...
FROM patients p
    JOIN patients_pathologies pp1 ON p.id = pp1.patient_id
    JOIN pathologies pa1 ON pp1.pathologie_id = pa1.id
WHERE (pa1.pathologie LIKE ? AND p.id != ?)
ORDER BY p.id
-- Params: ['beance%', 2]
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

## 5. Interface utilisateur (web24)

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

### 5.1 Affichage des fiches patients

<!-- KEY: Les badges utilisent deux styles : light (fond clair) pour Prénom/Sexe, dark (fond sombre) pour Nom/Âge -->

#### Structure des badges

| Élément | Style CSS | Apparence |
|---------|-----------|-----------|
| Prénom | `.info-badge-light` | Noir sur fond clair (#e8eaf6) |
| Nom | `.info-badge-dark` | Blanc sur fond sombre (#37474f) |
| Sexe | `.info-badge-light` | Noir sur fond clair |
| Âge | `.info-badge-dark` | Blanc sur fond sombre |
| Tag seul | `.patho-tag-dark` | Blanc sur fond sombre |
| Pathologie complète | `.patho-full-light` | Noir sur fond clair |

#### Groupement des pathologies

Les pathologies sont groupées par **tag parent** :

```
Béance (tag)
├── Béance Antérieure Gauche (pathologie)
└── Béance Latérale Modérée (pathologie)

Bruxisme (tag seul, sans pathologies dérivées)
```

#### Position de l'ID patient

L'ID est affiché en **haut à gauche** de la fiche via `.patient-id-badge` :

```css
.patient-id-badge {
    position: absolute;
    top: 8px;
    left: 8px;
    font-size: 11px;
    color: var(--text-secondary);
    opacity: 0.6;
    font-family: monospace;
}
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

### 5.2 États visuels

<!-- KEY: Fond jaune = patient de référence, bordure rouge = critère actif, cursor pointer = élément cliquable -->

<!-- TABLE
titre: "États visuels des éléments"
colonnes_cles: "État,Classe CSS,Style"
style: "large"
-->

| État | Classe CSS | Style appliqué |
|------|------------|----------------|
| Patient de référence | `.meme-reference-card` | Fond `#fff9c4` (jaune), bordure `#ffc107` |
| Critère actif | `.meme-active` | Texte `#d32f2f` (rouge), `font-weight: bold` |
| Tag actif | `.patho-tag-dark.meme-active` | Fond `#d32f2f` (rouge) |
| Pathologie active | `.patho-full-light.meme-active` | Fond `#ffebee`, bordure rouge |
| Élément cliquable | `.meme-clickable` | `cursor: pointer`, hover avec scale(1.03) |
| Portrait cliquable | `.meme-portrait-clickable` | Bordure orange au hover |
| Portrait référence | `.meme-portrait-reference` | Bordure rouge permanente |
| Élément désactivé | `.meme-disabled` | `opacity: 0.5`, `cursor: not-allowed` |

<!-- /TABLE -->

#### Mode sombre

En mode sombre (`[data-theme="dark"]`), le patient de référence utilise :

```css
[data-theme="dark"] .meme-reference-card {
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

### 5.3 Logique d'interaction JavaScript

<!-- KEY: memeState gère l'état, handleMemeClick traite les clics, generateMemeQuestion construit la requête -->

#### Objet memeState (gestion de l'état)

<!-- CODE
langage: "javascript"
titre: "Structure de memeState (web24.html lignes 4490-4552)"
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

#### Fonction handleMemeClick (traitement des clics)

<!-- CODE
langage: "javascript"
titre: "Logique de handleMemeClick (web24.html lignes 4598-4666)"
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

#### Fonction generateMemeQuestion (construction de la requête)

<!-- CODE
langage: "javascript"
titre: "Construction de la question (web24.html lignes 4559-4583)"
executable: "false"
-->

```javascript
function generateMemeQuestion() {
    if (!memeState.referenceId || memeState.criteres.length === 0) {
        return { display: '', technical: '' };
    }
    
    // Construire "même X et même Y et même Z"
    const parts = memeState.criteres.map(c => {
        if (c.value) {
            return `même ${c.value}`;        // "même béance antérieure"
        } else {
            return `même ${c.type}`;         // "même portrait"
        }
    });
    
    const criteresStr = parts.join(' et ');
    
    return {
        display: `${criteresStr} que ${memeState.referenceName}`,
        technical: `${criteresStr} que ${memeState.referenceName}`
    };
}
```

<!-- /CODE -->

---

<!-- SLIDE
id: "fichiers-impliques"
titre: "Fichiers impliqués"
template: "tableau"
emoji: "📁"
timing: "2min"
transition: "fade"
-->

## 6. Fichiers impliqués

<!-- KEY: 5 fichiers principaux : 2 backend (parsing, SQL), 2 frontend (HTML, CSS), 1 résolution d'identité -->

<!-- TABLE
titre: "Récapitulatif des fichiers"
colonnes_cles: "Fichier,Version,Rôle"
style: "large"
-->

| Fichier | Version | Rôle | Lignes clés |
|---------|---------|------|-------------|
| `detmeme.py` | V1.0.3 | Parser syntaxe "même X que" | `detecter_meme()` L272-541 |
| `trouveid.py` | V1.0.1 | Résolution nom → ID + données patient | `enrichir_avec_reference()` L127-185 |
| `jsonsql.py` | V1.0.7 | Génération SQL avec critères "meme" | `_generer_clause_meme()` L179-343 |
| `web24.html` | V1.1.1 | Interface utilisateur + JS interactif | `memeState` L4490-4552, `handleMemeClick` L4598-4666 |
| `web24.css` | V1.0.0 | Styles visuels "même" | `.meme-*` L3247-3375, `.meme-reference-card` L1336-1345 |

<!-- /TABLE -->

### Dépendances

```
commun.csv (refs/)
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

## 7. Tests et validation

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

| # | Question test | Résultat attendu |
|---|---------------|------------------|
| 1 | `même portrait que Guillaume Moulin` | cible=portrait, ref=Guillaume Moulin |
| 2 | `même âge et même sexe que id 123` | cibles=[age,sexe], ref=id:123 |
| 3 | `mêmes portrait, nom, prénom que Jean Dupont` | cibles=[portrait,nom,prenom] |
| 4 | `même béance antérieure que Marie` | cible=pathologie, valeur=béance antérieure |
| 5 | `même bruxisme que Paul` | cible=tag, valeur=bruxisme |

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

## 8. Limitations connues et évolutions futures

<!-- KEY: Limitations actuelles : 1 seul patient de référence, pas de combinaisons OR, pas d'authentification API -->

### Limitations actuelles (V5.1)

- **Patient de référence unique** : Impossible de comparer à plusieurs patients simultanément
- **Critères en AND** : Tous les critères sont combinés en ET logique (pas de OU)
- **Première pathologie** : Pour "même pathologie", seule la première pathologie du patient de référence est utilisée
- **Recherche séquentielle** : La résolution du nom parcourt tous les patients

### Évolutions prévues (V5.2+)

| Version | Fonctionnalité | Description |
|---------|----------------|-------------|
| V5.2 | Multiple références | "Même X que Patient1 ou Patient2" |
| V5.2 | API authentifiée | Token JWT pour accès externe |
| V5.3 | Critères OR | "Même âge ou même sexe que..." |
| V5.3 | Historique de recherche | Mémorisation des dernières recherches "même" |

### Améliorations UX envisagées

- **Auto-complétion** des noms de patients dans la barre de recherche
- **Preview** du patient de référence au survol
- **Raccourcis clavier** pour les critères fréquents
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
    'pathologie': ('pathologie', 'Même pathologie'),
    'portrait': ('portrait', 'Même portrait'),
    'sexe': ('sexe', 'Même sexe'),
    'age': ('age', 'Même âge'),
    'nom': ('nom', 'Même nom'),
    'prenom': ('prenom', 'Même prénom'),
}
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

<!-- /NO_SLIDE -->

---

**Document généré le 21/01/2026** | KITVIEW Search V5 | Fonctionnalité "Même X"
