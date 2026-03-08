# Conversation : classe i classe II

## Échange 1 — 05/02/2026

### Question
Bug dans `dettags.py` : la phrase "classe i classe II" ne détecte qu'un seul tag ("classe ii") au lieu de deux. Le mot "classe" est éliminé deux fois car `mots_utilises` est un `set` de **mots** et non de **positions**. Demande aussi d'enrichir le verbose.

### Analyse
Le problème se situe dans `detecter_tags()` :
- **Ligne 257** : `mots_utilises = set()` stocke des **mots** (chaînes)
- **Ligne 289** : `mot_question in mots_utilises` rejette un mot dès qu'il a été consommé **n'importe où**
- **Ligne 304-305** : `mots_utilises.add(mot)` ajoute le mot "classe" une seule fois (c'est un set), ce qui bloque toutes les autres occurrences du même mot

Conséquence : quand "classe ii" est trouvé, le mot "classe" est marqué utilisé → "classe i" ne peut plus matcher car "classe" est déjà dans le set.

Bug secondaire : `question_norm.find(texte_detecte)` retourne toujours la **première** occurrence dans la chaîne, ce qui peut donner la mauvaise position quand un même texte apparaît plusieurs fois.

### Corrections apportées (dettags.py V1.2.0)

1. **Fix critique** : `mots_utilises: set[str]` → `indices_utilises: set[int]` — on traque les indices de position des mots, pas les mots eux-mêmes
2. **Fix position** : Calcul de `pos_debut`/`pos_fin` via sommation des longueurs de mots au lieu de `str.find()`
3. **Verbose enrichi** : Affiche les mots analysés, les positions des candidats, le bilan (n tags, n mots consommés) et le résidu
4. **CLI** : Ajout des raccourcis `-v`/`-d`, aide affichée sans argument, exemples d'utilisation

### Fichier livré
- `dettags.py` (V1.2.0) — à déposer dans `c:/g/boitedereception/`

### Résultat attendu après correction
```
python dettags.py "classe i classe II" -v
  ✓ Tag: 'classe ii' → 'classe ii d'angle' (genre=f) [adjs: aucun]
  ✓ Tag: 'classe i' → 'classe i d'angle' (genre=f) [adjs: aucun]
  Bilan: 2 tag(s) détecté(s), 4/4 mots consommés
Résidu: ''
```
