/*
 * sw_photofit.js V1.0.0 - 17/02/2026
 * Service Worker minimal pour Kitview Portrait Search
 * 
 * Objectif principal : permettre l'accès caméra en mode PWA
 * Cache minimal des assets statiques
 */

const CACHE_NAME = 'photofit-v1';
const ASSETS = [
    '/ihm/photofit30.html',
    '/ihm/css/photofit30.css',
    '/ihm/js/photofit30_main.js',
    '/ihm/manifest_photofit.json',
];

// Installation : cache les assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(ASSETS))
            .then(() => self.skipWaiting())
    );
});

// Activation : nettoie les anciens caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(
                keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
            )
        ).then(() => self.clients.claim())
    );
});

// Fetch : network-first pour les API, cache-first pour les assets
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // API calls → toujours réseau
    if (url.pathname.startsWith('/photofit/') || url.pathname.startsWith('/bases')) {
        event.respondWith(fetch(event.request));
        return;
    }

    // Assets → cache-first, fallback réseau
    event.respondWith(
        caches.match(event.request)
            .then(cached => cached || fetch(event.request))
    );
});
