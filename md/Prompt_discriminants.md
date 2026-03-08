# Prompt_discriminants.md

## Objectif

Créer le programme `discriminants.py` qui génère le fichier `discriminants.csv` contenant les mots-clés et caractères spéciaux discriminants des langues gérées par le projet.

## Contexte

Le projet Kitview gère une recherche multilingue sur des patients d'orthodontie. La détection de la langue d'une requête utilisateur est une étape clé. Ce programme génère un fichier de référence des éléments discriminants permettant d'identifier chaque langue.

## Fichiers à joindre en PJ

1. **commun.csv** - Fichier de configuration contenant la colonne `languescibles` listant toutes les langues cibles du projet
2. **Prompt_contexte0412.md** - Fichier de contexte général du projet (conventions, encodages, etc.)

## Spécifications fonctionnelles

### Entrée
- `commun.csv` : fichier CSV (UTF-8-BOM, séparateur `;`) contenant une colonne `languescibles` avec les codes langues (fr, en, de, th, es, it, pt, pl, ro, ar, cn)

### Sortie
- `discriminants.csv` : fichier CSV (UTF-8-BOM, séparateur `;`) avec :
  - Colonne `type` : identifiant du type de discriminant
  - Une colonne par langue cible

### Structure de discriminants.csv

```csv
type;fr;en;de;th;es;it;pt;pl;ro;ar;cn
vocabulaire;avec,sans,les,...;with,without,the,...;mit,ohne,die,...;;con,sin,los,...;...
accent;é,è,ê,...;;ä,ö,ü,ß,...;;á,é,í,...;...
```

### Types de lignes

1. **vocabulaire** : mots courants et discriminants de chaque langue
   - Séparateur multivaleurs : `,` (virgule)
   - Vide pour les langues non-latines (th, ar, cn) car détection par Unicode

2. **accent** : caractères accentués ou spéciaux discriminants
   - Inclut majuscules et minuscules
   - Vide pour les langues non-latines (th, ar, cn) et l'anglais

### Comportement si le fichier existe

- **Lignes existantes** : préservées intégralement (le fichier peut être enrichi manuellement)
- **Nouvelles lignes type** : ajoutées automatiquement
- **Nouvelles colonnes langues** : ajoutées si de nouvelles langues apparaissent dans commun.csv

### Langues à alphabet non-latin

Pour le thaï (th), l'arabe (ar) et le chinois (cn), les colonnes restent vides car la détection se fait par plages Unicode :
- Caractères thaï détectés → "th"
- Caractères arabes détectés → "ar"  
- Caractères chinois détectés → "cn"

## Spécifications techniques

### Conventions (voir Prompt_contexte0412.md)
- Python 3.13+
- Encodage CSV : UTF-8-BOM (utf-8-sig)
- Séparateur colonnes : `;`
- Séparateur multivaleurs : `,`
- Lignes de commentaires : commencent par `#`

### Cartouche de version
```python
#*TO*#
__pgm__ = "discriminants.py"
__version__ = "0.0.0"
__date__ = "01/01/1970 00:00"
```

### Affichage
- Afficher nom, version, date au démarrage
- Messages d'information préfixés `[INFO]`
- Messages d'erreur préfixés `[ERREUR]`
- Chemins absolus dans tous les messages
- Message final `[OK]` avec statistiques

### Usage
```bash
# Par défaut (fichiers dans le même répertoire)
python discriminants.py

# Avec chemins personnalisés
python discriminants.py chemin/vers/commun.csv chemin/vers/discriminants.csv
```

## Données discriminantes par langue

### Vocabulaire (mots courants)

| Langue | Mots discriminants |
|--------|-------------------|
| FR | avec, sans, les, des, qui, ont, dans, pour, que, est, une, sur, pas, mais, aux, cette, tout, être, faire, comme |
| EN | with, without, the, who, have, has, this, that, from, are, was, were, been, being, which, their, would, could, should, about |
| DE | mit, ohne, die, der, das, haben, ist, sind, und, ein, eine, nicht, auch, sich, auf, für, werden, kann, nach, bei |
| ES | con, sin, los, las, que, tienen, está, son, una, para, por, como, pero, más, este, esta, todo, puede, hace, sobre |
| IT | con, senza, gli, che, hanno, sono, una, per, come, più, questo, questa, tutto, può, fare, essere, anche, della, nella, sulla |
| PT | com, sem, os, as, que, têm, está, são, uma, para, por, como, mais, este, esta, todo, pode, fazer, também, sobre |
| PL | z, bez, który, która, które, mają, jest, są, dla, jak, ale, też, przez, przy, nad, pod, można, będzie, bardzo, tylko |
| RO | cu, fără, care, sunt, este, pentru, dar, mai, acest, această, tot, poate, face, fiind, prin, asupra, într, dintre, după, când |
| TH | *(vide - détection Unicode)* |
| AR | *(vide - détection Unicode)* |
| CN | *(vide - détection Unicode)* |

### Accents (caractères spéciaux)

| Langue | Caractères discriminants |
|--------|-------------------------|
| FR | é, è, ê, ë, à, â, ù, û, ô, î, ï, ç, œ, æ + majuscules |
| EN | *(vide)* |
| DE | ä, ö, ü, ß, Ä, Ö, Ü, ẞ |
| ES | á, é, í, ó, ú, ñ, ü, ¿, ¡ + majuscules |
| IT | à, è, é, ì, ò, ù + majuscules |
| PT | á, â, ã, à, é, ê, í, ó, ô, õ, ú, ç + majuscules |
| PL | ą, ć, ę, ł, ń, ó, ś, ź, ż + majuscules |
| RO | ă, â, î, ș, ț + majuscules |
| TH | *(vide - détection Unicode)* |
| AR | *(vide - détection Unicode)* |
| CN | *(vide - détection Unicode)* |

## Tests de validation

1. **Création initiale** : Exécuter sur un répertoire sans discriminants.csv → doit créer le fichier
2. **Préservation** : Relancer → doit afficher "conservée" pour les lignes existantes
3. **Nouvelle langue** : Ajouter une langue dans commun.csv → doit ajouter la colonne
4. **Encodage** : Vérifier que le fichier commence par le BOM UTF-8 (EF BB BF)

---

**Fin du prompt**
