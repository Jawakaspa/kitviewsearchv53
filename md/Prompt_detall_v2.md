# Prompt_detall_v2.md

## Objet

Documentation de l'architecture complète de `detall.py` incluant l'intégration de `detangles.py` dans la chaîne de détection.

---

## Architecture de la chaîne de détection

### Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              detall.py                                       │
│                         (Orchestrateur principal)                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Question: "combien de femmes avec ANB > 4° et béance sévère de 30 ans"    │
│                                    │                                         │
│                                    ▼                                         │
│   ┌────────────────────────────────────────────────────────────────────┐    │
│   │ ÉTAPE 1: detcount.py                                               │    │
│   │ Détecte: "combien" → listcount = COUNT                             │    │
│   │ Résidu: "de femmes avec ANB > 4° et béance sévère de 30 ans"       │    │
│   └────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│   ┌────────────────────────────────────────────────────────────────────┐    │
│   │ ÉTAPE 2: detangles.py                              ◄ NOUVEAU       │    │
│   │ Détecte: "anb > 4" → Tag: "Classe II squelettique"                 │    │
│   │ Résidu: "de femmes avec et béance sévère de 30 ans"                │    │
│   └────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│   ┌────────────────────────────────────────────────────────────────────┐    │
│   │ ÉTAPE 3: detquals.py                                               │    │
│   │ Appelle detqual.py en boucle pour chaque tag+adjectifs             │    │
│   │   ├── dettag.py  → Détecte: "béance"                               │    │
│   │   └── detadjs.py → Détecte: "sévère"                               │    │
│   │ Résultat: Tag "béance" + Adj "sévère"                              │    │
│   │ Résidu: "de femmes avec et de 30 ans"                              │    │
│   └────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│   ┌────────────────────────────────────────────────────────────────────┐    │
│   │ ÉTAPE 4: detage.py                                                 │    │
│   │ Détecte: "femmes" → sexe=F, "30 ans" → age=30                      │    │
│   │ Résidu: "de avec et de"                                            │    │
│   └────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│   ┌────────────────────────────────────────────────────────────────────┐    │
│   │ RÉSULTAT FINAL (JSON unifié)                                       │    │
│   │ {                                                                  │    │
│   │   "langue": "fr",                                                  │    │
│   │   "listcount": "COUNT",                                            │    │
│   │   "criteres": [                                                    │    │
│   │     {"type": "count", ...},                                        │    │
│   │     {"type": "tag", "canonique": "classe ii squelettique", ...},   │    │
│   │     {"type": "tag", "canonique": "béance", "adjectifs": [...]},    │    │
│   │     {"type": "sexe", ...},                                         │    │
│   │     {"type": "age", ...}                                           │    │
│   │   ],                                                               │    │
│   │   "residu": "de avec et de"                                        │    │
│   │ }                                                                  │    │
│   └────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Ordre des étapes (justification)

| Étape | Module | Pourquoi cet ordre |
|-------|--------|-------------------|
| 1 | detcount | Détecte LIST/COUNT en premier (mots isolés simples) |
| 2 | detangles | Angles céphalo = tags spéciaux avec patterns regex |
| 3 | detquals | Tags généraux + adjectifs (après angles pour éviter doublons) |
| 4 | detage | Âge/sexe en dernier (patterns souvent courts) |

---

## Fichiers de référence

| Module | Fichier CSV | Description |
|--------|-------------|-------------|
| detcount | `refs/commun.csv` | Mots-clés COUNT (colonne `combien`) |
| detangles | `refs/angles.csv` | Patterns angles céphalométriques |
| detquals | `refs/tags.csv`, `refs/adjs.csv` | Tags et adjectifs orthodontiques |
| detage | `refs/ages.csv` | Patterns âge/sexe |

---

## Structure de sortie JSON unifiée

### Format complet

```json
{
  "langue": "fr",
  "listcount": "COUNT",
  "criteres": [
    {
      "type": "count",
      "detecte": "combien",
      "label": "Comptage demandé"
    },
    {
      "type": "tag",
      "detecte": "anb > 4",
      "canonique": "classe ii squelettique",
      "label": "Classe II squelettique",
      "sql": {
        "colonne": "pathologie",
        "operateur": "=",
        "valeur": "classe ii squelettique"
      },
      "adjectifs_possibles": ["division 1", "division 2", "sévère"],
      "source": "detangles"
    },
    {
      "type": "tag",
      "detecte": "beance",
      "canonique": "béance",
      "label": "Béance",
      "sql": {
        "colonne": "pathologie",
        "operateur": "=",
        "valeur": "béance"
      },
      "adjectifs": [
        {
          "detecte": "severe",
          "canonique": "sévère",
          "label": "Sévère"
        }
      ],
      "source": "detquals"
    },
    {
      "type": "sexe",
      "detecte": "femmes",
      "label": "Femme",
      "sql": {
        "colonne": "sexe",
        "operateur": "=",
        "valeur": "F"
      }
    },
    {
      "type": "age",
      "detecte": "30 ans",
      "label": "30 ans",
      "sql": {
        "colonne": "age",
        "operateur": "BETWEEN",
        "valeur": [30, 31]
      }
    }
  ],
  "residu": "de avec et de",
  "question_originale": "combien de femmes avec ANB > 4° et béance sévère de 30 ans",
  "question_standardisee": "combien de femmes avec anb > 4 et beance severe de 30 ans",
  "pathologies": ["classe ii squelettique", "béance"]
}
```

### Types de critères possibles

| Type | Source | Description |
|------|--------|-------------|
| `count` | detcount | Indicateur LIST/COUNT |
| `tag` | detangles, detquals | Pathologie/caractéristique orthodontique |
| `adjectif` | detadjs (via detquals) | Qualificatif d'un tag |
| `sexe` | detage | Critère de sexe |
| `age` | detage | Critère d'âge |

---

## Code de detall.py (mise à jour)

### Imports

```python
from detcount import charger_patterns_count, detecter_count
from detangles import charger_patterns_angles, detecter_angles  # NOUVEAU
from detquals import detecter_qualificatifs  # ou identifier_qualificatifs
from detage import charger_patterns_ages, detecter_age
```

### Fonction charger_references()

```python
def charger_references(verbose=False, debug=False) -> dict:
    """
    Charge tous les fichiers de référence.
    
    Returns:
        {
            'patterns_count': [...],
            'patterns_angles': [...],     # NOUVEAU
            'mapping_tags': {...},
            'mapping_adjs': {...},
            'patterns_ages': [...]
        }
    """
    script_dir = Path(__file__).parent
    
    # Chemins
    commun_path = script_dir / "refs" / "commun.csv"
    angles_path = script_dir / "refs" / "angles.csv"  # NOUVEAU
    tags_path = script_dir / "refs" / "tags.csv"
    adjs_path = script_dir / "refs" / "adjs.csv"
    ages_path = script_dir / "refs" / "ages.csv"
    
    references = {
        'patterns_count': [],
        'patterns_angles': [],  # NOUVEAU
        'mapping_tags': {},
        'mapping_adjs': {},
        'patterns_ages': []
    }
    
    # Charger chaque fichier...
    if angles_path.exists():
        references['patterns_angles'] = charger_patterns_angles(
            str(angles_path), verbose=verbose, debug=debug
        )
    
    return references
```

### Fonction detecter_tout()

```python
def detecter_tout(question: str, references: dict, verbose=False, debug=False) -> dict:
    """
    Orchestre toutes les détections.
    """
    question_originale = question
    question_norm = standardise(question)
    question_norm = re.sub(r'[,;]+', ' ', question_norm)
    question_norm = re.sub(r'\s+', ' ', question_norm).strip()
    
    resultat = {
        'langue': 'fr',
        'listcount': 'LIST',
        'criteres': [],
        'residu': question_norm,
        'question_originale': question_originale,
        'question_standardisee': question_norm,
        'pathologies': []
    }
    
    residu = question_norm
    tags_detectes = set()  # Pour éviter doublons entre detangles et detquals
    
    # ═══════════════════════════════════════════════════════════════════
    # ÉTAPE 1 : detcount
    # ═══════════════════════════════════════════════════════════════════
    if debug:
        print(f"\n[DEBUG] detall: === ÉTAPE 1 : detcount ===")
    
    resultat_count = detecter_count(residu, references['patterns_count'], 
                                     verbose=verbose, debug=debug)
    resultat['listcount'] = resultat_count['listcount']
    resultat['criteres'].extend(resultat_count['criteres'])
    residu = resultat_count['residu']
    
    # ═══════════════════════════════════════════════════════════════════
    # ÉTAPE 2 : detangles (NOUVEAU)
    # ═══════════════════════════════════════════════════════════════════
    if debug:
        print(f"\n[DEBUG] detall: === ÉTAPE 2 : detangles ===")
    
    resultat_angles = detecter_angles(residu, references['patterns_angles'],
                                       verbose=verbose, debug=debug)
    
    for critere in resultat_angles['criteres']:
        resultat['criteres'].append(critere)
        # Mémoriser les tags détectés pour éviter re-détection par detquals
        if critere.get('canonique'):
            tags_detectes.add(critere['canonique'])
            resultat['pathologies'].append(critere['canonique'])
    
    residu = resultat_angles['residu']
    
    # ═══════════════════════════════════════════════════════════════════
    # ÉTAPE 3 : detquals (tags + adjectifs)
    # ═══════════════════════════════════════════════════════════════════
    if debug:
        print(f"\n[DEBUG] detall: === ÉTAPE 3 : detquals ===")
    
    resultat_quals = detecter_qualificatifs(
        residu, 
        references['mapping_tags'],
        references['mapping_adjs'],
        tags_a_exclure=tags_detectes,  # Exclure tags déjà détectés
        verbose=verbose, 
        debug=debug
    )
    
    for critere in resultat_quals['criteres']:
        resultat['criteres'].append(critere)
        if critere.get('type') == 'tag' and critere.get('canonique'):
            resultat['pathologies'].append(critere['canonique'])
    
    residu = resultat_quals['residu']
    
    # ═══════════════════════════════════════════════════════════════════
    # ÉTAPE 4 : detage
    # ═══════════════════════════════════════════════════════════════════
    if debug:
        print(f"\n[DEBUG] detall: === ÉTAPE 4 : detage ===")
    
    resultat_age = detecter_age(residu, references['patterns_ages'],
                                 verbose=verbose, debug=debug)
    resultat['criteres'].extend(resultat_age['criteres'])
    residu = resultat_age['residu']
    
    # ═══════════════════════════════════════════════════════════════════
    # FINALISATION
    # ═══════════════════════════════════════════════════════════════════
    resultat['residu'] = residu
    
    return resultat
```

---

## Gestion des doublons entre detangles et detquals

### Problème potentiel

`detangles` peut détecter "Classe II squelettique" via le pattern `anb > 4`.
`detquals` pourrait aussi détecter "classe 2 squelettique" via synonymes.

### Solution

1. `detangles` retourne les tags canoniques détectés
2. `detall` mémorise ces tags dans `tags_detectes`
3. `detquals` reçoit `tags_a_exclure` et ignore ces tags

```python
# Dans detquals.py
def detecter_qualificatifs(residu, mapping_tags, mapping_adjs, 
                           tags_a_exclure=None, verbose=False, debug=False):
    tags_a_exclure = tags_a_exclure or set()
    
    for tag_candidat in tags_trouves:
        if tag_candidat['canonique'] in tags_a_exclure:
            if debug:
                print(f"[DEBUG] Tag '{tag_candidat['canonique']}' déjà détecté par detangles, ignoré")
            continue
        # ... traitement normal
```

---

## CLI de detall.py

### Mode unitaire

```bash
python detall.py "combien de femmes avec ANB > 4° et béance sévère de 30 ans"
```

Sortie JSON formatée.

### Mode batch

```bash
python detall.py tests/tests55allin.csv
```

Génère `tests/tests55allout.csv`.

---

## Fichiers nécessaires pour recréer detall.py

1. `Prompt_contexte0412.md` — Contexte général
2. `Prompt_detall_v2.md` — Ce document
3. `Prompt_detcount_detage_detall.md` — Format JSON unifié
4. `detcount.py` — Module COUNT
5. `detangles.py` — Module angles (à créer)
6. `detquals.py` — Module qualificatifs
7. `detage.py` — Module âge/sexe
8. Fichiers CSV de référence

---

## Évolutions futures possibles

| Module | Description |
|--------|-------------|
| `detlang` | Détection automatique de la langue |
| `detmesures` | Détection d'autres mesures (OPT, surplomb, etc.) |
| `detdates` | Détection de dates/périodes (consultations, traitements) |

---

**FIN DU DOCUMENT**
