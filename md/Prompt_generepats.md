# Prompt_generepats.md

**Version :** 2.0.0  
**Date :** 24/12/2025  
**Objectif :** Recréer le programme generepats.py à l'identique

---

## 🎯 Objectif du programme

Créer `generepats.py`, un script Python qui génère des fichiers CSV de patients orthodontiques fictifs pour tester Kitview.

**Structure simplifiée** : Le CSV de sortie contient uniquement **9 colonnes**.

---

## 📋 Spécifications fonctionnelles

### Usage en ligne de commande

```bash
python generepats.py <nombre> [--silent]
```

- `<nombre>` : Nombre de patients à générer (2 à 200000)
- `--silent` : Mode silencieux (optionnel)

### Fichiers de sortie

- `data/pats{N}.csv` : Fichier patients (9 colonnes)
- `stats/stats{N}_tags.csv` : Statistiques des tags
- `stats/stats{N}_age.csv` : Statistiques des âges

---

## 📊 Structure du CSV de sortie (9 colonnes)

```
id;canontags;canonadjs;sexe;age;datenaissance;prenom;nom;idportrait
```

| Colonne | Description | Exemple |
|---------|-------------|---------|
| `id` | Identifiant unique | `1` |
| `canontags` | Tags canoniques séparés par `,` | `béance,Bruxisme` |
| `canonadjs` | Adjectifs par tag (`,` entre tags, `\|` entre adjs d'un même tag) | `latérale,nocturne\|sévère` |
| `sexe` | M ou F | `F` |
| `age` | Âge en années (3 décimales) | `12.345` |
| `datenaissance` | Date ISO | `2012-03-15` |
| `prenom` | Prénom | `Marie` |
| `nom` | Nom de famille | `Dupont` |
| `idportrait` | Identifiant du portrait | `P001` |

---

## 📁 Fichiers de référence requis

Les fichiers doivent être dans le répertoire `refs/` :

| Fichier | Colonnes utilisées | Description |
|---------|-------------------|-------------|
| `portraits.csv` | `sexe`, `idportrait` | Portraits par sexe |
| `tagsadjs.csv` | `canon`, `type`, `Xgn`, `adjs`, `m`, `f`, `mp`, `fp` | Tags et adjectifs |
| `sexeorigine.csv` | `sexe`, `nom`, `prenom`, `poidsnom`, `poidsprenom` | Noms/prénoms par origine |
| `commun.csv` | `incompatibles` | Groupes d'adjectifs incompatibles |

---

## 🔧 Algorithmes de génération

### Distribution du nombre de tags par patient

```python
TAGS_DISTRIBUTION = [(1, 0.40), (2, 0.25), (3, 0.20), (4, 0.15)]
```

### Distribution du nombre d'adjectifs par tag

```python
ADJS_DISTRIBUTION = [(0, 0.30), (1, 0.20), (2, 0.20), (3, 0.20), (4, 0.10)]
```

### Pondération spéciale pour certains tags

```python
TAG_BEANCE_WEIGHT = 0.20   # 20% de chance de sélectionner béance
TAG_BRUXISME_WEIGHT = 0.10 # 10% de chance de sélectionner bruxisme
TAG_OTHER_WEIGHT = 0.70    # 70% autres tags
```

### Génération de l'âge

- Distribution gaussienne : moyenne=15, écart-type=6
- Bornes : [5, 50] ans
- Format : 3 décimales

### Génération des noms/prénoms

- 75% : Faker (fr_FR)
- 25% : sexeorigine.csv avec pondération

---

## 🔄 Gestion des incompatibilités

Les adjectifs incompatibles (définis dans `commun.csv`, colonne `incompatibles`) ne peuvent pas être attribués ensemble au même tag.

Exemple : si "gauche" et "droite" sont incompatibles, un tag ne peut pas avoir les deux.

**Important** : La comparaison des adjectifs est **insensible à la casse**.

---

## 🎭 Accord en genre des adjectifs

Les adjectifs sont accordés selon le genre du tag (colonne `Xgn` dans tagsadjs.csv) :
- `m` : masculin singulier
- `f` : féminin singulier  
- `mp` : masculin pluriel
- `fp` : féminin pluriel

Les formes accordées sont définies dans tagsadjs.csv pour les entrées de type `a`.

---

## 🎲 Seeds pour reproductibilité

```python
SEED_GENERAL = 42
SEED_SEXE = 43
SEED_AGE = 44
SEED_TAGS = 45
SEED_ADJS = 46
```

---

## 📊 Affichage attendu

### Barre de progression

```
[████████████████████░░░░░░░░░░░░░░░░░░░░] 60% - Patient 600/1000
```

### Récapitulatif final

```
============================================================
📋 RÉCAPITULATIF
============================================================

✅ 1000 patients générés

📁 Fichiers créés:
  • /path/to/data/pats1000.csv (45.23 Ko)
  • /path/to/stats/stats1000_tags.csv (1.23 Ko)
  • /path/to/stats/stats1000_age.csv (0.89 Ko)

⏱️  Temps d'exécution:
  • Chargement:  0.123s
  • Génération:  1.234s
  • Écriture:    0.056s
  • TOTAL:       1.413s
  • Vitesse:     789 patients/s

🏷️  TOP 10 tags:
  1. béance: 234 (23.4%)
  ...

🏷️  TOP 10 tags+adjectifs:
  1. béance + antérieure: 123 (12.3%)
  ...

📊 Répartition par tranches d'âge:
  • 5-10 ans: 156 (15.6%)
  ...

✅ Génération terminée avec succès!
```

---

## ⚠️ Points critiques

1. **9 colonnes uniquement** : Ne pas générer les colonnes supplémentaires (oripathologies, ville, etc.)
2. **Encodage CSV** : UTF-8-SIG obligatoire
3. **Séparateur** : Point-virgule (`;`)
4. **Cartouche CSV** : Ligne de commentaire `#filename v1.0.0 - DD/MM/YYYY HH:MM:SS`
5. **Accord genre** : Les adjectifs doivent être accordés selon le genre du tag
6. **Incompatibilités** : Comparaison insensible à la casse

---

## 📖 Cartouche du programme

```python
#*TO*#
__pgm__ = "generepats.py"
__version__ = "0.0.0"
__date__ = "01/01/1970 00:00"
```

---

## 🔗 Fichiers nécessaires en PJ

| Fichier | Emplacement | Description |
|---------|-------------|-------------|
| `Prompt_contexte2312.md` | projet | Contexte général du projet |
| `portraits.csv` | refs/ | Liste des portraits |
| `tagsadjs.csv` | refs/ | Tags et adjectifs |
| `sexeorigine.csv` | refs/ | Noms/prénoms par origine |
| `commun.csv` | refs/ | Incompatibilités |

---

## Dépendances Python

```bash
pip install faker tqdm
```

---

## Historique des versions du prompt

| Version | Date | Modifications |
|---------|------|---------------|
| 1.0.0 | 19/12/2025 | Version initiale (32 colonnes) |
| 2.0.0 | 24/12/2025 | Simplification à 9 colonnes, suppression oripathologies |

---

**Fin du prompt**
