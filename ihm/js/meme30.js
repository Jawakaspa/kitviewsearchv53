/**
 * meme.js V1.0.0 - 24/01/2026
 * Kitview Search - Module de gestion "même que"
 * 
 * Ce module gère la fonctionnalité de recherche "même que" :
 * - État des critères sélectionnés (portrait, pathologie, tag, etc.)
 * - Génération des questions "même X que Patient"
 * - Gestion des clics sur les éléments cliquables
 * - Classes CSS pour l'affichage actif/inactif
 * 
 * Dépendances :
 * - search.js (searchPatients)
 * - Requiert que les éléments DOM soient initialisés (elements)
 * - Requiert currentMode, updateSearchButtonState
 * 
 * Exports (variables globales) :
 * - memeState (objet d'état)
 * - generateMemeQuestion(), handleMemeClick()
 * - isMemeActive(), isMemeClickable()
 * - makePortraitMemeClickable(), makeMemeClickable()
 * - lastSearchQuery
 */

/* ═══════════════════════════════════════════════════════════════════════
   ÉTAT GLOBAL "MÊME QUE"
   ═══════════════════════════════════════════════════════════════════════ */

// Sauvegarde de la dernière recherche (pour retour si plus de critères)
let lastSearchQuery = '';

/**
 * État global des critères "même" en cours
 * Gère le patient de référence et les critères actifs
 */
const memeState = {
    referenceId: null,           // ID du patient de référence
    referenceName: '',           // Nom complet pour affichage
    criteres: [],                // Critères actifs [{type: 'portrait', value: null}, ...]
    
    /**
     * Réinitialise l'état complet
     */
    reset() {
        this.referenceId = null;
        this.referenceName = '';
        this.criteres = [];
    },
    
    /**
     * Vérifie si un critère est déjà actif
     * @param {string} type - Type de critère (portrait, pathologie, tag, age, sexe)
     * @param {string|null} value - Valeur du critère (pour tag/pathologie)
     * @returns {boolean}
     */
    hasCritere(type, value = null) {
        return this.criteres.some(c => 
            c.type === type && 
            (value === null ? c.value === null : c.value === value)
        );
    },
    
    /**
     * Ajoute un critère
     * @param {string} type - Type de critère
     * @param {string|null} value - Valeur du critère
     * @returns {boolean} true si ajouté, false si déjà présent
     */
    addCritere(type, value = null) {
        if (!this.hasCritere(type, value)) {
            this.criteres.push({ type, value });
            return true;
        }
        return false;
    },
    
    /**
     * Retire un critère
     * @param {string} type - Type de critère
     * @param {string|null} value - Valeur du critère
     * @returns {boolean} true si retiré, false si non trouvé
     */
    removeCritere(type, value = null) {
        const index = this.criteres.findIndex(c => 
            c.type === type && 
            (value === null ? c.value === null : c.value === value)
        );
        if (index !== -1) {
            this.criteres.splice(index, 1);
            return true;
        }
        return false;
    },
    
    /**
     * Toggle un critère (ajoute ou retire)
     * @param {string} type - Type de critère
     * @param {string|null} value - Valeur du critère
     * @returns {boolean} true si ajouté, false si retiré
     */
    toggleCritere(type, value = null) {
        if (this.hasCritere(type, value)) {
            this.removeCritere(type, value);
            return false; // Retiré
        } else {
            this.addCritere(type, value);
            return true; // Ajouté
        }
    },
    
    /**
     * Vérifie si un patient est la référence
     * FIX 25/01/2026 : Comparaison avec conversion de type (number vs string)
     * @param {number|string} patientId - ID du patient
     * @returns {boolean}
     */
    isReference(patientId) {
        // Convertir les deux en nombre pour comparaison fiable
        return Number(this.referenceId) === Number(patientId);
    },
    
    /**
     * Vérifie s'il y a une référence active
     * @returns {boolean}
     */
    hasReference() {
        return this.referenceId !== null;
    }
};

/* ═══════════════════════════════════════════════════════════════════════
   GÉNÉRATION DE LA QUESTION
   ═══════════════════════════════════════════════════════════════════════ */

/**
 * Génère la question affichée (lisible) et technique (avec id)
 * Format display  : "Même X et même Y que Prénom Nom" (lisible)
 * Format technical: "Même X et même Y que id 10122 Prénom Nom" (pour detmeme.py)
 * Le nom est conservé à titre indicatif après l'id.
 * @returns {Object} {display: string, technical: string}
 */
function generateMemeQuestion() {
    if (!memeState.referenceId || memeState.criteres.length === 0) {
        return { display: '', technical: '' };
    }
    
    // Construire les parties de la question avec "et" entre chaque
    const parts = memeState.criteres.map(c => {
        if (c.value) {
            // Critère avec valeur (tag ou pathologie)
            return `même ${c.value}`;
        } else {
            // Critère simple (portrait, age, sexe, nom, prenom)
            return `même ${c.type}`;
        }
    });
    
    // Joindre avec " et "
    const criteresStr = parts.join(' et ');
    
    return {
        // Display : lisible pour l'utilisateur (prénom nom)
        display: `${criteresStr} que ${memeState.referenceName}`,
        // Technical : id XXX + nom indicatif (pour detmeme.py / detid.py)
        technical: `${criteresStr} que id ${memeState.referenceId} ${memeState.referenceName}`
    };
}

/**
 * Met à jour l'affichage des cards après une action même
 * (Placeholder pour rafraîchissement visuel si nécessaire)
 */
function refreshMemeDisplay() {
    console.log('[MÊME] Refresh display - Référence:', memeState.referenceId, 'Critères:', memeState.criteres.length);
}

/* ═══════════════════════════════════════════════════════════════════════
   GESTION DES CLICS
   ═══════════════════════════════════════════════════════════════════════ */

/**
 * Gère un clic sur un élément "même"
 * V2.1 : Tous les critères cliquables sur tous les patients
 *        Clic sur autre patient = changement de référence avec ce critère
 *        Clic pathologie = désélectionne le tag correspondant
 * 
 * @param {number|string} patientId - ID du patient cliqué
 * @param {string} patientName - Nom complet du patient
 * @param {string} critereType - Type de critère (portrait, pathologie, tag, etc.)
 * @param {string|null} critereValue - Valeur du critère (pour tag/pathologie)
 */
function handleMemeClick(patientId, patientName, critereType, critereValue = null) {
    console.log('[MÊME] Clic:', patientId, patientName, critereType, critereValue);
    
    // CAS 1 : Changement de patient de référence
    // N'importe quel critère peut changer de référence (pas seulement portrait)
    if (memeState.hasReference() && !memeState.isReference(patientId)) {
        console.log('[MÊME] Changement de référence vers:', patientName);
        memeState.reset();
        memeState.referenceId = patientId;
        memeState.referenceName = patientName;
        memeState.addCritere(critereType, critereValue);
    }
    // CAS 2 : Premier clic ou même patient
    else {
        // Initialiser la référence si nécessaire
        if (!memeState.hasReference()) {
            memeState.referenceId = patientId;
            memeState.referenceName = patientName;
        }
        
        // FIX 25/01/2026 : Ne plus désélectionner automatiquement le tag
        // quand on clique sur une pathologie. Permet de garder les critères
        // séparés et de les retirer un par un (même si ça fait "bégaiement")
        // ANCIEN CODE SUPPRIMÉ :
        // if (critereType === 'pathologie' && critereValue) {
        //     const tag = critereValue.split(/\s+/)[0];
        //     if (memeState.hasCritere('tag', tag)) {
        //         memeState.removeCritere('tag', tag);
        //     }
        // }
        
        // Toggle le critère
        const wasAdded = memeState.toggleCritere(critereType, critereValue);
        console.log('[MÊME] Critère', wasAdded ? 'ajouté' : 'retiré');
    }
    
    // Si plus aucun critère, retour à la recherche initiale
    if (memeState.criteres.length === 0) {
        console.log('[MÊME] Plus de critères - retour recherche initiale');
        memeState.reset();
        
        // Utiliser les variables globales de main.js
        const activeInput = (typeof currentMode !== 'undefined' && currentMode === 'chat')
            ? (typeof elements !== 'undefined' ? elements.searchInputBottom : null)
            : (typeof elements !== 'undefined' ? elements.searchInputTop : null);
        
        if (activeInput && lastSearchQuery) {
            activeInput.value = lastSearchQuery;
            if (typeof searchPatients === 'function') {
                searchPatients(lastSearchQuery);
            }
        }
        return;
    }
    
    // Générer et exécuter la nouvelle recherche
    const questions = generateMemeQuestion();
    console.log('[MÊME] Question:', questions.display);
    
    const activeInput = (typeof currentMode !== 'undefined' && currentMode === 'chat')
        ? (typeof elements !== 'undefined' ? elements.searchInputBottom : null)
        : (typeof elements !== 'undefined' ? elements.searchInputTop : null);
    
    if (activeInput) {
        activeInput.value = questions.display;
        
        const activeButton = (typeof currentMode !== 'undefined' && currentMode === 'chat')
            ? (typeof elements !== 'undefined' ? elements.searchButtonBottom : null)
            : (typeof elements !== 'undefined' ? elements.searchButtonTop : null);
        
        if (typeof updateSearchButtonState === 'function' && activeButton) {
            updateSearchButtonState(activeInput, activeButton);
        }
    }
    
    // Lancer la recherche
    if (typeof searchPatients === 'function') {
        searchPatients(questions.technical);
    }
}

/* ═══════════════════════════════════════════════════════════════════════
   VÉRIFICATION D'ÉTAT
   ═══════════════════════════════════════════════════════════════════════ */

/**
 * Vérifie si un critère est actuellement actif (pour affichage rouge)
 * @param {number|string} patientId - ID du patient
 * @param {string} critereType - Type de critère
 * @param {string|null} critereValue - Valeur du critère
 * @returns {boolean}
 */
function isMemeActive(patientId, critereType, critereValue = null) {
    if (!memeState.isReference(patientId)) return false;
    return memeState.hasCritere(critereType, critereValue);
}

/**
 * Vérifie si un élément doit être cliquable
 * V2.1 : Tout est cliquable sur tous les patients
 * @param {number|string} patientId - ID du patient
 * @param {string} critereType - Type de critère
 * @returns {boolean}
 */
function isMemeClickable(patientId, critereType) {
    // Si pas de référence, tout est cliquable
    if (!memeState.hasReference()) return true;
    
    // Si c'est le patient de référence, tout est cliquable
    if (memeState.isReference(patientId)) return true;
    
    // V2.1 : Tout est cliquable sur tous les patients
    // Clic sur autre patient = changement de référence avec ce critère
    return true;
}

/* ═══════════════════════════════════════════════════════════════════════
   CONFIGURATION DES ÉLÉMENTS CLIQUABLES
   ═══════════════════════════════════════════════════════════════════════ */

/**
 * Configure le portrait comme cliquable
 * @param {HTMLElement} container - Conteneur du portrait
 * @param {number|string} patientId - ID du patient
 * @param {string} patientName - Nom complet du patient
 */
function makePortraitMemeClickable(container, patientId, patientName) {
    const isReference = memeState.isReference(patientId);
    const isActive = isMemeActive(patientId, 'portrait');
    
    // Le portrait est toujours cliquable
    container.classList.add('meme-portrait-clickable');
    
    if (isReference) {
        container.classList.add('meme-portrait-reference');
        if (isActive) {
            container.classList.add('meme-portrait-active');
        }
    }
    
    container.title = isActive 
        ? 'Retirer ce critère' 
        : 'Rechercher même portrait';
    
    container.onclick = (e) => {
        e.stopPropagation();
        handleMemeClick(patientId, patientName, 'portrait');
    };
}

/**
 * Crée un élément cliquable "même" avec gestion du toggle
 * @param {HTMLElement} element - Élément DOM à rendre cliquable
 * @param {number|string} patientId - ID du patient
 * @param {string} patientName - Nom complet du patient
 * @param {string} critereType - Type de critère
 * @param {string|null} critereValue - Valeur du critère
 * @param {string} tooltip - Texte du tooltip
 */
function makeMemeClickable(element, patientId, patientName, critereType, critereValue = null, tooltip = '') {
    const isClickable = isMemeClickable(patientId, critereType);
    const isActive = isMemeActive(patientId, critereType, critereValue);
    
    element.classList.add('meme-clickable');
    
    if (isActive) {
        element.classList.add('meme-active');
    }
    
    if (isClickable) {
        element.title = isActive ? 'Retirer ce critère' : tooltip;
        element.onclick = (e) => {
            e.stopPropagation();
            handleMemeClick(patientId, patientName, critereType, critereValue);
        };
    } else {
        element.classList.add('meme-disabled');
        element.title = '';
    }
}

/* ═══════════════════════════════════════════════════════════════════════
   EXPORTS GLOBAUX
   ═══════════════════════════════════════════════════════════════════════ */

// Les variables et fonctions sont déjà globales (pas de module ES6)
// Elles seront accessibles depuis main.js et autres modules
