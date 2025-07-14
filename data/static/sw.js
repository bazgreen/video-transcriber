// Video Transcriber PWA Service Worker
// Version 1.0.0

const CACHE_NAME = 'video-transcriber-v1.0.0';
const OFFLINE_URL = '/offline';

// Assets to cache immediately
const STATIC_CACHE_FILES = [
    '/',
    '/static/css/app.css',
    '/static/css/batch.css',
    '/static/js/app.js',
    '/static/js/batch.js',
    '/static/js/video-player.js',
    '/static/manifest.json',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png',
    '/offline'
];

// Dynamic cache for API responses and uploaded content
const DYNAMIC_CACHE_NAME = 'video-transcriber-dynamic-v1.0.0';

// Background sync tags
const SYNC_TAGS = {
    TRANSCRIPTION_QUEUE: 'transcription-queue',
    OFFLINE_SESSIONS: 'offline-sessions',
    ANALYTICS: 'analytics-sync'
};

// Install event - cache static assets
self.addEventListener('install', (event) => {
    console.log('🔧 Service Worker: Installing...');

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('📦 Service Worker: Caching static assets');
                return cache.addAll(STATIC_CACHE_FILES.map(url => new Request(url, {
                    cache: 'reload'
                })));
            })
            .then(() => {
                console.log('✅ Service Worker: Installation complete');
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('❌ Service Worker: Installation failed', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    console.log('🚀 Service Worker: Activating...');

    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== CACHE_NAME && cacheName !== DYNAMIC_CACHE_NAME) {
                            console.log('🗑️ Service Worker: Deleting old cache', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('✅ Service Worker: Activation complete');
                return self.clients.claim();
            })
    );
});

// Fetch event - implement caching strategies
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests and chrome extensions
    if (request.method !== 'GET' || url.protocol.startsWith('chrome-extension')) {
        return;
    }

    // Handle different types of requests
    if (isStaticAsset(url)) {
        event.respondWith(handleStaticAsset(request));
    } else if (isApiRequest(url)) {
        event.respondWith(handleApiRequest(request));
    } else if (isNavigationRequest(request)) {
        event.respondWith(handleNavigationRequest(request));
    } else {
        event.respondWith(handleOtherRequests(request));
    }
});

// Handle static assets with cache-first strategy
async function handleStaticAsset(request) {
    try {
        const cache = await caches.open(CACHE_NAME);
        const cachedResponse = await cache.match(request);

        if (cachedResponse) {
            return cachedResponse;
        }

        const networkResponse = await fetch(request);

        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        console.log('📦 Service Worker: Serving cached static asset for', request.url);
        const cache = await caches.open(CACHE_NAME);
        return cache.match(request);
    }
}

// Handle API requests with network-first strategy
async function handleApiRequest(request) {
    try {
        // Try network first for fresh data
        const networkResponse = await fetch(request);

        if (networkResponse.ok) {
            // Cache successful API responses
            const cache = await caches.open(DYNAMIC_CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }

        return networkResponse;
    } catch (error) {
        console.log('📡 Service Worker: Network failed, checking cache for', request.url);

        // Fallback to cache
        const cache = await caches.open(DYNAMIC_CACHE_NAME);
        const cachedResponse = await cache.match(request);

        if (cachedResponse) {
            return cachedResponse;
        }

        // Return offline indicator for API requests
        return new Response(JSON.stringify({
            error: 'Offline',
            message: 'This request requires internet connection',
            offline: true
        }), {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
        });
    }
}

// Handle navigation requests
async function handleNavigationRequest(request) {
    try {
        const networkResponse = await fetch(request);
        return networkResponse;
    } catch (error) {
        console.log('🧭 Service Worker: Navigation offline, serving cached page');

        // Try to serve cached version of requested page
        const cache = await caches.open(CACHE_NAME);
        const cachedResponse = await cache.match(request);

        if (cachedResponse) {
            return cachedResponse;
        }

        // Fallback to offline page
        return cache.match(OFFLINE_URL);
    }
}

// Handle other requests
async function handleOtherRequests(request) {
    try {
        return await fetch(request);
    } catch (error) {
        const cache = await caches.open(DYNAMIC_CACHE_NAME);
        return cache.match(request);
    }
}

// Background sync for offline functionality
self.addEventListener('sync', (event) => {
    console.log('🔄 Service Worker: Background sync triggered', event.tag);

    switch (event.tag) {
        case SYNC_TAGS.TRANSCRIPTION_QUEUE:
            event.waitUntil(processOfflineTranscriptionQueue());
            break;
        case SYNC_TAGS.OFFLINE_SESSIONS:
            event.waitUntil(syncOfflineSessions());
            break;
        case SYNC_TAGS.ANALYTICS:
            event.waitUntil(syncAnalytics());
            break;
        default:
            console.log('❓ Service Worker: Unknown sync tag', event.tag);
    }
});

// Process offline transcription queue
async function processOfflineTranscriptionQueue() {
    try {
        console.log('📋 Service Worker: Processing offline transcription queue');

        const queueData = await getFromIndexedDB('transcriptionQueue');

        if (!queueData || queueData.length === 0) {
            console.log('📋 Service Worker: No items in transcription queue');
            return;
        }

        for (const item of queueData) {
            try {
                await processTranscriptionItem(item);
                await removeFromIndexedDB('transcriptionQueue', item.id);
                console.log('✅ Service Worker: Processed transcription item', item.id);
            } catch (error) {
                console.error('❌ Service Worker: Failed to process item', item.id, error);
                // Update item with error status
                item.status = 'failed';
                item.error = error.message;
                await updateInIndexedDB('transcriptionQueue', item);
            }
        }

        // Notify clients about queue processing completion
        notifyClients({
            type: 'QUEUE_PROCESSED',
            message: 'Offline transcription queue processed'
        });

    } catch (error) {
        console.error('❌ Service Worker: Failed to process transcription queue', error);
    }
}

// Process individual transcription item
async function processTranscriptionItem(item) {
    const formData = new FormData();
    formData.append('video', item.videoBlob, item.filename);
    formData.append('session_name', item.sessionName);
    formData.append('options', JSON.stringify(item.options));
    formData.append('offline_queued', 'true');

    const response = await fetch('/upload', {
        method: 'POST',
        body: formData
    });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
}

// Sync offline sessions
async function syncOfflineSessions() {
    try {
        console.log('📊 Service Worker: Syncing offline sessions');

        const offlineSessions = await getFromIndexedDB('offlineSessions');

        for (const session of offlineSessions) {
            try {
                await uploadSession(session);
                await removeFromIndexedDB('offlineSessions', session.id);
            } catch (error) {
                console.error('❌ Service Worker: Failed to sync session', session.id, error);
            }
        }
    } catch (error) {
        console.error('❌ Service Worker: Failed to sync offline sessions', error);
    }
}

// Sync analytics data
async function syncAnalytics() {
    try {
        console.log('📈 Service Worker: Syncing analytics data');

        const analyticsData = await getFromIndexedDB('analytics');

        if (analyticsData && analyticsData.length > 0) {
            await fetch('/api/analytics/batch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(analyticsData)
            });

            await clearIndexedDBStore('analytics');
        }
    } catch (error) {
        console.error('❌ Service Worker: Failed to sync analytics', error);
    }
}

// Push notification handling
self.addEventListener('push', (event) => {
    console.log('🔔 Service Worker: Push notification received');

    const options = {
        body: 'Your video transcription is complete!',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/icon-72x72.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: 1
        },
        actions: [
            {
                action: 'view',
                title: 'View Results',
                icon: '/static/icons/view-action.png'
            },
            {
                action: 'close',
                title: 'Close',
                icon: '/static/icons/close-action.png'
            }
        ]
    };

    if (event.data) {
        const data = event.data.json();
        options.body = data.message || options.body;
        options.data = { ...options.data, ...data };
    }

    event.waitUntil(
        self.registration.showNotification('Video Transcriber', options)
    );
});

// Notification click handling
self.addEventListener('notificationclick', (event) => {
    console.log('🔔 Service Worker: Notification clicked', event.action);

    event.notification.close();

    if (event.action === 'view') {
        event.waitUntil(
            clients.openWindow('/sessions')
        );
    } else if (event.action === 'close') {
        // Just close the notification
        return;
    } else {
        // Default action - open app
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

// Utility functions
function isStaticAsset(url) {
    return url.pathname.startsWith('/static/') ||
           url.pathname.endsWith('.css') ||
           url.pathname.endsWith('.js') ||
           url.pathname.endsWith('.png') ||
           url.pathname.endsWith('.jpg') ||
           url.pathname.endsWith('.ico');
}

function isApiRequest(url) {
    return url.pathname.startsWith('/api/') ||
           url.pathname.startsWith('/upload') ||
           url.pathname.startsWith('/health');
}

function isNavigationRequest(request) {
    return request.mode === 'navigate';
}

// IndexedDB helpers
function getFromIndexedDB(storeName) {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('VideoTranscriberDB', 1);

        request.onerror = () => reject(request.error);

        request.onsuccess = () => {
            const db = request.result;
            const transaction = db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const getAllRequest = store.getAll();

            getAllRequest.onsuccess = () => resolve(getAllRequest.result);
            getAllRequest.onerror = () => reject(getAllRequest.error);
        };

        request.onupgradeneeded = () => {
            const db = request.result;
            if (!db.objectStoreNames.contains(storeName)) {
                db.createObjectStore(storeName, { keyPath: 'id', autoIncrement: true });
            }
        };
    });
}

function removeFromIndexedDB(storeName, id) {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('VideoTranscriberDB', 1);

        request.onsuccess = () => {
            const db = request.result;
            const transaction = db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const deleteRequest = store.delete(id);

            deleteRequest.onsuccess = () => resolve();
            deleteRequest.onerror = () => reject(deleteRequest.error);
        };
    });
}

function updateInIndexedDB(storeName, item) {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('VideoTranscriberDB', 1);

        request.onsuccess = () => {
            const db = request.result;
            const transaction = db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const putRequest = store.put(item);

            putRequest.onsuccess = () => resolve();
            putRequest.onerror = () => reject(putRequest.error);
        };
    });
}

function clearIndexedDBStore(storeName) {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('VideoTranscriberDB', 1);

        request.onsuccess = () => {
            const db = request.result;
            const transaction = db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const clearRequest = store.clear();

            clearRequest.onsuccess = () => resolve();
            clearRequest.onerror = () => reject(clearRequest.error);
        };
    });
}

// Notify all clients
function notifyClients(message) {
    self.clients.matchAll().then(clients => {
        clients.forEach(client => {
            client.postMessage(message);
        });
    });
}

console.log('🚀 Service Worker: Loaded successfully');
