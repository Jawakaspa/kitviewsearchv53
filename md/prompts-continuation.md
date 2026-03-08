# Prompts de continuation — 5 projets indépendants

---

## 1️⃣ Migration tags V1 → V2 et pipeline du projet

```
CONTEXTE : Je travaille sur un système de tagging orthodontique pour Kitview (Groupe Orqual). Le système utilise deux fichiers CSV parsés au runtime :
- tags.csv : 143 tags avec structure `tag;genre;qualificateurs;synonymes_patterns`
- adjectifs.csv : 42 adjectifs avec structure `adj;genre(m/f/mf);féminin;pluriel_m;pluriel_f;synonymes`

Un audit complet a produit tags_v2.csv (151 tags, 1111 patterns, 0 doublons) et adjectifs_v2.csv (51 adjectifs). Les fichiers V2 sont joints à cette conversation.

CHANGEMENTS CLÉS V1 → V2 :
- Ajout d'une 5ème colonne `cat` (pathologie, traitement, biomécanique, fonction, diagnostic, anatomie, matériau, gestion)
- 0 doublons de patterns (9 résolus : "appareil dentaire", "disjoncteur", "dent bloquée"...)
- 0 espaces parasites (70 corrigés)
- Case normalisée (tout en minuscules)
- Tags supprimés : enclavement (→ fusionné dans inclusion), supraposition (→ splitté en overjet + égression)
- Tags ajoutés : overjet, endoalvéolie, ancrage, force orthodontique, nivellement, analyse de bolton, photographie clinique, orthodontie linguale, auxiliaire, arc transpalatin
- 9 adjectifs ajoutés : chirurgical, ectopique, inférieur, invisible, labial, labio-palatin, palatin, retardé, supérieur
- Tag "malocclusion" nettoyé (12 patterns mal placés redistribués)

RISQUES DE MIGRATION IDENTIFIÉS :
1. La 5ème colonne `cat` peut casser les parseurs existants qui attendent 4 champs
2. Les tags supprimés (enclavement, supraposition) orphelinent les données patients existantes
3. Les patterns déplacés changent les résultats de recherche (ex: "disjoncteur" ne matche plus "malocclusion")
4. Référence à un fichier `angles.csv` dans des commentaires — rôle inconnu
5. Sensibilité à la casse : si le système stockait "PALATOVERSION", le matching lowercase peut casser

CE QUE J'ATTENDS :
1. Stratégie de migration complète avec table de correspondance old→new
2. Script de migration des données patients existantes
3. Couche de rétro-compatibilité si nécessaire
4. Décision sur la colonne `cat` : garder (adapter le parseur) ou retirer (rétro-compatible)
5. Plan de test / rollback
6. Investigation du fichier angles.csv

Je vais te fournir : les fichiers V2 corrigés, des détails sur l'architecture du parseur, et le fichier angles.csv si je le retrouve.
```

---

## 2️⃣ Intégration Knowledge Graph Orthodontie V2 dans Kitview Search V5.2

```
CONTEXTE : Je développe Kitview Search V5.2, le moteur de recherche intelligent de Kitview (logiciel de bibliothèque numérique orthodontique, Groupe Orqual). Je souhaite intégrer un Knowledge Graph (KG) interactif dans cette interface.

LE KG EXISTANT : Un composant React (ortho-kg-v2.jsx) qui visualise les 151 tags orthodontiques du système de tagging V2, organisés en 8 catégories (pathologie:71, traitement:31, biomécanique:13, fonction:12, diagnostic:9, anatomie:8, matériaux:4, gestion:3) avec ~70 relations cliniques entre nœuds. Features actuelles : survol, clic pour verrouiller, filtres par catégorie, recherche textuelle, panneau de détail avec relations.

CAS D'USAGE ENVISAGÉS :
A) Panneau latéral (pas modale) depuis les résultats de recherche : quand l'utilisateur clique sur un tag dans les résultats, un panneau slide à droite avec le sous-graphe centré sur ce nœud et ses voisins directs.
B) Suggestions contextuelles invisibles : le KG alimente un système de suggestions — l'utilisateur tape "béance" → le système suggère aussi "dysfonction linguale", "interposition linguale", "succion", "ingression" (voisins dans le graphe).
C) Micro-graphe patient : depuis un dossier patient taggé (ex: "classe II d'angle" + "rétrognathie mandibulaire"), un bouton affiche un graphe contextuel avec uniquement les nœuds pertinents + traitements possibles + diagnostics associés.

QUESTIONS TECHNIQUES À RÉSOUDRE :
- Le KG doit-il être un composant unique paramétrable (mode="overview"|"focused"|"patient", focusNode="béance") ou des composants distincts ?
- Le graphe doit être dynamique (dérivé des CSV au runtime) pour éviter deux sources de vérité
- Les relations (edges) ne sont pas dans les CSV — faut-il un relations.csv dédié ou les inférer ?
- Performance : le SVG actuel avec 151 nœuds + 70 edges est-il viable dans un panneau latéral ?

Je vais te fournir : le composant ortho-kg-v2.jsx actuel, les fichiers tags_v2.csv et adjectifs_v2.csv, et le contexte de l'architecture de Kitview Search V5.2.
```

---

## 3️⃣ Intégration Knowledge Graph Orthodontie V1 dans KVM (manuel d'emploi Kitview)

```
CONTEXTE : KVM est le manuel d'emploi / mode d'emploi interactif de Kitview (logiciel de bibliothèque numérique orthodontique, Groupe Orqual). Je souhaite intégrer un Knowledge Graph (KG) simplifié dans la page d'accueil de ce manuel.

LE KG EXISTANT : Un composant React (orthodontie-kg.jsx, version V1) avec 30 nœuds et 36 relations couvrant 5 domaines (Pathologies en rouge, Traitements en vert, Anatomie en jaune, Diagnostic en bleu, Biomécanique en violet). Features : hover/click pour connexions, drag to reorganize, panneau info avec relations.

CAS D'USAGE : 
- Page d'accueil du mode d'emploi : le KG remplace un sommaire textuel par une carte mentale navigable. L'utilisateur comprend en 3 secondes la couverture fonctionnelle de l'app.
- Mode lecture seule : dans ce contexte, le KG doit être non-interactif au-delà du survol pour ne pas perdre l'utilisateur qui veut juste comprendre "à quoi ça sert".
- Navigation vers les sections du manuel : chaque nœud cliquable pourrait amener à la section correspondante du mode d'emploi (ex: clic sur "Céphalométrie" → section diagnostic du manuel).

CONTRAINTES :
- Utiliser la V1 simplifiée (30 nœuds) et non la V2 complète (151 nœuds) — le manuel doit rester accessible
- Le KG doit s'intégrer dans l'architecture existante de KVM
- Responsive : doit fonctionner sur tablette (usage fréquent au cabinet)

Je vais te fournir : le composant orthodontie-kg.jsx V1, la structure actuelle de KVM, et les contraintes d'intégration.
```

---

## 4️⃣ Séminaire IA : compléter tous les chapitres et intégrer le KG

```
CONTEXTE : Je prépare un séminaire de formation IA en entreprise pour Actimage Academy. La formation est structurée en chapitres Reveal.js. Deux chapitres sont rédigés (joints) :

CHAPITRE 1 — Introduction & Mise en contexte (22 slides)
Contenu : Tour de table, définition IA (faible vs forte/AGI), histoire chronologique (Turing 1950 → Dartmouth 1956 → Perceptron 1958 → ELIZA 1966 → 1er hiver 1970s → Systèmes experts 1980s → 2ème hiver 1987-2010 → Deep Blue → Renaissance deep learning 2012 → AlphaGo → Transformer 2017 → ChatGPT 2022), panorama modèles actuels (GPT, Claude, Gemini, Mistral, Copilot, DALL-E), Quiz Mythes vs Réalités (4 questions : compréhension, emploi, hallucinations, biais).

CHAPITRE 2 — Types d'IA et concepts clés (22 slides)
Contenu : IA symbolique vs connexionniste (comparaison détaillée, neuro-symbolique), 3 types d'apprentissage (supervisé, non supervisé, par renforcement + RLHF), Deep Learning (couches, paramètres, citation LeCun), Architecture Transformer (attention, "Attention Is All You Need", GPT = Generative Pre-trained Transformer), IA traditionnelle vs IA générative (comparatif, exercice de classification 8 cas), Score BLEU, Humanity's Last Exam.

CHAPITRES À CRÉER (3-10, estimés) :
- Ch.3 : Fonctionnement des LLM (tokens, probabilités, génération, température, contexte window)
- Ch.4 : Panorama des outils IA (ChatGPT, Claude, Gemini, Mistral, Copilot, Perplexity — comparatif détaillé)
- Ch.5 : Prompting & bonnes pratiques (techniques de prompt, few-shot, chain-of-thought, systèmes)
- Ch.6 : IA et productivité en entreprise (cas d'usage concrets par métier)
- Ch.7 : IA et création de contenu (texte, image, vidéo, audio, code)
- Ch.8 : RAG, fine-tuning, agents (concepts avancés vulgarisés)
- Ch.9 : Sécurité et confidentialité (données, RGPD, risques)
- Ch.10 : Éthique, régulation et avenir (AI Act, biais, emploi, AGI)

CHARTE GRAPHIQUE : Les slides utilisent un design system cohérent (fond #0a0e1a, variables CSS --blue --purple --pink --green --orange --red --cyan --muted, composants : .card, .info-box, .stat-box, .quote-box, .badge, .columns/.column, .check-list, .cross-list, .arrow-list, .code-block, .timeline-item, .chapter-tag). Chaque slide a des speaker notes avec timing, questions à poser, anecdotes, et conseils pédagogiques.

KG SÉMINAIRE IA : Un Knowledge Graph React unifié (kg-seminaire-ia.jsx) a été créé avec ~45 nœuds mappés aux slides des Ch.1 et Ch.2. Il inclut 8 catégories (histoire, concept, technique, modèle, apprentissage, architecture, application, éthique), un filtrage par chapitre, et 8 types d'actions au clic (SLIDE, DEFINITION, QUIZ, RESOURCE, TIMELINE, DEMO, FILTER, PATH). Chaque nœud a un champ slide: "chapitre:numéro". Le KG doit être étendu aux chapitres 3-10 au fur et à mesure.

INTÉGRATION REVEAL.JS : 3 stratégies documentées dans le code (modale overlay avec Reveal.slide(), iframe avec postMessage, BroadcastChannel). À choisir et implémenter.

CE QUE J'ATTENDS :
1. Rédaction des chapitres 3 à 10 dans le même format Reveal.js avec la même charte graphique
2. Extension du KG avec les nœuds des nouveaux chapitres
3. Implémentation de l'intégration KG ↔ Reveal.js
4. Cohérence des renvois inter-chapitres (les notes mentionnent déjà "on verra ça au chapitre X")
```

---

## 5️⃣ Fun : Knowledge Graph pour le projet Parkings

```
CONTEXTE : J'ai un projet lié aux parkings (détails à préciser). J'aimerais créer un Knowledge Graph interactif dans le même style que ceux réalisés pour l'orthodontie et la dermatologie — composant React avec nœuds colorés par catégorie, relations sémantiques, survol/clic, filtres, panneau de détail.

Domaines possibles à explorer selon la nature du projet :
- Infrastructure : types de parkings (souterrain, aérien, surface, relais P+R), équipements (bornes de charge, barrières, caméras LAPI, horodateurs, capteurs)
- Gestion : tarification (horaire, abonnement, dynamique), occupation temps réel, rotation, taux de remplissage
- Technologie : guidage à la place, LAPI (Lecture Automatique de Plaques d'Immatriculation), paiement dématérialisé, apps mobiles, IoT/capteurs
- Mobilité urbaine : intermodalité, vélos, covoiturage, zones piétonnes, politique de stationnement
- Réglementation : PLU, normes PMR, sécurité incendie, ventilation
- Acteurs : exploitants (Indigo, Effia, Q-Park), collectivités, promoteurs, usagers

Dis-moi quels aspects du projet parking tu veux couvrir et je te construirai un KG sur mesure. On peut aussi explorer d'autres angles si le projet est plus spécifique (app de recherche de places, gestion de parc privé, smart parking IoT, etc.).
```

---

*Chaque prompt est autonome et contient tout le contexte nécessaire pour démarrer une conversation indépendante. Les fichiers à joindre sont indiqués dans chaque prompt.*
