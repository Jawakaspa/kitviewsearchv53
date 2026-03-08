# Prompt conv_search_v2 V1.0.2 - 23/12/2025 18:13:46

# Synthèse conversation : search_v2

**Date de création** : 23/12/2025 01:15  
**Dernière mise à jour** : 23/12/2025 02:00

---

## Résumé de la conversation

### Objectif
Améliorer la chaîne de recherche `search.py → trouve.py → detia.py` avec :
1. Affichage CLI enrichi pour modes compare/union
2. Arguments flexibles (sans préfixe `--`)
3. Choix du modèle IA
4. Support accès direct OpenAI (GPT-4o, GPT-4o-mini)
5. **Nouveau fichier ia.csv** pour centraliser la configuration des modèles

---

## Échange 4 - 23/12/2025 02:00 (FINAL)

### Problème signalé
Erreur avec `gpt52` - le modèle GPT-5.2 n'existe pas sur l'API OpenAI

### Correction appliquée
- **ia.csv** : gpt52, gpt5mini, gpt5nano marqués comme **inactifs** (N)
- Modèles OpenAI actifs : `gpt4o` et `gpt4omini` uniquement

---

## Fichiers produits (version finale)

| Fichier | Version | Description |
|---------|---------|-------------|
| ia.csv | 1.0.1 | Configuration modèles IA - gpt5x désactivés |
| search.py | 2.0.0 | Charge modèles depuis ia.csv |
| trouve.py | 2.0.0 | Charge modèles depuis ia.csv |
| detia.py | 2.0.0 | Routing OpenAI/Eden selon ia.csv |

---

## Modèles IA disponibles (ia.csv)

**Modèles actifs** :
| Alias | Via | Description |
|-------|-----|-------------|
| rapide | - | Mode regex (pas d'IA) |
| sonnet | eden | Claude Sonnet 3.7 - **défaut** |
| opus | eden | Claude Opus 3 |
| haiku | eden | Claude Haiku 3.5 |
| **gpt4o** | openai | GPT-4o - recommandé OpenAI |
| **gpt4omini** | openai | GPT-4o-mini - économique |
| gemini25flash | eden | Gemini 2.5 Flash |
| gemini15pro | eden | Gemini 1.5 Pro |

**Modèles inactifs** (futurs ou remplacés) :
- gpt52, gpt5mini, gpt5nano → marqués `N` (non disponibles)
- gemini15flash → remplacé par gemini25flash

---

## Tests de validation

```bash
# Mode rapide (par défaut)
python search.py base100.db "bruxisme"

# Mode IA avec modèle par défaut (sonnet)
python search.py base100.db "bruxisme" ia

# Mode IA avec GPT-4o-mini (OpenAI direct) - RECOMMANDÉ
python search.py base100.db "bruxisme" gpt4omini

# Mode IA avec GPT-4o (OpenAI direct)
python search.py base100.db "bruxisme" gpt4o

# Mode compare
python search.py base100.db "bruxisme" compare

# Mode union
python search.py base100.db "bruxisme" union
```

---

## Installation

1. Copier `ia.csv` dans `c:\cx\refs\`
2. Copier `search.py`, `trouve.py`, `detia.py` dans `c:\cx\`
3. Configurer les clés API (voir ci-dessous)

---

## Configuration des clés API

### Windows (permanent)
1. `Win + R` → `sysdm.cpl` → Entrée
2. Onglet "Avancé" → "Variables d'environnement"
3. Nouvelle variable utilisateur :
   - `OPENAI_API_KEY` = `sk-proj-...`
   - `EDENAI_API_KEY` = `eyJ...` (si utilisé)

---

## Tâches restantes

1. ⏳ **server.py** : Lire langues depuis commun.csv
2. ⏳ **Refonte commun.csv** : Passer de colonnes à lignes

---

## Prompts pour recréer les fichiers

### ia.csv
```
Créer refs/ia.csv avec colonnes : court, via, actif, complet, cout, notes
Modèles actifs : rapide, sonnet, opus, haiku, gpt4o, gpt4omini, gemini25flash, gemini15pro
Modèles inactifs : gpt52, gpt5mini, gpt5nano, gemini15flash

PJ nécessaires : Prompt_contexte2312.md
```

### search.py, trouve.py, detia.py V2.0.0
```
Modifier pour charger les modèles IA depuis refs/ia.csv
Filtrer sur modèles actifs uniquement
Routing automatique : via=openai → OpenAI direct, via=eden → Eden AI

PJ nécessaires : ia.csv, Prompt_contexte2312.md
```

---

**FIN DE SYNTHÈSE**
