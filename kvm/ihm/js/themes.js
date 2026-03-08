/**
 * Sélecteur de Thèmes Kitview
 * ===========================
 * Permet de changer l'apparence du manuel avec 10 thèmes différents
 */

(function() {
    'use strict';
    
    const STORAGE_KEY = 'kvm_theme';
    
    // Liste des thèmes disponibles
    const THEMES = [
        { id: 'kitview', name: 'Kitview', emoji: '💙', color: '#2563eb' },
        { id: 'orchidee', name: 'Orchidée', emoji: '💜', color: '#7c3aed' },
        { id: 'foret', name: 'Forêt', emoji: '🌲', color: '#059669' },
        { id: 'ocean', name: 'Océan', emoji: '🌊', color: '#0891b2' },
        { id: 'sunset', name: 'Sunset', emoji: '🌅', color: '#ea580c' },
        { id: 'rose', name: 'Rose', emoji: '🌸', color: '#db2777' },
        { id: 'nuit', name: 'Nuit', emoji: '🌙', color: '#6366f1' },
        { id: 'minimal', name: 'Minimal', emoji: '⬜', color: '#374151' },
        { id: 'lavande', name: 'Lavande', emoji: '💐', color: '#9333ea' },
        { id: 'cafe', name: 'Café', emoji: '☕', color: '#92400e' }
    ];
    
    // Charger le thème sauvegardé
    function loadSavedTheme() {
        const saved = localStorage.getItem(STORAGE_KEY);
        if (saved && THEMES.find(t => t.id === saved)) {
            applyTheme(saved);
        }
    }
    
    // Appliquer un thème
    function applyTheme(themeId) {
        document.documentElement.setAttribute('data-theme', themeId);
        localStorage.setItem(STORAGE_KEY, themeId);
        
        // Mettre à jour le bouton
        const btn = document.getElementById('themeButton');
        const theme = THEMES.find(t => t.id === themeId);
        if (btn && theme) {
            btn.innerHTML = `
                <span class="theme-preview" style="background: ${theme.color}"></span>
                <span class="theme-emoji">${theme.emoji}</span>
                <span class="dropdown-arrow">▼</span>
            `;
        }
        
        // Fermer le popup
        const popup = document.getElementById('themePopup');
        if (popup) popup.style.display = 'none';
    }
    
    // Créer le HTML du sélecteur
    function createThemeSelector() {
        const container = document.createElement('div');
        container.className = 'theme-button-container';
        container.innerHTML = `
            <button class="theme-button" id="themeButton" onclick="toggleThemePopup()">
                <span class="theme-preview" style="background: #2563eb"></span>
                <span class="theme-emoji">💙</span>
                <span class="dropdown-arrow">▼</span>
            </button>
            <div class="theme-popup" id="themePopup" style="display: none;">
                <div class="theme-popup-header">
                    <span>🎨</span> Thème visuel
                </div>
                <div class="themes-grid">
                    ${THEMES.map(theme => `
                        <div class="theme-option" onclick="selectTheme('${theme.id}')" data-theme-id="${theme.id}">
                            <span class="theme-color" style="background: ${theme.color}"></span>
                            <span class="theme-name">${theme.emoji} ${theme.name}</span>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        return container;
    }
    
    // Injecter les styles du sélecteur
    function injectStyles() {
        const style = document.createElement('style');
        style.textContent = `
            /* Container du sélecteur de thème */
            .theme-button-container {
                position: relative;
                margin-left: 8px;
            }
            
            /* Bouton principal */
            .theme-button {
                display: flex;
                align-items: center;
                gap: 6px;
                padding: 8px 12px;
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.2s;
                color: white;
                font-size: 14px;
            }
            
            .theme-button:hover {
                background: rgba(255, 255, 255, 0.25);
            }
            
            .theme-preview {
                width: 16px;
                height: 16px;
                border-radius: 50%;
                border: 2px solid rgba(255, 255, 255, 0.5);
            }
            
            .theme-emoji {
                font-size: 16px;
            }
            
            .theme-button .dropdown-arrow {
                font-size: 10px;
                opacity: 0.7;
            }
            
            /* Popup des thèmes */
            .theme-popup {
                position: absolute;
                top: calc(100% + 8px);
                right: 0;
                background: white;
                border-radius: 12px;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
                z-index: 1000;
                min-width: 280px;
                overflow: hidden;
                border: 1px solid #e5e7eb;
            }
            
            .theme-popup-header {
                padding: 12px 16px;
                background: #f8fafc;
                border-bottom: 1px solid #e5e7eb;
                font-weight: 600;
                font-size: 14px;
                color: #374151;
            }
            
            .themes-grid {
                padding: 8px;
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 4px;
            }
            
            .theme-option {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 10px 12px;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.2s;
            }
            
            .theme-option:hover {
                background: #f1f5f9;
            }
            
            .theme-option.active {
                background: #eff6ff;
                outline: 2px solid #3b82f6;
            }
            
            .theme-color {
                width: 20px;
                height: 20px;
                border-radius: 50%;
                flex-shrink: 0;
                border: 2px solid rgba(0, 0, 0, 0.1);
            }
            
            .theme-name {
                font-size: 13px;
                color: #374151;
                white-space: nowrap;
            }
            
            /* Mode sombre */
            [data-theme="nuit"] .theme-popup {
                background: #1e293b;
                border-color: #334155;
            }
            
            [data-theme="nuit"] .theme-popup-header {
                background: #0f172a;
                border-color: #334155;
                color: #f1f5f9;
            }
            
            [data-theme="nuit"] .theme-option:hover {
                background: #334155;
            }
            
            [data-theme="nuit"] .theme-name {
                color: #f1f5f9;
            }
            
            /* Responsive */
            @media (max-width: 768px) {
                .theme-popup {
                    right: -50px;
                    min-width: 260px;
                }
                
                .themes-grid {
                    grid-template-columns: 1fr;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    // Fonctions globales
    window.toggleThemePopup = function() {
        const popup = document.getElementById('themePopup');
        if (popup) {
            popup.style.display = popup.style.display === 'none' ? 'block' : 'none';
        }
    };
    
    window.selectTheme = function(themeId) {
        applyTheme(themeId);
        
        // Mettre à jour l'état actif
        document.querySelectorAll('.theme-option').forEach(opt => {
            opt.classList.toggle('active', opt.dataset.themeId === themeId);
        });
    };
    
    // Fermer le popup en cliquant dehors
    document.addEventListener('click', function(e) {
        const container = document.querySelector('.theme-button-container');
        const popup = document.getElementById('themePopup');
        if (container && popup && !container.contains(e.target)) {
            popup.style.display = 'none';
        }
    });
    
    // Initialisation
    function init() {
        injectStyles();
        
        // Trouver l'emplacement pour insérer le sélecteur (à côté du sélecteur de langue)
        const headerRight = document.querySelector('.header-right');
        if (headerRight) {
            const selector = createThemeSelector();
            // Insérer avant le sélecteur de langue
            const langContainer = headerRight.querySelector('.lang-button-container');
            if (langContainer) {
                headerRight.insertBefore(selector, langContainer);
            } else {
                headerRight.appendChild(selector);
            }
        }
        
        // Charger le thème sauvegardé
        loadSavedTheme();
        
        console.log('[Themes] Sélecteur initialisé avec', THEMES.length, 'thèmes');
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
})();
