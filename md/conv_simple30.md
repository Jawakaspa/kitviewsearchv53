# conv_simple30 — Synthèse de conversation

## 2025-02-11 11:50 — Demande initiale

**Question** : Simplifier l'interface chat29.html → simple30.html en supprimant les options de paramétrage complexes tout en conservant toutes les fonctionnalités de recherche.

**Réponse** : Analyse des 9 fichiers source (HTML 14K, CSS 109K, JS principal 246K + 6 utilitaires). Identification des éléments à supprimer et des éléments à conserver.

## 2025-02-11 ~12:00 — Clarifications et décisions

| Question | Réponse |
|----------|---------|
| Sélecteurs header tous visibles ou toolbar cachée ? | Tous visibles directement |
| Fichiers utilitaires : renommage ? | Copie avec préfixe `simple30_` |
| Agencement header ? | ☰ Logo Search [base] [langue] [détection] 🌙 |

## 2025-02-11 ~12:10 — Construction HTML + copie utilitaires

- ✅ `simple30.html` créé (header simplifié, sans toolbar toggle/demo/help/analyse/settings)
- ✅ 6 fichiers JS utilitaires copiés avec renommage `simple30_*`

## 2025-02-11 ~13:00 — Construction simple30_main.js

Modifications chirurgicales sur main_chat.js (4775 → 4306 lignes) :

**Supprimé :**
- Variables démo : `demoMode`, `demoDuration`, `demoTimers`, `demoPhase`, `demoProgress`
- Fonctions démo : `updateDemoProgress`, `startDemoMode`, `stopDemoMode`, `runDemoCycleA/B`, `runDemoSearch`, `decideNextDemoCycle`, `startDemoProgressAnimation`
- `applyBandeauStates()` — tout toujours visible dans simple30
- Event listeners : `searchToolbarToggle`, `settingsButton` (navigation webparams), `demoToggle`
- Second `DOMContentLoaded` (gestion visibilité bandeau)
- `window.addEventListener('storage')` (synchronisation inter-onglets avec webparams)
- Références `baseSelectorSettings`
- Paramètres localStorage bandeau : `activeTheme`, `bandeauTheme`, `activeStyle`, `bandeauBases`, etc.

**Modifié :**
- `loadSettings()` : nettoyé des paramètres bandeau/démo
- `initElements()` : supprimé `searchToolbarToggle`, `headerToolbar`, `settingsButton`, `demoToggle`, `demoProgressRing`
- `toggleTheme()` : utilise `localStorage.getItem('theme')` au lieu de `elements.themeSelect.value`
- `matchMedia` listener : même correction localStorage
- **Score badge relocalisé** : de `position: absolute; top: 6px; right: 8px` sur la carte → `display: inline-block` **AVANT** le titre PATHOLOGIES (dans `createPatientCardChat` ET `createPatientItemClassique`)

## 2025-02-11 ~13:15 — Construction simple30.css

Modifications chirurgicales sur chat29.css (3695 → 3556 lignes) :

**Supprimé :**
- `.search-toggle-container` + `.search-toggle-checkbox` + `.search-toggle-visual` (48 lignes)
- `.header-toolbar.hidden` (7 lignes)
- `.help-button` + `.help-button:hover` (22 lignes)
- `.demo-switch` + `.demo-label` + `.demo-progress-ring` + animation `pulse-ring` (52 lignes)
- `[data-theme="dark"] .help-button` + `[data-style="glass"] .help-button` (10 lignes)

## Livrables

```
simple30/
├── simple30.html              (12K)  — HTML simplifié
├── css/
│   └── simple30.css           (104K) — CSS nettoyé
└── js/
    ├── simple30_utils.js      (2K)   — Utilitaires
    ├── simple30_voice.js      (20K)  — Reconnaissance vocale
    ├── simple30_illustrations.js (23K) — Filigrane/images
    ├── simple30_search.js     (36K)  — API recherche
    ├── simple30_i18n.js       (33K)  — Internationalisation
    ├── simple30_meme.js       (15K)  — Logique "même que"
    └── simple30_main.js       (229K) — Code principal simplifié
```

Total : 468K (9 fichiers)
