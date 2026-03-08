# Prompt conv_gardefou V1.0.1 - 09/01/2026 19:21:56

# Synthèse conversation : gardefou

**Projet** : KITVIEW - Recherche multilingue orthodontique  
**Date de début** : 09/01/2026 14:23

---

## 📅 09/01/2026 14:23 - Bug gardefou - Régression fonctionnelle

### Problème rapporté

La fonctionnalité "gardefou" qui devait empêcher de retourner toute la base de données (25000 patients) quand aucun critère de recherche n'est détecté ne fonctionnait plus.

**Commande de test :**
```bash
python search.py base25000.db "et ta soeur elle bat le beurre" -v
```

**Comportement observé :** 25000 patients retournés au lieu de 0
**Comportement attendu :** 0 patient avec message d'erreur explicatif

### Analyse

Après analyse des fichiers fournis (`gardefou.py`, `trouve.py`, `search.py`, `detall.py`, `detia.py`), le bug a été identifié dans `trouve.py` aux lignes 331-335 :

```python
if GARDEFOU_DISPONIBLE and len(criteres_detectes) == 0 and nb_resultats > 100:
    syntags_data = get_syntags_gardefou()
    
    if syntags_data:  # ← BUG ICI : si syntags.csv absent/vide, gardefou ignoré !
        # ... vérification garde-fou
```

**Cause racine** : Le bloc `if syntags_data:` faisait que le gardefou était silencieusement désactivé quand `syntags.csv` n'était pas trouvé ou était vide.

### Correction apportée

**Fichier modifié** : `trouve.py` V1.0.17 → V1.0.18

**Modifications clés :**

1. **Suppression complète de syntags.csv** : Ce fichier obsolète n'est plus référencé du tout
2. **Filtrage des critères "count"** : Seuls les vrais critères de filtrage (tags, âges, angles, sexe) sont comptés
3. **Simplification du code** : Suppression du cache `_SYNTAGS_GARDEFOU_CACHE` et de `get_syntags_gardefou()`
4. **Amélioration de l'affichage CLI** : Message explicite quand le gardefou est activé

**Code corrigé (extrait) :**
```python
# Filtrer les critères de type "count" qui ne sont pas des vrais filtres
criteres_filtrage = [c for c in criteres_detectes if c.get('type') not in ('count', 'list')]

if GARDEFOU_DISPONIBLE and len(criteres_filtrage) == 0 and nb_resultats > 100:
    # Appeler le gardefou sans syntags (liste vide)
    verdict = verifier_intention_tous(question, [], verbose=verbose, debug=debug)
    # ... reste du code
```

### Fichiers livrés

| Fichier | Version | Description |
|---------|---------|-------------|
| `trouve.py` | V1.0.18 | Correction gardefou + suppression syntags.csv |

### Tests à effectuer

```bash
# Test 1 : Question absurde → doit retourner 0 patient
python search.py base25000.db "et ta soeur elle bat le beurre" -v

# Test 2 : Question légitime → doit retourner des résultats
python search.py base25000.db "bruxisme" -v

# Test 3 : Demande explicite "tous" → doit retourner tous les patients
python search.py base25000.db "tous les patients" -v
```

---

## Prompt de recréation - trouve.py V1.0.18

### Fichiers à fournir en PJ
- `trouve.py` (version 1.0.17 ou actuelle)
- `gardefou.py` (pour référence)
- `Prompt_contexte2312.md` (contexte projet)

### Prompt

```
Contexte : Application KITVIEW de recherche multilingue orthodontique.

Le module gardefou.py a pour fonction d'empêcher qu'une requête sans critères de recherche détectés retourne toute la base de données. Cette fonctionnalité s'est perdue suite à une régression.

Bug identifié dans trouve.py : Le gardefou dépendait de syntags.csv (obsolète) et était ignoré si ce fichier était absent.

Correction demandée :
1. Supprimer TOUTES les références à syntags.csv (fichier obsolète)
2. Supprimer le cache _SYNTAGS_GARDEFOU_CACHE et la fonction get_syntags_gardefou()
3. Appeler verifier_intention_tous() avec une liste vide : verifier_intention_tous(question, [], ...)
4. Filtrer les critères de type "count"/"list" car ce ne sont pas des critères de filtrage réels
5. Améliorer l'affichage CLI pour montrer clairement quand le gardefou est activé

Livrer trouve.py V1.0.18 avec les modifications.
```

---

*Document mis à jour le 09/01/2026 14:45*

---

## 📅 09/01/2026 15:15 - Ajout des modes purstandard et puria

### Demande

Ajouter deux modes de recherche sans fallback automatique pour faciliter les tests CLI :
- `purstandard` : detall.py uniquement, aucun fallback IA ni DeepL
- `puria` : detia.py uniquement, aucun fallback DeepL

### Analyse préalable

**Modes existants et leurs fallbacks :**

| Mode | Fallback IA | Fallback DeepL |
|------|-------------|----------------|
| `standard` | ✅ Si 0 résultat | ✅ Si toujours 0 ET langue ≠ fr |
| `ia` | - | ✅ Si 0 résultat ET langue ≠ fr |

**Chaîne de fallback mode standard :**
```
standard → ia (si 0) → deepl+standard (si 0) → deepl+ia (si 0)
```

**Chaîne de fallback mode ia :**
```
ia → deepl+ia (si 0 et langue ≠ fr)
```

### Décision

- Ajouter `purstandard` et `puria` dans `ia.csv` pour qu'ils soient sélectionnables dans l'interface web
- Modifier `search.py` pour gérer ces modes explicitement (pas de logique "magique" avec préfixe)

### Modifications apportées

**ia.csv V1.0.12 → V1.0.13 :**
```csv
purstandard;;O;;0;Recherche standard SANS fallback (tests/debug);...
puria;;O;;0;Recherche IA SANS fallback DeepL (tests/debug);...
```

**search.py V1.0.27 → V1.0.28 :**
- `MODES_VALIDES` étendu à `['standard', 'ia', 'purstandard', 'puria']`
- Logique de routage modifiée avec 4 branches explicites :
  1. `puria` → IA seule
  2. `ia` → IA + fallback DeepL
  3. `purstandard` → Standard seul
  4. `standard` (else) → Standard + fallback IA + fallback DeepL

### Fichiers livrés

| Fichier | Version | Description |
|---------|---------|-------------|
| `ia.csv` | V1.0.13 | Ajout des modes purstandard et puria |
| `search.py` | V1.0.28 | Support des nouveaux modes |
| `Fiche_modes_recherche.md` | V1.0 | Documentation complète des modes |

### Tests à effectuer

```bash
# Test purstandard - doit donner le résultat detall.py sans fallback
python search.py base25000.db "bruxisme" purstandard -v
# Attendu: parcours = "purstandard:N"

# Test puria - doit donner le résultat detia.py sans fallback
python search.py base25000.db "bruxisme" puria -v
# Attendu: parcours = "puria:N"

# Test standard - doit faire fallback si 0
python search.py base25000.db "terme_inconnu_xyz" standard -v
# Attendu: parcours = "standard:0→ia:N" ou plus

# Comparaison des modes
python search.py base25000.db "béance antérieure" purstandard -v
python search.py base25000.db "béance antérieure" puria -v
```

---

*Document mis à jour le 09/01/2026 15:20*
