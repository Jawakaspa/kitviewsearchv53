# Prompt_classe2_disambiguation.md

## Objet

Correction du prompt IA de `detia.py` pour résoudre une erreur d'interprétation de "classe 2" en recherche orthodontique.

---

## Problème constaté

### Symptôme

| Requête | detall (standard) | detia (IA) |
|---------|-------------------|------------|
| "patients en classe 2 agés de plus de 20 ans et de moins de 23 ans" | `[tag] classe ii d'angle` → **0 patient** | `[tag] classe ii squelettique` → **2 patients** |

L'IA détecte "classe ii squelettique" au lieu de "classe ii d'angle". Les 2 patients trouvés (Olivier Diaz, Aimé Robin) ont effectivement "Classe li Squelettique" dans leurs pathologies, mais la requête demandait "classe 2" tout court.

### Cause racine

Le prompt de detia.py contient une section ANGLES CÉPHALOMÉTRIQUES :

```
| Angle | Condition | Seuil | Tag résultant        |
|-------|-----------|-------|----------------------|
| ANB   | BETWEEN   | 0-4   | classe i squelettique  |
| ANB   | >         | 4     | classe ii squelettique |
| ANB   | <         | 0     | classe iii squelettique |
```

L'IA confond deux concepts distincts :
- **"classe 2"** = classification d'Angle (dentaire, rapport molaire)
- **"classe 2 squelettique"** = classification de Ballard (squelettique, rapport osseux)

L'IA, voyant "classe ii squelettique" dans la section angles, l'utilise comme synonyme de "classe 2" alors que ce sont deux diagnostics **différents**.

---

## Justification médicale

### Deux classifications distinctes

En orthodontie, il existe deux systèmes de classification indépendants :

| | Classification d'Angle | Classification de Ballard |
|---|---|---|
| **Nom** | Classification dentaire | Classification squelettique |
| **Objet** | Rapport des premières molaires entre elles | Rapport des bases osseuses (maxillaire/mandibule) |
| **Classe II** | Molaire mandibulaire en position distale | Mandibule en retrait (ANB > 4°) |
| **Usage courant** | "classe 2" ou "classe II" | "classe II squelettique" |
| **Qualificatif requis** | Non (c'est la classification par défaut) | Oui ("squelettique" obligatoire) |

### Règle d'usage professionnel

- **"classe 2"** seul → toujours **Angle** (dentaire)
- **"classe 2 squelettique"** → toujours **Ballard** (squelettique)
- **ANB > 4°** → toujours **squelettique** (c'est une mesure osseuse)

Sources : Fédération Française d'Orthodontie, Ameli.fr, Réalités Pédiatriques (nov. 2023), ClearCorrect.

---

## Correction appliquée

### Fichier modifié : `detia.py`

**Fonction :** `_construire_prompt_systeme()` (et `_construire_prompt_systeme_brut()` dans detiabrut.py)

### Texte ajouté dans la section RÈGLES du prompt système

Après la ligne `RÈGLES: Retourne UNIQUEMENT du JSON valide.`, ajouter :

```
=== RÈGLE CRITIQUE : CLASSIFICATION "CLASSE" ===
En orthodontie, il existe DEUX classifications différentes pour les "classes" :

1. Classification d'ANGLE (dentaire) → rapport des molaires
   - "classe 2", "classe II", "classe 2 div 1", "classe 2 div 2"
   - Tag à utiliser : "classe ii" ou ses variantes d'Angle (division 1, division 2)
   
2. Classification SQUELETTIQUE de Ballard → rapport des bases osseuses
   - UNIQUEMENT si le mot "squelettique" est EXPLICITEMENT présent
   - Ou si c'est un critère d'ANGLE céphalométrique (ANB > 4)
   - Tag à utiliser : "classe ii squelettique"

RÈGLE : Quand la question dit "classe 2" SANS le mot "squelettique",
tu DOIS utiliser le tag de la classification d'Angle, JAMAIS "classe ii squelettique".
Le mot "squelettique" doit être EXPLICITEMENT écrit dans la question pour utiliser ce tag.
```

### Localisation exacte dans le code

Dans `detia.py`, fonction `_construire_prompt_systeme()`, le prompt se termine par :

```python
RÈGLES: Retourne UNIQUEMENT du JSON valide."""
```

Remplacer par :

```python
=== RÈGLE CRITIQUE : CLASSIFICATION "CLASSE" ===
En orthodontie, "classe 2" seul = classification d'ANGLE (rapport molaire).
"classe 2 squelettique" = classification de Ballard (rapport osseux, ANB).
→ JAMAIS utiliser "classe ii squelettique" sauf si "squelettique" est ÉCRIT dans la question
  ou si c'est un critère d'angle céphalométrique (ANB > 4).

RÈGLES: Retourne UNIQUEMENT du JSON valide."""
```

### Même correction dans `detiabrut.py`

Appliquer la même modification dans `_construire_prompt_systeme_brut()`.

---

## Résultat attendu après correction

| Requête | detia AVANT | detia APRÈS |
|---------|-------------|-------------|
| "patients en classe 2" | `[tag] classe ii squelettique` ✗ | `[tag] classe ii` (d'Angle) ✓ |
| "classe 2 squelettique" | `[tag] classe ii squelettique` ✓ | `[tag] classe ii squelettique` ✓ |
| "patients avec ANB > 5" | `[angle] classe ii squelettique` ✓ | `[angle] classe ii squelettique` ✓ |
| "classe 2 div 1" | dépend du modèle | `[tag] classe ii division 1` ✓ |

---

## Impact

- **detall** : Aucun changement (fait déjà le bon mapping via tags.csv)
- **detia** : Prompt modifié → "classe 2" seul ne produira plus "squelettique"
- **detiabrut** : Même correction dans le prompt brut
- **tags.csv** : Aucun changement nécessaire
- **Patients en base** : Aucun changement. Les patients Olivier Diaz et Aimé Robin resteront avec "Classe li Squelettique" et ne seront logiquement PAS trouvés par "classe 2" (ce qui est correct : ils sont en classe II squelettique, pas forcément en classe II d'Angle)

---

## Comment tester

```bash
# Avant correction : doit donner "classe ii squelettique" (bug)
python detia.py "patients en classe 2"

# Après correction : doit donner "classe ii" (d'Angle)
python detia.py "patients en classe 2"

# Ceux-ci ne doivent PAS changer :
python detia.py "patients en classe 2 squelettique"
python detia.py "patients avec ANB supérieur à 5"
```

---

## PJ nécessaires pour appliquer

- `detia.py` (fichier actuel à modifier)
- `detiabrut.py` (même modification dans le prompt brut)
- Ce document (`Prompt_classe2_disambiguation.md`)

**FIN DU DOCUMENT**
