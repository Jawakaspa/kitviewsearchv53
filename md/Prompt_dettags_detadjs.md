# Prompt_dettags_detadjs.md

## Objet

Ce prompt permet de recréer à l'identique les fichiers `dettags.py` et `detadjs.py` qui forment le système de détection des tags orthodontiques et de leurs adjectifs qualificatifs.

---

## Pièces jointes requises

1. **Prompt_contexte0412.md** — Contexte général du projet (contraintes, conventions, encodage, etc.)
2. **standardise.py** — Module de normalisation de texte (importé par les deux programmes)
3. **syntags.csv** — Fichier de référence des tags (format : `stdtag;canontag`)
4. **synadjs.csv** — Fichier de référence des adjectifs (format : `stdadj;canonadj;canontag`)

---

## Architecture globale

```
detall.py (orchestrateur principal)
  ├── detcount.py      → LIST/COUNT
  ├── detangles.py     → Angles céphalo → tags qualifiés
  ├── dettags.py       → Tags + adjectifs (CE MODULE)
  │     └── detadjs.py → Adjectifs associés à un tag
  └── detage.py        → Âge/sexe
```

**Principe** : `dettags.py` détecte les tags dans une question, puis pour chaque tag trouvé, appelle `detadjs.py` pour trouver les adjectifs associés dans une fenêtre de proximité.

**Note importante** : La détection travaille exclusivement en français. La traduction est gérée en amont et en aval par d'autres modules.

---

## Spécification de detadjs.py

### Rôle
Détecte les adjectifs qualifiant un tag orthodontique donné, en cherchant dans une fenêtre de proximité autour de la position du tag.

### Constante
```python
FENETRE_PROXIMITE = 5  # Nombre de mots avant/après le tag
```

### Format CSV synadjs.csv
```
stdadj;canonadj;canontag
gauche;gauche;béance
severe;sévère;béance
```
- `stdadj` : forme standardisée (sans accents, minuscules)
- `canonadj` : forme canonique avec accents
- `canontag` : tag auquel cet adjectif s'applique

### Fonctions à implémenter

#### `charger_adjectifs(fichier_csv, verbose=False, debug=False)`
- Charge les adjectifs depuis synadjs.csv
- Retourne un dict : `{canontag_lower: [{'stdadj': ..., 'canonadj': ...}, ...]}`
- Les clés sont en minuscules pour faciliter la recherche
- Gère les commentaires (lignes commençant par #)
- Essaie plusieurs encodages : utf-8-sig, utf-8, windows-1252, iso-8859-1
- Évite les doublons

#### `detecter_adjectifs(question, tag_canonique, position_tag, adjs_data, verbose=False, debug=False)`
- Détecte les adjectifs associés à un tag dans une question
- Algorithme :
  1. Standardiser la question
  2. Récupérer les adjectifs possibles pour le tag (via `canontag.lower()`)
  3. Calculer la fenêtre de recherche autour de la position du tag
  4. Trier les adjectifs par longueur décroissante (multi-mots d'abord)
  5. Pour chaque adjectif, chercher une correspondance dans la fenêtre
  6. Un mot déjà utilisé ne peut pas être réutilisé
- Retourne : `{'adjectifs': [{'detecte': ..., 'canonique': ..., 'standardise': ...}], 'mots_utilises': set()}`

#### `traiter_fichier_batch(fichier_entree, adjs_data, verbose=False, debug=False)`
- Traite un fichier CSV de test batch
- Format d'entrée : colonnes `tag;question`
- Génère un fichier `xxx_out.csv` avec colonnes : `tag;question;nb_adjs;adjs_detectes;adjs_canoniques`
- Retourne : `(nb_lignes_traitees, fichier_sortie)`

### Interface CLI
```
Usage:
  python detadjs.py "tag" "question"        # Test unitaire
  python detadjs.py fichier.csv             # Test batch

Options:
  --verbose   Affichage modéré (résultats)
  --debug     Affichage complet (tout)

Exemples:
  python detadjs.py "béance" "patients avec béance gauche sévère"
  python detadjs.py tests_adjs.csv
```

### Chemins de recherche pour synadjs.csv
```python
chemins_possibles = [
    Path("refs/synadjs.csv"),
    Path("synadjs.csv"),
    Path(__file__).parent / "refs" / "synadjs.csv",
    Path("c:/g/refs/synadjs.csv"),
]
```

### Format de sortie JSON (mode unitaire)
```json
{
  "adjectifs": [
    {"detecte": "gauche", "canonique": "gauche", "standardise": "gauche"},
    {"detecte": "severe", "canonique": "sévère", "standardise": "severe"}
  ],
  "mots_utilises": ["gauche", "severe"]
}
```

---

## Spécification de dettags.py

### Rôle
Détecte les tags orthodontiques (pathologies, caractéristiques) dans une question en langage naturel, puis appelle `detadjs.py` pour trouver les adjectifs associés à chaque tag.

### Format CSV syntags.csv
```
stdtag;canontag
beance;béance
classe ii d angle;classe II d'Angle
```
- `stdtag` : forme standardisée (sans accents, minuscules)
- `canontag` : forme canonique avec accents et casse

### Fonctions à implémenter

#### `charger_tags(fichier_tags, fichier_adjs=None, verbose=False, debug=False)`
- Charge les tags depuis syntags.csv
- Optionnellement charge aussi les adjectifs via `charger_adjectifs()`
- Retourne : `(tags_data, adjs_data)`
  - `tags_data` : liste triée par nombre de mots décroissant `[{'stdtag': ..., 'canontag': ..., 'nb_mots': ...}, ...]`
  - `adjs_data` : dict des adjectifs par tag
- Gère les commentaires
- Évite les doublons

#### `detecter_tags(question, tags_data, adjs_data=None, verbose=False, debug=False)`
- Détecte les tags et leurs adjectifs dans une question
- Algorithme :
  1. Standardiser la question
  2. Créer la liste des mots et un set des mots utilisés
  3. Pour chaque tag (du plus long au plus court) :
     - Chercher le tag dans la question (correspondance exacte des mots)
     - Si trouvé ET mots disponibles → marquer comme utilisé
     - Appeler `detecter_adjectifs()` pour ce tag
     - Marquer aussi les mots des adjectifs comme utilisés
  4. Calculer le résidu (mots non utilisés)
- Retourne :
```json
{
  "criteres": [
    {
      "type": "tag",
      "detecte": "beance",
      "canonique": "béance",
      "label": "béance",
      "sql": {
        "colonne": "canontags",
        "operateur": "=",
        "valeur": "beance"
      },
      "adjectifs": [
        {"colonne": "canonadjs", "operateur": "=", "valeur": "gauche"}
      ],
      "position": {"debut": 15, "fin": 21}
    }
  ],
  "residu": "patients avec de moins de 30 ans",
  "question_standardisee": "..."
}
```

#### `identifier_tags(residu, tags_data, adjs_data, filtres, verbose=False, debug=False)`
- Wrapper de compatibilité pour `detall.py`
- Signature standard : `identifier_XXX(residu, data, filtres, verbose, debug) -> (filtres, residu)`
- Enrichit `filtres['criteres']` avec les critères détectés

#### `traiter_fichier_batch(fichier_entree, tags_data, adjs_data, verbose=False, debug=False)`
- Traite un fichier CSV de test batch
- Format d'entrée : colonne `question` requise
- Génère `xxx_out.csv` avec colonnes : `question;nb_tags;tags_detectes;adjs_detectes;residu`

### Interface CLI
```
Usage:
  python dettags.py "question"              # Test unitaire
  python dettags.py fichier.csv             # Test batch

Options:
  --verbose   Affichage modéré (résultats)
  --debug     Affichage complet (tout)

Exemples:
  python dettags.py "patients avec béance gauche sévère"
  python dettags.py testscomplets.csv
```

### Chemins de recherche
```python
chemins_tags = [
    Path("refs/syntags.csv"),
    Path("syntags.csv"),
    Path(__file__).parent / "refs" / "syntags.csv",
    Path("c:/g/refs/syntags.csv"),
]

chemins_adjs = [
    Path("refs/synadjs.csv"),
    Path("synadjs.csv"),
    Path(__file__).parent / "refs" / "synadjs.csv",
    Path("c:/g/refs/synadjs.csv"),
]
```

---

## Import de standardise.py

Les deux programmes doivent inclure un fallback si `standardise.py` n'est pas disponible :

```python
try:
    from standardise import standardise
except ImportError:
    import unicodedata
    def standardise(texte):
        """Version simplifiée de standardise si le module n'est pas disponible."""
        if texte is None or texte == "":
            return ""
        texte = texte.lower()
        texte = unicodedata.normalize('NFD', texte)
        texte = ''.join(char for char in texte if unicodedata.category(char) != 'Mn')
        for char in ".!-_?":
            texte = texte.replace(char, " ")
        texte = re.sub(r'\s+', ' ', texte)
        return texte.strip()
```

---

## Import croisé dettags ↔ detadjs

Dans `dettags.py`, prévoir un fallback si `detadjs.py` n'est pas disponible :

```python
try:
    from detadjs import charger_adjectifs, detecter_adjectifs
except ImportError:
    def charger_adjectifs(*args, **kwargs):
        return {}
    def detecter_adjectifs(*args, **kwargs):
        return {'adjectifs': [], 'mots_utilises': set()}
```

---

## Conventions d'affichage

### Cartouche de démarrage
```
╔════════════════════════════════════════════════════════════════
║ dettags.py V1.1.0 - 16/12/2025
║ Détection des tags orthodontiques avec adjectifs
╚════════════════════════════════════════════════════════════════
```

### Messages de debug
- Préfixe : `[DEBUG] detXXX: `
- Exemple : `[DEBUG] dettags: Tag trouvé: 'beance' à position {'debut': 15, 'fin': 21}`

### Messages de résultat
- Checkmark : `✓ Tag: 'beance' → 'béance' [adjs: gauche, severe]`

---

## Gestion des encodages CSV

Ordre des encodages à essayer :
```python
encodages = ["utf-8-sig", "utf-8", "windows-1252", "iso-8859-1"]
```

Fichiers de sortie : toujours `utf-8-sig` avec `newline=''`.

---

## Convention de nommage des fichiers de sortie batch

- Si le nom se termine par `in` → remplacer par `out` (ex: `testsin.csv` → `testsout.csv`)
- Sinon → ajouter `_out` (ex: `tests.csv` → `tests_out.csv`)

---

## Points critiques

1. **Tri par longueur décroissante** : Les tags/adjectifs multi-mots doivent être testés avant les mono-mots
2. **Mots déjà utilisés** : Un mot ne peut être attribué qu'à un seul tag ou adjectif
3. **Fenêtre de proximité** : Les adjectifs doivent être dans une fenêtre de ±5 mots autour du tag
4. **Forme SQL** : Utiliser `stdtag`/`stdadj` (forme standardisée) pour les valeurs SQL
5. **Forme label** : Utiliser `canontag`/`canonadj` (forme canonique) pour l'affichage

---

**FIN DU PROMPT**
