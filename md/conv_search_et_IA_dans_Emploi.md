# conv_search_et_IA_dans_Emploi.md

## Synthèse de conversation

---

### 11/02/2026 — Ajout recherche full-text et chatbot IA dans les modes d'emploi

**Demande :**
1. Renommer `simpleemploi.html` → `modesimple30.html`
2. Ajouter la recherche full-text et l'assistant chatbot IA dans les deux modes d'emploi (`modesimple30.html` et `modedemo30.html`), inspirés de `kvms.html`
3. Utiliser les variables d'environnement serveur (ANTHROPIC_API_KEY, OPENAI_API_KEY) au lieu de clés API côté client
4. Ajouter un endpoint serveur si nécessaire

**Réponse — Fichiers créés/modifiés :**

| Fichier | Action | Description |
|---------|--------|-------------|
| `modesimple30.html` | Créé (renommé depuis simpleemploi.html) | Mode d'emploi simplifié avec recherche full-text + chatbot IA |
| `modedemo30.html` | Modifié | Mode d'emploi démo avec recherche full-text + chatbot IA |
| `server.py` | Modifié (v1.1.9) | Nouveau endpoint POST /ia/help-chatbot + fonction _appeler_anthropic |
| `simple30.html` | Modifié | Lien aide mis à jour : simpleemploi.html → modesimple30.html |

**Détails techniques :**

#### 1. Endpoint serveur `POST /ia/help-chatbot`
- Reçoit : `question`, `page_context` (texte extrait de la page), `history`, `lang`
- Priorité : ANTHROPIC_API_KEY (Claude) → fallback OPENAI_API_KEY (GPT-4o)
- Le contexte de la page (~4000 chars) est envoyé au LLM pour des réponses contextuelles
- Aucune clé API stockée côté navigateur

#### 2. Fonction `_appeler_anthropic()`
- Appel API Anthropic via `https://api.anthropic.com/v1/messages`
- Utilise `anthropic-version: 2023-06-01`
- Modèle par défaut : `claude-sonnet-4-20250514`
- Temperature: 0.3, max_tokens: 1500

#### 3. Recherche full-text dans la page
- Barre de recherche 🔍 dans le bandeau supérieur
- Surlignage jaune/orange des occurrences avec navigation ◀ ▶
- Raccourcis : F3 (suivant), Shift+F3 (précédent), Escape (effacer)
- TreeWalker DOM pour parcourir les nœuds texte sans toucher au code/scripts

#### 4. Chatbot assistant IA
- Bouton flottant bleu en bas à droite
- Modale de chat avec suggestions cliquables
- Appel serveur `POST /ia/help-chatbot` (pas d'appel direct aux API)
- Support du Markdown léger (gras, listes) dans les réponses
- Historique de conversation conservé dans la session

#### 5. Documentation
- Section 5 (simple) / 8 (démo) : Recherche dans le guide
- Section 6 (simple) / 9 (démo) : Assistant IA
- TOC mis à jour avec les nouvelles sections

**Points d'attention :**
- Les variables d'environnement `ANTHROPIC_API_KEY` et `OPENAI_API_KEY` doivent être configurées sur Render
- Le chatbot nécessite que le serveur soit accessible (pas de mode offline)
- Le contexte de page est extrait dynamiquement du DOM pour être envoyé au LLM

---

## Prompts de recréation

### server.py (v1.1.9)
```
Ajouter au server.py existant :
1. Fonction _appeler_anthropic() après _appeler_eden()
2. Endpoint POST /ia/help-chatbot avec modèle HelpChatbotRequest
3. Priorité : ANTHROPIC_API_KEY → OPENAI_API_KEY
PJ nécessaires : server.py (version précédente v1.1.8)
```

### modesimple30.html
```
Renommer simpleemploi.html → modesimple30.html
Ajouter :
- CSS pour recherche full-text et chatbot
- Barre de recherche dans le header
- Sections 5 (Recherche dans le guide) et 6 (Assistant IA)
- HTML chatbot (bouton flottant + modale)
- JavaScript : recherche full-text + chatbot appelant POST /ia/help-chatbot
PJ nécessaires : simpleemploi.html (version précédente)
```

### modedemo30.html
```
Ajouter :
- CSS pour recherche full-text et chatbot
- Barre de recherche dans le header
- Sections 8 (Recherche dans le guide) et 9 (Assistant IA)
- HTML chatbot (bouton flottant + modale)  
- JavaScript : recherche full-text + chatbot appelant POST /ia/help-chatbot
PJ nécessaires : modedemo30.html (version précédente)
```

### simple30.html
```
Modifier le lien du bouton aide :
onclick="window.open('simpleemploi.html', '_blank')" → onclick="window.open('modesimple30.html', '_blank')"
PJ nécessaires : simple30.html (version précédente)
```
