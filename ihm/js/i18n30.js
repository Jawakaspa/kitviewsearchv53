/**
 * i18n.js V2.0.0 - 26/01/2026
 * Kitview Search - Module d'internationalisation
 * 
 * CHANGEMENTS V2.0.0 (depuis V1.0.0) :
 *   - CLIC DIRECT : Les chips de langue changent immédiatement la langue
 *   - FERMETURE AUTO : La popup se ferme après sélection d'une langue
 *   - SUPPRESSION BOUTON OK : Plus de footer dans la popup
 *   - SUPPRESSION SECTION RÉPONSE : Switch Origine/FR retiré de la popup
 *   - CASE FR EXTERNE : Nouvelle checkbox "fr" dans le header (hors popup)
 *   - SIMPLIFICATION : Popup allégée, plus intuitive
 * 
 * Ce module gère toutes les fonctionnalités multilingues :
 * - Chargement des traductions depuis /i18n
 * - Traduction des textes UI (t) et pathologies (tPatho)
 * - Gestion des langues actives et drapeaux
 * - Messages de résultats traduits
 * - Popup de sélection de langue (simplifiée)
 * 
 * Dépendances :
 * - utils.js (addDebugLog)
 * - search.js (API_BASE_URL)
 * - Requiert que les éléments DOM soient initialisés (elements)
 * 
 * Exports (variables globales) :
 * - I18N_CACHE, I18N_LOADED, currentUILang
 * - LANGUES, LANG_TO_FLAG, MESSAGES_RESULTATS, MESSAGES_LANG_INFO
 * - selectedLanguage, responseLanguage, languesActives
 * - t(), tPatho(), loadI18n(), setUILanguage()
 * - generateLangChips(), updateLangButton(), toggleLangPopup()
 * - formatResultMessage(), formatPaginationMessage(), getNextPageText()
 * - createLangInfoMessage(), getFlagUrl(), updateLangAfterResponse()
 * - initResponseFrCheckbox(), updateResponseFrCheckbox()
 */

/* ═══════════════════════════════════════════════════════════════════════
   CACHE ET ÉTAT I18N
   ═══════════════════════════════════════════════════════════════════════ */

let I18N_CACHE = {};       // Cache des textes UI {cle_fr: {fr, en, ja, ...}}
let I18N_CACHE_LOWER = {}; // Cache avec clés en minuscules pour recherche insensible
let I18N_LOADED = false;   // Flag de chargement réussi
let currentUILang = 'fr';  // Langue courante de l'interface

// État de la sélection de langue
let selectedLanguage = localStorage.getItem('selectedLanguage') || 'auto';
let responseLanguage = localStorage.getItem('responseLanguage') || 'fr';

// Variable pour stocker la langue effective de la dernière recherche
let lastSearchLang = 'fr';

/* ═══════════════════════════════════════════════════════════════════════
   DÉFINITION DES LANGUES ET DRAPEAUX
   ═══════════════════════════════════════════════════════════════════════ */

/**
 * Langues supportées avec drapeaux SVG (v1.7.0)
 * Utilise flagcdn.com (gratuit, pas de clé API)
 */
const LANGUES = {
    'fr':   { code: 'FR',   nom: 'Français',   flag: 'fr' },
    'auto': { code: 'Auto', nom: 'Auto',       flag: null },
    'en':   { code: 'EN',   nom: 'English',    flag: 'gb' },
    'de':   { code: 'DE',   nom: 'Deutsch',    flag: 'de' },
    'es':   { code: 'ES',   nom: 'Español',    flag: 'es' },
    'it':   { code: 'IT',   nom: 'Italiano',   flag: 'it' },
    'pt':   { code: 'PT',   nom: 'Português',  flag: 'pt' },
    'pl':   { code: 'PL',   nom: 'Polski',     flag: 'pl' },
    'ro':   { code: 'RO',   nom: 'Română',     flag: 'ro' },
    'th':   { code: 'TH',   nom: 'ไทย',        flag: 'th' },
    'ar':   { code: 'AR',   nom: 'العربية',    flag: 'sa' },
    'cn':   { code: 'CN',   nom: '中文',       flag: 'cn' },
    'ja':   { code: 'JA',   nom: '日本語',     flag: 'jp' }
};

/**
 * Mapping code langue → code pays pour drapeaux
 * Inclut les langues non supportées mais avec drapeaux
 */
const LANG_TO_FLAG = {
    'fr': 'fr', 'en': 'gb', 'de': 'de', 'es': 'es', 'it': 'it',
    'pt': 'pt', 'pl': 'pl', 'ro': 'ro', 'th': 'th', 'ar': 'sa',
    'cn': 'cn', 'zh': 'cn',
    // Langues non supportées mais avec drapeaux
    'tr': 'tr', 'nl': 'nl', 'ru': 'ru', 'ja': 'jp', 'ko': 'kr',
    'sv': 'se', 'da': 'dk', 'fi': 'fi', 'no': 'no', 'cs': 'cz',
    'hu': 'hu', 'el': 'gr', 'he': 'il', 'vi': 'vn', 'id': 'id',
    'ms': 'my', 'uk': 'ua', 'sk': 'sk', 'bg': 'bg', 'hr': 'hr',
    'sl': 'si', 'et': 'ee', 'lv': 'lv', 'lt': 'lt'
};

// Langues actives (chargées depuis /params ou fallback)
let languesActives = ['fr', 'en', 'de', 'es', 'it', 'pt', 'pl', 'ro', 'th', 'ar', 'cn', 'ja'];

/* ═══════════════════════════════════════════════════════════════════════
   MESSAGES DE RÉSULTATS TRADUITS
   ═══════════════════════════════════════════════════════════════════════ */

const MESSAGES_RESULTATS = {
    'fr': { 
        patient: 'patient', patients: 'patients', 
        trouve: 'trouvé', trouves: 'trouvés', 
        avec: 'avec', aucun: 'Aucun patient trouvé',
        affiches: 'affichés', pageSuivante: 'Page suivante', tous: 'tous'
    },
    'en': { 
        patient: 'patient', patients: 'patients', 
        trouve: 'found', trouves: 'found', 
        avec: 'with', aucun: 'No patient found',
        affiches: 'displayed', pageSuivante: 'Next page', tous: 'all'
    },
    'de': { 
        patient: 'Patient', patients: 'Patienten', 
        trouve: 'gefunden', trouves: 'gefunden', 
        avec: 'mit', aucun: 'Kein Patient gefunden',
        affiches: 'angezeigt', pageSuivante: 'Nächste Seite', tous: 'alle'
    },
    'es': { 
        patient: 'paciente', patients: 'pacientes', 
        trouve: 'encontrado', trouves: 'encontrados', 
        avec: 'con', aucun: 'Ningún paciente encontrado',
        affiches: 'mostrados', pageSuivante: 'Página siguiente', tous: 'todos'
    },
    'it': { 
        patient: 'paziente', patients: 'pazienti', 
        trouve: 'trovato', trouves: 'trovati', 
        avec: 'con', aucun: 'Nessun paziente trovato',
        affiches: 'visualizzati', pageSuivante: 'Pagina seguente', tous: 'tutti'
    },
    'pt': { 
        patient: 'paciente', patients: 'pacientes', 
        trouve: 'encontrado', trouves: 'encontrados', 
        avec: 'com', aucun: 'Nenhum paciente encontrado',
        affiches: 'exibidos', pageSuivante: 'Próxima página', tous: 'todos'
    },
    'pl': { 
        patient: 'pacjent', patients: 'pacjentów', 
        trouve: 'znaleziony', trouves: 'znalezionych', 
        avec: 'z', aucun: 'Nie znaleziono pacjenta',
        affiches: 'wyświetlonych', pageSuivante: 'Następna strona', tous: 'wszystkie'
    },
    'ro': { 
        patient: 'pacient', patients: 'pacienți', 
        trouve: 'găsit', trouves: 'găsiți', 
        avec: 'cu', aucun: 'Niciun pacient găsit',
        affiches: 'afișați', pageSuivante: 'Pagina următoare', tous: 'toți'
    },
    'th': { 
        patient: 'ผู้ป่วย', patients: 'ผู้ป่วย', 
        trouve: 'พบ', trouves: 'พบ', 
        avec: 'กับ', aucun: 'ไม่พบผู้ป่วย',
        affiches: 'แสดง', pageSuivante: 'หน้าถัดไป', tous: 'ทั้งหมด'
    },
    'ar': { 
        patient: 'مريض', patients: 'مرضى', 
        trouve: 'تم العثور على', trouves: 'تم العثور على', 
        avec: 'مع', aucun: 'لم يتم العثور على مريض',
        affiches: 'معروضين', pageSuivante: 'الصفحة التالية', tous: 'الكل'
    },
    'cn': { 
        patient: '患者', patients: '患者', 
        trouve: '找到', trouves: '找到', 
        avec: '符合', aucun: '未找到患者',
        affiches: '已显示', pageSuivante: '下一页', tous: '全部'
    },
    'ja': { 
        patient: '患者', patients: '患者', 
        trouve: '見つかりました', trouves: '見つかりました', 
        avec: '条件', aucun: '患者が見つかりません',
        affiches: '表示中', pageSuivante: '次のページ', tous: 'すべて'
    }
};

/* ═══════════════════════════════════════════════════════════════════════
   MESSAGES D'INFORMATION LANGUE
   ═══════════════════════════════════════════════════════════════════════ */

const MESSAGES_LANG_INFO = {
    'fr': { detected: 'Langue détectée', answersIn: 'Réponses en français', answersInOriginal: 'Réponses dans la langue d\'origine' },
    'en': { detected: 'Language detected', answersIn: 'Answers in French', answersInOriginal: 'Answers in original language' },
    'de': { detected: 'Erkannte Sprache', answersIn: 'Antworten auf Französisch', answersInOriginal: 'Antworten in Originalsprache' },
    'es': { detected: 'Idioma detectado', answersIn: 'Respuestas en francés', answersInOriginal: 'Respuestas en idioma original' },
    'it': { detected: 'Lingua rilevata', answersIn: 'Risposte in francese', answersInOriginal: 'Risposte in lingua originale' },
    'pt': { detected: 'Idioma detectado', answersIn: 'Respostas em francês', answersInOriginal: 'Respostas no idioma original' },
    'pl': { detected: 'Wykryty język', answersIn: 'Odpowiedzi po francusku', answersInOriginal: 'Odpowiedzi w języku oryginalnym' },
    'ro': { detected: 'Limbă detectată', answersIn: 'Răspunsuri în franceză', answersInOriginal: 'Răspunsuri în limba originală' },
    'th': { detected: 'ตรวจพบภาษา', answersIn: 'คำตอบเป็นภาษาฝรั่งเศส', answersInOriginal: 'คำตอบในภาษาต้นฉบับ' },
    'ar': { detected: 'اللغة المكتشفة', answersIn: 'الإجابات باللغة الفرنسية', answersInOriginal: 'الإجابات باللغة الأصلية' },
    'cn': { detected: '检测到语言', answersIn: '以法语回复', answersInOriginal: '以原语言回复' },
    'ja': { detected: '検出された言語', answersIn: 'フランス語で回答', answersInOriginal: '元の言語で回答' }
};

/* ═══════════════════════════════════════════════════════════════════════
   CHARGEMENT DES TRADUCTIONS
   ═══════════════════════════════════════════════════════════════════════ */

/**
 * Charge les textes UI depuis /i18n
 * @returns {Promise<boolean>} true si chargement réussi
 */
async function loadI18n() {
    try {
        const response = await fetch(API_BASE_URL + '/i18n');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const data = await response.json();
        I18N_CACHE = data.ui || {};
        
        // Créer un cache avec clés normalisées (minuscules) pour recherche insensible
        I18N_CACHE_LOWER = {};
        for (const [key, value] of Object.entries(I18N_CACHE)) {
            I18N_CACHE_LOWER[key.toLowerCase().trim()] = value;
        }
        
        I18N_LOADED = true;
        console.log(`[i18n] Chargé: ${Object.keys(I18N_CACHE).length} textes UI`);
        return true;
    } catch (error) {
        console.warn('[i18n] Erreur de chargement, fallback français:', error.message);
        I18N_CACHE = {};
        I18N_CACHE_LOWER = {};
        I18N_LOADED = false;
        return false;
    }
}

/**
 * Charge les langues actives depuis /params?param=languesactives
 */
async function loadActiveLanguages() {
    try {
        const response = await fetch(`${API_BASE_URL}/params?param=languesactives`);
        if (response.ok) {
            const data = await response.json();
            if (data.languesactives && data.languesactives.length > 0) {
                languesActives = data.languesactives;
                if (typeof addDebugLog === 'function') {
                    addDebugLog(`Langues actives chargées: ${languesActives.join(', ')}`, 'success');
                }
            }
        }
    } catch (error) {
        if (typeof addDebugLog === 'function') {
            addDebugLog(`Erreur chargement langues actives: ${error.message}`, 'error');
        }
    }
}

/* ═══════════════════════════════════════════════════════════════════════
   FONCTIONS DE TRADUCTION
   ═══════════════════════════════════════════════════════════════════════ */

/**
 * Retourne le texte traduit pour une clé donnée
 * @param {string} cle - Clé française du texte
 * @param {string} lang - Langue cible (optionnel, utilise currentUILang par défaut)
 * @returns {string} Texte traduit ou clé française en fallback
 */
function t(cle, lang = null) {
    if (!cle) return cle;
    
    const targetLang = lang || currentUILang || 'fr';
    
    // Recherche exacte d'abord
    if (I18N_CACHE[cle]) {
        return I18N_CACHE[cle][targetLang] || I18N_CACHE[cle]['fr'] || cle;
    }
    
    // Recherche insensible à la casse
    const cleLower = cle.toLowerCase().trim();
    if (I18N_CACHE_LOWER[cleLower]) {
        return I18N_CACHE_LOWER[cleLower][targetLang] || I18N_CACHE_LOWER[cleLower]['fr'] || cle;
    }
    
    // Fallback: retourner la clé telle quelle
    return cle;
}

/**
 * Traduit une pathologie composée (ex: "Bruxisme Nocturne Sévère") 
 * Les pathologies sont des combinaisons tag + adjectifs.
 * Utilise un algorithme glouton pour trouver les plus longues correspondances.
 * @param {string} pathologie - Pathologie complète en français
 * @param {string} lang - Langue cible (optionnel)
 * @returns {string} Pathologie traduite
 */
function tPatho(pathologie, lang = null) {
    if (!pathologie) return pathologie;
    
    const targetLang = lang || currentUILang || 'fr';
    
    // Si langue française, pas besoin de traduire
    if (targetLang === 'fr') return pathologie;
    
    // Essayer d'abord de traduire l'expression complète
    const completeLower = pathologie.toLowerCase().trim();
    if (I18N_CACHE_LOWER[completeLower]) {
        const trad = I18N_CACHE_LOWER[completeLower][targetLang];
        if (trad) return trad;
    }
    
    // Sinon, découper en mots et chercher les plus longues correspondances
    const mots = pathologie.trim().split(/\s+/);
    const result = [];
    let i = 0;
    
    while (i < mots.length) {
        let matched = false;
        
        // Essayer des expressions de plus en plus courtes à partir de la position i
        for (let len = mots.length - i; len > 0; len--) {
            const expression = mots.slice(i, i + len).join(' ');
            const expressionLower = expression.toLowerCase();
            
            if (I18N_CACHE_LOWER[expressionLower]) {
                const trad = I18N_CACHE_LOWER[expressionLower][targetLang];
                if (trad) {
                    result.push(trad);
                    i += len;
                    matched = true;
                    break;
                }
            }
        }
        
        // Si aucune correspondance, garder le mot original
        if (!matched) {
            result.push(mots[i]);
            i++;
        }
    }
    
    return result.join(' ');
}

/* ═══════════════════════════════════════════════════════════════════════
   GESTION DE LA LANGUE UI
   ═══════════════════════════════════════════════════════════════════════ */

/**
 * Met à jour la langue de l'interface
 * @param {string} lang - Code langue (fr, en, ja, etc.)
 */
function setUILanguage(lang) {
    currentUILang = lang || 'fr';
    console.log(`[i18n] Langue UI: ${currentUILang}`);
    updateStaticUITexts();
}

/**
 * Met à jour les textes statiques de l'interface
 * Appelé après changement de langue
 */
function updateStaticUITexts() {
    // Bouton Nouvelle recherche
    const newSearchBtn = document.getElementById('newSearchBtn');
    if (newSearchBtn) {
        newSearchBtn.innerHTML = `✨ ${t('Nouvelle recherche')}`;
    }
    
    // Titres sidebar
    const sidebarTitles = document.querySelectorAll('.sidebar-title');
    sidebarTitles.forEach(el => {
        if (el.textContent.includes('Conversations') || el.textContent.includes('récentes')) {
            el.textContent = t('Conversations récentes');
        } else if (el.textContent.includes('Exemples') || el.textContent.includes('Examples')) {
            el.textContent = t('Exemples');
        }
    });
    
    // Placeholders des inputs de recherche
    const searchInputCenter = document.getElementById('searchInputCenter');
    if (searchInputCenter) {
        searchInputCenter.placeholder = t('Rechercher un patient (ex: béance, classe 2, diabète...)');
    }
    
    const searchInputTop = document.getElementById('searchInputTop');
    if (searchInputTop) {
        searchInputTop.placeholder = t('Rechercher un patient...');
    }
    
    const searchInputBottom = document.getElementById('searchInputBottom');
    if (searchInputBottom) {
        searchInputBottom.placeholder = t('Poser une autre question...');
    }
    
    // Message de bienvenue
    const welcomeMessage = document.querySelector('.welcome-message');
    if (welcomeMessage) {
        const userName = document.getElementById('welcomeUserName')?.textContent || '';
        welcomeMessage.innerHTML = `${t('Bienvenue')} <span class="user-name" id="welcomeUserName">${userName}</span> 👋`;
    }
    
    // Loading text
    const loadingTextEl = document.getElementById('loadingText');
    if (loadingTextEl) {
        loadingTextEl.textContent = t('Recherche en cours...');
    }
}

/* ═══════════════════════════════════════════════════════════════════════
   FORMATAGE DES MESSAGES
   ═══════════════════════════════════════════════════════════════════════ */

/**
 * Formate le message de résultat dans la langue appropriée
 * @param {number} count - Nombre de patients
 * @param {string} criteria - Description des critères
 * @param {number} time - Temps en ms
 * @param {string} langEffective - Langue effective (détectée ou sélectionnée)
 * @returns {string} Message formaté
 */
function formatResultMessage(count, criteria, time, langEffective) {
    // Si réponse en français forcée, utiliser français
    const lang = (responseLanguage === 'fr') ? 'fr' : (langEffective || 'fr');
    lastSearchLang = lang; // Mémoriser pour la pagination
    const msg = MESSAGES_RESULTATS[lang] || MESSAGES_RESULTATS['fr'];
    
    if (count === 0) {
        return msg.aucun;
    }
    
    const patientWord = count === 1 ? msg.patient : msg.patients;
    const foundWord = count === 1 ? msg.trouve : msg.trouves;
    
    return `${count} ${patientWord} ${foundWord} ${msg.avec} ${criteria} (${time}ms)`;
}

/**
 * Formate le message de pagination dans la langue appropriée
 * @param {number} displayed - Nombre affiché
 * @param {number} total - Nombre total
 * @param {string} criteria - Description des critères
 * @param {string} langEffective - Langue effective
 * @param {boolean} isAll - Si tous les patients sont affichés
 * @returns {string} Message formaté
 */
function formatPaginationMessage(displayed, total, criteria, langEffective, isAll = false) {
    const lang = (responseLanguage === 'fr') ? 'fr' : (langEffective || lastSearchLang || 'fr');
    const msg = MESSAGES_RESULTATS[lang] || MESSAGES_RESULTATS['fr'];
    
    if (isAll) {
        return `${displayed} ${msg.patients} ${msg.affiches} ${msg.avec} ${criteria} (${msg.tous})`;
    }
    return `${displayed} / ${total} ${msg.patients} ${msg.affiches} ${msg.avec} ${criteria}`;
}

/**
 * Retourne le texte "Page suivante" traduit
 * @param {string} langEffective - Langue effective
 * @returns {string} Texte traduit
 */
function getNextPageText(langEffective) {
    const lang = (responseLanguage === 'fr') ? 'fr' : (langEffective || lastSearchLang || 'fr');
    const msg = MESSAGES_RESULTATS[lang] || MESSAGES_RESULTATS['fr'];
    return `${msg.pageSuivante} →`;
}

/* ═══════════════════════════════════════════════════════════════════════
   GESTION DES DRAPEAUX
   ═══════════════════════════════════════════════════════════════════════ */

/**
 * Retourne l'URL du drapeau pour un code pays
 * @param {string} countryCode - Code pays (fr, gb, etc.)
 * @param {string} size - Taille (w20, w40, w80)
 * @returns {string|null} URL du drapeau
 */
function getFlagUrl(countryCode, size = 'w40') {
    if (!countryCode) return null;
    return `https://flagcdn.com/${size}/${countryCode}.png`;
}

/**
 * Crée un message d'information sur la langue de recherche
 * @param {string} langDetectee - Langue détectée par le backend
 * @param {string} langSelectionnee - Langue sélectionnée par l'utilisateur
 * @returns {HTMLElement|null} Élément HTML ou null si pas de message
 */
function createLangInfoMessage(langDetectee, langSelectionnee) {
    // Pas de message si langDetectee est null/undefined
    if (!langDetectee) {
        return null;
    }
    
    // Pas de message si la langue détectée est le français (cas normal, rien à signaler)
    if (langDetectee === 'fr') {
        return null;
    }
    
    // V1.0.6 : Pas de message si détection échouée (unknown)
    if (langDetectee === 'unknown') {
        return null;
    }
    
    const msg = MESSAGES_LANG_INFO[langDetectee] || MESSAGES_LANG_INFO['fr'];
    const langName = LANGUES[langDetectee]?.nom || langDetectee.toUpperCase();
    
    // Choisir le texte selon responseLanguage
    const answerText = (responseLanguage === 'fr') 
        ? (msg.answersIn || 'Answers in French')
        : (msg.answersInOriginal || 'Answers in original language');
    
    const infoDiv = document.createElement('div');
    infoDiv.style.cssText = `
        background: linear-gradient(135deg, rgba(59, 157, 216, 0.1), rgba(59, 157, 216, 0.05));
        border: 1px solid rgba(59, 157, 216, 0.3);
        border-radius: 8px;
        padding: 8px 12px;
        margin-bottom: 10px;
        font-size: 13px;
        color: var(--text-secondary);
        display: flex;
        align-items: center;
        gap: 8px;
    `;
    
    infoDiv.innerHTML = `
        <span style="font-size: 16px;">🌐</span>
        <span>${msg.detected}: <strong>${langName}</strong> — ${answerText}</span>
    `;
    
    return infoDiv;
}

/* ═══════════════════════════════════════════════════════════════════════
   GÉNÉRATION DES CHIPS DE LANGUE (V2.0 - Clic direct)
   ═══════════════════════════════════════════════════════════════════════ */

/**
 * Génère les chips de sélection de langue dans le popup
 * V2.0 : Clic direct = changement immédiat + fermeture popup
 */
function generateLangChips() {
    if (typeof elements === 'undefined' || !elements.chipsContainer) return;
    elements.chipsContainer.innerHTML = '';
    
    // 1. D'abord ajouter le chip Auto (rouge, gras, pleine largeur)
    const autoChip = document.createElement('div');
    autoChip.className = 'lang-chip auto-chip' + (selectedLanguage === 'auto' ? ' selected' : '');
    autoChip.dataset.lang = 'auto';
    autoChip.innerHTML = `
        <span style="font-size: 16px;">🔄</span>
        <span class="chip-name">Auto</span>
    `;
    autoChip.addEventListener('click', () => {
        selectLanguageAndClose('auto');
    });
    elements.chipsContainer.appendChild(autoChip);
    
    // 2. Ensuite les langues actives (filtrées depuis commun.csv)
    for (const langCode of languesActives) {
        const lang = LANGUES[langCode];
        if (!lang || langCode === 'auto') continue; // Skip auto (déjà ajouté) et langues inconnues
        
        const chip = document.createElement('div');
        chip.className = 'lang-chip' + (langCode === selectedLanguage ? ' selected' : '');
        chip.dataset.lang = langCode;
        
        if (lang.flag) {
            chip.innerHTML = `
                <img class="chip-flag" src="${getFlagUrl(lang.flag)}" alt="${lang.code}">
                <span class="chip-name">${lang.nom}</span>
            `;
        } else {
            chip.innerHTML = `
                <span class="chip-name">${lang.nom}</span>
            `;
        }
        
        chip.addEventListener('click', () => {
            selectLanguageAndClose(langCode);
        });
        elements.chipsContainer.appendChild(chip);
    }
}

/**
 * V2.0 : Sélectionne une langue ET ferme la popup immédiatement
 * @param {string} lang - Code langue
 */
function selectLanguageAndClose(lang) {
    // 1. Mettre à jour la sélection visuelle
    document.querySelectorAll('.lang-chip').forEach(c => {
        c.classList.toggle('selected', c.dataset.lang === lang);
    });
    
    // 2. Appliquer le changement
    setQuestionLanguage(lang);
    
    // 3. Fermer la popup après un court délai (feedback visuel)
    setTimeout(() => {
        closeLangPopup();
    }, 150);
}

/* ═══════════════════════════════════════════════════════════════════════
   MISE À JOUR DU BOUTON LANGUE
   ═══════════════════════════════════════════════════════════════════════ */

/**
 * Met à jour l'affichage du bouton de langue
 */
function updateLangButton() {
    if (typeof elements === 'undefined' || !elements.langFlag || !elements.langText) return;
    
    const lang = LANGUES[selectedLanguage] || LANGUES['fr'];
    
    // Drapeau
    if (lang.flag) {
        elements.langFlag.src = getFlagUrl(lang.flag);
        elements.langFlag.style.display = 'block';
    } else {
        elements.langFlag.style.display = 'none';
    }
    
    // Texte (sans flèche →fr, c'est géré par la checkbox externe maintenant)
    elements.langText.textContent = lang.code;
}

/**
 * Met à jour la checkbox "fr" externe selon responseLanguage
 */
function updateResponseFrCheckbox() {
    const checkbox = document.getElementById('responseFrCheckbox');
    if (checkbox) {
        checkbox.checked = (responseLanguage === 'fr');
    }
}

/**
 * Met à jour l'affichage de la langue après réponse
 * @param {string} langDetectee - Langue détectée par le backend
 */
function updateLangAfterResponse(langDetectee) {
    if (typeof elements === 'undefined' || !elements.langFlag || !elements.langText) return;
    
    const effectiveLang = langDetectee || selectedLanguage;
    const isAuto = selectedLanguage === 'auto';
    
    // Déterminer le code drapeau
    let flagCode = LANG_TO_FLAG[effectiveLang.toLowerCase()] || null;
    
    // Afficher le drapeau
    if (flagCode) {
        elements.langFlag.src = getFlagUrl(flagCode);
        elements.langFlag.style.display = 'block';
    } else {
        elements.langFlag.style.display = 'none';
    }
    
    // Déterminer le texte du combo
    let comboText;
    if (isAuto) {
        comboText = 'Auto';
    } else {
        const lang = LANGUES[selectedLanguage];
        comboText = lang ? lang.code : selectedLanguage.toUpperCase();
    }
    
    // Afficher sans flèche (la checkbox externe gère ça)
    elements.langText.textContent = comboText;
    
    if (typeof addDebugLog === 'function') {
        addDebugLog(`Langue affichée: ${comboText} (détectée: ${langDetectee || 'N/A'})`, 'info');
    }
}

/* ═══════════════════════════════════════════════════════════════════════
   CONTRÔLES POPUP LANGUE (V2.0 - Simplifiée)
   ═══════════════════════════════════════════════════════════════════════ */

/**
 * Ouvre/ferme le popup de sélection de langue
 */
function toggleLangPopup() {
    if (typeof elements === 'undefined' || !elements.langPopup) return;
    
    if (elements.langPopup.style.display === 'none') {
        elements.langPopup.style.display = 'block';
    } else {
        elements.langPopup.style.display = 'none';
    }
}

/**
 * Ferme la popup de langue
 */
function closeLangPopup() {
    if (typeof elements === 'undefined' || !elements.langPopup) return;
    elements.langPopup.style.display = 'none';
}

/**
 * Définit la langue de la question
 * @param {string} lang - Code langue
 */
function setQuestionLanguage(lang) {
    selectedLanguage = lang;
    localStorage.setItem('selectedLanguage', lang);
    updateLangButton();
    if (typeof addDebugLog === 'function') {
        addDebugLog(`Langue question: ${lang}`, 'info');
    }
}

/**
 * Définit la langue de la réponse (fr ou same)
 * @param {string} lang - 'fr' ou 'same'
 */
function setResponseLanguage(lang) {
    responseLanguage = lang;
    localStorage.setItem('responseLanguage', lang);
    updateLangButton();
    updateResponseFrCheckbox();
    if (typeof addDebugLog === 'function') {
        addDebugLog(`Langue réponse: ${lang}`, 'info');
    }
}

/* ═══════════════════════════════════════════════════════════════════════
   INITIALISATION CHECKBOX FR EXTERNE (V2.0 - Nouveau)
   ═══════════════════════════════════════════════════════════════════════ */

/**
 * Initialise la checkbox "fr" externe pour forcer la réponse en français
 * Appelée depuis main.js après chargement du DOM
 */
function initResponseFrCheckbox() {
    const checkbox = document.getElementById('responseFrCheckbox');
    if (!checkbox) {
        console.warn('[i18n] Checkbox responseFrCheckbox non trouvée');
        return;
    }
    
    // État initial depuis localStorage
    checkbox.checked = (responseLanguage === 'fr');
    
    // Événement de changement
    checkbox.addEventListener('change', () => {
        const newLang = checkbox.checked ? 'fr' : 'same';
        setResponseLanguage(newLang);
    });
    
    console.log('[i18n] Checkbox fr initialisée:', responseLanguage);
}

/* ═══════════════════════════════════════════════════════════════════════
   EXPORTS GLOBAUX
   ═══════════════════════════════════════════════════════════════════════ */

// Les variables et fonctions sont déjà globales (pas de module ES6)
// Elles seront accessibles depuis main.js et autres modules
