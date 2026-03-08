# Synthèse de conversation : détection

**Projet** : KITVIEW Search V5  
**Date de création** : 18/01/2026  
**Dernière mise à jour** : 30/01/2026

---

## Échanges

### 30/01/2026 ~14:30 - Ajout de detmeme.py (détection similarités)

**Question** : Mettre à jour detection.md pour inclure la nouveauté detmeme.py (détection des similarités) intégrée dans detall.py mais pas dans detia.py. Ajouter une annexe expliquant ce choix et les évolutions possibles.

**Fichiers analysés** :
- detmeme.py V1.0.7 (25/01/2026) : Détection des expressions "même X que Y"
- detall.py V1.0.10 (21/01/2026) : Intègre detmeme comme étape 1.5
- detia.py V1.0.29 (14/01/2026) : N'intègre PAS detmeme (utilise le module algorithmique)

**Modifications apportées à detection.md (V1.0.0 → V1.1.0)** :
1. Mise à jour PRESENTATION_META (durée 50min, fichiers concernés)
2. Section 6 detall.py : Pipeline mis à jour avec 6 étapes (ajout detmeme en 1.5)
3. charger_references() : Ajout patterns_meme
4. Table des fichiers CSV : Ajout communb.csv
5. Section 7 detia.py : Note sur l'absence d'intégration detmeme + lien annexe F
6. Nouvelle section 9.0 : detmeme.py - Détection des Similarités
7. Section 12 Format JSON : Ajout type "meme" et reference_meme
8. Nouvelle Annexe F : Pourquoi detia utilise detmeme (algorithmique)
   - Justification du choix (pattern simple, fiable, gratuit)
   - Modifications à apporter pour intégrer la détection IA
   - Recommandation : approche hybride

**Cibles de similarité detmeme.py** :
- tag, pathologie, portrait, sexe, age, nom, prenom

**Format JSON critère meme** :
```json
{
    "type": "meme",
    "cible": "portrait",
    "label": "Même portrait",
    "valeur": null
}
```

---

### 18/01/2026 ~11:00 - Création du script md2reveal.py

**Question** : Créer un script réutilisable pour convertir les fichiers MD avec métadonnées en présentations Reveal.js.

**Réponse** : Création du script `md2reveal.py` avec :
- Parsing complet des métadonnées (PRESENTATION_META, SLIDE, KEY, QUESTION, DIAGRAM, CODE, TABLE, SUBSLIDE, NO_SLIDE)
- Conversion Markdown → HTML (titres, listes, code, tableaux, formatage inline)
- Génération HTML Reveal.js avec :
  - Slides horizontales et verticales (SUBSLIDE)
  - Speaker notes avec les KEY
  - Questions audience mises en valeur
  - Templates visuels par type (titre-section, schema, code, 2colonnes...)
  - CSS personnalisé intégré
  - Reveal.js chargé via CDN (pas d'installation)
- Support de 11 thèmes Reveal.js (black, white, moon, dracula...)

**Test réussi** sur detection.md :
- 23 slides générées (14 principales + 8 sous-slides + 1 titre)
- 13 messages clés (speaker notes)
- 3 questions audience

**Usage** :
```bash
python md2reveal.py input.md [output.html] [--theme=moon]
python md2reveal.py detection.md
python md2reveal.py detection.md presentation.html --theme=dracula
```

---

### 18/01/2026 ~10:45 - Régénération avec métadonnées Slides

**Question** : Appliquer Prompt_MD_to_Slides_Ready.md pour régénérer detection.md avec des métadonnées facilitant la conversion en présentation Reveal.js.

**Réponse** : Régénération complète du document avec ajout de :
- En-tête `PRESENTATION_META` (titre court, durée estimée 45min, audience, fichiers concernés)
- Balises `SLIDE` pour chaque section (id, titre, template, emoji, timing, transition)
- Balises `KEY` avec message clé à retenir pour chaque slide
- Balises `QUESTION` pour engagement de l'audience
- Balises `DIAGRAM` pour les schémas ASCII
- Balises `CODE` pour les blocs de code
- Balises `TABLE` pour les tableaux
- Balises `SUBSLIDE` pour les slides verticales
- Balises `NO_SLIDE` pour la table des matières

**Templates utilisés** : titre-section, schema, 2colonnes, tableau, code, synthese

---

### 18/01/2026 ~10:15 - Demande de documentation technique

**Question** : Création d'un document technique `detection.md` (5-10 pages) pour ingénieurs de haut niveau, expliquant l'architecture de détection de KITVIEW Search V5, de server.py jusqu'à trouve.py, avec focus sur detall, detia, detiabrut et leurs sous-programmes.

**Fichiers fournis** :
- **Modules de détection** : detall.py, detia.py, detiabrut.py, detcount.py, detangles.py, detage.py, detadjs.py, dettags.py
- **Couches hautes** : server.py, search.py, trouve.py
- **Couches SQL** : jsonsql.py, lancesql.py
- **Utilitaires** : standardise.py, motsvides.py, gardefou.py
- **Référentiels CSV** : tags.csv, adjectifs.csv, angles.csv, ages.csv, commun.csv, glossaire.csv, ia.csv, motsvides.csv, commentaires.csv
- **Documentation** : AnglesANBSNASNB.txt (référence céphalométrie)

**Réponse** : Création du document `detection.md` couvrant :

1. **Architecture 6 couches** :
   - Couche 1 : API (server.py - FastAPI/Uvicorn)
   - Couche 2 : Orchestration (search.py - routage intelligent)
   - Couche 3 : Pipeline (trouve.py - coordination)
   - Couche 4 : Détection (detall/detia/detiabrut)
   - Couche 5 : Génération SQL (jsonsql.py)
   - Couche 6 : Exécution SQL (lancesql.py)

2. **Système de détection algorithmique (detall.py)** :
   - Pipeline séquentiel : detcount → detangles → dettags → detage → motsvides
   - Auteur : "cx"
   - Chargement références depuis CSV

3. **Système de détection IA (detia.py)** :
   - LLM (GPT-4, Claude via OpenAI/EdenAI)
   - Prompt système avec injection des référentiels
   - Auteur : "eden/{model}" ou "openai/{model}"

4. **Mode configurable (detiabrut.py)** :
   - Activation/désactivation sélective des référentiels
   - Mesure d'impact de chaque composant

5. **Mécanismes de protection** :
   - gardefou.py : protection anti-saturation
   - standardise.py : normalisation texte
   - motsvides.py : filtrage stopwords

6. **Format JSON unifié** entre tous les modules

**Livrable** : `detection.md` (~12 pages avec annexes)

---

## Documents produits

| Fichier | Description | Version | Date |
|---------|-------------|---------|------|
| `detection.md` | Documentation technique système de détection V5 (Slides-Ready) | 1.1.0 | 30/01/2026 |
| `detection.html` | Présentation Reveal.js générée (23 slides, thème moon) | 1.0.0 | 18/01/2026 |
| `md2reveal.py` | Script de conversion MD → Reveal.js (réutilisable) | 1.0.0 | 18/01/2026 |
| `conv_détection.md` | Ce fichier de synthèse | - | 30/01/2026 |

---

## Prompts pour recréer les fichiers

### Pour recréer detection.md (version Slides-Ready V1.1.0)

**Prompt** :
```
Crée un document technique detection.md de 5 à 10 pages pour des ingénieurs de haut niveau.

Le document doit :
1. Expliquer l'architecture technique de KITVIEW Search V5 en 6 couches (server → search → trouve → détection → jsonsql → lancesql)
2. Détailler le fonctionnement des couches de détection :
   - detall.py : orchestrateur algorithmique (pipeline detcount → detmeme → detangles → dettags → detage → motsvides)
   - detia.py : détection par IA (LLM avec prompt injecté) - NOTE: n'intègre PAS detmeme
   - detiabrut.py : mode configurable pour mesurer l'impact des référentiels
3. Documenter les modules spécialisés : detcount, detmeme (V5.1), detangles, dettags, detadjs, detage
4. Expliquer les couches SQL (jsonsql, lancesql)
5. Présenter les mécanismes de protection (gardefou, standardise, motsvides)
6. Illustrer avec des exemples concrets en annexe
7. Ajouter une Annexe F expliquant pourquoi detia utilise detmeme (algorithmique) et non l'IA pour les similarités, avec les modifications à apporter pour changer cela

Inclure des diagrammes ASCII pour l'architecture et les flux de données.

IMPORTANT : Appliquer le format Prompt_MD_to_Slides_Ready.md pour ajouter des métadonnées de slides :
- En-tête PRESENTATION_META
- Balises SLIDE avec id, titre, template, emoji, timing, transition pour chaque section ##
- Balises KEY avec message clé à retenir
- Balises QUESTION pour l'engagement audience
- Balises DIAGRAM, CODE, TABLE autour des éléments concernés
- Balises SUBSLIDE pour les sous-sections importantes
- Balises NO_SLIDE pour la table des matières
```

**Pièces jointes requises** :
- detall.py, detia.py, detiabrut.py
- **detmeme.py** (V5.1 - détection similarités)
- detcount.py, detangles.py, dettags.py, detadjs.py, detage.py
- server.py, search.py, trouve.py
- jsonsql.py, lancesql.py
- standardise.py, motsvides.py, gardefou.py
- tags.csv, adjectifs.csv, angles.csv, ages.csv, commun.csv, **communb.csv**
- AnglesANBSNASNB.txt
- Prompt_contexte1301.md
- Prompt_MD_to_Slides_Ready.md (pour le format des métadonnées)

### Pour recréer md2reveal.py

**Prompt** :
```
Crée un script Python md2reveal.py qui convertit des fichiers Markdown avec métadonnées de slides en présentations HTML Reveal.js.

Le script doit :
1. Parser les métadonnées personnalisées dans les commentaires HTML :
   - PRESENTATION_META : titre, sous-titre, durée, audience, emoji
   - SLIDE : id, titre, template, emoji, timing, transition
   - KEY : message clé (→ speaker notes)
   - QUESTION : question pour l'audience
   - DIAGRAM, CODE, TABLE : marqueurs de blocs spéciaux
   - SUBSLIDE : slides verticales
   - NO_SLIDE : contenu à exclure

2. Convertir le Markdown en HTML (titres, listes, code, tableaux, gras, italique, liens)

3. Générer un HTML Reveal.js complet avec :
   - Slide de titre générée depuis PRESENTATION_META
   - Slides horizontales pour chaque ## avec SLIDE
   - Slides verticales pour les SUBSLIDE
   - Speaker notes avec les KEY
   - Questions audience en blockquote stylé
   - CSS personnalisé intégré
   - Reveal.js chargé via CDN

4. Supporter les templates visuels :
   - titre-section : fond dégradé sombre
   - schema/code : fond noir
   - synthese : fond dégradé bleu
   - 2colonnes, tableau : style standard

5. CLI avec arguments :
   - input.md (obligatoire)
   - output.html (optionnel, défaut = input.html)
   - --theme (black, white, moon, dracula...)

Respecter les conventions du projet : cartouche __pgm__, __version__, __date__, UTF-8 sans BOM.
```

**Pièces jointes requises** :
- Prompt_MD_to_Slides_Ready.md (format des métadonnées)
- Prompt_contexte1301.md (conventions du projet)

---

## Versions des fichiers analysés

| Fichier | Version | Date |
|---------|---------|------|
| server.py | 1.0.50 | 12/01/2026 |
| search.py | 1.0.28 | 09/01/2026 |
| trouve.py | 1.0.18 | 09/01/2026 |
| **detall.py** | **1.0.10** | **21/01/2026** |
| **detia.py** | **1.0.29** | **14/01/2026** |
| **detmeme.py** | **1.0.7** | **25/01/2026** |
| detiabrut.py | 1.0.3 | 08/01/2026 |
| dettags.py | 1.0.15 | 07/01/2026 |
| detadjs.py | 1.0.11 | 07/01/2026 |
| detangles.py | 1.0.8 | 08/01/2026 |
| detage.py | 1.0.5 | 20/12/2025 |
| detcount.py | 1.0.0 | 09/12/2025 |
| jsonsql.py | 1.0.6 | 07/01/2026 |
| lancesql.py | 1.0.4 | 04/01/2026 |
| gardefou.py | 1.0.0 | 19/12/2025 |
| standardise.py | 1.0.2 | 17/12/2025 |
| motsvides.py | 1.0.2 | 17/12/2025 |

---

## Points clés de l'architecture

### Auteurs de détection

| Auteur | Source | Signification |
|--------|--------|---------------|
| `cx` | detall.py | Détection algorithmique |
| `eden/{model}` | detia.py | IA via EdenAI |
| `openai/{model}` | detia.py | IA via OpenAI direct |
| `cx→eden` | search.py | Fallback algo → IA |

### Modes de recherche

| Mode | Description | Fallback |
|------|-------------|----------|
| `standard` | detall.py en premier | → IA → DeepL |
| `ia` | detia.py forcé | → DeepL |
| `purstandard` | detall.py uniquement | Aucun |
| `puria` | detia.py uniquement | Aucun |

### Format JSON unifié

Tous les modules de détection produisent :
```json
{
  "auteur": "cx|eden/...",
  "listcount": "LIST|COUNT",
  "criteres": [
    {"type": "tag|age|sexe|count", ...}
  ],
  "residu": "mots non reconnus"
}
```

---

*Dernière mise à jour : 18/01/2026 10:15*
