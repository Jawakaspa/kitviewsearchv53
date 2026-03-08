# conv_renommer.md

## Conversation : renommer

---

### 2025-02-11 21:09 — Création de renomme.py

**Demande** : Créer `renomme.py` qui renomme des images (png/jpg) d'un répertoire donné en paramètre, selon un fichier CSV à 2 colonnes (`ancien;nouveau`). L'extension d'origine est conservée.

**Fichier fourni** : `renomme.csv` (62 lignes, UTF-8-SIG, séparateur `;`)

**Observations** :
- La colonne `ancien` contient le nom complet avec extension
- La colonne `nouveau` contient le nouveau nom SANS extension
- Plusieurs lignes partagent le même `nouveau` + même extension → doublons gérés avec suffixe `_2`, `_3`...

**Livré** : `renomme.py`
- CLI avec aide auto si aucun argument
- Options : `-d`/`--debug`, `-v`/`--verbose`, `--dry-run`
- Recherche insensible à la casse pour trouver les fichiers sources
- Extension d'origine conservée telle quelle (casse incluse)
- Ne touche pas aux fichiers non listés dans le CSV
- Vérifie l'encodage UTF-8-SIG du CSV

**Tests** : OK — dry-run puis exécution réelle sur 6 fichiers simulés, doublons gérés, fichier `.txt` non touché.

---

### 2025-02-11 21:15 — Debug de gen1964_v2.py

**Demande** : 2026 lignes en entrée mais seulement 1986 en sortie + CSV pas en UTF-8-SIG.

**3 bugs trouvés et corrigés** :

1. **Regex extensions** (ligne 92) : `(jpg|JPG)` → ajout `png|jpeg` + `re.IGNORECASE`
   - 40 fichiers `.PNG`/`.png` étaient ignorés

2. **Regex taille fichier** (ligne 92) : `[\d ]+` → `[\dÿ ]+`
   - Le caractère `ÿ` (séparateur de milliers Windows FR dans `dir`) n'était pas reconnu
   - Par backtracking, la taille du fichier polluait la colonne portrait : `23ÿ217 ABAIDIA...` au lieu de `ABAIDIA...`

3. **Encodage sortie** (ligne 99) : `encoding="utf-8"` → `encoding="utf-8-sig"`

4. **extract_name_parts** (ligne 70) : même fix extensions que le bug 1

**Résultat** : 2026/2026 lignes, portraits propres, BOM OK.

---

### Prompts de recréation

#### renomme.py
```
Crée renomme.py : programme CLI qui renomme des images (png/jpg/jpeg) d'un répertoire
selon un fichier CSV de correspondance (ancien;nouveau).

Entrées :
- Argument 1 : répertoire contenant les images
- Argument 2 : fichier CSV (UTF-8-SIG, séparateur ;, colonnes : ancien;nouveau)
  - ancien = nom complet avec extension
  - nouveau = nouveau nom SANS extension

Comportement :
- Conserve l'extension d'origine (y compris sa casse)
- Recherche insensible à la casse pour trouver les fichiers
- Gère les doublons avec suffixe _2, _3...
- Ne touche pas aux fichiers absents du CSV
- Vérifie le BOM UTF-8-SIG du CSV
- Sans argument → affiche l'aide
- Options : -d/--debug, -v/--verbose, --dry-run
- Bilan en fin d'exécution (renommés, absents, erreurs, doublons)

PJ nécessaire : renomme.csv
Respecter Prompt_contexte.md
```

#### gen1964_v2.py
```
Pas de prompt de recréation : ce fichier est fourni par l'utilisateur, corrigé uniquement sur les 3 bugs identifiés.
PJ nécessaires : DirCcxphotothumbsbase_yu.txt, prenoms_insee.csv
```
