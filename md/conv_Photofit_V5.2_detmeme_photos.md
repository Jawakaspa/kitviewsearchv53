# conv_Photofit_V5.2_detmeme_photos

## Contexte
Développement du système de recherche de portraits similaires (V5.2). Intégration de la recherche par similarité faciale dans le pipeline detmeme → jsonsql → lancesql.

## Échanges

### 07/02/2026 — Échange 1 : Analyse des résultats et plan d'intégration

**Question Thierry :** Résultat test poids 0.3h/0.7f + plan stockage GitHub + intégration pipeline.

**Résultat test :** Recall 100% (9/9), face_embedding à 0.7 confirmé optimal.

**Décisions :** Chemin photofit.db via communb.csv (section bases). GitHub compte jawakaspa.

---

### 07/02/2026 — Échange 2 : Paramètres et livrables initiaux

**Décisions :** Vignettes 200px, photos dans `C:\cx\data\photos\`, noms `1000.jpg...2599.jpg`.

**Livrés :** `resize_portraits.py`, `update_portraits_csv.py` (v1), `Prompt_github_portraits.md`

---

### 07/02/2026 — Échange 3 : GitHub push OK + livrables finaux

**Thierry :** Repo GitHub créé et push OK (1523 objets, 6.99 Mo). Casse officielle : **Jawakaspa** (J majuscule). Image 1000.jpg accessible via URL raw.

**Livrés :**
- `update_portraits_csv.py` v2 (corrigé avec `Jawakaspa` en dur)
- `Prompt_integration_photofit.md` — prompt complet de continuation pour la prochaine conversation

**Clarification architecture :**

| Fichier | Modification nécessaire ? |
|---|---|
| `detmeme.py` | ❌ NON — détecte déjà `cible: portrait` correctement |
| `jsonsql.py` | ✅ OUI — `_generer_clause_meme` : si idportrait >= 1000 → recherche similarité photofit.db au lieu de match exact |
| `lancesql.py` | ❌ NON — exécute le SQL standard, clause IN(...) OK |
| `search_similar.py` | ✅ OUI — poids par défaut 0.5/0.5 → 0.3/0.7 |
| `portraits.csv` | ✅ À enrichir — +1600 lignes URLs GitHub |
| `communb.csv` | ✅ À enrichir — +section bases (photofit) |

**Portraits toujours sur GitHub (jamais en local)** : l'application web charge les images depuis `https://raw.githubusercontent.com/Jawakaspa/orqual-portraits/main/thumbs/{id}.jpg` via l'URL stockée dans portraits.csv.

## Prochaines étapes

1. ✅ Script resize → `resize_portraits.py`
2. ✅ GitHub repo créé + photos uploadées
3. ✅ Script update CSV → `update_portraits_csv.py` (Jawakaspa)
4. ✅ Prompt continuation → `Prompt_integration_photofit.md`
5. ⬜ Exécuter `update_portraits_csv.py` pour enrichir portraits.csv (Thierry)
6. ⬜ Ajouter section bases dans communb.csv (Thierry, manuellement)
7. ⬜ **Modifier `jsonsql.py`** → recherche similarité via photofit.db quand idportrait >= 1000
8. ⬜ **Modifier `search_similar.py`** → poids par défaut 0.3h/0.7f
9. ⬜ Tests locaux sur pats1600.db
10. ⬜ Déploiement photofit.db sur Render

## PJ nécessaires pour la prochaine conversation (étapes 7-8)

- `Prompt_integration_photofit.md`
- `Prompt_contexte0502.md`
- `jsonsql.py`
- `search_similar.py`
- `communb.csv` (avec section bases ajoutée)
