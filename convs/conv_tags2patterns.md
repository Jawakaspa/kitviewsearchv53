# Prompt conv_tags2patterns V1.0.0 - 27/12/2025 22:09:00

# Synthèse de conversation : tags2patterns

## Informations générales
- **Nom de la conversation** : tags2patterns
- **Date de création** : 27/12/2025

---

## Échanges

### Échange 1 - 27/12/2025 14:38

**Demande** : Créer `tags2patterns.py` selon le prompt `Prompt_tags2patterns.md`

**Questions de clarification posées** :
1. Demande de `standardise.py` (module obligatoire)
2. Clarification sur le nom du programme (tags2patterns.py vs tags2syn.py mentionné dans le prompt)
3. Question sur une apparente anomalie dans tagsadjs.csv (ligne 26)

**Réponses reçues** :
1. `standardise.py` fourni en pièce jointe
2. Nom confirmé : `tags2patterns.py`
3. Pas d'anomalie réelle - tout ce qui est après XY ne compte pas pour type=p

**Réalisation** :
- Création de `tags2patterns.py` conforme au prompt
- Fonctionnalités implémentées :
  - Chargement et validation de `tagsadjs.csv`
  - Vérification des colonnes obligatoires
  - Vérification des valeurs Xgn valides
  - Détection des doublons de patterns (synonymes)
  - Vérification de correspondance adjectifs (erreur si non défini, warning si non utilisé)
  - Génération de `patternstagsfr.csv` (canontag;synonyme;pattern)
  - Génération de `patternsadjsfr.csv` (canonadj;canontag;synonyme;pattern)
  - Tri par longueur décroissante de pattern
  - Support import et CLI avec --verbose et --debug

**Test réussi** :
- 134 tags chargés
- 28 adjectifs chargés
- 778 lignes générées dans `patternstagsfr.csv`
- 539 lignes générées dans `patternsadjsfr.csv`

---

## Fichiers créés

| Fichier | Description |
|---------|-------------|
| `tags2patterns.py` | Programme de transformation tagsadjs.csv → patterns CSV |
| `patternstagsfr.csv` | Synonymes des tags (778 lignes) |
| `patternsadjsfr.csv` | Synonymes des adjectifs par tag (539 lignes) |

---

## Prompt de recréation

Pour recréer `tags2patterns.py` à partir de zéro :

**Pièces jointes requises** :
1. `Prompt_contexte2312.md` - Contexte général du projet
2. `Prompt_tags2patterns.md` - Spécifications détaillées
3. `standardise.py` - Module de normalisation (import obligatoire)
4. `tagsadjs.csv` - Fichier source pour test

**Instruction** :
```
Crée tags2patterns.py selon Prompt_tags2patterns.md.
Le programme transforme tagsadjs.csv en :
- patternstagsfr.csv (canontag;synonyme;pattern)
- patternsadjsfr.csv (canonadj;canontag;synonyme;pattern)

Fonctionnalités requises :
- Import obligatoire de standardise.py (pas de fallback)
- Validation complète du fichier source
- Détection doublons patterns → erreur fatale
- Adjectifs utilisés mais non définis → erreur fatale
- Adjectifs définis mais non utilisés → warning
- Tri par longueur décroissante de pattern
- Interface CLI (--verbose, --debug) et import
```

---

## Notes techniques

- Encodage CSV sortie : UTF-8-SIG (avec BOM)
- Séparateur : `;`
- Le canon est inclus comme premier synonyme dans patternstagsfr.csv
- Les formes conjuguées des adjectifs (m/f/mp/fp) sont dédupliquées
- Les patterns courts apparaissent en fin de fichier (tri décroissant)
