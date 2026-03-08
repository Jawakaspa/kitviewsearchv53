# Conversation Photofit V5.2 - Synthèse complète

**Projet** : Recherche de portraits similaires par IA pour KITVIEW Search  
**Dates** : 30/01/2026 → 12/02/2026  
**Version** : V5.2  

---

## 1. Objectif du projet

Remplacer le **placeholder "même portrait"** (qui faisait un simple match exact sur `idportrait`) par une **vraie recherche de similarité faciale** utilisant l'API Photofit de Maxime.

**Avant V5.2** : `même portrait que id 123` → retourne uniquement le patient avec `idportrait = 123`  
**Après V5.2** : `même portrait que id 10000` → retourne les N patients avec les visages les plus ressemblants

---

## 2. Architecture technique

### API Photofit (Maxime)

- **URL** : `https://demo.ia.orqual.info:506/photofit/api/v1/extract-features`
- **Méthode** : POST multipart/form-data avec paramètre `img`
- **Réponse** :
  - `attributes` : 16 attributs faciaux (probabilités 0-1)
  - `hair_embedding` : vecteur 384 dimensions (style capillaire)
  - `face_embedding` : vecteur 128 dimensions (reconnaissance faciale)

### Base vectorielle `photofit.db`

```sql
CREATE TABLE portraits (
    idportrait TEXT PRIMARY KEY,      -- "1000", "10000", etc.
    filepath TEXT NOT NULL,           -- Chemin local de l'image
    attributes_json TEXT,             -- JSON brut des 16 attributs
    attributes_bin TEXT,              -- Binarisé "1,0,1,0,..." (seuil 0.5)
    hair_embedding BLOB,              -- 384 floats sérialisés (1536 bytes)
    face_embedding BLOB,              -- 128 floats sérialisés (512 bytes)
    status TEXT,                      -- 'ok' ou 'error'
    error_message TEXT,               -- Détail si erreur
    created_at TEXT,
    updated_at TEXT
);
```

### Logique hybride dans `jsonsql.py`

| idportrait | Comportement |
|------------|--------------|
| < 1000 | Match exact (`WHERE idportrait = ?`) - placeholder ancien système |
| ≥ 1000 | Recherche par similarité faciale via `photofit.db` |

---

## 3. Bases de données disponibles

| Base | Patients | Description |
|------|----------|-------------|
| `base01600.db` | 1 600 | 160 photos originales × 10 (1 original + 9 variantes IA). **Idéal pour tester les ressemblances** car les variantes doivent être retrouvées. |
| `base01964.db` | 1 964 | Photos réelles fournies par Maxime (idportrait 10000-11963) |
| `base03200.db` | 3 200 | base01600 + 1600 tests préliminaires avec 50 photos partagées. Similarité placeholder (même id). |
| `base03564.db` | 3 564 | base01600 (1600) + base01964 (1964). **Base de test principale V5.2** |
| `base25000.db` | 25 000 | base03564 complétée par des patients avec 50 photos partagées. **Base de production** |

### Numérotation des portraits

| Plage idportrait | Source | Similarité |
|------------------|--------|------------|
| 1-50 | Photos Google Cloud Storage | Match exact (< 1000) |
| 1000-2599 | Jeu synthétique (160×10 variantes) | Similarité faciale |
| 10000-11963 | Photos réelles Maxime | Similarité faciale |

---

## 4. Résultats des tests comparatifs

Tests sur **160 groupes synthétiques** (1600 images : 160 originaux + 9 variantes dégradées chacun)

| Mode | Recall@10 | Groupes parfaits @10 |
|------|-----------|----------------------|
| **face** (100% face_embedding) | **71.60%** | **42/160** |
| both (30h/70f) | 68.06% | 24/160 |
| hair (100% hair_embedding) | 55.07% | 5/160 |

**Conclusion** : Contrairement à l'hypothèse initiale, le `face_embedding` surpasse le `hair_embedding` pour la recherche de ressemblance.

### Test avec poids optimisés (30h/70f)

```
python search_similar.py 1000 --weight-hair 0.3 --weight-face 0.7 -n 15
→ Recall 100% : les 9 variantes de 1000 sont dans le top 9
```

---

## 5. Paramètres Photofit configurables

Tous les paramètres sont dans `refs/communb.csv` (section `bases`) :

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| `photofit` | `bases/photofit.db` | Chemin de la base vectorielle |
| `photofit_max_results` | `20` | Nombre max de portraits retournés (référent inclus) |
| `photofit_weight_hair` | `0.3` | Poids du hair_embedding (30%) |
| `photofit_weight_face` | `0.7` | Poids du face_embedding (70%) |
| `photofit_seuil` | `1000` | Seuil idportrait pour activer la similarité |
| `photofit_distance_max` | `0.5` | Distance max pour calcul score 0-100 |
| `photofit_score_min` | `30` | Score minimum pour inclure un portrait |

### Ajuster les paramètres

- **Plus de résultats** : Augmenter `photofit_max_results` (ex: 50)
- **Résultats plus stricts** : Augmenter `photofit_score_min` (ex: 50)
- **Résultats plus larges** : Diminuer `photofit_score_min` (ex: 20)
- **Privilégier les cheveux** : `weight_hair=0.7`, `weight_face=0.3`

---

## 6. Programmes développés

| Programme | Description |
|-----------|-------------|
| `build_photofit_db.py` | Construit la base vectorielle via API Photofit |
| `search_similar.py` | CLI de recherche de portraits similaires |
| `test_photofit.py` | Validation du système (Recall, MRR, Precision) |
| `gen_variantes.py` | Génère les variantes dégradées pour les tests |
| `resize_portraits.py` | Redimensionne les images pour GitHub |

### Usage des programmes

```bash
# Construire la base
python build_photofit_db.py C:\cx\data\photofit -o C:\cx\bases\photofit.db -v
python build_photofit_db.py C:\cx\data\photofit --resume  # Reprendre si interrompu

# Rechercher des similaires
python search_similar.py 10000 --db C:\cx\bases\photofit.db -n 15
python search_similar.py 1000 --face -n 20  # Mode face uniquement

# Tester le système
python test_photofit.py --db C:\cx\bases\photofit.db --mode face
python test_photofit.py --db C:\cx\bases\photofit.db --limit 20  # Test rapide
```

---

## 7. Opérations backoffice : Intégrer de nouvelles images

### Étape 1 : Préparer les images

1. **Numéroter les images** avec des idportrait ≥ 1000 (ex: 12000, 12001, ...)
2. **Placer les images** dans un répertoire dédié (ex: `C:\cx\data\nouvelles_photos\`)
3. **Formats acceptés** : .jpg, .jpeg, .png, .bmp, .webp

### Étape 2 : Extraire les embeddings via l'API Photofit

```bash
cd C:\cx

# Test sur quelques images d'abord
python build_photofit_db.py C:\cx\data\nouvelles_photos --limit 10 -v

# Si OK, lancer sur tout le lot
python build_photofit_db.py C:\cx\data\nouvelles_photos -o C:\cx\bases\photofit.db --resume -v
```

**Temps estimé** : ~1-2 secondes par image

### Étape 3 : Vérifier les erreurs

```bash
python -c "import sqlite3; conn=sqlite3.connect('C:/cx/bases/photofit.db'); c=conn.cursor(); c.execute(\"SELECT idportrait, error_message FROM portraits WHERE status='error'\"); print(c.fetchall())"
```

Si des images sont en erreur (HTTP 500, visage non détecté), vous pouvez :
- Les ignorer (acceptable si peu nombreuses)
- Les corriger manuellement (copier les données d'une image similaire)

### Étape 4 : Mettre à jour `portraits.csv`

Ajouter les nouvelles lignes dans `refs/portraits.csv` :

```csv
idportrait;sexe;portrait
12000;F;https://raw.githubusercontent.com/Jawakaspa/orqual-portraits/main/thumbs/12000.jpg
12001;M;https://raw.githubusercontent.com/Jawakaspa/orqual-portraits/main/thumbs/12001.jpg
...
```

### Étape 5 : Uploader les thumbnails sur GitHub

1. **Redimensionner les images** (si pas déjà fait) :
```bash
python resize_portraits.py C:\cx\data\nouvelles_photos C:\cx\thumbs
```

2. **Pousser sur GitHub** :
```bash
cd C:\chemin\vers\orqual-portraits
copy C:\cx\thumbs\*.jpg thumbs\
git add thumbs\
git commit -m "Ajout de X nouveaux portraits"
git push
```

### Étape 6 : Mettre à jour la base patients

Si les nouvelles images correspondent à de nouveaux patients :

1. Ajouter les patients dans le CSV source (`patsXXXXX.csv`)
2. Régénérer la base patients :
```bash
python chargebase.py
```

### Étape 7 : Tester

```bash
# Vérifier qu'un nouveau portrait est trouvable
python search_similar.py 12000 --db C:\cx\bases\photofit.db -n 10

# Test de non-régression sur les anciens
python test_photofit.py --db C:\cx\bases\photofit.db --limit 20
```

### Étape 8 : Déployer

```bash
cd D:\KitviewSearchV52
git add bases/photofit.db refs/portraits.csv
git commit -m "Ajout de X nouveaux portraits"
git push
```

Render redéploie automatiquement.

---

## 8. Récapitulatif des fichiers

### Fichiers de configuration

| Fichier | Rôle |
|---------|------|
| `refs/communb.csv` | Paramètres Photofit (section `bases`) |
| `refs/portraits.csv` | Mapping idportrait → URL image |

### Bases de données

| Fichier | Rôle |
|---------|------|
| `bases/photofit.db` | Embeddings faciaux (hair + face) |
| `bases/baseXXXXX.db` | Données patients |

### Programmes backoffice

| Fichier | Rôle |
|---------|------|
| `build_photofit_db.py` | Construction base vectorielle |
| `search_similar.py` | Test CLI recherche |
| `test_photofit.py` | Validation Recall/MRR |

---

## 9. Déploiement V5.2

### URLs

| Version | URL | Plan Render |
|---------|-----|-------------|
| V5.1 | https://kitviewsearchv51.onrender.com | Free |
| **V5.2** | **https://kitviewsearchv52.onrender.com** | **Starter** |

### Repo GitHub

- V5.1 : `Jawakaspa/KitviewSearchV51`
- V5.2 : `Jawakaspa/KitviewSearchV52`

---

## 10. Problèmes connus et limitations

1. **Recherche par clic sur résultat** : La fonctionnalité "même portrait que X" en cliquant sur un patient dans les résultats ne fonctionne pas encore correctement.

2. **Seuil de similarité** : Le `score_min=30` peut être trop permissif pour certains cas. À ajuster selon les retours utilisateurs.

3. **Temps de traitement API** : ~1-2s par image. Pour de gros lots (>1000 images), prévoir ~30-60 minutes.

---

## 11. Évolutions futures envisagées

- [ ] Recherche par similarité en cliquant sur un portrait dans les résultats
- [ ] Affichage du score de similarité dans l'interface
- [ ] Filtrage par sexe avant recherche de similarité (optimisation)
- [ ] Mode "face only" configurable dans l'interface
- [ ] Export de la cohorte de portraits similaires

---

**Document généré le 12/02/2026** | KITVIEW Search V5.2 | Photofit
