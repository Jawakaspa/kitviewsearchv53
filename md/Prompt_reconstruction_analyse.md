# Prompt_reconstruction_analyse.md

## Objectif

Créer un système complet d'analyse des logs de recherche pour Kitview Search :
- `analyse.html` V2.0.0 - Dashboard web
- `analyse.py` V2.0.0 - Backend API 
- Structure `logrecherche.csv`

---

## 1. Structure logrecherche.csv (24 colonnes, séparateur `;`)

### En-tête
```
module;timestamp;temps_ms;languesaisie;langueutilisee;modulelangue;questionoriginale;question;filtres;sql;tri;base;mode;moteur;nb_patients;pathologies;ages;residu;erreur;session_id;ip_utilisateur;rating;type_probleme;commentaire
```

### Format de date CRITIQUE
**timestamp** : Format français `DD/MM/YYYY HH:MM` (ex: `01/12/2025 08:35`)

### Modes valides
`standard`, `ia`, `standarddeepl`, `iadeepl`, `standardia`

### Moteurs IA (colonne moteur)
`sonnet`, `gpt4o`, `gpt4omini`, `deepseekr1`, `deepseekv3`, `gemini25flash`, `gemini15pro`, `mistrallarge`, `mistralsmall`, `llama33`, `haiku`, `command`

---

## 2. Backend analyse.py V2.0.0

### Endpoints requis

#### GET /analyse/stats
```json
{
  "total_recherches": 3105,
  "periode": {"debut": "01/12/2025 00:35", "fin": "05/01/2026 17:00"},
  "ratings": {"positif": 503, "negatif": 1001, "sans": 1601},
  "taux_satisfaction": 33.4,
  "modes": {"standard": 920, "ia": 776, "standardia": 1407},
  "moteurs": {"sonnet": 200, "gpt4o": 150, ...},
  "top_pathologies": [{"pathologie": "bruxisme", "count": 450}, ...],
  "types_problemes": [{"type": "Trop de patients", "count": 120}, ...],
  "termes_non_reconnus": [{"terme": "xyz", "count": 50}, ...],
  "temps_moyen_ms": 1397,
  "erreurs": 19
}
```

#### GET /analyse/recherches
Paramètres : `offset`, `limit`, `q`, `rating`, `mode`, `date_debut`, `date_fin`, `type_probleme`, `erreur`

**CRITIQUE** : Retourner TOUTES les colonnes dans chaque recherche (pas seulement un sous-ensemble).

#### GET /analyse/recherche/{session_id}
Détail complet d'une recherche.

#### GET /analyse/export
Export CSV filtré.

### Lecture CSV
**OBLIGATOIRE** : Utiliser `csv.DictReader` pour lire par NOM de colonne, JAMAIS par index.

---

## 3. Dashboard analyse.html V2.0.0

### 3.1 Parsing des dates françaises (CRITIQUE)

```javascript
// Convertit "DD/MM/YYYY HH:MM" en objet Date
function parseDateFR(str) {
    if (!str) return null;
    const match = str.match(/^(\d{2})\/(\d{2})\/(\d{4})(?:\s+(\d{2}):(\d{2}))?/);
    if (!match) return null;
    const [, day, month, year, hour = '0', minute = '0'] = match;
    return new Date(parseInt(year), parseInt(month) - 1, parseInt(day), 
                    parseInt(hour), parseInt(minute));
}

// Convertit date FR en YYYY-MM-DD pour tri/comparaison
function dateToISO(str) {
    const d = parseDateFR(str);
    if (!d || isNaN(d.getTime())) return null;
    return d.toISOString().split('T')[0];
}
```

### 3.2 Stats cards cliquables
6 cards en haut :
- Total recherches → vue classique sans filtre
- Positifs (vert) → filtre rating=👍
- Négatifs (rouge) → filtre rating=👎
- Satisfaction (%) 
- Erreurs → filtre erreur=true
- Temps moyen (ms)

### 3.3 Zone de filtres
- Recherche question (texte)
- Recherche commentaires (texte, filtrage côté client)
- Rating : Tous, 👍, 👎, Sans rating
- Mode : Tous, standard, ia, standarddeepl, iadeepl, standardia
- Date début / Date fin (format YYYY-MM-DD pour l'input)
- Problème : Tous, Bug IHM, Trop de patients, Pas assez de patients, Autre
- Boutons : Filtrer, Réinitialiser

### 3.4 Quatre onglets

#### Onglet Récapitulatif
- Taux satisfaction avec couleur (vert >70%, orange >50%, rouge sinon)
- Nombre d'erreurs
- Top problèmes signalés
- Termes non reconnus fréquents
- Recommandations automatiques

#### Onglet Graphiques
6 graphiques avec **sélecteur de période** (7j, 30j, 90j, 1an, Tout) :

1. **Évolution journalière** (barres empilées)
   - Agrégation par `dateToISO(timestamp)`
   - Séries : Positifs, Négatifs, Sans rating

2. **Répartition ratings** (donut)
   - Données depuis stats.ratings

3. **Répartition par mode** (barres horizontales)
   - Agrégation par colonne `mode`
   - Couleurs : standard=#3B9DD8, ia=#9b59b6, standardia=#1abc9c, standarddeepl=#f39c12, iadeepl=#e74c3c

4. **Temps de réponse moyen par jour** (ligne)
   - Agrégation : moyenne de `temps_ms` par jour
   - **Utiliser dateToISO() pour grouper**

5. **Top 10 termes recherchés** (barres horizontales)
   - Extraire de colonne `pathologies` (split par virgule)
   - Compter occurrences, top 10

6. **Répartition par moteur IA** (donut)
   - Filtrer recherches où `moteur` non vide
   - Couleurs par famille

**CRITIQUE** : Charger TOUTES les données (`limit=10000`) pour les graphiques.

#### Onglet Vue Cards
- Barre de tri : Date, Question, Patients, Rating, Mode
- Grille responsive de cards
- Bouton relancer sur chaque card

#### Onglet Vue Classique
- Tableau avec colonnes triables (clic sur header)
- Tri bidirectionnel (asc/desc toggle)
- Flèches visuelles ▲/▼

### 3.5 Pagination
- Dropdown items/page : 10, 20, 50, 100, 200
- Boutons : ← 1 ... [4] [5] [6] ... 100 → + total
- **CRITIQUE** : Recharger complètement à chaque changement de page (pas d'accumulation)

### 3.6 Tri bidirectionnel
```javascript
let currentSort = { column: 'timestamp', direction: 'desc' };

function sortTable(column) {
    if (currentSort.column === column) {
        currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
        currentSort.column = column;
        currentSort.direction = 'asc';
    }
    sortAndRender();
}
```

### 3.7 Modal détail
- Clic sur une recherche → modal avec toutes les infos
- Bouton "Relancer" pour rejouer la recherche

---

## 4. Fichiers à joindre pour recréation

### Pour analyse.html V2.0.0
- `Prompt_contexte2312.md`
- `Prompt_reconstruction_analyse.md` (ce fichier)

### Pour analyse.py V2.0.0
- `Prompt_contexte2312.md`
- `Prompt_reconstruction_analyse.md`
- Un exemple de `logrecherche.csv` (quelques lignes)

### Pour modifications search.py
- `search.py` actuel
- `Prompt_contexte2312.md`

---

## 5. Points critiques à ne pas oublier

1. **Dates françaises** : TOUJOURS utiliser `parseDateFR()` avant toute manipulation de date
2. **Lecture CSV** : TOUJOURS par nom de colonne via DictReader
3. **Graphiques** : Charger TOUTES les données (limit=10000)
4. **Pagination** : Reset complet à chaque page, pas d'accumulation
5. **Tri** : Fonctionne sur Cards ET Classique, bidirectionnel
6. **Encodage** : UTF-8-SIG pour le CSV (BOM)
7. **Séparateur** : Point-virgule `;`

---

## 6. Couleurs par mode

```javascript
const MODE_COLORS = {
    'standard': '#3B9DD8',      // Bleu
    'ia': '#9b59b6',            // Violet
    'standardia': '#1abc9c',    // Turquoise
    'standarddeepl': '#f39c12', // Orange
    'iadeepl': '#e74c3c'        // Rouge
};
```

## 7. Couleurs par moteur IA

```javascript
const MOTEUR_COLORS = {
    // OpenAI (vert)
    'gpt4o': '#10a37f',
    'gpt4omini': '#10a37f',
    // Anthropic (orange)
    'sonnet': '#d97706',
    'haiku': '#d97706',
    'opus': '#d97706',
    // Google (bleu)
    'gemini25flash': '#4285f4',
    'gemini15pro': '#4285f4',
    // Mistral (orange vif)
    'mistrallarge': '#ff7000',
    'mistralsmall': '#ff7000',
    // DeepSeek (bleu foncé)
    'deepseekr1': '#0066ff',
    'deepseekv3': '#0066ff',
    // Meta (bleu Facebook)
    'llama33': '#0668E1',
    // Cohere
    'command': '#5046e5'
};
```
