# Synthèse conversation debug27 - KITVIEW Search

## Date et heure de dernière mise à jour : 30/01/2025 19:15

---

## LIVRAISON FINALE - Séparation Chat / Classique

Approche simplifiée : copie de web28 avec toggle masqué et mode forcé.

---

## chat29/ - Mode CHAT

| Fichier | Description |
|---------|-------------|
| chat29.html | web28 + toggle masqué + modePillChat actif |
| chat29.css | web28.css renommé |
| main_chat.js | main.js avec `currentMode='chat'` forcé |
| chatparams.html | webparams renommé |

**Installation :**
```
/ihm/
├── chat29.html
├── chatparams.html
├── css/chat29.css
└── js/
    ├── main_chat.js
    ├── utils.js, voice.js, illustrations.js
    ├── search.js, i18n.js, meme.js
```

---

## clas29/ - Mode CLASSIQUE

| Fichier | Description |
|---------|-------------|
| clas29.html | web28 + toggle masqué + modePillClassique actif |
| clas29.css | web28.css renommé |
| main_clas.js | main.js avec `currentMode='classique'` forcé |
| classparams.html | webparams renommé |

**Installation :**
```
/ihm/
├── clas29.html
├── classparams.html
├── css/clas29.css
└── js/
    ├── main_clas.js
    ├── utils.js, voice.js, illustrations.js
    ├── search.js, i18n.js, meme.js
```

---

## Fichiers communs (à copier dans les deux)

- utils.js
- voice.js  
- illustrations.js
- search.js
- i18n.js
- meme.js

---

## Ce qui a été modifié

### HTML
- Toggle `chatSwitchContainer` : `style="display: none !important;"`
- Chat : `modePillChat` a la classe `active`
- Classique : `modePillClassique` a la classe `active` + `modeToggle` a `checked`

### JS
- `currentMode = 'chat'` ou `'classique'` selon la version

### CSS
- Juste l'en-tête modifié

---

**FIN DE SYNTHÈSE**
