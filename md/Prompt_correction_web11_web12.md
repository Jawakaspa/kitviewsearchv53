# Prompt_correction_web11_web12.md

## Objectif

Appliquer les corrections identifiées sur web8/web9/web10 aux fichiers web11 et web12 :
1. **Chargement parallèle** : IA, illustrations et i18n ne bloquent plus sur l'animation de 4 secondes
2. **Fix file://** : Détection du protocole pour supporter l'ouverture directe depuis le système de fichiers
3. **CSS inline** : Si le fichier utilise un CSS externe (webXX.css), réintégrer le CSS inline pour le rendre autonome

---

## Contexte du problème

### Problème 1 : Lenteur de chargement des moteurs IA
La séquence de chargement était 100% séquentielle avec `await` :
```javascript
await loadActiveLanguages();
await loadServerVersion();
await loadAvailableBases();  // ← Contient 4 secondes de délais (animation)
await illustrationsManager.init();  // Bloqué
await loadIAModels();  // Bloqué
await loadI18n();  // Bloqué
```

**Solution** : Charger IA, illustrations et i18n en parallèle, sans attendre l'animation.

### Problème 2 : Erreur CORS en mode file://
Quand on ouvre le fichier HTML directement depuis le système de fichiers (`file:///C:/...`), `window.location.hostname` est vide et `window.location.origin` retourne `'null'`.

Les fichiers `*params.html` utilisaient une détection basée sur `hostname` qui ne gérait pas ce cas.

**Solution** : Ajouter la détection du protocole `file:`.

### Problème 3 : CSS externe manquant
web10.html utilisait `<link rel="stylesheet" href="web10.css">` mais ce fichier CSS n'était pas fourni.

**Solution** : Réintégrer le CSS inline dans le fichier HTML pour le rendre autonome.

---

## Fichiers à joindre en PJ

1. **Prompt_contexte2312.md** - Règles du projet
2. **web11.html** - Version à corriger
3. **web11params.html** - Version à corriger (si existe)
4. **web12.html** - Version à corriger
5. **web12params.html** - Version à corriger (si existe)
6. **web9.html** (V1.1.0 corrigé) - Pour référence du CSS inline si nécessaire

---

## Corrections à appliquer

### 1. Pour les fichiers principaux (web11.html, web12.html)

#### 1.1 Vérifier/corriger API_BASE_URL
S'assurer que la détection file:// est présente :
```javascript
const API_BASE_URL = (function() {
    const origin = window.location.origin;
    // Si on est sur Render ou un serveur web, utiliser l'origine
    if (origin.includes('onrender.com') || origin.startsWith('http://localhost') || origin.startsWith('http://127.0.0.1')) {
        return origin;
    }
    // Si on ouvre le fichier localement (file://), utiliser localhost
    if (origin.startsWith('file://') || origin === 'null') {
        return 'http://localhost:8000';
    }
    // Sinon (autre serveur web), utiliser l'origine
    return origin;
})();
```

#### 1.2 Appliquer le chargement parallèle
Remplacer la séquence de chargement séquentielle par :
```javascript
// ╔════════════════════════════════════════════════════════════════
// ║ Chargement initial v1.1.0 : Parallélisation optimisée
// ╚════════════════════════════════════════════════════════════════

await loadActiveLanguages();
loadSettings();
document.body.classList.add('mode-ia');

// Lancer les chargements en parallèle (sans await)
const iaPromise = loadIAModels().then(ok => {
    if (ok) {
        addDebugLog(`Moteurs IA chargés ✓ (${Object.keys(IA_MODELS_CACHE).length} moteurs)`, 'success');
        updateFiligraneGhost();
    } else {
        addDebugLog('Moteurs IA non disponibles (fallback statique)', 'info');
    }
    return ok;
});

const illusPromise = illustrationsManager.init(API_BASE_URL).then(ok => {
    if (ok) {
        addDebugLog(`Illustrations chargées ✓`, 'success');
    } else {
        addDebugLog('Illustrations non disponibles (fallback)', 'info');
    }
    return ok;
});

const i18nPromise = loadI18n().then(ok => {
    if (ok) {
        addDebugLog(`i18n chargé ✓`, 'success');
    } else {
        addDebugLog('i18n non disponible (fallback français)', 'info');
    }
    return ok;
});

// Version serveur (rapide)
await loadServerVersion();

// Animation de connexion SANS AWAIT (ne bloque plus)
loadAvailableBases();

// Attendre IA + illustrations + i18n en parallèle
await Promise.all([iaPromise, illusPromise, i18nPromise]);

addDebugLog('Application prête', 'success');
```

#### 1.3 Si CSS externe, réintégrer en inline
Si le fichier contient `<link rel="stylesheet" href="webXX.css">` :
1. Supprimer cette ligne
2. Copier tout le contenu CSS de web9.html (lignes 9 à 2618) à la place
3. Ajouter les styles spécifiques du fichier (ex: styles sidebar avec bouton Run)

---

### 2. Pour les fichiers params (web11params.html, web12params.html)

#### 2.1 Corriger API_BASE_URL
Remplacer la détection existante par :
```javascript
const API_BASE_URL = (function() {
    const hostname = window.location.hostname;
    const protocol = window.location.protocol;
    
    // Si on ouvre le fichier directement (file://), forcer localhost:8000
    if (protocol === 'file:') {
        console.log('[API] Mode file:// détecté → http://localhost:8000');
        return 'http://localhost:8000';
    }
    
    // Si on est sur Render (*.onrender.com)
    if (hostname.includes('onrender.com')) {
        return window.location.origin;
    }
    
    // Si on est sur localhost ou IP locale
    if (hostname === 'localhost' || hostname === '127.0.0.1' || hostname.startsWith('192.168.')) {
        return 'http://localhost:8000';
    }
    
    // Sinon, utiliser l'origine actuelle
    return window.location.origin;
})();
```

#### 2.2 Chargement parallèle
Remplacer :
```javascript
await loadAvailableBases();
await loadIAModels();
```

Par :
```javascript
// Charger les données dynamiques EN PARALLÈLE
const basesPromise = loadAvailableBases();
const iaPromise = loadIAModels();

// Attendre les deux en parallèle
await Promise.all([basesPromise, iaPromise]);

console.log('✓ Données dynamiques chargées');
```

---

## Checklist de validation

- [ ] API_BASE_URL détecte le protocole `file:`
- [ ] Chargement parallèle implémenté (Promise.all)
- [ ] Pas de CSS externe (fichier autonome)
- [ ] Version mise à jour dans le cartouche
- [ ] Test ouverture directe depuis système de fichiers (file://)
- [ ] Test avec serveur local (http://localhost:8080)
- [ ] Moteurs IA se chargent rapidement (< 1 seconde)

---

## Versions de référence

| Fichier | Version corrigée |
|---------|------------------|
| web8.html | V1.2.0 |
| web8params.html | V1.0.1 |
| web9.html | V1.1.0 |
| web9params.html | V1.1.1 |
| web10.html | V1.1.0 |
| web10params.html | V1.1.0 |

---

**FIN DU PROMPT**
