/*
 * com_photofit.js V0.0.0 - 01/01/1970 00:00
 * Kitview Portrait Search - Logique commune
 * Partagé entre photofit31.html et pwa31.html
 *
 * FONCTIONNALITÉS :
 *   1. Upload image (file, camera, drag & drop)
 *   2. Compression JPEG côté client (canvas)
 *   3. POST /photofit/search-by-image → résultats enrichis
 *   4. POST /photofit/search-by-prospect-id → recherche via prospect existant
 *   5. Affichage cards : prénom, nom, sexe, âge, pathologies
 *   6. Suppression prospect (DELETE /photofit/prospects/{id})
 *   7. Panneau liste prospects (slide-in)
 *   8. Sauvegarde prospect (POST /photofit/save-prospect)
 *   9. Modal photo plein écran
 *
 * CONFIG OVERRIDE (côté serveur) :
 *   score_min = 1, max_results = 3
 */

/*═══════════════════════════════════════════════════════════════
   CONFIGURATION
  ═══════════════════════════════════════════════════════════════*/

const CONFIG = {
    MAX_RESULTS: 3,
    SCORE_MIN: 1,
    JPEG_QUALITY: 0.85,
    JPEG_MAX_SIZE: 1200,
    COMPRESS_THRESHOLD: 200,    // Ko
    API_BASE: '',
    DEFAULT_BASE: 'base1964.db',
};

/* État global */
let STATE = {
    currentFile: null,
    originalFile: null,
    currentPreviewUrl: null,
    lastResponse: null,
    prospectSaved: false,
    compressionInfo: null,
    searchMode: 'upload',       // 'upload' | 'prospect'
    currentProspect: null,      // prospect source (si searchMode=prospect)
    prospectPanelOpen: false,
    prospectsList: [],
};


/*═══════════════════════════════════════════════════════════════
   INITIALISATION
  ═══════════════════════════════════════════════════════════════*/

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initBaseSelector();
    initUpload();
    initProspectForm();
    initModal();
    initNewSearch();
    initProspectPanel();
    initToastContainer();
    detectMobile();

    // PWA : enregistrer le SW seulement si la page le demande
    if (window.PHOTOFIT_PWA === true) {
        registerServiceWorker();
    }
});


/*═══════════════════════════════════════════════════════════════
   THÈME JOUR/NUIT
  ═══════════════════════════════════════════════════════════════*/

function initTheme() {
    const saved = localStorage.getItem('theme');
    const prefer = window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    const theme = saved || prefer;
    document.body.setAttribute('data-theme', theme);
    updateThemeIcon(theme);

    document.getElementById('themeToggle').addEventListener('click', () => {
        const current = document.body.getAttribute('data-theme');
        const next = current === 'dark' ? 'light' : 'dark';
        document.body.setAttribute('data-theme', next);
        localStorage.setItem('theme', next);
        updateThemeIcon(next);
    });
}

function updateThemeIcon(theme) {
    document.getElementById('themeToggle').textContent = theme === 'dark' ? '☀️' : '🌙';
}


/*═══════════════════════════════════════════════════════════════
   SÉLECTEUR DE BASE
  ═══════════════════════════════════════════════════════════════*/

async function initBaseSelector() {
    const selector = document.getElementById('baseSelector');
    try {
        const resp = await fetch(`${CONFIG.API_BASE}/bases`);
        const data = await resp.json();
        selector.innerHTML = '';
        for (const base of data.bases) {
            if (base === 'prospects.db' || base === 'photofit.db') continue;
            const opt = document.createElement('option');
            opt.value = base;
            opt.textContent = base.replace('.db', '');
            if (base === CONFIG.DEFAULT_BASE) opt.selected = true;
            selector.appendChild(opt);
        }
    } catch (e) {
        selector.innerHTML = `<option value="${CONFIG.DEFAULT_BASE}">${CONFIG.DEFAULT_BASE.replace('.db', '')}</option>`;
    }
}

function getSelectedBase() {
    return document.getElementById('baseSelector').value || CONFIG.DEFAULT_BASE;
}


/*═══════════════════════════════════════════════════════════════
   UPLOAD (fichier, caméra, drag & drop)
  ═══════════════════════════════════════════════════════════════*/

function initUpload() {
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    const cameraInput = document.getElementById('cameraInput');

    fileInput.addEventListener('change', (e) => {
        if (e.target.files[0]) handleFile(e.target.files[0]);
    });

    cameraInput.addEventListener('change', (e) => {
        if (e.target.files[0]) handleFile(e.target.files[0]);
    });

    uploadZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadZone.classList.add('drag-over');
    });

    uploadZone.addEventListener('dragleave', () => {
        uploadZone.classList.remove('drag-over');
    });

    uploadZone.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadZone.classList.remove('drag-over');
        const file = e.dataTransfer.files[0];
        if (file && file.type.startsWith('image/')) {
            handleFile(file);
        }
    });
}

function detectMobile() {
    const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
    const cameraLabel = document.getElementById('cameraBtnLabel');
    if (!isMobile && cameraLabel) {
        cameraLabel.style.display = 'none';
    }
}


/*═══════════════════════════════════════════════════════════════
   TRAITEMENT DU FICHIER
  ═══════════════════════════════════════════════════════════════*/

function handleFile(file) {
    const validTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/bmp'];
    if (!validTypes.includes(file.type)) {
        showToast('Format non supporté. Utilisez JPG, PNG, WebP ou BMP.', 'error');
        return;
    }

    if (file.size > 10 * 1024 * 1024) {
        showToast('Image trop volumineuse (max 10 Mo).', 'error');
        return;
    }

    STATE.originalFile = file;
    STATE.prospectSaved = false;
    STATE.compressionInfo = null;
    STATE.searchMode = 'upload';
    STATE.currentProspect = null;

    const isJpeg = (file.type === 'image/jpeg');
    const isSmall = (file.size < CONFIG.COMPRESS_THRESHOLD * 1024);

    if (isJpeg && isSmall) {
        console.log(`⏭️ Compression ignorée : JPEG ${(file.size/1024).toFixed(0)} Ko < ${CONFIG.COMPRESS_THRESHOLD} Ko`);
        STATE.currentFile = file;
        STATE.compressionInfo = { originalSize: file.size, compressedSize: file.size, originalName: file.name, compressedName: file.name, skipped: true };
        const reader = new FileReader();
        reader.onload = (e) => {
            STATE.currentPreviewUrl = e.target.result;
            launchSearch(file);
        };
        reader.readAsDataURL(file);
        return;
    }

    compressImage(file).then(({ compressedFile, previewUrl }) => {
        const ratio = ((1 - compressedFile.size / file.size) * 100).toFixed(0);
        STATE.currentFile = compressedFile;
        STATE.currentPreviewUrl = previewUrl;
        STATE.compressionInfo = {
            originalSize: file.size,
            compressedSize: compressedFile.size,
            originalName: file.name,
            compressedName: compressedFile.name,
            skipped: false,
        };
        console.log(`✅ Compression: ${(file.size/1024).toFixed(0)} Ko → ${(compressedFile.size/1024).toFixed(0)} Ko (-${ratio}%)`);
        launchSearch(compressedFile);
    }).catch(err => {
        console.warn('⚠️ Compression échouée, utilisation de l\'original:', err);
        STATE.currentFile = file;
        STATE.compressionInfo = { originalSize: file.size, compressedSize: file.size, originalName: file.name, compressedName: file.name, skipped: false };
        const reader = new FileReader();
        reader.onload = (e) => {
            STATE.currentPreviewUrl = e.target.result;
            launchSearch(file);
        };
        reader.readAsDataURL(file);
    });
}


/*═══════════════════════════════════════════════════════════════
   COMPRESSION IMAGE (canvas → JPEG)
  ═══════════════════════════════════════════════════════════════*/

function compressImage(file) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        const url = URL.createObjectURL(file);

        img.onload = () => {
            URL.revokeObjectURL(url);
            let { width, height } = img;
            const maxDim = CONFIG.JPEG_MAX_SIZE;

            if (width > maxDim || height > maxDim) {
                const ratio = Math.min(maxDim / width, maxDim / height);
                width = Math.round(width * ratio);
                height = Math.round(height * ratio);
            }

            const canvas = document.createElement('canvas');
            canvas.width = width;
            canvas.height = height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, width, height);

            canvas.toBlob((blob) => {
                if (!blob) { reject(new Error('Canvas toBlob null')); return; }
                const baseName = file.name.replace(/\.[^.]+$/, '');
                const compressedFile = new File([blob], `${baseName}.jpg`, {
                    type: 'image/jpeg', lastModified: Date.now(),
                });
                const previewUrl = canvas.toDataURL('image/jpeg', CONFIG.JPEG_QUALITY);
                resolve({ compressedFile, previewUrl });
            }, 'image/jpeg', CONFIG.JPEG_QUALITY);
        };

        img.onerror = () => { URL.revokeObjectURL(url); reject(new Error('Chargement image échoué')); };
        img.src = url;
    });
}


/*═══════════════════════════════════════════════════════════════
   RECHERCHE API (par image uploadée)
  ═══════════════════════════════════════════════════════════════*/

async function launchSearch(file) {
    showLoading();

    const formData = new FormData();
    formData.append('img', file);
    formData.append('base', getSelectedBase());
    formData.append('score_min', CONFIG.SCORE_MIN);
    formData.append('max_results', CONFIG.MAX_RESULTS);

    try {
        updateLoadingText('Analyse du portrait en cours...', 'Extraction des caractéristiques faciales via Photofit');

        const resp = await fetch(`${CONFIG.API_BASE}/photofit/search-by-image`, {
            method: 'POST', body: formData,
        });

        if (!resp.ok) {
            const err = await resp.json().catch(() => ({ detail: resp.statusText }));
            throw new Error(err.detail || `Erreur ${resp.status}`);
        }

        const data = await resp.json();
        STATE.lastResponse = data;

        updateLoadingText('Résultats trouvés !', `${data.nb_resultats} portrait(s) en ${data.temps_ms}ms`);
        setTimeout(() => showResults(data), 400);

    } catch (e) {
        showError(e.message);
    }
}


/*═══════════════════════════════════════════════════════════════
   RECHERCHE PAR PROSPECT (pas d'appel API Photofit)
  ═══════════════════════════════════════════════════════════════*/

async function launchSearchByProspect(prospect) {
    STATE.searchMode = 'prospect';
    STATE.currentProspect = prospect;
    STATE.currentPreviewUrl = prospect.photo_url;
    STATE.prospectSaved = false;
    STATE.compressionInfo = null;
    STATE.originalFile = null;
    STATE.currentFile = null;

    closeProspectPanel();
    showLoading();

    const formData = new FormData();
    formData.append('prospect_id', prospect.id);
    formData.append('base', getSelectedBase());
    formData.append('score_min', CONFIG.SCORE_MIN);
    formData.append('max_results', CONFIG.MAX_RESULTS);

    try {
        updateLoadingText('Recherche par prospect...', `${prospect.prenom} ${prospect.nom} — pas d'appel API`);

        const resp = await fetch(`${CONFIG.API_BASE}/photofit/search-by-prospect-id`, {
            method: 'POST', body: formData,
        });

        if (!resp.ok) {
            const err = await resp.json().catch(() => ({ detail: resp.statusText }));
            throw new Error(err.detail || `Erreur ${resp.status}`);
        }

        const data = await resp.json();
        STATE.lastResponse = data;

        updateLoadingText('Résultats trouvés !', `${data.nb_resultats} portrait(s) en ${data.temps_ms}ms (0ms API)`);
        setTimeout(() => showResults(data), 400);

    } catch (e) {
        showError(e.message);
    }
}


function updateLoadingText(text, detail) {
    document.getElementById('loadingText').textContent = text;
    document.getElementById('loadingDetail').textContent = detail;
}


/*═══════════════════════════════════════════════════════════════
   AFFICHAGE RÉSULTATS
  ═══════════════════════════════════════════════════════════════*/

function showResults(data) {
    // Photo référence
    document.getElementById('referencePhoto').src = STATE.currentPreviewUrl;

    // Label référence selon le mode
    const refLabel = document.getElementById('referenceLabel');
    if (STATE.searchMode === 'prospect' && STATE.currentProspect) {
        refLabel.textContent = `${STATE.currentProspect.prenom} ${STATE.currentProspect.nom} (prospect)`;
    } else {
        refLabel.textContent = 'Photo uploadée';
    }

    // Infos taille et temps
    const info = STATE.compressionInfo;
    let sizeText = '';
    if (info) {
        const origKo = (info.originalSize / 1024).toFixed(0);
        if (info.skipped) {
            sizeText = `${origKo} Ko (JPEG, compression ignorée)`;
        } else if (info.originalSize !== info.compressedSize) {
            const compKo = (info.compressedSize / 1024).toFixed(0);
            const ratio = ((1 - info.compressedSize / info.originalSize) * 100).toFixed(0);
            sizeText = `${origKo} Ko → ${compKo} Ko (-${ratio}%)`;
        } else {
            sizeText = `${origKo} Ko (non compressé)`;
        }
    }

    let timeText = `${data.temps_ms}ms`;
    if (data.temps_api_ms > 0) timeText += ` (API: ${data.temps_api_ms}ms)`;
    if (STATE.originalFile) timeText += ` — ${STATE.originalFile.name}`;
    if (sizeText) timeText += ` — ${sizeText}`;

    document.getElementById('referenceTime').textContent = timeText;

    // Prospect form : cacher si recherche par prospect
    const prospectToggle = document.getElementById('prospectToggle');
    if (STATE.searchMode === 'prospect') {
        prospectToggle.style.display = 'none';
    } else {
        prospectToggle.style.display = '';
    }

    // Reset prospect form
    document.getElementById('saveProspectCheck').checked = false;
    document.getElementById('prospectForm').style.display = 'none';
    document.getElementById('prospectSaveStatus').textContent = '';

    // Résultats
    const resultats = data.resultats;

    // Header résultats
    const headerEl = document.getElementById('resultsHeader');
    if (resultats.length === 0) {
        headerEl.textContent = '🔍 Aucun portrait similaire trouvé dans la base.';
    } else {
        const nbPatients = resultats.filter(r => r.source === 'photofit').length;
        const nbProspects = resultats.filter(r => r.source === 'prospect').length;
        let msg = `🎯 ${resultats.length} portrait(s) similaire(s) trouvé(s)`;
        if (nbProspects > 0) msg += ` (${nbPatients} patient(s), ${nbProspects} prospect(s))`;
        headerEl.textContent = msg;
    }

    // Construire les cards
    const grid = document.getElementById('resultsGrid');
    grid.innerHTML = '';
    for (const r of resultats) {
        grid.appendChild(buildCard(r));
    }

    // Afficher
    document.getElementById('uploadZone').style.display = 'none';
    document.getElementById('loadingZone').style.display = 'none';
    document.getElementById('resultsZone').style.display = 'block';
}


/*═══════════════════════════════════════════════════════════════
   CONSTRUCTION D'UNE CARD
  ═══════════════════════════════════════════════════════════════*/

function buildCard(result) {
    const card = document.createElement('div');
    card.className = 'patient-card';
    if (result.source === 'prospect') {
        card.classList.add('prospect-card');
        card.dataset.prospectId = result.prospect_id;
    }

    // Score badge
    const scoreClass = result.score >= 70 ? 'score-high'
        : result.score >= 40 ? 'score-medium'
        : 'score-low';

    let html = `<div class="score-badge ${scoreClass}">${result.score}</div>`;

    // Prospect badge + delete button
    if (result.source === 'prospect') {
        html += `<div class="prospect-badge">Prospect</div>`;
        html += `<button class="card-delete-btn" title="Supprimer ce prospect" 
                         onclick="deleteProspectFromCard(event, ${result.prospect_id})">✕</button>`;
    }

    // Header (photo + infos)
    html += `<div class="card-header">`;

    // Photo
    const portraitUrl = result.portrait || result.photo_url || '';
    if (portraitUrl) {
        html += `<img class="card-photo" src="${escapeHtml(portraitUrl)}" 
                      alt="Portrait" loading="lazy"
                      onerror="this.style.display='none';this.nextElementSibling.style.display='flex'"
                      onclick="openModal('${escapeHtml(portraitUrl)}')">`;
        html += `<div class="card-photo-placeholder" style="display:none">👤</div>`;
    } else {
        html += `<div class="card-photo-placeholder">👤</div>`;
    }

    // Infos principales
    html += `<div class="card-info">`;

    // Prénom + Nom
    const prenom = result.prenom || '';
    const nom = result.nom || '';
    if (prenom || nom) {
        html += `<div class="card-name">${escapeHtml(prenom)} ${escapeHtml(nom)}</div>`;
    }

    // Sexe + âge
    const parts = [];
    if (result.sexe) parts.push(result.sexe === 'M' ? '♂ Masculin' : result.sexe === 'F' ? '♀ Féminin' : result.sexe);
    if (result.age != null && result.age > 0) parts.push(`${Math.round(result.age)} ans`);
    if (parts.length) {
        html += `<div class="card-gender-age">${escapeHtml(parts.join(' · '))}</div>`;
    }

    // ID (patients seulement)
    if (result.source === 'photofit' && result.idportrait) {
        html += `<div class="card-id">ID: ${escapeHtml(result.idportrait)}</div>`;
    }

    html += `</div></div>`;  // ferme card-info + card-header

    // Pathologies (patients) ou Tags (prospects)
    const rawTags = result.source === 'prospect'
        ? (result.tags || '')
        : (result.oripathologies || '');

    const tags = rawTags.split(',').map(t => t.trim()).filter(Boolean);

    if (tags.length > 0) {
        html += `<div class="card-tags">`;
        const maxShow = 8;
        for (const tag of tags.slice(0, maxShow)) {
            html += `<span class="card-tag">${escapeHtml(tag)}</span>`;
        }
        if (tags.length > maxShow) {
            html += `<span class="card-tag">+${tags.length - maxShow}</span>`;
        }
        html += `</div>`;
    }

    card.innerHTML = html;
    return card;
}


/*═══════════════════════════════════════════════════════════════
   SUPPRESSION PROSPECT (depuis une card résultat)
  ═══════════════════════════════════════════════════════════════*/

async function deleteProspectFromCard(event, prospectId) {
    event.stopPropagation();

    if (!confirm(`Supprimer le prospect #${prospectId} ?`)) return;

    try {
        const resp = await fetch(`${CONFIG.API_BASE}/photofit/prospects/${prospectId}`, {
            method: 'DELETE',
        });

        if (!resp.ok) {
            const err = await resp.json().catch(() => ({ detail: resp.statusText }));
            throw new Error(err.detail || `Erreur ${resp.status}`);
        }

        // Animation de suppression
        const card = document.querySelector(`.patient-card[data-prospect-id="${prospectId}"]`);
        if (card) {
            card.classList.add('deleting');
            setTimeout(() => card.remove(), 400);
        }

        showToast(`Prospect #${prospectId} supprimé`, 'success');

    } catch (e) {
        showToast(`Erreur : ${e.message}`, 'error');
    }
}


/*═══════════════════════════════════════════════════════════════
   PROSPECT FORM (sauvegarde)
  ═══════════════════════════════════════════════════════════════*/

function initProspectForm() {
    document.getElementById('saveProspectCheck').addEventListener('change', (e) => {
        document.getElementById('prospectForm').style.display = e.target.checked ? 'block' : 'none';
    });

    document.getElementById('prospectSaveBtn').addEventListener('click', saveProspect);
}

async function saveProspect() {
    if (STATE.prospectSaved) {
        showToast('Ce prospect a déjà été sauvegardé.', 'info');
        return;
    }

    const prenom = document.getElementById('prospectPrenom').value.trim();
    const nom = document.getElementById('prospectNom').value.trim();

    if (!prenom || !nom) {
        document.getElementById('prospectSaveStatus').textContent = '⚠️ Prénom et nom obligatoires';
        document.getElementById('prospectSaveStatus').className = 'prospect-save-status error';
        return;
    }

    const btn = document.getElementById('prospectSaveBtn');
    btn.disabled = true;
    btn.textContent = '⏳ Sauvegarde...';

    const statusEl = document.getElementById('prospectSaveStatus');

    try {
        const formData = new FormData();
        formData.append('img', STATE.currentFile);
        formData.append('prenom', prenom);
        formData.append('nom', nom);
        formData.append('sexe', document.getElementById('prospectSexe').value);
        const age = document.getElementById('prospectAge').value;
        if (age) formData.append('age', age);
        formData.append('tags', document.getElementById('prospectTags').value || 'prospect');

        formData.append('hair_embedding', JSON.stringify(STATE.lastResponse.hair_embedding));
        formData.append('face_embedding', JSON.stringify(STATE.lastResponse.face_embedding));
        formData.append('attributes', JSON.stringify(STATE.lastResponse.attributes));

        const resp = await fetch(`${CONFIG.API_BASE}/photofit/save-prospect`, {
            method: 'POST', body: formData,
        });

        if (!resp.ok) {
            const err = await resp.json().catch(() => ({ detail: resp.statusText }));
            throw new Error(err.detail || `Erreur ${resp.status}`);
        }

        const data = await resp.json();
        STATE.prospectSaved = true;

        statusEl.textContent = `✅ Prospect #${data.prospect.id} sauvegardé : ${data.prospect.prenom} ${data.prospect.nom}`;
        statusEl.className = 'prospect-save-status success';
        btn.textContent = '✅ Sauvegardé';

        showToast(`Prospect #${data.prospect.id} sauvegardé`, 'success');

    } catch (e) {
        statusEl.textContent = `❌ Erreur : ${e.message}`;
        statusEl.className = 'prospect-save-status error';
        btn.disabled = false;
        btn.textContent = '💾 Sauvegarder le prospect';
    }
}


/*═══════════════════════════════════════════════════════════════
   PANNEAU LISTE DES PROSPECTS
  ═══════════════════════════════════════════════════════════════*/

function initProspectPanel() {
    const toggleBtn = document.getElementById('prospectListBtn');
    if (toggleBtn) {
        toggleBtn.addEventListener('click', toggleProspectPanel);
    }

    const closeBtn = document.getElementById('prospectPanelClose');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeProspectPanel);
    }

    const overlay = document.getElementById('prospectPanelOverlay');
    if (overlay) {
        overlay.addEventListener('click', closeProspectPanel);
    }

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && STATE.prospectPanelOpen) closeProspectPanel();
    });
}

function toggleProspectPanel() {
    if (STATE.prospectPanelOpen) {
        closeProspectPanel();
    } else {
        openProspectPanel();
    }
}

async function openProspectPanel() {
    STATE.prospectPanelOpen = true;

    const panel = document.getElementById('prospectPanel');
    const overlay = document.getElementById('prospectPanelOverlay');
    panel.classList.add('open');
    overlay.classList.add('visible');

    // Charger la liste
    await loadProspectsList();
}

function closeProspectPanel() {
    STATE.prospectPanelOpen = false;

    const panel = document.getElementById('prospectPanel');
    const overlay = document.getElementById('prospectPanelOverlay');
    panel.classList.remove('open');
    overlay.classList.remove('visible');
}

async function loadProspectsList() {
    const body = document.getElementById('prospectPanelBody');
    body.innerHTML = '<div class="prospect-panel-empty">Chargement...</div>';

    try {
        const resp = await fetch(`${CONFIG.API_BASE}/photofit/prospects`);
        if (!resp.ok) throw new Error(`Erreur ${resp.status}`);

        const data = await resp.json();
        STATE.prospectsList = data.prospects || [];

        // Mettre à jour le badge compteur
        updateProspectBadge(STATE.prospectsList.length);

        if (STATE.prospectsList.length === 0) {
            body.innerHTML = '<div class="prospect-panel-empty">Aucun prospect enregistré</div>';
            return;
        }

        body.innerHTML = '';
        for (const p of STATE.prospectsList) {
            body.appendChild(buildProspectListItem(p));
        }

    } catch (e) {
        body.innerHTML = `<div class="prospect-panel-empty">❌ ${e.message}</div>`;
    }
}

function buildProspectListItem(prospect) {
    const item = document.createElement('div');
    item.className = 'prospect-list-item';
    item.dataset.prospectId = prospect.id;

    const photoUrl = prospect.photo_url || '';
    const meta = [];
    if (prospect.sexe) meta.push(prospect.sexe === 'M' ? '♂' : '♀');
    if (prospect.age) meta.push(`${Math.round(prospect.age)} ans`);
    if (prospect.created_at) meta.push(prospect.created_at.substring(0, 10));

    item.innerHTML = `
        <img class="prospect-list-photo" src="${escapeHtml(photoUrl)}" alt=""
             onerror="this.style.display='none'">
        <div class="prospect-list-info">
            <div class="prospect-list-name">${escapeHtml(prospect.prenom)} ${escapeHtml(prospect.nom)}</div>
            <div class="prospect-list-meta">${escapeHtml(meta.join(' · '))}</div>
        </div>
        <div class="prospect-list-actions">
            <button class="prospect-list-btn search-btn" title="Rechercher avec ce prospect">🔍</button>
            <button class="prospect-list-btn delete-btn" title="Supprimer">✕</button>
        </div>
    `;

    // Recherche par ce prospect
    item.querySelector('.search-btn').addEventListener('click', (e) => {
        e.stopPropagation();
        launchSearchByProspect(prospect);
    });

    // Suppression
    item.querySelector('.delete-btn').addEventListener('click', (e) => {
        e.stopPropagation();
        deleteProspectFromPanel(prospect.id, item);
    });

    return item;
}

async function deleteProspectFromPanel(prospectId, itemEl) {
    if (!confirm(`Supprimer le prospect #${prospectId} ?`)) return;

    try {
        const resp = await fetch(`${CONFIG.API_BASE}/photofit/prospects/${prospectId}`, {
            method: 'DELETE',
        });

        if (!resp.ok) {
            const err = await resp.json().catch(() => ({ detail: resp.statusText }));
            throw new Error(err.detail || `Erreur ${resp.status}`);
        }

        itemEl.classList.add('deleting');
        setTimeout(() => {
            itemEl.remove();
            // Mettre à jour le badge
            STATE.prospectsList = STATE.prospectsList.filter(p => p.id !== prospectId);
            updateProspectBadge(STATE.prospectsList.length);

            if (STATE.prospectsList.length === 0) {
                document.getElementById('prospectPanelBody').innerHTML =
                    '<div class="prospect-panel-empty">Aucun prospect enregistré</div>';
            }
        }, 350);

        // Supprimer aussi la card résultat si elle est affichée
        const card = document.querySelector(`.patient-card[data-prospect-id="${prospectId}"]`);
        if (card) {
            card.classList.add('deleting');
            setTimeout(() => card.remove(), 400);
        }

        showToast(`Prospect #${prospectId} supprimé`, 'success');

    } catch (e) {
        showToast(`Erreur : ${e.message}`, 'error');
    }
}

function updateProspectBadge(count) {
    const badge = document.getElementById('prospectBadge');
    if (!badge) return;
    if (count > 0) {
        badge.textContent = count;
        badge.style.display = 'flex';
    } else {
        badge.style.display = 'none';
    }
}


/*═══════════════════════════════════════════════════════════════
   MODAL PHOTO
  ═══════════════════════════════════════════════════════════════*/

function initModal() {
    const overlay = document.getElementById('photoModalOverlay');
    const closeBtn = document.getElementById('photoModalClose');

    overlay.addEventListener('click', closeModal);
    closeBtn.addEventListener('click', closeModal);

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !STATE.prospectPanelOpen) closeModal();
    });

    document.getElementById('referencePhoto').addEventListener('click', () => {
        openModal(STATE.currentPreviewUrl);
    });
}

function openModal(src) {
    document.getElementById('photoModalImg').src = src;
    document.getElementById('photoModal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('photoModal').style.display = 'none';
    document.getElementById('photoModalImg').src = '';
}


/*═══════════════════════════════════════════════════════════════
   NOUVELLE RECHERCHE
  ═══════════════════════════════════════════════════════════════*/

function initNewSearch() {
    document.getElementById('newSearchBtn').addEventListener('click', resetSearch);
}

function resetSearch() {
    STATE.currentFile = null;
    STATE.originalFile = null;
    STATE.currentPreviewUrl = null;
    STATE.lastResponse = null;
    STATE.prospectSaved = false;
    STATE.compressionInfo = null;
    STATE.searchMode = 'upload';
    STATE.currentProspect = null;

    document.getElementById('fileInput').value = '';
    document.getElementById('cameraInput').value = '';
    document.getElementById('prospectPrenom').value = '';
    document.getElementById('prospectNom').value = '';
    document.getElementById('prospectSexe').value = '';
    document.getElementById('prospectAge').value = '';
    document.getElementById('prospectTags').value = 'prospect';

    const btn = document.getElementById('prospectSaveBtn');
    btn.disabled = false;
    btn.textContent = '💾 Sauvegarder le prospect';

    document.getElementById('uploadZone').style.display = '';
    document.getElementById('loadingZone').style.display = 'none';
    document.getElementById('resultsZone').style.display = 'none';
}


/*═══════════════════════════════════════════════════════════════
   ÉTATS D'AFFICHAGE
  ═══════════════════════════════════════════════════════════════*/

function showLoading() {
    document.getElementById('uploadZone').style.display = 'none';
    document.getElementById('resultsZone').style.display = 'none';
    document.getElementById('loadingZone').style.display = 'block';
    updateLoadingText('Analyse du portrait en cours...', 'Extraction des caractéristiques faciales');
}

function showError(message) {
    document.getElementById('loadingZone').style.display = 'none';
    document.getElementById('uploadZone').style.display = '';
    showToast(`Erreur : ${message}`, 'error');
}


/*═══════════════════════════════════════════════════════════════
   TOAST NOTIFICATIONS
  ═══════════════════════════════════════════════════════════════*/

function initToastContainer() {
    if (!document.getElementById('toastContainer')) {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
}

function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}


/*═══════════════════════════════════════════════════════════════
   UTILITAIRES
  ═══════════════════════════════════════════════════════════════*/

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = String(str);
    return div.innerHTML;
}


/*═══════════════════════════════════════════════════════════════
   SERVICE WORKER (PWA)
  ═══════════════════════════════════════════════════════════════*/

function registerServiceWorker() {
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.getRegistrations().then(registrations => {
            for (const reg of registrations) {
                if (reg.scope === `${location.origin}/`) {
                    reg.unregister().then(() => console.log('Ancien SW racine désenregistré'));
                }
            }
        });

        navigator.serviceWorker.register('/ihm/js/sw_photofit.js')
            .then(reg => console.log('SW photofit enregistré, scope:', reg.scope))
            .catch(err => console.warn('SW photofit non enregistré:', err));
    }
}
