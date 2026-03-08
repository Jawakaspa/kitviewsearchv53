# Prompt Fiche_modes_recherche V1.0.0 - 09/01/2026 19:21:56

# Fiche thématique : Modes de recherche KITVIEW

**Version** : 1.0  
**Date** : 09/01/2026  
**Fichiers concernés** : `search.py`, `trouve.py`, `ia.csv`

---

## Vue d'ensemble

KITVIEW propose **4 modes de détection** pour la recherche de patients, chacun avec un comportement différent en termes de fallback automatique.

| Mode | Moteur principal | Fallback IA | Fallback DeepL | Usage |
|------|------------------|-------------|----------------|-------|
| `standard` | detall.py | ✅ Oui | ✅ Oui | **Production** (défaut) |
| `ia` | detia.py | - | ✅ Oui | Production avec IA |
| `purstandard` | detall.py | ❌ Non | ❌ Non | Tests / Debug |
| `puria` | detia.py | - | ❌ Non | Tests / Debug |

---

## Moteurs de détection

### detall.py (détection algorithmique)
- **Auteur** : `cx`
- **Coût** : Gratuit (0$)
- **Principe** : Patterns regex, tags.csv, adjectifs.csv, angles.csv, ages.csv
- **Vitesse** : Très rapide (~50-100ms)
- **Limitation** : Ne comprend que les formulations prévues dans les référentiels

### detia.py (détection par IA)
- **Auteur** : Variable selon le modèle (ex: `eden/gpt41mini`)
- **Coût** : Variable (0.15$ à 15$ / million de tokens selon modèle)
- **Principe** : Prompt envoyé à un LLM qui extrait les critères
- **Vitesse** : Plus lent (~500-2000ms selon modèle)
- **Avantage** : Comprend les reformulations, fautes d'orthographe, synonymes

---

## Diagrammes de flux détaillés

### MODE STANDARD (défaut)

```
Question utilisateur
        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│  ÉTAPE 1 : STANDARD (detall.py)                                   │
│  Parcours: "standard:N"                                           │
└───────────────────────────────────────────────────────────────────┘
        │
        ├── Si N > 0 ────────────────────────────────────────────────► FIN ✅
        │   Mode effectif: "standard"                                  Résultat direct
        │
        ▼ Si N = 0
┌───────────────────────────────────────────────────────────────────┐
│  ÉTAPE 2 : FALLBACK IA (detia.py) 🤖                              │
│  Parcours: "standard:0→ia:N"                                      │
└───────────────────────────────────────────────────────────────────┘
        │
        ├── Si N > 0 ────────────────────────────────────────────────► FIN ✅
        │   Mode effectif: "ia (standardia)"                           L'IA a trouvé
        │   Indicateur: 🤖
        │
        ▼ Si N = 0 ET langue ≠ fr ET clé DeepL présente
┌───────────────────────────────────────────────────────────────────┐
│  ÉTAPE 3 : TRADUCTION DEEPL 🌐                                    │
│  Traduit la question originale vers le français                   │
│  Parcours: "standard:0→ia:0→deepl"                                │
└───────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│  ÉTAPE 3a : RETRY STANDARD avec question traduite                 │
│  Parcours: "standard:0→ia:0→deepl→standard:N"                     │
└───────────────────────────────────────────────────────────────────┘
        │
        ├── Si N > 0 ────────────────────────────────────────────────► FIN ✅
        │   Mode effectif: "standard (standarddeepl)"                  DeepL a aidé
        │   Indicateur: 🌐
        │
        ▼ Si N = 0
┌───────────────────────────────────────────────────────────────────┐
│  ÉTAPE 3b : RETRY IA avec question traduite 🤖🌐                  │
│  Parcours: "standard:0→ia:0→deepl→standard:0→ia:N"                │
└───────────────────────────────────────────────────────────────────┘
        │
        ▼
    FIN (même si N = 0)
    Mode effectif: "ia (iadeepl)"
    Indicateurs: 🤖🌐
```

### MODE IA (forcé)

```
Question utilisateur
        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│  ÉTAPE 1 : IA DIRECTE (detia.py) 🤖                               │
│  Parcours: "ia:N"                                                 │
└───────────────────────────────────────────────────────────────────┘
        │
        ├── Si N > 0 ────────────────────────────────────────────────► FIN ✅
        │   Mode effectif: "ia"                                        Résultat IA direct
        │
        ▼ Si N = 0 ET langue ≠ fr ET clé DeepL présente
┌───────────────────────────────────────────────────────────────────┐
│  ÉTAPE 2 : TRADUCTION DEEPL 🌐                                    │
│  Traduit la question originale vers le français                   │
│  Parcours: "ia:0→deepl"                                           │
└───────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│  ÉTAPE 2a : RETRY IA avec question traduite 🤖🌐                  │
│  Parcours: "ia:0→deepl→ia:N"                                      │
└───────────────────────────────────────────────────────────────────┘
        │
        ▼
    FIN (même si N = 0)
    Mode effectif: "ia (iadeepl)"
    Indicateur: 🌐
```

### MODE PURSTANDARD (sans fallback)

```
Question utilisateur
        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│  STANDARD UNIQUEMENT (detall.py)                                  │
│  Parcours: "purstandard:N"                                        │
│  AUCUN FALLBACK                                                   │
└───────────────────────────────────────────────────────────────────┘
        │
        ▼
    FIN (quel que soit N)
    Mode effectif: "purstandard"
```

### MODE PURIA (sans fallback)

```
Question utilisateur
        │
        ▼
┌───────────────────────────────────────────────────────────────────┐
│  IA UNIQUEMENT (detia.py) 🤖                                      │
│  Parcours: "puria:N"                                              │
│  AUCUN FALLBACK DEEPL                                             │
└───────────────────────────────────────────────────────────────────┘
        │
        ▼
    FIN (quel que soit N)
    Mode effectif: "puria"
```

---

## Modes effectifs dans les logs

| Mode effectif | Signification | Parcours typique |
|---------------|---------------|------------------|
| `standard` | Résultat direct detall.py | `standard:42` |
| `purstandard` | Standard sans fallback | `purstandard:42` |
| `ia` | Résultat direct detia.py | `ia:42` |
| `puria` | IA sans fallback | `puria:42` |
| `ia (standardia)` | Standard échoué → IA OK | `standard:0→ia:42` |
| `standard (standarddeepl)` | DeepL → Standard OK | `standard:0→ia:0→deepl→standard:42` |
| `ia (iadeepl)` | DeepL → IA | `standard:0→ia:0→deepl→standard:0→ia:42` |

---

## Indicateurs de routage (emojis)

| Emoji | Signification |
|-------|---------------|
| 🤖 | Fallback IA utilisé |
| 🌐 | Traduction DeepL utilisée |
| 🤖🌐 | IA + DeepL utilisés |

Ces emojis apparaissent dans :
- Le champ `question_affichee` (ex: "bruxisme 🤖")
- Le champ `indicateurs_routage`
- Les logs de recherche

---

## Configuration dans ia.csv

```csv
moteur;via;actif;complet;cout;notes;image
standard;;O;;0;Recherche standard avec fallback IA si 0 résultat;...
purstandard;;O;;0;Recherche standard SANS fallback (tests/debug);...
puria;;O;;0;Recherche IA SANS fallback DeepL (tests/debug);...
gpt41mini;openai;O;gpt-4.1-mini;0.40;GPT-4.1 Mini - RECOMMANDÉ;...
...
```

**Notes sur ia.csv** :
- Les modes `standard`, `purstandard` et `puria` ont `via` vide (pas de modèle IA externe pour la détection)
- `puria` utilise quand même un modèle IA via detia.py, mais le champ `via` dans ia.csv ne concerne que la configuration affichée
- Le modèle IA réellement utilisé est déterminé par le paramètre `--model` ou le défaut (`gpt41mini`)

---

## Usage CLI

```bash
# Mode standard (défaut) - avec tous les fallbacks
python search.py base25000.db "bruxisme"

# Mode standard explicite
python search.py base25000.db "bruxisme" standard

# Mode IA avec modèle par défaut
python search.py base25000.db "bruxisme" ia

# Mode IA avec modèle spécifique
python search.py base25000.db "bruxisme" ia sonnet

# Mode PURSTANDARD - standard seul, pas de fallback
python search.py base25000.db "bruxisme" purstandard

# Mode PURIA - IA seule, pas de fallback DeepL
python search.py base25000.db "bruxisme" puria

# Mode PURIA avec modèle spécifique
python search.py base25000.db "bruxisme" puria gpt41mini
```

---

## Quand utiliser chaque mode ?

| Situation | Mode recommandé |
|-----------|-----------------|
| **Production normale** | `standard` (défaut) |
| **Forcer l'IA** | `ia` |
| **Test de performance detall.py** | `purstandard` |
| **Test de qualité detia.py** | `puria` |
| **Debug : pourquoi standard ne trouve pas ?** | `purstandard` puis `puria` |
| **Comparaison standard vs IA** | Lancer `purstandard` puis `puria` |
| **Question en langue étrangère** | `standard` (avec fallback DeepL) |

---

## Conditions de déclenchement des fallbacks

### Fallback IA (standard → ia)
- **Déclenché si** : `nb_resultats == 0`
- **Non déclenché si** : Mode `purstandard`

### Fallback DeepL (→ deepl)
- **Déclenché si** : 
  - `nb_resultats == 0` après tentative(s) précédente(s)
  - ET `langue != 'fr'`
  - ET `clé DeepL présente` (variable d'environnement ou paramètre)
- **Non déclenché si** : 
  - Mode `purstandard` ou `puria`
  - Ou langue = français
  - Ou pas de clé DeepL

---

## Fichiers impactés

| Fichier | Rôle |
|---------|------|
| `search.py` | Orchestration du routage intelligent, gestion des fallbacks |
| `trouve.py` | Appel à detall.py ou detia.py selon le mode |
| `ia.csv` | Configuration des modes pour l'interface web |
| `detall.py` | Moteur de détection algorithmique |
| `detia.py` | Moteur de détection par IA |

---

*Document mis à jour le 09/01/2026*
