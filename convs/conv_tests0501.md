# Synthèse de conversation : tests0501

## Informations générales
- **Date de création** : 04/01/2026
- **Objet** : Tests de l'ensemble du système KITVIEW selon Prompt_scenarios_test.md

---

## Échanges

### 04/01/2026 19:02 - Problèmes lors des tests initiaux

**Question de Thierry :**
1. La vue d'ensemble de l'architecture ne mentionne pas `trouve.py`
2. L'option `--model` n'existe pas dans `detia.py` pour tester différents moteurs IA
   - Tentatives échouées : `--model sonnet`, `--model deepseekr1`, `--model eden/deepseekr1`
   - Erreur : `unrecognized arguments: --model`

**Analyse de Claude :**
1. **Architecture** : trouve.py se positionne entre search.py et detall.py (niveau 3.5)
2. **Option --model** : N'existe pas car syntaxe positionnelle utilisée → `python detia.py "question" sonnet`
3. **Fichier ia.csv** : Contient bien les modèles demandés avec 5 modèles actifs

**Résolution :**
- [x] Position de `trouve.py` clarifiée
- [x] Syntaxe --model : conservée positionnelle (doc à corriger)

---

## Fichiers à créer/modifier

| Fichier | Action | Statut |
|---------|--------|--------|
| detiabrut.py | Nouvelle syntaxe +/- | ✓ Créé |
| webparams.html | Adapter interface pour +/- | ✓ Modifié V1.1.0 |
| Prompt_detiabruthelp.md | Guide d'utilisation | ✓ Créé |
| detia.py | Ajout synonymes et angles SNA/SNB | ✓ Modifié V1.0.26 |
| Architecture (schéma) | Ajouter trouve.py entre search et detall | À faire en fin de conversation |
| Prompt_scenarios_test.md | Corriger syntaxe --model → positionnelle + tests detiabrut pertinents | À faire en fin de conversation |

---

## Architecture mise à jour (trouve.py ajouté)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NIVEAU 4 : search.py                                │
│    Résolution sémantique multilingue via glossaire.csv                      │
│    Question (xx) → Question hybride (fr) → trouve.py                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                       NIVEAU 3.5 : trouve.py                                │
│    Détection en français - Appelle detia.py ou detall.py                    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
┌─────────────────────────────────────────────────────────────────────────────┐
│                         NIVEAU 3 : detall.py                                │
│    Pipeline V2 : detcount → detangles → dettags → detage                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

### 04/01/2026 19:08 - Analyse de detia.py

**Fichier reçu :** detia.py V1.0.25 (830 lignes)

**Constat :**
Le code utilise `_identifier_argument()` (lignes 717-725) pour identifier automatiquement la nature de chaque argument positionnel :
- Si se termine par `.csv` → fichier batch
- Si présent dans `ia.csv` → moteur IA
- Si présent dans langues actives → langue
- Sinon → question

**Syntaxe fonctionnelle actuelle :**
```bash
python detia.py "bruxisme sévère avec classe ii" sonnet
python detia.py "question" deepseekr1 fr
python detia.py -l   # Liste les moteurs disponibles
```

---

### 04/01/2026 19:18 - Clarifications et tests 3.3-3.4

**Position de trouve.py clarifiée :**
- Appelé par `search.py` après traduction en français
- Fait la détection avec `detia` ou `detall`
- **Position** : Entre search.py (niveau 4) et detall.py (niveau 3)

**Décision syntaxe --model :** Conservée telle quelle (positionnelle). Doc de test à modifier à la fin.

**Tests réalisés :**
| Test | Commande | Résultat |
|------|----------|----------|
| 3.3 verbose | `python detia.py "patients de moins de 30 ans avec béance" --verbose` | ✓ OK - 2 critères (tag béance + age < 30) |
| 3.4 brut vs detia | `python detiabrut.py "bruxisme sévère" brut/detia` | ✓ OK - Résultats similaires |

**Note pour Prompt_scenarios_test.md :**
Les tests de désactivation partielle (detiabrut) nécessitent des questions où le mapping fait une différence :
- Synonymes : `"occlusion inversée"` → articulé inversé
- Formes fléchies : `"classes II sévères"` → classe ii d'angle, sévère
- Patterns : `"CL2"` → classe ii d'angle
- Multilingue : `"severe overbite"` → supraclusion sévère

---

### 04/01/2026 19:35 - Analyse comportement detiabrut.py

**Constat de Thierry :** Quand on passe `tags` ou `adjs`, ça semble ACTIVER ces référentiels au lieu de les désactiver.

**Analyse des résultats :**
| Question | Mode brut | Mode avec arg | Différence |
|----------|-----------|---------------|------------|
| "grincement sévère" | Grincement | bruxisme | tags fait le mapping |
| "extraction dentaire important" | Extraction Dentaire, Important | avulsion, sévère | tags+adjs font le mapping |

**Diagnostic :** L'affichage `options_desactivees` est trompeur. La logique réelle semble être :
- `brut` = IA seule, aucun référentiel
- `detia` = tous les référentiels actifs
- `tags`/`adjs` = active CE référentiel dans le prompt

**Exemples discriminants proposés par Claude :**
1. TAGS : "grincement" → bruxisme
2. ADJS : "importante" → sévère  
3. AGES : "trentenaires" → age 30-39
4. ANGLES : "ANB de 6" → classe ii squelettique
5. MAPPING : "BRUXISME" → bruxisme (canonisation)

**En attente :** Décision de Thierry sur la clarification de l'interface CLI

---

### 04/01/2026 19:52 - Création nouvelle syntaxe detiabrut +/-

**Demande :** Option B choisie - nouvelle syntaxe avec +/- pour les référentiels

**Fichiers créés :**

1. **detiabrut.py** (nouvelle version) :
   - Syntaxe `+xxx` pour activer un référentiel
   - Syntaxe `-xxx` pour désactiver un référentiel
   - `all` = tout actif (défaut)
   - `none` = tout désactivé
   - Rétrocompatibilité avec `detia` et `brut`

2. **webparams.html** (V1.1.0) :
   - Boutons "Tout activer (all)" et "Tout désactiver (none)"
   - Commande CLI générée avec la nouvelle syntaxe +/-
   - Logique intelligente : affiche `-xxx` si peu de désactivations, sinon `none +xxx`

3. **Prompt_detiabruthelp.md** :
   - Guide complet d'utilisation
   - Exemples discriminants par référentiel
   - Tableau de configuration

**Explication de `+tags -adjs` :**
- Base de départ : tout ACTIF
- `+tags` : active tags (redondant mais explicite)
- `-adjs` : désactive adjs
- Résultat : tags=ON, adjs=OFF, ages=ON, angles=ON, mapping=ON

**Exemples de la nouvelle syntaxe :**
```bash
python detiabrut.py "question" all           # Tout actif
python detiabrut.py "question" none          # Tout désactivé
python detiabrut.py "question" -tags         # Sans liste tags
python detiabrut.py "question" -tags -mapping # Sans tags ni mapping
python detiabrut.py "question" none +mapping  # Brut + mapping seul
```

---

## Prompts de recréation des fichiers

### detiabrut.py
**Prompt :** Crée une version modifiée de detia.py appelée detiabrut.py qui permet de configurer les référentiels utilisés par l'IA avec la syntaxe suivante :
- `+xxx` active le référentiel xxx
- `-xxx` désactive le référentiel xxx  
- `all` active tout (défaut)
- `none` désactive tout

Les référentiels sont : tags, adjs, ages, angles, mapping

Le fichier doit :
1. Importer les fonctions de detia.py
2. Permettre de construire un prompt système avec/sans chaque référentiel
3. Permettre le mapping canonique optionnel
4. Afficher la configuration dans la signature auteur
5. Supporter le mode batch

**PJ nécessaires :** detia.py, ia.csv

### detia.py V1.0.26
**Prompt :** Modifie detia.py pour améliorer la concordance avec detall en ajoutant :
1. Extraction des synonymes/patterns depuis tags.csv (colonne pts) pour les inclure dans le prompt IA
2. Section SYNONYMES IMPORTANTS dans le prompt avec : tong e → dysfonction linguale, rétrusion → classe ii d'angle, spacing → diastème, etc.
3. Angles SNA et SNB complets dans le prompt (pas seulement ANB) avec les seuils normaux et pathologiques
4. Exemples concrets pour les angles

**PJ nécessaires :** detia.py original, tags.csv

### webparams.html
**Prompt :** Modifie webparams.html pour adapter la section detiabrut à la nouvelle syntaxe +/- :
- Remplacer les boutons "detia/brut" par "all/none"
- Modifier updateDetiabrut() pour générer la syntaxe `-xxx` ou `none +xxx`
- Modifier setDetiabrut() pour accepter 'all'/'none'

**PJ nécessaires :** webparams.html original

### Prompt_detiabruthelp.md
**Prompt :** Crée un guide d'utilisation pour detiabrut.py avec :
- Explication de chaque référentiel
- Syntaxe CLI avec +/-
- Exemples discriminants par référentiel montrant l'impact de chaque option
- Tableau des signatures JSON

**PJ nécessaires :** Aucune

---

### 04/01/2026 20:52 - Analyse audit concordance et correction detia.py

**Demande :** Analyse des écarts entre detall et detia sur l'audit 25000 patients

**Résultats de l'audit initial :**
- Concordance listcount : 99.0%
- Concordance tags exacte : 83.2%
- Concordance tags Jaccard : 87.8%

**Problèmes identifiés :**

| Catégorie | Exemple | detall | detia | Cause |
|-----------|---------|--------|-------|-------|
| Pattern non reconnu | `tong e` | dysfonction linguale | rien | Prompt IA sans synonymes |
| Pattern non reconnu | `rétrusion` | classe ii d'angle | rien | Prompt IA sans synonymes |
| Pattern non reconnu | `spacing` | diastème | rien | Prompt IA sans synonymes |
| Angle SNA ignoré | `SNA = 84` | position maxillaire normale | rien | SNA absent du prompt |
| Angle SNB ignoré | `SNB de 81` | position mandibulaire normale | rien | SNB absent du prompt |
| Angle SNB erroné | `SNB > 84` | prognathisme mandibulaire | **classe iii squelettique** | Confusion IA |

**Fichier modifié : detia.py V1.0.26**

Modifications apportées :
1. **Chargement des synonymes** : `_charger_tags_csv()` retourne maintenant aussi `tags_synonymes`
2. **Section SYNONYMES IMPORTANTS** ajoutée au prompt IA avec les patterns clés
3. **Section ANGLES complète** avec SNA et SNB (pas seulement ANB)
4. **Exemples concrets** pour les angles dans le prompt

**Nouveaux synonymes dans le prompt :**
```
tong e → dysfonction linguale
interposition linguale → dysfonction linguale
rétrusion → classe ii d'angle
spacing → diastème
fil qui pique → arc
grincement → bruxisme
extraction dentaire → avulsion
```

**Nouvelles règles d'angles :**
```
| Angle | Condition | Valeur | Tag résultant |
|-------|-----------|--------|---------------|
| SNA   | =         | 79-85  | position maxillaire normale |
| SNA   | >         | 85     | prognathisme maxillaire |
| SNA   | <         | 79     | rétrognathisme maxillaire |
| SNB   | =         | 77-83  | position mandibulaire normale |
| SNB   | >         | 83     | prognathisme mandibulaire |
| SNB   | <         | 77     | rétrognathisme mandibulaire |
```

**Note sur tags.csv :** Les patterns "inclus/incluse" ont été retirés du tag "inclusion" par Thierry.

---

## Notes
- Le fichier `ia.csv` V1.0.12 est correctement structuré avec 14 modèles dont 5 actifs
- La colonne `via` détermine le routage : `openai` (direct) ou `eden` (via Eden AI gateway)
