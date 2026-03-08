# Prompt_detangles.md

## Objet

Création du programme `detangles.py` pour la détection des angles céphalométriques (ANB, SNA, SNB) dans une question en langage naturel et leur conversion en tags orthodontiques qualifiés.

---

## Contexte

### Position dans la chaîne de détection

```
detall.py
  ├── detcount.py      → LIST/COUNT
  ├── detangles.py     → Angles céphalo → tags qualifiés ◄ CE MODULE
  ├── detquals.py      → Tags + adjectifs (complète les tags)
  └── detage.py        → Âge/sexe
```

`detangles.py` est appelé **avant** `detquals.py` car :
1. Les angles céphalo sont logiquement des tags (pathologies/caractéristiques)
2. Ils doivent être détectés en priorité avec leurs patterns spécifiques
3. Les résultats alimentent la même structure de tags que `detquals.py`

### Objectif fonctionnel

Transformer des expressions comme :
- `"ANB > 4°"` → Tag: "Classe II squelettique"
- `"SNA < 80°"` → Tag: "Rétrognathisme maxillaire"
- `"ANB entre 2 et 4 degrés"` → Tag: "Classe I squelettique" + Adjectif: "normal"

---

## Rappel orthodontique : Les angles céphalométriques

### Angle ANB (relation maxillo-mandibulaire)

| Condition | Interprétation | Tag canonique |
|-----------|----------------|---------------|
| ANB = 0° | Classe I idéale | Classe I squelettique |
| ANB entre 0° et 4° | Classe I normale | Classe I squelettique |
| ANB > 4° | Classe II | Classe II squelettique |
| ANB < 0° | Classe III | Classe III squelettique |

### Angle SNA (position du maxillaire)

| Condition | Interprétation | Tag canonique |
|-----------|----------------|---------------|
| SNA entre 80° et 84° | Normal | Position maxillaire normale |
| SNA > 84° | Prognathisme maxillaire | Prognathisme maxillaire |
| SNA < 80° | Rétrognathisme maxillaire | Rétrognathisme maxillaire |

### Angle SNB (position de la mandibule)

| Condition | Interprétation | Tag canonique |
|-----------|----------------|---------------|
| SNB entre 78° et 82° | Normal | Position mandibulaire normale |
| SNB > 82° | Prognathisme mandibulaire | Prognathisme mandibulaire |
| SNB < 78° | Rétrognathisme mandibulaire | Rétrognathisme mandibulaire |

---

## Structure du fichier de référence : angles.csv

### Format CSV

```
# angles.csv V1.0.0 - [DATE]
# Fichier de référence pour la détection des angles céphalométriques
# Format : expression;operateur;valeur_sql;tag_canonique;adjectifs_possibles;label
expression;operateur;valeur_sql;tag_canonique;adjectifs_possibles;label
```

### Description des colonnes

| Colonne | Description | Exemple |
|---------|-------------|---------|
| `expression` | Pattern(s) à détecter, séparés par `\|` | `anb > {n}°\|anb superieur a {n}\|anb plus de {n}` |
| `operateur` | Opérateur de comparaison pour la valeur | `>`, `<`, `>=`, `<=`, `=`, `BETWEEN` |
| `valeur_sql` | Seuil(s) de déclenchement | `4` ou `BETWEEN 0 AND 4` ou `{1}` |
| `tag_canonique` | Tag orthodontique résultant | `Classe II squelettique` |
| `adjectifs_possibles` | Adjectifs optionnels associés, séparés par `,` | `division 1,division 2,sévère` |
| `label` | Libellé affiché à l'utilisateur | `Classe II squelettique` |

### Placeholders

- `{n}` : Capture une valeur numérique (entière ou décimale)
- `{1}`, `{2}` : Références aux valeurs capturées dans `valeur_sql`

### Exemple de contenu angles.csv

```csv
# angles.csv V1.0.0 - 11/12/2025
# Détection des angles céphalométriques orthodontiques
expression;operateur;valeur_sql;tag_canonique;adjectifs_possibles;label
# ═══════════════════════════════════════════════════════════════════════════════
# ANGLE ANB - Relation maxillo-mandibulaire
# ═══════════════════════════════════════════════════════════════════════════════
# Classe I squelettique (ANB entre 0 et 4°)
anb = {n}|anb={n}|anb ={n}|anb= {n}|anb de {n}|anb a {n};BETWEEN;BETWEEN 0 AND 4;Classe I squelettique;idéale,parfaite,harmonieuse,normale;Classe I squelettique
anb entre {n} et {n}|anb de {n} a {n}|anb {n} a {n}|anb {n}/{n};BETWEEN;BETWEEN {1} AND {2};Classe I squelettique;normale;Classe I squelettique (ANB entre {n} et {n}°)
classe 1 squelettique|classe i squelettique|classe un squelettique;;;Classe I squelettique;idéale,parfaite,harmonieuse,normale;Classe I squelettique
# Classe II squelettique (ANB > 4°)
anb > {n}|anb>{n}|anb >{n}|anb> {n}|anb superieur a {n}|anb plus de {n}|anb au dessus de {n}|anb au dela de {n};>;4;Classe II squelettique;division 1,division 2,div 1,div 2,sévère;Classe II squelettique
classe 2 squelettique|classe ii squelettique|classe deux squelettique;;;Classe II squelettique;division 1,division 2,div 1,div 2,sévère;Classe II squelettique
# Classe III squelettique (ANB < 0°)
anb < {n}|anb<{n}|anb <{n}|anb< {n}|anb inferieur a {n}|anb moins de {n}|anb en dessous de {n}|anb negatif;<;0;Classe III squelettique;sévère,vraie,fausse;Classe III squelettique
classe 3 squelettique|classe iii squelettique|classe trois squelettique;;;Classe III squelettique;sévère,vraie,fausse;Classe III squelettique
# ═══════════════════════════════════════════════════════════════════════════════
# ANGLE SNA - Position du maxillaire par rapport à la base du crâne
# ═══════════════════════════════════════════════════════════════════════════════
# Position maxillaire normale (SNA entre 80 et 84°)
sna entre {n} et {n}|sna de {n} a {n}|sna {n}/{n};BETWEEN;BETWEEN 80 AND 84;Position maxillaire normale;;Position maxillaire normale
sna = {n}|sna={n}|sna de {n};BETWEEN;BETWEEN 80 AND 84;Position maxillaire normale;;Position maxillaire normale
# Prognathisme maxillaire (SNA > 84°)
sna > {n}|sna>{n}|sna superieur a {n}|sna plus de {n}|sna au dessus de {n};>;84;Prognathisme maxillaire;sévère,modéré,léger;Prognathisme maxillaire
prognathisme maxillaire|prognathe maxillaire|maxillaire prognathe|maxillaire en avant;;;Prognathisme maxillaire;sévère,modéré,léger;Prognathisme maxillaire
# Rétrognathisme maxillaire (SNA < 80°)
sna < {n}|sna<{n}|sna inferieur a {n}|sna moins de {n}|sna en dessous de {n};<;80;Rétrognathisme maxillaire;sévère,modéré,léger;Rétrognathisme maxillaire
retrognathisme maxillaire|retrognathe maxillaire|maxillaire retrognathe|maxillaire en arriere;;;Rétrognathisme maxillaire;sévère,modéré,léger;Rétrognathisme maxillaire
# ═══════════════════════════════════════════════════════════════════════════════
# ANGLE SNB - Position de la mandibule par rapport à la base du crâne
# ═══════════════════════════════════════════════════════════════════════════════
# Position mandibulaire normale (SNB entre 78 et 82°)
snb entre {n} et {n}|snb de {n} a {n}|snb {n}/{n};BETWEEN;BETWEEN 78 AND 82;Position mandibulaire normale;;Position mandibulaire normale
snb = {n}|snb={n}|snb de {n};BETWEEN;BETWEEN 78 AND 82;Position mandibulaire normale;;Position mandibulaire normale
# Prognathisme mandibulaire (SNB > 82°)
snb > {n}|snb>{n}|snb superieur a {n}|snb plus de {n};>;82;Prognathisme mandibulaire;sévère,modéré,léger;Prognathisme mandibulaire
prognathisme mandibulaire|prognathe mandibulaire|mandibule prognathe|mandibule en avant;;;Prognathisme mandibulaire;sévère,modéré,léger;Prognathisme mandibulaire
# Rétrognathisme mandibulaire (SNB < 78°)
snb < {n}|snb<{n}|snb inferieur a {n}|snb moins de {n};<;78;Rétrognathisme mandibulaire;sévère,modéré,léger;Rétrognathisme mandibulaire
retrognathisme mandibulaire|retrognathe mandibulaire|mandibule retrognathe|mandibule en arriere;;;Rétrognathisme mandibulaire;sévère,modéré,léger;Rétrognathisme mandibulaire
# ═══════════════════════════════════════════════════════════════════════════════
# VARIANTES D'UNITÉS (°, degré, degrés, rien)
# ═══════════════════════════════════════════════════════════════════════════════
# Note : Les patterns ci-dessus sont en version standardisée (sans °)
# La standardisation transforme "°" en "" et "degrés/degré" en ""
# Donc "ANB > 4°" devient "anb > 4" après standardisation
```

### Règles de construction des patterns

1. **Expressions standardisées** : Les patterns sont écrits en minuscules, sans accents, sans symbole `°`
2. **Alternatives** : Séparées par `|` dans la même cellule
3. **Espaces optionnels** : Gérer `anb>4`, `anb > 4`, `anb> 4`, `anb >4`
4. **Unités** : Le symbole `°` et les mots "degré(s)" sont supprimés lors de la standardisation
5. **Valeurs décimales** : `{n}` capture aussi `3.5`, `2,5`

---

## Nouveau format JSON unifié de sortie

### Structure de sortie de detecter_angles()

```json
{
  "criteres": [
    {
      "type": "tag",
      "detecte": "anb > 4",
      "canonique": "classe ii squelettique",
      "label": "Classe II squelettique",
      "sql": {
        "colonne": "pathologie",
        "operateur": "=",
        "valeur": "classe ii squelettique"
      },
      "adjectifs_possibles": ["division 1", "division 2", "sévère"],
      "position": {
        "debut": 39,
        "fin": 47
      }
    }
  ],
  "residu": "je voudrais les patients avec un angle"
}
```

### Champs du critère

| Champ | Obligatoire | Description |
|-------|-------------|-------------|
| `type` | ✅ | Toujours `"tag"` (les angles produisent des tags) |
| `detecte` | ✅ | Texte exact détecté dans la question standardisée |
| `canonique` | ✅ | Forme canonique du tag (standardisée) |
| `label` | ✅ | Libellé lisible pour l'utilisateur |
| `sql` | ✅ | Conditions SQL pour la recherche |
| `adjectifs_possibles` | ❌ | Liste des adjectifs applicables à ce tag |
| `position` | ❌ | Position dans la question (utile pour debug) |

---

## Programme detangles.py

### Signature des fonctions principales

```python
def charger_patterns_angles(fichier_csv, verbose=False, debug=False) -> list:
    """
    Charge les patterns d'angles depuis angles.csv
    
    Returns:
        Liste de dicts triés par nb_mots décroissant
    """

def detecter_angles(question, patterns_angles, verbose=False, debug=False) -> dict:
    """
    Détecte les angles céphalométriques dans une question.
    
    Returns:
        {
            'criteres': [...],  # Liste de critères de type 'tag'
            'residu': str       # Texte restant
        }
    """

def identifier_angles(residu, patterns_angles, filtres, verbose=False, debug=False):
    """
    Wrapper de compatibilité avec signature standard.
    
    Returns:
        Tuple (filtres, residu)
    """
```

### Logique de détection

1. **Standardiser** la question (minuscules, sans accents, `°` supprimé)
2. **Trier** les patterns par nombre de mots décroissant (longest match first)
3. **Pour chaque pattern** :
   - Construire la regex depuis l'expression
   - Chercher un match dans la question
   - Si match ET valeur capturée correspond à la condition (operateur + valeur_sql) :
     - Créer le critère avec le tag_canonique
     - Marquer les mots comme utilisés
4. **Retourner** les critères et le résidu

### Gestion des conditions numériques

Pour les patterns avec `{n}` :
- Capturer la valeur numérique
- Évaluer la condition : `valeur_capturee OPERATEUR seuil`
- Exemple : `anb > 4` avec valeur capturée `5` → condition `5 > 4` vraie → match

```python
def evaluer_condition(valeur_capturee, operateur, seuil):
    """
    Évalue si la valeur capturée satisfait la condition.
    
    Args:
        valeur_capturee: Valeur numérique extraite de la question
        operateur: '>', '<', '>=', '<=', '=', 'BETWEEN'
        seuil: Valeur(s) de référence
    
    Returns:
        bool: True si la condition est satisfaite
    """
    if operateur == '>':
        return valeur_capturee > seuil
    elif operateur == '<':
        return valeur_capturee < seuil
    elif operateur == '>=':
        return valeur_capturee >= seuil
    elif operateur == '<=':
        return valeur_capturee <= seuil
    elif operateur == '=' or operateur == '':
        return seuil_min <= valeur_capturee <= seuil_max  # Pour plage implicite
    elif operateur == 'BETWEEN':
        return seuil[0] <= valeur_capturee <= seuil[1]
    return False
```

### Cas particulier : Patterns sans valeur numérique

Pour les patterns textuels comme `"classe 2 squelettique"` :
- Pas de `{n}` dans l'expression
- Pas d'opérateur ni de valeur_sql
- Match direct sur le texte

---

## CLI

### Mode unitaire

```bash
python detangles.py "patients avec ANB > 4°" [--verbose] [--debug]
```

Sortie JSON :
```json
{
  "criteres": [
    {
      "type": "tag",
      "detecte": "anb > 4",
      "canonique": "classe ii squelettique",
      "label": "Classe II squelettique",
      "sql": {"colonne": "pathologie", "operateur": "=", "valeur": "classe ii squelettique"},
      "adjectifs_possibles": ["division 1", "division 2", "sévère"]
    }
  ],
  "residu": "patients avec"
}
```

### Mode batch

```bash
python detangles.py tests/testsanglesin.csv [--verbose] [--debug]
# Sortie : tests/testsanglesout.csv
```

---

## Intégration dans detall.py

### Ordre d'appel

```python
def detecter_tout(question, references, verbose=False, debug=False):
    # 1. detcount → listcount
    # 2. detangles → tags depuis angles céphalo (NOUVEAU)
    # 3. detquals → tags + adjectifs
    # 4. detage → âge/sexe
```

### Fusion des critères

Les critères de `detangles` sont de type `"tag"` et s'ajoutent à la liste des critères. `detquals` ne doit pas re-détecter les tags déjà trouvés par `detangles`.

---

## Fichiers de référence nécessaires

| Fichier | Description |
|---------|-------------|
| `refs/angles.csv` | Patterns des angles céphalométriques |

---

## Pièces jointes pour recréer le programme

1. `Prompt_contexte0412.md` — Contexte général du projet
2. `Prompt_detangles.md` — Ce document
3. `detage.py` — Modèle de structure (logique regex similaire)
4. `ages.csv` — Modèle de format CSV

---

## Résumé des changements par rapport à l'existant

| Aspect | Ancien (dettags) | Nouveau (detangles) |
|--------|------------------|---------------------|
| Approche | Synonymes listés manuellement | Patterns regex avec `{n}` |
| Gestion des valeurs | `Anb=0°,Anb=1°,Anb=2°...` | `anb = {n}` + condition |
| Espaces | Chaque variante listée | Regex `\s*` automatique |
| Extensibilité | Difficile | Ajout de patterns simples |
| Position dans chaîne | Mélangé avec autres tags | Dédié, avant detquals |

---

**FIN DU DOCUMENT**
