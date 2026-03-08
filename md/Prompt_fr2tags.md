# Prompt_fr2tags.md

## Objet

Prompt de recréation du programme `fr2tags.py` - Internationalisation des tags orthodontiques avec glossaire comme source de vérité.

---

## Contexte

Le projet Kitview est une application de recherche multilingue sur plus de 25 000 patients d'un cabinet d'orthodontie. L'internationalisation des tags et adjectifs doit utiliser un glossaire central (`glossaire.csv`) comme source de vérité unique pour toutes les traductions.

---

## Fichiers requis en pièces jointes

1. **Prompt_contexte.md** - Contexte général du projet (encodages, conventions, etc.)
2. **commun.csv** - Configuration des langues (colonne `languescibles`)
3. **glossaire.csv** - Glossaire multilingue (source de vérité)
4. **tagsfr.csv** - Tags et adjectifs en français (source)

---

## Spécifications fonctionnelles

### Objectif principal

Créer `fr2tags.py` qui :
1. Lit les tags et adjectifs français depuis `tagsfr.csv`
2. Consulte `glossaire.csv` pour les traductions existantes
3. Traduit les termes manquants via API (DeepL → MyMemory → LibreTranslate)
4. Enrichit `glossaire.csv` avec les nouvelles traductions
5. Génère `tags.csv` avec toutes les traductions

### Structure des fichiers

#### tagsfr.csv (entrée)
```
type;frtags;stdfrtags;fradjs;stdfradjs
p;Classe I squelettique,classe 1 squelettique;classe i squelettique,classe 1 squelettique;idéal|idéale|idéaux;ideal|ideale|ideaux
```

- `type` : Type de tag (p=pathologie, c=courant, t=traitements, z=ne pas traduire, m=manuel, jjmmaaaa=temporaire)
- `frtags` : Tags en français, séparés par virgule
- `stdfrtags` : Tags standardisés (minuscules, sans accents)
- `fradjs` : Adjectifs associés, groupes séparés par virgule, variantes par pipe `|`
- `stdfradjs` : Adjectifs standardisés

#### glossaire.csv (source de vérité)
```
type;fr;en;de;es;it;pt;pl;ro;th;ar;cn
p;aussi;also;auch;también;anche;também;także;de asemenea;ด้วย;أيضا;也
```

- `type` : Type de terme (p=permanent, c=courant, o=orthodontie, z=ne pas traduire)
- `fr` : Terme français (clé unique)
- Autres colonnes : Une par langue cible

#### tags.csv (sortie)
```
canonfr;type;frtags;stdfrtags;fradjs;stdfradjs;entags;stdentags;enadjs;stdenadjs;...
```

- `canonfr` : Premier tag français (terme canonique)
- Colonnes `{lang}tags`, `std{lang}tags`, `{lang}adjs`, `std{lang}adjs` pour chaque langue

#### commun.csv (configuration)
```
combien;devant;langues;languescibles;ecartlang;seuillang
combien;sévère;fr;fr;2;5
denombre;;en;en;;
```

- `langues` : Liste des langues **actives** pour la traduction (seules ces langues seront traduites)
- `languescibles` : Liste complète des langues cibles (pour référence future)

**Important** : On traduit uniquement vers les langues de la colonne `langues`, pas `languescibles`. Si le glossaire contient d'autres colonnes de langue (ex: `de`, `th`), elles sont préservées mais pas mises à jour.

---

## Spécifications techniques

### Règles de traduction

1. **Ne pas traduire** : Les termes de type `z` ne sont jamais traduits
2. **Ne pas retraduire** : Si une traduction existe déjà dans le glossaire (case non vide), on la réutilise
3. **Stockage individuel** : Chaque terme est stocké individuellement dans le glossaire, pas les groupes
   - Exemple : "sévère", "sévères", "grave", "graves" sont 4 entrées distinctes
4. **Expressions complètes** : Les expressions multi-mots sont stockées telles quelles
   - Exemple : "Classe I squelettique" est une entrée, pas "Classe" + "I" + "squelettique"

### Cascade de traduction

Ordre de priorité pour les APIs :
1. **DeepL** (si clé API disponible via `DEEPL_API_KEY`)
2. **MyMemory** (gratuit, limité)
3. **LibreTranslate** (gratuit)

### Gestion des colonnes

- Le programme détecte les colonnes existantes dans `glossaire.csv`
- Il ajoute automatiquement les colonnes manquantes pour les langues de `languescibles`
- Les commentaires (lignes commençant par `#`) sont préservés

### Statistiques et audit

Le programme génère :
- `tags_audit.csv` : Trace de chaque traduction (terme, langue, fournisseur, date)
- Statistiques console : termes réutilisés vs nouveaux, par langue, par fournisseur

---

## Structure du programme

```python
#*TO*#
__pgm__ = "fr2tags.py"
__version__ = "0.0.0"
__date__ = "01/01/1970 00:00"

# Classes
class AuditTraduction      # Trace l'origine des traductions
class StatsTraduction      # Statistiques de traduction

# Fonctions utilitaires
def standardise(texte)     # Normalisation (minuscules, sans accents)
def extraire_canonfr()     # Extrait le premier tag (canonique)
def verifier_encodage_bom()# Vérifie UTF-8-BOM

# Services de traduction
def traduire_deepl()       # API DeepL
def traduire_mymemory()    # API MyMemory
def traduire_libretranslate() # API LibreTranslate
def traduire_avec_fallback()  # Cascade des 3 services

# Gestion glossaire
def charger_langues_actives()  # Lit langues depuis commun.csv (colonne 'langues')
def charger_glossaire()        # Charge glossaire.csv en mémoire
def sauvegarder_glossaire()    # Écrit glossaire.csv enrichi

# Traduction
def traduire_terme()       # Traduit un terme via glossaire
def traduire_liste()       # Traduit une liste CSV
def standardise_liste()    # Standardise une liste traduite

def main()                 # Point d'entrée
```

---

## Mapping des codes langue DeepL

```python
MAPPING_DEEPL = {
    'fr': 'FR',
    'en': 'EN-GB',
    'de': 'DE',
    'es': 'ES',
    'it': 'IT',
    'pt': 'PT-PT',
    'pl': 'PL',
    'ro': 'RO',
    'th': 'TH',
    'ar': 'AR',
    'cn': 'ZH-HANS'
}
```

---

## Exemple d'exécution

```
fr2tags.py V2.0.0 - 12/12/2025 17:00

======================================================================
FICHIERS
======================================================================
Fichier commun     : c:/g/refs/commun.csv
Fichier glossaire  : c:/g/refs/glossaire.csv
Fichier d'entree   : c:/g/refs/tagsfr.csv
Fichier de sortie  : c:/g/refs/tags.csv
Fichier audit      : c:/g/refs/tags_audit.csv

Encodage UTF-8-BOM verifie OK pour tagsfr.csv
DeepL : Disponible (prioritaire)
Langues actives depuis commun.csv : ['fr', 'en']
Langues a traduire : ['en']

======================================================================
CHARGEMENT GLOSSAIRE
======================================================================
Glossaire charge depuis : c:/g/refs/glossaire.csv
  - Termes charges : 58
  - Termes type 'z' ignores : 5
  - Colonnes existantes : ['type', 'fr', 'en', 'de', 'th']
  - Langues actives pour traduction : ['en']

======================================================================
TRADUCTION EN COURS (glossaire.csv = source de verite)
======================================================================

[1/6] Classe I squelettique
  -> EN: nouveau:3 glossaire:0

[2/6] Classe II squelettique
  -> EN: glossaire OK (6 termes)

======================================================================
ECRITURE DES FICHIERS
======================================================================
Glossaire sauvegarde : c:/g/refs/glossaire.csv
  - Lignes totales : 65
  - Nouveaux termes ajoutes : 7

======================================================================
STATISTIQUES DE TRADUCTION
======================================================================
...

TEMPS TOTAL : 12.3 secondes
```

---

## Contraintes

- Python 3.13+ uniquement
- Encodage UTF-8-BOM pour tous les CSV
- Séparateur `;` pour les colonnes CSV
- Séparateur `,` pour les listes de valeurs
- Séparateur `|` pour les variantes/synonymes
- Ne jamais écraser les fichiers protégés sans backup préalable

---

## Points d'attention

1. **Préserver les commentaires** : Les lignes `#` en début de glossaire.csv doivent être conservées
2. **Backup systématique** : Créer `glossaireold.csv` et `tagsold.csv` avant modification
3. **Pause entre appels API** : 0.1 seconde entre chaque appel pour éviter le throttling
4. **Type par défaut** : Les nouveaux termes ajoutés au glossaire ont le type `o` (orthodontie)

---

**FIN DU PROMPT**
