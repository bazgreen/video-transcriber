/**
 * Touch Navigation for Transcript
 * Provides gesture-based navigation through transcripts on mobile devices
 */

class TranscriptTouchNavigation {
    constructor(transcriptContainer) {
        this.container = transcriptContainer;
        this.segments = [];
        this.currentSegment = 0;

        // Touch state
        this.touchState = {
            startY: 0,
            startX: 0,
            currentY: 0,
            currentX: 0,
            isScrolling: false,
            startTime: 0,
            velocity: 0,
            direction: null
        };

        // Navigation state
        this.navigationMode = 'normal'; // normal, search, chapter
        this.searchResults = [];
        this.currentSearchIndex = 0;

        this.init();
    }

    init() {
        this.setupTranscriptStructure();
        this.bindTouchEvents();
        this.createNavigationControls();
        this.setupMobileSearch();
        this.setupKeyboardShortcuts();
    }

    setupTranscriptStructure() {
        // Find and structure transcript segments
        this.segments = Array.from(this.container.querySelectorAll('.transcript-segment, .transcript-line, [data-timestamp]'));

        // Add navigation attributes
        this.segments.forEach((segment, index) => {
            segment.setAttribute('data-segment-index', index);
            segment.classList.add('navigable-segment');
        });

        // Add intersection observer for auto-scroll detection
        this.setupIntersectionObserver();
    }

    setupIntersectionObserver() {
        const options = {
            root: this.container,
            rootMargin: '-50% 0px -50% 0px',
            threshold: 0
        };

        this.observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const index = parseInt(entry.target.getAttribute('data-segment-index'));
                    this.currentSegment = index;
                    this.updateNavigationIndicator();
                }
            });
        }, options);

        this.segments.forEach(segment => {
            this.observer.observe(segment);
        });
    }

    bindTouchEvents() {
        // Touch events for navigation
        this.container.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });
        this.container.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
        this.container.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: false });

        // Long press for context menu
        this.container.addEventListener('touchstart', this.handleLongPressStart.bind(this));
        this.container.addEventListener('touchend', this.handleLongPressEnd.bind(this));

        // Double tap for actions
        this.container.addEventListener('touchend', this.handleDoubleTap.bind(this));
    }

    handleTouchStart(e) {
        const touch = e.touches[0];
        this.touchState.startY = touch.clientY;
        this.touchState.startX = touch.clientX;
        this.touchState.currentY = touch.clientY;
        this.touchState.currentX = touch.clientX;
        this.touchState.startTime = Date.now();
        this.touchState.isScrolling = false;
        this.touchState.direction = null;

        // Clear any ongoing momentum
        this.stopMomentumScroll();
    }

    handleTouchMove(e) {
        const touch = e.touches[0];
        this.touchState.currentY = touch.clientY;
        this.touchState.currentX = touch.clientX;

        const deltaY = this.touchState.currentY - this.touchState.startY;
        const deltaX = this.touchState.currentX - this.touchState.startX;
        const distance = Math.sqrt(deltaY * deltaY + deltaX * deltaX);

        // Determine scroll direction
        if (distance > 10 && !this.touchState.isScrolling) {
            this.touchState.isScrolling = true;

            if (Math.abs(deltaY) > Math.abs(deltaX)) {
                this.touchState.direction = deltaY > 0 ? 'down' : 'up';
            } else {
                this.touchState.direction = deltaX > 0 ? 'right' : 'left';

                // Horizontal swipe for navigation
                e.preventDefault();
                this.handleHorizontalSwipe(deltaX);
            }
        }

        // Calculate velocity for momentum
        const currentTime = Date.now();
        const timeDelta = currentTime - this.touchState.startTime;
        if (timeDelta > 0) {
            this.touchState.velocity = deltaY / timeDelta;
        }
    }

    handleTouchEnd(e) {
        const deltaY = this.touchState.currentY - this.touchState.startY;
        const deltaX = this.touchState.currentX - this.touchState.startX;
        const duration = Date.now() - this.touchState.startTime;
        const distance = Math.sqrt(deltaY * deltaY + deltaX * deltaX);

        // Handle quick swipes
        if (duration < 300 && distance > 50) {
            if (Math.abs(deltaX) > Math.abs(deltaY)) {
                this.handleSwipeGesture(deltaX > 0 ? 'right' : 'left');
            } else {
                this.handleQuickScroll(deltaY > 0 ? 'down' : 'up');
            }
        }

        // Add momentum scrolling
        if (Math.abs(this.touchState.velocity) > 0.5 && this.touchState.direction) {
            this.startMomentumScroll();
        }

        this.resetTouchState();
    }

    handleHorizontalSwipe(deltaX) {
        // Visual feedback for horizontal swipe
        const opacity = Math.min(1, Math.abs(deltaX) / 100);
        this.showSwipeIndicator(deltaX > 0 ? 'next' : 'prev', opacity);
    }

    handleSwipeGesture(direction) {
        switch (direction) {
            case 'right':
                this.navigateToNext();
                break;
            case 'left':
                this.navigateToPrevious();
                break;
        }

        this.triggerHapticFeedback();
    }

    handleQuickScroll(direction) {
        // Jump to next/previous chapter or significant segment
        if (direction === 'up') {
            this.jumpToPreviousChapter();
        } else {
            this.jumpToNextChapter();
        }
    }

    navigateToNext() {
        if (this.navigationMode === 'search') {
            this.navigateToNextSearchResult();
        } else {
            const nextIndex = Math.min(this.segments.length - 1, this.currentSegment + 1);
            this.scrollToSegment(nextIndex);
        }
    }

    navigateToPrevious() {
        if (this.navigationMode === 'search') {
            this.navigateToPreviousSearchResult();
        } else {
            const prevIndex = Math.max(0, this.currentSegment - 1);
            this.scrollToSegment(prevIndex);
        }
    }

    scrollToSegment(index, behavior = 'smooth') {
        if (index < 0 || index >= this.segments.length) return;

        const segment = this.segments[index];
        const containerRect = this.container.getBoundingClientRect();
        const segmentRect = segment.getBoundingClientRect();

        // Calculate scroll position to center the segment
        const scrollTop = this.container.scrollTop + segmentRect.top - containerRect.top - (containerRect.height / 2);

        this.container.scrollTo({
            top: scrollTop,
            behavior: behavior
        });

        // Highlight the segment
        this.highlightSegment(segment);

        // Update current segment
        this.currentSegment = index;
        this.updateNavigationIndicator();
    }

    highlightSegment(segment) {
        // Remove existing highlights
        this.segments.forEach(s => s.classList.remove('highlighted-segment'));

        // Add highlight to current segment
        segment.classList.add('highlighted-segment');

        // Auto-remove highlight after 2 seconds
        setTimeout(() => {
            segment.classList.remove('highlighted-segment');
        }, 2000);
    }

    jumpToNextChapter() {
        // Find next chapter or major section
        const currentPos = this.currentSegment;
        for (let i = currentPos + 1; i < this.segments.length; i++) {
            const segment = this.segments[i];
            if (segment.classList.contains('chapter-marker') ||
                segment.hasAttribute('data-chapter') ||
                this.isSignificantSegment(segment)) {
                this.scrollToSegment(i);
                return;
            }
        }

        // If no chapter found, jump by percentage
        const jumpIndex = Math.min(this.segments.length - 1, currentPos + Math.floor(this.segments.length * 0.1));
        this.scrollToSegment(jumpIndex);
    }

    jumpToPreviousChapter() {
        // Find previous chapter or major section
        const currentPos = this.currentSegment;
        for (let i = currentPos - 1; i >= 0; i--) {
            const segment = this.segments[i];
            if (segment.classList.contains('chapter-marker') ||
                segment.hasAttribute('data-chapter') ||
                this.isSignificantSegment(segment)) {
                this.scrollToSegment(i);
                return;
            }
        }

        // If no chapter found, jump by percentage
        const jumpIndex = Math.max(0, currentPos - Math.floor(this.segments.length * 0.1));
        this.scrollToSegment(jumpIndex);
    }

    isSignificantSegment(segment) {
        // Determine if segment is significant (speaker change, long pause, etc.)
        const text = segment.textContent;
        return text.includes('Speaker') ||
               text.includes('Chapter') ||
               segment.classList.contains('speaker-change') ||
               segment.hasAttribute('data-speaker-change');
    }

    createNavigationControls() {
        // Create floating navigation controls for mobile
        this.navControls = document.createElement('div');
        this.navControls.className = 'transcript-nav-controls';
        this.navControls.innerHTML = `
            <div class="nav-control nav-up" data-action="previous">
                <i class="fas fa-chevron-up"></i>
            </div>
            <div class="nav-control nav-indicator">
                <span class="current-segment">1</span>
                <span class="total-segments">${this.segments.length}</span>
            </div>
            <div class="nav-control nav-down" data-action="next">
                <i class="fas fa-chevron-down"></i>
            </div>
            <div class="nav-control nav-search" data-action="search">
                <i class="fas fa-search"></i>
            </div>
        `;

        this.container.appendChild(this.navControls);

        // Bind navigation control events
        this.navControls.addEventListener('click', this.handleNavControlClick.bind(this));
        this.navControls.addEventListener('touchstart', (e) => e.stopPropagation());
    }

    handleNavControlClick(e) {
        const action = e.target.closest('[data-action]')?.getAttribute('data-action');

        switch (action) {
            case 'previous':
                this.navigateToPrevious();
                break;
            case 'next':
                this.navigateToNext();
                break;
            case 'search':
                this.toggleSearchMode();
                break;
        }
    }

    updateNavigationIndicator() {
        const indicator = this.navControls.querySelector('.current-segment');
        if (indicator) {
            indicator.textContent = this.currentSegment + 1;
        }
    }

    setupMobileSearch() {
        // Create mobile search interface
        this.searchInterface = document.createElement('div');
        this.searchInterface.className = 'mobile-search-interface';
        this.searchInterface.innerHTML = `
            <div class="search-input-container">
                <input type="text" class="search-input" placeholder="Search transcript...">
                <button class="search-close">×</button>
            </div>
            <div class="search-results">
                <div class="search-navigation">
                    <button class="search-prev">▲</button>
                    <span class="search-counter">0 / 0</span>
                    <button class="search-next">▼</button>
                </div>
            </div>
        `;

        this.container.appendChild(this.searchInterface);

        // Bind search events
        const searchInput = this.searchInterface.querySelector('.search-input');
        const searchClose = this.searchInterface.querySelector('.search-close');
        const searchPrev = this.searchInterface.querySelector('.search-prev');
        const searchNext = this.searchInterface.querySelector('.search-next');

        searchInput.addEventListener('input', this.handleSearchInput.bind(this));
        searchClose.addEventListener('click', this.closeSearchMode.bind(this));
        searchPrev.addEventListener('click', () => this.navigateToPreviousSearchResult());
        searchNext.addEventListener('click', () => this.navigateToNextSearchResult());
    }

    toggleSearchMode() {
        if (this.navigationMode === 'search') {
            this.closeSearchMode();
        } else {
            this.openSearchMode();
        }
    }

    openSearchMode() {
        this.navigationMode = 'search';
        this.searchInterface.classList.add('active');
        this.navControls.classList.add('search-mode');

        const searchInput = this.searchInterface.querySelector('.search-input');
        searchInput.focus();

        // Show virtual keyboard helper
        this.showVirtualKeyboardHelper();
    }

    closeSearchMode() {
        this.navigationMode = 'normal';
        this.searchInterface.classList.remove('active');
        this.navControls.classList.remove('search-mode');

        // Clear search highlights
        this.clearSearchHighlights();
        this.searchResults = [];
        this.currentSearchIndex = 0;
    }

    handleSearchInput(e) {
        const query = e.target.value.trim();

        if (query.length < 2) {
            this.clearSearchHighlights();
            this.searchResults = [];
            this.updateSearchCounter();
            return;
        }

        this.performSearch(query);
    }

    performSearch(query) {
        this.clearSearchHighlights();
        this.searchResults = [];

        const regex = new RegExp(query, 'gi');

        this.segments.forEach((segment, index) => {
            const text = segment.textContent;
            if (regex.test(text)) {
                this.searchResults.push({
                    index: index,
                    segment: segment,
                    text: text
                });

                // Highlight the text
                this.highlightSearchText(segment, query);
            }
        });

        this.currentSearchIndex = 0;
        this.updateSearchCounter();

        // Navigate to first result
        if (this.searchResults.length > 0) {
            this.scrollToSegment(this.searchResults[0].index, 'smooth');
        }
    }

    highlightSearchText(segment, query) {
        const regex = new RegExp(`(${query})`, 'gi');
        const html = segment.innerHTML.replace(regex, '<mark class="search-highlight">$1</mark>');
        segment.innerHTML = html;
        segment.classList.add('has-search-results');
    }

    clearSearchHighlights() {
        this.segments.forEach(segment => {
            const highlights = segment.querySelectorAll('.search-highlight');
            highlights.forEach(highlight => {
                highlight.replaceWith(document.createTextNode(highlight.textContent));
            });
            segment.classList.remove('has-search-results');
        });
    }

    navigateToNextSearchResult() {
        if (this.searchResults.length === 0) return;

        this.currentSearchIndex = (this.currentSearchIndex + 1) % this.searchResults.length;
        const result = this.searchResults[this.currentSearchIndex];
        this.scrollToSegment(result.index);
        this.updateSearchCounter();
    }

    navigateToPreviousSearchResult() {
        if (this.searchResults.length === 0) return;

        this.currentSearchIndex = this.currentSearchIndex === 0 ?
            this.searchResults.length - 1 : this.currentSearchIndex - 1;
        const result = this.searchResults[this.currentSearchIndex];
        this.scrollToSegment(result.index);
        this.updateSearchCounter();
    }

    updateSearchCounter() {
        const counter = this.searchInterface.querySelector('.search-counter');
        if (counter) {
            if (this.searchResults.length === 0) {
                counter.textContent = '0 / 0';
            } else {
                counter.textContent = `${this.currentSearchIndex + 1} / ${this.searchResults.length}`;
            }
        }
    }

    // Long press handlers
    handleLongPressStart(e) {
        this.longPressTimer = setTimeout(() => {
            this.showContextMenu(e);
        }, 800);
    }

    handleLongPressEnd(e) {
        if (this.longPressTimer) {
            clearTimeout(this.longPressTimer);
            this.longPressTimer = null;
        }
    }

    showContextMenu(e) {
        const target = e.target.closest('.navigable-segment');
        if (!target) return;

        // Show context menu with options
        this.showSegmentActions(target, e.touches[0]);
        this.triggerHapticFeedback('heavy');
    }

    showSegmentActions(segment, touch) {
        // Create context menu
        const menu = document.createElement('div');
        menu.className = 'segment-context-menu';
        menu.innerHTML = `
            <div class="context-action" data-action="copy">📋 Copy</div>
            <div class="context-action" data-action="share">📤 Share</div>
            <div class="context-action" data-action="bookmark">🔖 Bookmark</div>
            <div class="context-action" data-action="jump-video">📹 Jump to Video</div>
        `;

        // Position menu
        menu.style.position = 'fixed';
        menu.style.left = touch.clientX + 'px';
        menu.style.top = touch.clientY + 'px';
        menu.style.zIndex = '1000';

        document.body.appendChild(menu);

        // Handle menu clicks
        menu.addEventListener('click', (e) => {
            const action = e.target.getAttribute('data-action');
            this.handleSegmentAction(action, segment);
            document.body.removeChild(menu);
        });

        // Auto-remove menu
        setTimeout(() => {
            if (document.body.contains(menu)) {
                document.body.removeChild(menu);
            }
        }, 5000);
    }

    handleSegmentAction(action, segment) {
        switch (action) {
            case 'copy':
                this.copySegmentText(segment);
                break;
            case 'share':
                this.shareSegment(segment);
                break;
            case 'bookmark':
                this.bookmarkSegment(segment);
                break;
            case 'jump-video':
                this.jumpToVideoTime(segment);
                break;
        }
    }

    copySegmentText(segment) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(segment.textContent);
            this.showToast('Text copied to clipboard');
        }
    }

    shareSegment(segment) {
        if (navigator.share) {
            navigator.share({
                title: 'Transcript Segment',
                text: segment.textContent,
                url: window.location.href
            });
        }
    }

    jumpToVideoTime(segment) {
        const timestamp = segment.getAttribute('data-timestamp') ||
                         segment.querySelector('[data-timestamp]')?.getAttribute('data-timestamp');

        if (timestamp) {
            // Dispatch event to video player
            document.dispatchEvent(new CustomEvent('seekToTime', {
                detail: { time: parseFloat(timestamp) }
            }));
        }
    }

    // Utility methods
    showSwipeIndicator(direction, opacity) {
        // Visual feedback for swipe gestures
        const indicator = document.createElement('div');
        indicator.className = `swipe-indicator swipe-${direction}`;
        indicator.style.opacity = opacity;
        indicator.textContent = direction === 'next' ? '→' : '←';

        this.container.appendChild(indicator);

        setTimeout(() => {
            this.container.removeChild(indicator);
        }, 300);
    }

    startMomentumScroll() {
        // Add momentum to scrolling
        const deceleration = 0.95;
        let velocity = this.touchState.velocity * 100;

        const animate = () => {
            if (Math.abs(velocity) < 1) return;

            this.container.scrollTop += velocity;
            velocity *= deceleration;

            requestAnimationFrame(animate);
        };

        this.momentumFrame = requestAnimationFrame(animate);
    }

    stopMomentumScroll() {
        if (this.momentumFrame) {
            cancelAnimationFrame(this.momentumFrame);
            this.momentumFrame = null;
        }
    }

    resetTouchState() {
        this.touchState = {
            startY: 0,
            startX: 0,
            currentY: 0,
            currentX: 0,
            isScrolling: false,
            startTime: 0,
            velocity: 0,
            direction: null
        };
    }

    triggerHapticFeedback(type = 'light') {
        if (navigator.vibrate) {
            const patterns = {
                light: 50,
                medium: 100,
                heavy: 200
            };
            navigator.vibrate(patterns[type] || 50);
        }
    }

    showToast(message) {
        // Show temporary toast message
        const toast = document.createElement('div');
        toast.className = 'mobile-toast';
        toast.textContent = message;
        document.body.appendChild(toast);

        setTimeout(() => {
            toast.classList.add('visible');
        }, 10);

        setTimeout(() => {
            toast.classList.remove('visible');
            setTimeout(() => {
                document.body.removeChild(toast);
            }, 300);
        }, 2000);
    }

    showVirtualKeyboardHelper() {
        // Helper for virtual keyboard on mobile
        const helper = document.createElement('div');
        helper.className = 'keyboard-helper';
        helper.textContent = 'Use keyboard or voice input to search';
        this.searchInterface.appendChild(helper);

        setTimeout(() => {
            if (this.searchInterface.contains(helper)) {
                this.searchInterface.removeChild(helper);
            }
        }, 3000);
    }

    setupKeyboardShortcuts() {
        // Keyboard shortcuts for desktop and mobile with bluetooth keyboard
        document.addEventListener('keydown', (e) => {
            if (this.navigationMode === 'search' && e.target.tagName === 'INPUT') {
                return; // Don't handle shortcuts while typing in search
            }

            switch (e.key) {
                case 'ArrowUp':
                    e.preventDefault();
                    this.navigateToPrevious();
                    break;
                case 'ArrowDown':
                    e.preventDefault();
                    this.navigateToNext();
                    break;
                case '/':
                    e.preventDefault();
                    this.toggleSearchMode();
                    break;
                case 'Escape':
                    if (this.navigationMode === 'search') {
                        this.closeSearchMode();
                    }
                    break;
            }
        });
    }
}

// Auto-initialize for transcript containers
document.addEventListener('DOMContentLoaded', function() {
    const transcriptContainers = document.querySelectorAll('.transcript-container, .transcript-viewer, [data-transcript]');
    transcriptContainers.forEach(container => {
        new TranscriptTouchNavigation(container);
    });
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TranscriptTouchNavigation;
}
