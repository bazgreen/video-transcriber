// Video Transcriber PWA Client Library
// Handles PWA functionality, offline support, and mobile features

class VideoTranscriberPWA {
    constructor() {
        this.isOnline = navigator.onLine;
        this.installPrompt = null;
        this.registration = null;
        this.db = null;
        this.offlineQueue = [];

        this.init();
    }

    async init() {
        console.log('🚀 PWA: Initializing Video Transcriber PWA');

        // Initialize IndexedDB
        await this.initIndexedDB();

        // Register service worker
        await this.registerServiceWorker();

        // Setup event listeners
        this.setupEventListeners();

        // Setup install prompt
        this.setupInstallPrompt();

        // Initialize offline support
        this.initOfflineSupport();

        // Setup background sync
        this.setupBackgroundSync();

        // Initialize push notifications
        this.initPushNotifications();

        console.log('✅ PWA: Initialization complete');
    }

    // Service Worker Registration
    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                console.log('🔧 PWA: Registering service worker');

                this.registration = await navigator.serviceWorker.register('/static/sw.js', {
                    scope: '/'
                });

                // Handle updates
                this.registration.addEventListener('updatefound', () => {
                    const newWorker = this.registration.installing;

                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            this.showUpdateNotification();
                        }
                    });
                });

                console.log('✅ PWA: Service worker registered successfully');

                // Listen for messages from service worker
                navigator.serviceWorker.addEventListener('message', this.handleServiceWorkerMessage.bind(this));

            } catch (error) {
                console.error('❌ PWA: Service worker registration failed', error);
            }
        } else {
            console.warn('⚠️ PWA: Service workers not supported');
        }
    }

    // IndexedDB Initialization
    async initIndexedDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('VideoTranscriberDB', 1);

            request.onerror = () => reject(request.error);

            request.onsuccess = () => {
                this.db = request.result;
                console.log('✅ PWA: IndexedDB initialized');
                resolve();
            };

            request.onupgradeneeded = () => {
                const db = request.result;

                // Create object stores
                if (!db.objectStoreNames.contains('transcriptionQueue')) {
                    db.createObjectStore('transcriptionQueue', { keyPath: 'id', autoIncrement: true });
                }

                if (!db.objectStoreNames.contains('offlineSessions')) {
                    db.createObjectStore('offlineSessions', { keyPath: 'id', autoIncrement: true });
                }

                if (!db.objectStoreNames.contains('analytics')) {
                    db.createObjectStore('analytics', { keyPath: 'id', autoIncrement: true });
                }

                if (!db.objectStoreNames.contains('cachedResults')) {
                    db.createObjectStore('cachedResults', { keyPath: 'sessionId' });
                }

                console.log('🔧 PWA: IndexedDB stores created');
            };
        });
    }

    // Event Listeners Setup
    setupEventListeners() {
        // Online/offline detection
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.onOnlineStatusChange(true);
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.onOnlineStatusChange(false);
        });

        // Beforeinstallprompt event
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            this.installPrompt = e;
            this.showInstallBanner();
        });

        // App installed event
        window.addEventListener('appinstalled', () => {
            console.log('🎉 PWA: App installed successfully');
            this.hideInstallBanner();
            this.trackEvent('pwa_installed');
        });

        // Visibility change for background sync
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && this.isOnline) {
                this.processPendingSync();
            }
        });
    }

    // Install Prompt Setup
    setupInstallPrompt() {
        // Create install banner
        this.createInstallBanner();

        // Show install button in header if appropriate
        this.updateInstallButton();
    }

    createInstallBanner() {
        const banner = document.createElement('div');
        banner.id = 'pwa-install-banner';
        banner.className = 'pwa-install-banner hidden';
        banner.innerHTML = `
            <div class="install-banner-content">
                <div class="install-banner-text">
                    <strong>📱 Install Video Transcriber</strong>
                    <p>Access your transcriptions offline and get a native app experience!</p>
                </div>
                <div class="install-banner-actions">
                    <button id="pwa-install-btn" class="btn btn-primary btn-sm">
                        <i class="bi bi-download"></i> Install
                    </button>
                    <button id="pwa-dismiss-btn" class="btn btn-outline-secondary btn-sm">
                        <i class="bi bi-x"></i> Dismiss
                    </button>
                </div>
            </div>
        `;

        document.body.appendChild(banner);

        // Event listeners for banner
        document.getElementById('pwa-install-btn').addEventListener('click', () => {
            this.promptInstall();
        });

        document.getElementById('pwa-dismiss-btn').addEventListener('click', () => {
            this.hideInstallBanner();
            localStorage.setItem('pwa-install-dismissed', Date.now());
        });
    }

    showInstallBanner() {
        // Don't show if recently dismissed
        const dismissed = localStorage.getItem('pwa-install-dismissed');
        if (dismissed && Date.now() - dismissed < 7 * 24 * 60 * 60 * 1000) { // 7 days
            return;
        }

        // Don't show if already installed
        if (window.matchMedia('(display-mode: standalone)').matches) {
            return;
        }

        const banner = document.getElementById('pwa-install-banner');
        if (banner) {
            banner.classList.remove('hidden');

            // Auto-hide after 10 seconds
            setTimeout(() => {
                this.hideInstallBanner();
            }, 10000);
        }
    }

    hideInstallBanner() {
        const banner = document.getElementById('pwa-install-banner');
        if (banner) {
            banner.classList.add('hidden');
        }
    }

    async promptInstall() {
        if (!this.installPrompt) {
            this.showToast('Install not available on this device', 'info');
            return;
        }

        try {
            const result = await this.installPrompt.prompt();
            console.log('🎯 PWA: Install prompt result:', result.outcome);

            if (result.outcome === 'accepted') {
                this.trackEvent('pwa_install_accepted');
            } else {
                this.trackEvent('pwa_install_dismissed');
            }

            this.installPrompt = null;
            this.hideInstallBanner();
        } catch (error) {
            console.error('❌ PWA: Install prompt failed', error);
        }
    }

    updateInstallButton() {
        // Add install button to navigation if not already installed
        if (!window.matchMedia('(display-mode: standalone)').matches) {
            const navbar = document.querySelector('.navbar-nav');
            if (navbar && !document.getElementById('nav-install-btn')) {
                const installBtn = document.createElement('li');
                installBtn.className = 'nav-item';
                installBtn.innerHTML = `
                    <button id="nav-install-btn" class="btn btn-outline-light btn-sm ms-2">
                        <i class="bi bi-download"></i> Install App
                    </button>
                `;

                navbar.appendChild(installBtn);

                document.getElementById('nav-install-btn').addEventListener('click', () => {
                    this.promptInstall();
                });
            }
        }
    }

    // Offline Support
    initOfflineSupport() {
        this.updateOfflineIndicator();
        this.loadOfflineQueue();

        // Intercept form submissions for offline queuing
        this.interceptFormSubmissions();
    }

    updateOfflineIndicator() {
        let indicator = document.getElementById('offline-indicator');

        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'offline-indicator';
            indicator.className = 'offline-indicator';
            document.body.appendChild(indicator);
        }

        if (this.isOnline) {
            indicator.className = 'offline-indicator online';
            indicator.innerHTML = '<i class="bi bi-wifi"></i> Online';
        } else {
            indicator.className = 'offline-indicator offline';
            indicator.innerHTML = '<i class="bi bi-wifi-off"></i> Offline - Changes will sync when connected';
        }
    }

    onOnlineStatusChange(isOnline) {
        console.log('🌐 PWA: Network status changed:', isOnline ? 'online' : 'offline');

        this.updateOfflineIndicator();

        if (isOnline) {
            this.processPendingSync();
            this.showToast('🌐 Back online! Syncing data...', 'success');
        } else {
            this.showToast('📱 You\'re offline. Changes will be saved locally.', 'info');
        }
    }

    interceptFormSubmissions() {
        // Intercept upload form
        const uploadForm = document.getElementById('uploadForm');
        if (uploadForm) {
            uploadForm.addEventListener('submit', (e) => {
                if (!this.isOnline) {
                    e.preventDefault();
                    this.queueForOfflineProcessing(e.target);
                }
            });
        }
    }

    async queueForOfflineProcessing(form) {
        try {
            const formData = new FormData(form);
            const videoFile = formData.get('video');

            if (!videoFile) {
                this.showToast('No video file selected', 'error');
                return;
            }

            // Store in IndexedDB for background sync
            const queueItem = {
                filename: videoFile.name,
                sessionName: formData.get('session_name') || 'Offline Session',
                videoBlob: videoFile,
                options: {
                    chunkDuration: formData.get('chunk_duration'),
                    enableAnalysis: formData.get('enable_analysis') === 'on'
                },
                status: 'queued',
                timestamp: Date.now()
            };

            await this.addToIndexedDB('transcriptionQueue', queueItem);

            this.showToast(`📋 Video queued for processing when online: ${videoFile.name}`, 'info');

            // Register background sync
            if (this.registration && this.registration.sync) {
                await this.registration.sync.register('transcription-queue');
            }

        } catch (error) {
            console.error('❌ PWA: Failed to queue for offline processing', error);
            this.showToast('Failed to queue video for offline processing', 'error');
        }
    }

    // Background Sync
    setupBackgroundSync() {
        if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
            console.log('✅ PWA: Background sync supported');
        } else {
            console.warn('⚠️ PWA: Background sync not supported');
        }
    }

    async processPendingSync() {
        if (!this.isOnline || !this.registration) return;

        try {
            // Trigger background sync for queued items
            if (this.registration.sync) {
                await this.registration.sync.register('transcription-queue');
                await this.registration.sync.register('offline-sessions');
                await this.registration.sync.register('analytics');
            }
        } catch (error) {
            console.error('❌ PWA: Background sync failed', error);
        }
    }

    // Push Notifications
    async initPushNotifications() {
        if (!('Notification' in window) || !('PushManager' in window)) {
            console.warn('⚠️ PWA: Push notifications not supported');
            return;
        }

        // Check current permission
        if (Notification.permission === 'granted') {
            console.log('✅ PWA: Push notifications already granted');
            await this.subscribeToPush();
        } else if (Notification.permission !== 'denied') {
            // Will prompt for permission when user triggers action
            this.addNotificationPrompt();
        }
    }

    addNotificationPrompt() {
        // Add notification prompt to settings or after successful upload
        const promptUser = () => {
            this.requestNotificationPermission();
        };

        // Add to event listeners for appropriate triggers
        window.addEventListener('transcription-complete', promptUser, { once: true });
    }

    async requestNotificationPermission() {
        try {
            const permission = await Notification.requestPermission();

            if (permission === 'granted') {
                console.log('✅ PWA: Notification permission granted');
                await this.subscribeToPush();
                this.showToast('🔔 Notifications enabled! You\'ll be notified when transcriptions complete.', 'success');
            } else {
                console.log('❌ PWA: Notification permission denied');
            }
        } catch (error) {
            console.error('❌ PWA: Notification permission request failed', error);
        }
    }

    async subscribeToPush() {
        if (!this.registration) return;

        try {
            const subscription = await this.registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: this.urlB64ToUint8Array(await this.getVapidPublicKey())
            });

            // Send subscription to server
            await fetch('/api/push/subscribe', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(subscription)
            });

            console.log('✅ PWA: Push subscription created');
        } catch (error) {
            console.error('❌ PWA: Push subscription failed', error);
        }
    }

    async getVapidPublicKey() {
        try {
            const response = await fetch('/api/push/vapid-key');
            const data = await response.json();
            return data.publicKey;
        } catch (error) {
            console.error('❌ PWA: Failed to get VAPID key', error);
            return null;
        }
    }

    urlB64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/\-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }

    // Service Worker Message Handler
    handleServiceWorkerMessage(event) {
        const { data } = event;

        switch (data.type) {
            case 'QUEUE_PROCESSED':
                this.showToast('✅ Offline queue processed successfully!', 'success');
                this.loadOfflineQueue(); // Refresh queue display
                break;

            case 'TRANSCRIPTION_COMPLETE':
                this.showToast(`🎉 Transcription complete: ${data.filename}`, 'success');
                if (window.location.pathname === '/sessions') {
                    window.location.reload(); // Refresh sessions page
                }
                break;

            default:
                console.log('💬 PWA: Service worker message:', data);
        }
    }

    // IndexedDB Helpers
    async addToIndexedDB(storeName, data) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.add(data);

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async getFromIndexedDB(storeName, key = null) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const request = key ? store.get(key) : store.getAll();

            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    }

    async loadOfflineQueue() {
        try {
            const queue = await this.getFromIndexedDB('transcriptionQueue');
            this.offlineQueue = queue || [];
            this.updateQueueDisplay();
        } catch (error) {
            console.error('❌ PWA: Failed to load offline queue', error);
        }
    }

    updateQueueDisplay() {
        // Update UI to show queued items
        const queueCount = this.offlineQueue.length;

        let queueIndicator = document.getElementById('queue-indicator');
        if (!queueIndicator && queueCount > 0) {
            queueIndicator = document.createElement('div');
            queueIndicator.id = 'queue-indicator';
            queueIndicator.className = 'queue-indicator';
            document.body.appendChild(queueIndicator);
        }

        if (queueIndicator) {
            if (queueCount > 0) {
                queueIndicator.innerHTML = `
                    <i class="bi bi-clock"></i>
                    ${queueCount} video${queueCount > 1 ? 's' : ''} queued for processing
                `;
                queueIndicator.style.display = 'block';
            } else {
                queueIndicator.style.display = 'none';
            }
        }
    }

    // Utility Methods
    showToast(message, type = 'info') {
        // Use existing toast system or create one
        if (window.showToast) {
            window.showToast(message, type);
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }

    trackEvent(eventName, properties = {}) {
        // Track PWA events for analytics
        if (window.gtag) {
            window.gtag('event', eventName, properties);
        }

        // Store locally for offline sync
        if (this.db) {
            this.addToIndexedDB('analytics', {
                event: eventName,
                properties,
                timestamp: Date.now()
            }).catch(console.error);
        }
    }

    showUpdateNotification() {
        this.showToast('🔄 App update available! Refresh to get the latest features.', 'info');

        // Option to auto-refresh
        setTimeout(() => {
            if (confirm('A new version is available. Refresh now?')) {
                window.location.reload();
            }
        }, 5000);
    }

    // Check if app is installed
    isInstalled() {
        return window.matchMedia('(display-mode: standalone)').matches ||
               window.navigator.standalone === true;
    }

    // Get installation status
    getInstallationInfo() {
        return {
            isInstalled: this.isInstalled(),
            canInstall: !!this.installPrompt,
            isOnline: this.isOnline,
            hasServiceWorker: !!this.registration,
            queueLength: this.offlineQueue.length
        };
    }
}

// Initialize PWA when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.videoTranscriberPWA = new VideoTranscriberPWA();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VideoTranscriberPWA;
}
