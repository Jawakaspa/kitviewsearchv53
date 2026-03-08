// kvm.js - Scripts du manuel Kitview
// V2.1.0 - 26/01/2026 - Amélioration recherche
// - Correction highlight courant (classe .current au lieu de classe séparée)
// - Masquage automatique des sections TOC sans résultats
// - Utilisation de la classe .visible pour l'affichage de la navigation

/*
 * JavaScript avec sélecteur de langue custom + Google Translate
 * Correction: Initialise la langue à partir de <html lang="...">
 */

// ═══════════════════════════════════════════════════════════════
// GOOGLE TRANSLATE WIDGET
// ═══════════════════════════════════════════════════════════════

function googleTranslateElementInit() {
    new google.translate.TranslateElement({
        pageLanguage: 'fr',
        includedLanguages: 'en,de,es,it,pt,pl,ro,th,ar,zh-CN',
        layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
        autoDisplay: false
    }, 'google_translate_element');
    
    console.log('[Lang] Google Translate initialisé');
}

// ═══════════════════════════════════════════════════════════════
// SÉLECTEUR DE LANGUE CUSTOM
// ═══════════════════════════════════════════════════════════════

let currentLang = 'fr';
let selectedLang = 'fr';
let selectedDisplayCode = 'FR';
let selectedFlagCode = 'fr';

// Mapping des codes langue vers drapeaux
const LANG_MAP = {
    'fr': { display: 'FR', flag: 'fr' },
    'en': { display: 'EN', flag: 'gb' },
    'de': { display: 'DE', flag: 'de' },
    'es': { display: 'ES', flag: 'es' },
    'it': { display: 'IT', flag: 'it' },
    'pt': { display: 'PT', flag: 'pt' },
    'pl': { display: 'PL', flag: 'pl' },
    'ro': { display: 'RO', flag: 'ro' },
    'th': { display: 'TH', flag: 'th' },
    'ar': { display: 'AR', flag: 'sa' },
    'zh-CN': { display: 'CN', flag: 'cn' }
};

function toggleLangPopup() {
    const popup = document.getElementById('langPopup');
    const isHidden = popup.style.display === 'none' || popup.style.display === '';
    popup.style.display = isHidden ? 'block' : 'none';
}

function closeLangPopup() {
    document.getElementById('langPopup').style.display = 'none';
}

function selectLanguage(langCode, displayCode, flagCode) {
    selectedLang = langCode;
    selectedDisplayCode = displayCode;
    selectedFlagCode = flagCode;
    
    document.querySelectorAll('.lang-chip').forEach(chip => {
        chip.classList.remove('selected');
        if (chip.dataset.lang === langCode) {
            chip.classList.add('selected');
        }
    });
    
    // Appliquer immédiatement
    applyLanguage();
}

function applyLanguage() {
    closeLangPopup();
    
    if (selectedLang === currentLang) {
        return;
    }
    
    // Détecter la version actuelle (standard, débutant, etc.)
    const currentFile = window.location.pathname.split('/').pop() || 'kvms.html';
    const isDebutant = currentFile.includes('kvmd');
    const isIntermediaire = currentFile.includes('kvmi');
    const isExpert = currentFile.includes('kvme');
    
    // Construire le nom du fichier cible selon la langue
    let targetFile = '';
    
    if (selectedLang === 'fr') {
        // Retour au français
        if (isDebutant) targetFile = 'kvmd.html';
        else if (isIntermediaire) targetFile = 'kvmi.html';
        else if (isExpert) targetFile = 'kvme.html';
        else targetFile = 'kvms.html';
    } else if (selectedLang === 'en') {
        // Anglais - fichiers pré-traduits disponibles
        // Note: pour l'instant seule la version standard a une traduction EN
        targetFile = 'kvm_en.html';
    } else {
        // Autres langues - utiliser Google Translate sur la version FR
        updateLangButton(selectedDisplayCode, selectedFlagCode);
        triggerGoogleTranslate(selectedLang);
        currentLang = selectedLang;
        return;
    }
    
    // Rediriger vers le fichier cible
    window.location.href = targetFile;
}

function updateLangButton(displayCode, flagCode) {
    const flagImg = document.getElementById('currentFlag');
    const langCode = document.getElementById('currentLangCode');
    
    if (flagImg) {
        flagImg.src = `https://flagcdn.com/w40/${flagCode}.png`;
        flagImg.alt = displayCode;
    }
    if (langCode) {
        langCode.textContent = displayCode;
    }
}

function triggerGoogleTranslate(langCode) {
    const select = document.querySelector('.goog-te-combo');
    if (select) {
        select.value = langCode;
        select.dispatchEvent(new Event('change', { bubbles: true }));
        return;
    }
    
    document.cookie = `googtrans=/fr/${langCode}; path=/`;
    setTimeout(() => {
        window.location.reload();
    }, 100);
}

function resetGoogleTranslate() {
    const select = document.querySelector('.goog-te-combo');
    if (select) {
        select.value = 'fr';
        select.dispatchEvent(new Event('change', { bubbles: true }));
        document.cookie = 'googtrans=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
        return;
    }
    
    document.cookie = 'googtrans=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
    window.location.reload();
}

document.addEventListener('click', (e) => {
    const container = document.querySelector('.lang-button-container');
    const popup = document.getElementById('langPopup');
    if (container && popup && popup.style.display === 'block') {
        if (!container.contains(e.target)) {
            closeLangPopup();
        }
    }
});

/**
 * Détecte la langue actuelle à partir de:
 * 1. L'attribut lang du document HTML
 * 2. Le cookie Google Translate
 * 3. Défaut: français
 */
function detectCurrentLanguage() {
    // 1. D'abord vérifier l'attribut lang du HTML
    const htmlLang = document.documentElement.lang || 'fr';
    
    // Normaliser (en-US -> en, etc.)
    let detectedLang = htmlLang.split('-')[0].toLowerCase();
    if (htmlLang === 'zh-CN') detectedLang = 'zh-CN'; // Exception pour chinois
    
    // 2. Vérifier si Google Translate a été utilisé
    const match = document.cookie.match(/googtrans=\/fr\/([^;]+)/);
    if (match && match[1]) {
        detectedLang = match[1];
    }
    
    // 3. Appliquer la langue détectée
    const langInfo = LANG_MAP[detectedLang] || LANG_MAP['fr'];
    
    currentLang = detectedLang;
    selectedLang = detectedLang;
    selectedDisplayCode = langInfo.display;
    selectedFlagCode = langInfo.flag;
    
    // Mettre à jour le bouton
    updateLangButton(langInfo.display, langInfo.flag);
    
    // Mettre à jour le chip sélectionné
    document.querySelectorAll('.lang-chip').forEach(chip => {
        chip.classList.remove('selected');
        if (chip.dataset.lang === detectedLang) {
            chip.classList.add('selected');
        }
    });
    
    console.log('[Lang] Langue détectée:', detectedLang);
}

// ═══════════════════════════════════════════════════════════════
// GESTION DU THÈME
// ═══════════════════════════════════════════════════════════════

const elements = {
    themeToggle: null
};

function initTheme() {
    elements.themeToggle = document.getElementById('themeToggle');
    if (!elements.themeToggle) return;
    
    const savedTheme = localStorage.getItem('kitview-theme');
    if (savedTheme === 'dark') {
        document.body.setAttribute('data-theme', 'dark');
        elements.themeToggle.textContent = '☀️';
    } else if (savedTheme === 'light') {
        document.body.removeAttribute('data-theme');
        elements.themeToggle.textContent = '🌙';
    } else {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            document.body.setAttribute('data-theme', 'dark');
            elements.themeToggle.textContent = '☀️';
        }
    }
}

function toggleTheme() {
    const isDark = document.body.hasAttribute('data-theme');
    if (isDark) {
        document.body.removeAttribute('data-theme');
        localStorage.setItem('kitview-theme', 'light');
        if (elements.themeToggle) elements.themeToggle.textContent = '🌙';
    } else {
        document.body.setAttribute('data-theme', 'dark');
        localStorage.setItem('kitview-theme', 'dark');
        if (elements.themeToggle) elements.themeToggle.textContent = '☀️';
    }
}

// ═══════════════════════════════════════════════════════════════
// NAVIGATION
// ═══════════════════════════════════════════════════════════════

function goBack() {
    if (window.history.length > 1) {
        window.history.back();
    } else {
        window.close();
        setTimeout(() => {
            alert('Utilisez le bouton de fermeture de votre navigateur.');
        }, 100);
    }
}

// ═══════════════════════════════════════════════════════════════
// RECHERCHE
// ═══════════════════════════════════════════════════════════════

let currentMatches = [];
let currentMatchIndex = 0;

function setupSearch() {
    const searchInput = document.getElementById('searchInput');
    const clearBtn = document.getElementById('clearSearch');
    const prevBtn = document.getElementById('prevResult');
    const nextBtn = document.getElementById('nextResult');
    const closeBtn = document.getElementById('closeSearchResults');
    const sectionFilter = document.getElementById('sectionFilter');
    
    if (searchInput) {
        searchInput.addEventListener('input', debounce(performSearch, 300));
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                if (e.shiftKey) navigateResults(-1);
                else navigateResults(1);
            } else if (e.key === 'Escape') {
                clearSearch();
            }
        });
    }
    
    if (clearBtn) clearBtn.addEventListener('click', clearSearch);
    if (prevBtn) prevBtn.addEventListener('click', () => navigateResults(-1));
    if (nextBtn) nextBtn.addEventListener('click', () => navigateResults(1));
    if (closeBtn) closeBtn.addEventListener('click', clearSearch);
    
    if (sectionFilter) {
        sectionFilter.addEventListener('change', () => {
            if (searchInput && searchInput.value.trim()) {
                performSearch();
            } else {
                scrollToSection(sectionFilter.value);
            }
        });
    }
    
    // Raccourcis clavier globaux
    document.addEventListener('keydown', (e) => {
        if (e.key === 'F3') {
            e.preventDefault();
            if (e.shiftKey) navigateResults(-1);
            else navigateResults(1);
        }
        if ((e.ctrlKey || e.metaKey) && e.key === 'f') {
            e.preventDefault();
            if (searchInput) searchInput.focus();
        }
    });
}

function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

function performSearch() {
    const searchInput = document.getElementById('searchInput');
    const query = searchInput?.value.trim().toLowerCase() || '';
    
    // Nettoyer les anciens highlights (une seule classe)
    document.querySelectorAll('.search-highlight').forEach(el => {
        const parent = el.parentNode;
        parent.replaceChild(document.createTextNode(el.textContent), el);
        parent.normalize();
    });
    
    currentMatches = [];
    currentMatchIndex = 0;
    
    if (query.length < 2) {
        updateSearchUI();
        return;
    }
    
    // Filtrer par section si sélectionnée
    const sectionFilter = document.getElementById('sectionFilter');
    const filterValue = sectionFilter?.value || 'all';
    
    let sections = document.querySelectorAll('.help-section');
    if (filterValue !== 'all') {
        sections = document.querySelectorAll(`.help-section[id="${filterValue}"]`);
    }
    
    // Rechercher dans les sections
    sections.forEach(section => {
        const walker = document.createTreeWalker(
            section,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode: (node) => {
                    const parent = node.parentElement;
                    if (parent.closest('script, style, .notranslate')) return NodeFilter.FILTER_REJECT;
                    if (node.textContent.toLowerCase().includes(query)) return NodeFilter.FILTER_ACCEPT;
                    return NodeFilter.FILTER_REJECT;
                }
            }
        );
        
        let node;
        while (node = walker.nextNode()) {
            highlightMatches(node, query);
        }
    });
    
    currentMatches = Array.from(document.querySelectorAll('.search-highlight'));
    if (currentMatches.length > 0) {
        currentMatchIndex = 0;
        showCurrentMatch();
    }
    
    updateSearchUI();
}

function highlightMatches(textNode, query) {
    const text = textNode.textContent;
    const lowerText = text.toLowerCase();
    const index = lowerText.indexOf(query);
    
    if (index === -1) return;
    
    const before = text.substring(0, index);
    const match = text.substring(index, index + query.length);
    const after = text.substring(index + query.length);
    
    const span = document.createElement('span');
    span.className = 'search-highlight';
    span.textContent = match;
    
    const parent = textNode.parentNode;
    parent.insertBefore(document.createTextNode(before), textNode);
    parent.insertBefore(span, textNode);
    parent.replaceChild(document.createTextNode(after), textNode);
    
    // Récursivement chercher dans le reste
    if (after.toLowerCase().includes(query)) {
        const afterNode = span.nextSibling;
        if (afterNode) highlightMatches(afterNode, query);
    }
}

function showCurrentMatch() {
    // Retirer le highlight courant de tous les éléments
    document.querySelectorAll('.search-highlight.current').forEach(el => {
        el.classList.remove('current');
    });
    
    if (currentMatches.length > 0 && currentMatches[currentMatchIndex]) {
        const match = currentMatches[currentMatchIndex];
        match.classList.add('current');
        match.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
}

function navigateResults(direction) {
    if (currentMatches.length === 0) return;
    
    currentMatchIndex += direction;
    if (currentMatchIndex < 0) currentMatchIndex = currentMatches.length - 1;
    if (currentMatchIndex >= currentMatches.length) currentMatchIndex = 0;
    
    showCurrentMatch();
    updateSearchUI();
}

function updateSearchUI() {
    const nav = document.getElementById('searchNavInline');
    const count = document.getElementById('searchResultsCount');
    const index = document.getElementById('currentResultIndex');
    const clearBtn = document.getElementById('clearSearch');
    const searchInput = document.getElementById('searchInput');
    
    const hasResults = currentMatches.length > 0;
    const hasQuery = searchInput?.value.trim().length >= 2;
    
    // Afficher/masquer la navigation avec la classe visible
    if (nav) {
        if (hasQuery) {
            nav.classList.add('visible');
        } else {
            nav.classList.remove('visible');
        }
    }
    
    if (count) count.textContent = currentMatches.length;
    if (index) index.textContent = hasResults ? `${currentMatchIndex + 1}/${currentMatches.length}` : '0/0';
    if (clearBtn) clearBtn.style.display = searchInput?.value ? 'block' : 'none';
    
    // Masquer les sections du TOC sans résultats
    updateTOCVisibility(hasQuery);
}

/**
 * Met à jour la visibilité des éléments du sommaire (TOC)
 * Masque les sections sans résultats de recherche
 */
function updateTOCVisibility(hasQuery) {
    const tocItems = document.querySelectorAll('.toc-list li');
    
    if (!hasQuery) {
        // Réinitialiser : tout afficher
        tocItems.forEach(item => {
            item.classList.remove('toc-hidden', 'toc-has-results');
        });
        return;
    }
    
    // Identifier les sections qui ont des résultats
    const sectionsWithResults = new Set();
    currentMatches.forEach(match => {
        const section = match.closest('.help-section');
        if (section && section.id) {
            sectionsWithResults.add(section.id);
        }
    });
    
    // Mettre à jour chaque élément du TOC
    tocItems.forEach(item => {
        const link = item.querySelector('a');
        if (!link) return;
        
        const href = link.getAttribute('href');
        if (!href || !href.startsWith('#')) return;
        
        const sectionId = href.substring(1);
        const hasResults = sectionsWithResults.has(sectionId);
        
        // Pour les éléments principaux (non toc-sub), vérifier aussi les sous-sections
        const isMainItem = !item.classList.contains('toc-sub');
        let hasSubResults = false;
        
        if (isMainItem) {
            // Vérifier si une sous-section a des résultats
            let nextItem = item.nextElementSibling;
            while (nextItem && nextItem.classList.contains('toc-sub')) {
                const subLink = nextItem.querySelector('a');
                if (subLink) {
                    const subHref = subLink.getAttribute('href');
                    if (subHref && sectionsWithResults.has(subHref.substring(1))) {
                        hasSubResults = true;
                        break;
                    }
                }
                nextItem = nextItem.nextElementSibling;
            }
        }
        
        // Appliquer les classes
        if (hasResults || hasSubResults) {
            item.classList.remove('toc-hidden');
            item.classList.add('toc-has-results');
        } else {
            item.classList.add('toc-hidden');
            item.classList.remove('toc-has-results');
        }
    });
}

function clearSearch() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) searchInput.value = '';
    
    // Nettoyer les highlights (utiliser les bonnes classes)
    document.querySelectorAll('.search-highlight').forEach(el => {
        const parent = el.parentNode;
        parent.replaceChild(document.createTextNode(el.textContent), el);
        parent.normalize();
    });
    
    currentMatches = [];
    currentMatchIndex = 0;
    updateSearchUI();
}

function scrollToSection(sectionId) {
    if (sectionId === 'all') return;
    
    const section = document.getElementById(sectionId);
    if (section) {
        section.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
}

// ═══════════════════════════════════════════════════════════════
// SOMMAIRE (TOC)
// ═══════════════════════════════════════════════════════════════

function setupTOC() {
    const toc = document.querySelector('.toc-card');
    if (!toc) return;
    
    // Gérer le toggle mobile
    const tocHeader = toc.querySelector('.toc-header');
    if (tocHeader) {
        tocHeader.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                toc.classList.toggle('expanded');
            }
        });
    }
    
    // Highlight de la section active au scroll
    const sections = document.querySelectorAll('.help-section');
    const tocLinks = document.querySelectorAll('.toc-link');
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                tocLinks.forEach(link => {
                    link.classList.remove('active');
                    if (link.getAttribute('href') === `#${entry.target.id}`) {
                        link.classList.add('active');
                    }
                });
            }
        });
    }, { threshold: 0.2, rootMargin: '-20% 0px -70% 0px' });
    
    sections.forEach(section => observer.observe(section));
}

// ═══════════════════════════════════════════════════════════════
// IMAGES
// ═══════════════════════════════════════════════════════════════

function setupImages() {
    // Lightbox pour les images
    document.querySelectorAll('.help-section img').forEach(img => {
        img.style.cursor = 'zoom-in';
        img.addEventListener('click', () => openLightbox(img));
    });
}

function openLightbox(img) {
    const existing = document.getElementById('lightbox');
    if (existing) existing.remove();
    
    const lightbox = document.createElement('div');
    lightbox.id = 'lightbox';
    lightbox.innerHTML = `
        <div class="lightbox-overlay" onclick="closeLightbox()"></div>
        <img class="lightbox-img" src="${img.src}" alt="${img.alt || ''}">
        <button class="lightbox-close" onclick="closeLightbox()">✕</button>
    `;
    document.body.appendChild(lightbox);
    document.body.style.overflow = 'hidden';
}

function closeLightbox() {
    const lightbox = document.getElementById('lightbox');
    if (lightbox) {
        lightbox.remove();
        document.body.style.overflow = '';
    }
}

// ═══════════════════════════════════════════════════════════════
// INITIALISATION
// ═══════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    console.log('[KVM] Initialisation...');
    
    initTheme();
    detectCurrentLanguage();
    setupSearch();
    setupTOC();
    setupImages();
    
    // Bind events
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) themeToggle.addEventListener('click', toggleTheme);
    
    console.log('[KVM] Initialisation terminée');
});

// Fermer lightbox avec Escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeLightbox();
});
