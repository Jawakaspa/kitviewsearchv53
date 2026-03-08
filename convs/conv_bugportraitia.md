# Prompt conv_bugportraitia V1.0.0 - 28/01/2026 14:55:26

# Synthèse de conversation : bugportraitia

**Projet** : KITVIEW Search - Application de recherche multilingue orthodontique

---

## Session du 28 janvier 2026

### 17:42 UTC - Signalement du bug

**Problème signalé** :
- Recherche "même portrait que Guillaume Moulin"
- **Mode standard** : 458 patients trouvés ✓
- **Mode IA (purstandard/puria)** : 0 patient trouvé ✗

**Captures d'écran fournies** : 2 images montrant le comportement différent

---

### 17:47 UTC - Analyse des fichiers sources

**Fichiers analysés** :
- `server.py` V1.0.52 - API FastAPI
- `search.py` V1.0.28 - Module de recherche avec routage intelligent
- `trouve.py` V1.0.19 - Orchestrateur du pipeline
- `detall.py` V1.0.10 - Détection mode standard
- `detia.py` V1.0.29 - Détection mode IA
- `detmeme.py` V1.0.7 - Détection des expressions "même X"
- `trouveid.py` V1.0.5 - Identification patient de référence

---

### Diagnostic établi

**Cause racine identifiée** :
- En mode **standard** : `detall.py` appelle `detmeme.py` (étape 1.5 du pipeline)
- En mode **IA** : `detia.py` **n'appelle JAMAIS** `detmeme.py`

**Pipeline mode standard** (fonctionne) :
```
Question → detcount → detmeme → detangles → dettags → detage → motsvides → JSON
                ↓
          detecte "même portrait"
          extrait référence "Guillaume Moulin"
                ↓
          trouveid.py enrichit avec idportrait
                ↓
          jsonsql.py génère SQL correct
```

**Pipeline mode IA** (bug) :
```
Question → IA (Eden/OpenAI) → JSON
                ↓
          L'IA ne connaît PAS les critères "même"
          Prompt système ne mentionne pas les similarités
                ↓
          Aucun critère détecté → 0 résultat
```

---

### Solutions proposées

**Option A** (Recommandée) : Pré-traitement `detmeme` dans `detia.py`
- Appeler `detmeme.py` AVANT d'envoyer à l'IA
- Même logique que `detall.py`
- Module déjà testé et fonctionnel

**Option B** : Enrichir le prompt IA
- Ajouter les critères "même" dans le prompt système
- Plus complexe, nécessite extraction du nom de référence par l'IA

**Option C** : Post-traitement dans `trouve.py`
- Appeler `detmeme` après l'IA si aucun critère "meme" détecté
- Risque de conflits d'interprétation

---

### 18:02 UTC - Validation et implémentation

**Option choisie** : **A** - Pré-traitement `detmeme` dans `detia.py`

**Fichiers créés** :

| Fichier | Description |
|---------|-------------|
| `detia.py` V1.0.30 | Version corrigée avec intégration de `detmeme.py` |
| `Prompt_detia_systeme.md` | Extraction du prompt système IA |

---

## Modifications apportées à detia.py V1.0.30

### Imports ajoutés
```python
# Import de detmeme pour pré-traitement des similarités
try:
    from detmeme import charger_patterns_meme, detecter_meme
    DETMEME_DISPONIBLE = True
except ImportError:
    DETMEME_DISPONIBLE = False
```

### Nouveau cache
```python
_PATTERNS_MEME_CACHE = None
```

### Nouvelle fonction
```python
def get_patterns_meme(refs_dir, verbose, debug) -> dict
```

### Modification de `charger_references()`
- Ajout du chargement de `patterns_meme` via `get_patterns_meme()`

### Modification de `detecter_tout()`
- **Pré-traitement** : Appel à `detecter_meme()` AVANT l'IA
- Extraction des critères "même" et de la référence patient
- Envoi de la question résiduelle à l'IA
- Fusion des critères : `meme` + `IA`
- Propagation de `reference` dans le JSON de sortie

### Pipeline corrigé
```
Question
    │
    ▼
┌─────────────────┐
│  detmeme.py     │  → Critères "même" + référence patient
└────────┬────────┘
         │
    ▼
┌─────────────────┐
│  IA (OpenAI/    │  → Critères tags, ages, sexe
│  Eden AI)       │     (sur question résiduelle)
└────────┬────────┘
         │
    ▼
┌─────────────────┐
│  motsvides      │  → Nettoyage résidu
└────────┬────────┘
         │
         ▼
     JSON unifié
```

---

## Prompt de recréation de detia.py

Pour recréer `detia.py` V1.0.30 à partir de zéro :

### Fichiers PJ nécessaires
1. `Prompt_contexte1301.md` - Règles du projet
2. `detia.py` V1.0.29 - Version précédente (optionnel, pour référence)
3. `detmeme.py` - Module de détection des similarités
4. `Prompt_detia_systeme.md` - Prompt système IA

### Prompt
```
Contexte : Projet KITVIEW Search (voir Prompt_contexte1301.md en PJ)

Objectif : Corriger detia.py pour intégrer detmeme.py en pré-traitement

Bug identifié : En mode IA, les critères "même X" (même portrait, même âge, etc.) 
ne sont pas détectés car detia.py n'appelle pas detmeme.py.

Solution : Intégrer detmeme.py en PRÉ-TRAITEMENT dans detecter_tout() :
1. Appeler detmeme.detecter_meme() sur la question originale
2. Extraire les critères "même" et la référence patient
3. Envoyer la question RÉSIDUELLE à l'IA
4. Fusionner les critères : meme + IA
5. Propager la référence dans le JSON de sortie

Le pipeline doit être : detmeme → IA → motsvides

Fichiers fournis :
- detmeme.py : Module à intégrer (voir fonctions charger_patterns_meme, detecter_meme)
- Prompt_detia_systeme.md : Prompt système IA (ne pas modifier)

Contraintes :
- Respecter le format de sortie JSON existant
- Ajouter la clé 'reference' si des critères "même" sont détectés
- Cache global _PATTERNS_MEME_CACHE pour les patterns detmeme
- Si la question est entièrement consommée par detmeme, ne pas appeler l'IA

Génère detia.py V1.0.30 complet.
```

---

## Test de validation

Commande CLI pour tester le fix :
```bash
python detia.py "même portrait que Guillaume Moulin" gpt4o -v
```

Résultat attendu :
- 1 critère de type "meme" avec cible "portrait"
- Référence : "Guillaume Moulin"
- Latence IA : 0ms (car question consommée par detmeme)

---

*Document mis à jour : 28/01/2026 18:10 UTC*
