# Prompt de recréation - trouve.py V1.0.18

## Fichiers à fournir en PJ
1. `trouve.py` (version 1.0.17 - fichier à corriger)
2. `gardefou.py` (référence pour comprendre le garde-fou)
3. `Prompt_contexte2312.md` (contexte projet TDD)

## Prompt complet

```
Je travaille sur l'application KITVIEW, un système de recherche multilingue orthodontique avec +25000 patients. Le projet suit la philosophie TDD.

### Problème à corriger

Le module gardefou.py est conçu pour empêcher qu'une requête sans critères de recherche détectés (ex: "et ta soeur elle bat le beurre") retourne toute la base de données. 

Cette fonctionnalité a régressé : maintenant une telle requête retourne 25000 patients au lieu de 0.

### Bug identifié dans trouve.py

Le code dépendait de syntags.csv (fichier obsolète) et était ignoré si ce fichier était absent.

### Correction demandée

1. **Supprimer TOUTES les références à syntags.csv** (fichier obsolète)
   - Supprimer le cache `_SYNTAGS_GARDEFOU_CACHE`
   - Supprimer la fonction `get_syntags_gardefou()`
   - Supprimer l'import de `charger_syntags_pour_gardefou`

2. **Appeler verifier_intention_tous() avec une liste vide**
   ```python
   verdict = verifier_intention_tous(question, [], verbose=verbose, debug=debug)
   ```

3. **Filtrer les critères de type "count"/"list"**
   - Ces critères (LIST/COUNT) ne sont pas des critères de filtrage réels
   - Seuls les critères de type 'tag', 'age', 'sexe', 'angle' comptent

4. **Améliorer l'affichage CLI**
   - Afficher clairement quand le gardefou est activé avec sa raison et ses suggestions

### Spécifications techniques

- Python 3.13+
- Encodage UTF-8 sans BOM pour les .py
- Cartouche standard au début :
  ```python
  __pgm__ = "trouve.py"
  __version__ = "1.0.18"
  __date__ = "09/01/2026 14:45:00"
  ```
- Docstring avec CHANGEMENTS V1.0.18 expliquant la correction et le nettoyage

### Comportement attendu après correction

```bash
# Question absurde → 0 patient + message gardefou
python search.py base25000.db "et ta soeur elle bat le beurre" -v
# → Garde-fou activé: aucun_critere_clair
# → Message: Aucun critère de recherche détecté...

# Question légitime → résultats normaux  
python search.py base25000.db "bruxisme" -v
# → 42 patients trouvés

# Demande explicite "tous" → tous les patients
python search.py base25000.db "tous les patients" -v
# → 25000 patients trouvés
```

Livrer trouve.py V1.0.18 complet avec toutes les corrections.
```

## Notes importantes

- Ne pas modifier la signature de la fonction `rechercher()`
- Ne pas modifier les autres fichiers (gardefou.py, search.py, etc.)
- Le gardefou.py fonctionne correctement, c'est l'appel depuis trouve.py qui était défaillant
