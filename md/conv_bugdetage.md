# conv_bugdetage

## Échange 1 — 21/02/2026 ~14:00

**Question** : Bug dans detage.py — `"patients en classe 2 agés de plus de 20 ans et de moins de 23 ans"` ne détecte qu'un seul critère au lieu de deux.

**Diagnostic** : Tracking par `set()` de mots-chaînes → les mots partagés "de", "ans" bloquaient le 2e match.

**Correction** : Remplacement par tracking par **plages de caractères** `(start, end)`.

**Fichier livré** : `detage.py`

---

## Échange 2 — 21/02/2026 ~14:15

**Question** : `"Patient compris entre 13 et 16 avec une classe d'angle de 1 uniquement"` — ni l'âge ni la classe ne sont détectés.

**Diagnostic** : Patterns manquants dans les CSV :
- **ages.csv** : pas de variante sans "ans" pour "entre X et Y" → ajout `|compris entre {n} et {n}|entre {n} et {n}`
- **tags.csv** (protégé) : pas de synonyme "classe d angle de 1" (chiffre après) → 3 ajouts manuels pour classes I/II/III

**Fichiers livrés** : `ages.csv` (enrichi)

---

## Échange 3 — 21/02/2026 ~14:30

**Question** : Résultats detia.py sur quentin.csv — affichage incomplet + BETWEEN cassé.

**3 bugs corrigés dans detia.py** :
1. **Affichage batch** : ajout `{len(ages)} âge(s)` dans le print
2. **Mapping BETWEEN** : `valeur2` était ignorée → SQL `BETWEEN 13` au lieu de `BETWEEN 13 AND 16`
3. **Label BETWEEN** : `"Âge BETWEEN 13"` → `"entre 13 et 16 ans"`

**Fichier livré** : `detia.py`

---

## Échange 4 — 21/02/2026 ~14:45

**Question** : Q3 `"supérieur à 17 et inférieur à 23"` → l'IA fusionne en 1 BETWEEN au lieu de 2 critères.

**Corrections** :
- **detia.py prompt** : règle CRITIQUE ajoutée interdisant la fusion de conditions séparées en BETWEEN
- **ages.csv** : ajout `|inferieur a {n} ans` et `|superieur a {n} ans` pour detage.py

**Fichiers livrés** : `detia.py`, `ages.csv`

---

## Échange 5 — 21/02/2026 ~15:00

**Question** : Le mode batch de detall, detage, dettags et detia n'affiche pas de résumé lisible pour chaque question. Demande d'un mini-résumé identique au mode unitaire.

**Modification** : Ajout dans `traiter_fichier_batch()` de chaque fichier d'un mini-résumé **toujours affiché** (avec ou sans --verbose) pour chaque question :

```
  [1/5] "patients en classe 2 agés de plus de 20 ans et de moins de 23 ans"
        1. [tag] classe ii d'angle
        2. [age] moins de 23 ans
        3. [age] plus age que 20 ans
        Résidu: 'patients en ages de et de'
```

**Détail par fichier** :
- **detall.py** : remplace `{i+1}. {question[:40]}... → N critère(s)` par le mini-résumé complet (tags avec adjectifs, ages, sexe, meme)
- **detage.py** : remplace `→ {question}: N critère(s) [{sorties}]` par le mini-résumé (type + label par critère)
- **dettags.py** : remplace `✓ {question[:50]}... → N tag(s)` par le mini-résumé (tag canonique + catégorie + adjectifs)
- **detia.py** : conserve `[i/n] question... ✓ Nms` en première ligne, puis affiche le détail des critères en dessous

Le --verbose et --debug continuent de contrôler les lignes intermédiaires de diagnostic (regex, patterns testés, etc.).

**4 fichiers livrés** : `detall.py`, `detage.py`, `dettags.py`, `detia.py`

**Exemple de sortie detage.py en batch** (testé) :
```
  [1/5] "patients en classe 2 agés de plus de 20 ans et de moins de 23 ans"
        1. [age] moins de 23 ans
        2. [age] plus age que 20 ans
        Résidu: 'patients en classe 2 ages de et de'

  [3/5] "Patients avec un age supérieur à 17 ans et inférieur à 23 ans de classe 3"
        1. [age] moins de 23 ans
        2. [age] plus age que 17 ans
        Résidu: 'patients avec un age et de classe 3'
```

**Notes sur quentin.csv Q5** : `"Patient metal compris entre 20 e 24 ans"` — le "e" au lieu de "et" empêche le pattern BETWEEN de matcher. Seul "24 ans" est détecté. C'est un manque de pattern dans ages.csv (variante avec "e" au lieu de "et") ou une faute de frappe dans la question.

---

## Échange 6 — 21/02/2026 ~15:15

**Question** : ages.csv — ajouter le pattern avec "e" (faute de frappe) et "&" comme variantes de "et" dans les BETWEEN.

**Correction** : Ajout de `|entre {n} e {n} ans|compris entre {n} e {n}|entre {n} e {n}|entre {n} & {n} ans|compris entre {n} & {n}|entre {n} & {n}|de {n} a {n}` sur la ligne BETWEEN.

**Test validé** : "entre 20 e 24 ans" → BETWEEN [20, 24] ✅

**Fichier livré** : `ages.csv`

---

## Échange 7 — 21/02/2026 ~15:30

**Question** : Étendre le mini-résumé batch à tous les det*.py + search.py pour uniformiser l'affichage.

**7 fichiers modifiés** :

| Fichier | Modification |
|---------|-------------|
| `detcount.py` | `[i/n] "question"` + `→ LIST/COUNT` + résidu |
| `detangles.py` | `[i/n] "question"` + `j. [angle] label → canonique` + résidu |
| `detmeme.py` | `[i/n] "question"` + `j. [meme] label` + référence + résidu |
| `detadjs.py` | `[i/n] "question" (tag: X)` + `j. [adj] canon → accordé` |
| `detid.py` | `[i/n] "question"` + `j. [id] Patient ID XXXX` + résidu |
| `detiabrut.py` | `[i/n] question... ✓ Nms` + détail critères + résidu |
| `search.py` | `[i/n] "question"` + critères détectés + `→ N patient(s) en Nms` + routage |

**Fichiers non modifiés** (pas de mode batch) : `trouve.py`, `trouveid.py`

**Format uniforme** :
```
  [1/5] "patients en classe 2 agés de plus de 20 ans"
        1. [tag] classe ii d'angle
        2. [age] moins de 23 ans
        Résidu: 'patients en ages de'
```

Le `--verbose` / `--debug` continue de contrôler les lignes intermédiaires de diagnostic.

---

## Échange 8 — 21/02/2026 ~16:00

**Question** : Ajouter mode batch à trouve.py et trouveid.py + corriger search.py (complètement cassé en batch).

### search.py — 3 bugs corrigés

| Bug | Cause | Correction |
|-----|-------|------------|
| **Langue "zu"** | `_traiter_fichier_batch` ne reçoit PAS le `lang` du CLI. Chaque question utilise `lang='auto'` du CSV → `detecter_langue()` renvoie 'zu', 'id', etc. | Ajout paramètre `lang_override` à la fonction batch. Si CLI spécifie une langue → forcée pour toutes les questions. Si 'auto' → défaut CSV changé de `'auto'` à `'fr'` |
| **Fichier introuvable** | Pas de recherche multi-répertoires (contrairement aux autres det*.py) | Ajout `_trouver_fichier()` identique aux autres modules (., tests/, script_dir/tests/) |
| **Pas de mini-résumé** | Affichage batch basique sans détail critères | Ajout format uniforme `[i/n] "question"` + critères numérotés + `→ N patient(s) en Nms` |

**Appel corrigé dans main()** :
```python
nb_lignes = _traiter_fichier_batch(
    base_path, question_or_file, mode_detection, model, verbose, api_key,
    lang_override=lang  # ← NOUVEAU : passe le lang CLI
)
```

### trouve.py — Mode batch ajouté

- `_trouver_fichier()` : recherche CSV dans `.`, `tests/`, `script_dir/tests/`
- `traiter_fichier_batch()` : charge les références UNE SEULE FOIS, puis boucle sur les questions
- Sortie CSV : `question;nb_patients;nb_criteres;mode;temps_ms;residu;erreur`
- Mini-résumé identique aux det*.py
- main() modifié : si arg2 finit par `.csv` → mode batch

**Exemples CLI** :
```
python trouve.py base1000.db quentin.csv
python trouve.py base1000.db quentin.csv -v
python trouve.py base1000.db quentin.csv ia
```

### trouveid.py — Mode batch ajouté

- Import conditionnel de `detmeme` pour le batch
- `traiter_fichier_batch()` : pour chaque question → `detmeme` → `enrichir_avec_reference`
- Sortie CSV : `question;nb_criteres;reference;residu`
- Mini-résumé avec patient de référence résolu
- main() modifié : argparse avec `add_help=False`, aide si pas d'args, détection `.csv`
- Résolution base dans `bases/` comme les autres modules

**Exemples CLI** :
```
python trouveid.py base1000.db testsmemein.csv
python trouveid.py base1000.db '{"criteres": [...]}' -v
```

**3 fichiers livrés** : `search.py`, `trouve.py`, `trouveid.py`

---

## Échange 9 — 21/02/2026 ~16:30

**Question** : search.py toujours cassé. `python search.py quentin.csv base1964.db` → prend quentin.csv comme base. `python search.py tests/quentin.csv base1964.db` → traite "base1964.db" comme question → langue "zu". Français par défaut SVP.

### Diagnostic — 3 bugs racine

| Bug | Cause | Correction |
|-----|-------|------------|
| **Parser rigide** | `argv[1]` = base, `argv[2]` = question. L'utilisateur doit respecter l'ordre exact, contrairement à tous les autres modules (trouve.py etc.) qui détectent `.db` automatiquement | Parser flexible : boucle sur tous les args, `.db` → base, `.csv` → batch, reste → question. **Ordre libre.** |
| **Langue 'auto' par défaut** | `_parser_arguments_flexibles` : `'lang': 'auto'`. En batch, chaque question part en auto-détection → `detecter_langue("base1964.db")` renvoie "zu" (zoulou) | `'lang': 'fr'` par défaut. En batch, `lang_cli='fr'` forcé pour toutes les questions |
| **Mots-clés vs arguments** | Modes (ia, standard), langues (de, fr) et modèles mélangés avec les positionnels | Set `mots_cles` = modes ∪ langues ∪ modèles. Ces mots sont exclus de la détection base/question |

### Comportement après fix

```
python search.py quentin.csv base1964.db       ✓ base=base1964.db, fichier=quentin.csv
python search.py base1964.db quentin.csv       ✓ idem
python search.py base1964.db "bruxisme"        ✓ question unitaire en fr
python search.py base1964.db "bruxisme" ia     ✓ mode IA
python search.py "Tiefbiss" base1964.db de     ✓ question en allemand
python search.py base1964.db quentin.csv --lang=de  ✓ batch forcé en de
```

**Fichier livré** : `search.py`
