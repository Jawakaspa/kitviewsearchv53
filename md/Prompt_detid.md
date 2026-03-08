# Prompt_detid.md — Intégration de la recherche par identifiant

## Objet

Ajout de la recherche par identifiant patient (`id XXX`) dans le pipeline de détection.
Le nouveau module `detid.py` s'intègre dans les trois branches : `detall.py`, `detia.py`, `detiabrut.py`.

## Fichier nouveau à créer

- **detid.py** : Module de détection des identifiants patients

## Fichiers à modifier

- **jsonsql.py** : Ajout du type de critère `id` dans la génération SQL
- **detall.py** : Ajout de l'étape 1.6 dans le pipeline
- **detia.py** : Ajout du pré-traitement detid (comme detmeme)
- **detiabrut.py** : Ajout du pré-traitement detid

## PJ nécessaires pour recréation complète

Pour recréer `detid.py` à partir de zéro :
- Ce fichier `Prompt_detid.md`
- `Prompt_contexte0502.md` (conventions projet)
- `detage.py` (modèle de structure similaire)
- `detmeme.py` (modèle d'intégration dans detia/detiabrut)
- `standardise.py` (dépendance import)

---

## 1. detid.py — Recréation complète

### Spécification

```
python detid.py                          # → Affiche l'aide
python detid.py "id 10122"              # → Analyse unitaire, sortie JSON
python detid.py "id 10122 avec béance" -v  # → Verbose
python detid.py "id ABC123 femme" -d    # → Debug complet
python detid.py tests/testsidin.csv     # → Mode batch → testsidout.csv
python detid.py tests/testsidin.csv -v  # → Batch verbose
```

### Comportement

- Pattern détecté : `\bid\s+([a-z0-9]+)` sur la question standardisée
- Retourne toujours 0 ou 1 critère (un seul identifiant par question)
- L'identifiant est converti en `int` si possible, sinon reste `str`
- Le résidu contient le texte de la question sans le pattern `id XXX`

### Format de sortie

```json
{
    "criteres": [
        {
            "type": "id",
            "detecte": "id 10122",
            "label": "Patient ID 10122",
            "sql": {"colonne": "id", "operateur": "=", "valeur": 10122}
        }
    ],
    "residu": "texte restant"
}
```

### Fonctions exportées

- `detecter_id(question, verbose, debug)` → dict
- `identifier_id(residu, filtres, verbose, debug)` → (filtres, residu)
- `traiter_fichier_batch(fichier, verbose, debug)` → (nb, path)

---

## 2. jsonsql.py — Patches

### Patch 2a : Ajouter la fonction `_generer_clause_id`

**Insérer APRÈS** la fonction `_generer_clause_age` (après son `return`) et **AVANT** `_generer_clause_meme` :

```python
def _generer_clause_id(critere: dict, debug=False) -> tuple:
    """
    Génère la clause SQL pour un critère de type 'id'.
    
    Recherche par identifiant : p.id = ?
    Retourne toujours 0 ou 1 résultat (PRIMARY KEY).
    """
    sql_info = critere.get('sql', {})
    valeur = sql_info.get('valeur', '')
    
    if not valeur and valeur != 0:
        if debug:
            print(f"[DEBUG] jsonsql: Critère id sans valeur, ignoré")
        return "", []
    
    return "p.id = ?", [valeur]
```

### Patch 2b : Gérer le type 'id' dans `generer_sql()`

**Dans** la fonction `generer_sql()`, **après** le bloc `elif type_critere == 'age':` (qui se termine par `if verbose or debug: print(f"  ✓ {debug_str}")`), **ajouter** :

```python
        elif type_critere == 'id':
            where_clause, crit_params = _generer_clause_id(critere, debug=debug)
            if where_clause:
                where_clauses.append(where_clause)
                params.extend(crit_params)
                
                debug_str = f"id = {crit_params[0]}"
                debug_clauses.append(debug_str)
                
                if verbose or debug:
                    print(f"  ✓ {debug_str}")
```

---

## 3. detall.py — Patches

### Patch 3a : Ajouter l'import de detid

**Insérer APRÈS** le bloc d'import de detage (après `def detecter_age(q, p, **kw): ...`) et **AVANT** le bloc d'import de motsvides :

```python
# detid - Détection des identifiants patients
try:
    from detid import detecter_id
    DETID_DISPONIBLE = True
except ImportError:
    DETID_DISPONIBLE = False
    def detecter_id(q, **kw): return {'criteres': [], 'residu': q}
```

### Patch 3b : Ajouter l'étape 1.6 dans `detecter_tout()`

**Insérer APRÈS** le bloc de l'étape 1.5 (detmeme) — après `print(f"[DEBUG] detall: Résidu après meme: '{residu}'")`  — et **AVANT** l'étape 2 (detangles) :

```python
    # =========================================================================
    # ÉTAPE 1.6 : detid - Détection des identifiants patients
    # =========================================================================
    if debug:
        print()
        print(f"[DEBUG] detall: === ÉTAPE 1.6 : detid ===")
    
    if DETID_DISPONIBLE:
        resultat_id = detecter_id(
            residu,
            verbose=verbose,
            debug=debug
        )
        resultat['criteres'].extend(resultat_id['criteres'])
        residu = resultat_id['residu']
        
        if debug:
            nb_id = len(resultat_id['criteres'])
            print(f"[DEBUG] detall: {nb_id} identifiant(s) détecté(s)")
            print(f"[DEBUG] detall: Résidu après id: '{residu}'")
```

### Patch 3c : Ajouter l'affichage du module dans `main()`

**Dans** `main()`, dans la section "Modules de détection:", **ajouter** après la ligne `print(f"  detmeme:   {'✓' if DETMEME_DISPONIBLE else '✗'} (V5.1)")` :

```python
    print(f"  detid:     {'✓' if DETID_DISPONIBLE else '✗'}")
```

### Patch 3d : Ajouter le comptage nb_id dans `traiter_fichier_batch()`

**Dans** `traiter_fichier_batch()`, **après** la ligne `nb_meme = len(...)` et **avant** `nb_tags = len(...)`, **ajouter** :

```python
        nb_id = len([c for c in resultat['criteres'] if c.get('type') == 'id'])
```

Et adapter l'écriture CSV si besoin (ajout colonne `nb_id`).

---

## 4. detia.py — Patches

### Patch 4a : Ajouter l'import de detid

**Insérer APRÈS** le bloc d'import de detmeme et **AVANT** la ligne `# Configuration` :

```python
# Import de detid pour pré-traitement des identifiants
try:
    from detid import detecter_id
    DETID_DISPONIBLE = True
except ImportError:
    DETID_DISPONIBLE = False
    def detecter_id(q, **kw): return {'criteres': [], 'residu': q}
```

### Patch 4b : Ajouter le pré-traitement detid dans `detecter_tout()`

**Dans** `detecter_tout()`, **APRÈS** le bloc de pré-traitement detmeme (qui se termine par `print(f"[DEBUG] detia: Question résiduelle pour IA: '{question_pour_ia}'")`), et **AVANT** le commentaire `# APPEL À L'IA`, **ajouter** :

```python
    # ═══════════════════════════════════════════════════════════════════════════
    # NOUVEAU : PRÉ-TRAITEMENT PAR DETID
    # ═══════════════════════════════════════════════════════════════════════════
    criteres_id = []
    
    if DETID_DISPONIBLE:
        if verbose:
            print(f"  → Pré-traitement detid...", end=" ", flush=True)
        
        resultat_detid = detecter_id(
            question_pour_ia,
            verbose=False,
            debug=debug
        )
        
        criteres_id = resultat_detid.get('criteres', [])
        question_pour_ia = resultat_detid.get('residu', question_pour_ia)
        
        if verbose:
            if criteres_id:
                print(f"{len(criteres_id)} identifiant(s) détecté(s)")
            else:
                print(f"aucun identifiant")
        
        if debug and criteres_id:
            print(f"[DEBUG] detia: Critères 'id' détectés: {criteres_id}")
            print(f"[DEBUG] detia: Question résiduelle pour IA: '{question_pour_ia}'")
```

### Patch 4c : Fusionner les critères id dans le résultat

**Dans** `detecter_tout()`, **remplacer** la ligne :
```python
    criteres_fusionnes = criteres_meme + criteres_ia
```

**Par** :
```python
    criteres_fusionnes = criteres_meme + criteres_id + criteres_ia
```

### Patch 4d : Afficher le module dans `main()`

**Dans** `main()`, **après** la ligne `print(f"  detmeme:   {'✓' if DETMEME_DISPONIBLE else '✗'} (V1.0.30)")` :

```python
    print(f"  detid:     {'✓' if DETID_DISPONIBLE else '✗'}")
```

---

## 5. detiabrut.py — Patches

### Patch 5a : Ajouter l'import de detid

**Insérer APRÈS** le bloc `DETIA_DISPONIBLE = True` et les imports de detia, **AVANT** les constantes `REFERENTIELS_DISPONIBLES` :

```python
# Import de detid pour pré-traitement des identifiants
try:
    from detid import detecter_id
    DETID_DISPONIBLE = True
except ImportError:
    DETID_DISPONIBLE = False
    def detecter_id(q, **kw): return {'criteres': [], 'residu': q}
```

### Patch 5b : Ajouter le pré-traitement dans `detecter_tout_brut()`

**Dans** `detecter_tout_brut()`, **APRÈS** la ligne `question_std = standardise(question)` et **AVANT** `# Construction du prompt`, **ajouter** :

```python
    # Pré-traitement detid : extraire l'identifiant avant l'envoi à l'IA
    criteres_id = []
    question_effective = question
    
    if DETID_DISPONIBLE:
        resultat_detid = detecter_id(question, verbose=False, debug=debug)
        criteres_id = resultat_detid.get('criteres', [])
        if criteres_id:
            question_effective = resultat_detid.get('residu', question)
            if debug:
                print(f"[DEBUG] detiabrut: ID détecté, question pour IA: '{question_effective}'")
```

Puis **remplacer** dans la suite de la fonction :
```python
    prompt_utilisateur = _construire_prompt_utilisateur(question)
```
**Par** :
```python
    prompt_utilisateur = _construire_prompt_utilisateur(question_effective)
```

Et dans la fusion des critères, **ajouter** `criteres_id` :
```python
    # Mapping vers canonique
    criteres_enrichis = criteres_id + _mapper_vers_canonique_brut(resultat_ia, references, actifs, debug)
```

---

## 6. Pipeline résultant

### detall.py (branche standard)
```
Question
  → detcount     → LIST/COUNT
  → detmeme      → Similarités (même X que Y)
  → detid        → Identifiant patient (id XXX)       ← NOUVEAU
  → detangles    → Angles céphalométriques
  → dettags      → Tags + adjectifs
  → detage       → Âge et sexe
  → motsvides    → Nettoyage résidu
  → JSON unifié
```

### detia.py / detiabrut.py (branche IA)
```
Question
  → detmeme      → Pré-traitement similarités
  → detid        → Pré-traitement identifiant          ← NOUVEAU
  → IA (OpenAI/Eden)  → Tags, adjectifs, âge, sexe, angles
  → Fusion critères (meme + id + IA)
  → motsvides    → Nettoyage résidu
  → JSON unifié
```

### jsonsql.py → SQL
```
Type "id" → WHERE p.id = ?   (0 ou 1 résultat garanti)
```

---

## 7. Cas d'usage

| Question | detmeme | detid | Autres | Résultat |
|----------|---------|-------|--------|----------|
| `id 10122` | - | id=10122 | - | 0 ou 1 patient |
| `id 10122 avec béance` | - | id=10122 | tag=béance | 0 ou 1 patient |
| `id ABC123 femme` | - | id=ABC123 | sexe=F | 0 ou 1 patient |
| `même portrait que id 10122` | ref=id:10122, cible=portrait | - | - | N patients similaires |
| `même nom que id 5 femme` | ref=id:5, cible=nom | - | sexe=F | N patients même nom + femme |
| `patients avec béance` | - | - | tag=béance | N patients |

---

**FIN DU DOCUMENT**
