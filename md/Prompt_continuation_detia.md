# Prompt de continuation : KITVIEW - Optimisation detia.py

## Contexte

Ce prompt fait suite à la conversation "detia" du 22/12/2025. L'objectif est de finaliser l'optimisation du module de détection IA.

## Ce qui a été fait

1. **Analyse de detia.py** : Module de détection par IA via Eden AI, latence ~4.7s
2. **Analyse de detangles.py** : Détection des angles céphalométriques (ANB, SNA, SNB)
3. **Document comparatif** : `Prompt_comparatif_detia_detall.md` créé
4. **Correction frtagsadjs.csv** : 27 adjectifs manquants ajoutés → `frtagsadjs_complet.csv`
5. **Pipeline créé** : `pipeline.py` génère les fichiers complets + slim + map
6. **Gain mesuré** : Réduction de 53.6% de la taille des fichiers pour le contexte IA

## Fichiers à joindre en PJ

1. `Prompt_contexte2312.md` - Contexte projet KITVIEW
2. `detia.py` - Module actuel à modifier
3. `pipeline.py` - Pipeline de génération (déjà créé)
4. `frsyntags_slim.csv` - Exemple de fichier slim généré
5. `frsynadjs_slim.csv` - Exemple de fichier slim adjectifs
6. `angles.csv` - Référence des angles céphalométriques
7. `detangles.py` - Module de détection des angles (pour référence)

## Étapes à réaliser

### Étape 1 : Intégrer slim dans detia.py

**Objectif** : Modifier detia.py pour utiliser les fichiers slim et réduire la latence.

**Modifications requises** :
1. Charger `xxsyntags_slim.csv` au lieu de `syntags.csv` dans le prompt
2. Charger `xxsynadjs_slim.csv` au lieu de `synadjs.csv` dans le prompt
3. Charger `xxsyntags_map.csv` et `xxsynadjs_map.csv` pour le post-traitement
4. Modifier `_construire_prompt_systeme()` pour utiliser le format slim
5. Ajouter une fonction `mapper_vers_canonique()` en post-traitement
6. L'IA retourne le stdtag/stdadj, Python fait le lookup vers canontag/canonadj

**Nouveau prompt système (structure)** :
```
Tu es un analyseur de requêtes orthodontiques.

MISSION : Identifier les termes de ces listes qui apparaissent dans la question.
Retourner le terme EXACT tel qu'il apparaît dans la liste.

=== Tags pathologiques reconnus ===
beance
beance anterieure
bruxisme
classe ii squelettique
...

=== Adjectifs reconnus ===
severe
modere
lateral
...

=== Angles céphalométriques ===
[Ajouter la logique des angles - voir étape 2]
```

**Signature inchangée** : `detecter_tout(question, references, model, verbose, debug)`

### Étape 2 : Intégrer les angles dans detia.py

**Objectif** : Permettre à detia.py de détecter les requêtes avec angles (ANB, SNA, SNB).

**Logique à implémenter** :
- "ANB > 5" → vérifier 5 > 4 → tag "classe ii squelettique"
- "SNA < 78" → vérifier 78 < 80 → tag "rétrognathisme maxillaire"
- "SNB > 84" → vérifier 84 > 82 → tag "prognathisme mandibulaire"

**Approche recommandée** :
1. Ajouter une section dans le prompt avec les seuils cliniques
2. Ajouter 2-3 exemples few-shot pour les angles
3. Le post-traitement vérifie la cohérence angle/seuil/tag

**Table de référence à inclure** :
```
Angle | Condition | Seuil | Tag résultant
ANB   | BETWEEN   | 0-4   | classe i squelettique
ANB   | >         | 4     | classe ii squelettique
ANB   | <         | 0     | classe iii squelettique
SNA   | BETWEEN   | 80-84 | position maxillaire normale
SNA   | >         | 84    | prognathisme maxillaire
SNA   | <         | 80    | rétrognathisme maxillaire
SNB   | BETWEEN   | 78-82 | position mandibulaire normale
SNB   | >         | 82    | prognathisme mandibulaire
SNB   | <         | 78    | rétrognathisme mandibulaire
```

### Étape 3 : Compléter pipeline.py (étapes 3 et 4)

**Étape 3 du pipeline - Génération de questions test** :
- Entrée : `xxsyntags.csv` + base patients (baseN.db)
- Sortie : `testsquestionsin.csv`
- Méthode "cheat" : Créer des questions à partir de patients existants pour garantir résultats non-nuls
- Distribution : 30% COUNT, 70% LIST, 10% avec angles
- Complexité : 1-4 critères par question

**Étape 4 du pipeline - Audit de concordance** :
- Entrée : `testsquestionsout.csv` (detall) + `testsquestionsout_ia.csv` (detia)
- Sortie : `audit_concordance.csv`
- Métriques : 
  - Concordance listcount (%)
  - Concordance tags exacte (%)
  - Concordance tags partielle (%)
  - Écart moyen nb_critères
  - Latence moyenne detall vs detia

## Contraintes

- Python 3.13+ uniquement
- UTF-8-SIG pour les CSV
- Séparateur `;` pour colonnes, `,` pour multivaleurs
- Pas de données en dur (sauf exceptions du prompt contexte)
- Affichage verbose avec progression (tqdm si batch)
- Signature des fonctions existantes inchangée

## Résultat attendu

1. `detia_slim.py` - Version optimisée avec slim + angles
2. `pipeline.py` - Complété avec étapes 3 et 4
3. `conv_detia.md` - Synthèse mise à jour
4. Mesure du gain de latence (objectif : -25% soit ~3.5s au lieu de 4.7s)

## Architecture cible detia_slim.py

**Dans le prompt IA** (taille réduite ~50%) :
- `xxsyntags_slim.csv` : Liste des stdtag uniquement
- `xxsynadjs_slim.csv` : Liste des stdadj uniquement  
- `ages.csv` : Complet (logique complexe)
- `angles.csv` : Complet (logique complexe)

**En post-traitement Python** :
- `xxsyntags_map.csv` : Lookup stdtag → canontag
- `xxsynadjs_map.csv` : Lookup stdadj → canonadj + canontag

L'IA retourne les termes slim détectés, Python fait le mapping vers les formes canoniques.

## Exercice futur : "Déshabillage du roi"

Une fois detia_slim.py finalisé, prévoir un mode benchmark pour mesurer la contribution de chaque élément :

| Niveau | Configuration | À mesurer |
|--------|---------------|-----------|
| 0 | Version slim complète | Baseline (référence) |
| 1 | Sans slim (complets) | Impact taille contexte |
| 2 | Sans synonymes | Capacité native LLM |
| 3 | Sans ages.csv | Détection âge intuitive |
| 4 | Sans angles.csv | Détection angles intuitive |
| 5 | Juste tagsadjs brut | LLM seul, données minimales |

Cet exercice permettra de quantifier la valeur ajoutée de chaque couche d'optimisation.

## Question initiale suggérée

"Continue le travail sur KITVIEW. Voici les fichiers de la conversation précédente. Réalise les 3 étapes dans l'ordre : 1) Intégrer slim dans detia.py, 2) Ajouter les angles, 3) Compléter le pipeline. Commence par l'étape 1."

---
*Prompt généré le 22/12/2025 - Conversation: detia*
