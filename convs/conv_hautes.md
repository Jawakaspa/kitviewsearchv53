# Prompt conv_hautes V1.0.1 - 21/01/2026 16:00:51

# Synthèse de conversation : hautes

| Métadonnée | Valeur |
|------------|--------|
| Nom conversation | hautes |
| Date création | 17/01/2026 |
| Dernière MAJ | 17/01/2026 14:32 |

---

## Échange 1 — 17/01/2026 14:32

### Question
Demande de création d'un document technique `hautes.md` (5-10 pages) pour ingénieurs de haut niveau, couvrant :
- Architecture technique de KITVIEW Search V5
- Couches hautes côté serveur (server, search, trouve)
- Sous-programmes (lancesql, jsonsql)
- Stratégies de traduction (glossaire vs DeepL)
- Exemples en annexes

### Fichiers fournis
- `server.py` (v1.0.50) — API FastAPI
- `search.py` (v1.0.28) — Orchestration multilingue
- `trouve.py` (v1.0.18) — Pipeline recherche
- `traduire.py` (v1.0.6) — Traduction hybride
- `traduis.py` (v1.0.11) — CLI traduction
- `glossaire.csv` (v1.1.0) — Référentiel multilingue (~2200 termes)
- `ia.csv` (v1.0.15) — Configuration moteurs IA
- `jsonsql.py` (v1.0.6) — Génération SQL
- `lancesql.py` (v1.0.4) — Exécution SQL

### Réponse
Création du document `hautes.md` comprenant :

1. **Vue d'ensemble architecture** — Diagramme ASCII des 6 couches (API → Orchestration → Recherche → Détection → SQL → Base)

2. **Couche API (server.py)** — Endpoints REST, cycle de vie, caches mémoire, flux /search

3. **Couche Orchestration (search.py)** — 4 modes de recherche, algorithme de routage intelligent avec escalades automatiques, résolution sémantique glossaire

4. **Couche Recherche (trouve.py)** — Pipeline detall/detia, garde-fou, fonction rechercher()

5. **Couche SQL (jsonsql.py + lancesql.py)** — Génération SQL paramétrisé, construction pathologies avec accord adjectifs, exécution SQLite

6. **Stratégies de traduction** — Architecture hybride glossaire prioritaire + DeepL fallback, détection Unicode pour scripts non-latins, justification du choix glossaire > DeepL

7. **Configuration moteurs IA** — Structure ia.csv, passerelles (openai, eden)

8. **Annexes** :
   - A : Exemple requête/réponse /search
   - B : Exemples de parcours de détection
   - C : Schéma base de données complet
   - D : Variables d'environnement

### Fichiers produits
- `hautes.md` — Document technique complet (~10 pages)

---

## Prompts de recréation

### Pour recréer hautes.md (version slides-ready)

**Prompt :**
```
Applique Prompt_MD_to_Slides_Ready.md pour régénérer hautes.md avec les métadonnées de slides Reveal.js.

Le document doit inclure :
1. PRESENTATION_META en en-tête avec titre_court, durée, niveau, audience
2. SLIDE avant chaque section ## avec id, titre, template, emoji, timing, transition
3. KEY pour le message clé de chaque slide
4. QUESTION pour les questions de discussion (optionnel)
5. DIAGRAM autour des schémas ASCII
6. CODE autour des blocs de code avec langage et titre
7. TABLE autour des tableaux avec colonnes_cles et style
8. SUBSLIDE pour les sous-slides verticaux
9. NO_SLIDE pour les annexes détaillées

Templates à utiliser : titre-section, schema, tableau, code, 2colonnes, timeline, synthese

Fichiers à joindre en PJ :
- hautes.md (version sans métadonnées)
- Prompt_MD_to_Slides_Ready.md
```

### Pour recréer hautes.md (version initiale sans métadonnées)

**Prompt :**
```
Crée un document technique hautes.md de 5 à 10 pages pour des ingénieurs de haut niveau.

Le document doit couvrir l'architecture technique de KITVIEW Search V5 incluant :
1. Architecture globale avec diagramme ASCII des couches
2. Couche API (server.py) : endpoints, caches, cycle de vie
3. Couche Orchestration (search.py) : modes de recherche, routage intelligent, résolution sémantique
4. Couche Recherche (trouve.py) : pipeline détection, garde-fou
5. Couche SQL (jsonsql.py + lancesql.py) : génération et exécution SQL
6. Stratégies de traduction : glossaire prioritaire vs DeepL fallback
7. Configuration moteurs IA (ia.csv)
8. Annexes avec exemples concrets

Fichiers à joindre en PJ :
- server.py
- search.py
- trouve.py
- jsonsql.py
- lancesql.py
- traduire.py
- traduis.py
- glossaire.csv
- ia.csv
- Prompt_contexte1301.md (contexte projet)
```

---

---

## Échange 2 — 17/01/2026 14:45

### Question
Appliquer `Prompt_MD_to_Slides_Ready.md` pour régénérer hautes.md avec métadonnées de slides Reveal.js.

### Réponse
Régénération complète de `hautes.md` avec ajout des métadonnées suivantes :

**Métadonnées ajoutées :**
- `PRESENTATION_META` en en-tête (titre, durée 35min, niveau avancé, audience)
- `SLIDE` avant chaque section ## avec id, titre, template, emoji, timing, transition
- `KEY` : message clé à retenir pour chaque slide
- `QUESTION` : questions de discussion pour l'audience (6 questions)
- `DIAGRAM` : balises autour des 3 schémas ASCII (architecture, routage, traduction)
- `CODE` : balises autour des 12 blocs de code
- `TABLE` : balises autour des 9 tableaux
- `SUBSLIDE` : 1 sous-slide pour le format de sortie SQL
- `NO_SLIDE` : annexes exclues de la présentation

**Templates utilisés :**
- `titre-section` : 8 slides de transition
- `schema` : 3 slides (architecture, routage, traduction)
- `tableau` : 9 slides
- `code` : 12 slides
- `2colonnes` : 4 slides
- `timeline` : 1 slide
- `synthese` : 1 slide final

**Estimation durée totale :** 35 minutes (~28 slides)

### Fichiers produits
- `hautes.md` — Version slides-ready avec ~80 balises de métadonnées

---

## Historique des versions

| Date | Action | Fichiers |
|------|--------|----------|
| 17/01/2026 14:32 | Création initiale | hautes.md |
| 17/01/2026 14:45 | Ajout métadonnées slides | hautes.md |
