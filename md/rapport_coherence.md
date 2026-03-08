# Prompt rapport_coherence V1.0.0 - 05/01/2026 14:55:34

# Rapport d'analyse de cohérence - glossaire.csv vs référentiels
# Date : 05/01/2026 12:55

## RÉSUMÉ EXÉCUTIF

Après analyse approfondie, **les référentiels sont globalement cohérents**. Le glossaire contient davantage de termes car il sert à la traduction multilingue de toutes les variantes possibles, tandis que les référentiels de détection (tags.csv, adjectifs.csv, ages.csv) contiennent les termes nécessaires pour la détection algorithmique.

---

## 1. ADJECTIFS (adjectifs.csv)

### État : ✅ COMPLET

Les 40 adjectifs canoniques sont bien présents avec leurs formes accordées (f, mp, fp) et leurs patterns (pas).

### À signaler - Formes dans adjectifs.csv absentes du glossaire type 'a' (18 formes)

Ces formes féminines/plurielles devraient être ajoutées au glossaire pour la traduction :
- antérieure, antérieures
- bactérienne
- bénigne, bénignes
- complète, complètes
- incisive
- incluse, incluses
- post-traumatique
- postérieure, postérieures
- pubertaire, pubertaires
- septiques
- unilatérales, unilatéraux

**Action suggérée** : Ajouter ces 18 formes au glossaire.csv avec type='a'

---

## 2. TAGS (tags.csv)

### État : ✅ COMPLET pour la détection

Les 133 tags canoniques avec leurs 980 patterns couvrent les besoins de détection.

### Patterns dans glossaire absents de tags.csv (644)

Ces patterns se répartissent en :

1. **Pluriels de termes existants** (~42) : couverts automatiquement
2. **Combinaisons tag+adjectif** (~200) : détectées par dettags + detadjs
   - Exemples : "béance antérieure", "asymétrie mandibulaire"
3. **Angles céphalométriques** (~20) : dans angles.csv, pas tags.csv
   - anb, sna, snb, analyse de wits, ao-bo
4. **Variantes générées automatiquement** (~380) : erreurs probables
   - Exemples : "appointmente", "articulationne", "avalère"

**Action suggérée** : Aucun ajout nécessaire à tags.csv. Les patterns sont dans glossaire pour la traduction uniquement.

---

## 3. AGES (ages.csv)

### État : ✅ COMPLET

Les 47 lignes couvrent tous les cas d'usage avec patterns {n}.

### Patterns dans glossaire signalés comme manquants mais présents (21)

Ces termes sont en fait présents via les patterns avec {n} :
- "berges", "balais" → "{n} berges|{n} balais"
- "génération x/y/z" → lignes 23, 26, 29
- "environ", "approximativement", "autour de" → lignes 12-14
- etc.

**Note** : L'utilisateur a mentionné avoir enlevé bébés et seniors, mais la ligne 17 (bébés) et la ligne 44 (seniors) sont encore présentes dans le fichier fourni.

---

## 4. ERREURS PROBABLES DANS GLOSSAIRE

### Patterns 'pa' bizarres (14 termes)

Ces termes semblent être des erreurs de génération automatique :

| Terme | Problème |
|-------|----------|
| ++ | Symbole invalide |
| consultère | Forme verbale erronée |
| expansionne, expansionnes | Forme verbale erronée |
| impactionnes | Forme verbale erronée |
| mastiquères | Forme erronée de "mastication" |
| pacifière, pacifières | Devrait être "pacifier" (sucette) |
| saosse | Terme inconnu |
| slicingue, slicingues | Francisation erronée de "slicing" |
| surjète, surjètes | Forme erronée |
| urgentes | Adjectif, pas pattern |

**Action suggérée** : Vérifier et corriger/supprimer ces 14 entrées dans glossaire.csv

### Patterns 'pt' variantes générées (exemples)

Ces termes semblent être des erreurs de génération :
- appointmente, appointmentes
- articulationne, articulationnes
- avalère, avalères
- basculemente
- brackète, brackètes
- chevauchemente
- cleaningue
- clickingue, clickingues
- etc.

---

## CONCLUSION

| Référentiel | Action requise |
|-------------|----------------|
| adjectifs.csv | ✅ Aucune |
| tags.csv | ✅ Aucune |
| ages.csv | ⚠️ Vérifier lignes bébés/seniors |
| glossaire.csv | ⚠️ Corriger 14 patterns 'pa' erronés |
| glossaire.csv | ⚠️ Ajouter 18 formes adjectifs manquantes |
