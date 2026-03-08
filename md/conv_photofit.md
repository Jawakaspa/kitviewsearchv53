# Synthèse de conversation : photofit

**Projet** : Recherche de portraits similaires via API IA  
**Date de début** : 30/01/2026

---

## Échange 1 - 30/01/2026 11:50

### Question de Thierry

Présentation du projet **photofit** : intégration d'une API de recherche de similitude faciale développée par Maxime. L'API est hébergée sur `https://demo.ia.orqual.info:506/photofit` et propose :

- **Endpoints** :
  - `/api/v1/attributes-names` : 15 attributs faciaux (eyeglasses, male, young, longueur/couleur cheveux, etc.)
  - `/api/v1/extra-features` : Analyse d'un portrait → attributes[15] + hair-embedding[384] + face-embedding[128]
  - `/api/v1/hair-embedding-size` : Taille de l'embedding cheveux

- **Stratégie de recherche** : Pré-filtrage par attributs binarisés (seuil 0.5) puis k-NN sur hair-embedding

### Réponse de Claude

Demande de clarifications sur :
1. L'objectif principal et l'intégration avec le projet existant
2. La source des images et le stockage
3. Le workflow batch et recherche
4. Les critères de similarité (V1, V2, V3)
5. L'interface CLI vs web
6. Le stockage vectoriel (suggestion : sqlite-vec)

---

## Échange 2 - 30/01/2026 12:05

### Réponses de Thierry

| Question | Réponse |
|----------|---------|
| **Objectif** | Intégration dans le projet existant (recherche orthodontie 25000 patients) |
| **Architecture** | Ne pas toucher à la table `patients` (garde `idportrait`), remplacer `portraits.csv` par sqlite-vec |
| **Source images** | À définir - Maxime fournira ~1000 portraits |
| **Stockage images** | URL externe (comme actuellement) |
| **Workflow** | Batch initial pour calculer embeddings, puis recherche par idportrait existant |
| **V1** | Attributs binarisés + hair-embedding |
| **V2** | Pondération configurable |
| **V3** | Ajout face-embedding |
| **Interface** | CLI d'abord, web ensuite |
| **Stockage vecteurs** | sqlite-vec validé |

### Architecture validée

```
portraits.db (sqlite-vec)
├── Table portraits
│   ├── idportrait INTEGER PRIMARY KEY
│   ├── sexe TEXT
│   ├── url TEXT
│   ├── attributes BLOB (15 floats)
│   └── hair_embedding vec(384)
```

**Programmes à créer** :
1. `build_portraits_db.py` - Batch initial
2. `search_similar.py` - CLI de recherche

---

## Échange 3 - 30/01/2026 12:20

### Demande de Thierry

Création d'un document `meme.md` actualisé expliquant :
1. Le fonctionnement actuel de `detmeme.py`
2. L'ajout/suppression de critères (via `meme.js` et `main.js`)
3. Le remplacement du placeholder "même portrait" par l'API Photofit de Maxime
4. Format compatible reveal.js

### Réponse de Claude

**Document créé** : `meme.md` (V6) - ~950 lignes

Contenu principal :
- **Section 1-3** : Vue d'ensemble, syntaxes supportées, critères de similarité
- **Section 4** : ⚠️ État actuel du critère "portrait" (PLACEHOLDER - compare uniquement idportrait)
- **Section 5** : API Photofit de Maxime - Description complète des endpoints, attributs, embeddings, et stratégie de recherche en 2 étapes
- **Section 6** : Architecture technique (pipeline detmeme → trouveid → jsonsql → lancesql)
- **Section 7** : Interface utilisateur - États visuels, logique JavaScript (meme.js extrait depuis main.js V2.4.0)
- **Section 7.4** : Ajout/suppression de critères - Toggle automatique, désélection tag/pathologie
- **Section 8** : Fichiers impliqués (6 fichiers principaux)
- **Section 9-10** : Tests et évolutions (roadmap V6.1 → V6.3)
- **Annexes** : Constantes, couleurs CSS, référence API Photofit

---

## Échange 4 - 06/02/2026 12:20

### Précisions de Thierry

- **Version** : Ce sera la V5.2 (pas V6)
- **Jeu de test** : 1600 photos numérotées 1000-2599, générées via `gen_variantes.py`
  - Organisation : groupes de 10 (1000=original, 1001-1009=variantes dégradées)
  - 160 "personnes" × 10 photos chacune
- **Base patients** : `pats1600.db` avec `idportrait` correspondant aux numéros de fichiers
- **Embeddings** : Utiliser les deux (hair + face) dès le départ pour comparer empiriquement
- **API corrigée** : L'endpoint est `/api/v1/extract-features` (pas `/extra-features`)
- **Réponse API** : 18 attributs (pas 15), hair_embedding, face_embedding

### Programmes créés

| Programme | Description |
|-----------|-------------|
| `build_photofit_db.py` | Batch pour appeler l'API et construire la base vectorielle |
| `search_similar.py` | CLI de recherche de portraits similaires |
| `test_photofit.py` | Validation du système (calcul Recall, MRR, etc.) |

### Architecture de la base `photofit.db`

```sql
CREATE TABLE portraits (
    idportrait TEXT PRIMARY KEY,
    filepath TEXT NOT NULL,
    attributes_json TEXT,      -- JSON brut des attributs
    attributes_bin TEXT,       -- Binarisé "1,0,1,0,..." pour filtrage rapide
    hair_embedding BLOB,       -- 384 floats sérialisés
    face_embedding BLOB,       -- 128 floats sérialisés
    status TEXT,               -- 'ok' ou 'error'
    error_message TEXT,
    created_at TEXT,
    updated_at TEXT
);
```

### Stratégie de recherche

1. **Pré-filtrage** (optionnel) : Distance de Hamming sur attributs binarisés
2. **Classement** : Distance cosinus sur embeddings
   - Mode `hair` : uniquement hair_embedding (384 dims)
   - Mode `face` : uniquement face_embedding (128 dims)
   - Mode `both` : combinaison pondérée (70% hair, 30% face par défaut)

---

## Fichiers produits

| Fichier | Description |
|---------|-------------|
| `meme.md` | Documentation technique V6 du système "Même X" avec section Photofit |
| `conv_photofit.md` | Ce fichier de synthèse |
| `build_photofit_db.py` | Programme batch pour construire la base vectorielle |
| `search_similar.py` | Programme CLI de recherche de portraits similaires |
| `test_photofit.py` | Programme de validation/tests du système |

---

## Prochaines étapes

1. **Tester `build_photofit_db.py`** sur les 1600 images
   ```bash
   python build_photofit_db.py C:\2702s\bases\photofit -v --limit 10
   ```

2. **Valider avec `test_photofit.py`** 
   ```bash
   python test_photofit.py --db photofit.db --mode both
   ```

3. **Comparer les modes** hair vs face vs both

4. **Intégrer dans le système de recherche** (modification de `jsonsql.py`)

---

## Prompts pour recréer les programmes

### build_photofit_db.py

```bash
python build_photofit_db.py                     # Affiche l'aide
python build_photofit_db.py <répertoire>        # Traite toutes les images
python build_photofit_db.py <répertoire> -v     # Mode verbose
python build_photofit_db.py <répertoire> --resume  # Reprend où on s'est arrêté
```

### search_similar.py

```bash
python search_similar.py                        # Affiche l'aide
python search_similar.py 1000                   # Recherche similaires à 1000
python search_similar.py 1000 -n 20 --hair      # Top 20, mode hair uniquement
```

### test_photofit.py

```bash
python test_photofit.py                         # Affiche l'aide
python test_photofit.py --db photofit.db        # Lance tous les tests
python test_photofit.py --db photofit.db --mode hair --limit 10  # Test rapide
```

---

*Dernière mise à jour : 30/01/2026 12:20*
