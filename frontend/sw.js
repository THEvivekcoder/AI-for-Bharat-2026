// Service Worker for BharatSahayak PWA
const CACHE_VERSION = 'v1';
const CACHE_NAME = `bharatsahayak-${CACHE_VERSION}`;

// Assets to cache on install
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/css/styles.css',
  '/js/app.js',
  '/js/api.js',
  '/js/voice.js',
  '/js/chat.js',
  '/js/offline.js',
  '/icons/icon-192x192.png',
  '/icons/icon-512x512.png'
];

// API endpoints to cache (for offline support)
const API_CACHE_NAME = `bharatsahayak-api-${CACHE_VERSION}`;
const CACHEABLE_API_PATTERNS = [
  '/api/schemes',
  '/api/languages',
  '/api/health/facilities'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker...');
  
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('[SW] Service worker installed');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('[SW] Installation failed:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker...');
  
  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames
            .filter((name) => {
              return name.startsWith('bharatsahayak-') && name !== CACHE_NAME && name !== API_CACHE_NAME;
            })
            .map((name) => {
              console.log('[SW] Deleting old cache:', name);
              return caches.delete(name);
            })
        );
      })
      .then(() => {
        console.log('[SW] Service worker activated');
        return self.clients.claim();
      })
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Handle API requests
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(handleApiRequest(request));
    return;
  }

  // Handle static assets
  event.respondWith(handleStaticRequest(request));
});

// Handle static asset requests (cache-first strategy)
async function handleStaticRequest(request) {
  try {
    // Try cache first
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      console.log('[SW] Serving from cache:', request.url);
      return cachedResponse;
    }

    // Fallback to network
    console.log('[SW] Fetching from network:', request.url);
    const networkResponse = await fetch(request);

    // Cache successful responses
    if (networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.error('[SW] Fetch failed:', error);
    
    // Return offline page for navigation requests
    if (request.mode === 'navigate') {
      const cache = await caches.open(CACHE_NAME);
      return cache.match('/index.html');
    }

    throw error;
  }
}

// Handle API requests (network-first strategy with cache fallback)
async function handleApiRequest(request) {
  const url = new URL(request.url);
  const shouldCache = CACHEABLE_API_PATTERNS.some(pattern => url.pathname.startsWith(pattern));

  try {
    // Try network first
    console.log('[SW] Fetching API from network:', request.url);
    const networkResponse = await fetch(request);

    // Cache successful GET responses for cacheable endpoints
    if (networkResponse.ok && shouldCache) {
      const cache = await caches.open(API_CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }

    return networkResponse;
  } catch (error) {
    console.log('[SW] Network failed, trying cache:', request.url);

    // Fallback to cache for cacheable endpoints
    if (shouldCache) {
      const cachedResponse = await caches.match(request);
      if (cachedResponse) {
        console.log('[SW] Serving API from cache:', request.url);
        // Add custom header to indicate cached response
        const headers = new Headers(cachedResponse.headers);
        headers.set('X-From-Cache', 'true');
        return new Response(cachedResponse.body, {
          status: cachedResponse.status,
          statusText: cachedResponse.statusText,
          headers: headers
        });
      }
    }

    // Return error response
    return new Response(
      JSON.stringify({
        error: 'Network unavailable',
        message: 'Unable to fetch data. Please check your connection.',
        offline: true
      }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}

// Handle background sync
self.addEventListener('sync', (event) => {
  console.log('[SW] Background sync triggered:', event.tag);
  
  if (event.tag === 'sync-data') {
    event.waitUntil(syncData());
  }
});

// Sync cached data with server
async function syncData() {
  try {
    console.log('[SW] Syncing data with server...');
    
    // Get pending sync items from IndexedDB or cache
    // This would be implemented based on your offline data strategy
    
    // Send sync request to server
    const response = await fetch('/api/cache/sync', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ timestamp: Date.now() })
    });

    if (response.ok) {
      console.log('[SW] Data synced successfully');
      // Clear pending sync items
    } else {
      console.error('[SW] Sync failed:', response.status);
    }
  } catch (error) {
    console.error('[SW] Sync error:', error);
    throw error; // Retry sync
  }
}

// Handle push notifications (for future use)
self.addEventListener('push', (event) => {
  console.log('[SW] Push notification received');
  
  const data = event.data ? event.data.json() : {};
  const title = data.title || 'BharatSahayak';
  const options = {
    body: data.body || 'New update available',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/icon-72x72.png',
    data: data
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  console.log('[SW] Notification clicked');
  
  event.notification.close();
  
  event.waitUntil(
    clients.openWindow(event.notification.data.url || '/')
  );
});

// Message handler for communication with app
self.addEventListener('message', (event) => {
  console.log('[SW] Message received:', event.data);
  
  if (event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
  
  if (event.data.type === 'CACHE_URLS') {
    event.waitUntil(
      caches.open(CACHE_NAME).then((cache) => {
        return cache.addAll(event.data.urls);
      })
    );
  }
});
