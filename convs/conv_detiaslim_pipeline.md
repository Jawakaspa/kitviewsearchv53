# Prompt conv_detiaslim_pipeline V1.0.6 - 02/01/2026 02:10:09

# Conversation : detiaslim&pipeline
## Synthèse KITVIEW - Pipeline de test (questions + audit)

---

## Informations

| Élément | Valeur |
|---------|--------|
| Date de début | 23/12/2025 15:47 |
| Dernière mise à jour | 02/01/2026 02:15 |
| Objectif | Pipeline de génération de questions et audit concordance |

---

## Architecture actuelle (V4)

**Fichiers de référence** (nouvelle structure) :
- `refs/tags.csv` : Tags avec patterns (colonnes: `t;gn;as;pts`)
- `refs/adjectifs.csv` : Adjectifs avec formes (colonnes: `a;f;mp;fp;pas`)
- `refs/ages.csv` : Patterns âge/sexe
- `refs/angles.csv` : Seuils céphalométriques (colonnes: `expression;operateur;seuil;tag_canonique;adjectifs_possibles;label`)
- `refs/ia.csv` : Configuration moteurs IA

**Note** : Les fichiers `syn*.csv` et `*_slim.csv` sont supprimés. Les lookups sont générés en mémoire à la volée.

---

## Questions et Réponses

### Q1-Q4 : Travail initial (obsolète)
Le travail initial concernait l'intégration des fichiers slim et la génération de synonymes. Cette partie est **obsolète** suite au changement d'architecture.

### Q5 : Adaptation nouvelle architecture
**Date** : 28/12/2025 17:05

**Contexte** : Le référentiel a été scindé en deux fichiers séparés (tags.csv + adjectifs.csv).

**Modifications** : Suppression de la commande `synonymes`, mise à jour de `afficher_status()`.

### Q6 : Intégration des angles dans la génération de questions
**Date** : 28/12/2025 17:25

**Problème** : Les angles n'étaient pas générés (0 patterns d'angles chargés).

**Cause initiale** : La fonction `charger_angles()` ne lisait pas correctement le fichier `angles.csv`.

### Q7 : Correction du BOM mal encodé dans angles.csv
**Date** : 02/01/2026 00:15

**Problème persistant** : Toujours 0 patterns d'angles chargés.

**Cause réelle** : Le fichier `angles.csv` contient une ligne avec un BOM littéral :
```
\xef\xbb\xbf# angles.csv V1.0.0 - 11/12/2025
```
Cette ligne n'est pas filtrée car elle ne commence pas par `#` mais par `\xef`.

**Correction** : Amélioration de `lire_csv_utf8()` pour filtrer aussi les lignes commençant par `\xef\xbb\xbf` (BOM mal encodé littéralement).

```python
# Ignorer BOM mal encodé littéralement
if ligne.startswith('\\xef\\xbb\\xbf') or ligne.startswith(r'\xef\xbb\xbf'):
    continue
```

**Résultat** : 9 patterns d'angles chargés (3 ANB + 3 SNA + 3 SNB)

### Q8 : Améliorations multiples de la génération de questions
**Date** : 02/01/2026 02:05

**Problèmes signalés** :
1. Questions avec `|` dans les tags (ex: "béance gauche|modérée")
2. Manque la colonne `nb_reponses`
3. Seulement 1% d'angles au lieu de 10%
4. Pas de statistiques sur les âges et critères

**Corrections apportées** :

1. **Nettoyage des données patients** :
   - `charger_patients_avec_tags()` filtre maintenant les tags/adjs contenant `|`
   - Ces valeurs sont des patterns, pas des données valides

2. **Nouvelle colonne `nb_reponses`** :
   - Ajoutée au CSV de sortie
   - Pour l'instant = 1 (le patient source)
   - TODO: Implémenter le comptage réel via SQL

3. **Distribution corrigée** :
   - `pct_angles: 10` (10% des questions avec angle)
   - `pct_ages: 20` (20% des questions avec critère d'âge)
   - Système de priorité pour garantir l'inclusion

4. **Stats détaillées affichées** :
```
  Répartition:
    - COUNT: 600 (30%)
    - LIST: 1400 (70%)
    
    - ANGLES: 200 (10%)
    - AGES: 400 (20%)
    
  Par nombre de critères:
    - 1 critère(s): 600 (30%)
    - 2 critère(s): 800 (40%)
    - 3 critère(s): 400 (20%)
    - 4 critère(s): 200 (10%)
```

5. **Signature modifiée de `generer_question_depuis_patient()`** :
   - Nouveau paramètre `inclure_age: bool`
   - Système de priorité pour garantir l'inclusion des critères demandés
   - Retourne `a_angle` et `a_age` pour les stats

**Corrections apportées** :

1. **Nouvelle fonction `charger_angles()`** :
   - Parse correctement les colonnes `expression;operateur;seuil;tag_canonique;label`
   - Identifie le type d'angle (ANB, SNA, SNB)
   - Parse les seuils simples et les plages (ex: "0,4" → tuple (0, 4))

2. **Nouvelle fonction `generer_expression_angle()`** :
   - Génère une valeur cohérente avec la condition (ex: ANB > 5 pour Classe II)
   - Crée des expressions naturelles variées ("ANB > 5", "ANB supérieur à 5", etc.)

3. **Modification de `generer_question_depuis_patient()`** :
   - Nouveau paramètre `inclure_angle: bool`
   - Si True, ajoute un critère angle comme premier critère
   - Le tag résultant (ex: "classe ii squelettique") est ajouté aux tags attendus

4. **Modification de `etape_3_questions()`** :
   - 10% des questions incluent maintenant un angle (`pct_angles: 10`)
   - Affichage du nombre de questions avec angles

**Distribution des questions** :
- COUNT: 30%
- LIST: 70%
- Avec angles: 10%
- Complexité: 1 critère (30%), 2 critères (40%), 3 critères (20%), 4 critères (10%)

---

## Fichiers générés

| Fichier | Version | Lignes | Description |
|---------|---------|--------|-------------|
| `pipeline.py` | 2.2.0 | ~1050 | Pipeline questions + audit (avec angles, âges, nb_reponses) |
| `conv_detiaslim_pipeline.md` | - | - | Ce document de synthèse |

---

## Utilisation de pipeline.py

### Commandes disponibles

```bash
# Afficher l'aide
python pipeline.py
python pipeline.py help

# Voir l'état des fichiers
python pipeline.py status

# Générer des questions de test (10% avec angles)
python pipeline.py questions bases/base1000.db
python pipeline.py quest bases/base1000.db 50
python pipeline.py quest 100 bases/pats500.db verbose

# Lancer l'audit de concordance
python pipeline.py audit 1000
python pipeline.py audit 1000 verbose
```

### Colonnes du fichier de questions

| Colonne | Description |
|---------|-------------|
| `fr` | Question en français |
| `listcount` | COUNT ou LIST |
| `nb_criteres` | Nombre de critères (1-4) |
| `nb_reponses` | Nombre de patients correspondants |
| `tags` | Tags attendus (séparés par virgule) |
| `adjectifs` | Adjectifs attendus |
| `patient_id` | ID du patient source |

### Exemple de sortie attendue

```
✓ 200 patients chargés avec tags
✓ 9 patterns d'angles chargés
  Types: ANB, SNA, SNB

✓ 2000 questions générées → tests/qpats25000in.csv

  Répartition:
    - COUNT: 600 (30%)
    - LIST: 1400 (70%)
    
    - ANGLES: 200 (10%)
    - AGES: 400 (20%)
    
  Par nombre de critères:
    - 1 critère(s): 600 (30%)
    - 2 critère(s): 800 (40%)
    - 3 critère(s): 400 (20%)
    - 4 critère(s): 200 (10%)
```

### Exemples de questions avec angles générées

- "Combien de patients avec ANB > 5 de moins de 25 ans ?"
  - Tags attendus: `classe ii squelettique`
- "patients avec SNA inférieur à 78 hommes ?"
  - Tags attendus: `rétrognathisme maxillaire`

---

## Prompt de recréation

### Pour recréer pipeline.py

**Fichiers à joindre en PJ :**
- `Prompt_contexte2312.md`
- `angles.csv` (pour voir la structure)
- `detangles.py` (pour référence)

**Prompt :**
```
Crée le module pipeline.py V2.1 pour KITVIEW avec deux commandes principales :

COMMANDE questions (ou quest) :
- Génère des questions de test depuis une base patients SQLite
- Méthode "cheat" : utilise des patients réels pour garantir des résultats
- Distribution : 30% COUNT, 70% LIST
- Complexité variable : 1-4 critères par question
- **10% des questions incluent un angle céphalométrique**
- Sortie : tests/qpatsNNNNin.csv (N = numéro extrait du nom de la base)
- Colonne question nommée 'fr' pour traduction ultérieure
- Âges toujours en entiers

GÉNÉRATION D'ANGLES :
- Charger angles.csv (colonnes: expression;operateur;seuil;tag_canonique;label)
- Identifier le type d'angle (ANB, SNA, SNB) depuis l'expression
- Parser les seuils : simples (4) ou plages (0,4)
- Générer des expressions naturelles : "ANB > 5", "ANB supérieur à 5"
- La valeur générée doit être cohérente avec l'opérateur et le seuil
- Le tag_canonique (ex: "classe ii squelettique") est ajouté aux tags attendus

COMMANDE audit :
- Compare les sorties de detall et detia
- Métriques : concordance listcount, concordance tags exacte, Jaccard, latences
- Sortie : tests/auditNNNN.csv

PARSING INTELLIGENT (ordre des paramètres libre, sans --) :
- Commande : questions/quest, audit, status, help
- Base : tout ce qui finit par .db
- Nombre : entier seul
- verbose : le mot verbose

CONSTANTES :
DISTRIBUTION_QUESTIONS = {
    'pct_count': 30,      # 30% COUNT, 70% LIST
    'pct_angles': 10,     # 10% des questions avec angle
    'complexite': {1: 30, 2: 40, 3: 20, 4: 10}  # Distribution des critères
}
```

---

## Points d'attention

1. **Colonne `fr`** : Les questions sont dans la colonne `fr` (pas `question`) pour la traduction
2. **Âges entiers** : Toujours `int(age)` pour éviter les décimales
3. **Angles 10%** : Distribution contrôlée des questions avec angles
4. **Valeurs cohérentes** : ANB > 5 génère une Classe II car 5 > 4 (seuil)
5. **Tags des angles** : Le `tag_canonique` de l'angle est ajouté à la liste des tags attendus

---

*Document mis à jour le 02/01/2026 02:15*
