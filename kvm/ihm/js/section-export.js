/**
 * Section Export - Kitview Manual
 * ================================
 * Bouton d'export style iPhone (carré + flèche vers le haut)
 * Options: PDF, Copier texte, Copier Markdown, Imprimer
 * 
 * Usage: Inclure ce script après le DOM chargé
 * Les boutons sont ajoutés automatiquement aux titres h2 des sections
 */

(function() {
    'use strict';

    // ========================================
    // CONFIGURATION
    // ========================================
    
    // Icône style iPhone (carré + flèche)
    const EXPORT_ICON = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/>
        <polyline points="16 6 12 2 8 6"/>
        <line x1="12" y1="2" x2="12" y2="15"/>
    </svg>`;

    // Traductions
    const TRANSLATIONS = {
        fr: {
            exportTitle: 'Exporter ce chapitre',
            exportPdf: 'Exporter en PDF',
            copyText: 'Copier le texte',
            copyMarkdown: 'Copier en Markdown',
            print: 'Imprimer',
            copied: '✅ Copié !',
            markdownCopied: '✅ Markdown copié !',
            pdfHint: '📄 Choisissez "Enregistrer en PDF" dans la boîte d\'impression'
        },
        en: {
            exportTitle: 'Export this chapter',
            exportPdf: 'Export as PDF',
            copyText: 'Copy text',
            copyMarkdown: 'Copy as Markdown',
            print: 'Print',
            copied: '✅ Copied!',
            markdownCopied: '✅ Markdown copied!',
            pdfHint: '📄 Choose "Save as PDF" in the print dialog'
        }
    };

    // ========================================
    // UTILITAIRES
    // ========================================

    function getLang() {
        return document.documentElement.lang || 'fr';
    }

    function t(key) {
        const lang = getLang();
        return TRANSLATIONS[lang]?.[key] || TRANSLATIONS.fr[key] || key;
    }

    function showToast(message) {
        // Supprimer les toasts existants
        document.querySelectorAll('.export-toast').forEach(t => t.remove());
        
        const toast = document.createElement('div');
        toast.className = 'export-toast';
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => toast.remove(), 2500);
    }

    // ========================================
    // EXTRACTION DU CONTENU
    // ========================================

    function getSectionContent(sectionId) {
        const section = document.getElementById(sectionId);
        if (!section) return null;

        // Cloner la section pour ne pas modifier l'original
        const clone = section.cloneNode(true);
        
        // Retirer les éléments non voulus (boutons export, etc.)
        clone.querySelectorAll('.section-export-container, .section-export-btn, script, style').forEach(el => el.remove());
        
        return {
            title: section.querySelector('h2, h3')?.textContent?.trim() || '',
            html: clone.innerHTML,
            text: clone.textContent?.trim() || ''
        };
    }

    function htmlToMarkdown(html) {
        const temp = document.createElement('div');
        temp.innerHTML = html;
        
        // Convertir les titres
        temp.querySelectorAll('h2').forEach(h => {
            h.outerHTML = `\n## ${h.textContent.trim()}\n`;
        });
        temp.querySelectorAll('h3').forEach(h => {
            h.outerHTML = `\n### ${h.textContent.trim()}\n`;
        });
        temp.querySelectorAll('h4').forEach(h => {
            h.outerHTML = `\n#### ${h.textContent.trim()}\n`;
        });
        
        // Convertir les listes
        temp.querySelectorAll('ul li').forEach(li => {
            li.outerHTML = `- ${li.textContent.trim()}\n`;
        });
        temp.querySelectorAll('ol li').forEach((li, i) => {
            li.outerHTML = `${i + 1}. ${li.textContent.trim()}\n`;
        });
        
        // Convertir les paragraphes
        temp.querySelectorAll('p').forEach(p => {
            p.outerHTML = `\n${p.textContent.trim()}\n`;
        });
        
        // Convertir le gras et l'italique
        temp.querySelectorAll('strong, b').forEach(el => {
            el.outerHTML = `**${el.textContent}**`;
        });
        temp.querySelectorAll('em, i').forEach(el => {
            el.outerHTML = `*${el.textContent}*`;
        });
        
        // Convertir les liens
        temp.querySelectorAll('a').forEach(a => {
            const href = a.getAttribute('href') || '';
            a.outerHTML = `[${a.textContent}](${href})`;
        });
        
        // Convertir les images
        temp.querySelectorAll('img').forEach(img => {
            const alt = img.getAttribute('alt') || 'image';
            const src = img.getAttribute('src') || '';
            img.outerHTML = `![${alt}](${src})`;
        });
        
        // Convertir les blocs de code
        temp.querySelectorAll('pre, code').forEach(code => {
            code.outerHTML = `\`${code.textContent}\``;
        });
        
        // Nettoyer
        let md = temp.textContent || temp.innerText;
        md = md.replace(/\n{3,}/g, '\n\n').trim();
        
        return md;
    }

    // ========================================
    // ACTIONS D'EXPORT
    // ========================================

    function copyText(sectionId) {
        const content = getSectionContent(sectionId);
        if (!content) return;
        
        navigator.clipboard.writeText(content.text).then(() => {
            showToast(t('copied'));
        }).catch(err => {
            console.error('[Export] Erreur copie:', err);
        });
    }

    function copyMarkdown(sectionId) {
        const content = getSectionContent(sectionId);
        if (!content) return;
        
        const markdown = htmlToMarkdown(content.html);
        
        navigator.clipboard.writeText(markdown).then(() => {
            showToast(t('markdownCopied'));
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
        
        // Nettoyer après impression
        setTimeout(() => {
            section.classList.remove('print-target');
        }, 1000);
    }

    function exportPdf(sectionId) {
        showToast(t('pdfHint'));
        setTimeout(() => printSection(sectionId), 500);
    }

    // ========================================
    // CRÉATION DES BOUTONS
    // ========================================

    function createExportButton(sectionId) {
        const container = document.createElement('span');
        container.className = 'section-export-container';
        
        // Bouton principal
        const btn = document.createElement('button');
        btn.className = 'section-export-btn';
        btn.innerHTML = EXPORT_ICON;
        btn.title = t('exportTitle');
        btn.setAttribute('aria-label', t('exportTitle'));
        btn.setAttribute('aria-haspopup', 'true');
        btn.setAttribute('aria-expanded', 'false');
        
        // Menu dropdown
        const menu = document.createElement('div');
        menu.className = 'section-export-menu';
        menu.innerHTML = `
            <button data-action="pdf">
                <span class="icon">📄</span>
                <span>${t('exportPdf')}</span>
            </button>
            <button data-action="copy">
                <span class="icon">📋</span>
                <span>${t('copyText')}</span>
            </button>
            <button data-action="markdown">
                <span class="icon">📝</span>
                <span>${t('copyMarkdown')}</span>
            </button>
            <div class="separator"></div>
            <button data-action="print">
                <span class="icon">🖨️</span>
                <span>${t('print')}</span>
            </button>
        `;
        
        container.appendChild(btn);
        container.appendChild(menu);
        
        // Gestion du clic sur le bouton
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isOpen = menu.classList.contains('show');
            
            // Fermer tous les autres menus
            document.querySelectorAll('.section-export-menu.show').forEach(m => {
                m.classList.remove('show');
                m.previousElementSibling?.setAttribute('aria-expanded', 'false');
                m.previousElementSibling?.classList.remove('active');
            });
            
            if (!isOpen) {
                menu.classList.add('show');
                btn.setAttribute('aria-expanded', 'true');
                btn.classList.add('active');
            }
        });
        
        // Gestion des actions du menu
        menu.querySelectorAll('button').forEach(item => {
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = item.dataset.action;
                
                switch (action) {
                    case 'pdf':
                        exportPdf(sectionId);
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
                
                // Fermer le menu
                menu.classList.remove('show');
                btn.setAttribute('aria-expanded', 'false');
                btn.classList.remove('active');
            });
        });
        
        return container;
    }

    // ========================================
    // INITIALISATION
    // ========================================

    function init() {
        // Ajouter les boutons d'export à chaque section
        document.querySelectorAll('.help-section').forEach(section => {
            const sectionId = section.id;
            if (!sectionId) return;
            
            const title = section.querySelector('h2, h3');
            if (!title) return;
            
            // Ne pas ajouter si déjà présent
            if (title.querySelector('.section-export-container')) return;
            
            const exportBtn = createExportButton(sectionId);
            title.appendChild(exportBtn);
        });
        
        // Fermer les menus au clic extérieur
        document.addEventListener('click', () => {
            document.querySelectorAll('.section-export-menu.show').forEach(menu => {
                menu.classList.remove('show');
                menu.previousElementSibling?.setAttribute('aria-expanded', 'false');
                menu.previousElementSibling?.classList.remove('active');
            });
        });
        
        // Fermer les menus avec Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                document.querySelectorAll('.section-export-menu.show').forEach(menu => {
                    menu.classList.remove('show');
                    menu.previousElementSibling?.setAttribute('aria-expanded', 'false');
                    menu.previousElementSibling?.classList.remove('active');
                });
            }
        });
        
        console.log('[SectionExport] Initialisé -', document.querySelectorAll('.section-export-btn').length, 'boutons ajoutés');
    }

    // Lancer l'initialisation quand le DOM est prêt
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
