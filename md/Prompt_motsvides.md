# Prompt_motsvides.md

## Objet

Création du programme `motsvides.py` qui supprime les mots vides (stopwords) d'un texte pour obtenir un résidu minimal.

---

## Contexte

Dans la chaîne de détection Kitview, `motsvides.py` est appelé en fin de processus pour :
1. Nettoyer le résidu après toutes les détections (tags, adjectifs, âge, sexe)
2. Ne garder que les mots potentiellement significatifs
3. Faciliter l'identification de termes non reconnus

---

## Fichier de référence : motsvides.csv

### Format multilingue (recommandé)

```csv
fr;en;de;th;ar;cn
avec;with;mit;กับ;مع;与
sans;without;ohne;โดยไม่มี;بدون;没有
les;the;die;ที่;ال;的
...
```

### Format monolingue (legacy)

```csv
mot
avec
sans
les
...
```

Le programme détecte automatiquement le format et s'adapte.

---

## Signature CLI

```bash
python motsvides.py "texte" [--langue fr] [--verbose] [--debug] [--json]
```

### Paramètres

| Paramètre | Description |
|-----------|-------------|
| `texte` | Texte à nettoyer |
| `--langue` | Code langue (défaut: fr) |
| `--verbose` | Afficher les mots supprimés |
| `--debug` | Afficher les informations de debug |
| `--json` | Sortie JSON uniquement |

---

## Format de sortie JSON

```json
{
  "residu": "patients",
  "mots_supprimes": ["avec", "de", "la"],
  "nb_mots_avant": 4,
  "nb_mots_apres": 1
}
```

---

## Fonction exportable

```python
def supprimer_motsvides(
    texte: str,
    langue: Optional[str] = "fr",
    verbose: bool = False,
    debug: bool = False,
    refs_dir: Optional[Path] = None
) -> dict:
    """
    Supprime les mots vides d'un texte.
    
    Args:
        texte: Texte à nettoyer
        langue: Code langue pour les mots vides à utiliser
        verbose: Afficher les détails
        debug: Afficher les infos de debug
        refs_dir: Répertoire des fichiers de référence
        
    Returns:
        dict avec residu, mots_supprimes, nb_mots_avant, nb_mots_apres
    """
```

---

## Algorithme

1. **Charger** les mots vides depuis `motsvides.csv`
2. **Standardiser** le texte (minuscules, sans accents)
3. **Découper** en mots
4. **Filtrer** : garder uniquement les mots non présents dans la liste
5. **Reconstruire** le texte nettoyé

---

## Cas de test

| Texte | Langue | Résidu attendu |
|-------|--------|----------------|
| `"patients avec de la"` | fr | `"patients"` |
| `"the patient with"` | en | `"patient"` |
| `"le patient qui a une béance"` | fr | `"patient beance"` |

---

## Structure du fichier motsvides.csv multilingue

Pour créer un fichier multilingue à partir du fichier monolingue existant :

```csv
fr;en;de;th
a;a;ein;-
ai;have;habe;-
avec;with;mit;กับ
ce;this;dies;นี้
...
```

**Note** : Utiliser `-` ou laisser vide pour les mots sans équivalent dans une langue.

---

## Points clés

1. **Standardisation** : Les mots vides et le texte sont standardisés avant comparaison
2. **Multilingue** : Support des colonnes par langue
3. **Fallback** : Si format monolingue, tout va dans 'fr'
4. **Cache** : Les mots vides sont chargés une seule fois

---

## Pièces jointes nécessaires pour recréer

1. `Prompt_contexte0412.md` — Contexte général du projet
2. `Prompt_motsvides.md` — Ce document
3. `motsvides.csv` — Liste des mots vides
4. `commun.csv` — Configuration (langues actives)

---

**FIN DU DOCUMENT**
