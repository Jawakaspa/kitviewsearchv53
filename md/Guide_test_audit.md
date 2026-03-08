# Prompt Guide_test_audit V1.0.1 - 25/12/2025 09:06:41

# Guide de Test et Audit - Système KITVIEW

## ⚠️ Convention de répertoires (IMPORTANT)

```
c:\cx\                          # Répertoire racine du projet
├── refs/                       # Fichiers de RÉFÉRENCE (lecture seule)
│   ├── tagsadjs.xlsx          
│   ├── ages.csv               
│   ├── angles.csv             
│   ├── cadavreexquis.csv      
│   ├── syntags.csv            
│   └── synadjs.csv            
├── bases/                      # Bases de données SQLite
│   ├── base100.db             
│   └── base25000.db           
├── tests/                      # Fichiers générés et de test
│   ├── templatequestion.csv   # Généré par templatequestion.py
│   ├── testspats100.csv       # Généré par generequestion.py
│   ├── testspats25000.csv     
│   └── audit_pats100.csv      # Généré par auditquestions.py
└── *.py                        # Programmes Python
```

**Les programmes cherchent automatiquement dans ces répertoires !**

---

## Vue d'ensemble

Ce guide détaille les étapes pour tester et auditer le système de recherche de patients.

### Architecture des programmes

```
┌─────────────────────────────────────────────────────────────────────┐
│                     GÉNÉRATION DE QUESTIONS                          │
├─────────────────────────────────────────────────────────────────────┤
│  templatequestion.py  →  templatequestion.csv (100 templates)       │
│                              ↓                                       │
│  generequestion.py    →  testspatsN.csv (questions + résultats)     │
│         ↑                                                            │
│    baseN.db (lecture directe pour garantir nb_resultats > 0)        │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                     DÉTECTION DE CRITÈRES                            │
├─────────────────────────────────────────────────────────────────────┤
│  TRADITIONNELLE           │  IA (Eden AI)                           │
│  ───────────────          │  ────────────                           │
│  identall.py              │  detia.py                               │
│    ├── detcount.py        │    └── API Eden AI                      │
│    ├── detangles.py       │        ├── Claude Sonnet                │
│    ├── dettags.py         │        ├── GPT-4o                       │
│    └── detage.py          │        └── Gemini Flash                 │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                     RECHERCHE PATIENTS                               │
├─────────────────────────────────────────────────────────────────────┤
│  cherche.py (français)    │  suche.py (multilingue)                 │
│       ↓                   │       ↓                                 │
│  Construction SQL + Exécution sur baseN.db                          │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                     AUDIT ET COMPARAISON                             │
├─────────────────────────────────────────────────────────────────────┤
│  auditquestions.py  →  audit_patsN.csv (rapport détaillé)           │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Prérequis

### Fichiers nécessaires (même répertoire)

| Fichier | Description | Source |
|---------|-------------|--------|
| `generequestion.py` | Génération de questions | Claude |
| `templatequestion.py` | Génération de templates | Claude |
| `auditquestions.py` | Audit des résultats | Claude |
| `templatequestion.csv` | 100 templates | Généré |
| `cadavreexquis.csv` | Composants questions | Généré |
| `tagsadjs.xlsx` | Tags et adjectifs | Fourni |
| `ages.csv` | Patterns d'âge | Fourni |
| `angles.csv` | Angles céphalométriques | Fourni |
| `base100.db` | Base test 100 patients | Fourni |
| `base25000.db` | Base production | Fourni |

### Fichiers de détection (pour audit avancé)

| Fichier | Description |
|---------|-------------|
| `cherche.py` | Recherche française |
| `identall.py` | Orchestrateur détection |
| `detage.py` | Détection âges |
| `detangles.py` | Détection angles |
| `dettags.py` | Détection tags |
| `detcount.py` | Détection LIST/COUNT |
| `detia.py` | Détection par IA |

---

## ÉTAPE 1 : Générer les templates (une seule fois)

```bash
python templatequestion.py
```

**Résultat** : 
- `templatequestion.csv` (100 templates)
- `cadavreexquis.csv` (composants)

---

## ÉTAPE 2 : Générer les questions de test

### Pour base100 (test rapide)

```bash
python generequestion.py base100.db 50
```

**Résultat** : `testspats100.csv`

### Pour base25000 (production)

```bash
python generequestion.py base25000.db 100
```

**Résultat** : `testspats25000.csv`

### Structure du fichier généré

```csv
question;type;nb_criteres;nb_resultats;ids_10
Cherche les patients avec bruxisme nocturne.;LIST;1;10;8,11,16,24,34,52,55,68,99,100
Combien ai-je de patients avec béance sévère?;COUNT;1;12;4,10,15,27,29,43,55,65,72,78
```

---

## ÉTAPE 3 : Auditer les questions

### Moteurs disponibles (configurés dans refs/ia.csv)

| Moteur | Via | Description |
|--------|-----|-------------|
| `rapide` | (local) | Détection regex/synonymes via detall.py - instantané |
| `sonnet` | eden | Claude 3.7 Sonnet via Eden AI |
| `haiku` | eden | Claude 3.5 Haiku via Eden AI |
| `opus` | eden | Claude 3 Opus via Eden AI |
| `gpt4o` | openai | GPT-4o via OpenAI direct |
| `gpt4omini` | openai | GPT-4o-mini via OpenAI direct |
| `gemini25flash` | eden | Gemini 2.5 Flash via Eden AI |

### Audit avec moteur rapide (défaut)

```bash
python auditquestions.py base100.db testspats100.csv
# ou explicitement :
python auditquestions.py base100.db testspats100.csv --moteur rapide
```

### Audit avec moteur IA

```bash
# Nécessite EDENAI_API_KEY ou OPENAI_API_KEY selon le moteur
set EDENAI_API_KEY=votre_clé
python auditquestions.py base100.db testspats100.csv --moteur sonnet
```

### Audit comparatif (plusieurs moteurs)

```bash
python auditquestions.py base100.db testspats100.csv --moteur rapide,sonnet
python auditquestions.py base100.db testspats100.csv --moteur rapide,sonnet,gpt4omini
```

**Résultat** : `tests/audit_pats100.csv`

---

## ÉTAPE 4 : Analyser le rapport d'audit

### Colonnes du rapport

| Colonne | Description |
|---------|-------------|
| `num` | Numéro de la question |
| `question` | Texte de la question |
| `type` | COUNT ou LIST |
| `nb_criteres` | Nombre de critères dans la question |
| `nb_attendu` | Résultats attendus (generequestion) |
| `ids_attendu` | IDs des 10 premiers patients attendus |
| `trad_nb` | Résultats obtenus (traditionnel) |
| `trad_criteres` | Critères détectés |
| `trad_residu` | Texte non reconnu |
| `trad_categorie` | Catégorie d'écart |
| `trad_temps_ms` | Temps de traitement |

### Catégories d'écart

| Catégorie | Signification | Action |
|-----------|---------------|--------|
| `OK` | Résultat identique | ✓ |
| `DETECTION:residu_important` | Critère non reconnu | Vérifier synonymes |
| `DETECTION:aucun_resultat` | Rien détecté | Vérifier patterns |
| `SURDETECTION:+N` | Plus de résultats | Critère trop large |
| `SOUSDETECTION:-N` | Moins de résultats | Critère trop strict |
| `ERREUR:xxx` | Erreur technique | Corriger le bug |

---

## ÉTAPE 5 : Corriger les écarts

### Écarts de détection

1. Ouvrir `audit_patsN.csv`
2. Filtrer sur `trad_categorie = DETECTION`
3. Examiner `trad_residu` pour voir ce qui n'est pas reconnu
4. Ajouter les synonymes manquants dans :
   - `syntags.csv` pour les tags
   - `synadjs.csv` pour les adjectifs
   - `ages.csv` pour les expressions d'âge
   - `angles.csv` pour les angles

### Écarts de sur/sous-détection

1. Comparer `trad_criteres` avec les critères attendus
2. Vérifier si les critères sont correctement traduits en SQL
3. Vérifier les incompatibilités dans `commun.csv`

---

## Résumé des commandes

```bash
# ═══════════════════════════════════════════════════════════════════
# BASE 100 (test rapide)
# ═══════════════════════════════════════════════════════════════════

# 1. Générer templates (une seule fois)
python templatequestion.py

# 2. Générer questions
python generequestion.py base100.db 50

# 3. Auditer (moteur rapide = detall.py)
python auditquestions.py base100.db testspats100.csv

# 4. Auditer avec moteur IA (nécessite clé API)
python auditquestions.py base100.db testspats100.csv --moteur sonnet

# 5. Auditer comparatif (plusieurs moteurs)
python auditquestions.py base100.db testspats100.csv --moteur rapide,sonnet

# 6. Analyser tests/audit_pats100.csv

# ═══════════════════════════════════════════════════════════════════
# BASE 25000 (production)
# ═══════════════════════════════════════════════════════════════════

# 1. Générer questions
python generequestion.py base25000.db 100

# 2. Auditer
python auditquestions.py base25000.db testspats25000.csv --moteur rapide

# 3. Analyser tests/audit_pats25000.csv
```

---

## ⚠️ Points critiques

### 1. Cohérence base/fichier de test

**TOUJOURS utiliser la MÊME base pour générer ET tester !**

| Fichier | Base obligatoire |
|---------|------------------|
| `testspats100.csv` | `base100.db` |
| `testspats25000.csv` | `base25000.db` |

### 2. Patterns reconnus

Les expressions générées doivent correspondre aux patterns de détection :

**Âges** (dans `ages.csv`) :
- ✅ "adolescents", "adultes", "mineurs", "enfants"
- ✅ "moins de N ans", "plus de N ans"
- ✅ "entre N et N ans", "N ans"
- ❌ Formes non listées

**Angles** (dans `angles.csv`) :
- ✅ "ANB > N", "ANB < N", "ANB entre N et N"
- ✅ "SNA > N", "SNB > N"
- ❌ Formes alternatives non listées

**Tags** (dans `tagsadjs.xlsx` / `syntags.csv`) :
- ✅ Formes canoniques en minuscules
- ✅ Synonymes listés
- ❌ Variantes non référencées

### 3. Normalisation

Le système normalise les textes (minuscules, sans accents pour comparaison).
Les tags générés doivent être en **minuscules** pour correspondre.

---

## Objectif de convergence

| Métrique | Cible | Acceptable |
|----------|-------|------------|
| Taux OK | > 90% | > 80% |
| Écarts explicables | 100% | 95% |
| Temps moyen | < 100ms | < 500ms |

Les écarts résiduels doivent être :
1. **Logiques** : différence d'interprétation
2. **Documentés** : cause identifiée
3. **Non-bugs** : pas d'erreur technique

---

**Version** : 1.0.0 - 19/12/2025
