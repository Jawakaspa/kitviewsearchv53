# Prompt conv_questionsavecréponses V1.0.0 - 09/12/2025 21:27:57

# conv_questionsavecréponses.md

## Synthèse de la conversation

**Projet** : Kitview - Système de recherche multilingue orthodontique  
**Conversation** : questionsavecréponses  
**Date de début** : 09/12/2025 17:42 UTC

---

## Objectif de la conversation

Créer un générateur de questions de test (`questions.py`) qui :
1. Génère 100 questions de recherche (25 par niveau de 1 à 4 critères)
2. Modifie un fichier patients pour que chaque question matche 2-10% de la base
3. Produit un fichier de questions avec critères canoniques et synonymes

---

## Échange 1 - 09/12/2025 17:42 UTC

### Demande initiale
Créer un prompt et un programme pour :
- Modifier un fichier patients (structure `pats100.csv`)
- Utiliser `tagssaisis.csv` pour les pathologies/adjectifs
- Utiliser `ages.csv` pour les patterns âge/sexe
- Générer des questions avec 1 à 4 critères
- Assurer 2-10% de match par question

### Clarifications demandées
1. Incompatibilités d'adjectifs
2. Patterns âge avec `{n}`
3. Structure du fichier qfichier.csv
4. Contrainte 2-10% de match
5. Nom du fichier patients modifié

---

## Échange 2 - 09/12/2025 (réponses aux clarifications)

### Réponses de Thierry
1. **Incompatibilités** : Paires exclusives définies :
   - gauche/droite
   - antérieure/postérieure
   - maxillaire/mandibulaire
   - maxillaire/mandibule

2. **Patterns {n}** : Valeur aléatoire 5-30 ans + patterns fixes (adulte, adolescent...)

3. **Structure qfichier.csv** : Ajouter une colonne `question` avec le texte généré

4. **Contrainte 2-10%** : Forcer des patients à correspondre si nécessaire

5. **Fichier sortie** : `mpats100.csv` (m pour modifié)

---

## Livrables produits

### 1. Prompt_questions.md
Documentation complète pour recréer `questions.py` :
- Objectif et fichiers requis
- Structure des fichiers d'entrée/sortie
- Règles de génération des questions
- Algorithme principal
- Contraintes techniques

### 2. questions.py (V0.0.0)
Programme Python complet avec :
- Chargement des données (tags, patterns âge, patients)
- Génération de 100 questions (25 × 4 niveaux)
- Équiprobabilité sur le nombre d'adjectifs
- Gestion des incompatibilités d'adjectifs
- Ajustement des données patients
- Calcul des résultats (nb, ids, extrait)
- Sauvegarde en UTF-8-BOM

### 3. Fichiers générés (test)
- `qpats100.csv` : 100 questions avec critères et résultats
- `mpats100.csv` : Patients modifiés pour satisfaire les questions

---

## Résultats du test

```
Statistiques:
  1 critère(s): moyenne 34.3 patients/question
  2 critère(s): moyenne 7.6 patients/question
  3 critère(s): moyenne 2.6 patients/question
  4 critère(s): moyenne 2.0 patients/question
```

---

## Structure des fichiers

### qfichier.csv (sortie questions)
```
crit1_canon;crit2_canon;crit3_canon;crit4_canon;crit1_syn;crit2_syn;crit3_syn;crit4_syn;question;nb;ids;extrait
```

### mfichier.csv (sortie patients modifiés)
```
id;canontags;canonadjs;sexe;age;datenaissance;prenom;nom;portrait
```

---

## Commande d'utilisation

```bash
python questions.py <fichier_patients.csv>
```

**Prérequis** : `tagssaisis.csv` et `ages.csv` dans le même répertoire.

**Exemple** :
```bash
python questions.py pats100.csv
# Génère: qpats100.csv et mpats100.csv
```

---

## Points techniques importants

1. **Ne pas modifier sexe/âge** : Évite les incohérences avec prénom/date de naissance
2. **Sélection intelligente des candidats** : Pour l'ajustement, priorité aux patients matchant déjà les critères âge/sexe
3. **Validation des patterns âge** : Exclusion des patterns qui matchent < 5% de la base
4. **Équiprobabilité** : 1/(n+1) pour 0 à n adjectifs par tag

---

## Fichiers à fournir pour recréer questions.py

| Fichier | Description |
|---------|-------------|
| `Prompt_questions.md` | Prompt complet |
| `pats100.csv` | Structure de référence patients |
| `tagssaisis.csv` | Pathologies et adjectifs |
| `ages.csv` | Patterns âge/sexe |

---

**Fin de synthèse** - Mise à jour : 09/12/2025 17:55 UTC
