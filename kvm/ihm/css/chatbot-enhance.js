/**
 * Chatbot Enhancements - Kitview Manual
 * ======================================
 * Ajoute les fonctionnalités :
 * - Bouton plein écran (loupe) dans la toolbar
 * - Bouton export avec menu (PDF, Copier, MD)
 * 
 * Ce script s'ajoute APRÈS chatbot.js
 */

(function() {
    'use strict';

    // Attendre que le DOM soit prêt
    function init() {
        const toolbar = document.getElementById('chatbot-toolbar');
        const modal = document.getElementById('chatbot-modal');
        const settingsBtn = document.getElementById('chatbot-settings-btn');
        
        if (!toolbar || !modal) {
            console.warn('[ChatbotEnhance] Toolbar ou modal non trouvé');
            return;
        }

        // Vérifier si déjà initialisé
        if (document.getElementById('chatbot-fullscreen-btn')) {
            return;
        }

        const lang = document.documentElement.lang || 'fr';
        const t = {
            fullscreen: lang === 'fr' ? 'Plein écran' : 'Fullscreen',
            exitFullscreen: lang === 'fr' ? 'Quitter plein écran' : 'Exit fullscreen',
            export: lang === 'fr' ? 'Exporter' : 'Export',
            exportPdf: lang === 'fr' ? 'Exporter en PDF' : 'Export as PDF',
            copyText: lang === 'fr' ? 'Copier le texte' : 'Copy text',
            copyMd: lang === 'fr' ? 'Copier en Markdown' : 'Copy as Markdown',
            copied: lang === 'fr' ? '✅ Copié !' : '✅ Copied!',
            pdfHint: lang === 'fr' ? '📄 Utilisez Ctrl+P puis "Enregistrer en PDF"' : '📄 Use Ctrl+P then "Save as PDF"'
        };

        // Créer le groupe de boutons à droite
        const rightGroup = document.createElement('div');
        rightGroup.className = 'toolbar-right';

        // === BOUTON PLEIN ÉCRAN ===
        const fullscreenBtn = document.createElement('button');
        fullscreenBtn.id = 'chatbot-fullscreen-btn';
        fullscreenBtn.innerHTML = '🔍';
        fullscreenBtn.title = t.fullscreen;
        fullscreenBtn.setAttribute('aria-label', t.fullscreen);

        fullscreenBtn.addEventListener('click', () => {
            modal.classList.toggle('fullscreen');
            const isFullscreen = modal.classList.contains('fullscreen');
            fullscreenBtn.innerHTML = isFullscreen ? '🔍' : '🔍';
            fullscreenBtn.title = isFullscreen ? t.exitFullscreen : t.fullscreen;
        });

        // === BOUTON EXPORT ===
        const exportContainer = document.createElement('div');
        exportContainer.id = 'chatbot-export-btn';
        exportContainer.style.position = 'relative';

        const exportBtn = document.createElement('button');
        exportBtn.innerHTML = '📤';
        exportBtn.title = t.export;
        exportBtn.setAttribute('aria-label', t.export);
        exportBtn.setAttribute('aria-haspopup', 'true');

        const exportMenu = document.createElement('div');
        exportMenu.id = 'chatbot-export-menu';
        exportMenu.innerHTML = `
            <button data-action="pdf">📄 ${t.exportPdf}</button>
            <button data-action="copy">📋 ${t.copyText}</button>
            <button data-action="markdown">📝 ${t.copyMd}</button>
        `;

        exportContainer.appendChild(exportBtn);
        exportContainer.appendChild(exportMenu);

        // Toggle menu
        exportBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            exportMenu.classList.toggle('show');
        });

        // Fermer le menu au clic ailleurs
        document.addEventListener('click', () => {
            exportMenu.classList.remove('show');
        });

        // Actions d'export
        exportMenu.querySelectorAll('button').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const action = btn.dataset.action;
                
                const messages = document.getElementById('chatbot-messages');
                if (!messages) return;

                const content = getMessagesContent(messages);

                switch (action) {
                    case 'pdf':
                        showToast(t.pdfHint);
                        setTimeout(() => {
                            // Passer en plein écran pour un meilleur rendu
                            modal.classList.add('fullscreen');
                            window.print();
                        }, 500);
                        break;
                    case 'copy':
                        navigator.clipboard.writeText(content.text).then(() => {
                            showToast(t.copied);
                        });
                        break;
                    case 'markdown':
                        navigator.clipboard.writeText(content.markdown).then(() => {
                            showToast(t.copied);
                        });
                        break;
                }

                exportMenu.classList.remove('show');
            });
        });

        // Assembler
        rightGroup.appendChild(fullscreenBtn);
        rightGroup.appendChild(exportContainer);

        // Déplacer le bouton settings dans le groupe de droite s'il existe
        if (settingsBtn) {
            rightGroup.appendChild(settingsBtn);
        }

        toolbar.appendChild(rightGroup);

        console.log('[ChatbotEnhance] Boutons plein écran et export ajoutés');
    }

    // Extraire le contenu des messages
    function getMessagesContent(messagesContainer) {
        const messages = messagesContainer.querySelectorAll('.chat-message');
        let text = '';
        let markdown = '';

        messages.forEach(msg => {
            const isUser = msg.classList.contains('user');
            const prefix = isUser ? '**Vous:** ' : '**Assistant:** ';
            const content = msg.textContent.trim();

            text += (isUser ? 'Vous: ' : 'Assistant: ') + content + '\n\n';
            markdown += prefix + content + '\n\n';
        });

        return { text: text.trim(), markdown: markdown.trim() };
    }

    // Afficher un toast
    function showToast(message) {
        const existing = document.querySelector('.export-toast');
        if (existing) existing.remove();

        const toast = document.createElement('div');
        toast.className = 'export-toast';
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => toast.remove(), 3000);
    }

    // Lancer l'initialisation
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        // Attendre un peu que chatbot.js soit initialisé
        setTimeout(init, 100);
    }

})();
