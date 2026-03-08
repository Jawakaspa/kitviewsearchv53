# Prompt Cerbere - Gardien du Projet Kitview

**Version :** 2.4.6  
**Date :** 12/12/2025  
**Usage :** Prompt à utiliser pour faire évoluer cerbere.py

---

## 🎯 Objectif de ce prompt

Ce document contient toutes les informations nécessaires pour reprendre le développement de `cerbere.py` dans une nouvelle conversation Claude.

---

## 📋 Contexte du projet

### Qu'est-ce que cerbere.py ?

`cerbere.py` est un **démon Python** (programme qui tourne en continu) qui surveille le répertoire `c:\boitedereception\` et effectue automatiquement :

1. **VALIDATION** : Vérifie encodage et format des fichiers
2. **CONVERSION** : Convertit automatiquement les CSV mal formatés
3. **TRAITEMENT XLSX** : Convertit les xlsx si un csv correspondant existe dans refs
4. **VERSIONNING** : Attribue et incrémente les versions (système comptable)
5. **DISPATCHING** : Distribue les fichiers vers les bons répertoires
6. **SAUVEGARDE** : Copie incrémentale avec archivage vers `c:\cxsauve\`
7. **BACKUP SSD** : Backup quotidien sur SSD externe si branché

### Version actuelle

**cerbere.py v1.4.6** - 12/12/2025

### Dépendances

- **Python 3.13+**
- **openpyxl** : `pip install openpyxl` (pour conversion xlsx → csv)

---

## 🗂️ Architecture des répertoires

```
c:\boitedereception\     # Entrée : déposer les fichiers ici
c:\cx\                   # Projet principal (fichiers .py)
c:\cx\ihm\               # Pages HTML générées (searchX.html)
c:\cx\db\                # Bases de données .db
c:\cx\prompts\           # Fichiers Prompt_*.md
c:\cx\doc\               # Documentation (.md, .xlsx, .docx, .txt)
c:\cx\convs\             # Conversations (con*.md)
c:\cx\ztri\              # Fichiers non reconnus
c:\cx\data\              # CSV data*.csv et *pat*.csv
c:\cx\tests\             # CSV test*.csv
c:\cx\logs\              # CSV logs*.csv
c:\cx\refs\              # grandlivre.csv + journal.csv + autres CSV
c:\cxsauve\              # Sauvegarde incrémentale
c:\cxarchives\           # Archives des anciennes versions
g:\cxssd\                # Backup SSD (si branché)
```

---

## 📜 Règles de dispatching (v1.4.2)

### Traitement préliminaire xlsx

**Avant le dispatching normal**, pour chaque fichier `.xlsx` :
1. Vérifier si un fichier `.csv` de même nom existe dans `refs/`
2. Si oui : convertir le xlsx en csv (utf-8-sig, séparateur `;`) et remplacer le csv existant
3. **Dans tous les cas** : le xlsx est ensuite dispatché vers `doc/` (pas supprimé)

### Fichiers Markdown (.md)

| Pattern              | Destination        | Exemple               |
| -------------------- | ------------------ | --------------------- |
| `Prompt_*` ou `prompt_*` | `c:\cx\prompts\`   | Prompt_cerbere.md     |
| `con*`               | `c:\cx\convs\`     | conv_debug.md         |
| Autres `.md`         | `c:\cx\doc\`       | notes.md, readme.md   |

### Fichiers CSV

| Pattern     | Destination      | Exemple           |
| ----------- | ---------------- | ----------------- |
| `data*`     | `c:\cx\data\`    | data_patients.csv |
| `*pat*`     | `c:\cx\data\`    | mpat100.csv, qpat100.csv |
| `test*`     | `c:\cx\tests\`   | test_import.csv   |
| `logs*`     | `c:\cx\logs\`    | logs_erreurs.csv  |
| Autres `*`  | `c:\cx\refs\`    | inconnu.csv       |

### Autres fichiers

| Pattern     | Extension                | Destination      |
| ----------- | ------------------------ | ---------------- |
| `*`         | `.db`                    | `c:\cx\db\`      |
| `*`         | `.html`, `.css`          | `c:\cx\ihm\`     |
| `*`         | `.py`                    | `c:\cx\`         |
| `*`         | `.xlsx`                  | `c:\cx\doc\`     |
| `*`         | `.docx`, `.txt`          | `c:\cx\doc\`     |
| Autres `*`  | *                        | `c:\cx\ztri\`    |

---

## 🔄 Conversion automatique des CSV

### Comportement (v1.4.2)

Quand un fichier CSV arrive dans `boitedereception/` :

1. **Vérification** : encodage et séparateur
2. **Si non conforme** : conversion automatique
   - Détection de l'encodage (utf-8, latin-1, cp1252)
   - Détection du séparateur (`,`, `;`, `\t`)
   - Conversion vers : **utf-8-sig** + séparateur **`;`**
3. **Si conversion réussie** : traitement normal
4. **Si conversion échoue** : fichier reste dans `boitedereception/`

### Format CSV standard

- **Encodage** : UTF-8 avec BOM (`utf-8-sig`) obligatoire
- **Séparateur colonnes** : `;` (point-virgule) obligatoire
- **Séparateur multivaleurs** : `,` (virgule)
- **Commentaires** : Lignes commençant par `#` ignorées

---

## 🔢 Système de versionning

### Fichiers de contrôle

- `c:\cx\refs\grandlivre.csv` : Situation actualisée (dernière version de chaque fichier)
- `c:\cx\refs\journal.csv` : Historique complet de toutes les versions

### Format CSV

```csv
nomdufichier;version;timestamp
cerbere.py;V1.4.2;10/12/2025 10:04:08
hmodconf4.txt;V1.0.0;24/11/2025 17:30:00
```

### Règles de version

- Nouveau fichier : `V1.0.0`
- Fichier existant : Incrémente le dernier nombre (`V1.0.0` → `V1.0.1`)
- Format : `MAJOR.MINOR.PATCH`
- La version dans le grand livre fait **référence** : si on veut forcer une version, il faut modifier le grand livre

---

## ⚠️ RÈGLE CRITIQUE : Fichiers à NE JAMAIS MODIFIER

### Liste complète des extensions à ne JAMAIS modifier

| Extension                      | Raison                                        |
| ------------------------------ | --------------------------------------------- |
| `.txt`                         | Documents textes bruts (modules hmod avec JS) |
| `.db`                          | Bases de données binaires                     |
| `.png`, `.jpg`, `.gif`, `.pdf` | Fichiers binaires                             |
| `.xlsx`, `.docx`               | Documents Office (binaires)                   |

### Extensions recevant un cartouche de version

| Extension | Format du cartouche                                                                |
| --------- | ---------------------------------------------------------------------------------- |
| `.py`     | `# fichier.py V1.0.0 - timestamp` + variables `__pgm__`, `__version__`, `__date__` |
| `.csv`    | `# fichier.csv V1.0.0 - timestamp` (première ligne)                                |
| `.md`     | `# Prompt fichier V1.0.0 - timestamp` (si contient "Prompt" dans le nom)           |
| `.html`   | Version inscrite dans commentaire `/* */` existant si présent                      |

---

## 🔄 Cycle de surveillance

```
Toutes les minutes :
  1. IMPORT (traiter c:\boitedereception\)
     a. Phase 1 : traitement préliminaire xlsx
     b. Phase 2 : traitement normal des autres fichiers
  2. Attendre 30s
  3. SAUVEGARDE (c:\cx\ → c:\cxsauve\)
  4. Attendre 30s
  5. BACKUP SSD (si g:\cxssd\ accessible et pas de backup du jour)
  6. Reboucle
```

---

## 🛠 Historique des versions

### v1.4.6 (12/12/2025)

- **Ajout dispatching .css** :
  - Fichiers `.css` → `ihm/` (avec les `.html`)

### v1.4.5 (12/12/2025)

- **Correction SyntaxWarning** :
  - Utilisation de raw strings (`r"""..."""`) pour les docstrings
  - Remplacement des backslashes par forward slashes dans la doc

### v1.4.4 (10/12/2025)

- **Simplification dispatching** :
  - Suppression du répertoire `hmod/` (plus utilisé)
  - Tous les `.md` non triés → `doc/` (au lieu de `ztri/`)

### v1.4.3 (10/12/2025)

- **Correction traitement xlsx** :
  - Le xlsx n'est plus supprimé après conversion
  - Il est dispatché vers `doc/` dans tous les cas

### v1.4.2 (10/12/2025)

- **Conversion automatique CSV** :
  - CSV mal encodés : conversion auto en utf-8-sig avec ;
  - Détection multi-encodage (utf-8, latin-1, cp1252)
  - Détection séparateur (;, ,, tab)
- **Traitement préliminaire xlsx** :
  - Si un .csv de même nom existe dans refs, convertit et remplace
  - Dépendance ajoutée : openpyxl
- **Pattern CSV modifié** :
  - `*pat*` (contient "pat") au lieu de `pat*` (commence par)
  - Exemples : mpat100.csv, qpat100.csv → data/

### v1.4.1 (08/12/2025)

- **Correction dispatching CSV** :
  - CSV sans pattern connu → `refs\` (et non `ztri\`)

### v1.4.0 (07/12/2025)

- **Corrections dispatching** :
  - `zarchives\` renommé en `convs\` (con*.md)
  - Ajout pattern `pat*.csv` → `data\`

### v1.3.0 (05/12/2025)

- **Renommage répertoires racines** :
  - `c:\g\` → `c:\cx\`
  - `c:\gsauve\` → `c:\cxsauve\`
  - `c:\gsauve\archives\` → `c:\cxarchives\`
  - `g:\gssd\` → `g:\cxssd\`
- **Renommage sous-répertoires** :
  - `documentation\` → `doc\`
  - `web\` → `ihm\`
  - `zatrier\` → `ztri\`
  - `bases\` → `db\`

### v1.2.0 (30/11/2025)

- Nouvelles règles de dispatching .md

### v1.0.3 (24/11/2025)

- **CRITIQUE** : Les fichiers `.txt` ne sont plus modifiés

---

## 📌 Pour commencer une nouvelle conversation

Pour une conversation sur cerbere.py, joindre :

1. **cerbere.py** (version actuelle v1.4.6)
2. **Prompt_cerbere.md** (ce document v2.4.6)

Copier-coller ce texte au début de la conversation :

```
Je travaille sur cerbere.py, un démon Python de validation, versionning et sauvegarde automatique.

Version actuelle : v1.4.6
Fichiers joints : cerbere.py, Prompt_cerbere.md
Dépendance : openpyxl (pip install openpyxl)

Le programme surveille c:\boitedereception\ et :
1. Convertit automatiquement les CSV mal formatés (encodage, séparateur)
2. Traite les xlsx (si csv correspondant dans refs, met à jour le csv)
3. Versionne (grand livre + journal) - SANS modifier le contenu des .txt
4. Dispatche vers les bons répertoires de c:\cx\
5. Sauvegarde vers c:\cxsauve\ avec archivage
6. Backup SSD quotidien si g:\cxssd\ accessible

Règles de dispatch (v1.4.6) :
- Prompt_*.md → prompts/
- con*.md → convs/
- autres .md → doc/
- data*.csv ou *pat*.csv → data/
- test*.csv → tests/
- logs*.csv → logs/
- autres *.csv → refs/
- *.html, *.css → ihm/
- *.xlsx → doc/ (après mise à jour éventuelle du csv dans refs)

⚠️ IMPORTANT : Les fichiers .txt ne doivent JAMAIS être modifiés !

Je voudrais [décrire l'évolution souhaitée].
```

---

## 🔧 Contraintes techniques

- **Python** : 3.13+ uniquement
- **Dépendances** : openpyxl (`pip install openpyxl`)
- **Encodage** : UTF-8 partout (BOM pour CSV uniquement)
- **Séparateurs CSV** : `;` colonnes, `,` multivaleurs
- **Timestamps** : Format `jj/mm/aaaa hh:mm:ss`
- **Format date SSD** : `jjmmaaaa` (ex: `10122025`)

---

## 📊 Métriques actuelles

| Métrique            | Valeur      |
| ------------------- | ----------- |
| Lignes de code      | ~780        |
| Taille fichier      | ~28 Ko      |
| Fonctions           | ~32         |
| Cycle surveillance  | 1 minute    |
| Attente inter-phase | 30 secondes |

---

## 🚀 Évolutions possibles

### Priorité haute

1. **Notification sonore** : Bip quand un fichier est traité ou en erreur
2. **Interface graphique** : Fenêtre tkinter avec statut en temps réel
3. **Exclusions** : Fichier de config pour exclure certains patterns du backup

### Priorité moyenne

4. **Compression archives** : Zipper les archives pour gagner de l'espace
5. **Retention policy** : Supprimer les archives de plus de N jours
6. **Logs fichier** : Écrire les logs dans un fichier en plus de la console

### Priorité basse

7. **API REST** : Exposer un endpoint pour interroger le statut
8. **Multi-répertoires** : Surveiller plusieurs répertoires d'entrée
9. **Plugins** : Système de hooks pour actions personnalisées

---

**Fin du prompt - Version 2.4.6**
