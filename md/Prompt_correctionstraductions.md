# Prompt_correctionstraductions.md

## Objectif
1. Corriger les traductions dans le module IA de Kitview Search
2. Créer une version anglaise du mode d'emploi
3. Implémenter un système de redirection FR ↔ EN simple

## Fichiers à joindre (PJ obligatoires)
- `web20.html` - Interface à modifier → produira `web21.html`
- `server.py` - API à modifier
- `modedemploi.html` - Page d'aide à traduire
- `Prompt_contexte2312.md` - Contexte projet

---

## PARTIE 1 : Modifications web21.html

### 1. Fonction askIA() - Ajouter la langue au payload
Dans le payload, après `question: question`, ajouter :
```javascript
lang: selectedLanguage === 'auto' ? 'fr' : selectedLanguage
```

### 2. Appel showIAModal - Passer la question
Remplacer `showIAModal(response, patient);` par :
```javascript
showIAModal(response, patient, question);
```

### 3. Fonction showIAModal - Ajouter section question
Signature : `function showIAModal(response, patient, question)`
Après le header, ajouter section question avec :
- Fond bleu `var(--primary-color)`
- Texte question en blanc
- Info base/moteur en petits caractères noirs (11px)

---

## PARTIE 2 : Modifications server.py

### 1. IaAskRequest - Ajouter lang
```python
lang: Optional[str] = "fr"
```

### 2. ask_ia() - Prompt multilingue
- Si `lang == 'fr'` : prompt français existant
- Sinon : prompt en anglais avec "You MUST respond in {langue}"

---

## PARTIE 3 : Créer modedemploi_en.html

### Traduction complète de modedemploi.html en anglais

| Section FR | Section EN |
|------------|------------|
| Mode d'emploi | User Guide |
| Sommaire | Contents |
| 1. Présentation | 1. Overview |
| 2. Premier démarrage | 2. Getting Started |
| Écran d'accueil | Home Screen |
| Indicateur d'état | Status Indicator |
| 3. Utilisation de base | 3. Basic Usage |
| Recherche texte | Text Search |
| Recherche vocale | Voice Search |
| Panneau latéral | Side Panel |
| 4. Mode avancé | 4. Advanced Mode |
| Barre d'outils | Toolbar |
| Sélection langue | Language Selection |
| 5. Page Paramètres | 5. Settings Page |
| 5bis. Page Illustrations | 5bis. Illustrations Page |
| 6. Page Analyse | 6. Analytics Page |
| 7. Raccourcis et astuces | 7. Shortcuts and Tips |

### Éléments HTML à traduire
- `<html lang="en">`
- `<title>Kitview Search - User Guide</title>`
- Header : "User Guide", "Back", tooltips
- Popup langue : "User Guide Language", "Select a language"
- Footer : "User Guide v1.0 - January 2026"

### Fonction loadTranslation() pour version anglaise
```javascript
async function loadTranslation(langCode) {
    if (langCode === 'fr') {
        // Redirige vers version française
        window.location.href = 'modedemploi.html';
        return;
    }
    if (langCode === 'en') {
        // Déjà sur version anglaise
        elements.translationInfo.innerHTML = '✓ You are viewing the English version';
        return;
    }
    // Autres langues → message traduction navigateur
    elements.translationInfo.innerHTML = `ℹ️ ${langName} not available. Use browser translation.`;
}
```

---

## PARTIE 4 : Modifier modedemploi.html (version française)

### Fonction loadTranslation() pour version française
```javascript
async function loadTranslation(langCode) {
    if (langCode === 'fr') {
        // Déjà sur version française
        elements.translationInfo.innerHTML = '✓ Vous consultez la version française';
        return;
    }
    // Toute autre langue → redirige vers anglais
    elements.translationInfo.innerHTML = '✓ Redirection vers la version anglaise...';
    window.location.href = 'modedemploi_en.html';
}
```

### Message d'info
Remplacer "Les traductions sont générées à la demande" par :
"💡 Disponible : Français et Anglais"

---

## Fichiers produits

| Fichier | Description |
|---------|-------------|
| `web21.html` | Interface avec traduction IA multilingue |
| `server.py` | API V1.0.50 avec support lang |
| `modedemploi.html` | V1.0.6 - Version française avec redirection vers EN |
| `modedemploi_en.html` | V1.0.5 - Version anglaise complète |

---

## Installation

```
Copier vers c:\cx\ :
- modedemploi.html
- modedemploi_en.html
- web21.html (ou renommer en web20.html)
- server.py
```

## Test

1. Ouvrir `http://localhost:8000/help` → version française
2. Cliquer sur EN → redirige vers version anglaise
3. Sur version anglaise, cliquer FR → retour version française
4. Sur version anglaise, cliquer DE → message "use browser translation"
