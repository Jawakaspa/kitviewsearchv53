# Prompt : Création de auditquestions.py

## ⚠️ Convention de répertoires (OBLIGATOIRE)

```
racine/
├── refs/                       # Fichiers de référence
│   └── ia.csv                 # Configuration des moteurs
├── bases/                      # Bases de données
│   └── base100.db
├── tests/                      # Fichiers de test
│   ├── testspats100.csv       # Input
│   └── audit_pats100.csv      # Output
└── auditquestions.py
```

**Le programme cherche automatiquement dans ces répertoires !**

---

## Objectif

Créer un programme d'audit qui compare les résultats attendus (générés par generequestion.py) avec les résultats obtenus par les systèmes de détection.

## Contexte

Le projet KITVIEW utilise deux types de détection :

- **detall.py** (moteur `rapide`) : détection regex/synonymes, instantané
- **detia.py** (moteurs IA) : détection par LLM via Eden AI ou OpenAI

La configuration des moteurs est centralisée dans `refs/ia.csv`.

## Pièces jointes requises

1. `Prompt_contexte2312.md` - Contexte du projet
2. `ia.csv` - Configuration des moteurs
3. `detall.py` - Module de détection traditionnelle
4. `detia.py` - Module de détection IA (optionnel)

## Spécifications

### Moteurs (depuis refs/ia.csv)

| Moteur          | Via    | Description                 |
| --------------- | ------ | --------------------------- |
| `rapide`        | (vide) | detall.py - regex/synonymes |
| `sonnet`        | eden   | Claude 3.7 Sonnet           |
| `haiku`         | eden   | Claude 3.5 Haiku            |
| `gpt4o`         | openai | GPT-4o                      |
| `gpt4omini`     | openai | GPT-4o-mini                 |
| `gemini25flash` | eden   | Gemini 2.5 Flash            |

### Usage CLI

```bash
python auditquestions.py base100.db testspats100.csv
python auditquestions.py base100.db testspats100.csv --moteur rapide
python auditquestions.py base100.db testspats100.csv --moteur sonnet
python auditquestions.py base100.db testspats100.csv --moteur rapide,sonnet
```

### Fichier d'entrée (testspatsN.csv)

```csv
question;type;nb_criteres;nb_resultats;ids_10
Cherche les patients avec bruxisme.;LIST;1;10;8,11,16,24,...
```

### Fichier de sortie (audit_patsN.csv)

Colonnes de base :

- `num`, `question`, `type`, `nb_criteres_attendu`, `nb_resultats_attendu`

Colonnes par moteur (ex: rapide) :

- `rapide_categorie` : OK, SUR:+N, SOUS:-N, DETECTION:residu, ERREUR:xxx
- `rapide_nb_crit` : Nombre de critères détectés
- `rapide_criteres` : Liste des critères (tag:xxx; adj:yyy; age:zzz)
- `rapide_residu` : Texte non reconnu
- `rapide_temps_ms` : Temps de traitement
- `rapide_erreur` : Message d'erreur éventuel

### Catégories d'écart

| Catégorie          | Signification                         |
| ------------------ | ------------------------------------- |
| `OK`               | Nombre de critères identique          |
| `DETECTION:residu` | Critère non détecté (residu non vide) |
| `DETECTION:vide`   | Aucun critère détecté                 |
| `SUR:+N`           | N critères de trop                    |
| `SOUS:-N`          | N critères manquants                  |
| `ERREUR:xxx`       | Erreur technique                      |

### Fonctions principales

1. `charger_moteurs_config()` : Charge refs/ia.csv
2. `detecter_avec_moteur(question, moteur, config, refs_trad, refs_ia)` : Détection selon le moteur
3. `extraire_criteres_str(resultat)` : Formate les critères en chaîne
4. `categoriser_ecart(attendu, obtenu, residu, erreur)` : Détermine la catégorie
5. `auditer_questions(base_path, questions_path, moteurs, config)` : Fonction principale
6. `generer_rapport(resultats, output_path, moteurs)` : Génère le CSV
7. `afficher_statistiques(resultats, moteurs)` : Affiche le résumé

### Exemple d'exécution

```bash
$ python auditquestions.py base100.db testspats100.csv --moteur rapide,sonnet

auditquestions.py V1.0.0 - 19/12/2025 18:30

Modules disponibles :
  detall  : ✓
  detia   : ✓
  cherche : ✓

======================================================================
AUDIT DES QUESTIONS
======================================================================
Base      : C:\cx\bases\base100.db
Questions : C:\cx\tests\testspats100.csv
Mode      : detection
Moteurs   : rapide, sonnet

50 questions à auditer
----------------------------------------------------------------------
  [  1/50] ✓✓
  [  2/50] ✓✗
  ...

======================================================================
STATISTIQUES
======================================================================

Moteur : RAPIDE
----------------------------------------
  ✓ OK                   : 45 (90.0%)
  ✗ SOUS:-1              :  3 ( 6.0%)
  ...
  ⏱ Temps moyen       : 12 ms

Moteur : SONNET
----------------------------------------
  ✓ OK                   : 48 (96.0%)
  ...
  ⏱ Temps moyen       : 3200 ms

======================================================================
[OK] Audit terminé
======================================================================

✓ Rapport d'audit : C:\cx\tests\audit_pats100.csv
```

## Contraintes techniques

- Python 3.13+
- UTF-8-SIG pour CSV
- Séparateur `;`
- Gestion d'erreurs robuste pour imports optionnels
- Affichage de progression pendant l'audit
- Lecture de la configuration des moteurs depuis refs/ia.csv
