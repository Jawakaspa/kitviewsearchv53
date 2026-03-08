# Prompt_tagssaisis2tagsfr

## Objet

Transformation du fichier `tagssaisis.csv` (format utilisateur français, facile à saisir) en `tagsfr.csv` (format informatique, préparé pour l'internationalisation).

---

## Fichier d'entrée : tagssaisis.csv

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

**Cas particulier — adjectifs à supprimer** :

Quand le terme canonique est vide, tous les synonymes listés sont des termes à ignorer (ils n'ajoutent ni n'enlèvent rien au sens du tag).

**Exemple pour bruxisme** :
```
|nocturne|la nuit|nuitamment|des dents|les dents|dents|dent|dentaire|dentaires
```

Signification : tous ces termes (nocturne, la nuit, nuitamment, des dents, etc.) peuvent être supprimés sans perte de sens.

### Exemples de lignes

```csv
type;canonfr;synonymesfr;adjectifsfr
p;Béance;beance,béance dentaire,espace entre les dents,espace interdentaire,morsure béante,morsure ouverte,trou,open bite,openbite;gauche,antérieure|face,droite,latérale,postérieure,sévère|grave|marqué|important|majeur|marquée|importante|majeure|complexe,modérée|bénin|bénine|léger|faible|limité|mineur|discret|légère|limitée|mineure|discrète
p;bruxisme;bruxomanie,clenching,grincement,grincements,grinding,serrement,usure,grince,grincent;|nocturne|la nuit|nuitamment|des dents|les dents|dents|dent|dentaire|dentaires
p;avulsion;arrachage dentaire,arracher,dédentation,enlever,exodontie,extraction,extraction dentaire,extraire;immédiate,immédiat
```

---

## Fichier de sortie : tagsfr.csv

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

## Programme : tagssaisis2tagsfr.py

### Fonctionnalités

1. Vérifie l'encodage UTF-8-BOM du fichier d'entrée
2. Vérifie la présence des colonnes attendues
3. Ignore les lignes de commentaires (commençant par `#`)
4. Transforme chaque ligne selon les règles définies
5. Génère le fichier de sortie en UTF-8-BOM

### Utilisation

```bash
python tagssaisis2tagsfr.py
```

Le programme :
- Lit `tagssaisis.csv` dans le même répertoire
- Génère `tagsfr.csv` dans le même répertoire

### Affichage

- Affiche le cartouche (nom, version, date)
- Affiche les chemins absolus des fichiers
- Affiche chaque ligne traitée avec son numéro
- Affiche un résumé final (lignes traitées, commentaires ignorés)

---

## Prochaine étape

Ajout de 4 colonnes par langue pour l'internationalisation :
- `{lang}tags` : traduction des tags
- `std{lang}tags` : tags traduits standardisés
- `{lang}adjs` : traduction des adjectifs
- `std{lang}adjs` : adjectifs traduits standardisés

Langues prévues : en, de, es, it, pt, pl, ro, th, ar, cn

---

## Fichiers associés

| Fichier | Rôle |
|---------|------|
| `tagssaisis.csv` | Fichier d'entrée (protégé, données utilisateur) |
| `tagsfr.csv` | Fichier de sortie |
| `standardise.py` | Module de standardisation |
| `tagssaisis2tagsfr.py` | Programme de transformation |

---

**FIN DU DOCUMENT**
