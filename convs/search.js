/**
 * search.js V1.0.0 - 24/01/2026
 * Kitview Search - Module de recherche API
 * 
 * Ce module gère toutes les interactions avec l'API backend :
 * - Configuration de l'URL API
 * - Chargement des bases disponibles
 * - Chargement des moteurs IA
 * - Construction des payloads de recherche
 * - Exécution des recherches patients
 * 
 * Dépendances :
 * - utils.js (addDebugLog, DEBUG)
 * - Requiert que les éléments DOM soient initialisés (elements)
 * 
 * Exports (variables globales) :
 * - API_BASE_URL
 * - currentBase, currentSessionId
 * - detectionMode, detectionMode2, compareMode, unionMode
 * - IA_MODELS_CACHE (aussi sur window)
 * - searchPatients(), loadAvailableBases(), loadIAModels()
 */

/* ═══════════════════════════════════════════════════════════════════════
   CONFIGURATION API
   ═══════════════════════════════════════════════════════════════════════ */

/**
 * URL de base de l'API - Détection automatique selon l'environnement
 * - Render : utilise l'origine
 * - Localhost : utilise localhost:8000
 * - Fichier local : utilise localhost:8000
 */
const API_BASE_URL = (function() {
    const origin = window.location.origin;
    
    // Si on est sur Render ou un serveur web, utiliser l'origine
    if (origin.includes('onrender.com') || 
        origin.startsWith('http://localhost') || 
        origin.startsWith('http://127.0.0.1')) {
        return origin;
    }
    
    // Si on ouvre le fichier localement (file://), utiliser localhost
    if (origin.startsWith('file://') || origin === 'null') {
        return 'http://localhost:8000';
    }
    
    // Sinon (autre serveur web), utiliser l'origine
    return origin;
})();

// Base par défaut
const DEFAULT_BASE = 'base25000.db';

/* ═══════════════════════════════════════════════════════════════════════
   ÉTAT DE LA RECHERCHE
   ═══════════════════════════════════════════════════════════════════════ */

// Base de données active
let currentBase = DEFAULT_BASE;

// Session ID pour le système de rating
let currentSessionId = null;

// Mode de détection (IA ou standard)
let detectionMode = 'standard';
let detectionMode2 = 'gpt4o';    // Mode secondaire pour compare/union
let compareMode = false;          // Mode comparaison actif
let unionMode = false;            // Mode union actif

// Cache des moteurs IA chargés depuis /ia
// Structure: { moteur: { notes: string, image: string, actif: string } }
let IA_MODELS_CACHE = {};
window.IA_MODELS_CACHE = IA_MODELS_CACHE;  // Accessible globalement

/* ═══════════════════════════════════════════════════════════════════════
   GÉNÉRATION SESSION ID
   ═══════════════════════════════════════════════════════════════════════ */

/**
 * Génère un UUID unique pour chaque recherche (système de rating)
 * @returns {string} UUID v4
 */
function generateSessionId() {
    return crypto.randomUUID();
}

/* ═══════════════════════════════════════════════════════════════════════
   NORMALISATION DE TEXTE
   ═══════════════════════════════════════════════════════════════════════ */

/**
 * Normalise un texte pour la recherche
 * @param {string} text - Texte à normaliser
 * @returns {string} Texte normalisé (minuscules, sans accents, espaces uniques)
 */
function normalizeText(text) {
    if (!text) return '';
    
    // 1. Minuscules
    let normalized = text.toLowerCase();
    
    // 2. Suppression des accents (décomposition Unicode + suppression des diacritiques)
    normalized = normalized.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    
    // 3. Remplacement des tirets et apostrophes par des espaces
    normalized = normalized.replace(/[-_'']/g, ' ');
    
    // 4. Dédoublonnage des espaces
    normalized = normalized.replace(/\s+/g, ' ').trim();
    
    return normalized;
}

/* ═══════════════════════════════════════════════════════════════════════
   ANIMATION SEARCH STATUS
   ═══════════════════════════════════════════════════════════════════════ */

/**
 * Définit le statut visuel du titre "Search"
 * @param {string} status - 'loading' (rouge), 'connecting' (orange), 'ready' (vert), 'error' (rouge)
 */
function setSearchStatus(status) {
    const title = elements?.searchTitle;
    if (!title) return;
    
    // Enlever toutes les classes de status
    title.classList.remove('status-loading', 'status-connecting', 'status-ready', 'status-error');
    
    // Ajouter la nouvelle classe
    title.classList.add(`status-${status}`);
}

/**
 * Affiche un bandeau d'erreur serveur
 * @param {string} baseName - Nom de la base concernée
 * @param {string} errorMessage - Message d'erreur
 */
function showServerError(baseName, errorMessage) {
    // Supprimer un éventuel bandeau existant
    const existing = document.querySelector('.server-error-banner');
    if (existing) existing.remove();
    
    const banner = document.createElement('div');
    banner.className = 'server-error-banner';
    banner.innerHTML = `
        <h3>⚠️ Erreur de connexion au serveur</h3>
        <p>Base : <strong>${baseName || 'inconnue'}</strong></p>
        <p>${errorMessage}</p>
        <code>python server.py</code>
        <p style="margin-top: 10px; font-size: 12px;">Vérifiez que le serveur est lancé sur le port 8000</p>
    `;
    document.body.appendChild(banner);
    
    // Auto-suppression après 10 secondes
    setTimeout(() => {
        if (banner.parentNode) banner.remove();
    }, 10000);
}

/**
 * Cache le bandeau d'erreur serveur
 */
function hideServerError() {
    const existing = document.querySelector('.server-error-banner');
    if (existing) existing.remove();
}

/* ═══════════════════════════════════════════════════════════════════════
   CHARGEMENT DES BASES DISPONIBLES
   ═══════════════════════════════════════════════════════════════════════ */

/**
 * Charge la liste des bases disponibles depuis /bases
 * Met à jour les sélecteurs et lance l'animation de connexion
 */
async function loadAvailableBases() {
    try {
        // Rouge au départ
        setSearchStatus('loading');
        addDebugLog('Tentative de connexion à l\'API...', 'info');
        
        const response = await fetch(`${API_BASE_URL}/bases`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        const bases = data.bases || [];
        
        // Peupler le sélecteur toolbar
        elements.baseSelector.innerHTML = '';
        
        // Peupler aussi le sélecteur dans les paramètres (si existe)
        if (elements.baseSelectorSettings) {
            elements.baseSelectorSettings.innerHTML = '';
        }
        
        bases.forEach(base => {
            const option = document.createElement('option');
            option.value = base;
            option.textContent = base;
            elements.baseSelector.appendChild(option);
            
            // Dupliquer pour le sélecteur paramètres
            if (elements.baseSelectorSettings) {
                const optionSettings = option.cloneNode(true);
                elements.baseSelectorSettings.appendChild(optionSettings);
            }
        });
        
        if (bases.length === 0) {
            elements.baseSelector.innerHTML = '<option value="">Aucune base disponible</option>';
            if (elements.baseSelectorSettings) {
                elements.baseSelectorSettings.innerHTML = '<option value="">Aucune base disponible</option>';
            }
            setSearchStatus('error');
            showServerError('', 'Aucune base de données trouvée');
        } else {
            // Restaurer la base depuis localStorage ou URL
            const urlParams = new URLSearchParams(window.location.search);
            const baseFromUrl = urlParams.get('base');
            const savedBase = localStorage.getItem('currentBase');
            
            // Priorité : URL > localStorage > DEFAULT_BASE
            let targetBase = DEFAULT_BASE;
            if (baseFromUrl && bases.includes(baseFromUrl)) {
                targetBase = baseFromUrl;
            } else if (savedBase && bases.includes(savedBase)) {
                targetBase = savedBase;
            }
            
            elements.baseSelector.value = targetBase;
            if (elements.baseSelectorSettings) {
                elements.baseSelectorSettings.value = targetBase;
            }
            currentBase = targetBase;
            localStorage.setItem('currentBase', currentBase);
            
            // Mettre à jour le sous-titre de la base
            updateBaseSubtitle();
            
            // Vérifier si une requête arrive par URL (skip les délais d'animation)
            const queryFromUrl = urlParams.get('q');
            const hasUrlQuery = queryFromUrl && queryFromUrl.trim().length > 0;
            
            // Lancer l'animation de count
            await runSearchAnimation(hasUrlQuery);
            addDebugLog(`${bases.length} base(s) chargée(s), active: ${currentBase}`, 'success');
        }
        
    } catch (error) {
        console.error('Erreur chargement bases:', error);
        addDebugLog(`ERREUR chargement bases: ${error.message}`, 'error');
        
        setSearchStatus('error');
        elements.baseSelector.innerHTML = '<option value="">Serveur non connecté</option>';
        if (elements.baseSelectorSettings) {
            elements.baseSelectorSettings.innerHTML = '<option value="">Serveur non connecté</option>';
        }
        
        // Afficher la base par défaut même en cas d'erreur
        currentBase = DEFAULT_BASE;
        updateBaseSubtitle();
        
        showServerError('', error.message);
    }
}

/**
 * Animation de connexion au serveur avec comptage des patients
 * @param {boolean} skipDelays - true pour sauter les délais (requête URL)
 */
async function runSearchAnimation(skipDelays = false) {
    // Étape 1 : Rouge (déjà fait au lancement)
    setSearchStatus('loading');
    hideServerError();
    
    // Attendre 2 secondes (sauf si skipDelays)
    if (!skipDelays) {
        await new Promise(resolve => setTimeout(resolve, 2000));
    }
    
    // Étape 2 : Orange - lancement du count
    setSearchStatus('connecting');
    
    try {
        const response = await fetch(`${API_BASE_URL}/count?base=${currentBase}`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        const count = data.count || 0;
        
        // Attendre 2 secondes après réponse OK (sauf si skipDelays)
        if (!skipDelays) {
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
        
        // Étape 3 : Vert - succès
        setSearchStatus('ready');
        addDebugLog(`${count} patients dans ${currentBase}`, 'success');
        
    } catch (error) {
        console.error('Erreur comptage:', error);
        addDebugLog(`Erreur comptage: ${error.message}`, 'error');
        setSearchStatus('error');
        showServerError(currentBase, error.message);
    }
}

/**
 * Met à jour le sous-titre affichant la base active
 */
function updateBaseSubtitle() {
    if (elements?.baseSubtitle) {
        elements.baseSubtitle.textContent = currentBase || '';
    }
}

/**
 * Gestion du changement de base
 * @param {boolean} fromSettings - true si changé depuis les paramètres
 */
async function onBaseChange(fromSettings = false) {
    // Synchroniser les deux sélecteurs
    if (fromSettings && elements.baseSelectorSettings) {
        elements.baseSelector.value = elements.baseSelectorSettings.value;
    } else if (elements.baseSelectorSettings) {
        elements.baseSelectorSettings.value = elements.baseSelector.value;
    }
    
    // Mettre à jour currentBase IMMÉDIATEMENT
    currentBase = elements.baseSelector.value;
    localStorage.setItem('currentBase', currentBase);
    
    // Mettre à jour le sous-titre
    updateBaseSubtitle();
    
    addDebugLog(`Base changée: ${currentBase}`, 'info');
    
    // Fermer la modale et revenir à l'accueil (si newSearch existe)
    if (typeof elements.settingsModal !== 'undefined') {
        elements.settingsModal.classList.remove('active');
    }
    if (typeof newSearch === 'function') {
        newSearch();
    }
    
    // Relancer l'animation
    await runSearchAnimation();
}

/* ═══════════════════════════════════════════════════════════════════════
   CHARGEMENT DES MOTEURS IA
   ═══════════════════════════════════════════════════════════════════════ */

/**
 * Charge les moteurs IA depuis /ia et peuple les sélecteurs
 * @returns {boolean} true si succès
 */
async function loadIAModels() {
    try {
        const response = await fetch(`${API_BASE_URL}/ia`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        const moteursRaw = data.moteurs || [];
        
        // Filtrer uniquement les moteurs actifs (actif='O')
        const moteurs = moteursRaw.filter(m => m.actif === 'O');
        
        if (window.DEBUG) {
            console.log(`[IA] ${moteursRaw.length} moteurs chargés, ${moteurs.length} actifs`);
        }
        
        if (moteurs.length === 0) {
            console.warn('[IA] Aucun moteur IA actif');
            elements.detectionModeSelector.innerHTML = '<option value="standard">⚡ Standard</option>';
            elements.detectionModeSelector.disabled = false;
            return false;
        }
        
        // Construire le cache
        IA_MODELS_CACHE = {};
        moteurs.forEach(m => {
            IA_MODELS_CACHE[m.moteur] = {
                notes: m.notes || '',
                image: m.image || '',
                actif: m.actif || 'N'
            };
        });
        
        // Mettre à jour la référence globale
        window.IA_MODELS_CACHE = IA_MODELS_CACHE;
        
        if (window.DEBUG) {
            console.log(`[IA] ${moteurs.length} moteurs chargés:`, Object.keys(IA_MODELS_CACHE));
        }
        
        // Peupler le sélecteur principal (toolbar)
        populateIASelector(elements.detectionModeSelector, true);
        elements.detectionModeSelector.disabled = false;
        
        // Peupler le sélecteur Union (paramètres) - sans "standard"
        if (elements.unionIASelect) {
            populateIASelector(elements.unionIASelect, false);
        }
        
        // Restaurer la valeur sauvegardée
        const savedMode = localStorage.getItem('detectionMode');
        if (savedMode && IA_MODELS_CACHE[savedMode]) {
            elements.detectionModeSelector.value = savedMode;
            detectionMode = savedMode;
        } else {
            detectionMode = 'standard';
        }
        
        const savedUnionIA = localStorage.getItem('unionIA');
        if (savedUnionIA && IA_MODELS_CACHE[savedUnionIA] && elements.unionIASelect) {
            elements.unionIASelect.value = savedUnionIA;
        }
        
        return true;
        
    } catch (error) {
        console.error('[IA] Erreur chargement moteurs:', error);
        elements.detectionModeSelector.innerHTML = '<option value="standard">⚡ Standard</option>';
        elements.detectionModeSelector.disabled = false;
        return false;
    }
}

/**
 * Peuple un sélecteur avec les moteurs IA
 * @param {HTMLSelectElement} selectElement - Sélecteur à peupler
 * @param {boolean} includeStandard - Inclure le mode "standard"
 */
function populateIASelector(selectElement, includeStandard = true) {
    if (!selectElement) return;
    
    selectElement.innerHTML = '';
    
    Object.entries(IA_MODELS_CACHE).forEach(([moteur, info]) => {
        // Filtrer "standard" si demandé
        if (!includeStandard && moteur === 'standard') return;
        
        const option = document.createElement('option');
        option.value = moteur;
        
        // Afficher avec emoji selon le type
        const isIA = moteur !== 'standard';
        const emoji = isIA ? '🤖' : '⚡';
        const displayName = info.notes || moteur;
        option.textContent = `${emoji} ${displayName}`;
        
        // Sélectionner "standard" par défaut
        if (includeStandard && moteur === 'standard') {
            option.selected = true;
        }
        
        selectElement.appendChild(option);
    });
    
    // Si pas de standard et pas de sélection, sélectionner le premier
    if (!includeStandard && selectElement.options.length > 0) {
        selectElement.options[0].selected = true;
    }
}

/**
 * Gestion du changement de moteur IA
 */
function onDetectionModeChange() {
    const newMode = elements.detectionModeSelector.value;
    detectionMode = newMode;
    localStorage.setItem('detectionMode', newMode);
    
    if (window.DEBUG) {
        console.log(`[IA] Mode changé: ${newMode}`);
    }
    
    // Mettre à jour le filigrane (si fonction disponible)
    if (typeof updateFiligraneGhost === 'function') {
        updateFiligraneGhost();
    }
}

/* ═══════════════════════════════════════════════════════════════════════
   CONSTRUCTION DES REQUÊTES
   ═══════════════════════════════════════════════════════════════════════ */

/**
 * Retourne l'endpoint de recherche à utiliser
 * @returns {string} '/search'
 */
function getSearchEndpoint() {
    return '/search';
}

/**
 * Construit le payload pour la requête /search
 * @param {string} query - Question de recherche
 * @returns {Object} Payload JSON
 */
function buildSearchPayload(query) {
    // Générer un nouveau session_id
    currentSessionId = generateSessionId();
    
    // Déterminer le mode_detection effectif
    let effectiveMode = detectionMode;
    let mode2 = null;
    
    if (compareMode) {
        effectiveMode = 'compare';
        mode2 = detectionMode2;
    } else if (unionMode) {
        effectiveMode = 'union';
        mode2 = detectionMode2;
    }
    
    const payload = {
        question: query,
        base: currentBase,
        mode_detection: effectiveMode,
        lang: selectedLanguage || 'auto',
        lang_reponse: responseLanguage || 'same',
        limit: resultsLimit || 100,
        offset: 0,
        session_id: currentSessionId
    };
    
    // Ajouter le mode secondaire si compare ou union
    if (mode2) {
        payload.mode_detection_2 = mode2;
    }
    
    return payload;
}

/* ═══════════════════════════════════════════════════════════════════════
   RECHERCHE DE PATIENTS
   ═══════════════════════════════════════════════════════════════════════ */

/**
 * Exécute une recherche de patients
 * @param {string} query - Question de recherche
 */
async function searchPatients(query) {
    if (!query || query.trim().length === 0) {
        return;
    }
    
    query = query.trim();
    
    // Reset memeState si ce n'est PAS une recherche "même"
    if (!query.toLowerCase().includes('même ') && !query.toLowerCase().includes('meme ')) {
        lastSearchQuery = query;
        if (window.DEBUG) {
            console.log('[MÊME] Sauvegarde recherche initiale:', lastSearchQuery);
        }
        
        // Reset de l'état "même" pour nouvelle recherche
        if (typeof memeState !== 'undefined' && memeState.hasReference && memeState.hasReference()) {
            if (window.DEBUG) {
                console.log('[MÊME] Reset état même (nouvelle recherche normale)');
            }
            memeState.reset();
        }
    }
    
    try {
        // Masquer le welcome et afficher la zone de recherche selon le mode
        elements.welcomeContainer.style.display = 'none';
        
        if (currentMode === 'chat') {
            elements.searchContainerTop.classList.remove('active');
            elements.searchContainerBottom.classList.add('active');
        } else {
            elements.searchContainerBottom.classList.remove('active');
            elements.searchContainerTop.classList.add('active');
        }
        
        elements.loading.classList.add('active');
        elements.resultsContainer.classList.remove('active');
        
        // Debug timing
        if (window.DEBUG) {
            const debugTs = new Date().toISOString().substr(11, 12);
            console.log(`[SearchPatients ${debugTs}] Loading activé, appel updateLoadingBanner...`);
        }
        
        // Mettre à jour le bandeau loading (si fonction disponible)
        if (typeof updateLoadingBanner === 'function') {
            updateLoadingBanner(query, detectionMode, currentBase);
        }
        
        // Forcer un repaint
        await new Promise(resolve => setTimeout(resolve, 10));
        
        // Déterminer endpoint et payload
        const endpoint = getSearchEndpoint();
        const payload = buildSearchPayload(query);
        
        addDebugLog(`Recherche: "${query}" sur ${currentBase}`, 'info');
        addDebugLog(`Endpoint: ${endpoint}`, 'info');
        addDebugLog(`Détection: ${payload.mode_detection}${payload.mode_detection_2 ? ' vs ' + payload.mode_detection_2 : ''}, Langue: ${payload.lang}`, 'info');
        
        const startTime = performance.now();
        
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        const elapsedTime = data.temps_ms || Math.round(performance.now() - startTime);
        
        addDebugLog(`Réponse reçue en ${elapsedTime}ms: ${data.nb_patients} patients`, 'success');
        
        // Vérifier le garde-fou
        if (data.gardefou === true) {
            addDebugLog(`⚠️ Garde-fou activé: ${data.gardefou_raison}`, 'warning');
            
            const gardefouResponse = {
                query: query,
                response: {
                    nb_patients: 0,
                    nb_patients_retournes: 0,
                    patients: [],
                    gardefou: true,
                    gardefou_message: data.gardefou_message || t('Aucun critère de recherche détecté'),
                    gardefou_suggestions: data.gardefou_suggestions || [],
                    temps_ms: elapsedTime
                },
                timestamp: new Date().toISOString(),
                elapsedTime: elapsedTime,
                base: currentBase,
                moteur: detectionMode
            };
            
            conversationHistory.push(gardefouResponse);
            saveConversationHistory();
            
            if (typeof renderGardefouMessage === 'function') {
                renderGardefouMessage(gardefouResponse);
            }
            return;
        }
        
        // Log langue détectée
        if (data.lang_detectee) {
            addDebugLog(`Langue détectée: ${data.lang_detectee}`, 'info');
        }
        
        // Mettre à jour l'affichage de la langue (si fonction disponible)
        if (typeof updateLangAfterResponse === 'function') {
            updateLangAfterResponse(data.lang_detectee);
        }
        
        // Mettre à jour la langue UI
        if (typeof setUILanguage === 'function') {
            if (responseLanguage === 'same' && data.lang_detectee) {
                setUILanguage(data.lang_detectee);
            } else {
                setUILanguage('fr');
            }
        }
        
        // Stocker les critères pour mise en gras
        if (data.criteres && Array.isArray(data.criteres)) {
            lastSearchCriteria = data.criteres;
            addDebugLog(`Critères stockés: ${lastSearchCriteria.length}`, 'info');
        } else {
            lastSearchCriteria = [];
        }
        
        // Debug enrichi
        if (window.DEBUG) {
            console.log('[DEBUG] Recherche:', {
                question: query,
                question_technique_fr: data.question_technique_fr || '(non disponible)',
                lang_detectee: data.lang_detectee || data.lang || 'unknown',
                endpoint: endpoint,
                mode_detection: data.mode_detection || payload.mode_detection,
                auteur: data.auteur,
                nb_patients: data.nb_patients,
                parcours: data.parcours_detection || '',
                resolution_provider: data.resolution_provider || ''
            });
        }
        
        // Ajouter à l'historique
        conversationHistory.push({
            query: query,
            response: data,
            timestamp: new Date().toISOString(),
            elapsedTime: elapsedTime,
            endpoint: endpoint,
            lang: payload.lang || 'fr',
            lang_detectee: data.lang_detectee || null,
            session_id: currentSessionId,
            base: currentBase,
            moteur: detectionMode
        });
        
        saveConversationHistory();
        
        // Afficher les résultats
        if (typeof renderResponse === 'function') {
            if (currentMode === 'classique') {
                elements.resultsContainer.innerHTML = '';
            }
            renderResponse(conversationHistory[conversationHistory.length - 1]);
        }
        
        elements.loading.classList.remove('active');
        elements.resultsContainer.classList.add('active');
        
        // Masquer le filigrane (si fonction disponible)
        if (typeof hideFiligraneForResults === 'function') {
            hideFiligraneForResults();
        }
        
        // Vider les inputs
        if (elements.searchInputCenter) elements.searchInputCenter.value = '';
        if (elements.searchInputBottom) elements.searchInputBottom.value = '';
        if (elements.searchInputTop) elements.searchInputTop.value = '';
        
        // Réinitialiser l'état des boutons (si fonction disponible)
        if (typeof updateSearchButtonState === 'function') {
            updateSearchButtonState(elements.searchInputCenter, elements.searchButtonCenter);
            updateSearchButtonState(elements.searchInputBottom, elements.searchButtonBottom);
            updateSearchButtonState(elements.searchInputTop, elements.searchButtonTop);
        }
        
        // Mettre à jour la sidebar (si fonction disponible)
        if (typeof renderRecentConversations === 'function') {
            renderRecentConversations();
        }
        
    } catch (error) {
        console.error('Erreur recherche:', error);
        addDebugLog(`ERREUR recherche: ${error.message}`, 'error');
        
        elements.loading.classList.remove('active');
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message active';
        errorDiv.textContent = `Erreur lors de la recherche: ${error.message}. Vérifiez que le serveur API est démarré.`;
        elements.resultsContainer.appendChild(errorDiv);
        elements.resultsContainer.classList.add('active');
    }
}

/* ═══════════════════════════════════════════════════════════════════════
   CHARGEMENT VERSION SERVEUR
   ═══════════════════════════════════════════════════════════════════════ */

/**
 * Charge et affiche la version du serveur
 */
async function loadServerVersion() {
    try {
        const response = await fetch(`${API_BASE_URL}/version`);
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }
        
        const data = await response.json();
        const clientVersion = 'F1.1.0';
        const serverVersion = `S${data.version}`;
        
        if (elements.versionDisplay) {
            elements.versionDisplay.textContent = `${clientVersion}/${serverVersion}`;
        }
        
        addDebugLog(`Versions: Client ${clientVersion}, Serveur ${serverVersion}`, 'success');
        
    } catch (error) {
        console.error('Erreur chargement version serveur:', error);
        if (elements.versionDisplay) {
            elements.versionDisplay.textContent = 'F1.1.0/S???';
        }
        addDebugLog(`ERREUR version serveur: ${error.message}`, 'error');
    }
}

/* ═══════════════════════════════════════════════════════════════════════
   EXPORTS (variables et fonctions globales)
   ═══════════════════════════════════════════════════════════════════════ */

// Les variables sont déjà globales (pas de module ES6)
// Les fonctions sont accessibles globalement
