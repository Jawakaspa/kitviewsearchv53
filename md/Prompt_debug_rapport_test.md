# Prompt_debug_rapport_test.md

## Objectif

Modifications de 3 fichiers Python pour supporter la **triple détection** dans le pipeline de test detfull, avec rapport DOCX enrichi.

---

## Fichiers modifiés

### 1. detfull.py — Exécution batch + rapport DOCX

**Changements :**
- **Modules virtuels** : `trouve_ia`, `trouve_iabrut`, `search_purstandard`, `search_puria`
  - Chaque module virtuel appelle le script réel avec des arguments supplémentaires
  - Mapping dans `MODULES_VIRTUELS` : `{'trouve_ia': ('trouve', ['ia'], '_ia'), ...}`
- **Rapport DOCX** :
  - Légende des couleurs ajoutée en début de rapport (section 🎨)
  - Tableaux comparatifs entre méthodes (fonction `_generer_tableau_comparatif`)
  - Coloration routage (vert pour `Routage:`)
- **Helpers ajoutés** :
  - `_extraire_nb_patients()` : extrait N de "→ N patient(s) en Xms"
  - `_extraire_routage()` : extrait emoji de "Routage: 🤖"
  - `_generer_tableau_comparatif()` : tableau Question × N méthodes

**CLI :**
```
python detfull.py quentin.csv base1964.db        # Tout
python detfull.py quentin.csv base1964.db -v      # Verbose
python detfull.py quentin.csv base1964.db --no-ia # Sans IA
python detfull.py quentin.csv base1964.db --only=trouve_ia  # Un seul module
```

### 2. trouve.py — Ajout mode iabrut

**Changements :**
- `_charger_module_detection()` : 3 modes → `standard`, `ia`, `iabrut`
  - `iabrut` charge `detiabrut.py` (charger_references, detecter_tout)
- **CLI** : `iabrut` reconnu comme mode valide
- **Batch** : suffixe de mode dans le nom du fichier de sortie
  - `standard` → `quentintrouve.csv`
  - `ia` → `quentintrouve_ia.csv`
  - `iabrut` → `quentintrouve_iabrut.csv`

**CLI :**
```
python trouve.py base1964.db "patients classe 2"           # Standard
python trouve.py base1964.db "patients classe 2" ia         # IA
python trouve.py base1964.db "patients classe 2" iabrut     # IA brut
python trouve.py base1964.db quentin.csv                    # Batch standard
python trouve.py base1964.db quentin.csv ia                 # Batch IA
python trouve.py base1964.db quentin.csv iabrut             # Batch IA brut
```

### 3. search.py — Suffixe mode dans sortie batch

**Changement unique :**
- Fichier de sortie batch inclut le suffixe de mode si ≠ standard
  - `standard` → `quentinsearch.csv`
  - `purstandard` → `quentinsearch_purstandard.csv`
  - `puria` → `quentinsearch_puria.csv`

---

## PJ nécessaires pour recréer

- `Prompt_contexte0502.md` (projet)
- `Prompt_debug_rapport_test.md` (ce fichier)
- Modules de détection : `detall.py`, `detia.py`, `detiabrut.py`
- Modules SQL : `jsonsql.py`, `lancesql.py`
- Modules recherche : `trouveid.py`, `gardefou.py`
- Fichiers CSV de test : `quentin.csv`
- Base de données : `base1964.db` (dans bases/)

---

## Bug identifié : purstandard web ≠ CLI

**Symptôme :** Sur Render en mode "purstandard", 2 patients trouvés en 3449ms.
En CLI avec `trouve.py` (standard), 0 patients en 18ms.

**Cause :** Le web utilise en réalité l'IA malgré le label "purstandard".
- Preuve par le temps : 3449ms = appel IA, pas 18ms = standard
- Preuve par les tags : detia détecte "classe ii squelettique" (2 résultats), detall détecte "classe ii d'angle" (0 résultat)

**Action :** Vérifier le code déployé sur Render — soit le search.py est une ancienne version, soit le frontend envoie le mauvais paramètre `mode_detection`.
