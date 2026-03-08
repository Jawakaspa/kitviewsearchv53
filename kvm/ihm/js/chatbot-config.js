// chatbot-config.js — Version Render/FastAPI + Local
// ⚠️  window.CHATBOT_CONFIG (pas const) — requis par chatbot.js ligne 31
// Priorité des clés : ENV_CONFIG (Render) → localStorage (local) → modale saisie

window.CHATBOT_CONFIG = {

  // ── Clés API ──────────────────────────────────────────────────────────
  // Noms lus par chatbot.js : claudeKey (l.42) et openaiKey (l.53)
  // 1. ENV_CONFIG  : injecté par server.py via /api/kvm/env-config.js (Render)
  // 2. localStorage: saisi via modale ⚙️ (local / GitHub Pages)
  get claudeKey() {
    return (window.ENV_CONFIG && window.ENV_CONFIG.claudeApiKey)
        || localStorage.getItem('chatbot_api_key_claude')
        || "";
  },
  get openaiKey() {
    return (window.ENV_CONFIG && window.ENV_CONFIG.chatgptApiKey)
        || localStorage.getItem('chatbot_api_key_openai')
        || "";
  },

  // ── Fournisseur IA préféré ────────────────────────────────────────────
  defaultProvider:   "claude",

  // ── Modèles ──────────────────────────────────────────────────────────
  claudeModel:  "claude-haiku-4-5-20251001",
  openaiModel:  "gpt-4o-mini",

  // ── Comportement ─────────────────────────────────────────────────────
  maxTokens:       1024,
  contextMaxChars: 12000,

  // ── UI ───────────────────────────────────────────────────────────────
  showSuggestions: true,
  floatingButton:  true,

  // ── Debug ────────────────────────────────────────────────────────────
  debug: false,

};

if (window.CHATBOT_CONFIG.debug) {
  const src = (window.ENV_CONFIG && window.ENV_CONFIG.claudeApiKey) ? "ENV_CONFIG (Render)"
            : localStorage.getItem('chatbot_api_key_claude')         ? "localStorage (local)"
            : "absente → modale ⚙️";
  console.log(`[KVM Chatbot] Clé Claude : ${src}`);
}
