# tags2patterns.md

## Objet

Ce prompt permet de créer `tags2patterns.py` qui transforme `tagsadjs.csv` en deux fichiers. Cesdeux fichiers contiendent la version française et seront complétés ultérieurement pour remplir les colonnes des autres langues.

- `patternstagsfr.csv` : synonymes des tags pour `dettags.py`
- `patternsadjsfr.csv` : synonymes des adjectifs pour `detadjs.py`

---

## Pièces jointes requises

1. **Prompt_contexte.md** — Contexte général du projet
2. **standardise.py** — Module de normalisation de texte (import obligatoire, pas de fallback)
3. **tagsadjs.csv** — Fichier source contenant tags et adjectifs

---

## Structure de tagsadjs.csv

### Colonnes obligatoires

| Colonne     | Description                                              |
| ----------- | -------------------------------------------------------- |
| `canon`     | Forme canonique du mot ou expression                     |
| `type`      | `p` = tag/pathologie, `a` = adjectif                     |
| `Xgn`       | Genre/nombre : `m`, `f`, `mp`, `fp`, ou vide             |
| `synonymes` | Liste de synonymes séparés par `,`                       |
| XX          | Placeholder                                              |
| `adjs`      | Liste des adjectifs applicables au tag (séparés par `,`) |
| XY          | Placeholder                                              |
| `m`         | Forme accordée masculin singulier                        |
| `f`         | Forme accordée féminin singulier                         |
| `mp`        | Forme accordée masculin pluriel                          |
| `fp`        | Forme accordée féminin pluriel                           |

### Exemple de ligne tag (type=p)

béance;p;f;beance,béance dentaire,espace entre les dents,espace interdentaire,morsure béante,morsure ouverte,open bite,openbite,écartement,écart,cavité;XX;antérieur,postérieur,latéral,gauche,droit,sévère,modéré;XY;;;;



### Exemple de ligne adjectif (type=a)

modéré;a;;léger,légere,légers,légeres;XX;;XY;modéré;modérée;modérés;modérées

## Vérifications obligatoires

### 1. Colonnes présentes

Arrêt si colonnes manquantes : `canon`, `type`, `Xgn`, `synonymes`, `adjs`, `m`, `f`, `mp`, `fp`

### 2. Valeurs gn valides

Arrêt si `Xgn` contient autre chose que : `m`, `f`, `mp`, `fp`, ou vide

### 3. Doublons de synonymes

**ERREUR + ARRÊT** si un synonyme (après standardisation) apparaît plusieurs fois :

- Dans la même ligne
- Dans des lignes différentes
- Message clair avec les deux canons en conflit

### 4. Correspondance adjectifs

**ERREUR + ARRÊT** si un adjectif utilisé dans la colonne `adjs` n'a pas de définition (ligne type=a) correspondante.

**AVERTISSEMENT** (continue) si un adjectif est défini (type=a) mais jamais utilisé dans `adjs`.

---

## Fichiers générés

### patternstagsfr.csv

Format : `canontag;synonyme;pattern

Pour chaque tag (type=p) :

1. canon` → canontag 
2. Pour chaque synonyme : synonyme)` → fr
3. et : `standardise(synonyme)` → pattern

Tri par longueur décroissante de la colonne pattern.

### patternsadjsfr.csv

Format : `canonadj;canontag;synonyme;pattern

Pour chaque tag ayant des adjectifs dans tagsadjs.csv (par exemple avulsion)

1. Pour chaque adjectif de la colonne`adjs` (pour avulsion : immédiat,différé,programmé,total)
2. - Trouver la définition (type=a) (donc les 4 définitions de immédiat,différé,programmé,total dans notre cas)
3. Pour chaque définition trouver créer des lignes dont les 2 premières colonnes sont le canonadj de l'adjectif (par exemple immédiat) et le canontag dont on est parti plus haut pour récupérer sa liste d'adjectifs (par exemple avulsion)
* 4 lignes pour les 4 formes conjugées de l'adjectif. Par exemple pour immédiat ça fera les lignes immédiat,immédiate,immédiats et immédiates.
  
  Pour ces 4 lignes le synonyme sera en réalité la forme canonymique de l'adjectif donc immédiat,différé,programmé et total dans nos exemples.
  
  Sauf s'il y a des doublons qu'il ne faut pas créer et dans ce cas il y a moins de 4 lignes. Par exemple pour sévère il n'y aura que 2 lignes sévère et sévères.

* Et une ligne par synonyme. Par exemple pour programmé qui a les 4 synonymes prévu,prévue,prévus et prévues cela fera 4 lignes supplémentaires. Pour ces lignes c'est le synonyme qui sera dans la colonne synonyme (donc pour les 4 lignes prévu,prévue,prévus et prévues)

* Enfin le traitement de chaque ligne se terminera pas la standardisation avec standardise(synonyme)` → pattern

La colonne pattern est celle qui est le point d'entrée de ces fichiers c'est grâce à elle que les programmes de détection detags et detadjs détecteront les tags et les adjectifs correspondants recherchés dans une question.

## Interface

### Import depuis un autre programme

```python
from tags2syn import generer_synonymes
nb_tags, nb_adjs = generer_synonymes('tagsadjs.csv', 'refs/', verbose=True)
```

### CLI

```
Usage:
  python tags2syn.py                    # Exécution standard
  python tags2syn.py --verbose          # Affichage détaillé
  python tags2syn.py --debug            # Affichage complet

Exemples:
  python tags2syn.py
  python tags2syn.py --verbose
```

### Chemins de recherche pour tagsadjs.csv

```python
chemins_possibles = [
    Path("refs/tagsadjs.csv"),
    Path("tagsadjs.csv"),
    Path(__file__).parent / "refs" / "tagsadjs.csv",
    Path("c:/g/refs/tagsadjs.csv"),
]
```

---

## Fonctions à implémenter

### `charger_tagsadjs(fichier_csv, verbose=False, debug=False)`

- Charge et valide le fichier tagsadjs.csv
- Effectue toutes les vérifications
- Retourne : `(tags, adjectifs, avertissements)`
  - `tags` : liste de dicts pour les lignes type='p'
  - `adjectifs` : dict {canon_lower: dict_adjectif}
  - `avertissements` : liste des warnings
- Arrêt avec `sys.exit(1)` en cas d'erreur fatale

### `generer_patternstagsfr(tags, fichier_sortie, verbose=False, debug=False)`

- Génère patternstagsfr.csv
- Retourne le nombre de lignes générées

### `generer_patternsadjsfr(tags, adjectifs, fichier_sortie, verbose=False, debug=False)`

- Génère patternsadjsfr.csv
- Retourne le nombre de lignes générées

### `generer_synonymes(fichier_entree, dossier_sortie=None, verbose=False, debug=False)`

- Fonction principale, peut être importée
- Retourne : `(nb_tags, nb_adjs)`

---

## Règles critiques

1. **Pas de fallback** pour `standardise.py` : erreur fatale si absent
2. **Encodage sortie** : `utf-8-sig` avec `newline=''`
3. **Commentaires d'en-tête** dans les fichiers générés avec date et nombre de lignes
4. **Éviter les doublons** dans les fichiers de sortie
5. **Messages d'erreur clairs** avec numéros de ligne et valeurs concernées

---

## Conventions d'affichage

### Erreurs

```
======================================================================
ERREURS DÉTECTÉES - ARRÊT DU TRAITEMENT
======================================================================
  ✗ Ligne 28: Pattern'xxx' déjà utilisé pour 'yyy' (conflit avec 'zzz')
```

### Avertissements

```
----------------------------------------------------------------------
AVERTISSEMENTS (le traitement continue)
----------------------------------------------------------------------
  ⚠ Adjectif 'xxx' défini (ligne N) mais jamais utilisé
```

### Succès

```
✓ 500 lignes générées → /chemin/absolu/syntags.csv
```

---

**FIN DU PROMPT**
