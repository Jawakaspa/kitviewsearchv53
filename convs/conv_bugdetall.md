# Prompt conv_bugdetall V1.0.2 - 07/01/2026 13:54:47

# Synthèse de conversation : bugdetall

## Informations
- **Date de création** : 07/01/2026
- **Projet** : KITVIEW - Application de recherche orthodontique multilingue

---

## Échanges

### 07/01/2026 - Signalement du bug

**Question utilisateur :**
Bug identifié : la recherche "Patient avec béance antérieure et classe II" retourne 0 résultat, alors que "Patient avec béance et classe II" retourne 98 résultats. Parmi ces 98 résultats, on trouve Amina Cissé avec "béance antérieure droite sévère" - preuve que des patients avec "béance antérieure" existent bien en base.

**Analyse préliminaire :**
- Le parcours de détection montre `standard:0→ia:0` pour "béance antérieure"
- Le parcours montre `standard:98` pour "béance" seule
- Le problème est dans la détection de l'expression composée "béance + qualificatif"
- Le module detall.py (détection algorithmique) échoue à reconnaître "béance antérieure"

**Fichiers reçus et analysés :**
- detall.py V1.0.7 - orchestrateur de détection
- dettags.py V1.0.13 - détection des tags orthodontiques
- detadjs.py V1.0.9 - détection des adjectifs qualifiant un tag
- tags.csv - contient bien "béance" avec adjectifs autorisés : antérieur, postérieur, latéral, gauche, droit, sévère, modéré
- adjectifs.csv - contient bien "antérieur" avec formes : antérieure, antérieurs, antérieures + patterns

**Diagnostic établi :**
Le bug n'est PAS dans la détection mais dans la **génération SQL** !

1. ✅ La détection fonctionne : "béance" est trouvé, "antérieure" est mappé vers "antérieur"
2. ❌ Le JSON génère deux critères séparés :
   - `canontags = "béance"`
   - `canonadjs = "antérieur"`
3. ❌ Mais dans la base, Amina Cissé a `béance antérieure droite sévère` comme **texte libre unique**
4. ❌ La colonne `canonadjs` n'existe probablement pas ou n'est pas peuplée

**Fichiers supplémentaires demandés :**
- search.py (ou cherche.py) - pour voir la construction SQL
- Structure de la base (base.txt ou schéma)

**Statut :** ✅ CORRIGÉ - 3 fichiers livrés

---

### 07/01/2026 - Explication du fallback IA qui échoue aussi

**Question utilisateur :** Pourquoi l'IA échoue aussi avec le parcours `standard:0→ia:0` ?

**Explication :** Le bug n'est pas dans la détection mais dans **jsonsql.py** qui est commun aux deux chemins :

```
detall.py (standard) ─┐
                      ├──► JSON ──► jsonsql.py ──► SQL ──► 0 résultat
detia.py (IA)     ────┘
```

L'IA détecte correctement "béance antérieure", mais produit un JSON avec `canonique: "antérieur"`. Ensuite `jsonsql.py` reconstruit "beance anterieur" au lieu de "beance anterieure".

**Tests confirmant le diagnostic :**
- "béance anterieur" → 0 résultat (base contient "anterieure")
- "beance anterieur" → 0 résultat (même raison)

---

## Fichiers corrigés livrés

### 1. detadjs.py V1.1.0
- NOUVEAU : Paramètre `genre_tag` pour accorder l'adjectif
- NOUVEAU : Champ `forme_accordee` dans le retour
- Fonction `_get_forme_accordee()` qui retourne la bonne forme selon le genre

### 2. dettags.py V1.1.0  
- Récupère le genre du tag (`gn`) depuis tags.csv
- Passe `genre_tag` à `detecter_adjectifs()`
- Inclut `forme_accordee` dans les adjectifs retournés
- Inclut `gn` dans le critère JSON

### 3. jsonsql.py V1.1.0
- `_construire_pathologie_complete()` utilise `forme_accordee` au lieu de `canonique`
- Priorité : `forme_accordee` > `canonique` > `valeur`

---

## Fichiers créés/modifiés
| Fichier | Action | Date |
|---------|--------|------|
| conv_bugdetall.md | Création + MAJ | 07/01/2026 |
| detadjs.py | Corrigé V1.1.0 | 07/01/2026 |
| dettags.py | Corrigé V1.1.0 | 07/01/2026 |
| jsonsql.py | Corrigé V1.1.0 | 07/01/2026 |

---

### 07/01/2026 - Nouveau double bug sur l'âge

**Requête test :** "Patientes de 14 ans présentant une malocclusion avec bruxisme"

**Bug 1 - Mode standard échoue (0 résultat) :**
- Parcours : `standard:0→ia:19`
- Le mode standard ne détecte pas "14 ans"
- Hypothèse : detage.py ne matche pas le pattern "de 14 ans"

**Bug 2 - Mode IA ignore l'âge :**
- Trouve 19 patientes mais la plupart n'ont PAS 14 ans (6, 11, 16, 12, 7, 17 ans...)
- Seule Sabine (14 ans) est correcte
- L'IA a ignoré la contrainte d'âge, ne filtrant que sur Femme + malocclusion + bruxisme

**Remarque utilisateur :** Pourquoi DeepL apparaît-il dans le header pour une question 100% française ?
- Le header affiche les capacités, pas l'utilisation réelle
- Le parcours `standard:0→ia:19` confirme que DeepL n'a pas été utilisé

**Fichiers demandés :** detage.py, ages.csv, detia.py

**Fichiers fournis :** ✅ Les 3 fichiers + jsonsql.py actuel

---

### 07/01/2026 - Analyse et correction des bugs d'âge

**Double bug identifié :**

#### Bug 1 - jsonsql.py incompatible avec detage.py pour BETWEEN
- detage.py retourne : `'sql': {'operateur': 'BETWEEN', 'valeur': [14, 15]}`
- jsonsql.py attend : `valeur: 14, valeur2: 15` (deux clés séparées)
- Résultat : SQL reçoit une liste au lieu d'un entier → 0 résultat

**Correction jsonsql.py V1.1.0 :**
```python
if operateur.upper() == 'BETWEEN':
    if isinstance(valeur, list) and len(valeur) >= 2:
        val1, val2 = valeur[0], valeur[1]  # Format detage.py
    else:
        val1 = valeur
        val2 = sql_info.get('valeur2', valeur)  # Format alternatif
    return f"p.age BETWEEN ? AND ?", [val1, val2]
```

#### Bug 2 - Le prompt IA n'explique pas les âges exacts
Le prompt (lignes 417-422) montre seulement :
```
- "moins de 30 ans" → age < 30
- "plus de 30 ans" → age > 30
```

Mais **PAS** d'exemple pour un âge exact comme "14 ans" ou "de 14 ans" !

**Correction detia.py :** Ajouter dans le prompt :
```
- "14 ans", "de 14 ans", "âgé de 14 ans" → age = 14 (âge EXACT)
- "entre 10 et 15 ans" → age BETWEEN 10 AND 15
```

---

## Fichiers livrés

| Fichier | Version | Action | Date |
|---------|---------|--------|------|
| jsonsql.py | V1.1.0 | FIX accord adjectifs + BETWEEN avec liste | 07/01/2026 |
| detadjs.py | V1.1.0 | Accord en genre des adjectifs | 07/01/2026 |
| dettags.py | V1.1.0 | Passe le genre à detadjs | 07/01/2026 |
| detia.py | V1.0.28 | FIX prompt IA pour âges exacts | 07/01/2026 |
| conv_bugdetall.md | - | Synthèse mise à jour | 07/01/2026 |

---

## Tests validés ✅

### Test 1 - Mode standard avec âge exact
```
python search.py base25000.db "Patientes de 14 ans avec malocclusion et bruxisme"
→ Résultat : 1 patiente (Sabine Navarro, F, 14 ans) ✅
```

---

## Prompt de recréation

### Pour recréer detadjs.py V1.1.0

**Prompt :**
```
Crée detadjs.py V1.1.0 - Module de détection des adjectifs qualifiant un tag orthodontique.

CHANGEMENT PRINCIPAL : Supporter l'accord en genre des adjectifs.

Fonctionnalités :
1. Nouveau paramètre `genre_tag` (m/f/mp/fp) dans detecter_adjectifs()
2. Nouvelle fonction `_get_forme_accordee(adjs_data, canon_adj, genre_tag)` qui retourne
   la forme accordée selon le genre (utilise colonnes m/f/mp/fp de adjectifs.csv)
3. Le retour inclut `forme_accordee` en plus de `canonique` et `detecte`

Structure du retour :
{
    "adjectifs": [
        {"detecte": "anterieure", "canonique": "antérieur", "forme_accordee": "antérieure", "standardise": "anterieure"}
    ],
    "mots_utilises": set()
}

Fichiers en PJ : adjectifs.csv, Prompt_contexte2312.md
```

### Pour recréer dettags.py V1.1.0

**Prompt :**
```
Crée dettags.py V1.1.0 - Module de détection des tags orthodontiques.

CHANGEMENT PRINCIPAL : Passer le genre du tag à detadjs pour l'accord des adjectifs.

Modifications :
1. Récupérer `gn` (genre) depuis tags.csv pour chaque tag
2. Passer `genre_tag=gn` à detecter_adjectifs()
3. Inclure `gn` et `forme_accordee` dans le critère JSON retourné

Le JSON de sortie doit inclure :
- critere['gn'] = genre du tag
- critere['adjectifs'][i]['forme_accordee'] = forme accordée

Fichiers en PJ : tags.csv, adjectifs.csv, detadjs.py, Prompt_contexte2312.md
```

### Pour recréer jsonsql.py V1.1.0

**Prompt :**
```
Crée jsonsql.py V1.1.0 - Module de génération SQL à partir du JSON de détection.

DEUX CHANGEMENTS PRINCIPAUX :

1. Utiliser forme_accordee des adjectifs pour construire la pathologie :
   - Priorité : forme_accordee > canonique > valeur
   - Avant : "béance" + "antérieur" → "beance anterieur" ❌
   - Après : "béance" + "antérieure" → "beance anterieure" ✅

2. Gérer BETWEEN quand valeur est une liste :
   - detage.py retourne : valeur = [14, 15]
   - jsonsql.py attendait : valeur = 14, valeur2 = 15
   - FIX : if isinstance(valeur, list): val1, val2 = valeur[0], valeur[1]

Fichiers en PJ : Prompt_contexte2312.md
```

### Pour corriger detia.py V1.0.28 (âges exacts)

**Modification appliquée dans detia.py :**

Localisation : fonction `_construire_prompt_systeme()`, vers ligne 417

Ancien code :
```python
=== CRITÈRES D'ÂGE ET SEXE ===
- "moins de 30 ans", "de moins de 30 ans" → age < 30
- "plus de 30 ans", "de plus de 30 ans" → age > 30
- "enfants" → age < 12
- "adultes" → age >= 18
- femme/fille/femmes → "F", homme/garçon/hommes → "M"
```

Nouveau code :
```python
=== CRITÈRES D'ÂGE ET SEXE ===
IMPORTANT - Règles pour l'âge :
- "{n} ans", "de {n} ans", "âgé de {n} ans" → âge EXACT, operateur "="
- "moins de {n} ans", "de moins de {n} ans" → operateur "<"
- "plus de {n} ans", "de plus de {n} ans" → operateur ">"
- "entre {n} et {n} ans" → operateur "BETWEEN" avec valeur et valeur2

Exemples :
- "14 ans" ou "de 14 ans" → {"type": "age", "detecte": "14 ans", "operateur": "=", "valeur": 14}
- "moins de 30 ans" → {"type": "age", "detecte": "moins de 30 ans", "operateur": "<", "valeur": 30}
- etc.

Sexe :
- femme/fille/femmes/patiente/patientes → "F"
- homme/garçon/hommes/patient/patients → "M"
```

---

### 07/01/2026 - Diagnostic confirmé avec jsonsql.py

**Fichiers analysés :**
- search.py V1.0.24
- jsonsql.py V1.0.3
- lancesql.py V1.0.4

**Bug identifié - DOUBLE PROBLÈME (recherche + restitution) :**

```
Question : "béance antérieure"
→ Détection : tag="béance" (féminin gn=f), adj="antérieur" (canonique masculin)
→ jsonsql construit : "béance antérieur" (SANS accord)
→ Standardise : "beance anterieur"
→ Cherche : pathologie = 'beance anterieur'
→ Base contient : "beance anterieure..." (avec accord féminin)
→ Résultat : 0 match ❌
→ Restitution afficherait : "béance antérieur" ❌ (au lieu de "béance antérieure")
```

**Analyse de cxchargepats.py :**
- Les adjectifs dans le CSV source sont DÉJÀ accordés au genre du tag
- `generate_oripathologies()` concatène directement tag + adjs accordés
- Donc la base stocke bien "beance anterieure" (forme féminine)

**Solution identifiée - 3 fichiers à modifier :**
1. **dettags.py** : passer le genre du tag (gn) à detadjs
2. **detadjs.py** : retourner la forme accordée en plus du canonique
3. **jsonsql.py** : utiliser forme_accordee pour la recherche ET la restitution

Les données nécessaires existent :
- tags.csv : colonne `gn` (m, f, mp, fp)
- adjectifs.csv : colonnes `a`, `f`, `mp`, `fp`

---

## Fichiers créés/modifiés
| Fichier | Action | Date |
|---------|--------|------|
| conv_bugdetall.md | Création | 07/01/2026 |

---

## Prompts de recréation
*(Section à compléter après correction du bug)*

