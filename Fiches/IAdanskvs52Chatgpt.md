# GPT IA dans KVS 5.2

**Version** : 0.1 (brouillon)

## 1. Situation actuelle (KVS 5.1 – synthèse)

KVS 5.1 intègre déjà l’IA de manière transversale et cohérente, avec une approche hybride très mature :

- **LLM généralistes (GPT-4o, Claude)** utilisés comme moteur sémantique principal
- **Référentiels métier forts** (tags, adjectifs, âges, angles, synonymes) injectés dans les prompts
- **Architecture hybride** :
  - déterministe (detall.py) pour la performance et la régression
  - probabiliste (detia.py) pour la flexibilité sémantique
- **IA clinique contextuelle** : chatbot patient + analyse de cohorte
- **Gouvernance des données** claire (CSV protégés, pas de fuite patient)

👉 En résumé : KVS 5.1 utilise très bien des *LLM généralistes guidés par du métier*, mais **sans LLM spécialisés par domaine**.

---

## 2. État de l’art – LLM spécialisés orthodontie & dermatologie

### 2.1 Orthodontie / dentaire

On observe 3 grandes familles :

1. **LLM généralistes spécialisés par prompt / RAG**  
   - GPT-4o, Claude, Gemini
   - Spécialisation par : glossaires, guidelines, publications
   - Avantage : flexibilité, disponibilité
   - Limite : pas d’apprentissage profond du domaine

2. **LLM fine-tunés domaine dentaire / médical**  
   (cf. CSV fourni)
   - BioGPT (Microsoft)
   - Med-PaLM / Med-Gemini
   - DentalGPT (recherche)
   - LLaMA médical (PubMed, PMC)

3. **Modèles multimodaux orientés imagerie**  
   - Très actifs en orthodontie (radio, photos intra/extra-orales)
   - Peu encore connectés à des moteurs de recherche textuelle clinique

👉 **Constat clé** : aucun LLM orthodontique “clé en main” n’est aujourd’hui supérieur à un GPT-4o *bien contraint*, **sauf** pour :
- compréhension fine de la littérature
- similarité de cas
- raisonnement clinique guidé par guidelines


### 2.2 Dermatologie

La dermatologie est plus avancée sur :

- **classification** (lésions, images)
- **ontologies riches** (SNOMED, ICD-10, DermLex)

Écosystème :
- DermGPT (recherche)
- BioGPT / PubMedGPT
- Modèles vision + texte très performants

👉 **Atout clé pour KVS** : dermatologie = terrain idéal pour
- recherche de similarité
- phénotypage
- cohortes comparatives

---

## 3. Où des IA spécialisées apportent une vraie valeur dans KVS 5.2

### 3.1 Recherche de similarité (chantier clé)

Cas évoqué dans ton lien Claude :
> « patients similaires », « cas proches », « situations comparables »

Apports d’IA spécialisées :

- Embeddings cliniques **métier** (et non génériques)
- Pondération implicite des critères (âge, sévérité, associations)
- Raisonnement de type *case-based reasoning*

➡️ **Évolution proposée** :

- Passer de :
  - similarité booléenne / pondérée manuelle
- À :
  - similarité vectorielle métier (LLM ou embedding médical)


### 3.2 Enrichissement des référentiels

- Détection automatique de **patterns émergents**
- Suggestion de nouveaux synonymes / regroupements
- Aide à la maintenance de `communb.csv`


### 3.3 Raisonnement clinique explicite

- Pourquoi ces patients sont similaires ?
- Quelles différences clés ?
- Quels sous-groupes dans une cohorte ?

➡️ Rôle idéal d’un LLM spécialisé (ou fine-tuné léger)

---

## 4. Plan d’action IA – Orthodontie

### Axe 1 – Court terme (simple, ROI immédiat)

1. **Embeddings orthodontiques dédiés**
   - Base : GPT-4o / text-embedding-3-large
   - Corpus :
     - tags.csv
     - commentaires.csv
     - cas patients anonymisés
   - Usage : similarité patient ↔ patient

**Pré-requis** :
- Normalisation des fiches patients
- Pipeline d’anonymisation
- Stockage vecteur (FAISS, pgvector)

---

### Axe 2 – Moyen terme

2. **RAG orthodontique**
   - Corpus : guidelines, littérature, notes cliniques validées
   - LLM généraliste + contexte métier

**Pré-requis** :
- Corpus structuré
- Indexation sémantique
- Stratégie de mise à jour

---

### Axe 3 – Avancé

3. **Fine-tuning léger (LoRA) orthodontie**
   - Sur tâches ciblées :
     - similarité
     - explication clinique
   - Modèle open (LLaMA médical)

**Pré-requis lourds** :
- Dataset annoté
- Expertise ML
- Infrastructure GPU

---

## 5. Plan d’action IA – Dermatologie

### Axe 1 – Court terme

1. **Transposition du moteur KVS orthodontie → dermatologie**
   - Tags dermatologiques
   - Adjectifs spécifiques
   - Âges / localisations

Avantage : réutilisation quasi directe de l’architecture 5.1

---

### Axe 2 – Moyen terme

2. **Recherche de similarité dermatologique**
   - Très forte valeur clinique
   - Cas + images (plus tard)

Pré-requis :
- Ontologie dermatologique
- Nettoyage terminologique

---

### Axe 3 – Avancé

3. **Couplage vision + texte**
   - Modèles multimodaux
   - Analyse photo + contexte clinique

Pré-requis lourds :
- Données image annotées
- Contraintes réglementaires fortes

---

## 6. Ordonnancement global des travaux

1. Embeddings métier (ortho) ⭐⭐⭐
2. Recherche de similarité patient
3. Explicabilité de similarité
4. RAG clinique
5. Extension dermatologie (texte)
6. Fine-tuning ciblé
7. Multimodalité image

---

## 7. Message clé

👉 **KVS n’a pas besoin “d’un LLM orthodontique magique”**.

Sa force est déjà là :
- structuration métier
- hybridation déterministe / IA

La V5.2 doit surtout :
- introduire la **similarité sémantique métier**
- utiliser les LLM spécialisés **comme briques**, pas comme cœur aveugle

---

*Document de travail – destiné à itérations*

