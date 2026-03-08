# L'IA dans KITVIEW Search V5.1

<!-- PRESENTATION_META
titre_court: "L'IA dans KITVIEW Search V5.1"
sous_titre: "De la génération de référentiels au chatbot clinique : une intégration IA complète"
duree_estimee: "45min"
niveau: "intermédiaire"
audience: "Développeurs, architectes, praticiens orthodontistes"
fichiers_concernes: "traducteur.py, traduire.py, detia.py, detiabrut.py, detall.py, creecommentaires.py"
emoji_principal: "🤖"
-->

**Version** : 1.0.0  
**Date** : 30/01/2026  
**Auteur** : Documentation technique KITVIEW Search V5.1  
**Audience** : Développeurs, architectes logiciel, praticiens orthodontistes

---

<!-- NO_SLIDE -->

## Table des matières

1. [Vue d'ensemble : L'IA omniprésente](#1-vue-densemble--lia-omniprésente)
2. [Vibe Programming : L'IA comme partenaire de développement](#2-vibe-programming--lia-comme-partenaire-de-développement)
3. [Génération de référentiels](#3-génération-de-référentiels)
   - 3.1 [Traducteur multilingue et glossaire](#31-traducteur-multilingue-et-glossaire)
   - 3.2 [Génération des commentaires pathologiques](#32-génération-des-commentaires-pathologiques)
4. [Détection de langue](#4-détection-de-langue)
5. [Cœur de métier : Détection IA](#5-cœur-de-métier--détection-ia)
   - 5.1 [detia.py : Détection enrichie](#51-detiappy--détection-enrichie)
   - 5.2 [detiabrut.py : Mesure d'impact](#52-detiabrut--mesure-dimpact)
   - 5.3 [Comparaison detia vs detall](#53-comparaison-detia-vs-detall)
6. [Chatbot clinique intégré](#6-chatbot-clinique-intégré)
7. [Analyse de cohorte](#7-analyse-de-cohorte)
8. [Annexes : Prompts IA](#annexes--prompts-ia)
   
   <!-- /NO_SLIDE -->

---

<!-- SLIDE
id: "vue-ensemble"
titre: "L'IA omniprésente dans KITVIEW"
template: "schema"
emoji: "🌐"
timing: "4min"
transition: "zoom"
-->

## 1. Vue d'ensemble : L'IA omniprésente

<!-- KEY: KITVIEW V5.1 intègre l'IA à 6 niveaux distincts : développement, référentiels, traduction, détection, chatbot clinique et analyse de cohorte -->

<!-- QUESTION: Pourquoi utiliser plusieurs types d'IA (DeepL, GPT, Claude) plutôt qu'un seul modèle ? -->

KITVIEW Search V5.1 intègre l'intelligence artificielle à **tous les niveaux** de son architecture, du développement à l'utilisation finale.

<!-- DIAGRAM
type: "architecture"
titre: "Les 6 niveaux d'intégration IA dans KITVIEW"
legende: "Du code source jusqu'à l'analyse clinique"
-->

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    INTÉGRATION IA DANS KITVIEW V5.1                         │
└─────────────────────────────────────────────────────────────────────────────┘

   DÉVELOPPEMENT                     RÉFÉRENTIELS                    RUNTIME
   ─────────────                     ────────────                    ───────

┌─────────────────┐             ┌─────────────────┐           ┌─────────────────┐
│ 🎨 NIVEAU 1     │             │ 📚 NIVEAU 2     │           │ 🌍 NIVEAU 3     │
│ Vibe Programming│             │ Glossaire       │           │ Détection       │
│                 │             │ multilingue     │           │ de langue       │
│ Claude + Cursor │             │                 │           │                 │
│ + ChatGPT       │────────────▶│ DeepL API       │──────────▶│ DeepL +         │
│                 │             │ 12 langues      │           │ Glossaire       │
│ Génération code │             │ traducteur.py   │           │ traduire.py     │
└─────────────────┘             └─────────────────┘           └─────────────────┘
                                        │
                                        ▼
                                ┌─────────────────┐
                                │ 💬 NIVEAU 2b    │
                                │ Commentaires    │
                                │ pathologiques   │
                                │                 │
                                │ LLM (GPT/Claude)│
                                │ creecommentaires│
                                └─────────────────┘

   RECHERCHE                        CLINIQUE                      ANALYTICS
   ─────────                        ────────                      ─────────

┌─────────────────┐             ┌─────────────────┐           ┌─────────────────┐
│ 🔍 NIVEAU 4     │             │ 🏥 NIVEAU 5     │           │ 📊 NIVEAU 6     │
│ Détection IA    │             │ Chatbot         │           │ Analyse         │
│                 │             │ clinique        │           │ de cohorte      │
│ GPT-4o / Claude │             │                 │           │                 │
│ detia.py        │────────────▶│ GPT-4o / Claude │──────────▶│ GPT-4o / Claude │
│ detiabrut.py    │             │ Fiche patient   │           │ Sélection       │
│                 │             │ personnalisée   │           │ multi-patients  │
└─────────────────┘             └─────────────────┘           └─────────────────┘
```

<!-- /DIAGRAM -->

<!-- SUBSLIDE
titre: "Technologies IA utilisées"
parent: "vue-ensemble"
-->

### Technologies IA utilisées

<!-- TABLE
titre: "Mapping niveau → technologie IA"
colonnes_cles: "Niveau,Technologie"
style: "large"
-->

| Niveau | Usage         | Technologie                | Coût              |
| ------ | ------------- | -------------------------- | ----------------- |
| 1      | Développement | Claude Opus, GPT-4, Cursor | Variable          |
| 2a     | Glossaire     | DeepL API                  | ~0.02€/1000 chars |
| 2b     | Commentaires  | GPT-4o / Claude            | ~0.01€/requête    |
| 3      | Langue        | DeepL + Glossaire          | ~0.001€/détection |
| 4      | Détection     | GPT-4o / Claude            | ~0.01€/requête    |
| 5      | Chatbot       | GPT-4o / Claude            | ~0.02€/échange    |
| 6      | Cohorte       | GPT-4o / Claude            | ~0.05€/analyse    |

<!-- /TABLE -->

<!-- /SUBSLIDE -->

---

<!-- SLIDE
id: "vibe-programming"
titre: "Vibe Programming"
template: "2colonnes"
emoji: "🎨"
timing: "3min"
transition: "slide"
-->

## 2. Vibe Programming : L'IA comme partenaire de développement

<!-- KEY: Le vibe programming utilise l'IA (Claude, GPT) comme co-développeur pour générer, corriger et optimiser le code -->

Le **vibe programming** est une approche de développement où l'IA agit comme co-pilote, générant du code à partir de descriptions en langage naturel et itérant via le dialogue.

### Outils utilisés

- **Claude (Anthropic)** : Génération de code complexe, architecture
- **GPT-4 (OpenAI)** : Débogage, optimisation
- **Cursor** : IDE avec IA intégrée

### Avantages observés

- Accélération du développement ×3-5
- Exploration rapide de solutions alternatives
- Documentation générée automatiquement
- Réduction des bugs par revue IA

### Limites à connaître

- Nécessite une validation humaine systématique
- L'IA peut "halluciner" des APIs inexistantes
- Cohérence à maintenir sur les gros projets

> **Note** : Ce mode de développement est désormais standard dans l'industrie et n'est pas spécifique à KITVIEW.

---

<!-- SLIDE
id: "generation-referentiels"
titre: "Génération de référentiels"
template: "titre-section"
emoji: "📚"
timing: "1min"
transition: "zoom"
-->

## 3. Génération de référentiels

<!-- KEY: L'IA génère et maintient les référentiels multilingues (glossaire) et les commentaires explicatifs des pathologies -->

---

<!-- SLIDE
id: "traducteur-glossaire"
titre: "Traducteur multilingue et glossaire"
template: "schema"
emoji: "🌍"
timing: "5min"
transition: "slide"
-->

### 3.1 Traducteur multilingue et glossaire

<!-- KEY: traducteur.py utilise DeepL pour générer glossaire.csv en 12 langues avec contrôle terminologique médical -->

<!-- QUESTION: Pourquoi un glossaire contrôlé plutôt que de la traduction à la volée ? -->

Le fichier `glossaire.csv` est le **cœur multilingue** de KITVIEW. Il contient la traduction contrôlée de tous les termes orthodontiques en 12 langues.

<!-- DIAGRAM
type: "flux"
titre: "Pipeline de génération du glossaire"
legende: "traducteur.py enrichit glossaire.csv via DeepL"
-->

```
┌─────────────────┐
│ Terme français  │
│ "béance"        │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    traducteur.py                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ 1. Lecture glossaire.csv existant                   │    │
│  │ 2. Détection cases vides                            │    │
│  │ 3. Appel DeepL API pour chaque langue manquante     │    │
│  │ 4. Validation terminologique                         │    │
│  │ 5. Sauvegarde UTF-8-BOM avec garde-fou              │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                     glossaire.csv                            │
│  type;fr;en;de;es;it;ja;pt;pl;ro;th;ar;cn                   │
│  ─────────────────────────────────────────────────────────  │
│  patho;béance;open bite;Offener Biss;mordida abierta;...    │
│  patho;bruxisme;bruxism;Bruxismus;bruxismo;歯ぎしり;...     │
│  adj;sévère;severe;schwer;severo;重度の;...                 │
└─────────────────────────────────────────────────────────────┘
```

<!-- /DIAGRAM -->

<!-- SUBSLIDE
titre: "Modes d'utilisation de traducteur.py"
parent: "traducteur-glossaire"
-->

### Modes d'utilisation

<!-- CODE
langage: "bash"
titre: "Commandes traducteur.py"
executable: "false"
-->

```bash
# Compléter toutes les cases vides du glossaire
python traducteur.py glossaire.csv

# Compléter uniquement l'allemand
python traducteur.py glossaire.csv de

# Mode test (10 premières lignes)
python traducteur.py glossaire.csv -t10

# Traduire une phrase avec le glossaire
python traducteur.py "bruxisme sévère" fren

# Traduire avec DeepL (fallback)
python traducteur.py "béance antérieure" frde --deepl
```

<!-- /CODE -->

### Avantage du glossaire contrôlé

<!-- TABLE
titre: "Glossaire vs Traduction à la volée"
colonnes_cles: "Aspect,Glossaire,DeepL direct"
style: "large"
-->

| Aspect             | Glossaire contrôlé      | DeepL direct    |
| ------------------ | ----------------------- | --------------- |
| Précision médicale | ✓ Validé par expert     | ✗ Approximatif  |
| Cohérence          | ✓ Même terme partout    | ✗ Variations    |
| Coût               | ✓ Gratuit (pré-calculé) | ✗ Par caractère |
| Latence            | ✓ <1ms                  | ✗ 200-500ms     |
| Synonymes          | ✓ Gérés (pts/pas)       | ✗ Non gérés     |

<!-- /TABLE -->

<!-- /SUBSLIDE -->

---

<!-- SLIDE
id: "commentaires-pathologiques"
titre: "Génération des commentaires pathologiques"
template: "code"
emoji: "💬"
timing: "4min"
transition: "slide"
-->

### 3.2 Génération des commentaires pathologiques

<!-- KEY: creecommentaires.py extrait les pathologies uniques et prépare commentaires.csv pour enrichissement IA -->

Le fichier `commentaires.csv` contient des descriptions explicatives de chaque pathologie, utilisées pour enrichir la fiche patient.

<!-- CODE
langage: "bash"
titre: "Génération initiale des commentaires"
executable: "false"
-->

```bash
# Extraction des pathologies uniques depuis les patients
python creecommentaires.py pats100.csv

# Résultat : refs/commentaires.csv avec colonnes :
# oripathologie;commentaire
# béance antérieure;(à compléter)
# bruxisme nocturne;(à compléter)
```

<!-- /CODE -->

### Enrichissement par IA

Une fois `commentaires.csv` généré, l'utilisateur peut utiliser un LLM pour remplir la colonne `commentaire` avec des descriptions cliniques :

<!-- CODE
langage: "text"
titre: "Exemple de prompt pour enrichissement"
executable: "false"
-->

```
Pour chaque pathologie de cette liste, génère une description 
clinique de 2-3 phrases destinée aux praticiens orthodontistes.
La description doit inclure :
- Définition succincte
- Étiologie principale
- Impact sur le traitement

Pathologies :
- béance antérieure
- bruxisme nocturne
- classe ii d'angle division 1
...
```

<!-- /CODE -->

### Protection des données utilisateur

<!-- TABLE
titre: "Fichiers protégés vs générés"
colonnes_cles: "Fichier,Statut"
style: "compact"
-->

| Fichier          | Statut     | Raison                    |
| ---------------- | ---------- | ------------------------- |
| commentaires.csv | 🔒 Protégé | Enrichi par l'utilisateur |
| glossaire.csv    | 🔒 Protégé | Validé par expert         |
| tags.csv         | 🔒 Protégé | Configuration métier      |
| *_out.csv        | ✓ Généré   | Résultats de traitement   |

<!-- /TABLE -->

---

<!-- SLIDE
id: "detection-langue"
titre: "Détection de langue"
template: "schema"
emoji: "🗣️"
timing: "4min"
transition: "slide"
-->

## 4. Détection de langue

<!-- KEY: traduire.py détecte la langue en 3 étapes : Unicode (scripts non-latins), glossaire (pathologies), DeepL (fallback) -->

<!-- QUESTION: Pourquoi détecter d'abord par Unicode avant d'utiliser le glossaire ? -->

Le module `traduire.py` implémente une détection de langue en **3 étapes** pour optimiser performance et coût.

<!-- DIAGRAM
type: "flux"
titre: "Pipeline de détection de langue"
legende: "Chaque étape filtre avant de passer à la suivante"
-->

```
Question entrante
       │
       ▼
┌──────────────────────────────────────────────────────────────┐
│ ÉTAPE 1 : DÉTECTION UNICODE (gratuit, <1ms)                  │
│                                                              │
│ Analyse des caractères Unicode :                             │
│ • Hiragana/Katakana (3040-30FF) → Japonais                   │
│ • CJK sans kana (4E00-9FFF) → Chinois                        │
│ • Thai (0E00-0E7F) → Thaï                                    │
│ • Arabic (0600-06FF) → Arabe                                 │
│                                                              │
│ Résultat : "ja" | "cn" | "th" | "ar" | None                  │
└──────────────────────────────────────────────────────────────┘
       │
       │ Si None (script latin)
       ▼
┌──────────────────────────────────────────────────────────────┐
│ ÉTAPE 2 : DÉTECTION GLOSSAIRE (gratuit, <5ms)                │
│                                                              │
│ Recherche de pathologies connues dans le texte :             │
│ • "open bite" trouvé en colonne EN → Anglais                 │
│ • "Tiefbiss" trouvé en colonne DE → Allemand                 │
│ • Score par langue = nombre de termes trouvés                │
│                                                              │
│ Résultat : langue avec score max | None si ex-aequo          │
└──────────────────────────────────────────────────────────────┘
       │
       │ Si None ou ambiguïté
       ▼
┌──────────────────────────────────────────────────────────────┐
│ ÉTAPE 3 : DÉTECTION DEEPL (payant, ~200ms)                   │
│                                                              │
│ Appel API DeepL avec traduction vers FR :                    │
│ → La langue source est retournée dans la réponse             │
│                                                              │
│ Fallback : Si erreur API et texte latin → "fr"               │
└──────────────────────────────────────────────────────────────┘
       │
       ▼
   Langue détectée
```

<!-- /DIAGRAM -->

<!-- SUBSLIDE
titre: "Exemples de détection"
parent: "detection-langue"
-->

### Exemples de détection

<!-- TABLE
titre: "Exemples par étape de détection"
colonnes_cles: "Texte,Étape,Langue"
style: "large"
-->

| Texte                 | Étape     | Langue | Temps  |
| --------------------- | --------- | ------ | ------ |
| `歯ぎしりの患者`             | Unicode   | ja     | <1ms   |
| `开口畸形患者`              | Unicode   | cn     | <1ms   |
| `open bite female`    | Glossaire | en     | ~3ms   |
| `Tiefbiss bei Frauen` | Glossaire | de     | ~3ms   |
| `linguo-version`      | DeepL     | fr/en  | ~200ms |
| `bonjour`             | DeepL     | fr     | ~200ms |

<!-- /TABLE -->

<!-- /SUBSLIDE -->

---

<!-- SLIDE
id: "detection-ia"
titre: "Cœur de métier : Détection IA"
template: "titre-section"
emoji: "🔍"
timing: "1min"
transition: "zoom"
-->

## 5. Cœur de métier : Détection IA

<!-- KEY: La détection IA (detia.py) est le mode intelligent de recherche, utilisant un LLM enrichi des référentiels métier -->

---

<!-- SLIDE
id: "detia-enrichie"
titre: "detia.py : Détection enrichie"
template: "schema"
emoji: "🧠"
timing: "6min"
transition: "slide"
-->

### 5.1 detia.py : Détection enrichie

<!-- KEY: detia.py construit un prompt enrichi avec tags, adjectifs, angles et âges, puis mappe les résultats vers le canonique -->

<!-- QUESTION: Pourquoi injecter les référentiels dans le prompt plutôt que de faire confiance au LLM ? -->

`detia.py` envoie la question à un LLM avec un **prompt système enrichi** contenant les référentiels métier.

<!-- DIAGRAM
type: "flux"
titre: "Pipeline detia.py"
legende: "Le LLM reçoit la question ET les référentiels pour une détection guidée"
-->

```
Question utilisateur : "grincement sévère chez les adolescents"
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         CONSTRUCTION DU PROMPT                            │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │ PROMPT SYSTÈME (enrichi dynamiquement)                             │  │
│  │                                                                    │  │
│  │ === TAGS PATHOLOGIQUES ===                                         │  │
│  │ - béance                                                           │  │
│  │ - bruxisme                                                         │  │
│  │ - classe ii d'angle                                                │  │
│  │ ... (~100 tags)                                                    │  │
│  │                                                                    │  │
│  │ === SYNONYMES IMPORTANTS ===                                       │  │
│  │ grincement → bruxisme                                              │  │
│  │ open bite → béance                                                 │  │
│  │ tongue thrust → interposition linguale                             │  │
│  │ ... (~60 synonymes)                                                │  │
│  │                                                                    │  │
│  │ === ADJECTIFS ===                                                  │  │
│  │ - antérieur/antérieure                                             │  │
│  │ - sévère                                                           │  │
│  │ - nocturne                                                         │  │
│  │ ... (~50 adjectifs)                                                │  │
│  │                                                                    │  │
│  │ === ANGLES CÉPHALOMÉTRIQUES ===                                    │  │
│  │ ANB > 4 → classe ii squelettique                                   │  │
│  │ ANB < 0 → classe iii squelettique                                  │  │
│  │ SNA > 85 → prognathisme maxillaire                                 │  │
│  │ ...                                                                │  │
│  │                                                                    │  │
│  │ === RÈGLES ÂGE/SEXE ===                                            │  │
│  │ adolescents → BETWEEN 12, 18                                       │  │
│  │ enfants → < 12                                                     │  │
│  │ femme/fille → sexe = 'F'                                           │  │
│  │ ...                                                                │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                                                          │
│  PROMPT UTILISATEUR : "grincement sévère chez les adolescents"           │
└──────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   LLM (GPT-4o   │
                    │   ou Claude)    │
                    │   ~500-2000ms   │
                    └────────┬────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         RÉPONSE IA (JSON)                                 │
│  {                                                                       │
│    "criteres": [                                                         │
│      {"type": "tag", "detecte": "grincement", "adjectifs": ["sévère"]}, │
│      {"type": "age", "detecte": "adolescents", "operateur": "BETWEEN"}   │
│    ]                                                                     │
│  }                                                                       │
└──────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    MAPPING VERS CANONIQUE                                 │
│                                                                          │
│  "grincement" → tags_map["grincement"] → "bruxisme"                      │
│  "sévère" → adjs_map["severe"] → "sévère"                                │
│                                                                          │
│  Résultat final :                                                        │
│  - tag: bruxisme + adjectif: sévère                                      │
│  - age: BETWEEN 12 AND 18                                                │
└──────────────────────────────────────────────────────────────────────────┘
```

<!-- /DIAGRAM -->

<!-- SUBSLIDE
titre: "Fichiers de référence utilisés"
parent: "detia-enrichie"
-->

### Fichiers de référence utilisés par detia.py

<!-- TABLE
titre: "Référentiels injectés dans le prompt"
colonnes_cles: "Fichier,Contenu,Usage"
style: "large"
-->

| Fichier         | Contenu                        | Usage dans le prompt          |
| --------------- | ------------------------------ | ----------------------------- |
| `tags.csv`      | 100+ pathologies (t;gn;as;pts) | Liste des tags reconnus       |
| `adjectifs.csv` | 50+ adjectifs (a;f;mp;fp;pas)  | Qualificatifs acceptés        |
| `angles.csv`    | Seuils ANB/SNA/SNB             | Table de conversion angle→tag |
| `ages.csv`      | Patterns âge/sexe              | Règles d'interprétation       |
| `ia.csv`        | Moteurs IA disponibles         | Configuration modèle          |
| `communb.csv`   | Synonymes "même X"             | Détection similarités (V5.1)  |

<!-- /TABLE -->

<!-- /SUBSLIDE -->

---

<!-- SLIDE
id: "detiabrut"
titre: "detiabrut.py : Mesure d'impact"
template: "code"
emoji: "🎛️"
timing: "4min"
transition: "slide"
-->

### 5.2 detiabrut.py : Mesure d'impact

<!-- KEY: detiabrut.py permet d'activer/désactiver sélectivement les référentiels pour mesurer leur importance -->

`detiabrut.py` est une version **configurable** de detia.py permettant de mesurer l'impact de chaque référentiel.

<!-- CODE
langage: "bash"
titre: "Syntaxe detiabrut.py"
executable: "false"
-->

```bash
# Tout actif (équivalent à detia.py)
python detiabrut.py "bruxisme sévère" all

# Tout désactivé (IA brute sans aide)
python detiabrut.py "bruxisme sévère" none

# Sans liste de tags (teste si l'IA connaît "bruxisme")
python detiabrut.py "grincement" -tags

# Sans adjectifs ni mapping
python detiabrut.py "bruxisme important" -adjs -mapping

# Mode brut SAUF le mapping (post-traitement seul)
python detiabrut.py "grincement" none +mapping
```

<!-- /CODE -->

### Référentiels configurables

<!-- TABLE
titre: "5 référentiels activables/désactivables"
colonnes_cles: "Référentiel,Impact mesuré"
style: "compact"
-->

| Référentiel | Description                          | Impact mesuré                    |
| ----------- | ------------------------------------ | -------------------------------- |
| `tags`      | Liste des pathologies dans le prompt | Reconnaissance des termes métier |
| `adjs`      | Liste des adjectifs                  | Qualificatifs détectés           |
| `ages`      | Patterns âge/sexe                    | Critères démographiques          |
| `angles`    | Seuils céphalométriques              | Conversion angle→pathologie      |
| `mapping`   | Post-traitement détecté→canonique    | Normalisation finale             |

<!-- /TABLE -->

### Signature de l'auteur

Le champ `auteur` du JSON reflète la configuration :

- `"openai/gpt-4o"` → Mode all
- `"openai/gpt-4o [none]"` → IA brute
- `"openai/gpt-4o [-tags,-mapping]"` → Sans tags ni mapping

---

<!-- SLIDE
id: "comparaison-detia-detall"
titre: "Comparaison detia vs detall"
template: "2colonnes"
emoji: "⚖️"
timing: "5min"
transition: "slide"
-->

### 5.3 Comparaison detia vs detall

<!-- KEY: detall est gratuit et rapide (5-20ms) mais rigide | detia est flexible mais payant et lent (500-2000ms) -->

<!-- QUESTION: Dans quel cas privilégier detall sur detia ? -->

<!-- TABLE
titre: "Comparaison complète"
colonnes_cles: "Aspect,detall.py,detia.py"
style: "large"
-->

| Aspect               | detall.py (algorithmique) | detia.py (IA)          |
| -------------------- | ------------------------- | ---------------------- |
| **Auteur**           | `cx`                      | `eden/gpt-4o` ou autre |
| **Méthode**          | Regex + pattern matching  | LLM (GPT-4, Claude)    |
| **Latence**          | 5-20ms                    | 500-2000ms             |
| **Coût**             | Gratuit                   | ~0.01€/requête         |
| **Flexibilité**      | Patterns prédéfinis       | Comprend le contexte   |
| **Synonymes**        | Via pts/pas dans CSV      | Compréhension native   |
| **Fautes de frappe** | Non tolérées              | Partiellement tolérées |
| **Reformulations**   | Non comprises             | Comprises              |
| **Résidu**           | Peut rester pollué        | Plus propre            |
| **Prévisibilité**    | 100% déterministe         | Variable               |

<!-- /TABLE -->

### Cas d'usage recommandés

<!-- TABLE
titre: "Quand utiliser chaque mode"
colonnes_cles: "Situation,Mode recommandé"
style: "compact"
-->

| Situation                         | Mode recommandé                |
| --------------------------------- | ------------------------------ |
| Requêtes simples et standardisées | detall (purstandard)           |
| Volumes importants (batch)        | detall                         |
| Requêtes complexes ou ambiguës    | detia (standard avec fallback) |
| Tests de régression               | detall (déterministe)          |
| Démonstration/UX premium          | detia                          |

<!-- /TABLE -->

### Stratégie de fallback

Le mode `standard` combine les deux approches :

1. Essai avec detall.py (rapide, gratuit)
2. Si résultat = 0 → Fallback vers detia.py
3. Si encore 0 → Traduction DeepL puis retry

Indicateur `parcours_detection` : `"standard"`, `"standard→ia"`, `"standard→ia→deepl→ia"`

---

<!-- SLIDE
id: "chatbot-clinique"
titre: "Chatbot clinique intégré"
template: "schema"
emoji: "🏥"
timing: "5min"
transition: "slide"
-->

## 6. Chatbot clinique intégré

<!-- KEY: Le chatbot de la fiche patient permet au praticien d'interroger l'IA sur un patient spécifique avec contexte complet -->

<!-- QUESTION: Pourquoi injecter le contexte patient plutôt que de laisser l'IA poser des questions ? -->

La fiche détail de chaque patient intègre un **chatbot contextuel** permettant au praticien de poser des questions cliniques.

<!-- DIAGRAM
type: "architecture"
titre: "Architecture du chatbot clinique"
legende: "Le contexte patient est injecté automatiquement dans chaque échange"
-->

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        FICHE PATIENT                                     │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ Patient: Marie Dupont, 14 ans, F                                  │  │
│  │ Pathologies: béance antérieure, bruxisme nocturne                 │  │
│  │ Portrait: [photo]                                                 │  │
│  │ Commentaires: [texte enrichi]                                     │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                      CHATBOT INTÉGRÉ                               │  │
│  │                                                                   │  │
│  │  Praticien: "Quelles sont les options de traitement ?"           │  │
│  │                                                                   │  │
│  │  IA: "Pour cette patiente de 14 ans présentant une              │  │
│  │       béance antérieure associée à un bruxisme nocturne,         │  │
│  │       je recommande :                                             │  │
│  │       1. Évaluation de la dysfonction linguale...                │  │
│  │       2. Gouttière nocturne pour le bruxisme...                  │  │
│  │       3. Traitement orthodontique multibague..."                 │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    CONSTRUCTION DU PROMPT                                │
│                                                                         │
│  SYSTÈME:                                                               │
│  "Tu es un assistant orthodontiste. Voici le contexte patient:          │
│   - Nom: Marie Dupont                                                   │
│   - Âge: 14 ans                                                         │
│   - Sexe: Féminin                                                       │
│   - Pathologies: béance antérieure, bruxisme nocturne                   │
│   - Commentaires cliniques: [injection automatique]                     │
│                                                                         │
│   Réponds de façon professionnelle et circonstanciée."                  │
│                                                                         │
│  UTILISATEUR:                                                           │
│  "Quelles sont les options de traitement ?"                             │
└─────────────────────────────────────────────────────────────────────────┘
```

<!-- /DIAGRAM -->

### Avantages du contexte injecté

- **Personnalisation** : Réponses adaptées à ce patient précis
- **Cohérence** : L'IA connaît déjà les pathologies identifiées
- **Efficacité** : Pas besoin de ré-expliquer le cas
- **Traçabilité** : Historique des échanges conservé

---

<!-- SLIDE
id: "analyse-cohorte"
titre: "Analyse de cohorte"
template: "schema"
emoji: "📊"
timing: "5min"
transition: "slide"
-->

## 7. Analyse de cohorte

<!-- KEY: L'analyse de cohorte permet de demander à l'IA une synthèse des patients sélectionnés par une recherche -->

<!-- QUESTION: Quel volume de patients peut-on analyser en une seule requête ? -->

L'analyse de cohorte permet au praticien de demander une **synthèse IA** d'un groupe de patients issus d'une recherche.

<!-- DIAGRAM
type: "flux"
titre: "Pipeline d'analyse de cohorte"
legende: "De la recherche à la synthèse IA"
-->

```
┌─────────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 1 : RECHERCHE                                                     │
│                                                                         │
│ Question: "femmes avec béance antérieure de moins de 20 ans"            │
│ Résultat: 47 patientes                                                  │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 2 : PRÉPARATION CONTEXTE                                          │
│                                                                         │
│ Extraction des données agrégées :                                       │
│ - Distribution des âges : min=8, max=19, moyenne=14.2                   │
│ - Pathologies associées :                                               │
│   * bruxisme: 23 patientes (49%)                                        │
│   * interposition linguale: 18 patientes (38%)                          │
│   * respiration buccale: 15 patientes (32%)                             │
│ - Répartition par tranche d'âge :                                       │
│   * 8-12 ans: 12 patientes                                              │
│   * 13-16 ans: 28 patientes                                             │
│   * 17-19 ans: 7 patientes                                              │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 3 : PROMPT COHORTE                                                │
│                                                                         │
│ SYSTÈME:                                                                │
│ "Tu es un analyste clinique orthodontique. Voici les données d'une     │
│  cohorte de 47 patientes présentant une béance antérieure.              │
│  Analyse ces données et fournis :                                       │
│  1. Les tendances principales                                           │
│  2. Les corrélations pathologiques significatives                       │
│  3. Les recommandations pour cette population"                          │
│                                                                         │
│ UTILISATEUR:                                                            │
│ [Données agrégées de la cohorte]                                        │
└─────────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ ÉTAPE 4 : SYNTHÈSE IA                                                   │
│                                                                         │
│ "Analyse de la cohorte de 47 patientes avec béance antérieure :        │
│                                                                         │
│  TENDANCES PRINCIPALES :                                                │
│  Cette cohorte présente un pic d'incidence entre 13 et 16 ans          │
│  (60% des cas), ce qui correspond à la phase de croissance             │
│  pubertaire où les dyspraxies linguales ont un impact maximal.         │
│                                                                         │
│  CORRÉLATIONS SIGNIFICATIVES :                                          │
│  - 49% présentent un bruxisme associé, suggérant une composante        │
│    de dysfonction oro-faciale commune.                                  │
│  - 38% ont une interposition linguale, étiologie fréquente de la       │
│    béance antérieure.                                                   │
│                                                                         │
│  RECOMMANDATIONS :                                                      │
│  - Évaluation systématique de la déglutition atypique                  │
│  - Prise en charge pluridisciplinaire (orthophoniste)                  │
│  - Surveillance du bruxisme nocturne..."                                │
└─────────────────────────────────────────────────────────────────────────┘
```

<!-- /DIAGRAM -->

### Limites et bonnes pratiques

<!-- TABLE
titre: "Limites de l'analyse de cohorte"
colonnes_cles: "Aspect,Limite"
style: "compact"
-->

| Aspect          | Limite            | Recommandation                  |
| --------------- | ----------------- | ------------------------------- |
| Taille cohorte  | ~100 patients max | Agréger les données avant envoi |
| Contexte LLM    | ~8000 tokens      | Résumer les pathologies         |
| Coût            | ~0.05€/analyse    | Utiliser pour synthèses finales |
| Confidentialité | Données patient   | Anonymiser avant envoi          |

<!-- /TABLE -->

---

<!-- SLIDE
id: "annexes"
titre: "Annexes : Prompts IA"
template: "titre-section"
emoji: "📎"
timing: "1min"
transition: "zoom"
-->

## Annexes : Prompts IA

<!-- KEY: Cette annexe contient les prompts système utilisés par detia.py, le chatbot clinique et l'analyse de cohorte -->

---

<!-- SLIDE
id: "prompt-detia"
titre: "Annexe A : Prompt detia.py"
template: "code"
emoji: "A"
timing: "3min"
transition: "slide"
-->

### Annexe A : Prompt système de detia.py

<!-- CODE
langage: "text"
titre: "Prompt système complet (extrait)"
executable: "false"
-->

```
Tu es un analyseur de requêtes orthodontiques. Tu dois IDENTIFIER les termes 
présents dans la question.

=== MISSION ===
1. Détecter les TAGS (pathologies) de la liste ci-dessous
2. Détecter les ADJECTIFS qualifiant ces tags
3. Détecter les critères d'ÂGE et de SEXE
4. Détecter les demandes de COMPTAGE (combien, nombre de)
5. Détecter les ANGLES céphalométriques (ANB, SNA, SNB)

=== TAGS PATHOLOGIQUES ===
- béance
- bruxisme
- classe i d'angle
- classe ii d'angle
- classe iii d'angle
- encombrement
- diastème
- supraclusion
- infraclusion
- prognathisme mandibulaire
- rétrognathisme mandibulaire
- prognathisme maxillaire
- rétrognathisme maxillaire
[... ~100 tags ...]

=== SYNONYMES IMPORTANTS ===
Quand tu détectes ces termes, utilise le tag canonique correspondant :
  grincement → bruxisme
  grince des dents → bruxisme
  open bite → béance
  deep bite → supraclusion
  tongue thrust → interposition linguale
  tong e → interposition linguale
  retrusion → rétroalvéolie
  spacing → diastème
  crowding → encombrement
  overjet → surplomb
  overbite → supraclusion
  crossbite → occlusion croisée
  underbite → prognathisme mandibulaire
[... ~60 synonymes ...]

=== ADJECTIFS ===
- antérieur/antérieure
- postérieur/postérieure
- latéral/latérale
- gauche
- droit/droite
- sévère
- modéré/modérée
- léger/légère
- nocturne
- diurne
[... ~50 adjectifs ...]

=== ANGLES CÉPHALOMÉTRIQUES ===
IMPORTANT: Convertis les valeurs d'angles en tags pathologiques.

| Angle | Condition | Valeur | Tag résultant |
|-------|-----------|--------|---------------|
| ANB   | =         | 0 à 4  | classe i squelettique |
| ANB   | >         | 4      | classe ii squelettique |
| ANB   | <         | 0      | classe iii squelettique |
| SNA   | =         | 79-85  | position maxillaire normale |
| SNA   | >         | 85     | prognathisme maxillaire |
| SNA   | <         | 79     | rétrognathisme maxillaire |
| SNB   | =         | 77-83  | position mandibulaire normale |
| SNB   | >         | 83     | prognathisme mandibulaire |
| SNB   | <         | 77     | rétrognathisme mandibulaire |

=== CRITÈRES D'ÂGE ET SEXE ===
- "{n} ans" → âge EXACT, operateur "="
- "moins de {n} ans" → operateur "<"
- "plus de {n} ans" → operateur ">"
- "entre {n} et {n} ans" → operateur "BETWEEN"
- "enfants" → operateur "<", valeur 12
- "adolescents" → operateur "BETWEEN", valeur 12, valeur2 18
- "adultes" → operateur ">=", valeur 18
- femme/fille/femmes/patiente → "F"
- homme/garçon/hommes/patient → "M"

=== FORMAT DE SORTIE (JSON strict) ===
{
    "langue": "fr",
    "listcount": "COUNT" ou "LIST",
    "criteres": [
        {"type": "tag", "detecte": "terme", "adjectifs": ["adj1"]},
        {"type": "age", "detecte": "...", "operateur": "<", "valeur": 30},
        {"type": "sexe", "detecte": "...", "valeur": "M|F"}
    ],
    "residu": "mots non reconnus"
}

RÈGLES IMPORTANTES:
- Retourne UNIQUEMENT du JSON valide.
- Pour les angles, génère un critère de type "tag" avec le tag résultant.
- Utilise les synonymes pour mapper vers les tags canoniques.
```

<!-- /CODE -->

---

<!-- SLIDE
id: "prompt-chatbot"
titre: "Annexe B : Prompt chatbot clinique"
template: "code"
emoji: "B"
timing: "2min"
transition: "slide"
-->

### Annexe B : Prompt chatbot clinique

<!-- CODE
langage: "text"
titre: "Prompt système chatbot patient"
executable: "false"
-->

```
Tu es un assistant clinique orthodontique expérimenté. Tu aides les 
praticiens à analyser les cas patients et à prendre des décisions 
cliniques éclairées.

=== CONTEXTE PATIENT ===
- Identifiant: {patient_id}
- Nom: {prenom} {nom}
- Âge: {age} ans
- Sexe: {sexe}
- Pathologies identifiées: {pathologies}
- Commentaires cliniques: {commentaires}

=== CONSIGNES ===
1. Réponds de façon professionnelle et concise
2. Base tes recommandations sur les données du patient ci-dessus
3. Cite les pathologies spécifiques quand pertinent
4. Propose des options thérapeutiques adaptées à l'âge
5. Signale les contre-indications éventuelles
6. Recommande une prise en charge pluridisciplinaire si nécessaire

=== LIMITES ===
- Tu ne poses pas de diagnostic, tu assistes le praticien
- Tu ne prescris pas de médicaments
- Tu rappelles que l'examen clinique reste indispensable

=== FORMAT DE RÉPONSE ===
Utilise des paragraphes courts et lisibles.
Évite les listes à puces sauf si vraiment nécessaire.
Adapte ton niveau de détail à la question posée.
```

<!-- /CODE -->

---

<!-- SLIDE
id: "prompt-cohorte"
titre: "Annexe C : Prompt analyse de cohorte"
template: "code"
emoji: "C"
timing: "2min"
transition: "slide"
-->

### Annexe C : Prompt analyse de cohorte

<!-- CODE
langage: "text"
titre: "Prompt système analyse de cohorte"
executable: "false"
-->

```
Tu es un analyste clinique spécialisé en orthodontie. Tu analyses des 
cohortes de patients pour identifier des tendances et formuler des 
recommandations cliniques.

=== DONNÉES DE LA COHORTE ===
- Critères de recherche: {criteres_recherche}
- Nombre de patients: {nb_patients}
- Distribution des âges: min={age_min}, max={age_max}, moyenne={age_moy}
- Répartition par sexe: {pct_hommes}% hommes, {pct_femmes}% femmes

=== PATHOLOGIES ASSOCIÉES ===
{tableau_pathologies_associees}

=== CONSIGNES D'ANALYSE ===
Fournis une analyse structurée incluant :

1. TENDANCES PRINCIPALES
   - Profil démographique de la cohorte
   - Pics d'incidence par tranche d'âge
   - Différences hommes/femmes si significatives

2. CORRÉLATIONS PATHOLOGIQUES
   - Pathologies fréquemment associées
   - Hypothèses étiologiques
   - Facteurs de risque identifiables

3. RECOMMANDATIONS CLINIQUES
   - Protocole de prise en charge adapté
   - Examens complémentaires suggérés
   - Points de vigilance spécifiques

4. LIMITES DE L'ANALYSE
   - Biais potentiels de l'échantillon
   - Données manquantes
   - Prudence dans les conclusions

=== FORMAT ===
Utilise des paragraphes structurés, pas de listes à puces excessives.
Cite des chiffres précis quand disponibles.
Reste factuel et évite les généralisations non fondées.
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

<!-- KEY: KITVIEW V5.1 intègre l'IA à 6 niveaux : développement, référentiels, traduction, détection, chatbot et cohorte -->

### Points clés à retenir

1. **IA omniprésente** : Du développement (vibe programming) à l'analyse clinique
2. **Glossaire contrôlé** : DeepL génère, l'expert valide, le système utilise
3. **Détection hybride** : detall (rapide, gratuit) + detia (flexible, payant)
4. **Référentiels injectés** : Le prompt IA contient tags, adjectifs, angles, âges
5. **Chatbot contextuel** : Chaque patient a son contexte pré-injecté
6. **Analyse de cohorte** : Synthèse IA de groupes de patients

### Métriques de performance IA

<!-- TABLE
titre: "Performances par niveau d'intégration"
colonnes_cles: "Niveau,Latence,Coût"
style: "compact"
-->

| Niveau                  | Latence    | Coût/requête |
| ----------------------- | ---------- | ------------ |
| Glossaire (pré-calculé) | <1ms       | 0€           |
| Détection Unicode       | <1ms       | 0€           |
| Détection glossaire     | ~5ms       | 0€           |
| Détection DeepL         | ~200ms     | ~0.001€      |
| detall.py               | 5-20ms     | 0€           |
| detia.py                | 500-2000ms | ~0.01€       |
| Chatbot/Cohorte         | 1-3s       | ~0.02-0.05€  |

<!-- /TABLE -->

---

**Fin du document**

*Document généré le 30/01/2026 - KITVIEW Search V5.1 Documentation Technique*
*Version 1.0.0 - Slides-Ready avec métadonnées Reveal.js*
