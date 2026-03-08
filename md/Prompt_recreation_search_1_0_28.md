# Prompt de recréation - search.py V1.0.28

## Fichiers à fournir en PJ
1. `search.py` (version 1.0.27 - fichier à modifier)
2. `ia.csv` (version 1.0.13 avec les nouveaux modes)
3. `Prompt_contexte2312.md` (contexte projet TDD)
4. `Fiche_modes_recherche.md` (documentation des modes)

## Prompt complet

```
Je travaille sur l'application KITVIEW, un système de recherche multilingue orthodontique. Le projet suit la philosophie TDD.

### Contexte

search.py gère le routage intelligent des recherches avec des fallbacks automatiques :
- Mode `standard` : detall.py → fallback IA si 0 → fallback DeepL si toujours 0
- Mode `ia` : detia.py → fallback DeepL si 0

### Besoin

Ajouter deux nouveaux modes SANS fallback pour les tests CLI et le debug :
- `purstandard` : detall.py uniquement, aucun fallback
- `puria` : detia.py uniquement, aucun fallback DeepL

Ces modes doivent être :
1. Ajoutés dans MODES_VALIDES
2. Gérés explicitement dans la logique de routage (pas de magie avec startswith)
3. Documentés dans la docstring

### Modifications demandées dans search.py

1. **Version** : V1.0.27 → V1.0.28, date 09/01/2026 15:20:00

2. **Docstring** : Ajouter les changements V1.0.28 :
   - NOUVEAUX MODES : 'purstandard' et 'puria' sans fallback automatique
   - purstandard : detall.py uniquement
   - puria : detia.py uniquement
   - MODES_VALIDES étendu

3. **MODES_VALIDES** : 
   ```python
   MODES_VALIDES = ['standard', 'ia', 'purstandard', 'puria']
   ```
   Avec commentaires explicatifs pour chaque mode.

4. **Logique de routage** dans la fonction search() :
   Remplacer le bloc `if mode_detection == 'ia': ... else: ...` par 4 branches :
   
   ```python
   if mode_detection == 'puria':
       # IA seule sans fallback
       parcours_detection.append(f"puria:...")
       resultats = rechercher(..., mode='ia', ...)
       mode_effectif = 'puria'
       # PAS DE FALLBACK
   
   elif mode_detection == 'ia':
       # IA avec fallback DeepL (code existant)
       ...
   
   elif mode_detection == 'purstandard':
       # Standard seul sans fallback
       parcours_detection.append(f"purstandard:...")
       resultats = rechercher(..., mode='standard', ...)
       mode_effectif = 'purstandard'
       # PAS DE FALLBACK
   
   else:  # standard
       # Standard avec tous les fallbacks (code existant)
       ...
   ```

### Spécifications techniques

- Python 3.13+
- Encodage UTF-8 sans BOM
- Ne pas modifier la signature de search()
- Conserver toute la logique existante pour les modes 'standard' et 'ia'

### Comportement attendu

```bash
# purstandard : un seul appel à detall.py
python search.py base.db "test" purstandard -v
# → Parcours: purstandard:N (pas de →ia, pas de →deepl)

# puria : un seul appel à detia.py
python search.py base.db "test" puria -v
# → Parcours: puria:N (pas de →deepl)
```

Livrer search.py V1.0.28 complet.
```

## Notes

- Le fichier ia.csv doit aussi être mis à jour pour inclure `purstandard` et `puria` (V1.0.13)
- Ces modes apparaîtront dans le dropdown de l'interface web grâce à ia.csv
