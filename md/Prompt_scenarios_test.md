# Prompt Prompt_scenarios_test V1.0.2 - 04/01/2026 17:41:51

# Scénarios de Test - Pipeline Orthodontique KITVIEW

**Date de création** : 28/12/2025  
**Dernière mise à jour** : 04/01/2026  
**Version** : 2.0.0

Ce document décrit les scénarios de test pour valider l'ensemble des composants du projet KITVIEW, du plus profond (modules de détection) au plus global (interface web et dashboard analytics).

---

## Table des matières

1. [Vue d'ensemble de l'architecture](#1-vue-densemble-de-larchitecture)
2. [Prérequis](#2-prérequis)
3. [Niveau 1 : Modules de détection unitaires](#3-niveau-1--modules-de-détection-unitaires)
4. [Niveau 2 : Utilitaires](#4-niveau-2--utilitaires)
5. [Niveau 3 : Pipeline orchestrateur](#5-niveau-3--pipeline-orchestrateur)
6. [Niveau 4 : Recherche globale](#6-niveau-4--recherche-globale)
7. [Niveau 5 : Serveur](#7-niveau-5--serveur)
8. [Niveau 6 : Interface web](#8-niveau-6--interface-web)
9. [Niveau 7 : Dashboard analytics](#9-niveau-7--dashboard-analytics)
10. [Niveau 8 : Outils de génération de tests](#10-niveau-8--outils-de-génération-de-tests)
11. [Scénarios d'intégration multilingue](#11-scénarios-dintégration-multilingue)
12. [Checklist de validation](#12-checklist-de-validation)

---

## 1. Vue d'ensemble de l'architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      NIVEAU 7 : Dashboard Analytics                         │
│    analyse.py (CLI) + analyse12.html (Web)                                  │
│    Stats, filtres, 3 vues (résumé/cards/table), recherche commentaires      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                      NIVEAU 6 : Interface Web                               │
│    web13.html (recherche) + web13params.html (paramètres)                   │
│    i18n, cards patients, zone IA, pathologies                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NIVEAU 5 : server.py                                │
│    Serveur FastAPI - Endpoints /search, /ia, /analyse, /i18n                │
│    Lazy loading dictionnaires multilingues                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NIVEAU 4 : search.py                                │
│    Résolution sémantique multilingue via glossaire.csv                      │
│    Question (xx) → Question hybride (fr) → Résultats SQL                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NIVEAU 3 : detall.py                                │
│    Pipeline V2 : detcount → detangles → dettags → detage                    │
└─────────────────────────────────────────────────────────────────────────────┘
                    │               │               │               │
                    ▼               ▼               ▼               ▼
           ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
           │ detcount.py │ │detangles.py │ │ dettags.py  │ │  detage.py  │
           │  LIST/COUNT │ │ ANB SNA SNB │ │ + detadjs   │ │  Âge/Sexe   │
           └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘
                                                  │
                                                  ▼
                                         ┌─────────────┐
                                         │ detadjs.py  │
                                         │  Adjectifs  │
                                         └─────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│           NIVEAU 2 : Utilitaires                                            │
│    traducteur.py (traduction glossaire/DeepL)                               │
│    lazycommentaires.py (traduction à la demande)                            │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│           NIVEAU 1 : Alternative IA                                         │
│    detia.py (détection par LLM)                                             │
│    detiabrut.py (test sans référentiels)                                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│           OUTILS DE TEST                                                    │
│    pipeline.py (génération questions)                                       │
│    creefakelog.py (génération logs fictifs)                                 │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                       FICHIERS DE RÉFÉRENCE                                 │
│  tags.csv │ adjectifs.csv │ glossaire.csv │ angles.csv │ ages.csv │ ia.csv  │
│  commentaires.csv │ fr100.csv │ logrecherche.csv                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Prérequis

### 2.1 Structure des répertoires

```
racine/
├── bases/
│   ├── base100.db
│   ├── base1000.db
│   └── base25000.db
├── refs/
│   ├── tags.csv           (t;gn;as;pts)
│   ├── adjectifs.csv      (a;f;mp;fp;pas)
│   ├── glossaire.csv      (type;fr;en;de;es;it;ja;pt;pl;ro;th;ar;cn)
│   ├── ages.csv
│   ├── angles.csv
│   ├── ia.csv
│   └── commentaires.csv
├── tests/
│   ├── fr100.csv          (questions multilingues)
│   ├── qpats1000in.csv    (questions générées)
│   └── qpats1000out.csv   (résultats detall)
├── logs/
│   └── logrecherche.csv
├── detadjs.py
├── dettags.py
├── detia.py
├── detiabrut.py
├── detall.py
├── detage.py
├── detangles.py
├── detcount.py
├── search.py
├── server.py
├── traducteur.py
├── lazycommentaires.py
├── analyse.py
├── pipeline.py
├── creefakelog.py
├── web13.html
├── web13params.html
└── analyse12.html
```

### 2.2 Contrôles initiaux

```cmd
# Vérifier l'existence des fichiers de référence
dir refs\*.csv

# Vérifier l'encodage UTF-8-SIG
python -c "open('refs/glossaire.csv', encoding='utf-8-sig').read(); print('OK')"

# Vérifier les colonnes de tags.csv
python -c "import csv; r=csv.DictReader(open('refs/tags.csv', encoding='utf-8-sig'), delimiter=';'); print(r.fieldnames)"
# Attendu : ['t', 'gn', 'as', 'pts']

# Vérifier les colonnes de adjectifs.csv
python -c "import csv; r=csv.DictReader(open('refs/adjectifs.csv', encoding='utf-8-sig'), delimiter=';'); print(r.fieldnames)"
# Attendu : ['a', 'f', 'mp', 'fp', 'pas']

# Vérifier la base de test
python -c "import sqlite3; c=sqlite3.connect('bases/base100.db'); print(c.execute('SELECT COUNT(*) FROM patients').fetchone()[0], 'patients')"
```

---

## 3. Niveau 1 : Modules de détection unitaires

### 3.1 Test detadjs.py (Détection des adjectifs)

**Objectif** : Vérifier le chargement de `adjectifs.csv` et la détection.

**Syntaxe** : `python detadjs.py <tag> <question>`

```cmd
# Test CLI basique (2 arguments : tag + question)
python detadjs.py "béance" "patient avec béance sévère gauche"

# Sortie attendue (JSON) :
# {
#   "adjectifs": [
#     {"detecte": "gauche", "canonique": "gauche", "standardise": "gauche"},
#     {"detecte": "severe", "canonique": "sévère", "standardise": "severe"}
#   ],
#   "mots_utilises": ["gauche", "severe"]
# }

# Test avec autre tag
python detadjs.py "classe ii d'angle" "classe II sévère division 1"
```

**Points de contrôle** :
- [ ] Fichier `adjectifs.csv` chargé sans erreur
- [ ] Patterns générés en mémoire (pas de fichier synadjs.csv)
- [ ] Tri par longueur décroissante respecté
- [ ] Format JSON de sortie conforme (adjectifs + mots_utilises)

---

### 3.2 Test dettags.py (Détection des tags + adjectifs)

**Objectif** : Vérifier la détection combinée tags + adjectifs.

**Syntaxe** : `python dettags.py <question>`

```cmd
# Test CLI basique
python dettags.py "patients avec béance latérale sévère"

# Sortie attendue (JSON) :
# {
#   "criteres": [
#     {
#       "detecte": "beance",
#       "canonique": "béance",
#       "standardise": "beance",
#       "adjectifs": [
#         {"detecte": "lateral", "canonique": "latéral", "standardise": "lateral"},
#         {"detecte": "severe", "canonique": "sévère", "standardise": "severe"}
#       ],
#       "operateur": "=",
#       "valeur": "béance"
#     }
#   ],
#   "residu": "patients avec",
#   "question_standardisee": "patients avec beance lateral severe"
# }

# Test avec plusieurs tags
python dettags.py "bruxisme sévère avec classe ii"
```

**Points de contrôle** :
- [ ] Fichiers `tags.csv` et `adjectifs.csv` chargés
- [ ] Colonne `as` (adjectifs autorisés) utilisée pour filtrer
- [ ] Un mot ne peut être consommé qu'une seule fois
- [ ] Format JSON compatible avec detia.py

---

### 3.3 Test detia.py (Détection par IA)

**Objectif** : Vérifier la détection IA et la compatibilité de sortie avec detall.

**Syntaxe** : `python detia.py <question> [--model MODEL] [--verbose]`

```cmd
# Test avec modèle par défaut
python detia.py "bruxisme sévère avec classe ii"

# Test avec modèle spécifique
python detia.py "bruxisme sévère avec classe ii" --model gpt-4o-mini

# Test verbose
python detia.py "patients de moins de 30 ans avec béance" --verbose
```

**Points de contrôle** :
- [ ] Chargement de `tags.csv`, `adjectifs.csv`, `ages.csv`, `angles.csv`
- [ ] Appel API OpenAI ou Eden AI selon le modèle
- [ ] Format JSON identique à detall.py (sauf `auteur`)
- [ ] `question_standardisee` sans accents
- [ ] Opérateur SQL `=` (pas `LIKE`)

---

### 3.4 Test detiabrut.py (Détection IA sans référentiels)

**Objectif** : Comparer l'IA guidée vs non guidée.

**Syntaxe** : `python detiabrut.py <question> [options...]`

```cmd
# Mode normal (équivalent detia)
python detiabrut.py "bruxisme sévère" detia

# Mode brut complet (aucun référentiel)
python detiabrut.py "bruxisme sévère" brut

# Désactiver seulement les tags
python detiabrut.py "bruxisme sévère" tags

# Désactiver tags et mapping
python detiabrut.py "bruxisme sévère" tags mapping

# Afficher l'aide
python detiabrut.py --help
```

**Options disponibles** :
- `tags` : Désactive la liste des tags dans le prompt
- `adjs` : Désactive la liste des adjectifs
- `ages` : Désactive les patterns d'âge
- `angles` : Désactive les patterns d'angles
- `mapping` : Désactive le post-traitement canonique
- `brut` : Raccourci pour tout désactiver
- `detia` : Raccourci pour tout activer (défaut)

**Points de contrôle** :
- [ ] Signature `auteur` indique les options désactivées
- [ ] Format JSON identique aux autres modules
- [ ] Mode `brut` donne des résultats différents (moins précis)

---

## 4. Niveau 2 : Utilitaires

### 4.1 Test traducteur.py

**Objectif** : Vérifier la traduction glossaire et DeepL.

```cmd
# Aide
python traducteur.py -h

# Traduction phrase (glossaire)
python traducteur.py "bruxisme sévère" fren
# Attendu : bruxism severe

# Traduction phrase (DeepL)
python traducteur.py "bruxisme sévère" fren --deepl

# Traduction inverse
python traducteur.py "severe bruxism" enfr
# Attendu : sévères bruxisme (ou approchant)

# Expressions longues
python traducteur.py "classe ii squelettique avec béance" frde
# Attendu : skelettklasse ii mit offener biss

# Compléter le glossaire (5 termes max)
python traducteur.py refs/glossaire.csv th -t5

# Traduire un fichier CSV
python traducteur.py fichier.csv fren -t10
```

**Points de contrôle** :
- [ ] Glossaire exclusif sauf `--deepl` ou fichier glossaire lui-même
- [ ] Expressions longues d'abord (tri par longueur décroissante)
- [ ] Résultat hybride (mots traduits + mots non trouvés)
- [ ] 12 colonnes de langue créées automatiquement si absentes
- [ ] Garde-fou contre l'écrasement accidentel

---

### 4.2 Test lazycommentaires.py

**Objectif** : Vérifier la traduction à la demande des commentaires.

```cmd
# Statistiques
python lazycommentaires.py stats

# Obtenir un commentaire (traduit si nécessaire)
python lazycommentaires.py get "bruxisme" en

# Vérifier le taux de complétion par langue
python lazycommentaires.py completion
```

**Points de contrôle** :
- [ ] Chargement de `commentaires.csv` en mémoire
- [ ] Traduction DeepL à la demande si colonne vide
- [ ] Sauvegarde immédiate après traduction
- [ ] Retour vide avec warning si échec DeepL

---

## 5. Niveau 3 : Pipeline orchestrateur

### 5.1 Test detall.py

**Objectif** : Vérifier le pipeline complet de détection.

```cmd
# Test simple
python detall.py "bruxisme"
# Attendu : JSON avec criteres, residu, question_standardisee

# Test complexe
python detall.py "liste femmes de moins de 30 ans avec classe II sévère"
# Attendu : LIST + critères âge + sexe + tag avec adjectif

# Test angles
python detall.py "patients avec ANB > 5"
# Attendu : tag "classe ii squelettique" détecté

# Test COUNT
python detall.py "combien de patients avec béance"
# Attendu : listcount = "COUNT"

# Mode verbose
python detall.py "bruxisme sévère" --verbose

# Mode debug
python detall.py "bruxisme sévère" --debug
```

**Points de contrôle** :
- [ ] Pipeline exécuté dans l'ordre : detcount → detangles → dettags → detage
- [ ] Chaque mot consommé une seule fois
- [ ] `question_standardisee` sans accents
- [ ] Compatibilité format avec detia.py

---

### 5.2 Comparaison detall vs detia

**Objectif** : Vérifier que les deux méthodes donnent des résultats cohérents.

```cmd
# Même question avec les deux méthodes
python detall.py "bruxisme sévère avec classe ii" > detall_result.json
python detia.py "bruxisme sévère avec classe ii" > detia_result.json

# Comparer manuellement :
# - Même nombre de critères ?
# - Mêmes tags détectés (ordre peut varier) ?
# - Même question_standardisee ?
# - Seul auteur diffère ?
```

**Points de contrôle** :
- [ ] Tags détectés identiques (ordre peut varier)
- [ ] Adjectifs correctement associés aux tags
- [ ] Un adjectif n'est jamais utilisé deux fois
- [ ] Opérateur SQL identique (`=`)

---

## 6. Niveau 4 : Recherche globale

### 6.1 Test search.py

**Syntaxe** : `python search.py <base.db> <question> [--lang LANG] [--mode MODE]`

```cmd
# Recherche français
python search.py bases/base100.db "bruxisme"

# Recherche anglais
python search.py bases/base100.db "bruxism" --lang en

# Recherche auto-détection
python search.py bases/base100.db "severe bruxism" --lang auto

# Mode rapide (detall)
python search.py bases/base100.db "bruxisme" --mode rapide

# Mode IA (detia)
python search.py bases/base100.db "bruxisme" --mode ia

# Mode comparaison
python search.py bases/base100.db "bruxisme" --mode compare
```

**Points de contrôle** :
- [ ] Résolution sémantique via glossaire.csv
- [ ] Question hybride (termes résolus FR + termes non trouvés)
- [ ] Résultats SQL cohérents
- [ ] Temps de réponse < 10 secondes
- [ ] Logging dans `logs/logrecherche.csv`

---

## 7. Niveau 5 : Serveur

### 7.1 Test server.py

```cmd
# Démarrage
python server.py
# → http://localhost:8000

# Test endpoint /health
curl http://localhost:8000/health
# Attendu : {"status": "ok", "analyse_disponible": true, ...}

# Test endpoint /api
curl http://localhost:8000/api
# Attendu : Liste de tous les endpoints disponibles

# Test recherche
curl "http://localhost:8000/search?q=bruxisme&base=base100.db"

# Test recherche multilingue
curl "http://localhost:8000/search?q=bruxism&base=base100.db&lang=en"

# Test /ia (liste des moteurs)
curl http://localhost:8000/ia

# Test /i18n (textes interface)
curl "http://localhost:8000/i18n?lang=en"

# Test /analyse/stats
curl http://localhost:8000/analyse/stats
```

**Endpoints à tester** :

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/health` | GET | État du serveur |
| `/api` | GET | Liste des endpoints |
| `/search` | GET | Recherche de patients |
| `/ia` | GET | Liste des moteurs IA |
| `/ia/{moteur}` | PUT | Activer/désactiver un moteur |
| `/ia/ask` | POST | Interroger un LLM |
| `/i18n` | GET | Textes interface traduits |
| `/analyse` | GET | Page dashboard |
| `/analyse/stats` | GET | Statistiques globales |
| `/analyse/recherches` | GET | Liste paginée des recherches |
| `/analyse/recherche/{id}` | GET | Détail d'une recherche |
| `/analyse/export` | GET | Export CSV |

---

## 8. Niveau 6 : Interface web

### 8.1 Test web13.html

**Prérequis** : `python server.py` en cours d'exécution

```
Ouvrir http://localhost:8000 dans un navigateur
```

**Tests fonctionnels** :

| Test | Action | Résultat attendu |
|------|--------|------------------|
| Recherche simple | Taper "bruxisme" + Entrée | Liste de patients affichée |
| Recherche multilingue | Taper "bruxism" (EN détecté) | Résultats en français |
| Changement de base | Sélectionner base25000.db | Nouvelle recherche sur cette base |
| Changement de langue | Sélectionner "ja" | Interface en japonais |
| Card patient | Cliquer sur une card | Détail avec pathologies en gras |
| Zone IA | Poser une question IA | Modal avec réponse |
| Mode IA/Classique | Toggle le switch | Affichage bascule |
| Pagination | Cliquer "Page suivante" | Nouveaux patients affichés |

---

### 8.2 Test web13params.html

```
Ouvrir http://localhost:8000/params dans un navigateur
```

**Tests fonctionnels** :

| Test | Action | Résultat attendu |
|------|--------|------------------|
| Liste moteurs IA | Page chargée | 17 moteurs affichés avec logos |
| Activer/désactiver | Cliquer sur un toggle | Statut mis à jour |
| Bouton Analyse | Cliquer "Analyse des logs" | Redirection vers /analyse |
| Enregistrer | Cliquer "Enregistrer" | Message de confirmation |

---

## 9. Niveau 7 : Dashboard analytics

### 9.1 Test analyse.py (CLI)

```cmd
# Statistiques globales
python analyse.py stats

# Liste des recherches
python analyse.py list --limit=20

# Filtrer par rating
python analyse.py list --rating=👎 --limit=10

# Détail d'une recherche
python analyse.py detail <session_id>

# Recherches similaires
python analyse.py similaires <session_id> --by=ip

# Analyse IA
python analyse.py ia-summary

# Export CSV
python analyse.py export --output=export.csv

# Recherche dans les commentaires
python analyse.py search-comment "bug"
```

---

### 9.2 Test analyse12.html

```
Ouvrir http://localhost:8000/analyse dans un navigateur
```

**Tests fonctionnels** :

| Test | Action | Résultat attendu |
|------|--------|------------------|
| Stats cards | Page chargée | 6 cards avec chiffres |
| Clic sur stat | Cliquer sur "👎 Négatifs" | Filtre appliqué automatiquement |
| Vue Résumé | Onglet "Résumé" | Analyse IA affichée |
| Vue Cards | Onglet "Cards" | Recherches en cards |
| Vue Table | Onglet "Table" | Tableau avec tri bidirectionnel |
| Tri colonnes | Cliquer sur entête | Tri ASC/DESC |
| Recherche commentaires | Taper dans le champ | Filtre appliqué |
| Bouton Play | Cliquer sur ▶ | web13.html ouvert avec la question |
| Modal détail | Cliquer sur une ligne | Modal avec tous les champs |
| Export | Cliquer "Export CSV" | Téléchargement du fichier |

---

## 10. Niveau 8 : Outils de génération de tests

### 10.1 Test pipeline.py

**Objectif** : Générer des questions de test à partir d'une base.

```cmd
# Générer 100 questions depuis base1000.db
python pipeline.py quest bases/base1000.db 100

# Sortie attendue :
# ✓ 200 patients chargés avec tags
# ✓ 9 patterns d'angles chargés
# ✓ 100 questions générées → tests/qpats1000in.csv
#   - COUNT: 28 (28%)
#   - LIST: 72 (72%)
#   - ANGLES: 10 (10%)
#   - AGES: 20 (20%)

# Vérifier le fichier généré
type tests\qpats1000in.csv
# Colonnes attendues : question;listcount;nb_criteres;tags;adjectifs;patient_id;nb_reponses
```

**Points de contrôle** :
- [ ] Nom du fichier intègre le nombre de patients (qpats1000in.csv)
- [ ] ~10% des questions avec angles
- [ ] ~20% des questions avec critère d'âge
- [ ] Colonne `nb_reponses` présente (nombre de patients correspondants)
- [ ] Pas de caractère `|` dans les questions

---

### 10.2 Test creefakelog.py

**Objectif** : Générer des logs de recherche fictifs pour tester le dashboard.

```cmd
# Générer 300 lignes de logs
python creefakelog.py 300 tests/fr100.csv

# Sortie attendue :
# ╔════════════════════════════════════════════════════════════════
# ║ creefakelog.py V1.x.x - ...
# ╚════════════════════════════════════════════════════════════════
#
# Phase 1 : 78 lignes copiées
# Phase 2 : 78 lignes générées (1-17 déc)
# Phase 3 : 144 lignes générées (18 déc - 5 jan)
#
# ✅ Fichier généré : logs/logrechercheout.csv
#    → 300 lignes écrites

# Vérifier la diversification des questions
# (max 2 occurrences identiques, sinon mot ajouté)
```

**Points de contrôle** :
- [ ] N ≥ 3 × LR (lignes originales)
- [ ] Phase 1 : copie exacte des lignes originales
- [ ] Phase 2 : timestamps 1-17 déc + ratings obligatoires
- [ ] Phase 3 : 20% ja, 25% en, 55% fr
- [ ] Max 2 occurrences d'une même question (diversification avec motsvides.csv)
- [ ] Fichier trié par timestamp croissant

---

## 11. Scénarios d'intégration multilingue

### 11.1 Scénario : Recherche japonaise bout en bout

```cmd
# 1. Vérifier que le glossaire contient des termes japonais
python -c "
import csv
with open('refs/glossaire.csv', encoding='utf-8-sig') as f:
    r = csv.DictReader(f, delimiter=';')
    ja_count = sum(1 for row in r if row.get('ja'))
print(f'{ja_count} termes japonais dans le glossaire')
"

# 2. Tester la résolution sémantique
python traducteur.py "歯ぎしり" jafr
# Attendu : bruxisme

# 3. Recherche via search.py
python search.py bases/base100.db "歯ぎしり" --lang ja

# 4. Recherche via server.py
curl "http://localhost:8000/search?q=歯ぎしり&base=base100.db&lang=ja"
```

---

### 11.2 Scénario : Question hybride (mots résolus + non résolus)

```cmd
# Question avec terme inconnu
python search.py bases/base100.db "severe malocclusion with unknown_term" --lang en

# Attendu :
# - "severe" → "sévère"
# - "malocclusion" → "malocclusion"
# - "unknown_term" → conservé tel quel
# - Question hybride : "sévère malocclusion unknown_term"
```

---

### 11.3 Scénario : Traduction puis recherche

```cmd
# 1. Compléter le glossaire pour une nouvelle langue
python traducteur.py refs/glossaire.csv th --deepl -t50

# 2. Relancer le serveur (recharge les dictionnaires)
python server.py

# 3. Tester une recherche en thaï
curl "http://localhost:8000/search?q=...&base=base100.db&lang=th"
```

---

## 12. Checklist de validation

### 12.1 Tests unitaires (Niveau 1)

| Test | Commande | Statut |
|------|----------|--------|
| detadjs CLI | `python detadjs.py "béance" "sévère gauche"` | ☐ |
| dettags CLI | `python dettags.py "béance sévère"` | ☐ |
| detia CLI | `python detia.py "bruxisme" --model gpt-4o-mini` | ☐ |
| detiabrut brut | `python detiabrut.py "bruxisme" brut` | ☐ |
| Compatibilité JSON | Comparer sorties detall/detia | ☐ |

### 12.2 Tests utilitaires (Niveau 2)

| Test | Commande | Statut |
|------|----------|--------|
| traducteur aide | `python traducteur.py -h` | ☐ |
| traducteur phrase | `python traducteur.py "bruxisme" fren` | ☐ |
| traducteur DeepL | `python traducteur.py "bruxisme" fren --deepl` | ☐ |
| lazycommentaires stats | `python lazycommentaires.py stats` | ☐ |

### 12.3 Tests pipeline (Niveau 3)

| Test | Commande | Statut |
|------|----------|--------|
| detall simple | `python detall.py "bruxisme"` | ☐ |
| detall complexe | `python detall.py "liste femmes <30 ans classe II"` | ☐ |
| detall angles | `python detall.py "ANB>4°"` | ☐ |

### 12.4 Tests search (Niveau 4)

| Test | Commande | Statut |
|------|----------|--------|
| search français | `python search.py base100.db "bruxisme"` | ☐ |
| search anglais | `python search.py base100.db "bruxism" --lang en` | ☐ |
| search auto | `python search.py base100.db "bruxism" --lang auto` | ☐ |
| search mode IA | `python search.py base100.db "bruxisme" --mode ia` | ☐ |

### 12.5 Tests server (Niveau 5)

| Test | Méthode | Statut |
|------|---------|--------|
| Démarrage serveur | `python server.py` | ☐ |
| Endpoint /health | curl | ☐ |
| Endpoint /search FR | curl | ☐ |
| Endpoint /search EN | curl | ☐ |
| Endpoint /ia | curl | ☐ |
| Endpoint /i18n | curl | ☐ |
| Endpoint /analyse/stats | curl | ☐ |

### 12.6 Tests interface (Niveau 6)

| Test | Action | Statut |
|------|--------|--------|
| web13 chargement | Ouvrir localhost:8000 | ☐ |
| web13 recherche | Taper "bruxisme" | ☐ |
| web13 changement base | Sélectionner base25000 | ☐ |
| web13 i18n japonais | Sélectionner ja | ☐ |
| web13 zone IA | Poser question | ☐ |
| web13params moteurs | Voir la liste | ☐ |

### 12.7 Tests analytics (Niveau 7)

| Test | Action | Statut |
|------|--------|--------|
| analyse CLI stats | `python analyse.py stats` | ☐ |
| analyse CLI list | `python analyse.py list` | ☐ |
| analyse12 chargement | Ouvrir /analyse | ☐ |
| analyse12 vue résumé | Onglet Résumé | ☐ |
| analyse12 vue cards | Onglet Cards | ☐ |
| analyse12 vue table | Onglet Table | ☐ |
| analyse12 tri colonnes | Clic entête | ☐ |
| analyse12 bouton play | Clic ▶ | ☐ |

### 12.8 Tests outils (Niveau 8)

| Test | Commande | Statut |
|------|----------|--------|
| pipeline quest | `python pipeline.py quest bases/base1000.db 100` | ☐ |
| creefakelog | `python creefakelog.py 300 tests/fr100.csv` | ☐ |

### 12.9 Validation finale

| Critère | Statut |
|---------|--------|
| Aucun fichier syntags.csv/synadjs.csv requis | ☐ |
| Tous les formats JSON compatibles | ☐ |
| Garde-fous actifs (pas d'écrasement) | ☐ |
| Résolution sémantique fonctionnelle | ☐ |
| Performance < 10 secondes | ☐ |
| Logs correctement écrits | ☐ |
| i18n fonctionnel (12 langues) | ☐ |
| Dashboard analytics opérationnel | ☐ |

---

## Annexe : Commandes de diagnostic

```cmd
# Vérifier les fichiers de référence
dir refs\*.csv

# Vérifier l'encodage d'un fichier
python -c "open('refs/glossaire.csv', encoding='utf-8-sig').read()"

# Compter les lignes du glossaire
python -c "print(len(open('refs/glossaire.csv', encoding='utf-8-sig').readlines()))"

# Vérifier les colonnes de tags.csv
python -c "import csv; r=csv.DictReader(open('refs/tags.csv', encoding='utf-8-sig'), delimiter=';'); print(r.fieldnames)"

# Vérifier les logs
type logs\logrecherche.csv | find /c ";"

# Tester une connexion base
python -c "import sqlite3; print(sqlite3.connect('bases/base100.db').execute('SELECT COUNT(*) FROM patients').fetchone())"
```

---

## Annexe : Fichiers de test fournis

### fr100.csv

Fichier de 100 questions multilingues pour les tests.

**Colonnes** : `fr;en;ja;de;es;it;pt;pl;ro;th;ar;cn`

**Exemples** :
```csv
fr;en;ja
patients avec bruxisme ?;patients with bruxism ?;歯ぎしりの患者？
combien de patients avec béance ?;how many patients with open bite ?;開咬の患者は何人？
```

### logrecherche.csv

Fichier de logs de recherche pour le dashboard analytics.

**Colonnes** (22) : `timestamp;session_id;ip_utilisateur;questionoriginale;questiontraduite;question_standardisee;languedetectee;languesaisie;mode;nb_patients;temps_ms;base;criteres_json;auteur;rating;type_probleme;commentaire;...`

---

*Document généré le 04/01/2026 - Projet KITVIEW Orthodontie*
