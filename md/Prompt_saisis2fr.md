# Prompt_saisis2fr

## Objet

Transformation du fichier `tagssaisis.csv` (format utilisateur français, facile à saisir) en `tagsfr.csv` (format informatique, préparé pour l'internationalisation).

---

## Fichier d'entrée : refs/tagssaisis.csv

### Structure

| Colonne | Description |
|---------|-------------|
| `type` | Type de tag : `p` = pathologie, `a` = traitement/appareil, ou tout autre code de 1 à 10 caractères (ex: `s` pour sports, `rel` pour relations). Permet un classement par type des résultats. |
| `canonfr` | Tag canonique en français |
| `synonymesfr` | Synonymes du tag, séparés par une virgule `,` |
| `adjectifsfr` | Adjectifs qualificatifs en français, séparés par une virgule `,`. Les synonymes d'un même adjectif sont séparés par `\|`, le premier étant le terme canonique. |

### Format des adjectifs

Les adjectifs peuvent avoir des synonymes. La syntaxe est : `canonique|synonyme1|synonyme2|...`

**Exemple pour béance** :
```
gauche,antérieure|face,droite,latérale,postérieure,sévère|grave|marqué|important|majeur|marquée|importante|majeure|complexe,modérée|bénin|bénine|léger|faible|limité|mineur|discret|légère|limitée|mineure|discrète
```

- `sévère` est le terme canonique, avec synonymes : grave, marqué, important, majeur, marquée, importante, majeure, complexe
- `modérée` est le terme canonique, avec synonymes : bénin, bénine, léger, faible, limité, mineur, discret, légère, limitée, mineure, discrète

### Exemples de lignes

```csv
type;canonfr;synonymesfr;adjectifsfr
p;Béance;beance,béance dentaire,espace entre les dents,espace interdentaire,morsure béante,morsure ouverte,trou,open bite,openbite;gauche,antérieure|face,droite,latérale,postérieure,sévère|grave|marqué
p;bruxisme;bruxomanie,clenching,grincement,grincements,grinding,serrement,usure,grince,grincent;|nocturne|la nuit|nuitamment|des dents|les dents|dents|dent|dentaire|dentaires
p;avulsion;arrachage dentaire,arracher,dédentation,enlever,exodontie,extraction,extraction dentaire,extraire;immédiate,immédiat
```

---

## Fichier de sortie : refs/tagsfr.csv

### Structure

| Colonne | Description | Construction |
|---------|-------------|--------------|
| `type` | Type de tag | Copie de la colonne `type` de tagssaisis.csv |
| `frtags` | Tags français | `canonfr` suivi des `synonymesfr`, séparés par virgule. Si `synonymesfr` est vide, copie de `canonfr` uniquement. |
| `stdfrtags` | Tags standardisés | `frtags` passé par la fonction `standardise()` (appliquée à chaque élément) |
| `fradjs` | Adjectifs français | Copie de la colonne `adjectifsfr` de tagssaisis.csv |
| `stdfradjs` | Adjectifs standardisés | `fradjs` passé par la fonction `standardise()` (appliquée à chaque élément, en conservant la structure `\|`) |

### Fonction de standardisation

La fonction `standardise()` (définie dans `standardise.py`) applique les transformations suivantes :
1. Conversion en minuscules
2. Suppression des accents et diacritiques
3. Remplacement de `.`, `!`, `-`, `?`, `_` par des espaces
4. Dédoublonnage des espaces multiples
5. Suppression des espaces en début et fin

### Exemple de transformation

**Entrée (tagssaisis.csv)** :
```csv
p;Béance;beance,béance dentaire,open bite;gauche,antérieure|face,sévère|grave
```

**Sortie (tagsfr.csv)** :
```csv
p;Béance,beance,béance dentaire,open bite;beance,beance,beance dentaire,open bite;gauche,antérieure|face,sévère|grave;gauche,anterieure|face,severe|grave
```

---

## Programme : saisis2fr.py

### Fonctionnalités

1. Vérifie l'encodage UTF-8-BOM du fichier d'entrée
2. Ignore les lignes de commentaires (commençant par `#`) y compris en entête
3. Vérifie la présence des colonnes attendues
4. Transforme chaque ligne selon les règles définies
5. Génère le fichier de sortie en UTF-8-BOM

### Utilisation

```bash
python saisis2fr.py
```

Le programme :
- Lit `refs/tagssaisis.csv` (sous-répertoire refs du répertoire du script)
- Génère `refs/tagsfr.csv` dans le même sous-répertoire

### Affichage

- Affiche le cartouche (nom, version, date)
- Affiche les chemins absolus des fichiers
- Affiche le nombre de commentaires ignorés
- Affiche chaque ligne traitée avec son numéro
- Affiche un résumé final (lignes traitées, commentaires ignorés)

---

## Pièces jointes nécessaires pour recréer le programme

1. `Prompt_contexte0412.md` — Contexte général du projet
2. `Prompt_saisis2fr.md` — Ce document
3. `tagssaisis.csv` — Exemple de fichier d'entrée
4. `standardise.py` — Module de standardisation (pour référence de la fonction)

---

## Fichiers associés

| Fichier | Rôle |
|---------|------|
| `refs/tagssaisis.csv` | Fichier d'entrée (protégé, données utilisateur) |
| `refs/tagsfr.csv` | Fichier de sortie |
| `standardise.py` | Module de standardisation |
| `saisis2fr.py` | Programme de transformation |

---

**FIN DU DOCUMENT**
