# Prompt de régénération MD → Slides-Ready

## Instructions

Tu vas régénérer un document technique Markdown en y ajoutant des **métadonnées de slides** qui faciliteront sa conversion automatique en présentation Reveal.js.

Le contenu technique reste IDENTIQUE. Tu ajoutes uniquement des balises de métadonnées en commentaires HTML.

---

## Format des métadonnées à ajouter

### 1. En-tête du document (OBLIGATOIRE)

Au tout début du fichier, après le titre principal :

```markdown
<!-- PRESENTATION_META
titre_court: "Titre court pour la slide de titre"
sous_titre: "Sous-titre explicatif"
duree_estimee: "20min"
niveau: "intermédiaire"
audience: "Développeurs, architectes"
fichiers_concernes: "fichier1.py, fichier2.py"
emoji_principal: "🔍"
-->
```

### 2. Avant chaque section majeure (## Titre)

```markdown
<!-- SLIDE
id: "section-unique-id"
titre: "Titre de la slide"
template: "tableau|2colonnes|schema|code|timeline|synthese|titre-section"
emoji: "📊"
timing: "3min"
transition: "slide|fade|zoom"
-->

## Titre de la section

<!-- KEY: Message clé en une phrase (ce que l'audience doit retenir) -->

<!-- QUESTION: Question de discussion pour l'audience ? -->
```

### 3. Pour les schémas ASCII/diagrammes

```markdown
<!-- DIAGRAM
type: "architecture|flux|sequence|comparaison"
titre: "Titre descriptif du schéma"
legende: "Légende optionnelle"
-->
```

[schéma ASCII ici]

```
<!-- /DIAGRAM -->
```

### 4. Pour les blocs de code

```markdown
<!-- CODE
langage: "python|bash|sql|json"
titre: "Titre du bloc de code"
executable: "true|false"
-->
```python
# code ici
```

<!-- /CODE -->

```
### 5. Pour les tableaux

```markdown
<!-- TABLE
titre: "Titre du tableau"
colonnes_cles: "colonne1,colonne2"
style: "compact|large"
-->

| Col1 | Col2 | Col3 |
|------|------|------|
| ... | ... | ... |

<!-- /TABLE -->
```

### 6. Pour créer un sous-slide vertical (↓)

```markdown
<!-- SUBSLIDE
titre: "Titre du sous-slide"
parent: "id-du-slide-parent"
-->

Contenu du sous-slide...

<!-- /SUBSLIDE -->
```

### 7. Pour marquer une section à NE PAS inclure dans les slides

```markdown
<!-- NO_SLIDE -->
Cette section est trop détaillée pour les slides.
Elle reste dans le MD mais ne sera pas convertie.
<!-- /NO_SLIDE -->
```

---

## Templates disponibles

| Template        | Usage                                | Éléments attendus     |
| --------------- | ------------------------------------ | --------------------- |
| `titre-section` | Slide de transition entre parties    | Titre + sous-titre    |
| `2colonnes`     | Comparaison, avantages/inconvénients | 2 blocs de contenu    |
| `tableau`       | Données structurées                  | Un tableau markdown   |
| `schema`        | Diagramme ASCII                      | Un bloc DIAGRAM       |
| `code`          | Exemple de code                      | Un bloc CODE          |
| `timeline`      | Chronologie                          | Liste ordonnée        |
| `stats`         | Chiffres clés                        | 3-4 statistiques      |
| `quote`         | Citation                             | Blockquote + source   |
| `exercice`      | Travail pratique                     | Consignes + livrables |
| `synthese`      | Récapitulatif                        | Cards + message clé   |

---

## Règles de conversion

1. **Chaque `## Titre` = 1 slide** (sauf si `NO_SLIDE`)
2. **Chaque `### Sous-titre` = contenu de la slide** (pas une nouvelle slide)
3. **Les listes longues (>6 items)** = scinder ou passer en sous-slide
4. **Les schémas ASCII** = toujours balisés `DIAGRAM`
5. **Les blocs de code >10 lignes** = raccourcir ou sous-slide
6. **Toujours un KEY** = ce que l'audience doit retenir
7. **QUESTION optionnelle** = pour engagement audience

---

## Exemple de section convertie

### AVANT (MD classique)

```markdown
## Moteurs de détection

### detall.py (détection algorithmique)
- **Auteur** : `cx`
- **Coût** : Gratuit (0$)
- **Principe** : Patterns regex, tags.csv
- **Vitesse** : Très rapide (~50-100ms)
- **Limitation** : Ne comprend que les formulations prévues

### detia.py (détection par IA)
- **Auteur** : Variable selon le modèle
- **Coût** : Variable (0.15$ à 15$ / million de tokens)
- **Principe** : Prompt envoyé à un LLM
- **Vitesse** : Plus lent (~500-2000ms)
- **Avantage** : Comprend les reformulations
```

### APRÈS (MD avec métadonnées)

```markdown
<!-- SLIDE
id: "moteurs-detection"
titre: "Deux moteurs de détection"
template: "2colonnes"
emoji: "🔧"
timing: "3min"
-->

## Moteurs de détection

<!-- KEY: detall.py = rapide et gratuit mais rigide | detia.py = intelligent mais coûteux -->

<!-- QUESTION: Dans quel cas privilégieriez-vous la rapidité sur l'intelligence ? -->

### detall.py (détection algorithmique)
- **Auteur** : `cx`
- **Coût** : Gratuit (0$)
- **Principe** : Patterns regex, tags.csv
- **Vitesse** : Très rapide (~50-100ms)
- **Limitation** : Ne comprend que les formulations prévues

### detia.py (détection par IA)
- **Auteur** : Variable selon le modèle
- **Coût** : Variable (0.15$ à 15$ / million de tokens)
- **Principe** : Prompt envoyé à un LLM
- **Vitesse** : Plus lent (~500-2000ms)
- **Avantage** : Comprend les reformulations
```

---

## Exemple pour un schéma ASCII

### AVANT

```markdown
## Flux de données
```

Question → detall.py → JSON → SQL → Résultats

```

```

### APRÈS

```markdown
<!-- SLIDE
id: "flux-donnees"
titre: "Flux de données principal"
template: "schema"
emoji: "🔄"
timing: "2min"
-->

## Flux de données

<!-- KEY: Le flux traverse 5 étapes : Question → Détection → JSON → SQL → Résultats -->

<!-- DIAGRAM
type: "flux"
titre: "Pipeline de recherche simplifié"
-->
```

Question → detall.py → JSON → SQL → Résultats

```
<!-- /DIAGRAM -->
```

---

## Ta mission

1. **Lis le document MD fourni**
2. **Identifie les sections** qui correspondent à des slides
3. **Ajoute les métadonnées** SLIDE, KEY, QUESTION, DIAGRAM, etc.
4. **Choisis le template approprié** pour chaque section
5. **Estime le timing** (total ≈ 1 slide par 2-3 minutes)
6. **Conserve 100% du contenu technique** — tu ajoutes, tu ne supprimes rien

---

## Sortie attendue

Le fichier MD complet avec toutes les métadonnées ajoutées, prêt pour conversion automatique.

Commence par l'en-tête `PRESENTATION_META` puis traite chaque section.
