## Prompt_contexte

## Objet de ce fichier

Ce fichier doit être systématiquement joint au projet et disponible pour tous les chatsqui en feront partie.

Il fixe le cadre sur plusieurs paramètres : séparateurs de fichiers, méthodes de travail et contexte du projet.

---

## Contexte du projet

Le projet consiste à développer une application de recherche multilingue sur plus de 25 000 patients d'un cabinet d'orthodontie. Le développement est fait pour des utilisateurs majoritairement en France.

La philosophie du projet est **TDD (Test Driven Development)**. C'est-à-dire qu'avant tout développement on va passer un temps important avec des fichiers de test pour vérifier le comportement des applicatifs et les corriger sur cette base.

---

## Contraintes techniques

### Langage et versions

- Python 3.13+ uniquement (aucun downgrade, aucune bibliothèque dépréciée)
- Aucun outil obsolète accepté

### Environnement d'exécution

- Exécution `python script.py` normalement
- Ou exceptionnellement via scripts `.cmd` uniquement (aucun PowerShell requis)
- Scripts indépendants du chemin (détectent la racine avec `%~dp0`)
- Déploiement final envisagé sur AWS (EC2, S3, Lambda éventuel)

### Performance

- Temps de réponse cible : **< 10 secondes**
- Les programmes batch/CLI doivent être bavards : ne jamais rester plus de 5 secondes sans afficher quelque chose
- Afficher des barres de progression avec pourcentage pour les traitements longs (utiliser **tqdm**)
- Format de barre : `[████████░░░░░░░░░░░░] 40% - Ligne 2/5`

### Interface web (si applicable)

- Pages web responsive (PC, iPhone, iPad, Android)
- Mode clair/sombre auto ou manuel

---

## Spécifications techniques

### Encodage des fichiers

💡 **Règle simple** : UTF-8 partout, avec BOM uniquement pour Excel/CSV

- Fichiers Python (`.py`), Batch/CMD (`.bat`, `.cmd`), texte (`.txt`), markdown (`.md`) : **UTF-8 sans BOM**
- Fichiers CSV (`.csv`) ou Excel (`.xlsx`) : **UTF-8-SIG avec BOM** (obligatoire !!!)

### Versionning

Chaque fichier .py commence par les lignes suivantes **avant les imports** :

```python
#*TO*#
__pgm__ = "nom_du_programme.py"
__version__ = "0.0.0"
__date__ = "01/01/1970 00:00"
```

Exemple : toto.py V0.0.0 - 01/01/1970 00:00

**Important** : Ces valeurs seront automatiquement mises à jour par `horodateur.py`. Ne pas se soucier des valeurs réelles lors de la génération initiale.

#### Processus de gestion des fichiers

1. Les fichiers générés sont déposés dans `c:/g/boitedereception/`
2. `cerbere.py` sauvegarde la version originale dans `c:/gs/`
3. Le fichier est déplacé vers `c:/g/vrac/`
4. `horodateur.py` lit le fichier, met à jour les valeurs de version et date, puis le déplace vers :
   - `c:/g/` pour les fichiers `.py`
   - `c:/g/refs/` pour les fichiers `.csv` (après vérification encodage UTF-8-BOM, séparateurs)

#### Où sont les fichiers ?

Le projet est organisé et tous les fichiers sont positionnés comme suit à partir de la racine :

- à la racine tous les .py et .cmd

- dans /bases pour toutes les bases de données .db

- dans /data pour tous les csv de type pat*.csv. Le préfixe pat indique que c'est un fichier de patients et il doit donc être dans /data et non dans /refs.

- dans le sous répertoire /refs tous les csv de référence comme par exemple tags.csv, adjectifs.csv, ages.csv, angles.csv etc...

- dans le sous répertoire /tests tous les fichiers de test et d'audit : Leur nom commence par test et c'est en général mais pas toujours des .csv

Tous les .

### Format de version sémantique (SemVer)

Toutes les versions suivent le format **MAJOR.MINOR.PATCH** (ex: v1.2.3)

- **MAJOR** : Changements incompatibles (breaking changes)  
  Exemple : v3.x.x → v4.0.0
- **MINOR** : Ajouts de fonctionnalités rétrocompatibles  
  Exemple : v3.10.x → v3.11.0
- **PATCH** : Corrections de bugs rétrocompatibles  
  Exemple : v3.11.0 → v3.11.1

La date et l'heure dans le cartouche sont celles de la création de la version.

### Séparateurs CSV

- Séparateur de colonnes : `;` (point-virgule)
- Séparateur de multivaleurs : `,` (virgule)
- Commentaires : Lignes commençant par `#` (ignorées lors du traitement)

### Utilisation des CSV

Dans tous les CSV commencent par une ligne entête de colonne après d'éventuelles lignes de commentaires identifiées par # en début de ligne.

Tous les CSV sont en utf-8-sig sinon c'est affichage d'un message d'erreur et arrêt du traitement.
Tous les CSV ont une entête avec des noms de colonne comme par exemple : 
original;standard;synonymes;fr;en;de;es;it;pt;pl;ro;th;ar;cn

Ne jamais chercher dans des csv par position de colonne susceptible de varier mais uniquement par nom de colonne.
Donc le code cherche ce qu'il y a dans la colonne d'entête synonyme par exemple mais jamais dans la 3ème colonne !!!

## Display des programmes

### Affichage initial

Au minimum, chaque script signale qu'il démarre son traitement en affichant son nom, la version et la date.

Si le programme contient une fonction `main()`, celle-ci doit commencer par :

```python
def main():
    print(f"{__pgm__} V{__version__} - {__date__}")
    # reste du code...
```

### Niveaux d'affichage

Les programmes doivent permettre de voir ce qui se passe à deux niveaux :

#### 1. Pour le site web

- **Affichage DEBUG** : Commence systématiquement par `[DEBUG] `
  
  - Console de debug qu'on peut afficher ou non via une checkbox :
    
    ```html
    <input type="checkbox" id="debugCheckbox"> 
    Mode debug (affiche la console en bas de l'écran principal)
    ```
  
  - Les lignes de debug sont **toujours envoyées** à la page web, même si non affichées
  
  - Permet d'afficher rétroactivement tout l'historique si on coche la case

- **Affichage utilisateur** :
  
  - Pour les modes de recherche (progressif ou classique) : chaque étape active fait l'objet d'un affichage
    - Détection d'un pattern
    - Exécution d'un ordre SQL
  - L'affichage se fait dans une logique de chatbot :
    - Mode IA : avec scroll
    - Mode classique : zone fixe en haut de l'écran
  - Avant de rendre la main : message formatté à l'aide de `phrases_chatbot.csv`
  - Exemple : `🎯 J'ai trouvé exactement 42 patients avec bruxisme et béance latérale de moins de 30 ans en 1432 ms.`

#### 2. Pour l'interface CLI unitaire ou batch

- **Mode normal** : Affiche tout (équivalent console debug web)
- **Mode silencieux** : Option `--silent` pour désactiver les affichages détaillés
- Mêmes informations que sur le web dans la console de debug

### Fichier phrases_chatbot.csv

Structure : `usage;phrase;emoji`

- **Colonnes** :
  
  - `usage` : Contexte d'utilisation (ex: `final_exact`, `etape_patho`, `etape_age`)
  - `phrase` : Template de phrase avec placeholders
  - `emoji` : Emoji associé

- **Placeholders** :
  
  - `xx` : Sera remplacé par le nombre de patients
  - `{ff}` : Sera remplacé par le filtre appliqué (pathologie, âge, etc.)

- **Variabilisation** : Plusieurs phrases par usage pour varier les affichages

- **Fichier protégé** : Ce fichier peut être enrichi par l'utilisateur, ne **JAMAIS l'écraser**

Exemple :

```csv
usage;phrase;emoji
final_exact;J'ai trouvé exactement xx patients !;🎯
etape_patho;Avec {ff} : xx patients;🔬
```

---

## Affichage des chemins de fichiers

Chaque affichage de nom de fichier dans la console doit inclure le **chemin absolu complet**.

Exemples :

- Windows : `D:\find\py\build_synonyms.py`
- Linux : `/home/user/projet/build_synonyms.py`

Cela s'applique notamment aux :

- Messages de début de traitement
- Messages de fin de traitement
- Messages d'erreur
- Logs de progression

---

## 🔒 Règles de protection des fichiers utilisateur

### Fichiers à NE JAMAIS créer/écraser

**CRITIQUE - RÈGLES ABSOLUES** :

Les fichiers qui contiennent des données saisies par l'utilisateur et que tu n'as pas créés ne doivent **JAMAIS** être créés, modifiés ou écrasés par les programmes.

Exemples (liste non exhaustive) :

- `motsvides.csv` (contient les mots vides de l'utilisateur)
- ages.csv
- glossaire.csv
- Tout autre fichier CSV d'entrée utilisateur...

### Fichiers d'exemple

Pour fournir des exemples, créer des fichiers avec des noms **DISTINCTS** contenant `_EXEMPLE` :

- `transforme_EXEMPLE.csv` (à renommer par l'utilisateur en `transforme.csv`)
- `pathologiessaisies_EXEMPLE.csv` (à renommer en `pathologiessaisies.csv`)
- `test_data_EXEMPLE.csv` (données de test)

Les fichiers d'exemple doivent inclure dans leur cartouche une note expliquant qu'ils doivent être renommés.

---

## Gestion des données

### Principe général : Aucune donnée en dur

**Règle stricte** : Les programmes ne doivent contenir aucune donnée en dur, sauf exceptions listées ci-dessous.

### Exceptions autorisées (données en dur)

Les seules données pouvant être en dur dans le code sont :

1. **Valeurs binaires simples** : M/F, Oui/Non, True/False
2. **Constantes techniques** : encodages, séparateurs, formats
3. **Énumérations exhaustives** définies dans le prompt :
   - Exemple : `mode = "", "R", "X", "D"` si les 4 valeurs sont listées exhaustivement
   - Ces valeurs doivent être exactement celles spécifiées, sans ajout

### Tout le reste doit être fourni via fichiers externes

- Listes de synonymes → `synonyms.csv`
- Cas cliniques → `cas_cliniques.csv`
- Tags, catégories → fichiers dédiés
- Mots vides → `transforme.csv`
- Pathologies → `pathologiessaisies.csv`
- Phrases d'affichage → `phrases_chatbot.csv`

### Structure des fichiers de données

Fournir des fichiers placeholder avec structure correcte :

- `data/synonyms.csv`
- Par langue si besoin : `synonyms.fr.csv`, `synonyms.en.csv`, etc.

Une étape de remplissage enrichira ces fichiers pour garantir la qualité de la recherche orientée utilisateur.

### Stratégie multilingue

Définir l'approche la plus adaptée :

- Garder uniquement le français
- Traduire partiellement
- Maintenir une copie par langue

Contrainte : **< 10 Mo par langue**

---

## Architecture de recherche

L'objectif est de construire un outil de **recherche hybride** :

### 1. Filtrage SQL initial

Premier filtrage par requête SQL sur certains champs indexés.

La donnée la plus importante dans une recherche orthodontique est la **pathologie**. C'est la raison pour laquelle les pathologies ont droit à quelques particularités :

- Ce sont les données que l'on va rechercher en premier en analysant une question
- Pour aller vite, la base de données est organisée avec :
  - Une table des pathologies indexée
  - Une table de jointure associée indexée
- On veut que ça aille **vite, très vite**
- Si tu vois des améliorations possibles, n'hésite pas à les proposer

### 2. Recherche FTS5

Sur les données résiduelles, recherche sur une colonne `search_text` qui sera la concaténation de différentes informations sur le patient, transformée et normalisée.

### 3. Correction orthographique

Une solution de correction d'orthographe sera adjointe ultérieurement avec la recherche FTS5.

### Exemple de structure

On aura dans ce projet plusieurs bases de taille différente pour tester les temps de réponse en fonction de la taille de la base.

Le nom de la base contiendra un **N** qui est le nombre de patients de la base.

Ainsi les noms pourront varier entre `base2.db` et `base200000.db` pour la plus grosse base supportée.

Les noms des fichiers intermédiaires suivent la même logique : `brutN.csv` et `netN.csv`.

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

## 📊 Index à créer

```sql
CREATE INDEX idx_patients_sexe ON patients(sexe);
CREATE INDEX idx_patients_age ON patients(age);
CREATE INDEX idx_patients_datenaissance ON patients(datenaissance);
CREATE INDEX idx_patients_pathologies_patient_id ON patients_pathologies(patient_id);
CREATE INDEX idx_patients_pathologies_pathologie_id ON patients_pathologies(pathologie_id);
CREATE INDEX idx_pathologies_nom ON pathologies(pathologie);
```

**6 index**

---

---

## Organisation du code

### Modularité

- Création systématique d'un fichier Python pour chaque opération de transformation de données
- But : Reproduire ces actions sur d'autres fichiers
- Chaque transformation doit être réutilisable et testable

### Debug et monitoring

- Debug intégré dès la conception
- Affichage optionnel des performances
- Affichage optionnel des résultats intermédiaires
- Logs détaillés pour faciliter le diagnostic

En ce qui concerne les programmes CLI la règle de base c'est que s'il n'y a pas de paramètres ça doit être traité comme l'aide -h. Cela explique alors les options et les paramètres. En tout cas jamais de traitement si on ne donne pas d'option ou de paramètres après le .py

---

## Instructions à l'IA

- **Respecter strictement les règles** : Ne rien inventer, suivre exactement les spécifications

- **Pas de validations inutiles** : Aller directement au résultat, ne pas demander de confirmations superflues

- **Amélioration continue** : Intégrer toute amélioration du prompt générique dans la version suivante du document

- **Résultats exploitables** : Produire des résultats immédiatement exploitables (scripts, fichiers, documentation)

- **Qualité avant tout** : Assurer robustesse, modularité et maintenabilité
  
  > « Le prix s'oublie, la qualité reste »

- **Pas de downgrade** : Python 3.13 uniquement, aucun outil obsolète

- **Résumé systématique** : À la fin de chaque étape, fournir un résumé clair des actions réalisées

- **Données externes** : Privilégier l'utilisation de fichiers externes pour toutes les données (sauf exceptions listées)

- **Test-Driven Development** : Penser aux tests dès la conception, créer des fichiers de test quand pertinent

- **Protection des données utilisateur** : Ne JAMAIS écraser les fichiers protégés listés dans la section 🔒

- **On n'invente rien** : Fichiers programmes, ou exemples ou autres s'ils sont cités comme fournis doivent être fournis. Si ce n'est pas le cas il faut les demander et non prendre l'initiative de les créer.

- **Pas de cow-boy** : Tu ne te lances pas comme un cow-boy si tu as des incertitudes ou des ambigüités sur ce que je demande. Donc analyse bien la demande et fais toi préciser les choses nécessaires avant de faire quoi que ce soit.
  
  Je te demande donc dans ce projet de ma réactualiser à chaque réponse un document réactualisé  appelé nc qui résume mes questions et tes réponses de façon synthétique. Au fur et à mesure de la conversation le document s'enrichira. A chaque échange affiche la date et l'heure dès que tu commences à traiter ma question et rajoute la dans le document.
  En début de chaque conversation, je te donnerai son nom par nc=[nom]
   Le fichier de synthèse doit s'appeler conv_[nom].md (espaces → underscores)
  Si je ne t'ai pas donné le nom de la conversation, demande le moi avant de créer la synthèse.

Deuxième demande : quand tu crées des documents 
Prompt appelle les toujours Prompt_xxx. Quand c'est des programmes .py ne change jamais ni le nom ni la signature sans demande explicite. 

Je te demande également de systématiquement me faire les prompts complets permettant de recréer tous les .py en indiquant les fichiers à rajouter en pj. Le but c'est de pouvoir à tout moment refaire tous les .py à partir de rien uniquement avec les .md et les pj  nécessaires. Par exemple : 
python creeexemple.py           # → Affiche l'aide
python creeexemple.py all       # → Génère tout
python creeexemple.py all -d    # → Génère avec debug
python creeexemple.py --chapitre 5 -v  # → Chapitre 5 en verbose

Et si tu n'es pas sûr d'une demande qu'il te faille des précisions ou corriger des ambigüités ou si tu as des suggestions qui te paraissent meilleures que mon analyse ne fais rien et demande moi des précisions ou fais moi tes suggestions. Elles seront toujours les bienvenues.

Chaque fois que tu crées un .py il faut qu'il puisse être utilisé en cli. Et en cli quand on ne lui donne pas d'argument il faut systématiquement qu'il affiche les arguments et les options disponibles. Et les options -v et --verbose -d et -debug seront toujours proposées et équivalentes (seules les courtes -d et -v seront affichées)

Ne jamais me proposer de copier des trucs du genre : 

cd C:\2702s
pip install beautifulsoup4    # Si pas déjà installé
html.cmd chapitre1

Car je l'exécute sans regarder et ça finit par : 

C:\2702s>pip install beautifulsoup4    # Si pas déjà installé
Defaulting to user installation because normal site-packages is not writeable
ERROR: Invalid requirement: '#': Expected package name at the start of dependency specifier
  Pareil pour les USERNAME à remplacer pour mon identifiant sur github ou autre. 
Ce qu'il faut retenir c'est que je ne veux que des trucs copiables sans me poser de question. Si tu as besoin que je te donne USERNAME sur github tu demandes pour pouvoir me donner un cmd copiable à l'aveugle.

## Commentaires dans les fichiers

### Convention pour ignorer du texte

Dans les requêtes et documents, le texte entre balises `[COMMENTAIRE]` et `[FIN COMMENTAIRE]` doit être ignoré par l'IA.

Les lignes commençant par `REM` dans le contexte des requêtes doivent également être ignorées ainsi que celles commençant par # dans les .py ou les .csv.

Pour les pages .htm ou .html les commentaires sont entre les balises /* et */

Par exemple :

/*═════════════════════════════════════════
           MODULE 2 : STRUCTURE & LAYOUT (CSS + HTML)
  ══════════════════════════════════════════*/

Autre Exemple :

```
lorem

[COMMENTAIRE]
Ceci est un commentaire pour expliquer le contexte,
mais ne doit pas être pris en compte dans la réponse.
[FIN COMMENTAIRE]

REM Ceci aussi est ignoré

ipsum
```

est équivalent à :

```
lorem

ipsum
```

---

## Checklist de livraison

Avant de livrer un fichier, vérifier :

- [ ] Encodage correct (UTF-8 sans BOM pour `.py`/`.cmd`, UTF-8-SIG pour `.csv`)
- [ ] Séparateurs corrects dans les CSV (`;` et `,`)
- [ ] Pas de données en dur (sauf exceptions autorisées)
- [ ] Fichiers protégés non écrasés
- [ ] Chemins absolus dans les affichages console
- [ ] Gestion d'erreurs robuste
- [ ] Messages de progression pour traitements longs (tqdm)
- [ ] Documentation claire et résumé fourni
- [ ] Variables `__pgm__`, `__version__`, `__date__` présentes avant les imports
- [ ] Affichage initial dans `main()` si applicable

---

**FIN DU DOCUMENT** - Version v1.1.0
