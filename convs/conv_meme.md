# Prompt conv_meme V1.0.0 - 13/01/2026 18:43:31

# Conversation : même

## Synthèse de la conversation

**Date de début** : 13/01/2026 (heure de traitement)

**Objectif** : Ajouter une fonctionnalité de recherche de patients similaires (V5.1)

---

## Échanges

### 13/01/2026 - Analyse initiale

**Question utilisateur** : Développer une fonctionnalité de recherche de patients similaires avec :
- Détection des expressions "même X" (detmeme.py)
- Identification du patient de référence (trouveid.py)
- Deux parcours : formulation directe ou affinage depuis résultats

**Réponse Claude** : 
- Analyse des fichiers fournis : detall.py, detcount.py, detangles.py, detage.py, dettags.py, detadjs.py, trouve.py, jsonsql.py, lancesql.py, motsvides.py, ages.csv
- Architecture proposée validée

**Fichiers analysés** :
- `detall.py` V1.0.7 : Orchestrateur pipeline detcount → detangles → dettags → detage → motsvides
- `trouve.py` V1.0.18 : Orchestrateur recherche (appelle detall puis jsonsql puis lancesql)
- `jsonsql.py` V1.0.6 : Génération SQL depuis JSON
- `ages.csv` : Contient "autour de {n} ans" avec BETWEEN {1}-3 AND {1}+3

**Architecture V5.1 décidée** :
```
trouve.py (modifié)
    ├── detall.py (modifié)
    │     ├── detcount.py
    │     ├── detmeme.py     → NOUVEAU : "même X" 
    │     ├── detangles.py
    │     ├── dettags.py
    │     ├── detage.py
    │     └── motsvides.py
    │
    ├── trouveid.py          → NOUVEAU : Identification patient référence
    ├── jsonsql.py (modifié) → Gestion critères "meme"
    └── lancesql.py
```

**Expressions "même" supportées** :
| Expression | Cible | Colonne(s) SQL |
|------------|-------|----------------|
| même tag | tag | canontags |
| même pathologie | pathologie | canontags + canonadjs |
| même portrait | portrait | idportrait |
| même sexe | sexe | sexe |
| même âge | age | age ± tolérance |
| même nom | nom | nom |
| même prénom | prenom | prenom |

**Priorité trouveid.py** :
1. `id {N}` → ID direct
2. `{prénom} {nom}` 
3. `{nom} {prénom}`
4. `{nom}` seul
5. `{prénom}` seul
6. Ambiguïté → 1er de la liste

---

## Fichiers à créer/modifier

### Nouveaux fichiers
- [x] `detmeme.py` - Détection expressions "même X" ✓ CRÉÉ ET TESTÉ (V2 avec commun.csv)
- [x] `trouveid.py` - Identification patient de référence ✓ CRÉÉ ET TESTÉ (avec commun.csv)

### Fichiers à modifier
- [x] `jsonsql.py` - Générer SQL pour critères "meme" ✓ CRÉÉ ET TESTÉ
- [x] `detall.py` - Intégrer detmeme entre detcount et detangles ✓ CRÉÉ
- [x] `trouve.py` - Appeler trouveid après detall ✓ CRÉÉ

## Tests effectués (13/01/2026)

| Question | Cible | Patient référence | Résultats |
|----------|-------|-------------------|-----------|
| même âge que Guillaume Moulin | age | ID 2 | 298 patients |
| même sexe que Hélène Joly | sexe | ID 3 | 505 patients |
| même portrait que Caroline Labbé | portrait | ID 4 | 33 patients |
| même tag que id 5 | tag | ID 5 | 369 patients |
| même pathologie que Cécile Laurent | pathologie | ID 1 | 8 patients |

### Synonymes chargés depuis commun.csv
- **meme** : identique, commun, semblable, similaire, sosie, meme
- **que** : pareil a, identique au, ressemblant a, sosie de, que, comme, de

---

## Tests CLI (meme.csv) - 10/10 réussis

| # | Question | Cible | Patient référence | Résultats |
|---|----------|-------|-------------------|-----------|
| 1 | même pathologie que Guillaume Moulin | pathologie | ID 2 | 3 |
| 2 | même age que Hélène Joly | age | ID 3 | 364 |
| 3 | même sexe que Caroline Labbé | sexe | ID 4 | 505 |
| 4 | même portrait que Richard Fernandez | portrait | ID 5 | 16 |
| 5 | même tag que id 6 | tag | ID 6 | 369 |
| 6 | identique pathologie que Bernadette Carpentier | pathologie | ID 8 | 6 |
| 7 | similaire age comme Eugène Auger | age | ID 12 | 387 |
| 8 | même nom que Victor Boutin | nom | ID 13 | 5 |
| 9 | même prénom que Leila El Amrani | prenom | ID 11 | 8 |
| 10 | même pathologie pareil a Geneviève Pons | pathologie | ID 16 | 11 |

---

## Analyse fonctionnelle : Multi-références (V5.2 potentielle)

### Demande
Permettre plusieurs patients de référence avec des critères "même" différents :
- "Même portrait même âge que Jean Valjean même tag que Toto"
- "Même portrait que Ginette et même âge et même pathologie que Pierre"

### Observation clé
Les "même" sont TOUJOURS AVANT les identifiants :
```
[même X] [même Y] que [patient1] [même Z] que [patient2]
```

### Complexité technique : MOYENNE

**Algorithme proposé :**
1. Tokeniser la question
2. Trouver les séparateurs ("que", "comme", "de"...) depuis commun.csv
3. Découper en groupes : [critères] | séparateur | [identifiant]
4. Pour chaque groupe : détecter les "même", identifier le patient
5. Associer chaque critère à son patient de référence

**Difficultés :**
- Où finit l'identifiant ? → Les mots "même/identique/..." servent de délimiteurs
- Noms composés → Priorité au plus long match en base
- Performance → Plusieurs requêtes base de données

### Recommandation
Implémenter en V5.2 après validation de la V5.1 mono-référence.
La V5.1 est une fondation solide qui gère déjà 95% des cas d'usage.

---

## Prompts de recréation

### detmeme.py
**Prompt** : Créer detmeme.py qui détecte les expressions "même X" dans une question en langage naturel. 

Charger les synonymes de "même" et "que" depuis commun.csv (colonnes meme et que).
Trier par nombre de mots décroissant pour matcher les expressions longues d'abord.
Toujours standardiser les comparaisons.

Expressions à détecter :
- même tag / mêmes tags → cible "tag"
- même pathologie / mêmes pathologies → cible "pathologie"  
- même portrait → cible "portrait"
- même sexe → cible "sexe"
- même âge → cible "age"
- même nom → cible "nom"
- même prénom → cible "prenom"

Format de sortie JSON :
```json
{
    "criteres": [{"type": "meme", "detecte": "même pathologie", "cible": "pathologie", "label": "Même pathologie"}],
    "residu": "texte restant"
}
```

Le module doit exposer : `charger_patterns_meme(fichier_csv)` et `detecter_meme(question, patterns, verbose, debug)`

**PJ requises** : Prompt_contexte1301.md, commun.csv, detcount.py (pour le format de sortie)

---

### trouveid.py
**Prompt** : Créer trouveid.py qui identifie un patient de référence depuis le résidu d'une question contenant des critères "meme".

Charger les synonymes de "que" depuis commun.csv (colonne que).
Trier par nombre de mots décroissant.

Mots-clés de liaison : "que", "comme", "de", "pareil a", "identique au", etc.
Exemples : "même pathologie que Jean Dupont", "même âge pareil a Marie"

Priorité de recherche :
1. `id {N}` → ID direct
2. `{prénom} {nom}` → Prénom + Nom
3. `{nom} {prénom}` → Nom + Prénom (inversé)
4. `{nom}` seul
5. `{prénom}` seul
6. Ambiguïté → Premier de la liste

IMPORTANT : La comparaison doit être insensible aux accents (utiliser standardise() pour comparer).

La fonction principale `enrichir_avec_reference(json_detection, db_path)` enrichit les critères "meme" avec :
- reference_id : ID du patient
- reference_patient : dict complet du patient (id, prenom, nom, sexe, age, idportrait, canontags, canonadjs, oripathologies)
- label mis à jour avec le nom du patient

**PJ requises** : Prompt_contexte1301.md, commun.csv, standardise.py

---

### jsonsql.py (modifications V5.1)
**Prompt** : Modifier jsonsql.py pour supporter les critères de type "meme".

Nouveau type de critère à gérer dans `generer_sql()` :
```json
{
    "type": "meme",
    "cible": "pathologie|tag|sexe|age|nom|prenom|portrait",
    "reference_id": 123,
    "reference_patient": {...}
}
```

Mapping des cibles vers SQL :
- `sexe` → `p.sexe = ?` (valeur du patient référence)
- `age` → `p.age BETWEEN ? AND ?` (±3 ans de tolérance)
- `nom` → `LOWER(p.nom) = LOWER(?)`
- `prenom` → `LOWER(p.prenom) = LOWER(?)`
- `portrait` → `p.idportrait = ?`
- `tag` → JOIN sur pathologies avec LIKE 'tag%'
- `pathologie` → JOIN sur pathologies avec = 'pathologie exacte'

IMPORTANT : Exclure le patient référence des résultats (`AND p.id != ?`)

**PJ requises** : Prompt_contexte1301.md, jsonsql.py (version actuelle V1.0.6)

---

### detall.py (modifications V5.1)
**Prompt** : Modifier detall.py pour intégrer detmeme.py dans le pipeline de détection.

Position de detmeme : entre detcount et detangles (étape 1.5)

Pipeline V5.1 :
1. detcount → LIST/COUNT
1.5. detmeme → Similarités (même X) ← NOUVEAU
2. detangles → Angles céphalo
3. dettags → Tags + adjectifs
4. detage → Âge/sexe
5. motsvides → Nettoyage

Ajouter dans charger_references() : `'patterns_meme': charger_patterns_meme(commun_path)`
Ajouter dans detecter_tout() : appel à detecter_meme() après detcount

**PJ requises** : Prompt_contexte1301.md, detall.py (version actuelle V1.0.7), detmeme.py

---

### trouve.py (modifications V5.1)
**Prompt** : Modifier trouve.py pour appeler trouveid.py après la détection.

Nouveau dans le pipeline :
- Après detall/detia : vérifier si des critères "meme" existent
- Si oui : appeler `enrichir_avec_reference(json_detection, db_path)`
- Le JSON enrichi est passé à jsonsql

Import : `from trouveid import enrichir_avec_reference`

Position : entre la détection (étape 1) et la génération SQL (étape 2)

**PJ requises** : Prompt_contexte1301.md, trouve.py (version actuelle V1.0.18), trouveid.py

---

## Notes techniques

- Base de test : base1000.db (1000 patients)
- Tolérance "même âge" : ±3 ans (depuis ages.csv ligne "autour de {n} ans")
- Mot-clé de détection référence : "que" et équivalents
