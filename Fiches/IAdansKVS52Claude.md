# L'IA dans KITVIEW Search V5.2 : Perspectives et améliorations

<!-- PRESENTATION_META
titre_court: "L'IA dans KITVIEW Search V5.2"
sous_titre: "État de l'art des LLM spécialisés et roadmap d'amélioration"
duree_estimee: "35min"
niveau: "avancé"
audience: "Développeurs, architectes, direction technique"
fichiers_concernes: "detia.py, detmeme.py, traducteur.py, creecommentaires.py"
emoji_principal: "🚀"
-->

**Version** : 1.0.0  
**Date** : 30/01/2026  
**Auteur** : Documentation technique KITVIEW Search V5.2  
**Audience** : Développeurs, architectes logiciel, direction technique

---

<!-- NO_SLIDE -->
## Table des matières

1. [Rappel V5.1 : L'IA aujourd'hui](#1-rappel-v51--lia-aujourdhui)
2. [État de l'art : LLM spécialisés](#2-état-de-lart--llm-spécialisés)
   - 2.1 [LLM spécialisés orthodontie](#21-llm-spécialisés-orthodontie)
   - 2.2 [LLM spécialisés dermatologie](#22-llm-spécialisés-dermatologie)
   - 2.3 [Synthèse comparative](#23-synthèse-comparative)
3. [Cas d'usage identifiés pour V5.2](#3-cas-dusage-identifiés-pour-v52)
4. [Plan d'action Orthodontie](#4-plan-daction-orthodontie)
5. [Plan d'action Dermatologie](#5-plan-daction-dermatologie)
6. [Priorisation par complexité](#6-priorisation-par-complexité)
7. [Prérequis techniques](#7-prérequis-techniques)
8. [Roadmap V5.2](#8-roadmap-v52)
<!-- /NO_SLIDE -->

---

<!-- SLIDE
id: "rappel-v51"
titre: "Rappel V5.1"
template: "schema"
emoji: "📋"
timing: "3min"
transition: "slide"
-->

## 1. Rappel V5.1 : L'IA aujourd'hui

<!-- KEY: V5.1 intègre l'IA à 6 niveaux : développement, glossaire, traduction, détection, chatbot patient et analyse de cohorte -->

<!-- QUESTION: Quels sont les points de friction actuels dans l'utilisation de l'IA ? -->

### Architecture IA actuelle

<!-- DIAGRAM
type: "architecture"
titre: "Les 6 niveaux d'intégration IA dans V5.1"
legende: "Du développement à l'analyse clinique"
-->
```
┌─────────────────────────────────────────────────────────────────────────┐
│                    INTÉGRATION IA DANS KITVIEW V5.1                     │
└─────────────────────────────────────────────────────────────────────────┘

  NIVEAU 1          NIVEAU 2          NIVEAU 3          NIVEAU 4
  Vibe Prog.        Glossaire         Détection         Chatbot
  ──────────        ─────────         ─────────         ───────
  Claude/GPT        DeepL API         GPT-4o/Claude     GPT-4o/Claude
  Développement     12 langues        detia.py          Fiche patient
  
  NIVEAU 5          NIVEAU 6
  Cohorte           Similarité (NEW)
  ───────           ──────────────────
  GPT-4o/Claude     detmeme.py
  Analyse groupe    "Même X que Y"
```
<!-- /DIAGRAM -->

### Points forts V5.1

- **Glossaire contrôlé** : 12 langues avec terminologie médicale validée
- **Détection hybride** : detall (rapide, gratuit) + detia (intelligent, payant)
- **Injection de référentiels** : tags, adjectifs, angles dans les prompts IA
- **Recherche par similarité** : nouvelle fonctionnalité "Même X que Patient"

### Limitations identifiées

- LLM généralistes (GPT-4o, Claude) sans expertise médicale native
- Pas de compréhension visuelle des photos patients
- Hallucinations possibles sur terminologie orthodontique rare
- Coûts API croissants avec le volume de requêtes

---

<!-- SLIDE
id: "etat-art-intro"
titre: "État de l'art LLM spécialisés"
template: "titre-section"
emoji: "🔬"
timing: "1min"
transition: "zoom"
-->

## 2. État de l'art : LLM spécialisés

<!-- KEY: Des LLM spécialisés émergent en orthodontie et dermatologie avec des performances supérieures aux généralistes -->

---

<!-- SLIDE
id: "llm-orthodontie"
titre: "LLM spécialisés Orthodontie"
template: "tableau"
emoji: "🦷"
timing: "5min"
transition: "slide"
-->

### 2.1 LLM spécialisés orthodontie

<!-- KEY: 5 catégories de LLM pour l'orthodontie : spécialisés dentaires, médicaux généraux, généralistes fine-tunés, open-source -->

<!-- TABLE
titre: "Panorama des LLM pour l'orthodontie"
colonnes_cles: "Modèle,Type,Statut"
style: "large"
-->

| Modèle | Type | Spécialisation | Statut | Notes |
|--------|------|----------------|--------|-------|
| **DentalGPT** | LLM spécialisé dentaire | Dentisterie / Orthodontie | Recherche / Prototype | Modèle expérimental pour QA clinique dentaire |
| **OrthoLM** | LLM spécialisé orthodontie | Orthodontie pure | Recherche | Fine-tuning sur cas orthodontiques |
| **Med-PaLM** | LLM médical (Google) | Médecine générale | Propriétaire | Applicable à l'orthodontie via prompt engineering |
| **GPT-4 / GPT-4o fine-tuned** | Généraliste adapté | Orthodontie via fine-tuning | Commercial | Utilisé avec bases de connaissances privées |
| **LLaMA / Mistral fine-tuned** | Open-source | Orthodontie via fine-tuning | Open-source | Projets hospitalo-universitaires |

<!-- /TABLE -->

### Analyse des options orthodontie

**DentalGPT et OrthoLM** sont des prototypes académiques prometteurs mais non disponibles en production. Leur intérêt réside dans la preuve de concept que le fine-tuning sur données orthodontiques améliore significativement la pertinence des réponses.

**Med-PaLM** (Google) offre un raisonnement clinique de qualité mais reste propriétaire et sans focus orthodontique spécifique. Son accès est limité aux partenaires Google Health.

**GPT-4/4o avec RAG** (Retrieval-Augmented Generation) représente l'approche la plus pragmatique : injection de contexte orthodontique dans les prompts, ce que KITVIEW V5.1 fait déjà avec tags.csv et adjectifs.csv.

**LLaMA/Mistral fine-tunés** permettraient un contrôle total et un hébergement local, mais nécessitent une infrastructure GPU significative et un dataset d'entraînement orthodontique.

---

<!-- SLIDE
id: "llm-dermatologie"
titre: "LLM spécialisés Dermatologie"
template: "tableau"
emoji: "🔬"
timing: "5min"
transition: "slide"
-->

### 2.2 LLM spécialisés dermatologie

<!-- KEY: SkinGPT-4 est le modèle de référence avec 52,929 images et publication Nature Communications 2024 -->

<!-- TABLE
titre: "Panorama des LLM pour la dermatologie"
colonnes_cles: "Modèle,Type,Statut"
style: "large"
-->

| Modèle | Type | Architecture | Statut | Dataset |
|--------|------|--------------|--------|---------|
| **SkinGPT-4** | Multimodal spécialisé | LLaMA-2-13b + Vision Transformer | Recherche (Nature 2024) | 52,929 images dermato |
| **Google DermAssist** | Deep Learning | CNN propriétaire | CE-marqué (EU) | 65,000 images, 288 conditions |
| **Derm Foundation** | Embeddings | Vision Transformer | API Google | Large scale datasets |
| **SkinGEN** | Diagnostic + Génération | SkinGPT-4 + Stable Diffusion | Recherche 2025 | Génère des visualisations |
| **MelaFind** | Instrument spécialisé | Analyse multispectrale | FDA approuvé (2011) | Détection mélanome |

<!-- /TABLE -->

### Focus sur SkinGPT-4

SkinGPT-4, publié dans Nature Communications en juillet 2024, représente l'état de l'art des LLM dermatologiques. Son architecture combine un Vision Transformer pré-entraîné avec LLaMA-2-13b-chat, permettant une analyse multimodale texte + image.

**Points forts :**
- Entraînement sur 52,929 images avec notes cliniques
- Évaluation par dermatologues certifiés (150 cas réels)
- Diagnostic interactif avec recommandations thérapeutiques
- Déploiement local possible (respect vie privée)

**Limitations :**
- Performance réduite sur peaux foncées (Fitzpatrick V-VI)
- Pas de support dermoscopie/histopathologie
- Modèle complet non disponible publiquement (privacy)
- Risque d'hallucinations sur cas complexes

### Google DermAssist

Intégré à Google Lens, DermAssist permet aux utilisateurs de photographier des lésions cutanées pour obtenir une liste de conditions possibles. CE-marqué comme dispositif médical classe I en Europe, il analyse 288 conditions mais n'est pas disponible aux États-Unis.

---

<!-- SLIDE
id: "synthese-comparative"
titre: "Synthèse comparative"
template: "2colonnes"
emoji: "⚖️"
timing: "4min"
transition: "fade"
-->

### 2.3 Synthèse comparative

<!-- KEY: L'orthodontie manque de LLM spécialisés matures vs la dermatologie qui bénéficie de SkinGPT-4 et DermAssist -->

#### Maturité par domaine

| Critère | Orthodontie | Dermatologie |
|---------|-------------|--------------|
| **LLM dédié production-ready** | ❌ Non | ⚠️ Partiel (DermAssist) |
| **Publication Nature/JAMA** | ❌ Non | ✅ SkinGPT-4 (Nature 2024) |
| **Dataset public images** | ❌ Limité | ✅ Plusieurs (DDI, etc.) |
| **Multimodal (texte+image)** | ❌ Non | ✅ SkinGPT-4 |
| **Fine-tuning accessible** | ⚠️ Expérimental | ⚠️ Partiel |
| **Déploiement local possible** | ✅ Via LLaMA | ✅ SkinGPT-4 |

#### Implications pour KITVIEW V5.2

**Orthodontie** : L'approche actuelle (RAG avec référentiels injectés) reste la plus pragmatique. Un fine-tuning propriétaire pourrait être envisagé à moyen terme si un dataset suffisant est constitué.

**Dermatologie** : L'intégration d'un modèle de type SkinGPT-4 offrirait une vraie valeur ajoutée pour l'analyse des photos patients, sous réserve de résoudre les questions de déploiement et de responsabilité médicale.

---

<!-- SLIDE
id: "cas-usage"
titre: "Cas d'usage V5.2"
template: "titre-section"
emoji: "💡"
timing: "1min"
transition: "zoom"
-->

## 3. Cas d'usage identifiés pour V5.2

<!-- KEY: 8 cas d'usage prioritaires répartis en 3 catégories : amélioration existant, nouvelles fonctionnalités, vision long terme -->

---

<!-- SLIDE
id: "cas-usage-detail"
titre: "Détail des cas d'usage"
template: "tableau"
emoji: "📝"
timing: "5min"
transition: "slide"
-->

### Catalogue des cas d'usage

<!-- TABLE
titre: "Cas d'usage IA pour V5.2"
colonnes_cles: "ID,Cas d'usage,Priorité"
style: "large"
-->

| ID | Cas d'usage | Catégorie | Priorité | Domaine |
|----|-------------|-----------|----------|---------|
| **CU-01** | Améliorer la détection de pathologies rares | Existant | Haute | Ortho |
| **CU-02** | Réduire les hallucinations terminologiques | Existant | Haute | Ortho/Dermo |
| **CU-03** | Enrichir la recherche par similarité | Existant | Moyenne | Ortho |
| **CU-04** | Analyse automatique des photos patients | Nouveau | Haute | Dermo |
| **CU-05** | Suggestions de diagnostic différentiel | Nouveau | Moyenne | Ortho/Dermo |
| **CU-06** | Génération de rapports cliniques | Nouveau | Basse | Ortho |
| **CU-07** | Assistant vocal praticien | Vision | Basse | Ortho/Dermo |
| **CU-08** | Fine-tuning modèle propriétaire | Vision | Basse | Ortho |

<!-- /TABLE -->

### Détail des cas d'usage prioritaires

**CU-01 : Détection pathologies rares**
Actuellement, detia.py s'appuie sur tags.csv qui liste ~100 pathologies. Les pathologies rares non listées sont mal détectées. Solution : enrichir le prompt avec synonymes étendus et demander au LLM de signaler les termes non reconnus plutôt que de les ignorer.

**CU-02 : Réduire les hallucinations**
Les LLM généralistes peuvent inventer des termes orthodontiques. Solution : validation systématique des outputs IA contre glossaire.csv et alerte si terme inconnu.

**CU-04 : Analyse photos patients**
Cas d'usage dermatologique majeur. Permettrait d'analyser automatiquement les photos pour suggérer des pathologies visibles (lésions, asymétries). Nécessite un modèle multimodal type SkinGPT-4.

---

<!-- SLIDE
id: "plan-orthodontie"
titre: "Plan d'action Orthodontie"
template: "timeline"
emoji: "🦷"
timing: "4min"
transition: "slide"
-->

## 4. Plan d'action Orthodontie

<!-- KEY: Approche progressive : améliorer RAG existant, puis enrichir référentiels, puis envisager fine-tuning -->

### Phase 1 : Amélioration RAG (Q1 2026)

1. **Enrichir tags.csv** avec pathologies rares et synonymes internationaux
2. **Améliorer le prompt detia.py** : demander explicitement de signaler les termes non reconnus
3. **Ajouter validation post-IA** : vérifier chaque tag détecté contre glossaire.csv
4. **Intégrer angles céphalométriques étendus** : ajouter GoGn-SN, FMA, IMPA

### Phase 2 : Référentiels enrichis (Q2 2026)

1. **Créer classifications.csv** : taxonomie hiérarchique des pathologies (classe I/II/III → sous-types)
2. **Ajouter traitements.csv** : mapping pathologie → traitements recommandés
3. **Enrichir commentaires générés** via creecommentaires.py avec contexte traitement

### Phase 3 : Exploration fine-tuning (Q3-Q4 2026)

1. **Constituer dataset** : extraire questions/réponses des conversations chatbot
2. **Évaluer LLaMA-3 fine-tuné** sur terminologie orthodontique
3. **Benchmark** : comparer fine-tuné vs RAG sur jeu de test standardisé

---

<!-- SLIDE
id: "plan-dermatologie"
titre: "Plan d'action Dermatologie"
template: "timeline"
emoji: "🔬"
timing: "4min"
transition: "slide"
-->

## 5. Plan d'action Dermatologie

<!-- KEY: L'analyse d'images dermato nécessite un modèle multimodal - SkinGPT-4 ou alternative à évaluer -->

### Phase 1 : Évaluation (Q1 2026)

1. **Contacter équipe SkinGPT-4** (KAUST) pour collaboration potentielle
2. **Tester Google Derm Foundation API** pour embeddings d'images
3. **Évaluer GPT-4 Vision** sur échantillon de photos dermato
4. **Définir périmètre légal** : responsabilité médicale, RGPD images

### Phase 2 : Intégration pilote (Q2 2026)

1. **Créer module detdermo.py** : analyse photos peau via API sélectionnée
2. **Interface utilisateur** : upload photo, affichage suggestions
3. **Validation praticien obligatoire** : l'IA suggère, le médecin valide
4. **Logging exhaustif** : traçabilité des suggestions IA

### Phase 3 : Production (Q3 2026)

1. **Intégration fiche patient** : suggestions dermato sur photos existantes
2. **Recherche par similarité visuelle** : "Patients avec lésions similaires"
3. **Alertes automatiques** : signaler photos nécessitant attention

### Points d'attention

- **Peaux foncées** : SkinGPT-4 moins performant sur Fitzpatrick V-VI
- **Responsabilité** : l'IA ne remplace pas le diagnostic médical
- **Consentement** : traitement images médicales soumis au RGPD
- **Coûts** : analyse image plus coûteuse que texte

---

<!-- SLIDE
id: "priorisation"
titre: "Priorisation par complexité"
template: "tableau"
emoji: "📊"
timing: "4min"
transition: "fade"
-->

## 6. Priorisation par complexité

<!-- KEY: Du plus simple (enrichir CSV) au plus complexe (fine-tuning propriétaire) -->

<!-- TABLE
titre: "Matrice effort/impact"
colonnes_cles: "Action,Effort,Impact"
style: "large"
-->

| # | Action | Effort | Impact | ROI | Délai |
|---|--------|--------|--------|-----|-------|
| 1 | Enrichir tags.csv (synonymes) | 🟢 Faible | 🟢 Moyen | ⭐⭐⭐ | 1 sem |
| 2 | Validation post-IA vs glossaire | 🟢 Faible | 🟢 Moyen | ⭐⭐⭐ | 1 sem |
| 3 | Améliorer prompt detia.py | 🟢 Faible | 🟡 Moyen | ⭐⭐⭐ | 2 sem |
| 4 | Créer classifications.csv | 🟡 Moyen | 🟢 Moyen | ⭐⭐ | 2 sem |
| 5 | Tester GPT-4 Vision (dermato) | 🟡 Moyen | 🟡 Moyen | ⭐⭐ | 3 sem |
| 6 | Créer module detdermo.py | 🟠 Élevé | 🟠 Élevé | ⭐⭐ | 1 mois |
| 7 | Intégrer SkinGPT-4 ou équivalent | 🔴 Très élevé | 🟠 Élevé | ⭐ | 3 mois |
| 8 | Fine-tuning LLaMA orthodontie | 🔴 Très élevé | 🟡 Moyen | ⭐ | 6 mois |

<!-- /TABLE -->

### Recommandation

**Quick wins (Q1 2026)** : Actions 1-3 représentent le meilleur ROI avec un effort minimal. À implémenter immédiatement.

**Moyen terme (Q2 2026)** : Actions 4-6 nécessitent plus de travail mais ouvrent de nouvelles fonctionnalités.

**Long terme (Q3-Q4 2026)** : Actions 7-8 sont des investissements lourds à valider après retour d'expérience sur les premières phases.

---

<!-- SLIDE
id: "prerequis"
titre: "Prérequis techniques"
template: "2colonnes"
emoji: "⚙️"
timing: "4min"
transition: "slide"
-->

## 7. Prérequis techniques

<!-- KEY: Données, APIs, infrastructure et compétences nécessaires pour chaque niveau d'ambition -->

### Prérequis par phase

#### Phase 1 : Amélioration RAG

| Ressource | Description | Disponibilité |
|-----------|-------------|---------------|
| tags.csv enrichi | +50 pathologies rares | À créer |
| synonymes.csv | Synonymes internationaux | À créer |
| Tests unitaires | Jeu de 200+ questions | Existant partiel |
| API OpenAI/Anthropic | Accès actuel | ✅ Disponible |

#### Phase 2 : Intégration dermato

| Ressource | Description | Disponibilité |
|-----------|-------------|---------------|
| API GPT-4 Vision | Accès multimodal | ✅ Disponible |
| Google Derm Foundation | API embeddings | À demander |
| Dataset test dermato | 100+ images annotées | À constituer |
| Avis juridique RGPD | Images médicales | À obtenir |

#### Phase 3 : Fine-tuning

| Ressource | Description | Disponibilité |
|-----------|-------------|---------------|
| Dataset orthodontique | 10,000+ Q/R annotées | À constituer |
| Infrastructure GPU | A100 ou équivalent | À provisionner |
| Expertise ML | Fine-tuning LLM | À recruter/former |
| Budget compute | ~5,000€ estimation | À valider |

---

<!-- SLIDE
id: "roadmap"
titre: "Roadmap V5.2"
template: "timeline"
emoji: "🗓️"
timing: "3min"
transition: "zoom"
-->

## 8. Roadmap V5.2

<!-- KEY: Roadmap en 4 phases sur 2026 : quick wins, dermato pilote, intégration, exploration fine-tuning -->

### Timeline V5.2

<!-- DIAGRAM
type: "timeline"
titre: "Roadmap IA KITVIEW V5.2"
legende: "4 phases de janvier à décembre 2026"
-->
```
Q1 2026                 Q2 2026                 Q3 2026                 Q4 2026
────────────────────────────────────────────────────────────────────────────────
│                       │                       │                       │
▼                       ▼                       ▼                       ▼
┌───────────────┐       ┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│ PHASE 1       │       │ PHASE 2       │       │ PHASE 3       │       │ PHASE 4       │
│ Quick Wins    │       │ Dermato Pilot │       │ Intégration   │       │ Exploration   │
├───────────────┤       ├───────────────┤       ├───────────────┤       ├───────────────┤
│ • tags.csv+   │       │ • Test GPT-4V │       │ • detdermo.py │       │ • Dataset     │
│ • validation  │       │ • Eval Derm   │       │ • UI upload   │       │ • LLaMA test  │
│ • prompt opt  │       │   Foundation  │       │ • Similarité  │       │ • Benchmark   │
│ • classif.csv │       │ • Avis RGPD   │       │   visuelle    │       │ • Décision    │
└───────────────┘       └───────────────┘       └───────────────┘       └───────────────┘
        │                       │                       │                       │
        └───────────────────────┴───────────────────────┴───────────────────────┘
                                V5.2.0          V5.2.1          V5.2.2
```
<!-- /DIAGRAM -->

### Livrables par version

| Version | Date cible | Livrables |
|---------|------------|-----------|
| **V5.2.0** | Mars 2026 | tags.csv enrichi, validation post-IA, prompt optimisé |
| **V5.2.1** | Juin 2026 | detdermo.py pilote, interface upload photo |
| **V5.2.2** | Sept 2026 | Similarité visuelle, alertes dermato |
| **V5.3.0** | Déc 2026 | Décision fine-tuning, prototype si validé |

---

<!-- SLIDE
id: "conclusion"
titre: "Conclusion"
template: "synthese"
emoji: "✅"
timing: "2min"
transition: "zoom"
-->

## Conclusion

<!-- KEY: V5.2 mise sur l'amélioration du RAG existant en orthodontie et l'exploration dermato avec modèles multimodaux -->

### Points clés à retenir

1. **Orthodontie** : Pas de LLM spécialisé mature → améliorer l'approche RAG actuelle
2. **Dermatologie** : SkinGPT-4 et DermAssist ouvrent des possibilités d'analyse d'images
3. **Quick wins** : Enrichir référentiels et valider outputs IA = ROI immédiat
4. **Dermato pilote** : GPT-4 Vision permet de tester l'analyse d'images sans infrastructure lourde
5. **Fine-tuning** : À explorer après validation des phases précédentes

### Prochaines étapes immédiates

1. ☐ Enrichir tags.csv avec 50+ pathologies rares
2. ☐ Implémenter validation post-IA dans detia.py
3. ☐ Contacter équipe SkinGPT-4 pour collaboration
4. ☐ Obtenir avis juridique RGPD images médicales

---

<!-- NO_SLIDE -->

## Annexes

### Annexe A : Sources LLM Orthodontie

- llmsOrtho.csv (fichier projet)
- Publications académiques DentalGPT, OrthoLM
- Documentation Med-PaLM (Google Health)

### Annexe B : Sources LLM Dermatologie

- Zhou et al. (2024) "Pre-trained multimodal large language model enhances dermatological diagnosis using SkinGPT-4" - Nature Communications
- Google DermAssist documentation
- Google Derm Foundation API

### Annexe C : Références

| Référence | URL |
|-----------|-----|
| SkinGPT-4 Paper | https://www.nature.com/articles/s41467-024-50043-3 |
| SkinGPT-4 GitHub | https://github.com/JoshuaChou2018/SkinGPT-4 |
| Google Derm Foundation | https://developers.google.com/health-ai-developer-foundations/derm-foundation |
| Google DermAssist Blog | https://blog.google/technology/health/ai-dermatology-preview-io-2021/ |

<!-- /NO_SLIDE -->

---

**Fin du document**

*Document généré le 30/01/2026 - KITVIEW Search V5.2 Documentation Technique*
*Version 1.0.0 - Slides-Ready avec métadonnées Reveal.js*
