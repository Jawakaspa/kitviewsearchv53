# conv_publication51.md
## Synthèse de conversation - Publication V51

**Date de début** : 26/01/2026 14:35
**Dernière mise à jour** : 26/01/2026 16:45

---

## 📋 Résumé des échanges

### Demande initiale (26/01/2026 14:35)
Évolution web25 → web26 avec réorganisation CSS, simplification langue, publication Render.

### Bugs détectés et corrigés (26/01/2026 15:35-16:45)

| Bug | Description | Correction |
|-----|-------------|------------|
| **Mode Classique pauvre** | Contenu différent du Chat, loupe au lieu de chevron | Uniformisé avec Chat |
| **Bases de test affichées** | Toutes les bases visibles | Filtre `base*.db` |
| **webparams API incorrecte** | URL en dur vers v5 | Détection dynamique |
| **Largeur mode Classique** | Espace vide à droite | `width: 100%` |
| **Nouvelle recherche → Chat** | Forçait le mode Chat | Maintient le mode actuel |
| **Pagination scroll infini** | Ajoutait les résultats | Style Google (remplace) |

---

## ✅ Fichiers modifiés

| Fichier | Version | Modifications |
|---------|---------|---------------|
| **main.js** | V2.1.0 | Mode Classique uniformisé, pagination Google, newSearch conserve le mode |
| **search.js** | V2.0.0 | Filtre bases `base*.db` |
| **web26.css** | V1.0.0 | Styles mode Classique uniformisé, `width: 100%` |
| **webparams.html** | V2.0.0 | API_BASE_URL dynamique + filtre bases |

---

## 📦 Structure finale

```
web26/
├── web26.html
├── webparams.html        ← CORRIGÉ (API + filtre bases)
├── css/
│   └── web26.css         ← CORRIGÉ (largeur 100%)
└── js/
    ├── main.js           ← CORRIGÉ (V2.1.0)
    ├── search.js         ← CORRIGÉ (V2.0.0)
    ├── i18n.js           (V2.0.0)
    └── [autres .js]
```

---

## 🔧 Détails des corrections

### 1. Mode Classique uniformisé (main.js V2.1.0)
- **Même contenu** : badges `info-badge-light`, pathologies groupées, tags, commentaires, zone IA
- **Chevron** (▼) au lieu de loupe (🔍)
- **ID patient** visible en haut à gauche
- **Patient référence** en jaune fluo

### 2. Pagination style Google (main.js V2.1.0)
- Mode **Chat** : scroll infini (ajoute les résultats)
- Mode **Classique** : style Google (remplace les résultats)
- Scroll automatique en haut après changement de page

### 3. Nouvelle recherche (main.js V2.1.0)
- Ne force plus le mode Chat
- Maintient le mode actuel (Chat ou Classique)

### 4. webparams.html (V2.0.0)
```javascript
// AVANT (bug)
const API_BASE_URL = hostname === 'localhost' 
    ? 'http://localhost:8000' 
    : 'https://kitviewsearchv5.onrender.com';  // ← URL en dur !

// APRÈS (corrigé)
const API_BASE_URL = (() => {
    if (protocol === 'file:' || hostname === 'localhost') {
        return 'http://localhost:8000';
    }
    return window.location.origin;  // ← Dynamique !
})();
```

### 5. Filtre bases (search.js + webparams.html)
```javascript
const bases = allBases.filter(base => /^base\d+\.db$/i.test(base));
// Garde : base1000.db, base25000.db
// Exclut : test*.db, brut*.db, base1.db, base10.db
```

---

## 🚀 Prochaine étape

Tester les fichiers corrigés en local, puis suivre la marche à suivre GitHub + Render dans ce document.

---

## 📁 Structure finale web26

```
web26/
├── web26.html              (15 Ko)
├── css/
│   └── web26.css           (98 Ko)
└── js/
    ├── utils.js            (2 Ko)
    ├── voice.js            (20 Ko)
    ├── illustrations.js    (23 Ko)
    ├── search.js           (34 Ko)
    ├── i18n.js             (33 Ko) ← V2.0.0
    ├── meme.js             (16 Ko)
    └── main.js             (229 Ko) ← V2.0.1
```

---

## 🚀 MARCHE À SUIVRE : Publication sur Render

### Étape 1 : Préparer le dossier local

```cmd
REM Créer le dossier de publication
mkdir c:\kitviewsearchv51
cd c:\kitviewsearchv51

REM Copier web26 comme base
xcopy /E /I "C:\chemin\vers\web26\*" "c:\kitviewsearchv51\"

REM Créer index.html (copie figée de web26.html)
copy web26.html index.html

REM Créer les dossiers pour index.html (versions figées)
mkdir css_index
mkdir js_index
xcopy /E /I css\* css_index\
xcopy /E /I js\* js_index\
```

**Modifier `index.html`** pour pointer vers les versions figées :
```html
<!-- Remplacer -->
<link rel="stylesheet" href="css/web26.css">
<!-- Par -->
<link rel="stylesheet" href="css_index/web26.css">

<!-- Et pour les scripts, remplacer js/ par js_index/ -->
```

### Étape 2 : Ajouter les fichiers backend

Copier depuis votre projet existant (v5 ou source) :
```
c:\kitviewsearchv51\
├── index.html
├── web26.html
├── webparams.html
├── modedemploi.html (si existe)
├── webanalyse.html (si existe)
├── css/
├── css_index/
├── js/
├── js_index/
├── bases/                  ← Bases de données .db
├── refs/                   ← Fichiers CSV de référence
├── i18n/                   ← Fichiers de traduction
├── main.py                 ← Point d'entrée FastAPI
├── requirements.txt        ← Dépendances Python
└── [autres .py nécessaires]
```

### Étape 3 : Créer le repository GitHub

```cmd
cd c:\kitviewsearchv51
git init
git add .
git commit -m "Initial commit - Kitview Search V51"
```

Puis sur GitHub.com :
1. Créer un nouveau repository : `kitviewsearchv51`
2. Ne PAS initialiser avec README (on a déjà des fichiers)
3. Copier les commandes affichées :

```cmd
git remote add origin https://github.com/VOTRE_USERNAME/kitviewsearchv51.git
git branch -M main
git push -u origin main
```

### Étape 4 : Configurer Render

1. Aller sur https://dashboard.render.com/
2. Cliquer sur **"New +"** → **"Web Service"**
3. Connecter votre repository GitHub `kitviewsearchv51`
4. Configuration :

| Paramètre | Valeur |
|-----------|--------|
| Name | kitviewsearchv51 |
| Region | Frankfurt (EU Central) ou Oregon (US West) |
| Branch | main |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |

5. Variables d'environnement (si nécessaires) :
   - `EDENAI_API_KEY` (si utilisé)
   - `DEEPL_API_KEY` (si utilisé)

6. Cliquer **"Create Web Service"**

### Étape 5 : Vérifier le déploiement

- URL finale : https://kitviewsearchv51.onrender.com/
- Attendre que le build soit terminé (quelques minutes)
- Tester l'application

### Étape 6 : Mises à jour futures

Pour les mises à jour :
```cmd
cd c:\kitviewsearchv51
git add .
git commit -m "Description de la modification"
git push
```
Render redéploiera automatiquement.

---

## 📝 Notes importantes

### Fichiers à NE PAS oublier pour Render
- `requirements.txt` avec toutes les dépendances Python
- Fichiers `.db` dans `/bases/`
- Fichiers CSV dans `/refs/`
- Dossier `/i18n/` avec les traductions

### Différence web26 vs index
- `web26.html` + `css/` + `js/` : Version évolutive (peut changer)
- `index.html` + `css_index/` + `js_index/` : Version figée pour production

---

## 🔄 Prompt de recréation

Pour recréer les fichiers web26 à partir de zéro :

**Fichiers à fournir en PJ** :
- web25.html
- web25.css
- i18n.js (version originale)
- main.js (version originale)
- utils.js, voice.js, illustrations.js, search.js, meme.js

**Prompt** :
```
Créer web26 avec les modifications suivantes :
1. Réorganiser : CSS dans /css/web26.css, JS dans /js/
2. Simplifier la popup langue :
   - Supprimer le footer avec bouton OK
   - Supprimer la section "Réponse" avec switch Origine/FR
   - Clic sur un chip = changement immédiat + fermeture auto popup
3. Ajouter checkbox "→fr" externe dans le header (à côté du bouton langue)
   - Cochée = réponses forcées en français
   - Décochée = réponses dans la langue d'origine
4. Mettre à jour i18n.js V2.0.0 avec :
   - selectLanguageAndClose() pour clic direct
   - closeLangPopup() pour fermeture
   - initResponseFrCheckbox() pour initialiser la checkbox externe
   - updateResponseFrCheckbox() pour synchroniser l'état
5. Mettre à jour main.js pour retirer les références aux éléments supprimés
```

---

**Dernière mise à jour** : 26/01/2026 15:10
