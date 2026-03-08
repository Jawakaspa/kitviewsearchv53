# Prompt Cerbere - Gardien du Projet Kitview

**Version :** 2.4.1  
**Date :** 08/12/2025  
**Usage :** Prompt à utiliser pour faire évoluer cerbere.py

---

## 🎯 Objectif de ce prompt

Ce document contient toutes les informations nécessaires pour reprendre le développement de `cerbere.py` dans une nouvelle conversation Claude.

---

## 📋 Contexte du projet

### Qu'est-ce que cerbere.py ?

`cerbere.py` est un **démon Python** (programme qui tourne en continu) qui surveille le répertoire `c:\boitedereception\` et effectue automatiquement :

1. **VALIDATION** : Vérifie encodage et format des fichiers
2. **VERSIONNING** : Attribue et incrémente les versions (système comptable)
3. **DISPATCHING** : Distribue les fichiers vers les bons répertoires
4. **SAUVEGARDE** : Copie incrémentale avec archivage vers `c:\cxsauve\`
5. **BACKUP SSD** : Backup quotidien sur SSD externe si branché

### Version actuelle

**cerbere.py v1.4.1** - 08/12/2025

---

## 🗂️ Architecture des répertoires

```
c:\boitedereception\     # Entrée : déposer les fichiers ici
c:\cx\                   # Projet principal
c:\cx\hmod\              # Modules HTML (hmod*.txt, hmod*.md)
c:\cx\ihm\               # Pages HTML générées (searchX.html)
c:\cx\db\                # Bases de données .db
c:\cx\prompts\           # Fichiers Prompt_*.md
c:\cx\doc\               # Documentation (doc*.md, .xlsx, .docx, .txt)
c:\cx\convs\             # Conversations (con*.md)
c:\cx\ztri\              # Documents non triés (autres .md, CSV sans pattern, etc.)
c:\cx\data\              # CSV data*.csv et pat*.csv
c:\cx\tests\             # CSV test*.csv
c:\cx\logs\              # CSV logs*.csv
c:\cx\refs\              # grandlivre.csv + journal.csv
c:\cxsauve\              # Sauvegarde incrémentale
c:\cxarchives\           # Archives des anciennes versions
g:\cxssd\                # Backup SSD (si branché)
```

---

## 📜 Règles de dispatching (v1.4.0)

### Fichiers Markdown (.md)

| Pattern                  | Destination      | Exemple               |
| ------------------------ | ---------------- | --------------------- |
| `Prompt_*` ou `prompt_*` | `c:\cx\prompts\` | Prompt_cerbere.md     |
| `doc*`                   | `c:\cx\doc\`     | documentation_api.md  |
| `con*`                   | `c:\cx\convs\`   | conversation_debug.md |
| Autres `.md`             | `c:\cx\ztri\`    | notes.md              |

### Fichiers CSV

| Pattern    | Destination    | Exemple           |
| ---------- | -------------- | ----------------- |
| `data*`    | `c:\cx\data\`  | data_patients.csv |
| `pat*`     | `c:\cx\data\`  | patients2024.csv  |
| `test*`    | `c:\cx\tests\` | test_import.csv   |
| `logs*`    | `c:\cx\logs\`  | logs_erreurs.csv  |
| Autres `*` | `c:\cx\refs\`  | inconnu.csv       |

### Autres fichiers

| Pattern    | Extension                | Destination       |
| ---------- | ------------------------ | ----------------- |
| `hmod*`    | `.py`                    | `c:\cx\` (racine) |
| `hmod*`    | `.txt`, `.md`            | `c:\cx\hmod\`     |
| `*`        | `.db`                    | `c:\cx\db\`       |
| `*`        | `.html`                  | `c:\cx\ihm\`      |
| `*`        | `.py`                    | `c:\cx\`          |
| `*`        | `.xlsx`, `.docx`, `.txt` | `c:\cx\doc\`      |
| Autres `*` | *                        | `c:\cx\ztri\`     |

---

## 🔢 Système de versionning

### Fichiers de contrôle

- `c:\cx\refs\grandlivre.csv` : Situation actualisée (dernière version de chaque fichier)
- `c:\cx\refs\journal.csv` : Historique complet de toutes les versions

### Format CSV

```csv
nomdufichier;version;timestamp
cerbere.py;V1.4.0;07/12/2025 23:09:41
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

## ✅ Règles de validation

### Fichiers CSV

- **Encodage** : UTF-8 avec BOM (`utf-8-sig`) obligatoire
- **Séparateur colonnes** : `;` (point-virgule) obligatoire
- **Séparateur multivaleurs** : `,` (virgule) obligatoire
- **Commentaires** : Lignes commençant par `#` ignorées (peut y en avoir plusieurs)

### Autres fichiers

- **Encodage** : UTF-8 sans BOM obligatoire
- Pas de validation de contenu

### Comportement en cas d'erreur

- Le fichier reste dans `c:\boitedereception\`
- Message d'erreur affiché avec raison
- Action requise : corriger manuellement

---

## 🔄 Cycle de surveillance

```
Toutes les minutes :
  1. IMPORT (traiter c:\boitedereception\)
  2. Attendre 30s
  3. SAUVEGARDE (c:\cx\ → c:\cxsauve\)
  4. Attendre 30s
  5. BACKUP SSD (si g:\cxssd\ accessible et qu'il n'y a pas encore de backup du jour au format jjmmaaaa)
  6. Reboucle
```

---

## 🛠 Historique des versions

### v1.4.1 (08/12/2025)

- **Correction dispatching CSV** :
  - CSV sans pattern connu → `refs\` (et non `ztri\`)

### v1.4.0 (07/12/2025)

- **Corrections dispatching** :
  - `zarchives\` renommé en `convs\` (con*.md)
  - Ajout pattern `pat*.csv` → `data\`
  - CSV sans pattern connu → `ztri\` (au lieu de `refs\`)

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
- **Renommage patterns CSV** :
  - `patients*.csv` → `data*.csv`
  - `tests*.csv` → `test*.csv`

### v1.2.0 (30/11/2025)

- **Nouvelles règles de dispatching .md** :
  - `doc*.md` → `documentation/`
  - `con*.md` → `zarchives/`
  - Autres `.md` → `zatrier/`
- **Nouveaux répertoires** : `documentation/`, `zarchives/`, `zatrier/`
- Renommage `docs/` → `documentation/`

### v1.1.0 → v1.1.4 (24/11/2025)

- **CRITIQUE** : Les fichiers `.txt` ne sont plus modifiés
- Versionning dans grand livre uniquement, contenu intact
- Suppression de la fonction `update_version_txt()`

### v1.0.0 → v1.0.3 (24/11/2025)

- Version initiale
- Correctifs validation CSV multi-commentaires
- Ajout règle dispatch `hmod*.py` → racine

---

## 📌 Pour commencer une nouvelle conversation

Pour une conversation sur cerbere.py, joindre :

1. **cerbere.py** (version actuelle v1.4.1)
2. **Prompt_cerbere.md** (ce document v2.4.1)

Copier-coller ce texte au début de la conversation :

```
Je travaille sur cerbere.py, un démon Python de validation, versionning et sauvegarde automatique.

Version actuelle : v1.4.1
Fichiers joints : cerbere.py, Prompt_cerbere.md

Le programme surveille c:\boitedereception\ et :
1. Valide les fichiers (encodage, format CSV)
2. Versionne (grand livre + journal) - SANS modifier le contenu des .txt
3. Dispatche vers les bons répertoires de c:\cx\
4. Sauvegarde vers c:\cxsauve\ avec archivage
5. Backup SSD quotidien si g:\cxssd\ accessible

Règles de dispatch (v1.4.1) :
- Prompt_*.md → prompts/
- doc*.md → doc/
- con*.md → convs/
- autres .md → ztri/
- data*.csv ou pat*.csv → data/
- test*.csv → tests/
- logs*.csv → logs/
- autres *.csv → refs/

⚠️ IMPORTANT : Les fichiers .txt (modules hmod) ne doivent JAMAIS être modifiés !
Ils contiennent du JS avec commentaires multilignes qui seraient cassés.

Je voudrais [décrire l'évolution souhaitée].
```

---

## 🔧 Contraintes techniques

- **Python** : 3.13+ uniquement
- **Encodage** : UTF-8 partout (BOM pour CSV uniquement)
- **Séparateurs CSV** : `;` colonnes, `,` multivaleurs
- **Timestamps** : Format `jj/mm/aaaa hh:mm:ss`
- **Format date SSD** : `jjmmaaaa` (ex: `07122025`)
- **Pas de dépendances externes** : Uniquement bibliothèque standard Python

---

## 📊 Métriques actuelles

| Métrique            | Valeur      |
| ------------------- | ----------- |
| Lignes de code      | ~680        |
| Taille fichier      | ~25 Ko      |
| Fonctions           | ~28         |
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

**Fin du prompt - Version 2.4.1**
