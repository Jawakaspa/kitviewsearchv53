# Prompt_cxchargepats.md

**Version :** 3.1.0  
**Date :** 24/12/2025  
**Objectif :** Recréer le programme cxchargepats.py à l'identique

---

## 🎯 Objectif du programme

Créer `cxchargepats.py`, un script Python qui charge des patients depuis un fichier CSV simplifié vers une base SQLite avec :

- Génération automatique de `oripathologies` à partir de `canontags` + `canonadjs`
- Gestion des pathologies avec préfixes progressifs
- Structure simplifiée (11 colonnes)

---

## 📋 Spécifications fonctionnelles

### Usage en ligne de commande

```bash
python cxchargepats.py <fichier_patients.csv> <N>
```

- `<fichier_patients.csv>` : Chemin vers le CSV (absolu, relatif, ou nom simple cherché dans `data/`)
- `<N>` : Nombre de patients à charger

### Exemples d'utilisation

```bash
python cxchargepats.py pats100.csv 99       # Cherche dans data/
python cxchargepats.py data/pats100.csv 99  # Chemin relatif
python cxchargepats.py c:/data/pats.csv 50  # Chemin absolu
```

### Fichiers de sortie

- Base créée dans `bases/base{N}.db`
- Si la base existe déjà, elle est **supprimée et recréée**

---

## 🗃️ Structure de la base de données

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

**Note importante** : Structure simplifiée par rapport à la v2.x (suppression de 21 colonnes inutilisées).

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

**Note** : Pas de table `patients_fts` (supprimée).

---

## 📊 Index à créer

```sql
CREATE INDEX idx_patients_sexe ON patients(sexe);
CREATE INDEX idx_patients_age ON patients(age);
CREATE INDEX idx_patients_datenaissance ON patients(datenaissance);
CREATE INDEX idx_patients_pathologies_patient_id ON patients_pathologies(patient_id);
CREATE INDEX idx_patients_pathologies_pathologie_id ON patients_pathologies(pathologie_id);
CREATE INDEX idx_pathologies_nom ON pathologies(pathologie);
```

**6 index** (suppression de l'index sur `ville` qui n'existe plus).

---

## 📄 Format du CSV patients

### Colonnes attendues (ordre EXACT)

```
id;canontags;canonadjs;sexe;age;datenaissance;prenom;nom;idportrait
```

**9 colonnes au total.**

### Encodage

- Encodage attendu : **UTF-8-SIG** (UTF-8 avec BOM)
- Si autre encodage détecté : afficher un WARNING
- Encodages testés dans l'ordre : `utf-8-sig`, `utf-8`, `cp1252`, `iso-8859-1`

### Commentaires

- Ignorer les lignes vides ou commençant par `#` (entre 0 et 100 lignes de commentaires possibles)

---

## 🔧 Génération de oripathologies

### Principe de combinaison canontags + canonadjs

Pour chaque patient :

1. Séparer `canontags` par `,` → liste de tags
2. Séparer `canonadjs` par `,` → liste d'adjectifs (correspondance positionnelle)
3. Pour chaque position `i` :
   - Si `canonadjs[i]` contient des `|`, séparer et **trier alphabétiquement**
   - Concaténer : `tag[i] + " " + adjs_triés`
4. Joindre toutes les pathologies par `,`

### Exemples

| canontags         | canonadjs                   | oripathologies                             |
| ----------------- | --------------------------- | ------------------------------------------ |
| `Bruxisme`        | `nocturne\|sévère`          | `Bruxisme nocturne sévère`                 |
| `béance,Bruxisme` | `latérale,nocturne\|sévère` | `béance latérale,Bruxisme nocturne sévère` |
| `béance`          | ``                          | `béance`                                   |
| `latérodéviation` | `mandibulaire\|gauche`      | `latérodéviation gauche mandibulaire`      |

**Important** : Les adjectifs multiples (séparés par `|`) sont triés **alphabétiquement**.

---

## 🔧 Dépendance externe

### Module standardise.py

Le programme utilise `standardise.py` pour normaliser les textes.

**Recherche du module dans cet ordre :**

1. `./standardise.py` (répertoire courant)
2. `../standardise.py` (répertoire parent)

**Import dynamique** via `importlib.util` pour éviter les problèmes d'encodage Windows avec subprocess.

---

## 🔄 Algorithme de traitement des pathologies

### Principe des préfixes progressifs

Pour chaque pathologie normalisée (ex: `beance anterieure gauche`), créer les entrées :

- `beance`
- `beance anterieure`
- `beance anterieure gauche`

Chaque préfixe est lié au patient via `patients_pathologies`.

### Flux de traitement

1. Générer `oripathologies` à partir de `canontags` + `canonadjs`
2. Pour chaque pathologie dans `oripathologies` :
   - Normaliser avec `standardise()`
   - Utiliser la pathologie normalisée
3. Insérer tous les préfixes progressifs dans `pathologies`
4. Créer les liaisons dans `patients_pathologies`
5. Reconstituer le champ `pathologies` (liste sans doublons, séparée par `, `)

---

## 📝 Fonctions principales

### `print_header()`

Affiche le cartouche du programme.

### `create_db_and_tables(db_path)`

Crée la base et les 3 tables (patients, pathologies, patients_pathologies).

### `create_indexes(conn)`

Crée les 6 index de performance.

### `parse_date(date_str)`

Parse une date `JJ/MM/AAAA` ou `YYYY-MM-DD` → `YYYY-MM-DD` (ISO).

### `parse_float(value, default=0.0)`

Parse un float avec gestion d'erreur.

### `parse_int(value, default=0)`

Parse un int avec gestion d'erreur.

### `standardise(text)`

Wrapper qui importe dynamiquement `standardise.py` et appelle sa fonction `standardise()`.

### `generate_oripathologies(canontags, canonadjs)`

Combine tags et adjectifs pour générer oripathologies.

### `get_or_create_pathology_id(cursor, pathology_name)`

Récupère ou crée une pathologie et retourne son ID.

### `insert_pathology_with_prefixes(conn, patient_id, pathology_name, linked_pathologies)`

Insère une pathologie ET tous ses préfixes progressifs, avec liaisons patient.

### `charge_patients(conn, csv_file, N)`

Fonction principale de chargement :

- Valide les colonnes (9 attendues)
- Génère oripathologies pour chaque patient
- Affiche une barre de progression
- Insère les patients avec commit par ligne
- Affiche les statistiques finales

---

## 📊 Affichage attendu

### Barre de progression

```
[████████████████████░░░░░░░░░░░░░░░░░░░░] 60% - Ligne 60/100
```

### Statistiques finales

```
============================================================
Chargement terminé
  ✔ Patients chargés : 100/100
  ✔ Pathologies uniques (avec préfixes) : 176
  ✔ Liaisons patient-pathologie : 381
  ⏱ Durée : 0.20s
============================================================
```

### Debug pathologies

```
[DEBUG] Exemples de pathologies dans la base :
  - 'activateur'
  - 'agenesie'
  - 'beance'
  - 'beance anterieure'
  - 'beance anterieure gauche'
  ...
```

---

## ⚠️ Points critiques

1. **Colonnes CSV** : 9 colonnes en entrée, 11 dans la table patients
2. **Génération oripathologies** : Combinaison canontags + canonadjs avec tri alphabétique des adjs
3. **Pas de patients_fts** : Table supprimée
4. **Encodage CSV** : Tester plusieurs encodages, préférer UTF-8-SIG
5. **Cartouche** : Détecter automatiquement (ligne commence par `#`)
6. **Import standardise.py** : Via `importlib.util`, pas subprocess
7. **Préfixes progressifs** : Générer TOUS les préfixes pour chaque pathologie
8. **Commit par ligne** : Un `conn.commit()` après chaque patient (robustesse)

---

## 📖 Cartouche du programme

```python
#*TO*#
__pgm__ = "cxchargepats.py"
__version__ = "0.0.0"
__date__ = "01/01/1970 00:00"
```

---

## 🔗 Fichiers nécessaires en PJ

| Fichier                  | Emplacement      | Description                |
| ------------------------ | ---------------- | -------------------------- |
| `standardise.py`         | racine ou parent | Fonction de normalisation  |
| `Prompt_contexte2312.md` | projet           | Contexte général du projet |

---

## Historique des versions du prompt

| Version | Date       | Modifications                                                                                    |
| ------- | ---------- | ------------------------------------------------------------------------------------------------ |
| 2.0.0   | 13/12/2025 | Version initiale                                                                                 |
| 2.1.0   | 15/12/2025 | Ajout colonnes `canontags` et `canonadjs`                                                        |
| 3.0.0   | 17/12/2025 | Simplification structure (11 colonnes), génération auto oripathologies, suppression patients_fts |
| 3.1.0   | 24/12/2025 | Correction champ `idportrait` (au lieu de `portrait`)                                            |

---

**Fin du prompt**
