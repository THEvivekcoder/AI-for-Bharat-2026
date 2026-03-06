// BharatSahayak Service Worker
// Version 1.0.0

const CACHE_NAME = 'bharatsahayak-v1';
const RUNTIME_CACHE = 'bharatsahayak-runtime-v1';

// Assets to cache on install
const PRECACHE_ASSETS = [
    '/',
    '/index.html',
    '/styles.css',
    '/app.js',
    '/manifest.json',
    // Add icon paths when available
    // '/icons/icon-192x192.png',
    // '/icons/icon-512x512.png'
];

// API endpoints to cache
const API_CACHE_PATTERNS = [
    '/schemes',
    '/user/profile'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('[Service Worker] Installing...');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[Service Worker] Precaching assets');
                return cache.addAll(PRECACHE_ASSETS);
            })
            .then(() => {
                console.log('[Service Worker] Skip waiting');
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('[Service Worker] Precaching failed:', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('[Service Worker] Activating...');
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((cacheName) => {
                            return cacheName !== CACHE_NAME && cacheName !== RUNTIME_CACHE;
                        })
                        .map((cacheName) => {
                            console.log('[Service Worker] Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        })
                );
            })
            .then(() => {
                console.log('[Service Worker] Claiming clients');
                return self.clients.claim();
            })
    );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip cross-origin requests
    if (url.origin !== location.origin) {
        return;
    }
    
    // Handle API requests differently
    if (isAPIRequest(request)) {
        event.respondWith(networkFirstStrategy(request));
    } else {
        event.respondWith(cacheFirstStrategy(request));
    }
});

// Cache-first strategy (for static assets)
async function cacheFirstStrategy(request) {
    try {
        const cachedResponse = await caches.match(request);
        
        if (cachedResponse) {
            console.log('[Service Worker] Serving from cache:', request.url);
            return cachedResponse;
        }
        
        console.log('[Service Worker] Fetching from network:', request.url);
        const networkResponse = await fetch(request);
        
        // Cache successful responses
        if (networkResponse && networkResponse.status === 200) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.error('[Service Worker] Fetch failed:', error);
        
        // Return offline page if available
        const offlinePage = await caches.match('/offline.html');
        if (offlinePage) {
            return offlinePage;
        }
        
        // Return a basic offline response
        return new Response('Offline - Please check your internet connection', {
            status: 503,
            statusText: 'Service Unavailable',
            headers: new Headers({
                'Content-Type': 'text/plain'
            })
        });
    }
}

// Network-first strategy (for API requests)
async function networkFirstStrategy(request) {
    try {
        console.log('[Service Worker] Network first for:', request.url);
        const networkResponse = await fetch(request);
        
        // Cache successful GET requests
        if (request.method === 'GET' && networkResponse && networkResponse.status === 200) {
            const cache = await caches.open(RUNTIME_CACHE);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.log('[Service Worker] Network failed, trying cache:', request.url);
        
        // Try to serve from cache
        const cachedResponse = await caches.match(request);
        
        if (cachedResponse) {
            console.log('[Service Worker] Serving API from cache:', request.url);
            return cachedResponse;
        }
        
        // Return error response
        return new Response(JSON.stringify({
            error: 'Offline',
            message: 'No internet connection and no cached data available'
        }), {
            status: 503,
            statusText: 'Service Unavailable',
            headers: new Headers({
                'Content-Type': 'application/json'
            })
        });
    }
}

// Check if request is an API call
function isAPIRequest(request) {
    const url = new URL(request.url);
    
    // Check if URL matches API patterns
    return API_CACHE_PATTERNS.some(pattern => url.pathname.includes(pattern));
}

// Background sync for offline actions
self.addEventListener('sync', (event) => {
    console.log('[Service Worker] Background sync:', event.tag);
    
    if (event.tag === 'sync-schemes') {
        event.waitUntil(syncSchemes());
    }
});

async function syncSchemes() {
    try {
        console.log('[Service Worker] Syncing schemes...');
        // Implement scheme sync logic here
        return Promise.resolve();
    } catch (error) {
        console.error('[Service Worker] Sync failed:', error);
        return Promise.reject(error);
    }
}

// Push notification handler
self.addEventListener('push', (event) => {
    console.log('[Service Worker] Push received');
    
    const options = {
        body: event.data ? event.data.text() : 'New update available',
        icon: '/icons/icon-192x192.png',
        badge: '/icons/badge-72x72.png',
        vibrate: [200, 100, 200],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1
        },
        actions: [
            {
                action: 'explore',
                title: 'View',
                icon: '/icons/checkmark.png'
            },
            {
                action: 'close',
                title: 'Close',
                icon: '/icons/xmark.png'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification('BharatSahayak', options)
    );
});

// Notification click handler
self.addEventListener('notificationclick', (event) => {
    console.log('[Service Worker] Notification clicked:', event.action);
    
    event.notification.close();
    
    if (event.action === 'explore') {
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

// Message handler for communication with main thread
self.addEventListener('message', (event) => {
    console.log('[Service Worker] Message received:', event.data);
    
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
    
    if (event.data && event.data.type === 'CACHE_URLS') {
        event.waitUntil(
            caches.open(RUNTIME_CACHE)
                .then((cache) => cache.addAll(event.data.urls))
        );
    }
});

// Periodic background sync (if supported)
self.addEventListener('periodicsync', (event) => {
    console.log('[Service Worker] Periodic sync:', event.tag);
    
    if (event.tag === 'update-schemes') {
        event.waitUntil(updateSchemes());
    }
});

async function updateSchemes() {
    try {
        console.log('[Service Worker] Updating schemes in background...');
        // Implement periodic scheme update logic
        return Promise.resolve();
    } catch (error) {
        console.error('[Service Worker] Periodic update failed:', error);
        return Promise.reject(error);
    }
}

console.log('[Service Worker] Loaded successfully');
