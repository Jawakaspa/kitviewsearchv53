# Prompt_search.md

## Objectif

Créer `search.py`, un module de recherche multilingue pour patients orthodontiques utilisant `trouve.py` comme moteur de détection.

Ce module remplace `suche.py` (qui utilisait `cherche.py`) par une nouvelle architecture basée sur `trouve.py` avec support des modes de détection traditionnel et IA.

---

## Architecture

```
Question (any lang) → search.py → trouve.py → Résultats traduits
                          ↓
                    - Détection langue (traduire.py)
                    - Traduction question → français
                    - Appel trouve.rechercher()
                    - Traduction résultats → langue sortie
```

---

## Dépendances

### Fichiers requis en PJ

- `Prompt_contexte0412.md` - Règles du projet (encodage, versions, etc.)
- `trouve.py` - Orchestrateur de recherche avec modes traditionnel/IA/mix/union

### Modules importés

- `trouve.py` : `rechercher()`, `rechercher_mix()`, `rechercher_union()`
- `traduire.py` : `traduire()`, `detecter_langue()`, `LANGUES_NATIVES`
- `standardise.py` : `standardise()` (normalisation texte)

### Fichiers de référence (dans `refs/`)

- `pathoori.csv` : Pathologies multilingues (original;standard;synonymes;fr;en;de;es;it;pt;pl;ro;th;ar;cn;ja)
- `messages.csv` : Messages UI multilingues (usage;fr;en;de;...)

---

## Modes de détection (via trouve.py)

| Mode | Auteur | Description |
|------|--------|-------------|
| `traditionnel` | `cx` | Détection regex/synonymes via detall.py (rapide) |
| `ia` | `eden/claude-sonnet-3.7` | Détection IA via detia.py (Claude) |
| `mix` | - | Compare traditionnel vs IA côte à côte |
| `union` | `cxgti` | Fusionne les résultats (A ∪ B) |

---

## Traductions gérées

### 1. Pathologies patients
- Source : `pathoori.csv`
- Champ : `patients[].oripathologies`
- Méthode : Lookup par terme standardisé, premier synonyme uniquement

### 2. Description des filtres (terme recherché)
- Source : `pathoori.csv`
- Champ : `description_filtres`
- Exemple : "bruxisme + béance" → "歯軋り + 開咬"

### 3. Unité d'âge
- Source : `messages.csv` (clé `unit_year`)
- Champ : `unit_year` + `patients[].unit_year`
- Exemple : "ans" → "歳" (japonais)

### 4. Messages UI
- Source : `messages.csv`
- Champ : `message`
- Clés : `final_none`, `final_exact`, `final_multiple`

---

## Langues natives

Traductions pré-enregistrées dans les fichiers CSV :
```
fr, en, de, es, it, pt, pl, ro, th, ar, cn, ja
```

Autres langues : traduction à la volée via DeepL/MyMemory.

---

## Signature de la fonction principale

```python
def search(
    question: str,                          # Question (n'importe quelle langue)
    base_path: str,                         # Chemin base SQLite
    lang: Optional[str] = None,             # Langue question ('auto', 'fr', 'en', ...)
    mode_detection: str = 'traditionnel',   # traditionnel, ia, mix, union
    verbose: bool = False,                  # Mode debug
    mapping_patho: Optional[dict] = None,   # Cache pathologies (chargé si None)
    messages: Optional[dict] = None,        # Cache messages (chargé si None)
    response_lang: Optional[str] = None,    # 'same' ou 'fr'
    limit: int = 100,                       # Limite résultats
    offset: int = 0,                        # Pagination
    api_key: str = None                     # Clé API DeepL
) -> dict:
```

---

## Format de sortie

```json
{
    "auteur": "cx",
    "mode_detection": "traditionnel",
    
    "lang": "ja",
    "lang_detectee": "ja",
    "response_lang": "ja",
    "question_originale": "歯軋り",
    "question_traduite": "bruxisme",
    "traduction_provider": "deepl",
    
    "nb_patients": 42,
    "nb_returned": 20,
    "patients": [
        {
            "id": 123,
            "oriprenom": "Céline",
            "orinom": "Bègue",
            "age": 32,
            "sexe": "F",
            "oripathologies": "歯軋り, 開咬",
            "unit_year": "歳"
        }
    ],
    
    "description_filtres": "歯軋り",
    "description_filtres_fr": "bruxisme",
    "message": "42 患者 見つかりました 条件 歯軋り",
    
    "criteres_detectes": [...],
    "residu": "",
    "listcount": "LIST",
    
    "temps_ms": 125,
    "temps_detection_ms": 15,
    "temps_sql_ms": 8,
    
    "unit_year": "歳",
    "erreur": null
}
```

---

## Flux de traitement

### Étape 1 : Détection de langue
```python
if lang is None or lang.lower() == 'auto':
    lang = detecter_langue(question, deepl_key, verbose)
```

### Étape 2 : Traduction question → français
```python
if lang != 'fr':
    question_fr, provider = traduire(question, lang, 'fr', deepl_key, verbose)
```

### Étape 3 : Chargement des références
```python
mapping_patho = charger_pathologies_multilingues(pathoori_path)
messages = charger_messages_multilingues(messages_path)
```

### Étape 4 : Appel trouve.py
```python
if mode_detection == 'mix':
    resultats = rechercher_mix(question_fr, base_path, ...)
elif mode_detection == 'union':
    resultats = rechercher_union(question_fr, base_path, ...)
else:
    resultats = rechercher(question_fr, base_path, mode=mode_detection, ...)
```

### Étape 5 : Traduction des pathologies patients
```python
for patient in resultats['patients']:
    patient['oripathologies'] = traduire_pathologies_patient(
        patient['oripathologies'], mapping_patho, output_lang
    )
    patient['unit_year'] = get_unit_year(messages, output_lang)
```

### Étape 6 : Traduction description filtres
```python
description_filtres = traduire_description_filtres(
    description_fr, mapping_patho, output_lang
)
```

### Étape 7 : Génération message traduit
```python
message = get_message(messages, usage, output_lang, nb_patients, description)
```

### Étape 8 : Auto-retry si 0 résultats
Si 0 résultats avec langue imposée → relancer en Auto.

---

## Fonctions auxiliaires

### `charger_pathologies_multilingues(pathoori_path)`
- Charge pathoori.csv
- Clé = colonne 'standard' (normalisé)
- Indexe aussi par chaque synonyme

### `charger_messages_multilingues(messages_path)`
- Charge messages.csv
- Clé = colonne 'usage'

### `traduire_pathologie(patho_fr, mapping, lang)`
- Lookup dans mapping (pas d'API)
- Prend uniquement le premier terme (split sur virgule)

### `traduire_description_filtres(description, mapping, lang)`
- Sépare par ' + ' et ', '
- Traduit chaque terme individuellement

### `get_unit_year(messages, lang)`
- Retourne l'unité d'âge traduite
- Fallback hardcodé si pas dans messages.csv

### `_construire_description_filtres(resultats)`
- Construit description depuis criteres_detectes
- Format : "tag1, tag2 + age + sexe"

---

## Usage CLI

```bash
# Mode unitaire
python search.py base.db "bruxisme" --lang=fr
python search.py base.db "歯軋り" --lang=ja --mode=ia
python search.py base.db "bruxism women under 30" --lang=en --mode=union

# Mode batch
python search.py base.db tests.csv --verbose
```

---

## Usage en import

```python
from search import search

resultat = search(
    question="歯軋り",
    base_path="bases/base25000.db",
    lang="auto",
    mode_detection="traditionnel"
)

print(f"Trouvé: {resultat['nb_patients']} patients")
print(f"Auteur: {resultat['auteur']}")
```

---

## Logs

Fichier : `c:\g\logs\logrecherche.csv`

Colonnes : module, timestamp, temps_ms, languesaisie, langueutilisee, modulelangue, questionoriginale, question, filtres, sql, tri, base, mode, nb_patients, pathologies, ages, residu, erreur

---

## Alias pour compatibilité

```python
sucher = search
suche = search
```

---

## Notes importantes

1. **Lookup seulement** : Les pathologies sont traduites par lookup glossaire, pas d'API. C'est rapide.

2. **Premier terme** : Si une traduction contient des virgules (synonymes), prendre uniquement le premier.

3. **unit_year** : Toujours ajouter aux patients, même si pas de traduction (fallback "ans").

4. **Auto-retry** : Si langue imposée donne 0 résultats, relancer en Auto et ajouter `retry_info`.

5. **Mode mix** : Retourne les résultats du mode traditionnel avec `mix_comparison` ajouté.

6. **Mode union** : Retourne les résultats fusionnés avec `fusion` et `resultats_sources`.
