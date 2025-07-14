/**
 * Enhanced Touch Controls for Video Player
 * Provides gesture-based video navigation and mobile-optimized controls
 */

class VideoTouchControls {
    constructor(videoElement, transcriptContainer) {
        this.video = videoElement;
        this.transcript = transcriptContainer;
        this.videoContainer = videoElement.parentElement;

        // Touch state
        this.touchState = {
            isTouch: false,
            startX: 0,
            startY: 0,
            startTime: 0,
            currentX: 0,
            currentY: 0,
            direction: null,
            gestureStarted: false,
            doubleTapTimer: null,
            lastTap: 0,
            pinchDistance: 0,
            scale: 1
        };

        // Gesture thresholds
        this.thresholds = {
            swipeMinDistance: 50,
            swipeMaxTime: 300,
            doubleTapDelay: 300,
            pinchMinDistance: 50,
            seekSensitivity: 0.1 // seconds per pixel
        };

        this.init();
    }

    init() {
        this.createTouchOverlay();
        this.bindTouchEvents();
        this.createGestureIndicators();
        this.setupVideoControls();
    }

    createTouchOverlay() {
        // Create touch overlay for gesture detection
        this.touchOverlay = document.createElement('div');
        this.touchOverlay.className = 'video-touch-overlay';
        this.touchOverlay.innerHTML = `
            <div class="touch-zone touch-zone-left" data-action="rewind">
                <i class="fas fa-backward"></i>
                <span>-10s</span>
            </div>
            <div class="touch-zone touch-zone-center" data-action="playpause">
                <i class="fas fa-play"></i>
            </div>
            <div class="touch-zone touch-zone-right" data-action="forward">
                <i class="fas fa-forward"></i>
                <span>+10s</span>
            </div>
            <div class="gesture-indicator"></div>
        `;

        this.videoContainer.appendChild(this.touchOverlay);
        this.gestureIndicator = this.touchOverlay.querySelector('.gesture-indicator');
    }

    bindTouchEvents() {
        // Touch events
        this.touchOverlay.addEventListener('touchstart', this.handleTouchStart.bind(this), { passive: false });
        this.touchOverlay.addEventListener('touchmove', this.handleTouchMove.bind(this), { passive: false });
        this.touchOverlay.addEventListener('touchend', this.handleTouchEnd.bind(this), { passive: false });

        // Mouse events for desktop testing
        this.touchOverlay.addEventListener('mousedown', this.handleMouseStart.bind(this));
        this.touchOverlay.addEventListener('mousemove', this.handleMouseMove.bind(this));
        this.touchOverlay.addEventListener('mouseup', this.handleMouseEnd.bind(this));

        // Prevent context menu on long press
        this.touchOverlay.addEventListener('contextmenu', (e) => e.preventDefault());

        // Handle video element gestures
        this.video.addEventListener('touchstart', this.handleVideoTouch.bind(this), { passive: false });
    }

    handleTouchStart(e) {
        e.preventDefault();

        if (e.touches.length === 1) {
            this.startSingleTouch(e.touches[0]);
        } else if (e.touches.length === 2) {
            this.startPinchGesture(e.touches);
        }
    }

    startSingleTouch(touch) {
        this.touchState.isTouch = true;
        this.touchState.startX = touch.clientX;
        this.touchState.startY = touch.clientY;
        this.touchState.currentX = touch.clientX;
        this.touchState.currentY = touch.clientY;
        this.touchState.startTime = Date.now();
        this.touchState.gestureStarted = false;

        // Show touch zones briefly
        this.showTouchZones();

        // Check for double tap
        this.checkDoubleTap();
    }

    startPinchGesture(touches) {
        const distance = this.getDistance(touches[0], touches[1]);
        this.touchState.pinchDistance = distance;
        this.touchState.scale = 1;
        this.showGestureIndicator('🔍 Pinch to zoom');
    }

    handleTouchMove(e) {
        e.preventDefault();

        if (e.touches.length === 1) {
            this.handleSingleTouchMove(e.touches[0]);
        } else if (e.touches.length === 2) {
            this.handlePinchMove(e.touches);
        }
    }

    handleSingleTouchMove(touch) {
        if (!this.touchState.isTouch) return;

        this.touchState.currentX = touch.clientX;
        this.touchState.currentY = touch.clientY;

        const deltaX = this.touchState.currentX - this.touchState.startX;
        const deltaY = this.touchState.currentY - this.touchState.startY;
        const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);

        // Determine gesture direction
        if (distance > 20 && !this.touchState.gestureStarted) {
            this.touchState.gestureStarted = true;

            if (Math.abs(deltaX) > Math.abs(deltaY)) {
                // Horizontal swipe for seeking
                this.touchState.direction = deltaX > 0 ? 'right' : 'left';
                this.startSeekGesture(deltaX);
            } else {
                // Vertical swipe for volume/brightness
                this.touchState.direction = deltaY > 0 ? 'down' : 'up';
                this.startVolumeGesture(deltaY);
            }
        }

        // Continue gesture
        if (this.touchState.gestureStarted) {
            if (this.touchState.direction === 'left' || this.touchState.direction === 'right') {
                this.updateSeekGesture(deltaX);
            } else {
                this.updateVolumeGesture(deltaY);
            }
        }
    }

    handlePinchMove(touches) {
        const distance = this.getDistance(touches[0], touches[1]);
        const scale = distance / this.touchState.pinchDistance;

        if (Math.abs(scale - 1) > 0.1) {
            this.handlePinchZoom(scale);
        }
    }

    handleTouchEnd(e) {
        if (e.touches.length === 0) {
            this.completeTouchGesture();
        }
    }

    completeTouchGesture() {
        const duration = Date.now() - this.touchState.startTime;
        const deltaX = this.touchState.currentX - this.touchState.startX;
        const deltaY = this.touchState.currentY - this.touchState.startY;
        const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);

        this.hideTouchZones();
        this.hideGestureIndicator();

        if (!this.touchState.gestureStarted) {
            // Simple tap
            if (duration < 200 && distance < 10) {
                this.handleTap();
            }
        }

        // Reset touch state
        this.touchState.isTouch = false;
        this.touchState.gestureStarted = false;
        this.touchState.direction = null;
    }

    handleTap() {
        const rect = this.touchOverlay.getBoundingClientRect();
        const x = this.touchState.startX - rect.left;
        const width = rect.width;

        if (x < width / 3) {
            // Left third - rewind
            this.rewind(10);
        } else if (x > (2 * width) / 3) {
            // Right third - forward
            this.forward(10);
        } else {
            // Center - play/pause
            this.togglePlayPause();
        }
    }

    checkDoubleTap() {
        const now = Date.now();

        if (this.touchState.doubleTapTimer) {
            clearTimeout(this.touchState.doubleTapTimer);
            this.touchState.doubleTapTimer = null;

            if (now - this.touchState.lastTap < this.thresholds.doubleTapDelay) {
                this.handleDoubleTap();
                return;
            }
        }

        this.touchState.lastTap = now;
        this.touchState.doubleTapTimer = setTimeout(() => {
            this.touchState.doubleTapTimer = null;
        }, this.thresholds.doubleTapDelay);
    }

    handleDoubleTap() {
        // Toggle fullscreen on double tap
        this.toggleFullscreen();
        this.showGestureIndicator('⛶ Fullscreen toggled');
    }

    startSeekGesture(deltaX) {
        this.showGestureIndicator('⏪ Seeking...');
        this.videoContainer.classList.add('seeking');
    }

    updateSeekGesture(deltaX) {
        const seekTime = deltaX * this.thresholds.seekSensitivity;
        const newTime = Math.max(0, Math.min(this.video.duration, this.video.currentTime + seekTime));

        this.updateGestureIndicator(`⏪ ${seekTime > 0 ? '+' : ''}${seekTime.toFixed(1)}s`);
        this.showSeekPreview(newTime);
    }

    startVolumeGesture(deltaY) {
        this.showGestureIndicator('🔊 Volume...');
        this.videoContainer.classList.add('adjusting-volume');
    }

    updateVolumeGesture(deltaY) {
        const volumeChange = -deltaY / 200; // Negative for intuitive up = louder
        const newVolume = Math.max(0, Math.min(1, this.video.volume + volumeChange));

        this.video.volume = newVolume;
        this.updateGestureIndicator(`🔊 ${Math.round(newVolume * 100)}%`);
    }

    handlePinchZoom(scale) {
        // Apply zoom to video (within reasonable limits)
        const newScale = Math.max(0.5, Math.min(3, scale));
        this.video.style.transform = `scale(${newScale})`;
        this.updateGestureIndicator(`🔍 ${Math.round(newScale * 100)}%`);
    }

    // Mouse event handlers for desktop testing
    handleMouseStart(e) {
        this.startSingleTouch({ clientX: e.clientX, clientY: e.clientY });
    }

    handleMouseMove(e) {
        if (this.touchState.isTouch) {
            this.handleSingleTouchMove({ clientX: e.clientX, clientY: e.clientY });
        }
    }

    handleMouseEnd(e) {
        this.completeTouchGesture();
    }

    // Video control methods
    togglePlayPause() {
        if (this.video.paused) {
            this.video.play();
            this.showGestureIndicator('▶️ Play');
        } else {
            this.video.pause();
            this.showGestureIndicator('⏸️ Pause');
        }
    }

    rewind(seconds) {
        this.video.currentTime = Math.max(0, this.video.currentTime - seconds);
        this.showGestureIndicator(`⏪ -${seconds}s`);
        this.triggerHapticFeedback();
    }

    forward(seconds) {
        this.video.currentTime = Math.min(this.video.duration, this.video.currentTime + seconds);
        this.showGestureIndicator(`⏩ +${seconds}s`);
        this.triggerHapticFeedback();
    }

    toggleFullscreen() {
        if (!document.fullscreenElement) {
            this.videoContainer.requestFullscreen?.() ||
            this.videoContainer.webkitRequestFullscreen?.() ||
            this.videoContainer.mozRequestFullScreen?.();
        } else {
            document.exitFullscreen?.() ||
            document.webkitExitFullscreen?.() ||
            document.mozCancelFullScreen?.();
        }
    }

    // UI feedback methods
    showTouchZones() {
        this.touchOverlay.classList.add('active');
        setTimeout(() => {
            this.touchOverlay.classList.remove('active');
        }, 3000);
    }

    hideTouchZones() {
        this.touchOverlay.classList.remove('active');
    }

    showGestureIndicator(text) {
        this.gestureIndicator.textContent = text;
        this.gestureIndicator.classList.add('visible');
    }

    updateGestureIndicator(text) {
        this.gestureIndicator.textContent = text;
    }

    hideGestureIndicator() {
        this.gestureIndicator.classList.remove('visible');
        setTimeout(() => {
            this.gestureIndicator.textContent = '';
        }, 300);
    }

    showSeekPreview(time) {
        // Show thumbnail or time preview during seeking
        const minutes = Math.floor(time / 60);
        const seconds = Math.floor(time % 60);
        this.updateGestureIndicator(`⏪ ${minutes}:${seconds.toString().padStart(2, '0')}`);
    }

    triggerHapticFeedback() {
        // Haptic feedback for supported devices
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }
    }

    // Utility methods
    getDistance(touch1, touch2) {
        const dx = touch1.clientX - touch2.clientX;
        const dy = touch1.clientY - touch2.clientY;
        return Math.sqrt(dx * dx + dy * dy);
    }

    handleVideoTouch(e) {
        // Prevent default video controls on touch
        e.preventDefault();
    }

    createGestureIndicators() {
        // Add CSS classes for gesture feedback
        if (!document.querySelector('#touch-controls-styles')) {
            const style = document.createElement('style');
            style.id = 'touch-controls-styles';
            style.textContent = `
                .video-container.seeking .video-touch-overlay {
                    background: rgba(0, 0, 0, 0.3);
                }

                .video-container.adjusting-volume .video-touch-overlay {
                    background: rgba(0, 0, 255, 0.1);
                }

                .gesture-indicator {
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    background: rgba(0, 0, 0, 0.8);
                    color: white;
                    padding: 12px 20px;
                    border-radius: 25px;
                    font-size: 16px;
                    font-weight: bold;
                    opacity: 0;
                    transition: opacity 0.3s ease;
                    pointer-events: none;
                    z-index: 1000;
                }

                .gesture-indicator.visible {
                    opacity: 1;
                }
            `;
            document.head.appendChild(style);
        }
    }

    setupVideoControls() {
        // Enhanced video controls for mobile
        this.video.addEventListener('loadedmetadata', () => {
            this.createMobileProgressBar();
        });

        this.video.addEventListener('timeupdate', () => {
            this.updateMobileProgressBar();
        });
    }

    createMobileProgressBar() {
        if (this.mobileProgressBar) return;

        this.mobileProgressBar = document.createElement('div');
        this.mobileProgressBar.className = 'mobile-progress-bar';
        this.mobileProgressBar.innerHTML = `
            <div class="progress-track">
                <div class="progress-fill"></div>
                <div class="progress-thumb"></div>
            </div>
        `;

        this.videoContainer.appendChild(this.mobileProgressBar);

        // Touch handling for progress bar
        const track = this.mobileProgressBar.querySelector('.progress-track');
        track.addEventListener('touchstart', this.handleProgressTouch.bind(this));
        track.addEventListener('touchmove', this.handleProgressMove.bind(this));
    }

    updateMobileProgressBar() {
        if (!this.mobileProgressBar || !this.video.duration) return;

        const progress = (this.video.currentTime / this.video.duration) * 100;
        const fill = this.mobileProgressBar.querySelector('.progress-fill');
        const thumb = this.mobileProgressBar.querySelector('.progress-thumb');

        fill.style.width = `${progress}%`;
        thumb.style.left = `${progress}%`;
    }

    handleProgressTouch(e) {
        e.preventDefault();
        this.updateVideoTime(e.touches[0]);
    }

    handleProgressMove(e) {
        e.preventDefault();
        this.updateVideoTime(e.touches[0]);
    }

    updateVideoTime(touch) {
        const track = this.mobileProgressBar.querySelector('.progress-track');
        const rect = track.getBoundingClientRect();
        const x = touch.clientX - rect.left;
        const progress = Math.max(0, Math.min(1, x / rect.width));

        this.video.currentTime = progress * this.video.duration;
        this.triggerHapticFeedback();
    }
}

// Auto-initialize for video elements
document.addEventListener('DOMContentLoaded', function() {
    const videos = document.querySelectorAll('video');
    videos.forEach(video => {
        const transcript = document.querySelector('.transcript-container');
        if (video && transcript) {
            new VideoTouchControls(video, transcript);
        }
    });
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VideoTouchControls;
}
