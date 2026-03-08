# Prompt hautes V1.0.0 - 21/01/2026 13:18:43

# KITVIEW Search V5 — Architecture des Couches Hautes Serveur

**Document technique pour ingénieurs, architectes logiciel**

| Métadonnée | Valeur |
|------------|--------|
| Version | 1.0.0 |
| Date | 17/01/2026 |
| Auteur | Documentation technique |
| Statut | Initial |

---

## 1. Vue d'ensemble de l'architecture

KITVIEW Search V5 est une application de recherche multilingue sur une base de 25 000+ patients orthodontiques. L'architecture serveur se décompose en couches distinctes avec des responsabilités clairement définies.

### 1.1 Diagramme d'architecture globale

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              CLIENT (Browser)                                │
│                    Index.html / JavaScript / CSS                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ HTTP POST /search
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                          COUCHE API (server.py)                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │ FastAPI     │  │ Endpoints   │  │ Caches      │  │ Modules externes    │ │
│  │ + Uvicorn   │  │ REST/JSON   │  │ (mémoire)   │  │ (analyse, email...) │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      COUCHE ORCHESTRATION (search.py)                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────────────┐ │
│  │ Détection langue │  │ Résolution       │  │ Routage intelligent        │ │
│  │ (Unicode/DeepL)  │  │ sémantique       │  │ standard→IA→DeepL          │ │
│  └──────────────────┘  └──────────────────┘  └────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        COUCHE RECHERCHE (trouve.py)                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────────────────┐ │
│  │ Chargement       │  │ Détection        │  │ Garde-fou                  │ │
│  │ modules détection│  │ (detall/detia)   │  │ (gardefou.py)              │ │
│  └──────────────────┘  └──────────────────┘  └────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                     ┌────────────────┴────────────────┐
                     ▼                                 ▼
        ┌────────────────────┐            ┌────────────────────┐
        │   detall.py        │            │   detia.py         │
        │   (Mode standard)  │            │   (Mode IA)        │
        │   Patterns/Tags    │            │   Eden AI/OpenAI   │
        └────────────────────┘            └────────────────────┘
                     │                                 │
                     └────────────────┬────────────────┘
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      COUCHE SQL (jsonsql.py + lancesql.py)                   │
│  ┌──────────────────────────┐      ┌──────────────────────────────────────┐ │
│  │ jsonsql.py               │      │ lancesql.py                          │ │
│  │ JSON critères → SQL      │  →   │ Exécution SQLite + formatage         │ │
│  └──────────────────────────┘      └──────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                          ┌─────────────────────┐
                          │   base{N}.db        │
                          │   SQLite            │
                          └─────────────────────┘
```

### 1.2 Flux de données principal

Une recherche traverse les couches dans l'ordre suivant :

1. **server.py** : Réception HTTP, validation, logging
2. **search.py** : Détection langue, traduction, routage intelligent
3. **trouve.py** : Orchestration détection, garde-fou
4. **detall.py/detia.py** : Analyse sémantique → JSON critères
5. **jsonsql.py** : JSON critères → Requête SQL
6. **lancesql.py** : Exécution SQL → Résultats formatés

---

## 2. Couche API — server.py

### 2.1 Responsabilités

Le module `server.py` (v1.0.50) est le point d'entrée unique de l'application. Il utilise **FastAPI** avec **Uvicorn** comme serveur ASGI.

**Fonctions principales :**
- Exposition des endpoints REST/JSON
- Gestion des caches en mémoire (illustrations, portraits, moteurs IA, i18n)
- Logging des requêtes
- Notifications email pour feedback utilisateur
- Traduction à la volée des pages d'aide (DeepL)

### 2.2 Architecture des endpoints

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/search` | POST | Recherche patients (multilingue) |
| `/ia` | GET | Liste des moteurs IA disponibles |
| `/ia/{moteur}` | PUT | Activer/désactiver un moteur |
| `/ia/ask` | POST | Interroger un LLM avec contexte |
| `/ia/cohorte` | POST | Analyse de cohorte par IA |
| `/i18n` | GET | Textes UI traduits |
| `/params` | GET | Paramètres (langues actives) |
| `/help/{lang}` | GET | Mode d'emploi traduit |
| `/analyse/*` | GET | Dashboard analytics |

### 2.3 Cycle de vie (Lifespan)

Au démarrage, le serveur exécute les opérations suivantes dans `lifespan()` :

```python
@asynccontextmanager
async def lifespan(app):
    # 1. Configuration des chemins
    BASES_DIR = SCRIPT_DIR / "bases"
    REFS_DIR = SCRIPT_DIR / "refs"
    
    # 2. Chargement des fichiers de référence
    #    - illustrations.csv → ILLUSTRATIONS_CACHE
    #    - portraits.csv → PORTRAITS_CACHE
    #    - ia.csv → IA_CACHE, IA_FULL_CACHE
    #    - glossaire.csv → I18N_CACHE (type=ui)
    #    - commentaires.csv → COMMENTAIRES_CACHE
    
    # 3. Création répertoires si absents (logs/, ihm/)
    
    yield  # Application en cours d'exécution
    
    # 4. Cleanup (si nécessaire)
```

### 2.4 Endpoint /search — Flux détaillé

```python
@app.post("/search")
async def search_patients(request: SearchRequest):
    # 1. Extraction paramètres
    question = request.question
    base = request.base or "base100.db"
    mode = request.mode or "standard"
    lang = request.lang or "auto"
    
    # 2. Génération session_id (UUID)
    session_id = str(uuid.uuid4())
    
    # 3. Appel search.search()
    resultat = search_func(
        question=question,
        base_path=base_path,
        lang=lang,
        mode_detection=mode,
        session_id=session_id,
        ip_utilisateur=ip
    )
    
    # 4. Enrichissement des résultats
    #    - Ajout URLs portraits
    #    - Ajout commentaires pathologies
    #    - Traduction pathologies si lang != fr
    
    # 5. Logging dans logrecherche.csv
    
    return resultat
```

**Voir Annexe A** pour un exemple complet de requête/réponse.

---

## 3. Couche Orchestration — search.py

### 3.1 Responsabilités

Le module `search.py` (v1.0.28) est l'orchestrateur principal de la recherche multilingue. Il gère :

- Détection automatique de la langue
- Résolution sémantique via glossaire
- Traduction vers le français (glossaire prioritaire, DeepL fallback)
- Routage intelligent avec escalades automatiques
- Logging enrichi dans `logrecherche.csv`

### 3.2 Modes de recherche

| Mode | Description | Fallback |
|------|-------------|----------|
| `standard` | detall.py (patterns, tags, adjectifs) | → IA → DeepL |
| `ia` | detia.py (LLM via Eden AI) | → DeepL |
| `purstandard` | detall.py uniquement | Aucun |
| `puria` | detia.py uniquement | Aucun |

### 3.3 Algorithme de routage intelligent

Le routage intelligent est le cœur de search.py. Il maximise les chances de trouver des résultats :

```
┌─────────────────────────────────────────────────────────────────┐
│                    ROUTAGE INTELLIGENT                          │
│                                                                 │
│  Question (lang=X) ──────────────────────────────────────────┐  │
│         │                                                    │  │
│         ▼                                                    │  │
│  ┌─────────────────┐                                         │  │
│  │ 1. STANDARD     │ detall.py                               │  │
│  │    (patterns)   │                                         │  │
│  └────────┬────────┘                                         │  │
│           │                                                  │  │
│      nb > 0 ?                                                │  │
│      ╱    ╲                                                  │  │
│    OUI    NON                                                │  │
│     │      │                                                 │  │
│     │      ▼                                                 │  │
│     │  ┌─────────────────┐                                   │  │
│     │  │ 2. IA (fallback)│ detia.py 🤖                      │  │
│     │  │    (LLM)        │                                   │  │
│     │  └────────┬────────┘                                   │  │
│     │           │                                            │  │
│     │      nb > 0 ?                                          │  │
│     │      ╱    ╲                                            │  │
│     │    OUI    NON ──── lang != 'fr' ?                      │  │
│     │     │      │       ╱          ╲                        │  │
│     │     │      │     OUI          NON ── FIN (0 résultat)  │  │
│     │     │      │      │                                    │  │
│     │     │      │      ▼                                    │  │
│     │     │      │  ┌─────────────────┐                      │  │
│     │     │      │  │ 3. DEEPL        │ traduction 🌐       │  │
│     │     │      │  │    complète     │                      │  │
│     │     │      │  └────────┬────────┘                      │  │
│     │     │      │           │                               │  │
│     │     │      │           ▼                               │  │
│     │     │      │  ┌─────────────────┐                      │  │
│     │     │      │  │ 4. STANDARD     │ avec question FR     │  │
│     │     │      │  │    (retry)      │                      │  │
│     │     │      │  └────────┬────────┘                      │  │
│     │     │      │           │                               │  │
│     │     │      │      nb > 0 ?                             │  │
│     │     │      │      ╱    ╲                               │  │
│     │     │      │    OUI    NON                             │  │
│     │     │      │     │      │                              │  │
│     │     │      │     │      ▼                              │  │
│     │     │      │     │  ┌─────────────────┐                │  │
│     │     │      │     │  │ 5. IA (retry)   │ 🤖🌐          │  │
│     │     │      │     │  └────────┬────────┘                │  │
│     │     │      │     │           │                         │  │
│     └─────┴──────┴─────┴───────────┴─────── RÉSULTAT         │  │
│                                                              │  │
│  Indicateurs : 🤖 = IA utilisée, 🌐 = traduction DeepL       │  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.4 Parcours de détection

Le champ `parcours_detection` trace les escalades :

| Parcours | Signification |
|----------|---------------|
| `standard:42` | Résultat direct (42 patients) |
| `standard:0→ia:15` | Fallback IA après échec standard |
| `standard:0→ia:0→deepl→standard:8` | Traduction puis standard |
| `standard:0→ia:0→deepl→ia:3` | Traduction puis IA |

**Voir Annexe B** pour des exemples de parcours complets.

### 3.5 Résolution sémantique via glossaire

Avant d'interroger trouve.py, search.py résout les termes médicaux :

```python
def resoudre_question_semantique(question: str, lang: str) -> Tuple[str, List[str]]:
    """
    Résout une question d'une langue vers le français via glossaire.csv.
    
    Algorithme :
    1. Charger le dictionnaire lang→fr depuis glossaire.csv
    2. Normaliser la question (minuscules, sans accents)
    3. Chercher les expressions les plus longues d'abord
    4. Remplacer chaque match par son équivalent français
    5. Retourner (question_résolue, mots_non_résolus)
    
    Exemple :
        "歯ぎしり" (ja) → "bruxisme" (fr)
        "offener Biss" (de) → "béance" (fr)
    """
```

---

## 4. Couche Recherche — trouve.py

### 4.1 Responsabilités

Le module `trouve.py` (v1.0.18) orchestre le pipeline de recherche :

- Chargement dynamique des modules de détection
- Appel du détecteur approprié (detall ou detia)
- Génération SQL via jsonsql.py
- Exécution SQL via lancesql.py
- Activation du garde-fou si nécessaire

### 4.2 Fonction principale rechercher()

```python
def rechercher(
    question: str,
    db_path: Path,
    mode: str = "standard",      # standard | ia
    model: str = None,           # gpt41mini, sonnet, etc.
    include_details: bool = True,
    verbose: bool = False
) -> dict:
    """
    Pipeline complet :
    
    ÉTAPE 1 : Charger le module de détection
              mode='standard' → detall.py
              mode='ia' → detia.py
    
    ÉTAPE 2 : Exécuter la détection
              question → JSON critères
    
    ÉTAPE 3 : Générer le SQL
              JSON critères → SQL (via jsonsql.py)
    
    ÉTAPE 4 : Exécuter le SQL
              SQL → résultats (via lancesql.py)
    
    ÉTAPE 5 : Vérifier le garde-fou
              Si aucun critère ET >100 résultats → blocage
    """
```

### 4.3 Garde-fou (gardefou.py)

Le garde-fou empêche les requêtes trop larges (retournant >80% de la base) :

```python
# Déclenchement si :
# - Aucun critère de FILTRAGE détecté (pas de tag, age, sexe)
# - Plus de 100 résultats retournés

if len(criteres_filtrage) == 0 and nb_resultats > 100:
    verdict = verifier_intention_tous(question, [], verbose)
    
    if not verdict['intention_tous']:
        return {
            "gardefou": True,
            "gardefou_raison": verdict['raison'],
            "gardefou_message": "Veuillez préciser votre recherche",
            "gardefou_suggestions": ["bruxisme", "femmes", "moins de 20 ans"]
        }
```

---

## 5. Couche SQL — jsonsql.py et lancesql.py

### 5.1 jsonsql.py — Génération SQL

Ce module transforme le JSON de détection en requête SQL paramétrisée.

**Format d'entrée (JSON de detall/detia) :**
```json
{
    "listcount": "LIST",
    "criteres": [
        {
            "type": "tag",
            "canonique": "béance",
            "gn": "f",
            "adjectifs": [
                {"canonique": "antérieur", "forme_accordee": "antérieure"}
            ]
        },
        {
            "type": "sexe",
            "sql": {"valeur": "F"}
        },
        {
            "type": "age",
            "sql": {"operateur": "BETWEEN", "valeur": [14, 18]}
        }
    ]
}
```

**Format de sortie :**
```json
{
    "sql": "SELECT DISTINCT p.id, p.prenom, ...\nFROM patients p\nJOIN patients_pathologies pp1 ON p.id = pp1.patient_id\nJOIN pathologies pa1 ON pp1.pathologie_id = pa1.id\nWHERE pa1.pathologie = ?\nAND p.sexe = ?\nAND p.age BETWEEN ? AND ?",
    "params": ["beance anterieure", "F", 14, 18],
    "listcount": "LIST",
    "debug_clauses": [
        "tag: béance + [antérieure] → pathologie = 'beance anterieure'",
        "sexe = 'F'",
        "age BETWEEN 14 AND 18"
    ]
}
```

### 5.2 Construction des pathologies

Point critique : les adjectifs sont **accordés** au genre du tag :

```python
def _construire_pathologie_complete(tag_canonique: str, adjectifs: list) -> str:
    """
    tag='béance' (f) + adj='antérieur' → 'béance antérieure'
    tag='encombrement' (m) + adj='antérieur' → 'encombrement antérieur'
    
    L'accord est fait dans detall.py/detia.py via forme_accordee.
    jsonsql.py utilise cette forme accordée (pas le canonique).
    """
    # Extraire les formes ACCORDÉES (pas les canoniques)
    adjs_accordes = [adj.get('forme_accordee', adj.get('canonique')) 
                    for adj in adjectifs]
    
    # Trier alphabétiquement (convention de la base)
    adjs_tries = sorted(adjs_accordes)
    
    # Construire et standardiser
    pathologie = f"{tag_canonique} {' '.join(adjs_tries)}"
    return standardise(pathologie)  # "beance anterieure"
```

### 5.3 lancesql.py — Exécution SQL

Ce module exécute la requête SQL sur la base SQLite :

```python
def executer_sql(sql_dict: dict, db_path: Path, include_details: bool = True) -> dict:
    """
    Exécute la requête et formate les résultats.
    
    Modes :
    - COUNT : Retourne uniquement le nombre
    - LIST : Retourne les détails des patients
    
    Retour :
    {
        "nb": 42,
        "ids": [1, 5, 12, ...],
        "patients": [
            {"id": 1, "prenom": "Marie", "nom": "Dupont", 
             "sexe": "F", "age": 16.5, "oripathologies": "béance antérieure"}
        ],
        "temps_ms": 12.5
    }
    """
```

**Voir Annexe C** pour le schéma de la base de données.

---

## 6. Stratégies de traduction

### 6.1 Architecture de traduction

KITVIEW Search utilise une stratégie hybride :

```
┌─────────────────────────────────────────────────────────────────┐
│                    STRATÉGIE DE TRADUCTION                      │
│                                                                 │
│  Question (langue X) ────────────────────────────────────────┐  │
│         │                                                    │  │
│         ▼                                                    │  │
│  ┌─────────────────────────────────────────────────────────┐ │  │
│  │ ÉTAPE 1 : Détection Unicode (rapide, sans API)          │ │  │
│  │           Scripts non-latins : ja, cn, th, ar           │ │  │
│  └─────────────────────────────────────────────────────────┘ │  │
│         │                                                    │  │
│         ▼                                                    │  │
│  ┌─────────────────────────────────────────────────────────┐ │  │
│  │ ÉTAPE 2 : Recherche dans GLOSSAIRE.CSV (prioritaire)    │ │  │
│  │           ~2200 termes médicaux × 12 langues            │ │  │
│  │           Résultat : termes trouvés traduits en FR      │ │  │
│  └─────────────────────────────────────────────────────────┘ │  │
│         │                                                    │  │
│         │ Résidu (mots non trouvés)                          │  │
│         ▼                                                    │  │
│  ┌─────────────────────────────────────────────────────────┐ │  │
│  │ ÉTAPE 3 : DEEPL API (fallback)                          │ │  │
│  │           Traduit le résidu vers le français            │ │  │
│  │           Cache pour optimiser les appels               │ │  │
│  └─────────────────────────────────────────────────────────┘ │  │
│         │                                                    │  │
│         ▼                                                    │  │
│  Question en français technique ─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 Glossaire contrôlé (glossaire.csv)

Le glossaire est le référentiel central des traductions médicales :

```csv
type;fr;en;de;es;it;ja;pt;pl;ro;th;ar;cn
o;bruxisme;bruxism;Bruxismus;bruxismo;bruxismo;歯ぎしり;bruxismo;bruksizm;bruxism;การนอนกัดฟัน;صرير الأسنان;磨牙症
o;béance;open bite;offener Biss;mordida abierta;morso aperto;開咬;mordida aberta;zgryz otwarty;mușcătură deschisă;การสบฟันเปิด;العضة المفتوحة;开颌
```

**Types de termes :**
- `o` : Orthodontie (pathologies)
- `a` : Adjectifs médicaux
- `p` : Permanent (mots fondamentaux)
- `c` : Courant
- `z` : Ne pas traduire (copier tel quel)

### 6.3 Pourquoi glossaire > DeepL ?

| Critère | Glossaire | DeepL |
|---------|-----------|-------|
| Précision médicale | ✅ Contrôlée | ❌ Variable |
| Latence | ✅ <1ms | ⚠️ 100-500ms |
| Coût | ✅ Gratuit | ⚠️ Payant |
| Disponibilité | ✅ Hors ligne | ❌ Réseau requis |

**Exemple de problème DeepL :**
```
"offener Biss" (de) 
  → DeepL : "occlusion ouverte" ❌ (traduction littérale)
  → Glossaire : "béance" ✅ (terme médical correct)
```

### 6.4 Module traduire.py

Ce module implémente la stratégie hybride :

```python
def traduire(texte: str, source_lang: str, target_lang: str = 'fr',
             api_key: str = None, verbose: bool = False) -> Tuple[str, str]:
    """
    Traduit un texte avec glossaire prioritaire + DeepL fallback.
    
    Retourne :
        (texte_traduit, fournisseur)
        
        fournisseur :
        - 'glossaire' : tout trouvé dans glossaire
        - 'deepl' : tout traduit par DeepL
        - 'glossaire+deepl' : hybride
        - 'none' : aucune traduction effectuée
    """
```

### 6.5 Détection de langue Unicode

Pour les scripts non-latins, une pré-détection rapide évite les appels API :

```python
def detecter_langue_unicode(texte: str) -> Tuple[str, float, dict]:
    """
    Détecte la langue par analyse des caractères Unicode.
    
    Plages utilisées :
    - Japonais : Hiragana (3040-309F), Katakana (30A0-30FF)
    - Chinois : CJK Unifié (4E00-9FFF)
    - Thaï : Thai (0E00-0E7F)
    - Arabe : Arabic (0600-06FF)
    
    Distinction JA/CN :
    - Présence de kana → Japonais certain
    - Uniquement CJK → Chinois
    
    Exemple :
        "歯ぎしり" → ('ja', 0.95, {'hiragana': 2, 'cjk': 1})
        "磨牙症" → ('cn', 0.90, {'cjk': 3})
    """
```

---

## 7. Configuration des moteurs IA (ia.csv)

### 7.1 Structure du fichier

```csv
moteur;via;actif;complet;cout;notes;image
standard;;O;standard avec ia;0.10;Recherche standard avec fallback IA;...
ia;;O;gpt-4.1-mini par défaut;0.40;Recherche IA avec fallback DeepL;...
gpt41mini;openai;O;gpt-4.1-mini;0.40;GPT-4.1 Mini - RECOMMANDÉ;...
sonnet;eden;O;anthropic/claude-3-7-sonnet-20250219;3.00;Claude Sonnet;...
deepseekr1;eden;O;deepseek/deepseek-r1;0.55;DeepSeek R1 🇨🇳;...
```

### 7.2 Passerelles API

| `via` | Description | Endpoint |
|-------|-------------|----------|
| `openai` | API OpenAI directe | api.openai.com |
| `eden` | Eden AI (gateway multi-provider) | api.edenai.run |
| (vide) | Mode standard (pas d'IA) | - |

---

## 8. Logging et analytics

### 8.1 Structure de logrecherche.csv

```csv
module;timestamp;temps_ms;languesaisie;langueutilisee;modulelangue;questionoriginale;question;filtres;sql;tri;base;mode;nb_patients;pathologies;ages;residu;erreur;session_id;ip_utilisateur;rating;type_probleme;commentaire
```

### 8.2 Champs clés

| Champ | Description |
|-------|-------------|
| `languesaisie` | Langue demandée (auto, fr, de...) |
| `langueutilisee` | Langue effectivement détectée |
| `modulelangue` | Source de traduction (glossaire, deepl, glossaire+deepl) |
| `parcours_detection` | Trace des escalades (standard:0→ia:15) |
| `rating` | Feedback utilisateur (👍 ou 👎) |

---

## Annexes

### Annexe A — Exemple requête/réponse /search

**Requête POST /search :**
```json
{
    "question": "offener Biss bei Frauen unter 20",
    "base": "base100.db",
    "mode": "standard",
    "lang": "auto"
}
```

**Réponse JSON :**
```json
{
    "auteur": "cx",
    "question_originale": "offener Biss bei Frauen unter 20",
    "question_resolue": "béance femmes moins de 20 ans",
    "question_affichee": "béance femmes moins de 20 ans",
    "question_technique_fr": "béance femmes moins de 20 ans",
    "lang": "de",
    "response_lang": "de",
    "mode_detection": "standard",
    "parcours_detection": "standard:8",
    "indicateurs_routage": "",
    "nb_patients": 8,
    "patients": [
        {
            "id": 42,
            "prenom": "Sophie",
            "nom": "M.",
            "sexe": "F",
            "age": 16.5,
            "oripathologies": "offener Biss, Tiefbiss",
            "portrait_url": "https://..."
        }
    ],
    "message": "8 Patienten gefunden",
    "description_filtres": "offener Biss + Frauen + unter 20",
    "temps_ms": 145,
    "session_id": "a1b2c3d4-..."
}
```

### Annexe B — Exemples de parcours de détection

| Question | Lang | Parcours | Résultat |
|----------|------|----------|----------|
| "bruxisme" | fr | `standard:42` | Direct |
| "xyz123" | fr | `standard:0→ia:0→(no deepl)` | Échec |
| "Tiefbiss" | de | `standard:0→ia:12` | Fallback IA |
| "歯ぎしり" | ja | `standard:35` | Glossaire OK |
| "dentes tortos" | pt | `standard:0→ia:0→deepl→standard:15` | Traduction DeepL |

### Annexe C — Schéma base de données

```sql
-- Table principale des patients
CREATE TABLE patients (
    id INTEGER PRIMARY KEY,
    canontags TEXT,           -- Tags standardisés (bruxisme, beance...)
    canonadjs TEXT,           -- Adjectifs standardisés
    sexe TEXT,                -- M ou F
    age DECIMAL(5, 3),        -- Âge en années décimales
    datenaissance DATE,
    prenom TEXT,
    nom TEXT,
    idportrait TEXT,          -- Clé pour portrait
    oripathologies TEXT,      -- Pathologies originales (affichage)
    pathologies TEXT          -- Pathologies standardisées
);

-- Table des pathologies uniques
CREATE TABLE pathologies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pathologie TEXT UNIQUE NOT NULL  -- Forme standardisée
);

-- Table de jointure
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

### Annexe D — Variables d'environnement

| Variable | Description | Obligatoire |
|----------|-------------|-------------|
| `DEEPL_API_KEY` | Clé API DeepL | Non (fallback glossaire) |
| `EDENAI_API_KEY` | Clé API Eden AI | Oui (mode IA) |
| `OPENAI_API_KEY` | Clé API OpenAI | Non (si Eden) |
| `SMTP_SERVER` | Serveur SMTP notifications | Non |
| `SMTP_USER` | Utilisateur SMTP | Non |
| `SMTP_PASSWORD` | Mot de passe SMTP | Non |

---

## Références fichiers

| Fichier | Version | Rôle |
|---------|---------|------|
| server.py | 1.0.50 | API FastAPI |
| search.py | 1.0.28 | Orchestration multilingue |
| trouve.py | 1.0.18 | Pipeline recherche |
| jsonsql.py | 1.0.6 | Génération SQL |
| lancesql.py | 1.0.4 | Exécution SQL |
| traduire.py | 1.0.6 | Traduction hybride |
| traduis.py | 1.0.11 | CLI traduction |
| glossaire.csv | 1.1.0 | Référentiel multilingue |
| ia.csv | 1.0.15 | Configuration moteurs IA |

---

**Fin du document**
