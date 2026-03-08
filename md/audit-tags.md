# Audit de tags.csv — Analyse à la lumière du Knowledge Graph Orthodontie

**143 tags · 41 adjectifs · ~1 400 patterns**

---

## 1. Patterns en double (même pattern → plusieurs tags)

C'est le problème le plus critique : si un mot-clé matche deux tags, le système ne sait pas lequel choisir.

| Pattern en conflit | Tag A | Tag B | Recommandation |
|---|---|---|---|
| `appareil dentaire` | activateur | bagues | Retirer d'`activateur` (trop générique, le grand public pense aux bagues) |
| `plaque orthodontique` | activateur | plaque amovible | Retirer d'`activateur` — une plaque orthodontique n'est pas forcément un activateur |
| `dent bloquée` | enclavement | inclusion | Fusionner enclavement dans inclusion (voir §6) |
| `dent qui ne sort pas` | enclavement | inclusion | Idem — fusionner |
| `deglutition atypique` | déglutition | dysfonction linguale | Retirer de `déglutition` — c'est spécifiquement une dysfonction |
| `interposition linguale` | béance | dysfonction linguale | Retirer de `béance` — c'est une *cause* de béance, pas un synonyme |
| `disjoncteur` / `disjoncteur palatin` | malocclusion | quad helix | Retirer de `malocclusion` — le disjoncteur est un *traitement*, pas une malocclusion |
| `dysharmonie` | ddm | wits | Clarifier : garder dans `ddm` (terme générique) ; dans `wits` utiliser uniquement `dysharmonie maxillo-mandibulaire` |
| `parodontie` | maladie parodontale | maladie parodontale | Doublon interne — apparaît 2× dans le même tag |

---

## 2. Patterns "fourre-tout" dans `malocclusion`

Le tag `malocclusion` est devenu un **sac de nœuds** avec des patterns qui appartiennent à d'autres catégories :

| Pattern dans malocclusion | Devrait être dans | Raison |
|---|---|---|
| `endoalvéolie` | **nouveau tag** ou `occlusion croisée` | C'est une endoalvéolie, pas une malocclusion générique |
| `rétroclusie` | `classe ii d'angle` ou `supraclusion` | Terme spécifique |
| `voûte palatine` / `voûte` | **anatomie** (pas un tag de pathologie) | C'est une structure anatomique |
| `disjoncteur` / `disjoncteur palatin` | `quad helix` | C'est un traitement |
| `ressaut` / `ressauts` | `ressaut articulaire` | Confusion avec le ressaut ATM |
| `ressort` / `ressorts` | `arc orthodontique` ou nouveau tag biomécanique | C'est un dispositif, pas une malocclusion |
| `underbite` | `classe iii d'angle` | Synonyme classique de classe III |
| `décalage` | Trop vague pour un seul tag | À supprimer ou qualifier (décalage dentaire, squelettique…) |

---

## 3. Qualificatifs utilisés mais NON DÉFINIS dans adjectifs.csv

Ces adjectifs sont référencés dans tags.csv mais n'existent pas dans adjectifs.csv (donc pas de gestion de genre/synonymes) :

| Adjectif manquant | Tag(s) concerné(s) | Action |
|---|---|---|
| `ectopique` | éruption | **Ajouter** dans adjectifs.csv |
| `retardé` | éruption | **Ajouter** |
| `labiale` | fente | **Ajouter** (+ labio-palatine, palatine) |
| `palatine` | fente | **Ajouter** |
| `labio-palatine` | fente | **Ajouter** |
| `chirurgical` | gouttière | **Ajouter** |
| `invisible` | gouttière | **Ajouter** |
| `supérieur` | procheilie, rétrocheilie | **Ajouter** |
| `inférieur` | procheilie, rétrocheilie | **Ajouter** |
| `droite` | déviation maxillaire | Existe déjà comme `droit` dans adjectifs.csv → utiliser la forme masculine `droit` |
| `antérieure` | déviation maxillaire | Existe déjà comme `antérieur` → utiliser la forme masculine |
| `temporo mandibulaire(s)` | dtm | Structure anormale — `temporo` est défini comme adjectif mais ses "synonymes" sont bizarres |

---

## 4. Espaces parasites (~70 occurrences)

De nombreux patterns et qualificatifs contiennent des **espaces en début** (` plaque`, ` sévère`, `  VENTILATOIRE`). Ceci peut casser le matching. Tags les plus affectés :

- `malocclusion` (10 espaces parasites)
- `activateur` (4)
- `béance` (4)
- `aéro` (4 + majuscules incohérentes)
- `bagues` (3)
- `dtm` (5 + qualificatif vide)
- `récession gingivale` (3)

**Action** : Trimmer systématiquement tous les champs.

---

## 5. Références circulaires

| Pattern | Est aussi un tag | Dans le tag |
|---|---|---|
| `interposition linguale` | ✅ tag existant | béance, dysfonction linguale |

Si `interposition linguale` est détecté, faut-il créer le tag `interposition linguale` OU le tag parent (`béance`) ? Il faut choisir : soit c'est un tag autonome, soit c'est un pattern d'un autre tag — pas les deux.

---

## 6. Tags à fusionner ou mieux différencier

### `enclavement` ↔ `inclusion`
Cliniquement quasi-synonymes (dent qui ne peut pas faire son éruption). **Recommandation** : fusionner dans `inclusion` et ajouter les patterns d'enclavement.

### `supraclusion` ↔ `supraposition`
- `supraclusion` = recouvrement **vertical** excessif (deep bite / overbite) ✅
- `supraposition` = mélange confus de décalage horizontal, overjet, ET supra-éruption

**Recommandation** : Scinder `supraposition` en :
- Les patterns d'**overjet** (`over jet`, `overjet`, `surplomb`, `surjet`) → dans un tag `overjet` dédié
- Les patterns de **supra-éruption** (`supra-éruption`, `éruption excessive`, `dent trop haute`) → dans un tag `supra-éruption` ou dans `égression`

### `dtm` — tag mal structuré
Qualificatifs incohérents (contient `temporo mandibulaire` comme qualificatif plutôt que comme pattern). `dtm` et `atm` se chevauchent aussi (DTM = dysfonction temporo-mandibulaire, ATM = articulation). **Recommandation** : réorganiser — `atm` = anatomie, `dtm` = pathologie.

---

## 7. Tags manquants vs Knowledge Graph

Le knowledge graph identifie des domaines non couverts ou sous-couverts dans tags.csv :

### Biomécanique (peu représentée)
| Tag à ajouter | Patterns suggérés |
|---|---|
| `ancrage` | ancrage dentaire, ancrage orthodontique, ancrage cortical, ancrage direct, ancrage indirect |
| `force orthodontique` | force légère, force continue, force intermittente, force de traction |
| `nivellement` | leveling, mise à niveau, alignement vertical |

### Diagnostic (partiellement couvert)
| Tag à ajouter | Patterns suggérés |
|---|---|
| `analyse de Bolton` | bolton, discrepance de Bolton, rapport Bolton |
| `indice de Little` | little's irregularity index, indice d'irrégularité |
| `photographie clinique` | photo intra-orale, photo extra-orale, photo de face, photo de profil |

### Appareillage (lacunes)
| Tag à ajouter | Patterns suggérés |
|---|---|
| `lingual` | orthodontie linguale, bagues linguales, appareil lingual, incognito |
| `auxiliaire` | ressort ouvert, ressort fermé, chaînette élastique, chaînette, power chain |
| `arc transpalatin` | transpalatin, atp, barre transpalatine |

---

## 8. Incohérences de casse et de format

- `aéro` : patterns en MAJUSCULES (`FONCTION VENTILATOIRE`, `RESPIRATOIRE`) alors que tout le reste est en minuscules
- `bipro` : `PRO INCLINAISON` en majuscules
- `quad helix` : `PALATOVERSION` en majuscules
- Certains patterns contiennent des articles définis/indéfinis inconsistants

---

## 9. Proposition de catégorisation (inspirée du Knowledge Graph)

Pour faciliter la maintenance, chaque tag pourrait porter une **catégorie** (nouveau champ) :

| Catégorie | Nb tags actuels | Exemples |
|---|---|---|
| **pathologie** | ~45 | malocclusion, béance, classe ii d'angle, crowding, agénésie |
| **traitement** | ~30 | bagues, gouttière, quad helix, stripping, chirurgie |
| **anatomie** | ~15 | canine, molaire, prémolaire, mandibule, atm |
| **diagnostic** | ~10 | céphalométrie, panoramique, scanner, empreinte |
| **biomécanique** | ~15 | torque, version, translation, distalisation, rotation |
| **fonction** | ~10 | déglutition, phonation, mastication, respiration buccale |
| **gestion** | ~5 | consultation, contrôle, urgence, favori |
| **matériau** | ~5 | niti, métal, céramique, composite |

Cela permettrait de valider qu'un pattern de type "traitement" n'est pas rangé dans un tag de type "pathologie" (comme `disjoncteur` dans `malocclusion`).

---

## Résumé des actions prioritaires

1. **🔴 Critique** — Résoudre les 9 doublons de patterns (ambiguïté de matching)
2. **🔴 Critique** — Nettoyer les ~70 espaces parasites (trim automatique)
3. **🟠 Important** — Ajouter les 9 adjectifs manquants dans adjectifs.csv
4. **🟠 Important** — Éclater le tag `malocclusion` fourre-tout
5. **🟠 Important** — Scinder `supraposition` (overjet vs supra-éruption)
6. **🟡 Recommandé** — Fusionner `enclavement` → `inclusion`
7. **🟡 Recommandé** — Normaliser la casse (tout en minuscules)
8. **🟢 Amélioration** — Ajouter les tags manquants (biomécanique, diagnostic, appareillage)
9. **🟢 Amélioration** — Ajouter un champ catégorie pour la gouvernance
