# Prompt_creecommentaires.md

## Objectif
Créer le programme `creecommentaires.py` qui génère un fichier de pathologies à partir d'un fichier CSV de patients.

## Pièces jointes requises
- `Prompt_contexte2312.md` (contexte général du projet)
- Un fichier de patients CSV (ex: `pats100.csv`) contenant les colonnes `canontags` et `canonadjs`

## Spécifications

### Fichier d'entrée (patients CSV)
- Encodage : UTF-8-BOM
- Séparateur : `;`
- Colonnes requises : `id`, `canontags`, `canonadjs`

### Fichier de sortie
- **Nom** : `commentaires.csv`
- **Emplacement** : `/refs/commentaires.csv`
- **Encodage** : UTF-8-BOM (utf-8-sig)
- **Séparateur** : `;`
- **Colonnes** : `oripathologie;commentaire`

### Règle de génération des oripathologies

Pour chaque patient :
1. Séparer `canontags` par `,` → liste de tags
2. Séparer `canonadjs` par `,` → liste d'adjectifs (correspondance positionnelle)
3. Pour chaque position `i` :
   - Si `canonadjs[i]` contient des `|`, séparer et trier alphabétiquement
   - Concaténer : `tag[i] + " " + adjs_triés`
   - **Normaliser en minuscules**
4. Dédoublonner toutes les oripathologies du fichier

**Exemples :**

| canontags | canonadjs | oripathologies |
|-----------|-----------|----------------|
| `Bruxisme` | `nocturne\|sévère` | `bruxisme nocturne sévère` |
| `béance,Bruxisme` | `latérale,nocturne\|sévère` | `béance latérale`, `bruxisme nocturne sévère` |
| `béance` | `` | `béance` |
| `latérodéviation` | `Mandibulaire\|gauche` | `latérodéviation gauche mandibulaire` |

### Comportement avec fichier existant

- Si `commentaires.csv` existe déjà :
  - Charger les entrées existantes en normalisant la casse (minuscules)
  - Conserver toutes les lignes existantes (y compris celles avec commentaire vide)
  - Conserver les oripathologies disparues (patients supprimés)
  - Fusionner les entrées avec casse différente (ex: `Bruxisme` → `bruxisme`)
  - Ajouter uniquement les nouvelles oripathologies détectées
- Tri alphabétique du fichier de sortie (insensible à la casse)

### Usage

```bash
python creecommentaires.py <fichier_patients.csv>
```

Exemple :
```bash
python creecommentaires.py pats100.csv
python creecommentaires.py data/pats100.csv
```

### Affichage attendu

```
creecommentaires.py V0.0.0 - 01/01/1970 00:00

[INFO] Racine du projet : /chemin/vers/projet
[INFO] Fichier patients : /chemin/vers/fichier.csv
[INFO] Fichier commentaires : /chemin/vers/refs/commentaires.csv

[INFO] Chargement du fichier existant : ...
[INFO] X oripathologies existantes chargées
[INFO] Lecture du fichier patients : ...
[INFO] Y patients traités
[INFO] Z oripathologies uniques extraites
[INFO] Écriture du fichier : ...
[INFO] N oripathologies écrites

============================================================
RÉSUMÉ
============================================================
  Oripathologies existantes conservées : X
  Nouvelles oripathologies ajoutées   : Y
  Total dans le fichier               : Z
  Fichier généré : /chemin/complet/refs/commentaires.csv
============================================================
```

### Contraintes techniques

- Python 3.13+
- Encodage UTF-8-BOM pour les CSV (lecture et écriture)
- Séparateur `;` pour les CSV
- Ignorer les lignes avec `id` vide (lignes parasites en fin de fichier)
- Détection automatique de la racine du projet (cherche `/refs` ou `/data`)
- Chemins absolus dans tous les affichages
- Cartouche de version au début du fichier (`__pgm__`, `__version__`, `__date__`)
