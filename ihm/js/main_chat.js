/**
 * main_chat.js V1.0.0 - 30/01/2026
 * Kitview Search - MODE CHAT uniquement
 * Basé sur main.js V2.5.3 avec currentMode='chat' forcé
 */




/* ═══════════════════════════════════════════════════════════════════════
   FIN ILLUSTRATIONS v1.0
   ═══════════════════════════════════════════════════════════════════════ */

/* ═══════════════════════════════════════════════════════════════════════
   FILIGRANE v1.1 - Gestion du fond fantomatique avec support moteur IA
   ═══════════════════════════════════════════════════════════════════════ */

/**
 * Définit l'image du filigrane à partir d'une URL spécifique
 * @param {string} imageUrl - URL de l'image à afficher
 */
function setFiligraneImage(imageUrl) {
    const filigraneEl = document.getElementById('filigraneGhost');
    if (!filigraneEl) return;
    
    if (imageUrl) {
        filigraneEl.style.backgroundImage = `url('${imageUrl}')`;
        const shortName = imageUrl.substring(imageUrl.lastIndexOf('/') + 1);
        console.log('[Filigrane] Image définie:', shortName);
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
            console.log('[Filigrane] Logo Kitview (premier chargement):', imageUrl.substring(imageUrl.lastIndexOf('/') + 1));
            filigraneEl.style.backgroundImage = `url('${imageUrl}')`;
            return;
        }
    }
    
    // Priorité 0.5 (si forceRandomImage) : Image aléatoire search/medical
    if (_forceRandomImage) {
        _forceRandomImage = false;  // Reset le flag
        imageUrl = illustrationsManager.getNewSearchImage();
        if (imageUrl) {
            console.log('[Filigrane] Image aléatoire (Nouvelle recherche):', imageUrl.substring(imageUrl.lastIndexOf('/') + 1));
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
            console.log('[Filigrane] Image moteur IA:', detectionMode, '->', imageUrl.substring(imageUrl.lastIndexOf('/') + 1));
        }
    }
    
    // Priorité 2 : Image aléatoire depuis illustrationsManager (fallback)
    if (!imageUrl) {
        imageUrl = illustrationsManager.getFiligraneImage();
        if (imageUrl) {
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
    
    console.log(`[Filigrane] Intensité ${intensity}% - opacity: ${opacity.toFixed(2)}, contrast: ${contrast.toFixed(2)}${isDark ? ', brightness: ' + brightness.toFixed(2) : ''}`);
}

/**
 * Met à jour le bandeau loading avec l'image du moteur et les infos de recherche
 * v1.3.1 : Paramètres explicites pour éviter problème de portée
 * v1.3.2 : Détection langue côté client pour afficher texte dans la bonne langue
 * v1.1.0 : Debug avancé pour diagnostic
 * @param {string} query - La requête de recherche en cours
 * @param {string} moteur - Le moteur IA utilisé
 * @param {string} base - La base de données utilisée
 */
function updateLoadingBanner(query, moteur, base) {
    const timestamp = new Date().toISOString().substr(11, 12);
    console.log(`%c[Loading ${timestamp}] ═══ updateLoadingBanner DEBUT ═══`, 'background: #ff9800; color: white; padding: 2px 5px;');
    console.log(`[Loading ${timestamp}] Paramètres:`, { query, moteur, base });
    
    // Vérifier que le conteneur loading existe et est visible
    const loadingContainer = document.getElementById('loading');
    const bandeauLoading = document.getElementById('bandeauLoading');
    console.log(`[Loading ${timestamp}] Container loading:`, {
        exists: !!loadingContainer,
        classList: loadingContainer?.classList?.toString(),
        display: loadingContainer?.style?.display,
        computedDisplay: loadingContainer ? getComputedStyle(loadingContainer).display : 'N/A'
    });
    console.log(`[Loading ${timestamp}] Bandeau loading:`, {
        exists: !!bandeauLoading,
        innerHTML_length: bandeauLoading?.innerHTML?.length
    });
    
    const loadingIllustration = document.getElementById('loadingIllustration');
    const loadingText = document.getElementById('loadingText');
    const loadingQuery = document.getElementById('loadingQuery');
    const loadingMeta = document.getElementById('loadingMeta');
    
    console.log(`[Loading ${timestamp}] Éléments DOM:`, {
        loadingIllustration: !!loadingIllustration,
        loadingText: !!loadingText,
        loadingQuery: !!loadingQuery,
        loadingMeta: !!loadingMeta
    });
    
    // Vérifier IA_MODELS_CACHE
    console.log(`[Loading ${timestamp}] window.IA_MODELS_CACHE:`, 
        window.IA_MODELS_CACHE ? Object.keys(window.IA_MODELS_CACHE) : 'UNDEFINED');
    
    // 1. Image du moteur IA actuel
    if (loadingIllustration) {
        const imageUrl = illustrationsManager.getMoteurImage(moteur);
        console.log(`[Loading ${timestamp}] getMoteurImage('${moteur}'):`, imageUrl ? imageUrl.substring(imageUrl.lastIndexOf('/') + 1) : 'NULL');
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
    } else {
        console.error(`[Loading ${timestamp}] ❌ loadingIllustration NON TROUVÉ !`);
    }
    
    // 2. Texte "Recherche en cours..." avec détection langue côté client
    if (loadingText) {
        const detectedLang = detectLanguageFromText(query);
        const searchingText = getSearchingText(detectedLang);
        loadingText.textContent = searchingText;
        console.log(`[Loading ${timestamp}] Langue: ${detectedLang} → "${searchingText}"`);
    } else {
        console.error(`[Loading ${timestamp}] ❌ loadingText NON TROUVÉ !`);
    }
    
    // 3. Question en sous-titre
    if (loadingQuery) {
        loadingQuery.textContent = query || '';
        console.log(`[Loading ${timestamp}] Question: "${query}"`);
    } else {
        console.error(`[Loading ${timestamp}] ❌ loadingQuery NON TROUVÉ !`);
    }
    
    // 4. Base / Moteur en tertiaire
    if (loadingMeta) {
        const baseName = base || 'base';
        const moteurName = moteur || 'standard';
        loadingMeta.textContent = `${baseName} / ${moteurName}`;
        console.log(`[Loading ${timestamp}] Meta: "${baseName} / ${moteurName}"`);
    } else {
        console.error(`[Loading ${timestamp}] ❌ loadingMeta NON TROUVÉ !`);
    }
    
    console.log(`%c[Loading ${timestamp}] ═══ updateLoadingBanner FIN ═══`, 'background: #4caf50; color: white; padding: 2px 5px;');
    
    // v1.1.1 : Bordure rouge pour visualiser le bandeau loading
    if (bandeauLoading) {
        bandeauLoading.style.border = '3px solid red';
        bandeauLoading.style.boxShadow = '0 0 20px red';
    }
}

/**
 * Détecte la langue d'un texte en se basant sur les caractères Unicode
 * v1.3.2 : Détection simple côté client pour le bandeau loading
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

/* ═══════════════════════════════════════════════════════════════════════
   FIN FILIGRANE v1.1
   ═══════════════════════════════════════════════════════════════════════ */

/* ═══════════════════════════════════════════════════════════════════════
   MODE DÉMO v1.0 - Démonstration automatique
   ═══════════════════════════════════════════════════════════════════════ */

/**
 * Passe le filigrane à l'intensité minimale (0%) - filigrane toujours visible mais très atténué
 * Utilisé lors de l'affichage des résultats (bandeau ou liste)
 */
function hideFiligraneForResults() {
    // Arrêter toute animation en cours
    if (window.filigraneAnimationTimer) {
        clearInterval(window.filigraneAnimationTimer);
        window.filigraneAnimationTimer = null;
    }
    applyFiligraneIntensity(0);
    console.log('[Filigrane] Intensité minimale pour affichage résultats');
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
    applyFiligraneIntensity(filigraneIntensity);
    console.log('[Filigrane] Restauré à', filigraneIntensity + '%');
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
    const targetIntensity = filigraneIntensity;
    const duration = 10000; // 10 secondes
    const startTime = Date.now();
    
    // Appliquer immédiatement l'intensité maximale
    applyFiligraneIntensity(startIntensity);
    console.log('[Filigrane] Animation: 100% →', targetIntensity + '% en 10s');
    
    window.filigraneAnimationTimer = setInterval(() => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Interpolation linéaire de 100% vers la valeur de consigne
        const currentIntensity = startIntensity - (startIntensity - targetIntensity) * progress;
        applyFiligraneIntensity(currentIntensity);
        
        if (progress >= 1) {
            clearInterval(window.filigraneAnimationTimer);
            window.filigraneAnimationTimer = null;
            console.log('[Filigrane] Animation terminée à', targetIntensity + '%');
        }
    }, 50); // 20 fps
}

/**
 * Met à jour le disque de progression du mode démo
 * @param {number} percent - Pourcentage de progression (0-100)
 */
function updateDemoProgress(percent) {
    const ring = document.getElementById('demoProgressRing');
    if (ring) {
        ring.style.setProperty('--progress', percent);
    }
    demoProgress = percent;
}

/**
 * Démarre le mode démo
 */
function startDemoMode() {
    if (demoMode) return;
    demoMode = true;
    
    const ring = document.getElementById('demoProgressRing');
    if (ring) ring.classList.add('active');
    
    console.log('[Démo] Démarrage du mode démo');
    addDebugLog('Mode démo activé', 'info');
    
    runDemoCycleA();
}

/**
 * Arrête le mode démo
 */
function stopDemoMode() {
    demoMode = false;
    demoPhase = 'idle';
    
    // Nettoyer les timers
    if (demoTimers.phase) {
        clearTimeout(demoTimers.phase);
        demoTimers.phase = null;
    }
    if (demoTimers.progress) {
        clearInterval(demoTimers.progress);
        demoTimers.progress = null;
    }
    
    const ring = document.getElementById('demoProgressRing');
    if (ring) ring.classList.remove('active');
    
    updateDemoProgress(0);
    
    console.log('[Démo] Mode démo arrêté');
    addDebugLog('Mode démo désactivé', 'info');
}

/**
 * Cycle A: Nouvelle recherche + nouveau filigrane
 */
function runDemoCycleA() {
    if (!demoMode) return;
    
    demoPhase = 'new-search';
    console.log('[Démo] Cycle A: Nouvelle recherche');
    addDebugLog('Démo: Nouvelle recherche', 'info');
    
    // Simuler un clic sur "Nouvelle recherche"
    newSearch();
    
    // Attendre t/10 secondes puis passer à B
    const waitTime = (demoDuration / 10) * 1000;
    startDemoProgressAnimation(0, 10, waitTime);
    
    demoTimers.phase = setTimeout(() => {
        runDemoCycleB();
    }, waitTime);
}

/**
 * Cycle B: Choisir et afficher un exemple
 */
function runDemoCycleB() {
    if (!demoMode) return;
    
    demoPhase = 'typing';
    console.log('[Démo] Cycle B: Affichage exemple');
    
    // Récupérer les exemples
    const examplesText = elements.examplesTextarea ? elements.examplesTextarea.value : '';
    const examples = examplesText.split('\n').map(e => e.trim()).filter(e => e.length > 0);
    
    if (examples.length === 0) {
        console.log('[Démo] Pas d\'exemples, utilisation des exemples par défaut');
        examples.push(...DEFAULT_EXAMPLES);
    }
    
    // Choisir un exemple au hasard
    const randomIndex = Math.floor(Math.random() * examples.length);
    const chosenExample = examples[randomIndex];
    
    addDebugLog(`Démo: Exemple "${chosenExample.substring(0, 30)}..."`, 'info');
    
    // Afficher dans la zone de recherche
    const activeInput = getActiveSearchInput();
    if (activeInput) {
        activeInput.value = chosenExample;
        // Déclencher l'événement input pour activer le bouton
        activeInput.dispatchEvent(new Event('input', { bubbles: true }));
    }
    
    // Attendre 2t/10 secondes puis lancer la recherche
    const waitTime = (2 * demoDuration / 10) * 1000;
    startDemoProgressAnimation(10, 30, waitTime);
    
    demoTimers.phase = setTimeout(() => {
        runDemoSearch();
    }, waitTime);
}

/**
 * Lancer la recherche et attendre les résultats
 */
function runDemoSearch() {
    if (!demoMode) return;
    
    demoPhase = 'searching';
    console.log('[Démo] Lancement recherche');
    
    const activeInput = getActiveSearchInput();
    const query = activeInput ? activeInput.value : '';
    
    if (query) {
        addDebugLog(`Démo: Recherche "${query.substring(0, 30)}..."`, 'info');
        searchPatients(query);
    }
    
    // Attendre 7t/10 secondes puis décider du prochain cycle
    const waitTime = (7 * demoDuration / 10) * 1000;
    startDemoProgressAnimation(30, 100, waitTime);
    
    demoTimers.phase = setTimeout(() => {
        decideNextDemoCycle();
    }, waitTime);
}

/**
 * Décide du prochain cycle: 2/3 → B, 1/3 → A
 */
function decideNextDemoCycle() {
    if (!demoMode) return;
    
    const random = Math.random();
    
    if (random < 0.33) {
        // 1/3: Retour en A (nouvelle recherche complète)
        console.log('[Démo] Décision: Retour en A (nouvelle recherche)');
        addDebugLog('Démo: Nouveau cycle complet', 'info');
        runDemoCycleA();
    } else {
        // 2/3: Retour en B (juste effacer et nouvel exemple)
        console.log('[Démo] Décision: Retour en B (nouvel exemple)');
        addDebugLog('Démo: Nouvel exemple', 'info');
        
        // Effacer la zone de recherche sans faire "nouvelle recherche"
        const activeInput = getActiveSearchInput();
        if (activeInput) {
            activeInput.value = '';
            activeInput.dispatchEvent(new Event('input', { bubbles: true }));
        }
        
        // Restaurer le filigrane car on commence une nouvelle saisie
        restoreFiligraneIntensity();
        
        runDemoCycleB();
    }
}

/**
 * Anime la progression du disque
 */
function startDemoProgressAnimation(startPercent, endPercent, duration) {
    if (demoTimers.progress) {
        clearInterval(demoTimers.progress);
    }
    
    const startTime = Date.now();
    updateDemoProgress(startPercent);
    
    demoTimers.progress = setInterval(() => {
        const elapsed = Date.now() - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const currentPercent = startPercent + (endPercent - startPercent) * progress;
        updateDemoProgress(currentPercent);
        
        if (progress >= 1) {
            clearInterval(demoTimers.progress);
            demoTimers.progress = null;
        }
    }, 50);
}

/**
 * Retourne l'input de recherche actif selon le mode
 */
function getActiveSearchInput() {
    if (elements.welcomeContainer && elements.welcomeContainer.style.display !== 'none') {
        return elements.searchInputCenter;
    } else if (currentMode === 'classique') {
        return elements.searchInputTop;
    } else {
        return elements.searchInputBottom;
    }
}

/* ═══════════════════════════════════════════════════════════════════════
   FIN MODE DÉMO v1.0
   ═══════════════════════════════════════════════════════════════════════ */

/* ═══════════════════════════════════════════════════════════════
           MODULE 1 : CONFIGURATION & VARIABLES (config7.txt)
           v1.0.7 - Ajout gestion multilingue + boutons flèches
           ═══════════════════════════════════════════════════════════════ */
        
        // ╔════════════════════════════════════════════════════════════════
        // ║ Configuration et constantes
        // ╚════════════════════════════════════════════════════════════════
        
        // API_BASE_URL intelligent : détection auto local vs Render
        // [SUPPRIMÉ - voir search.js] Lignes 621-633
        // [SUPPRIMÉ - voir search.js] Lignes 634-634
        const DEFAULT_EXAMPLES = [
            'patients qui grincent des dents',
            '歯ぎしり',
            'Nombre de patients avec linguo-version avec déviation maxillaire ?',
            'Number of patients with linguo-version with maxillary deviation?',
            'Patientes souffrant de béance antérieure et avec classe II',
            'Patientinnen mit Frontzahnlücke und Klasse II',
            'Patientes de moins de 39 ans présentant un encombrement et une rotation dentaire antihoraire',
            'Pazienti di età inferiore ai 39 anni con affollamento e rotazione dei denti in senso antiorario',
            'ado diabétique avec problème de bruxisme',
            'Adolescente diabético com problema de bruxismo',
            'Patientes d\'environ 14 ans avec malocclusion et bruxisme sévère',
            'Pacientes de unos 14 años con maloclusión y bruxismo severo'
        ];

        // ╔════════════════════════════════════════════════════════════════
        // ║ État de l'application
        // ╚════════════════════════════════════════════════════════════════
        
        // [SUPPRIMÉ - voir search.js] Lignes 654-654
        let currentMode = 'chat'; // MODE CHAT FORCÉ - V1.0.0
        
        // ╔═══════════════════════════════════════════════════════════════
        // ║ Mode de recherche backend (legacy - non utilisé avec /search)
        // ╚═══════════════════════════════════════════════════════════════
        let searchMode = 'sc'; // 'sc' (classique), 'sp' (progressive), 'se' (enlever)
        
        // ╔═══════════════════════════════════════════════════════════════
        // ║ Mode de détection (nouveau - /search via trouve.py)
        // ║ - "rapide" : détection regex/synonymes (ex-traditionnel)
        // ║ - "eden/xxx" : IA via Eden AI
        // ║ - "direct/xxx" : IA en direct (futur)
        // ╚═══════════════════════════════════════════════════════════════
        // [SUPPRIMÉ - voir search.js] Lignes 668-668
        // [SUPPRIMÉ - voir search.js] Lignes 669-669
        // [SUPPRIMÉ - voir search.js] Lignes 670-670
        // [SUPPRIMÉ - voir search.js] Lignes 671-671
        
        // Cache des moteurs IA chargé depuis /ia (dynamique)
        // Structure: { moteur: { notes: string, image: string } }
        // v1.3.2 : Accessible globalement via window pour illustrationsManager
        // [SUPPRIMÉ - voir search.js] Lignes 676-676
        // [SUPPRIMÉ - voir search.js] Lignes 677-677
        
        // ╔═══════════════════════════════════════════════════════════════
        // ║ SYSTÈME I18N v1.0.0 - Internationalisation depuis glossaire.csv
        // ║ Chargé depuis /i18n au démarrage, fallback français si erreur
        // ╚═══════════════════════════════════════════════════════════════
        // [SUPPRIMÉ - voir i18n.js] Lignes 683-683
        // [SUPPRIMÉ - voir i18n.js] Lignes 684-684
        // [SUPPRIMÉ - voir i18n.js] Lignes 685-685
        // [SUPPRIMÉ - voir i18n.js] Lignes 686-686
        
        // [SUPPRIMÉ - voir i18n.js] Lignes 688-715
        
        // [SUPPRIMÉ - voir i18n.js] Lignes 717-741
        
        // [SUPPRIMÉ - voir i18n.js] Lignes 743-800
        
        // [SUPPRIMÉ - voir i18n.js] Lignes 802-811
        
        // [SUPPRIMÉ - voir i18n.js] Lignes 813-864
        
        // Variable pour stocker les critères de la dernière recherche (pour mise en gras)
        let lastSearchCriteria = [];
        
        /**
         * Vérifie si un texte correspond à un critère de recherche
         * @param {string} text - Texte à vérifier (pathologie, tag, etc.)
         * @returns {boolean} true si le texte correspond à un critère
         */
        function isMatchingCriteria(text) {
            if (!lastSearchCriteria || lastSearchCriteria.length === 0) {
                return false;
            }
            
            const textLower = text.toLowerCase().trim();
            
            for (const critere of lastSearchCriteria) {
                // Vérifier le canonique (tag)
                if (critere.canonique && textLower.includes(critere.canonique.toLowerCase())) {
                    return true;
                }
                // Vérifier le label
                if (critere.label && textLower.includes(critere.label.toLowerCase())) {
                    return true;
                }
                // Vérifier les adjectifs
                if (critere.adjectifs && Array.isArray(critere.adjectifs)) {
                    for (const adj of critere.adjectifs) {
                        const adjText = (typeof adj === 'object') ? adj.canonique : adj;
                        if (adjText && textLower.includes(adjText.toLowerCase())) {
                            return true;
                        }
                    }
                }
            }
            
            return false;
        }
        
        // ╔═══════════════════════════════════════════════════════════════
        // ║ Gestion multilingue (Renaissance v1.2)
        // ║ Tout passe par /search - utilise trouve.py avec modes IA
        // ╚═══════════════════════════════════════════════════════════════
        // [SUPPRIMÉ - voir i18n.js] Lignes 908-908
        // [SUPPRIMÉ - voir i18n.js] Lignes 909-909
        
        // Codes internationaux pour modes de recherche
        const SEARCH_MODE_CODES = {
            'sc': 'SC', // Search Classic
            'sp': 'SP', // Search Progressive
            'se': 'SE'  // Search Exclude
        };
        
        let conversationHistory = [];
        let currentPage = 1;
        let pageSize = 20;
        let resultsLimit = 100;
        // SUPPRIMÉ v1.0.0 : let debugMode = false;
        let filigraneIntensity = 50;  // 0-100, 0=fantomatique, 100=grayscale visible (défaut: 50%)
        
        // ╔════════════════════════════════════════════════════════════════════════════
        // ║ PAGINATION V2.5.0 : Fonctions de formatage des messages
        // ║ NOUVEAU FORMAT : "Page 3 / 321" (numéro de page / nombre total de pages)
        // ║ Le nombre total de résultats (6407) est affiché en haut dans le message
        // ╚════════════════════════════════════════════════════════════════════════════
        
        /**
         * Formate le message de pagination
         * V2.5.0 : Format "Page 3 / 321" (page courante / total pages)
         * @param {number} displayed - Nombre affiché jusqu'ici
         * @param {number} total - Total de patients
         * @param {string} description - Description des filtres (non utilisé)
         * @param {string} lang - Langue
         * @param {boolean} isComplete - Si tous les patients sont affichés
         */
        function formatPaginationMessage(displayed, total, description, lang, isComplete = false) {
            // Calculer le numéro de page et le nombre total de pages
            const totalPages = Math.ceil(total / pageSize);
            const currentPage = Math.ceil(displayed / pageSize);
            
            if (isComplete || currentPage >= totalPages) {
                // Tous affichés - dernière page
                const pageText = lang === 'fr' ? 'Page' : 'Page';
                return `${pageText} ${totalPages} / ${totalPages}`;
            }
            
            // Format unifié pour les deux modes : "Page X / Y"
            const pageText = lang === 'fr' ? 'Page' : 'Page';
            return `${pageText} ${currentPage} / ${totalPages}`;
        }
        
        /**
         * Retourne le texte du bouton "Page suivante" selon la langue
         */
        function getNextPageText(lang) {
            const texts = {
                'fr': 'Page suivante →',
                'en': 'Next page →',
                'de': 'Nächste Seite →',
                'es': 'Página siguiente →',
                'it': 'Pagina successiva →',
                'pt': 'Próxima página →',
                'pl': 'Następna strona →',
                'ro': 'Pagina următoare →',
                'th': 'หน้าถัดไป →',
                'ar': '← الصفحة التالية',
                'cn': '下一页 →',
                'ja': '次のページ →'
            };
            return texts[lang] || texts['en'];
        }
        
        // ╔════════════════════════════════════════════════════════════════════════════
        // ║ PAGINATION V2.4.0 : Fonction pour charger plus de patients depuis le serveur
        // ║ CORRECTION : Demande pageSize (20) patients, pas resultsLimit (100)
        // ╔════════════════════════════════════════════════════════════════════════════
        // ║ PAGINATION OPTIMISÉE V2.5.1
        // ║ Utilise /search/page qui réutilise les critères en cache (30x plus rapide)
        // ║ Fallback vers /search si la session a expiré (cache TTL 30 min)
        // ╚════════════════════════════════════════════════════════════════════════════
        async function loadMorePatientsFromServer(btn, conversationItem, patientsContainer, countDiv, offset, descFiltres, effLang) {
            btn.disabled = true;
            btn.textContent = '...';
            countDiv.textContent = formatPaginationMessage(offset, conversationItem.response.nb_patients, descFiltres, effLang) + ' (...)';
            
            // V2.5.1 : Chercher session_id dans response OU dans l'item directement
            const sessionId = conversationItem.response?.session_id || conversationItem.session_id;
            
            // Debug : afficher où on a trouvé le session_id
            if (conversationItem.response?.session_id) {
                addDebugLog(`Session ID trouvé dans response: ${sessionId.substring(0,8)}...`, 'info');
            } else if (conversationItem.session_id) {
                addDebugLog(`Session ID trouvé dans item: ${sessionId.substring(0,8)}...`, 'info');
            } else {
                addDebugLog(`Session ID non trouvé, fallback vers /search classique`, 'warning');
            }
            
            // Essayer d'abord /search/page (pagination optimisée)
            let useOptimized = sessionId ? true : false;
            let response = null;
            let data = null;
            
            try {
                if (useOptimized) {
                    addDebugLog(`Pagination optimisée /search/page (offset=${offset}, session=${sessionId.substring(0,8)}...)`, 'info');
                    
                    response = await fetch(`${API_BASE_URL}/search/page`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            session_id: sessionId,
                            offset: offset,
                            limit: pageSize
                        })
                    });
                    
                    // Si session expirée (404), fallback vers /search classique
                    if (response.status === 404) {
                        addDebugLog(`Session expirée, fallback vers /search classique`, 'warning');
                        useOptimized = false;
                    } else if (!response.ok) {
                        throw new Error(`HTTP ${response.status}`);
                    } else {
                        data = await response.json();
                        addDebugLog(`Pagination optimisée: ${data.patients?.length || 0} patients en ${data.temps_ms}ms (cache hit)`, 'success');
                    }
                }
                
                // Fallback vers /search classique
                if (!useOptimized) {
                    addDebugLog(`Chargement classique /search (offset=${offset})`, 'info');
                    
                    response = await fetch(`${API_BASE_URL}/search`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            question: conversationItem.query,
                            base: currentBase,
                            mode: searchMode,
                            limit: pageSize,
                            offset: offset
                        })
                    });
                    
                    if (!response.ok) throw new Error(`HTTP ${response.status}`);
                    data = await response.json();
                    addDebugLog(`Chargement classique: ${data.patients?.length || 0} patients en ${data.temps_ms}ms`, 'success');
                }
                
                const newPatients = data.patients || [];
                
                // Fusionner les nouveaux patients
                conversationItem.response.patients = conversationItem.response.patients.concat(newPatients);
                
                // Mode Classique : remplacer, Mode Chat : ajouter
                if (currentMode === 'classique') {
                    patientsContainer.innerHTML = '';
                }
                
                // Afficher les patients
                const patientsToShow = newPatients.slice(0, pageSize);
                    
                patientsToShow.forEach(patient => {
                    // PHOTOFIT V5.2 : Enrichir avec score similarité
                    const ps = conversationItem.response.portrait_scores;
                    if (ps && patient.idportrait && ps[String(patient.idportrait)] !== undefined) {
                        patient.similarity_score = ps[String(patient.idportrait)];
                    }
                    const element = createPatientElement(patient);
                    patientsContainer.appendChild(element);
                });
                
                if (currentMode === 'classique') {
                    // V2.4.0 : Scroll instantané en mode classique (pas smooth)
                    patientsContainer.scrollIntoView({ behavior: 'instant', block: 'start' });
                }
                
                const finalOffset = offset + patientsToShow.length;
                btn.dataset.currentOffset = finalOffset.toString();
                btn.disabled = false;
                btn.textContent = getNextPageText(effLang);
                
                countDiv.textContent = formatPaginationMessage(finalOffset, conversationItem.response.nb_patients, descFiltres, effLang);
                
                addDebugLog(`${patientsToShow.length} patients supplémentaires affichés`, 'success');
                
                if (finalOffset >= conversationItem.response.nb_patients) {
                    btn.style.display = 'none';
                    countDiv.textContent = formatPaginationMessage(finalOffset, conversationItem.response.nb_patients, descFiltres, effLang, true);
                }
                
            } catch (error) {
                console.error('Erreur chargement pagination:', error);
                addDebugLog(`Erreur pagination: ${error.message}`, 'error');
                btn.disabled = false;
                btn.textContent = '↻';
            }
        }
        
        // ╔═══════════════════════════════════════════════════════════════
        // ║ RATING SYSTEM v1.0.0 - Session ID pour feedback
        // ║ UUID généré pour chaque recherche, utilisé pour le rating
        // ╚═══════════════════════════════════════════════════════════════
        // [SUPPRIMÉ - voir search.js] Lignes 929-929
        
        // Génère un nouveau session_id pour chaque recherche
        // [SUPPRIMÉ - voir search.js] Lignes 932-934
        
        // MODE DÉMO v1.0
        let demoMode = false;
        let demoDuration = 20;  // durée du cycle en secondes
        let demoTimers = { phase: null, progress: null };
        let demoPhase = 'idle';  // 'idle', 'waiting', 'typing', 'searching', 'displaying'
        let demoProgress = 0;  // progression 0-100 du cycle

        // ╔════════════════════════════════════════════════════════════════
        // ║ Éléments DOM
        // ║ IMPORTANT : Initialisé par initElements() après DOMContentLoaded
        // ║ Déclaré ici pour être accessible dans tout le module
        // ╚════════════════════════════════════════════════════════════════
        
        let elements = null;

        // ╔════════════════════════════════════════════════════════════════
        // ║ Gestion du localStorage
        // ╚════════════════════════════════════════════════════════════════
        
        // ╔═══════════════════════════════════════════════════════════════
        // ║ PARSE EXAMPLES v1.0.0 - Parse les exemples depuis localStorage
        // ║ webparams.html sauvegarde en texte brut (1 exemple par ligne)
        // ╚═══════════════════════════════════════════════════════════════
        function parseExamples(rawValue) {
            if (!rawValue) return DEFAULT_EXAMPLES;
            
            // Essayer d'abord JSON (ancien format possible)
            try {
                const parsed = JSON.parse(rawValue);
                if (Array.isArray(parsed) && parsed.length > 0) {
                    return parsed;
                }
            } catch (e) {
                // Ce n'est pas du JSON, c'est du texte brut
            }
            
            // Parser comme texte brut (1 exemple par ligne)
            const lines = rawValue.split('\n')
                .map(line => line.trim())
                .filter(line => line.length > 0);
            
            return lines.length > 0 ? lines : DEFAULT_EXAMPLES;
        }
        
        // ╔═══════════════════════════════════════════════════════════════
        // ║ LOADSETTTINGS v1.0.0 (web8) - Version simplifiée
        // ║ Lit depuis localStorage (écrit par web9params.html)
        // ║ N'essaie plus d'écrire dans les éléments du modal
        // ╚═══════════════════════════════════════════════════════════════
        function loadSettings() {
            const settings = {
                userName: localStorage.getItem('userName') || 'Utilisateur',
                theme: localStorage.getItem('theme') || 'auto',
                uiStyle: localStorage.getItem('uiStyle') || 'classic',
                resultsLimit: parseInt(localStorage.getItem('resultsLimit') || '100'),
                pageSize: parseInt(localStorage.getItem('pageSize') || '20'),
                filigraneIntensity: parseInt(localStorage.getItem('filigraneIntensity') || '50'),
                demoDuration: parseInt(localStorage.getItem('demoDuration') || '20'),
                searchMode: localStorage.getItem('searchMode') || 'sc',
                
                // Mode de détection v5.0 (simplifié)
                detectionMode: localStorage.getItem('detectionMode') || 'standard',
                unionMode: localStorage.getItem('unionMode') === 'true',
                unionIA: localStorage.getItem('unionIA') || 'gpt4o',
                
                // Paramètres Actif/Bandeau (lus depuis localStorage)
                activeTheme: localStorage.getItem('activeTheme') !== 'false',
                bandeauTheme: localStorage.getItem('bandeauTheme') === 'true',
                activeStyle: localStorage.getItem('activeStyle') !== 'false',
                activeUsername: localStorage.getItem('activeUsername') !== 'false',
                bandeauBases: localStorage.getItem('bandeauBases') === 'true',
                activeI18n: localStorage.getItem('activeI18n') !== 'false',
                bandeauI18n: localStorage.getItem('bandeauI18n') !== 'false',
                activePanel: localStorage.getItem('activePanel') === 'true',
                activeHistorique: localStorage.getItem('activeHistorique') !== 'false',
                activeExemples: localStorage.getItem('activeExemples') !== 'false',
                activeDemo: localStorage.getItem('activeDemo') !== 'false',
                activeLimit: localStorage.getItem('activeLimit') !== 'false',
                activePagesize: localStorage.getItem('activePagesize') !== 'false',
                
                // Langue
                selectedLanguage: localStorage.getItem('selectedLanguage') || 'auto',
                responseLanguage: localStorage.getItem('responseLanguage') || 'same',
                
                // Les exemples sont sauvegardés en texte brut par webparams (1 exemple par ligne)
                examples: parseExamples(localStorage.getItem('searchExamples')),
                conversationHistory: JSON.parse(localStorage.getItem('conversationHistory') || '[]')
            };
            
            // Migration anciens paramètres (rapide → standard)
            if (settings.detectionMode === 'traditionnel' || settings.detectionMode === 'rapide') {
                settings.detectionMode = 'standard';
                localStorage.setItem('detectionMode', 'standard');
            }
            
            // Appliquer le nom utilisateur à l'interface
            if (elements.welcomeUserName) {
                elements.welcomeUserName.textContent = settings.userName;
            }
            
            // Appliquer le style visuel
            applyStyle(settings.uiStyle);
            
            // Appliquer l'intensité du filigrane
            filigraneIntensity = settings.filigraneIntensity;
            applyFiligraneIntensity(filigraneIntensity);
            
            // Appliquer la durée de démo
            demoDuration = settings.demoDuration;
            
            // Mode détection
            detectionMode = settings.detectionMode || 'standard';
            unionMode = settings.unionMode || false;
            
            if (elements.detectionModeSelector) {
                elements.detectionModeSelector.value = detectionMode;
            }
            
            // Appliquer les états Bandeau à la toolbar
            applyBandeauStates(settings);
            
            // Langue
            selectedLanguage = settings.selectedLanguage || 'auto';
            responseLanguage = settings.responseLanguage || 'same';
            
            generateLangChips();
            
            // V2.0 : Mise à jour de la checkbox fr externe
            if (typeof updateResponseFrCheckbox === 'function') {
                updateResponseFrCheckbox();
            }
            
            updateLangButton();
            
            resultsLimit = settings.resultsLimit;
            pageSize = settings.pageSize;
            conversationHistory = settings.conversationHistory;
            
            applyTheme(settings.theme);
            renderExamples(settings.examples);
            renderRecentConversations();
            
            // Appliquer visibilité panel gauche
            applyPanelVisibility(settings);
        }
        
        // SUPPRIMÉ v1.0.0 (web8) : applyActiveStates - plus nécessaire sans modal
        
        // Nouvelle fonction v5.0 : Appliquer les états Bandeau (v5.1 : +bandeauTheme, v5.2 : logique corrigée)
        function applyBandeauStates(settings) {
            // Masquer/afficher les éléments de la toolbar selon Bandeau
            // LOGIQUE v5.2 : visible par défaut, masqué seulement si explicitement false
            const baseSelector = document.getElementById('baseSelector');
            const langButton = document.getElementById('langButton');
            const themeToggle = document.getElementById('themeToggle');
            
            // Sélecteur de base dans toolbar - visible sauf si bandeauBases === false
            if (baseSelector) {
                const bandeauBases = localStorage.getItem('bandeauBases');
                baseSelector.style.display = (bandeauBases === 'false') ? 'none' : '';
            }
            
            // Bouton langue - visible sauf si bandeauI18n === false ET activeI18n
            if (langButton) {
                const langContainer = langButton.closest('.lang-button-container');
                const bandeauI18n = localStorage.getItem('bandeauI18n');
                if (langContainer) {
                    langContainer.style.display = (bandeauI18n === 'false' || !settings.activeI18n) ? 'none' : '';
                }
            }
            
            // Bouton thème (jour/nuit) - visible si bandeauTheme === 'true'
            if (themeToggle) {
                themeToggle.style.display = settings.bandeauTheme ? '' : 'none';
            }
        }
        
        // Nouvelle fonction v5.0 : Appliquer visibilité panel gauche
        function applyPanelVisibility(settings) {
            const sidebar = document.querySelector('.sidebar');
            const recentSection = document.getElementById('recentConversations')?.closest('.sidebar-section');
            const examplesSection = document.getElementById('examplesList')?.closest('.sidebar-section');
            
            if (!settings.activePanel && sidebar) {
                // Utiliser collapsed pour que le CSS .sidebar.collapsed ~ .content fonctionne
                sidebar.classList.add('collapsed');
                sidebar.style.display = 'none'; // Masquer complètement
            } else if (sidebar) {
                sidebar.classList.remove('collapsed');
                sidebar.style.display = '';
                if (recentSection) recentSection.style.display = settings.activeHistorique ? '' : 'none';
                if (examplesSection) examplesSection.style.display = settings.activeExemples ? '' : 'none';
            }
        }

        // SUPPRIMÉ v1.0.0 (web8) : saveSettings - déplacé vers web9params.html

        function saveConversationHistory() {
            try {
                // Limiter la taille : ne garder que les 50 dernières conversations
                // et ne pas stocker les patients (trop volumineux)
                const historyToSave = conversationHistory.slice(-50).map(item => ({
                    query: item.query,
                    timestamp: item.timestamp,
                    elapsedTime: item.elapsedTime,
                    endpoint: item.endpoint,
                    lang: item.lang,
                    response: {
                        nb_patients: item.response.nb_patients,
                        nb_patients_retournes: item.response.nb_patients_retournes,
                        description_filtres: item.response.description_filtres,
                        // Ne PAS stocker patients[] pour éviter le quota exceeded
                        patients: [] // Sera rechargé si nécessaire
                    }
                }));
                localStorage.setItem('conversationHistory', JSON.stringify(historyToSave));
            } catch (e) {
                // Si quota exceeded, vider l'historique localStorage et continuer
                console.warn('localStorage quota exceeded, clearing history', e);
                try {
                    localStorage.removeItem('conversationHistory');
                } catch (e2) {
                    console.error('Cannot clear localStorage', e2);
                }
            }
        }

        // ╔════════════════════════════════════════════════════════════════
        // ║ BOUTON LANGUE + POPUP SIMPLIFIÉ (Renaissance v1.1)
        // ║ Tout passe par /suche - si langue=fr, comportement identique à /cherche
        // ╚════════════════════════════════════════════════════════════════
        
        // ╔═══════════════════════════════════════════════════════════════
        // ║ LANGUES avec drapeaux SVG (v1.7.0)
        // ║ Utilise flagcdn.com (gratuit, pas de clé API)
        // ╚═══════════════════════════════════════════════════════════════
        // [SUPPRIMÉ - voir i18n.js] Lignes 1172-1186
        
        // ╔═══════════════════════════════════════════════════════════════
        // ║ TRADUCTIONS MESSAGES RÉSULTATS (v1.2.0)
        // ║ Format complet pour tous les messages UI
        // ╚═══════════════════════════════════════════════════════════════
        // [SUPPRIMÉ - voir i18n.js] Lignes 1192-1265
        
        // Variable globale pour stocker la langue effective de la dernière recherche
        // [SUPPRIMÉ - voir i18n.js] Lignes 1268-1268
        
        // [SUPPRIMÉ - voir i18n.js] Lignes 1270-1292
        // [SUPPRIMÉ - voir i18n.js] Lignes 1273-1273
        
        // [SUPPRIMÉ - voir i18n.js] Lignes 1294-1311
        
        // [SUPPRIMÉ - voir i18n.js] Lignes 1313-1322
        
        // ╔═══════════════════════════════════════════════════════════════
        // ║ MESSAGES D'INFORMATION LANGUE (v1.2.0)
        // ║ Affichés quand la langue détectée diffère de la sélection
        // ╚═══════════════════════════════════════════════════════════════
        // [SUPPRIMÉ - voir i18n.js] Lignes 1328-1341
        
        // [SUPPRIMÉ - voir i18n.js] Lignes 1343-1395
        
        // [SUPPRIMÉ - voir i18n.js] Lignes 1397-1400
        
        // ╔═══════════════════════════════════════════════════════════════
        // ║ Génération des CHIPS de langue v1.1.0
        // ║ Charge les langues actives depuis /params?param=languesactives
        // ║ Auto en premier, rouge et gras, par défaut
        // ║ 3 langues par ligne
        // ╚═══════════════════════════════════════════════════════════════
        
        // [SUPPRIMÉ - voir i18n.js] Lignes 1409-1409
        
        // [SUPPRIMÉ - voir i18n.js] Lignes 1411-1424
        
        // [SUPPRIMÉ - voir i18n.js] Lignes 1426-1474
        
        // [SUPPRIMÉ - voir i18n.js] Lignes 1476-1495
        
        // [SUPPRIMÉ - voir i18n.js] Lignes 1497-1507
        
        // ╔═══════════════════════════════════════════════════════════════
        // ║ AFFICHAGE LANGUE APRÈS RÉPONSE (v1.1.0)
        // ║ Met à jour le bouton langue avec la langue détectée
        // ║ Selon le tableau : combo + drapeau de la langue effective
        // ╚═══════════════════════════════════════════════════════════════
        
        // Mapping code langue → code pays pour drapeaux (langues non supportées incluses)
        // [SUPPRIMÉ - voir i18n.js] Lignes 1516-1526
        
        // [SUPPRIMÉ - voir i18n.js] Lignes 1528-1567
        
        // [SUPPRIMÉ - voir i18n.js] Lignes 1569-1577
        
        // [SUPPRIMÉ - voir i18n.js] Lignes 1579-1584
        
        // [SUPPRIMÉ - voir i18n.js] Lignes 1586-1592

        // ╔════════════════════════════════════════════════════════════════
        // ║ Gestion du thème
        // ╚════════════════════════════════════════════════════════════════
        
        function applyTheme(theme) {
            if (theme === 'auto') {
                const isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
                elements.themeToggle.textContent = isDark ? '☀️' : '🌙';
            } else {
                document.documentElement.setAttribute('data-theme', theme);
                elements.themeToggle.textContent = theme === 'dark' ? '☀️' : '🌙';
            }
            // FILIGRANE v1.1 : Réappliquer l'intensité selon le nouveau thème
            applyFiligraneIntensity(filigraneIntensity);
        }

        function toggleTheme() {
            const currentTheme = elements.themeSelect.value;
            if (currentTheme === 'auto') {
                elements.themeSelect.value = 'light';
                localStorage.setItem('theme', 'light');
                applyTheme('light');
            } else if (currentTheme === 'light') {
                elements.themeSelect.value = 'dark';
                localStorage.setItem('theme', 'dark');
                applyTheme('dark');
            } else {
                elements.themeSelect.value = 'auto';
                localStorage.setItem('theme', 'auto');
                applyTheme('auto');
            }
        }

        // ╔════════════════════════════════════════════════════════════════
        // ║ STYLE v1.0.0 : Gestion du style d'interface
        // ║ "classic" = style sobre page4, "glass" = Liquid Glass iOS 26
        // ╚════════════════════════════════════════════════════════════════
        
        let currentStyle = 'classic';
        
        function applyStyle(style) {
            currentStyle = style;
            
            if (style === 'glass') {
                document.documentElement.setAttribute('data-style', 'glass');
                addDebugLog('Style appliqué: Liquid Glass', 'info');
            } else {
                document.documentElement.removeAttribute('data-style');
                addDebugLog('Style appliqué: Classique', 'info');
            }
        }
        
        function toggleStyle() {
            const newStyle = currentStyle === 'classic' ? 'glass' : 'classic';
            if (elements.styleSelect) {
                elements.styleSelect.value = newStyle;
            }
            localStorage.setItem('uiStyle', newStyle);
            applyStyle(newStyle);
        }

        // ╔════════════════════════════════════════════════════════════════
        // ║ Gestion du mode Chat / Classique
        // ║ V2.4.0 : Support des puces rondes (mode-pill)
        // ╚════════════════════════════════════════════════════════════════
        
        function switchMode(newMode = null) {
            // V2.4.0 : Si newMode est passé, l'utiliser (puces rondes)
            // Sinon, utiliser la checkbox (rétrocompatibilité)
            if (newMode) {
                currentMode = newMode;
                // Synchroniser la checkbox cachée
                if (elements.modeToggle) {
                    elements.modeToggle.checked = (newMode === 'classique');
                }
            } else {
                currentMode = elements.modeToggle.checked ? 'classique' : 'chat';
            }
            
            // V2.4.0 : Mettre à jour les puces rondes si elles existent
            const pillChat = document.getElementById('modePillChat');
            const pillClassique = document.getElementById('modePillClassique');
            if (pillChat && pillClassique) {
                pillChat.classList.toggle('active', currentMode === 'chat');
                pillClassique.classList.toggle('active', currentMode === 'classique');
            }
            
            // Mettre à jour le label si présent (ancien toggle)
            if (elements.modeLabel) {
                elements.modeLabel.textContent = currentMode === 'chat' ? 'Chat' : 'Classique';
            }
            
            // Appliquer les classes de fond
            document.body.classList.remove('mode-chat', 'mode-classique');
            document.body.classList.add(`mode-${currentMode}`);
            
            // Gérer l'affichage des zones de recherche
            if (conversationHistory.length > 0) {
                if (currentMode === 'classique') {
                    elements.searchContainerBottom.classList.remove('active');
                    elements.searchContainerTop.classList.add('active');
                } else {
                    elements.searchContainerTop.classList.remove('active');
                    elements.searchContainerBottom.classList.add('active');
                }
            }
            
            // Réafficher l'historique selon le mode
            renderConversationHistory();
            
            addDebugLog(`Basculé en mode ${currentMode.toUpperCase()}`, 'info');
        }


/* ═══════════════════════════════════════════════════════════════
           MODULE 3 : API & DATA MANAGEMENT (apidata6.txt)
           v1.0.6 - Ajout logique endpoint /cherche vs /suche selon mode langue
           ═══════════════════════════════════════════════════════════════ */
        
        // ╔════════════════════════════════════════════════════════════════
        // ║ Chargement de la version du serveur
        // ╚════════════════════════════════════════════════════════════════
        
        // [SUPPRIMÉ - voir search.js] Lignes 1695-1716
        
        // ╔════════════════════════════════════════════════════════════════
        // ║ Chargement des bases disponibles
        // ╚════════════════════════════════════════════════════════════════
        
        // ═══════════════════════════════════════════════════════════════
        // ANIMATION SEARCH v1.0.0 : Gestion des couleurs du titre
        // ═══════════════════════════════════════════════════════════════
        
        // [SUPPRIMÉ - voir search.js] Lignes 1726-1735
        
        // [SUPPRIMÉ - voir search.js] Lignes 1737-1757
        
        // [SUPPRIMÉ - voir search.js] Lignes 1759-1762
        
        // [SUPPRIMÉ - voir search.js] Lignes 1764-1858
        
        // [SUPPRIMÉ - voir search.js] Lignes 1860-1898
        
        // Fonction pour recharger après changement de base
        // [SUPPRIMÉ - voir search.js] Lignes 1901-1930
        
        // ╔════════════════════════════════════════════════════════════════
        // ║ BASE SUBTITLE v1.0.0 : Affiche la base active sous "Search"
        // ╚════════════════════════════════════════════════════════════════
        
        // [SUPPRIMÉ - voir search.js] Lignes 1936-1940

        // ╔════════════════════════════════════════════════════════════════
        // ║ MOTEURS IA v1.1 : Chargement depuis ia.csv avec filtre actif
        // ╚════════════════════════════════════════════════════════════════
        
        // [SUPPRIMÉ - voir search.js] Lignes 1946-2019
        
        // [SUPPRIMÉ - voir search.js] Lignes 2021-2057
        
        // [SUPPRIMÉ - voir search.js] Lignes 2059-2071

        // ╔════════════════════════════════════════════════════════════════
        // ║ Fonction de normalisation
        // ╚════════════════════════════════════════════════════════════════
        
        // [SUPPRIMÉ - voir search.js] Lignes 2077-2093

        // ╔════════════════════════════════════════════════════════════════
        // ║ Endpoint de recherche (Renaissance v1.2)
        // ║ Tout passe par /search - utilise trouve.py avec modes IA
        // ╚════════════════════════════════════════════════════════════════
        
        // [SUPPRIMÉ - voir search.js] Lignes 2100-2103
        
        // [SUPPRIMÉ - voir search.js] Lignes 2105-2147

        // ╔════════════════════════════════════════════════════════════════
        // ║ Recherche de patients
        // ╚════════════════════════════════════════════════════════════════
        
        // [SUPPRIMÉ - voir search.js] Lignes 2153-2356


        // ╔════════════════════════════════════════════════════════════════
        // ║ Rendu d'un message garde-fou (aucun critère détecté)
        // ╚════════════════════════════════════════════════════════════════
        
        function renderGardefouMessage(item) {
            const responseDiv = document.createElement('div');
            responseDiv.className = 'response-item';
            
            // Question
            const queryDiv = document.createElement('div');
            queryDiv.className = 'query-text';
            queryDiv.textContent = item.query;
            
            // v1.0.2 : Afficher base et moteur sous la question (petits caractères noirs)
            const baseMoteurDiv = document.createElement('div');
            baseMoteurDiv.style.cssText = 'font-size: 11px; color: #333; margin-top: 6px; font-weight: 400;';
            const baseInfo = item.base || currentBase || '';
            const moteurInfo = item.moteur || detectionMode || 'standard';
            baseMoteurDiv.textContent = `${baseInfo} / ${moteurInfo}`;
            queryDiv.appendChild(baseMoteurDiv);
            
            responseDiv.appendChild(queryDiv);
            
            // Message d'avertissement
            const warningDiv = document.createElement('div');
            warningDiv.className = 'response-text';
            warningDiv.style.cssText = `
                background: linear-gradient(135deg, #fff3cd 0%, #ffeeba 100%);
                border: 1px solid #ffc107;
                border-radius: 12px;
                padding: 20px;
                margin-top: 10px;
            `;
            
            // Icône et titre
            const headerDiv = document.createElement('div');
            headerDiv.style.cssText = 'display: flex; align-items: center; gap: 10px; margin-bottom: 15px;';
            headerDiv.innerHTML = `
                <span style="font-size: 24px;">⚠️</span>
                <span style="font-weight: bold; font-size: 16px; color: #856404;">${t('Aucun critère de recherche détecté')}</span>
            `;
            warningDiv.appendChild(headerDiv);
            
            // Message explicatif
            const messageDiv = document.createElement('div');
            messageDiv.style.cssText = 'color: #856404; margin-bottom: 15px; line-height: 1.5;';
            messageDiv.textContent = item.response.gardefou_message || t('Votre recherche ne correspond à aucun terme reconnu.');
            warningDiv.appendChild(messageDiv);
            
            // Suggestions si disponibles
            const suggestions = item.response.gardefou_suggestions || [];
            if (suggestions.length > 0) {
                const suggestDiv = document.createElement('div');
                suggestDiv.style.cssText = 'margin-top: 10px;';
                suggestDiv.innerHTML = `<strong style="color: #856404;">${t('Suggestions')} :</strong>`;
                
                const suggestList = document.createElement('div');
                suggestList.style.cssText = 'display: flex; flex-wrap: wrap; gap: 8px; margin-top: 8px;';
                
                suggestions.forEach(sugg => {
                    const btn = document.createElement('button');
                    btn.textContent = sugg;
                    btn.style.cssText = `
                        padding: 6px 12px;
                        border-radius: 20px;
                        border: 1px solid #ffc107;
                        background: white;
                        color: #856404;
                        cursor: pointer;
                        font-size: 13px;
                        transition: all 0.2s;
                    `;
                    btn.onmouseover = () => btn.style.background = '#ffc107';
                    btn.onmouseout = () => btn.style.background = 'white';
                    btn.onclick = () => {
                        // Lancer une nouvelle recherche avec la suggestion
                        elements.questionInput.value = sugg;
                        submitQuestion();
                    };
                    suggestList.appendChild(btn);
                });
                
                suggestDiv.appendChild(suggestList);
                warningDiv.appendChild(suggestDiv);
            }
            
            responseDiv.appendChild(warningDiv);
            
            // Ajouter au conteneur
            if (currentMode === 'classique') {
                elements.resultsContainer.innerHTML = '';
                elements.resultsContainer.appendChild(responseDiv);
            } else {
                elements.chatContainer.appendChild(responseDiv);
                elements.chatContainer.scrollTop = elements.chatContainer.scrollHeight;
            }
        }


        // ╔════════════════════════════════════════════════════════════════
        // ║ Rendu d'une réponse
        // ╚════════════════════════════════════════════════════════════════
        
        function renderResponse(item) {
            const responseDiv = document.createElement('div');
            responseDiv.className = 'response-item';
            
            // Question
            const queryDiv = document.createElement('div');
            queryDiv.className = 'query-text';
            queryDiv.textContent = item.query;
            
            // v1.0.2 : Afficher base et moteur sous la question (petits caractères noirs)
            const baseMoteurDiv = document.createElement('div');
            baseMoteurDiv.style.cssText = 'font-size: 11px; color: #333; margin-top: 6px; font-weight: 400;';
            const baseInfo = item.base || currentBase || '';
            const moteurInfo = item.moteur || detectionMode || 'standard';
            baseMoteurDiv.textContent = `${baseInfo} / ${moteurInfo}`;
            queryDiv.appendChild(baseMoteurDiv);
            
            responseDiv.appendChild(queryDiv);
            
            // Réponse
            const responseTextDiv = document.createElement('div');
            responseTextDiv.className = 'response-text';
            
            const nbTotal = item.response.nb_patients || 0;
            const patients = item.response.patients || [];
            const nbRetournes = item.response.nb_patients_retournes || patients.length;
            const descFiltres = item.response.description_filtres || t('critères de recherche');
            
            // ╔═══════════════════════════════════════════════════════════════
            // ║ ILLUSTRATIONS v1.1 : Logique améliorée
            // ║ - Bandeau "0 patients" : si nbTotal === 0
            // ║ - Bandeau "X patients" + bouton Voir : si nbTotal > 0 MAIS pas de liste (mode combien)
            // ║ - Pas de bandeau : si nbTotal > 0 ET liste présente (recherche normale)
            // ╚═══════════════════════════════════════════════════════════════
            
            let patientsContainer = null;
            const isCountOnlyMode = nbTotal > 0 && patients.length === 0;
            
            if (nbTotal === 0) {
                // Bandeau "0 patients" v1.3.0 : Affiche la question complète
                const banner = illustrationsManager.createZeroBanner(item.query);
                responseTextDiv.appendChild(banner);
            } else if (isCountOnlyMode) {
                // Bandeau "X patients" UNIQUEMENT pour mode "combien" (pas de liste)
                // Le bouton "Voir" lance une vraie recherche
                // v1.3.0 : Ajout du moteur pour afficher son image
                const banner = illustrationsManager.createResultBanner(
                    nbTotal,
                    descFiltres,
                    `${item.elapsedTime} ms`,
                    () => {
                        // Extraire les critères de la question originale
                        // Enlever tous les mots de la colonne "combien" de commun.csv
                        const countWordsPatterns = [
                            /compte\s+les\s*/gi,
                            /combien\s+de\s*/gi,
                            /nombre\s+de\s*/gi,
                            /l'effectif\s+des\s*/gi,
                            /l'effectif\s+de\s*/gi,
                            /l'effectif\s*/gi,
                            /combien\s*/gi,
                            /denombre\s*/gi,
                            /compte\s*/gi,
                            /total\s*/gi,
                            /nombre\s*/gi
                        ];
                        
                        let newQuery = item.query;
                        countWordsPatterns.forEach(pattern => {
                            newQuery = newQuery.replace(pattern, '');
                        });
                        
                        // Nettoyer aussi les mots liants orphelins
                        newQuery = newQuery.replace(/^\s*(de\s*)?(patients?\s*)?(avec|ont|ayant|présentant)?\s*/gi, '').trim();
                        newQuery = newQuery.replace(/\?\s*$/, '').trim(); // Enlever le ? final
                        
                        if (!newQuery) newQuery = item.query; // Fallback si rien ne reste
                        
                        // Lancer une vraie recherche avec les critères
                        addDebugLog(`Bouton Voir: recherche "${newQuery}"`, 'info');
                        
                        // Mettre la query dans le champ de recherche et lancer
                        if (currentMode === 'chat') {
                            elements.searchInputBottom.value = newQuery;
                        } else {
                            elements.searchInputTop.value = newQuery;
                        }
                        searchPatients(newQuery);
                    },
                    item.moteur  // v1.3.0 : Passer le moteur pour l'image
                );
                responseTextDiv.appendChild(banner);
            }
            // Si nbTotal > 0 ET patients.length > 0 : pas de bandeau, affichage direct de la liste
            
            // ╔═══════════════════════════════════════════════════════════════
            // ║ FIN ILLUSTRATIONS v1.1
            // ╚═══════════════════════════════════════════════════════════════
            
            // ╔═══════════════════════════════════════════════════════════════
            // ║ MESSAGE INFO LANGUE v1.2.0
            // ║ Affiche un message quand la langue détectée diffère de la sélection
            // ╚═══════════════════════════════════════════════════════════════
            const langInfoMsg = createLangInfoMessage(item.lang_detectee, item.lang);
            if (langInfoMsg) {
                responseTextDiv.appendChild(langInfoMsg);
            }
            
            // Header avec meta et actions (bouton Copier)
            const headerDiv = document.createElement('div');
            headerDiv.className = 'response-header';
            
            const metaDiv = document.createElement('div');
            metaDiv.className = 'response-meta';
            
            // v1.1.0 : Langue effective pour le message traduit
            const langEffective = item.lang_detectee || item.lang || 'fr';
            
            // Afficher le texte meta SEULEMENT si pas de bandeau (recherche normale avec liste)
            if (nbTotal > 0 && patients.length > 0) {
                if (nbTotal > nbRetournes) {
                    // Cas avec pagination
                    metaDiv.textContent = `${nbRetournes} / ${formatResultMessage(nbTotal, descFiltres, item.elapsedTime, langEffective)}`;
                } else {
                    metaDiv.textContent = formatResultMessage(nbTotal, descFiltres, item.elapsedTime, langEffective);
                }
            } else {
                metaDiv.style.display = 'none'; // Masqué car bandeau affiché
            }
            
            
            const actionsDiv = document.createElement('div');
            actionsDiv.className = 'response-actions';
            
            // V1.0.6 : Bouton Copier UNIQUEMENT si résultats > 0
            // V1.0.7 : Feedback visuel emoji ✅ après copie
            if (nbTotal > 0) {
                const copyBtn = document.createElement('button');
                copyBtn.className = 'action-btn';
                copyBtn.textContent = `📋 ${t('Copier')}`;
                copyBtn.onclick = () => copyResponse(item, copyBtn);
                actionsDiv.appendChild(copyBtn);
            }
            
            headerDiv.appendChild(metaDiv);
            headerDiv.appendChild(actionsDiv);
            responseTextDiv.appendChild(headerDiv);
            
            // Patients
            if (nbTotal > 0 && patients.length > 0) {
                
                if (currentMode === 'chat') {
                    patientsContainer = document.createElement('div');
                    patientsContainer.className = 'patients-grid-chat';
                } else {
                    patientsContainer = document.createElement('div');
                    patientsContainer.className = 'patients-list-classique';
                }
                
                // Afficher les N premiers patients
                const patientsToShow = patients.slice(0, pageSize);
                
                // ╔═══════════════════════════════════════════════════════════════
                // ║ PHOTOFIT V5.2 : Enrichir patients avec scores de similarité
                // ╚═══════════════════════════════════════════════════════════════
                const portraitScores = item.response.portrait_scores || null;
                
                patientsToShow.forEach(patient => {
                    if (portraitScores && patient.idportrait && portraitScores[String(patient.idportrait)] !== undefined) {
                        patient.similarity_score = portraitScores[String(patient.idportrait)];
                    }
                    const element = createPatientElement(patient);
                    patientsContainer.appendChild(element);
                });
                
                responseTextDiv.appendChild(patientsContainer);
                
                // Si plus de patients disponibles - PAGINATION PROGRESSIVE
                if (patients.length > pageSize || nbTotal > patients.length) {
                    const paginationDiv = document.createElement('div');
                    paginationDiv.style.textAlign = 'center';
                    paginationDiv.style.padding = '20px';
                    paginationDiv.style.display = 'flex';
                    paginationDiv.style.flexDirection = 'column';
                    paginationDiv.style.gap = '10px';
                    paginationDiv.style.alignItems = 'center';
                    
                    // Compteur affiché
                    const countDiv = document.createElement('div');
                    countDiv.style.color = 'var(--text-secondary)';
                    countDiv.style.fontSize = '14px';
                    countDiv.id = `count-${Date.now()}`;
                    
                    const displayed = pageSize;
                    const total = item.response.nb_patients;
                    // ╔═══════════════════════════════════════════════════════════════
                    // ║ MODIFICATION v1.2.0 : Message traduit
                    // ╚═══════════════════════════════════════════════════════════════
                    const descFiltres = item.response.description_filtres || t('critères');
                    const effLang = item.lang_detectee || item.lang || 'fr';
                    countDiv.textContent = formatPaginationMessage(displayed, total, descFiltres, effLang);
                    paginationDiv.appendChild(countDiv);
                    
                    // Bouton "Page suivante"
                    const nextBtn = document.createElement('button');
                    nextBtn.className = 'search-button';
                    nextBtn.style.padding = '10px 24px';
                    nextBtn.style.fontSize = '14px';
                    nextBtn.textContent = getNextPageText(effLang);
                    
                    // Variables de pagination stockées sur le bouton
                    nextBtn.dataset.query = item.query;
                    nextBtn.dataset.currentOffset = pageSize.toString();
                    nextBtn.dataset.allLoaded = 'false'; // Indique si tous les patients ont été chargés depuis SQL
                    
                    nextBtn.onclick = async function() {
                        const offset = parseInt(this.dataset.currentOffset);
                        const query = this.dataset.query;
                        const conversationItem = conversationHistory.find(c => c.query === query);
                        
                        if (!conversationItem) return;
                        
                        const descFiltres = conversationItem.response.description_filtres || t('critères');
                        const effLang = conversationItem.lang_detectee || conversationItem.lang || 'fr';
                        
                        // Phase 1 : Afficher les patients déjà en mémoire
                        if (offset < conversationItem.response.patients.length) {
                            const nextBatch = conversationItem.response.patients.slice(offset, offset + pageSize);
                            
                            // ╔═══════════════════════════════════════════════════════════════
                            // ║ V2.1.0 : Mode Classique = style Google (REMPLACER)
                            // ║ Mode Chat = scroll infini (AJOUTER)
                            // ╚═══════════════════════════════════════════════════════════════
                            if (currentMode === 'classique') {
                                // Style Google : vider et afficher uniquement la page courante
                                patientsContainer.innerHTML = '';
                            }
                            
                            nextBatch.forEach(patient => {
                                // PHOTOFIT V5.2 : Enrichir avec score similarité
                                const ps = conversationItem.response.portrait_scores;
                                if (ps && patient.idportrait && ps[String(patient.idportrait)] !== undefined) {
                                    patient.similarity_score = ps[String(patient.idportrait)];
                                }
                                const element = createPatientElement(patient);
                                patientsContainer.appendChild(element);
                            });
                            
                            // En mode Classique, scroller en haut des résultats (V2.4.0: instant)
                            if (currentMode === 'classique') {
                                patientsContainer.scrollIntoView({ behavior: 'instant', block: 'start' });
                            }
                            
                            const newOffset = offset + nextBatch.length;
                            this.dataset.currentOffset = newOffset.toString();
                            
                            countDiv.textContent = formatPaginationMessage(newOffset, conversationItem.response.nb_patients, descFiltres, effLang);
                            
                            // Si on a affiché tous ceux en mémoire mais il en reste
                            if (newOffset >= conversationItem.response.patients.length && newOffset < conversationItem.response.nb_patients) {
                                // Charger plus depuis le serveur
                                await loadMorePatientsFromServer(this, conversationItem, patientsContainer, countDiv, newOffset, descFiltres, effLang);
                            }
                            
                            // Si on a affiché TOUS les patients
                            if (newOffset >= conversationItem.response.nb_patients) {
                                this.style.display = 'none';
                                countDiv.textContent = formatPaginationMessage(newOffset, newOffset, descFiltres, effLang, true);
                            }
                            
                        } else if (offset < conversationItem.response.nb_patients) {
                            // Phase 2 : Pas de patients en mémoire, charger depuis le serveur
                            await loadMorePatientsFromServer(this, conversationItem, patientsContainer, countDiv, offset, descFiltres, effLang);
                        }
                    };
                    
                    paginationDiv.appendChild(nextBtn);
                    responseTextDiv.appendChild(paginationDiv);
                }
                
            } else {
                // Le bandeau "0 patients" est déjà affiché plus haut via illustrationsManager
                // Pas besoin d'afficher un message supplémentaire
            }
            
            // ╔═══════════════════════════════════════════════════════════════
            // ║ ANALYSE COHORTE v1.0.0 : Bouton pour analyser la cohorte par IA
            // ║ Condition : nb_patients > 0
            // ╚═══════════════════════════════════════════════════════════════
            if (nbTotal > 0) {
                const analyzeBtn = createAnalyzeCohorteButton(item);
                responseTextDiv.appendChild(analyzeBtn);
            }
            
            // ╔═══════════════════════════════════════════════════════════════
            // ║ RATING SYSTEM v1.0.0 : Boutons de feedback
            // ╚═══════════════════════════════════════════════════════════════
            const ratingDiv = createRatingWidget(item.session_id || currentSessionId);
            responseTextDiv.appendChild(ratingDiv);
            
            responseDiv.appendChild(responseTextDiv);
            elements.resultsContainer.appendChild(responseDiv);
            
            // Ajouter la classe de mode au container
            elements.resultsContainer.classList.remove('mode-chat', 'mode-classique');
            elements.resultsContainer.classList.add(`mode-${currentMode}`);
            
            // Scroll pour que la nouvelle question soit en haut de l'affichage
            // Attendre un court délai pour que le DOM soit bien rendu
            setTimeout(() => {
                responseDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 100);
        }
        
        // ╔═══════════════════════════════════════════════════════════════
        // ║ RATING SYSTEM v2.0.0 : Widget de feedback utilisateur avec modales
        // ╚═══════════════════════════════════════════════════════════════
        
        // Variable globale pour stocker la modale active
        let currentRatingModal = null;
        
        function createRatingWidget(sessionId) {
            const container = document.createElement('div');
            container.className = 'rating-container';
            container.dataset.sessionId = sessionId;
            
            // Label
            const label = document.createElement('span');
            label.className = 'rating-label';
            label.textContent = t('Cette recherche vous a-t-elle aidé ?');
            container.appendChild(label);
            
            // Boutons
            const buttonsDiv = document.createElement('div');
            buttonsDiv.className = 'rating-buttons';
            
            const thumbsUp = document.createElement('button');
            thumbsUp.className = 'rating-btn thumbs-up';
            thumbsUp.innerHTML = '👍';
            thumbsUp.title = 'Oui, résultats satisfaisants';
            thumbsUp.onclick = () => showRatingModal(container, sessionId, 'positive');
            
            const thumbsDown = document.createElement('button');
            thumbsDown.className = 'rating-btn thumbs-down';
            thumbsDown.innerHTML = '👎';
            thumbsDown.title = 'Non, résultats insatisfaisants';
            thumbsDown.onclick = () => showRatingModal(container, sessionId, 'negative');
            
            buttonsDiv.appendChild(thumbsUp);
            buttonsDiv.appendChild(thumbsDown);
            container.appendChild(buttonsDiv);
            
            // Message de confirmation (caché initialement)
            const sentDiv = document.createElement('div');
            sentDiv.className = 'rating-sent';
            sentDiv.innerHTML = `✓ ${t('Merci pour votre retour !')}`;
            container.appendChild(sentDiv);
            
            return container;
        }
        
        function showRatingModal(container, sessionId, type) {
            // Fermer la modale existante si présente
            if (currentRatingModal) {
                currentRatingModal.remove();
                currentRatingModal = null;
            }
            
            // Marquer le bon bouton comme sélectionné
            container.querySelectorAll('.rating-btn').forEach(btn => btn.classList.remove('selected'));
            if (type === 'positive') {
                container.querySelector('.thumbs-up').classList.add('selected');
            } else {
                container.querySelector('.thumbs-down').classList.add('selected');
            }
            
            // Créer l'overlay de la modale
            const overlay = document.createElement('div');
            overlay.className = 'rating-modal-overlay';
            
            // Créer la modale
            const modal = document.createElement('div');
            modal.className = 'rating-modal';
            
            // Titre
            const title = document.createElement('h3');
            title.className = 'rating-modal-title';
            title.textContent = t('Commentaire');
            modal.appendChild(title);
            
            // Champ dropdown (seulement pour feedback négatif)
            let selectProblem = null;
            if (type === 'negative') {
                const fieldSelect = document.createElement('div');
                fieldSelect.className = 'rating-modal-field';
                
                const labelSelect = document.createElement('label');
                labelSelect.textContent = t('Quel type de problème souhaitez-vous signaler ?') + ' ' + t('(facultatif)');
                fieldSelect.appendChild(labelSelect);
                
                selectProblem = document.createElement('select');
                selectProblem.innerHTML = `
                    <option value="">Sélectionner...</option>
                    <option value="Bug IHM">Bug de l'interface utilisateur</option>
                    <option value="Pas trouvé tous">N'a pas trouvé tous les patients</option>
                    <option value="Trop trouvé">A trouvé trop de patients</option>
                    <option value="Autre">Autre</option>
                `;
                fieldSelect.appendChild(selectProblem);
                modal.appendChild(fieldSelect);
            }
            
            // Champ textarea
            const fieldTextarea = document.createElement('div');
            fieldTextarea.className = 'rating-modal-field';
            
            const labelTextarea = document.createElement('label');
            labelTextarea.textContent = t('Veuillez fournir des détails :') + ' ' + t('(facultatif)');
            fieldTextarea.appendChild(labelTextarea);
            
            const textarea = document.createElement('textarea');
            textarea.placeholder = type === 'positive' 
                ? 'Dans quelle mesure cette réponse était-elle satisfaisante ?'
                : 'Dans quelle mesure cette réponse était-elle insatisfaisante ?';
            fieldTextarea.appendChild(textarea);
            modal.appendChild(fieldTextarea);
            
            // Boutons
            const buttonsDiv = document.createElement('div');
            buttonsDiv.className = 'rating-modal-buttons';
            
            const cancelBtn = document.createElement('button');
            cancelBtn.className = 'rating-modal-btn cancel';
            cancelBtn.textContent = t('Annuler');
            cancelBtn.onclick = () => closeRatingModal(container);
            
            const submitBtn = document.createElement('button');
            submitBtn.className = 'rating-modal-btn submit';
            submitBtn.textContent = t('Envoyer');
            submitBtn.onclick = () => {
                const rating = type === 'positive' ? '👍' : '👎';
                const typeProbleme = selectProblem ? selectProblem.value : null;
                const commentaire = textarea.value;
                submitRating(container, sessionId, rating, typeProbleme, commentaire);
            };
            
            buttonsDiv.appendChild(cancelBtn);
            buttonsDiv.appendChild(submitBtn);
            modal.appendChild(buttonsDiv);
            
            overlay.appendChild(modal);
            document.body.appendChild(overlay);
            
            // Stocker la référence de la modale
            currentRatingModal = overlay;
            
            // Fermer la modale si clic sur l'overlay (pas sur la modale)
            overlay.onclick = (e) => {
                if (e.target === overlay) {
                    closeRatingModal(container);
                }
            };
            
            // Animation d'ouverture
            requestAnimationFrame(() => {
                overlay.classList.add('active');
            });
            
            // Focus sur le textarea
            setTimeout(() => textarea.focus(), 200);
        }
        
        function closeRatingModal(container) {
            if (currentRatingModal) {
                currentRatingModal.classList.remove('active');
                setTimeout(() => {
                    if (currentRatingModal) {
                        currentRatingModal.remove();
                        currentRatingModal = null;
                    }
                }, 200);
            }
            
            // Désélectionner les boutons
            container.querySelectorAll('.rating-btn').forEach(btn => btn.classList.remove('selected'));
        }
        
        async function submitRating(container, sessionId, rating, typeProbleme = null, commentaire = null) {
            try {
                const response = await fetch(`${API_BASE_URL}/api/rating`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        session_id: sessionId,
                        rating: rating,
                        type_probleme: typeProbleme || null,
                        commentaire: commentaire || null
                    })
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const data = await response.json();
                console.log('[RATING] Feedback envoyé:', data);
                
                // Fermer la modale
                if (currentRatingModal) {
                    currentRatingModal.classList.remove('active');
                    setTimeout(() => {
                        if (currentRatingModal) {
                            currentRatingModal.remove();
                            currentRatingModal = null;
                        }
                    }, 200);
                }
                
                // Marquer le bon bouton comme sélectionné
                container.querySelectorAll('.rating-btn').forEach(btn => btn.classList.remove('selected'));
                if (rating === '👍') {
                    container.querySelector('.thumbs-up').classList.add('selected');
                } else {
                    container.querySelector('.thumbs-down').classList.add('selected');
                }
                
                // Afficher la confirmation
                container.querySelector('.rating-sent').classList.add('active');
                
                addDebugLog(`Rating ${rating} envoyé pour session ${sessionId}`, 'success');
                
            } catch (error) {
                console.error('Erreur envoi rating:', error);
                addDebugLog(`Erreur rating: ${error.message}`, 'error');
                
                // En cas d'erreur, fermer la modale mais ne pas afficher de confirmation
                closeRatingModal(container);
            }
        }

        // ╔═══════════════════════════════════════════════════════════════
        // ║ ANALYSE COHORTE v1.0.0 : Fonctions pour analyser une cohorte par IA
        // ╚═══════════════════════════════════════════════════════════════
        
        /**
         * Crée le bouton "Analyser cette cohorte"
         */
        function createAnalyzeCohorteButton(item) {
            const container = document.createElement('div');
            container.className = 'analyze-cohorte-container';
            container.style.marginTop = '15px';
            container.style.marginBottom = '10px';
            container.style.textAlign = 'center';
            
            const btn = document.createElement('button');
            btn.className = 'analyze-cohorte-btn';
            btn.innerHTML = `📊 ${t('Analyser cette cohorte')}`;
            btn.title = 'Obtenir un résumé analytique de la cohorte par IA';
            
            btn.onclick = async () => {
                btn.disabled = true;
                btn.innerHTML = `⏳ ${t('Analyse en cours...')}`;
                
                try {
                    await analyzeCohorte(item);
                } catch (error) {
                    console.error('Erreur analyse cohorte:', error);
                    alert('Erreur lors de l\'analyse : ' + error.message);
                } finally {
                    btn.disabled = false;
                    btn.innerHTML = `📊 ${t('Analyser cette cohorte')}`;
                }
            };
            
            container.appendChild(btn);
            return container;
        }
        
        /**
         * Lance l'analyse de cohorte via l'API
         */
        async function analyzeCohorte(item) {
            const patients = item.response.patients || [];
            const nbTotal = item.response.nb_patients || patients.length;
            const criteres = item.query || 'recherche';
            
            // Préparer les données patients (max 50 pour le LLM)
            const patientsData = patients.slice(0, 50).map(p => ({
                age: p.age,
                sexe: p.sexe,
                oripathologies: p.oripathologies || p.pathologies || '',
                commentaires: p.commentaires || []
            }));
            
            // Déterminer le moteur IA à utiliser
            const moteur = detectionMode !== 'standard' ? detectionMode : 'gpt4o';
            
            const response = await fetch(`${API_BASE_URL}/ia/cohorte`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    moteur: moteur,
                    patients: patientsData,
                    criteres_recherche: criteres,
                    nb_total: nbTotal,
                    langue: currentUILang || 'fr'  // Passer la langue courante pour l'analyse IA
                })
            });
            
            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || `Erreur HTTP ${response.status}`);
            }
            
            const data = await response.json();
            showCohorteModal(data, criteres, nbTotal);
        }
        
        /**
         * Affiche la modale avec les résultats d'analyse
         */
        function showCohorteModal(data, criteres, nbTotal) {
            // Créer l'overlay
            const overlay = document.createElement('div');
            overlay.className = 'cohorte-modal-overlay';
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.6);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 10000;
                backdrop-filter: blur(4px);
            `;
            
            // Créer la modale
            const modal = document.createElement('div');
            modal.className = 'cohorte-modal';
            modal.style.cssText = `
                background: var(--bg-primary, white);
                border-radius: 16px;
                padding: 24px;
                max-width: 700px;
                width: 90%;
                max-height: 85vh;
                overflow-y: auto;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                position: relative;
            `;
            
            // Header
            const header = document.createElement('div');
            header.style.cssText = `
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 20px;
                padding-bottom: 15px;
                border-bottom: 1px solid var(--border-color, #e0e0e0);
            `;
            
            const title = document.createElement('h3');
            title.style.cssText = 'margin: 0; color: var(--primary-color, #3b82f6);';
            title.innerHTML = `📊 ${t('Analyse de cohorte')}`;
            header.appendChild(title);
            
            const closeBtn = document.createElement('button');
            closeBtn.innerHTML = '✖';
            closeBtn.style.cssText = `
                background: none;
                border: none;
                font-size: 20px;
                cursor: pointer;
                color: var(--text-secondary, #666);
            `;
            closeBtn.onclick = () => overlay.remove();
            header.appendChild(closeBtn);
            
            modal.appendChild(header);
            
            // Info critères
            const criteresDiv = document.createElement('div');
            criteresDiv.style.cssText = `
                background: var(--bg-secondary, #f5f5f5);
                padding: 12px;
                border-radius: 8px;
                margin-bottom: 20px;
                font-size: 14px;
            `;
            criteresDiv.innerHTML = `
                <strong>${t('Critères')} :</strong> ${criteres}<br>
                <strong>${t('Patients')} :</strong> ${nbTotal} | 
                <strong>${t('Modèle')} :</strong> ${data.moteur} | 
                <strong>${t('Temps')} :</strong> ${data.temps_ms}ms
            `;
            modal.appendChild(criteresDiv);
            
            // Statistiques visuelles
            const stats = data.statistiques;
            const statsDiv = document.createElement('div');
            statsDiv.style.cssText = `
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
            `;
            
            // Âge moyen
            if (stats.age_moyen !== null) {
                statsDiv.appendChild(createStatCard('👤', t('Âge moyen'), `${stats.age_moyen} ${t('ans')}`));
            }
            
            // Répartition H/F
            const totalSexe = stats.repartition_sexe.M + stats.repartition_sexe.F;
            if (totalSexe > 0) {
                const pctH = Math.round(stats.repartition_sexe.M * 100 / totalSexe);
                const pctF = 100 - pctH;
                statsDiv.appendChild(createStatCard('⚥', t('Répartition'), `${pctH}% H / ${pctF}% F`));
            }
            
            // Échantillon
            statsDiv.appendChild(createStatCard('📋', t('Échantillon'), `${stats.nb_echantillon} / ${stats.nb_total}`));
            
            modal.appendChild(statsDiv);
            
            // Top pathologies
            if (stats.pathologies_frequentes && stats.pathologies_frequentes.length > 0) {
                const pathoSection = document.createElement('div');
                pathoSection.style.marginBottom = '20px';
                
                const pathoTitle = document.createElement('div');
                pathoTitle.style.cssText = 'font-weight: bold; margin-bottom: 10px; color: var(--text-primary);';
                pathoTitle.textContent = `🏥 ${t('Pathologies les plus fréquentes')}`;
                pathoSection.appendChild(pathoTitle);
                
                const pathoList = document.createElement('div');
                pathoList.style.cssText = 'display: flex; flex-direction: column; gap: 8px;';
                
                stats.pathologies_frequentes.slice(0, 5).forEach((p, i) => {
                    const bar = document.createElement('div');
                    bar.style.cssText = 'display: flex; align-items: center; gap: 10px;';
                    
                    const label = document.createElement('span');
                    label.style.cssText = 'min-width: 180px; font-size: 13px; color: var(--text-primary);';
                    label.textContent = tPatho(p.pathologie);
                    bar.appendChild(label);
                    
                    const barBg = document.createElement('div');
                    barBg.style.cssText = `
                        flex: 1;
                        height: 20px;
                        background: var(--bg-tertiary, #e0e0e0);
                        border-radius: 4px;
                        overflow: hidden;
                    `;
                    
                    const barFill = document.createElement('div');
                    barFill.style.cssText = `
                        height: 100%;
                        width: ${p.pct}%;
                        background: linear-gradient(90deg, var(--primary-color, #3b82f6), #60a5fa);
                        border-radius: 4px;
                        transition: width 0.5s ease;
                    `;
                    barBg.appendChild(barFill);
                    bar.appendChild(barBg);
                    
                    const pct = document.createElement('span');
                    pct.style.cssText = 'min-width: 50px; font-size: 12px; color: var(--text-secondary); text-align: right;';
                    pct.textContent = `${p.pct}%`;
                    bar.appendChild(pct);
                    
                    pathoList.appendChild(bar);
                });
                
                pathoSection.appendChild(pathoList);
                modal.appendChild(pathoSection);
            }
            
            // Résumé IA
            const resumeSection = document.createElement('div');
            resumeSection.style.marginBottom = '20px';
            
            const resumeTitle = document.createElement('div');
            resumeTitle.style.cssText = 'font-weight: bold; margin-bottom: 10px; color: var(--text-primary);';
            resumeTitle.textContent = `🤖 ${t('Analyse IA')}`;
            resumeSection.appendChild(resumeTitle);
            
            const resumeText = document.createElement('div');
            resumeText.style.cssText = `
                background: var(--bg-secondary, #f5f5f5);
                padding: 15px;
                border-radius: 8px;
                line-height: 1.6;
                font-size: 14px;
                color: var(--text-primary);
                white-space: pre-wrap;
            `;
            resumeText.textContent = data.resume;
            resumeSection.appendChild(resumeText);
            
            modal.appendChild(resumeSection);
            
            // Footer avec boutons
            const footer = document.createElement('div');
            footer.style.cssText = `
                display: flex;
                justify-content: flex-end;
                gap: 10px;
                margin-top: 20px;
                padding-top: 15px;
                border-top: 1px solid var(--border-color, #e0e0e0);
            `;
            
            // Bouton Copier
            const copyBtn = document.createElement('button');
            copyBtn.innerHTML = `📋 ${t('Copier')}`;
            copyBtn.style.cssText = `
                padding: 8px 15px;
                border-radius: 8px;
                border: 1px solid var(--border-color, #e0e0e0);
                background: var(--bg-secondary, #f5f5f5);
                cursor: pointer;
                font-size: 14px;
            `;
            copyBtn.onclick = async () => {
                const textToCopy = `${t('Analyse de cohorte')} - ${criteres}\n\n` +
                    `${t('Patients')}: ${nbTotal}\n` +
                    `${t('Âge moyen')}: ${stats.age_moyen || 'N/A'} ${t('ans')}\n` +
                    `${t('Répartition')}: ${stats.repartition_sexe.M}H / ${stats.repartition_sexe.F}F\n\n` +
                    `${t('Pathologies les plus fréquentes')}:\n` +
                    stats.pathologies_frequentes.slice(0, 5).map(p => `- ${tPatho(p.pathologie)}: ${p.pct}%`).join('\n') +
                    `\n\n${t('Analyse IA')}:\n${data.resume}`;
                
                try {
                    await navigator.clipboard.writeText(textToCopy);
                    copyBtn.innerHTML = `✓ ${t('Copié')}`;
                    setTimeout(() => copyBtn.innerHTML = `📋 ${t('Copier')}`, 2000);
                } catch (err) {
                    console.error('Erreur copie:', err);
                }
            };
            footer.appendChild(copyBtn);
            
            // Bouton Fermer
            const closeFooterBtn = document.createElement('button');
            closeFooterBtn.textContent = t('Fermer');
            closeFooterBtn.style.cssText = `
                padding: 8px 20px;
                border-radius: 8px;
                border: none;
                background: var(--primary-color, #3b82f6);
                color: white;
                cursor: pointer;
                font-size: 14px;
            `;
            closeFooterBtn.onclick = () => overlay.remove();
            footer.appendChild(closeFooterBtn);
            
            modal.appendChild(footer);
            overlay.appendChild(modal);
            
            // Fermer si clic sur overlay
            overlay.onclick = (e) => {
                if (e.target === overlay) overlay.remove();
            };
            
            // Fermer avec Escape
            const escHandler = (e) => {
                if (e.key === 'Escape') {
                    overlay.remove();
                    document.removeEventListener('keydown', escHandler);
                }
            };
            document.addEventListener('keydown', escHandler);
            
            document.body.appendChild(overlay);
        }
        
        /**
         * Crée une carte statistique pour la modale
         */
        function createStatCard(emoji, label, value) {
            const card = document.createElement('div');
            card.style.cssText = `
                background: var(--bg-secondary, #f5f5f5);
                padding: 15px;
                border-radius: 10px;
                text-align: center;
            `;
            
            const emojiDiv = document.createElement('div');
            emojiDiv.style.cssText = 'font-size: 24px; margin-bottom: 5px;';
            emojiDiv.textContent = emoji;
            card.appendChild(emojiDiv);
            
            const labelDiv = document.createElement('div');
            labelDiv.style.cssText = 'font-size: 12px; color: var(--text-secondary); margin-bottom: 3px;';
            labelDiv.textContent = label;
            card.appendChild(labelDiv);
            
            const valueDiv = document.createElement('div');
            valueDiv.style.cssText = 'font-size: 16px; font-weight: bold; color: var(--text-primary);';
            valueDiv.textContent = value;
            card.appendChild(valueDiv);
            
            return card;
        }

        /* ═══════════════════════════════════════════════════════════════
           MODULE "MÊME" v2.0.0 - Recherche par similarité (REFONTE)
           
           LOGIQUE :
           - Patient de référence affiché en JAUNE FLUO
           - Critères actifs en ROUGE
           - Question lisible : "Même X et même Y que Nom Prénom"
           - Toggle : re-clic retire le critère
           - Autres patients : seul portrait cliquable (pour changer de référence)
           ═══════════════════════════════════════════════════════════════ */
        
        // Sauvegarde de la dernière recherche (pour retour si plus de critères)
        // [SUPPRIMÉ - voir meme.js] Lignes 3441-3441
        
        // État global des critères "même" en cours
        // [SUPPRIMÉ - voir meme.js] Lignes 3444-3506
        
        // [SUPPRIMÉ - voir meme.js] Lignes 3508-3537
        
        // [SUPPRIMÉ - voir meme.js] Lignes 3539-3544
        
        // [SUPPRIMÉ - voir meme.js] Lignes 3546-3620
        
        // [SUPPRIMÉ - voir meme.js] Lignes 3622-3628
        
        // [SUPPRIMÉ - voir meme.js] Lignes 3630-3645
        
        // [SUPPRIMÉ - voir meme.js] Lignes 3647-3672
        
        // [SUPPRIMÉ - voir meme.js] Lignes 3674-3697
        
        /**
         * Crée l'affichage des pathologies avec la nouvelle logique v2.1
         * GROUPEMENT : Tag + ses pathologies associées ensemble
         * 
         * Affichage souhaité pour patient #9 :
         *   Récession                    (tag sombre)
         *   Récession Gingivale          (pathologie claire)
         *   
         *   Bruxisme                     (tag sombre)
         *   Bruxisme Modéré              (pathologie claire)
         *   
         *   Protrusion Ankylose          (tags sombres sans pathologie)
         * 
         * @param {Array} pathoList - Liste des pathologies
         * @param {number} patientId - ID du patient
         * @param {string} patientName - Nom du patient
         * @returns {HTMLElement} Container avec les pathologies formatées
         */
        function createPathologiesDisplay(pathoList, patientId, patientName) {
            const container = document.createElement('div');
            container.className = 'pathologies-container-v2';
            
            // Regrouper par tag
            const groupes = new Map(); // tag -> {pathosCompletes: [...]}
            const tagsSeuls = new Set(); // Tags sans pathologie associée
            
            pathoList.forEach(patho => {
                const mots = patho.trim().split(/\s+/);
                if (mots.length === 0) return;
                
                const tag = mots[0].toLowerCase();
                
                if (mots.length === 1) {
                    // Tag seul (sera affiché seulement s'il n'a pas de pathologie)
                    if (!groupes.has(tag)) {
                        tagsSeuls.add(tag);
                    }
                } else {
                    // Pathologie complète
                    tagsSeuls.delete(tag); // Ce tag a une pathologie
                    
                    if (!groupes.has(tag)) {
                        groupes.set(tag, []);
                    }
                    groupes.get(tag).push({
                        full: patho,
                        length: patho.length
                    });
                }
            });
            
            // Trier les pathologies dans chaque groupe par longueur décroissante
            groupes.forEach((pathos, tag) => {
                pathos.sort((a, b) => b.length - a.length);
            });
            
            // Trier les groupes par longueur de la plus longue pathologie
            const groupesTries = [...groupes.entries()].sort((a, b) => {
                const maxA = a[1].length > 0 ? a[1][0].length : 0;
                const maxB = b[1].length > 0 ? b[1][0].length : 0;
                return maxB - maxA;
            });
            
            // Créer l'affichage groupé
            groupesTries.forEach(([tag, pathos], index) => {
                const groupe = document.createElement('div');
                groupe.className = 'patho-groupe';
                
                // Tag (BLANC sur SOMBRE)
                const tagEl = document.createElement('span');
                tagEl.className = 'patho-tag-dark';
                tagEl.textContent = tPatho(tag);
                
                const tagClickable = isMemeClickable(patientId, 'tag');
                const tagActive = isMemeActive(patientId, 'tag', tag);
                
                if (tagActive) {
                    tagEl.classList.add('meme-active');
                }
                
                if (tagClickable) {
                    tagEl.classList.add('patho-clickable');
                    tagEl.title = tagActive ? 'Retirer ce critère' : `Même ${tag}`;
                    tagEl.onclick = (e) => {
                        e.stopPropagation();
                        handleMemeClick(patientId, patientName, 'tag', tag);
                    };
                }
                
                groupe.appendChild(tagEl);
                
                // Pathologies associées (NOIR sur CLAIR)
                pathos.forEach(pathoObj => {
                    const pathoEl = document.createElement('div');
                    pathoEl.className = 'patho-full-light';
                    pathoEl.textContent = tPatho(pathoObj.full);
                    
                    const pathoClickable = isMemeClickable(patientId, 'pathologie');
                    const pathoActive = isMemeActive(patientId, 'pathologie', pathoObj.full.toLowerCase());
                    
                    if (pathoActive) {
                        pathoEl.classList.add('meme-active');
                    }
                    
                    if (pathoClickable) {
                        pathoEl.classList.add('patho-clickable');
                        pathoEl.title = pathoActive ? 'Retirer ce critère' : `Même ${pathoObj.full}`;
                        pathoEl.onclick = (e) => {
                            e.stopPropagation();
                            handleMemeClick(patientId, patientName, 'pathologie', pathoObj.full.toLowerCase());
                        };
                    }
                    
                    groupe.appendChild(pathoEl);
                });
                
                container.appendChild(groupe);
            });
            
            // Tags seuls (sans pathologie associée) - sur une ligne
            if (tagsSeuls.size > 0) {
                const tagsSeulsRow = document.createElement('div');
                tagsSeulsRow.className = 'patho-tags-row';
                
                // Trier les tags seuls par longueur décroissante
                const tagsSeulsTries = [...tagsSeuls].sort((a, b) => b.length - a.length);
                
                tagsSeulsTries.forEach(tag => {
                    const tagEl = document.createElement('span');
                    tagEl.className = 'patho-tag-dark';
                    tagEl.textContent = tPatho(tag);
                    
                    const tagClickable = isMemeClickable(patientId, 'tag');
                    const tagActive = isMemeActive(patientId, 'tag', tag);
                    
                    if (tagActive) {
                        tagEl.classList.add('meme-active');
                    }
                    
                    if (tagClickable) {
                        tagEl.classList.add('patho-clickable');
                        tagEl.title = tagActive ? 'Retirer ce critère' : `Même ${tag}`;
                        tagEl.onclick = (e) => {
                            e.stopPropagation();
                            handleMemeClick(patientId, patientName, 'tag', tag);
                        };
                    }
                    
                    tagsSeulsRow.appendChild(tagEl);
                });
                
                container.appendChild(tagsSeulsRow);
            }
            
            return container;
        }

        /* ═══════════════════════════════════════════════════════════════
           FIN MODULE "MÊME" v2.0.0
           ═══════════════════════════════════════════════════════════════ */

        function createPatientElement(patient) {
            if (currentMode === 'chat') {
                return createPatientCardChat(patient);
            } else {
                return createPatientItemClassique(patient);
            }
        }

        function createPatientCardChat(patient) {
            const card = document.createElement('div');
            card.className = 'patient-card-chat';
            
            // Récupérer l'ID et le nom du patient
            const patientId = patient.id;
            const patientFullName = (patient.oriprenom && patient.orinom) 
                ? `${patient.oriprenom} ${patient.orinom}`.trim()
                : `${capitalize(patient.prenom || '')} ${capitalize(patient.nom || '')}`.trim() || 'Patient';
            
            // ╔═══════════════════════════════════════════════════════════════
            // ║ v2.1.1 : Patient référence en JAUNE FLUO
            // ║ FIX 25/01/2026 : Classe CSS corrigée (meme-reference-card → reference-patient)
            // ╚═══════════════════════════════════════════════════════════════
            const isReference = memeState.isReference(patientId);
            if (isReference) {
                card.classList.add('reference-patient');
            }
            
            // ╔═══════════════════════════════════════════════════════════════
            // ║ v2.1 : ID patient en haut à GAUCHE (sans #)
            // ╚═══════════════════════════════════════════════════════════════
            const idBadge = document.createElement('div');
            idBadge.className = 'patient-id-badge';
            idBadge.textContent = patientId;
            card.appendChild(idBadge);
            
            // ╔═══════════════════════════════════════════════════════════════
            // ║ PHOTOFIT V5.2 : Badge score de similarité (haut droite)
            // ║ 100 = jaune (référence), ≥80 = vert, ≥60 = bleu, ≥40 = orange
            // ╚═══════════════════════════════════════════════════════════════
            if (patient.similarity_score !== undefined && patient.similarity_score !== null) {
                const score = patient.similarity_score;
                const scoreBadge = document.createElement('div');
                scoreBadge.className = 'similarity-score-badge';
                
                // Couleur selon le score
                let badgeColor, badgeEmoji;
                if (score === 100) {
                    badgeColor = '#ffc107'; badgeEmoji = '🎯';  // Référence
                } else if (score >= 80) {
                    badgeColor = '#28a745'; badgeEmoji = '🟢';  // Excellent
                } else if (score >= 60) {
                    badgeColor = '#17a2b8'; badgeEmoji = '🔵';  // Bon
                } else {
                    badgeColor = '#fd7e14'; badgeEmoji = '🟠';  // Moyen
                }
                
                scoreBadge.style.cssText = `
                    position: absolute; top: 6px; right: 8px;
                    background: ${badgeColor}; color: #fff;
                    padding: 2px 8px; border-radius: 12px;
                    font-size: 11px; font-weight: 700;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.3);
                    z-index: 2; cursor: default;
                `;
                scoreBadge.textContent = `${badgeEmoji} ${score}%`;
                scoreBadge.title = score === 100 
                    ? 'Portrait de référence' 
                    : `Similarité : ${score}%`;
                card.appendChild(scoreBadge);
                
                // S'assurer que la carte est en position relative
                card.style.position = 'relative';
            }
            
            // v2.1 : Bouton X supprimé (réservé pour favori futur)
            
            // Header avec photo et infos principales
            const header = document.createElement('div');
            header.className = 'patient-card-header';
            
            // Photo container - CLIQUABLE pour "même portrait"
            const photoContainer = document.createElement('div');
            photoContainer.className = 'patient-photo-container';
            
            // Configurer le portrait comme cliquable pour "même portrait"
            makePortraitMemeClickable(photoContainer, patientId, patientFullName);
            
            if (patient.portrait) {
                const photo = document.createElement('img');
                photo.className = 'patient-photo';
                photo.style.width = '60px';
                photo.style.height = '60px';
                photo.src = patient.portrait;
                const altName = (patient.oriprenom && patient.orinom) 
                    ? `${patient.oriprenom} ${patient.orinom}`
                    : `${patient.prenom} ${patient.nom}`;
                photo.alt = altName;
                photo.onerror = () => {
                    const placeholder = document.createElement('div');
                    placeholder.className = 'patient-photo-placeholder';
                    placeholder.style.width = '60px';
                    placeholder.style.height = '60px';
                    placeholder.style.fontSize = '22px';
                    const initPrenom = patient.oriprenom?.[0] || patient.prenom?.[0] || '';
                    const initNom = patient.orinom?.[0] || patient.nom?.[0] || '';
                    placeholder.textContent = initPrenom.toUpperCase() + initNom.toUpperCase();
                    photo.parentNode.replaceChild(placeholder, photo);
                };
                photoContainer.appendChild(photo);
            } else {
                const placeholder = document.createElement('div');
                placeholder.className = 'patient-photo-placeholder';
                placeholder.style.width = '60px';
                placeholder.style.height = '60px';
                placeholder.style.fontSize = '22px';
                const initPrenom = patient.oriprenom?.[0] || patient.prenom?.[0] || '';
                const initNom = patient.orinom?.[0] || patient.nom?.[0] || '';
                placeholder.textContent = initPrenom.toUpperCase() + initNom.toUpperCase();
                photoContainer.appendChild(placeholder);
            }
            
            header.appendChild(photoContainer);
            
            // ╔═══════════════════════════════════════════════════════════════
            // ║ v2.1.1 : Tous les badges en style CLAIR (lisibles)
            // ╚═══════════════════════════════════════════════════════════════
            const mainInfo = document.createElement('div');
            mainInfo.className = 'patient-card-main-info';
            
            // Prénom - cliquable, fond CLAIR
            const prenomSpan = document.createElement('span');
            prenomSpan.className = 'info-badge-light';
            const prenomText = patient.oriprenom || capitalize(patient.prenom || '');
            prenomSpan.textContent = prenomText;
            if (prenomText) {
                makeMemeClickable(prenomSpan, patientId, patientFullName, 'prenom', null, 'Même prénom');
            }
            mainInfo.appendChild(prenomSpan);
            
            // Nom - cliquable, fond CLAIR
            const nomSpan = document.createElement('span');
            nomSpan.className = 'info-badge-light';
            const nomText = patient.orinom || capitalize(patient.nom || '');
            nomSpan.textContent = nomText;
            if (nomText) {
                makeMemeClickable(nomSpan, patientId, patientFullName, 'nom', null, 'Même nom');
            }
            mainInfo.appendChild(nomSpan);
            
            // Ligne sexe + âge
            const genderAgeLine = document.createElement('div');
            genderAgeLine.className = 'gender-age-line';
            
            // Sexe - cliquable, fond CLAIR
            if (patient.sexe) {
                const sexeSpan = document.createElement('span');
                sexeSpan.className = 'info-badge-light info-badge-small';
                const sexeSymbol = patient.sexe === 'F' ? '♀' : patient.sexe === 'M' ? '♂' : '';
                sexeSpan.textContent = sexeSymbol;
                makeMemeClickable(sexeSpan, patientId, patientFullName, 'sexe', null, 'Même sexe');
                genderAgeLine.appendChild(sexeSpan);
            }
            
            // Âge - cliquable, fond CLAIR
            if (patient.age) {
                const ageSpan = document.createElement('span');
                ageSpan.className = 'info-badge-light';
                ageSpan.textContent = `${Math.floor(patient.age)} ${t('ans')}`;
                makeMemeClickable(ageSpan, patientId, patientFullName, 'age', null, 'Même âge (±3 ans)');
                genderAgeLine.appendChild(ageSpan);
            }
            
            mainInfo.appendChild(genderAgeLine);
            
            header.appendChild(mainInfo);
            card.appendChild(header);
            
            // ╔═══════════════════════════════════════════════════════════════
            // ║ v2.1 : Section Pathologies - GROUPÉ par tag
            // ║ - Tags : BLANC sur SOMBRE
            // ║ - Pathologies complètes : NOIR sur CLAIR  
            // ║ - Groupement : tag + ses pathologies ensemble
            // ╚═══════════════════════════════════════════════════════════════
            const pathoSource = patient.oripathologies || patient.pathologies;
            if (pathoSource) {
                const pathoSection = document.createElement('div');
                pathoSection.className = 'patient-card-section';
                
                const pathoTitle = document.createElement('div');
                pathoTitle.className = 'patient-card-section-title';
                pathoTitle.textContent = t('PATHOLOGIES');
                pathoSection.appendChild(pathoTitle);
                
                // Parser les pathologies
                let pathoList = [];
                if (typeof pathoSource === 'string') {
                    pathoList = pathoSource.split(',').map(p => p.trim()).filter(p => p.length > 0);
                } else if (Array.isArray(pathoSource)) {
                    pathoList = pathoSource;
                }
                
                // Utiliser la nouvelle fonction d'affichage v2.1
                const pathosDisplay = createPathologiesDisplay(pathoList, patientId, patientFullName);
                pathoSection.appendChild(pathosDisplay);
                
                card.appendChild(pathoSection);
            }
            
            // Section Tags (toujours visible) - CLIQUABLES
            if (patient.tags) {
                const tagsSection = document.createElement('div');
                tagsSection.className = 'patient-card-section';
                
                const tagsTitle = document.createElement('div');
                tagsTitle.className = 'patient-card-section-title';
                tagsTitle.textContent = t('Tags');
                tagsSection.appendChild(tagsTitle);
                
                const tagsDiv = document.createElement('div');
                tagsDiv.className = 'patient-tags';
                tagsDiv.style.justifyContent = 'flex-start';
                
                // Gérer le cas où tags est une chaîne ou un array
                let tagsList = [];
                if (typeof patient.tags === 'string') {
                    tagsList = patient.tags.split(',').map(t => t.trim()).filter(t => t.length > 0);
                } else if (Array.isArray(patient.tags)) {
                    tagsList = patient.tags;
                }
                
                tagsList.forEach(tag => {
                    const tagSpan = document.createElement('span');
                    tagSpan.className = 'tag-badge';
                    tagSpan.textContent = capitalize(tag);
                    
                    // Rendre le tag cliquable pour "même tag"
                    makeMemeClickable(tagSpan, patientId, patientFullName, 'tag', tag, `Rechercher même ${tag}`);
                    
                    tagsDiv.appendChild(tagSpan);
                });
                
                tagsSection.appendChild(tagsDiv);
                card.appendChild(tagsSection);
            }
            
            // ═══════════════════════════════════════════════════════════════
            // Section Commentaires v6.0 (visible uniquement quand agrandi)
            // Remplace l'ancienne section Détails (Localisation/Praticien/Traitement)
            // ═══════════════════════════════════════════════════════════════
            const detailsDiv = document.createElement('div');
            detailsDiv.className = 'patient-card-details';
            
            // Afficher les commentaires des pathologies
            if (patient.commentaires && patient.commentaires.length > 0) {
                const commSection = document.createElement('div');
                commSection.style.marginTop = '15px';
                commSection.style.paddingTop = '15px';
                commSection.style.borderTop = '1px solid var(--border-color)';
                
                const commTitle = document.createElement('div');
                commTitle.className = 'patient-card-section-title';
                commTitle.textContent = t('COMMENTAIRES CLINIQUES');
                commSection.appendChild(commTitle);
                
                // Parcourir les commentaires de chaque pathologie
                patient.commentaires.forEach((item, index) => {
                    const commItem = document.createElement('div');
                    commItem.style.marginTop = index === 0 ? '10px' : '15px';
                    commItem.style.paddingLeft = '10px';
                    commItem.style.borderLeft = '3px solid var(--primary-color)';
                    
                    // Titre = nom de la pathologie en gras (traduit via glossaire)
                    const pathoTitle = document.createElement('div');
                    pathoTitle.style.fontWeight = 'bold';
                    pathoTitle.style.fontSize = '13px';
                    pathoTitle.style.color = 'var(--text-primary)';
                    pathoTitle.style.marginBottom = '5px';
                    pathoTitle.textContent = capitalize(tPatho(item.pathologie));
                    commItem.appendChild(pathoTitle);
                    
                    // Commentaire en dessous (s'il existe)
                    if (item.commentaire) {
                        const commText = document.createElement('div');
                        commText.style.fontSize = '12px';
                        commText.style.color = 'var(--text-secondary)';
                        commText.style.lineHeight = '1.5';
                        commText.style.fontStyle = 'italic';
                        commText.textContent = item.commentaire;
                        commItem.appendChild(commText);
                    } else {
                        const noComm = document.createElement('div');
                        noComm.style.fontSize = '12px';
                        noComm.style.color = 'var(--text-secondary)';
                        noComm.style.opacity = '0.6';
                        noComm.textContent = t('(pas de commentaire)');
                        commItem.appendChild(noComm);
                    }
                    
                    commSection.appendChild(commItem);
                });
                
                detailsDiv.appendChild(commSection);
            } else {
                // Pas de commentaires disponibles
                const noCommSection = document.createElement('div');
                noCommSection.style.marginTop = '15px';
                noCommSection.style.paddingTop = '15px';
                noCommSection.style.borderTop = '1px solid var(--border-color)';
                noCommSection.style.fontSize = '13px';
                noCommSection.style.color = 'var(--text-secondary)';
                noCommSection.style.fontStyle = 'italic';
                noCommSection.textContent = t('Aucun commentaire clinique disponible');
                detailsDiv.appendChild(noCommSection);
            }
            
            // ╔═══════════════════════════════════════════════════════════════
            // ║ ZONE IA v1.0 - Chat avec l'IA sur ce patient
            // ╚═══════════════════════════════════════════════════════════════
            const iaSection = document.createElement('div');
            iaSection.style.marginTop = '20px';
            iaSection.style.paddingTop = '15px';
            iaSection.style.borderTop = '2px solid var(--primary-color)';
            
            const iaTitle = document.createElement('div');
            iaTitle.className = 'patient-card-section-title';
            iaTitle.style.color = 'var(--primary-color)';
            iaTitle.innerHTML = '🤖 ' + t('Demander à l\'IA');
            iaSection.appendChild(iaTitle);
            
            // Container pour input + bouton
            const iaInputContainer = document.createElement('div');
            iaInputContainer.style.display = 'flex';
            iaInputContainer.style.gap = '10px';
            iaInputContainer.style.marginTop = '10px';
            
            const iaInput = document.createElement('textarea');
            iaInput.placeholder = t('Votre question pour l\'IA...');
            iaInput.style.flex = '1';
            iaInput.style.padding = '10px';
            iaInput.style.borderRadius = '8px';
            iaInput.style.border = '1px solid var(--border-color)';
            iaInput.style.backgroundColor = 'var(--bg-secondary)';
            iaInput.style.color = 'var(--text-primary)';
            iaInput.style.fontSize = '13px';
            iaInput.style.resize = 'vertical';
            iaInput.style.minHeight = '60px';
            iaInput.style.maxHeight = '150px';
            iaInputContainer.appendChild(iaInput);
            
            const iaButton = document.createElement('button');
            iaButton.innerHTML = '🤖';
            iaButton.title = t('Demander à l\'IA');
            iaButton.style.padding = '10px 15px';
            iaButton.style.borderRadius = '8px';
            iaButton.style.border = 'none';
            iaButton.style.backgroundColor = 'var(--primary-color)';
            iaButton.style.color = 'white';
            iaButton.style.fontSize = '18px';
            iaButton.style.cursor = 'pointer';
            iaButton.style.transition = 'background-color 0.2s';
            iaButton.onmouseover = () => iaButton.style.backgroundColor = 'var(--button-hover)';
            iaButton.onmouseout = () => iaButton.style.backgroundColor = 'var(--primary-color)';
            
            // Handler du clic sur le bouton IA
            iaButton.onclick = async (e) => {
                e.stopPropagation();
                const question = iaInput.value.trim();
                if (!question) {
                    alert('Veuillez saisir une question');
                    return;
                }
                
                // Désactiver le bouton pendant le chargement
                iaButton.disabled = true;
                iaButton.innerHTML = '⏳';
                
                try {
                    const response = await askIA(patient, question);
                    showIAModal(response, patient, question);
                } catch (error) {
                    console.error('Erreur IA:', error);
                    alert('Erreur lors de la requête IA: ' + error.message);
                } finally {
                    iaButton.disabled = false;
                    iaButton.innerHTML = '🤖';
                }
            };
            
            iaInputContainer.appendChild(iaButton);
            iaSection.appendChild(iaInputContainer);
            detailsDiv.appendChild(iaSection);
            
            card.appendChild(detailsDiv);
            
            // ╔═══════════════════════════════════════════════════════════════
            // ║ v2.0 : BOUTON EXPAND - Chevron en bas de carte
            // ╚═══════════════════════════════════════════════════════════════
            const expandBtn = document.createElement('button');
            expandBtn.className = 'expand-card-btn';
            expandBtn.title = 'Voir plus de détails';
            expandBtn.onclick = (e) => {
                e.stopPropagation();
                card.classList.toggle('expanded');
                expandBtn.title = card.classList.contains('expanded') 
                    ? 'Réduire' 
                    : 'Voir plus de détails';
            };
            card.appendChild(expandBtn);
            
            return card;
        }

        function createDetailSectionCard(title, items) {
            const section = document.createElement('div');
            section.style.marginTop = '15px';
            section.style.paddingTop = '15px';
            section.style.borderTop = '1px solid var(--border-color)';
            
            const sectionTitle = document.createElement('div');
            sectionTitle.className = 'patient-card-section-title';
            sectionTitle.textContent = title;
            section.appendChild(sectionTitle);
            
            const grid = document.createElement('div');
            grid.style.display = 'grid';
            grid.style.gridTemplateColumns = 'repeat(auto-fit, minmax(150px, 1fr))';
            grid.style.gap = '12px';
            grid.style.marginTop = '8px';
            
            items.forEach(item => {
                const itemDiv = document.createElement('div');
                
                const label = document.createElement('div');
                label.style.fontSize = '11px';
                label.style.color = 'var(--text-secondary)';
                label.style.fontWeight = '500';
                label.style.marginBottom = '2px';
                label.textContent = item.label;
                itemDiv.appendChild(label);
                
                const value = document.createElement('div');
                value.style.fontSize = '13px';
                value.style.color = 'var(--text-primary)';
                value.textContent = item.value;
                itemDiv.appendChild(value);
                
                grid.appendChild(itemDiv);
            });
            
            section.appendChild(grid);
            return section;
        }

        function capitalize(str) {
            if (!str) return '';
            return str.split(' ')
                .map(word => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
                .join(' ');
        }

        /**
         * createPatientItemClassique - V3.0.0 COMPACT HORIZONTAL
         * 
         * CHANGEMENTS V3.0.0 (29/01/2026) :
         *   - Layout HORIZONTAL COMPACT : tout sur une ligne
         *   - Structure : [ID] [Photo] [Nom ♂ Âge] [Pathologies inline] [›]
         *   - Réduit drastiquement l'espace blanc vertical
         *   - Expand restaure le layout vertical détaillé
         * 
         * CHANGEMENTS V2.0.0 (26/01/2026) :
         *   - UNIFORMISATION avec createPatientCardChat
         *   - Même contenu : ID, badges, pathologies groupées, tags, commentaires, IA
         *   - Chevron au lieu de loupe pour expand/collapse
         *   - Mêmes styles CSS (info-badge-light, patho-tag-dark, etc.)
         */
        function createPatientItemClassique(patient) {
            const item = document.createElement('div');
            item.className = 'patient-item-classique';
            
            // Récupérer l'ID et le nom du patient
            const patientId = patient.id;
            const patientFullName = (patient.oriprenom && patient.orinom) 
                ? `${patient.oriprenom} ${patient.orinom}`.trim()
                : `${capitalize(patient.prenom || '')} ${capitalize(patient.nom || '')}`.trim() || 'Patient';
            
            // V3.0 : Patient référence en JAUNE FLUO
            const isReference = memeState.isReference(patientId);
            if (isReference) {
                item.classList.add('reference-patient');
            }
            
            // ╔═══════════════════════════════════════════════════════════════
            // ║ V3.0 COMPACT : ID badge inline
            // ╚═══════════════════════════════════════════════════════════════
            const idBadge = document.createElement('div');
            idBadge.className = 'patient-id-badge';
            idBadge.textContent = patientId;
            item.appendChild(idBadge);
            
            // ╔═══════════════════════════════════════════════════════════════
            // ║ PHOTOFIT V5.2 : Badge score de similarité (mode Classique)
            // ╚═══════════════════════════════════════════════════════════════
            if (patient.similarity_score !== undefined && patient.similarity_score !== null) {
                const score = patient.similarity_score;
                const scoreBadge = document.createElement('span');
                scoreBadge.className = 'similarity-score-badge';
                
                let badgeColor, badgeEmoji;
                if (score === 100) {
                    badgeColor = '#ffc107'; badgeEmoji = '🎯';
                } else if (score >= 80) {
                    badgeColor = '#28a745'; badgeEmoji = '🟢';
                } else if (score >= 60) {
                    badgeColor = '#17a2b8'; badgeEmoji = '🔵';
                } else {
                    badgeColor = '#fd7e14'; badgeEmoji = '🟠';
                }
                
                scoreBadge.style.cssText = `
                    display: inline-block; margin-left: 6px;
                    background: ${badgeColor}; color: #fff;
                    padding: 1px 7px; border-radius: 10px;
                    font-size: 10px; font-weight: 700;
                    vertical-align: middle;
                `;
                scoreBadge.textContent = `${badgeEmoji} ${score}%`;
                scoreBadge.title = score === 100 ? 'Portrait de référence' : `Similarité : ${score}%`;
                item.appendChild(scoreBadge);
            }
            
            // ╔═══════════════════════════════════════════════════════════════
            // ║ V3.0 COMPACT : Header avec photo uniquement
            // ╚═══════════════════════════════════════════════════════════════
            const header = document.createElement('div');
            header.className = 'patient-item-header';
            
            // Photo container - CLIQUABLE pour "même portrait"
            const photoContainer = document.createElement('div');
            photoContainer.className = 'patient-photo-container';
            makePortraitMemeClickable(photoContainer, patientId, patientFullName);
            
            if (patient.portrait) {
                const photo = document.createElement('img');
                photo.className = 'patient-photo';
                photo.src = patient.portrait;
                const altName = (patient.oriprenom && patient.orinom) 
                    ? `${patient.oriprenom} ${patient.orinom}`
                    : `${patient.prenom} ${patient.nom}`;
                photo.alt = altName;
                photo.onerror = () => {
                    const placeholder = document.createElement('div');
                    placeholder.className = 'patient-photo-placeholder';
                    const initPrenom = patient.oriprenom?.[0] || patient.prenom?.[0] || '';
                    const initNom = patient.orinom?.[0] || patient.nom?.[0] || '';
                    placeholder.textContent = initPrenom.toUpperCase() + initNom.toUpperCase();
                    photo.parentNode.replaceChild(placeholder, photo);
                };
                photoContainer.appendChild(photo);
            } else {
                const placeholder = document.createElement('div');
                placeholder.className = 'patient-photo-placeholder';
                const initPrenom = patient.oriprenom?.[0] || patient.prenom?.[0] || '';
                const initNom = patient.orinom?.[0] || patient.nom?.[0] || '';
                placeholder.textContent = initPrenom.toUpperCase() + initNom.toUpperCase();
                photoContainer.appendChild(placeholder);
            }
            header.appendChild(photoContainer);
            
            // ╔═══════════════════════════════════════════════════════════════
            // ║ V3.0 COMPACT : Infos en ligne (Nom + Sexe + Âge)
            // ╚═══════════════════════════════════════════════════════════════
            const mainInfo = document.createElement('div');
            mainInfo.className = 'patient-card-main-info';
            
            // Prénom - cliquable
            const prenomSpan = document.createElement('span');
            prenomSpan.className = 'info-badge-light';
            const prenomText = patient.oriprenom || capitalize(patient.prenom || '');
            prenomSpan.textContent = prenomText;
            if (prenomText) {
                makeMemeClickable(prenomSpan, patientId, patientFullName, 'prenom', null, 'Même prénom');
            }
            mainInfo.appendChild(prenomSpan);
            
            // Nom - cliquable
            const nomSpan = document.createElement('span');
            nomSpan.className = 'info-badge-light';
            const nomText = patient.orinom || capitalize(patient.nom || '');
            nomSpan.textContent = nomText;
            if (nomText) {
                makeMemeClickable(nomSpan, patientId, patientFullName, 'nom', null, 'Même nom');
            }
            mainInfo.appendChild(nomSpan);
            
            // Sexe/Âge inline
            const genderAgeLine = document.createElement('div');
            genderAgeLine.className = 'gender-age-line';
            
            if (patient.sexe) {
                const sexeSpan = document.createElement('span');
                sexeSpan.className = 'info-badge-light info-badge-small';
                const sexeSymbol = patient.sexe === 'F' ? '♀' : patient.sexe === 'M' ? '♂' : '';
                sexeSpan.textContent = sexeSymbol;
                makeMemeClickable(sexeSpan, patientId, patientFullName, 'sexe', null, 'Même sexe');
                genderAgeLine.appendChild(sexeSpan);
            }
            
            if (patient.age) {
                const ageSpan = document.createElement('span');
                ageSpan.className = 'info-badge-light';
                ageSpan.textContent = `${Math.floor(patient.age)} ${t('ans')}`;
                makeMemeClickable(ageSpan, patientId, patientFullName, 'age', null, 'Même âge (±3 ans)');
                genderAgeLine.appendChild(ageSpan);
            }
            
            mainInfo.appendChild(genderAgeLine);
            header.appendChild(mainInfo);
            item.appendChild(header);
            
            // ╔═══════════════════════════════════════════════════════════════
            // ║ V3.0 COMPACT : Pathologies INLINE (pas de section séparée)
            // ╚═══════════════════════════════════════════════════════════════
            const pathoSource = patient.oripathologies || patient.pathologies;
            if (pathoSource) {
                const pathoSection = document.createElement('div');
                pathoSection.className = 'patient-card-section';
                
                // Titre caché en mode compact (via CSS)
                const pathoTitle = document.createElement('div');
                pathoTitle.className = 'patient-card-section-title';
                pathoTitle.textContent = t('PATHOLOGIES');
                pathoSection.appendChild(pathoTitle);
                
                // Parser les pathologies
                let pathoList = [];
                if (typeof pathoSource === 'string') {
                    pathoList = pathoSource.split(',').map(p => p.trim()).filter(p => p.length > 0);
                } else if (Array.isArray(pathoSource)) {
                    pathoList = pathoSource;
                }
                
                // Utiliser la même fonction d'affichage que le mode Chat
                const pathosDisplay = createPathologiesDisplay(pathoList, patientId, patientFullName);
                pathoSection.appendChild(pathosDisplay);
                
                item.appendChild(pathoSection);
            }
            
            // ╔═══════════════════════════════════════════════════════════════
            // ║ V3.0 : Bouton expand (chevron à droite)
            // ╚═══════════════════════════════════════════════════════════════
            const expandBtn = document.createElement('button');
            expandBtn.className = 'expand-card-btn';
            expandBtn.title = t('Voir détails');
            expandBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                item.classList.toggle('expanded');
            });
            item.appendChild(expandBtn);
            
            // ╔═══════════════════════════════════════════════════════════════
            // ║ V3.0 : Détails (masqués par défaut, visibles en expanded)
            // ╚═══════════════════════════════════════════════════════════════
            const details = document.createElement('div');
            details.className = 'patient-card-details';
            
            // Tags (si présents)
            if (patient.tags) {
                const tagsSection = document.createElement('div');
                tagsSection.className = 'patient-card-section';
                
                const tagsTitle = document.createElement('div');
                tagsTitle.className = 'patient-card-section-title';
                tagsTitle.textContent = t('Tags');
                tagsSection.appendChild(tagsTitle);
                
                const tagsDiv = document.createElement('div');
                tagsDiv.className = 'patient-tags';
                tagsDiv.style.display = 'flex';
                tagsDiv.style.flexWrap = 'wrap';
                tagsDiv.style.gap = '6px';
                
                const tagsList = typeof patient.tags === 'string' 
                    ? patient.tags.split(',').map(t => t.trim()).filter(t => t.length > 0)
                    : (Array.isArray(patient.tags) ? patient.tags : []);
                
                tagsList.forEach(tag => {
                    const tagSpan = document.createElement('span');
                    tagSpan.className = 'patho-tag-dark patho-clickable';
                    tagSpan.textContent = tag;
                    makeMemeClickable(tagSpan, patientId, patientFullName, 'tag', tag, `Même tag "${tag}"`);
                    tagsDiv.appendChild(tagSpan);
                });
                
                tagsSection.appendChild(tagsDiv);
                details.appendChild(tagsSection);
            }
            
            // Commentaires (si présents)
            if (patient.commentaires && patient.commentaires.length > 0) {
                const commSection = document.createElement('div');
                commSection.className = 'patient-card-section';
                
                const commTitle = document.createElement('div');
                commTitle.className = 'patient-card-section-title';
                commTitle.textContent = t('Commentaires');
                commSection.appendChild(commTitle);
                
                patient.commentaires.forEach(comm => {
                    if (comm.commentaire) {
                        const commDiv = document.createElement('div');
                        commDiv.className = 'patient-comment';
                        commDiv.innerHTML = `<strong>${comm.pathologie}</strong>: ${comm.commentaire}`;
                        if (comm.auteur) {
                            commDiv.innerHTML += ` <em>(${comm.auteur})</em>`;
                        }
                        commSection.appendChild(commDiv);
                    }
                });
                
                details.appendChild(commSection);
            }
            
            // ╔═══════════════════════════════════════════════════════════════
            // ║ ZONE IA v1.0 - Chat avec l'IA sur ce patient (MODE CLASSIQUE)
            // ║ Ajouté V2.5.2 - Uniformisation avec createPatientCardChat
            // ║ V2.5.3 - Suppression ligne bleue séparatrice
            // ╚═══════════════════════════════════════════════════════════════
            const iaSection = document.createElement('div');
            iaSection.style.marginTop = '15px';
            
            const iaTitle = document.createElement('div');
            iaTitle.className = 'patient-card-section-title';
            iaTitle.style.color = 'var(--primary-color)';
            iaTitle.innerHTML = '🤖 ' + t('Demander à l\'IA');
            iaSection.appendChild(iaTitle);
            
            // Container pour input + bouton
            const iaInputContainer = document.createElement('div');
            iaInputContainer.style.display = 'flex';
            iaInputContainer.style.gap = '10px';
            iaInputContainer.style.marginTop = '10px';
            
            const iaInput = document.createElement('textarea');
            iaInput.placeholder = t('Votre question pour l\'IA...');
            iaInput.style.flex = '1';
            iaInput.style.padding = '10px';
            iaInput.style.borderRadius = '8px';
            iaInput.style.border = '1px solid var(--border-color)';
            iaInput.style.backgroundColor = 'var(--bg-secondary)';
            iaInput.style.color = 'var(--text-primary)';
            iaInput.style.fontSize = '13px';
            iaInput.style.resize = 'vertical';
            iaInput.style.minHeight = '60px';
            iaInput.style.maxHeight = '150px';
            iaInputContainer.appendChild(iaInput);
            
            const iaButton = document.createElement('button');
            iaButton.innerHTML = '🤖';
            iaButton.title = t('Demander à l\'IA');
            iaButton.style.padding = '10px 15px';
            iaButton.style.borderRadius = '8px';
            iaButton.style.border = 'none';
            iaButton.style.backgroundColor = 'var(--primary-color)';
            iaButton.style.color = 'white';
            iaButton.style.fontSize = '18px';
            iaButton.style.cursor = 'pointer';
            iaButton.style.transition = 'background-color 0.2s';
            iaButton.onmouseover = () => iaButton.style.backgroundColor = 'var(--button-hover)';
            iaButton.onmouseout = () => iaButton.style.backgroundColor = 'var(--primary-color)';
            
            // Handler du clic sur le bouton IA
            iaButton.onclick = async (e) => {
                e.stopPropagation();
                const question = iaInput.value.trim();
                if (!question) {
                    alert(t('Veuillez saisir une question'));
                    return;
                }
                
                // Désactiver le bouton pendant le chargement
                iaButton.disabled = true;
                iaButton.innerHTML = '⏳';
                
                try {
                    const response = await askIA(patient, question);
                    showIAModal(response, patient, question);
                } catch (error) {
                    console.error('Erreur IA:', error);
                    alert(t('Erreur lors de la requête IA') + ': ' + error.message);
                } finally {
                    iaButton.disabled = false;
                    iaButton.innerHTML = '🤖';
                }
            };
            
            iaInputContainer.appendChild(iaButton);
            iaSection.appendChild(iaInputContainer);
            details.appendChild(iaSection);
            
            item.appendChild(details);
            
            return item;
        }

        // ╔════════════════════════════════════════════════════════════════
        // ║ MODIFICATION v1.0.3 : Export CSV de tous les patients
        // ║ Réexécute la requête avec limit=100000 pour récupérer tous les patients
        // ╚════════════════════════════════════════════════════════════════
        async function copyResponse(item, btn = null) {
            const nbTotal = item.response.nb_patients || 0;
            const originalText = btn ? btn.textContent : null;
            
            if (nbTotal === 0) {
                addDebugLog('Aucun patient à copier', 'info');
                return;
            }
            
            addDebugLog(`Export CSV: récupération de ${nbTotal} patients...`, 'info');
            
            // V1.0.7 : Feedback visuel - montrer que le travail est en cours
            if (btn) {
                btn.textContent = '⏳';
                btn.disabled = true;
            }
            
            try {
                // Réexécuter la requête avec limit très élevé pour tout récupérer
                const endpoint = getSearchEndpoint();
                const payload = {
                    question: item.query,
                    base: currentBase,
                    mode: searchMode,
                    lang: item.lang || selectedLanguage,
                    lang_reponse: responseLanguage,
                    limit: 100000,  // Récupérer tous les patients
                    offset: 0
                };
                
                const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const data = await response.json();
                const patients = data.patients || [];
                
                if (patients.length === 0) {
                    addDebugLog('Aucun patient récupéré', 'error');
                    // V1.0.7 : Feedback visuel - erreur
                    if (btn) {
                        btn.textContent = '❌';
                        setTimeout(() => {
                            btn.textContent = originalText;
                            btn.disabled = false;
                        }, 1500);
                    }
                    return;
                }
                
                // Construire le CSV (toutes colonnes sauf search_text)
                const colonnesExclues = ['search_text'];
                
                // Récupérer les colonnes depuis le premier patient
                const premierePatient = patients[0];
                const colonnes = Object.keys(premierePatient).filter(col => !colonnesExclues.includes(col));
                
                // En-tête CSV
                let csv = colonnes.join(';') + '\n';
                
                // Données
                patients.forEach(patient => {
                    const ligne = colonnes.map(col => {
                        let val = patient[col];
                        if (val === null || val === undefined) {
                            val = '';
                        } else if (typeof val === 'object') {
                            // Si c'est un array ou objet, le convertir en string
                            val = Array.isArray(val) ? val.join(',') : JSON.stringify(val);
                        } else {
                            val = String(val);
                        }
                        // Échapper les ; et les retours à la ligne
                        if (val.includes(';') || val.includes('\n') || val.includes('"')) {
                            val = '"' + val.replace(/"/g, '""') + '"';
                        }
                        return val;
                    });
                    csv += ligne.join(';') + '\n';
                });
                
                // Copier dans le presse-papier
                await navigator.clipboard.writeText(csv);
                
                addDebugLog(`✓ ${patients.length} patients exportés en CSV (${colonnes.length} colonnes)`, 'success');
                
                // V1.0.7 : Feedback visuel - succès ✅
                if (btn) {
                    btn.textContent = '✅';
                    setTimeout(() => {
                        btn.textContent = originalText;
                        btn.disabled = false;
                    }, 2000);
                }
                
            } catch (err) {
                console.error('Erreur export CSV:', err);
                addDebugLog(`Erreur export CSV: ${err.message}`, 'error');
                // V1.0.7 : Feedback visuel - erreur
                if (btn) {
                    btn.textContent = '❌';
                    setTimeout(() => {
                        btn.textContent = originalText;
                        btn.disabled = false;
                    }, 1500);
                }
            }
        }

        // ╔════════════════════════════════════════════════════════════════
        // ║ Rendu de l'historique complet
        // ╚════════════════════════════════════════════════════════════════
        
        function renderConversationHistory() {
            elements.resultsContainer.innerHTML = '';
            
            if (currentMode === 'classique') {
                // Mode Classique : afficher seulement la dernière
                if (conversationHistory.length > 0) {
                    renderResponse(conversationHistory[conversationHistory.length - 1]);
                }
            } else {
                // Mode IA : afficher tout l'historique
                conversationHistory.forEach(item => {
                    renderResponse(item);
                });
            }
            
            if (conversationHistory.length > 0) {
                elements.resultsContainer.classList.add('active');
                elements.welcomeContainer.style.display = 'none';
                
                if (currentMode === 'chat') {
                    elements.searchContainerBottom.classList.add('active');
                    elements.searchContainerTop.classList.remove('active');
                } else {
                    elements.searchContainerTop.classList.add('active');
                    elements.searchContainerBottom.classList.remove('active');
                }
            }
        }

        // ╔════════════════════════════════════════════════════════════════
        // ║ Sidebar - Conversations récentes
        // ╚════════════════════════════════════════════════════════════════
        
        function renderRecentConversations() {
            elements.recentConversations.innerHTML = '';
            
            // Éliminer les doublons en gardant la plus récente de chaque question
            const uniqueConversations = [];
            const seenQuestions = new Set();
            
            // Parcourir de la plus récente à la plus ancienne
            for (let i = conversationHistory.length - 1; i >= 0; i--) {
                const item = conversationHistory[i];
                const queryLower = item.query.toLowerCase().trim();
                
                if (!seenQuestions.has(queryLower)) {
                    seenQuestions.add(queryLower);
                    uniqueConversations.push(item);
                }
            }
            
            // Prendre les 10 plus récentes (après dédoublonnage)
            const recent = uniqueConversations.slice(0, 10);
            
            recent.forEach((item, index) => {
                // ╔═══════════════════════════════════════════════════════════════
                // ║ SIDEBAR v1.1.0 : Deux zones cliquables (texte + bouton ▶)
                // ╚═══════════════════════════════════════════════════════════════
                const div = document.createElement('div');
                div.className = 'sidebar-item sidebar-item-with-run';
                
                // Zone texte (cliquable pour copier)
                const textZone = document.createElement('span');
                textZone.className = 'sidebar-item-text';
                textZone.textContent = item.query;
                
                // Tooltip avec question complète + date (v1.8.0)
                const date = new Date(item.timestamp);
                const formattedDate = `${String(date.getDate()).padStart(2, '0')}/${String(date.getMonth() + 1).padStart(2, '0')}/${date.getFullYear().toString().slice(-2)} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
                textZone.title = `Clic = Copier\n─────────────\n${item.query}\n─────────────\n${formattedDate}`;
                
                // Copier dans la zone de saisie au clic sur le texte
                textZone.onclick = (e) => {
                    e.stopPropagation();
                    if (conversationHistory.length === 0 || elements.welcomeContainer.style.display !== 'none') {
                        elements.searchInputCenter.value = item.query;
                        updateSearchButtonState(elements.searchInputCenter, elements.searchButtonCenter);
                    } else {
                        if (currentMode === 'chat') {
                            elements.searchInputBottom.value = item.query;
                            updateSearchButtonState(elements.searchInputBottom, elements.searchButtonBottom);
                        } else {
                            elements.searchInputTop.value = item.query;
                            updateSearchButtonState(elements.searchInputTop, elements.searchButtonTop);
                        }
                    }
                    addDebugLog(`Conversation récente copiée: "${item.query}"`, 'info');
                };
                
                // Bouton Run (cliquable pour exécuter directement)
                const runBtn = document.createElement('button');
                runBtn.className = 'sidebar-run-btn';
                runBtn.innerHTML = '▶';
                runBtn.title = 'Exécuter cette recherche';
                runBtn.onclick = (e) => {
                    e.stopPropagation();
                    addDebugLog(`Exécution directe: "${item.query}"`, 'info');
                    searchPatients(item.query);
                };
                
                div.appendChild(textZone);
                div.appendChild(runBtn);
                elements.recentConversations.appendChild(div);
            });
            
            if (recent.length === 0) {
                const emptyDiv = document.createElement('div');
                emptyDiv.style.padding = '10px';
                emptyDiv.style.color = 'var(--text-secondary)';
                emptyDiv.style.fontSize = '14px';
                emptyDiv.textContent = 'Aucune recherche récente';
                elements.recentConversations.appendChild(emptyDiv);
            }
            
            // Mettre à jour les suggestions du datalist
            updateSearchSuggestions();
        }

        // ╔════════════════════════════════════════════════════════════════
        // ║ Sidebar - Exemples
        // ╚════════════════════════════════════════════════════════════════
        
        function renderExamples(examples) {
            elements.examplesList.innerHTML = '';
            
            examples.forEach(example => {
                // ╔═══════════════════════════════════════════════════════════════
                // ║ SIDEBAR v1.1.0 : Deux zones cliquables (texte + bouton ▶)
                // ╚═══════════════════════════════════════════════════════════════
                const div = document.createElement('div');
                div.className = 'sidebar-item sidebar-item-with-run';
                
                // Zone texte (cliquable pour copier)
                const textZone = document.createElement('span');
                textZone.className = 'sidebar-item-text';
                textZone.textContent = example;
                textZone.title = `Clic = Copier\n─────────────\n${example}`;
                
                textZone.onclick = (e) => {
                    e.stopPropagation();
                    if (conversationHistory.length === 0) {
                        elements.searchInputCenter.value = example;
                        updateSearchButtonState(elements.searchInputCenter, elements.searchButtonCenter);
                    } else {
                        if (currentMode === 'chat') {
                            elements.searchInputBottom.value = example;
                            updateSearchButtonState(elements.searchInputBottom, elements.searchButtonBottom);
                        } else {
                            elements.searchInputTop.value = example;
                            updateSearchButtonState(elements.searchInputTop, elements.searchButtonTop);
                        }
                    }
                    addDebugLog(`Exemple copié: "${example}"`, 'info');
                };
                
                // Bouton Run (cliquable pour exécuter directement)
                const runBtn = document.createElement('button');
                runBtn.className = 'sidebar-run-btn';
                runBtn.innerHTML = '▶';
                runBtn.title = 'Exécuter cette recherche';
                runBtn.onclick = (e) => {
                    e.stopPropagation();
                    addDebugLog(`Exécution directe exemple: "${example}"`, 'info');
                    searchPatients(example);
                };
                
                div.appendChild(textZone);
                div.appendChild(runBtn);
                elements.examplesList.appendChild(div);
            });
            
            // Mettre à jour les suggestions du datalist
            updateSearchSuggestions();
        }

        // ╔════════════════════════════════════════════════════════════════
        // ║ SUGGESTIONS v1.1.0 : Mise à jour du datalist pour autocomplétion
        // ║ Combine historique récent + exemples sans doublons
        // ╚════════════════════════════════════════════════════════════════
        
        function updateSearchSuggestions() {
            const datalist = document.getElementById('searchSuggestions');
            if (!datalist) return;
            
            // Vider le datalist
            datalist.innerHTML = '';
            
            const suggestions = new Set();
            
            // 1. Ajouter les recherches récentes (les plus récentes en premier)
            for (let i = conversationHistory.length - 1; i >= 0; i--) {
                const query = conversationHistory[i].query;
                if (query && query.trim()) {
                    suggestions.add(query.trim());
                }
            }
            
            // 2. Ajouter les exemples (parseExamples gère texte brut et JSON)
            const examplesText = localStorage.getItem('searchExamples');
            const examples = parseExamples(examplesText);
            
            examples.forEach(example => {
                if (example && example.trim()) {
                    suggestions.add(example.trim());
                }
            });
            
            // 3. Créer les options du datalist
            suggestions.forEach(suggestion => {
                const option = document.createElement('option');
                option.value = suggestion;
                datalist.appendChild(option);
            });
            
            console.log(`[Suggestions] ${suggestions.size} suggestions chargées dans le datalist`);
        }

        // ╔════════════════════════════════════════════════════════════════
        // ║ Nouvelle recherche
        // ║ v1.2.0 : Force une nouvelle illustration aléatoire (search/medical)
        // ╚════════════════════════════════════════════════════════════════
        
        function newSearch() {
            conversationHistory = [];
            saveConversationHistory();
            
            elements.resultsContainer.innerHTML = '';
            elements.resultsContainer.classList.remove('active');
            elements.searchContainerBottom.classList.remove('active');
            elements.searchContainerTop.classList.remove('active');
            elements.welcomeContainer.style.display = 'flex';
            elements.searchInputCenter.value = '';
            elements.searchInputBottom.value = '';
            elements.searchInputTop.value = '';
            
            // V2.1.0 : MAINTENIR le mode actuel (Chat ou Classique)
            // Ne plus forcer le mode Chat
            // Le mode reste inchangé (currentMode conserve sa valeur)
            
            renderRecentConversations();
            
            // FILIGRANE DYNAMIQUE v1.5 : Forcer une image aléatoire search/medical
            _forceRandomImage = true;  // Active le flag pour ignorer l'image du moteur
            updateFiligraneGhost();
            animateFiligraneFromMax();
            
            addDebugLog('Nouvelle recherche initiée (mode conservé: ' + currentMode + ')', 'info');
        }

        

        // ╔════════════════════════════════════════════════════════════════
        // ║ MODULE 6 : SEARCH & INTERACTIONS (search9.txt)
        // ║ v10 - Nettoyage code mort, séparation CSS
        // ╚════════════════════════════════════════════════════════════════
        
        // ╔════════════════════════════════════════════════════════════════
        // ║ Initialisation des éléments DOM
        // ╚════════════════════════════════════════════════════════════════
        
        function initElements() {
            /**
             * Réinitialise l'objet elements avec les éléments DOM réels.
             * À appeler APRÈS DOMContentLoaded pour garantir que le DOM est prêt.
             */
            elements = {
                // Header
                logo: document.getElementById('logo'),
                baseSelector: document.getElementById('baseSelector'),
                baseSubtitle: document.getElementById('baseSubtitle'),
                
                // TOOLBAR TOGGLE v1.0.0 : Checkbox et container masquable
                searchToolbarToggle: document.getElementById('searchToolbarToggle'),
                headerToolbar: document.getElementById('headerToolbar'),
                searchTitle: document.getElementById('searchTitle'),
                
                // Bouton langue + popup CHIPS (V2.0 - simplifié)
                langButton: document.getElementById('langButton'),
                langFlag: document.getElementById('langFlag'),
                langText: document.getElementById('langText'),
                langPopup: document.getElementById('langPopup'),
                chipsContainer: document.getElementById('chipsContainer'),
                // V2.0 : responseFrCheckbox géré dans i18n.js via initResponseFrCheckbox()
                // SUPPRIMÉ V2.0 : langPopupClose, responseLangToggle, labelOrigine, labelFR
                
                searchModeSelector: document.getElementById('searchModeSelector'),
                
                // Mode de détection v5.0 (simplifié - Compare supprimé)
                detectionModeControls: document.getElementById('detectionModeControls'),
                detectionModeSelector: document.getElementById('detectionModeSelector'),
                // SUPPRIMÉ web5 : detectionMode2Container, detectionMode2Selector, compareModeCheckbox, unionModeCheckbox
                
                modeToggle: document.getElementById('modeToggle'),
                modeLabel: document.getElementById('modeLabel'),
                themeToggle: document.getElementById('themeToggle'),
                settingsButton: document.getElementById('settingsButton'),
                
                // Containers
                welcomeContainer: document.getElementById('welcomeContainer'),
                resultsContainer: document.getElementById('resultsContainer'),
                searchContainerBottom: document.getElementById('searchContainerBottom'),
                searchContainerTop: document.getElementById('searchContainerTop'),
                loading: document.getElementById('loading'),
                
                // Inputs
                searchInputCenter: document.getElementById('searchInputCenter'),
                searchInputBottom: document.getElementById('searchInputBottom'),
                searchInputTop: document.getElementById('searchInputTop'),
                searchButtonCenter: document.getElementById('searchButtonCenter'),
                searchButtonBottom: document.getElementById('searchButtonBottom'),
                searchButtonTop: document.getElementById('searchButtonTop'),
                
                // Sidebar
                newSearchBtn: document.getElementById('newSearchBtn'),
                recentConversations: document.getElementById('recentConversations'),
                examplesList: document.getElementById('examplesList'),
                sidebarToggle: document.getElementById('sidebarToggle'),
                sidebar: document.querySelector('.sidebar'),
                sidebarResizeHandle: document.getElementById('sidebarResizeHandle'),
                versionDisplay: document.getElementById('versionDisplay'),
                
                // SUPPRIMÉ v1.0.0 (web8) : Modal Paramètres déplacé vers web9params.html
                // Les éléments suivants n'existent plus dans cette page :
                // settingsModal, closeSettings, userNameInput, themeSelect, styleSelect,
                // resultsLimitInput, pageSizeInput, filigraneSlider, filigraneValue,
                // demoDurationInput, examplesTextarea, saveSettingsBtn, et toutes les checkboxes
                
                welcomeUserName: document.getElementById('welcomeUserName'),
                
                // MODE DÉMO v1.0
                demoToggle: document.getElementById('demoToggle'),
                demoProgressRing: document.getElementById('demoProgressRing')
                
                // SUPPRIMÉ v1.0.0 : Debug panel et DeepL API supprimés
            };
            
            // Vérifier que tous les éléments essentiels sont trouvés
            const essentiels = [
                'baseSelector', 'searchInputCenter', 'resultsContainer', 
                'welcomeContainer', 'loading', 'searchModeSelector'
            ];
            
            let manquants = [];
            for (let key of essentiels) {
                if (!elements[key]) {
                    manquants.push(key);
                }
            }
            
            if (manquants.length > 0) {
                console.error('⚠️ Éléments DOM manquants:', manquants);
                addDebugLog(`⚠️ Éléments DOM manquants: ${manquants.join(', ')}`, 'error');
            } else {
                console.log('✅ Tous les éléments DOM initialisés');
                addDebugLog('✅ Éléments DOM initialisés', 'success');
            }
        }
        
        // ╔════════════════════════════════════════════════════════════════
        // ║ NOUVEAU v1.0.7 : Gestion activation/désactivation boutons
        // ╚════════════════════════════════════════════════════════════════
        
        function updateSearchButtonState(inputElement, buttonElement) {
            /**
             * Active ou désactive un bouton de recherche selon le contenu de l'input.
             * 
             * État 1 : Input vide → Bouton disabled (grisé) avec flèche ⬆️
             * État 2 : Input rempli → Bouton enabled (bleu) avec flèche ⬆️
             * État 3 : Recherche en cours → Bouton loading avec horloge ⏳
             */
            if (!inputElement || !buttonElement) return;
            
            const hasText = inputElement.value.trim().length > 0;
            
            if (hasText) {
                buttonElement.disabled = false;
                buttonElement.title = 'Lancer la recherche';
            } else {
                buttonElement.disabled = true;
                buttonElement.title = 'Saisir du texte pour rechercher';
            }
        }
        
        function setButtonLoading(buttonElement, isLoading) {
            /**
             * Passe un bouton en mode loading (horloge tournante) ou normal.
             */
            if (!buttonElement) return;
            
            if (isLoading) {
                buttonElement.classList.add('loading');
                buttonElement.disabled = true;
                buttonElement.textContent = ''; // Le ::before avec ⏳ s'affiche via CSS
            } else {
                buttonElement.classList.remove('loading');
                buttonElement.textContent = '⬆️';
                // Réactiver selon le contenu de l'input
                const inputId = buttonElement.id.replace('Button', 'Input');
                const inputElement = document.getElementById(inputId);
                updateSearchButtonState(inputElement, buttonElement);
            }
        }
        
        function attachInputListeners(inputElement, buttonElement) {
            /**
             * Attache les listeners d'input pour activer/désactiver le bouton.
             */
            if (!inputElement || !buttonElement) return;
            
            inputElement.addEventListener('input', () => {
                updateSearchButtonState(inputElement, buttonElement);
                
                // FILIGRANE DYNAMIQUE v1.1 : Restaurer le filigrane quand on commence à saisir
                if (inputElement.value.length > 0 && typeof restoreFiligraneIntensity === 'function') {
                    restoreFiligraneIntensity();
                }
            });
            
            inputElement.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !buttonElement.disabled) {
                    buttonElement.click();
                }
            });
        }
        
        // ╔════════════════════════════════════════════════════════════════
        // ║ Initialisation
        // ╚════════════════════════════════════════════════════════════════
        
        window.addEventListener('DOMContentLoaded', async () => {
            // Initialiser les éléments DOM EN PREMIER
            initElements();
            
            addDebugLog('═══════════════════════════════════════', 'info');
            addDebugLog('Initialisation de l\'application...', 'info');
            addDebugLog(`Version: search v9 (multilingue + boutons flèches)`, 'info');
            addDebugLog('═══════════════════════════════════════', 'info');
            
            // ╔════════════════════════════════════════════════════════════════
            // ║ Event listeners (après initElements)
            // ╚════════════════════════════════════════════════════════════════
            
            // Recherche - Bouton center
            elements.searchButtonCenter.addEventListener('click', () => {
                const query = elements.searchInputCenter.value;
                if (query.trim()) {
                    setButtonLoading(elements.searchButtonCenter, true);
                    searchPatients(query).finally(() => {
                        setButtonLoading(elements.searchButtonCenter, false);
                    });
                }
            });
            
            // Recherche - Bouton bottom
            elements.searchButtonBottom.addEventListener('click', () => {
                const query = elements.searchInputBottom.value;
                if (query.trim()) {
                    setButtonLoading(elements.searchButtonBottom, true);
                    searchPatients(query).finally(() => {
                        setButtonLoading(elements.searchButtonBottom, false);
                    });
                }
            });
            
            // Recherche - Bouton top
            elements.searchButtonTop.addEventListener('click', () => {
                const query = elements.searchInputTop.value;
                if (query.trim()) {
                    setButtonLoading(elements.searchButtonTop, true);
                    searchPatients(query).finally(() => {
                        setButtonLoading(elements.searchButtonTop, false);
                    });
                }
            });
            
            // NOUVEAU v1.0.7 : Attacher listeners pour activation/désactivation boutons
            attachInputListeners(elements.searchInputCenter, elements.searchButtonCenter);
            attachInputListeners(elements.searchInputBottom, elements.searchButtonBottom);
            attachInputListeners(elements.searchInputTop, elements.searchButtonTop);
            
            // Initialiser l'état des boutons
            updateSearchButtonState(elements.searchInputCenter, elements.searchButtonCenter);
            updateSearchButtonState(elements.searchInputBottom, elements.searchButtonBottom);
            updateSearchButtonState(elements.searchInputTop, elements.searchButtonTop);
            
            // ╔════════════════════════════════════════════════════════════════
            // ║ VOICE SEARCH v1.0.0 : Initialisation des boutons micro
            // ╚════════════════════════════════════════════════════════════════
            voiceSearchManager.initButtons([
                { inputId: 'searchInputCenter', buttonId: 'voiceBtnCenter' },
                { inputId: 'searchInputTop', buttonId: 'voiceBtnTop' },
                { inputId: 'searchInputBottom', buttonId: 'voiceBtnBottom' }
            ]);
            
            // Nouvelle recherche
            elements.newSearchBtn.addEventListener('click', newSearch);
            
            // Toggle sidebar
            elements.sidebarToggle.addEventListener('click', () => {
                elements.sidebar.classList.toggle('collapsed');
            });
            
            // SUPPRIMÉ v1.0.25 : Event listener baseSelector déplacé plus bas (était en doublon)
            
            // Changement de mode de recherche
            elements.searchModeSelector.addEventListener('change', () => {
                searchMode = elements.searchModeSelector.value;
                localStorage.setItem('searchMode', searchMode);
                addDebugLog(`Mode de recherche changé: ${searchMode}`, 'info');
            });
            
            // ╔════════════════════════════════════════════════════════════════
            // ║ Mode de détection v1.3 - avec mise à jour filigrane
            // ╚════════════════════════════════════════════════════════════════
            
            // Changement du mode de détection principal
            if (elements.detectionModeSelector) {
                elements.detectionModeSelector.addEventListener('change', () => {
                    onDetectionModeChange();
                    addDebugLog(`Mode de détection: ${detectionMode}`, 'info');
                });
            }
            
            // SUPPRIMÉ web10 : Event listeners pour detectionMode2, compareMode, unionMode
            // Ces éléments n'existent plus dans l'interface
            
            // Event listeners bouton langue + popup CHIPS (v1.7.0)
            if (elements.langButton) {
                elements.langButton.addEventListener('click', toggleLangPopup);
            }
            // V2.0 : Plus de bouton langPopupClose (supprimé)
            
            // V2.0 : Initialiser la checkbox fr externe
            if (typeof initResponseFrCheckbox === 'function') {
                initResponseFrCheckbox();
            }
            
            // Fermer popup langue si clic en dehors
            document.addEventListener('click', (e) => {
                if (elements.langPopup && elements.langPopup.style.display === 'block') {
                    if (!elements.langButton.contains(e.target) && !elements.langPopup.contains(e.target)) {
                        elements.langPopup.style.display = 'none';
                    }
                }
            });
            
            // ╔════════════════════════════════════════════════════════════════
            // ║ Sidebar redimensionnable (v1.8.0)
            // ╚════════════════════════════════════════════════════════════════
            if (elements.sidebarResizeHandle && elements.sidebar) {
                let isResizing = false;
                let startX = 0;
                let startWidth = 0;
                
                elements.sidebarResizeHandle.addEventListener('mousedown', (e) => {
                    isResizing = true;
                    startX = e.clientX;
                    startWidth = elements.sidebar.offsetWidth;
                    elements.sidebarResizeHandle.classList.add('dragging');
                    document.body.style.cursor = 'ew-resize';
                    document.body.style.userSelect = 'none';
                    e.preventDefault();
                });
                
                document.addEventListener('mousemove', (e) => {
                    if (!isResizing) return;
                    
                    const diff = e.clientX - startX;
                    const newWidth = Math.min(Math.max(startWidth + diff, 200), 500);
                    elements.sidebar.style.width = newWidth + 'px';
                });
                
                document.addEventListener('mouseup', () => {
                    if (isResizing) {
                        isResizing = false;
                        elements.sidebarResizeHandle.classList.remove('dragging');
                        document.body.style.cursor = '';
                        document.body.style.userSelect = '';
                        // Sauvegarder la largeur
                        localStorage.setItem('sidebarWidth', elements.sidebar.offsetWidth);
                    }
                });
                
                // Restaurer la largeur sauvegardée
                const savedWidth = localStorage.getItem('sidebarWidth');
                if (savedWidth) {
                    elements.sidebar.style.width = savedWidth + 'px';
                }
            }
            
            // Toggle mode IA/Classique (checkbox cachée - rétrocompatibilité)
            if (elements.modeToggle) {
                elements.modeToggle.addEventListener('change', () => switchMode());
            }
            
            // V2.4.0 : Event listeners pour les puces rondes
            const pillChat = document.getElementById('modePillChat');
            const pillClassique = document.getElementById('modePillClassique');
            if (pillChat && pillClassique) {
                pillChat.addEventListener('click', () => switchMode('chat'));
                pillClassique.addEventListener('click', () => switchMode('classique'));
                
                // Initialiser l'état des puces selon currentMode
                pillChat.classList.toggle('active', currentMode === 'chat');
                pillClassique.classList.toggle('active', currentMode === 'classique');
            }
            
            // ═══════════════════════════════════════════════════════════════
            // BASE CHANGE v5.1 : Event listeners changement de base
            // ═══════════════════════════════════════════════════════════════
            // Changement depuis la toolbar
            if (elements.baseSelector) {
                elements.baseSelector.addEventListener('change', () => {
                    onBaseChange(false); // false = depuis toolbar
                });
            }
            // Changement depuis les paramètres
            if (elements.baseSelectorSettings) {
                elements.baseSelectorSettings.addEventListener('change', () => {
                    onBaseChange(true); // true = depuis paramètres
                });
            }
            // ═══════════════════════════════════════════════════════════════
            // FIN BASE CHANGE v5.1
            // ═══════════════════════════════════════════════════════════════
            
            // ═══════════════════════════════════════════════════════════════
            // TOOLBAR TOGGLE v1.0.0 : Masquer/afficher la barre d'outils
            // ═══════════════════════════════════════════════════════════════
            if (elements.searchToolbarToggle && elements.headerToolbar) {
                // Charger l'état depuis localStorage
                const toolbarVisible = localStorage.getItem('searchToolbarVisible');
                if (toolbarVisible === 'true') {
                    elements.searchToolbarToggle.checked = true;
                    elements.headerToolbar.classList.remove('hidden');
                } else {
                    elements.searchToolbarToggle.checked = false;
                    elements.headerToolbar.classList.add('hidden');
                }
                
                // Écouter les changements
                elements.searchToolbarToggle.addEventListener('change', () => {
                    const isChecked = elements.searchToolbarToggle.checked;
                    if (isChecked) {
                        elements.headerToolbar.classList.remove('hidden');
                    } else {
                        elements.headerToolbar.classList.add('hidden');
                    }
                    localStorage.setItem('searchToolbarVisible', isChecked);
                    addDebugLog(`Toolbar ${isChecked ? 'affichée' : 'masquée'}`, 'info');
                });
            }
            // ═══════════════════════════════════════════════════════════════
            // FIN TOOLBAR TOGGLE v1.0.0
            // ═══════════════════════════════════════════════════════════════
            
            // Toggle thème
            elements.themeToggle.addEventListener('click', toggleTheme);
            
            // ╔═══════════════════════════════════════════════════════════════
            // ║ PARAMÈTRES v1.0.0 (web8) : Navigation vers page dédiée
            // ║ Remplace le modal par une navigation vers web9params.html
            // ╚═══════════════════════════════════════════════════════════════
            elements.settingsButton.addEventListener('click', () => {
                window.location.href = 'webparams.html';
            });
            
            // SUPPRIMÉ v1.0.0 (web8) : Event listeners du modal paramètres
            // closeSettings, settingsModal click, saveSettingsBtn
            
            // SUPPRIMÉ v1.0.0 : Debug checkbox event listener supprimé
            
            // SUPPRIMÉ v1.0.0 (web8) : filigraneSlider event listener (déplacé vers web9params.html)
            
            // STYLE v1.0.0 : Event listener du sélecteur de style (applique en temps réel)
            if (elements.styleSelect) {
                elements.styleSelect.addEventListener('change', () => {
                    const style = elements.styleSelect.value;
                    applyStyle(style);
                    localStorage.setItem('uiStyle', style);
                });
            }
            
            // MODE DÉMO v1.0 : Event listener du switch
            if (elements.demoToggle) {
                elements.demoToggle.addEventListener('change', () => {
                    if (elements.demoToggle.checked) {
                        startDemoMode();
                    } else {
                        stopDemoMode();
                    }
                });
            }
            
            // SUPPRIMÉ v1.0.0 : Debug panel buttons event listeners supprimés
            
            // ╔════════════════════════════════════════════════════════════════
            // ║ Chargement initial
            // ╚════════════════════════════════════════════════════════════════
            
            // Charger les langues actives depuis /params AVANT loadSettings
            await loadActiveLanguages();
            
            loadSettings();
            
            // Appliquer le mode moderne par défaut
            document.body.classList.add('mode-chat');
            
            // ╔═══════════════════════════════════════════════════════════════
            // ║ FORCER RENDU v1.0.0 : Régénérer les chips et exemples après init
            // ╚═══════════════════════════════════════════════════════════════
            generateLangChips();
            updateBaseSubtitle(); // Afficher la base par défaut
            
            // ╔═══════════════════════════════════════════════════════════════
            // ║ CHARGEMENT PARALLÈLE v1.1 : Ne pas bloquer l'UI sur l'animation
            // ║ Les moteurs IA, illustrations et i18n se chargent en parallèle
            // ╚═══════════════════════════════════════════════════════════════
            
            // Charger version serveur (rapide, pas de délai)
            await loadServerVersion();
            
            // Déterminer si on a une requête URL (pour skip les délais)
            const urlParams = new URLSearchParams(window.location.search);
            const queryFromUrl = urlParams.get('q');
            const hasUrlQuery = queryFromUrl && queryFromUrl.trim().length > 0;
            
            // Lancer TOUS les chargements en parallèle
            const [basesResult, iaResult, illusResult, i18nResult] = await Promise.all([
                loadAvailableBases(hasUrlQuery),  // Passer hasUrlQuery pour skip animation
                loadIAModels(),
                illustrationsManager.init(API_BASE_URL),
                loadI18n()
            ]);
            
            // Logs des résultats
            if (iaResult) {
                addDebugLog(`Moteurs IA chargés ✓ (${Object.keys(IA_MODELS_CACHE).length} moteurs)`, 'success');
            } else {
                addDebugLog('Moteurs IA non disponibles (fallback statique)', 'info');
            }
            
            if (illusResult) {
                addDebugLog(`Illustrations chargées ✓ (${illustrationsManager.hasImages() ? 'images disponibles' : 'VIDE!'})`, 'success');
            } else {
                addDebugLog('Illustrations non disponibles (fallback)', 'info');
            }
            
            if (i18nResult) {
                addDebugLog(`i18n chargé ✓ (${Object.keys(I18N_CACHE).length} textes UI)`, 'success');
            } else {
                addDebugLog('i18n non disponible (fallback français)', 'info');
            }
            
            // Afficher le filigrane initial (après chargement IA et illustrations)
            updateFiligraneGhost();
            
            // ╔═══════════════════════════════════════════════════════════════
            // ║ URL PARAMS v1.1 : Gérer les paramètres ?q=, ?base=, ?lang=
            // ╚═══════════════════════════════════════════════════════════════
            const langFromUrl = urlParams.get('lang');
            
            // Appliquer la langue si fournie
            if (langFromUrl && elements.langSelector) {
                elements.langSelector.value = langFromUrl;
                selectedLanguage = langFromUrl;
                addDebugLog(`Langue depuis URL: ${langFromUrl}`, 'info');
            }
            
            if (queryFromUrl) {
                addDebugLog(`Recherche depuis URL: "${queryFromUrl}"`, 'info');
                // Remplir le champ de recherche
                if (elements.searchInputCenter) {
                    elements.searchInputCenter.value = queryFromUrl;
                }
                // Lancer la recherche immédiatement (sans délai pour requête URL)
                searchPatients(queryFromUrl);
            }
            
            addDebugLog('Application prête', 'success');
        });
        
        // Écouter les changements de thème système
        window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
            if (elements.themeSelect.value === 'auto') {
                applyTheme('auto');
            }
        });


/* ═══════════════════════════════════════════════════════════════
           MODULE 6bis : CHAT IA - Interrogation LLM sur un patient
           ═══════════════════════════════════════════════════════════════ */

        /**
         * Interroge l'IA via POST /ia/ask
         * @param {object} patient - Données du patient
         * @param {string} question - Question de l'utilisateur
         * @returns {Promise<object>} Réponse de l'IA
         */
        async function askIA(patient, question) {
            const payload = {
                moteur: detectionMode !== 'standard' ? detectionMode : 'gpt4o',
                patient: {
                    nom: patient.orinom || patient.nom || 'Inconnu',
                    prenom: patient.oriprenom || patient.prenom || '',
                    age: patient.age,
                    sexe: patient.sexe,
                    oripathologies: patient.oripathologies || patient.pathologies || '',
                    commentaires: patient.commentaires || []
                },
                question: question,
                lang: selectedLanguage === 'auto' ? 'fr' : selectedLanguage  // Langue pour la réponse IA
            };
            
            const response = await fetch(`${API_BASE_URL}/ia/ask`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.detail || `HTTP ${response.status}`);
            }
            
            return await response.json();
        }
        
        /**
         * Affiche la modale avec la réponse de l'IA
         * @param {object} response - Réponse de /ia/ask {reponse, moteur, temps_ms}
         * @param {object} patient - Données du patient (pour contexte)
         * @param {string} question - Question posée à l'IA
         */
        function showIAModal(response, patient, question) {
            // Supprimer une éventuelle modale existante
            const existingModal = document.getElementById('iaResponseModal');
            if (existingModal) {
                existingModal.remove();
            }
            
            // Créer l'overlay
            const overlay = document.createElement('div');
            overlay.id = 'iaResponseModal';
            overlay.style.position = 'fixed';
            overlay.style.top = '0';
            overlay.style.left = '0';
            overlay.style.width = '100%';
            overlay.style.height = '100%';
            overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.6)';
            overlay.style.display = 'flex';
            overlay.style.alignItems = 'center';
            overlay.style.justifyContent = 'center';
            overlay.style.zIndex = '10000';
            overlay.style.backdropFilter = 'blur(4px)';
            
            // Créer la modale
            const modal = document.createElement('div');
            modal.style.backgroundColor = 'var(--bg-primary)';
            modal.style.borderRadius = '16px';
            modal.style.padding = '25px';
            modal.style.maxWidth = '600px';
            modal.style.width = '90%';
            modal.style.maxHeight = '80vh';
            modal.style.overflow = 'auto';
            modal.style.boxShadow = '0 20px 60px rgba(0, 0, 0, 0.3)';
            modal.style.position = 'relative';
            
            // Header avec titre et bouton fermer
            const header = document.createElement('div');
            header.style.display = 'flex';
            header.style.justifyContent = 'space-between';
            header.style.alignItems = 'center';
            header.style.marginBottom = '20px';
            header.style.paddingBottom = '15px';
            header.style.borderBottom = '1px solid var(--border-color)';
            
            const title = document.createElement('h3');
            title.style.margin = '0';
            title.style.color = 'var(--primary-color)';
            title.innerHTML = `🤖 ${t('Réponse IA')}`;
            header.appendChild(title);
            
            const closeBtn = document.createElement('button');
            closeBtn.innerHTML = '✖';
            closeBtn.style.background = 'none';
            closeBtn.style.border = 'none';
            closeBtn.style.fontSize = '20px';
            closeBtn.style.cursor = 'pointer';
            closeBtn.style.color = 'var(--text-secondary)';
            closeBtn.onclick = () => overlay.remove();
            header.appendChild(closeBtn);
            
            modal.appendChild(header);
            
            // ═══════════════════════════════════════════════════════════════
            // SECTION QUESTION v1.0.0 - Fond bleu avec info base/moteur
            // ═══════════════════════════════════════════════════════════════
            const questionSection = document.createElement('div');
            questionSection.style.backgroundColor = 'var(--primary-color)';
            questionSection.style.padding = '15px';
            questionSection.style.borderRadius = '8px';
            questionSection.style.marginBottom = '15px';
            
            // Texte de la question (blanc sur bleu)
            const questionText = document.createElement('div');
            questionText.style.color = 'white';
            questionText.style.fontSize = '14px';
            questionText.style.fontWeight = '500';
            questionText.style.lineHeight = '1.5';
            questionText.textContent = question || '';
            questionSection.appendChild(questionText);
            
            // Info base/moteur (petits caractères noirs sur bleu, comme le sous-titre de Search)
            const baseMoteurInfo = document.createElement('div');
            baseMoteurInfo.style.fontSize = '11px';
            baseMoteurInfo.style.color = '#1a1a1a';
            baseMoteurInfo.style.marginTop = '8px';
            baseMoteurInfo.style.opacity = '0.85';
            // Récupérer le nom de la base depuis le sélecteur
            const baseSelector = document.getElementById('baseSelector');
            const baseName = baseSelector ? baseSelector.options[baseSelector.selectedIndex]?.text || selectedBase : selectedBase;
            baseMoteurInfo.textContent = `${t('Base')}: ${baseName} • ${t('Moteur')}: ${response.moteur}`;
            questionSection.appendChild(baseMoteurInfo);
            
            modal.appendChild(questionSection);
            
            // Info patient
            const patientInfo = document.createElement('div');
            patientInfo.style.backgroundColor = 'var(--bg-secondary)';
            patientInfo.style.padding = '12px';
            patientInfo.style.borderRadius = '8px';
            patientInfo.style.marginBottom = '15px';
            patientInfo.style.fontSize = '13px';
            patientInfo.style.color = 'var(--text-secondary)';
            const patientName = (patient.oriprenom || patient.prenom || '') + ' ' + (patient.orinom || patient.nom || '');
            patientInfo.innerHTML = `<strong>Patient :</strong> ${patientName.trim()} | <strong>Modèle :</strong> ${response.moteur} | <strong>Temps :</strong> ${response.temps_ms}ms`;
            modal.appendChild(patientInfo);
            
            // Contenu de la réponse
            const content = document.createElement('div');
            content.style.lineHeight = '1.7';
            content.style.color = 'var(--text-primary)';
            content.style.whiteSpace = 'pre-wrap';
            content.style.fontSize = '14px';
            content.textContent = response.reponse;
            modal.appendChild(content);
            
            // Footer avec boutons
            const footer = document.createElement('div');
            footer.style.display = 'flex';
            footer.style.justifyContent = 'flex-end';
            footer.style.gap = '10px';
            footer.style.marginTop = '20px';
            footer.style.paddingTop = '15px';
            footer.style.borderTop = '1px solid var(--border-color)';
            
            // Bouton Copier
            const copyBtn = document.createElement('button');
            copyBtn.innerHTML = '📋';
            copyBtn.title = t('Copier');
            copyBtn.style.padding = '8px 15px';
            copyBtn.style.borderRadius = '8px';
            copyBtn.style.border = '1px solid var(--border-color)';
            copyBtn.style.backgroundColor = 'var(--bg-secondary)';
            copyBtn.style.cursor = 'pointer';
            copyBtn.style.fontSize = '16px';
            copyBtn.onclick = async () => {
                try {
                    await navigator.clipboard.writeText(response.reponse);
                    copyBtn.innerHTML = '✓';
                    setTimeout(() => copyBtn.innerHTML = '📋', 2000);
                } catch (err) {
                    console.error('Erreur copie:', err);
                }
            };
            footer.appendChild(copyBtn);
            
            // Bouton Fermer
            const closeFooterBtn = document.createElement('button');
            closeFooterBtn.textContent = t('Fermer');
            closeFooterBtn.style.padding = '8px 20px';
            closeFooterBtn.style.borderRadius = '8px';
            closeFooterBtn.style.border = 'none';
            closeFooterBtn.style.backgroundColor = 'var(--primary-color)';
            closeFooterBtn.style.color = 'white';
            closeFooterBtn.style.cursor = 'pointer';
            closeFooterBtn.onclick = () => overlay.remove();
            footer.appendChild(closeFooterBtn);
            
            modal.appendChild(footer);
            overlay.appendChild(modal);
            
            // Fermer si clic sur l'overlay (pas sur la modale)
            overlay.onclick = (e) => {
                if (e.target === overlay) {
                    overlay.remove();
                }
            };
            
            // Fermer avec Escape
            const escHandler = (e) => {
                if (e.key === 'Escape') {
                    overlay.remove();
                    document.removeEventListener('keydown', escHandler);
                }
            };
            document.addEventListener('keydown', escHandler);
            
            document.body.appendChild(overlay);
        }


/* ═══════════════════════════════════════════════════════════════
           MODULE 7 : DEBUG & UTILITAIRES
           ═══════════════════════════════════════════════════════════════ */
        
        // ╔════════════════════════════════════════════════════════════════
        // ║ SUPPRIMÉ v1.0.0 : Console de debug supprimée
        // ║ Remplacée par simple console.log pour développement
        // ╚════════════════════════════════════════════════════════════════
        
        function addDebugLog(message, type = 'info') {
            // Simple log dans la console navigateur pour debug
            if (type === 'error') {
                console.error('[DEBUG]', message);
            } else {
                console.log('[DEBUG]', message);
            }
        }

        // ╔════════════════════════════════════════════════════════════════
        // ║ Fonction de formatage de date
        // ╚════════════════════════════════════════════════════════════════
        
        function formatDateToFR(dateString) {
            if (!dateString) return '';
            
            // Si format AAAA-MM-JJ, convertir en JJ/MM/AAAA
            if (dateString.includes('-')) {
                const parts = dateString.split('-');
                if (parts.length === 3) {
                    return `${parts[2]}/${parts[1]}/${parts[0]}`;
                }
            }
            
            // Si format JJ/MM/AAAA, retourner tel quel
            if (dateString.includes('/')) {
                return dateString;
            }
            
            return dateString;
        }

        

        // ╔════════════════════════════════════════════════════════════════
        // ║ INITIALISATION - Kitview Search v1
        // ╚════════════════════════════════════════════════════════════════
        
        document.addEventListener('DOMContentLoaded', function() {
            console.log('🚀 Kitview Search v20 initialisé (Voice Search v2.0.0 + mode mains libres)');
            
            // ═══════════════════════════════════════════════════════════════
            // GESTION VISIBILITÉ DES ÉLÉMENTS DU BANDEAU (v1.0.0 web18)
            // Lecture des paramètres localStorage pour afficher/masquer
            // ═══════════════════════════════════════════════════════════════
            
            // Sélecteur de bases : visible sauf si bandeauBases === 'false'
            const baseSelector = document.getElementById('baseSelector');
            if (baseSelector) {
                const bandeauBases = localStorage.getItem('bandeauBases');
                baseSelector.style.display = (bandeauBases === 'false') ? 'none' : '';
                console.log(`[BANDEAU] Bases: ${bandeauBases} → display: ${baseSelector.style.display || 'visible'}`);
            }
            
            // Sélecteur de moteur IA : visible sauf si bandeauMoteur === 'false'
            const detectionModeSelector = document.getElementById('detectionModeSelector');
            if (detectionModeSelector) {
                const bandeauMoteur = localStorage.getItem('bandeauMoteur');
                // Par défaut MASQUÉ (null = false pour config zen initiale)
                detectionModeSelector.style.display = (bandeauMoteur === 'true') ? '' : 'none';
                console.log(`[BANDEAU] Moteur: ${bandeauMoteur} → display: ${detectionModeSelector.style.display || 'visible'}`);
            }
            
            // Boutons micro : visible sauf si activeMicro === 'false'
            const voiceBtns = document.querySelectorAll('.voice-btn');
            const activeMicro = localStorage.getItem('activeMicro');
            voiceBtns.forEach(btn => {
                btn.style.display = (activeMicro === 'false') ? 'none' : '';
            });
            console.log(`[BANDEAU] Micro: ${activeMicro} → ${voiceBtns.length} boutons ${activeMicro === 'false' ? 'masqués' : 'visibles'}`);
            
            // Switch Démo : visible sauf si bandeauSwitchDemo === 'false'
            const demoSwitchContainer = document.getElementById('demoSwitchContainer');
            if (demoSwitchContainer) {
                const bandeauSwitchDemo = localStorage.getItem('bandeauSwitchDemo');
                demoSwitchContainer.style.display = (bandeauSwitchDemo === 'false') ? 'none' : 'flex';
                console.log(`[BANDEAU] Switch Démo: ${bandeauSwitchDemo} → display: ${demoSwitchContainer.style.display}`);
            }
            
            // Switch IA/Classique : visible sauf si bandeauSwitchChat === 'false'
            const chatSwitchContainer = document.getElementById('chatSwitchContainer');
            if (chatSwitchContainer) {
                const bandeauSwitchChat = localStorage.getItem('bandeauSwitchChat');
                chatSwitchContainer.style.display = (bandeauSwitchChat === 'false') ? 'none' : 'flex';
                console.log(`[BANDEAU] Switch IA: ${bandeauSwitchChat} → display: ${chatSwitchContainer.style.display}`);
            }
            
            // Bouton Analyse : visible seulement si bandeauAnalyse === 'true'
            const analyseButton = document.getElementById('analyseButton');
            if (analyseButton) {
                const bandeauAnalyse = localStorage.getItem('bandeauAnalyse');
                analyseButton.style.display = (bandeauAnalyse === 'true') ? 'flex' : 'none';
                console.log(`[BANDEAU] Bouton Analyse: ${bandeauAnalyse} → display: ${analyseButton.style.display}`);
            }
            
            // Message de bienvenue avec nom : visible sauf si activeUsername === 'false'
            const welcomeMessage = document.querySelector('.welcome-message');
            if (welcomeMessage) {
                const activeUsername = localStorage.getItem('activeUsername');
                welcomeMessage.style.display = (activeUsername === 'false') ? 'none' : '';
                console.log(`[BANDEAU] Nom utilisateur: ${activeUsername} → display: ${welcomeMessage.style.display || 'visible'}`);
            }
        });

        // ═══════════════════════════════════════════════════════════════
        // SYNCHRONISATION INTER-ONGLETS v1.0.0
        // Écoute les changements de localStorage faits par webparams.html
        // ═══════════════════════════════════════════════════════════════
        
        window.addEventListener('storage', function(event) {
            console.log(`[SYNC] localStorage modifié: ${event.key} = ${event.newValue}`);
            
            // Sélecteur de bases
            if (event.key === 'bandeauBases') {
                const baseSelector = document.getElementById('baseSelector');
                if (baseSelector) {
                    baseSelector.style.display = (event.newValue === 'false') ? 'none' : '';
                    console.log(`[SYNC] Bases: ${event.newValue} → display: ${baseSelector.style.display || 'visible'}`);
                }
            }
            
            // Sélecteur de moteur IA
            if (event.key === 'bandeauMoteur') {
                const detectionModeSelector = document.getElementById('detectionModeSelector');
                if (detectionModeSelector) {
                    detectionModeSelector.style.display = (event.newValue === 'true') ? '' : 'none';
                    console.log(`[SYNC] Moteur: ${event.newValue} → display: ${detectionModeSelector.style.display || 'visible'}`);
                }
            }
            
            // Boutons micro
            if (event.key === 'activeMicro') {
                const voiceBtns = document.querySelectorAll('.voice-btn');
                voiceBtns.forEach(btn => {
                    btn.style.display = (event.newValue === 'false') ? 'none' : '';
                });
                console.log(`[SYNC] Micro: ${event.newValue} → ${voiceBtns.length} boutons ${event.newValue === 'false' ? 'masqués' : 'visibles'}`);
            }
            
            // Switch Démo
            if (event.key === 'bandeauSwitchDemo') {
                const demoSwitchContainer = document.getElementById('demoSwitchContainer');
                if (demoSwitchContainer) {
                    demoSwitchContainer.style.display = (event.newValue === 'false') ? 'none' : 'flex';
                    console.log(`[SYNC] Switch Démo: ${event.newValue} → display: ${demoSwitchContainer.style.display}`);
                }
            }
            
            // Switch Chat/IA
            if (event.key === 'bandeauSwitchChat') {
                const chatSwitchContainer = document.getElementById('chatSwitchContainer');
                if (chatSwitchContainer) {
                    chatSwitchContainer.style.display = (event.newValue === 'false') ? 'none' : 'flex';
                    console.log(`[SYNC] Switch Chat: ${event.newValue} → display: ${chatSwitchContainer.style.display}`);
                }
            }
            
            // Bouton Analyse
            if (event.key === 'bandeauAnalyse') {
                const analyseButton = document.getElementById('analyseButton');
                if (analyseButton) {
                    analyseButton.style.display = (event.newValue === 'true') ? 'flex' : 'none';
                    console.log(`[SYNC] Bouton Analyse: ${event.newValue} → display: ${analyseButton.style.display}`);
                }
            }
            
            // Message de bienvenue
            if (event.key === 'activeUsername' || event.key === 'userName') {
                const welcomeMessage = document.querySelector('.welcome-message');
                if (welcomeMessage) {
                    const activeUsername = localStorage.getItem('activeUsername');
                    welcomeMessage.style.display = (activeUsername === 'false') ? 'none' : '';
                    // Si le nom a changé, mettre à jour le texte
                    if (event.key === 'userName' && activeUsername !== 'false') {
                        const userName = event.newValue || '';
                        if (userName) {
                            welcomeMessage.textContent = `Bonjour ${userName} !`;
                        }
                    }
                    console.log(`[SYNC] Nom utilisateur: ${activeUsername} → display: ${welcomeMessage.style.display || 'visible'}`);
                }
            }
            
            // Base de données sélectionnée
            if (event.key === 'currentBase') {
                const baseSelector = document.getElementById('baseSelector');
                if (baseSelector && event.newValue) {
                    baseSelector.value = event.newValue;
                    console.log(`[SYNC] Base changée: ${event.newValue}`);
                }
            }
            
            // Mode de détection
            if (event.key === 'detectionMode') {
                const detectionModeSelector = document.getElementById('detectionModeSelector');
                if (detectionModeSelector && event.newValue) {
                    detectionModeSelector.value = event.newValue;
                    if (typeof detectionMode !== 'undefined') {
                        detectionMode = event.newValue;
                    }
                    if (typeof updateFiligraneGhost === 'function') {
                        updateFiligraneGhost();
                    }
                    console.log(`[SYNC] Mode détection changé: ${event.newValue}`);
                }
            }
        });
