# Prompt conv_search_server V1.0.2 - 19/12/2025 19:18:08

# conv_search_server.md

## Synthèse de conversation - search.py et endpoint /search

---

## Session du 18/12/2025 16:45 UTC

### Demande initiale

Créer `search.py` pour remplacer `suche.py` (qui utilisait `cherche.py`) par une nouvelle architecture utilisant `trouve.py` avec support des modes de détection traditionnel/IA/mix/union.

Ajouter l'endpoint `/search` dans `server.py`.

### Contexte

Problèmes identifiés dans la capture d'écran (interface japonaise) :

| Élément | État | Origine | Solution |
|---------|------|---------|----------|
| "bruxisme" bandeau | Français | description_filtres | Traduire via pathoori.csv |
| "19 ans" | "ans" en français | Base de données | Ajouter unit_year traduite |
| Pathologies patients | ✓ Traduites | OK | Via pathoori.csv |

### Fichiers créés

#### 1. search.py

**Architecture** :
```
Question (any lang) → search.py → trouve.py → Résultats traduits
```

**Modes de détection** :
- `traditionnel` : detall.py (regex, synonymes) → auteur: "cx"
- `ia` : detia.py (Claude via Eden AI) → auteur: "eden/claude-sonnet-3.7"
- `mix` : Compare les deux méthodes côte à côte
- `union` : Fusionne les résultats (A ∪ B) → auteur: "cxgti"

**Traductions gérées** :
- Pathologies patients via pathoori.csv (lookup uniquement, pas d'API)
- Description filtres (terme recherché) via pathoori.csv
- Unité d'âge (unit_year) via messages.csv
- Messages UI via messages.csv

**Langues natives** : fr, en, de, es, it, pt, pl, ro, th, ar, cn, ja

#### 2. server.py (mis à jour)

**Nouvel endpoint** : `POST /search`

---

## Session du 18/12/2025 17:20 UTC

### Bugs signalés et corrigés

#### Bug 1 : dettags.py - Paramètre inexistant

**Ligne 582** : Appel avec `langue='fr'` qui n'existe pas dans la signature de `charger_tags()`

**Impact** : `TypeError: charger_tags() got an unexpected keyword argument 'langue'`

**Correction** : Suppression du paramètre `langue='fr'`

#### Bug 2 : detia.py - L'IA ne détecte pas "bruxisme"

**Symptôme** : Le mode IA retourne `criteres_detectes: []` pour "bruxisme"

**Cause** : Prompt insuffisant, pas d'exemples concrets

**Correction** :
- Ajout de 3 exemples concrets (bruxisme seul, femmes+âge+béance, combien+classe II)
- Règle explicite "CHERCHE ACTIVEMENT chaque mot dans syntags.csv"
- Règle "Si la question est juste un terme médical, c'est un critère tag"
- Augmentation taille CSV syntags de 8000 à 10000 caractères

#### Bug 3 : Absence de garde-fou "tous les patients"

**Symptôme** : Si détection échoue → retourne TOUS les patients (100 sur 100)

**Solution** : Nouveau module `gardefou.py`

### Nouveau fichier : gardefou.py

Module de vérification "dernière chance" avant de retourner tous les patients.

**Logique** :
1. Vérifier si l'utilisateur veut vraiment TOUS les patients
   - Mots explicites : "tous", "tout", "all", "alle", "everyone"
   - Phrases : "tous les patients", "sans filtre", "liste complète"

2. Vérifier si la question ressemble à une recherche de pathologie
   - Correspondance LIKE% avec syntags.csv
   - Termes médicaux (suffixes -isme, -ite, -gnathie...)
   - Contexte pathologique ("avec", "ayant", "présentant"...)

3. Décision finale :
   - Intention "tous" confirmée → OK
   - Ressemble à pathologie → bloquer + suggérer
   - Ambigu → bloquer par sécurité

**Cas traités** :

| Situation | Verdict | Action |
|-----------|---------|--------|
| "tous les patients" | ✅ intention_tous | Retourner tout |
| "bruxisme" (non détecté mais LIKE% ok) | ❌ tag_exact_non_detecte | Suggérer "Bruxisme" |
| "brux" (LIKE% partiel) | ❌ tag_partiel_suggere | Suggérer "Bruxisme" |
| "patients avec xyz" | ❌ contexte_patho_sans_tag | Demander reformulation |
| Question vide ou 1 mot inconnu | ❌ question_trop_courte | Demander précision |

### Intégration dans trouve.py (FAIT)

**Modifications apportées** :

1. **Import du garde-fou** (lignes 66-78) :
```python
try:
    from gardefou import verifier_intention_tous, charger_syntags_pour_gardefou
    GARDEFOU_DISPONIBLE = True
except ImportError:
    GARDEFOU_DISPONIBLE = False
```

2. **Nouvelles fonctions** :
   - `_charger_syntags_gardefou()` : Charge les syntags une seule fois (cache)
   - `_compter_total_patients()` : Compte le total de la base pour le seuil

3. **Étape 4 dans `rechercher()`** (après exécution SQL) :
```python
# Seuil = 80% de la base ou minimum 50
seuil_alerte = max(total_base * 0.8, 50)

# Activer si : beaucoup de résultats ET pas de critères filtrants
criteres_filtrants = [c for c in criteres if c.get('type') != 'count']

if nb_patients >= seuil_alerte and len(criteres_filtrants) == 0:
    verdict = verifier_intention_tous(question, syntags_gardefou)
    if not verdict['intention_tous']:
        return {..., "garde_fou": {"actif": True, ...}, "erreur": verdict['message']}
```

4. **Nouveau champ `auteur`** dans le résultat :
   - Mode traditionnel → `"cx"`
   - Mode IA → `"eden/claude-sonnet-3.7"` (ou depuis json_detection)

5. **Nouveau champ `garde_fou`** dans le résultat :
```json
{
    "garde_fou": {
        "actif": true/false,
        "raison": "tag_exact_non_detecte",
        "message": "Le terme 'bruxisme' correspond...",
        "suggestions": ["Bruxisme"]
    }
}
```

6. **Affichage CLI amélioré** :
   - Affiche l'auteur
   - Affiche le garde-fou s'il est activé avec suggestions

### Fichiers à fournir en PJ pour recréer

**dettags.py** : `Prompt_contexte0412.md`

**detia.py** : `Prompt_contexte0412.md` + `detia.py` (version corrigée)

**gardefou.py** : `Prompt_contexte0412.md` + description du besoin

### Livrables

Fichiers dans `/mnt/user-data/outputs/` :
- `search.py` - Module de recherche multilingue
- `server.py` - Serveur FastAPI mis à jour
- `Prompt_search.md` - Prompt de documentation
- `dettags.py` - Bug paramètre corrigé
- `detia.py` - Prompt IA amélioré
- `gardefou.py` - Garde-fou "tous les patients"
- `trouve.py` - **Avec intégration garde-fou** ⭐
- `Prompt_gardefou.md` - Prompt pour recréer gardefou.py
- `conv_search_server.md` - Cette synthèse

### Travail restant

1. ~~**Intégrer gardefou.py dans trouve.py**~~ ✅ FAIT
2. **Tester detia.py corrigé** avec "bruxisme"
3. **Tester trouve.py** avec le garde-fou
4. **Page web** : Traduction des éléments UI

---

## Notes techniques

### Amélioration du prompt detia.py

**Avant** : "Si aucun critère trouvé, retourne un tableau criteres vide"

**Après** : 
- 3 exemples concrets avec JSON attendu
- "CHERCHE ACTIVEMENT chaque mot dans syntags.csv"
- "Si la question est juste un terme médical, c'est un critère tag"

### Garde-fou - Mots d'intention "tous"

```python
MOTS_INTENTION_TOUS = {
    'tous', 'tout', 'toutes', 'tous les patients',
    'all', 'everyone', 'alle patienten', 'todos',
    'sans filtre', 'liste complete', ...
}
```

### Garde-fou - Détection termes médicaux

```python
SUFFIXES_MEDICAUX = [
    'isme', 'ite', 'ose', 'ie', 'pathie', 'plasie',
    'gnathie', 'doncie', 'occlus', 'dental', 'orthodont'
]
```
