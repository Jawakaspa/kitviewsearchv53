# conv_detid.md — Synthèse de conversation

## 15/02/2026 ~10:00 — Demande initiale

**Question** : Ajout de la recherche par identifiant patient (`id XXX`) dans le pipeline de détection.

**Spécifications reçues** :
- Pattern : quand la requête commence par `id ` ou contient ` id `, prendre le token suivant comme identifiant
- Identifiant alphanumérique possible (pas seulement entier)
- S'intègre dans toute la chaîne : detall.py, detia.py, detiabrut.py
- Peut être combiné avec d'autres critères : `id 10122 femme avec béance` → 0 ou 1 résultat
- Peut être utilisé comme référence de similarité : `même portrait que id 10122`
- Pour l'instant back-office uniquement (pas d'interface web)

**Fichiers fournis en PJ** : detage.py, detiabrut.py, detall.py, jsonsql.py, detia.py, trouve.py, detmeme.py, trouveid.py

---

## 15/02/2026 ~10:05 — Questions préalables

**Questions posées** :
1. detmeme.py et trouveid.py nécessaires → **Fournis**
2. Format identifiant → **Alphanumérique possible**
3. Position pipeline (après detmeme, avant detangles) → **OK**
4. Cas combiné (id + autres critères) → **Oui, 0 ou 1 résultat**

---

## 15/02/2026 ~10:15 — Livraison

### Fichiers créés

| Fichier | Action | Description |
|---------|--------|-------------|
| `detid.py` | **NOUVEAU** | Module de détection des identifiants patients |
| `Prompt_detid.md` | **NOUVEAU** | Prompt complet de recréation + patches d'intégration |
| `conv_detid.md` | **NOUVEAU** | Ce fichier de synthèse |

### Fichiers à modifier (patches dans Prompt_detid.md)

| Fichier | Patches | Description |
|---------|---------|-------------|
| `jsonsql.py` | 2a, 2b | Ajout `_generer_clause_id()` + gestion type 'id' dans `generer_sql()` |
| `detall.py` | 3a-3d | Import detid + étape 1.6 + affichage module + comptage batch |
| `detia.py` | 4a-4d | Import detid + pré-traitement + fusion critères + affichage |
| `detiabrut.py` | 5a-5b | Import detid + pré-traitement dans `detecter_tout_brut()` |

### Architecture

Pipeline detall.py :
```
detcount → detmeme → detid → detangles → dettags → detage → motsvides
```

Pipeline detia.py / detiabrut.py :
```
detmeme → detid → IA → fusion → motsvides
```

### Décisions techniques

1. **Pattern** : `\bid\s+([a-z0-9]+)` sur texte standardisé — robuste contre "kid", "idée", etc.
2. **Position après detmeme** : évite que detid consomme `id 10122` dans `même portrait que id 10122`
3. **Conversion int/str** : l'identifiant est converti en `int` si possible (colonne `id INTEGER PRIMARY KEY`), sinon reste `str`
4. **Pas de CSV nécessaire** : contrairement à detage/dettags, le pattern est fixe

### Limitation identifiée

`detmeme.py` utilise `\d+` pour capturer l'identifiant dans `que id 123`. Si des identifiants alphanumériques sont utilisés en contexte "même X que id ABC123", il faudra mettre à jour le pattern dans detmeme.py (non modifié dans cette livraison).

---

**FIN DU DOCUMENT**
