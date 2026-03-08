# Prompt_sync.md

## Objectif
Créer un programme Python `sync.py` pour comparer et synchroniser récursivement deux répertoires sous Windows, avec gestion des exclusions.

## Pièces jointes requises
- `Prompt_contexte.md` (règles du projet)

## Spécifications fonctionnelles

### Usage
```
python sync.py [repa] [repb] [ok]
```

### Arguments
| Argument | Obligatoire | Défaut | Description |
|----------|-------------|--------|-------------|
| `repa` | Non | `c:\cx` | Premier répertoire à comparer |
| `repb` | Non | `c:\kitviewsearchv5` | Second répertoire à comparer |
| `ok` | Non | - | Si présent, effectue la synchronisation |

### Exemples d'appel
```cmd
python sync.py                           # Compare avec valeurs par défaut
python sync.py c:\cx c:\projet           # Compare deux répertoires spécifiques
python sync.py c:\cx c:\projet ok        # Compare ET synchronise
```

## Exclusions

### Fichiers à ignorer
- Extension `.tmp`

### Répertoires à ignorer

**Par nom exact** (correspondance exacte, insensible à la casse) :
- `.git`
- `__pycache__`
- `.tmp.driveupload`

**Par pattern contenu** (le nom contient le pattern, insensible à la casse) :
- `old` (ex: old, oldies, myold, old_backup, archives_old)
- `convs` (ex: convs, conversations, myconvs)

Les fichiers situés dans ces répertoires (ou leurs sous-répertoires) sont ignorés.

### Implémentation
```python
EXCLUDED_EXTENSIONS = {".tmp"}
EXCLUDED_DIR_EXACT = {".git", "__pycache__", ".tmp.driveupload"}
EXCLUDED_DIR_CONTAINS = {"old", "convs"}
```

La fonction `should_exclude_path(path, base_dir)` vérifie :
1. L'extension du fichier
2. Chaque composant du chemin relatif pour les patterns de répertoires

## Comportement attendu

### Mode comparaison (sans "ok")
1. Afficher les exclusions actives au démarrage
2. Scanner récursivement les deux répertoires (en excluant les patterns)
3. Afficher le nombre de fichiers exclus par les filtres
4. Afficher 4 listes :
   - **Fichiers plus récents dans A** (avec dates A et B)
   - **Fichiers plus récents dans B** (avec dates A et B)
   - **Fichiers uniquement dans A**
   - **Fichiers uniquement dans B**
5. Suggérer la commande pour synchroniser

### Mode synchronisation (avec "ok")
1. Effectuer la comparaison
2. Pour chaque différence :
   - Copier le fichier le plus récent vers l'autre répertoire
   - Copier les fichiers uniques vers l'autre répertoire
3. Afficher le bilan (fichiers copiés, erreurs)

## Format de sortie attendu

```
sync.py V1.0.3 - 12/01/2026 14:35:00
Heure de début: 2026-01-12 14:35:00

[CONFIG] Extensions exclues: .tmp
[CONFIG] Répertoires exclus (exact): .git, .tmp.driveupload, __pycache__
[CONFIG] Répertoires exclus (contenant): convs, old

Répertoire A: C:\cx
Répertoire B: C:\kitviewsearchv5
Mode: COMPARAISON SEULE

[INFO] Scan de C:\cx...
       → 188 fichier(s) exclu(s) par les filtres
       → 284 fichier(s) retenu(s)
[INFO] Scan de C:\kitviewsearchv5...
       → 1000 fichier(s) exclu(s) par les filtres
       → 285 fichier(s) retenu(s)

[INFO] Fichiers identiques (même date): 248

================================================================================
RÉSULTATS DE LA COMPARAISON
================================================================================
...
```

## Contraintes techniques

### Tolérance de date
- Utiliser une tolérance de 2 secondes pour les comparaisons de dates
- Raison : différences entre systèmes de fichiers FAT32/NTFS

### Copie de fichiers
- Utiliser `shutil.copy2` pour préserver les métadonnées (dates, attributs)
- Créer automatiquement les sous-répertoires manquants

### Affichage
- Afficher les chemins absolus
- Format des dates : `YYYY-MM-DD HH:MM:SS`
- Afficher l'heure de début et de fin du traitement
- Afficher les exclusions actives au démarrage

## Respect des conventions projet
- Cartouche `#*TO*#` avec `__pgm__`, `__version__`, `__date__` avant les imports
- Encodage UTF-8 sans BOM
- Affichage du nom, version et date au démarrage de `main()`
- Chemins absolus dans tous les affichages
