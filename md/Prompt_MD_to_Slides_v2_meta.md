# Prompt : Enrichissement MD pour Slides Reveal.js

<!-- PRESENTATION_META
titre_court: "Prompt MD → Slides"
sous_titre: "Guide d'enrichissement de documents Markdown pour conversion en présentations"
duree_estimee: "15min de lecture, application variable"
niveau: "intermédiaire"
audience: "Rédacteurs techniques, formateurs, documentalistes"
fichiers_concernes: "*.md sources, parse_md_to_csv.py, csv_to_html.py"
emoji_principal: "🎭"
-->

**Version** : 2.0.0 — Auto-référentielle  
**Date** : 21/01/2026  
**Particularité** : Ce document applique les règles qu'il énonce. Chaque section démontre ce qu'elle explique.

---

<!-- SLIDE
id: "intro-meta"
titre: "Un prompt qui se documente lui-même"
template: "titre-chapitre"
emoji: "🎭"
timing: "2min"
-->

## Introduction : La mise en abyme documentaire

<!-- KEY: Ce prompt EST un exemple de ce qu'il demande de produire — chaque section démontre la règle qu'elle énonce. -->

<!-- QUESTION: Avez-vous déjà vu un document qui s'utilise comme sa propre démonstration ? -->

Ce document a une particularité : **il applique exactement les règles qu'il vous demande d'appliquer**.

Quand vous lisez une section expliquant comment ajouter une balise `<!-- SLIDE -->`, vous voyez cette même balise juste au-dessus de la section. C'est de la **documentation auto-référentielle**.

**Pourquoi cette approche ?**

- Vous voyez immédiatement le résultat attendu
- Pas d'ambiguïté sur le format
- Le document lui-même est testable par le pipeline

---

<!-- SLIDE
id: "objectif"
titre: "Objectif de ce prompt"
template: "2colonnes"
emoji: "🎯"
timing: "2min"
-->

## Objectif

<!-- KEY: Transformer un document MD technique en document MD enrichi, prêt pour conversion automatique en slides Reveal.js. -->

### Ce que vous avez (entrée)

Un document Markdown classique :

- Titres `##` et `###`
- Listes à puces
- Tableaux
- Blocs de code
- Schémas ASCII

### Ce que vous obtiendrez (sortie)

Le même document enrichi avec :

- Métadonnées de présentation globale
- Balises `<!-- SLIDE -->` avant chaque section
- Points clés `<!-- KEY: ... -->`
- Questions de discussion `<!-- QUESTION: ... -->`
- Schémas balisés `<!-- DIAGRAM -->`

**Le contenu technique reste 100% identique.**

---

<!-- SLIDE
id: "regle-presentation-meta"
titre: "Règle 1 : En-tête PRESENTATION_META"
template: "code"
emoji: "📋"
timing: "3min"
-->

## Règle 1 : L'en-tête global

<!-- KEY: Toujours commencer le document par un bloc PRESENTATION_META qui définit le contexte global de la présentation. -->

Tout document enrichi commence par un bloc de métadonnées globales, **juste après le titre principal** :

<!-- CODE
langage: "html"
titre: "Format du bloc PRESENTATION_META"
-->

```html
<!-- PRESENTATION_META
titre_court: "Titre pour la slide de titre"
sous_titre: "Sous-titre explicatif"
duree_estimee: "25min"
niveau: "débutant|intermédiaire|avancé"
audience: "Description du public cible"
fichiers_concernes: "fichier1.py, fichier2.csv"
emoji_principal: "🔍"
-->
```

<!-- /CODE -->

**Champs obligatoires** : `titre_court`, `duree_estimee`  
**Champs recommandés** : `sous_titre`, `niveau`, `audience`  
**Champs optionnels** : `fichiers_concernes`, `emoji_principal`

---

<!-- SLIDE
id: "regle-slide"
titre: "Règle 2 : Balise SLIDE avant chaque section"
template: "code"
emoji: "🏷️"
timing: "4min"
-->

## Règle 2 : Baliser chaque section majeure

<!-- KEY: Chaque titre de niveau 2 (##) doit être précédé d'une balise SLIDE définissant ses métadonnées. -->

<!-- QUESTION: Regardez juste au-dessus de ce titre : voyez-vous la balise SLIDE qui définit cette section ? -->

Avant **chaque section `## Titre`**, insérez :

<!-- CODE
langage: "html"
titre: "Format de la balise SLIDE"
-->

```html
<!-- SLIDE
id: "identifiant-unique"
titre: "Titre affiché dans la slide"
template: "tableau|2colonnes|schema|code|synthese"
emoji: "📊"
timing: "3min"
transition: "slide|fade|zoom"
-->

## Titre de la section dans le MD

<!-- KEY: Message clé en une phrase -->

<!-- QUESTION: Question pour l'audience ? -->

Contenu de la section...
```

<!-- /CODE -->

### Champs de la balise SLIDE

| Champ        | Obligatoire | Description                            |
| ------------ | ----------- | -------------------------------------- |
| `id`         | ✅ Oui       | Identifiant unique (kebab-case)        |
| `titre`      | ✅ Oui       | Titre affiché (peut différer du ## MD) |
| `template`   | ✅ Oui       | Type de mise en page                   |
| `emoji`      | Recommandé  | Emoji illustratif                      |
| `timing`     | Recommandé  | Durée estimée                          |
| `transition` | Non         | Effet de transition (défaut: slide)    |

---

<!-- SLIDE
id: "regle-templates"
titre: "Règle 3 : Choisir le bon template"
template: "tableau"
emoji: "🎨"
timing: "3min"
-->

## Règle 3 : Les templates disponibles

<!-- KEY: Le choix du template guide la mise en page finale — choisissez selon le type de contenu. -->

| Template         | Usage                    | Contenu attendu               |
| ---------------- | ------------------------ | ----------------------------- |
| `titre-chapitre` | Slide d'ouverture        | Titre + sous-titre uniquement |
| `tableau`        | Données structurées      | Un ou plusieurs tableaux MD   |
| `2colonnes`      | Comparaison, pour/contre | Deux `###` sous-titres        |
| `schema`         | Diagramme ASCII          | Bloc `<!-- DIAGRAM -->`       |
| `code`           | Exemples de code         | Bloc(s) de code MD            |
| `timeline`       | Chronologie              | Liste ordonnée d'événements   |
| `stats`          | Chiffres clés            | 3-4 métriques importantes     |
| `quote`          | Citation                 | Blockquote MD                 |
| `exercice`       | Travail pratique         | Consignes + livrables         |
| `synthese`       | Récapitulatif            | Résumé + transition           |
| `contenu`        | Générique                | Tout type de contenu          |

**Règle de choix** : Si votre section contient un tableau → `tableau`. Un schéma ASCII → `schema`. Deux parties à comparer → `2colonnes`. En doute → `contenu`.

---

<!-- SLIDE
id: "regle-key"
titre: "Règle 4 : Le point clé KEY"
template: "2colonnes"
emoji: "🎯"
timing: "2min"
-->

## Règle 4 : Toujours un point clé

<!-- KEY: Chaque slide DOIT avoir un KEY — c'est ce que l'audience doit retenir si elle n'écoute qu'une phrase. -->

### Pourquoi c'est obligatoire

Le `<!-- KEY: ... -->` représente :

- Le **message principal** de la slide
- Ce que l'audience retient si elle décroche
- Le **fil rouge** de la présentation
- La base des **révisions** post-formation

### Comment le rédiger

- **Une seule phrase** (max 150 caractères)
- **Actionnable** ou **mémorable**
- **Auto-suffisant** (compréhensible seul)
- Commence souvent par un verbe ou un nom

**Mauvais** : "Cette section parle des modes de recherche"  
**Bon** : "Le mode standard maximise les résultats grâce aux fallbacks automatiques"

---

<!-- SLIDE
id: "regle-question"
titre: "Règle 5 : Questions de discussion"
template: "contenu"
emoji: "💬"
timing: "2min"
-->

## Règle 5 : Engager l'audience

<!-- KEY: Les questions QUESTION transforment une présentation passive en session interactive. -->

<!-- QUESTION: À votre avis, quel pourcentage de rétention gagne-t-on avec des questions interactives ? -->

La balise `<!-- QUESTION: ... -->` est **optionnelle mais recommandée**.

### Types de questions efficaces

1. **Question d'expérience** : "Qui a déjà rencontré ce problème ?"
2. **Question de réflexion** : "Pourquoi pensez-vous que... ?"
3. **Question de choix** : "Entre A et B, que choisiriez-vous ?"
4. **Question d'application** : "Comment appliqueriez-vous cela chez vous ?"

### Où placer la question

- **Après le KEY** : Pour lancer la discussion sur le point clé
- **En fin de slide** : Pour faire la transition vers la suite
- **Jamais au début** : L'audience n'a pas encore le contexte

---

<!-- SLIDE
id: "regle-diagram"
titre: "Règle 6 : Baliser les schémas ASCII"
template: "schema"
emoji: "📐"
timing: "3min"
-->

## Règle 6 : Les schémas ASCII

<!-- KEY: Les schémas ASCII doivent être encadrés par DIAGRAM pour être correctement stylisés en HTML. -->

Tout schéma en caractères ASCII doit être balisé :

<!-- DIAGRAM
type: "flux"
titre: "Exemple de balisage DIAGRAM"
-->

```
Entrée ──► Traitement ──► Sortie
              │
              ▼
          Logging
```

<!-- /DIAGRAM -->

### Format de la balise DIAGRAM

<!-- CODE
langage: "html"
titre: "Structure DIAGRAM complète"
-->

```html
<!-- DIAGRAM
type: "architecture|flux|sequence|comparaison"
titre: "Titre descriptif du schéma"
legende: "Légende optionnelle"
-->
```

[Votre schéma ASCII ici]

```
<!-- /DIAGRAM -->
```

<!-- /CODE -->

### Types de diagrammes

| Type           | Usage                    |
| -------------- | ------------------------ |
| `architecture` | Structure de composants  |
| `flux`         | Processus, workflow      |
| `sequence`     | Interactions temporelles |
| `comparaison`  | Côte à côte              |

---

<!-- SLIDE
id: "regle-subslide"
titre: "Règle 7 : Les sous-slides verticaux"
template: "2colonnes"
emoji: "⬇️"
timing: "2min"
-->

## Règle 7 : Créer des sous-slides

<!-- KEY: Utilisez SUBSLIDE pour du contenu lié mais trop long pour une seule slide — l'utilisateur navigue avec ↓ -->

### Quand utiliser SUBSLIDE

- Détail d'un concept introduit dans la slide parente
- Suite d'un schéma trop grand
- Exemples supplémentaires optionnels
- Réponse à une question posée

### Syntaxe

<!-- CODE
langage: "html"
titre: "Balise SUBSLIDE"
-->

```html
<!-- SUBSLIDE
id: "detail-concept"
titre: "Détail du concept"
parent: "id-slide-parente"
template: "contenu"
emoji: "📎"
timing: "2min"
transition: "fade"
-->

## Contenu du sous-slide

...

<!-- /SUBSLIDE -->
```

<!-- /CODE -->

Le `parent` fait référence à l'`id` de la slide principale.

---

<!-- SLIDE
id: "regle-no-slide"
titre: "Règle 8 : Exclure du contenu"
template: "contenu"
emoji: "🚫"
timing: "1min"
-->

## Règle 8 : Sections à ne pas convertir

<!-- KEY: Utilisez NO_SLIDE pour garder du contenu dans le MD source sans le transformer en slide. -->

Certaines sections sont utiles dans la documentation mais pas en présentation :

<!-- CODE
langage: "html"
titre: "Balise NO_SLIDE"
-->

```html
<!-- NO_SLIDE -->

## Notes techniques détaillées

Ce contenu reste dans le fichier MD pour référence,
mais ne sera pas converti en slide.

Idéal pour :
- Annexes techniques
- Références bibliographiques
- Notes de maintenance
- Historique des versions

<!-- /NO_SLIDE -->
```

<!-- /CODE -->

---

<!-- SLIDE
id: "conversion-equivalence"
titre: "Règles de conversion MD → Slides"
template: "tableau"
emoji: "🔄"
timing: "2min"
-->

## Équivalences de conversion

<!-- KEY: Un titre ## = une slide. Un titre ### = du contenu dans la slide. Les listes longues doivent être scindées. -->

| Élément MD         | Devient en slide                    | Règle                      |
| ------------------ | ----------------------------------- | -------------------------- |
| `# Titre`          | Ignoré (utilisez PRESENTATION_META) | —                          |
| `## Section`       | **1 slide**                         | Toujours avec balise SLIDE |
| `### Sous-titre`   | Titre dans la slide                 | Max 2-3 par slide          |
| Liste > 6 items    | Scinder ou sous-slide               | Éviter le scroll           |
| Tableau > 8 lignes | Scinder                             | Lisibilité                 |
| Code > 15 lignes   | Raccourcir ou sous-slide            | Focus                      |
| Schéma ASCII       | Balise DIAGRAM                      | Styling                    |
| `> Citation`       | Quote box                           | Avec source                |

---

<!-- SLIDE
id: "exemple-avant-apres"
titre: "Exemple complet : Avant / Après"
template: "2colonnes"
emoji: "✨"
timing: "4min"
-->

## Exemple de transformation

<!-- KEY: La transformation ajoute des métadonnées sans modifier le contenu technique — c'est de l'enrichissement, pas de la réécriture. -->

### AVANT (MD classique)

```markdown
## Moteurs de détection

### detall.py
- Auteur : cx
- Coût : Gratuit
- Vitesse : 50-100ms

### detia.py
- Auteur : Variable
- Coût : 0.15$ à 15$
- Vitesse : 500-2000ms
```

### APRÈS (MD enrichi)

```markdown
<!-- SLIDE
id: "moteurs"
titre: "Deux moteurs"
template: "2colonnes"
emoji: "🔧"
timing: "3min"
-->

## Moteurs de détection

<!-- KEY: detall = rapide/gratuit | detia = intelligent/coûteux -->

<!-- QUESTION: Quand privilégier la rapidité ? -->

### detall.py
- Auteur : cx
- Coût : Gratuit
- Vitesse : 50-100ms

### detia.py
- Auteur : Variable
- Coût : 0.15$ à 15$
- Vitesse : 500-2000ms
```

---

<!-- SLIDE
id: "pipeline"
titre: "Pipeline de génération complet"
template: "schema"
emoji: "🔧"
timing: "3min"
-->

## Pipeline MD → HTML

<!-- KEY: Trois étapes : enrichir le MD avec Claude, parser vers CSV, générer le HTML Reveal.js. -->

<!-- DIAGRAM
type: "flux"
titre: "Pipeline de génération de slides"
-->

```
┌─────────────────────────────────────────────────────────────────┐
│  ÉTAPE 1 : ENRICHIR LE MD                                       │
│  ─────────────────────────────────────────────────────────────  │
│  • Ouvrir une conversation Claude                               │
│  • Coller CE PROMPT en premier message                          │
│  • Attacher le fichier .md à enrichir                           │
│  • Claude régénère avec les balises                             │
│  → Sortie : fichier_enrichi.md                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  ÉTAPE 2 : PARSER VERS CSV                                      │
│  ─────────────────────────────────────────────────────────────  │
│  python parse_md_to_csv.py fichier_enrichi.md                   │
│  → Sortie : fichier_enrichi.csv                                 │
│                                                                 │
│  Options :                                                      │
│    --preview     Aperçu sans générer de fichier                 │
│    output.csv    Nom de sortie personnalisé                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  ÉTAPE 3 : GÉNÉRER LE HTML                                      │
│  ─────────────────────────────────────────────────────────────  │
│  python csv_to_html.py fichier_enrichi.csv                      │
│  → Sortie : fichier_enrichi.html                                │
│                                                                 │
│  Options :                                                      │
│    --title "Titre"    Titre de la présentation                  │
│    output.html        Nom de sortie personnalisé                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  RÉSULTAT : Présentation Reveal.js                              │
│  ─────────────────────────────────────────────────────────────  │
│  • Ouvrir le fichier .html dans un navigateur                   │
│  • Touche S pour les notes présentateur                         │
│  • Touche F pour plein écran                                    │
│  • Flèches ← → ↑ ↓ pour naviguer                                │
└─────────────────────────────────────────────────────────────────┘
```

<!-- /DIAGRAM -->

---

<!-- SLIDE
id: "synthese"
titre: "Synthèse des règles"
template: "synthese"
emoji: "📝"
timing: "2min"
transition: "zoom"
-->

## Synthèse

<!-- KEY: 8 règles simples : PRESENTATION_META en tête, SLIDE avant chaque ##, KEY obligatoire, QUESTION recommandé, DIAGRAM pour les schémas. -->

<!-- QUESTION: Quelle règle vous semble la plus importante pour vos documents ? -->

| #   | Règle               | Balise              | Obligatoire   |
| --- | ------------------- | ------------------- | ------------- |
| 1   | En-tête global      | `PRESENTATION_META` | ✅             |
| 2   | Section = slide     | `SLIDE`             | ✅             |
| 3   | Choisir template    | `template: "..."`   | ✅             |
| 4   | Point clé           | `KEY`               | ✅             |
| 5   | Question discussion | `QUESTION`          | Recommandé    |
| 6   | Schémas balisés     | `DIAGRAM`           | Si applicable |
| 7   | Sous-slides         | `SUBSLIDE`          | Si applicable |
| 8   | Exclusions          | `NO_SLIDE`          | Si applicable |

---

<!-- NO_SLIDE -->

## Instructions pour Claude (section non convertie)

### Ta mission

Quand on te donne un fichier MD à enrichir :

1. **Lis d'abord** tout le document pour comprendre sa structure
2. **Identifie** les sections `##` qui deviendront des slides
3. **Ajoute** `PRESENTATION_META` au début
4. **Pour chaque `##`** : ajoute `SLIDE`, `KEY`, et optionnellement `QUESTION`
5. **Balise** les schémas ASCII avec `DIAGRAM`
6. **Choisis** le template approprié selon le contenu
7. **Estime** le timing (1 slide ≈ 2-3 min)
8. **Conserve** 100% du contenu technique original

### Ce que tu ne fais PAS

- Tu ne **résumes** pas le contenu
- Tu ne **réorganises** pas les sections
- Tu ne **supprimes** rien
- Tu ne **reformules** pas le texte technique
- Tu n'**inventes** pas de contenu

### Format de sortie

Le fichier MD complet avec toutes les balises ajoutées, prêt pour `parse_md_to_csv.py`.

<!-- /NO_SLIDE -->

---

**Fin du document auto-référentiel**

*Ce prompt a été généré en appliquant ses propres règles. Méta, n'est-ce pas ? 🎭*
