# Prompt_diag_photofit.md — Diagnostic & correction recherche portraits similaires

## Contexte

La recherche "même portrait que X" dans Kitview Search donne des résultats incohérents.

## Bug identifié (analyse de jsonsql.py)

### Cause racine : le seuil `photofit_seuil=1000`

Dans `_generer_clause_meme()` de jsonsql.py, quand `cible == 'portrait'` :

```python
if id_num >= seuil:    # seuil = 1000 (communb.csv)
    # CHEMIN A : Recherche vectorielle dans photofit.db
    resultats = _rechercher_portraits_similaires(idportrait_ref, config)
    # → WHERE p.idportrait IN (id1, id2, ..., id20)
else:
    # CHEMIN B : Match exact
    # → WHERE p.idportrait = '5'
```

**Chemin A** (idportrait >= 1000) : fonctionne correctement côté similarité, mais le `WHERE IN` avec 20 IDs photofit peut retourner bien plus de 20 patients si plusieurs patients partagent le même idportrait.

**Chemin B** (idportrait < 1000) : aucune similarité calculée. Seuls les patients avec le même `idportrait` exact matchent → en général 1 seul résultat (le patient lui-même).

### Impact observé

| Patient | idportrait | Chemin | Résultats | Explication |
|---|---|---|---|---|
| Simon-mohamed | >= 1000 | A (vectoriel) | 100 | 20 IDs × ~5 patients/ID |
| Nouredine | < 1000 | B (exact) | 1 | Seul lui-même matche |
| Anita | < 1000 | B (exact) | 1 | Seule elle-même matche |

## Outil de diagnostic : `diag_photofit.py`

Script CLI, 7 commandes. La plus importante est **`trace`** qui reproduit exactement le chemin de jsonsql.py.

### Tests à exécuter

```
python diag_photofit.py trace bases/base1964.db bases/photofit.db Simon-mohamed
python diag_photofit.py trace bases/base1964.db bases/photofit.db Nouredine
python diag_photofit.py trace bases/base1964.db bases/photofit.db Anita
python diag_photofit.py audit bases/base1964.db bases/photofit.db -v
```

## Pistes de correction

### Option 1 : Supprimer le seuil (recommandé)
Tous les patients avec un idportrait présent dans photofit.db passent par la similarité vectorielle, quel que soit la valeur numérique de l'idportrait.

```python
# AVANT
if id_num >= seuil:
    # similarité
else:
    # match exact

# APRÈS
# Vérifier directement si le portrait existe dans photofit.db
resultats = _rechercher_portraits_similaires(idportrait_ref, config, debug=debug)
if resultats:
    # similarité (portrait trouvé dans photofit.db)
else:
    # match exact (portrait absent de photofit.db)
```

### Option 2 : Limiter le nombre de patients retournés
Ajouter un LIMIT au SQL final pour éviter les 100 résultats quand plusieurs patients partagent un idportrait.

### Option 3 : Reprocesser les portraits < 1000
S'assurer que tous les patients avec des photos ont un idportrait >= 1000 dans photofit.db.

## Fichiers concernés

- **jsonsql.py** : `_generer_clause_meme()` — correction du seuil
- **communb.csv** : `photofit_seuil` — à ajuster ou supprimer
- **diag_photofit.py** : diagnostic (nouveau fichier)

## PJ nécessaires pour recréer diag_photofit.py

- `Prompt_contexte0502.md` (conventions)
- `Prompt_diag_photofit.md` (ce fichier)
- Accès aux bases `base1964.db` et `photofit.db`

## Prompt pour recréer diag_photofit.py

```
Crée un script Python CLI `diag_photofit.py` qui diagnostique la recherche de portraits similaires.
Le script doit tracer le chemin EXACT de jsonsql.py/_generer_clause_meme() pour un patient donné,
en vérifiant le seuil photofit_seuil, le chemin pris (vectoriel vs exact), et le nombre de résultats.

Commandes :
  trace DBPATIENTS DBPHOTOFIT NOM — trace complète pour un patient
  audit DBPATIENTS DBPHOTOFIT     — audit global (répartition exact vs similarité)
  stats DBPHOTOFIT                — stats sur les embeddings
  search DBPHOTOFIT IDPORTRAIT    — recherche similaires avec distribution des scores
  compare DBPHOTOFIT ID1 ID2      — compare 2 portraits
  matrix DBPHOTOFIT               — matrice NxN
  anomalies DBPHOTOFIT            — détection anomalies

Options : -n, --all, --wh, --wf, --dmax, --seuil, --score-min, --csv, -v, -d

Le script utilise les mêmes fonctions de calcul que jsonsql.py :
_deserialize_float_vector, _cosine_distance, _distance_to_score.
```
