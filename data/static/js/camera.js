/**
 * Mobile Camera Integration for Video Recording
 * Handles camera access, recording, and file management on mobile devices
 */

class MobileCameraManager {
    constructor() {
        this.mediaStream = null;
        this.mediaRecorder = null;
        this.recordedChunks = [];
        this.isRecording = false;
        this.isInitialized = false;

        this.init();
    }

    async init() {
        this.checkCameraSupport();
        this.setupEventListeners();
        this.isInitialized = true;
    }

    checkCameraSupport() {
        this.capabilities = {
            mediaDevices: 'mediaDevices' in navigator,
            getUserMedia: 'getUserMedia' in navigator.mediaDevices,
            mediaRecorder: 'MediaRecorder' in window,
            fileSystemAccess: 'showSaveFilePicker' in window,
            shareAPI: 'share' in navigator
        };

        console.log('Camera capabilities:', this.capabilities);
    }

    setupEventListeners() {
        // Listen for camera button clicks
        document.addEventListener('click', (e) => {
            if (e.target.matches('.camera-record-btn, .camera-record-btn *')) {
                e.preventDefault();
                this.toggleRecording();
            }

            if (e.target.matches('.camera-switch-btn, .camera-switch-btn *')) {
                e.preventDefault();
                this.switchCamera();
            }
        });

        // Handle orientation changes
        window.addEventListener('orientationchange', () => {
            setTimeout(() => this.adjustCameraLayout(), 100);
        });

        // Handle visibility changes (pause recording when app goes to background)
        document.addEventListener('visibilitychange', () => {
            if (document.hidden && this.isRecording) {
                this.pauseRecording();
            }
        });
    }

    async requestCameraAccess(constraints = {}) {
        if (!this.capabilities.mediaDevices || !this.capabilities.getUserMedia) {
            throw new Error('Camera access not supported on this device');
        }

        const defaultConstraints = {
            video: {
                facingMode: 'environment', // Use back camera by default
                width: { ideal: 1920, max: 1920 },
                height: { ideal: 1080, max: 1080 },
                frameRate: { ideal: 30, max: 60 }
            },
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                autoGainControl: true,
                sampleRate: 44100
            }
        };

        const finalConstraints = { ...defaultConstraints, ...constraints };

        try {
            this.mediaStream = await navigator.mediaDevices.getUserMedia(finalConstraints);
            return this.mediaStream;
        } catch (error) {
            console.error('Camera access failed:', error);
            throw this.handleCameraError(error);
        }
    }

    handleCameraError(error) {
        const errorMessages = {
            'NotFoundError': 'No camera found on this device',
            'NotAllowedError': 'Camera access denied. Please allow camera permissions.',
            'NotReadableError': 'Camera is being used by another application',
            'OverconstrainedError': 'Camera settings not supported on this device',
            'SecurityError': 'Camera access blocked due to security settings',
            'TypeError': 'Camera constraints are invalid'
        };

        const message = errorMessages[error.name] || `Camera error: ${error.message}`;
        return new Error(message);
    }

    async startRecording() {
        if (this.isRecording) {
            throw new Error('Recording already in progress');
        }

        try {
            // Request camera access
            const stream = await this.requestCameraAccess();

            // Setup media recorder
            const options = {
                mimeType: this.getSupportedMimeType(),
                videoBitsPerSecond: 2500000, // 2.5 Mbps for good quality
                audioBitsPerSecond: 128000   // 128 kbps for audio
            };

            this.mediaRecorder = new MediaRecorder(stream, options);
            this.recordedChunks = [];

            // Setup recording event handlers
            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.recordedChunks.push(event.data);
                }
            };

            this.mediaRecorder.onstop = () => {
                this.handleRecordingComplete();
            };

            this.mediaRecorder.onerror = (error) => {
                console.error('MediaRecorder error:', error);
                this.showError('Recording failed: ' + error.message);
                this.stopRecording();
            };

            // Start recording
            this.mediaRecorder.start(1000); // Collect data every second
            this.isRecording = true;

            // Update UI
            this.updateRecordingUI(true);
            this.showCameraPreview(stream);

            // Start recording timer
            this.startRecordingTimer();

            return true;

        } catch (error) {
            console.error('Failed to start recording:', error);
            this.showError(error.message);
            return false;
        }
    }

    getSupportedMimeType() {
        const types = [
            'video/webm;codecs=vp9,opus',
            'video/webm;codecs=vp8,opus',
            'video/webm;codecs=h264,opus',
            'video/mp4;codecs=h264,aac',
            'video/webm'
        ];

        for (const type of types) {
            if (MediaRecorder.isTypeSupported(type)) {
                return type;
            }
        }

        return 'video/webm'; // Fallback
    }

    async stopRecording() {
        if (!this.isRecording || !this.mediaRecorder) {
            return;
        }

        this.isRecording = false;
        this.mediaRecorder.stop();

        // Stop all media tracks
        if (this.mediaStream) {
            this.mediaStream.getTracks().forEach(track => track.stop());
            this.mediaStream = null;
        }

        // Update UI
        this.updateRecordingUI(false);
        this.hideCameraPreview();
        this.stopRecordingTimer();
    }

    pauseRecording() {
        if (this.isRecording && this.mediaRecorder && this.mediaRecorder.state === 'recording') {
            this.mediaRecorder.pause();
            this.updateRecordingUI(false, true); // paused state
        }
    }

    resumeRecording() {
        if (this.mediaRecorder && this.mediaRecorder.state === 'paused') {
            this.mediaRecorder.resume();
            this.updateRecordingUI(true);
        }
    }

    async toggleRecording() {
        if (this.isRecording) {
            await this.stopRecording();
        } else {
            await this.startRecording();
        }
    }

    async switchCamera() {
        if (!this.mediaStream) return;

        const videoTrack = this.mediaStream.getVideoTracks()[0];
        const currentFacingMode = videoTrack.getSettings().facingMode;
        const newFacingMode = currentFacingMode === 'user' ? 'environment' : 'user';

        try {
            // Stop current stream
            this.mediaStream.getTracks().forEach(track => track.stop());

            // Start new stream with different camera
            const newStream = await this.requestCameraAccess({
                video: { facingMode: newFacingMode }
            });

            // Update preview
            this.showCameraPreview(newStream);

            // Update media recorder if recording
            if (this.isRecording && this.mediaRecorder) {
                // Note: Switching cameras during recording requires stopping and restarting
                // This is a limitation of the MediaRecorder API
                this.showNotification('Camera switched. Recording will restart.');
                await this.stopRecording();
                setTimeout(() => this.startRecording(), 500);
            }

        } catch (error) {
            console.error('Failed to switch camera:', error);
            this.showError('Failed to switch camera: ' + error.message);
        }
    }

    handleRecordingComplete() {
        if (this.recordedChunks.length === 0) {
            this.showError('No video data recorded');
            return;
        }

        const blob = new Blob(this.recordedChunks, {
            type: this.getSupportedMimeType()
        });

        const fileName = `mobile-recording-${Date.now()}.webm`;
        const file = new File([blob], fileName, { type: blob.type });

        // Create preview and upload options
        this.showRecordingPreview(file, blob);
    }

    showCameraPreview(stream) {
        let preview = document.getElementById('camera-preview');
        if (!preview) {
            preview = document.createElement('video');
            preview.id = 'camera-preview';
            preview.autoplay = true;
            preview.muted = true;
            preview.playsInline = true;
            preview.className = 'camera-preview';

            // Add to camera container
            const container = this.getCameraContainer();
            container.appendChild(preview);
        }

        preview.srcObject = stream;
        preview.style.display = 'block';
    }

    hideCameraPreview() {
        const preview = document.getElementById('camera-preview');
        if (preview) {
            preview.style.display = 'none';
            preview.srcObject = null;
        }
    }

    showRecordingPreview(file, blob) {
        const url = URL.createObjectURL(blob);

        // Create preview modal
        const modal = document.createElement('div');
        modal.className = 'recording-preview-modal';
        modal.innerHTML = `
            <div class="recording-preview-content">
                <div class="recording-preview-header">
                    <h3>Recording Complete</h3>
                    <button class="close-preview-btn">&times;</button>
                </div>
                <div class="recording-preview-body">
                    <video class="recording-preview-video" controls>
                        <source src="${url}" type="${file.type}">
                    </video>
                    <div class="recording-info">
                        <p><strong>File:</strong> ${file.name}</p>
                        <p><strong>Size:</strong> ${this.formatFileSize(file.size)}</p>
                        <p><strong>Duration:</strong> <span id="recording-duration">Loading...</span></p>
                    </div>
                </div>
                <div class="recording-preview-actions">
                    <button class="btn btn-secondary discard-recording-btn">Discard</button>
                    <button class="btn btn-primary upload-recording-btn">Upload for Transcription</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Setup event listeners
        modal.querySelector('.close-preview-btn').onclick = () => this.closeRecordingPreview(modal, url);
        modal.querySelector('.discard-recording-btn').onclick = () => this.closeRecordingPreview(modal, url);
        modal.querySelector('.upload-recording-btn').onclick = () => this.uploadRecording(file, modal, url);

        // Get video duration
        const video = modal.querySelector('.recording-preview-video');
        video.onloadedmetadata = () => {
            document.getElementById('recording-duration').textContent = this.formatDuration(video.duration);
        };

        // Show modal
        modal.style.display = 'flex';
    }

    closeRecordingPreview(modal, url) {
        URL.revokeObjectURL(url);
        modal.remove();
    }

    async uploadRecording(file, modal, url) {
        try {
            // Show upload progress
            const uploadBtn = modal.querySelector('.upload-recording-btn');
            uploadBtn.textContent = 'Uploading...';
            uploadBtn.disabled = true;

            // Create form data
            const formData = new FormData();
            formData.append('video', file);
            formData.append('source', 'mobile-recording');

            // Upload to server
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                const result = await response.json();
                this.showSuccess('Recording uploaded successfully!');

                // Redirect to transcription session
                if (result.session_id) {
                    window.location.href = `/sessions/${result.session_id}`;
                }
            } else {
                throw new Error('Upload failed');
            }

        } catch (error) {
            console.error('Upload failed:', error);
            this.showError('Failed to upload recording: ' + error.message);

            // Reset button
            const uploadBtn = modal.querySelector('.upload-recording-btn');
            uploadBtn.textContent = 'Upload for Transcription';
            uploadBtn.disabled = false;
        } finally {
            this.closeRecordingPreview(modal, url);
        }
    }

    getCameraContainer() {
        let container = document.getElementById('camera-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'camera-container';
            container.className = 'camera-container';
            document.body.appendChild(container);
        }
        return container;
    }

    updateRecordingUI(isRecording, isPaused = false) {
        const recordBtn = document.querySelector('.camera-record-btn');
        const recordIcon = document.querySelector('.record-icon');
        const recordingIndicator = document.querySelector('.recording-indicator');

        if (recordBtn) {
            if (isRecording && !isPaused) {
                recordBtn.classList.add('recording');
                recordBtn.innerHTML = '<i class="fas fa-stop record-icon"></i> Stop Recording';
            } else if (isPaused) {
                recordBtn.classList.add('paused');
                recordBtn.innerHTML = '<i class="fas fa-play record-icon"></i> Resume';
            } else {
                recordBtn.classList.remove('recording', 'paused');
                recordBtn.innerHTML = '<i class="fas fa-video record-icon"></i> Start Recording';
            }
        }

        // Show/hide recording indicator
        if (recordingIndicator) {
            recordingIndicator.style.display = isRecording && !isPaused ? 'block' : 'none';
        }
    }

    startRecordingTimer() {
        this.recordingStartTime = Date.now();
        this.recordingTimer = setInterval(() => {
            const elapsed = Date.now() - this.recordingStartTime;
            const duration = this.formatDuration(elapsed / 1000);

            const timerDisplay = document.querySelector('.recording-timer');
            if (timerDisplay) {
                timerDisplay.textContent = duration;
            }
        }, 1000);
    }

    stopRecordingTimer() {
        if (this.recordingTimer) {
            clearInterval(this.recordingTimer);
            this.recordingTimer = null;
        }
    }

    adjustCameraLayout() {
        const preview = document.getElementById('camera-preview');
        if (preview && preview.style.display !== 'none') {
            // Adjust camera preview for orientation
            const isLandscape = window.orientation === 90 || window.orientation === -90;
            preview.style.width = isLandscape ? '100vw' : '100%';
            preview.style.height = isLandscape ? '100vh' : 'auto';
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    formatDuration(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);

        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }

    showNotification(message) {
        // Use existing notification system or create simple toast
        console.log('Camera notification:', message);

        if (window.pwaApp && window.pwaApp.showNotification) {
            window.pwaApp.showNotification(message, 'info');
        } else {
            alert(message); // Fallback
        }
    }

    showError(message) {
        console.error('Camera error:', message);

        if (window.pwaApp && window.pwaApp.showNotification) {
            window.pwaApp.showNotification(message, 'error');
        } else {
            alert('Error: ' + message); // Fallback
        }
    }

    showSuccess(message) {
        console.log('Camera success:', message);

        if (window.pwaApp && window.pwaApp.showNotification) {
            window.pwaApp.showNotification(message, 'success');
        } else {
            alert(message); // Fallback
        }
    }
}

// Initialize camera manager when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if ('mediaDevices' in navigator && 'getUserMedia' in navigator.mediaDevices) {
        window.cameraManager = new MobileCameraManager();
    } else {
        console.log('Camera features not supported on this device');
    }
});
