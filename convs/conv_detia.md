# Prompt conv_detia V1.0.1 - 26/12/2025 10:10:34

# Conversation : detia
## Synthèse KITVIEW - Évolution de detia.py

---

## Informations

| Élément | Valeur |
|---------|--------|
| Date de début | 24/12/2025 10:15 UTC |
| Dernière mise à jour | 24/12/2025 12:20 UTC |
| Objectif | Évolution detia.py : ia.csv, parsing intelligent, architecture unifiée |

---

## Échanges

### Q1 : Parsing intelligent des arguments CLI
**Date** : 24/12/2025 ~10:15 UTC

**Demande** : Les arguments CLI doivent fonctionner dans n'importe quel ordre (question, moteur, langue) sans ambiguïté.

**Solution implémentée** :
- Fonction `_identifier_argument(arg)` qui détecte la nature par le contenu :
  - Finit par `.csv` → fichier batch
  - Nom connu dans ia.csv → moteur
  - Code langue dans commun.csv → langue
  - Sinon → question

**Exemples d'usage** :
```bash
python detia.py "bruxisme" sonnet     # Question + moteur
python detia.py sonnet "bruxisme"     # Moteur + question
python detia.py tests.csv haiku fr    # Fichier + moteur + langue
```

---

### Q2 : Erreur parsing JSON avec version 1.0.13
**Date** : 24/12/2025 ~10:30 UTC

**Problème** : `ia_erreur_parsing": "Expecting value: line 1 column 1 (char 0)"` - L'IA retourne une réponse vide.

**Diagnostic** : Version non-slim utilisait un prompt trop gros.

**Solution** : Utiliser la version SLIM qui réduit le prompt de ~50%.

---

### Q3 : Fusion version SLIM + ia.csv + parsing intelligent
**Date** : 24/12/2025 ~11:00 UTC

**Demande** : Fusionner la version SLIM (de conv_detiaslim_pipeline) avec les nouvelles fonctionnalités.

**Résultat** : detia.py V2.1.0
- Fichiers SLIM pour prompt réduit
- Configuration moteurs via ia.csv
- Langues actives depuis commun.csv (colonne `langues`)
- Parsing intelligent des arguments

---

### Q4 : Changer moteur par défaut à gpt4o
**Date** : 24/12/2025 ~11:45 UTC

**Demande** : Moteur par défaut = gpt4o au lieu de sonnet.

**Résultat** : `DEFAULT_MODEL = "gpt4o"`

---

### Q5 : Architecture unifiée - Supprimer fichiers slim/map séparés
**Date** : 24/12/2025 ~12:00 UTC

**Problème identifié** : Doublons de fichiers :
- `syntags.csv` (complet)
- `frsyntags_slim.csv` (juste stdtag)
- `frsyntags_map.csv` (stdtag → canontag)

**Solution adoptée** : Architecture UNIFIÉE
- Utiliser directement `syntags.csv` et `synadjs.csv`
- Une seule lecture qui extrait :
  - Liste des stdtag/stdadj (pour le prompt IA)
  - Mapping stdtag → canontag (pour le post-traitement)
- Plus besoin des fichiers `_slim.csv` et `_map.csv`

**Résultat** : detia.py V2.2.0

---

### Q6 : Stratégie pour compléter glossaire.csv
**Date** : 24/12/2025 ~12:00 UTC

**Question** : Comment ajouter des langues de façon maîtrisée ?

**Réponse** : Utiliser traduis.py avec l'option `--only` :

```bash
# 1. Tester sur 5 lignes
python traduis.py -t syntags.csv --only de

# 2. Si OK, lancer la traduction complète
python traduis.py syntags.csv --only de

# 3. Répéter pour chaque langue
python traduis.py syntags.csv --only es
```

**Prérequis** :
1. Ajouter la colonne vide dans glossaire.csv
2. Ajouter la langue dans commun.csv (colonne `langues`)
3. Lancer traduis.py

---

## Fichiers générés

| Fichier | Version | Description |
|---------|---------|-------------|
| `detia.py` | 2.2.0 | Module IA unifié (syntags.csv direct) |
| `conv_detia.md` | - | Ce document de synthèse |

---

## Architecture finale detia.py V2.2.0

```
FICHIERS UTILISÉS :
├── refs/
│   ├── frsyntags.csv      → Tags (stdtag;canontag)
│   ├── frsynadjs.csv      → Adjectifs (stdadj;canonadj;canontag)
│   ├── ages.csv           → Patterns âge/sexe
│   ├── angles.csv         → Seuils céphalométriques
│   ├── ia.csv             → Configuration moteurs IA
│   └── commun.csv         → Langues actives

FLUX DE DONNÉES :
1. charger_references()
   → Lit syntags.csv → {syntags_liste, syntags_map}
   → Lit synadjs.csv → {synadjs_liste, synadjs_map}

2. _construire_prompt_systeme()
   → Utilise syntags_liste (stdtag uniquement, compact)
   → Utilise synadjs_liste (stdadj uniquement, compact)
   → Prompt ~50% plus petit qu'avec les fichiers complets

3. detecter_tout()
   → Appel API (gpt4o par défaut)
   → Post-traitement avec syntags_map/synadjs_map
   → Mapping stdtag → canontag
```

---

## Prompt de recréation detia.py V2.2.0

**Prompt** :
```
Crée detia.py V2.2.0 pour KITVIEW avec les caractéristiques suivantes :

1. ARCHITECTURE UNIFIÉE :
- Utiliser directement syntags.csv et synadjs.csv (pas de fichiers _slim/_map)
- Une seule lecture par fichier : extraire liste (pour prompt) + mapping (pour post-traitement)
- Fonctions _charger_syntags() et _charger_synadjs() retournent Tuple[liste, mapping]

2. CONFIGURATION MOTEURS (ia.csv) :
- Charger les moteurs depuis refs/ia.csv (colonne 'moteur')
- Moteur par défaut : gpt4o
- Support OpenAI direct (via='openai') et Eden AI (via='eden')

3. LANGUES ACTIVES (commun.csv) :
- Charger les langues actives depuis refs/commun.csv (colonne 'langues')
- Utilisé pour identifier les arguments CLI

4. PARSING CLI INTELLIGENT :
- Arguments dans n'importe quel ordre
- Détection automatique : moteur (ia.csv), langue (commun.csv), fichier (.csv), question
- Options : -l (liste moteurs), -v (verbose), -d (debug)

5. PROMPT OPTIMISÉ :
- Envoyer uniquement les stdtag/stdadj (pas les canontag/canonadj)
- Table des angles céphalométriques (ANB, SNA, SNB)
- Exemples few-shot

6. POST-TRAITEMENT :
- Mapper stdtag → canontag via syntags_map
- Mapper stdadj → canonadj via synadjs_map
- Générer les clauses SQL
```

**PJ nécessaires** :
- `Prompt_contexte2312.md`
- `frsyntags.csv` (exemple de structure)
- `frsynadjs.csv` (exemple de structure)
- `ia.csv`
- `commun.csv`
- `angles.csv`

---

## Fichiers obsolètes (à supprimer)

Après validation de detia.py V2.2.0, ces fichiers peuvent être supprimés :
- `frsyntags_slim.csv`
- `frsyntags_map.csv`
- `frsynadjs_slim.csv`
- `frsynadjs_map.csv`
- (et équivalents pour autres langues : en, ja...)

---

*Document généré le 24/12/2025 12:20 UTC*
