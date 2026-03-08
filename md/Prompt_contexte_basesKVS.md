## Prompt_contexte_annexe

Ce fichier contient les sections détaillées déplacées depuis le prompt principal pour économiser des tokens. À joindre en PJ uniquement quand le sujet est abordé.

---

## Versionning détaillé

Format SemVer

**MAJOR.MINOR.PATCH** (ex: v1.2.3)

- MAJOR : Changements incompatibles (breaking changes)
- MINOR : Ajouts rétrocompatibles
- PATCH : Corrections de bugs rétrocompatibles

La date dans le cartouche est celle de la création de la version.

Tu gères les versions et tu décides des versions MINOR et PATCH mais pas de MAJOR que je gère.

Chaque fichier .py commence par les lignes suivantes **avant les imports** :

```python
#*TO*#
__pgm__ = "nom_du_programme.py"
__version__ = version
__date__ = date
```

L'affichage initial rappelle la version :

```python
def main():
    print(f"{__pgm__} V{__version__} - {__date__}")
```

### 

---

## Pipeline de gestion des fichiers

1. Fichiers déposés dans `un répertoire d'entrée de chaque projet.
2. cerbere.py` sauvegarde l'original puis déplace vers les répertoires de destination :à la racine pour les `.py, dans ihm pour les .html etc...
   
   

---

## Affichage détaillé

### Affichage initial

```python
def main():
    print(f"{__pgm__} V{__version__} - {__date__}")
```

### Niveaux d'affichage web

- **DEBUG** : Préfixé `[DEBUG] `, toujours envoyé à la page, affiché via checkbox
- **Utilisateur** : Chaque étape active affichée (détection pattern, exécution SQL)
- Logique chatbot : mode IA avec scroll, mode classique en zone fixe
- Message final formatté via `phrases_chatbot.csv`
- Exemple : `🎯 J'ai trouvé exactement 42 patients avec bruxisme et béance latérale de moins de 30 ans en 1432 ms.`

### Affichage chemins

Chaque nom de fichier dans la console inclut le **chemin absolu complet**.

### phrases_chatbot.csv

Structure : `usage;phrase;emoji`

- `usage` : contexte (final_exact, etape_patho, etape_age)
- `phrase` : template avec placeholders `xx` (nombre) et `{ff}` (filtre)
- Plusieurs phrases par usage pour variété
- **Fichier protégé** : ne JAMAIS l'écraser

---

## Fichiers d'exemple

Convention `_EXEMPLE` pour les exemples (ex: `transforme_EXEMPLE.csv`). À renommer par l'utilisateur.

---

## Gestion données — Fichiers externes

- Synonymes → `synonyms.csv` (par langue si besoin)
- Cas cliniques → `cas_cliniques.csv`
- Tags/catégories → fichiers dédiés
- Mots vides → `transforme.csv`
- Pathologies → `pathologiessaisies.csv`
- Phrases → `phrases_chatbot.csv`

### Stratégie multilingue

- Garder FR seul, traduire partiellement, ou copie par langue
- Contrainte : < 10 Mo par langue

---

## Architecture de recherche

### 1. Filtrage SQL initial

Premier filtrage par SQL sur champs indexés. La **pathologie** est la donnée la plus importante :

- Recherchée en premier dans l'analyse de question
- Table pathologies indexée + table de jointure indexée
- Objectif : rapidité maximale

### 2. Recherche FTS5

Sur données résiduelles, recherche sur `search_text` (concaténation normalisée d'infos patient).

### 3. Correction orthographique

À adjoindre ultérieurement avec FTS5.

### Nommage des bases

Le nom contient **N** = nombre de patients : `base2.db` à `base200000.db`. Fichiers intermédiaires : `brutN.csv`, `netN.csv`.

---

## 🗃️ Structure BDD

### Table `patients` (11 colonnes)

```sql
CREATE TABLE patients (
    id INTEGER PRIMARY KEY,
    canontags TEXT,
    canonadjs TEXT,
    sexe TEXT,
    age DECIMAL(5, 3),
    datenaissance DATE,
    prenom TEXT,
    nom TEXT,
    idportrait TEXT,
    oripathologies TEXT,
    pathologies TEXT
);
```

### Table `pathologies`

```sql
CREATE TABLE pathologies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pathologie TEXT UNIQUE NOT NULL
);
```

### Table de jointure `patients_pathologies`

```sql
CREATE TABLE patients_pathologies (
    patient_id INTEGER NOT NULL,
    pathologie_id INTEGER NOT NULL,
    PRIMARY KEY (patient_id, pathologie_id),
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (pathologie_id) REFERENCES pathologies(id) ON DELETE CASCADE
);
```

### 6 Index

```sql
CREATE INDEX idx_patients_sexe ON patients(sexe);
CREATE INDEX idx_patients_age ON patients(age);
CREATE INDEX idx_patients_datenaissance ON patients(datenaissance);
CREATE INDEX idx_patients_pathologies_patient_id ON patients_pathologies(patient_id);
CREATE INDEX idx_patients_pathologies_pathologie_id ON patients_pathologies(pathologie_id);
CREATE INDEX idx_pathologies_nom ON pathologies(pathologie);
```

---

## Debug et monitoring

- Debug intégré dès la conception
- Affichage optionnel des performances et résultats intermédiaires
- Logs détaillés pour diagnostic

---

## Checklist de livraison

- [ ] Encodage correct (UTF-8 sans BOM pour `.py`/`.cmd`, UTF-8-SIG pour `.csv`)
- [ ] Séparateurs corrects dans les CSV (`;` et `,`)
- [ ] Pas de données en dur (sauf exceptions)
- [ ] Fichiers protégés non écrasés
- [ ] Chemins absolus dans les affichages console
- [ ] Gestion d'erreurs robuste
- [ ] Messages de progression pour traitements longs (tqdm)
- [ ] Documentation claire et résumé fourni
- [ ] Variables `__pgm__`, `__version__`, `__date__` présentes avant les imports
- [ ] Affichage initial dans `main()` si applicable
