# Prompt de recréation : chargebase.py

## Objectif

Créer `chargebase.py`, un programme Python qui charge des données patients depuis un fichier CSV vers une base SQLite normalisée à 5 tables pour permettre une recherche efficace par tags (pathologies) et adjectifs (qualificatifs).

---

## Usage

```
chargebase.py <fichier.csv> <N>
```

- `<fichier.csv>` : fichier source des patients au format UTF-8-BOM, séparateur `;`
- `<N>` : nombre de lignes à charger (doit être ≤ lignes utiles du CSV)

**Exemples :**
- `chargebase.py pats100.csv 100` → crée `base100.db`
- `chargebase.py pats100.csv 50` → crée `base50.db`
- `chargebase.py pats100.csv 200` → **ERREUR** si le fichier contient moins de 200 lignes utiles

---

## Fichiers PJ requis

1. **`standardise.py`** - Module de normalisation de texte (minuscules, suppression accents latins)
2. **`pats100.csv`** - Fichier de test avec données patients (optionnel, pour les tests)
3. **`Prompt_contexte0412.md`** - Contexte général du projet Kitview

---

## Structure du fichier CSV source

```csv
#commentaire (ignoré)
id;canontags;canonadjs;sexe;age;datenaissance;prenom;nom;portrait
1;diastème;;M;8.706;26/03/2017;Timothée;Marie;https://...
3;béance;latérale|gauche|postérieure;M;17.421;07/07/2008;Guillaume;Moulin;https://...
```

### Colonnes

| Colonne | Type | Description |
|---------|------|-------------|
| id | INTEGER | Identifiant patient |
| canontags | TEXT | Tags canoniques séparés par `,` |
| canonadjs | TEXT | Adjectifs par tag, séparés par `,` (adjectifs d'un même tag séparés par `\|`) |
| sexe | TEXT | M ou F |
| age | DECIMAL | Âge en années décimales |
| datenaissance | DATE | Format JJ/MM/AAAA |
| prenom | TEXT | Prénom |
| nom | TEXT | Nom |
| portrait | TEXT | URL de la photo |

### Format canontags / canonadjs

```
canontags: Tag1,Tag2,Tag3
canonadjs: adj1a|adj1b,adj2a,adj3a|adj3b|adj3c
           └──Tag1──┘ └Tag2┘ └────Tag3────┘
```

**Règle critique :** Le nombre de groupes d'adjectifs (séparés par `,`) doit égaler le nombre de tags.

---

## Structure de la base SQLite cible

### Table patients
```sql
CREATE TABLE patients (
    id INTEGER PRIMARY KEY,
    canontags TEXT,
    canonadjs TEXT,
    stdcanontags TEXT,      -- Version standardisée de canontags
    stdcanonadjs TEXT,      -- Version standardisée de canonadjs
    sexe TEXT,
    age DECIMAL(5, 3),
    datenaissance TEXT,
    prenom TEXT,
    nom TEXT,
    portrait TEXT
);
CREATE INDEX idx_patients_sexe ON patients(sexe);
CREATE INDEX idx_patients_age ON patients(age);
```

### Table tags
```sql
CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag TEXT UNIQUE NOT NULL  -- Version standardisée
);
CREATE INDEX idx_tags_tag ON tags(tag);
```

### Table adjectifs
```sql
CREATE TABLE adjectifs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    adjectif TEXT UNIQUE NOT NULL  -- Version standardisée
);
CREATE INDEX idx_adjectifs_adjectif ON adjectifs(adjectif);
```

### Table patients_tags
```sql
CREATE TABLE patients_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER NOT NULL,
    tag_id INTEGER NOT NULL,
    UNIQUE(patient_id, tag_id),
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
);
CREATE INDEX idx_patients_tags_patient ON patients_tags(patient_id);
CREATE INDEX idx_patients_tags_tag ON patients_tags(tag_id);
```

### Table patients_tags_adjectifs
```sql
CREATE TABLE patients_tags_adjectifs (
    patient_tag_id INTEGER NOT NULL,
    adjectif_id INTEGER NOT NULL,
    PRIMARY KEY (patient_tag_id, adjectif_id),
    FOREIGN KEY (patient_tag_id) REFERENCES patients_tags(id) ON DELETE CASCADE,
    FOREIGN KEY (adjectif_id) REFERENCES adjectifs(id) ON DELETE CASCADE
);
CREATE INDEX idx_pta_patient_tag ON patients_tags_adjectifs(patient_tag_id);
CREATE INDEX idx_pta_adjectif ON patients_tags_adjectifs(adjectif_id);
```

---

## Algorithme de chargement

1. **Validation initiale**
   - Vérifier que le fichier CSV existe
   - Compter les lignes utiles (non vides, ne commençant pas par `#`)
   - Si N > lignes utiles → ERREUR et arrêt

2. **Création de la base**
   - Créer/écraser `baseN.db` dans le même répertoire que le CSV
   - DROP toutes les tables existantes
   - CREATE toutes les tables + index
   - Activer `PRAGMA foreign_keys = ON`

3. **Chargement des données**
   - Filtrer les lignes de commentaires (commençant par `#`)
   - Pour chaque patient :
     - Parser canontags et canonadjs
     - Standardiser avec `standardise()` pour stdcanontags/stdcanonadjs
     - Insérer dans patients
     - Pour chaque tag : INSERT OR IGNORE dans tags, récupérer id, INSERT dans patients_tags
     - Pour chaque adjectif du tag : INSERT OR IGNORE dans adjectifs, INSERT dans patients_tags_adjectifs
   - Afficher barre de progression avec tqdm

4. **Finalisation**
   - COMMIT
   - Afficher statistiques (patients, tags distincts, adjectifs distincts, associations)

---

## Gestion des erreurs

| Erreur | Action |
|--------|--------|
| Fichier inexistant | Message + arrêt |
| N > lignes utiles | Message + arrêt |
| Colonne manquante | Message + arrêt |
| Erreur SQL | Message + rollback + arrêt |

---

## Affichage attendu

```
chargebase.py V1.0.0 - DD/MM/YYYY HH:MM

Fichier source    : C:\g\pats100.csv
Lignes utiles     : 100
Lignes à charger  : 50
Base cible        : C:\g\base50.db

[████████████████████] 100% - Patient 50/50

✓ Chargement terminé en 0.146 s
  - Patients                  : 50
  - Tags distincts            : 43
  - Adjectifs distincts       : 17
  - Associations patient-tag  : 107
  - Associations tag-adjectif : 73
```

---

## Dépendances

- Python 3.13+
- tqdm (barre de progression)
- standardise.py (module local)

---

## Contraintes techniques

- Encodage CSV : UTF-8-SIG (BOM)
- Séparateur colonnes : `;`
- Séparateur tags : `,`
- Séparateur adjectifs d'un tag : `|`
- Séparateur groupes d'adjectifs : `,`
- Cartouche standard avec `__pgm__`, `__version__`, `__date__`
- Chemins absolus dans tous les affichages

---

## Requêtes SQL de vérification

### Patients avec un tag spécifique
```sql
SELECT p.prenom, p.nom, t.tag
FROM patients p
JOIN patients_tags pt ON p.id = pt.patient_id
JOIN tags t ON pt.tag_id = t.id
WHERE t.tag = 'beance';
```

### Patients avec tag + adjectif
```sql
SELECT DISTINCT p.prenom, p.nom
FROM patients p
JOIN patients_tags pt ON p.id = pt.patient_id
JOIN tags t ON pt.tag_id = t.id
JOIN patients_tags_adjectifs pta ON pt.id = pta.patient_tag_id
JOIN adjectifs a ON pta.adjectif_id = a.id
WHERE t.tag = 'beance' AND a.adjectif = 'gauche';
```

---

*Prompt généré le 12/12/2025 - Conversation chargebase*
