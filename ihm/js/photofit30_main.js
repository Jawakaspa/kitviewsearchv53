/*
 * photofit30_main.js V1.0.0 - 17/02/2026
 * Kitview Portrait Search - Logique principale
 *
 * ARCHITECTURE :
 *   1. Upload image (file, camera, drag & drop)
 *   2. POST /photofit/search-by-image → résultats enrichis
 *   3. Affichage : photo référence (jaune) + cards patients similaires
 *   4. Option : POST /photofit/save-prospect
 *
 * OVERRIDE CONFIG :
 *   score_min = 1 (au lieu de communb.csv)
 *   max_results = 3 (au lieu de communb.csv)
 *   → passés au serveur via FormData (overrides communb.csv côté serveur)
 */

// ═══════════════════════════════════════════════════════════════
// CONFIGURATION
// ═══════════════════════════════════════════════════════════════

const CONFIG = {
    MAX_RESULTS: 3,
    SCORE_MIN: 1,
    JPEG_QUALITY: 0.85,         // Qualité compression JPEG (0-1)
    JPEG_MAX_SIZE: 1200,        // Dimension max en pixels (largeur ou hauteur)
    COMPRESS_THRESHOLD: 200,    // Ko : skip compression si JPEG et < ce seuil
    API_BASE: '',               // même origine
    DEFAULT_BASE: 'base1964.db',
};

// État global
let STATE = {
    currentFile: null,          // Fichier image (compressé si possible)
    originalFile: null,         // Fichier original avant compression
    currentPreviewUrl: null,    // URL data: pour le preview local
    lastResponse: null,         // Dernière réponse API complète
    prospectSaved: false,       // Prospect déjà sauvegardé ?
    compressionInfo: null,      // {originalSize, compressedSize, ratio}
};


// ═══════════════════════════════════════════════════════════════
// INITIALISATION
// ═══════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initBaseSelector();
    initUpload();
    initProspectForm();
    initModal();
    initNewSearch();
    detectMobile();
    registerServiceWorker();
});


// ═══════════════════════════════════════════════════════════════
// THÈME JOUR/NUIT
// ═══════════════════════════════════════════════════════════════

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


// ═══════════════════════════════════════════════════════════════
// SÉLECTEUR DE BASE
// ═══════════════════════════════════════════════════════════════

async function initBaseSelector() {
    const selector = document.getElementById('baseSelector');
    try {
        const resp = await fetch(`${CONFIG.API_BASE}/bases`);
        const data = await resp.json();
        selector.innerHTML = '';
        for (const base of data.bases) {
            // Exclure prospects.db et photofit.db
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


// ═══════════════════════════════════════════════════════════════
// UPLOAD (fichier, caméra, drag & drop)
// ═══════════════════════════════════════════════════════════════

function initUpload() {
    const uploadZone = document.getElementById('uploadZone');
    const fileInput = document.getElementById('fileInput');
    const cameraInput = document.getElementById('cameraInput');

    // Clic sur bouton fichier
    fileInput.addEventListener('change', (e) => {
        if (e.target.files[0]) handleFile(e.target.files[0]);
    });

    // Clic sur bouton caméra
    cameraInput.addEventListener('change', (e) => {
        if (e.target.files[0]) handleFile(e.target.files[0]);
    });

    // Drag & drop
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


// ═══════════════════════════════════════════════════════════════
// TRAITEMENT DU FICHIER
// ═══════════════════════════════════════════════════════════════

function handleFile(file) {
    // Valider le type
    const validTypes = ['image/jpeg', 'image/png', 'image/webp', 'image/bmp'];
    if (!validTypes.includes(file.type)) {
        alert('Format non supporté. Utilisez JPG, PNG, WebP ou BMP.');
        return;
    }

    // Valider la taille (10 Mo max)
    if (file.size > 10 * 1024 * 1024) {
        alert('Image trop volumineuse (max 10 Mo).');
        return;
    }

    STATE.originalFile = file;
    STATE.prospectSaved = false;
    STATE.compressionInfo = null;

    // Skip compression si déjà JPEG et petit fichier (re-encoder gonfle)
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

    // Compresser via canvas → JPEG puis lancer la recherche
    compressImage(file).then(({ compressedFile, previewUrl }) => {
        const originalKo = (file.size / 1024).toFixed(0);
        const compressedKo = (compressedFile.size / 1024).toFixed(0);
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

        console.log(`✅ Compression: ${originalKo} Ko → ${compressedKo} Ko (-${ratio}%) [${file.name} → ${compressedFile.name}]`);
        launchSearch(compressedFile);

    }).catch(err => {
        // Fallback : utiliser le fichier original si la compression échoue
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


// ═══════════════════════════════════════════════════════════════
// COMPRESSION IMAGE (canvas → JPEG 85%)
// ═══════════════════════════════════════════════════════════════

function compressImage(file) {
    return new Promise((resolve, reject) => {
        const img = new Image();
        const url = URL.createObjectURL(file);

        img.onload = () => {
            URL.revokeObjectURL(url);

            // Calculer les dimensions réduites
            let { width, height } = img;
            const maxDim = CONFIG.JPEG_MAX_SIZE;

            if (width > maxDim || height > maxDim) {
                const ratio = Math.min(maxDim / width, maxDim / height);
                width = Math.round(width * ratio);
                height = Math.round(height * ratio);
            }

            // Dessiner sur canvas
            const canvas = document.createElement('canvas');
            canvas.width = width;
            canvas.height = height;
            const ctx = canvas.getContext('2d');
            ctx.drawImage(img, 0, 0, width, height);

            // Convertir en JPEG blob
            canvas.toBlob((blob) => {
                if (!blob) {
                    reject(new Error('Canvas toBlob a retourné null'));
                    return;
                }

                // Créer un nouveau File avec extension .jpg
                const baseName = file.name.replace(/\.[^.]+$/, '');
                const compressedFile = new File([blob], `${baseName}.jpg`, {
                    type: 'image/jpeg',
                    lastModified: Date.now(),
                });

                // Preview URL
                const previewUrl = canvas.toDataURL('image/jpeg', CONFIG.JPEG_QUALITY);

                resolve({ compressedFile, previewUrl });
            }, 'image/jpeg', CONFIG.JPEG_QUALITY);
        };

        img.onerror = () => {
            URL.revokeObjectURL(url);
            reject(new Error('Impossible de charger l\'image'));
        };

        img.src = url;
    });
}


// ═══════════════════════════════════════════════════════════════
// RECHERCHE API
// ═══════════════════════════════════════════════════════════════

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
            method: 'POST',
            body: formData,
        });

        if (!resp.ok) {
            const err = await resp.json().catch(() => ({ detail: resp.statusText }));
            throw new Error(err.detail || `Erreur ${resp.status}`);
        }

        const data = await resp.json();
        STATE.lastResponse = data;

        updateLoadingText('Résultats trouvés !', `${data.nb_resultats} portrait(s) en ${data.temps_ms}ms`);

        // Petit délai pour que le message soit visible
        setTimeout(() => showResults(data), 400);

    } catch (e) {
        showError(e.message);
    }
}

function updateLoadingText(text, detail) {
    document.getElementById('loadingText').textContent = text;
    document.getElementById('loadingDetail').textContent = detail;
}


// ═══════════════════════════════════════════════════════════════
// AFFICHAGE RÉSULTATS
// ═══════════════════════════════════════════════════════════════

function showResults(data) {
    // Photo référence
    document.getElementById('referencePhoto').src = STATE.currentPreviewUrl;

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

    document.getElementById('referenceTime').textContent =
        `${data.temps_ms}ms (API: ${data.temps_api_ms}ms) — ${STATE.originalFile.name} — ${sizeText}`;

    // Reset prospect form
    document.getElementById('saveProspectCheck').checked = false;
    document.getElementById('prospectForm').style.display = 'none';
    document.getElementById('prospectSaveStatus').textContent = '';

    // Résultats (déjà filtrés par score_min et limités par max_results côté serveur)
    let resultats = data.resultats;

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


function buildCard(result) {
    const card = document.createElement('div');
    card.className = 'patient-card';
    if (result.source === 'prospect') card.classList.add('prospect-card');

    // Score badge
    const scoreClass = result.score >= 70 ? 'score-high'
        : result.score >= 40 ? 'score-medium'
        : 'score-low';

    let html = `<div class="score-badge ${scoreClass}">${result.score}</div>`;

    // Prospect badge
    if (result.source === 'prospect') {
        html += `<div class="prospect-badge">Prospect</div>`;
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

    // Infos
    html += `<div class="card-info">`;

    const prenom = result.prenom || '';
    const nom = result.nom || '';
    if (prenom || nom) {
        html += `<div class="card-name">${escapeHtml(prenom)} ${escapeHtml(nom)}</div>`;
    }

    // Sexe + âge
    const parts = [];
    if (result.sexe) parts.push(result.sexe === 'M' ? '♂' : result.sexe === 'F' ? '♀' : result.sexe);
    if (result.age) parts.push(`${Math.round(result.age)} ans`);
    if (parts.length) {
        html += `<div class="card-gender-age">${escapeHtml(parts.join(' · '))}</div>`;
    }

    // ID
    if (result.source === 'photofit' && result.idportrait) {
        html += `<div class="card-id">ID: ${escapeHtml(result.idportrait)}</div>`;
    }

    html += `</div></div>`;  // ferme card-info + card-header

    // Pathologies / Tags
    const tags = result.source === 'prospect'
        ? (result.tags || '').split(',').filter(Boolean)
        : (result.oripathologies || '').split(',').filter(Boolean);

    if (tags.length > 0) {
        html += `<div class="card-tags">`;
        for (const tag of tags.slice(0, 6)) {
            html += `<span class="card-tag">${escapeHtml(tag.trim())}</span>`;
        }
        if (tags.length > 6) {
            html += `<span class="card-tag">+${tags.length - 6}</span>`;
        }
        html += `</div>`;
    }

    card.innerHTML = html;
    return card;
}


// ═══════════════════════════════════════════════════════════════
// PROSPECT FORM
// ═══════════════════════════════════════════════════════════════

function initProspectForm() {
    document.getElementById('saveProspectCheck').addEventListener('change', (e) => {
        document.getElementById('prospectForm').style.display = e.target.checked ? 'block' : 'none';
    });

    document.getElementById('prospectSaveBtn').addEventListener('click', saveProspect);
}

async function saveProspect() {
    if (STATE.prospectSaved) {
        alert('Ce prospect a déjà été sauvegardé.');
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

        // Embeddings depuis la dernière réponse (évite de rappeler l'API)
        formData.append('hair_embedding', JSON.stringify(STATE.lastResponse.hair_embedding));
        formData.append('face_embedding', JSON.stringify(STATE.lastResponse.face_embedding));
        formData.append('attributes', JSON.stringify(STATE.lastResponse.attributes));

        const resp = await fetch(`${CONFIG.API_BASE}/photofit/save-prospect`, {
            method: 'POST',
            body: formData,
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

    } catch (e) {
        statusEl.textContent = `❌ Erreur : ${e.message}`;
        statusEl.className = 'prospect-save-status error';
        btn.disabled = false;
        btn.textContent = '💾 Sauvegarder le prospect';
    }
}


// ═══════════════════════════════════════════════════════════════
// MODAL PHOTO
// ═══════════════════════════════════════════════════════════════

function initModal() {
    const modal = document.getElementById('photoModal');
    const overlay = document.getElementById('photoModalOverlay');
    const closeBtn = document.getElementById('photoModalClose');

    overlay.addEventListener('click', closeModal);
    closeBtn.addEventListener('click', closeModal);

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeModal();
    });

    // Clic sur la photo référence → modal
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


// ═══════════════════════════════════════════════════════════════
// NOUVELLE RECHERCHE
// ═══════════════════════════════════════════════════════════════

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

    // Reset inputs
    document.getElementById('fileInput').value = '';
    document.getElementById('cameraInput').value = '';
    document.getElementById('prospectPrenom').value = '';
    document.getElementById('prospectNom').value = '';
    document.getElementById('prospectSexe').value = '';
    document.getElementById('prospectAge').value = '';
    document.getElementById('prospectTags').value = 'prospect';

    // Afficher upload, masquer résultats
    document.getElementById('uploadZone').style.display = '';
    document.getElementById('loadingZone').style.display = 'none';
    document.getElementById('resultsZone').style.display = 'none';
}


// ═══════════════════════════════════════════════════════════════
// ÉTATS D'AFFICHAGE
// ═══════════════════════════════════════════════════════════════

function showLoading() {
    document.getElementById('uploadZone').style.display = 'none';
    document.getElementById('resultsZone').style.display = 'none';
    document.getElementById('loadingZone').style.display = 'block';
    updateLoadingText('Analyse du portrait en cours...', 'Extraction des caractéristiques faciales');
}

function showError(message) {
    document.getElementById('loadingZone').style.display = 'none';
    document.getElementById('uploadZone').style.display = '';

    alert(`Erreur : ${message}`);
}


// ═══════════════════════════════════════════════════════════════
// UTILITAIRES
// ═══════════════════════════════════════════════════════════════

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = String(str);
    return div.innerHTML;
}


// ═══════════════════════════════════════════════════════════════
// SERVICE WORKER (PWA)
// ═══════════════════════════════════════════════════════════════

function registerServiceWorker() {
    if ('serviceWorker' in navigator) {
        // Nettoyer les anciens SW enregistrés à la racine (cause du 404 /sw.js)
        navigator.serviceWorker.getRegistrations().then(registrations => {
            for (const reg of registrations) {
                if (reg.scope === `${location.origin}/`) {
                    reg.unregister().then(() => console.log('Ancien SW racine désenregistré'));
                }
            }
        });

        // Le SW est dans /ihm/js/ (cerbere range les .js là)
        // Scope limité à /ihm/js/ (impossible de remonter sans header spécial)
        navigator.serviceWorker.register('/ihm/js/sw_photofit.js')
            .then(reg => console.log('SW photofit enregistré, scope:', reg.scope))
            .catch(err => console.warn('SW photofit non enregistré:', err));
    }
}
