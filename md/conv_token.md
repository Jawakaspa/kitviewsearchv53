# conv_token — Synthèse de conversation

## 19/02/2026 11:30 — Audit d'utilisation des tokens

### Question
Thierry demande un audit de sa consommation de tokens pour optimiser son usage sans perdre en qualité. Première intuition : réduire la taille des fichiers joints. Question initiale : comparer l'impact des 3 bases (base1.db, base10.db, base100.db) pour une requête simple.

### Réponses

**Comparaison .db :** Les fichiers SQLite étant binaires, ils ne sont PAS injectés dans la fenêtre de contexte. Impact identique (quasi nul) quelle que soit la taille. Si c'étaient des CSV, le ratio serait ×100 entre base1 et base100.

**Audit complet des 5 conversations du projet :**

Les principaux postes de consommation identifiés :

| Priorité | Poste | Impact |
|----------|-------|--------|
| 🔴 | Conversations longues (historique cumulatif) | MAJEUR |
| 🔴 | Fichiers complets (.py/.html) collés dans le chat | FORT |
| 🟡 | Prompt_contexte0502.md (~3500 tokens × chaque message) | MOYEN |
| 🟡 | Itérations de debug successives | MOYEN |
| 🟢 | Fichiers .db uploadés | NÉGLIGEABLE |

**7 recommandations émises :**
- R1 : Limiter conversations à ~10 échanges (gain 30-50%)
- R2 : Ne coller que les zones concernées, pas les fichiers entiers (gain 20-40%)
- R3 : Alléger le Prompt_contexte (passer de ~3500 à ~1500 tokens)
- R4 : Demander des réponses concises quand suffisant
- R5 : Privilégier .db aux .csv pour les uploads
- R6 : Être précis dès le 1er message
- R7 : Grouper les demandes liées

---

## 19/02/2026 11:40 — Version allégée du Prompt_contexte

### Question
Thierry valide la proposition d'alléger le Prompt_contexte.

### Réponse
Analyse section par section du fichier original (32 sections identifiées) :
- 16 sections GARDER (essentielles à chaque échange)
- 15 sections ANNEXE (utiles ponctuellement)
- 1 section SUPPRIMER (meta-info inutile)

Deux fichiers produits :

| Fichier | Rôle | Tokens |
|---------|------|--------|
| `Prompt_contexte_light.md` | Fichier projet permanent | ~755 |
| `Prompt_contexte_annexe.md` | Joint en PJ à la demande | ~1 293 |
| Original `Prompt_contexte0502.md` | Remplacé | ~3 400 |

**Résultat : -78% de tokens par message** (~2 645 tokens économisés par échange).
Sur 10 échanges × 5 conversations = ~132 000 tokens économisés.

### Mise en œuvre
1. Remplacer `Prompt_contexte0502.md` par `Prompt_contexte_light.md` dans les fichiers du projet
2. Garder `Prompt_contexte_annexe.md` hors du projet, à joindre en PJ quand on parle de BDD, architecture SQL, affichage chatbot, pipeline cerbere/horodateur, checklist de livraison
