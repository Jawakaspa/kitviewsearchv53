# Prompt - Améliorations search.py et commun.csv

## Nom de conversation : search_v2

---

## Contexte

La chaîne de recherche `search.py → trouve.py` fonctionne avec les modes :
- `rapide` : detall.py (regex, ~20ms)
- `ia` : detia.py via Eden AI (~4s)
- `compare` : compare rapide vs IA
- `union` : fusionne les résultats

**Problèmes identifiés** :
1. Les modes `compare` et `union` ne font rien côté affichage CLI
2. Les options `--mode=` et `--lang=` sont obligatoires alors que les valeurs sont distinctes
3. Pas de choix du modèle IA en CLI
4. Liste des langues hardcodée dans `server.py`

---

## Tâche 1 : Enrichir commun.csv

Ajouter des colonnes pour les modèles IA et les langues.

### Structure actuelle

```csv
combien;devant;langues;languescibles;ecartlang;seuillang;incompatibles
combien;sévère;fr;fr;2;5;gauche,droit,droite
```

### Structure cible

Ajouter les colonnes `modele_court`, `modele_via`, `modele_complet` :

```csv
combien;devant;langues;languescibles;ecartlang;seuillang;incompatibles;modele_court;modele_via;modele_complet
combien;sévère;fr;fr;2;5;gauche,droit,droite;sonnet;edenai;anthropic/claude-3-7-sonnet-20250219
denombre;;en;en;;;maxillaire,mandibulaire;opus;edenai;anthropic/claude-3-opus-20240229
compte;;ja;ja;;;sévère,modéré...;haiku;edenai;anthropic/claude-3-5-haiku-20241022
...;;;de;;;...;gpt4o;edenai;openai/gpt-4o
...;;;es;;;...;gpt4omini;edenai;openai/gpt-4o-mini
...;;;it;;;...;gemini15pro;edenai;google/gemini-1.5-pro
...;;;ja;;;...;gemini15flash;edenai;google/gemini-1.5-flash
...;;;pt;;;...;gemini25flash;edenai;google/gemini-2.5-flash
```

**Règle** : Les colonnes modele_* peuvent être vides sur certaines lignes (données indépendantes).

---

## Tâche 2 : Simplifier les arguments CLI de search.py

### Comportement actuel
```bash
python search.py base.db "question" --mode=ia --lang=ja
```

### Comportement cible
```bash
# Les mots-clés sont détectés automatiquement (pas d'ambiguïté)
python search.py base.db "question" ia ja
python search.py base.db "question" ja ia
python search.py base.db "question" compare
python search.py base.db "question" union sonnet
python search.py base.db "question" gpt4o en
```

**Logique de détection** :
- Si le mot est dans la colonne `langues` de commun.csv → c'est une langue
- Si le mot est dans la colonne `modele_court` de commun.csv → c'est un modèle
- Si le mot est `rapide`, `ia`, `compare`, `union` → c'est un mode
- Les options longues `--mode=`, `--lang=`, `--model=` restent supportées

---

## Tâche 3 : Ajouter le choix du modèle IA

### En CLI
```bash
python search.py base.db "question" ia sonnet      # Sonnet (défaut)
python search.py base.db "question" ia gpt4o       # GPT-4o
python search.py base.db "question" ia gemini25flash
```

### En import
```python
from search import search
resultat = search("question", db_path, mode="ia", model="gpt4o")
```

### Fonction charger_modeles()
Ajouter dans search.py :
```python
def charger_modeles(commun_path: str) -> dict:
    """
    Charge les modèles IA depuis commun.csv.
    
    Returns:
        dict: {nom_court: {"via": "edenai", "complet": "anthropic/..."}}
    """
```

---

## Tâche 4 : Corriger l'affichage des modes compare/union en CLI

### Mode compare
Afficher les différences entre rapide et IA :
```
══════════════════════════════════════════════════════════════════════
COMPARAISON rapide vs IA
══════════════════════════════════════════════════════════════════════
Mode rapide : 26 patients (21ms)
Mode IA     : 26 patients (4200ms)

Communs           : 26
Uniquement rapide : 0
Uniquement IA     : 0

Concordance : 100%
══════════════════════════════════════════════════════════════════════
```

### Mode union
Afficher la provenance des résultats :
```
══════════════════════════════════════════════════════════════════════
UNION rapide + IA
══════════════════════════════════════════════════════════════════════
Total     : 28 patients
Rapide    : 26
IA        : 27
Communs   : 25
Ajoutés   : +1 (rapide seul) +2 (IA seul)
══════════════════════════════════════════════════════════════════════
```

---

## Tâche 5 : server.py utilise commun.csv pour les langues

### Comportement actuel
```python
LANGUES_NATIVES = ['fr', 'en', 'de', 'es', 'it', 'pt', 'pl', 'ro', 'th', 'ar', 'cn', 'ja']
```

### Comportement cible
```python
def charger_langues_natives(commun_path: str) -> list:
    """Charge les langues depuis la colonne 'langues' de commun.csv."""
    ...

# Au démarrage
LANGUES_NATIVES = charger_langues_natives(REFS_DIR / "commun.csv")
```

---

## Fichiers à modifier

| Fichier | Modifications |
|---------|---------------|
| `commun.csv` | Ajouter colonnes modele_court, modele_via, modele_complet |
| `search.py` | Arguments flexibles, choix modèle, affichage compare/union |
| `server.py` | Lire langues depuis commun.csv |
| `trouve.py` | Passer le modèle à detia.py |
| `detia.py` | Accepter paramètre model |

---

## Fichiers PJ nécessaires

- `commun.csv` (structure actuelle)
- `search.py` (version actuelle)
- `server.py` (version actuelle)
- `trouve.py` (version actuelle)
- `detia.py` (version actuelle)
- `Prompt_contexte0412.md`

---

## Tests de validation

```bash
# Syntaxe simplifiée
python search.py base100.db "bruxisme" ia
python search.py base100.db "bruxisme" ja
python search.py base100.db "bruxisme" ia gpt4o ja

# Modes compare et union avec affichage
python search.py base100.db "bruxisme" compare
python search.py base100.db "bruxisme" union

# Choix du modèle
python search.py base100.db "bruxisme" ia sonnet
python search.py base100.db "bruxisme" ia gpt4o
python search.py base100.db "bruxisme" ia gemini25flash
```

---

**FIN DU PROMPT**
