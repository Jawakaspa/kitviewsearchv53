# Prompt_detcount_detage_detall.md

## Objet

Migration et renommage des programmes de détection :
- `identcount.py` → `detcount.py`
- `identages.py` → `detage.py`
- `identall.py` → `detall.py`

Avec adoption d'un **nouveau format JSON unifié** pour les critères de recherche.

---

## Contexte

L'application Kitview analyse des questions en langage naturel pour rechercher des patients. La chaîne de détection comprend plusieurs modules :

1. **detlang** : Détection de la langue (nouveau, à créer séparément)
2. **detcount** : Détection LIST/COUNT
3. **dettags** : Détection des pathologies/tags (nouveau, à créer séparément)
4. **detadjs** : Détection des adjectifs qualificatifs (nouveau, à créer séparément)
5. **detage** : Détection des critères d'âge/sexe
6. **detall** : Orchestrateur de tous les modules

Les anciens programmes (`identcount.py`, `identages.py`, `identall.py`) utilisent un format de critères hétérogène. Le nouveau format JSON unifié permettra une meilleure cohérence et une intégration facilitée avec les nouveaux modules (`dettags`, `detadjs`).

---

## Nouveau format JSON unifié des critères

### Structure globale de sortie

```json
{
  "langue": "fr",
  "listcount": "COUNT",
  "criteres": [
    { /* critère 1 */ },
    { /* critère 2 */ },
    ...
  ],
  "residu": "texte restant après détections",
  "question_originale": "combien de femmes de moins de 39 ans",
  "question_standardisee": "combien de femmes de moins de 39 ans"
}
```

### Structure d'un critère

Chaque critère suit **exactement** cette structure :

```json
{
  "type": "age|sexe|tag|adjectif|count",
  "detecte": "texte détecté dans la question",
  "canonique": "forme canonique (pour tags/adjectifs)",
  "label": "libellé lisible pour l'utilisateur",
  "sql": {
    "colonne": "nom_colonne",
    "operateur": "=|<|>|<=|>=|BETWEEN|IN",
    "valeur": "valeur ou [val1, val2] pour BETWEEN"
  },
  "position": {
    "debut": 0,
    "fin": 10
  }
}
```

### Champs obligatoires et optionnels

| Champ | Obligatoire | Description |
|-------|-------------|-------------|
| `type` | ✅ | Type de critère : `age`, `sexe`, `tag`, `adjectif`, `count` |
| `detecte` | ✅ | Texte exact détecté dans la question (standardisé) |
| `canonique` | ❌ | Forme canonique (obligatoire pour `tag` et `adjectif`) |
| `label` | ✅ | Libellé lisible pour affichage utilisateur |
| `sql` | ❌ | Conditions SQL (absent pour `count` qui n'a pas de condition SQL) |
| `sql.colonne` | ✅* | Nom de la colonne SQL (*si sql présent) |
| `sql.operateur` | ✅* | Opérateur SQL |
| `sql.valeur` | ✅* | Valeur ou tableau de valeurs |
| `position` | ❌ | Position dans la question (optionnel, utile pour debug) |

### Exemples de critères par type

#### Type `count`
```json
{
  "type": "count",
  "detecte": "combien",
  "label": "Comptage demandé"
}
```
*Note : pas de champ `sql` car COUNT n'est pas un filtre SQL mais un mode d'affichage*

#### Type `sexe`
```json
{
  "type": "sexe",
  "detecte": "femmes",
  "label": "Femme",
  "sql": {
    "colonne": "sexe",
    "operateur": "=",
    "valeur": "F"
  }
}
```

#### Type `age` (opérateur simple)
```json
{
  "type": "age",
  "detecte": "moins de 39 ans",
  "label": "Moins de 39 ans",
  "sql": {
    "colonne": "age",
    "operateur": "<",
    "valeur": 39
  }
}
```

#### Type `age` (BETWEEN)
```json
{
  "type": "age",
  "detecte": "entre 20 et 30 ans",
  "label": "Entre 20 et 30 ans",
  "sql": {
    "colonne": "age",
    "operateur": "BETWEEN",
    "valeur": [20, 30]
  }
}
```

#### Type `tag`
```json
{
  "type": "tag",
  "detecte": "open bite",
  "canonique": "béance",
  "label": "Béance",
  "sql": {
    "colonne": "pathologie",
    "operateur": "=",
    "valeur": "béance"
  }
}
```

#### Type `adjectif`
```json
{
  "type": "adjectif",
  "detecte": "severe",
  "canonique": "sévère",
  "label": "Sévère",
  "parent_tag": "béance",
  "sql": {
    "colonne": "qualificatif",
    "operateur": "=",
    "valeur": "sévère"
  }
}
```

---

## Programme 1 : detcount.py

### Origine
Basé sur `identcount.py` V1.0.1

### Modifications requises

1. **Renommer** le programme en `detcount.py`
2. **Adapter la sortie JSON** au nouveau format
3. **Ajouter le critère de type `count`** dans la liste des critères (au lieu de juste `filtres['listcount']`)
4. **Conserver** la compatibilité avec le mode batch

### Nouvelle signature

```python
def detecter_count(question, patterns_count, verbose=False, debug=False) -> dict:
    """
    Retourne:
    {
        "listcount": "COUNT" ou "LIST",
        "criteres": [
            {
                "type": "count",
                "detecte": "combien",
                "label": "Comptage demandé"
            }
        ] ou [],
        "residu": "texte restant"
    }
    """
```

### Fichier de référence
- `refs/combien.csv` (inchangé) ou colonne `combien` de `refs/commun.csv`

---

## Programme 2 : detage.py

### Origine
Basé sur `identages.py` V1.0.1

### Modifications requises

1. **Renommer** le programme en `detage.py`
2. **Séparer les critères sexe et âge** : un critère par détection (pas de critère combiné sexe+âge)
3. **Adapter la structure des critères** au nouveau format JSON
4. **Supprimer** l'ancienne structure `conditions: [...]` au profit de `sql: {...}`

### Nouvelle signature

```python
def detecter_age(question, patterns_ages, verbose=False, debug=False) -> dict:
    """
    Retourne:
    {
        "criteres": [
            {
                "type": "sexe",
                "detecte": "femme",
                "label": "Femme",
                "sql": {"colonne": "sexe", "operateur": "=", "valeur": "F"}
            },
            {
                "type": "age",
                "detecte": "moins de 39 ans",
                "label": "Moins de 39 ans",
                "sql": {"colonne": "age", "operateur": "<", "valeur": 39}
            }
        ],
        "residu": "texte restant"
    }
    """
```

### Fichier de référence
- `refs/ages.csv` (inchangé)

### Point d'attention
L'ancien format combinait sexe et âge dans un seul critère avec `conditions: [...]`. Le nouveau format **sépare** chaque condition en un critère distinct de type `sexe` ou `age`.

---

## Programme 3 : detall.py

### Origine
Basé sur `identall.py` V1.0.1

### Modifications requises

1. **Renommer** le programme en `detall.py`
2. **Mettre à jour les imports** : `identcount` → `detcount`, `identages` → `detage`
3. **Préparer l'intégration** des futurs modules `detlang`, `dettags`, `detadjs`
4. **Fusionner les critères** de tous les modules dans une liste unique
5. **Ajouter le champ `langue`** (valeur par défaut `"fr"` en attendant `detlang`)

### Nouvelle signature

```python
def detecter_tout(question, references, verbose=False, debug=False) -> dict:
    """
    Retourne:
    {
        "langue": "fr",
        "listcount": "COUNT" ou "LIST",
        "criteres": [
            /* tous les critères de tous les modules */
        ],
        "residu": "texte restant",
        "question_originale": "...",
        "question_standardisee": "..."
    }
    """
```

### Ordre de détection (actuel)

1. `detcount` → critères de type `count`
2. *(futur)* `detlang` → champ `langue`
3. *(futur)* `dettags` → critères de type `tag`
4. *(futur)* `detadjs` → critères de type `adjectif`
5. `detage` → critères de type `sexe` et `age`

### Fichiers de référence
- `refs/combien.csv` ou `refs/commun.csv` (colonne `combien`)
- `refs/ages.csv`
- *(futur)* `refs/tags.csv`, `refs/syntags.csv`, `refs/synadjs.csv`

---

## Rétrocompatibilité

### Champ `pathologies` (temporaire)

Pour assurer la transition, `detall.py` peut conserver temporairement un champ `pathologies: []` qui sera alimenté par `dettags` une fois celui-ci intégré.

### Fonction wrapper (optionnelle)

Si nécessaire, une fonction `identifier_tout()` peut être conservée comme alias de `detecter_tout()` pour les anciens appelants.

---

## CLI et modes d'exécution

Chaque programme conserve les mêmes modes :

### Mode unitaire
```bash
python detcount.py "combien de patients"
python detage.py "femmes de moins de 39 ans"
python detall.py "combien de femmes avec béance"
```

### Mode batch
```bash
python detcount.py tests/testscountin.csv
python detage.py tests/testsagesin.csv
python detall.py tests/tests55allin.csv
```

### Options
- `--verbose` : Affichage modéré
- `--debug` : Affichage complet

---

## Sortie JSON formatée (CLI)

En mode unitaire, afficher le JSON formaté avec indentation :

```python
import json
print(json.dumps(resultat, indent=2, ensure_ascii=False))
```

---

## Pièces jointes nécessaires pour recréer les programmes

1. `Prompt_contexte0412.md` — Contexte général du projet
2. `Prompt_detcount_detage_detall.md` — Ce document
3. `identcount.py` — Programme source à migrer
4. `identages.py` — Programme source à migrer
5. `identall.py` — Programme source à migrer
6. `ages.csv` — Fichier de référence des patterns d'âge
7. `commun.csv` — Configuration (colonne `combien` pour les mots-clés COUNT)

---

## Résumé des changements

| Aspect | Ancien format | Nouveau format |
|--------|---------------|----------------|
| Nom programmes | `identXXX.py` | `detXXX.py` |
| Structure critère | `conditions: [...]` | `sql: {...}` |
| Critères combinés | sexe+âge ensemble | séparés par type |
| Champ type | implicite | explicite (`type: "age"`) |
| Champ canonique | absent | présent pour tags/adjs |
| Sortie CLI | texte formaté | JSON indenté |

---

**FIN DU DOCUMENT**
