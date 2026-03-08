# Prompt conv_search_web V1.0.3 - 22/12/2025 22:36:23

# conv_search_web.md

## Synthèse de conversation - Intégration search.py dans l'interface web

---

## Session du 22/12/2025 21:50 UTC

### Tests CLI réussis ✅

Tous les modes fonctionnent en CLI :
- `rapide` : 26 patients en 21ms
- `ia` : 26 patients en 4422ms  
- `compare` : 26 patients en 4033ms
- `union` : 26 patients en 730ms (auteur: cxgti)
- Japonais : 歯軋り → 26 patients avec "歳" au lieu de "ans"

### Problèmes identifiés pour v2

1. **Modes compare/union** : Ne montrent pas les différences en CLI
2. **Arguments CLI** : `--mode=` et `--lang=` obligatoires alors que les valeurs sont distinctes
3. **Choix modèle IA** : Pas possible en CLI (toujours Sonnet)
4. **Langues hardcodées** : Liste dans server.py au lieu de commun.csv

### Prompt créé pour prochaine conversation

Fichier `Prompt_search_v2.md` avec :
- Enrichissement de commun.csv (colonnes modele_court, modele_via, modele_complet)
- Arguments CLI flexibles (détection auto des mots)
- Choix du modèle IA (`ia sonnet`, `ia gpt4o`, etc.)
- Affichage compare/union amélioré
- server.py lit langues depuis commun.csv

---

## Session du 22/12/2025 20:05 UTC

### Correction de trouve.py

**Erreur rencontrée** :
```
cannot import name 'rechercher_compare' from 'trouve'
```

**Cause** : `trouve.py` n'avait que `rechercher()`, pas les fonctions `rechercher_compare()` et `rechercher_union()`.

### Modifications apportées à trouve.py

#### 1. Renommage `traditionnel` → `rapide`
```python
# AVANT
mode: str = "traditionnel"

# APRÈS
mode: str = "rapide"
```

#### 2. Recherche automatique dans `bases/`
```python
# Fonction rechercher()
if not db_path.exists():
    script_dir = Path(__file__).parent
    base_in_bases = script_dir / "bases" / db_path.name
    if base_in_bases.exists():
        db_path = base_in_bases
```

#### 3. Nouvelles fonctions ajoutées

**`rechercher_compare()`** : Compare rapide vs IA
```python
def rechercher_compare(question, db_path, ...) -> dict:
    """
    Returns:
        {
            "rapide": {...résultats mode rapide...},
            "ia": {...résultats mode IA...},
            "comparaison": {
                "communs": [ids],
                "uniquement_rapide": [ids],
                "uniquement_ia": [ids]
            }
        }
    """
```

**`rechercher_union()`** : Fusionne les résultats (A ∪ B)
```python
def rechercher_union(question, db_path, ...) -> dict:
    """
    Returns:
        {
            "nb": len(union),
            "ids": [...],
            "patients": [...],  # avec champ 'source': 'rapide'|'ia'|'both'
            "auteur": "cxgti"
        }
    """
```

**Alias** pour compatibilité : `rechercher_mix = rechercher_compare`

#### 4. Simplification de search.py

Suppression du mapping `rapide` → `traditionnel` puisque trouve.py accepte maintenant `rapide` directement.

### Fichiers livrés

| Fichier | Lignes | Description |
|---------|--------|-------------|
| **trouve.py** | ~800 | Renommé rapide, recherche bases/, fonctions compare/union |
| **search.py** | ~1230 | Import simplifié, plus de mapping |
| **server.py** | ~500 | Inchangé |

### Test à effectuer

```bash
python trouve.py base100.db "bruxisme"
# Devrait trouver la base dans bases/ automatiquement

python search.py bases/base100.db "bruxisme"
# Devrait retourner 26 patients
```

---

## Session du 22/12/2025 19:30 UTC

### Diagnostic du problème

**Symptôme** : `search.py "bruxisme"` retourne "ERREUR: Module trouve.py non disponible" alors que `trouve.py "bruxisme"` fonctionne (26 patients)

**Analyse des tests CLI** :
```
dettags.py "bruxisme" → ✓ 1 critère détecté (Bruxisme)
detall.py "bruxisme"  → ✓ Auteur: cx, Mode: LIST
trouve.py bases/base100.db "bruxisme" → ✓ 26 patients
search.py bases/base50000.db "bruxisme" → ❌ Module trouve.py non disponible
```

**Causes identifiées** :

1. **Import trouve.py échoue** : `search.py` n'ajoutait pas son répertoire au `sys.path`
2. **Chemins hardcodés** : `RACINE = r"c:\g"` au lieu de détection automatique
3. **Base non trouvée** : Pas de recherche dans `bases/` si chemin relatif
4. **Nomenclature incohérente** : `traditionnel` vs `rapide`, `mix` vs `compare`

### Corrections apportées

#### 1. search.py - Correction complète

```python
# AVANT : Chemin hardcodé
RACINE = r"c:\g"

# APRÈS : Détection automatique + ajout au path
SCRIPT_DIR = Path(__file__).parent.resolve()
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

RACINE = str(SCRIPT_DIR)
BASES_DIR = SCRIPT_DIR / "bases"
REFS_DIR = SCRIPT_DIR / "refs"
```

**Autres corrections** :
- Import de `rechercher_compare` au lieu de `rechercher_mix`
- Recherche automatique dans `bases/` si la base n'existe pas
- Renommage : `traditionnel` → `rapide`, `mix` → `compare`
- Mapping temporaire `rapide` → `traditionnel` pour trouve.py (en attendant modification de trouve.py)

#### 2. server.py - Nettoyage complet

**Supprimés** :
- Import de `cherche.py` et `suche.py`
- Endpoints `/cherche` et `/suche`
- Toutes les références aux anciens modules

**Modifié** :
- Modes valides : `['rapide', 'ia', 'compare', 'union']`
- Messages de log simplifiés
- Code réduit de 948 → ~500 lignes

#### 3. web2.html - Cohérence des valeurs

```javascript
// AVANT
let detectionMode = 'traditionnel';
<option value="traditionnel" selected>⚡ Rapide</option>

// APRÈS  
let detectionMode = 'rapide';
<option value="rapide" selected>⚡ Rapide</option>
```

### Flux de données corrigé

```
web2.html           server.py           search.py           trouve.py
    │                   │                   │                   │
    ├─ mode_detection   │                   │                   │
    │  = "rapide"  ────►│                   │                   │
    │                   ├─ mode_detection   │                   │
    │                   │  = "rapide"  ────►│                   │
    │                   │                   ├─ mapping:         │
    │                   │                   │  rapide→tradition │
    │                   │                   │  nel pour trouve ─►│
    │                   │                   │                   │
```

### Fichiers livrés

| Fichier | Lignes | Description |
|---------|--------|-------------|
| `server.py` | ~500 | Nettoyé, uniquement /search |
| `search.py` | ~1230 | Corrigé imports + chemins |
| `web2.html` | ~5870 | Cohérence rapide/compare |

### À faire : modifier trouve.py

Pour finaliser, il faut modifier `trouve.py` pour :
1. Accepter "rapide" au lieu de "traditionnel"
2. Accepter "compare" au lieu de "mix"

Ensuite supprimer le mapping dans search.py.

---

## Session du 22/12/2025 16:00 UTC

### Problème rencontré

Erreur JavaScript lors de la recherche :
```
Cannot read properties of null (reading 'toUpperCase')
at createLangInfoMessage (web2.html:3593:73)
```

### Causes identifiées

1. **Endpoint incorrect** : web2.html appelait `/suche` au lieu de `/search`
2. **lang_detectee null** : La fonction `createLangInfoMessage` ne gérait pas le cas où `lang_detectee` est `null`
3. **Valeur mode invalide** : Le frontend envoyait `"rapide"` mais le serveur attend `"traditionnel"`

### Corrections appliquées

```javascript
// 1. Endpoint corrigé
function getSearchEndpoint() {
    return '/search';  // ✅ au lieu de '/suche'
}

// 2. Protection contre null
function createLangInfoMessage(langDetectee, langSelectionnee) {
    if (!langDetectee) {  // ✅ Nouvelle vérification
        return null;
    }
    // ...
}

// 3. Valeur technique correcte
<option value="traditionnel" selected>⚡ Rapide</option>  // ✅ au lieu de value="rapide"
```

### Limitation identifiée

Le serveur (`server.py`) n'accepte que 4 modes de détection :
- `traditionnel`
- `ia`
- `mix` (renommé `compare`)
- `union`

Les modèles spécifiques (`eden/claude-sonnet-3.7`, `eden/gpt-4o`, etc.) ne sont **pas encore supportés** côté serveur.

**Solution temporaire** : Le select affiche "⚡ Rapide" mais envoie `"traditionnel"` au serveur.

**À faire plus tard** : Ajouter un champ `ia_model` dans SearchRequest pour supporter le choix du modèle IA.

---

## Session du 19/12/2025 18:22 UTC

### Demande initiale

Remplacer l'appel à `/suche` par `/search` dans la page web, avec intégration du nouveau système de modes de détection (Rapide, Eden AI, etc.).

### Contexte récupéré

Conversation précédente retrouvée : **"Correction régression trouve et options de comparaison"**
- URL : https://claude.ai/chat/54d55311-2246-45a1-8034-3dfe45392206
- Synthèse existante : `conv_search_server.md`

### Fichiers analysés

| Fichier | Rôle |
|---------|------|
| `web1.html` | Page web actuelle utilisant `/suche` |
| `search.py` | Nouveau module utilisant `trouve.py` |
| `server.py` | Serveur avec endpoint `/search` ajouté |
| `detia.py` | Module de détection IA avec liste des modèles |

### Modifications apportées (web2.html)

#### 1. Changement d'endpoint

```javascript
// AVANT (web1.html)
function getSearchEndpoint() {
    return '/suche';
}

// APRÈS (web2.html)
function getSearchEndpoint() {
    return '/search';
}
```

#### 2. Nouveau payload avec mode_detection

```javascript
function buildSearchPayload(query) {
    let effectiveMode = detectionMode;
    let mode2 = null;
    
    if (compareMode) {
        effectiveMode = 'compare';
        mode2 = detectionMode2;
    } else if (unionMode) {
        effectiveMode = 'union';
        mode2 = detectionMode2;
    }
    
    return {
        question: query,
        base: currentBase,
        mode_detection: effectiveMode,  // ⭐ Nouveau
        mode_detection_2: mode2,         // ⭐ Pour compare/union
        lang: selectedLanguage,
        lang_reponse: responseLanguage,
        limit: resultsLimit,
        offset: 0,
        api_key: deeplKey || null
    };
}
```

#### 3. Nouvelles variables JavaScript

```javascript
let detectionMode = 'rapide';  // Mode principal
let detectionMode2 = 'eden/claude-sonnet-3.7';  // Mode secondaire
let compareMode = false;  // ⚖️ Comparer
let unionMode = false;    // 🔗 Fusionner

const EDEN_MODELS = {
    'eden/claude-sonnet-3.7': 'Claude Sonnet 3.7',
    'eden/claude-opus-3': 'Claude Opus 3',
    'eden/claude-haiku-3.5': 'Claude Haiku 3.5',
    'eden/gpt-4o': 'GPT-4o',
    'eden/gpt-4o-mini': 'GPT-4o Mini',
    'eden/gemini-1.5-pro': 'Gemini 1.5 Pro',
    'eden/gemini-1.5-flash': 'Gemini 1.5 Flash',
    'eden/gemini-2.5-flash': 'Gemini 2.5 Flash'
};
```

#### 4. Interface utilisateur ajoutée

**Sélecteur de mode de détection** (dans le header) :
- ⚡ Rapide (ex-traditionnel)
- 🤖 Modèles Eden AI (optgroup)

**Checkboxes** :
- ⚖️ Comparer → Active le 2ème sélecteur
- 🔗 Fusionner → Active le 2ème sélecteur + cards bleues

**2ème sélecteur** : Visible uniquement si Comparer ou Fusionner activé

#### 5. Styles CSS ajoutés

```css
.detection-mode-controls { display: flex; gap: 8px; }
.detection-checkbox { width: 32px; height: 32px; }
.detection-mode2-container { display: flex; gap: 6px; }
.mode2-label { font-size: 12px; color: var(--text-secondary); }

/* Cards du 2ème mode (union) */
.patient-card-ia.union-mode-2 {
    background: linear-gradient(135deg, #1e3a5f, #2c5282);
    border-color: #3182ce;
}
```

### Modèles disponibles via Eden AI

Récupérés de `detia.py --list-models` :

| Alias | Modèle complet |
|-------|----------------|
| `claude-sonnet` | anthropic/claude-3-7-sonnet-20250219 |
| `claude-opus` | anthropic/claude-3-opus-latest |
| `claude-haiku` | anthropic/claude-3-5-haiku-latest |
| `gpt-4o` | openai/gpt-4o |
| `gpt-4o-mini` | openai/gpt-4o-mini |
| `gemini-pro` | google/gemini-1.5-pro |
| `gemini-flash` | google/gemini-1.5-flash |
| `gemini-2.5-flash` | google/gemini-2.5-flash |

### Format mode_detection envoyé au backend

| Situation | mode_detection | mode_detection_2 |
|-----------|----------------|------------------|
| Rapide seul | `rapide` | - |
| Eden AI seul | `eden/claude-sonnet-3.7` | - |
| Comparer | `compare` | `eden/gpt-4o` |
| Fusionner | `union` | `eden/gemini-2.5-flash` |

### Renommage effectué

- `traditionnel` → `rapide` (dans l'interface)
- `mix` → `compare` (dans le code)

### Fichiers livrés

| Fichier | Description |
|---------|-------------|
| `web2.html` | Page web avec `/search` et modes de détection |
| `conv_search_web.md` | Cette synthèse |

### Points à noter

1. **Responsive** : Les contrôles de détection sont masqués sur petits écrans (`@media max-width: 768px`)
2. **Mutually exclusive** : Comparer et Fusionner ne peuvent pas être activés simultanément
3. **Persistence** : Tous les settings sont sauvegardés dans localStorage
4. **Logs debug** : Affichent maintenant `mode_detection` et `auteur`

### Travail restant

1. **Backend** : Adapter `server.py` et `search.py` pour gérer `mode_detection_2`
2. **Affichage compare** : Implémenter l'affichage côte à côte des résultats
3. **Affichage union** : Appliquer la classe `union-mode-2` aux cards du 2ème mode
4. **Responsive** : Revoir l'organisation de la page pour petits écrans

---

## Prompts de recréation

### server.py

**Prompt :**
```
Créer server.py, serveur FastAPI pour l'API de recherche patients.

ARCHITECTURE SIMPLIFIÉE v4.0.0 :
- Uniquement endpoint /search via search.py + trouve.py
- Suppression de /cherche et /suche (legacy)
- Modes de détection : rapide, ia, compare, union

ENDPOINTS :
- GET /         - Page d'accueil
- GET /api      - Info API
- GET /health   - État du serveur
- GET /version  - Version
- GET /bases    - Liste des bases dans bases/
- GET /count    - Nombre de patients
- GET /illustrations - Bandeaux de résultats
- POST /search  - Recherche multilingue

MODÈLE SearchRequest :
- question: str
- base: str = "base100.db"
- lang: Optional[str] = "auto"
- lang_reponse: Optional[str] = "same"
- mode_detection: str = "rapide"  # rapide, ia, compare, union
- limit: int = 100
- offset: int = 0
- api_key: Optional[str] = None

CHEMINS :
- SCRIPT_DIR détecté automatiquement
- BASES_DIR = SCRIPT_DIR / "bases"
- REFS_DIR = SCRIPT_DIR / "refs"

Respecter Prompt_contexte0412.md
```

**Fichiers PJ nécessaires :**
- `search.py`
- `Prompt_contexte0412.md`

---

### search.py

**Prompt :**
```
Créer search.py, module de recherche multilingue utilisant trouve.py.

ARCHITECTURE :
Question (any lang) → search.py → trouve.py → Résultats traduits

FONCTIONS PRINCIPALES :
- search() : Point d'entrée multilingue
- charger_pathologies_multilingues() : Charge pathoori.csv
- charger_messages_multilingues() : Charge messages.csv

MODES DE DÉTECTION :
- "rapide" : detall.py (regex, synonymes)
- "ia" : detia.py (Claude via Eden AI)
- "compare" : Compare rapide vs IA
- "union" : Fusionne les résultats

CHEMINS AUTOMATIQUES :
- SCRIPT_DIR détecté via __file__
- sys.path.insert(0, SCRIPT_DIR) pour imports locaux
- BASES_DIR = SCRIPT_DIR / "bases"
- REFS_DIR = SCRIPT_DIR / "refs"

LANGUES NATIVES :
fr, en, de, es, it, pt, pl, ro, th, ar, cn, ja

FORMAT SORTIE :
{
    "auteur": "cx|eden/...|cxgti",
    "question_originale": "...",
    "question_traduite": "...",
    "lang": "ja",
    "response_lang": "same",
    "nb_patients": 42,
    "patients": [...],
    "description_filtres": "...",
    "temps_ms": 125
}

Respecter Prompt_contexte0412.md
```

**Fichiers PJ nécessaires :**
- `trouve.py`
- `traduire.py` (optionnel)
- `Prompt_contexte0412.md`

---

### web2.html

**Prompt :**
```
Créer web2.html, page web de recherche patients multilingue.

MODIFICATIONS PAR RAPPORT À web1.html :
1. Endpoint /search au lieu de /suche (utilise trouve.py)
2. Mode de détection "rapide" (valeur envoyée au serveur)
3. Ajouter sélecteur mode de détection : Rapide + modèles Eden AI
4. Ajouter checkboxes ⚖️ Comparer et 🔗 Fusionner
5. Afficher 2ème sélecteur si compare/union activé
6. Payload envoie mode_detection + mode_detection_2
7. Protection null sur lang_detectee dans createLangInfoMessage()

MODÈLES EDEN AI :
- eden/claude-sonnet-3.7, eden/claude-opus-3, eden/claude-haiku-3.5
- eden/gpt-4o, eden/gpt-4o-mini
- eden/gemini-1.5-pro, eden/gemini-1.5-flash, eden/gemini-2.5-flash

STYLES CSS :
- .detection-mode-controls, .detection-checkbox
- .patient-card-ia.union-mode-2 avec fond bleu foncé

PERSISTENCE localStorage :
- detectionMode (défaut: 'rapide'), detectionMode2, compareMode, unionMode

Respecter Prompt_contexte0412.md
```

**Fichiers PJ nécessaires :**
- `web1.html` (base)
- `Prompt_contexte0412.md`
