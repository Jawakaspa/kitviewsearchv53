# Prompt_detquals.md

## Objet

Création du programme `detquals.py` qui orchestre la détection des **tags qualifiés** (pathologies + adjectifs associés) dans une question en langage naturel.

---

## Contexte

Dans la chaîne de détection Kitview, `detquals.py` est le module intermédiaire qui :
1. Utilise `dettags.py` pour détecter les tags de pathologie (un par un)
2. Utilise `detadjs.py` pour détecter les adjectifs associés à chaque tag
3. Produit un JSON structuré des "tags qualifiés" prêt pour la génération SQL

---

## Architecture de détection

```
Question → detquals.py → JSON tags qualifiés
              │
              ├── dettags.py (avec detlang.py intégré)
              │      └── Détecte UN tag (le premier par position)
              │
              └── detadjs.py
                     └── Détecte les adjectifs autour du tag
```

### Algorithme "cueillette de groseilles"

L'idée est de traiter les tags **un par un, dans l'ordre d'apparition** :

1. **Détecter le premier tag** (mode single_tag) dans la question
2. **Chercher ses adjectifs** dans la zone de proximité
3. **Mettre à jour le résidu** (retirer tag + adjectifs)
4. **Répéter** sur le résidu jusqu'à ce qu'il n'y ait plus de tag

Cette approche garantit que chaque adjectif est attribué au bon tag.

---

## Format de sortie JSON

```json
{
  "langue_detectee": "fr",
  "tags_qualifies": [
    {
      "tag": {
        "type": "tag",
        "detecte": "beance",
        "canonique": "béance",
        "label": "Béance",
        "langue_detectee": "fr",
        "sql": {
          "colonne": "pathologie",
          "operateur": "=",
          "valeur": "béance"
        },
        "position": {"debut": 14, "fin": 20}
      },
      "adjectifs": [
        {
          "type": "adjectif",
          "detecte": "severe",
          "canonique": "sévère",
          "label": "Sévère",
          "langue_detectee": "fr",
          "parent_tag": "béance",
          "position_relative": "après",
          "sql": {
            "colonne": "qualificatif",
            "operateur": "=",
            "valeur": "sévère"
          }
        }
      ]
    }
  ],
  "residu": "patients avec",
  "question_originale": "patients avec béance sévère",
  "question_standardisee": "patients avec beance severe"
}
```

---

## Signature CLI

```bash
python detquals.py "question utilisateur" [--langue auto] [--verbose] [--debug] [--json]
```

### Paramètres

| Paramètre | Description |
|-----------|-------------|
| `question` | Question en langage naturel |
| `--langue` | Code langue ou "auto" (défaut: auto) |
| `--verbose` | Afficher les détails de détection |
| `--debug` | Afficher les informations de debug |
| `--json` | Sortie JSON uniquement |

---

## Fonction exportable

```python
def detecter_tags_qualifies(
    question: str,
    langue: Optional[str] = "auto",
    verbose: bool = False,
    debug: bool = False,
    refs_dir: Optional[Path] = None
) -> dict:
    """
    Détecte tous les tags qualifiés (tags + adjectifs) dans une question.
    
    Args:
        question: Question en langage naturel
        langue: Code langue ("auto" pour détection automatique)
        verbose: Afficher les détails
        debug: Afficher les infos de debug
        refs_dir: Répertoire des fichiers de référence
        
    Returns:
        dict avec langue_detectee, tags_qualifies, residu, etc.
    """
```

---

## Dépendances

| Module | Fonction importée |
|--------|-------------------|
| `dettags.py` | `detecter_tags`, `standardiser_texte` |
| `detadjs.py` | `detecter_adjectifs` |

Ces modules doivent être dans le même répertoire que `detquals.py`.

---

## Cas de test

| Question | Tags qualifiés attendus |
|----------|------------------------|
| `"béance sévère"` | béance + [sévère] |
| `"bruxisme nocturne et béance antérieure"` | bruxisme + [nocturne], béance + [antérieure] |
| `"patients with severe open bite"` | béance + [sévère] |
| `"sévère béance latérale gauche"` | béance + [sévère (avant), latérale, gauche] |

---

## Points clés

1. **Ordre de détection** : Le premier tag par position est traité en premier
2. **Zone de proximité** : Les adjectifs sont cherchés dans la question standardisée complète, mais la zone de proximité (3 mots avant, 5 mots après) évite les attributions erronées
3. **Résidu progressif** : Chaque tag et ses adjectifs sont retirés du résidu pour l'itération suivante
4. **Limite de sécurité** : Maximum 20 itérations pour éviter les boucles infinies

---

## Pièces jointes nécessaires pour recréer

1. `Prompt_contexte0412.md` — Contexte général du projet
2. `Prompt_dettags_detadjs.md` — Spécifications de dettags et detadjs
3. `Prompt_detquals.md` — Ce document
4. `syntags.csv` — Synonymes de tags
5. `synadjs.csv` — Synonymes d'adjectifs
6. `commun.csv` — Configuration

---

**FIN DU DOCUMENT**
