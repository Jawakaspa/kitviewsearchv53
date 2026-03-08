# Prompt_questions.md

## Objectif

Créer `questions.py`, un programme Python qui génère :
1. Un fichier de questions de test (`qfichier.csv`) avec 100 questions (25 par niveau de 1 à 4 critères)
2. Un fichier patients modifié (`mfichier.csv`) dont les données sont ajustées pour que chaque question matche 2-10% des patients

## Fichiers requis en pièces jointes

- `pats100.csv` : Fichier patients de référence (structure à respecter)
- `tagssaisis.csv` : Pathologies avec synonymes et adjectifs
- `ages.csv` : Patterns âge/sexe avec leurs expressions

## Fichiers de référence

### Structure de pats100.csv (entrée)
```
id;canontags;canonadjs;sexe;age;datenaissance;prenom;nom;portrait
```
- `canontags` : Tags canoniques séparés par `,`
- `canonadjs` : Adjectifs par tag séparés par `,` (position correspondante), chaque groupe d'adjectifs séparé par `|`
- `sexe` : M ou F
- `age` : Âge en années (décimal)

### Structure de tagssaisis.csv
```
type;canonfr;synonymesfr;adjectifsfr
```
- `canonfr` : Forme canonique du tag
- `synonymesfr` : Synonymes séparés par `,`
- `adjectifsfr` : Groupes d'adjectifs séparés par `,`, synonymes dans chaque groupe séparés par `|` (premier = canonique)

### Structure de ages.csv
```
expression;operateur;valeur_sql;sexe;label;pourquestion
```
- `expression` : Patterns séparés par `|`, certains avec `{n}` à remplacer par une valeur
- `sexe` : F, M ou vide
- `label` : Libellé pour affichage

## Règles de génération des questions

### Distribution des critères (100 questions)
- 25 questions à 1 critère
- 25 questions à 2 critères
- 25 questions à 3 critères
- 25 questions à 4 critères

### Contraintes sur les types de critères
- Maximum 1 critère âge par question
- Maximum 1 critère sexe par question (certains patterns comme "femme" incluent âge ET sexe, comptés comme 1 critère sexe)
- Pour 4 critères : minimum 2 critères tags (avec ou sans adjectifs)

### Équiprobabilité des adjectifs
Pour chaque critère tag, si le tag possède n groupes d'adjectifs canoniques :
- Probabilité 1/(n+1) d'avoir 0, 1, 2, ... ou n adjectifs
- Les adjectifs sont tirés parmi les groupes disponibles

### Incompatibilités d'adjectifs
Les paires suivantes sont mutuellement exclusives (si l'un est tiré, l'autre est interdit) :
- gauche / droite
- antérieure / postérieure
- maxillaire / mandibulaire
- maxillaire / mandibule

### Patterns âge avec {n}
- `{n}` doit être remplacé par une valeur aléatoire cohérente (5-30 ans)
- Patterns fixes (adulte, adolescent, etc.) également utilisables

## Structure du fichier qfichier.csv (sortie)

```
crit1_canon;crit2_canon;crit3_canon;crit4_canon;crit1_syn;crit2_syn;crit3_syn;crit4_syn;question;nb;ids;extrait
```

### Colonnes critères canoniques (crit1_canon à crit4_canon)
- Pour un tag : `tag_canonique adj1 adj2` (séparés par espaces)
- Pour âge/sexe : le pattern utilisé
- Vide si moins de critères

### Colonnes critères synonymes (crit1_syn à crit4_syn)
- Même structure mais avec des synonymes (incluant possiblement la forme canonique)
- Permettent de variabiliser les questions

### Colonne question
- Question générée en français naturel
- Exemple : "Quels sont les patients avec béance antérieure sévère qui sont adolescents ?"

### Colonnes résultats
- `nb` : Nombre de patients matchant la question
- `ids` : Liste des IDs séparés par `,`
- `extrait` : Jusqu'à 10 couples "prénom nom" séparés par `, `

## Structure du fichier mfichier.csv (sortie)

Même structure que le fichier patients d'entrée, mais avec :
- `canontags` et `canonadjs` modifiés pour satisfaire les questions
- `sexe` et `age` potentiellement ajustés
- Garantie : chaque question matche 2-10% des patients

## Algorithme principal

1. **Charger les références** : tags, adjectifs, patterns âge/sexe
2. **Générer 100 squelettes de questions** avec leurs critères
3. **Pour chaque question** :
   - Tirer les critères selon les règles d'équiprobabilité
   - Générer versions canoniques et synonymes
   - Générer le texte de la question
4. **Ajuster les données patients** :
   - Pour chaque question, vérifier le taux de match
   - Si < 2%, modifier des patients pour augmenter les matchs
   - Si > 10%, réduire (modifier des patients ou ajuster la question)
5. **Calculer les résultats** (nb, ids, extrait) pour chaque question
6. **Sauvegarder** qfichier.csv et mfichier.csv

## Contraintes techniques

- Python 3.13+
- Encodage UTF-8-BOM pour les CSV
- Séparateur `;` pour colonnes, `,` pour multivaleurs
- Affichage progression avec tqdm
- Variables `__pgm__`, `__version__`, `__date__` en début de fichier

## Appel du programme

```bash
python questions.py fichier.csv
```

Génère :
- `qfichier.csv` (questions)
- `mfichier.csv` (patients modifiés)

## Exemple

```bash
python questions.py pats100.csv
```

Génère :
- `qpats100.csv`
- `mpats100.csv`
