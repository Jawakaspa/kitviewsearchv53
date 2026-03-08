# Prompt_recreer_jsonsql_photofit.md

## Objet

Prompt permettant de recréer `jsonsql.py` V1.3.0 et `search_similar.py` (poids corrigés) pour l'intégration Photofit V5.2 avec scores de ressemblance.

---

## Modifications à appliquer

### 1. `search_similar.py` — Poids par défaut

Changer les constantes :
```python
WEIGHT_HAIR = 0.3   # était 0.7
WEIGHT_FACE = 0.7   # était 0.3
```
Et mettre à jour l'aide CLI en cohérence.

### 2. `jsonsql.py` — V1.1.0 → V1.3.0

**Imports à ajouter** : `csv`, `sqlite3`, `struct`, `math`

**Fonctions à ajouter** (après `TOLERANCE_AGE_DEFAUT`) :

#### `_lire_config_photofit(debug) → dict`
Lit la section `bases` de communb.csv (cherche dans `refs/communb.csv` puis `./communb.csv`). Cache global. Retourne :
- photofit_db, max_results, weight_hair, weight_face, seuil
- **V1.3.0** : distance_max (défaut 0.5), score_min (défaut 30)

#### `_distance_to_score(distance, distance_max) → int`
Score = max(0, min(100, round(100 × (1 - distance / distance_max))))

#### `_deserialize_float_vector(data: bytes) → List[float]`
Désérialise BLOB en vecteur float via struct.unpack.

#### `_cosine_distance(vec1, vec2) → float`
Distance cosinus standard (1 - similarité).

#### `_rechercher_portraits_similaires(idportrait_ref, config, debug) → List[Tuple[str, int]]`
Retourne des tuples (id, score_0_100) triés par score décroissant. Le référent est en premier avec score=100. Les portraits sous `score_min` sont exclus.

**Modification de `_generer_clause_meme()`** :
- Retourne désormais 5 éléments : `(join, where, params, counter, portrait_scores)`
- `portrait_scores` est un dict `{idportrait: score}` ou None
- Bloc portrait : utilise `_rechercher_portraits_similaires()` et construit le dict portrait_scores

**Modification de `generer_sql()`** :
- Capture `portrait_scores` via le 5ème retour
- Si portrait_scores : génère `ORDER BY CASE p.idportrait WHEN 'id' THEN rank ...` pour trier par score décroissant
- Sinon : `ORDER BY p.id` (comportement par défaut)
- Ajoute `portrait_scores` au dict résultat

**Grille de couleurs pour le frontend** :
| Score | Couleur CSS | Label |
|---|---|---|
| 100 | #ffc107 | Référent (jaune) |
| ≥ 80 | #28a745 | Excellent (vert) |
| ≥ 60 | #17a2b8 | Bon (bleu) |
| ≥ 40 | #fd7e14 | Moyen (orange) |
| < 30 | — | Exclu |

---

## Paramètres communb.csv (section bases)

```csv
bases;photofit;bases/photofit.db;Base des embeddings faciaux Photofit
bases;photofit_max_results;20;Nombre max de portraits similaires (référent compris)
bases;photofit_weight_hair;0.3;Poids du hair_embedding
bases;photofit_weight_face;0.7;Poids du face_embedding
bases;photofit_seuil;1000;Seuil idportrait pour recherche par similarité
bases;photofit_distance_max;0.5;Distance max pour conversion score 0-100
bases;photofit_score_min;30;Score minimum pour inclure un portrait
```

---

## Pièces jointes nécessaires

1. **jsonsql.py** (V1.1.0 — version de base avant modification)
2. **search_similar.py** (version actuelle)
3. **communb.csv** (avec section bases complète)
4. **Prompt_contexte0502.md** (conventions du projet)

---

## Usage CLI

```cmd
python jsonsql.py '{"listcount":"LIST","criteres":[{"type":"meme","cible":"portrait","reference_id":42,"reference_patient":{"idportrait":"1000"}}]}'
python jsonsql.py fichier.json -d
python jsonsql.py --help

python search_similar.py 1000 -n 20 --db bases/photofit.db -v
python search_similar.py          # Affiche l'aide
```

---

**FIN DU DOCUMENT**
