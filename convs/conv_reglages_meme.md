# Prompt conv_reglages_meme V1.0.5 - 21/01/2026 18:12:57

# Conversation : reglages_meme

## Synthèse des échanges

### Mercredi 21 janvier 2026

---

#### 15:45 - Problème d'encodage script CMD
**Question** : Le script test_meme_cli.cmd affiche des erreurs de caractères UTF-8
**Réponse** : Recréation du script en ASCII pur (sans caractères Unicode spéciaux)
**Fichier** : `test_meme_cli.cmd` (ASCII)

---

#### 16:00 - Diagnostic pipeline "même"
**Question** : Test du pipeline avec "meme portrait et meme nom que Guillaume Moulin"
**Diagnostic** :
- TEST 1 (detmeme.py) : Bug - détecte "meme meme nom" au lieu de "meme nom"
- TEST 2 (trouveid.py) : OK - trouve Guillaume Moulin ID 2
- TEST 3 (jsonsql.py) : OK - génère SQL correct
- TEST 4 (trouve.py) : ÉCHEC - "Patient non trouvé: inconnu" → retourne 1000 patients

**Cause identifiée** : `detall.py` ne propage pas la clé `reference` de detmeme vers le JSON de sortie

---

#### 16:30 - Correction detall.py
**Problème** : La référence patient n'était pas propagée
**Correction** : Ajout dans `detecter_tout()` :
```python
# V5.1.1 : Propager la référence pour les critères "même"
if resultat_meme.get('reference'):
    resultat['reference'] = resultat_meme['reference']
```
**Fichier** : `detall.py` V1.0.9

---

#### 16:45 - Test pipeline corrigé
**Résultats** :
- "meme nom que Guillaume Moulin" → **0 résultats** (normal, pas d'autre Moulin)
- "meme sexe que Guillaume Moulin" → **493 résultats** ✅ (hommes)
- "meme age que Guillaume Moulin" → **298 résultats** ✅ (16-22 ans)

**Validation** : Pipeline fonctionnel !

---

#### 17:00 - Migration commun.csv → communb.csv
**Problème** : Les modules cherchent `commun.csv` mais le fichier a été remplacé par `communb.csv` (format vertical)
**Fichiers modifiés** :
- `detmeme.py` V1.0.5 : Support communb.csv (format vertical)
- `detcount.py` V1.0.1 : Support communb.csv (format vertical)
- `detall.py` V1.0.9 : Recherche communb.csv avant commun.csv

**Format communb.csv** (vertical) :
```csv
section;parametre;valeur;description
synonymes;combien;combien,nombre,total,...;Expressions COUNT
synonymes;meme;identique,similaire,...;Synonymes de même
synonymes;que;pareil,comme,...;Synonymes de que
```

---

## Fichiers livrés

| Fichier | Version | Description |
|---------|---------|-------------|
| detall.py | V1.0.9 | Propagation reference + support communb.csv |
| detmeme.py | V1.0.5 | Support communb.csv (format vertical) |
| detcount.py | V1.0.1 | Support communb.csv (format vertical) |
| trouveid.py | V2.0.0 | Résolution nom→ID pour critères "même" |
| test_meme_cli.cmd | - | Script de test CLI (ASCII) |

---

## Tests à effectuer

```cmd
REM Après déploiement des nouveaux fichiers :
python trouve.py bases\base1000.db "meme sexe que Guillaume Moulin" --verbose
REM Attendu : ~493 résultats

python trouve.py bases\base1000.db "meme age que Guillaume Moulin" --verbose  
REM Attendu : ~298 résultats

python trouve.py bases\base1000.db "combien de patients avec béance" --verbose
REM Attendu : mode COUNT, nombre affiché
```

---

## Prompts pour recréer les fichiers

### Prompt detall.py V1.0.9
```
Créer detall.py V1.0.9 - Orchestrateur de détection pour KITVIEW.

Modifications par rapport à V1.0.8 :
1. Ajouter recherche de communb.csv AVANT commun.csv
2. Dans detecter_tout(), après appel à detecter_meme(), ajouter :
   if resultat_meme.get('reference'):
       resultat['reference'] = resultat_meme['reference']
3. Mettre à jour le docstring avec CHANGEMENTS V5.1.1

PJ nécessaires : detall.py V1.0.8
```

### Prompt detmeme.py V1.0.5
```
Créer detmeme.py V1.0.5 - Détection expressions "même X".

Modifications :
1. Ajouter fonction _charger_synonymes_communb() pour format vertical
2. Modifier charger_patterns_meme() pour chercher communb.csv d'abord
3. Fallback vers commun.csv puis valeurs par défaut

Format communb.csv : section;parametre;valeur;description
- synonymes;meme;mot1,mot2,...
- synonymes;que;mot1,mot2,...

PJ nécessaires : detmeme.py V1.0.4, communb.csv
```

### Prompt detcount.py V1.0.1
```
Créer detcount.py V1.0.1 - Détection LIST/COUNT.

Modifications :
1. Ajouter fonction _charger_patterns_communb() pour format vertical
2. Modifier charger_patterns_count() pour chercher communb.csv d'abord
3. Renommer ancienne fonction en _charger_patterns_commun_ancien()

Format communb.csv : synonymes;combien;mot1,mot2,...

PJ nécessaires : detcount.py V1.0.0, communb.csv
```

### Prompt trouveid.py V2.0.0
```
Créer trouveid.py V2.0.0 - Résolution patient de référence.

Fonction principale : enrichir_avec_reference(json_detection, db_path, verbose, debug)

Logique :
1. Extraire reference du JSON (type 'nom' ou 'id')
2. Rechercher patient dans base SQLite
3. Enrichir chaque critère type='meme' avec reference_id et reference_patient

PJ nécessaires : Structure base patients (id, prenom, nom, sexe, age, canontags, canonadjs, idportrait, oripathologies)
```
