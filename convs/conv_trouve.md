# Prompt conv_trouve V1.0.0 - 18/12/2025 20:00:03

# Synthèse conversation : trouve

**Projet** : Kitview - Recherche multilingue de patients orthodontiques  
**Date de début** : 18/12/2025 15:42 UTC

---

## Échange 1 - 18/12/2025 15:42 UTC

### Question
Thierry signale plusieurs problèmes avec `trouve.py` :

1. **Bug mode traditionnel** : La recherche sans IA retourne 0 résultats alors que ça marchait. Le warning "Âge(s) implicite(s) ignoré(s) car âge explicite présent" indique une régression causée par la dernière modification sur les âges implicites/explicites.

2. **Mode mix demandé** : Nouvelle option pour comparer côte à côte les résultats des deux méthodes (traditionnel vs IA) dans un tableau comparatif.

3. **Champ auteur** : Ajouter un champ `auteur` dans le JSON pour identifier la source :
   - `"cx"` pour detall
   - `"eden/claude-sonnet-3.7"` pour detia via Eden (simplifié)
   - `"anthropic/claude-sonnet-3.7"` pour detia en direct
   - `"cxgti"` pour le mode union (fusion des deux)

4. **Mode union** : Nouvelle option qui :
   - Exécute detall puis detia
   - Fusionne les résultats (union mathématique)
   - Affiche les détails : commun, cx_seul (uniquement detall), ia_seul (uniquement detia)
   - Affiche les 10 premiers IDs de chaque catégorie

5. **Affichage JSON systématique** : Toujours afficher le JSON à la fin.

### Analyse

**Bug mode traditionnel** :
- `detage.py` (lignes 531-563) supprime les âges implicites quand un âge explicite est présent
- "femme de moins de 25 ans" → sexe=F + ~~age>=18~~ + age<25
- Résultat : 0 patients car la condition est trop large (femmes de 0 à 25 ans au lieu de 18 à 25)

**Correction demandée** :
- "femme de moins de 25 ans" doit signifier : sexe=F ET 18<=age<25
- Garder les deux critères d'âge au lieu de supprimer l'implicite

**Bug mode IA** :
- L'IA retourne des critères vides → SQL sans WHERE → 100 résultats

### Fichiers fournis
- `trouve.py` V1.0.2
- `detall.py` V1.0.5
- `detia.py` V1.0.5
- `detage.py` V1.0.3
- `jsonsql.py` V1.0.0
- `lancesql.py` V1.0.0

### Fichiers à modifier
| Fichier | Modification |
|---------|-------------|
| `detage.py` | Retirer la suppression des âges implicites (garder tous les critères) |
| `detall.py` | Ajouter champ `"auteur": "cx"` |
| `detia.py` | Ajouter champ `"auteur": "eden/..." ou "anthropic/..."` |
| `trouve.py` | Ajouter modes `mix` et `union`, afficher JSON systématiquement |

### Réponse
Corrections effectuées :

| Fichier | Modifications |
|---------|--------------|
| `detage.py` | Suppression du post-traitement lignes 531-563. Tous les critères d'âge sont gardés. |
| `detall.py` | Ajout du champ `"auteur": "cx"` dans le JSON de sortie |
| `detia.py` | Ajout fonction `_construire_auteur()` + champ `"auteur": "eden/..."` |
| `trouve.py` | Ajout modes `mix` et `union`, affichage JSON systématique |

**Comportement corrigé :**
- "femme de moins de 25 ans" → sexe=F + age>=18 + age<25 (combinés avec AND)

---

## Prompts de recréation

### detage.py
**Fichiers PJ nécessaires** : `Prompt_contexte0412.md`

```
Crée un module Python `detage.py` pour détecter les critères d'âge et de sexe dans une question en langage naturel.

FONCTIONNALITÉS :
1. Charger les patterns depuis `refs/ages.csv` (format : expression;operateur;valeur_sql;sexe;label)
2. Détecter les critères de sexe (homme/femme/garçon/fille) et d'âge (moins de X ans, entre X et Y ans, etc.)
3. Retourner des critères SÉPARÉS au format JSON unifié

FORMAT DE SORTIE JSON :
{
    "criteres": [
        {"type": "sexe", "detecte": "femme", "label": "Féminin", "sql": {"colonne": "sexe", "operateur": "=", "valeur": "F"}},
        {"type": "age", "detecte": "moins de 25 ans", "label": "Moins de 25 ans", "sql": {"colonne": "age", "operateur": "<", "valeur": 25}},
        {"type": "age", "detecte": "femme", "label": "Adulte (>=18)", "sql": {"colonne": "age", "operateur": ">=", "valeur": 18}}
    ],
    "residu": "texte restant"
}

RÈGLES IMPORTANTES :
- NE PAS supprimer les âges implicites quand un âge explicite est présent
- Garder TOUS les critères détectés pour qu'ils soient combinés avec AND dans le SQL
- "femme de moins de 25 ans" = sexe=F + age>=18 + age<25

Fonctions principales :
- charger_patterns_ages(fichier_csv, verbose, debug) → liste de patterns
- detecter_age(question, patterns_ages, verbose, debug) → dict JSON
```

### detall.py
**Fichiers PJ nécessaires** : `Prompt_contexte0412.md`, `detcount.py`, `detangles.py`, `dettags.py`, `detage.py`, `motsvides.py`

```
Crée un module Python `detall.py` orchestrateur du pipeline de détection V2.

PIPELINE :
Question → detcount → detangles → dettags → detage → motsvides → JSON

FORMAT DE SORTIE JSON :
{
    "auteur": "cx",
    "langue": "fr",
    "listcount": "COUNT" ou "LIST",
    "criteres": [...],
    "residu": "...",
    "question_originale": "...",
    "question_standardisee": "..."
}

Le champ "auteur" vaut toujours "cx" (pour Kitview classique).
```

### detia.py
**Fichiers PJ nécessaires** : `Prompt_contexte0412.md`, fichiers CSV de références

```
Crée un module Python `detia.py` pour détecter les critères via IA (Eden AI).

FORMAT DE SORTIE JSON (identique à detall.py + métadonnées IA) :
{
    "auteur": "eden/claude-sonnet-3.7",  // ou "anthropic/..." si direct
    "langue": "fr",
    "listcount": "COUNT" ou "LIST",
    "criteres": [...],
    "residu": "...",
    "ia_model": "...",
    "ia_latency_ms": ...
}

Le champ "auteur" est construit ainsi :
- Via Eden AI : "eden/" + nom simplifié du modèle
- En direct : provider + "/" + nom simplifié
```

### trouve.py
**Fichiers PJ nécessaires** : `Prompt_contexte0412.md`, `detall.py`, `detia.py`, `jsonsql.py`, `lancesql.py`

```
Crée un module Python `trouve.py` orchestrateur du pipeline complet de recherche.

MODES DE RECHERCHE :
- "traditionnel" (défaut) : utilise detall.py
- "ia" : utilise detia.py
- "mix" : exécute les deux et affiche une comparaison côte à côte
- "union" : fusionne les résultats (A ∪ B) avec détail commun/cx_seul/ia_seul

AFFICHAGE MIX :
Tableau comparatif avec colonnes Traditionnel et IA montrant :
- Temps de détection
- Temps SQL
- Nombre de résultats
- Critères détectés

AFFICHAGE UNION :
- Résultat fusionné (union des IDs)
- Détail : commun (A ∩ B), cx_seul (A - B), ia_seul (B - A)
- 10 premiers IDs de chaque catégorie

IMPORTANT :
- Toujours afficher le JSON complet à la fin
- Le champ "auteur" du JSON reflète le mode utilisé
```

---
