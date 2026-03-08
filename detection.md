# Documentation Technique : Système de Détection KITVIEW Search V5

<!-- PRESENTATION_META
titre_court: "Architecture de Détection KITVIEW V5"
sous_titre: "Du serveur à la base de données : un pipeline multilingue intelligent"
duree_estimee: "45min"
niveau: "avancé"
audience: "Ingénieurs de haut niveau, architectes logiciel"
fichiers_concernes: "server.py, search.py, trouve.py, detall.py, detia.py, detiabrut.py, jsonsql.py, lancesql.py"
emoji_principal: "🔍"
-->

**Version** : 1.0.0  
**Date** : 18/01/2026  
**Auteur** : Documentation générée pour l'équipe technique  
**Audience** : Ingénieurs de haut niveau, architectes logiciel

---

<!-- NO_SLIDE -->
## Table des matières

1. [Architecture globale](#1-architecture-globale)
2. [Flux de données complet](#2-flux-de-données-complet)
3. [Couche API : server.py](#3-couche-api--serverpy)
4. [Couche Orchestration : search.py](#4-couche-orchestration--searchpy)
5. [Couche Pipeline : trouve.py](#5-couche-pipeline--trouvepy)
6. [Couche Détection Algorithmique : detall.py](#6-couche-détection-algorithmique--detallpy)
7. [Couche Détection IA : detia.py](#7-couche-détection-ia--detiapay)
8. [Mode Configurable : detiabrut.py](#8-mode-configurable--detiabrut)
9. [Modules de Détection Spécialisés](#9-modules-de-détection-spécialisés)
10. [Couches SQL : jsonsql.py et lancesql.py](#10-couches-sql--jsonsqlpy-et-lancesqlpy)
11. [Mécanismes de Protection](#11-mécanismes-de-protection)
12. [Format JSON Unifié](#12-format-json-unifié)
13. [Annexes : Exemples](#annexes--exemples)
<!-- /NO_SLIDE -->

---

<!-- SLIDE
id: "intro-architecture"
titre: "Architecture 6 Couches"
template: "schema"
emoji: "🏗️"
timing: "4min"
transition: "zoom"
-->

## 1. Architecture globale

<!-- KEY: L'architecture KITVIEW V5 sépare strictement les responsabilités en 6 couches : API → Orchestration → Pipeline → Détection → SQL → Exécution -->

<!-- QUESTION: Pourquoi isoler complètement la détection de l'accès base de données ? -->

KITVIEW Search V5 est une application de recherche multilingue permettant d'interroger une base de données orthodontique de 25 000+ patients en langage naturel. L'architecture adopte une approche **6 couches** avec séparation stricte des responsabilités.

<!-- DIAGRAM
type: "architecture"
titre: "Architecture 6 couches KITVIEW Search V5"
legende: "Flux descendant de la requête utilisateur jusqu'à la base SQLite"
-->
```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COUCHE 1 : API (server.py)                          │
│           FastAPI/Uvicorn - Endpoints REST - Sessions - i18n                │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
┌─────────────────────────────────────────▼───────────────────────────────────┐
│                    COUCHE 2 : ORCHESTRATION (search.py)                     │
│      Routage intelligent - Fallback IA/DeepL - Logging - Traduction         │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
┌─────────────────────────────────────────▼───────────────────────────────────┐
│                      COUCHE 3 : PIPELINE (trouve.py)                        │
│            Chargement modules - Coordination détection→SQL                  │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
          ┌───────────────────────────────┼───────────────────────────────┐
          │                               │                               │
┌─────────▼─────────┐         ┌───────────▼───────────┐         ┌─────────▼─────────┐
│ COUCHE 4a         │         │ COUCHE 4b             │         │ COUCHE 4c         │
│ DÉTECTION ALGO    │         │ DÉTECTION IA          │         │ DÉTECTION CONFIG  │
│ (detall.py)       │         │ (detia.py)            │         │ (detiabrut.py)    │
│ Auteur: "cx"      │         │ Auteur: "eden/..."    │         │ Auteur: variable  │
└─────────┬─────────┘         └───────────┬───────────┘         └─────────┬─────────┘
          │                               │                               │
          └───────────────────────────────┼───────────────────────────────┘
                                          │
┌─────────────────────────────────────────▼───────────────────────────────────┐
│                    COUCHE 5 : GÉNÉRATION SQL (jsonsql.py)                   │
│           JSON → Clauses WHERE/JOIN → Requête SQL paramétrée                │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
┌─────────────────────────────────────────▼───────────────────────────────────┐
│                    COUCHE 6 : EXÉCUTION SQL (lancesql.py)                   │
│              SQLite - Requêtes préparées - Formatage résultats              │
└─────────────────────────────────────────┬───────────────────────────────────┘
                                          │
                                          ▼
                                   base{N}.db (SQLite)
```
<!-- /DIAGRAM -->

<!-- SUBSLIDE
titre: "Principes architecturaux"
parent: "intro-architecture"
-->

### Principes architecturaux

<!-- TABLE
titre: "5 principes fondamentaux de l'architecture"
colonnes_cles: "Principe,Description"
style: "compact"
-->

| Principe | Description |
|----------|-------------|
| **Séparation des concerns** | Chaque module a une responsabilité unique |
| **Aucun accès DB dans la détection** | Les modules det*.py ne touchent jamais à SQLite |
| **Format JSON unifié** | Communication inter-modules via structure JSON standardisée |
| **Fallback automatique** | Escalade progressive : Algo → IA → DeepL |
| **Multilingue natif** | 12 langues supportées nativement |

<!-- /TABLE -->

<!-- /SUBSLIDE -->

---

<!-- SLIDE
id: "flux-donnees"
titre: "Flux de données complet"
template: "schema"
emoji: "🔄"
timing: "4min"
transition: "slide"
-->

## 2. Flux de données complet

<!-- KEY: Une question traverse 7 étapes : API → Détection langue → Traduction → Détection critères → SQL → Exécution → Traduction résultats -->

### Diagramme de séquence simplifié

<!-- DIAGRAM
type: "sequence"
titre: "Séquence d'une recherche multilingue"
legende: "Exemple : question en allemand 'Tiefbiss bei Frauen über 30 Jahre'"
-->
```
Utilisateur          server.py       search.py       trouve.py       detall/ia       jsonsql       lancesql
     │                   │               │               │               │               │             │
     │ POST /search      │               │               │               │               │             │
     │   {question,      │               │               │               │               │             │
     │    lang, mode}    │               │               │               │               │             │
     │──────────────────>│               │               │               │               │             │
     │                   │ search()      │               │               │               │             │
     │                   │──────────────>│               │               │               │             │
     │                   │               │ détect lang   │               │               │             │
     │                   │               │ traduit→FR    │               │               │             │
     │                   │               │               │               │               │             │
     │                   │               │ rechercher()  │               │               │             │
     │                   │               │──────────────>│               │               │             │
     │                   │               │               │ detecter_tout()               │             │
     │                   │               │               │──────────────>│               │             │
     │                   │               │               │               │ JSON critères │             │
     │                   │               │               │<──────────────│               │             │
     │                   │               │               │               │               │             │
     │                   │               │               │ generer_sql() │               │             │
     │                   │               │               │──────────────────────────────>│             │
     │                   │               │               │               │ SQL + params  │             │
     │                   │               │               │<──────────────────────────────│             │
     │                   │               │               │               │               │             │
     │                   │               │               │ executer_sql()│               │             │
     │                   │               │               │────────────────────────────────────────────>│
     │                   │               │               │               │               │  résultats  │
     │                   │               │               │<────────────────────────────────────────────│
     │                   │               │               │               │               │             │
     │                   │               │   résultats + │               │               │             │
     │                   │               │   traduction  │               │               │             │
     │                   │<──────────────│<──────────────│               │               │             │
     │   JSON réponse    │               │               │               │               │             │
     │<──────────────────│               │               │               │               │             │
```
<!-- /DIAGRAM -->

<!-- SUBSLIDE
titre: "Exemple concret de transformation"
parent: "flux-donnees"
-->

### Exemple concret de transformation

**Question utilisateur** (allemand) : `"Tiefbiss bei Frauen über 30 Jahre"`

<!-- TABLE
titre: "Transformation étape par étape"
colonnes_cles: "Étape,Module,Sortie"
style: "large"
-->

| Étape | Module | Entrée | Sortie |
|-------|--------|--------|--------|
| 1 | server.py | Question brute | Appel search() avec lang="de" |
| 2 | search.py | Question DE | `supraclusion femmes plus de 30 ans` (FR) |
| 3 | trouve.py | Question FR | Appel module détection |
| 4 | detall.py | Question FR | JSON avec critères structurés |
| 5 | jsonsql.py | JSON critères | `SELECT ... WHERE sexe='F' AND age > 30 JOIN...` |
| 6 | lancesql.py | SQL | Liste de 127 patients |
| 7 | search.py | Résultats FR | Traduction labels → DE |

<!-- /TABLE -->

<!-- /SUBSLIDE -->

---

<!-- SLIDE
id: "couche-api"
titre: "Couche API : server.py"
template: "2colonnes"
emoji: "🌐"
timing: "3min"
transition: "slide"
-->

## 3. Couche API : server.py

<!-- KEY: server.py est le point d'entrée unique - FastAPI expose 20+ endpoints REST avec gestion sessions, i18n et enrichissement des résultats -->

**Version** : 1.0.50 | **Framework** : FastAPI + Uvicorn

### Responsabilités

- Exposition des endpoints REST
- Gestion des sessions et authentification
- Routage vers search.py
- Enrichissement des résultats (portraits, commentaires)
- Internationalisation (i18n)

### Endpoints principaux

<!-- TABLE
titre: "Endpoints REST principaux"
colonnes_cles: "Endpoint,Description"
style: "compact"
-->

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/search` | POST | Recherche patients (point d'entrée principal) |
| `/ia` | GET | Liste des moteurs IA disponibles |
| `/ia/{moteur}` | PUT | Activer/désactiver un moteur |
| `/ia/ask` | POST | Interroger un LLM avec contexte |
| `/ia/cohorte` | POST | Analyse de cohorte par IA |
| `/params` | GET | Paramètres (langues actives) |
| `/i18n` | GET | Textes UI traduits |

<!-- /TABLE -->

### Structure de la requête `/search`

<!-- CODE
langage: "json"
titre: "Payload de requête /search"
executable: "false"
-->
```json
{
  "question": "bruxisme sévère",
  "base": "base100.db",
  "lang": "fr",
  "response_lang": "fr",
  "mode": "standard",
  "model": null,
  "session_id": "abc123"
}
```
<!-- /CODE -->

---

<!-- SLIDE
id: "couche-orchestration"
titre: "Couche Orchestration : search.py"
template: "schema"
emoji: "🎯"
timing: "4min"
transition: "slide"
-->

## 4. Couche Orchestration : search.py

<!-- KEY: search.py implémente le routage intelligent avec fallback automatique : Standard → IA 🤖 → DeepL 🌐 -->

<!-- QUESTION: Quand faut-il utiliser le mode 'purstandard' plutôt que 'standard' ? -->

**Version** : 1.0.28 | **Rôle** : Routage intelligent et traduction

### Modes de détection

<!-- TABLE
titre: "4 modes de détection disponibles"
colonnes_cles: "Mode,Auteur"
style: "compact"
-->

| Mode | Description | Auteur |
|------|-------------|--------|
| `standard` | Détection algorithmique (detall.py) avec fallback IA | cx ou cx→eden |
| `ia` | Détection IA forcée (detia.py) | eden/... |
| `purstandard` | Algorithmique pur, sans fallback | cx |
| `puria` | IA pure, sans fallback | eden/... |

<!-- /TABLE -->

### Mécanisme de fallback

<!-- DIAGRAM
type: "flux"
titre: "Escalade automatique en cas d'échec"
legende: "🤖 = Fallback IA | 🌐 = Traduction DeepL"
-->
```
Question → Standard (detall.py)
              │
              ├─ Résultats > 0 → Retour ✓
              │
              └─ Résultats = 0
                    │
                    ▼
              Fallback IA (detia.py) 🤖
                    │
                    ├─ Résultats > 0 → Retour ✓
                    │
                    └─ Résultats = 0
                          │
                          ▼
                    Traduction DeepL 🌐
                    + Nouvelle recherche
```
<!-- /DIAGRAM -->

<!-- SUBSLIDE
titre: "Indicateurs de routage"
parent: "couche-orchestration"
-->

### Indicateurs de routage

Le champ `parcours_detection` trace le chemin emprunté :

- `"standard"` : Résultat direct
- `"standard→ia"` : Fallback IA utilisé
- `"standard→ia→deepl→ia"` : Traduction après échec IA
- `"ia→deepl→ia"` : Mode IA forcé avec traduction

<!-- /SUBSLIDE -->

---

<!-- SLIDE
id: "couche-pipeline"
titre: "Couche Pipeline : trouve.py"
template: "code"
emoji: "⚙️"
timing: "3min"
transition: "slide"
-->

## 5. Couche Pipeline : trouve.py

<!-- KEY: trouve.py coordonne le pipeline complet : Détection → JSON → SQL → Exécution → Garde-fou -->

**Version** : 1.0.18 | **Rôle** : Coordination détection → SQL → exécution

### Fonction principale : `rechercher()`

<!-- CODE
langage: "python"
titre: "Signature de la fonction rechercher()"
executable: "false"
-->
```python
def rechercher(
    question: str,
    db_path: Path,
    mode: str = "standard",      # standard | ia
    model: str = None,           # gpt4o, sonnet, etc.
    references: dict = None,     # Cache des référentiels
    include_details: bool = True,
    verbose: bool = False
) -> dict
```
<!-- /CODE -->

### Pipeline interne

1. **Chargement module** : Sélection dynamique de detall.py ou detia.py
2. **Détection** : Appel `detecter_tout()` → JSON critères
3. **Génération SQL** : jsonsql.py
4. **Exécution** : lancesql.py
5. **Garde-fou** : Vérification si trop de résultats sans critères
6. **Formatage** : Construction réponse finale

### Garde-fou intégré

Quand aucun critère de filtrage n'est détecté et que le nombre de résultats dépasse 100, le garde-fou est activé (voir section 11).

---

<!-- SLIDE
id: "detection-algo"
titre: "Détection Algorithmique : detall.py"
template: "schema"
emoji: "🔧"
timing: "5min"
transition: "zoom"
-->

## 6. Couche Détection Algorithmique : detall.py

<!-- KEY: detall.py orchestre 5 modules spécialisés dans un ordre précis : detcount → detangles → dettags → detage → motsvides -->

<!-- QUESTION: Pourquoi detangles est-il appelé AVANT dettags ? -->

**Version** : 1.0.7 | **Auteur** : `cx`

### Architecture interne

detall.py est un **orchestrateur** qui chaîne les modules de détection spécialisés dans un ordre précis :

<!-- DIAGRAM
type: "flux"
titre: "Pipeline de détection algorithmique"
legende: "Chaque étape consomme une partie de la question et passe le résidu à l'étape suivante"
-->
```
Question standardisée
         │
         ▼
┌─────────────────────┐
│ ÉTAPE 1: detcount   │  Détection LIST/COUNT
│ "combien de..."     │  → listcount = COUNT|LIST
└─────────┬───────────┘
          │ résidu
          ▼
┌─────────────────────┐
│ ÉTAPE 2: detangles  │  Angles céphalométriques
│ "ANB > 4"           │  → critère type "tag"
└─────────┬───────────┘
          │ résidu
          ▼
┌─────────────────────┐
│ ÉTAPE 3: dettags    │  Tags orthodontiques
│ "béance gauche"     │  + adjectifs (via detadjs)
└─────────┬───────────┘
          │ résidu
          ▼
┌─────────────────────┐
│ ÉTAPE 4: detage     │  Âge et sexe
│ "femme de 30 ans"   │  → critères age/sexe
└─────────┬───────────┘
          │ résidu
          ▼
┌─────────────────────┐
│ ÉTAPE 5: motsvides  │  Nettoyage final
│ "les, de, avec..."  │  → résidu minimal
└─────────┴───────────┘
```
<!-- /DIAGRAM -->

<!-- SUBSLIDE
titre: "Chargement des références"
parent: "detection-algo"
-->

### Chargement des références

<!-- CODE
langage: "python"
titre: "Structure retournée par charger_references()"
executable: "false"
-->
```python
def charger_references(verbose=False, debug=False) -> dict:
    """
    Retourne:
        {
            'patterns_count': [...],   # depuis commun.csv
            'patterns_angles': [...],  # depuis angles.csv
            'tags_data': {...},        # depuis tags.csv
            'adjs_data': {...},        # depuis adjectifs.csv
            'patterns_ages': [...]     # depuis ages.csv
        }
    """
```
<!-- /CODE -->

### Fichiers de référence

<!-- TABLE
titre: "5 fichiers CSV de référence"
colonnes_cles: "Fichier,Colonnes principales"
style: "compact"
-->

| Fichier | Description | Colonnes principales |
|---------|-------------|---------------------|
| `commun.csv` | Mots COUNT/LIST | combien;devant;langues |
| `angles.csv` | Seuils céphalométriques | expression;operateur;seuil;tag_canonique |
| `tags.csv` | Pathologies | t;gn;as;pts |
| `adjectifs.csv` | Adjectifs | a;f;mp;fp;pas |
| `ages.csv` | Patterns âge/sexe | expression;operateur;valeur_sql;sexe;label |

<!-- /TABLE -->

<!-- /SUBSLIDE -->

---

<!-- SLIDE
id: "detection-ia"
titre: "Détection IA : detia.py"
template: "2colonnes"
emoji: "🤖"
timing: "5min"
transition: "slide"
-->

## 7. Couche Détection IA : detia.py

<!-- KEY: detia.py utilise un LLM avec prompt enrichi des référentiels - plus flexible mais 100x plus lent et payant -->

**Version** : 1.0.29 | **Auteur** : `eden/{model}` ou `openai/{model}`

### Différences avec detall.py

<!-- TABLE
titre: "Comparaison Algorithmique vs IA"
colonnes_cles: "Aspect,detall.py,detia.py"
style: "large"
-->

| Aspect | detall.py | detia.py |
|--------|-----------|----------|
| Méthode | Pattern matching regex | LLM (GPT-4, Claude) |
| Latence | ~5-20ms | ~500-2000ms |
| Flexibilité | Limitée aux patterns | Comprend le contexte |
| Coût | Gratuit | Payant (API) |
| Auteur | "cx" | "eden/gpt-4o", etc. |

<!-- /TABLE -->

### Moteurs IA supportés (ia.csv)

<!-- TABLE
titre: "Moteurs IA configurés"
colonnes_cles: "Moteur,Modèle"
style: "compact"
-->

| Moteur | Via | Modèle complet |
|--------|-----|----------------|
| gpt41mini | openai | gpt-4.1-mini |
| gpt4o | openai | gpt-4o |
| sonnet | eden | anthropic/claude-3-7-sonnet |

<!-- /TABLE -->

<!-- SUBSLIDE
titre: "Construction du prompt système"
parent: "detection-ia"
-->

### Construction du prompt système

Le prompt est construit dynamiquement avec injection des référentiels :

<!-- CODE
langage: "python"
titre: "Sections injectées dans le prompt"
executable: "false"
-->
```python
def _construire_prompt_systeme(references: dict) -> str:
    """
    Sections injectées:
    - Liste des tags (~100 pathologies)
    - Synonymes importants (tong-e → dysfonction linguale)
    - Liste des adjectifs
    - Table des angles céphalométriques
    - Règles d'âge et sexe
    - Format JSON attendu
    """
```
<!-- /CODE -->

**Extrait du prompt** :

```
=== MISSION ===
1. Détecter les TAGS (pathologies) de la liste ci-dessous
2. Détecter les ADJECTIFS qualifiant ces tags
3. Détecter les critères d'ÂGE et de SEXE
4. Détecter les demandes de COMPTAGE
5. Détecter les ANGLES céphalométriques

=== ANGLES CÉPHALOMÉTRIQUES ===
| Angle | Condition | Valeur | Tag résultant |
| ANB   | >         | 4      | classe ii squelettique |
...
```

<!-- /SUBSLIDE -->

<!-- SUBSLIDE
titre: "Post-traitement : mapping canonique"
parent: "detection-ia"
-->

### Post-traitement : mapping vers canonique

Après réponse de l'IA, `_mapper_vers_canonique()` normalise les termes détectés :

<!-- CODE
langage: "python"
titre: "Exemple de mapping"
executable: "false"
-->
```python
# IA retourne: {"detecte": "grincement"}
# Mapping: grincement → bruxisme
# Résultat: {"canonique": "bruxisme"}
```
<!-- /CODE -->

<!-- /SUBSLIDE -->

---

<!-- SLIDE
id: "detection-config"
titre: "Mode Configurable : detiabrut.py"
template: "code"
emoji: "🎛️"
timing: "3min"
transition: "slide"
-->

## 8. Mode Configurable : detiabrut.py

<!-- KEY: detiabrut.py permet d'activer/désactiver sélectivement les référentiels pour mesurer leur impact sur la qualité -->

**Version** : 1.0.3 | **Rôle** : Mesure d'impact des référentiels

### Objectif

Permettre l'activation/désactivation sélective des référentiels pour mesurer leur importance dans la qualité des résultats.

### Référentiels configurables

<!-- TABLE
titre: "5 référentiels configurables"
colonnes_cles: "Référentiel,Impact"
style: "compact"
-->

| Référentiel | Description | Impact |
|-------------|-------------|--------|
| `tags` | Liste des tags dans le prompt | Reconnaissance pathologies |
| `adjs` | Liste des adjectifs | Qualificatifs |
| `ages` | Patterns âge/sexe | Critères démographiques |
| `angles` | Seuils ANB/SNA/SNB | Céphalométrie |
| `mapping` | Post-traitement → canonique | Normalisation |

<!-- /TABLE -->

### Syntaxe CLI

<!-- CODE
langage: "bash"
titre: "Exemples d'utilisation CLI"
executable: "false"
-->
```bash
# Tout actif (équivalent detia.py)
python detiabrut.py "bruxisme sévère" all

# Tout désactivé (IA brute)
python detiabrut.py "bruxisme sévère" none

# Sans liste de tags
python detiabrut.py "grincement" -tags

# Brut sauf mapping
python detiabrut.py "bruxisme" none +mapping
```
<!-- /CODE -->

### Signature de l'auteur

Le champ `auteur` reflète la configuration :

- `"openai/gpt-4o"` → Mode all (tout activé)
- `"openai/gpt-4o [none]"` → Mode none
- `"openai/gpt-4o [-tags,-mapping]"` → Tags et mapping désactivés

---

<!-- SLIDE
id: "modules-specialises"
titre: "Modules de Détection Spécialisés"
template: "titre-section"
emoji: "🔬"
timing: "1min"
transition: "zoom"
-->

## 9. Modules de Détection Spécialisés

<!-- KEY: 5 modules spécialisés traitent chacun un type de critère : count, angles, tags+adjectifs, âge/sexe -->

---

<!-- SLIDE
id: "detcount"
titre: "detcount.py - Détection LIST/COUNT"
template: "code"
emoji: "🔢"
timing: "2min"
transition: "slide"
-->

### 9.1 detcount.py - Détection LIST/COUNT

**Entrée** : Question standardisée  
**Sortie** : `{listcount: "COUNT"|"LIST", residu: "..."}`

Mots déclencheurs (depuis commun.csv) :
- FR : combien, nombre de, quantité
- EN : how many, count
- DE : wie viele, anzahl

---

<!-- SLIDE
id: "detangles"
titre: "detangles.py - Angles céphalométriques"
template: "tableau"
emoji: "📐"
timing: "4min"
transition: "slide"
-->

### 9.2 detangles.py - Angles céphalométriques

<!-- KEY: Les angles ANB/SNA/SNB sont convertis en tags pathologiques selon des seuils cliniques standardisés -->

**Entrée** : Résidu après detcount  
**Sortie** : Critères de type "tag" correspondant aux classifications

#### Seuils cliniques codés en dur

<!-- CODE
langage: "python"
titre: "Seuils cliniques ANB/SNA/SNB"
executable: "false"
-->
```python
SEUILS_CLINIQUES = {
    'anb': {
        'classifications': [
            {'condition': lambda v: v < 2, 'tag': 'classe iii squelettique'},
            {'condition': lambda v: 2 <= v <= 4, 'tag': 'classe i squelettique'},
            {'condition': lambda v: v > 4, 'tag': 'classe ii squelettique'},
        ]
    },
    'sna': { ... },  # 80-86° normal
    'snb': { ... },  # 77-83° normal
}
```
<!-- /CODE -->

#### Exemple de transformation

<!-- TABLE
titre: "Conversion angle → tag pathologique"
colonnes_cles: "Entrée,Sortie"
style: "compact"
-->

| Entrée | Évaluation | Sortie |
|--------|------------|--------|
| "ANB = 0" | 0 < 2 | classe iii squelettique |
| "ANB > 5" | 5 > 4 | classe ii squelettique |
| "SNA de 84" | 80 ≤ 84 ≤ 86 | maxillaire normopositionné |

<!-- /TABLE -->

---

<!-- SLIDE
id: "dettags"
titre: "dettags.py - Tags orthodontiques"
template: "schema"
emoji: "🏷️"
timing: "3min"
transition: "slide"
-->

### 9.3 dettags.py - Tags orthodontiques

<!-- KEY: dettags détecte les tags puis appelle detadjs pour trouver les adjectifs dans une fenêtre de 5 mots -->

**Entrée** : Résidu après detangles  
**Sortie** : Critères de type "tag" avec adjectifs

#### Algorithme de détection

1. **Lookup trié** par nombre de mots décroissant (expressions longues d'abord)
2. **Recherche exacte** dans la question standardisée
3. **Appel detadjs** pour chaque tag trouvé
4. **Retrait du résidu** des mots matchés

#### Gestion du genre

Chaque tag a un genre (m/f/mp/fp) utilisé pour accorder les adjectifs :

```
Tag: béance (f)
Adjectif: antérieur → antérieure (forme féminine)
```

---

<!-- SLIDE
id: "detadjs"
titre: "detadjs.py - Adjectifs qualificatifs"
template: "schema"
emoji: "📝"
timing: "2min"
transition: "slide"
-->

### 9.4 detadjs.py - Adjectifs qualificatifs

**Entrée** : Tag détecté + position + question  
**Sortie** : Liste d'adjectifs avec formes accordées

#### Fenêtre de proximité

Les adjectifs sont recherchés dans une fenêtre de **5 mots** autour du tag :

<!-- DIAGRAM
type: "flux"
titre: "Fenêtre de recherche des adjectifs"
-->
```
"patients avec béance [←────5────→] sévère gauche de moins de 30 ans"
                      ─────▲─────
                   Fenêtre de recherche
```
<!-- /DIAGRAM -->

---

<!-- SLIDE
id: "detage"
titre: "detage.py - Âge et sexe"
template: "tableau"
emoji: "👤"
timing: "3min"
transition: "slide"
-->

### 9.5 detage.py - Âge et sexe

**Entrée** : Résidu après dettags  
**Sortie** : Critères de type "age" et "sexe"

#### Patterns supportés

<!-- TABLE
titre: "Patterns d'âge reconnus"
colonnes_cles: "Pattern,Opérateur,Exemple"
style: "large"
-->

| Pattern | Opérateur | Exemple |
|---------|-----------|---------|
| `{n} ans` | = | "14 ans" → age = 14 |
| `moins de {n} ans` | < | "moins de 30 ans" → age < 30 |
| `plus de {n} ans` | > | "plus de 18 ans" → age > 18 |
| `entre {n} et {n} ans` | BETWEEN | → age BETWEEN 10 AND 15 |
| `femme/fille/patiente` | = | → sexe = 'F' |
| `homme/garçon/patient` | = | → sexe = 'M' |

<!-- /TABLE -->

---

<!-- SLIDE
id: "couches-sql"
titre: "Couches SQL : jsonsql.py et lancesql.py"
template: "2colonnes"
emoji: "💾"
timing: "4min"
transition: "slide"
-->

## 10. Couches SQL : jsonsql.py et lancesql.py

<!-- KEY: jsonsql transforme les critères JSON en SQL paramétré, lancesql exécute et formate les résultats -->

### 10.1 jsonsql.py - Génération SQL

**Entrée** : JSON unifié des critères  
**Sortie** : Requête SQL paramétrée

#### Stratégie de génération

<!-- TABLE
titre: "Stratégie SQL par type de critère"
colonnes_cles: "Type,Stratégie"
style: "compact"
-->

| Type critère | Stratégie SQL |
|--------------|---------------|
| tag | JOIN pathologies + patients_pathologies |
| tag + adjectifs | Pathologie composée (tag + adjs triés alphabétiquement) |
| sexe | WHERE sur colonne patients.sexe |
| age | WHERE sur colonne patients.age |

<!-- /TABLE -->

<!-- SUBSLIDE
titre: "Exemple de transformation JSON → SQL"
parent: "couches-sql"
-->

#### Exemple de transformation

**Entrée JSON** :

<!-- CODE
langage: "json"
titre: "JSON de critères"
executable: "false"
-->
```json
{
  "criteres": [
    {"type": "tag", "canonique": "béance", "adjectifs": [{"forme_accordee": "antérieure"}]},
    {"type": "sexe", "sql": {"valeur": "F"}},
    {"type": "age", "sql": {"operateur": "<", "valeur": 30}}
  ]
}
```
<!-- /CODE -->

**SQL généré** :

<!-- CODE
langage: "sql"
titre: "Requête SQL générée"
executable: "false"
-->
```sql
SELECT DISTINCT p.id, p.prenom, p.nom, p.sexe, p.age, p.idportrait, p.oripathologies
FROM patients p
    JOIN patients_pathologies pp1 ON p.id = pp1.patient_id
    JOIN pathologies pa1 ON pp1.pathologie_id = pa1.id
WHERE pa1.pathologie = ?
  AND p.sexe = ?
  AND p.age < ?
ORDER BY p.id

-- Params: ['beance anterieure', 'F', 30]
```
<!-- /CODE -->

<!-- /SUBSLIDE -->

<!-- SUBSLIDE
titre: "lancesql.py - Exécution SQL"
parent: "couches-sql"
-->

### 10.2 lancesql.py - Exécution SQL

**Version** : 1.0.4 | **Entrée** : SQL + params + chemin base  
**Sortie** : Résultats formatés

#### Structure de sortie

<!-- CODE
langage: "python"
titre: "Format de sortie lancesql"
executable: "false"
-->
```python
{
    "nb": 42,                    # Nombre de résultats
    "ids": [1, 5, 12, ...],      # Liste des IDs (si LIST)
    "patients": [                # Détails patients
        {
            "id": 1,
            "prenom": "Marie",
            "nom": "Dupont",
            "sexe": "F",
            "age": 25.3,
            "oripathologies": "Béance antérieure, Bruxisme"
        },
        ...
    ],
    "temps_ms": 12.5,            # Temps d'exécution
    "sql_execute": "SELECT ..."  # SQL exécuté (debug)
}
```
<!-- /CODE -->

<!-- /SUBSLIDE -->

---

<!-- SLIDE
id: "protections"
titre: "Mécanismes de Protection"
template: "titre-section"
emoji: "🛡️"
timing: "1min"
transition: "zoom"
-->

## 11. Mécanismes de Protection

<!-- KEY: 3 niveaux de protection : garde-fou anti-saturation, normalisation des entrées, filtrage des mots vides -->

---

<!-- SLIDE
id: "gardefou"
titre: "gardefou.py - Protection anti-saturation"
template: "schema"
emoji: "🚧"
timing: "3min"
transition: "slide"
-->

### 11.1 gardefou.py - Protection anti-saturation

<!-- KEY: Le garde-fou empêche de retourner tous les patients quand la détection échoue, sauf si l'utilisateur le demande explicitement -->

**Problème résolu** : Quand la détection échoue (critères vides), le système retournait TOUS les patients.

#### Logique de vérification

<!-- DIAGRAM
type: "flux"
titre: "Arbre de décision du garde-fou"
-->
```
Question sans critères détectés
              │
              ▼
┌─────────────────────────────────┐
│ 1. Mots explicites "tous" ?    │
│    tous, all, alle, tutti...   │
└─────────────┬───────────────────┘
              │
         ┌────┴────┐
         │ OUI     │ NON
         ▼         ▼
   ┌─────────┐  ┌─────────────────────────┐
   │ OK      │  │ 2. Ressemble pathologie?│
   │ Retour  │  │    (préfixe dans tags)  │
   └─────────┘  └───────────┬─────────────┘
                            │
                       ┌────┴────┐
                       │ OUI     │ NON
                       ▼         ▼
                 ┌──────────┐  ┌──────────┐
                 │ Suggérer │  │ Bloquer  │
                 │ tags     │  │ + message│
                 └──────────┘  └──────────┘
```
<!-- /DIAGRAM -->

#### Mots déclencheurs "tous"

<!-- CODE
langage: "python"
titre: "Mots indiquant l'intention 'tous les patients'"
executable: "false"
-->
```python
MOTS_INTENTION_TOUS = {
    'tous', 'tout', 'toutes', 'tous les patients',
    'all', 'everyone', 'all patients',
    'alle', 'alle patienten',
    'todos', 'todas',
    'tutti', 'tutte',
}
```
<!-- /CODE -->

---

<!-- SLIDE
id: "standardise"
titre: "standardise.py - Normalisation"
template: "code"
emoji: "🔤"
timing: "2min"
transition: "slide"
-->

### 11.2 standardise.py - Normalisation

**Version** : 1.0.2 | Fonction de normalisation appliquée à toutes les entrées

<!-- CODE
langage: "python"
titre: "Fonction de standardisation"
executable: "false"
-->
```python
def standardise(texte):
    """
    Standardise un texte pour la recherche.
    
    Returns:
        Texte standardisé (minuscules, sans accents, sans ponctuation)
    """
    if texte is None or texte == "":
        return ""
    
    # Minuscules
    texte = texte.lower()
    
    # Supprimer les accents
    texte = unicodedata.normalize('NFD', texte)
    texte = ''.join(char for char in texte if unicodedata.category(char) != 'Mn')
    
    # Supprimer la ponctuation (SAUF {} qui sont des placeholders techniques)
    for char in ".!-_?',;:\"()[]":
        texte = texte.replace(char, " ")
    
    # Normaliser les espaces
    texte = re.sub(r'\s+', ' ', texte)
    
    return texte.strip()
```
<!-- /CODE -->

#### Exemples de transformation

<!-- TABLE
titre: "Exemples de standardisation"
colonnes_cles: "Entrée,Sortie"
style: "compact"
-->

| Entrée | Sortie |
|--------|--------|
| `"Béance antérieure"` | `"beance anterieure"` |
| `"Classe II d'Angle"` | `"classe ii d angle"` |
| `"  Multiple   espaces  "` | `"multiple espaces"` |
| `"àéïôù"` | `"aeiou"` |

<!-- /TABLE -->

---

<!-- SLIDE
id: "motsvides"
titre: "motsvides.py - Filtrage stopwords"
template: "code"
emoji: "🗑️"
timing: "2min"
transition: "slide"
-->

### 11.3 motsvides.py - Filtrage stopwords

**Version** : 1.0.2 | Suppression des mots non significatifs du résidu

#### Liste des mots vides

<!-- CODE
langage: "python"
titre: "Extrait de la liste des mots vides"
executable: "false"
-->
```python
MOTS_VIDES = {
    # Articles
    'le', 'la', 'les', 'un', 'une', 'des', 'du', 'de', 'l',
    # Prépositions
    'a', 'au', 'aux', 'avec', 'dans', 'en', 'pour', 'par', 'sur', 'sous',
    # Conjonctions
    'et', 'ou', 'mais', 'donc', 'car', 'ni', 'que', 'qui', 'quoi',
    # Mots spécifiques au domaine
    'patient', 'patients', 'patiente', 'patientes',
    'ans', 'an', 'annee', 'annees',
}
```
<!-- /CODE -->

#### Exemples

<!-- TABLE
titre: "Exemples de filtrage"
colonnes_cles: "Entrée,Sortie"
style: "compact"
-->

| Entrée | Sortie |
|--------|--------|
| `"les patients avec une beance"` | `"beance"` |
| `"quels sont les patients de moins de 30 ans"` | `"30"` |
| `"combien de femmes avec bruxisme"` | `"femmes bruxisme"` |

<!-- /TABLE -->

---

<!-- SLIDE
id: "format-json"
titre: "Format JSON Unifié"
template: "code"
emoji: "📋"
timing: "3min"
transition: "slide"
-->

## 12. Format JSON Unifié

<!-- KEY: Tous les modules de détection produisent le même format JSON avec auteur, listcount, critères et résidu -->

Tous les modules de détection produisent le même format JSON :

<!-- CODE
langage: "json"
titre: "Structure JSON unifiée"
executable: "false"
-->
```json
{
    "auteur": "cx",
    "langue": "fr",
    "listcount": "LIST",
    "criteres": [
        {
            "type": "tag",
            "detecte": "beance anterieure",
            "canonique": "béance",
            "label": "Béance",
            "gn": "f",
            "sql": {
                "colonne": "canontags",
                "operateur": "=",
                "valeur": "béance"
            },
            "adjectifs": [
                {
                    "detecte": "anterieure",
                    "canonique": "antérieur",
                    "forme_accordee": "antérieure"
                }
            ]
        },
        {
            "type": "sexe",
            "detecte": "femme",
            "label": "Féminin",
            "sql": {"colonne": "sexe", "operateur": "=", "valeur": "F"}
        },
        {
            "type": "age",
            "detecte": "moins de 30 ans",
            "label": "Moins de 30 ans",
            "sql": {"colonne": "age", "operateur": "<", "valeur": 30}
        }
    ],
    "residu": "",
    "question_originale": "femmes avec béance antérieure de moins de 30 ans"
}
```
<!-- /CODE -->

### Types de critères

<!-- TABLE
titre: "4 types de critères"
colonnes_cles: "Type,Champs spécifiques"
style: "compact"
-->

| Type | Description | Champs spécifiques |
|------|-------------|-------------------|
| `count` | Indicateur comptage | detecte, label |
| `tag` | Pathologie/caractéristique | canonique, gn, adjectifs, sql |
| `age` | Critère d'âge | operateur, valeur, (valeur2 pour BETWEEN) |
| `sexe` | Critère de sexe | valeur (M/F) |

<!-- /TABLE -->

---

<!-- SLIDE
id: "annexes"
titre: "Annexes : Exemples"
template: "titre-section"
emoji: "📎"
timing: "1min"
transition: "zoom"
-->

## Annexes : Exemples

---

<!-- SLIDE
id: "exemple-simple"
titre: "Exemple 1 : Question simple"
template: "tableau"
emoji: "1️⃣"
timing: "3min"
transition: "slide"
-->

### Annexe A : Exemples de détection detall.py

**Exemple 1 : Question simple**

```
Entrée : "combien de patients avec bruxisme"
```

<!-- TABLE
titre: "Trace de détection étape par étape"
colonnes_cles: "Étape,Module,Détection,Résidu"
style: "large"
-->

| Étape | Module | Détection | Résidu |
|-------|--------|-----------|--------|
| 1 | detcount | listcount=COUNT, "combien" | "de patients avec bruxisme" |
| 2 | detangles | (aucun) | "de patients avec bruxisme" |
| 3 | dettags | tag="bruxisme" | "de patients avec" |
| 4 | detage | (aucun) | "de patients avec" |
| 5 | motsvides | - | "" |

<!-- /TABLE -->

**JSON produit** :

<!-- CODE
langage: "json"
titre: "Résultat JSON"
executable: "false"
-->
```json
{
    "auteur": "cx",
    "listcount": "COUNT",
    "criteres": [
        {"type": "count", "detecte": "combien", "label": "Comptage demandé"},
        {"type": "tag", "detecte": "bruxisme", "canonique": "bruxisme"}
    ],
    "residu": ""
}
```
<!-- /CODE -->

---

<!-- SLIDE
id: "exemple-complexe"
titre: "Exemple 2 : Question complexe"
template: "tableau"
emoji: "2️⃣"
timing: "3min"
transition: "slide"
-->

**Exemple 2 : Question complexe avec angle**

```
Entrée : "femmes de plus de 25 ans avec ANB > 5 et béance latérale gauche"
```

<!-- TABLE
titre: "Trace de détection"
colonnes_cles: "Étape,Module,Détection"
style: "compact"
-->

| Étape | Module | Détection |
|-------|--------|-----------|
| 1 | detcount | listcount=LIST |
| 2 | detangles | ANB > 5 → classe ii squelettique |
| 3 | dettags | béance + [latéral, gauche] |
| 4 | detage | sexe=F, age > 25 |

<!-- /TABLE -->

**JSON produit** :

<!-- CODE
langage: "json"
titre: "Résultat JSON avec 4 critères"
executable: "false"
-->
```json
{
    "auteur": "cx",
    "listcount": "LIST",
    "criteres": [
        {
            "type": "tag",
            "detecte": "anb > 5",
            "canonique": "classe ii squelettique",
            "source": "angle"
        },
        {
            "type": "tag",
            "detecte": "beance laterale gauche",
            "canonique": "béance",
            "adjectifs": [
                {"canonique": "latéral", "forme_accordee": "latérale"},
                {"canonique": "gauche", "forme_accordee": "gauche"}
            ]
        },
        {"type": "sexe", "sql": {"valeur": "F"}},
        {"type": "age", "sql": {"operateur": ">", "valeur": 25}}
    ]
}
```
<!-- /CODE -->

---

<!-- SLIDE
id: "comparaison-algo-ia"
titre: "Comparaison detall vs detia"
template: "tableau"
emoji: "⚖️"
timing: "3min"
transition: "slide"
-->

### Annexe B : Comparaison detall vs detia

<!-- KEY: detia.py produit un résidu plus propre mais est 100x plus lent et coûte de l'argent -->

**Question test** : "grincement des dents nocturne chez les adolescents"

<!-- TABLE
titre: "Comparaison des résultats"
colonnes_cles: "Aspect,detall.py,detia.py"
style: "large"
-->

| Aspect | detall.py | detia.py |
|--------|-----------|----------|
| Temps | 8ms | 1250ms |
| Auteur | cx | openai/gpt-4o |
| Tag détecté | bruxisme (via pattern "grincement") | bruxisme |
| Adjectif | nocturne | nocturne |
| Âge | adolescents → BETWEEN 12, 18 | BETWEEN 12, 18 |
| Résidu | "des dents chez les" | "" |

<!-- /TABLE -->

**Observation** : detia.py produit un résidu plus propre car l'IA comprend le contexte complet.

---

<!-- SLIDE
id: "trace-execution"
titre: "Trace d'exécution CLI"
template: "code"
emoji: "🖥️"
timing: "2min"
transition: "slide"
-->

### Annexe C : Trace d'exécution avec parcours

<!-- CODE
langage: "bash"
titre: "Commande CLI"
executable: "false"
-->
```bash
$ python search.py base100.db "grincement" --mode=standard -v
```
<!-- /CODE -->

<!-- CODE
langage: "text"
titre: "Sortie console"
executable: "false"
-->
```
╔════════════════════════════════════════════════════════════════
║ search.py V1.0.28 - Recherche multilingue avec routage intelligent
╚════════════════════════════════════════════════════════════════

Question: grincement
Mode: standard

═══════════════════════════════════════════════════════════════════
Question affichée  : bruxisme
Parcours détection : standard
Question originale : grincement
Question tech FR   : grincement
Auteur             : cx
Mode effectif      : standard
═══════════════════════════════════════════════════════════════════
Message: 47 patients trouvés

Patients (10 sur 47):
  1. Paul Martin, M, 34 ans - Bruxisme nocturne, ...
  ...

⏱️  Temps: 45ms
```
<!-- /CODE -->

---

<!-- SLIDE
id: "schema-bdd"
titre: "Structure de la base de données"
template: "code"
emoji: "🗄️"
timing: "3min"
transition: "slide"
-->

### Annexe D : Structure de la base de données

<!-- CODE
langage: "sql"
titre: "Schéma SQLite"
executable: "false"
-->
```sql
-- Table principale
CREATE TABLE patients (
    id INTEGER PRIMARY KEY,
    canontags TEXT,      -- Tags standardisés (séparés par |)
    canonadjs TEXT,      -- Adjectifs standardisés
    sexe TEXT,           -- M ou F
    age DECIMAL(5,3),    -- Âge en années décimales
    datenaissance DATE,
    prenom TEXT,
    nom TEXT,
    idportrait TEXT,     -- Référence image
    oripathologies TEXT, -- Pathologies originales (affichage)
    pathologies TEXT     -- Pathologies normalisées
);

-- Table des pathologies (lookup)
CREATE TABLE pathologies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pathologie TEXT UNIQUE NOT NULL  -- Forme STANDARDISÉE
);

-- Table de jointure N:M
CREATE TABLE patients_pathologies (
    patient_id INTEGER NOT NULL,
    pathologie_id INTEGER NOT NULL,
    PRIMARY KEY (patient_id, pathologie_id),
    FOREIGN KEY (patient_id) REFERENCES patients(id),
    FOREIGN KEY (pathologie_id) REFERENCES pathologies(id)
);

-- Index pour performance
CREATE INDEX idx_patients_sexe ON patients(sexe);
CREATE INDEX idx_patients_age ON patients(age);
CREATE INDEX idx_pp_patient_id ON patients_pathologies(patient_id);
CREATE INDEX idx_pp_pathologie_id ON patients_pathologies(pathologie_id);
CREATE INDEX idx_pathologies_nom ON pathologies(pathologie);
```
<!-- /CODE -->

---

<!-- SLIDE
id: "referentiels-csv"
titre: "Référentiels CSV"
template: "code"
emoji: "📊"
timing: "2min"
transition: "slide"
-->

### Annexe E : Référentiels CSV

#### tags.csv (extrait)

<!-- CODE
langage: "csv"
titre: "Format tags.csv"
executable: "false"
-->
```csv
t;gn;as;pts
béance;f;antérieur,postérieur,latéral,gauche,droit,sévère;beance,open bite,morsure ouverte
bruxisme;m;nocturne,diurne,sévère;grincement,grince des dents,clenching
classe ii d'angle;f;sévère,division 1,division 2;classe 2,distocclusion,rétrusion
```
<!-- /CODE -->

#### adjectifs.csv (extrait)

<!-- CODE
langage: "csv"
titre: "Format adjectifs.csv"
executable: "false"
-->
```csv
a;f;mp;fp;pas
antérieur;antérieure;antérieurs;antérieures;frontal,avant
sévère;sévère;sévères;sévères;grave,important,marqué
gauche;gauche;gauches;gauches;left,côté gauche
```
<!-- /CODE -->

#### angles.csv (extrait)

<!-- CODE
langage: "csv"
titre: "Format angles.csv"
executable: "false"
-->
```csv
expression;operateur;seuil;tag_canonique;label
anb > {n};>;4;classe ii squelettique;Classe II squelettique
anb < {n};<;2;classe iii squelettique;Classe III squelettique
sna > {n};>;86;prognathisme maxillaire;Prognathisme maxillaire
```
<!-- /CODE -->

---

<!-- SLIDE
id: "synthese-finale"
titre: "Synthèse"
template: "synthese"
emoji: "✅"
timing: "2min"
transition: "zoom"
-->

## Synthèse

<!-- KEY: KITVIEW V5 combine détection algorithmique (rapide, gratuite) et IA (flexible, payante) avec fallback intelligent pour atteindre 89% de succès sans intervention -->

### Points clés à retenir

1. **Architecture modulaire** : 6 couches avec responsabilités distinctes
2. **Détection hybride** : Algorithmique (cx) + IA (eden) avec fallback automatique
3. **Format unifié** : JSON standardisé entre tous les modules
4. **Protection intégrée** : Garde-fou contre les requêtes sans filtres
5. **Multilingue natif** : 12 langues avec traduction bidirectionnelle

### Métriques de performance

- **detall.py** : ~5-20ms, gratuit
- **detia.py** : ~500-2000ms, payant
- **Taux de succès** : 89% sans intervention, 100% avec correction utilisateur

---

**Fin du document**

*Document généré le 18/01/2026 - KITVIEW Search V5 Documentation Technique*
*Version Slides-Ready avec métadonnées Reveal.js*
