# Prompt conv_debug_meme V1.0.0 - 22/01/2026 19:22:14

# Synthèse conversation : debug_meme

## Informations générales
- **Date de création** : Jeudi 22 janvier 2026
- **Projet** : KITVIEW - Recherche patients orthodontie
- **Sujet** : Debug du pipeline "même X que patient"

---

## Échange 1 - 22/01/2026 17:42 → 18:30 UTC

### Question initiale
Thierry signale que la recherche "même portrait que Guillaume Moulin" ne fonctionne pas sur `base25000.db` :
- Guillaume Moulin n'apparaît pas dans les résultats (pas de fond jaune)
- Impossible d'affiner la recherche
- Le test "patients qui grincent des dents" fonctionne (6407 résultats, Guillaume Moulin ID 2 visible)

### Fichiers fournis
- `detmeme.py` V1.0.5
- `detcount.py`
- `trouveid.py` V1.0.5
- `jsonsql.py` V1.0.7
- `trouve.py` V1.0.19
- `gardefou.py`
- `lancesql.py` V1.0.4
- `communb.csv` V1.0.0
- `test_meme_cli.cmd` (résultats sur base1000)
- Captures d'écran web24.html

### Clarifications obtenues
1. **Guillaume Moulin existe dans base25000.db** (ID 2, 19 ans, bruxisme, idportrait=29)
2. **commun.csv remplacé par communb.csv** (format vertical section;parametre;valeur)
3. **Le patient de référence DOIT être inclus dans les résultats** (Option A) pour permettre :
   - Affichage en fond jaune comme référence
   - Possibilité d'affiner avec "même âge", "même sexe", etc.

### Diagnostic

**BUG IDENTIFIÉ dans jsonsql.py V1.0.7 lignes 338-341** :
```python
# Exclure le patient de référence lui-même des résultats
if where_clause and ref_id:
    where_clause = f"({where_clause} AND p.id != ?)"
    params.append(ref_id)
```

Le code **excluait systématiquement le patient de référence** ce qui empêchait :
1. L'affichage de Guillaume Moulin en fond jaune
2. L'affinement progressif en entonnoir

### Tests de diagnostic effectués

| Module | Version | Test | Résultat |
|--------|---------|------|----------|
| `detmeme.py` | V1.0.5 | Parsing "meme portrait que Guillaume Moulin" | ✅ OK |
| `trouveid.py` | V1.0.5 | Résolution nom → ID 2 | ✅ OK |
| `jsonsql.py` | V1.0.7 | Génération SQL | ❌ **BUG** `AND p.id != 2` |

### Correction appliquée

**jsonsql.py V1.0.7 → V1.0.8**

Suppression de l'exclusion du patient de référence :
```python
# AVANT (V1.0.7) - BUGUÉ
if where_clause and ref_id:
    where_clause = f"({where_clause} AND p.id != ?)"
    params.append(ref_id)

# APRÈS (V1.0.8) - CORRIGÉ
# Le patient de référence est maintenant INCLUS
# (code supprimé, remplacé par commentaire explicatif)
```

### Validation de la correction

```
AVANT: WHERE (p.idportrait = ? AND p.id != ?)  Params: ['29', 2]
APRÈS: WHERE p.idportrait = ?                   Params: ['29']
```

✅ Guillaume Moulin (ID 2) sera maintenant inclus dans les résultats.

---

## Fichiers modifiés

| Fichier | Ancienne version | Nouvelle version | Modification |
|---------|------------------|------------------|--------------|
| jsonsql.py | V1.0.7 | **V1.0.8** | Suppression exclusion patient référence |

---

## Prochaines étapes
1. ✅ Tests CLI systématiques sur base25000.db - FAIT
2. ✅ Correction de jsonsql.py - FAIT  
3. [ ] Tester sur l'IHM web24.html que Guillaume Moulin apparaît avec fond jaune
4. [ ] Vérifier que l'affinement "même âge", "même sexe" fonctionne

---

## Prompt de recréation de jsonsql.py V1.0.8

Pour recréer `jsonsql.py` V1.0.8 à partir de zéro :

**Fichiers PJ nécessaires :**
- `jsonsql.py` V1.0.7 (version précédente)
- `communb.csv` (pour les synonymes)

**Instructions :**
1. Prendre jsonsql.py V1.0.7
2. Supprimer les lignes 338-341 qui excluent le patient de référence
3. Ajouter le commentaire explicatif V5.1.1
4. Mettre à jour le cartouche de version

---

## Historique des versions du document
- V1.0.0 - 22/01/2026 17:58 : Création initiale, diagnostic du bug
- V1.1.0 - 22/01/2026 18:30 : Ajout correction jsonsql.py V1.0.8
