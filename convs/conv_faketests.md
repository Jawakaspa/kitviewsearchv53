# Prompt conv_faketests V1.0.1 - 02/01/2026 19:30:34

# conv_faketests.md

## Synthèse de la conversation : faketests

---

## Échanges

### 31/12/2025 18:45 - Création de creefakelog.py

**Demande utilisateur :**
Développer `creefakelog.py`, un générateur de fichier de logs de recherches fictives au format de `logrecherche.csv`.

**Spécifications initiales :**
- Usage : `python creefakelog.py N y.db z.csv`
- N ≥ 3 × LR (nombre de lignes de logrecherche.csv)
- 3 phases de génération :
  1. Copie des lignes originales
  2. Duplication avec timestamps 1-17 déc + ratings
  3. Nouvelles lignes 18 déc - 5 jan avec questions aléatoires

**Questions de clarification posées par Claude :**
1. Base de données : `y.db` vs `base25000.db` ?
2. Colonne "question" vs colonnes langues dans fr100.csv ?
3. Répartition des langues phase 3 (20% ja, 25% en, 55% fr) ?
4. Valeurs exactes de `type_probleme` ?
5. Règles de rating phase 3 ?
6. Gestion des colonnes vides dans fr100.csv ?
7. Appel réel à search.py ou simulation ?

**Réponses utilisateur :**
1. Base : `base25000.db` (hardcodé, paramètre `y.db` supprimé)
2. Colonne `fr` = colonne question par défaut
3. Répartition confirmée : 20% ja, 25% en, 55% fr
4. 4 types confirmés : Bug IHM, Trop de patients, Pas assez de patients, Autre
5. Phase 3 : 1/2 avec rating, puis 1/3 positif et 2/3 négatif
6. Ignorer les lignes où la colonne tirée au sort est vide
7. **SIMULER les résultats** - pas d'appel réel à search.py

**Usage final simplifié :**
```
python creefakelog.py N z.csv
```

**Livrables produits :**
- `creefakelog.py` : Générateur de logs fictifs
- `Prompt_creefakelog.md` : Prompt de recréation complet

---

### 02/01/2026 10:15 - Limitation des questions identiques

**Demande utilisateur :**
Modifier `creefakelog.py` pour limiter le nombre de questions strictement identiques à 2 maximum. Si une 3ème question identique est tirée, ajouter un mot tiré au hasard de `motsvides.csv` avant le `?` final ou à la fin s'il n'y a pas de `?`.

**Modifications apportées :**
1. Ajout du fichier `refs/motsvides.csv` comme source de mots vides
2. Création de la fonction `charger_motsvides()` pour charger les mots
3. Création de la fonction `diversifier_question()` pour ajouter un mot vide
4. Modification de `generer_lignes_phase3()` :
   - Ajout d'un compteur `occurrences_questions`
   - Vérification si question déjà utilisée ≥ 2 fois
   - Diversification automatique avec mot vide
   - Affichage du nombre de questions diversifiées

**Exemple de diversification :**
- Original : `"Combien de patients avec claquement articulaire avec béance de plus de 8.561 ans ?"`
- Diversifié : `"Combien de patients avec claquement articulaire avec béance de plus de 8.561 ans ferions ?"`

**Test réussi :**
- 300 lignes générées
- 17 questions diversifiées (> 2 occurrences)
- Toutes les questions phase 3 limitées à 2 occurrences max

---

## Fichiers créés/modifiés

| Fichier | Description | Version |
|---------|-------------|---------|
| `creefakelog.py` | Générateur de fichier de logs de recherches fictives | V1.1.0 |
| `Prompt_creefakelog.md` | Prompt permettant de recréer creefakelog.py | V1.1.0 |
| `conv_faketests.md` | Ce document de synthèse | V1.1.0 |

---

## Points techniques clés

### Structure du log généré

```
Phase 1 (originales)     : LR lignes
Phase 2 (1-17 déc)       : LR lignes avec rating obligatoire
Phase 3 (18 déc - 5 jan) : N - 2×LR lignes avec questions aléatoires (max 2 identiques)
Total                    : N lignes triées par timestamp
```

### Répartition des ratings

| Phase | Avec rating | 👍 (positif) | 👎 (négatif) |
|-------|-------------|--------------|--------------|
| Phase 2 | 100% | 33% | 67% (4 types équirépartis) |
| Phase 3 | 50% | 33% | 67% (4 types équirépartis) |

### Répartition des langues (Phase 3)

| Langue | Probabilité |
|--------|-------------|
| Japonais (ja) | 20% |
| Anglais (en) | 25% |
| Français (fr) | 55% |

### Simulation des résultats

- `temps_ms` : 10-150ms (rapide), 1500-5000ms (IA)
- `nb_patients` : Distribution exponentielle, max 25000
- `mode` : Aléatoire parmi [rapide, ia, compare, union]
- `base` : Toujours "base25000.db"

### Limitation des doublons (nouveau)

- Maximum 2 questions strictement identiques en phase 3
- Au-delà, ajout d'un mot de `motsvides.csv` :
  - Avant le `?` si présent
  - À la fin sinon
- Compteur basé sur la question originale (avant diversification)

---

## Fichiers nécessaires pour recréation

Pour recréer `creefakelog.py` à partir de zéro :

1. `Prompt_contexte.md` (contexte général)
2. `Prompt_creefakelog.md` (ce prompt)
3. `logrecherche.csv` (exemple de format)
4. `fr100.csv` (exemple de fichier de questions)
5. `motsvides.csv` (mots vides pour diversification)

---

## Prochaines étapes potentielles

- [ ] Test du générateur avec différentes valeurs de N
- [ ] Validation du format de sortie
- [ ] Intégration avec les outils d'analyse de logs

---

**Dernière mise à jour : 02/01/2026 10:15**
