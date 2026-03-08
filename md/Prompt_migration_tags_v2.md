# Prompt_migration_tags_v2.md — Migration tags.csv / adjectifs.csv V1 → V2

**Date** : 09/02/2026  
**Contexte** : Remplacement de tags.csv (V1, 143 tags) et adjectifs.csv (V1, 42 adjectifs) par les versions auditées V2 (151 tags, 51 adjectifs)  
**Risque** : FAIBLE — données patients fictives, parseurs par nom de colonne

---

## 1. Diagnostic d'impact par fichier

### 1.1 dettags.py — charger_tags()

| Point de contrôle | Code (ligne) | Verdict |
|---|---|---|
| Validation colonnes | `colonnes_requises = {'t', 'gn', 'as', 'pts'}` → `issubset()` (L170) | ✅ La 5e colonne `cat` est ignorée |
| Accès données | `row.get('t')`, `row.get('gn')`, `row.get('as')`, `row.get('pts')` (L178-188) | ✅ Par nom, jamais par position |
| Structure stockée | `tags_data['tags'][canon_lower] = {'canon', 'gn', 'adjs_autorises', 'patterns'}` (L192) | ⚠️ `cat` n'est PAS stockée — à enrichir |

**Action** : Ajouter lecture de `cat` et stockage dans `tags_data['tags'][canon_lower]['cat']`

### 1.2 detadjs.py — charger_adjectifs()

| Point de contrôle | Code (ligne) | Verdict |
|---|---|---|
| Validation colonnes | `colonnes_requises = {'a', 'f', 'mp', 'fp', 'pas'}` → `issubset()` (L158) | ✅ Aucune colonne ajoutée |
| Accès données | `row.get('a')`, `row.get('f')`, etc. (L169-181) | ✅ Par nom |

**Action** : Aucune modification nécessaire. Le fichier adjectifs_v2.csv garde la même structure.

### 1.3 detia.py — _charger_tags_csv()

| Point de contrôle | Code (ligne) | Verdict |
|---|---|---|
| Lecture | `csv.DictReader` + `row.get('t')`, `row.get('pts')` (L268-291) | ✅ `cat` ignorée |
| Prompt IA | Injecte `liste_stdtag` comme liste plate (L391) | ⚠️ Pas de catégorie → opportunité manquée |

**Action** : Enrichir pour que le prompt IA injecte `"béance (pathologie)"` au lieu de `"béance"`.

### 1.4 detiabrut.py

| Point de contrôle | Verdict |
|---|---|
| Utilise `charger_references()` de detia.py | ✅ Même code, même conclusion |
| Prompt enrichi | ⚠️ Même opportunité que detia.py |

**Action** : Bénéficie automatiquement des changements dans detia.py.

---

## 2. Table de correspondance V1 → V2

### 2.1 Tags supprimés

| Tag V1 | Action V2 | Destination |
|---|---|---|
| `enclavement` | Fusionné | → `inclusion` (patterns : "dent enclavée", "enclavement", "enclavée" ajoutés) |
| `supraposition` | Splitté | → `overjet` (surplomb horizontal) + `égression` (supra-éruption, "dent en supraposition") |

### 2.2 Tags ajoutés (10)

| Tag V2 | cat | Origine |
|---|---|---|
| `overjet` | pathologie | Scission de supraposition |
| `endoalvéolie` | pathologie | Nouveau |
| `ancrage` | traitement | Nouveau |
| `force orthodontique` | biomécanique | Nouveau |
| `nivellement` | biomécanique | Nouveau |
| `analyse de bolton` | diagnostic | Nouveau |
| `photographie clinique` | diagnostic | Nouveau |
| `orthodontie linguale` | traitement | Nouveau |
| `auxiliaire` | traitement | Nouveau |
| `arc transpalatin` | traitement | Nouveau |

### 2.3 Adjectifs ajoutés (9)

| Adjectif V2 | Genre | Féminin |
|---|---|---|
| `chirurgical` | m | chirurgicale |
| `ectopique` | mf | ectopique |
| `inférieur` | m | inférieure |
| `invisible` | mf | invisible |
| `labial` | m | labiale |
| `labio-palatin` | m | labio-palatine |
| `palatin` | m | palatine |
| `retardé` | m | retardée |
| `supérieur` | m | supérieure |

### 2.4 Patterns redistribués (malocclusion nettoyée)

12 patterns retirés de `malocclusion` et redistribués vers les tags spécifiques :

| Pattern | De (V1) | Vers (V2) |
|---|---|---|
| `disjoncteur` | malocclusion | quad helix |
| `disjoncteur palatin` | malocclusion | quad helix |
| `appareil dentaire` | malocclusion | bagues |
| `dent bloquée` | malocclusion | inclusion |
| et 8 autres patterns... | malocclusion | tags spécifiques |

---

## 3. Plan d'exécution

### Phase 1 : Copie directe (immédiat, sans modification de code)

```
1. Copier tags_v2.csv → refs/tags.csv
2. Copier adjectifs_v2.csv → refs/adjectifs.csv
3. Tester : python dettags.py "béance antérieure" -v
4. Tester : python dettags.py "overjet sévère" -v
5. Tester : python dettags.py "inclusion" -v (doit matcher "enclavement" en pattern)
```

**Résultat attendu** : Fonctionnel immédiatement. La colonne `cat` est ignorée par les parseurs existants. Aucun code cassé.

### Phase 2 : Exploiter `cat` dans le code (4 fichiers à modifier)

#### 2a. dettags.py — Stocker `cat`

```python
# Ligne ~192, dans charger_tags(), ajouter 'cat' au dict stocké :
tags_data['tags'][canon_lower] = {
    'canon': canon,
    'gn': gn,
    'cat': (row.get('cat') or '').strip(),  # NOUVEAU V2
    'adjs_autorises': adjs_autorises,
    'patterns': patterns
}
```

```python
# Ligne ~375, dans le critère JSON de sortie, ajouter :
critere = {
    'type': 'tag',
    'detecte': texte_detecte,
    'canonique': canontag,
    'label': canontag,
    'gn': genre_tag,
    'cat': tag_info.get('cat', ''),  # NOUVEAU V2
    'sql': { ... }
}
```

#### 2b. detia.py — Enrichir le prompt IA

```python
# Dans _charger_tags_csv(), ligne ~280, stocker aussi la catégorie :
categories = {}  # {canon_std: cat}

for row in reader:
    canon = (row.get('t') or '').strip()
    cat = (row.get('cat') or '').strip()
    # ...existant...
    if cat:
        categories[canon_std] = cat

return liste_stdtag, mapping, synonymes_importants, categories
```

```python
# Dans _construire_prompt_systeme(), enrichir la liste :
# Au lieu de : "- béance"
# Produire : "- béance (pathologie)"
tags_liste = '\n'.join(
    f"- {t} ({categories.get(t, '')})" if categories.get(t) else f"- {t}"
    for t in references.get('liste_tags', [])[:100]
)
```

#### 2c. detiabrut.py — Bénéficie automatiquement

Puisqu'il utilise `charger_references()` de detia.py, les changements se propagent.

### Phase 3 : Régénérer les bases fictives

```
python build_base.py all   # Régénère les bases avec les nouveaux tags
```

Les tags fictifs seront générés depuis le nouveau tags.csv (151 tags) — aucune migration de données puisqu'elles sont fictives.

### Phase 4 : Tests de non-régression

Fichier de test recommandé (`tests/testtagsin_v2.csv`) :

```csv
# Tests de non-régression migration V2
# Cas existants qui doivent continuer à fonctionner
question
béance antérieure sévère
classe i classe ii
bruxisme nocturne
patients avec malocclusion modérée
# Nouveaux tags V2
overjet sévère
endoalvéolie maxillaire
ancrage cortical
force orthodontique modérée
analyse de bolton
# Tags fusionnés (enclavement → inclusion)
dent enclavée
enclavement dentaire
# Patterns redistribués (doivent matcher le bon tag)
disjoncteur palatin
appareil dentaire métallique
dent bloquée
# Adjectifs V2
gouttière chirurgicale
gouttière invisible
éruption ectopique
éruption retardée
fente labio-palatine
procheilie supérieure
```

---

## 4. Fichier angles.csv — Verdict

Toutes les références de `angles.csv` vers les tags canoniques ont été vérifiées :

| Tag dans angles.csv | Présent dans tags_v2.csv | Ligne |
|---|---|---|
| classe i squelettique | ✅ | 33 |
| classe ii squelettique | ✅ | 35 |
| classe iii squelettique | ✅ | 37 |
| prognathisme maxillaire | ✅ | 122 |
| rétrognathie maxillaire | ✅ | 136 |
| prognathie mandibulaire | ✅ | 121 |
| rétrognathie mandibulaire | ✅ | 135 |
| mandibule normopositionnée | ✅ | 93 |
| maxillaire normopositionné | ✅ | 95 |

**→ angles.csv est 100% compatible. Aucune modification nécessaire.**

---

## 5. Rollback

En cas de problème :

```
1. Restaurer tags.csv et adjectifs.csv depuis les sauvegardes (c:/gs/)
2. Reverter les modifications code (git revert ou copie depuis c:/gs/)
3. Régénérer les bases : python build_base.py all
```

---

## 6. Résumé des livrables

| # | Livrable | État |
|---|---|---|
| 1 | Ce document (Prompt_migration_tags_v2.md) | ✅ Fait |
| 2 | Tags_v2.csv → copie vers refs/tags.csv | 🔜 Phase 1 |
| 3 | Adjectifs_v2.csv → copie vers refs/adjectifs.csv | 🔜 Phase 1 |
| 4 | Modifications dettags.py (stocker `cat`) | 🔜 Phase 2 |
| 5 | Modifications detia.py (prompt enrichi avec `cat`) | 🔜 Phase 2 |
| 6 | Fichier de test testtagsin_v2.csv | 🔜 Phase 4 |
| 7 | Régénération bases fictives | 🔜 Phase 3 |

---

## 7. Prompt de recréation

Pour recréer les .py modifiés depuis zéro :

### dettags.py
```
python dettags.py                              # → Affiche l'aide
python dettags.py "béance antérieure" -v       # → Test unitaire verbose
python dettags.py "béance antérieure" -d       # → Test unitaire debug
python dettags.py testtagsin.csv -v            # → Test batch
```
**PJ nécessaires** : tags.csv, adjectifs.csv, standardise.py, detadjs.py

### detia.py
```
python detia.py                                # → Affiche l'aide  
python detia.py "bruxisme sévère" -v           # → Test unitaire
python detia.py "béance antérieure" -d         # → Debug complet
```
**PJ nécessaires** : tags.csv, adjectifs.csv, angles.csv, ages.csv, standardise.py, ia.csv

### detiabrut.py
```
python detiabrut.py "bruxisme sévère" -v                        # → Tous référentiels
python detiabrut.py "grincement" -tags -v                       # → Sans tags
python detiabrut.py "bruxisme sévère" -tags -mapping -v         # → Sans tags ni mapping
```
**PJ nécessaires** : Mêmes que detia.py
