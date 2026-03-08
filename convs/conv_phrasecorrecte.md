# Prompt conv_phrasecorrecte V1.0.3 - 08/12/2025 20:29:02

# Synthèse conversation : phrasecorrecte

## Informations
- **Fichier** : conv_phrasecorrecte.md
- **Projet** : Kitview - Génération de phrases de test multilingues

---

## Échanges

### 07/12/2025 17:42 UTC - Question initiale
**Question** : Comment générer des phrases avec des bribes et des pathologies, en gérant correctement les accords de genre (masculin/féminin), nombre (singulier/pluriel) et les verbes ?

**Réponse** : Demande de clarifications sur la structure des bribes, la source des pathologies, et la préférence entre correction a priori ou a posteriori.

---

### 07/12/2025 18:12 UTC - Clarifications et choix techniques
**Question** : Fourniture des fichiers `exquis.csv` (brouillon) et `exemplesquestions.csv`. Préférence pour correction a posteriori avec LanguageTool.

**Réponse** : 
- **Recommandation** : LanguageTool pour la correction grammaticale (30+ langues, gratuit)
- **Limitation** : Thaï, Arabe, Chinois non supportés par LanguageTool
- **Alternative** : DeepL en complément pour ces 3 langues

**Langues supportées par LanguageTool** :
| Langue | Support |
|--------|---------|
| FR, EN, DE, ES, IT, PT, PL, RO | ✅ Complet |
| TH, AR, CN | ❌ Non supporté |

---

### 07/12/2025 18:31 UTC - Analyse du besoin complet
**Question** : Fourniture de `tagssaisis.csv` avec convention Majuscule=masculin, minuscule=féminin. Demande de création d'un vrai `exquis.csv` et vision du pipeline complet.

**Réponse** : Identification de 3 étapes distinctes :
1. `exquis.csv` - Structure des bribes de phrases
2. Programme de génération base + phrases
3. Programme de correction grammaticale

---

### 07/12/2025 18:45 UTC - Validation structure et création exquis.csv
**Question** : Validation des choix de structure avec extension jusqu'à 4 tags ({T1} à {T4}), 30% de patterns "Combien", sujets pluriels uniquement.

**Réponse** : Création de `exquis.csv` avec :
- **Structure** : 9 colonnes (A à I)
- **Conventions** :
  - `{T1}` à `{T4}` : placeholders pour tags
  - `{G1}` à `{G3}` : accord en genre avec tag précédent
- **Patterns** : 1 tag (15), 2 tags (28), 3 tags (18), 4 tags (13) = 74 patterns total
- **Répartition** : ~30% "Combien", ~70% autres (Quels, Montre-moi, Trouve, etc.)

---

### 07/12/2025 18:52 UTC - Correction encodage exquis.csv
**Problème** : Accents mal affichés (ex: "gÃ©nÃ©ration" au lieu de "génération")

**Solution** : Recréation du fichier avec BOM UTF-8 correct (`\xEF\xBB\xBF` en début de fichier)

---

### 07/12/2025 19:05 UTC - Fourniture fichiers patients existants
**Fichiers fournis** :
- `pats100.csv` et `pats1000.csv` — patients générés avec `canontags` et `canonadjs`
- `generepats.py` — générateur existant (seeds fixes, distribution pyramidale)
- `conv_structurebase.md` — conversation sur structure SQL

**Structure observée** :
- `canontags` : tags séparés par `,`
- `canonadjs` : adjectifs positionnels, séparés par `,` entre tags et `|` entre adjectifs d'un même tag

---

### 07/12/2025 19:15 UTC - Analyse et suggestions
**Remarques** :
1. Incohérence nommage : `canonfr` (tagssaisis) vs `stdtag` (conv_structurebase)
2. Distribution existante : `{1: 0.40, 2: 0.25, 3: 0.20, 4: 0.15}` dans generepats.py

**Pipeline confirmé** :
```
tagssaisis.csv → tags2refs.py → tagsrefs.csv → tags2tag.py → syntag.csv
                                             → tags2adj.py → synadj.csv
```

**Suggestion ordre des tâches** :
1. Valider `tagssaisis.csv`
2. Créer `syntag.csv` et `synadj.csv`
3. Développer `dettag.py`
4. Puis `genquest.py`

---

### 08/12/2025 08:45-09:25 UTC - Clarification pipeline et création tags2synta.py

**Clarifications nomenclature** :
- `std` = forme standardisée (minuscules, sans accents) via `standardise.py`
- `canon` = forme canonique (avec majuscules/accents)
- `tagssaisis.csv` → `tagsfr.csv` → `tags.csv` (multilingue via `fr2tags.py`)

**Pipeline complet confirmé** :
```
tagssaisis.csv (saisie manuelle)
      │
      ▼ (transformation structure)
tagsfr.csv (type;frtags;stdfrtags;fradjs;stdfradjs)
      │
      ▼ fr2tags.py (internationalisation)
tags.csv (colonnes pour chaque langue: XXtags, stdXXtags, XXadjs, stdXXadjs)
      │
      ▼ tags2synta.py
      │
      ├──► syntags.csv (stdtag;canontag;langue)
      │
      └──► synadjs.csv (stdadj;canonadj;langue;canontag)
```

**Décision architecture i18n** :
- `canontag` et `canonadj` = toujours forme française
- Traductions récupérées via `tags.csv` à la demande (dictionnaire Python)
- Avantages : DRY, maintenance simplifiée, performance O(1)

**Distribution tags modifiée** :
- Ancienne : `{1: 0.40, 2: 0.25, 3: 0.20, 4: 0.15}`
- Nouvelle : `{1: 0.10, 2: 0.20, 3: 0.30, 4: 0.40}` (pyramide inversée pour démos)

**Programme créé** : `tags2synta.py`
- Entrée : `refs/tags.csv`, `refs/commun.csv` (langues)
- Sortie : `refs/syntags.csv` (188 entrées), `refs/synadjs.csv` (70 entrées)
- Détection automatique des langues depuis colonnes `XXtags`
- Tri par langue puis longueur décroissante (pour détection par grignotage)

---

### 08/12/2025 09:45 UTC - Préparation tests de détection

**Contexte** : L'utilisateur a créé `dettags.py` et `detadjs.py` et souhaite les tester.

**Nouveau fichier tags.csv** : 11 tags × 4 langues (fr, en, de, th)

**Priorité clarifiée** : 
- La sophistication d'accord M/F et S/P n'est PAS prioritaire
- Priorité = avoir des questions variées multilingues pour tester la détection

**Objectifs des tests** :
1. Détecter la langue à partir des synonymes dans `tags.csv`
2. Détecter les tags et adjectifs une fois la langue identifiée

**Livrable** : Prompt de continuation `Prompt_testsdetections.md` créé pour nouvelle conversation

---

## Fichiers générés

| Fichier | Description | Statut |
|---------|-------------|--------|
| `exquis.csv` | Bribes de phrases cadavres exquis (74 patterns) | ✅ Créé |
| `tags2synta.py` | Génère syntags.csv et synadjs.csv | ✅ Créé |
| `syntags.csv` | Lookup stdtag → canontag français (188 entrées) | ✅ Généré |
| `synadjs.csv` | Lookup stdadj → canonadj français + tag parent (70 entrées) | ✅ Généré |
| `Prompt_testsdetections.md` | Prompt de continuation pour tests | ✅ Créé |

---

## Fichiers fournis par l'utilisateur

| Fichier | Description |
|---------|-------------|
| `exquis.csv` (brouillon) | Premier jet des bribes |
| `exemplesquestions.csv` | Exemples de questions multilingues |
| `tagssaisis.csv` | Tags avec convention M/F par initiale |
| `tags.csv` | Fichier multilingue de référence (fr, en, de, th) |
| `pathosyn.csv` | Ancien format lookup synonymes (modèle) |
| `commun.csv` | Paramètres communs dont liste des langues |
| `generepats.py` | Générateur de patients existant |
| `pats100.csv`, `pats1000.csv` | Patients générés |
| `conv_structurebase.md` | Synthèse conversation structure base |

---

## Pipeline prévu (à développer)

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  1. exquis.csv  │     │  2. genbase.py  │     │  3. genquest.py │
│  (bribes)       │     │  Base de test   │     │  Questions      │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 ▼
                    ┌─────────────────────┐
                    │  4. corrigephrase.py│
                    │  (LanguageTool)     │
                    └─────────────────────┘
```

### Programmes à créer

1. **genbase.py** - Génère des bases de test (100 à 25000 patients) avec 1-4 tags/patient
2. **genquest.py** - Génère des questions à partir de exquis.csv + base, garantit 1-10% de résultats
3. **corrigephrase.py** - Corrige les accords grammaticaux (LanguageTool + DeepL pour TH/AR/CN)

---

## Décisions prises

| Sujet | Décision |
|-------|----------|
| Correction grammaticale | A posteriori (pas a priori) |
| Outil principal | LanguageTool (gratuit, multilingue) |
| Langues exotiques | DeepL en complément (TH, AR, CN) |
| Sujets des phrases | Pluriels uniquement (V1) |
| Nombre max de tags | 4 par phrase |
| Convention genre | Majuscule=M, minuscule=F dans tags |
| Notation accord | `{G1}` = accord avec T1, etc. |

---

## Prochaines étapes

1. [x] Valider `exquis.csv` généré — corrigé encodage UTF-8-BOM
2. [x] Structure base de test — existe déjà via `generepats.py`
3. [x] Créer `tags2synta.py` — génère syntags.csv et synadjs.csv ✅
4. [ ] Modifier `generepats.py` — nouvelle distribution {1:10%, 2:20%, 3:30%, 4:40%}
5. [ ] Créer `dettag.py` (détection tags dans phrase)
6. [ ] Créer `genquest.py` (génération questions garantissant 1-10% résultats)
7. [ ] Créer `corrigephrase.py` (LanguageTool + DeepL)

---

## Prompts de recréation des programmes

### tags2synta.py
**Prompt** : Créer `tags2synta.py` qui génère `syntags.csv` et `synadjs.csv` à partir de `tags.csv`.
- Entrée : `refs/tags.csv` (multilingue), `refs/commun.csv` (langues)
- Sortie : `refs/syntags.csv` (stdtag;canontag;langue), `refs/synadjs.csv` (stdadj;canonadj;langue;canontag)
- `canontag` et `canonadj` = toujours forme canonique française
- Détection automatique des langues depuis colonnes XXtags
- Tri par langue puis longueur décroissante de stdtag/stdadj
- Ignorer les adjectifs avec canonadj vide
- Dédoublonnage des entrées

**Fichiers PJ** : `tags.csv`, `commun.csv`, `pathosyn.csv` (modèle), `Prompt_contexte.md`

---

## Liens avec autres conversations

- **conv_structurebase.md** : Structure SQL 5 tables, pipeline de transformation tags

---

## Questions en suspens

1. ~~Nommage : `canonfr` vs `stdtag`~~ → Clarifié : `std` = standardisé, `canon` = canonique
2. ~~Pipeline exact~~ → Confirmé avec `fr2tags.py` ajouté

---

*Dernière mise à jour : 08/12/2025 09:45 UTC*
