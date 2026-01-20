// CasettaFit Service Worker - v1.1.6
const CACHE_VERSION = 'casettafit-v1.1.6';
const STATIC_CACHE = 'casettafit-static-v1.1.6';
const DYNAMIC_CACHE = 'casettafit-dynamic-v1.1.6';

// Assets to cache immediately on install (conservative approach)
const CRITICAL_ASSETS = [
  '/',
  '/static/css/custom.css',
  '/static/js/common.js',
  '/static/images/logo-white.png',
  '/static/images/icons/icon-192x192.png',
  '/static/images/icons/icon-512x512.png',
];

// Install event - cache critical assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('[SW] Caching critical assets');
        return cache.addAll(CRITICAL_ASSETS);
      })
      .then(() => {
        console.log('[SW] Install complete');
        return self.skipWaiting();
      })
      .catch((error) => {
        console.error('[SW] Install failed:', error);
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
          cacheNames.map((cacheName) => {
            // Delete old caches
            if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
              console.log('[SW] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('[SW] Activation complete');
        return self.clients.claim();
      })
  );
});

// Fetch event - serve from cache or network
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }

  // Skip cross-origin requests (except CDN assets we want to cache)
  if (url.origin !== self.location.origin && !url.hostname.includes('cdn.jsdelivr.net')) {
    return;
  }

  // Never cache authentication or API write operations
  if (url.pathname.startsWith('/auth/') || 
      url.pathname.includes('/logout') ||
      url.pathname.includes('/login')) {
    return;
  }

  // Never intercept manifest or service worker itself
  if (url.pathname === '/manifest.json' || url.pathname === '/sw.js') {
    return;
  }

  // API requests - Network First (with cache fallback for GET requests)
  if (url.pathname.startsWith('/workout/api/') || 
      url.pathname.startsWith('/api/')) {
    event.respondWith(networkFirst(request));
    return;
  }

  // Static assets (CSS, JS, Images) - Cache First
  if (request.destination === 'style' || 
      request.destination === 'script' || 
      request.destination === 'image' ||
      request.destination === 'font') {
    event.respondWith(cacheFirst(request));
    return;
  }

  // HTML pages - Network First (fresher content)
  if (request.destination === 'document' || 
      request.headers.get('accept').includes('text/html')) {
    event.respondWith(networkFirst(request));
    return;
  }

  // Default: Network First
  event.respondWith(networkFirst(request));
});

// Cache First strategy (for static assets)
async function cacheFirst(request) {
  try {
    // Try cache first
    const cached = await caches.match(request);
    if (cached) {
      console.log('[SW] Serving from cache:', request.url);
      return cached;
    }

    // If not in cache, fetch from network
    console.log('[SW] Fetching from network:', request.url);
    const response = await fetch(request);
    
    // Cache the response for next time
    if (response && response.status === 200) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    console.error('[SW] Cache First failed:', error);
    // Try cache as last resort
    const cached = await caches.match(request);
    if (cached) {
      return cached;
    }
    // Return a basic offline response
    return new Response('Offline', { 
      status: 503,
      statusText: 'Service Unavailable',
      headers: new Headers({
        'Content-Type': 'text/plain'
      })
    });
  }
}

// Network First strategy (for dynamic content)
async function networkFirst(request) {
  try {
    // Try network first
    console.log('[SW] Fetching from network:', request.url);
    const response = await fetch(request);
    
    // Cache the response if successful
    if (response && response.status === 200) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, response.clone());
    }
    
    return response;
  } catch (error) {
    console.log('[SW] Network failed, trying cache:', request.url);
    
    // If network fails, try cache
    const cached = await caches.match(request);
    if (cached) {
      console.log('[SW] Serving from cache (offline):', request.url);
      return cached;
    }
    
    // If both fail, return offline response
    console.error('[SW] Network First failed completely:', error);
    return new Response('Offline', { 
      status: 503,
      statusText: 'Service Unavailable',
      headers: new Headers({
        'Content-Type': 'text/plain'
      })
    });
  }
}

console.log('[SW] Service worker loaded');
