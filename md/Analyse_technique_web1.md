# Prompt Analyse_technique_web1 V1.0.0 - 11/12/2025 17:45:46

# Analyse technique de web1.html

## 1. Framework et technologie

### 🔧 Aucun framework !

**web1.html est développé en "Vanilla JS"** (JavaScript pur, sans framework).

| Question | Réponse |
|----------|---------|
| React ? | ❌ Non |
| Angular ? | ❌ Non |
| Vue.js ? | ❌ Non |
| jQuery ? | ❌ Non |
| Bootstrap ? | ❌ Non |
| Tailwind ? | ❌ Non |

### Pourquoi ce choix ?

| Avantage | Explication |
|----------|-------------|
| **Zéro dépendance** | Pas de npm, pas de build, pas de node_modules |
| **Fichier unique** | 1 seul fichier HTML = déploiement simple |
| **Performance** | Pas de surcharge framework (~50-200 Ko économisés) |
| **Maintenabilité** | Pas de breaking changes de versions |
| **Compatibilité** | Fonctionne partout, même en file:// |

### Inconvénients

| Inconvénient | Impact |
|--------------|--------|
| Pas de composants réutilisables | Code plus verbeux |
| Pas de gestion d'état centralisée | Variables globales |
| Pas de routing | Page unique |

---

## 2. Architecture du fichier

### Répartition des sections

```
┌─────────────────────────────────────────────────────────────┐
│ web1.html (5575 lignes)                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ <style> CSS (lignes 9-2074)                         │   │
│  │ ≈ 2065 lignes (37%)                                 │   │
│  │                                                     │   │
│  │ • Variables CSS (:root)                             │   │
│  │ • Styles Classique                                  │   │
│  │ • Surcharges Liquid Glass [data-style="glass"]      │   │
│  │ • Media queries responsive                          │   │
│  │ • Thème sombre [data-theme="dark"]                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ <body> HTML (lignes 2075-2446)                      │   │
│  │ ≈ 372 lignes (7%)                                   │   │
│  │                                                     │   │
│  │ • Header (logo, contrôles)                          │   │
│  │ • Sidebar (navigation, exemples)                    │   │
│  │ • Zone principale (welcome, résultats)              │   │
│  │ • Modales (paramètres, langue)                      │   │
│  │ • Debug panel                                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ <script> JavaScript (lignes 2447-5574)              │   │
│  │ ≈ 3127 lignes (56%)                                 │   │
│  │                                                     │   │
│  │ • Configuration & variables globales                │   │
│  │ • Dictionnaires de traduction                       │   │
│  │ • Fonctions métier (65 fonctions)                   │   │
│  │ • Event listeners                                   │   │
│  │ • Initialisation                                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Diagramme de proportions

```
CSS ████████████████████████████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  37%
HTML ██████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░   7%
JS  ████████████████████████████████████████████████████████░░░░░░░░░░░░  56%
```

---

## 3. Arborescence des fonctionnalités

```
web1.html
│
├── 🎨 STYLES (CSS)
│   ├── Variables CSS (:root)
│   │   ├── Couleurs principales (--primary-color, --bg-primary, etc.)
│   │   ├── Variables Glass (--glass-bg, --glass-blur, etc.)
│   │   └── Rayons et ombres (--card-radius, --shadow, etc.)
│   │
│   ├── Thème Classique (défaut)
│   │   ├── Header sobre
│   │   ├── Cards avec bordures
│   │   └── Fond blanc/gris
│   │
│   ├── Thème Liquid Glass [data-style="glass"]
│   │   ├── Fond gradient (violet/rose)
│   │   ├── Glassmorphism (blur, transparence)
│   │   ├── Effets hover lumineux
│   │   └── Reflets et ombres colorées
│   │
│   ├── Mode sombre [data-theme="dark"]
│   │   ├── Fond sombre
│   │   └── Texte clair
│   │
│   └── Responsive (media queries)
│       ├── Mobile (< 768px)
│       ├── Tablette (768-1024px)
│       ├── Desktop (1024-1920px)
│       └── Multi-écrans (> 1920px)
│
├── 🏗️ STRUCTURE (HTML)
│   │
│   ├── Header (.header)
│   │   ├── Logo Kitview
│   │   ├── Sélecteur de base de données
│   │   ├── Compteur patients
│   │   ├── Bouton langue (popup chips)
│   │   ├── Mode recherche (SC/SP/SE)
│   │   ├── Toggle IA/Classique
│   │   ├── Toggle thème clair/sombre
│   │   └── Roue dentée (paramètres)
│   │
│   ├── Sidebar (.sidebar)
│   │   ├── Bouton "Nouvelle recherche"
│   │   ├── Conversations récentes
│   │   ├── Exemples de recherche
│   │   ├── Toggle démo
│   │   ├── Version serveur
│   │   └── Handle resize (redimensionnable)
│   │
│   ├── Zone principale
│   │   ├── Welcome container (accueil)
│   │   │   ├── Message de bienvenue
│   │   │   ├── Input recherche central
│   │   │   └── Filigrane animé
│   │   │
│   │   ├── Results container (résultats)
│   │   │   ├── Mode IA (cards grid)
│   │   │   └── Mode Classique (liste)
│   │   │
│   │   ├── Search container bottom (mode IA)
│   │   └── Search container top (mode Classique)
│   │
│   ├── Modales
│   │   ├── Modal Paramètres (#settingsModal)
│   │   │   ├── Nom utilisateur
│   │   │   ├── Thème (auto/clair/sombre)
│   │   │   ├── Style (classique/glass) ← NOUVEAU
│   │   │   ├── Limite résultats
│   │   │   ├── Taille page
│   │   │   ├── Mode debug
│   │   │   ├── Intensité filigrane
│   │   │   ├── Durée cycle démo
│   │   │   ├── Clé API DeepL
│   │   │   └── Exemples personnalisés
│   │   │
│   │   └── Popup Langue (#langPopup)
│   │       ├── Chips de langues (11)
│   │       └── Toggle réponse (origine/FR)
│   │
│   └── Debug panel (#debugPanel)
│       ├── Historique des logs
│       ├── Bouton copier
│       └── Bouton effacer
│
├── ⚙️ JAVASCRIPT - Variables globales
│   ├── Configuration
│   │   ├── API_BASE_URL (auto-détecté)
│   │   ├── DEFAULT_BASE
│   │   └── DEFAULT_EXAMPLES
│   │
│   ├── État application
│   │   ├── currentBase (base sélectionnée)
│   │   ├── currentMode ('ia' | 'classique')
│   │   ├── currentStyle ('classic' | 'glass')
│   │   ├── searchMode ('sc' | 'sp' | 'se')
│   │   └── debugMode (boolean)
│   │
│   ├── Langue
│   │   ├── selectedLanguage ('fr', 'en', etc.)
│   │   ├── responseLanguage ('same' | 'fr')
│   │   └── lastSearchLang
│   │
│   ├── Pagination
│   │   ├── currentPage
│   │   ├── pageSize
│   │   └── resultsLimit
│   │
│   ├── Historique
│   │   └── conversationHistory[]
│   │
│   ├── Filigrane
│   │   ├── illustrations (medical, search, zero)
│   │   ├── piles (pools d'images)
│   │   └── filigraneIntensity
│   │
│   └── Mode démo
│       ├── demoMode, demoPhase
│       ├── demoDuration, demoProgress
│       └── demoTimers
│
├── ⚙️ JAVASCRIPT - Dictionnaires
│   ├── LANGUES (11 langues + auto)
│   │   └── { code, nom, flag }
│   │
│   ├── MESSAGES_RESULTATS (11 langues)
│   │   └── { patient, patients, trouve, avec, aucun, affiches, pageSuivante, tous }
│   │
│   ├── MESSAGES_LANG_INFO (11 langues)
│   │   └── { detected, searchIn }
│   │
│   └── LANG_TO_FLAG
│       └── { 'fr': 'fr', 'en': 'gb', ... }
│
└── ⚙️ JAVASCRIPT - Fonctions (65)
    │
    ├── 🖼️ Filigrane (8 fonctions)
    │   ├── shuffle() - Mélanger un tableau
    │   ├── rechargerPile() - Recharger pile d'images
    │   ├── tirerImage() - Tirer image de la pile
    │   ├── updateFiligraneGhost() - Mettre à jour le fond
    │   ├── applyFiligraneIntensity() - Appliquer intensité
    │   ├── hideFiligraneForResults() - Masquer pour résultats
    │   ├── restoreFiligraneIntensity() - Restaurer intensité
    │   └── animateFiligraneFromMax() - Animation 100% → cible
    │
    ├── 🎬 Mode démo (7 fonctions)
    │   ├── startDemoMode() - Démarrer la démo
    │   ├── stopDemoMode() - Arrêter la démo
    │   ├── runDemoCycleA() - Cycle nouvelle recherche
    │   ├── runDemoCycleB() - Cycle exemple
    │   ├── runDemoSearch() - Lancer recherche démo
    │   ├── decideNextDemoCycle() - Choisir prochain cycle
    │   ├── updateDemoProgress() - Mettre à jour progression
    │   └── startDemoProgressAnimation() - Animer le ring
    │
    ├── 💾 Persistance (3 fonctions)
    │   ├── loadSettings() - Charger depuis localStorage
    │   ├── saveSettings() - Sauvegarder dans localStorage
    │   └── saveConversationHistory() - Sauvegarder historique
    │
    ├── 🌍 Multilingue (12 fonctions)
    │   ├── formatResultMessage() - Message résultat traduit
    │   ├── formatPaginationMessage() - Message pagination traduit
    │   ├── getNextPageText() - Texte "Page suivante" traduit
    │   ├── createLangInfoMessage() - Bannière langue détectée
    │   ├── getFlagUrl() - URL drapeau flagcdn.com
    │   ├── generateLangChips() - Générer chips de langue
    │   ├── updateLangButton() - Mettre à jour bouton langue
    │   ├── updateResponseSwitchLabels() - Mettre à jour labels
    │   ├── updateLangAfterResponse() - MAJ après réponse
    │   ├── toggleLangPopup() - Ouvrir/fermer popup
    │   ├── setQuestionLanguage() - Définir langue question
    │   └── setResponseLanguage() - Définir langue réponse
    │
    ├── 🎨 Apparence (5 fonctions)
    │   ├── applyTheme() - Appliquer thème (auto/light/dark)
    │   ├── toggleTheme() - Basculer thème
    │   ├── applyStyle() - Appliquer style (classic/glass)
    │   ├── toggleStyle() - Basculer style
    │   └── switchMode() - Basculer IA/Classique
    │
    ├── 🔌 API & Données (6 fonctions)
    │   ├── loadServerVersion() - Charger version serveur
    │   ├── loadAvailableBases() - Charger bases disponibles
    │   ├── loadPatientCount() - Charger nombre patients
    │   ├── getSearchEndpoint() - Obtenir endpoint selon langue
    │   ├── buildSearchPayload() - Construire payload recherche
    │   └── searchPatients() - Rechercher patients (async)
    │
    ├── 📊 Affichage résultats (8 fonctions)
    │   ├── renderResponse() - Afficher réponse complète
    │   ├── createPatientElement() - Créer élément patient
    │   ├── createPatientCardIA() - Créer card mode IA
    │   ├── createDetailSectionCard() - Créer section détail
    │   ├── createPatientItemClassique() - Créer item mode Classique
    │   ├── copyResponse() - Copier réponse
    │   ├── renderConversationHistory() - Afficher historique
    │   └── renderRecentConversations() - Afficher récentes (sidebar)
    │
    ├── 🔧 Utilitaires (4 fonctions)
    │   ├── normalizeText() - Normaliser texte
    │   ├── capitalize() - Première lettre majuscule
    │   ├── formatDateToFR() - Date au format français
    │   └── getActiveSearchInput() - Input actif selon mode
    │
    ├── 🖱️ Interactions (5 fonctions)
    │   ├── initElements() - Initialiser éléments DOM
    │   ├── updateSearchButtonState() - État boutons recherche
    │   ├── setButtonLoading() - État loading bouton
    │   ├── attachInputListeners() - Attacher listeners inputs
    │   └── newSearch() - Nouvelle recherche (reset)
    │
    ├── 📝 UI (2 fonctions)
    │   ├── renderExamples() - Afficher exemples sidebar
    │   └── (Event listeners inline)
    │
    └── 🐛 Debug (5 fonctions)
        ├── updateDebugConsole() - Afficher/masquer console
        ├── addDebugLog() - Ajouter log
        ├── clearDebugLog() - Effacer logs
        ├── copyDebugLog() - Copier logs
        └── closeDebugPanel() - Fermer panel
```

---

## 4. Flux de données

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Saisie    │────▶│  Payload    │────▶│   Backend   │
│   (input)   │     │  JSON       │     │   FastAPI   │
└─────────────┘     └─────────────┘     └─────────────┘
                                              │
                                              ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Affichage  │◀────│  Rendu      │◀────│  Réponse    │
│  (cards)    │     │  (render)   │     │  JSON       │
└─────────────┘     └─────────────┘     └─────────────┘
                          │
                          ▼
                    ┌─────────────┐
                    │ localStorage│
                    │ (historique)│
                    └─────────────┘
```

---

## 5. Technologies utilisées

| Couche | Technologie | Version |
|--------|-------------|---------|
| Markup | HTML5 | - |
| Style | CSS3 | Variables, Grid, Flexbox, backdrop-filter |
| Logique | JavaScript ES6+ | async/await, arrow functions, template literals |
| Icônes | Emoji Unicode | 🔍 ⚙️ 🌙 etc. |
| Drapeaux | flagcdn.com | API externe |
| Stockage | localStorage | Web API native |
| Serveur | FastAPI | Python (backend séparé) |

---

## 6. Résumé

**web1.html** est une **Single Page Application (SPA) Vanilla JS** :

- ✅ **Zéro dépendance** npm/framework
- ✅ **Fichier unique** auto-suffisant (sauf backend)
- ✅ **Responsive** mobile-first
- ✅ **Bilingue** (11 langues)
- ✅ **Bi-thème** (clair/sombre)
- ✅ **Bi-style** (classique/glass)
- ✅ **Persistant** (localStorage)

C'est une approche "old school" mais robuste, parfaitement adaptée pour une application métier spécifique ne nécessitant pas l'écosystème complexe des frameworks modernes.
