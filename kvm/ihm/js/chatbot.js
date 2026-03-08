/**
 * Chatbot Kitview - JavaScript V4
 * ================================
 * Support Claude ET ChatGPT avec switch dynamique
 * 
 * V4 - Nouveautés :
 * - Support OpenAI ChatGPT en plus de Claude
 * - Switch Claude/ChatGPT si les deux clés sont présentes
 * - Auto-détection du provider disponible
 * - Sauvegarde du provider préféré
 */

(function() {
    'use strict';
    
    // ========================================
    // CONFIGURATION
    // ========================================
    
    const STORAGE_KEY_CLAUDE = 'chatbot_api_key_claude';
    const STORAGE_KEY_OPENAI = 'chatbot_api_key_openai';
    const STORAGE_PROVIDER = 'chatbot_provider';
    const STORAGE_SIZE_KEY = 'chatbot_size';
    
    const DEFAULT_CLAUDE_MODEL = 'claude-haiku-4-5-20251001';
    const DEFAULT_OPENAI_MODEL = 'gpt-4o-mini';
    
    let currentProvider = 'claude'; // 'claude' ou 'openai'
    
    function getConfig() {
        return window.CHATBOT_CONFIG || {};
    }
    
    /**
     * Détecte les providers disponibles et retourne leurs infos
     */
    function getAvailableProviders() {
        const config = getConfig();
        const providers = {};
        
        // Claude - config ou localStorage
        const claudeConfigKey = config.claudeKey || config.apiKey || '';
        const claudeUserKey = localStorage.getItem(STORAGE_KEY_CLAUDE) || '';
        if (claudeConfigKey.trim() || claudeUserKey.trim()) {
            providers.claude = {
                key: claudeConfigKey.trim() || claudeUserKey.trim(),
                source: claudeConfigKey.trim() ? 'config' : 'user',
                model: config.claudeModel || config.model || DEFAULT_CLAUDE_MODEL
            };
        }
        
        // OpenAI - config ou localStorage
        const openaiConfigKey = config.openaiKey || '';
        const openaiUserKey = localStorage.getItem(STORAGE_KEY_OPENAI) || '';
        if (openaiConfigKey.trim() || openaiUserKey.trim()) {
            providers.openai = {
                key: openaiConfigKey.trim() || openaiUserKey.trim(),
                source: openaiConfigKey.trim() ? 'config' : 'user',
                model: config.openaiModel || DEFAULT_OPENAI_MODEL
            };
        }
        
        return providers;
    }
    
    /**
     * Retourne le provider actuel avec sa clé
     */
    function getCurrentProvider() {
        const providers = getAvailableProviders();
        
        // Si un seul provider, l'utiliser
        const providerNames = Object.keys(providers);
        if (providerNames.length === 0) {
            return null;
        }
        if (providerNames.length === 1) {
            currentProvider = providerNames[0];
            return { name: currentProvider, ...providers[currentProvider] };
        }
        
        // Si deux providers, utiliser le préféré
        const savedProvider = localStorage.getItem(STORAGE_PROVIDER);
        if (savedProvider && providers[savedProvider]) {
            currentProvider = savedProvider;
        } else {
            const config = getConfig();
            currentProvider = config.defaultProvider || 'claude';
        }
        
        return { name: currentProvider, ...providers[currentProvider] };
    }
    
    function setProvider(providerName) {
        const providers = getAvailableProviders();
        if (providers[providerName]) {
            currentProvider = providerName;
            localStorage.setItem(STORAGE_PROVIDER, providerName);
            updateProviderSwitch();
            
            // Rafraîchir le welcome message si la conversation est vide
            if (conversationHistory.length === 0) {
                refreshWelcomeMessage();
            }
            
            return true;
        }
        return false;
    }
    
    function refreshWelcomeMessage() {
        const welcome = messagesContainer?.querySelector('.chat-welcome');
        if (welcome) {
            welcome.remove();
            showWelcomeMessage();
        }
    }
    
    function saveUserApiKey(key, provider = 'claude') {
        const storageKey = provider === 'openai' ? STORAGE_KEY_OPENAI : STORAGE_KEY_CLAUDE;
        localStorage.setItem(storageKey, key);
    }
    
    function clearUserApiKey(provider = 'claude') {
        const storageKey = provider === 'openai' ? STORAGE_KEY_OPENAI : STORAGE_KEY_CLAUDE;
        localStorage.removeItem(storageKey);
    }
    
    function saveSize(width, height) {
        localStorage.setItem(STORAGE_SIZE_KEY, JSON.stringify({ width, height }));
    }
    
    function getSavedSize() {
        try {
            const saved = localStorage.getItem(STORAGE_SIZE_KEY);
            return saved ? JSON.parse(saved) : null;
        } catch {
            return null;
        }
    }
    
    // ========================================
    // ÉLÉMENTS DOM
    // ========================================
    
    let toggleBtn, modal, closeBtn, messagesContainer, input, sendBtn;
    let suggestionsBtn, suggestionsPanel, clearBtn, settingsBtn;
    let configModal, configInput, configSave, configCancel;
    let minimizeBtn, fullscreenBtn, copyBtn, questionDisplay, resizeHandle;
    let providerSwitch, providerLabel;
    
    function initDOMElements() {
        toggleBtn = document.getElementById('chatbot-toggle');
        modal = document.getElementById('chatbot-modal');
        closeBtn = document.getElementById('chatbot-close');
        messagesContainer = document.getElementById('chatbot-messages');
        input = document.getElementById('chatbot-input');
        sendBtn = document.getElementById('chatbot-send');
        suggestionsBtn = document.getElementById('chatbot-suggestions-btn');
        suggestionsPanel = document.getElementById('chatbot-suggestions-panel');
        clearBtn = document.getElementById('chatbot-clear-btn');
        settingsBtn = document.getElementById('chatbot-settings-btn');
        configModal = document.getElementById('chatbot-config-modal');
        configInput = document.getElementById('chatbot-api-key-input');
        configSave = document.getElementById('chatbot-config-save');
        configCancel = document.getElementById('chatbot-config-cancel');
        minimizeBtn = document.getElementById('chatbot-minimize');
        fullscreenBtn = document.getElementById('chatbot-fullscreen');
        copyBtn = document.getElementById('chatbot-copy-btn');
        questionDisplay = document.getElementById('chatbot-current-question');
        resizeHandle = document.getElementById('chatbot-resize-handle');
        providerSwitch = document.getElementById('chatbot-provider-switch');
        providerLabel = document.getElementById('chatbot-provider-label');
    }
    
    // ========================================
    // ÉTAT
    // ========================================
    
    let conversationHistory = [];
    let isWaiting = false;
    let isFullscreen = false;
    let isMinimized = false;
    let currentQuestion = '';
    let lastAssistantMessage = '';
    
    // ========================================
    // EXTRACTION DU CONTENU
    // ========================================
    
    function extractPageContent() {
        const config = getConfig();
        const selector = config.contentSelector || '.help-section';
        const sections = document.querySelectorAll(selector);
        let content = [];
        
        sections.forEach((section) => {
            const id = section.id || '';
            const h2 = section.querySelector('h2');
            const h3 = section.querySelector('h3');
            const title = h2?.textContent?.trim() || h3?.textContent?.trim() || 'Section';
            
            const clone = section.cloneNode(true);
            clone.querySelectorAll('img').forEach(img => {
                const alt = img.alt || '';
                if (alt) {
                    const span = document.createElement('span');
                    span.textContent = `[Image: ${alt}]`;
                    img.replaceWith(span);
                }
            });
            
            const text = clone.textContent?.replace(/\s+/g, ' ').trim();
            
            content.push({
                id: id,
                title: title,
                content: text.substring(0, 2500)
            });
        });
        
        return content;
    }
    
    function formatContentForContext() {
        const content = extractPageContent();
        return content.map(section => 
            `## ${section.title}\n[ID: ${section.id}]\n${section.content}`
        ).join('\n\n---\n\n');
    }
    
    function getSystemPrompt(pageContent) {
        const lang = document.documentElement.lang || 'fr';
        const config = getConfig();
        const assistantName = config.assistantName || 'Assistant';
        const provider = getCurrentProvider();
        const providerName = provider?.name === 'openai' ? 'ChatGPT (OpenAI)' : 'Claude (Anthropic)';
        const providers = getAvailableProviders();
        const hasSwitch = Object.keys(providers).length === 2;
        
        const selfHelp = lang === 'fr'
            ? `
INFORMATIONS SUR TOI-MÊME (réponds à ces questions directement):
- Tu es "${assistantName}", propulsé par ${providerName}
- ${hasSwitch ? 'L\'utilisateur peut basculer entre Claude et ChatGPT via le switch 🟣/🟢 sous l\'en-tête du chat' : 'Un seul LLM est configuré actuellement'}
- Raccourcis clavier: Échap (fermer), F (plein écran), C (copier la réponse)
- L'utilisateur peut configurer sa clé API via le bouton ⚙️
- Le bouton 📋 copie ta dernière réponse
- Le bouton 💡 affiche des suggestions de questions
- Double-clic sur l'en-tête = plein écran`
            : `
INFORMATION ABOUT YOURSELF (answer these questions directly):
- You are "${assistantName}", powered by ${providerName}
- ${hasSwitch ? 'The user can switch between Claude and ChatGPT via the 🟣/🟢 switch below the chat header' : 'Only one LLM is currently configured'}
- Keyboard shortcuts: Escape (close), F (fullscreen), C (copy response)
- The user can configure their API key via the ⚙️ button
- The 📋 button copies your last response
- The 💡 button shows question suggestions
- Double-click on header = fullscreen`;
        
        const basePrompt = lang === 'fr' 
            ? `Tu es ${assistantName}, un assistant spécialisé dans le logiciel Kitview pour orthodontistes.
Tu réponds UNIQUEMENT en français.
${selfHelp}

RÈGLES POUR LES QUESTIONS SUR KITVIEW:
1. Base tes réponses sur le contenu fourni ci-dessous
2. Si l'information n'est pas dans le contenu, dis-le clairement
3. Utilise des liens vers les sections avec le format [Nom de section](#id-section)
4. Sois concis et pratique

CONTENU DU MANUEL:
${pageContent}`
            : `You are ${assistantName}, an assistant specialized in Kitview software for orthodontists.
You respond ONLY in English.
${selfHelp}

RULES FOR KITVIEW QUESTIONS:
1. Base your answers on the content provided below
2. If the information is not in the content, say so clearly
3. Use links to sections with the format [Section name](#section-id)
4. Be concise and practical

MANUAL CONTENT:
${pageContent}`;
        
        return basePrompt;
    }
    
    // ========================================
    // APPEL API (CLAUDE & OPENAI)
    // ========================================
    
    async function callAPI(userMessage) {
        const provider = getCurrentProvider();
        
        if (!provider) {
            return { error: 'NO_KEY' };
        }
        
        if (provider.name === 'openai') {
            return await callOpenAI(userMessage, provider);
        } else {
            return await callClaude(userMessage, provider);
        }
    }
    
    async function callClaude(userMessage, provider) {
        const config = getConfig();
        const pageContent = formatContentForContext();
        const systemPrompt = getSystemPrompt(pageContent);
        
        const messages = [
            ...conversationHistory,
            { role: 'user', content: userMessage }
        ];
        
        try {
            const response = await fetch('https://api.anthropic.com/v1/messages', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'x-api-key': provider.key,
                    'anthropic-version': '2023-06-01',
                    'anthropic-dangerous-direct-browser-access': 'true'
                },
                body: JSON.stringify({
                    model: provider.model,
                    max_tokens: config.maxTokens || 1024,
                    system: systemPrompt,
                    messages: messages
                })
            });
            
            if (!response.ok) {
                return handleAPIError(response, provider, 'claude');
            }
            
            const data = await response.json();
            const assistantMessage = data.content[0].text;
            
            conversationHistory.push({ role: 'user', content: userMessage });
            conversationHistory.push({ role: 'assistant', content: assistantMessage });
            lastAssistantMessage = assistantMessage;
            
            return { success: true, message: assistantMessage };
            
        } catch (error) {
            console.error('[Chatbot] Erreur réseau Claude:', error);
            return { error: 'NETWORK_ERROR' };
        }
    }
    
    async function callOpenAI(userMessage, provider) {
        const config = getConfig();
        const pageContent = formatContentForContext();
        const systemPrompt = getSystemPrompt(pageContent);
        
        const messages = [
            { role: 'system', content: systemPrompt },
            ...conversationHistory,
            { role: 'user', content: userMessage }
        ];
        
        try {
            const response = await fetch('https://api.openai.com/v1/chat/completions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${provider.key}`
                },
                body: JSON.stringify({
                    model: provider.model,
                    max_tokens: config.maxTokens || 1024,
                    temperature: config.temperature || 0.3,
                    messages: messages
                })
            });
            
            if (!response.ok) {
                return handleAPIError(response, provider, 'openai');
            }
            
            const data = await response.json();
            const assistantMessage = data.choices[0].message.content;
            
            conversationHistory.push({ role: 'user', content: userMessage });
            conversationHistory.push({ role: 'assistant', content: assistantMessage });
            lastAssistantMessage = assistantMessage;
            
            return { success: true, message: assistantMessage };
            
        } catch (error) {
            console.error('[Chatbot] Erreur réseau OpenAI:', error);
            return { error: 'NETWORK_ERROR' };
        }
    }
    
    async function handleAPIError(response, provider, type) {
        const errorData = await response.json().catch(() => ({}));
        const errorMessage = errorData.error?.message || '';
        
        if (response.status === 401) {
            return { error: 'INVALID_KEY', source: provider.source, provider: type };
        }
        if (response.status === 429) {
            if (errorMessage.includes('credit') || errorMessage.includes('quota') || errorMessage.includes('exceeded')) {
                return { error: 'QUOTA_EXCEEDED', source: provider.source, provider: type };
            }
            return { error: 'RATE_LIMIT' };
        }
        if (response.status === 404) {
            return { error: 'MODEL_NOT_FOUND', model: provider.model };
        }
        
        return { error: 'API_ERROR', message: errorMessage || `HTTP ${response.status}` };
    }
    
    // ========================================
    // GESTION DES ERREURS
    // ========================================
    
    function getErrorMessage(result) {
        const lang = document.documentElement.lang || 'fr';
        const providerName = result.provider === 'openai' ? 'ChatGPT' : 'Claude';
        
        const messages = {
            fr: {
                NO_KEY: '🔑 Aucune clé API configurée. Cliquez sur ⚙️ pour ajouter votre clé.',
                INVALID_KEY: `❌ Clé API ${providerName} invalide. Vérifiez dans les paramètres (⚙️).`,
                QUOTA_EXCEEDED: `💳 Quota ${providerName} épuisé. Rechargez vos crédits.`,
                RATE_LIMIT: '⏳ Trop de requêtes. Attendez quelques secondes...',
                NETWORK_ERROR: '🌐 Erreur réseau. Vérifiez votre connexion.',
                MODEL_NOT_FOUND: `❌ Modèle introuvable: ${result.model}`,
                API_ERROR: `⚠️ Erreur API: ${result.message || 'Erreur inconnue'}`
            },
            en: {
                NO_KEY: '🔑 No API key configured. Click ⚙️ to add your key.',
                INVALID_KEY: `❌ Invalid ${providerName} API key. Check in settings (⚙️).`,
                QUOTA_EXCEEDED: `💳 ${providerName} quota exceeded. Top up your credits.`,
                RATE_LIMIT: '⏳ Too many requests. Please wait...',
                NETWORK_ERROR: '🌐 Network error. Check your connection.',
                MODEL_NOT_FOUND: `❌ Model not found: ${result.model}`,
                API_ERROR: `⚠️ API error: ${result.message || 'Unknown error'}`
            }
        };
        
        const langMessages = messages[lang] || messages.fr;
        return langMessages[result.error] || langMessages.API_ERROR;
    }
    
    // ========================================
    // SWITCH PROVIDER
    // ========================================
    
    function createProviderSwitch() {
        const providers = getAvailableProviders();
        const providerNames = Object.keys(providers);
        
        // Ne créer le switch que si les deux providers sont disponibles
        if (providerNames.length !== 2) {
            return null;
        }
        
        const container = document.createElement('div');
        container.className = 'provider-switch-container';
        container.id = 'chatbot-provider-container';
        
        const lang = document.documentElement.lang || 'fr';
        
        container.innerHTML = `
            <div class="provider-switch">
                <button class="provider-btn ${currentProvider === 'claude' ? 'active' : ''}" 
                        data-provider="claude" title="Claude (Anthropic)">
                    <span class="provider-icon">🟣</span>
                    <span class="provider-name">Claude</span>
                </button>
                <button class="provider-btn ${currentProvider === 'openai' ? 'active' : ''}" 
                        data-provider="openai" title="ChatGPT (OpenAI)">
                    <span class="provider-icon">🟢</span>
                    <span class="provider-name">GPT</span>
                </button>
            </div>
        `;
        
        // Event listeners
        container.querySelectorAll('.provider-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const provider = btn.dataset.provider;
                setProvider(provider);
                container.querySelectorAll('.provider-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
        });
        
        return container;
    }
    
    function updateProviderSwitch() {
        const container = document.getElementById('chatbot-provider-container');
        if (container) {
            container.querySelectorAll('.provider-btn').forEach(btn => {
                btn.classList.toggle('active', btn.dataset.provider === currentProvider);
            });
        }
    }
    
    function injectProviderSwitchStyles() {
        if (document.getElementById('provider-switch-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'provider-switch-styles';
        style.textContent = `
            .provider-switch-container {
                display: flex;
                justify-content: center;
                padding: 8px 12px;
                border-bottom: 1px solid var(--chatbot-border, #e5e7eb);
                background: var(--chatbot-bg-secondary, #f8fafc);
            }
            
            .provider-switch {
                display: flex;
                gap: 4px;
                background: var(--chatbot-bg, #fff);
                border-radius: 8px;
                padding: 3px;
                box-shadow: inset 0 1px 2px rgba(0,0,0,0.05);
            }
            
            .provider-btn {
                display: flex;
                align-items: center;
                gap: 4px;
                padding: 6px 12px;
                border: none;
                background: transparent;
                border-radius: 6px;
                cursor: pointer;
                transition: all 0.2s;
                font-size: 12px;
                color: var(--chatbot-text-muted, #6b7280);
            }
            
            .provider-btn:hover {
                background: var(--chatbot-bg-hover, #f1f5f9);
            }
            
            .provider-btn.active {
                background: var(--chatbot-primary, #2563eb);
                color: white;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }
            
            .provider-icon {
                font-size: 14px;
            }
            
            .provider-name {
                font-weight: 500;
            }
            
            @media (max-width: 400px) {
                .provider-name {
                    display: none;
                }
                .provider-btn {
                    padding: 6px 10px;
                }
            }
        `;
        document.head.appendChild(style);
    }
    
    // ========================================
    // FORMATAGE MARKDOWN
    // ========================================
    
    function formatMarkdown(text) {
        // Liens avec ancres
        text = text.replace(/\[([^\]]+)\]\(#([^)]+)\)/g, (match, label, anchor) => {
            return `<a href="#${anchor}" class="chat-link" onclick="document.getElementById('${anchor}')?.scrollIntoView({behavior:'smooth'})">${label}</a>`;
        });
        
        // Liens externes
        text = text.replace(/\[([^\]]+)\]\((https?:\/\/[^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>');
        
        // Gras
        text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
        
        // Italique
        text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');
        
        // Code inline
        text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
        
        // Titres
        text = text.replace(/^### (.+)$/gm, '<h5>$1</h5>');
        text = text.replace(/^## (.+)$/gm, '<h4>$1</h4>');
        
        // Listes à puces
        text = text.replace(/^- (.+)$/gm, '<li>$1</li>');
        text = text.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
        
        // Listes numérotées
        text = text.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
        
        // Paragraphes
        text = text.replace(/\n\n/g, '</p><p>');
        text = '<p>' + text + '</p>';
        text = text.replace(/<p><\/p>/g, '');
        text = text.replace(/<p>(<h[45]>)/g, '$1');
        text = text.replace(/(<\/h[45]>)<\/p>/g, '$1');
        text = text.replace(/<p>(<ul>)/g, '$1');
        text = text.replace(/(<\/ul>)<\/p>/g, '$1');
        
        return text;
    }
    
    // ========================================
    // MESSAGES
    // ========================================
    
    function addMessage(content, type) {
        const div = document.createElement('div');
        div.className = `chat-message ${type}`;
        
        if (type === 'assistant') {
            div.innerHTML = formatMarkdown(content);
            if (copyBtn) copyBtn.disabled = false;
        } else if (type === 'error') {
            div.innerHTML = `<span class="error-message">${content}</span>`;
        } else {
            div.textContent = content;
        }
        
        messagesContainer.appendChild(div);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    function showTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'chat-message assistant typing';
        indicator.id = 'typing-indicator';
        
        // Afficher le provider actuel
        const provider = getCurrentProvider();
        const providerEmoji = provider?.name === 'openai' ? '🟢' : '🟣';
        const providerName = provider?.name === 'openai' ? 'ChatGPT' : 'Claude';
        
        indicator.innerHTML = `
            <div class="typing-dots">
                <span></span><span></span><span></span>
            </div>
            <span class="typing-provider">${providerEmoji} ${providerName}</span>
        `;
        messagesContainer.appendChild(indicator);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
    
    function hideTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) indicator.remove();
    }
    
    function updateQuestionDisplay(question) {
        if (questionDisplay) {
            if (question) {
                questionDisplay.textContent = question;
                questionDisplay.title = question;
                questionDisplay.style.display = 'block';
            } else {
                questionDisplay.style.display = 'none';
            }
        }
    }
    
    function showWelcomeMessage() {
        const lang = document.documentElement.lang || 'fr';
        const config = getConfig();
        const welcome = document.createElement('div');
        welcome.className = 'chat-welcome';
        
        const assistantName = config.assistantName || 'Assistant';
        const provider = getCurrentProvider();
        const providerInfo = provider 
            ? (provider.name === 'openai' ? '🟢 ChatGPT' : '🟣 Claude')
            : '';
        
        welcome.innerHTML = lang === 'fr'
            ? `<div class="welcome-icon">👋</div>
               <h5>Bienvenue !</h5>
               <p>Je suis ${assistantName}.<br>Posez-moi vos questions sur ce contenu.</p>
               ${providerInfo ? `<small class="welcome-provider">Propulsé par ${providerInfo}</small>` : ''}`
            : `<div class="welcome-icon">👋</div>
               <h5>Welcome!</h5>
               <p>I'm ${assistantName}.<br>Ask me your questions about this content.</p>
               ${providerInfo ? `<small class="welcome-provider">Powered by ${providerInfo}</small>` : ''}`;
        
        messagesContainer.appendChild(welcome);
    }
    
    function populateSuggestions() {
        const container = suggestionsPanel?.querySelector('.suggestions-list');
        if (!container) return;
        
        container.innerHTML = '';
        const config = getConfig();
        const lang = document.documentElement.lang || 'fr';
        const suggestions = config.suggestions?.[lang] || config.suggestions?.fr || [];
        
        suggestions.forEach(suggestion => {
            const chip = document.createElement('span');
            chip.className = 'suggestion-chip';
            chip.textContent = suggestion;
            chip.onclick = () => {
                input.value = suggestion;
                suggestionsPanel.classList.remove('open');
                handleSend();
            };
            container.appendChild(chip);
        });
    }
    
    async function handleSend() {
        const message = input.value.trim();
        if (!message || isWaiting) return;
        
        input.value = '';
        currentQuestion = message;
        updateQuestionDisplay(message);
        
        const welcome = messagesContainer.querySelector('.chat-welcome');
        if (welcome) welcome.remove();
        
        addMessage(message, 'user');
        
        isWaiting = true;
        sendBtn.disabled = true;
        if (copyBtn) copyBtn.disabled = true;
        showTypingIndicator();
        
        const result = await callAPI(message);
        
        hideTypingIndicator();
        
        if (result.success) {
            addMessage(result.message, 'assistant');
        } else {
            addMessage(getErrorMessage(result), 'error');
        }
        
        isWaiting = false;
        sendBtn.disabled = false;
        input.focus();
    }
    
    function clearConversation() {
        conversationHistory = [];
        messagesContainer.innerHTML = '';
        currentQuestion = '';
        lastAssistantMessage = '';
        updateQuestionDisplay('');
        if (copyBtn) copyBtn.disabled = true;
        showWelcomeMessage();
    }
    
    // ========================================
    // FONCTIONS V3 : COPIE, FULLSCREEN, MINIMIZE
    // ========================================
    
    function copyLastResponse() {
        if (!lastAssistantMessage) return;
        
        const lang = document.documentElement.lang || 'fr';
        
        navigator.clipboard.writeText(lastAssistantMessage).then(() => {
            const originalText = copyBtn.innerHTML;
            copyBtn.innerHTML = lang === 'fr' ? '✅ Copié !' : '✅ Copied!';
            copyBtn.classList.add('copied');
            
            setTimeout(() => {
                copyBtn.innerHTML = originalText;
                copyBtn.classList.remove('copied');
            }, 2000);
        }).catch(err => {
            console.error('[Chatbot] Erreur copie:', err);
        });
    }
    
    function toggleFullscreen() {
        isFullscreen = !isFullscreen;
        modal.classList.toggle('fullscreen', isFullscreen);
        
        if (fullscreenBtn) {
            fullscreenBtn.innerHTML = isFullscreen ? '⊡' : '□';
            fullscreenBtn.title = isFullscreen 
                ? (document.documentElement.lang === 'fr' ? 'Réduire' : 'Restore')
                : (document.documentElement.lang === 'fr' ? 'Plein écran' : 'Fullscreen');
        }
    }
    
    function toggleMinimize() {
        isMinimized = !isMinimized;
        modal.classList.toggle('minimized', isMinimized);
        
        if (minimizeBtn) {
            minimizeBtn.innerHTML = isMinimized ? '▢' : '−';
            minimizeBtn.title = isMinimized
                ? (document.documentElement.lang === 'fr' ? 'Restaurer' : 'Restore')
                : (document.documentElement.lang === 'fr' ? 'Réduire' : 'Minimize');
        }
    }
    
    // ========================================
    // REDIMENSIONNEMENT
    // ========================================
    
    function initResize() {
        if (!resizeHandle || !modal) return;
        
        let isResizing = false;
        let startX, startY, startWidth, startHeight;
        
        resizeHandle.addEventListener('mousedown', (e) => {
            isResizing = true;
            startX = e.clientX;
            startY = e.clientY;
            startWidth = modal.offsetWidth;
            startHeight = modal.offsetHeight;
            
            document.body.style.userSelect = 'none';
            e.preventDefault();
        });
        
        document.addEventListener('mousemove', (e) => {
            if (!isResizing) return;
            
            const newWidth = startWidth - (e.clientX - startX);
            const newHeight = startHeight - (e.clientY - startY);
            
            if (newWidth >= 300 && newWidth <= window.innerWidth * 0.9) {
                modal.style.width = newWidth + 'px';
            }
            if (newHeight >= 400 && newHeight <= window.innerHeight * 0.9) {
                modal.style.height = newHeight + 'px';
            }
        });
        
        document.addEventListener('mouseup', () => {
            if (isResizing) {
                isResizing = false;
                document.body.style.userSelect = '';
                saveSize(modal.offsetWidth, modal.offsetHeight);
            }
        });
        
        // Restaurer la taille sauvegardée
        const savedSize = getSavedSize();
        if (savedSize) {
            modal.style.width = savedSize.width + 'px';
            modal.style.height = savedSize.height + 'px';
        }
    }
    
    // ========================================
    // CONFIG MODAL
    // ========================================
    
    function openConfigModal() {
        if (!configModal) return;
        
        const providers = getAvailableProviders();
        const lang = document.documentElement.lang || 'fr';
        
        // Mettre à jour le contenu du modal pour supporter les deux providers
        const configContent = configModal.querySelector('.config-content');
        if (configContent) {
            configContent.innerHTML = `
                <h4>${lang === 'fr' ? '🔑 Configuration API' : '🔑 API Configuration'}</h4>
                
                <div class="config-section">
                    <label>🟣 Claude (Anthropic)</label>
                    <input type="password" id="chatbot-claude-key-input" 
                           placeholder="${lang === 'fr' ? 'sk-ant-api03-...' : 'sk-ant-api03-...'}"
                           value="${providers.claude?.source === 'user' ? providers.claude.key : ''}">
                    <small>${providers.claude?.source === 'config' 
                        ? (lang === 'fr' ? '✅ Clé intégrée disponible' : '✅ Embedded key available')
                        : (lang === 'fr' ? 'Entrez votre clé Claude' : 'Enter your Claude key')}</small>
                </div>
                
                <div class="config-section">
                    <label>🟢 ChatGPT (OpenAI)</label>
                    <input type="password" id="chatbot-openai-key-input" 
                           placeholder="${lang === 'fr' ? 'sk-...' : 'sk-...'}"
                           value="${providers.openai?.source === 'user' ? providers.openai.key : ''}">
                    <small>${providers.openai?.source === 'config' 
                        ? (lang === 'fr' ? '✅ Clé intégrée disponible' : '✅ Embedded key available')
                        : (lang === 'fr' ? 'Entrez votre clé OpenAI' : 'Enter your OpenAI key')}</small>
                </div>
                
                <div class="config-actions">
                    <button id="chatbot-config-save" class="config-btn primary">
                        ${lang === 'fr' ? '💾 Sauvegarder' : '💾 Save'}
                    </button>
                    <button id="chatbot-config-cancel" class="config-btn">
                        ${lang === 'fr' ? 'Annuler' : 'Cancel'}
                    </button>
                </div>
            `;
            
            // Rebind events
            document.getElementById('chatbot-config-save')?.addEventListener('click', saveConfig);
            document.getElementById('chatbot-config-cancel')?.addEventListener('click', closeConfigModal);
        }
        
        configModal.classList.add('open');
    }
    
    function closeConfigModal() {
        configModal?.classList.remove('open');
    }
    
    function saveConfig() {
        const claudeInput = document.getElementById('chatbot-claude-key-input');
        const openaiInput = document.getElementById('chatbot-openai-key-input');
        
        if (claudeInput?.value.trim()) {
            saveUserApiKey(claudeInput.value.trim(), 'claude');
        }
        if (openaiInput?.value.trim()) {
            saveUserApiKey(openaiInput.value.trim(), 'openai');
        }
        
        closeConfigModal();
        
        // Mettre à jour le switch si nécessaire
        const providers = getAvailableProviders();
        if (Object.keys(providers).length === 2) {
            const header = document.querySelector('.chatbot-header');
            if (header && !document.getElementById('chatbot-provider-container')) {
                const switchEl = createProviderSwitch();
                if (switchEl) {
                    header.after(switchEl);
                }
            }
        }
        
        // Rafraîchir le welcome message
        clearConversation();
    }
    
    // ========================================
    // EVENT LISTENERS
    // ========================================
    
    function initEventListeners() {
        // Toggle modal
        toggleBtn?.addEventListener('click', () => {
            modal.classList.toggle('open');
            toggleBtn.classList.toggle('active');
            if (modal.classList.contains('open')) {
                input?.focus();
            }
        });
        
        // Close
        closeBtn?.addEventListener('click', () => {
            modal.classList.remove('open');
            toggleBtn.classList.remove('active');
        });
        
        // Minimize
        minimizeBtn?.addEventListener('click', toggleMinimize);
        
        // Fullscreen
        fullscreenBtn?.addEventListener('click', toggleFullscreen);
        
        // Copy
        copyBtn?.addEventListener('click', copyLastResponse);
        
        // Send
        sendBtn?.addEventListener('click', handleSend);
        input?.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSend();
            }
        });
        
        // Suggestions
        suggestionsBtn?.addEventListener('click', () => {
            suggestionsPanel.classList.toggle('open');
            if (suggestionsPanel.classList.contains('open')) {
                populateSuggestions();
            }
        });
        
        // Clear
        clearBtn?.addEventListener('click', clearConversation);
        
        // Settings
        settingsBtn?.addEventListener('click', openConfigModal);
        
        // Config modal overlay
        configModal?.querySelector('.config-overlay')?.addEventListener('click', closeConfigModal);
        
        // Raccourcis clavier
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                if (configModal?.classList.contains('open')) {
                    closeConfigModal();
                } else if (isFullscreen) {
                    toggleFullscreen();
                } else if (modal?.classList.contains('open')) {
                    modal.classList.remove('open');
                    toggleBtn.classList.remove('active');
                }
            }
            
            if (e.key === 'f' && modal?.classList.contains('open') && 
                document.activeElement !== input) {
                toggleFullscreen();
            }
            
            if (e.key === 'c' && modal?.classList.contains('open') && 
                document.activeElement !== input &&
                !window.getSelection().toString()) {
                copyLastResponse();
            }
        });
        
        // Click outside to close
        document.addEventListener('click', (e) => {
            if (modal?.classList.contains('open') && 
                !isFullscreen &&
                !modal.contains(e.target) && 
                !toggleBtn.contains(e.target)) {
                modal.classList.remove('open');
                toggleBtn.classList.remove('active');
            }
        });
        
        // Double-clic header = fullscreen
        document.getElementById('chatbot-header')?.addEventListener('dblclick', toggleFullscreen);
    }
    
    // ========================================
    // INITIALISATION
    // ========================================
    
    function init() {
        initDOMElements();
        
        if (!toggleBtn || !modal) {
            console.warn('[Chatbot] Éléments HTML non trouvés');
            return;
        }
        
        // Injecter les styles du switch provider
        injectProviderSwitchStyles();
        
        // Initialiser le provider
        getCurrentProvider();
        
        // Ajouter le switch si les deux providers sont disponibles
        const providers = getAvailableProviders();
        console.log('[Chatbot] Providers disponibles:', Object.keys(providers));
        
        if (Object.keys(providers).length === 2) {
            // Chercher le header de plusieurs façons
            const header = document.querySelector('.chatbot-header') 
                        || document.getElementById('chatbot-header')
                        || modal.querySelector('.chatbot-header, [class*="header"]');
            
            console.log('[Chatbot] Header trouvé:', header);
            
            if (header) {
                const switchEl = createProviderSwitch();
                if (switchEl) {
                    header.after(switchEl);
                    console.log('[Chatbot] Switch provider ajouté');
                }
            } else {
                // Fallback: ajouter au début du modal
                const modalContent = modal.querySelector('.chatbot-content') || modal.firstElementChild;
                if (modalContent) {
                    const switchEl = createProviderSwitch();
                    if (switchEl) {
                        modalContent.insertBefore(switchEl, modalContent.firstChild);
                        console.log('[Chatbot] Switch provider ajouté (fallback)');
                    }
                }
            }
        } else {
            console.log('[Chatbot] Switch non affiché - providers:', Object.keys(providers).length);
        }
        
        initEventListeners();
        initResize();
        showWelcomeMessage();
        
        if (copyBtn) copyBtn.disabled = true;
        
        const provider = getCurrentProvider();
        if (provider) {
            console.log(`[Chatbot] Provider actif: ${provider.name} (source: ${provider.source})`);
        } else {
            console.log('[Chatbot] Aucune clé API - configuration requise');
        }
    }
    
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
})();
