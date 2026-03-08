# Prompt_github_portraits.md

## Objet

Instructions pas à pas pour héberger les vignettes de portraits sur GitHub et les intégrer dans `portraits.csv`.

---

## Étape 1 : Redimensionner les photos

```cmd
cd C:\cx
python resize_portraits.py C:\cx\data\photos -o C:\cx\data\thumbs -v
```

Résultat attendu : 1600 vignettes JPEG 200px dans `C:\cx\data\thumbs\` (~10 Mo total).

---

## Étape 2 : Créer le repo GitHub

### 2a. Aller sur GitHub

1. Se connecter à https://github.com avec le compte **jawakaspa**
2. Cliquer sur **"+"** en haut à droite → **"New repository"**
3. Remplir :
   - Repository name : `orqual-portraits`
   - Description : `Portrait thumbnails for KITVIEW orthodontic search`
   - Visibilité : **Public** (obligatoire pour les URLs raw gratuites)
   - Cocher : **"Add a README file"**
4. Cliquer **"Create repository"**

### 2b. Cloner le repo localement

```cmd
cd C:\cx
git clone https://github.com/jawakaspa/orqual-portraits.git
```

### 2c. Copier les vignettes

```cmd
mkdir C:\cx\orqual-portraits\thumbs
xcopy C:\cx\data\thumbs\*.jpg C:\cx\orqual-portraits\thumbs\ /Y
```

### 2d. Commit et push

```cmd
cd C:\cx\orqual-portraits
git add thumbs/
git commit -m "Add 1600 portrait thumbnails (200px JPEG)"
git push origin main
```

> ⚠️ Le push de ~10 Mo peut prendre 1-2 minutes selon la connexion.

---

## Étape 3 : Vérifier l'accès aux images

Après le push, chaque image est accessible via URL raw :

```
https://raw.githubusercontent.com/jawakaspa/orqual-portraits/main/thumbs/1000.jpg
https://raw.githubusercontent.com/jawakaspa/orqual-portraits/main/thumbs/1001.jpg
...
https://raw.githubusercontent.com/jawakaspa/orqual-portraits/main/thumbs/2599.jpg
```

Tester dans un navigateur : ouvrir l'URL du portrait 1000 pour vérifier.

---

## Étape 4 : Mettre à jour portraits.csv

```cmd
cd C:\cx
python update_portraits_csv.py C:\cx\refs\portraits.csv -v
```

Ce script ajoute les 1600 lignes (IDs 1000-2599) avec les URLs GitHub au fichier `portraits.csv` existant, sans toucher aux 50 premières lignes (placeholders 1-50).

---

## Étape 5 : Mettre à jour communb.csv

Ajouter manuellement la section `bases` dans `communb.csv` (fichier protégé) :

```csv
# ═══════════════════════════════════════════════════════════════;;;
# SECTION BASES - Chemins des bases de données et Photofit;;;
# ═══════════════════════════════════════════════════════════════;;;
bases;photofit;bases/photofit.db;Base des embeddings faciaux Photofit
bases;photofit_max_results;20;Nombre max de portraits similaires (référent compris)
bases;photofit_weight_hair;0.3;Poids du hair_embedding
bases;photofit_weight_face;0.7;Poids du face_embedding
bases;photofit_seuil;1000;Seuil idportrait pour recherche par similarité
```

> ⚠️ `communb.csv` est un fichier protégé → modification manuelle uniquement.

---

## Étape 6 : Tester

```cmd
REM Vérifier que portraits.csv contient bien 1650 lignes (50 + 1600)
python -c "import csv; r=list(csv.DictReader(open('refs/portraits.csv','r',encoding='utf-8-sig'),delimiter=';')); print(f'{len(r)} portraits')"

REM Vérifier une URL
python -c "import urllib.request; urllib.request.urlopen('https://raw.githubusercontent.com/jawakaspa/orqual-portraits/main/thumbs/1000.jpg'); print('OK')"
```

---

## Résumé des fichiers

| Fichier | Action |
|---|---|
| `resize_portraits.py` | NOUVEAU - Redimensionnement batch |
| `update_portraits_csv.py` | NOUVEAU - Ajout URLs GitHub dans portraits.csv |
| `portraits.csv` | MODIFIÉ - +1600 lignes (IDs 1000-2599) |
| `communb.csv` | MODIFIÉ - +section bases (Photofit) |
| `jsonsql.py` | À MODIFIER (étape suivante) - Recherche similarité |

---

**FIN DU DOCUMENT**
