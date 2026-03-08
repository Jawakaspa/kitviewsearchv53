/**
 * demo30_main.js V1.0.0 - 11/02/2026
 * Kitview Search - MODE DÉMO - Logique principale
 * Basé sur main_chat30.js avec simplification radicale :
 *   - Pas de sidebar
 *   - Pas de page paramètres / gear
 *   - Pas de mode classique (chat uniquement)
 *   - Zone textarea de config démo remplace la saisie
 *   - Lancement / arrêt démo depuis les boutons dédiés
 * 100% indépendant de main_chat30.js
 */

/* ═══════════════════════════════════════════════════════════════════════
   FILIGRANE, LOADING BANNER, DÉTECTION LANGUE
   → Fournis par demo30_illustrations.js (pas de duplication)
   ═══════════════════════════════════════════════════════════════════════ */

/* ═══════════════════════════════════════════════════════════════════════
   MODE DÉMO v2.0 - Cycles automatiques
   ═══════════════════════════════════════════════════════════════════════ */

function updateDemoProgress(percent) {
    const ring = document.getElementById('demoProgressRing');
    if (ring) ring.style.setProperty('--progress', percent);
    demoProgress = percent;
}

function startDemoMode() {
    if (demoMode) return;
    demoMode = true;
    const ring = document.getElementById('demoProgressRing');
    if (ring) ring.classList.add('active');
    addDebugLog('Mode démo activé', 'info');
    runDemoCycleA();
}

function stopDemoMode() {
    demoMode = false;
    demoPhase = 'idle';
    if (demoTimers.phase) { clearTimeout(demoTimers.phase); demoTimers.phase = null; }
    if (demoTimers.progress) { clearInterval(demoTimers.progress); demoTimers.progress = null; }
    const ring = document.getElementById('demoProgressRing');
    if (ring) ring.classList.remove('active');
    updateDemoProgress(0);
    addDebugLog('Mode démo désactivé', 'info');
}

function runDemoCycleA() {
    if (!demoMode) return;
    demoPhase = 'new-search';
    newSearch();
    const waitTime = (demoDuration / 10) * 1000;
    startDemoProgressAnimation(0, 10, waitTime);
    demoTimers.phase = setTimeout(() => runDemoCycleB(), waitTime);
}

function runDemoCycleB() {
    if (!demoMode) return;
    demoPhase = 'typing';

    // Récupérer exemples depuis le textarea
    const textarea = document.getElementById('demoTextarea');
    let examples = [];
    if (textarea && textarea.value.trim()) {
        examples = textarea.value.split('\n').map(e => e.trim()).filter(e => e.length > 0 && !e.startsWith('#'));
    }
    if (examples.length === 0) examples = [...DEFAULT_EXAMPLES];

    const chosen = examples[Math.floor(Math.random() * examples.length)];
    addDebugLog(`Démo: "${chosen.substring(0, 40)}..."`, 'info');

    // Afficher dans la zone de recherche bottom
    const input = elements.searchInputBottom;
    if (input) {
        input.value = chosen;
        input.dispatchEvent(new Event('input', { bubbles: true }));
    }

    const waitTime = (2 * demoDuration / 10) * 1000;
    startDemoProgressAnimation(10, 30, waitTime);
    demoTimers.phase = setTimeout(() => runDemoSearch(), waitTime);
}

function runDemoSearch() {
    if (!demoMode) return;
    demoPhase = 'searching';
    const input = elements.searchInputBottom;
    const query = input ? input.value : '';
    if (query) searchPatients(query);

    const waitTime = (7 * demoDuration / 10) * 1000;
    startDemoProgressAnimation(30, 100, waitTime);
    demoTimers.phase = setTimeout(() => decideNextDemoCycle(), waitTime);
}

function decideNextDemoCycle() {
    if (!demoMode) return;
    if (Math.random() < 0.33) {
        runDemoCycleA();
    } else {
        const input = elements.searchInputBottom;
        if (input) { input.value = ''; input.dispatchEvent(new Event('input', { bubbles: true })); }
        restoreFiligraneIntensity();
        runDemoCycleB();
    }
}

function startDemoProgressAnimation(start, end, duration) {
    if (demoTimers.progress) clearInterval(demoTimers.progress);
    const t0 = Date.now();
    updateDemoProgress(start);
    demoTimers.progress = setInterval(() => {
        const p = Math.min((Date.now() - t0) / duration, 1);
        updateDemoProgress(start + (end - start) * p);
        if (p >= 1) { clearInterval(demoTimers.progress); demoTimers.progress = null; }
    }, 50);
}

/* ═══════════════════════════════════════════════════════════════════════
   CONFIGURATION & VARIABLES
   ═══════════════════════════════════════════════════════════════════════ */

const DEFAULT_EXAMPLES = [
    'patients qui grincent des dents',
    '歯ぎしり',
    'Nombre de patients avec linguo-version avec déviation maxillaire ?',
    'Number of patients with linguo-version with maxillary deviation?',
    'Patientes souffrant de béance antérieure et avec classe II',
    'Patientinnen mit Frontzahnlücke und Klasse II',
    'Patientes de moins de 39 ans présentant un encombrement et une rotation dentaire antihoraire',
    'Pazienti di età inferiore ai 39 anni con affollamento e rotazione dei denti in senso antiorario',
    'ado diabétique avec problème de bruxisme',
    'Adolescente diabético com problema de bruxismo',
    'Patientes d\'environ 14 ans avec malocclusion et bruxisme sévère',
    'Pacientes de unos 14 años con maloclusión y bruxismo severo',
    'Je voudrais les patients avec un angle ANB = 0°',
    'patients qui zozottent des dents'
];

let currentMode = 'chat'; // Toujours chat en démo
let searchMode = 'sc';
let conversationHistory = [];
let currentPage = 1;
let pageSize = 20;
let resultsLimit = 100;
let filigraneIntensity = 50;
let lastSearchCriteria = [];

// Démo
let demoMode = false;
let demoDuration = 20;
let demoTimers = { phase: null, progress: null };
let demoPhase = 'idle';
let demoProgress = 0;

let elements = null;

const SEARCH_MODE_CODES = { sc: 'SC', sp: 'SP', se: 'SE' };

/* ═══════════════════════════════════════════════════════════════════════
   CRITÈRES
   ═══════════════════════════════════════════════════════════════════════ */

function isMatchingCriteria(text) {
    if (!lastSearchCriteria || lastSearchCriteria.length === 0) return false;
    const tl = text.toLowerCase().trim();
    for (const c of lastSearchCriteria) {
        if (c.canonique && tl.includes(c.canonique.toLowerCase())) return true;
        if (c.label && tl.includes(c.label.toLowerCase())) return true;
        if (c.adjectifs && Array.isArray(c.adjectifs)) {
            for (const adj of c.adjectifs) {
                const at = (typeof adj === 'object') ? adj.canonique : adj;
                if (at && tl.includes(at.toLowerCase())) return true;
            }
        }
    }
    return false;
}

/* ═══════════════════════════════════════════════════════════════════════
   PAGINATION
   ═══════════════════════════════════════════════════════════════════════ */

/* formatPaginationMessage, getNextPageText → fournis par demo30_i18n.js */

async function loadMorePatientsFromServer(btn, convItem, patientsContainer, countDiv, offset, descFiltres, effLang) {
    btn.disabled = true;
    btn.textContent = '...';
    const sessionId = convItem.response?.session_id || convItem.session_id;
    
    try {
        let data;
        if (sessionId) {
            const resp = await fetch(`${API_BASE_URL}/search/page?session_id=${sessionId}&offset=${offset}&limit=${pageSize}`);
            if (resp.ok) {
                data = await resp.json();
            }
        }
        
        if (!data) {
            // Fallback: full search
            const payload = { question: convItem.query, base: convItem.base || currentBase,
                mode_detection: convItem.moteur || detectionMode, mode_recherche: 'sc',
                offset: offset, limit: pageSize };
            const resp2 = await fetch(`${API_BASE_URL}/search`, {
                method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload)
            });
            data = await resp2.json();
        }

        const newPatients = data.patients || [];
        const portraitScores = data.portrait_scores || convItem.response?.portrait_scores || null;
        
        newPatients.forEach(p => {
            if (portraitScores && p.idportrait && portraitScores[String(p.idportrait)] !== undefined) {
                p.similarity_score = portraitScores[String(p.idportrait)];
            }
            patientsContainer.appendChild(createPatientElement(p));
        });

        const finalOffset = offset + newPatients.length;
        btn.dataset.currentOffset = finalOffset.toString();
        btn.disabled = false;
        btn.textContent = getNextPageText(effLang);
        countDiv.textContent = formatPaginationMessage(finalOffset, convItem.response.nb_patients, descFiltres, effLang);

        if (finalOffset >= convItem.response.nb_patients) {
            btn.style.display = 'none';
            countDiv.textContent = formatPaginationMessage(finalOffset, convItem.response.nb_patients, descFiltres, effLang, true);
        }
    } catch (err) {
        console.error('Erreur pagination:', err);
        btn.disabled = false;
        btn.textContent = '↻';
    }
}

/* ═══════════════════════════════════════════════════════════════════════
   SETTINGS (simplifié pour démo)
   ═══════════════════════════════════════════════════════════════════════ */

function parseExamples(rawValue) {
    if (!rawValue) return DEFAULT_EXAMPLES;
    try {
        const p = JSON.parse(rawValue);
        if (Array.isArray(p) && p.length > 0) return p;
    } catch (e) {}
    const lines = rawValue.split('\n').map(l => l.trim()).filter(l => l.length > 0);
    return lines.length > 0 ? lines : DEFAULT_EXAMPLES;
}

function loadSettings() {
    const theme = localStorage.getItem('theme') || 'auto';
    filigraneIntensity = parseInt(localStorage.getItem('filigraneIntensity') || '50');
    demoDuration = parseInt(localStorage.getItem('demoDuration') || '20');
    detectionMode = localStorage.getItem('detectionMode') || 'standard';
    if (detectionMode === 'traditionnel' || detectionMode === 'rapide') detectionMode = 'standard';
    if (elements.detectionModeSelector) elements.detectionModeSelector.value = detectionMode;

    resultsLimit = parseInt(localStorage.getItem('resultsLimit') || '100');
    pageSize = parseInt(localStorage.getItem('pageSize') || '20');

    applyFiligraneIntensity(filigraneIntensity);
    applyTheme(theme);

    // Charger les exemples dans le textarea
    const textarea = document.getElementById('demoTextarea');
    const saved = localStorage.getItem('searchExamples');
    const examples = parseExamples(saved);
    if (textarea) textarea.value = examples.join('\n');
}

function saveConversationHistory() {
    try {
        if (conversationHistory.length > 50) conversationHistory = conversationHistory.slice(-50);
        localStorage.setItem('conversationHistory_demo', JSON.stringify(conversationHistory));
    } catch (e) {
        console.warn('Erreur sauvegarde historique:', e);
    }
}

/* ═══════════════════════════════════════════════════════════════════════
   THÈME
   ═══════════════════════════════════════════════════════════════════════ */

function applyTheme(theme) {
    const html = document.documentElement;
    const toggle = document.getElementById('themeToggle');
    if (theme === 'dark' || (theme === 'auto' && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        html.setAttribute('data-theme', 'dark');
        if (toggle) toggle.textContent = '☀️';
    } else {
        html.removeAttribute('data-theme');
        if (toggle) toggle.textContent = '🌙';
    }
}

function toggleTheme() {
    const isDark = document.documentElement.hasAttribute('data-theme');
    if (isDark) {
        document.documentElement.removeAttribute('data-theme');
        localStorage.setItem('theme', 'light');
        document.getElementById('themeToggle').textContent = '🌙';
    } else {
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
        document.getElementById('themeToggle').textContent = '☀️';
    }
}

/* ═══════════════════════════════════════════════════════════════════════
   RENDER GARDEFOU
   ═══════════════════════════════════════════════════════════════════════ */

function renderGardefouMessage(item) {
    const div = document.createElement('div');
    div.className = 'response-item';
    const queryDiv = document.createElement('div');
    queryDiv.className = 'query-text';
    queryDiv.textContent = item.query;
    div.appendChild(queryDiv);
    
    const resp = document.createElement('div');
    resp.className = 'response-text';
    resp.style.background = '#fff3e0';
    resp.style.border = '1px solid #ffb74d';
    const msg = item.response?.garde_fou_message || item.response?.message || 'Question non liée à l\'orthodontie';
    resp.innerHTML = `<div style="padding:10px;font-size:14px;">⚠️ ${msg}</div>`;
    div.appendChild(resp);
    elements.resultsContainer.appendChild(div);
    
    elements.resultsContainer.classList.add('active');
    elements.welcomeContainer.style.display = 'none';
    elements.searchContainerBottom.classList.add('active');
    elements.resultsContainer.scrollTop = elements.resultsContainer.scrollHeight;
}

/* ═══════════════════════════════════════════════════════════════════════
   RENDER RESPONSE (mode Chat)
   ═══════════════════════════════════════════════════════════════════════ */

function renderResponse(item) {
    const responseDiv = document.createElement('div');
    responseDiv.className = 'response-item';

    // Question
    const queryDiv = document.createElement('div');
    queryDiv.className = 'query-text';
    queryDiv.textContent = item.query;
    const metaSmall = document.createElement('div');
    metaSmall.style.cssText = 'font-size:11px;color:#333;margin-top:6px;font-weight:400;';
    metaSmall.textContent = `${item.base || currentBase} / ${item.moteur || detectionMode}`;
    queryDiv.appendChild(metaSmall);
    responseDiv.appendChild(queryDiv);

    // Response
    const responseTextDiv = document.createElement('div');
    responseTextDiv.className = 'response-text';

    const nbTotal = item.response.nb_patients || 0;
    const patients = item.response.patients || [];
    const nbRetournes = item.response.nb_patients_retournes || patients.length;
    const descFiltres = item.response.description_filtres || t('critères de recherche');
    const langEffective = item.lang_detectee || item.lang || 'fr';

    let patientsContainer = null;
    const isCountOnly = nbTotal > 0 && patients.length === 0;

    if (nbTotal === 0) {
        const banner = illustrationsManager.createZeroBanner(item.query);
        responseTextDiv.appendChild(banner);
    } else if (isCountOnly) {
        const banner = illustrationsManager.createResultBanner(
            nbTotal, descFiltres, `${item.elapsedTime} ms`,
            () => {
                let q = item.query;
                [/combien\s+de\s*/gi, /nombre\s+de\s*/gi, /combien\s*/gi, /compte\s*/gi].forEach(p => { q = q.replace(p, ''); });
                q = q.replace(/^\s*(de\s*)?(patients?\s*)?(avec|ont|ayant)?\s*/gi, '').replace(/\?\s*$/, '').trim();
                if (!q) q = item.query;
                elements.searchInputBottom.value = q;
                searchPatients(q);
            },
            item.moteur
        );
        responseTextDiv.appendChild(banner);
    }

    // Lang info
    const langInfoMsg = createLangInfoMessage(item.lang_detectee, item.lang);
    if (langInfoMsg) responseTextDiv.appendChild(langInfoMsg);

    // Header meta + copier
    const headerDiv = document.createElement('div');
    headerDiv.className = 'response-header';
    const metaDiv = document.createElement('div');
    metaDiv.className = 'response-meta';
    if (nbTotal > 0 && patients.length > 0) {
        metaDiv.textContent = nbTotal > nbRetournes
            ? `${nbRetournes} / ${formatResultMessage(nbTotal, descFiltres, item.elapsedTime, langEffective)}`
            : formatResultMessage(nbTotal, descFiltres, item.elapsedTime, langEffective);
    } else {
        metaDiv.style.display = 'none';
    }
    const actionsDiv = document.createElement('div');
    actionsDiv.className = 'response-actions';
    if (nbTotal > 0) {
        const copyBtn = document.createElement('button');
        copyBtn.className = 'action-btn';
        copyBtn.textContent = `📋 ${t('Copier')}`;
        copyBtn.onclick = () => copyResponse(item, copyBtn);
        actionsDiv.appendChild(copyBtn);
    }
    headerDiv.appendChild(metaDiv);
    headerDiv.appendChild(actionsDiv);
    responseTextDiv.appendChild(headerDiv);

    // Patients grid
    if (nbTotal > 0 && patients.length > 0) {
        patientsContainer = document.createElement('div');
        patientsContainer.className = 'patients-grid-chat';

        const portraitScores = item.response.portrait_scores || null;
        const toShow = patients.slice(0, pageSize);
        toShow.forEach(p => {
            if (portraitScores && p.idportrait && portraitScores[String(p.idportrait)] !== undefined)
                p.similarity_score = portraitScores[String(p.idportrait)];
            patientsContainer.appendChild(createPatientElement(p));
        });
        responseTextDiv.appendChild(patientsContainer);

        // Pagination
        if (patients.length > pageSize || nbTotal > patients.length) {
            const pagDiv = document.createElement('div');
            pagDiv.className = 'pagination-container';
            const countDiv = document.createElement('div');
            countDiv.style.cssText = 'color:var(--text-secondary);font-size:14px;';
            countDiv.textContent = formatPaginationMessage(pageSize, nbTotal, descFiltres, langEffective);
            pagDiv.appendChild(countDiv);

            const nextBtn = document.createElement('button');
            nextBtn.className = 'search-button';
            nextBtn.style.cssText = 'width:auto;border-radius:8px;padding:10px 24px;font-size:14px;';
            nextBtn.textContent = getNextPageText(langEffective);
            nextBtn.dataset.currentOffset = pageSize.toString();
            nextBtn.onclick = async function () {
                const off = parseInt(this.dataset.currentOffset);
                const ci = conversationHistory.find(c => c.query === item.query);
                if (!ci) return;
                await loadMorePatientsFromServer(this, ci, patientsContainer, countDiv, off, descFiltres, langEffective);
            };
            pagDiv.appendChild(nextBtn);
            responseTextDiv.appendChild(pagDiv);
        }
    }

    // Rating
    if (nbTotal > 0 && item.session_id) {
        const ratingDiv = createRatingWidget(item.session_id);
        responseTextDiv.appendChild(ratingDiv);
    }

    responseDiv.appendChild(responseTextDiv);
    elements.resultsContainer.appendChild(responseDiv);

    elements.resultsContainer.classList.add('active');
    elements.welcomeContainer.style.display = 'none';
    elements.searchContainerBottom.classList.add('active');
    // Scroll to bottom
    elements.resultsContainer.scrollTop = elements.resultsContainer.scrollHeight;
}

/* ═══════════════════════════════════════════════════════════════════════
   RATING WIDGET (simplifié)
   ═══════════════════════════════════════════════════════════════════════ */

function createRatingWidget(sessionId) {
    const container = document.createElement('div');
    container.className = 'rating-container';

    const thumbUp = document.createElement('button');
    thumbUp.className = 'rating-btn';
    thumbUp.textContent = '👍';
    thumbUp.title = 'Pertinent';
    thumbUp.onclick = () => submitRating(container, sessionId, 'positive');

    const thumbDown = document.createElement('button');
    thumbDown.className = 'rating-btn';
    thumbDown.textContent = '👎';
    thumbDown.title = 'Pas pertinent';
    thumbDown.onclick = () => submitRating(container, sessionId, 'negative');

    container.appendChild(thumbUp);
    container.appendChild(thumbDown);
    return container;
}

async function submitRating(container, sessionId, rating) {
    try {
        await fetch(`${API_BASE_URL}/rating`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: sessionId, rating: rating })
        });
        container.innerHTML = `<span style="color:var(--text-muted);font-size:13px;">✅ Merci !</span>`;
    } catch (e) {
        console.error('Erreur rating:', e);
    }
}

/* ═══════════════════════════════════════════════════════════════════════
   COPY RESPONSE
   ═══════════════════════════════════════════════════════════════════════ */

async function copyResponse(item, btn) {
    try {
        const patients = item.response.patients || [];
        const lines = patients.map(p => {
            const name = `${p.oriprenom || p.prenom || ''} ${p.orinom || p.nom || ''}`.trim();
            const age = p.age ? `${Math.floor(p.age)} ans` : '';
            const sexe = p.sexe || '';
            const patho = p.oripathologies || p.pathologies || '';
            return `${name} | ${sexe} | ${age} | ${patho}`;
        });
        const text = `${item.query}\n${'─'.repeat(40)}\n${lines.join('\n')}`;
        await navigator.clipboard.writeText(text);
        if (btn) { const orig = btn.textContent; btn.textContent = '✅'; setTimeout(() => btn.textContent = orig, 2000); }
    } catch (e) { console.error('Erreur copie:', e); }
}

/* ═══════════════════════════════════════════════════════════════════════
   PATIENT CARD (Chat mode)
   ═══════════════════════════════════════════════════════════════════════ */

function createPatientElement(patient) {
    return createPatientCardChat(patient);
}

function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

function createPatientCardChat(patient) {
    const card = document.createElement('div');
    card.className = 'patient-card-chat';

    const patientId = patient.id;
    const patientFullName = (patient.oriprenom && patient.orinom)
        ? `${patient.oriprenom} ${patient.orinom}`.trim()
        : `${capitalize(patient.prenom || '')} ${capitalize(patient.nom || '')}`.trim() || 'Patient';

    if (memeState.isReference(patientId)) card.classList.add('reference-patient');

    // ID badge
    const idBadge = document.createElement('div');
    idBadge.className = 'patient-id-badge';
    idBadge.textContent = patientId;
    card.appendChild(idBadge);

    // Header
    const header = document.createElement('div');
    header.className = 'patient-card-header';

    // Photo
    const photoContainer = document.createElement('div');
    photoContainer.className = 'patient-photo-container';
    makePortraitMemeClickable(photoContainer, patientId, patientFullName);

    if (patient.portrait) {
        const photo = document.createElement('img');
        photo.className = 'patient-photo';
        photo.style.cssText = 'width:60px;height:60px;';
        photo.src = patient.portrait;
        photo.alt = patientFullName;
        photo.onerror = () => {
            const ph = createPlaceholder(patient);
            photo.parentNode.replaceChild(ph, photo);
        };
        photoContainer.appendChild(photo);
    } else {
        photoContainer.appendChild(createPlaceholder(patient));
    }
    header.appendChild(photoContainer);

    // Info
    const mainInfo = document.createElement('div');
    mainInfo.className = 'patient-info';

    const nameDiv = document.createElement('div');
    nameDiv.className = 'patient-name';
    nameDiv.textContent = patientFullName;
    makeMemeClickable(nameDiv, patientId, patientFullName, 'nom', null, 'Même nom');
    mainInfo.appendChild(nameDiv);

    const detailsDiv = document.createElement('div');
    detailsDiv.className = 'patient-details';
    if (patient.sexe) {
        const s = document.createElement('span');
        s.textContent = patient.sexe === 'F' ? '♀' : patient.sexe === 'M' ? '♂' : '';
        makeMemeClickable(s, patientId, patientFullName, 'sexe', null, 'Même sexe');
        detailsDiv.appendChild(s);
    }
    if (patient.age) {
        const a = document.createElement('span');
        a.textContent = `${Math.floor(patient.age)} ${t('ans')}`;
        makeMemeClickable(a, patientId, patientFullName, 'age', null, 'Même âge');
        detailsDiv.appendChild(a);
    }
    mainInfo.appendChild(detailsDiv);
    header.appendChild(mainInfo);
    card.appendChild(header);

    // Pathologies section with similarity score
    const pathoSource = patient.oripathologies || patient.pathologies;
    if (pathoSource) {
        const pathoSection = document.createElement('div');
        pathoSection.className = 'patient-pathologies';

        // Header: score + PATHOLOGIES label
        const pathoHeader = document.createElement('div');
        pathoHeader.style.cssText = 'display:flex;align-items:center;gap:8px;margin-bottom:4px;';

        if (patient.similarity_score != null) {
            const score = patient.similarity_score;
            const badge = document.createElement('span');
            let color, emoji;
            if (score === 100) { color = '#ffc107'; emoji = '🎯'; }
            else if (score >= 80) { color = '#28a745'; emoji = '🟢'; }
            else if (score >= 60) { color = '#17a2b8'; emoji = '🔵'; }
            else { color = '#fd7e14'; emoji = '🟠'; }
            badge.style.cssText = `background:${color};color:#fff;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:700;display:inline-flex;align-items:center;box-shadow:0 1px 3px rgba(0,0,0,0.2);cursor:default;white-space:nowrap;`;
            badge.textContent = `${emoji} ${score}%`;
            badge.title = score === 100 ? 'Portrait de référence' : `Similarité : ${score}%`;
            pathoHeader.appendChild(badge);
        }

        const label = document.createElement('div');
        label.className = 'pathologies-label';
        label.style.margin = '0';
        label.textContent = t('PATHOLOGIES');
        pathoHeader.appendChild(label);
        pathoSection.appendChild(pathoHeader);

        let pathoList = typeof pathoSource === 'string'
            ? pathoSource.split(',').map(p => p.trim()).filter(p => p)
            : Array.isArray(pathoSource) ? pathoSource : [];

        const display = createPathologiesDisplay(pathoList, patientId, patientFullName);
        pathoSection.appendChild(display);
        card.appendChild(pathoSection);
    }

    // Click to expand (simplified - toggle class)
    card.addEventListener('click', () => card.classList.toggle('expanded'));

    return card;
}

function createPlaceholder(patient) {
    const ph = document.createElement('div');
    ph.className = 'patient-photo-placeholder';
    ph.style.cssText = 'width:60px;height:60px;font-size:18px;';
    const i1 = patient.oriprenom?.[0] || patient.prenom?.[0] || '';
    const i2 = patient.orinom?.[0] || patient.nom?.[0] || '';
    ph.textContent = i1.toUpperCase() + i2.toUpperCase();
    return ph;
}

/* ═══════════════════════════════════════════════════════════════════════
   PATHOLOGIES DISPLAY (groupé par tag)
   ═══════════════════════════════════════════════════════════════════════ */

function createPathologiesDisplay(pathoList, patientId, patientName) {
    const container = document.createElement('div');
    container.className = 'pathologies-tags';
    const groupes = new Map();
    const tagsSeuls = new Set();

    pathoList.forEach(patho => {
        const mots = patho.trim().split(/\s+/);
        if (mots.length === 0) return;
        const tag = mots[0].toLowerCase();
        if (mots.length === 1) {
            if (!groupes.has(tag)) tagsSeuls.add(tag);
        } else {
            tagsSeuls.delete(tag);
            if (!groupes.has(tag)) groupes.set(tag, []);
            groupes.get(tag).push({ full: patho, length: patho.length });
        }
    });

    groupes.forEach(p => p.sort((a, b) => b.length - a.length));

    const sorted = [...groupes.entries()].sort((a, b) => (b[1][0]?.length || 0) - (a[1][0]?.length || 0));

    sorted.forEach(([tag, pathos]) => {
        const tagEl = document.createElement('span');
        tagEl.className = 'patho-tag';
        tagEl.textContent = tPatho(tag);
        if (isMatchingCriteria(tag)) tagEl.classList.add('matching');
        makeMemeClickable(tagEl, patientId, patientName, 'tag', tag, `Même ${tag}`);
        container.appendChild(tagEl);

        pathos.forEach(p => {
            const el = document.createElement('span');
            el.className = 'patho-tag';
            el.style.fontWeight = '400';
            el.textContent = tPatho(p.full);
            if (isMatchingCriteria(p.full)) el.classList.add('matching');
            makeMemeClickable(el, patientId, patientName, 'pathologie', p.full.toLowerCase(), `Même ${p.full}`);
            container.appendChild(el);
        });
    });

    [...tagsSeuls].forEach(tag => {
        const el = document.createElement('span');
        el.className = 'patho-tag';
        el.textContent = tPatho(tag);
        if (isMatchingCriteria(tag)) el.classList.add('matching');
        makeMemeClickable(el, patientId, patientName, 'tag', tag, `Même ${tag}`);
        container.appendChild(el);
    });

    return container;
}

/* ═══════════════════════════════════════════════════════════════════════
   NEW SEARCH
   ═══════════════════════════════════════════════════════════════════════ */

function newSearch() {
    conversationHistory = [];
    saveConversationHistory();
    elements.resultsContainer.innerHTML = '';
    elements.resultsContainer.classList.remove('active');
    elements.searchContainerBottom.classList.remove('active');
    elements.welcomeContainer.style.display = 'flex';
    if (elements.searchInputBottom) elements.searchInputBottom.value = '';

    _forceRandomImage = true;
    updateFiligraneGhost();
    animateFiligraneFromMax();
    addDebugLog('Nouvelle recherche', 'info');
}

/* ═══════════════════════════════════════════════════════════════════════
   SEARCH BUTTON STATE
   ═══════════════════════════════════════════════════════════════════════ */

function updateSearchButtonState(input, button) {
    if (!input || !button) return;
    const hasText = input.value.trim().length > 0;
    button.disabled = !hasText;
    button.style.opacity = hasText ? '1' : '0.4';
}

function setButtonLoading(btn, isLoading) {
    if (!btn) return;
    if (isLoading) { btn.disabled = true; btn.dataset.originalText = btn.textContent; btn.innerHTML = '<span class="loading-spinner-inline"></span>'; }
    else { btn.disabled = false; btn.textContent = btn.dataset.originalText || '⬆️'; }
}

function attachInputListeners(input, button) {
    if (!input || !button) return;
    input.addEventListener('input', () => updateSearchButtonState(input, button));
    input.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && input.value.trim()) {
            e.preventDefault();
            setButtonLoading(button, true);
            searchPatients(input.value).finally(() => setButtonLoading(button, false));
        }
    });
}

/* updateBaseSubtitle → fourni par demo30_search.js */

/* ═══════════════════════════════════════════════════════════════════════
   DEMO CONFIG - Gestion de la zone de configuration
   ═══════════════════════════════════════════════════════════════════════ */

/**
 * Lance la démo depuis le bouton dédié
 */
function launchDemo() {
    const configContainer = document.getElementById('demoConfigContainer');
    const stopBtn = document.getElementById('demoStopBtn');
    const launchBtn = document.getElementById('demoLaunchBtn');
    const toggle = document.getElementById('demoToggle');

    // Masquer la config, afficher le bouton stop
    if (configContainer) configContainer.style.display = 'none';
    if (launchBtn) launchBtn.style.display = 'none';
    if (stopBtn) stopBtn.style.display = 'flex';
    if (toggle) toggle.checked = true;

    startDemoMode();
}

/**
 * Arrête la démo et restaure la zone de configuration
 */
function stopDemo() {
    const configContainer = document.getElementById('demoConfigContainer');
    const stopBtn = document.getElementById('demoStopBtn');
    const launchBtn = document.getElementById('demoLaunchBtn');
    const toggle = document.getElementById('demoToggle');

    stopDemoMode();
    newSearch();

    // Restaurer la config
    if (configContainer) configContainer.style.display = '';
    if (launchBtn) launchBtn.style.display = '';
    if (stopBtn) stopBtn.style.display = 'none';
    if (toggle) toggle.checked = false;
}

/* ═══════════════════════════════════════════════════════════════════════
   INIT ELEMENTS
   ═══════════════════════════════════════════════════════════════════════ */

function initElements() {
    elements = {
        baseSelector: document.getElementById('baseSelector'),
        baseSubtitle: document.getElementById('baseSubtitle'),
        searchTitle: document.getElementById('searchTitle'),
        langButton: document.getElementById('langButton'),
        langFlag: document.getElementById('langFlag'),
        langText: document.getElementById('langText'),
        langPopup: document.getElementById('langPopup'),
        chipsContainer: document.getElementById('chipsContainer'),
        detectionModeSelector: document.getElementById('detectionModeSelector'),
        searchModeSelector: document.getElementById('searchModeSelector'),
        themeToggle: document.getElementById('themeToggle'),
        welcomeContainer: document.getElementById('welcomeContainer'),
        resultsContainer: document.getElementById('resultsContainer'),
        searchContainerBottom: document.getElementById('searchContainerBottom'),
        loading: document.getElementById('loading'),
        searchInputBottom: document.getElementById('searchInputBottom'),
        searchButtonBottom: document.getElementById('searchButtonBottom'),
        demoToggle: document.getElementById('demoToggle'),
        demoProgressRing: document.getElementById('demoProgressRing'),
        versionDisplay: document.getElementById('versionSubtitle'),
        // Demo config
        demoTextarea: document.getElementById('demoTextarea'),
        demoNameSelect: document.getElementById('demoNameSelect'),
        demoLaunchBtn: document.getElementById('demoLaunchBtn'),
        demoStopBtn: document.getElementById('demoStopBtn')
    };

    const essentiels = ['baseSelector', 'resultsContainer', 'welcomeContainer', 'loading'];
    const manquants = essentiels.filter(k => !elements[k]);
    if (manquants.length > 0) {
        console.error('⚠️ Éléments DOM manquants:', manquants);
    } else {
        console.log('✅ Éléments DOM initialisés (demo30)');
    }
}

/* ═══════════════════════════════════════════════════════════════════════
   DOMContentLoaded - INIT
   ═══════════════════════════════════════════════════════════════════════ */

window.addEventListener('DOMContentLoaded', async () => {
    initElements();
    addDebugLog('═══ demo30 - Initialisation ═══', 'info');

    // Event listeners recherche bottom
    elements.searchButtonBottom.addEventListener('click', () => {
        const q = elements.searchInputBottom.value;
        if (q.trim()) {
            setButtonLoading(elements.searchButtonBottom, true);
            searchPatients(q).finally(() => setButtonLoading(elements.searchButtonBottom, false));
        }
    });
    attachInputListeners(elements.searchInputBottom, elements.searchButtonBottom);
    updateSearchButtonState(elements.searchInputBottom, elements.searchButtonBottom);

    // Voice
    voiceSearchManager.initButtons([
        { inputId: 'searchInputBottom', buttonId: 'voiceBtnBottom' }
    ]);

    // Langue
    if (elements.langButton) elements.langButton.addEventListener('click', toggleLangPopup);
    if (typeof initResponseFrCheckbox === 'function') initResponseFrCheckbox();
    document.addEventListener('click', (e) => {
        if (elements.langPopup && elements.langPopup.style.display === 'block') {
            if (!elements.langButton.contains(e.target) && !elements.langPopup.contains(e.target))
                elements.langPopup.style.display = 'none';
        }
    });

    // Thème
    elements.themeToggle.addEventListener('click', toggleTheme);

    // Demo toggle (switch dans le header)
    if (elements.demoToggle) {
        elements.demoToggle.addEventListener('change', () => {
            if (elements.demoToggle.checked) launchDemo();
            else stopDemo();
        });
    }

    // Demo buttons
    if (elements.demoLaunchBtn) elements.demoLaunchBtn.addEventListener('click', launchDemo);
    if (elements.demoStopBtn) elements.demoStopBtn.addEventListener('click', stopDemo);

    // Mode de détection
    if (elements.detectionModeSelector) {
        elements.detectionModeSelector.addEventListener('change', () => {
            if (typeof onDetectionModeChange === 'function') onDetectionModeChange();
        });
    }

    // Charger langues actives
    await loadActiveLanguages();

    // Charger settings
    loadSettings();
    document.body.classList.add('mode-chat');

    // Régénérer les chips
    generateLangChips();
    updateBaseSubtitle();

    // Charger version serveur
    await loadServerVersion();

    // Chargement parallèle
    const [, , , ] = await Promise.all([
        loadAvailableBases(false),
        loadIAModels(),
        illustrationsManager.init(API_BASE_URL),
        loadI18n()
    ]);

    // Filigrane initial
    updateFiligraneGhost();

    // URL params
    const urlParams = new URLSearchParams(window.location.search);
    const qFromUrl = urlParams.get('q');
    if (qFromUrl) {
        if (elements.searchInputBottom) elements.searchInputBottom.value = qFromUrl;
        searchPatients(qFromUrl);
    }

    addDebugLog('demo30 prête', 'success');
});

// Écouter changement thème système
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
    const theme = localStorage.getItem('theme') || 'auto';
    if (theme === 'auto') applyTheme('auto');
});
