# Prompt_detlang.md

## Objet

Création de `detlang.py`, un programme de détection automatique de la langue d'une question utilisateur dans le contexte d'une application de recherche orthodontique multilingue.

---

## Contexte

L'application Kitview permet de rechercher des patients par pathologie en posant des questions en langage naturel. Les utilisateurs peuvent poser leurs questions dans plusieurs langues : français, anglais, allemand, thaï (et potentiellement espagnol, italien, portugais, polonais, roumain, arabe, chinois).

Avant de détecter les tags de pathologie et leurs adjectifs qualificatifs, il faut d'abord identifier la langue de la question pour :

1. Savoir dans quelle colonne de `tags.csv` chercher les synonymes
2. Pouvoir restituer les messages à l'utilisateur dans sa langue
3. Adapter le prétraitement (standardisation) si nécessaire

---

## Fichiers d'entrée

### refs/tags.csv

Fichier multilingue contenant les tags et adjectifs traduits. Structure :

```
canonfr;type;frtags;stdfrtags;fradjs;stdfradjs;entags;stdentags;enadjs;stdenadjs;detags;stddetags;deadjs;stddeadjs;thtags;stdthtags;thadjs;stdthadjs
```

Pour chaque langue `{lang}` :
- `{lang}tags` : synonymes du tag dans cette langue
- `std{lang}tags` : synonymes standardisés (utilisés pour la détection)
- `{lang}adjs` : adjectifs dans cette langue
- `std{lang}adjs` : adjectifs standardisés

### refs/discriminants.csv

Fichier contenant les mots-clés et caractères discriminants par langue :

```
type;fr;en;de;th;es;it;pt;pl;ro;ar;cn
vocabulaire;avec,sans,les,...;with,without,the,...;mit,ohne,die,...;;;...
accent;é,è,ê,...;;ä,ö,ü,ß,...;;;...
```

### refs/commun.csv

Fichier de configuration avec :
- `langues` : codes des langues actives (fr, en, de, th)
- `ecartlang` : écart minimum entre les 2 meilleurs scores pour être sûr (défaut: 2)
- `seuillang` : score minimum pour être sûr (défaut: 5)

---

## Stratégie de détection

### 1. Détection par script Unicode (prioritaire)

Certaines langues ont des alphabets distinctifs :
- **Thaï** : caractères Unicode U+0E00 à U+0E7F
- **Arabe** : caractères Unicode U+0600 à U+06FF
- **Chinois** : caractères CJK U+4E00 à U+9FFF

Si la question contient ces caractères → langue identifiée immédiatement avec score=10 et méthode="unicode".

### 2. Score de langue sélectionnée (select)

L'utilisateur peut présélectionner une langue via l'IHM ou en CLI. Ce score (valeur=3) favorise la langue choisie mais permet de détecter une autre langue si les indices sont plus forts.

- Si `langue_selectionnee` = "auto" → pas de score select
- Sinon → score de 3 pour la langue sélectionnée

### 3. Score par termes métier (terme)

Utilise les colonnes `std{lang}tags` et `std{lang}adjs` de `tags.csv` :
- Standardiser la question
- Pour chaque langue, compter les termes métier présents dans la question

### 4. Score par vocabulaire discriminant (vocabulaire)

Utilise la ligne `vocabulaire` de `discriminants.csv` :
- Utilise la question originale (avec accents) en minuscules
- Pour chaque langue, compter les mots discriminants trouvés

### 5. Score par caractères accentués (accent)

Utilise la ligne `accent` de `discriminants.csv` :
- Utilise la question originale
- Pour chaque langue, compter les caractères accentués discriminants

### 6. Score total et décision

```
score_total = score_select + score_terme + score_vocabulaire + score_accent
```

Critères de fiabilité :
- **Score suffisant** : score_total >= seuillang (défaut: 5)
- **Écart suffisant** : écart avec le 2e score >= ecartlang (défaut: 2)

### 7. Fallback DeepL (si résultat non fiable)

Si le score est trop bas OU l'écart trop faible :
- Appeler l'API DeepL pour détecter la langue
- Ajouter un score de 5 à la langue détectée par DeepL
- Recalculer le score total

Configuration : Variable d'environnement `DEEPL_API_KEY`

---

## Programme : detlang.py

### Signature CLI

```bash
python detlang.py "question" [langue_selectionnee] [--verbose]
```

- `question` : La question utilisateur (obligatoire)
- `langue_selectionnee` : fr (défaut), en, de, th, etc. ou "auto" pour désactiver le score select
- `--verbose` ou `-v` : Afficher les détails du calcul

### Sortie JSON

```json
{
  "langue_detectee": "fr",
  "score": 9,
  "scores_all": {
    "fr": 9,
    "en": 2,
    "de": 1,
    "th": 0
  },
  "methode": "select",
  "question_originale": "patients avec béance sévère",
  "question_standardisee": "patients avec beance severe"
}
```

### Champs de sortie

| Champ | Description |
|-------|-------------|
| `langue_detectee` | Code langue détecté (fr, en, de, th, etc.) |
| `score` | Score de la langue gagnante |
| `scores_all` | Scores de toutes les langues actives |
| `methode` | Méthode(s) ayant contribué : "unicode", "select", "terme", "vocabulaire", "accent", "deepl", "defaut" |
| `question_originale` | Question telle que saisie |
| `question_standardisee` | Question après standardisation |

### Fonction exportable

```python
def detecter_langue(question: str, langue_selectionnee: str = "fr", verbose: bool = False) -> dict:
    """
    Détecte la langue d'une question.

    Args:
        question: La question utilisateur
        langue_selectionnee: Langue présélectionnée (défaut: "fr", ou "auto")
        verbose: Afficher les détails

    Returns:
        dict avec langue_detectee, score, scores_all, methode, etc.
    """
```

### Fonction de cache

```python
def charger_vocabulaire() -> None:
    """
    Charge tous les vocabulaires en mémoire (cache global).
    À appeler une seule fois au démarrage de l'application.
    """
```

---

## Algorithme détaillé

```
1. Si question vide → retourner "fr" par défaut

2. Détection par script Unicode :
   - Si caractères thaï détectés → retourner "th" (score=10, methode="unicode")
   - Si caractères arabes détectés → retourner "ar" (score=10, methode="unicode")
   - Si caractères chinois détectés → retourner "cn" (score=10, methode="unicode")

3. Charger le cache (si pas déjà fait) :
   - Vocabulaire métier depuis tags.csv
   - Discriminants depuis discriminants.csv
   - Configuration depuis commun.csv

4. Calculer les 4 scores :
   - score_select : 3 si langue_selectionnee != "auto"
   - score_terme : termes métier trouvés (question standardisée)
   - score_vocabulaire : mots discriminants trouvés (question originale)
   - score_accent : caractères accentués trouvés (question originale)

5. Calculer score_total pour chaque langue

6. Vérifier fiabilité :
   - Si score_max < seuillang OU écart < ecartlang → appeler DeepL
   - Ajouter score DeepL (5) à la langue détectée

7. Déterminer la langue finale :
   - Si tous scores = 0 → "fr" (défaut)
   - Sinon → langue avec score max (priorité FR si égalité)

8. Déterminer la méthode :
   - Si une seule méthode dominante → afficher cette méthode
   - Sinon → liste des méthodes contributrices

9. Retourner le résultat JSON
```

---

## Cas de test

| Question | Langue attendue | Méthode |
|----------|-----------------|---------|
| `patients avec béance sévère` | fr | select, terme, vocabulaire, accent |
| `patients with open bite` (auto) | en | terme, vocabulaire |
| `Patienten mit Zahnlücke` (auto) | de | terme, vocabulaire, accent |
| `ผู้ป่วยที่มีฟันเปิด` | th | unicode |
| `sévère` (auto) | fr | terme, accent |
| `hello world` | fr | defaut (ou deepl si activé) |
| `` (vide) | fr | defaut |

---

## Gestion du cache

- **Mode CLI** : Le cache est chargé automatiquement au premier appel
- **Mode module** : Appeler `charger_vocabulaire()` une seule fois au démarrage

Variables globales utilisées :
- `_vocabulaire_metier` : termes de tags.csv par langue
- `_vocabulaire_discriminant` : mots de discriminants.csv par langue
- `_accents_discriminants` : caractères de discriminants.csv par langue
- `_langues_actives` : liste des langues depuis commun.csv
- `_config` : seuils ecartlang et seuillang

---

## Configuration DeepL

Variable d'environnement requise : `DEEPL_API_KEY`

L'API utilisée est l'endpoint gratuit : `https://api-free.deepl.com/v2/translate`

DeepL est appelé uniquement en fallback (score insuffisant ou écart trop faible).

---

## Pièces jointes nécessaires pour recréer le programme

1. `Prompt_contexte0412.md` — Contexte général du projet
2. `Prompt_detlang.md` — Ce document
3. `refs/tags.csv` — Fichier multilingue des tags/adjectifs
4. `refs/discriminants.csv` — Fichier des discriminants par langue
5. `refs/commun.csv` — Configuration des langues actives et seuils

---

## Spécifications techniques

### Cartouche de version
```python
#*TO*#
__pgm__ = "detlang.py"
__version__ = "0.0.0"
__date__ = "01/01/1970 00:00"
```

### Encodages
- Tous les fichiers CSV : UTF-8-BOM (utf-8-sig)
- Séparateur colonnes : `;`
- Séparateur multivaleurs : `,`
- Lignes de commentaires : commencent par `#`

### Dépendances
- Aucune bibliothèque externe requise (uniquement stdlib Python)
- DeepL : utilise `urllib.request` (stdlib)

---

**FIN DU DOCUMENT**
