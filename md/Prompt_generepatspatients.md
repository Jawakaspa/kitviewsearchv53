# Prompt_generepats.md

## Objet

Ce prompt permet de recréer intégralement le programme `generepats.py` à partir de zéro. 

Cette version compatible avec patientsN est la version 2.0.

---

## Fichiers à joindre en pièce jointe

1. **Prompt_contexte.md** - Le contexte du projet (joint au projet)
2. **refs/portraits.csv** - Portraits par sexe (colonnes : `sexe;portrait`)
3. **refs/tags.csv** - Tags et adjectifs (colonnes : `type;frtags;stdfrtags;fradjs;stdfradjs;entags;...`)
4. **refs/sexeorigine.csv** - Origines des noms/prénoms (colonnes : `sexe;origine;nom;poidsnom;prenom;poidsprenom`)

---

## Prompt de recréation

```
Crée le programme Python generepats.py selon les spécifications suivantes.

### Objectif

Générer des fichiers CSV de patients orthodontiques fictifs avec données réalistes pour tester le système de recherche Kitview. Le programme doit pouvoir générer de 2 à 200 000 patients.

### Usage

```bash
python generepats.py <nombre> [--silent]
```

- `<nombre>` : Nombre de patients à générer (2 à 200 000)
- `--silent` : Mode silencieux (optionnel)

### Structure des répertoires

Le programme utilise les répertoires suivants relatifs à son emplacement :

- `refs/` : Fichiers de référence en entrée (lecture seule)
- `data/` : Fichiers patients générés (écriture)
- `logs/` : Logs de génération (écriture)
- `stats/` : Statistiques de génération (écriture)

Les répertoires `data/`, `logs/` et `stats/` sont créés automatiquement s'ils n'existent pas.

### Fichiers de référence en entrée (dans refs/)

Tous les fichiers CSV utilisent le séparateur `;` et l'encodage UTF-8-SIG. Le programme doit supporter plusieurs encodages en lecture (utf-8-sig, utf-8, windows-1252, iso-8859-1) et afficher un warning si ce n'est pas UTF-8-SIG.

1. **portraits.csv** : `sexe;portrait`
2. **tags.csv** : `type;frtags;stdfrtags;fradjs;stdfradjs;entags;stdentags;enadjs;stdenadjs;...` (une colonne par langue avec le pattern xxtags, xxadjs où xx est le code langue)
3. **sexeorigine.csv** : `sexe;origine;nom;poidsnom;prenom;poidsprenom`

### Fichiers générés en sortie

#### data/patsN.csv

Colonnes dans l'ordre exact :



id;canontags;canonadjs;sexe;age;datenaissance;prenom;nom;portrait;oripathologies;oriprenom;orinom;ville;tags;agedebut;datedebut;traitement;statut;prix;dureemois;avancement;nbphotos;nodept;dept;region;regionhisto;sexepraticien;prenompraticien;nompraticien;portraitpraticien;search_text

A comparer à la version précédente :

```
id;canontags;canonadjs;sexe;age;datenaissance;prenom;nom;portrait
```

#### stats/statsN_tags.csv

Colonnes : `canontag;canonadj;effectif`

#### stats/statsN_age.csv

Colonnes : `age;effectif;pourcentage`

### Règles de génération

#### Dépendance Faker

Le programme utilise la bibliothèque `faker` (locale `fr_FR`). Si Faker n'est pas installé, afficher une erreur et quitter avec le code 2.

#### Reproductibilité

Utiliser des générateurs Random séparés avec seeds fixes pour chaque type de donnée :

- rand_general (seed 42) : usage général
- rand_sexe (seed 43) : génération du sexe
- rand_age (seed 44) : génération de l'âge
- rand_tags (seed 45) : sélection de tags
- rand_adjs (seed 46) : sélection d'adjectifs
- Faker.seed(42) pour Faker

#### Id

- Numéro séquentiel commençant par 1.

#### Génération de canontags et des canonadj

Le principe général c'est de ne stocker que les données brutes. C'est la raison pour laquelle dans ce fichier il n'y a aucune colonne de nom std...

Les tags et les adjectifs proviennent du fichier tags.csv et des colonnes françaises non standardisées respectivement `frtags` et `fradjs`.

Ces deux colonnes sont appelées canontags et canonadj car on ne va stocker dans le fichier que les valeurs canoniques. C'est à dire le premier tag de la colonne `frtags` pour les tags.

Distribution du nombre de tags :

- 1 tag: 40%
- 2 tags: 25%
- 3 tags: 20%
- 4 tags: 15%

Par ailleurs béance devra être 20% des tags et bruxisme 10%. Les autres tags se répartissent équitablement le reste (70%).

Les tags générés sont dans la colonne tags séparées par des virgules dès qu'il y en a plus d'un.

#### Génération des adjectifs

Distribution :

- 0 adjectif: 30%
- 1 adjectif: 20%
- 2 adjectifs: 20%
- 3 adjectifs: 20%
- 4 adjectifs: 10%

La colonne s'appelle canonadj car à l'instar des tags on ne va stocker dans le fichier que les valeurs canoniques. Pour les adjectifs le processus est le suivant :

- on regarde dans la colonne adjectifs combien il y a d'adjectifs.

- On fait un dédoublonnage large c'est à dire qu'on enlève les s finaux et ensuite les e finaux si le terme sans s fil ou sans e final existe. Et ensuite on dédoublonne.

Exemple pour les adjectifs de béance :

On part de :

gauche,antérieure|face,droite,latérale,postérieure,sévère|grave|marqué|important|majeur|marquée|importante|majeure|complexe,modérée|bénin

On enlève les s finaux s'il y a le même sans s final. Ce n'est pas le cas ici et donc on ne fait rien

On enlève les e finaux s'il y a le même terme sans e final :

gauche,antérieure|face,droite,latérale,postérieure,sévère|grave|marqué|important|majeur|marqué|important|majeur|complexe,modérée|bénin

4 e finaux ont été enlevés. On a alors des doublons qu'on va éliminer pour arriver à :

gauche,antérieure|face,droite,latérale,postérieure,sévère|grave|marqué|important|majeur|complexe,modérée|bénin

Ensuite on se retrouve avec un certain nombre d'adjectifs séparés par des ,. Et pour plusieurs adjectis il y a des synonymes comme par exemple pour sévère qui a comme synonymes grave, marqué, important, majeur et complexe.

Dans tous les cas, qu'il y ait des synonymes ou non c'est toujours le premier adjectif qui est la forme canonique qui est retenue. Par exemple : gauche, antérieure, modérée, sévère.

#### Format de stockage canontags et canonadjs

- **canontags** : Tags séparés par des virgules. Ex: `Béance,bruxisme,avulsion`
- **canonadjs** : Aligné avec les tags position par position :
  - Chaque groupe d'adjectifs (pour un tag) est séparé par une virgule
  - Les adjectifs d'un même tag sont séparés par `|`
  - Si un tag n'a pas d'adjectif, son slot est vide mais la virgule est présente

Exemples :

```
canontags: Béance
canonadjs: latérale|gauche|postérieure

canontags: bruxisme,avulsion,Classe III squelettique
canonadjs: ,immédiate,

canontags: Classe II squelettique,Classe III squelettique,avulsion
canonadjs: ,,immédiate

canontags: avulsion,Béance,Classe II squelettique
canonadjs: ,sévère|gauche|modérée,
```

#### Sexe

50% F, 50% M

#### Génération de l'âge

Distribution gaussienne : moyenne 15 ans, écart-type 6, borné entre 5 et 50 ans.
Stocker avec 3 décimales.

#### Génération de la date de naissance

Comme on a 3 décimales pour l'âge, ça donne en principe de façon certaine la date de naissance en fonction du jour de lancement de la génération. S'il y a malgré tout un doute sur 2 dates choisir la première.

#### Portrait

Sélection aléatoire dans portraits.csv selon le sexe

#### Génération des noms/prénoms

- 75% : Utiliser Faker (first_name_female/first_name_male + last_name)
- 25% : Utiliser sexeorigine.csv avec pondération (poidsnom pour les noms, poidsprenom pour les prénoms de même origine). Limiter le choix des prénoms aux prénoms de même sexe.
- Le prénom doit être généré à la fois dans les colonnes oriprenom et prenom 

- Le nom doit être généré à la fois dans les colonnes orinom et nom

#### Oripathologies

La colonne oripathologies doit concaténer les tags avec leurs adjectifs triés par ordre alphabétique croissant pour en faire une exception avec tags et adjectifs séparés par des espaces et expressions séparées par des virgules.

Dans les exemple qui suivent on a tous les tags canoniques d'un patient dans la colonne canontags séparés par des ",". On a ensuite pour chaque tag les adjectifs correspondants dans la colonne canonadjs avec à chaque virgule les adjectifs du tag correspondant. Dans la colonne oripathologies on voit le résultat de la transformation : on concatène le tag puis un espace puis tous ses adjectifs triés par ordre alphabétiques en remplaçant les | par des espaces. Les expressions sont comme pour les canontags et les canonadjs séparés par des espaces. Exemples :

id;canontags;canonadjs;oripathologies
8;Bruxisme,vestibulo-version,proalvéolie;nocturne,,mandibulaire|maxillaire|sévère;Bruxisme nocturne,vestibulo-version ,proalvéolie mandibulaire maxillaire sévère
9;avulsion;programmé;avulsion programmé, , 
10;supraposition,béance,avulsion;,antérieur|gauche|sévère|latéral,;supraposition ,béance antérieur gauche latéral sévère,avulsion 
14;nécrose pulpaire,macrodontie,béance;,modéré,antérieur;nécrose pulpaire ,macrodontie modéré,béance antérieur

On constate par exemple pour l'id 10 le tri pour les adjectifs de la béance.

#### Génération des autres colonnes

Toutes les autres colonnes à partir de la colonne ville à savoir ;ville;tags;agedebut;datedebut;traitement;statut;prix;dureemois;avancement;nbphotos;nodept;dept;region;regionhisto;sexepraticien;prenompraticien;nompraticien;portraitpraticien;search_text doivent rester vides.

### Affichage

#### Progression

- Afficher chaque fichier de référence chargé avec le nombre d'éléments
- Barre de progression tous les 500 patients : `[████████░░░░░░░░░░░░] 40% - Patient 2000/5000`
- Afficher chaque fichier généré avec son chemin absolu

#### Récapitulatif final

- Nombre de patients générés
- Liste des fichiers créés avec chemins absolus et tailles
- Temps d'exécution (chargement, génération, écriture, total, vitesse)
- TOP 10 tags
- TOP 10 tags+adjectifs
- Répartition des dates par période

### Codes de sortie

- 0 : Succès
- 1 : Erreur fichier
- 2 : Erreur Faker manquant
- 3 : Erreur génération
- 4 : Erreur écriture

### Cartouche des fichiers CSV générés

Chaque fichier CSV commence par une ligne de commentaire (#) :

```
#nomfichier.csv v1.0.0 - DD/MM/YYYY HH:MM:SS
```

### Gestion des erreurs

- Arrêt immédiat avec message clair si fichier de référence manquant
- Affichage du chemin absolu dans tous les messages d'erreur
- Capture KeyboardInterrupt pour interruption propre
- Traceback complet pour erreurs inattendues
  
  ```
  
  ```

---

## Version

- Document : v2.0.0
- Date : 13/12/2025
- Auteur : Claude Opus 4.5

## Historique

- v1.2.0 (07/12/2025) : Ajout spécification format canonadjs (alignement tags/adjs, séparateur | entre adjectifs d'un même tag)
- v1.1.0 (07/12/2025) : Corrections des noms de colonnes (frtags/fradjs au lieu de tagsrf/adjsfr), correction structure sexeorigine.csv
- v1.0.0 (07/12/2025) : Version initiale
