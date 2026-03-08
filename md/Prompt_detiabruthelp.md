# Prompt Prompt_detiabruthelp V1.0.0 - 05/01/2026 20:26:46

# Guide d'utilisation de detiabrut.py

## Objectif

`detiabrut.py` permet de **mesurer l'impact de chaque référentiel** sur la qualité de la détection IA. En activant/désactivant sélectivement les référentiels, on peut comparer :

- Ce que l'IA détecte **sans aide** (ses connaissances générales)
- Ce que l'IA détecte **avec les référentiels** (liste de tags, adjectifs, etc.)
- L'impact du **mapping** (conversion détecté → canonique)

---

## Référentiels disponibles

| Référentiel | Description | Impact |
|-------------|-------------|--------|
| `tags` | Liste des 129 tags pathologiques injectée dans le prompt | L'IA utilise cette liste pour détecter les termes exacts |
| `adjs` | Liste des 40 adjectifs injectée dans le prompt | L'IA utilise cette liste pour qualifier les pathologies |
| `ages` | Patterns âge/sexe (moins de X ans, femme, etc.) | Détection des critères démographiques |
| `angles` | Seuils ANB/SNA/SNB → classes squelettiques | Conversion automatique des angles en pathologies |
| `mapping` | Post-traitement détecté → forme canonique | "grincement" → "bruxisme", "important" → "sévère" |

---

## Syntaxe CLI

```
python detiabrut.py "question" [options] [moteur] [langue]
```

### Options de configuration

| Syntaxe | Effet |
|---------|-------|
| `+xxx` | Active le référentiel xxx |
| `-xxx` | Désactive le référentiel xxx |
| `all` | Active tous les référentiels (défaut) |
| `none` | Désactive tous les référentiels |

**Par défaut** : Tous les référentiels sont **ACTIFS** (comportement identique à `detia.py`)

### Compatibilité ancienne syntaxe

Pour assurer la rétrocompatibilité :
- `detia` = alias de `all`
- `brut` = alias de `none`

---

## Exemples de base

### Tout actif (défaut = detia.py)
```bash
python detiabrut.py "bruxisme sévère"
python detiabrut.py "bruxisme sévère" all
```

### Tout désactivé (IA brute)
```bash
python detiabrut.py "bruxisme sévère" none
```

### Désactivation sélective
```bash
python detiabrut.py "grincement" -tags           # Sans liste tags
python detiabrut.py "béance importante" -adjs    # Sans liste adjectifs
python detiabrut.py "bruxisme" -tags -mapping    # Sans tags ni mapping
```

### Activation sélective depuis none
```bash
python detiabrut.py "bruxisme" none +mapping     # Brut + mapping seul
python detiabrut.py "bruxisme" none +tags        # Brut + tags seul
```

### Avec moteur IA spécifique
```bash
python detiabrut.py "bruxisme" -tags sonnet
python detiabrut.py "bruxisme" none deepseekr1
```

### Mode batch
```bash
python detiabrut.py tests.csv none
python detiabrut.py tests.csv -tags -mapping sonnet
```

---

## Exemples discriminants par référentiel

Ces exemples montrent des cas où la présence/absence du référentiel change le résultat.

### 1. TAGS - Synonymes de pathologies

Le référentiel `tags` contient la liste des pathologies et leurs patterns/synonymes.

```bash
# Avec tags : l'IA connaît la liste exacte → trouve "bruxisme"
python detiabrut.py "grincement sévère" all
# → bruxisme [sévère]

# Sans tags : l'IA utilise ses connaissances générales
python detiabrut.py "grincement sévère" -tags
# → Grincement [Sévère]  (si mapping aussi désactivé)
# → bruxisme [sévère]    (si mapping actif, convertit)

# VRAIMENT sans aide : ni tags ni mapping
python detiabrut.py "grincement sévère" none
# → Grincement [Sévère]  (title case, pas de mapping)
```

**Autres tests discriminants pour TAGS :**
```bash
python detiabrut.py "grince des dents" all      # → bruxisme
python detiabrut.py "grince des dents" none     # → Grincement Des Dents

python detiabrut.py "dents qui se chevauchent" all   # → encombrement
python detiabrut.py "dents qui se chevauchent" none  # → Chevauchement Dentaire (?)
```

### 2. ADJS - Synonymes d'adjectifs

Le référentiel `adjs` contient les adjectifs et leurs formes (masculin, féminin, pluriel).

```bash
# Avec adjs : "importante" → "sévère" (forme canonique)
python detiabrut.py "béance importante" all
# → béance [sévère]

# Sans adjs : l'IA garde le terme détecté
python detiabrut.py "béance importante" -adjs
# → béance [Important]  (ou sévère si l'IA devine)

# Test avec forme fléchie
python detiabrut.py "béances sévères bilatérales" all
# → béance [sévère, bilatéral]

python detiabrut.py "béances sévères bilatérales" none
# → Béances [Sévères, Bilatérales]
```

**Autres tests discriminants pour ADJS :**
```bash
python detiabrut.py "encombrement important" all    # → encombrement [sévère]
python detiabrut.py "encombrement important" none   # → Encombrement [Important]

python detiabrut.py "classe II légère" all          # → classe ii d'angle [léger]
python detiabrut.py "classe II légère" none         # → Classe II [Légère]
```

### 3. AGES - Patterns démographiques

Le référentiel `ages` permet de détecter les critères d'âge et de sexe.

```bash
# Avec ages : détection des patterns
python detiabrut.py "bruxisme chez les trentenaires" all
# → bruxisme, age entre 30-39

# Sans ages : patterns ignorés
python detiabrut.py "bruxisme chez les trentenaires" -ages
# → bruxisme (pas de critère âge)

# Test avec sexe
python detiabrut.py "béance chez les femmes" all
# → béance, sexe = F

python detiabrut.py "béance chez les femmes" -ages
# → béance (pas de critère sexe)
```

**Autres tests discriminants pour AGES :**
```bash
python detiabrut.py "patients de moins de 12 ans" all    # → age < 12
python detiabrut.py "adultes avec béance" all            # → age >= 18, béance
python detiabrut.py "enfants avec encombrement" all      # → age < 18, encombrement
```

### 4. ANGLES - Conversion céphalométrique

Le référentiel `angles` convertit les valeurs ANB/SNA/SNB en classes squelettiques.

```bash
# Avec angles : ANB > 4 → classe ii squelettique
python detiabrut.py "patient avec ANB de 6 degrés" all
# → classe ii squelettique

# Sans angles : pas de conversion
python detiabrut.py "patient avec ANB de 6 degrés" -angles
# → (rien détecté ou ANB brut selon l'IA)

# Autre exemple
python detiabrut.py "ANB négatif" all
# → classe iii squelettique

python detiabrut.py "ANB négatif" -angles
# → (pas de conversion automatique)
```

### 5. MAPPING - Post-traitement canonique

Le `mapping` est le post-traitement qui convertit les termes détectés vers leur forme canonique.

```bash
# Avec mapping : "grincement" → "bruxisme" via le dictionnaire
python detiabrut.py "grincement" -tags
# L'IA détecte "grincement", le mapping le convertit en "bruxisme"
# → bruxisme

# Sans mapping : pas de conversion post-détection
python detiabrut.py "grincement" -tags -mapping
# L'IA détecte "grincement", affiché en title case
# → Grincement

# Différence de casse
python detiabrut.py "BRUXISME" all
# → bruxisme (forme canonique minuscule)

python detiabrut.py "BRUXISME" none
# → Bruxisme (title case)
```

---

## Combinaisons intéressantes

### Test de l'IA pure vs IA assistée

```bash
# Comparer la même question avec et sans aide
python detiabrut.py "extraction dentaire importante chez un enfant" all
# → avulsion [sévère], age < 18

python detiabrut.py "extraction dentaire importante chez un enfant" none
# → Extraction Dentaire [Important] (pas de mapping vers avulsion)
```

### Test du mapping seul

```bash
# L'IA sans liste mais avec mapping post-traitement
python detiabrut.py "grincement sévère" none +mapping
# → bruxisme [sévère] (si le mapping trouve la correspondance)
```

### Test des listes sans mapping

```bash
# L'IA avec listes mais sans conversion canonique
python detiabrut.py "grincement sévère" -mapping
# Les listes aident l'IA à détecter, mais pas de normalisation
```

---

## Signature JSON

Le champ `auteur` dans le résultat JSON indique la configuration utilisée :

| Configuration | Signature auteur |
|---------------|------------------|
| Tout actif | `openai/gpt-4.1-mini` |
| Tout désactivé | `openai/gpt-4.1-mini [none]` |
| Tags désactivé | `openai/gpt-4.1-mini [-tags]` |
| Tags et mapping désactivés | `openai/gpt-4.1-mini [-mapping,-tags]` |
| Brut + mapping | `openai/gpt-4.1-mini [none,+mapping]` |

---

## Interface web (webparams.html)

L'interface web permet de configurer visuellement les référentiels :

- Checkboxes pour chaque référentiel (cochée = actif)
- Boutons "Tout activer (all)" et "Tout désactiver (none)"
- Affichage de la commande CLI équivalente en temps réel

---

## Conseils d'utilisation

1. **Pour comparer les approches** : Lancer la même question en `all` puis `none` et comparer les résultats

2. **Pour diagnostiquer un problème** : Désactiver les référentiels un par un pour identifier lequel pose problème

3. **Pour tester l'IA brute** : Utiliser `none` pour voir ce que l'IA détecte avec ses seules connaissances

4. **Pour le batch** : Le nom du fichier de sortie inclut la configuration (ex: `tests_out_mtags.csv` pour `-tags`)

---

## Fichiers de référence utilisés

| Fichier | Référentiel | Colonnes clés |
|---------|-------------|---------------|
| `refs/tags.csv` | tags, mapping | t, gn, as, pts |
| `refs/adjectifs.csv` | adjs, mapping | a, f, mp, fp, pas |
| `refs/ages.csv` | ages | patterns âge/sexe |
| `refs/angles.csv` | angles | seuils ANB/SNA/SNB |
