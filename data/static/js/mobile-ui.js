/**
 * Mobile UI Components for PWA
 * Implements bottom navigation, slide-up panels, pull-to-refresh, and mobile layouts
 */

class MobileUIManager {
    constructor() {
        this.isInitialized = false;
        this.bottomNav = null;
        this.activePanel = null;
        this.pullToRefreshEnabled = false;
        this.scrollContainer = null;
        this.infiniteScrollEnabled = false;
        this.loadingMore = false;

        this.init();
    }

    init() {
        if (this.isInitialized) return;

        this.detectMobileEnvironment();
        this.createBottomNavigation();
        this.setupPullToRefresh();
        this.setupInfiniteScroll();
        this.setupGestureHandlers();
        this.setupKeyboardHandling();

        this.isInitialized = true;
        console.log('Mobile UI Manager initialized');
    }

    detectMobileEnvironment() {
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        const isTouch = 'ontouchstart' in window;
        const isSmallScreen = window.innerWidth <= 768;

        this.isMobileDevice = isMobile || (isTouch && isSmallScreen);

        if (this.isMobileDevice) {
            document.body.classList.add('mobile-ui-enabled');
            this.setupViewportMeta();
        }
    }

    setupViewportMeta() {
        let viewport = document.querySelector('meta[name="viewport"]');
        if (!viewport) {
            viewport = document.createElement('meta');
            viewport.name = 'viewport';
            document.head.appendChild(viewport);
        }
        viewport.content = 'width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, viewport-fit=cover';
    }

    createBottomNavigation() {
        if (!this.isMobileDevice) return;

        // Create bottom navigation container
        const bottomNav = document.createElement('div');
        bottomNav.className = 'mobile-bottom-nav';
        bottomNav.innerHTML = `
            <div class="bottom-nav-item" data-page="home">
                <i class="fas fa-home"></i>
                <span>Home</span>
            </div>
            <div class="bottom-nav-item" data-page="upload">
                <i class="fas fa-plus-circle"></i>
                <span>Upload</span>
            </div>
            <div class="bottom-nav-item" data-page="sessions">
                <i class="fas fa-video"></i>
                <span>Sessions</span>
            </div>
            <div class="bottom-nav-item" data-page="insights">
                <i class="fas fa-brain"></i>
                <span>Insights</span>
            </div>
            <div class="bottom-nav-item" data-page="profile">
                <i class="fas fa-user"></i>
                <span>Profile</span>
            </div>
        `;

        document.body.appendChild(bottomNav);
        this.bottomNav = bottomNav;

        // Add click handlers
        bottomNav.addEventListener('click', (e) => {
            const item = e.target.closest('.bottom-nav-item');
            if (item) {
                this.handleNavigation(item.dataset.page);
            }
        });

        // Set active item based on current page
        this.updateActiveNavItem();
    }

    handleNavigation(page) {
        // Remove active class from all items
        this.bottomNav.querySelectorAll('.bottom-nav-item').forEach(item => {
            item.classList.remove('active');
        });

        // Add active class to clicked item
        const activeItem = this.bottomNav.querySelector(`[data-page="${page}"]`);
        if (activeItem) {
            activeItem.classList.add('active');
        }

        // Handle navigation based on page
        switch (page) {
            case 'home':
                window.location.href = '/';
                break;
            case 'upload':
                this.showUploadPanel();
                break;
            case 'sessions':
                window.location.href = '/sessions';
                break;
            case 'insights':
                window.location.href = '/ai-insights';
                break;
            case 'profile':
                this.showProfilePanel();
                break;
        }
    }

    updateActiveNavItem() {
        if (!this.bottomNav) return;

        const path = window.location.pathname;
        let activePage = 'home';

        if (path.includes('/sessions')) activePage = 'sessions';
        else if (path.includes('/upload')) activePage = 'upload';
        else if (path.includes('/ai-insights')) activePage = 'insights';
        else if (path.includes('/profile')) activePage = 'profile';

        this.bottomNav.querySelectorAll('.bottom-nav-item').forEach(item => {
            item.classList.remove('active');
        });

        const activeItem = this.bottomNav.querySelector(`[data-page="${activePage}"]`);
        if (activeItem) {
            activeItem.classList.add('active');
        }
    }

    showUploadPanel() {
        const panel = this.createSlideUpPanel('upload-panel', 'Upload Video', `
            <div class="mobile-upload-options">
                <div class="upload-option" data-action="camera">
                    <i class="fas fa-camera"></i>
                    <span>Record Video</span>
                </div>
                <div class="upload-option" data-action="file">
                    <i class="fas fa-file-video"></i>
                    <span>Choose File</span>
                </div>
                <div class="upload-option" data-action="voice">
                    <i class="fas fa-microphone"></i>
                    <span>Voice Note</span>
                </div>
            </div>
        `);

        panel.addEventListener('click', (e) => {
            const option = e.target.closest('.upload-option');
            if (option) {
                const action = option.dataset.action;
                this.handleUploadAction(action);
                this.hideActivePanel();
            }
        });

        this.showPanel(panel);
    }

    showProfilePanel() {
        const panel = this.createSlideUpPanel('profile-panel', 'Profile', `
            <div class="mobile-profile-options">
                <div class="profile-option" data-action="settings">
                    <i class="fas fa-cog"></i>
                    <span>Settings</span>
                </div>
                <div class="profile-option" data-action="export">
                    <i class="fas fa-download"></i>
                    <span>Export Data</span>
                </div>
                <div class="profile-option" data-action="help">
                    <i class="fas fa-question-circle"></i>
                    <span>Help</span>
                </div>
                <div class="profile-option" data-action="about">
                    <i class="fas fa-info-circle"></i>
                    <span>About</span>
                </div>
            </div>
        `);

        panel.addEventListener('click', (e) => {
            const option = e.target.closest('.profile-option');
            if (option) {
                const action = option.dataset.action;
                this.handleProfileAction(action);
                this.hideActivePanel();
            }
        });

        this.showPanel(panel);
    }

    createSlideUpPanel(id, title, content) {
        // Remove existing panel if any
        const existing = document.getElementById(id);
        if (existing) {
            existing.remove();
        }

        const panel = document.createElement('div');
        panel.id = id;
        panel.className = 'mobile-slide-panel';
        panel.innerHTML = `
            <div class="panel-overlay"></div>
            <div class="panel-content">
                <div class="panel-header">
                    <div class="panel-handle"></div>
                    <h3>${title}</h3>
                    <button class="panel-close" aria-label="Close">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="panel-body">
                    ${content}
                </div>
            </div>
        `;

        document.body.appendChild(panel);

        // Add event listeners
        panel.querySelector('.panel-overlay').addEventListener('click', () => {
            this.hidePanel(panel);
        });

        panel.querySelector('.panel-close').addEventListener('click', () => {
            this.hidePanel(panel);
        });

        // Add swipe down to close
        this.setupPanelSwipeGestures(panel);

        return panel;
    }

    showPanel(panel) {
        this.activePanel = panel;
        panel.classList.add('show');
        document.body.classList.add('panel-open');

        // Prevent body scroll
        document.body.style.overflow = 'hidden';
    }

    hidePanel(panel) {
        panel.classList.remove('show');
        document.body.classList.remove('panel-open');
        document.body.style.overflow = '';

        setTimeout(() => {
            if (panel.parentNode) {
                panel.parentNode.removeChild(panel);
            }
        }, 300);

        this.activePanel = null;
    }

    hideActivePanel() {
        if (this.activePanel) {
            this.hidePanel(this.activePanel);
        }
    }

    setupPanelSwipeGestures(panel) {
        let startY = 0;
        let currentY = 0;
        let isDragging = false;
        const panelContent = panel.querySelector('.panel-content');

        panelContent.addEventListener('touchstart', (e) => {
            startY = e.touches[0].clientY;
            isDragging = true;
            panelContent.style.transition = 'none';
        });

        panelContent.addEventListener('touchmove', (e) => {
            if (!isDragging) return;

            currentY = e.touches[0].clientY;
            const deltaY = currentY - startY;

            if (deltaY > 0) { // Swiping down
                panelContent.style.transform = `translateY(${deltaY}px)`;
            }
        });

        panelContent.addEventListener('touchend', () => {
            if (!isDragging) return;

            isDragging = false;
            panelContent.style.transition = '';

            const deltaY = currentY - startY;
            if (deltaY > 100) { // Threshold for closing
                this.hidePanel(panel);
            } else {
                panelContent.style.transform = '';
            }
        });
    }

    setupPullToRefresh() {
        if (!this.isMobileDevice) return;

        const container = document.querySelector('.main-content') || document.body;
        let startY = 0;
        let currentY = 0;
        let isAtTop = false;
        let isPulling = false;

        // Create pull indicator
        const pullIndicator = document.createElement('div');
        pullIndicator.className = 'pull-to-refresh-indicator';
        pullIndicator.innerHTML = `
            <div class="pull-spinner">
                <i class="fas fa-sync-alt"></i>
            </div>
            <span>Pull to refresh</span>
        `;
        container.insertBefore(pullIndicator, container.firstChild);

        container.addEventListener('touchstart', (e) => {
            startY = e.touches[0].clientY;
            isAtTop = container.scrollTop === 0;
        });

        container.addEventListener('touchmove', (e) => {
            if (!isAtTop) return;

            currentY = e.touches[0].clientY;
            const deltaY = currentY - startY;

            if (deltaY > 0 && deltaY < 150) {
                isPulling = true;
                e.preventDefault();

                const progress = Math.min(deltaY / 100, 1);
                pullIndicator.style.transform = `translateY(${deltaY}px)`;
                pullIndicator.style.opacity = progress;

                if (deltaY > 80) {
                    pullIndicator.classList.add('ready');
                    pullIndicator.querySelector('span').textContent = 'Release to refresh';
                } else {
                    pullIndicator.classList.remove('ready');
                    pullIndicator.querySelector('span').textContent = 'Pull to refresh';
                }
            }
        });

        container.addEventListener('touchend', () => {
            if (isPulling) {
                const deltaY = currentY - startY;
                if (deltaY > 80) {
                    this.triggerRefresh(pullIndicator);
                } else {
                    this.resetPullIndicator(pullIndicator);
                }
            }
            isPulling = false;
        });
    }

    triggerRefresh(indicator) {
        indicator.classList.add('refreshing');
        indicator.querySelector('span').textContent = 'Refreshing...';
        indicator.style.transform = 'translateY(60px)';

        // Simulate refresh (replace with actual refresh logic)
        setTimeout(() => {
            window.location.reload();
        }, 1000);
    }

    resetPullIndicator(indicator) {
        indicator.style.transform = '';
        indicator.style.opacity = '';
        indicator.classList.remove('ready', 'refreshing');
        indicator.querySelector('span').textContent = 'Pull to refresh';
    }

    setupInfiniteScroll() {
        if (!this.isMobileDevice) return;

        const container = document.querySelector('.sessions-list, .content-list') || document.querySelector('.main-content');
        if (!container) return;

        this.scrollContainer = container;

        container.addEventListener('scroll', () => {
            if (this.loadingMore) return;

            const scrollTop = container.scrollTop;
            const scrollHeight = container.scrollHeight;
            const clientHeight = container.clientHeight;

            if (scrollTop + clientHeight >= scrollHeight - 100) {
                this.loadMoreContent();
            }
        });
    }

    loadMoreContent() {
        if (this.loadingMore) return;

        this.loadingMore = true;

        // Create loading indicator
        const loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'infinite-scroll-loading';
        loadingIndicator.innerHTML = `
            <div class="loading-spinner">
                <i class="fas fa-spinner fa-spin"></i>
            </div>
            <span>Loading more...</span>
        `;

        this.scrollContainer.appendChild(loadingIndicator);

        // Simulate loading (replace with actual API call)
        setTimeout(() => {
            loadingIndicator.remove();
            this.loadingMore = false;

            // Add some dummy content or trigger actual load
            if (window.loadMoreSessions) {
                window.loadMoreSessions();
            }
        }, 1500);
    }

    setupGestureHandlers() {
        if (!this.isMobileDevice) return;

        // Global gesture handlers
        document.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: true });
        document.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
        document.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: true });
    }

    handleTouchStart(e) {
        this.touchStartTime = Date.now();
        this.touchStartX = e.touches[0].clientX;
        this.touchStartY = e.touches[0].clientY;
    }

    handleTouchMove(e) {
        if (this.activePanel) {
            // Allow panel interactions
            return;
        }

        const deltaX = e.touches[0].clientX - this.touchStartX;
        const deltaY = e.touches[0].clientY - this.touchStartY;

        // Detect horizontal swipes for navigation
        if (Math.abs(deltaX) > Math.abs(deltaY) && Math.abs(deltaX) > 50) {
            if (deltaX > 0) {
                // Swipe right - go back
                this.handleSwipeRight();
            } else {
                // Swipe left - go forward (if applicable)
                this.handleSwipeLeft();
            }
        }
    }

    handleTouchEnd(e) {
        const touchDuration = Date.now() - this.touchStartTime;

        // Double tap detection
        if (touchDuration < 300) {
            if (this.lastTapTime && (Date.now() - this.lastTapTime) < 500) {
                this.handleDoubleTap(e);
            }
            this.lastTapTime = Date.now();
        }
    }

    handleSwipeRight() {
        // Go back if possible
        if (window.history.length > 1) {
            window.history.back();
        }
    }

    handleSwipeLeft() {
        // Go forward if possible (or implement custom navigation)
        if (window.history.length > 1) {
            window.history.forward();
        }
    }

    handleDoubleTap(e) {
        // Implement double tap actions (e.g., zoom, like, etc.)
        console.log('Double tap detected');
    }

    setupKeyboardHandling() {
        if (!this.isMobileDevice) return;

        // Handle virtual keyboard
        window.addEventListener('resize', () => {
            this.handleKeyboardResize();
        });

        // Focus/blur handling for inputs
        document.addEventListener('focusin', (e) => {
            if (e.target.matches('input, textarea')) {
                this.handleInputFocus(e.target);
            }
        });

        document.addEventListener('focusout', (e) => {
            if (e.target.matches('input, textarea')) {
                this.handleInputBlur(e.target);
            }
        });
    }

    handleKeyboardResize() {
        const viewport = window.visualViewport || {
            height: window.innerHeight,
            width: window.innerWidth
        };

        const keyboardHeight = window.innerHeight - viewport.height;

        if (keyboardHeight > 150) {
            document.body.classList.add('keyboard-open');
            document.documentElement.style.setProperty('--keyboard-height', `${keyboardHeight}px`);
        } else {
            document.body.classList.remove('keyboard-open');
            document.documentElement.style.setProperty('--keyboard-height', '0px');
        }
    }

    handleInputFocus(input) {
        // Scroll input into view
        setTimeout(() => {
            input.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 300);

        input.closest('.input-group, .form-group')?.classList.add('focused');
    }

    handleInputBlur(input) {
        input.closest('.input-group, .form-group')?.classList.remove('focused');
    }

    handleUploadAction(action) {
        switch (action) {
            case 'camera':
                if (window.mobileCameraManager) {
                    window.mobileCameraManager.openCamera();
                } else {
                    console.warn('Camera manager not available');
                }
                break;
            case 'file':
                const fileInput = document.querySelector('#file-upload') || document.createElement('input');
                fileInput.type = 'file';
                fileInput.accept = 'video/*';
                fileInput.click();
                break;
            case 'voice':
                if (window.voiceInputManager) {
                    window.voiceInputManager.startVoiceRecording();
                } else {
                    console.warn('Voice manager not available');
                }
                break;
        }
    }

    handleProfileAction(action) {
        switch (action) {
            case 'settings':
                window.location.href = '/settings';
                break;
            case 'export':
                window.location.href = '/export';
                break;
            case 'help':
                window.location.href = '/help';
                break;
            case 'about':
                window.location.href = '/about';
                break;
        }
    }

    // Public API methods
    showBottomNav() {
        if (this.bottomNav) {
            this.bottomNav.style.display = 'flex';
        }
    }

    hideBottomNav() {
        if (this.bottomNav) {
            this.bottomNav.style.display = 'none';
        }
    }

    updateNavBadge(page, count) {
        const item = this.bottomNav?.querySelector(`[data-page="${page}"]`);
        if (item) {
            let badge = item.querySelector('.nav-badge');
            if (!badge && count > 0) {
                badge = document.createElement('span');
                badge.className = 'nav-badge';
                item.appendChild(badge);
            }

            if (badge) {
                if (count > 0) {
                    badge.textContent = count > 99 ? '99+' : count;
                    badge.style.display = 'block';
                } else {
                    badge.style.display = 'none';
                }
            }
        }
    }
}

// Initialize mobile UI when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.mobileUIManager = new MobileUIManager();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MobileUIManager;
}
