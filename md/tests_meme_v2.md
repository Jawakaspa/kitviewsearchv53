# Prompt tests_meme_v2 V1.0.1 - 21/01/2026 10:01:35

# Plan de tests - Système "Même X" V2.0

**Date** : 20 janvier 2026  
**Fichiers concernés** : detmeme.py V2.0.0, web24.html V1.0.0, web24.css V1.0.0

---

## PARTIE 1 : Tests detmeme.py (CLI)

### 1.1 Tests unitaires basiques

```bash
# Test 1.1.1 - Critère simple avec ID
python detmeme.py "même portrait que id 123"
# Attendu : 1 critère (portrait), référence id:123

# Test 1.1.2 - Critère simple avec nom
python detmeme.py "même portrait que Guillaume Moulin"
# Attendu : 1 critère (portrait), référence nom:Guillaume Moulin

# Test 1.1.3 - Critère prénom
python detmeme.py "même prénom que Jean Dupont"
# Attendu : 1 critère (prenom), référence nom:Jean Dupont

# Test 1.1.4 - Critère âge
python detmeme.py "même âge que Marie Martin"
# Attendu : 1 critère (age), référence nom:Marie Martin

# Test 1.1.5 - Critère sexe
python detmeme.py "même sexe que Pierre Durand"
# Attendu : 1 critère (sexe), référence nom:Pierre Durand

# Test 1.1.6 - Critère nom de famille
python detmeme.py "même nom que Alice Bernard"
# Attendu : 1 critère (nom), référence nom:Alice Bernard
```

### 1.2 Tests critères multiples (avec "et")

```bash
# Test 1.2.1 - Deux critères
python detmeme.py "même portrait et même prénom que Guillaume Moulin"
# Attendu : 2 critères (portrait, prenom), référence nom:Guillaume Moulin

# Test 1.2.2 - Trois critères
python detmeme.py "même portrait et même prénom et même âge que Guillaume Moulin"
# Attendu : 3 critères (portrait, prenom, age), référence nom:Guillaume Moulin

# Test 1.2.3 - Quatre critères
python detmeme.py "même portrait et même prénom et même âge et même sexe que id 456"
# Attendu : 4 critères, référence id:456

# Test 1.2.4 - Cinq critères (max réaliste)
python detmeme.py "même portrait et même prénom et même nom et même âge et même sexe que Jean Valjean"
# Attendu : 5 critères, référence nom:Jean Valjean
```

### 1.3 Tests tags spécifiques (1 mot)

```bash
# Test 1.3.1 - Tag simple
python detmeme.py "même bruxisme que Guillaume Moulin"
# Attendu : 1 critère (tag, valeur="bruxisme"), référence nom:Guillaume Moulin

# Test 1.3.2 - Tag avec accent
python detmeme.py "même béance que Marie Martin"
# Attendu : 1 critère (tag, valeur="beance"), référence nom:Marie Martin

# Test 1.3.3 - Tag + critère générique
python detmeme.py "même bruxisme et même âge que id 789"
# Attendu : 2 critères (tag=bruxisme, age), référence id:789
```

### 1.4 Tests pathologies spécifiques (plusieurs mots)

```bash
# Test 1.4.1 - Pathologie 2 mots
python detmeme.py "même bruxisme nocturne que Guillaume Moulin"
# Attendu : 1 critère (pathologie, valeur="bruxisme nocturne")

# Test 1.4.2 - Pathologie 3 mots
python detmeme.py "même béance antérieure gauche que Jean Dupont"
# Attendu : 1 critère (pathologie, valeur="beance anterieure gauche")

# Test 1.4.3 - Pathologie 4 mots
python detmeme.py "même béance antérieure gauche modérée que Marie Martin"
# Attendu : 1 critère (pathologie, valeur="beance anterieure gauche moderee")

# Test 1.4.4 - Pathologie + critères génériques
python detmeme.py "même portrait et même bruxisme nocturne sévère et même âge que id 123"
# Attendu : 3 critères (portrait, pathologie="bruxisme nocturne severe", age)
```

### 1.5 Tests cas limites

```bash
# Test 1.5.1 - Sans référence (devrait échouer gracieusement)
python detmeme.py "même portrait"
# Attendu : 1 critère (portrait), référence null

# Test 1.5.2 - Nom composé avec tiret
python detmeme.py "même portrait que Jean-Pierre Dupont-Martin"
# Attendu : référence nom:Jean-Pierre Dupont-Martin

# Test 1.5.3 - Nom avec apostrophe
python detmeme.py "même portrait que Patrick O'Brien"
# Attendu : référence nom:Patrick O'Brien

# Test 1.5.4 - Question avec bruit avant
python detmeme.py "cherche les patients avec même portrait que Guillaume Moulin"
# Attendu : 1 critère (portrait), résidu contient "cherche les patients avec"

# Test 1.5.5 - Synonymes de "même"
python detmeme.py "identique portrait que Jean Dupont"
# Attendu : 1 critère (portrait) si "identique" est dans commun.csv
```

### 1.6 Test batch (fichier CSV)

Créer `tests/testsmemein.csv` :
```csv
# Tests detmeme v2.0
question
même portrait que Guillaume Moulin
même portrait et même prénom que id 123
même bruxisme nocturne que Marie Martin
même béance antérieure gauche et même âge que Jean Dupont
```

```bash
python detmeme.py tests/testsmemein.csv --verbose
# Vérifie le fichier testsmemeout.csv généré
```

---

## PARTIE 2 : Tests web24 (Interface)

### 2.1 Tests affichage de base

| # | Action | Résultat attendu |
|---|--------|------------------|
| 2.1.1 | Ouvrir web24.html | Page se charge sans erreur console |
| 2.1.2 | Vérifier version | "V1.0.0" affiché sous "Search" |
| 2.1.3 | Lancer recherche "bruxisme" | Résultats affichés avec nouveau style |

### 2.2 Tests affichage pathologies

| # | Action | Résultat attendu |
|---|--------|------------------|
| 2.2.1 | Observer une card patient | Tags en **blanc sur sombre** |
| 2.2.2 | Observer pathologies complètes | En **noir sur clair** sous les tags |
| 2.2.3 | Vérifier tri | Pathologies triées par longueur décroissante |
| 2.2.4 | Vérifier alignement | Texte aligné à gauche |

### 2.3 Tests affichage patient

| # | Action | Résultat attendu |
|---|--------|------------------|
| 2.3.1 | Observer ID patient | `#123` visible en haut à droite de la card |
| 2.3.2 | Observer nom/prénom | Badges **blanc sur sombre** |
| 2.3.3 | Observer sexe/âge | Badges **blanc sur sombre** sur ligne séparée |
| 2.3.4 | Hover sur badge | Légère animation (translateY) |

### 2.4 Tests bouton expand

| # | Action | Résultat attendu |
|---|--------|------------------|
| 2.4.1 | Observer bas de card | Chevron `⌄` visible |
| 2.4.2 | Cliquer sur chevron | Card s'agrandit, chevron devient `⌃` |
| 2.4.3 | Re-cliquer sur chevron | Card se réduit |
| 2.4.4 | Cliquer sur X rouge | Card se réduit (quand agrandie) |

---

## PARTIE 3 : Tests système "Même" (interaction)

### 3.1 Tests sélection patient référence

| # | Action | Résultat attendu |
|---|--------|------------------|
| 3.1.1 | Cliquer sur portrait patient | Card devient **jaune fluo** |
| 3.1.2 | Vérifier input | Affiche "Même portrait que Prénom Nom" |
| 3.1.3 | Vérifier bordure portrait | Bordure devient rouge (critère actif) |
| 3.1.4 | Vérifier recherche | Nouvelle recherche lancée automatiquement |

### 3.2 Tests critères multiples (même patient)

| # | Action | Résultat attendu |
|---|--------|------------------|
| 3.2.1 | Après 3.1.1, cliquer sur prénom | Input : "Même portrait et même prénom que Nom" |
| 3.2.2 | Cliquer sur âge | Input : "Même portrait et même prénom et même âge que Nom" |
| 3.2.3 | Cliquer sur tag (ex: Bruxisme) | Critère ajouté avec "et" |
| 3.2.4 | Vérifier couleur critères | Tous les critères actifs en **ROUGE** |

### 3.3 Tests toggle (retrait critère)

| # | Action | Résultat attendu |
|---|--------|------------------|
| 3.3.1 | Re-cliquer sur prénom (actif/rouge) | Critère retiré, recherche relancée |
| 3.3.2 | Vérifier input | "et même prénom" disparu de la question |
| 3.3.3 | Retirer tous les critères | Retour à la recherche initiale |
| 3.3.4 | Vérifier card | Plus de fond jaune fluo |

### 3.4 Tests changement de patient référence

| # | Action | Résultat attendu |
|---|--------|------------------|
| 3.4.1 | Patient A sélectionné, cliquer prénom patient B | **Ignoré** (pas d'effet) |
| 3.4.2 | Cliquer portrait patient B | Patient B devient référence |
| 3.4.3 | Vérifier card A | Plus de fond jaune |
| 3.4.4 | Vérifier card B | Fond **jaune fluo** |
| 3.4.5 | Vérifier critères A | Reset, seul "même portrait" actif pour B |

### 3.5 Tests zones non cliquables

| # | Action | Résultat attendu |
|---|--------|------------------|
| 3.5.1 | Patient A sélectionné, hover nom patient B | Curseur normal (pas pointer) |
| 3.5.2 | Hover âge patient B | Curseur normal, pas de tooltip |
| 3.5.3 | Hover portrait patient B | Curseur pointer (seul élément cliquable) |
| 3.5.4 | Vérifier opacité | Critères patient B légèrement grisés |

---

## PARTIE 4 : Tests pathologies cliquables

### 4.1 Tests tags (fond sombre)

| # | Action | Résultat attendu |
|---|--------|------------------|
| 4.1.1 | Cliquer sur tag "Bruxisme" | Critère "même bruxisme" ajouté |
| 4.1.2 | Vérifier input | Contient "même bruxisme que Nom" |
| 4.1.3 | Tag devient rouge | Indicateur critère actif |
| 4.1.4 | Re-cliquer tag rouge | Critère retiré |

### 4.2 Tests pathologies complètes (fond clair)

| # | Action | Résultat attendu |
|---|--------|------------------|
| 4.2.1 | Cliquer sur "Bruxisme Nocturne Sévère" | Critère pathologie complète ajouté |
| 4.2.2 | Vérifier input | "même bruxisme nocturne sévère que Nom" |
| 4.2.3 | Pathologie devient rouge | Indicateur actif |
| 4.2.4 | Re-cliquer | Critère retiré |

### 4.3 Tests combinaisons

| # | Action | Résultat attendu |
|---|--------|------------------|
| 4.3.1 | Sélectionner tag + pathologie complète | Les deux en rouge, question avec "et" |
| 4.3.2 | Ajouter portrait + âge | 4 critères, tous rouges |
| 4.3.3 | Retirer 2 critères | 2 restants, question mise à jour |

---

## PARTIE 5 : Tests intégration complète

### 5.1 Scénario complet 1 : Recherche simple

1. Lancer recherche "patients qui grincent des dents"
2. Observer résultats (6407 patients attendus)
3. Cliquer portrait premier patient
4. Vérifier : fond jaune, input mis à jour, nouvelle recherche
5. Cliquer prénom du même patient
6. Vérifier : 2 critères dans input
7. Retirer le prénom
8. Vérifier : retour à 1 critère
9. Retirer le portrait
10. Vérifier : retour recherche initiale

### 5.2 Scénario complet 2 : Multi-critères pathologies

1. Rechercher "béance"
2. Sélectionner portrait patient avec "Béance Antérieure Gauche Modérée"
3. Ajouter le tag "Béance" (fond sombre)
4. Ajouter la pathologie complète "Béance Antérieure Gauche Modérée" (fond clair)
5. Ajouter l'âge
6. Vérifier question : "Même portrait et même béance et même béance antérieure gauche modérée et même âge que Nom"
7. Changer de patient référence (clic portrait autre patient)
8. Vérifier : reset complet, nouveau patient en jaune

### 5.3 Scénario complet 3 : Vérification backend

1. Lancer recherche "même portrait et même bruxisme que Guillaume Moulin"
2. Vérifier console : question technique envoyée
3. Vérifier résultats : patients avec même portrait ET bruxisme
4. Cliquer sur un critère d'un résultat
5. Vérifier : critère ajouté à la recherche

---

## Checklist de validation finale

- [ ] detmeme.py parse correctement critères multiples
- [ ] detmeme.py extrait la référence (nom ou id)
- [ ] detmeme.py gère tags et pathologies spécifiques
- [ ] web24 affiche ID patient en haut à droite
- [ ] web24 affiche patient référence en jaune fluo
- [ ] web24 affiche badges blanc sur sombre
- [ ] web24 affiche pathologies avec nouveau style
- [ ] web24 trie pathologies par longueur
- [ ] web24 gère toggle critères (ajout/retrait)
- [ ] web24 génère question lisible avec "et"
- [ ] web24 désactive critères autres patients
- [ ] web24 permet changement référence via portrait
- [ ] web24 revient à recherche initiale si plus de critères
- [ ] Bouton expand fonctionne
- [ ] Pas d'erreur console JS
- [ ] Mode sombre fonctionne

---

**Fin du plan de tests**
