# Prompt conv_detia_plante V1.0.0 - 14/01/2026 20:42:02

# Synthèse de conversation : detia planté

## Informations générales
- **Date de début** : 14/01/2026 ~20:30
- **Projet** : KITVIEW - Application de recherche multilingue orthodontique
- **Fichiers concernés** : detia.py

---

## Échange 1 - 14/01/2026 ~20:30

### Question
Erreur à l'exécution de `detia.py "bruxisme"` :
```
NameError: name 'n' is not defined
```
L'erreur se produit ligne 419 dans la fonction `_construire_prompt_systeme`.

### Diagnostic
Le problème vient de la construction du prompt système (lignes 377-456) qui utilise une **f-string** (`f"""..."""`).

Dans cette f-string, les expressions `{n}` aux lignes 419-422 sont interprétées par Python comme des substitutions de variables, alors qu'elles devraient être du texte littéral destiné à l'IA.

**Lignes problématiques** :
```python
- "{n} ans", "de {n} ans", "âgé de {n} ans" → âge EXACT, operateur "="
- "moins de {n} ans", "de moins de {n} ans" → operateur "<"
- "plus de {n} ans", "de plus de {n} ans" → operateur ">"
- "entre {n} et {n} ans" → operateur "BETWEEN" avec valeur et valeur2
```

### Solution
Dans une f-string Python, pour avoir des accolades littérales, il faut les **doubler** : `{{n}}` produit le texte `{n}`.

**Lignes corrigées** :
```python
- "{{n}} ans", "de {{n}} ans", "âgé de {{n}} ans" → âge EXACT, operateur "="
- "moins de {{n}} ans", "de moins de {{n}} ans" → operateur "<"
- "plus de {{n}} ans", "de plus de {{n}} ans" → operateur ">"
- "entre {{n}} et {{n}} ans" → operateur "BETWEEN" avec valeur et valeur2
```

### Livrable
- `detia.py` corrigé (4 lignes modifiées : 419, 420, 421, 422)

---

## Prompt de recréation

Pour recréer `detia.py` avec cette correction :

**Contexte** : Le fichier detia.py contient une f-string multi-lignes dans la fonction `_construire_prompt_systeme()`. Cette f-string construit un prompt pour l'IA avec des exemples de syntaxe d'âge utilisant `{n}` comme placeholder.

**Action** : Dans la fonction `_construire_prompt_systeme()`, remplacer toutes les occurrences de `{n}` par `{{n}}` dans les lignes décrivant les règles d'âge (section "=== CRITÈRES D'ÂGE ET SEXE ===").

**Fichiers PJ nécessaires** :
- detia.py (version actuelle à corriger)
- ages.csv (référence)
- angles.csv (référence)
- Prompt_contexte1301.md (contexte projet)

---

## Résumé des modifications

| Fichier | Action | Lignes |
|---------|--------|--------|
| detia.py | Correction f-string `{n}` → `{{n}}` | 419, 420, 421, 422 |

---

*Document généré le 14/01/2026*
