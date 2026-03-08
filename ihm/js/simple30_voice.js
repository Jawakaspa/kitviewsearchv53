/**
 * voice.js V1.0.0 - 24/01/2026
 * Module de reconnaissance vocale pour Kitview Search
 * 
 * Fonctionnalités :
 * - Reconnaissance vocale avec Web Speech API
 * - Mode normal (clic court) avec timeout silence
 * - Mode mains libres (clic long) avec mot-clé "Kitview"
 * - Support multilingue (fr, en, de, es, it, pt, pl, ro, th, ar, cn, ja)
 * - Raccourci clavier Ctrl+Shift+M
 * 
 * Usage :
 *   voiceSearchManager.initButtons([
 *     { inputId: 'searchInputCenter', buttonId: 'voiceButtonCenter' },
 *     { inputId: 'searchInputBottom', buttonId: 'voiceButtonBottom' }
 *   ]);
 * 
 * Dépendances externes :
 * - Variable globale `selectedLanguage` (optionnelle, défaut: 'fr')
 */

const voiceSearchManager = (function() {
    
    // Vérification de la compatibilité
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const isSupported = !!SpeechRecognition;
    
    // Configuration
    const KEYWORD = 'kitview';  // Mot-clé déclencheur
    const SILENCE_TIMEOUT = 5000;  // 5 secondes de silence avant lancement auto (mode normal)
    
    // État interne
    let recognition = null;
    let isListening = false;
    let isHandsfreeMode = false;
    let currentInputId = null;
    let currentButtonId = null;
    let silenceTimer = null;
    let handsfreeTimer = null;
    let handsfreeStartTime = null;
    let progressInterval = null;
    let hasReceivedSpeech = false;
    let buttonConfigs = [];
    let accumulatedTranscript = '';  // Pour accumuler le texte en mode mains libres
    
    // Mapping langue sélectionnée → code BCP-47 pour SpeechRecognition
    const LANG_CODES = {
        'fr': 'fr-FR',
        'en': 'en-US',
        'de': 'de-DE',
        'es': 'es-ES',
        'it': 'it-IT',
        'pt': 'pt-PT',
        'pl': 'pl-PL',
        'ro': 'ro-RO',
        'th': 'th-TH',
        'ar': 'ar-SA',
        'cn': 'zh-CN',
        'ja': 'ja-JP',
        'auto': 'fr-FR'
    };
    
    /**
     * Récupère la durée du mode mains libres depuis localStorage (en minutes)
     */
    function getHandsfreeDuration() {
        const minutes = parseInt(localStorage.getItem('handsfreeDuration') || '5');
        return Math.max(1, Math.min(10, minutes)) * 60 * 1000;  // Convertir en ms
    }
    
    /**
     * Crée le SVG du cercle progressif
     */
    function createProgressRing() {
        const size = 40;
        const strokeWidth = 3;
        const radius = (size - strokeWidth) / 2;
        const circumference = 2 * Math.PI * radius;
        
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('class', 'progress-ring');
        svg.setAttribute('viewBox', `0 0 ${size} ${size}`);
        
        // Cercle de fond
        const bgCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        bgCircle.setAttribute('class', 'bg');
        bgCircle.setAttribute('cx', size / 2);
        bgCircle.setAttribute('cy', size / 2);
        bgCircle.setAttribute('r', radius);
        svg.appendChild(bgCircle);
        
        // Cercle de progression
        const progressCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        progressCircle.setAttribute('class', 'progress');
        progressCircle.setAttribute('cx', size / 2);
        progressCircle.setAttribute('cy', size / 2);
        progressCircle.setAttribute('r', radius);
        progressCircle.setAttribute('stroke-dasharray', circumference);
        progressCircle.setAttribute('stroke-dashoffset', circumference);
        svg.appendChild(progressCircle);
        
        return { svg, circumference, progressCircle };
    }
    
    /**
     * Met à jour la progression du cercle
     */
    function updateProgress(button, progress) {
        const progressCircle = button.querySelector('.progress-ring .progress');
        if (progressCircle) {
            const circumference = parseFloat(progressCircle.getAttribute('stroke-dasharray'));
            const offset = circumference * (1 - progress);
            progressCircle.setAttribute('stroke-dashoffset', offset);
        }
    }
    
    /**
     * Réinitialise le timer de silence (mode normal)
     */
    function resetSilenceTimer() {
        if (silenceTimer) clearTimeout(silenceTimer);
        
        if (!isHandsfreeMode) {
            silenceTimer = setTimeout(() => {
                if (isListening && hasReceivedSpeech && !isHandsfreeMode) {
                    if (window.DEBUG) console.log('[VoiceSearch] Timeout silence - Lancement recherche');
                    launchSearchAndStop();
                }
            }, SILENCE_TIMEOUT);
        }
    }
    
    /**
     * Démarre le timer et la progression du mode mains libres
     */
    function startHandsfreeTimer(button) {
        const duration = getHandsfreeDuration();
        handsfreeStartTime = Date.now();
        
        // Timer de fin
        handsfreeTimer = setTimeout(() => {
            if (window.DEBUG) console.log('[VoiceSearch] Fin du mode mains libres (timeout)');
            stopListening();
        }, duration);
        
        // Mise à jour de la progression toutes les 100ms
        progressInterval = setInterval(() => {
            const elapsed = Date.now() - handsfreeStartTime;
            const progress = Math.min(elapsed / duration, 1);
            updateProgress(button, progress);
            
            if (progress >= 1) {
                clearInterval(progressInterval);
            }
        }, 100);
    }
    
    /**
     * Lance la recherche et arrête l'écoute
     */
    function launchSearchAndStop() {
        const inputId = currentInputId;
        const query = accumulatedTranscript.trim();
        
        stopListening();
        
        if (query && inputId) {
            setTimeout(() => {
                const input = document.getElementById(inputId);
                if (input) {
                    input.value = query;
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                }
                
                const buttonId = inputId.replace('Input', 'Button');
                const button = document.getElementById(buttonId);
                if (button && !button.disabled) {
                    button.click();
                }
            }, 300);
        }
    }
    
    /**
     * Traite le transcript pour détecter le mot-clé "kitview"
     */
    function processTranscript(transcript) {
        const lower = transcript.toLowerCase();
        
        // Chercher le mot-clé "kitview" (ou variantes phonétiques)
        const keywordVariants = ['kitview', 'kit view', 'kitvue', 'kit vue', 'quitte view', 'quitte vue'];
        
        for (const variant of keywordVariants) {
            const index = lower.indexOf(variant);
            if (index !== -1) {
                // Extraire la requête après le mot-clé
                const afterKeyword = transcript.substring(index + variant.length).trim();
                if (afterKeyword.length > 0) {
                    if (window.DEBUG) console.log('[VoiceSearch] Mot-clé détecté, requête:', afterKeyword);
                    return { found: true, query: afterKeyword };
                }
            }
        }
        
        return { found: false, query: transcript };
    }
    
    /**
     * Initialise le moteur de reconnaissance vocale
     */
    function initRecognition() {
        if (!isSupported || recognition) return;
        
        recognition = new SpeechRecognition();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.maxAlternatives = 1;
        
        recognition.onresult = (event) => {
            let finalTranscript = '';
            let interimTranscript = '';
            
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const result = event.results[i];
                if (result.isFinal) {
                    finalTranscript += result[0].transcript;
                } else {
                    interimTranscript += result[0].transcript;
                }
            }
            
            hasReceivedSpeech = true;
            
            // Afficher le transcript en cours dans l'input
            const input = document.getElementById(currentInputId);
            if (input) {
                if (isHandsfreeMode) {
                    // En mode mains libres, afficher tout ce qui est dit
                    input.value = accumulatedTranscript + interimTranscript;
                } else {
                    input.value = interimTranscript || finalTranscript;
                }
                input.dispatchEvent(new Event('input', { bubbles: true }));
            }
            
            if (finalTranscript) {
                if (isHandsfreeMode) {
                    // Mode mains libres : chercher le mot-clé
                    const { found, query } = processTranscript(finalTranscript);
                    if (found && query) {
                        accumulatedTranscript = query;
                        launchSearchAndStop();
                    } else {
                        // Accumuler mais ne pas lancer
                        accumulatedTranscript += ' ' + finalTranscript;
                    }
                } else {
                    // Mode normal : réinitialiser le timer de silence
                    accumulatedTranscript = finalTranscript;
                    resetSilenceTimer();
                }
            }
        };
        
        recognition.onend = () => {
            if (window.DEBUG) console.log('[VoiceSearch] Écoute terminée par l\'API');
            
            if (isHandsfreeMode && isListening) {
                // En mode mains libres, redémarrer automatiquement
                try {
                    recognition.start();
                    if (window.DEBUG) console.log('[VoiceSearch] Redémarrage auto (mode mains libres)');
                } catch (e) {
                    console.error('[VoiceSearch] Erreur redémarrage:', e);
                    stopListening();
                }
            } else if (isListening && hasReceivedSpeech && !isHandsfreeMode) {
                launchSearchAndStop();
            } else {
                stopListening();
            }
        };
        
        recognition.onerror = (event) => {
            console.error('[VoiceSearch] Erreur:', event.error);
            
            if (event.error === 'no-speech') {
                if (isHandsfreeMode) {
                    // En mode mains libres, ignorer l'erreur no-speech
                    return;
                }
                if (window.DEBUG) console.log('[VoiceSearch] Aucune parole détectée');
            } else if (event.error === 'not-allowed') {
                alert('L\'accès au microphone a été refusé. Veuillez autoriser l\'accès dans les paramètres de votre navigateur.');
                stopListening();
            } else if (event.error === 'network') {
                alert('Erreur réseau. La reconnaissance vocale nécessite une connexion Internet.');
                stopListening();
            }
        };
        
        if (window.DEBUG) console.log('[VoiceSearch] Moteur initialisé');
    }
    
    /**
     * Démarre l'écoute
     * @param {string} inputId - ID de l'input
     * @param {string} buttonId - ID du bouton
     * @param {boolean} handsfree - Mode mains libres
     */
    function startListening(inputId, buttonId, handsfree = false) {
        if (!isSupported) return;
        
        if (isListening) {
            stopListening();
            if (currentButtonId === buttonId && !handsfree) {
                return;  // Toggle off
            }
        }
        
        initRecognition();
        
        currentInputId = inputId;
        currentButtonId = buttonId;
        isHandsfreeMode = handsfree;
        hasReceivedSpeech = false;
        accumulatedTranscript = '';
        
        const lang = typeof selectedLanguage !== 'undefined' ? selectedLanguage : 'fr';
        recognition.lang = LANG_CODES[lang] || LANG_CODES['fr'];
        if (window.DEBUG) console.log('[VoiceSearch] Langue:', recognition.lang, '| Mode:', handsfree ? 'mains libres' : 'normal');
        
        try {
            recognition.start();
            isListening = true;
            
            const button = document.getElementById(buttonId);
            if (button) {
                if (handsfree) {
                    button.classList.add('handsfree');
                    button.classList.remove('listening');
                    
                    // Ajouter le cercle progressif s'il n'existe pas
                    if (!button.querySelector('.progress-ring')) {
                        const { svg } = createProgressRing();
                        button.appendChild(svg);
                    }
                    
                    // Démarrer le timer
                    startHandsfreeTimer(button);
                    
                    const minutes = parseInt(localStorage.getItem('handsfreeDuration') || '5');
                    button.title = `Mode mains libres (${minutes}min) - Dites "Kitview" suivi de votre recherche`;
                } else {
                    button.classList.add('listening');
                    button.classList.remove('handsfree');
                    button.title = 'Cliquez pour arrêter (ou Ctrl+Shift+M)';
                }
            }
            
            if (window.DEBUG) console.log('[VoiceSearch] Écoute démarrée');
        } catch (error) {
            console.error('[VoiceSearch] Erreur démarrage:', error);
            stopListening();
        }
    }
    
    /**
     * Arrête l'écoute
     */
    function stopListening() {
        if (silenceTimer) clearTimeout(silenceTimer);
        if (handsfreeTimer) clearTimeout(handsfreeTimer);
        if (progressInterval) clearInterval(progressInterval);
        
        silenceTimer = null;
        handsfreeTimer = null;
        progressInterval = null;
        handsfreeStartTime = null;
        
        if (recognition && isListening) {
            try {
                recognition.stop();
            } catch (e) {}
        }
        
        isListening = false;
        const wasHandsfree = isHandsfreeMode;
        isHandsfreeMode = false;
        hasReceivedSpeech = false;
        
        if (currentButtonId) {
            const button = document.getElementById(currentButtonId);
            if (button) {
                button.classList.remove('listening', 'handsfree');
                button.title = 'Recherche vocale (Ctrl+Shift+M) | Clic long = mode mains libres';
                
                // Réinitialiser le cercle
                updateProgress(button, 0);
            }
        }
        
        currentInputId = null;
        currentButtonId = null;
        accumulatedTranscript = '';
    }
    
    /**
     * Toggle écoute (clic court = normal, clic long = mains libres)
     */
    function toggleListening(inputId, buttonId) {
        if (isListening && currentButtonId === buttonId) {
            stopListening();
        } else {
            startListening(inputId, buttonId, false);
        }
    }
    
    /**
     * Détermine l'input actif pour le raccourci clavier
     */
    function getActiveConfig() {
        const welcomeContainer = document.getElementById('welcomeContainer');
        if (welcomeContainer && welcomeContainer.style.display !== 'none') {
            return buttonConfigs.find(c => c.inputId === 'searchInputCenter');
        }
        
        const searchBottom = document.getElementById('searchContainerBottom');
        if (searchBottom && searchBottom.classList.contains('active')) {
            return buttonConfigs.find(c => c.inputId === 'searchInputBottom');
        }
        
        const searchTop = document.getElementById('searchContainerTop');
        if (searchTop && searchTop.classList.contains('active')) {
            return buttonConfigs.find(c => c.inputId === 'searchInputTop');
        }
        
        return buttonConfigs[0];
    }
    
    /**
     * Initialise les boutons micro
     */
    function initButtons(configs) {
        buttonConfigs = configs;
        
        if (!isSupported) {
            configs.forEach(config => {
                const button = document.getElementById(config.buttonId);
                if (button) {
                    button.classList.add('unsupported');
                }
            });
            if (window.DEBUG) console.log('[VoiceSearch] API non supportée - boutons masqués');
            return;
        }
        
        configs.forEach(config => {
            const button = document.getElementById(config.buttonId);
            if (button) {
                let pressTimer = null;
                let longPressTriggered = false;
                
                // Gestion du clic long pour mode mains libres
                button.addEventListener('mousedown', (e) => {
                    e.preventDefault();
                    longPressTriggered = false;
                    pressTimer = setTimeout(() => {
                        longPressTriggered = true;
                        startListening(config.inputId, config.buttonId, true);  // Mode mains libres
                    }, 500);  // 500ms pour déclencher le mode mains libres
                });
                
                button.addEventListener('mouseup', (e) => {
                    e.preventDefault();
                    clearTimeout(pressTimer);
                    if (!longPressTriggered) {
                        toggleListening(config.inputId, config.buttonId);
                    }
                });
                
                button.addEventListener('mouseleave', () => {
                    clearTimeout(pressTimer);
                });
                
                // Support tactile
                button.addEventListener('touchstart', (e) => {
                    e.preventDefault();
                    longPressTriggered = false;
                    pressTimer = setTimeout(() => {
                        longPressTriggered = true;
                        startListening(config.inputId, config.buttonId, true);
                    }, 500);
                });
                
                button.addEventListener('touchend', (e) => {
                    e.preventDefault();
                    clearTimeout(pressTimer);
                    if (!longPressTriggered) {
                        toggleListening(config.inputId, config.buttonId);
                    }
                });
                
                button.title = 'Recherche vocale (Ctrl+Shift+M) | Clic long = mode mains libres';
            }
        });
        
        // Raccourci clavier Ctrl+Shift+M
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'm') {
                e.preventDefault();
                
                if (isListening) {
                    stopListening();
                } else {
                    const config = getActiveConfig();
                    if (config) {
                        // Shift+Ctrl+M = mode normal, Alt+Shift+Ctrl+M = mode mains libres
                        startListening(config.inputId, config.buttonId, e.altKey);
                    }
                }
            }
        });
        
        if (window.DEBUG) console.log('[VoiceSearch v2.0.0] Boutons initialisés:', configs.length, '| Mot-clé:', KEYWORD);
    }
    
    return {
        isSupported,
        initButtons,
        startListening,
        stopListening,
        toggleListening,
        isListening: () => isListening,
        isHandsfreeMode: () => isHandsfreeMode,
        getActiveConfig,
        KEYWORD
    };
})();
