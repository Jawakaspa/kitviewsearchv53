# Prompt conv_question_de V1.0.5 - 25/12/2025 09:06:41

# Synthèse de conversation : question_de

## ⚠️ Convention de répertoires (RAPPEL PERMANENT)

```
c:\cx\                          # Répertoire racine
├── refs/                       # Fichiers de RÉFÉRENCE (tagsadjs.xlsx, ages.csv, angles.csv...)
├── bases/                      # Bases SQLite (base100.db, base25000.db)
├── tests/                      # Fichiers générés (testspats*.csv, audit_*.csv, templatequestion.csv)
└── *.py                        # Programmes Python
```

**Ne JAMAIS chercher les fichiers à la racine ! Utiliser les sous-répertoires appropriés.**

---

## Informations générales
- **Date de création** : 19/12/2025
- **Projet** : Kitview - Recherche multilingue de patients orthodontiques

---

## Échanges

### 19/12/2025 14:35 - Demande initiale

**Question** : Création d'un système de génération de questions aléatoires en deux étapes :
1. `templatequestion.py` : génération de 100 templates de questions style "cadavre exquis"
2. `generequestion.py` : utilisation des templates pour générer des questions concrètes (à faire ultérieurement)

**Spécifications des templates** :
- 30 COUNT / 70 LIST
- 10 avec angles (ANB, SNA, SNB)
- Répartition : 25 templates à 1 critère, 25 à 2, 25 à 3, 25 à 4
- Critères incluant âge et sexe dans le comptage
- Au moins 1 adjectif pour les templates à ≥2 critères

**Clarifications obtenues** :
- Fichier source : `tagsadjs.xlsx` (pas csv)
- Angles répartis au hasard dans les 100 templates
- COUNT/LIST répartis au hasard
- Génération dynamique (différente à chaque exécution)
- Ajout d'une colonne `article` dans tagsadjs suggérée et acceptée

### 19/12/2025 14:52 - Livraison templatequestion.py

**Fichiers créés** :

| Fichier | Description |
|---------|-------------|
| `templatequestion.py` | Programme de génération des templates |
| `cadavreexquis.csv` | Composants du cadavre exquis (débuts, liaisons, connecteurs, fins) |
| `templatequestion.csv` | 100 templates générés |
| `tagsadjs_enrichi.xlsx` | tagsadjs avec colonne `article` ajoutée |

### 19/12/2025 15:28 - Demande clarifications pour generequestion.py

Questions posées sur :
- Structure de la base de données
- Format des colonnes canontags/canonadjs
- Angles céphalométriques
- Traductions

### 19/12/2025 15:45 - Livraison generequestion.py

**Clarifications obtenues** :
- Base fournie : `base100.db`
- Structure : `canontags` séparés par `,`, `canonadjs` séparés par `,` avec `|` pour adjectifs alternatifs
- Pas de colonnes ANB/SNA/SNB, déduction via angles.csv
- Génération uniquement en français (multilingue géré par un py au-dessus)

**Méthode "cheat" implémentée** :
1. Lire les patients de la base
2. Pour les questions avec angles : chercher les patients ayant des tags correspondant à des angles
3. Générer une expression d'angle (ANB/SNA/SNB > ou < valeur)
4. Pour les autres questions : tirer un patient au hasard et utiliser ses tags
5. Ajouter critères d'âge basés sur l'âge réel du patient
6. Compter les patients correspondants et stocker nb_resultats + ids_10

**Fichiers créés** :

| Fichier | Description |
|---------|-------------|
| `generequestion.py` | Programme de génération de questions |
| `questions_generees.csv` | Questions générées avec colonnes question, type, nb_criteres, nb_resultats, ids_10 |

**Usage** :
```bash
python generequestion.py base.db N
```

---

## Structure des placeholders

- `{T1}`, `{T2}`, `{T3}`, `{T4}` : Tags (pathologies)
- `{A1}`, `{A2}`, `{A3}`, `{A4}` : Adjectifs associés aux tags
- `{AGE}` : Critère d'âge
- `{ANG}` : Angle céphalométrique

---

## Fichiers d'entrée requis

| Fichier | Description |
|---------|-------------|
| `tagsadjs.xlsx` | Pathologies et adjectifs avec colonnes : canon, type, Xgn, synonymes, adjs, m, f, mp, fp |
| `ages.csv` | Critères d'âge avec colonnes : expression, operateur, valeur_sql, sexe, label, pourquestion |
| `angles.csv` | Angles céphalométriques avec colonnes : expression, operateur, seuil, tag_canonique, adjectifs_possibles, label |
| `cadavreexquis.csv` | Composants du cadavre exquis avec colonnes : categorie, texte, variante, article |
| `templatequestion.csv` | Templates de questions générés |
| `base*.db` | Base de données SQLite avec table patients |

---

## Structure de la base de données

```sql
-- Table patients
id, canontags, canonadjs, stdcanontags, stdcanonadjs, sexe, age, datenaissance, prenom, nom, portrait

-- canontags : tags séparés par virgule (ex: "béance,bruxisme,classe ii")
-- canonadjs : adjectifs par position, séparés par virgule, alternatifs par | (ex: ",sévère|modéré,division 1")
```

---

## Prochaines étapes

1. **Tester avec base100** : Générer questions, auditer, analyser écarts
2. **Corriger les patterns** : Ajouter synonymes manquants si nécessaire
3. **Tester avec base25000** : Validation sur données réelles
4. **Intégration multilingue** : Programme au-dessus de generequestion.py

---

## Programme 3 : auditquestions.py [CRÉÉ 19/12/2025 17:35] [MAJ 19/12/2025 18:30]

### Objectif
Comparer les résultats attendus (generequestion.py) avec les résultats obtenus par les systèmes de détection.

### Moteurs (configurés dans refs/ia.csv)

| Moteur | Via | Programme |
|--------|-----|-----------|
| `rapide` | (local) | detall.py - instantané |
| `sonnet` | eden | detia.py via Eden AI |
| `haiku` | eden | detia.py via Eden AI |
| `gpt4o` | openai | detia.py via OpenAI |
| `gpt4omini` | openai | detia.py via OpenAI |
| `gemini25flash` | eden | detia.py via Eden AI |

### Usage
```bash
# Audit avec moteur rapide (défaut)
python auditquestions.py base100.db testspats100.csv

# Audit avec moteur IA
python auditquestions.py base100.db testspats100.csv --moteur sonnet

# Audit comparatif (plusieurs moteurs)
python auditquestions.py base100.db testspats100.csv --moteur rapide,sonnet,gpt4omini
```

### Catégories d'écart

| Catégorie | Signification |
|-----------|---------------|
| OK | Résultat identique |
| DETECTION:residu | Critère non reconnu (residu non vide) |
| SUR:+N | Plus de critères détectés qu'attendu |
| SOUS:-N | Moins de critères détectés qu'attendu |
| ERREUR:xxx | Erreur technique |

### Fichier de sortie
`tests/audit_patsN.csv` avec colonnes par moteur : {moteur}_categorie, {moteur}_nb_crit, {moteur}_criteres, {moteur}_residu, {moteur}_temps_ms

---

## Guide de test complet [CRÉÉ 19/12/2025 17:35]

[DOCUMENT] /mnt/user-data/outputs/Guide_test_audit.md

Contient :
- Architecture des programmes
- Étapes détaillées de test
- Commandes résumées
- Points critiques
- Objectifs de convergence

---

## Corrections apportées (19/12/2025 16:15 et 16:55)

### Problèmes identifiés et corrigés

| Problème | Cause | Correction |
|----------|-------|------------|
| Tags avec majuscules ("Bruxisme") | Copie depuis canontags | Normalisation en minuscules dans `parse_patient_tags()` |
| Comptage incorrect | Utilisation de `canontags` | Utilisation de `stdcanontags` et `stdcanonadjs` |
| Nom fichier fixe | - | Fichier nommé `testspatsN.csv` selon la base |
| **Expressions d'angle tronquées** ("SNB > 8" au lieu de "SNB > 85") | Bug `isinstance(seuil, (int, float))` retourne False car seuil est une string | Ajout de `parse_seuil()` pour convertir string → int |

### Bug critique corrigé (16:55)

Dans `generate_angle_expression()`, le seuil lu depuis angles.csv est une **string** ("82"), pas un int.

**Avant (bugué)** :
```python
seuil_int = int(seuil) if isinstance(seuil, (int, float)) else 4  # ← Toujours 4 !
```

**Après (corrigé)** :
```python
def parse_seuil(s):
    try:
        return int(float(str(s)))
    except (ValueError, TypeError):
        return 4
seuil_int = parse_seuil(seuil)  # ← 82 correct !
```

### Exemples avant/après

| Avant | Après |
|-------|-------|
| "SNB > 8" | "SNB > 85" |
| "SNA > 7" | "SNA > 87" |
| "ANB > 5" | "ANB > 6" |

### ⚠️ Important : Base de test

**Le fichier de test doit être utilisé avec la MÊME base que celle utilisée pour la génération !**

- `testspats100.csv` → à tester avec `base100.db`
- Si vous testez avec `radix100.db`, les nb_resultats et ids seront différents
