# Prompt_detage_structure.md

## Objet

Documentation détaillée de la structure du fichier `ages.csv` et de la logique de `detage.py`, servant de **modèle de référence** pour créer d'autres modules de détection basés sur des patterns regex (comme `detangles.py`).

---

## Philosophie générale

### Principe fondamental

> **Rien en dur dans le code** — Toutes les données de détection sont dans des fichiers CSV externes.

Le programme `detage.py` est un **moteur de patterns** générique. Sa logique peut être répliquée pour d'autres types de détection (angles, mesures, etc.) en créant simplement un nouveau fichier CSV de référence.

### Architecture du pattern matching

```
┌─────────────────────────────────────────────────────────────────┐
│                        ages.csv                                  │
│  ┌─────────────┬──────────┬───────────┬──────┬─────────────┐   │
│  │ expression  │ operateur│ valeur_sql│ sexe │    label    │   │
│  ├─────────────┼──────────┼───────────┼──────┼─────────────┤   │
│  │moins de {n} │    <     │    {1}    │      │Moins de {n} │   │
│  │    ans      │          │           │      │    ans      │   │
│  └─────────────┴──────────┴───────────┴──────┴─────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       detage.py                                  │
│  1. Charge les patterns                                         │
│  2. Construit les regex depuis les expressions                  │
│  3. Trie par longueur (longest match first)                     │
│  4. Cherche les matches dans la question                        │
│  5. Capture les valeurs numériques {n}                          │
│  6. Construit les critères JSON                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Sortie JSON                                  │
│  {                                                              │
│    "type": "age",                                               │
│    "detecte": "moins de 39 ans",                                │
│    "label": "Moins de 39 ans",                                  │
│    "sql": {"colonne": "age", "operateur": "<", "valeur": 39}   │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## Structure du fichier ages.csv

### Format général

```csv
# ages.csv V1.0.0 - [DATE]
expression;operateur;valeur_sql;sexe;label
```

### Description des colonnes

| # | Colonne | Type | Description | Exemples |
|---|---------|------|-------------|----------|
| 1 | `expression` | string | Pattern(s) à détecter, séparés par `\|` | `moins de {n} ans\|avant {n} ans` |
| 2 | `operateur` | string | Opérateur SQL de comparaison | `<`, `>`, `<=`, `>=`, `=`, `BETWEEN`, `` |
| 3 | `valeur_sql` | string | Template de valeur(s) | `{1}`, `18`, `BETWEEN {1} AND {2}` |
| 4 | `sexe` | string | Filtre de sexe optionnel | `M`, `F`, `` (vide) |
| 5 | `label` | string | Libellé affiché à l'utilisateur | `Moins de {n} ans`, `Femme` |

### Syntaxe des expressions

#### Alternatives avec `|`

Plusieurs formulations pour le même concept :
```
moins de {n} ans|avant {n} ans|pas encore {n} ans|strictement moins de {n} ans
```

#### Placeholder `{n}` pour les valeurs numériques

Capture un nombre entier ou décimal :
```
{n} ans              → capture "39" dans "39 ans"
entre {n} et {n}     → capture "20" et "30" dans "entre 20 et 30"
environ {n} ans      → capture "25" dans "environ 25 ans"
```

#### Patterns sans `{n}` (textuels)

Détection directe sans valeur numérique :
```
femme|femmes         → détection textuelle directe
adolescent|ado       → détection textuelle directe
```

### Syntaxe de valeur_sql

| Format | Description | Exemple expression | Exemple valeur_sql |
|--------|-------------|-------------------|-------------------|
| `{1}` | Première valeur capturée | `moins de {n} ans` | `{1}` |
| `{2}` | Deuxième valeur capturée | `entre {n} et {n}` | utilisé dans BETWEEN |
| `BETWEEN {1} AND {2}` | Plage entre 2 valeurs | `de {n} a {n} ans` | `BETWEEN {1} AND {2}` |
| `BETWEEN {1}-2 AND {1}+2` | Plage calculée | `environ {n} ans` | `BETWEEN {1}-2 AND {1}+2` |
| `BETWEEN 12 AND 18` | Plage fixe | `adolescent` | `BETWEEN 12 AND 18` |
| `18` | Valeur fixe | `adulte` | `18` |

### Exemple complet commenté

```csv
# ═══════════════════════════════════════════════════════════════════
# CATÉGORIE : Comparaisons simples avec valeur variable
# ═══════════════════════════════════════════════════════════════════
# Pattern avec opérateur < et valeur capturée
avant {n} ans|moins de {n} ans|pas encore {n} ans;<;{1};;Moins de {n} ans

# Pattern avec opérateur >= et valeur capturée  
{n} ans minimum|{n} ans au moins|a partir de {n} ans;>=;{1};;Au moins {n} ans

# ═══════════════════════════════════════════════════════════════════
# CATÉGORIE : Plages avec deux valeurs capturées
# ═══════════════════════════════════════════════════════════════════
# BETWEEN avec deux valeurs distinctes
de {n} a {n} ans|entre {n} et {n} ans|{n}/{n} ans;BETWEEN;BETWEEN {1} AND {2};;Entre {n} et {n} ans

# ═══════════════════════════════════════════════════════════════════
# CATÉGORIE : Plages calculées (approximations)
# ═══════════════════════════════════════════════════════════════════
# "environ 30 ans" → BETWEEN 28 AND 32 (±2)
environ {n} ans;BETWEEN;BETWEEN {1}-2 AND {1}+2;;Environ {n} ans

# "autour de 30 ans" → BETWEEN 27 AND 33 (±3)
autour de {n} ans;BETWEEN;BETWEEN {1}-3 AND {1}+3;;Autour de {n} ans

# ═══════════════════════════════════════════════════════════════════
# CATÉGORIE : Plages fixes (catégories prédéfinies)
# ═══════════════════════════════════════════════════════════════════
# Catégories d'âge sans valeur dans la question
adolescent|adolescents|ado|ados;BETWEEN;BETWEEN 12 AND 18;;Adolescent
adulte|adultes|majeur|majeurs;>=;18;;Adulte
enfant|enfants|gosse|gosses;<;12;;Enfant
senior|seniors|boomer|boomers;>=;65;;Sénior

# ═══════════════════════════════════════════════════════════════════
# CATÉGORIE : Sexe (avec ou sans condition d'âge)
# ═══════════════════════════════════════════════════════════════════
# Sexe seul (pas d'opérateur, pas de valeur)
femme|femmes;>=;18;F;Femme
homme|hommes;>=;18;M;Homme

# Sexe seul sans condition d'âge
de sexe feminin|f;;;F;Féminin
de sexe masculin|m|h;;;M;Masculin

# Combinaisons sexe + catégorie
adolescente|adolescentes;BETWEEN;BETWEEN 12 AND 18;F;Adolescente
etudiante|etudiantes;BETWEEN;BETWEEN 18 AND 25;F;Étudiante
```

---

## Algorithme de transformation expression → regex

### Étapes de construction

```python
def _build_age_regex(expression):
    """
    Transforme une expression du CSV en regex.
    
    Exemple:
        "moins de {n} ans" → r"moins\s+de\s+(\d+)\s+ans"
    """
    # 1. Standardiser (minuscules, sans accents)
    expr_norm = standardise(expression)
    
    # 2. Échapper les caractères spéciaux SAUF |
    result = []
    for char in expr_norm:
        if char == '|':
            result.append('|')  # Conservé pour alternatives
        elif char in r'\^$.*+?{}[]()':
            result.append('\\' + char)
        else:
            result.append(char)
    pattern = ''.join(result)
    
    # 3. Remplacer \{n\} par groupe capturant
    pattern = re.sub(r'\\{n\\}', r'(\d+)', pattern)
    
    # 4. Remplacer espaces par \s+ (espaces flexibles)
    pattern = pattern.replace(" ", r"\s+")
    
    return pattern
```

### Exemples de transformations

| Expression CSV | Regex générée |
|----------------|---------------|
| `moins de {n} ans` | `moins\s+de\s+(\d+)\s+ans` |
| `{n}/{n} ans` | `(\d+)/(\d+)\s+ans` |
| `femme\|femmes` | `femme\|femmes` |
| `environ {n} ans` | `environ\s+(\d+)\s+ans` |

---

## Algorithme de détection

### Pseudo-code

```
FONCTION detecter_ages(question, patterns):
    question_norm ← standardise(question)
    mots_question ← question_norm.split()
    mots_utilises ← ensemble vide
    criteres ← liste vide
    
    # Trier patterns par longueur décroissante (longest first)
    tous_patterns ← collecter et trier tous les patterns
    
    POUR CHAQUE pattern DANS tous_patterns:
        SI pattern.ligne déjà matchée:
            CONTINUER
        
        regex ← construire_regex(pattern.expression)
        match ← chercher(regex, question_norm)
        
        SI match:
            SI mots du match déjà utilisés:
                CONTINUER
            
            valeurs_capturees ← extraire_nombres(match)
            label ← remplacer_placeholders(pattern.label, valeurs_capturees)
            criteres_nouveaux ← construire_criteres(pattern, valeurs_capturees)
            
            criteres.ajouter(criteres_nouveaux)
            marquer_mots_utilises(match)
            marquer_ligne_matchee(pattern.ligne)
    
    residu ← mots non utilisés
    RETOURNER {criteres, residu}
```

### Règles de priorité

1. **Longest match first** : Les patterns avec plus de mots sont testés en premier
2. **Une ligne = un match** : Une fois qu'une ligne du CSV a matché, ses autres alternatives ne sont plus testées
3. **Mots non réutilisables** : Un mot consommé par un pattern ne peut pas être réutilisé

---

## Construction des critères de sortie

### Pour detage.py (critères séparés sexe/âge)

Une ligne du CSV peut générer **plusieurs critères** :

```csv
femme;>=;18;F;Femme
```

Génère :
```json
[
  {
    "type": "sexe",
    "detecte": "femme",
    "label": "Femme",
    "sql": {"colonne": "sexe", "operateur": "=", "valeur": "F"}
  },
  {
    "type": "age",
    "detecte": "femme",
    "label": "Femme",
    "sql": {"colonne": "age", "operateur": ">=", "valeur": 18}
  }
]
```

### Remplacement des placeholders dans le label

```python
def _construire_label_final(label_template, valeurs_capturees):
    """
    "Moins de {n} ans" + [39] → "Moins de 39 ans"
    "Entre {n} et {n} ans" + [20, 30] → "Entre 20 et 30 ans"
    """
    label = label_template
    for val in valeurs_capturees:
        label = label.replace('{n}', str(val), 1)  # Une substitution à la fois
    return label
```

---

## Adaptation pour d'autres modules

### Modèle générique

Pour créer un nouveau module de détection (ex: `detangles.py`), il suffit de :

1. **Créer le fichier CSV** avec la même structure (ou adaptée)
2. **Copier/adapter les fonctions** :
   - `charger_patterns_XXX()` — Chargement du CSV
   - `_build_XXX_regex()` — Construction des regex
   - `detecter_XXX()` — Logique de détection
   - `identifier_XXX()` — Wrapper de compatibilité

### Différences possibles selon le module

| Module | Colonnes spécifiques | Type de critère |
|--------|---------------------|-----------------|
| detage | `sexe` | `"age"`, `"sexe"` |
| detangles | `tag_canonique`, `adjectifs_possibles` | `"tag"` |
| detmesures | `unite`, `precision` | `"mesure"` |

---

## Bonnes pratiques pour les fichiers CSV

### Organisation

1. **Commentaires de section** avec `#` et lignes de séparation visuelles
2. **Groupement logique** des patterns similaires
3. **Patterns les plus spécifiques en premier** dans la colonne expression

### Gestion des variantes

```csv
# BON : Toutes les variantes dans une seule ligne
moins de {n} ans|avant {n} ans|pas encore {n} ans;<;{1};;Moins de {n} ans

# MAUVAIS : Chaque variante sur une ligne séparée (plus difficile à maintenir)
moins de {n} ans;<;{1};;Moins de {n} ans
avant {n} ans;<;{1};;Moins de {n} ans
pas encore {n} ans;<;{1};;Moins de {n} ans
```

### Test des patterns

Créer un fichier de test `testsagesin.csv` :
```csv
# Tests pour ages.csv
question
moins de 39 ans
femme de 25 ans
entre 20 et 30 ans
adolescent avec bruxisme
environ 45 ans
```

---

## Pièces jointes nécessaires

Pour recréer `detage.py` à partir de zéro :

1. `Prompt_contexte0412.md` — Contexte général
2. `Prompt_detage_structure.md` — Ce document
3. `Prompt_detcount_detage_detall.md` — Spécifications du format JSON
4. `ages.csv` — Fichier de référence actuel

---

**FIN DU DOCUMENT**
