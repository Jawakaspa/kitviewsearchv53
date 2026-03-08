# Prompt conv_bugtraductions V1.0.2 - 07/01/2026 14:52:51

# Synthèse Conversation : bugtraductions

## Informations
- **Date de début** : 07/01/2026 ~00:00
- **Fichiers modifiés** : 
  - traduire.py (V1.0.15 → V1.0.16) - Correction ambiguïté FR/EN
  - search.py (V1.0.24 → V1.0.25) - Traduction complète DeepL

---

## Échange 1 - 07/01/2026 00:00

### Question
Différence de résultats entre une question en FR et EN pour la même requête :
- FR : `"Nombre de patients avec linguo-version avec déviation maxillaire ?"` → **3 patients** ✓
- EN : `"Number of patients with linguo-version with maxillary deviation?"` → **276 patients** ✗

Demande d'afficher la "question technique FR" envoyée à `trouve.py`.

### Diagnostic
1. **Observation** : La question anglaise est détectée comme `Langue question: fr`
2. **Cause racine identifiée** : Dans `detecter_langue_glossaire()` (traduire.py), quand plusieurs langues trouvent le même nombre de pathologies (FR et EN trouvent tous les deux "linguo-version"), le code préfère FR par défaut :
   ```python
   # En cas d'ambiguïté, on préfère dans l'ordre: fr, en, de, es...
   for lang_pref in LANGUES_GLOSSAIRE:  # ['fr', 'en', 'de', ...]
   ```
3. **Conséquence** : La question anglaise n'est pas traduite/résolue → "maxillary deviation" n'est pas converti en terme français → pas de match sur ce critère → 276 patients (seulement "linguo-version")

### Solution implémentée (traduire.py V1.0.16)

**Modification 1** : `detecter_langue_glossaire()` retourne maintenant un 6ème élément `ambiguite` (bool)
```python
def detecter_langue_glossaire(texte, glossaire, verbose=False, debug=False):
    """
    Returns:
        tuple: (langue, pathologies_fr, positions, residu, score, ambiguite)
    """
    # ... 
    ambiguite = len(langues_meme_score) > 1
    return meilleure_langue, ..., ambiguite
```

**Modification 2** : `detecter_langue()` utilise DeepL pour trancher en cas d'ambiguïté
```python
if langue_glossaire:
    if ambiguite:
        # Utiliser DeepL pour trancher FR/EN
        _, langue_deepl, _ = deepl_traduire(question, verbose=verbose)
        if langue_deepl and langue_deepl != 'unknown':
            return langue_deepl
    return langue_glossaire
```

---

## Échange 2 - 07/01/2026 00:15

### Question
Nouveau problème en italien :
- FR : `"Patientes de moins de 39 ans présentant un encombrement et une rotation dentaire antihoraire"` → **3 patients** ✓
- IT : `"Pazienti di età inferiore ai 39 anni con affollamento e rotazione dei denti in senso antiorario"` → **0 patients** ✗

La résolution glossaire donne un mélange FR/IT :
`"patients di âge inférieur ai 39 ans avec crowding et rotation dei denti dans senso antiorario"`

Les termes médicaux sont traduits (`affollamento` → `crowding`) mais les mots courants italiens (`di`, `ai`, `dei denti`, `senso antiorario`) restent non traduits.

### Diagnostic
Le glossaire traduit uniquement les termes médicaux orthodontiques, pas les mots courants. La résolution sémantique est insuffisante pour les phrases complètes.

### Options proposées
- **Option A** : DeepL traduit la question ENTIÈRE, puis le glossaire valide les termes médicaux
- **Option B** : Après résolution glossaire, si trop de mots non résolus, utiliser DeepL
- **Option C** : Enrichir le glossaire avec les mots courants (lourd à maintenir)

**Choix utilisateur** : Option A

### Solution implémentée (search.py V1.0.25)

**Modification de l'ÉTAPE 3** : Remplacement de `resoudre_question_semantique()` par `traduire()` pour les langues non-FR

```python
# ÉTAPE 3 : TRADUCTION QUESTION → FRANÇAIS (Option A : DeepL complet)
if lang == 'fr':
    question_resolue = question
    question_technique_fr = question
else:
    if TRADUIRE_DISPONIBLE:
        question_traduite, fournisseur = traduire(
            texte=question,
            source_lang=lang,
            target_lang='fr',
            api_key=deepl_key,
            verbose=verbose
        )
        if question_traduite and question_traduite != question:
            question_resolue = question_traduite
            question_technique_fr = question_traduite
            modulelangue = f'traduire_{fournisseur}'
```

**Nouveaux champs** :
- `question_technique_fr` : Question effectivement envoyée à `trouve.py`
- `resolution_provider` : Indique le fournisseur réel (`traduire_deepl`, `traduire_glossaire`)

**Affichage CLI** : Nouvelle ligne `Question tech FR` pour debug

---

## Fichiers livrés
- `traduire.py` V1.0.16 - Correction bug ambiguïté FR/EN
- `search.py` V1.0.26 - Traduction complète DeepL directe (fix V1.0.25)

---

## Échange 3 - 07/01/2026 00:30

### Question
Après test de search.py V1.0.25, le résultat est meilleur (4 patients IT vs 3 FR - normal car "Pazienti" est mixte, "Patientes" est féminin). Mais la résolution indique toujours `traduire_glossaire` au lieu de `traduire_deepl`, et la question tech FR est bizarre :
> `crowding rotation patients âgés de moins de 39 ans avec et sans dents dans le sens inverse des aiguilles d'une montre`

Les pathologies sont au début, le reste mal traduit.

### Diagnostic
La fonction `traduire()` dans traduire.py utilise le glossaire en priorité :
1. Cherche des pathologies dans le glossaire
2. Si trouvées → traduit via glossaire, DeepL seulement pour le résidu
3. Résultat = mélange mal reconstruit

### Solution implémentée (search.py V1.0.26)
Appel direct à `deepl_traduire()` au lieu de `traduire()` :

```python
# Import ajouté
from traduire import (..., deepl_traduire)

# ÉTAPE 3 : Appel direct DeepL
question_traduite, langue_deepl, temps_trad = deepl_traduire(
    texte=question,
    source_lang=lang,
    verbose=verbose,
    debug=False
)
if question_traduite and question_traduite != question:
    question_technique_fr = question_traduite
    modulelangue = 'deepl_direct'
```

---

## Prompts de recréation

### traduire.py V1.0.16

**Fichiers PJ nécessaires** :
- `traduire.py` V1.0.15 (version précédente)
- `Prompt_contexte2312.md` (contraintes projet)

**Prompt** :
```
Contexte : Module traduire.py pour détection de langue et traduction multilingue dans KITVIEW.

BUG À CORRIGER : Quand une question anglaise contient des termes techniques orthodontiques 
identiques en FR/EN (ex: "linguo-version"), le glossaire trouve le même score pour les deux 
langues. Le code actuel préfère FR par défaut en cas d'ambiguïté, ce qui fait que les 
questions anglaises ne sont pas traduites.

SOLUTION : En cas d'ambiguïté (plusieurs langues avec même score dans detecter_langue_glossaire),
utiliser DeepL API pour trancher au lieu de préférer FR automatiquement.

MODIFICATIONS REQUISES :
1. detecter_langue_glossaire() : Ajouter un 6ème élément de retour "ambiguite" (bool)
2. detecter_langue() : Si ambiguite=True, appeler deepl_traduire() pour trancher
3. Mettre à jour tous les appels à detecter_langue_glossaire() pour gérer le 6ème élément

Version cible : 1.0.16
```

### search.py V1.0.26

**Fichiers PJ nécessaires** :
- `search.py` V1.0.24 (version précédente)
- `traduire.py` V1.0.16 (pour la fonction deepl_traduire())
- `Prompt_contexte2312.md` (contraintes projet)

**Prompt** :
```
Contexte : Module search.py pour recherche multilingue KITVIEW.

PROBLÈME : Pour les langues non-FR, la fonction traduire() utilise le glossaire en priorité,
ce qui donne des traductions partielles (termes médicaux traduits, mots courants non traduits).

SOLUTION (Option A corrigée) : Utiliser deepl_traduire() DIRECTEMENT au lieu de traduire()
pour avoir une traduction complète DeepL de la question entière.

MODIFICATIONS REQUISES :
1. Import : Ajouter deepl_traduire depuis traduire.py
2. ÉTAPE 3 : Remplacer l'appel à traduire() par deepl_traduire()
   - deepl_traduire(texte, source_lang, verbose, debug) → (texte_traduit, langue, temps_ms)
3. modulelangue = 'deepl_direct' quand traduction réussie
4. Fallback sur glossaire si DeepL échoue (langue_deepl == 'unknown')

Version cible : 1.0.26
```

---

## Résumé des changements

| Fichier | Version | Changement |
|---------|---------|------------|
| traduire.py | 1.0.15 → 1.0.16 | Fix bug ambiguïté FR/EN - DeepL tranche |
| search.py | 1.0.24 → 1.0.26 | Traduction complète DeepL directe (deepl_traduire) |

### Historique search.py
- **V1.0.25** : Tentative avec `traduire()` - problème glossaire prioritaire
- **V1.0.26** : Fix avec `deepl_traduire()` direct - traduction complète OK
