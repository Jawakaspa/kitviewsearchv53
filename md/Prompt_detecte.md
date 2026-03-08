# Prompt_detecte.md

## Objet

Création du programme `detecte.py` qui orchestre la **détection complète** de tous les critères dans une question en langage naturel.

---

## Contexte

`detecte.py` est le **module principal** de la chaîne de détection Kitview. Il enchaîne :

1. **detquals** : Détection des tags qualifiés (pathologies + adjectifs)
2. **detages** : Détection de l'âge et du sexe dans le résidu
3. **motsvides** : Nettoyage final du résidu

Le résultat est un JSON complet prêt pour la génération de requête SQL.

---

## Architecture complète

```
Question
    │
    ▼
┌─────────────────────────────────────────────────────┐
│                    detecte.py                        │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ÉTAPE 1: detquals.py                               │
│     ├── detlang.py (détection langue)               │
│     ├── dettags.py (détection tags)                 │
│     └── detadjs.py (détection adjectifs)            │
│              │                                       │
│              ▼                                       │
│     tags_qualifies + résidu                         │
│                                                      │
│  ÉTAPE 2: detages.py                                │
│     └── Détection âge et sexe dans le résidu        │
│              │                                       │
│              ▼                                       │
│     criteres_age_sexe + résidu                      │
│                                                      │
│  ÉTAPE 3: motsvides.py                              │
│     └── Suppression des mots vides                  │
│              │                                       │
│              ▼                                       │
│     résidu nettoyé                                  │
│                                                      │
└─────────────────────────────────────────────────────┘
    │
    ▼
JSON complet → Génération SQL
```

---

## Format de sortie JSON

```json
{
  "langue_detectee": "fr",
  "tags_qualifies": [
    {
      "tag": {
        "type": "tag",
        "canonique": "béance",
        "sql": {...}
      },
      "adjectifs": [
        {
          "type": "adjectif",
          "canonique": "sévère",
          "sql": {...}
        }
      ]
    }
  ],
  "criteres_age_sexe": [
    {
      "type": "age",
      "detecte": "moins de 30 ans",
      "sql": {...}
    }
  ],
  "residu": "patients avec",
  "residu_nettoye": "patients",
  "question_originale": "patients avec béance sévère de moins de 30 ans",
  "question_standardisee": "patients avec beance severe de moins de 30 ans"
}
```

---

## Signature CLI

```bash
python detecte.py "question utilisateur" [--langue auto] [--verbose] [--debug] [--json]
```

### Paramètres

| Paramètre | Description |
|-----------|-------------|
| `question` | Question en langage naturel |
| `--langue` | Code langue ou "auto" (défaut: auto) |
| `--verbose` | Afficher les détails à chaque étape |
| `--debug` | Afficher les informations de debug |
| `--json` | Sortie JSON uniquement |

---

## Fonction exportable

```python
def detecter_tout(
    question: str,
    langue: Optional[str] = "auto",
    verbose: bool = False,
    debug: bool = False,
    refs_dir: Optional[Path] = None
) -> dict:
    """
    Détecte tous les critères dans une question.
    
    Args:
        question: Question en langage naturel
        langue: Code langue ("auto" pour détection automatique)
        verbose: Afficher les détails
        debug: Afficher les infos de debug
        refs_dir: Répertoire des fichiers de référence
        
    Returns:
        dict complet avec tous les critères détectés
    """
```

---

## Gestion des modules optionnels

Le programme gère gracieusement l'absence de modules :

```python
try:
    from detquals import detecter_tags_qualifies
    DETQUALS_DISPONIBLE = True
except ImportError:
    DETQUALS_DISPONIBLE = False
```

Si un module n'est pas disponible, l'étape correspondante est ignorée avec un message informatif.

---

## Dépendances

| Module | Fonction | Obligatoire |
|--------|----------|-------------|
| `detquals.py` | Tags qualifiés | Oui |
| `detages.py` | Âge et sexe | Non (optionnel) |
| `motsvides.py` | Nettoyage résidu | Non (optionnel) |

---

## Cas de test

| Question | Résultat attendu |
|----------|------------------|
| `"béance sévère"` | 1 tag qualifié, résidu vide |
| `"bruxisme nocturne chez les garçons de 10 ans"` | 1 tag qualifié + critères âge/sexe |
| `"patients avec open bite"` | langue=en détectée, 1 tag qualifié |

---

## Utilisation pour la génération SQL

Le JSON produit contient toutes les informations nécessaires pour construire une requête SQL :

```python
result = detecter_tout("béance sévère de moins de 30 ans")

# Parcourir les tags qualifiés
for tq in result['tags_qualifies']:
    tag = tq['tag']
    # WHERE pathologie = 'béance'
    
    for adj in tq['adjectifs']:
        # AND qualificatif = 'sévère'

# Parcourir les critères âge/sexe
for crit in result['criteres_age_sexe']:
    # AND age < 30
```

---

## Pièces jointes nécessaires pour recréer

1. `Prompt_contexte0412.md` — Contexte général du projet
2. `Prompt_dettags_detadjs.md` — Spécifications dettags et detadjs
3. `Prompt_detquals.md` — Spécifications detquals
4. `Prompt_motsvides.md` — Spécifications motsvides
5. `Prompt_detecte.md` — Ce document
6. Fichiers de référence : `syntags.csv`, `synadjs.csv`, `commun.csv`, `motsvides.csv`

---

**FIN DU DOCUMENT**
