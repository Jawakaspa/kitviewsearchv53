# Prompt_standardise_tiret.md

## Objet

Modification de `standardise.py` pour **ne plus supprimer le caractère tiret `-`**.

---

## Contexte

La fonction `standardise()` est utilisée dans toute la chaîne de détection pour normaliser les textes (minuscules, suppression des accents, etc.).

Actuellement, le tiret `-` fait partie des caractères remplacés par des espaces. Cela pose problème pour :

1. **Nombres négatifs** : `ANB = -2` devient `ANB = 2` → perte d'information clinique critique
2. **Mots composés** : `pré-adolescent`, `sous-occlusion` → séparation non souhaitée

---

## Modification demandée

### Avant (ligne à modifier)

```python
for char in ".!-_?":
    texte = texte.replace(char, " ")
```

### Après

```python
for char in ".!_?":
    texte = texte.replace(char, " ")
```

Le tiret `-` est **retiré** de la liste des caractères à remplacer.

---

## Impact

### Fichiers concernés

| Fichier | Impact |
|---------|--------|
| `standardise.py` | Modification directe |
| Tous les modules `det*.py` | Bénéficient de la préservation du `-` |
| `tags.csv`, `ages.csv`, etc. | Peuvent désormais contenir des patterns avec `-` |

### Tests à effectuer après modification

```bash
# Vérifier que les nombres négatifs sont préservés
python -c "from standardise import standardise; print(standardise('ANB = -2'))"
# Attendu: "anb = -2"

# Vérifier que les mots composés sont préservés
python -c "from standardise import standardise; print(standardise('pré-adolescent'))"
# Attendu: "pre-adolescent"

# Vérifier que les autres règles fonctionnent toujours
python -c "from standardise import standardise; print(standardise('Béance Antérieure!'))"
# Attendu: "beance anterieure"
```

---

## Gestion des cas où le tiret gêne

Si dans certains contextes le tiret pose problème (par exemple dans une recherche full-text), le traitement spécifique devra être fait **en aval** de `standardise()`, au cas par cas.

Exemple :
```python
texte_std = standardise(question)
# Si besoin de supprimer les tirets pour FTS5 :
texte_fts = texte_std.replace('-', ' ')
```

---

## Pièces jointes pour recréer

1. `Prompt_contexte0412.md` — Contexte général
2. `standardise.py` — Fichier à modifier

---

**FIN DU DOCUMENT**
