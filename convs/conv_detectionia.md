# Prompt conv_detectionia V1.0.4 - 13/12/2025 21:44:39

# conv_detectionia.md

## Synthèse de la conversation : detectionia
### Projet Kitview - Comparaison détection traditionnelle vs IA

---

## Échange 1 - 13/12/2025 19:52

### Question
Analyse comparative des résultats de détection entre `detall.py` (pipeline traditionnel) et `detia.py` (IA via Eden AI avec Claude Sonnet). Objectif : évaluer objectivement la qualité des deux approches pour identifier les corrections nécessaires.

### Contexte fourni
- `questionspats100_out.csv` : 101 questions traitées par detall.py
- `questionspats100_out_ia.csv` : 101 questions traitées par detia.py (Claude Sonnet via Eden AI)
- Latence moyenne IA : 4705ms/question
- Latence totale IA : 475235ms (~8 minutes)

### Analyse réalisée

#### Programme créé : `compdetect.py`
Programme de comparaison ligne par ligne avec métriques :
- Concordance exacte par champ
- Score Jaccard pour les tags
- Distribution des différences
- Identification des divergences

#### Résultats de la comparaison

| Métrique | Valeur | Commentaire |
|----------|--------|-------------|
| Concordance listcount | 99.0% | Quasi parfait |
| Concordance nb_criteres (exact) | 20.8% | Très faible |
| Concordance tags (exact) | 31.7% | Faible |
| Score Jaccard tags moyen | 46.8% | Moyen |
| detall trouve plus | 26 questions | |
| detia trouve plus | 54 questions | Tendance à sur-détecter |
| Égalité | 21 questions | |

#### Problèmes identifiés dans detia.py

1. **Échecs de parsing JSON (21 questions)** :
   - Latence courte (~600-900ms) = erreur IA
   - Questions avec adjectifs contradictoires : "grave bénin", "modéré majeur"
   - L'IA refuse de traiter les combinaisons illogiques

2. **motsvides non intégré** :
   - Résidu contient "?", "et", etc.
   - detall nettoie correctement via motsvides.py

3. **Format adjectifs différent** :
   - detall : `severe, moderee` (formes canoniques sans accents)
   - detia : `%sévère%, %modéré%` (format SQL LIKE avec accents)

4. **Sur-détection des angles ANB** :
   - detia interprète `Anb<0°` → `classe iii squelettique`
   - Correct en orthodontie mais détecte 2 critères au lieu de 1

5. **Tags manqués** :
   - "écart" → béance (detall détecte, detia échoue)
   - "h" → Masculin (detall détecte via ages.csv)

#### Tags les plus manqués par detia (top 5)
1. classe ii squelettique : 3 fois
2. béance : 3 fois
3. prognathisme maxillaire : 3 fois
4. avulsion : 2 fois
5. bruxisme : 2 fois

#### Tags sur-détectés par detia (top 5)
1. classe ii squelettique : 14 fois (angles ANB > 4°)
2. classe i squelettique : 10 fois (angles ANB = 2-4°)
3. bruxisme : 9 fois
4. béance : 8 fois
5. rétrognathie maxillaire : 8 fois

### Corrections proposées

#### Pour detia.py V1.0.4
1. **Intégrer motsvides** dans le post-traitement du résidu
2. **Normaliser le format adjectifs** : retirer les `%` et accents
3. **Améliorer le prompt IA** pour :
   - Ne pas refuser les combinaisons contradictoires (les filtrer en amont)
   - Ne pas déduire de tag si non explicitement mentionné
4. **Gérer les angles ANB séparément** (type "angle" et non "tag")

### Fichiers générés
- `compdetect.py` : Programme de comparaison
- `comparaison_detall_detia.csv` : Résultats détaillés ligne par ligne

### Prochaines étapes
1. Corriger detia.py avec motsvides intégré
2. Re-tester sur questionspats100.csv
3. Comparer avec d'autres modèles (GPT-4o, Gemini)
4. Affiner le prompt IA pour aligner les résultats

---

## Fichiers PJ nécessaires pour recréer les programmes

### Pour recréer compdetect.py
- `Prompt_contexte0412.md` (contexte projet)
- Aucun fichier de données supplémentaire (autonome)

### Pour recréer/modifier detia.py
- `Prompt_contexte0412.md` (contexte projet)
- `syntags.csv` (synonymes tags)
- `synadjs.csv` (synonymes adjectifs)
- `ages.csv` (patterns âge/sexe)
- `angles.csv` (patterns ANB/SNA/SNB)
- `motsvides.csv` (mots vides multilingues)
- `commun.csv` (configuration)

---

## Échange 2 - 13/12/2025 20:38

### Questions posées par Claude

1. **Angles ANB** : Comment traiter `Anb<0°` ?
2. **Combinaisons contradictoires** ("grave bénin") : Les accepter ou signaler une erreur ?
3. **Format adjectifs** : Aligner sur detall (sans accents) ou detia (avec accents) ?

### Réponses de Thierry

1. **Alignement strict** : "Pas une feuille de cigarette de différence entre detia et detall au niveau des formats"
   - Différences de latence et de critères détectés = OK (normal)
   - Formats de sortie = strictement identiques

2. **Combinaisons contradictoires** : Signaler comme erreur utilisateur
   - Nouvelle colonne **MSFSMPFP** dans `tagssaisis.csv` pour gérer genre/nombre
   - MS = Masculin Singulier, FS = Féminin Singulier
   - Permet de valider les accords grammaticaux

3. **Format adjectifs avec accents** : 
   - "Les accents sont plus faciles à enlever qu'à ajouter"
   - **Aligner detall sur detia** (garder les accents)

### Analyse du fichier tagssaisis.csv

Structure de la colonne MSFSMPFP :
- **MS** : Masculin Singulier (ex: "Bruxisme", "activateur", "surplomb")
- **FS** : Féminin Singulier (ex: "Classe I squelettique", "béance", "avulsion")
- (MP/FP pour pluriel si nécessaire ultérieurement)

**Erreurs détectées dans les formes féminines** (génération automatique incorrecte) :
- `majeur|majeuse` → devrait être `majeur|majeure`
- `antérieur|antérieuse` → devrait être `antérieur|antérieure`  
- `postérieur|postérieuse` → devrait être `postérieur|postérieure`

### Recommandation sur MSFSMPFP

**Approche hybride recommandée** :
1. **MSFSMPFP** indique la forme canonique pour l'affichage et le SQL
2. **adjectifsfr** contient toutes les formes pour la détection (déjà le cas)
3. **Corriger les erreurs** de génération automatique (-eur → -eure, pas -euse)

### Modifications à faire

#### 1. detall.py - Extraire les adjectifs avec accents
```python
# Ligne 519 actuelle
adjectifs.append(adj.get('valeur', ''))

# Ligne 519 corrigée
adjectifs.append(adj.get('canonique', adj.get('valeur', '')))
```

#### 2. detia.py - Retirer les % et normaliser
- Post-traiter les adjectifs pour retirer le format SQL LIKE `%xxx%`
- Intégrer motsvides dans le nettoyage du résidu
- S'assurer que les tags sont en casse correcte (comme detall)

#### 3. Corriger tagssaisis.csv
- Remplacer `majeuse` par `majeure`
- Remplacer `antérieuse` par `antérieure`
- Remplacer `postérieuse` par `postérieure`

### Modifications effectuées

#### 1. detall.py V1.0.2
- Ligne 519 : Extraction des adjectifs avec `canonique` (accents) au lieu de `valeur` (sans accents)
- Ligne 645 : Affichage unitaire aligné

#### 2. detia.py V1.0.4
- Import de motsvides avec fallback si indisponible
- Post-traitement des adjectifs : retrait des `%` du format SQL LIKE
- Application de motsvides sur le résidu
- Priorité à `canonique` sur `valeur` pour les adjectifs

#### 3. tagssaisis.csv V1.0.7
Corrections des erreurs de génération automatique des formes féminines :
- `majeuse` → `majeure` (6 occurrences)
- `antérieuse` → `antérieure` (2 occurrences)
- `postérieuse` → `postérieure` (2 occurrences)

### Fichiers générés
- `detall.py` V1.0.2 (modifié)
- `detia.py` V1.0.4 (modifié)
- `tagssaisis.csv` V1.0.7 (corrigé)
- `compdetect.py` V1.0.0 (nouveau)
- `comparaison_detall_detia.csv` (résultats)

### Fichiers fournis
- `tagssaisis.csv` (avec nouvelle colonne MSFSMPFP)

### Prochaines étapes
1. Régénérer syntags.csv et synadjs.csv à partir de tagssaisis.csv corrigé
2. Re-tester les deux pipelines sur questionspats100.csv
3. Comparer à nouveau avec compdetect.py
4. Tester d'autres modèles IA (GPT-4o, Gemini)

---

## Échange 3 - 13/12/2025 21:15

### Résultats des tests V2

| Métrique | Avant (V1) | Après (V2) | Évolution |
|----------|------------|------------|-----------|
| Concordance listcount | 99.0% | 99.0% | = |
| Concordance nb_criteres | 20.8% | 23.8% | +3% |
| Concordance tags exacte | 31.7% | 30.7% | -1% |
| Jaccard tags moyen | 46.8% | 47.0% | +0.2% |
| detall trouve plus | 26 | 18 | -8 |
| detia trouve plus | 54 | 59 | +5 |
| Latence moyenne | 4705ms | 5090ms | +385ms |

### Observations

**Améliorations :**
- Format adjectifs detia : Maintenant avec accents (`sévère`, `modéré`)
- Certains résidus nettoyés par motsvides

**Problèmes persistants :**
1. **detall garde les adjectifs sans accents** : `severe`, `moderee` 
   - Cause : dettags.py stocke `valeur` (forme SQL) et non `canonique`
2. **"?" reste dans le résidu detia** : motsvides ne le supprime pas
3. **Casse des tags différente** : `Classe III` vs `classe iii`

### Questions de Thierry

#### Q1 : Fichiers CSV nécessaires pour l'IA ?

**Fichiers actuellement envoyés :**
- syntags.csv (501 lignes) - Synonymes → tag canonique
- synadjs.csv (501 lignes) - Synonymes adjectifs  
- ages.csv (45 lignes) - Patterns âge/sexe
- angles.csv (36 lignes) - Patterns ANB
- commun.csv (14 lignes) - Configuration

**Peut-elle s'en passer ?**
- Oui théoriquement, mais risque de divergences avec la nomenclature Kitview
- **Minimum viable** : Liste des tags canoniques uniquement (pas tous les synonymes)

**Recommandation** : Créer un prompt allégé avec :
1. Liste des `canonfr` uniquement (pas les synonymes)
2. Liste des adjectifs canoniques par tag
3. Règles âge/sexe dans le texte du prompt

#### Q2 : Mariages impossibles d'adjectifs

**Proposition acceptée** : Ajouter dans commun.csv
```csv
incompatible;sévère,modéré,léger,bénin
incompatible;majeur,mineur
incompatible;antérieur,postérieur
incompatible;gauche,droit
```

#### Q3 : Forme canonique féminine

**Stratégie validée** :
1. Modifier le programme de génération pour utiliser MSFSMPFP
2. Si FS → féminiser l'adjectif canonique
3. Correction manuelle des irréguliers

### Corrections à faire

#### Priorité 1 : Aligner les adjectifs detall/detia

Le problème racine est dans **dettags.py** qui retourne :
```python
'adjectifs': [{'colonne': 'canonadjs', 'operateur': '=', 'valeur': 'severe'}]
```

Au lieu de :
```python
'adjectifs': [{'colonne': 'canonadjs', 'operateur': '=', 'valeur': 'severe', 'canonique': 'sévère'}]
```

**Action** : Modifier dettags.py pour ajouter `canonique` dans chaque adjectif

#### Priorité 2 : Nettoyer le "?" du résidu

Ajouter "?" dans motsvides.csv ou le supprimer dans detia.py

#### Priorité 3 : Normaliser la casse des tags

Choisir une convention : soit tout en minuscules, soit garder la casse d'origine

### Fichiers joints
- questionspats100_out.csv (detall V1.0.2)
- questionspats100_out_ia.csv (detia V1.0.4)

---

*Document mis à jour : 13/12/2025 21:15*
