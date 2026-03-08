# Prompt : Développement tags2refs.py et tags2tag.py

## Nom de la conversation : tags2refs

---

## Contexte

Suite à la conversation **structurebase**, la structure de données pour la recherche de patients par tags et adjectifs a été définie.

Cette conversation porte sur le développement de deux programmes de transformation :
1. `tags2refs.py` : tags.csv → tagsrefs.csv (normalisation + traduction multilingue)
2. `tags2tag.py` : tagsrefs.csv → syntag.csv + synadj.csv (fichiers lookup)

---

## Fichiers d'entrée

### tags.csv (saisie utilisateur)

Structure : `type;tags;adj1;adj2;adj3;...`

- `type` : P=pathologie, T=traitement, ou libre (1-10 car)
- `tags` : tag officiel + synonymes séparés par `,`
- `adjN` : adjectif officiel + synonymes séparés par `,` (une colonne par adjectif)

**Exemple (une ligne sur plusieurs lignes pour lisibilité) :**
```csv
type;tags;adj1;adj2;adj3;adj4;adj5
P;béance,béances,béance dentaire,open bite,openbite;antérieure,devant,face,anterieur;gauche,senestre,à gauche;postérieur,derrière;droit,droite;latéral,latérale,de côté
P;bruxisme,bruxismes,grincement;nocturne,nuit;diurne,jour
T;aligneurs,aligneur,gouttières,gouttière;invisible,transparent
```

**Note :** Le nombre de colonnes d'adjectifs peut varier d'une ligne à l'autre.

---

## Fichiers de sortie

### tagsrefs.csv (normalisé + multilingue)

Structure : `type;frtags;stdfrtags;fradjs;stdfradjs;entags;stdentags;enadjs;stdenadjs;detags;stddetags;deadjs;stddedjs;...`

**Colonnes par langue (ex: fr) :**
- `frtags` : tags en français (copie de la colonne tags pour fr)
- `stdfrtags` : standardisation de frtags
- `fradjs` : tous les adjectifs regroupés (voir format ci-dessous)
- `stdfradjs` : standardisation de fradjs

**Format de la colonne adjs :**
Les adjectifs de toutes les colonnes sont regroupés ainsi :
- Les synonymes d'un adjectif sont séparés par `|`
- Les différents adjectifs sont séparés par `,`

```
Entrée (colonnes séparées) :
adj1: antérieure,devant,face
adj2: gauche,senestre

Sortie (colonne unique fradjs) :
antérieure|devant|face,gauche|senestre
```

**Langues :** Définies dans `commun.csv` ligne `langues` (ex: `langues;fr;en;de;th`)

### syntag.csv (lookup tags)

Structure : `stdtag;std1er;langue`

- `stdtag` : chaque synonyme standardisé (1 ligne par synonyme)
- `std1er` : le 1er tag standardisé (forme canonique)
- `langue` : fr, en, de, th...

**Exemple :**
```csv
stdtag;std1er;langue
beance;beance;fr
beances;beance;fr
beance dentaire;beance;fr
open bite;beance;fr
openbite;beance;fr
gap;gap;en
open bite;gap;en
```

### synadj.csv (lookup adjectifs)

Structure : `stdadj;std1er;stdtag;langue`

- `stdadj` : chaque synonyme d'adjectif standardisé (1 ligne par synonyme)
- `std1er` : le 1er adjectif standardisé (forme canonique)
- `stdtag` : le tag canonique auquel cet adjectif est rattaché
- `langue` : fr, en, de, th...

**Exemple :**
```csv
stdadj;std1er;stdtag;langue
anterieure;anterieure;beance;fr
devant;anterieure;beance;fr
face;anterieure;beance;fr
gauche;gauche;beance;fr
senestre;gauche;beance;fr
a gauche;gauche;beance;fr
nocturne;nocturne;bruxisme;fr
nuit;nocturne;bruxisme;fr
```

---

## Algorithme tags2refs.py

### Usage

```
tags2refs.py [--force]
```

- Sans `--force` : ne retraduit pas les colonnes non vides
- Avec `--force` : retraduit tout

### Étapes

1. **Lecture de commun.csv** → extraire liste des langues
2. **Lecture de tags.csv**
3. **Pour chaque ligne :**
   - Copier `type`
   - Copier `tags` → `frtags`
   - Standardiser → `stdfrtags`
   - Regrouper les colonnes adj1, adj2... → `fradjs` (avec `|` et `,`)
   - Standardiser → `stdfradjs`
   - **Pour chaque langue autre que fr :**
     - Traduire `frtags` → `{lang}tags` (si vide ou --force)
     - Standardiser → `std{lang}tags`
     - Traduire `fradjs` → `{lang}adjs` (si vide ou --force)
     - Standardiser → `std{lang}adjs`
4. **Écriture de tagsrefs.csv**

### Traduction

- Utiliser `traduis.py` (DeepL + fallbacks)
- Traduire les termes individuellement (pas la chaîne complète)
- Conserver les séparateurs `|` et `,`

---

## Algorithme tags2tag.py

### Usage

```
tags2tag.py
```

Lit `tagsrefs.csv` et produit `syntag.csv` + `synadj.csv`

### Étapes pour syntag.csv

1. **Pour chaque ligne de tagsrefs.csv :**
2. **Pour chaque langue :**
   - Lire `std{lang}tags`
   - Extraire le 1er tag (avant la première `,`) → `std1er`
   - Splitter sur `,` → liste de synonymes
   - Pour chaque synonyme → écrire une ligne `stdtag;std1er;langue`

### Étapes pour synadj.csv

1. **Pour chaque ligne de tagsrefs.csv :**
2. **Récupérer le tag canonique** (`std1er` de cette ligne)
3. **Pour chaque langue :**
   - Lire `std{lang}adjs`
   - Splitter sur `,` → groupes d'adjectifs
   - Pour chaque groupe :
     - Extraire le 1er adjectif (avant le premier `|`) → `std1er_adj`
     - Splitter sur `|` → liste de synonymes
     - Pour chaque synonyme → écrire une ligne `stdadj;std1er_adj;stdtag;langue`

---

## Programmes existants à utiliser

### standardize.py
Normalisation des chaînes (minuscules, suppression accents, etc.)

```python
from standardize import standardize
std = standardize("Béance dentaire")  # → "beance dentaire"
```

### traduis.py
Traduction via DeepL (solution nominale) avec fallbacks.
À fournir pour référence.

### commun.csv
Contient la configuration globale dont la ligne des langues.

```csv
cle;valeur
langues;fr;en;de;th
```

---

## Contraintes techniques

- Python 3.13+
- UTF-8-SIG (BOM) pour tous les CSV
- Séparateur colonnes : `;`
- Séparateur multivaleurs (tags, adjectifs entre eux) : `,`
- Sous-séparateur (synonymes d'un adjectif) : `|`
- Ne pas retraduire les colonnes non vides (sauf --force)
- Les colonnes std sont la standardisation des colonnes traduites, pas des traductions
- Utiliser tqdm pour les barres de progression

---

## Gestion des erreurs

| Erreur | Action |
|--------|--------|
| Fichier tags.csv inexistant | Message + arrêt |
| Fichier commun.csv inexistant | Message + arrêt |
| Erreur de traduction | Warning + garder valeur FR |
| Ligne mal formée | Warning + ignorer la ligne |

---

## Affichage attendu

### tags2refs.py

```
tags2refs.py V1.0.0 - DD/MM/YYYY HH:MM

Fichier source : C:\g\refs\tags.csv
Langues cibles : fr, en, de, th

[████████████████████] 100% - Ligne 15/15

Traductions effectuées : 45
Traductions réutilisées : 12
Erreurs de traduction : 0

✓ Fichier généré : C:\g\refs\tagsrefs.csv
```

### tags2tag.py

```
tags2tag.py V1.0.0 - DD/MM/YYYY HH:MM

Fichier source : C:\g\refs\tagsrefs.csv

[████████████████████] 100% - Ligne 15/15

✓ Fichiers générés :
  - C:\g\refs\syntag.csv (127 lignes)
  - C:\g\refs\synadj.csv (89 lignes)
```

---

## Livrables attendus

1. `tags2refs.py` : transformation tags.csv → tagsrefs.csv
2. `tags2tag.py` : transformation tagsrefs.csv → syntag.csv + synadj.csv
3. `tags_EXEMPLE.csv` : fichier de test avec quelques tags

---

## Fichiers à fournir au démarrage

- [ ] `traduis.py` (existant)
- [ ] `standardize.py` (existant)
- [ ] `commun.csv` (existant ou structure)
- [ ] `tags_EXEMPLE.csv` (quelques lignes de test) - optionnel, peut être généré

---

*Prompt généré le 2025-12-05 - Conversation structurebase*
