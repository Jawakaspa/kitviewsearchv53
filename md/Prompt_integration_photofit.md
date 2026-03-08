# Prompt_integration_photofit.md

## Objet

Prompt de continuation pour intégrer la recherche de portraits par similarité faciale (Photofit V5.2) dans le pipeline de recherche existant.

---

## Contexte du projet Photofit V5.2

### Ce qui existe déjà

**Base photofit.db** (`C:\cx\bases\photofit.db`) :
- 1600 portraits (IDs 1000 à 2599), organisés en 160 groupes de 10
- Chaque enregistrement contient : `portrait_id`, `attributes` (JSON, 16 attributs faciaux), `hair_embedding` (384 dims), `face_embedding` (128 dims)
- Poids optimaux validés par tests : **hair=0.3, face=0.7** (Recall@10 = 100% sur les groupes)

**Programme search_similar.py** :
- CLI de recherche de portraits similaires dans photofit.db
- Calcul de distance pondérée : `distance = weight_hair × cosine(hair) + weight_face × cosine(face)`
- Usage : `python search_similar.py 1000 --db bases/photofit.db --weight-hair 0.3 --weight-face 0.7 -n 20`
- **À MODIFIER** : mettre les poids par défaut à 0.3h/0.7f (actuellement 0.5/0.5)

**1600 vignettes sur GitHub** :
- Repo : `https://github.com/Jawakaspa/orqual-portraits`
- URL type : `https://raw.githubusercontent.com/Jawakaspa/orqual-portraits/main/thumbs/{id}.jpg`
- Vignettes 200px JPEG optimisées (~6-8 Ko chacune)

**portraits.csv** (`refs/portraits.csv`) :
- Actuellement 50 placeholders (IDs 1-50) pointant vers Google Storage
- **À ENRICHIR** avec 1600 lignes (IDs 1000-2599) pointant vers GitHub
- Script prêt : `python update_portraits_csv.py refs/portraits.csv -v`

**communb.csv** (`refs/communb.csv`) :
- **À ENRICHIR** avec la section `bases` suivante (fichier protégé, modification manuelle) :
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

### Principe de la recherche hybride portraits

Le champ `idportrait` de la table `patients` détermine le mode de recherche :

| idportrait | Type | Recherche "même portrait" | Source image |
|---|---|---|---|
| 1-999 | Placeholder | Match exact (`p.idportrait = ?`) | Google Storage (portraits.csv) |
| 1000-2599 | Photofit réel | Similarité faciale via photofit.db | GitHub (portraits.csv) |

Cela permet de **mixer les deux modes** dans une même base pendant la transition.

---

## Ce qu'il faut modifier

### 1. `jsonsql.py` — Fonction `_generer_clause_meme` (MODIFICATION PRINCIPALE)

**Fichier fourni en PJ.** Version actuelle : V1.1.0.

Le bloc à modifier se trouve dans `_generer_clause_meme()`, case `portrait` (lignes 252-258) :

```python
# CODE ACTUEL (match exact pour tous les portraits)
elif cible == 'portrait':
    idportrait_ref = ref_patient.get('idportrait', '')
    if idportrait_ref:
        where_clause = "p.idportrait = ?"
        params = [idportrait_ref]
```

**Comportement souhaité :**
```
Si idportrait >= seuil (1000, lu depuis communb.csv) :
    1. Ouvrir photofit.db (chemin lu depuis communb.csv, section bases, parametre photofit)
    2. Chercher les N portraits les plus similaires (N = photofit_max_results depuis communb.csv)
    3. Utiliser les poids hair/face depuis communb.csv
    4. Générer une clause : p.idportrait IN (id1, id2, ..., idN)
Sinon :
    Comportement actuel (match exact p.idportrait = ?)
```

**Points importants :**
- `jsonsql.py` doit lire communb.csv pour obtenir le chemin de photofit.db et les paramètres
- La recherche de similarité dans photofit.db utilise la même logique que `search_similar.py`
- Il faut extraire/factoriser la logique de recherche vectorielle pour pouvoir l'appeler depuis jsonsql.py
- Le résultat est une liste d'IDs de portraits similaires (en str, car idportrait est TEXT dans la base patients)

**Signature existante de `generer_sql()` — NE PAS MODIFIER** :
```python
def generer_sql(json_detection: dict, limit: int = None, offset: int = 0, 
                verbose: bool = False, debug: bool = False) -> dict:
```

La lecture de communb.csv doit se faire à l'intérieur de jsonsql.py, pas via un nouveau paramètre.

### 2. `search_similar.py` — Poids par défaut (MODIFICATION MINEURE)

**Fichier fourni en PJ.**

Changer les poids par défaut de 0.5/0.5 à 0.3/0.7 :
- `--weight-hair` : défaut 0.5 → **0.3**
- `--weight-face` : défaut 0.5 → **0.7**

### 3. `detmeme.py` — AUCUNE MODIFICATION

Ce fichier détecte déjà correctement `cible: 'portrait'` quand l'utilisateur dit "même portrait que...". Il n'a pas besoin d'être modifié.

### 4. `lancesql.py` — AUCUNE MODIFICATION

Ce fichier exécute le SQL généré par jsonsql.py. La clause `IN (...)` est du SQL standard, pas besoin de changement.

---

## Fichiers à joindre

Pour la modification de jsonsql.py, joindre :
1. **jsonsql.py** (version actuelle V1.1.0)
2. **communb.csv** (avec la section bases déjà ajoutée)
3. **search_similar.py** (pour la logique de recherche vectorielle à factoriser)
4. **Ce prompt** (Prompt_integration_photofit.md)
5. **Prompt_contexte0502.md** (conventions du projet)

---

## Tests attendus

Après modification, on doit pouvoir tester le pipeline complet :

```cmd
REM Test 1 : Recherche "même portrait" avec un patient ayant idportrait=1000
REM → Doit retourner ~20 patients dont les idportrait sont les plus similaires à 1000

REM Test 2 : Recherche "même portrait" avec un patient ayant idportrait=5
REM → Doit retourner les patients avec idportrait=5 (match exact, comportement actuel)

REM Test 3 : Vérifier que les portraits >= 1000 affichent les vignettes GitHub
REM → URL dans portraits.csv : https://raw.githubusercontent.com/Jawakaspa/orqual-portraits/main/thumbs/{id}.jpg
```

---

## Rappel : ne pas toucher

- `detmeme.py` : pas de modification
- `lancesql.py` : pas de modification
- `communb.csv` : fichier protégé (modification manuelle par l'utilisateur)
- `portraits.csv` : fichier protégé (enrichi par update_portraits_csv.py, pas d'écrasement)

---

**FIN DU DOCUMENT**
