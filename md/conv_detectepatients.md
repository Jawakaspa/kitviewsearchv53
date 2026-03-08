# Synthèse de conversation : detectepatients

## Informations générales
- **Projet** : Application de recherche multilingue orthodontique
- **Date de début** : 04/02/2026

---

## Échange 3 - 04/02/2026 16:25

### Question
Pourquoi "adolescent" est détecté=0 alors qu'il est bien détecté comme `âge:adolescent` ?

### Diagnostic
Dans `importtest.py`, la fonction `compter_criteres_significatifs()` ne comptait que les types `tag`, `meme`, `angle` et **excluait** `age` et `sexe`.

Mais la colonne `attendu` du fichier de test compte **tous les critères**, pas seulement les pathologies.

### Solution
Modifier `compter_criteres_significatifs()` pour compter aussi `age` et `sexe` :

```python
# Avant : if c_type in ('tag', 'meme', 'angle'):
# Après :
if c_type in ('tag', 'meme', 'angle', 'age', 'sexe'):
    count += 1
```

Seul `count` (qui est un modificateur "combien", pas un critère de recherche) reste exclu.

### Fichier modifié
| Fichier | Modification |
|---------|--------------|
| importtest.py | Inclure age/sexe dans le comptage |

---

## Échange 2 - 04/02/2026 16:05

### Question
Pourquoi `detall` ne détecte pas "système de bielles" alors que `dettags` le détecte ?

### Diagnostic
Le problème venait de **detmeme.py** qui s'exécute AVANT dettags dans le pipeline de detall :

1. detmeme cherche des références avec le pattern `que/de/comme + texte` à la fin de la chaîne
2. "de" est un synonyme de "que" dans detmeme (pour "même X **de** Nom Patient")
3. "système **de** bielles" → detmeme interprète "de bielles" comme référence patient
4. Le texte "bielles" est consommé avant que dettags puisse le traiter

**JSON de detall (bugué) :**
```json
"reference": {
    "type": "nom",
    "valeur": "bielles",
    "id": null
}
```

### Solution
Ajout d'une **ÉTAPE 0** dans `detecter_meme()` qui vérifie la présence d'un synonyme de "même" AVANT d'extraire une référence :

```python
# ÉTAPE 0 (V1.0.8) : Vérifier s'il y a un synonyme de "même"
contient_meme = False
for syn_meme in synonymes_meme:
    pattern_check = re.compile(r'\b' + re.escape(syn_meme) + r's?\b', re.IGNORECASE)
    if pattern_check.search(question_norm):
        contient_meme = True
        break

if not contient_meme:
    return {'criteres': [], 'reference': None, 'residu': question_norm}
```

### Fichier modifié
| Fichier | Version | Modification |
|---------|---------|--------------|
| detmeme.py | 1.0.7 → **1.0.8** | Ajout vérification préalable "même" |

---

## Échange 1 - 04/02/2026 15:47

### Question
Créer un fichier `importtest.py` qui :
- Lit `/refs/importtest.csv` (25000 lignes de test)
- Utilise `detall` (puis plus tard `detia`) pour détecter les critères
- Compare avec la colonne `attendu` (nombre de critères attendus)
- Ajoute `nb_detall` et `detecte` (uniquement si différence)

**Structure du fichier importtest.csv :**
| Colonne | Description |
|---------|-------------|
| id | Identifiant de la ligne |
| test | Expression à tester |
| attendu | Nombre de critères attendus |
| oripathologies | Pathologies de référence (séparées par `,`) |

### Clarifications obtenues
1. Séparateur : `;` (même si copié depuis Excel avec tabs)
2. Localisation : `/refs/` (pas `/tests/` car sert de référence)
3. Sortie : même répertoire, nom auto (`importtest_result.csv`)
4. Colonne `detecte` : uniquement si différence avec `attendu`
5. Stratégie : d'abord `detall` seul, puis `detia` sur les différences résiduelles

### Réponse
**Fichier créé : `importtest.py`**

Fonctionnalités :
- Lecture CSV avec auto-détection encodage (utf-8-sig, utf-8, windows-1252)
- Auto-détection séparateur (tab ou `;`)
- Utilisation de `detall.detecter_tout()` pour chaque ligne
- Comptage des critères significatifs (tags, meme, angles - hors age/sexe/count)
- Barre de progression avec `tqdm`
- Génération du fichier `_result.csv` avec colonnes ajoutées

**Options CLI :**
- `--verbose` / `-v` : Affichage détaillé des différences
- `--debug` / `-d` : Mode debug
- `--limit N` / `-l N` : Limiter à N lignes (pour tests rapides)
- `--input` / `-i` : Fichier d'entrée personnalisé
- `--output` / `-o` : Fichier de sortie personnalisé

**Statistiques affichées :**
- Total traité
- OK (= attendu)
- Différences (≠ attendu)
- Erreurs
- Temps total et temps/ligne

---

## Fichiers créés/modifiés

| Fichier | Version | Action | Date |
|---------|---------|--------|------|
| importtest.py | 0.0.0 | Créé | 04/02/2026 |
| detmeme.py | 1.0.8 | Corrigé (faux positifs référence) | 04/02/2026 |

---

## Fichiers de référence utilisés

| Fichier | Rôle |
|---------|------|
| detall.py | Orchestrateur de détection (analyse langage naturel) |
| detia.py | Détection par IA (à utiliser en phase 2) |
| refs/importtest.csv | Fichier de test avec 25000 lignes |

---

## Prochaines étapes envisagées

1. Exécuter `importtest.py` sur les 25000 lignes
2. Analyser les différences
3. Affiner detall pour réduire les écarts
4. Faire tourner `detia` uniquement sur les différences résiduelles

---

## Prompts de recréation

### importtest.py
**Prompt :**
> Créer `importtest.py` qui lit `/refs/importtest.csv` contenant 25000 lignes avec les colonnes (id, test, attendu, oripathologies). Utiliser uniquement `detall` pour détecter les critères. Ajouter une colonne `nb_detall` avec le nombre de critères trouvés. Si différent de `attendu`, ajouter une colonne `detecte` avec les pathologies détectées (format: tag [adj1, adj2]). Utiliser tqdm pour la progression. Options: --verbose, --limit N, --debug.

**PJ nécessaires :**
- Prompt_contexte.md
- detall.py (pour référence de l'interface)

### detmeme.py (correction V1.0.8)
**Prompt :**
> Dans detmeme.py, corriger le bug des faux positifs de référence patient. Le problème : "système de bielles" est interprété comme une référence "bielles" car "de" est un synonyme de "que". Solution : ajouter une ÉTAPE 0 dans `detecter_meme()` qui vérifie la présence d'un synonyme de "même" (meme, identique, similaire, etc.) AVANT d'essayer d'extraire une référence. Si aucun synonyme de "même" n'est trouvé, retourner immédiatement `{'criteres': [], 'reference': None, 'residu': question_norm}`.

**PJ nécessaires :**
- Prompt_contexte.md
- detmeme.py (version 1.0.7)
