/**
 * utils.js V1.0.0 - 24/01/2026
 * Utilitaires globaux pour Kitview Search
 * 
 * Contenu :
 * - debounce : Anti-rebond pour les événements fréquents
 * - Autres utilitaires à ajouter
 */

/**
 * Crée une fonction debounce qui retarde l'exécution
 * @param {Function} func - Fonction à exécuter
 * @param {number} wait - Délai en ms (défaut: 300)
 * @returns {Function} Fonction debounced
 */
function debounce(func, wait = 300) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Variable globale DEBUG - contrôle les logs conditionnels
 * Peut être activée/désactivée via webparams ou localStorage
 */
window.DEBUG = localStorage.getItem('debug') === 'true' || true;  // Activé par défaut pour l'instant

/**
 * Ajoute un log dans la console debug (si disponible)
 * @param {string} message - Message à logger
 * @param {string} type - Type de log (info, success, warning, error)
 */
function addDebugLog(message, type = 'info') {
    if (!window.DEBUG) return;
    
    const timestamp = new Date().toLocaleTimeString('fr-FR');
    const prefix = {
        'info': 'ℹ️',
        'success': '✅',
        'warning': '⚠️',
        'error': '❌'
    }[type] || 'ℹ️';
    
    console.log(`[${timestamp}] ${prefix} ${message}`);
    
    // Si une console debug HTML existe, y ajouter aussi
    const debugConsole = document.getElementById('debugConsole');
    if (debugConsole) {
        const line = document.createElement('div');
        line.className = `debug-line debug-${type}`;
        line.textContent = `[${timestamp}] ${message}`;
        debugConsole.appendChild(line);
        debugConsole.scrollTop = debugConsole.scrollHeight;
    }
}
