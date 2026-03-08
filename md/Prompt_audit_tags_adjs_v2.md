# Prompt_audit_tags_adjs_v2.md — Audit complet & correctifs

**Date** : 10/02/2026  
**Entrée** : Résultat test `testtagsin_v2.csv` — 37/37 traitées, 6 anomalies

---

## 1. Bilan du test

### Résultat : 31/37 ✅, 6 anomalies

| # | Question | Résultat | Problème | Catégorie |
|---|---|---|---|---|
| 1 | `crowding mandibulaire` | résidu "mandibulaire" | `as` vide | Données |
| 2 | `occlusion croisée gauche` | résidu "gauche" | `as` vide | Données |
| 3 | `procheilie supérieure` | → **bipro** [maxillaire] | Conflit tag/pattern + adj/pattern | Données |
| 4 | `rétrocheilie inférieure` | → **rétroalvéolie**, résidu "inferieure" | Conflit tag/pattern + adj non autorisé | Données |
| 5 | multi-tag crowding | résidu "mandibulaire" | Cascade #1 | Données |
| 6 | 50 adjectifs au lieu de 51 | Entête comptée | Faux positif, 50 est correct | ∅ |

### Comptage adjectifs : 50 (correct)

Le fichier contient 50 adjectifs + 1 ligne d'entête. Le `wc` comptait l'entête "a" comme donnée. **Pas de manquant.**

---

## 2. Correctif A — Conflits tag/pattern (2 corrections dans tags_v2.csv)

### Diagnostic clinique (confirmé ChatGPT + Thierry)

> Les dents sont alvéolaires, les lèvres sont chéiliennes.

- **procheilie** = lèvres projetées en avant (tissus mous) ≠ **bipro** = incisives vestibulées (dento-alvéolaire)
- **rétrocheilie** = lèvres en retrait ≠ **rétroalvéolie** = incisives rétro-inclinées

Ces 4 tags sont **indépendants**. Les patterns croisés doivent être retirés.

### Corrections

**Ligne 25 — bipro** : retirer `prochéilie,prochéilies` des patterns

```
AVANT: bipro;f;maxillaire,incisif,sévère;alvéolie,biproalvéolie,proalvéolie,prochéilie,prochéilies,proinclinaison,proinclinaisons,pro inclinaison;pathologie
APRÈS: bipro;f;maxillaire,incisif,sévère;alvéolie,biproalvéolie,proalvéolie,proinclinaison,proinclinaisons,pro inclinaison;pathologie
```

**Ligne 133 — rétroalvéolie** : retirer `rétrochéilie,rétrochéilies` des patterns

```
AVANT: rétroalvéolie;f;mandibulaire,maxillaire,sévère,modéré;rétrochéilie,rétrochéilies,rétroinclinaison,rétroinclinaisons;pathologie
APRÈS: rétroalvéolie;f;mandibulaire,maxillaire,sévère,modéré;rétroinclinaison,rétroinclinaisons;pathologie
```

---

## 3. Correctif B — Conflits adjectif/pattern (4 corrections dans adjectifs_v2.csv)

### Diagnostic

Références circulaires entre 2 paires d'adjectifs :

| Adj A | Patterns de A contiennent | Adj B | Patterns de B contiennent |
|---|---|---|---|
| maxillaire | `supérieur,supérieure` | supérieur | `maxillaire` |
| mandibulaire | `inférieur,inférieure` | inférieur | `mandibulaire` |

Conséquence : le premier chargé (ordre CSV) capture les patterns de l'autre → collision.

### ⚠️ Nuance clinique avant de fusionner

Thierry a choisi : **"synonymes exacts, garder un seul canonique par paire"**.

Cependant, il y a un cas limite : **procheilie** et **rétrocheilie** utilisent `supérieur/inférieur` dans leur colonne `as` (lèvre supérieure/inférieure). Si on fusionne supérieur→maxillaire :

- "procheilie supérieure" → canonique stocké = "maxillaire" → affichage "procheilie maxillaire"
- Cliniquement, "procheilie maxillaire" est fonctionnel mais moins précis que "procheilie supérieure"

**Recommandation alternative (plus sûre)** : garder les 4 adjectifs séparés, juste retirer les cross-patterns :

| Adjectif | Patterns AVANT | Patterns APRÈS |
|---|---|---|
| maxillaire | en haut,haut,du haut,mâchoire du haut,**supérieur,supérieure**,arcade supérieure,arc supérieur | en haut,haut,du haut,mâchoire du haut,arcade supérieure,arc supérieur |
| supérieur | du haut,en haut,**maxillaire**,sus | sus |
| mandibulaire | bas,en bas,du bas,mâchoire du bas,**inférieur,inférieure**,arcade inférieure,arc inférieur | bas,en bas,du bas,mâchoire du bas,arcade inférieure,arc inférieur |
| inférieur | du bas,en bas,**mandibulaire**,sous | sous |

Note : "du haut/en haut" restent dans maxillaire (chargé avant supérieur), "du bas/en bas" restent dans mandibulaire. C'est le comportement souhaité car en orthodontie "du haut" = maxillaire.

**Résultat** :
- "crowding maxillaire" → canonique `maxillaire` ✅
- "procheilie supérieure" → canonique `supérieur` ✅ (correct pour les lèvres)
- "arcade du haut" → canonique `maxillaire` ✅
- Plus de collision circulaire ✅

---

## 4. Correctif C — Colonnes `as` vides (tags_v2.csv)

### Méthode

Chaque tag a été évalué : quels adjectifs un orthodontiste utiliserait-il cliniquement avec ce tag ?

### Priorité HAUTE — Impact direct sur la recherche (13 tags)

| Tag | cat | `as` proposé | Justification |
|---|---|---|---|
| crowding | pathologie | `maxillaire,mandibulaire,antérieur,sévère,modéré` | "crowding mandibulaire sévère" très fréquent |
| supraclusion | pathologie | `antérieur,sévère,modéré` | "supraclusion antérieure sévère" très fréquent |
| occlusion croisée | pathologie | `antérieur,postérieur,latéral,gauche,droit,unilatéral,bilatéral,sévère,modéré` | Localisation essentielle |
| occlusion inversée | pathologie | `antérieur,postérieur,latéral,sévère,modéré` | Idem |
| inclusion | pathologie | `maxillaire,mandibulaire` | "canine incluse maxillaire" très fréquent |
| protrusion | pathologie | `maxillaire,mandibulaire,sévère,modéré` | "protrusion maxillaire sévère" courant |
| agénésie | pathologie | `maxillaire,mandibulaire,latéral,bilatéral,unilatéral` | "agénésie des latérales maxillaires" très courant |
| ddm | pathologie | `maxillaire,mandibulaire,sévère,modéré` | "ddm mandibulaire sévère" courant |
| classe ii squelettique | pathologie | `sévère,modéré` | Alignement avec classe iii squelettique qui a déjà sévère,modéré |
| déviation mandibulaire | pathologie | `droit,gauche,sévère,modéré` | Alignement avec déviation maxillaire |
| latérodéviation | pathologie | `droit,gauche,sévère,modéré` | Direction essentielle |
| apnée du sommeil | pathologie | `sévère,modéré` | "apnée du sommeil sévère" courant |
| asymétrie faciale | pathologie | `sévère,modéré,droit,gauche` | "asymétrie faciale sévère" courant |

### Priorité MOYENNE — Combinaisons cliniques courantes (14 tags)

| Tag | cat | `as` proposé | Justification |
|---|---|---|---|
| dent surnuméraire | pathologie | `maxillaire,mandibulaire` | Localisation utile |
| ectopie | pathologie | `maxillaire,mandibulaire` | "ectopie canine maxillaire" |
| luxation méniscale | pathologie | `réductible,bilatéral,unilatéral,droit,gauche` | "luxation méniscale réductible" classique |
| macrognathie | pathologie | `maxillaire,mandibulaire` | Obligatoire cliniquement |
| micrognathie | pathologie | `maxillaire,mandibulaire` | Idem |
| maladie parodontale | pathologie | `sévère,modéré` | Classification parodontale |
| gingivite | pathologie | `sévère,modéré` | Gradation clinique |
| récession gingivale | pathologie | `sévère,modéré,maxillaire,mandibulaire` | Localisation + sévérité |
| résorption radiculaire | pathologie | `sévère,modéré` | Gradation diagnostique |
| dtm | pathologie | `sévère,modéré,droit,gauche,bilatéral` | "dtm sévère bilatéral" |
| dysfonction linguale | pathologie | `sévère,modéré` | Gradation |
| canine | anatomie | `maxillaire,mandibulaire,inclus,ectopique` | "canine maxillaire incluse" très fréquent |
| molaire | anatomie | `maxillaire,mandibulaire` | Localisation standard |
| incisives latérales | anatomie | `maxillaire,mandibulaire` | "agénésie incisives latérales maxillaires" |

### Priorité BASSE — Utiles mais rares (10 tags)

| Tag | cat | `as` proposé |
|---|---|---|
| ankylose | pathologie | `maxillaire,mandibulaire` |
| dysplasie | pathologie | `sévère,modéré` |
| macrodontie | pathologie | `maxillaire,mandibulaire` |
| microdontie | pathologie | `maxillaire,mandibulaire` |
| récidive | pathologie | `sévère,modéré` |
| respiration buccale | pathologie | `sévère,modéré` |
| fracture | pathologie | `maxillaire,mandibulaire` |
| édentation | pathologie | `maxillaire,mandibulaire,total,complet` |
| proglissement | pathologie | `droit,gauche` |
| ostéotomie | traitement | `maxillaire,mandibulaire` |

### Tags sans adjectifs — NORMAL (pas de correction)

Les tags suivants n'ont pas d'adjectifs autorisés et c'est **correct** :

**Anatomie** : atm, mandibule normopositionnée, maxillaire normopositionné, incisives palatinées, prémolaire  
**Biomécanique** : alignement, arc orthodontique, ingression, linguo-version, nivellement, rotation, torque, translation, transposition, version, vestibulo-version, égression  
**Diagnostic** : analyse de bolton, céphalométrie, consultation, contrôle, empreinte, panoramique, photographie clinique, scanner, scanner intra-oral  
**Fonction** : aéro, croissance, dentition mixte/permanente/temporaire, déglutition, engrènement, mastication, phonation, succion, ventilation nasale  
**Gestion** : ef, favori, urgence  
**Matériau** : céramique, composite, métal, niti  
**Traitement** : activateur, arc transpalatin, auxiliaire, bagues, bielles, contention (déjà fixe,amovible), débandage, détartrage, distalisation, facette, implant, mainteneur d'espace, mésialisation, minivis, orthodontie linguale, pendulum, plaques (amovible/papillon/y/éventail), propulsor, quad helix, stripping, traitement interceptif, élastiques intermaxillaires  
**Pathologie** : arthrite, arthrose, caries dentaires, claquement articulaire, diabète, fluorose, interposition linguale, luxation, nécrose pulpaire, onychophagie, ressaut articulaire, érosion, éruption ectopique, wits

### Tag diabète — Anomalie

```
diabète;;;diabétique,diabétiques;pathologie
```

Le **genre manque** (devrait être `m`). Correction : `diabète;m;;diabétique,diabétiques;pathologie`

---

## 5. Résumé des corrections

| Fichier | Type | Nb corrections |
|---|---|---|
| tags_v2.csv → tags.csv | Retrait patterns conflictuels (bipro, rétroalvéolie) | 2 |
| tags_v2.csv → tags.csv | Ajout adjectifs autorisés (colonnes `as`) | 37 |
| tags_v2.csv → tags.csv | Genre manquant (diabète) | 1 |
| adjectifs_v2.csv → adjectifs.csv | Retrait cross-patterns (4 adjectifs) | 4 |
| **Total** | | **44 corrections** |
