# Prompt Cerbère Généralisé - Gardien Multi-Cibles du Projet Kitview

**Version :** 3.0.0  
**Date :** 09/01/2026  
**Usage :** Prompt à utiliser pour créer ou faire évoluer cerbere.py v2.x (version généralisée)

---

## 🎯 Objectif de ce prompt

Ce document contient toutes les informations nécessaires pour créer ou reprendre le développement de `cerbere.py` dans sa version généralisée supportant :
- **Multi-cibles** : Déploiement vers plusieurs environnements (tests, prod)
- **Règles externalisées** : Configuration des règles de dispatch dans des fichiers CSV
- **Exécution distante** : Exécution de commandes Python via fichiers déposés

---

## 📋 Contexte du projet

### Qu'est-ce que cerbere.py (généralisé) ?

`cerbere.py` est un **démon Python** (programme qui tourne en continu) qui surveille plusieurs répertoires d'entrée et effectue automatiquement :

1. **VALIDATION** : Vérifie encodage et format des fichiers
2. **CONVERSION** : Convertit automatiquement les CSV mal formatés (UTF-8-SIG, séparateur `;`)
3. **TRAITEMENT XLSX** : Convertit les xlsx si un csv correspondant existe dans refs de la cible
4. **VERSIONNING** : Attribue et incrémente les versions (système comptable) - **indépendant par cible**
5. **DISPATCHING** : Distribue les fichiers vers les bons répertoires selon les règles externalisées
6. **SAUVEGARDE** : Copie incrémentale avec archivage - **indépendante par cible**
7. **EXÉCUTION DISTANTE** : Exécute des commandes Python et retourne les résultats
8. **BACKUP SSD** : Backup quotidien sur SSD externe si branché

### Version cible

**cerbere.py v2.0.0** - Janvier 2026

### Dépendances

- **Python 3.13+**
- **openpyxl** : `pip install openpyxl` (pour conversion xlsx → csv)

---

## 🗂️ Architecture des répertoires

### Répertoires d'entrée (3 points d'entrée)

```
c:\cerberetests\              # Fichiers destinés à l'environnement de tests
    grandlivre.csv            # Situation actuelle des versions (tests)
    journal.csv               # Historique des versions (tests)
    cerbere_config.csv        # Règles de dispatch pour tests
    *.exec.csv                # Commandes à exécuter (tests)

c:\cerbereprod\               # Fichiers destinés à la production
    grandlivre.csv            # Situation actuelle des versions (prod)
    journal.csv               # Historique des versions (prod)
    cerbere_config.csv        # Règles de dispatch pour prod
    *.exec.csv                # Commandes à exécuter (prod)

c:\cerbereall\                # Fichiers à déployer vers TESTS ET PROD
    (pas de grandlivre/journal - utilise ceux des cibles)
    *.exec.csv                # Commandes à exécuter (sur les deux)
```

### Cibles et leurs sauvegardes

```
# Environnement TESTS
c:\cx\                        # Projet tests (fichiers .py, etc.)
c:\cx\ihm\                    # Pages HTML
c:\cx\db\                     # Bases de données .db
c:\cx\prompts\                # Fichiers Prompt_*.md
c:\cx\doc\                    # Documentation
c:\cx\convs\                  # Conversations (con*.md)
c:\cx\ztri\                   # Fichiers non reconnus
c:\cx\data\                   # CSV data*.csv et *pat*.csv
c:\cx\tests\                  # CSV test*.csv
c:\cx\logs\                   # CSV logs*.csv, logrecherche.csv
c:\cx\refs\                   # Autres CSV
c:\cxsauve\                   # Sauvegarde incrémentale tests
c:\cxarchives\                # Archives des anciennes versions tests

# Environnement PROD
c:\kitviewsearchV5\           # Projet production
c:\kitviewsearchV5\ihm\       # (mêmes sous-répertoires)
c:\kitviewsearchV5\...
c:\kitviewsearchV5sauve\      # Sauvegarde incrémentale prod
c:\kitviewsearchV5archives\   # Archives des anciennes versions prod

# Backup SSD (commun)
g:\cxssd\                     # Backup SSD quotidien
```

---

## 📄 Structure des fichiers de configuration

### 1. cerbere_config.csv (dans chaque dossier cerbere)

Ce fichier définit **la cible** et **les règles de dispatch** pour ce point d'entrée.

```csv
# Configuration Cerbère pour environnement TESTS
# cerbere_config.csv - c:\cerberetests\
#
# SECTION CIBLE
# Définit où vont les fichiers de ce point d'entrée
type;parametre;valeur
cible;nom;tests
cible;chemin;c:\cx
cible;sauve;c:\cxsauve
cible;archives;c:\cxarchives
cible;actif;oui
#
# SECTION REGLES DE DISPATCH
# pattern;extension;destination;commentaire
# - pattern : glob pattern (* = tout, *pat* = contient pat, data* = commence par data)
# - extension : .py, .csv, .md, .html, etc. (avec le point)
# - destination : sous-répertoire cible (vide = racine)
# - commentaire : description de la règle
#
# IMPORTANT : Les règles sont évaluées dans l'ordre, la PREMIERE qui matche gagne
# Donc mettre les règles spécifiques AVANT les règles générales
regle;Prompt_*;.md;prompts;Prompts de projet
regle;con*;.md;convs;Conversations
regle;*;.md;doc;Markdown par défaut
regle;logrecherche*;.csv;logs;Logs de recherche
regle;data*;.csv;data;Données
regle;*pat*;.csv;data;Fichiers patients (contient pat)
regle;test*;.csv;tests;Fichiers de test
regle;logs*;.csv;logs;Autres logs
regle;*;.csv;refs;CSV par défaut vers refs
regle;*;.py;;Scripts Python à la racine
regle;*;.html;ihm;Pages web
regle;*;.css;ihm;Feuilles de style
regle;*;.db;db;Bases de données
regle;*;.xlsx;doc;Documents Excel
regle;*;.docx;doc;Documents Word
regle;*;.txt;doc;Documents texte
regle;*;*;ztri;Tout le reste vers ztri
```

**Pour la PROD** (`c:\cerbereprod\cerbere_config.csv`) : même structure mais avec :
```csv
cible;nom;prod
cible;chemin;c:\kitviewsearchV5
cible;sauve;c:\kitviewsearchV5sauve
cible;archives;c:\kitviewsearchV5archives
```

### 2. grandlivre.csv (situation actuelle des versions)

```csv
nomdufichier;version;timestamp
cerbere.py;V1.4.6;10/12/2025 14:37:13
search.py;V1.0.26;07/01/2026 14:52:51
```

### 3. journal.csv (historique complet)

```csv
nomdufichier;version;timestamp
cerbere.py;V1.0.0;05/12/2025 21:15:55
cerbere.py;V1.0.1;08/12/2025 20:40:03
cerbere.py;V1.4.6;10/12/2025 14:37:13
```

---

## ⚡ Fichiers d'exécution distante (*.exec.csv)

### Format du fichier d'entrée

Nom : `[nom].exec.csv` (ex: `tests.exec.csv`, `build.exec.csv`)

```csv
# Commandes à exécuter
# Format : commande;arguments
#
commande;arguments
python;c:\cx\search.py --query "bruxisme"
python;c:\cx\pipeline.py --rebuild
python;c:\cx\analyse.py -v
```

### Format du fichier de sortie

Après exécution, le fichier est renommé en `[nom].exec.done.csv` et une colonne résultat est ajoutée :

```csv
# Exécution terminée le 09/01/2026 14:32:15
# Durée totale : 45.2 secondes
#
commande;arguments;statut;resultat;duree_sec
python;c:\cx\search.py --query "bruxisme";OK;42 patients trouvés;2.3
python;c:\cx\pipeline.py --rebuild;OK;Pipeline rebuilt;35.1
python;c:\cx\analyse.py -v;ERREUR;FileNotFoundError: base100.db;0.4
```

### Règles d'exécution

- Les fichiers `*.exec.csv` déposés dans `cerberetests` sont exécutés avec `c:\cx` comme répertoire de travail
- Les fichiers `*.exec.csv` déposés dans `cerbereprod` sont exécutés avec `c:\kitviewsearchV5` comme répertoire de travail
- Les fichiers `*.exec.csv` déposés dans `cerbereall` sont exécutés **deux fois** (une fois par cible)
- Seules les commandes commençant par `python` sont autorisées (sécurité)
- Le fichier est renommé en `.done.csv` et reste dans le dossier d'entrée pour consultation

---

## 📜 Règles de dispatching

### Traitement préliminaire xlsx

**Avant le dispatching normal**, pour chaque fichier `.xlsx` :
1. Vérifier si un fichier `.csv` de même nom existe dans `refs/` de la cible
2. Si oui : convertir le xlsx en csv (utf-8-sig, séparateur `;`) et remplacer le csv existant
3. **Dans tous les cas** : le xlsx est ensuite dispatché vers `doc/` (pas supprimé)

### Priorité des règles

Les règles sont évaluées **dans l'ordre du fichier** `cerbere_config.csv`. La première règle qui matche gagne.

**Exemple** : Si `logrecherche.csv` arrive :
1. Teste `regle;Prompt_*;.md;...` → NON (extension différente)
2. Teste `regle;con*;.md;...` → NON (extension différente)
3. ...
4. Teste `regle;logrecherche*;.csv;logs;...` → **OUI !** → va dans `logs/`

---

## 🔄 Conversion automatique des CSV

### Comportement

Quand un fichier CSV arrive :

1. **Vérification** : encodage et séparateur
2. **Si non conforme** : conversion automatique
   - Détection de l'encodage (utf-8, utf-8-sig, latin-1, cp1252)
   - Détection du séparateur (`,`, `;`, `\t`)
   - Conversion vers : **utf-8-sig** + séparateur **`;`**
3. **Si conversion réussie** : traitement normal
4. **Si conversion échoue** : fichier reste dans le dossier d'entrée

### Format CSV standard

- **Encodage** : UTF-8 avec BOM (`utf-8-sig`) obligatoire
- **Séparateur colonnes** : `;` (point-virgule) obligatoire
- **Séparateur multivaleurs** : `,` (virgule)
- **Commentaires** : Lignes commençant par `#` ignorées

---

## 📢 Système de versionning

### Fichiers de contrôle (PAR CIBLE)

- `c:\cerberetests\grandlivre.csv` : Situation actualisée (tests)
- `c:\cerberetests\journal.csv` : Historique complet (tests)
- `c:\cerbereprod\grandlivre.csv` : Situation actualisée (prod)
- `c:\cerbereprod\journal.csv` : Historique complet (prod)

### Règles de version

- Nouveau fichier : `V1.0.0`
- Fichier existant : Incrémente le dernier nombre (`V1.0.0` → `V1.0.1`)
- Format : `MAJOR.MINOR.PATCH`
- La version dans le grand livre fait **référence**

---

## ⚠️ RÈGLE CRITIQUE : Fichiers à NE JAMAIS MODIFIER

### Extensions à ne JAMAIS modifier (contenu inchangé)

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
Initialisation :
  - Charger les configurations de chaque cerbere* 
  - Vérifier/créer les répertoires cibles
  - Initialiser les fichiers de version si absents

Toutes les minutes :
  1. POUR CHAQUE dossier d'entrée (cerberetests, cerbereprod, cerbereall) :
     a. Phase 0 : Exécution des *.exec.csv
     b. Phase 1 : Traitement préliminaire xlsx
     c. Phase 2 : Traitement normal des autres fichiers
  2. Attendre 30s
  3. POUR CHAQUE cible active :
     - SAUVEGARDE (cible → cible_sauve)
  4. Attendre 30s
  5. BACKUP SSD (si g:\cxssd\ accessible et pas de backup du jour)
  6. Reboucle
```

---

## 🛠 Points d'attention pour le développement

### Structure suggérée du code

```python
class CibleConfig:
    """Configuration d'une cible de déploiement"""
    nom: str                    # "tests" ou "prod"
    chemin: str                 # c:\cx ou c:\kitviewsearchV5
    sauve: str                  # répertoire de sauvegarde
    archives: str               # répertoire d'archives
    actif: bool                 # actif ou non
    regles: list[tuple]         # [(pattern, ext, dest, comment), ...]

class PointEntree:
    """Point d'entrée de fichiers"""
    chemin: str                 # c:\cerberetests, c:\cerbereprod, c:\cerbereall
    cibles: list[CibleConfig]   # Une ou deux cibles
    grandlivre: str             # Chemin vers grandlivre.csv
    journal: str                # Chemin vers journal.csv

def charger_configuration() -> list[PointEntree]:
    """Charge la config de tous les points d'entrée"""
    pass

def traiter_fichier(filepath: str, point_entree: PointEntree):
    """Traite un fichier entrant pour toutes les cibles du point d'entrée"""
    pass

def executer_commandes(exec_file: str, cible: CibleConfig):
    """Exécute les commandes d'un fichier .exec.csv"""
    pass
```

### Gestion du cas `cerbereall`

Pour `cerbereall` :
- Pas de `grandlivre.csv` / `journal.csv` propre
- Le versionning utilise **celui de chaque cible** :
  - Si le fichier va dans tests ET prod, la version est incrémentée **dans les deux**
  - Les versions peuvent donc différer entre tests et prod si un fichier a été déployé uniquement dans l'un des deux avant
- Les règles de dispatch viennent des fichiers `cerbere_config.csv` de chaque cible

---

## 📌 Pour commencer une nouvelle conversation

Pour une conversation sur cerbere.py généralisé, joindre :

1. **cerbere.py** (version actuelle v1.4.6 comme base)
2. **Prompt_cerbere_generalise.md** (ce document v3.0.0)
3. **Prompt_contexte2312.md** (contexte projet)

Copier-coller ce texte au début de la conversation :

```
Je travaille sur cerbere.py v2.x, la version généralisée multi-cibles.

Version actuelle de base : v1.4.6
Fichiers joints : cerbere.py, Prompt_cerbere_generalise.md, Prompt_contexte2312.md
Dépendance : openpyxl (pip install openpyxl)

Nouvelles fonctionnalités v2.x :
1. Multi-cibles : 3 points d'entrée (cerberetests, cerbereprod, cerbereall)
2. Règles externalisées : cerbere_config.csv dans chaque point d'entrée
3. Versionning indépendant : grandlivre/journal par cible (dans cerberetests et cerbereprod)
4. Exécution distante : fichiers *.exec.csv pour lancer des commandes Python
5. Sauvegardes indépendantes : cxsauve pour tests, kitviewsearchV5sauve pour prod

Je voudrais [décrire l'évolution souhaitée].
```

---

## 🔧 Contraintes techniques

- **Python** : 3.13+ uniquement
- **Dépendances** : openpyxl (`pip install openpyxl`)
- **Encodage** : UTF-8 partout (BOM pour CSV uniquement)
- **Séparateurs CSV** : `;` colonnes, `,` multivaleurs
- **Timestamps** : Format `jj/mm/aaaa hh:mm:ss`
- **Format date SSD** : `jjmmaaaa` (ex: `09012026`)

---

## 📊 Métriques estimées (v2.0)

| Métrique            | Valeur estimée |
| ------------------- | -------------- |
| Lignes de code      | ~1200-1500     |
| Taille fichier      | ~45-55 Ko      |
| Fonctions           | ~45-50         |
| Classes             | 2-3            |
| Cycle surveillance  | 1 minute       |
| Attente inter-phase | 30 secondes    |

---

## 🚀 Évolutions possibles (post v2.0)

### Priorité haute

1. **Interface graphique** : Fenêtre tkinter avec statut en temps réel et indicateur par cible
2. **Notification sonore** : Bip quand un fichier est traité ou en erreur
3. **Logs fichier** : Écrire les logs dans un fichier en plus de la console

### Priorité moyenne

4. **Dry-run mode** : Option pour simuler sans rien déplacer
5. **Exclusions** : Fichier de config pour exclure certains patterns du backup
6. **Compression archives** : Zipper les archives pour gagner de l'espace

### Priorité basse

7. **API REST** : Exposer un endpoint pour interroger le statut
8. **Webhooks** : Notifier une URL quand un fichier est traité
9. **Plugins** : Système de hooks pour actions personnalisées

---

**Fin du prompt - Version 3.0.0**
