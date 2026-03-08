# Prompt conv_angles.py V1.0.4 - 12/12/2025 17:04:38

# Synthèse conversation : angles.py

## Informations générales

| Élément | Valeur |
|---------|--------|
| Nom conversation | angles.py |
| Date début | 11/12/2025 |
| Projet | Kitview - Recherche multilingue orthodontique |

---

## Échanges

### 11/12/2025 14:30 - Demande initiale

**Question** : Création de `detangles.py` et du fichier CSV associé selon le prompt `Prompt_detangles.md`

**Clarifications demandées par Claude** :
1. Nom du fichier CSV : `angles.csv` ou `detangles.csv` ?
2. Évaluation des conditions : Option A (clinique) ou B (match direct) ?
3. Patterns textuels sans `{n}` : inclus ou dans tags.csv ?
4. Nom de la colonne SQL : `pathologie` ou autre ?

---

### 11/12/2025 14:45 - Réponses de Thierry

1. **Fichier CSV** : `angles.csv` (cohérent avec `ages.csv`)
2. **Évaluation** : Option A - vérification clinique (ANB > 5 → vérifie 5 > 4 → Classe II)
3. **Patterns textuels** : Restent dans `tags.csv` (pas dans angles.csv)
4. **Colonnes SQL** : `canontags` pour les tags, `canonadjs` pour les adjectifs

---

### 11/12/2025 15:02 - Livraison V1.0.0

**Fichiers créés** : `detangles.py` V1.0.0, `angles.csv` V1.0.0

---

### 11/12/2025 21:15 - Bug report #1

**Problème** : `anb = 5` ne matche pas (devrait donner Classe II car 5 > 4)

**Cause** : Le pattern `anb = {n}` avait `BETWEEN 0,4` comme condition, donc 5 échouait.

**Solution** : Ajout de la fonction `determiner_classe_angle()` qui détermine cliniquement la classe pour les patterns d'égalité (`=`, `de {n}`).

---

### 11/12/2025 21:25 - Bug report #2

**Problème** : `anb = -2` devient `anb = 2` (signe négatif perdu)

**Cause** : `standardise()` supprime le `-` dans la liste `".!-_?"`

**Décision de Thierry** : Modifier `standardise.py` pour **ne plus supprimer le tiret `-`**. C'est plus simple de gérer les cas où il gêne que de le réinventer.

**Action** : Création de `Prompt_standardise_tiret.md` pour documenter la modification.

---

### 11/12/2025 21:30 - Livraison V1.0.1

**Fichiers mis à jour** :
- `detangles.py` V1.0.1 : Simplifié (retire le workaround NEGATIF), fallback standardise ne supprime plus le `-`
- `Prompt_standardise_tiret.md` : Instructions pour modifier `standardise.py`

---

### 11/12/2025 21:50 - Correction fallback

**Problème soulevé par Thierry** : Le fallback local pour `standardise()` est une mauvaise pratique. Le contexte dit clairement "on n'invente rien".

**Action** : Suppression du bloc `try/except ImportError` avec fallback. Import simple :
```python
from standardise import standardise
```

Si `standardise.py` n'est pas présent, le programme plante avec un message clair (comportement attendu).

**Règle à retenir** : Jamais de fallback qui invente une fonction manquante. Si un module requis est absent, erreur explicite.

---

## Spécifications techniques

### detangles.py V1.0.2

**Position dans la chaîne de détection** :
```
detall.py
  ├── detcount.py      → LIST/COUNT
  ├── detangles.py     → Angles céphalo → tags qualifiés ◄ CE MODULE
  ├── detquals.py      → Tags + adjectifs
  └── detage.py        → Âge/sexe
```

**Fonctions principales** :
- `charger_patterns_angles(fichier_csv, verbose, debug)` → Liste de patterns
- `detecter_angles(question, patterns_angles, verbose, debug)` → Dict JSON
- `identifier_angles(residu, patterns_angles, filtres, verbose, debug)` → (filtres, residu)
- `determiner_classe_angle(angle_type, valeur)` → Dict classification clinique
- `traiter_fichier_batch(fichier_entree, patterns_angles, verbose, debug)` → (nb_lignes, fichier_sortie)

**Format de sortie JSON** :
```json
{
  "criteres": [
    {
      "type": "tag",
      "detecte": "anb = 5",
      "canonique": "classe ii squelettique",
      "label": "Classe II squelettique",
      "sql": {"colonne": "canontags", "operateur": "=", "valeur": "classe ii squelettique"},
      "adjectifs_possibles": ["division 1", "division 2", "sévère"],
      "position": {"debut": 6, "fin": 13}
    }
  ],
  "residu": "angle",
  "question_standardisee": "angle anb = 5"
}
```

**CLI** :
```bash
# Mode unitaire
python detangles.py "patients avec ANB > 4°" [--verbose] [--debug]

# Mode batch
python detangles.py tests/testsanglesin.csv [--verbose] [--debug]
```

### angles.csv V1.0.0

**Format** : `expression;operateur;seuil;tag_canonique;adjectifs_possibles;label`

**Angles couverts** :
- **ANB** : Classe I (0-4°), Classe II (>4°), Classe III (<0°)
- **SNA** : Normal (80-84°), Prognathisme (>84°), Rétrognathisme (<80°)
- **SNB** : Normal (78-82°), Prognathisme (>82°), Rétrognathisme (<78°)

---

## Tests effectués

| Question | Résultat | Tag détecté |
|----------|----------|-------------|
| `"patients avec ANB > 5 degrés"` | ✅ | classe ii squelettique |
| `"SNA inferieur a 78 et SNB > 83"` | ✅ | rétrognathisme maxillaire + prognathisme mandibulaire |
| `"ANB entre 2 et 4"` | ✅ | classe i squelettique (ANB 2° à 4°) |
| `"ANB = 3"` | ✅ | classe i squelettique |
| `"ANB = 5"` | ✅ (V1.0.1) | classe ii squelettique |
| `"ANB = -2"` | ✅ (après modif standardise) | classe iii squelettique |
| `"ANB négatif"` | ❌ (attendu) | Pattern textuel → tags.csv |

---

## Prompt de recréation

### Pour recréer detangles.py

**Fichiers à joindre** :
1. `Prompt_contexte0412.md` — Contexte général du projet
2. `Prompt_detangles.md` — Spécifications détaillées
3. `detage.py` — Modèle de structure
4. `ages.csv` — Modèle de format CSV

**Instructions** :
> Crée `detangles.py` et `angles.csv` selon le prompt `Prompt_detangles.md`.
> 
> Précisions :
> - Fichier CSV : `angles.csv` (dans refs/)
> - Évaluation : Option A (clinique) - vérifier la valeur capturée vs seuil orthodontique
> - Pour les patterns d'égalité (`anb = {n}`, `anb de {n}`), utiliser une fonction `determiner_classe_angle()` qui détermine cliniquement la classe selon la valeur
> - Patterns textuels purs (sans {n}) : ne PAS inclure, ils restent dans tags.csv
> - Colonnes SQL : `canontags` pour les tags, `canonadjs` pour les adjectifs

### Pour modifier standardise.py

**Fichier à joindre** :
1. `Prompt_standardise_tiret.md`

---

## Points d'attention / Décisions

1. **Patterns textuels** (`classe 2 squelettique`, `anb negatif`) : restent dans `tags.csv` pour centraliser tous les synonymes de classes
2. **Logique clinique** : La valeur saisie par l'utilisateur est comparée au seuil orthodontique (pas de match direct)
3. **Patterns d'égalité** : Utilisent `determiner_classe_angle()` pour déterminer automatiquement la classe
4. **Tiret dans standardise** : **Ne plus supprimer** le `-` (décision du 11/12/2025) - utile pour nombres négatifs et mots composés

---

**FIN DE SYNTHÈSE**
