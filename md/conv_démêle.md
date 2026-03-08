# conv_démêle — Synthèse de conversation

## 13/02/2026 23:15 — Échange 1 : Bug similarité portraits

### Problème constaté (screenshots)
- **Simon-mohamed Aboulkacem** → 100 / 1964 patients (fallback IA, pas de vrais similaires)
- **Nouredine Abbou** → 1 seul patient à 100% (seulement lui-même)
- **Anita Dambrosio** → 1 seul patient à 100% (seulement elle-même)

---

## 13/02/2026 23:20 — Échange 2 : Première analyse (hypothèse seuil — invalidée)

Hypothèse initiale : le seuil `photofit_seuil=1000` crée 2 chemins.
→ **Invalidée** par l'audit : tous les patients ont `idportrait >= 10000`.

---

## 14/02/2026 — Échange 3 : Résultats trace + audit

Tous les patients passent par la similarité vectorielle. Le score max observé est de 10% → personne ne dépasse `score_min=30`. Seul le référent (score=100 par construction) est retourné.

---

## 14/02/2026 — Échange 4 : Calibration — BUG TROUVÉ ET RÉSOLU

### Cause racine : `distance_max=0.5` trop restrictif

La distance médiane entre portraits est **0.76**. Avec `distance_max=0.5`, le score tombe à 0 dès que la distance dépasse 0.5 — soit pour **99%** des portraits.

### Distribution réelle des distances (17 815 paires)
```
Min    = 0.082
P1     = 0.519
P5     = 0.605
Median = 0.759
P95    = 0.886
Max    = 1.084
```

### Config recommandée (calibrée automatiquement)

| Paramètre | Avant | Après | Effet |
|---|---|---|---|
| `photofit_distance_max` | 0.5 | **1.0** | Les distances 0-1.0 sont mappées sur les scores 100-0% |
| `photofit_score_min` | 30 | **50** | Seuls les portraits avec score >= 50% sont retenus |

### Résultat attendu : ~11 résultats par patient, scores 50-92%

### Correction
**Aucune modification de code** (jsonsql.py est correct). Seulement 2 valeurs dans communb.csv (section bases).

### Tests de validation
```
python diag_photofit.py trace bases/base1964.db bases/photofit.db Simon-mohamed --dmax 1.0 --score-min 50 -d
python diag_photofit.py trace bases/base1964.db bases/photofit.db Nouredine --dmax 1.0 --score-min 50 -d
```

### Livrables
- `diag_photofit.py` — diagnostic CLI avec 8 commandes dont `trace`, `audit`, `calibrate`
- `Prompt_diag_photofit.md` — documentation complète
- `conv_démêle.md` — cette synthèse

---

## 15/02/2026 — Échange 5 : Fix fond jaune (patient référence incorrect)

### Problème
Quand on tape "même portrait que Simon-mohamed" dans la barre de recherche alors qu'Anita était sélectionnée en référence, Anita garde le fond jaune au lieu de Simon-mohamed.

### Cause
Dans `simple30_search.js` ligne 722, le guard `if (memeState.referenceId !== refId)` empêchait la mise à jour dans certains cas :
1. Si le backend ne retournait pas `criteres_detectes` (fallback), l'ancien état Anita survivait
2. La comparaison `!==` pouvait être faussée par des types différents (string vs number)

### Correction (simple30_search.js)
1. **Suppression du guard** `memeState.referenceId !== refId` → TOUJOURS réinitialiser depuis le backend
2. **Ajout d'un filet de sécurité** : si la requête contient "même" mais le backend ne retourne pas de critère meme, reset de memeState pour éviter l'état stale

### Fichier modifié
- `simple30_search.js` — bloc lignes 708-754 remplacé

---

## 15/02/2026 — Échange 6 : Fix V2 fond jaune — fallback portrait_scores

### Problème
Le jaune s'efface bien (Anita n'est plus jaune) mais ne se met pas sur Simon-mohamed.

### Cause
Console : `[MÊME] Reset état (requête même sans critère meme dans la réponse)`

En mode "standard", le backend retourne `criteres_detectes` mais **sans** `reference_id` dans les critères meme. Le code cherchait uniquement dans `criteres_detectes` et, ne trouvant rien, faisait un reset sans initialiser le nouveau référent.

### Solution : 3 niveaux de détection du référent

```
PRIORITÉ 1 : data.criteres_detectes → critère meme avec reference_id (mode IA)
PRIORITÉ 2 : data.portrait_scores → portrait avec score=100 (mode standard)  
PRIORITÉ 3 : Reset memeState (filet de sécurité)
```

Le portrait avec score=100 est toujours le référent (codé en dur dans jsonsql.py `_rechercher_portraits_similaires`). On utilise cette info pour retrouver le patient correspondant dans les résultats.

### Point à vérifier
Le backend doit retourner `portrait_scores` dans la réponse JSON de l'API `/search`. Vérifier dans le endpoint Flask/FastAPI que le champ `portrait_scores` de `generer_sql()` est bien transmis au frontend.

### Fichier modifié
- `simple30_search.js` — bloc lignes 708-793 réécrit proprement

---

## 15/02/2026 — Échange 7 : Fix V3 fond jaune — fallback par nom dans la requête

### Problème
Le jaune fonctionne pour tous les patients sauf Simon-mohamed. Le backend ne retourne ni `criteres_detectes.reference_id` ni `portrait_scores` → les priorités 1 et 2 échouent silencieusement.

### Solution : Priorité 3 — extraction du nom depuis la requête

Logique : dans "même portrait que **simon-mohamed**", extraire ce qui suit "que" et chercher ce nom dans les résultats par matching souple.

Matching souple :
- Normalisation tirets → espaces ("simon-mohamed" → "simon mohamed")
- Recherche dans `prenom nom` ET `oriprenom orinom`
- `includes` bidirectionnel (nom partiel matche nom complet et inversement)

Déduction automatique du critère depuis la requête :
- "même **portrait**" → critère 'portrait'
- "même **pathologie**" → critère 'pathologie'
- etc.

### Structure finale des 4 niveaux

```
PRIORITÉ 1 : criteres_detectes avec reference_id (mode IA)
PRIORITÉ 2 : portrait_scores avec score=100 (mode standard)
PRIORITÉ 3 : Nom extrait de "même X que NOM" matché dans résultats (fallback)
PRIORITÉ 4 : Reset memeState (filet de sécurité)
```

### Fichier modifié
- `simple30_search.js` — ajout bloc priorité 3 (lignes 786-843)
