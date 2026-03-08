/**
 * Export de chapitres - Kitview Manual
 * =====================================
 * Bouton d'export style iPhone (carré + flèche vers le haut)
 * Options: PDF, Copier texte, Copier Markdown, Imprimer
 */

(function() {
    'use strict';
    
    // ========================================
    // CONFIGURATION
    // ========================================
    
    const EXPORT_ICON = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/>
        <polyline points="16 6 12 2 8 6"/>
        <line x1="12" y1="2" x2="12" y2="15"/>
    </svg>`;
    
    // ========================================
    // STYLES
    // ========================================
    
    function injectStyles() {
        if (document.getElementById('chapter-export-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'chapter-export-styles';
        style.textContent = `
            /* Bouton d'export - style discret */
            .chapter-export-btn {
                display: inline-flex;
                align-items: center;
                justify-content: center;
                width: 24px;
                height: 24px;
                padding: 0;
                margin-left: 8px;
                background: transparent;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                opacity: 0;
                transition: opacity 0.2s, background 0.2s;
                color: var(--text-muted, #6b7280);
                vertical-align: middle;
            }
            
            /* Afficher au survol du titre ou du lien TOC */
            .toc-link:hover .chapter-export-btn,
            .help-section h2:hover .chapter-export-btn,
            .help-section h3:hover .chapter-export-btn,
            .chapter-export-btn:hover,
            .chapter-export-btn:focus {
                opacity: 1;
            }
            
            .chapter-export-btn:hover {
                background: var(--bg-hover, rgba(0, 0, 0, 0.05));
                color: var(--primary, #2563eb);
            }
            
            .chapter-export-btn svg {
                width: 14px;
                height: 14px;
            }
            
            /* Menu popup d'export */
            .export-menu {
                position: absolute;
                top: 100%;
                right: 0;
                margin-top: 4px;
                background: var(--bg-card, #fff);
                border: 1px solid var(--border, #e5e7eb);
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                z-index: 1000;
                min-width: 180px;
                padding: 4px;
                display: none;
            }
            
            .export-menu.open {
                display: block;
            }
            
            .export-menu-item {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 10px 12px;
                border: none;
                background: transparent;
                width: 100%;
                text-align: left;
                cursor: pointer;
                border-radius: 6px;
                font-size: 14px;
                color: var(--text, #1f2937);
                transition: background 0.15s;
            }
            
            .export-menu-item:hover {
                background: var(--bg-hover, #f3f4f6);
            }
            
            .export-menu-item .icon {
                font-size: 16px;
                width: 20px;
                text-align: center;
            }
            
            .export-menu-separator {
                height: 1px;
                background: var(--border, #e5e7eb);
                margin: 4px 8px;
            }
            
            /* Container relatif pour le positionnement */
            .export-btn-container {
                position: relative;
                display: inline-block;
            }
            
            /* Mode sombre */
            [data-theme="dark"] .export-menu,
            [data-theme="nuit"] .export-menu {
                background: #1e293b;
                border-color: #334155;
            }
            
            [data-theme="dark"] .export-menu-item,
            [data-theme="nuit"] .export-menu-item {
                color: #f1f5f9;
            }
            
            [data-theme="dark"] .export-menu-item:hover,
            [data-theme="nuit"] .export-menu-item:hover {
                background: #334155;
            }
            
            /* Toast notification */
            .export-toast {
                position: fixed;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: #1f2937;
                color: white;
                padding: 12px 24px;
                border-radius: 8px;
                font-size: 14px;
                z-index: 10000;
                animation: toast-in 0.3s ease;
            }
            
            @keyframes toast-in {
                from {
                    opacity: 0;
                    transform: translateX(-50%) translateY(20px);
                }
                to {
                    opacity: 1;
                    transform: translateX(-50%) translateY(0);
                }
            }
            
            /* Print styles */
            @media print {
                .chapter-export-btn,
                .export-menu,
                .toc-card,
                .help-header,
                .chatbot-toggle,
                #chatbot-modal {
                    display: none !important;
                }
                
                .help-section.print-target {
                    display: block !important;
                }
                
                .help-section:not(.print-target) {
                    display: none !important;
                }
                
                body {
                    padding: 20px;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    // ========================================
    // EXTRACTION DU CONTENU
    // ========================================
    
    /**
     * Extrait le contenu d'une section
     */
    function getSectionContent(sectionId) {
        const section = document.getElementById(sectionId);
        if (!section) return null;
        
        const clone = section.cloneNode(true);
        
        // Supprimer les boutons d'export du clone
        clone.querySelectorAll('.chapter-export-btn, .export-btn-container, .export-menu').forEach(el => el.remove());
        
        return {
            element: section,
            html: clone.innerHTML,
            text: clone.textContent.trim(),
            title: clone.querySelector('h2, h3')?.textContent?.trim() || 'Section'
        };
    }
    
    /**
     * Convertit le HTML en Markdown simplifié
     */
    function htmlToMarkdown(html) {
        const temp = document.createElement('div');
        temp.innerHTML = html;
        
        // Titres
        temp.querySelectorAll('h2').forEach(h => {
            h.outerHTML = `\n## ${h.textContent}\n`;
        });
        temp.querySelectorAll('h3').forEach(h => {
            h.outerHTML = `\n### ${h.textContent}\n`;
        });
        temp.querySelectorAll('h4').forEach(h => {
            h.outerHTML = `\n#### ${h.textContent}\n`;
        });
        
        // Listes
        temp.querySelectorAll('li').forEach(li => {
            li.outerHTML = `- ${li.textContent}\n`;
        });
        
        // Gras
        temp.querySelectorAll('strong, b').forEach(el => {
            el.outerHTML = `**${el.textContent}**`;
        });
        
        // Italique
        temp.querySelectorAll('em, i').forEach(el => {
            el.outerHTML = `*${el.textContent}*`;
        });
        
        // Liens
        temp.querySelectorAll('a').forEach(a => {
            a.outerHTML = `[${a.textContent}](${a.href})`;
        });
        
        // Images
        temp.querySelectorAll('img').forEach(img => {
            img.outerHTML = `![${img.alt || 'image'}](${img.src})`;
        });
        
        // Nettoyer
        let md = temp.textContent || temp.innerText;
        md = md.replace(/\n{3,}/g, '\n\n');
        
        return md.trim();
    }
    
    // ========================================
    // ACTIONS D'EXPORT
    // ========================================
    
    function showToast(message) {
        const existing = document.querySelector('.export-toast');
        if (existing) existing.remove();
        
        const toast = document.createElement('div');
        toast.className = 'export-toast';
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => toast.remove(), 2500);
    }
    
    function copyText(sectionId) {
        const content = getSectionContent(sectionId);
        if (!content) return;
        
        navigator.clipboard.writeText(content.text).then(() => {
            const lang = document.documentElement.lang || 'fr';
            showToast(lang === 'fr' ? '✅ Texte copié !' : '✅ Text copied!');
        }).catch(err => {
            console.error('[Export] Erreur copie:', err);
        });
    }
    
    function copyMarkdown(sectionId) {
        const content = getSectionContent(sectionId);
        if (!content) return;
        
        const markdown = htmlToMarkdown(content.html);
        
        navigator.clipboard.writeText(markdown).then(() => {
            const lang = document.documentElement.lang || 'fr';
            showToast(lang === 'fr' ? '✅ Markdown copié !' : '✅ Markdown copied!');
        }).catch(err => {
            console.error('[Export] Erreur copie MD:', err);
        });
    }
    
    function printSection(sectionId) {
        const section = document.getElementById(sectionId);
        if (!section) return;
        
        // Marquer la section pour l'impression
        document.querySelectorAll('.help-section').forEach(s => s.classList.remove('print-target'));
        section.classList.add('print-target');
        
        // Imprimer
        window.print();
        
        // Nettoyer
        setTimeout(() => {
            section.classList.remove('print-target');
        }, 1000);
    }
    
    function exportPDF(sectionId) {
        // Pour le PDF, on utilise l'impression en PDF du navigateur
        const lang = document.documentElement.lang || 'fr';
        showToast(lang === 'fr' 
            ? '📄 Choisissez "Enregistrer en PDF" dans la boîte d\'impression'
            : '📄 Choose "Save as PDF" in the print dialog');
        
        setTimeout(() => printSection(sectionId), 500);
    }
    
    // ========================================
    // CRÉATION DES BOUTONS
    // ========================================
    
    function createExportButton(sectionId) {
        const lang = document.documentElement.lang || 'fr';
        
        const container = document.createElement('span');
        container.className = 'export-btn-container';
        
        const btn = document.createElement('button');
        btn.className = 'chapter-export-btn';
        btn.innerHTML = EXPORT_ICON;
        btn.title = lang === 'fr' ? 'Exporter ce chapitre' : 'Export this chapter';
        btn.setAttribute('aria-label', btn.title);
        
        const menu = document.createElement('div');
        menu.className = 'export-menu';
        menu.innerHTML = `
            <button class="export-menu-item" data-action="pdf">
                <span class="icon">📄</span>
                <span>${lang === 'fr' ? 'Exporter en PDF' : 'Export as PDF'}</span>
            </button>
            <button class="export-menu-item" data-action="copy">
                <span class="icon">📋</span>
                <span>${lang === 'fr' ? 'Copier le texte' : 'Copy text'}</span>
            </button>
            <button class="export-menu-item" data-action="markdown">
                <span class="icon">📝</span>
                <span>${lang === 'fr' ? 'Copier en Markdown' : 'Copy as Markdown'}</span>
            </button>
            <div class="export-menu-separator"></div>
            <button class="export-menu-item" data-action="print">
                <span class="icon">🖨️</span>
                <span>${lang === 'fr' ? 'Imprimer' : 'Print'}</span>
            </button>
        `;
        
        // Toggle menu
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            // Fermer les autres menus
            document.querySelectorAll('.export-menu.open').forEach(m => {
                if (m !== menu) m.classList.remove('open');
            });
            
            menu.classList.toggle('open');
        });
        
        // Actions du menu
        menu.querySelectorAll('.export-menu-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                const action = item.dataset.action;
                menu.classList.remove('open');
                
                switch (action) {
                    case 'pdf':
                        exportPDF(sectionId);
                        break;
                    case 'copy':
                        copyText(sectionId);
                        break;
                    case 'markdown':
                        copyMarkdown(sectionId);
                        break;
                    case 'print':
                        printSection(sectionId);
                        break;
                }
            });
        });
        
        container.appendChild(btn);
        container.appendChild(menu);
        
        return container;
    }
    
    // ========================================
    // INITIALISATION
    // ========================================
    
    function init() {
        injectStyles();
        
        // Ajouter les boutons aux liens du sommaire (TOC)
        document.querySelectorAll('.toc-link').forEach(link => {
            const href = link.getAttribute('href');
            if (!href || !href.startsWith('#')) return;
            
            const sectionId = href.slice(1);
            const exportBtn = createExportButton(sectionId);
            link.appendChild(exportBtn);
        });
        
        // Ajouter les boutons aux titres des sections
        document.querySelectorAll('.help-section').forEach(section => {
            const sectionId = section.id;
            if (!sectionId) return;
            
            const title = section.querySelector('h2, h3');
            if (title) {
                const exportBtn = createExportButton(sectionId);
                title.appendChild(exportBtn);
            }
        });
        
        // Fermer les menus au clic ailleurs
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.export-btn-container')) {
                document.querySelectorAll('.export-menu.open').forEach(m => m.classList.remove('open'));
            }
        });
        
        // Fermer avec Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                document.querySelectorAll('.export-menu.open').forEach(m => m.classList.remove('open'));
            }
        });
        
        console.log('[ChapterExport] Initialisé');
    }
    
    // Lancer à la fin du chargement
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
})();
