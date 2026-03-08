/**
 * illustrations.js V1.0.0 - 24/01/2026
 * Module de gestion des illustrations, filigrane et mode démo
 * 
 * Modules inclus :
 * - illustrationsManager : Gestion des bandeaux avec images
 * - Filigrane : Fond fantomatique avec support moteur IA
 * - Mode Démo : Démonstration automatique
 * 
 * Dépendances :
 * - Variable globale `window.API_BASE_URL`
 * - Variable globale `window.IA_MODELS_CACHE`
 * - Variable globale `window.DEBUG`
 * - Fonction `t()` pour traduction (i18n)
 * - Fonction `addDebugLog()` pour logs
 * - Variable `detectionMode` pour le moteur IA
 * - Variable `filigraneIntensity` pour l'intensité du filigrane
 * - Éléments DOM : filigraneGhost, loading, bandeauLoading, etc.
 */

/* ═══════════════════════════════════════════════════════════════════════
   ILLUSTRATIONS v1.3 - MODULE GESTION DES BANDEAUX
   Rotation aléatoire sans répétition jusqu'à avoir tout vu
   ═══════════════════════════════════════════════════════════════════════ */

const illustrationsManager = (function() {
    
    // État interne
    let illustrations = { medical: [], search: [], zero: [] };
    let piles = { result: [], zero: [] };
    let initialized = false;
    
    // Mélange Fisher-Yates
    function shuffle(array) {
        const result = [...array];
        for (let i = result.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [result[i], result[j]] = [result[j], result[i]];
        }
        return result;
    }
    
    // Recharge une pile
    function rechargerPile(type) {
        if (type === 'result') {
            piles.result = shuffle([...illustrations.medical, ...illustrations.search]);
        } else if (type === 'zero') {
            piles.zero = shuffle([...illustrations.zero]);
        }
    }
    
    // Tire une image
    function tirerImage(type) {
        if (piles[type].length === 0) rechargerPile(type);
        if (piles[type].length === 0) return null;
        return piles[type].pop();
    }
    
    return {
        async init(apiBaseUrl) {
            const baseUrl = apiBaseUrl || window.API_BASE_URL || 'http://localhost:8000';
            try {
                if (window.DEBUG) console.log('[Illustrations] Chargement depuis', baseUrl + '/illustrations');
                const response = await fetch(baseUrl + '/illustrations');
                if (!response.ok) throw new Error(`HTTP ${response.status}`);
                const data = await response.json();
                
                illustrations.medical = data.medical || [];
                illustrations.search = data.search || [];
                illustrations.zero = data.zero || [];
                
                rechargerPile('result');
                rechargerPile('zero');
                initialized = true;
                
                const total = illustrations.medical.length + illustrations.search.length + illustrations.zero.length;
                if (window.DEBUG) console.log(`[Illustrations] Chargées: ${total} images (medical:${illustrations.medical.length}, search:${illustrations.search.length}, zero:${illustrations.zero.length})`);
                return true;
            } catch (error) {
                console.warn('[Illustrations] Erreur de chargement:', error.message);
                initialized = false;
                return false;
            }
        },
        
        isInitialized() { return initialized; },
        hasImages() { return illustrations.medical.length + illustrations.search.length > 0; },
        
        getResultImage() { return tirerImage('result'); },
        getZeroImage() { return tirerImage('zero'); },
        getFiligraneImage() { return tirerImage('result'); },
        
        // v1.1.1 : Retourne l'URL du logo Kitview (id=0 dans illustrations.csv)
        getLogoImage() {
            // URL fixe du logo Kitview (même que dans le header)
            return 'https://www.kitview.com/wp-content/uploads/2023/03/cropped-logo-kitview-1.png';
        },
        
        // v1.2.0 : Retourne une image aléatoire pour "Nouvelle recherche" (search ou medical uniquement)
        getNewSearchImage() {
            return tirerImage('result');
        },
        
        // v1.2.0 : Retourne l'URL de l'image actuellement affichée dans le filigrane
        getCurrentFiligraneImage() {
            const filigraneEl = document.getElementById('filigraneGhost');
            if (!filigraneEl) return null;
            const bgImage = filigraneEl.style.backgroundImage;
            if (!bgImage || bgImage === 'none') return null;
            // Extraire l'URL de "url('...')"
            const match = bgImage.match(/url\(['"]?([^'"]+)['"]?\)/);
            return match ? match[1] : null;
        },
        
        // v1.3.0 : Retourne l'URL de l'image d'un moteur IA
        // v1.3.2 : Utilise window.IA_MODELS_CACHE pour accès global
        getMoteurImage(moteur) {
            if (typeof window.IA_MODELS_CACHE !== 'undefined' && moteur && window.IA_MODELS_CACHE[moteur]) {
                const model = window.IA_MODELS_CACHE[moteur];
                if (model && model.image && model.image.trim() !== '') {
                    return model.image.trim();
                }
            }
            return null;
        },
        
        // Crée le HTML du bandeau "X patients" (mode COUNT)
        // v1.3.0 : Affiche l'image du moteur à gauche
        createResultBanner(count, criteria, time, onClickCallback, moteur) {
            // v1.3.0 : Priorité à l'image du moteur, fallback sur image aléatoire
            let imageUrl = this.getMoteurImage(moteur);
            if (!imageUrl) {
                imageUrl = this.getResultImage();
            }
            
            const banner = document.createElement('div');
            banner.className = 'bandeau-count';
            
            if (imageUrl) {
                banner.innerHTML = `
                    <div class="illustration">
                        <img src="${imageUrl}" alt="${moteur || 'Résultat'}" onerror="this.style.display='none'">
                    </div>
                    <div class="bandeau-content">
                        <div class="message-principal">🎯 ${count === 1 ? 'J\'ai trouvé 1 patient' : `J'ai trouvé ${count} patients`}</div>
                        <div class="message-secondaire">${time ? `en ${time}` : ''}</div>
                    </div>
                    <button class="btn-voir"><span>👁️</span> Voir</button>
                `;
            } else {
                // Fallback sans image
                banner.innerHTML = `
                    <div class="bandeau-content" style="padding-left: 30px;">
                        <div class="message-principal">🎯 ${count === 1 ? 'J\'ai trouvé 1 patient' : `J'ai trouvé ${count} patients`}</div>
                        <div class="message-secondaire">${time ? `en ${time}` : ''}</div>
                    </div>
                    <button class="btn-voir"><span>👁️</span> Voir</button>
                `;
            }
            
            if (onClickCallback) {
                banner.querySelector('.btn-voir').addEventListener('click', onClickCallback);
            }
            
            return banner;
        },
        
        // Crée le HTML du bandeau "0 patients"
        // v1.3.0 : Affiche "Aucun patient trouvé pour [question]" sans message secondaire
        createZeroBanner(query) {
            const imageUrl = this.getZeroImage();
            const banner = document.createElement('div');
            banner.className = 'bandeau-zero';
            
            // Construire le message principal avec la question
            const messagePrincipal = query 
                ? `Aucun patient trouvé pour ${query}`
                : (typeof t === 'function' ? t('Aucun patient trouvé') : 'Aucun patient trouvé');
            
            if (imageUrl) {
                banner.innerHTML = `
                    <div class="illustration">
                        <img src="${imageUrl}" alt="Aucun résultat" onerror="this.style.display='none'">
                    </div>
                    <div class="bandeau-content">
                        <div class="message-principal">${messagePrincipal}</div>
                    </div>
                `;
            } else {
                // Fallback SVG
                banner.innerHTML = `
                    <div class="illustration">
                        <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
                            <circle cx="100" cy="100" r="90" fill="rgba(255,255,255,0.1)"/>
                            <circle cx="100" cy="80" r="35" fill="#FFE0BD"/>
                            <ellipse cx="88" cy="75" rx="5" ry="6" fill="#333"/>
                            <ellipse cx="112" cy="75" rx="5" ry="6" fill="#333"/>
                            <path d="M80 65 Q88 70, 95 68" stroke="#333" stroke-width="2" fill="none"/>
                            <path d="M105 68 Q112 70, 120 65" stroke="#333" stroke-width="2" fill="none"/>
                            <path d="M85 95 Q100 85, 115 95" stroke="#333" stroke-width="3" fill="none"/>
                            <path d="M70 115 Q100 130, 130 115 L140 180 L60 180 Z" fill="#4A90D9"/>
                            <text x="160" y="50" font-size="40" fill="rgba(255,255,255,0.5)">?</text>
                        </svg>
                    </div>
                    <div class="bandeau-content">
                        <div class="message-principal">${messagePrincipal}</div>
                    </div>
                `;
            }
            
            return banner;
        }
    };
})();

/* ═══════════════════════════════════════════════════════════════════════
   FILIGRANE v1.5 - Gestion du fond fantomatique avec support moteur IA
   ═══════════════════════════════════════════════════════════════════════ */

// Flags pour le filigrane
let _filigraneFirstLoad = true;   // Flag pour le premier chargement
let _forceRandomImage = false;    // Flag pour forcer une image aléatoire (Nouvelle recherche)

/**
 * Définit l'image du filigrane à partir d'une URL spécifique
 * @param {string} imageUrl - URL de l'image à afficher
 */
function setFiligraneImage(imageUrl) {
    const filigraneEl = document.getElementById('filigraneGhost');
    if (!filigraneEl) return;
    
    if (imageUrl) {
        filigraneEl.style.backgroundImage = `url('${imageUrl}')`;
        if (window.DEBUG) {
            const shortName = imageUrl.substring(imageUrl.lastIndexOf('/') + 1);
            console.log('[Filigrane] Image définie:', shortName);
        }
    }
}

/**
 * Met à jour le filigrane selon le moteur IA sélectionné
 * FILIGRANE v1.4 - Logo Kitview au premier chargement, puis image moteur IA ou aléatoire
 * FILIGRANE v1.5 - Support forceRandomImage pour "Nouvelle recherche"
 */
function updateFiligraneGhost() {
    const filigraneEl = document.getElementById('filigraneGhost');
    if (!filigraneEl) return;
    
    let imageUrl = null;
    
    // Priorité 0 (premier chargement uniquement) : Logo Kitview
    if (_filigraneFirstLoad) {
        _filigraneFirstLoad = false;
        imageUrl = illustrationsManager.getLogoImage();
        if (imageUrl) {
            if (window.DEBUG) console.log('[Filigrane] Logo Kitview (premier chargement):', imageUrl.substring(imageUrl.lastIndexOf('/') + 1));
            filigraneEl.style.backgroundImage = `url('${imageUrl}')`;
            return;
        }
    }
    
    // Priorité 0.5 (si forceRandomImage) : Image aléatoire search/medical
    if (_forceRandomImage) {
        _forceRandomImage = false;  // Reset le flag
        imageUrl = illustrationsManager.getNewSearchImage();
        if (imageUrl) {
            if (window.DEBUG) console.log('[Filigrane] Image aléatoire (Nouvelle recherche):', imageUrl.substring(imageUrl.lastIndexOf('/') + 1));
            filigraneEl.style.backgroundImage = `url('${imageUrl}')`;
            return;
        }
    }
    
    // Priorité 1 : Image du moteur IA sélectionné (si définie et non vide)
    // v1.3.2 : Utilise window.IA_MODELS_CACHE pour accès global fiable
    if (typeof window.IA_MODELS_CACHE !== 'undefined' && typeof detectionMode !== 'undefined') {
        const model = window.IA_MODELS_CACHE[detectionMode];
        if (model && model.image && model.image.trim() !== '') {
            imageUrl = model.image.trim();
            if (window.DEBUG) console.log('[Filigrane] Image moteur IA:', detectionMode, '->', imageUrl.substring(imageUrl.lastIndexOf('/') + 1));
        }
    }
    
    // Priorité 2 : Image aléatoire depuis illustrationsManager (fallback)
    if (!imageUrl) {
        imageUrl = illustrationsManager.getFiligraneImage();
        if (imageUrl && window.DEBUG) {
            console.log('[Filigrane] Image illustrations:', imageUrl.substring(imageUrl.lastIndexOf('/') + 1));
        }
    }
    
    // Appliquer l'image
    if (imageUrl) {
        filigraneEl.style.backgroundImage = `url('${imageUrl}')`;
    }
}

/**
 * Applique l'intensité du filigrane (0-100)
 * 0% = fantomatique (opacity très faible)
 * 100% = image grayscale visible
 */
function applyFiligraneIntensity(intensity) {
    const filigraneEl = document.getElementById('filigraneGhost');
    if (!filigraneEl) return;
    
    // Déterminer si on est en mode sombre
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    
    // Calculer les valeurs interpolées
    // Mode clair : opacity de 0.04 (0%) à 0.7 (100%)
    // Mode sombre : opacity de 0.08 (0%) à 0.75 (100%)
    const minOpacity = isDark ? 0.08 : 0.04;
    const maxOpacity = isDark ? 0.75 : 0.7;
    const opacity = minOpacity + (maxOpacity - minOpacity) * (intensity / 100);
    
    // Contrast diminue de 1.2/1.5 vers 1.0 quand intensity augmente
    const minContrast = isDark ? 1.5 : 1.2;
    const contrast = minContrast - (minContrast - 1.0) * (intensity / 100);
    
    // Brightness (sombre uniquement) : de 0.5 vers 1.0
    const brightness = isDark ? (0.5 + 0.5 * (intensity / 100)) : 1.0;
    
    // Appliquer les styles
    filigraneEl.style.opacity = opacity;
    filigraneEl.style.filter = isDark 
        ? `grayscale(100%) brightness(${brightness}) contrast(${contrast})`
        : `grayscale(100%) contrast(${contrast})`;
    
    if (window.DEBUG) console.log(`[Filigrane] Intensité ${intensity}% - opacity: ${opacity.toFixed(2)}, contrast: ${contrast.toFixed(2)}${isDark ? ', brightness: ' + brightness.toFixed(2) : ''}`);
}

/**
 * Met à jour le bandeau loading avec l'image du moteur et les infos de recherche
 * @param {string} query - La requête de recherche en cours
 * @param {string} moteur - Le moteur IA utilisé
 * @param {string} base - La base de données utilisée
 */
function updateLoadingBanner(query, moteur, base) {
    const timestamp = new Date().toISOString().substr(11, 12);
    if (window.DEBUG) {
        console.log(`%c[Loading ${timestamp}] ═══ updateLoadingBanner DEBUT ═══`, 'background: #ff9800; color: white; padding: 2px 5px;');
        console.log(`[Loading ${timestamp}] Paramètres:`, { query, moteur, base });
    }
    
    const loadingIllustration = document.getElementById('loadingIllustration');
    const loadingText = document.getElementById('loadingText');
    const loadingQuery = document.getElementById('loadingQuery');
    const loadingMeta = document.getElementById('loadingMeta');
    
    // 1. Image du moteur IA actuel
    if (loadingIllustration) {
        const imageUrl = illustrationsManager.getMoteurImage(moteur);
        if (window.DEBUG) console.log(`[Loading ${timestamp}] getMoteurImage('${moteur}'):`, imageUrl ? imageUrl.substring(imageUrl.lastIndexOf('/') + 1) : 'NULL');
        if (imageUrl) {
            loadingIllustration.innerHTML = `<img src="${imageUrl}" alt="${moteur}" onerror="this.style.display='none'">`;
        } else {
            // Fallback : spinner SVG animé
            loadingIllustration.innerHTML = `
                <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.3)" stroke-width="8"/>
                    <circle cx="50" cy="50" r="40" fill="none" stroke="white" stroke-width="8" stroke-dasharray="60 190" stroke-linecap="round">
                        <animateTransform attributeName="transform" type="rotate" from="0 50 50" to="360 50 50" dur="1s" repeatCount="indefinite"/>
                    </circle>
                </svg>
            `;
        }
    }
    
    // 2. Texte "Recherche en cours..." avec détection langue côté client
    if (loadingText) {
        const detectedLang = detectLanguageFromText(query);
        const searchingText = getSearchingText(detectedLang);
        loadingText.textContent = searchingText;
        if (window.DEBUG) console.log(`[Loading ${timestamp}] Langue: ${detectedLang} → "${searchingText}"`);
    }
    
    // 3. Question en sous-titre
    if (loadingQuery) {
        loadingQuery.textContent = query || '';
    }
    
    // 4. Base / Moteur en tertiaire
    if (loadingMeta) {
        const baseName = base || 'base';
        const moteurName = moteur || 'standard';
        loadingMeta.textContent = `${baseName} / ${moteurName}`;
    }
    
    if (window.DEBUG) console.log(`%c[Loading ${timestamp}] ═══ updateLoadingBanner FIN ═══`, 'background: #4caf50; color: white; padding: 2px 5px;');
}

/**
 * Détecte la langue d'un texte en se basant sur les caractères Unicode
 * @param {string} text - Le texte à analyser
 * @returns {string} Code langue détecté (fr, ja, zh, ar, th, etc.)
 */
function detectLanguageFromText(text) {
    if (!text) return 'fr';
    
    // Compteur de caractères par script
    let japanese = 0;  // Hiragana, Katakana, Kanji
    let chinese = 0;   // Han uniquement (sans kana)
    let arabic = 0;
    let thai = 0;
    let cyrillic = 0;
    let latin = 0;
    
    for (const char of text) {
        const code = char.charCodeAt(0);
        
        // Hiragana (3040-309F), Katakana (30A0-30FF)
        if ((code >= 0x3040 && code <= 0x309F) || (code >= 0x30A0 && code <= 0x30FF)) {
            japanese++;
        }
        // CJK Unified Ideographs (4E00-9FFF) - Kanji/Hanzi
        else if (code >= 0x4E00 && code <= 0x9FFF) {
            japanese++; // Priorité japonais si mélangé avec kana
            chinese++;
        }
        // Arabic (0600-06FF)
        else if (code >= 0x0600 && code <= 0x06FF) {
            arabic++;
        }
        // Thai (0E00-0E7F)
        else if (code >= 0x0E00 && code <= 0x0E7F) {
            thai++;
        }
        // Cyrillic (0400-04FF)
        else if (code >= 0x0400 && code <= 0x04FF) {
            cyrillic++;
        }
        // Latin de base + étendu
        else if ((code >= 0x0041 && code <= 0x007A) || (code >= 0x00C0 && code <= 0x017F)) {
            latin++;
        }
    }
    
    // Déterminer la langue dominante
    const max = Math.max(japanese, chinese, arabic, thai, cyrillic, latin);
    
    if (max === 0) return 'fr';  // Défaut si aucun caractère reconnu
    
    if (japanese > 0 && japanese >= chinese) return 'ja';  // Japonais si kana présents
    if (chinese > japanese) return 'cn';
    if (arabic === max) return 'ar';
    if (thai === max) return 'th';
    if (cyrillic === max) return 'ru';
    
    return 'fr';  // Défaut pour latin
}

/**
 * Retourne le texte "Recherche en cours..." dans la langue spécifiée
 * @param {string} lang - Code langue
 * @returns {string} Texte traduit
 */
function getSearchingText(lang) {
    const texts = {
        'fr': 'Recherche en cours...',
        'en': 'Searching...',
        'de': 'Suche läuft...',
        'es': 'Buscando...',
        'it': 'Ricerca in corso...',
        'pt': 'Pesquisando...',
        'pl': 'Wyszukiwanie...',
        'ro': 'Se caută...',
        'ja': '検索中...',
        'cn': '搜索中...',
        'ar': '...جاري البحث',
        'th': 'กำลังค้นหา...',
        'ru': 'Поиск...'
    };
    return texts[lang] || texts['fr'];
}

/**
 * Passe le filigrane à l'intensité minimale (0%)
 * Utilisé lors de l'affichage des résultats (bandeau ou liste)
 */
function hideFiligraneForResults() {
    // Arrêter toute animation en cours
    if (window.filigraneAnimationTimer) {
        clearInterval(window.filigraneAnimationTimer);
        window.filigraneAnimationTimer = null;
    }
    applyFiligraneIntensity(0);
    if (window.DEBUG) console.log('[Filigrane] Intensité minimale pour affichage résultats');
}

/**
 * Restaure le filigrane à sa valeur configurée (sans animation)
 */
function restoreFiligraneIntensity() {
    // Arrêter toute animation en cours
    if (window.filigraneAnimationTimer) {
        clearInterval(window.filigraneAnimationTimer);
        window.filigraneAnimationTimer = null;
    }
    if (typeof filigraneIntensity !== 'undefined') {
        applyFiligraneIntensity(filigraneIntensity);
        if (window.DEBUG) console.log('[Filigrane] Restauré à', filigraneIntensity + '%');
    }
}

/**
 * Animation : part de 100% et descend vers la valeur de consigne en 10 secondes
 * Utilisé lors de "Nouvelle recherche"
 */
function animateFiligraneFromMax() {
    // Arrêter toute animation en cours
    if (window.filigraneAnimationTimer) {
        clearInterval(window.filigraneAnimationTimer);
        window.filigraneAnimationTimer = null;
    }
    
    const startIntensity = 100;
    const targetIntensity = typeof filigraneIntensity !== 'undefined' ? filigraneIntensity : 50;
    const duration = 10000; // 10 secondes
    const startTime = Date.now();
    
    // Appliquer immédiatement l'intensité maximale
    applyFiligraneIntensity(startIntensity);
    if (window.DEBUG) console.log('[Filigrane] Animation: 100% →', targetIntensity + '% en 10s');
    
    window.filigraneAnimationTimer = setInterval(() => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Interpolation linéaire de 100% vers la valeur de consigne
        const currentIntensity = startIntensity - (startIntensity - targetIntensity) * progress;
        applyFiligraneIntensity(currentIntensity);
        
        if (progress >= 1) {
            clearInterval(window.filigraneAnimationTimer);
            window.filigraneAnimationTimer = null;
            if (window.DEBUG) console.log('[Filigrane] Animation terminée à', targetIntensity + '%');
        }
    }, 50); // 20 fps
}

/**
 * Force une image aléatoire au prochain appel de updateFiligraneGhost
 */
function setForceRandomImage() {
    _forceRandomImage = true;
}
