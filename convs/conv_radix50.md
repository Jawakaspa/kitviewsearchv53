# Prompt conv_radix50 V1.0.0 - 19/12/2025 19:28:09

# Synthèse de conversation : radix50

**Projet** : Kitview - Recherche multilingue patients orthodontie  
**Date de création** : 18/12/2025

---

## Échange 1 — 18/12/2025 16:08

### Question de Thierry

Conception d'un système de codage compact pour stocker les pathologies et leurs adjectifs :
- Table avec ~100 000 patients
- Max 10 pathologies par patient
- < 1000 pathologies canoniques, < 1000 adjectifs
- Chaque pathologie peut avoir 0 à 5 adjectifs (ordre alphabétique imposé)
- Les synonymes partagent le même code que leur forme canonique

**Exemple proposé** (format chaîne type Soundex) :
- `Béance` → `134 000 000 000 000 000`
- `Béance gauche latérale sévère` → `134 023 012 435 000 000`
- `Béance antérieure droite sévère` → `134 112 349 435 000 000`

Objectif : recherche efficace par préfixe (`LIKE%`) ou IA.

### Réponse de Claude

**Points forts identifiés** :
1. Gestion élégante des synonymes (un seul code)
2. Recherche par préfixe efficace pour la pathologie seule
3. Tri alphabétique des adjectifs (évite les permutations)

**Problème majeur** :
La recherche "pathologie + adjectif à n'importe quelle position" nécessite de tester 5 positions → non indexable, `SUBSTR()` répétés = lent.

**3 options proposées** :

| Option | Description | Avantages | Inconvénients |
|--------|-------------|-----------|---------------|
| **A** (recommandée) | Colonnes séparées : `patho_code`, `adj1`...`adj5` | Indexable, simple | 6 colonnes |
| **B** | Table de jointure normalisée | Flexible | Plus de jointures |
| **C** | Bitmap d'adjectifs (1 bit/adj) | Compact | Complexe |

**Question posée** : Recherches avec combien d'adjectifs typiquement ?

---

## Échange 2 — 18/12/2025 16:08

### Réponse de Thierry

Principalement **1 adjectif maximum** dans les recherches.

### Recommandation affinée de Claude

Structure optimisée pour ce cas d'usage :

```sql
CREATE TABLE patient_pathologies (
    patient_id    INTEGER NOT NULL,
    patho_code    SMALLINT NOT NULL,  -- 0-999
    adj1-adj5     SMALLINT DEFAULT 0
);

-- Index clés
CREATE INDEX idx_patho ON patient_pathologies(patho_code);
CREATE INDEX idx_patho_adj1 ON patient_pathologies(patho_code, adj1);
```

**Requête type "pathologie + 1 adjectif"** :
```sql
WHERE patho_code = 134 AND 435 IN (adj1, adj2, adj3, adj4, adj5)
```

**Stockage** : ~16 octets/ligne → ~16 Mo max pour 100k patients × 10 patho.

---

---

## Échange 3 — 18/12/2025 16:09

### Question de Thierry

Question stratégique : le système actuel (regex/IA → JSON → SQL jointures) fonctionne bien avec des temps de 1-18 ms côté SQL. **Est-ce que le projet de codage numérique a un bon ROI ?**

Thierry partage aussi la réponse enthousiaste de ChatGPT et un fichier de test (`radix100_out.csv`) montrant 50 requêtes avec temps de réponse.

### Analyse de Claude

**Constat clé** : Les temps SQL actuels (1-18 ms) sont déjà excellents. Le goulot d'étranglement est la détection IA (~4700 ms), pas le SQL.

| Composant | Temps actuel | Gain potentiel |
|-----------|--------------|----------------|
| Détection IA | 4700 ms | 0 |
| SQL jointures | 1-18 ms | ~0.5-5 ms |
| **Gain total** | — | **~0.3%** |

**Recommandation** : **Ne pas investir maintenant** dans le codage numérique.

**Priorités à meilleur ROI** :
1. Optimiser la détection IA (cache, modèle léger)
2. Améliorer le fallback regex
3. Alignement detall/detia (31.7% concordance actuelle)

**Cas où le codage numérique serait pertinent** :
- 1M+ patients
- Requêtes SQL > 500 ms
- Agrégations statistiques massives

---

## Décisions actées

- [x] Codage numérique : **reporté** (ROI insuffisant)
- [ ] Focus sur alignement detall/detia

---

## Échange 4 — 18/12/2025 16:15

### Question de Thierry

Comparer d'autres modèles IA à Claude Sonnet 3.7 (baseline Eden AI) :
- OpenAI via API directe (licence existante)
- Modèles légers sur Eden AI

### Recommandations de Claude

**5 modèles à benchmarker** :

| Alias court | Identifiant complet | Provider | Type |
|-------------|---------------------|----------|------|
| `claude-sonnet` | `anthropic/claude-3-7-sonnet-20250219` | Eden | Baseline |
| `claude-haiku` | `anthropic/claude-3-5-haiku-latest` | Eden | Léger |
| `gemini-2.5-flash` | `google/gemini-2.5-flash` | Eden | Léger |
| `gpt-4o` | `openai/gpt-4o` | Eden | Puissant |
| `gpt-4o-mini` | `openai/gpt-4o-mini` | Eden | Léger |

### Modification detia.py

**V1.1.0** : Ajout du support `gemini-2.5-flash` dans :
- `MODEL_SIMPLE_NAMES`
- `SUPPORTED_MODELS`

**Usage CLI** :
```bash
python detia.py "béance sévère" --model claude-haiku
python detia.py "béance sévère" --model gemini-2.5-flash
python detia.py "béance sévère" --model gpt-4o-mini
python detia.py tests/testscompletsin.csv --model gemini-2.5-flash
```

---

## Fichiers générés cette session

| Fichier | Version | Description |
|---------|---------|-------------|
| `detia.py` | 1.1.0 | Ajout Gemini 2.5 Flash |