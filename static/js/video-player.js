/**
 * Synchronized Video Player for Video Transcriber
 * This file contains JavaScript functionality for the synchronized video player feature.
 */

// Global variables for video player
let videoPlayer = null;
let videoMetadata = null;
let transcriptData = null;
let currentChapter = 0;
let syncEnabled = true;
let playbackSpeed = 1;

// DOM element cache for performance
const elements = {};

// Cache DOM elements on initialization
function cacheElements() {
    elements.videoSection = document.getElementById('videoSection');
    elements.transcriptSection = document.getElementById('transcriptSection');
    elements.videoPlayer = document.getElementById('videoPlayer');
    elements.chapterMarkers = document.getElementById('chapterMarkers');
    elements.keywordIndicators = document.getElementById('keywordIndicators');
    elements.questionIndicators = document.getElementById('questionIndicators');
    elements.chapterNavigation = document.getElementById('chapterNavigation');
    elements.chapterList = document.getElementById('chapterList');
    elements.transcriptContent = document.getElementById('transcriptContent');
    elements.playPauseBtn = document.getElementById('playPauseBtn');
    elements.syncBtn = document.getElementById('syncBtn');
    elements.speedBtn = document.getElementById('speedBtn');
    elements.chaptersBtn = document.getElementById('chaptersBtn');
    elements.currentTime = document.getElementById('currentTime');
    elements.duration = document.getElementById('duration');
    elements.transcriptSearch = document.getElementById('transcriptSearch');
}

// User Preferences Management
class UserPreferences {
    constructor() {
        this.storageKey = 'videoTranscriber_userPrefs';
        this.defaults = {
            playbackSpeed: 1,
            syncEnabled: true,
            volume: 1,
            chaptersVisible: false,
            transcriptFilterMode: 'all'
        };
        this.prefs = this.load();
    }

    load() {
        try {
            const stored = localStorage.getItem(this.storageKey);
            if (stored) {
                return { ...this.defaults, ...JSON.parse(stored) };
            }
        } catch (error) {
            console.warn('Failed to load user preferences:', error);
        }
        return { ...this.defaults };
    }

    save() {
        try {
            localStorage.setItem(this.storageKey, JSON.stringify(this.prefs));
        } catch (error) {
            console.warn('Failed to save user preferences:', error);
        }
    }

    get(key) {
        return this.prefs[key] ?? this.defaults[key];
    }

    set(key, value) {
        this.prefs[key] = value;
        this.save();
    }
}

// Enhanced Loading and Error Management
class UIStateManager {
    constructor() {
        this.loadingStates = new Map();
        this.errorHandlers = new Map();
    }

    showLoading(containerId, message = 'Loading...') {
        const container = document.getElementById(containerId);
        if (!container) return null;

        const loadingId = `loading_${Date.now()}`;
        const loadingDiv = document.createElement('div');
        loadingDiv.id = loadingId;
        loadingDiv.className = 'loading-spinner';
        loadingDiv.innerHTML = `
            <div class="spinner-animation"></div>
            <span class="loading-message">${message}</span>
        `;

        container.insertBefore(loadingDiv, container.firstChild);
        this.loadingStates.set(containerId, loadingId);
        return loadingId;
    }

    hideLoading(containerId) {
        const loadingId = this.loadingStates.get(containerId);
        if (loadingId) {
            const loadingElement = document.getElementById(loadingId);
            if (loadingElement) {
                loadingElement.remove();
            }
            this.loadingStates.delete(containerId);
        }
    }

    showError(containerId, error, retryCallback = null) {
        const container = document.getElementById(containerId);
        if (!container) return;

        // Hide any existing loading states
        this.hideLoading(containerId);

        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';

        const title = document.createElement('div');
        title.className = 'error-title';
        title.textContent = 'Something went wrong';

        const message = document.createElement('div');
        message.textContent = error.message || error.toString();

        errorDiv.appendChild(title);
        errorDiv.appendChild(message);

        if (retryCallback) {
            const actions = document.createElement('div');
            actions.className = 'error-actions';

            const retryBtn = document.createElement('button');
            retryBtn.className = 'retry-btn';
            retryBtn.textContent = 'Try Again';
            retryBtn.onclick = () => {
                errorDiv.remove();
                retryCallback();
            };

            const dismissBtn = document.createElement('button');
            dismissBtn.className = 'dismiss-btn';
            dismissBtn.textContent = 'Dismiss';
            dismissBtn.onclick = () => errorDiv.remove();

            actions.appendChild(retryBtn);
            actions.appendChild(dismissBtn);
            errorDiv.appendChild(actions);
        }

        container.insertBefore(errorDiv, container.firstChild);
    }

    clearErrors(containerId) {
        const container = document.getElementById(containerId);
        if (container) {
            const errors = container.querySelectorAll('.error-message');
            errors.forEach(error => error.remove());
        }
    }
}

// Initialize global managers
const userPrefs = new UserPreferences();
const uiState = new UIStateManager();

// Format time in MM:SS or HH:MM:SS format
function formatTime(seconds) {
    if (isNaN(seconds) || seconds < 0) return '00:00';

    seconds = Math.floor(seconds);

    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hrs > 0) {
        return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }

    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

// Check export format availability
function checkExportFormats() {
    fetch(`/api/export/formats`)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.formats) {
                // Update UI based on available formats
                Object.entries(data.formats).forEach(([format, info]) => {
                    const formatBtn = document.querySelector(`.action-card a[href$="/${format}"]`);
                    if (formatBtn) {
                        if (!info.available) {
                            formatBtn.classList.add('disabled');
                            formatBtn.title = `${format} export is not available (missing dependencies)`;
                        } else {
                            formatBtn.title = info.description || '';
                        }
                    }
                });
            }
        })
        .catch(error => {
            console.warn('Failed to check export formats:', error);
        });
}

// Generate all export formats
function generateExports() {
    const sessionId = document.querySelector('.session-id').textContent.trim();

    // Show loading state
    const exportBtn = document.querySelector('.generate-exports-btn');
    const originalText = exportBtn.textContent;
    exportBtn.textContent = 'Generating exports...';
    exportBtn.disabled = true;

    fetch(`/api/export/${sessionId}/generate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            formats: {
                srt: true,
                vtt: true,
                pdf: true,
                docx: true,
                enhanced_txt: true
            }
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            exportBtn.textContent = 'Exports generated!';
            setTimeout(() => {
                exportBtn.textContent = originalText;
                exportBtn.disabled = false;
            }, 3000);
        } else {
            exportBtn.textContent = 'Error generating exports';
            setTimeout(() => {
                exportBtn.textContent = originalText;
                exportBtn.disabled = false;
            }, 3000);
        }
    })
    .catch(error => {
        console.error('Error generating exports:', error);
        exportBtn.textContent = 'Error!';
        setTimeout(() => {
            exportBtn.textContent = originalText;
            exportBtn.disabled = false;
        }, 3000);
    });
}

// Check video availability for the current session
async function checkVideoAvailability() {
    const sessionId = document.querySelector('.session-id').textContent.trim();
    const containerId = 'videoSection';

    try {
        const response = await fetch(`/api/video/${sessionId}/metadata`);
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                // Video is available, show the video player action card
                const videoCard = document.querySelector('.action-card button[onclick="showVideoPlayer()"]')?.closest('.action-card');
                if (videoCard) {
                    videoCard.style.display = 'block';
                }
                return true;
            } else {
                console.log('Video not available:', data.error || 'No video file found');
                return false;
            }
        } else {
            console.log('Video metadata check failed:', response.status, response.statusText);
            return false;
        }
    } catch (error) {
        console.error('Video availability check failed:', error);
        return false;
    }
}

// Show video player and transcript
async function showVideoPlayer() {
    const containerId = 'videoSection';
    const sessionId = document.querySelector('.session-id').textContent.trim();

    try {
        // Clear any existing errors
        uiState.clearErrors(containerId);

        // Show sections and loading state
        if (elements.videoSection && elements.transcriptSection) {
            elements.videoSection.style.display = 'block';
            elements.transcriptSection.style.display = 'block';

            // Show enhanced loading indicator
            uiState.showLoading(containerId, 'Loading video player...');
        }

        // Load video metadata with retry capability
        const loadVideoMetadata = async () => {
            const metadataResponse = await fetch(`/api/video/${sessionId}/metadata`);
            if (!metadataResponse.ok) {
                throw new Error(`Failed to load video metadata: ${metadataResponse.status} ${metadataResponse.statusText}`);
            }

            videoMetadata = await metadataResponse.json();
            if (!videoMetadata.success) {
                throw new Error(videoMetadata.error || 'Video not available');
            }
        };

        await loadVideoMetadata();

        // Hide loading indicator
        uiState.hideLoading(containerId);

        // Initialize video player with preferences
        initializeVideoPlayer();

        // Load transcript data
        await loadTranscriptData();

        // Apply saved user preferences
        applyVideoPreferences();

        // Scroll to video section
        if (elements.videoSection) {
            elements.videoSection.scrollIntoView({ behavior: 'smooth' });
        }

    } catch (error) {
        console.error('Failed to load video player:', error);

        // Hide loading indicator
        uiState.hideLoading(containerId);

        // Show enhanced error message with retry option
        uiState.showError(containerId, error, () => showVideoPlayer());

        // Hide video sections if they were shown
        if (elements.videoSection) elements.videoSection.style.display = 'none';
        if (elements.transcriptSection) elements.transcriptSection.style.display = 'none';
    }
}

// Apply video player preferences
function applyVideoPreferences() {
    if (!videoPlayer) return;

    // Apply saved playback speed
    const savedSpeed = userPrefs.get('playbackSpeed');
    playbackSpeed = savedSpeed;
    videoPlayer.playbackRate = savedSpeed;
    if (elements.speedBtn) {
        elements.speedBtn.textContent = `${savedSpeed}x`;
    }

    // Apply saved volume
    const savedVolume = userPrefs.get('volume');
    videoPlayer.volume = savedVolume;

    // Apply sync preference
    syncEnabled = userPrefs.get('syncEnabled');
    if (elements.syncBtn) {
        elements.syncBtn.classList.toggle('active', syncEnabled);
        elements.syncBtn.title = syncEnabled ? 'Sync enabled' : 'Sync disabled';
    }

    // Apply chapters visibility
    const chaptersVisible = userPrefs.get('chaptersVisible');
    if (elements.chapterNavigation && chaptersVisible) {
        elements.chapterNavigation.style.display = 'block';
        if (elements.chaptersBtn) {
            elements.chaptersBtn.classList.add('active');
        }
    }
}

// Initialize video player
function initializeVideoPlayer() {
    videoPlayer = elements.videoPlayer;

    if (!videoPlayer) {
        throw new Error('Video player element not found');
    }

    // Setup video event listeners with error handling
    videoPlayer.addEventListener('loadedmetadata', function() {
        try {
            if (elements.duration) {
                elements.duration.textContent = formatTime(videoPlayer.duration);
            }
            createChapterMarkers();
            createProgressIndicators();
        } catch (error) {
            console.error('Error in loadedmetadata handler:', error);
        }
    });

    videoPlayer.addEventListener('timeupdate', function() {
        try {
            if (elements.currentTime) {
                elements.currentTime.textContent = formatTime(videoPlayer.currentTime);
            }
            updateCurrentChapter();
            if (syncEnabled) {
                highlightCurrentTranscriptSegment();
            }
        } catch (error) {
            console.error('Error in timeupdate handler:', error);
        }
    });

    videoPlayer.addEventListener('error', function(e) {
        console.error('Video player error:', e);
        const errorMsg = 'Video playback error. Please check your connection and try again.';
        uiState.showError('videoSection', { message: errorMsg }, () => {
            // Retry by reloading the video
            videoPlayer.load();
        });
    });

    // Save volume changes
    videoPlayer.addEventListener('volumechange', function() {
        userPrefs.set('volume', videoPlayer.volume);
    });

    // Setup enhanced control buttons
    setupVideoControls();
}

// Setup video controls
function setupVideoControls() {
    if (!elements.playPauseBtn || !elements.syncBtn || !elements.speedBtn || !elements.chaptersBtn) {
        console.error('Video control elements not found');
        return;
    }

    elements.playPauseBtn.addEventListener('click', function() {
        try {
            if (videoPlayer.paused) {
                videoPlayer.play();
            } else {
                videoPlayer.pause();
            }
        } catch (error) {
            console.error('Error controlling video playback:', error);
        }
    });

    elements.syncBtn.addEventListener('click', function() {
        syncEnabled = !syncEnabled;
        elements.syncBtn.classList.toggle('active', syncEnabled);
        elements.syncBtn.title = syncEnabled ? 'Sync enabled' : 'Sync disabled';

        // Save preference
        userPrefs.set('syncEnabled', syncEnabled);
    });

    elements.speedBtn.addEventListener('click', function() {
        const speeds = [0.5, 0.75, 1, 1.25, 1.5, 2];
        const currentIndex = speeds.indexOf(playbackSpeed);
        const nextIndex = (currentIndex + 1) % speeds.length;
        playbackSpeed = speeds[nextIndex];
        videoPlayer.playbackRate = playbackSpeed;
        elements.speedBtn.textContent = `${playbackSpeed}x`;

        // Save preference
        userPrefs.set('playbackSpeed', playbackSpeed);
    });

    elements.chaptersBtn.addEventListener('click', function() {
        if (!elements.chapterNavigation) return;

        const isVisible = elements.chapterNavigation.style.display !== 'none';
        elements.chapterNavigation.style.display = isVisible ? 'none' : 'block';
        elements.chaptersBtn.classList.toggle('active', !isVisible);

        // Save preference
        userPrefs.set('chaptersVisible', !isVisible);
    });
}

// Create chapter markers on video timeline
function createChapterMarkers() {
    if (!videoMetadata.chapters || !elements.chapterMarkers) return;

    // Clear existing markers
    elements.chapterMarkers.innerHTML = '';

    const duration = videoPlayer.duration;

    videoMetadata.chapters.forEach((chapter, index) => {
        const marker = document.createElement('div');
        marker.className = 'chapter-marker';
        marker.style.left = `${(chapter.time / duration) * 100}%`;
        marker.setAttribute('data-title', chapter.title);
        marker.addEventListener('click', () => seekToChapter(index));
        elements.chapterMarkers.appendChild(marker);
    });

    // Create chapter list
    createChapterList();
}

// Create chapter list
function createChapterList() {
    if (!videoMetadata.chapters || !elements.chapterList) return;

    elements.chapterList.innerHTML = '';

    videoMetadata.chapters.forEach((chapter, index) => {
        const item = document.createElement('div');
        item.className = 'chapter-item';
        item.innerHTML = `
            <div class="chapter-title">${chapter.title}</div>
            <div class="chapter-time">${formatTime(chapter.time)}</div>
        `;
        item.addEventListener('click', () => seekToChapter(index));
        elements.chapterList.appendChild(item);
    });
}

// Create progress indicators for keywords and questions
function createProgressIndicators() {
    const duration = videoPlayer.duration;
    createKeywordIndicators(duration);
    createQuestionIndicators(duration);
}

function createKeywordIndicators(duration) {
    if (!videoMetadata.keywords || !Array.isArray(videoMetadata.keywords) || !elements.keywordIndicators) return;

    // Clear existing indicators
    elements.keywordIndicators.innerHTML = '';

    videoMetadata.keywords.forEach(keyword => {
        // Handle actual keyword_matches structure - they don't have timestamps
        // Create approximate indicators based on keyword frequency distribution
        if (keyword.keyword && keyword.matches && Array.isArray(keyword.matches)) {
            keyword.matches.forEach((match, index) => {
                // Estimate timestamp based on position in matches and video duration
                const estimatedTime = (index / keyword.matches.length) * duration;
                const indicator = document.createElement('div');
                indicator.className = 'indicator-mark keyword-mark';
                indicator.style.left = `${(estimatedTime / duration) * 100}%`;
                indicator.title = `Keyword: ${keyword.keyword} (${keyword.matches.length} total matches)`;
                indicator.addEventListener('click', () => seekToTime(estimatedTime));
                elements.keywordIndicators.appendChild(indicator);
            });
        }
    });
}

function createQuestionIndicators(duration) {
    if (!videoMetadata.questions || !elements.questionIndicators) return;

    // Clear existing indicators
    elements.questionIndicators.innerHTML = '';

    videoMetadata.questions.forEach(question => {
        const indicator = document.createElement('div');
        indicator.className = 'indicator-mark question-mark';
        indicator.style.left = `${(question.start / duration) * 100}%`;
        indicator.title = `Question: ${question.text.substring(0, 50)}...`;
        indicator.addEventListener('click', () => seekToTime(question.start));
        elements.questionIndicators.appendChild(indicator);
    });
}

// Load transcript data for synchronized display
async function loadTranscriptData() {
    // For now, use the analysis data to create transcript segments
    // In a full implementation, this would load detailed segment data
    transcriptData = createTranscriptSegments();
    renderTranscript();
}

function createTranscriptSegments() {
    const segments = [];

    // Add question segments
    if (videoMetadata.questions && Array.isArray(videoMetadata.questions)) {
        videoMetadata.questions.forEach(question => {
            segments.push({
                start_time: question.start,
                end_time: question.start + 10, // Approximate duration
                text: question.text,
                type: 'question'
            });
        });
    }

    // Add keyword segments - handle the actual keyword_matches structure
    if (videoMetadata.keywords && Array.isArray(videoMetadata.keywords)) {
        videoMetadata.keywords.forEach(keyword => {
            // Handle actual keyword_matches structure - they don't have timestamps
            // Create approximate segments based on keyword frequency
            if (keyword.keyword && keyword.matches && Array.isArray(keyword.matches)) {
                keyword.matches.forEach((match, index) => {
                    // Estimate timestamp based on position in matches and video duration
                    // Default to 3600 seconds (1 hour) if total_duration is not available
                    const estimatedTime = (index / keyword.matches.length) * (videoMetadata.total_duration || 3600);
                    segments.push({
                        start_time: estimatedTime,
                        end_time: estimatedTime + 5, // Approximate duration
                        text: `[${keyword.keyword}] ${match.substring(0, 100)}...`,
                        type: 'keyword'
                    });
                });
            }
        });
    }

    // Add emphasis cue segments
    if (videoMetadata.emphasis_cues && Array.isArray(videoMetadata.emphasis_cues)) {
        videoMetadata.emphasis_cues.forEach(cue => {
            segments.push({
                start_time: cue.start,
                end_time: cue.start + 8, // Approximate duration
                text: cue.text,
                type: 'emphasis'
            });
        });
    }

    // Sort by start time
    segments.sort((a, b) => a.start_time - b.start_time);
    return segments;
}

function renderTranscript() {
    if (!elements.transcriptContent) {
        console.error('Transcript content element not found');
        return;
    }

    elements.transcriptContent.innerHTML = '';

    transcriptData.forEach((segment, index) => {
        const segmentEl = document.createElement('div');
        segmentEl.className = `transcript-segment ${segment.type}`;
        segmentEl.setAttribute('data-start', segment.start_time);
        segmentEl.innerHTML = `
            <div class="segment-time">${formatTime(segment.start_time)}</div>
            <div class="segment-text">${segment.text}</div>
        `;

        segmentEl.addEventListener('click', () => {
            seekToTime(segment.start_time);
        });

        elements.transcriptContent.appendChild(segmentEl);
    });

    // Setup transcript search and filters
    setupTranscriptControls();
}

function setupTranscriptControls() {
    if (!elements.transcriptSearch) {
        console.error('Transcript search element not found');
        return;
    }

    const filterButtons = document.querySelectorAll('.filter-btn');

    elements.transcriptSearch.addEventListener('input', function() {
        filterTranscript(this.value, getActiveFilter());
    });

    filterButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            filterButtons.forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            filterTranscript(elements.transcriptSearch.value, this.getAttribute('data-filter'));

            // Save filter preference
            userPrefs.set('transcriptFilterMode', this.getAttribute('data-filter'));
        });
    });

    // Apply saved filter preference
    const savedFilter = userPrefs.get('transcriptFilterMode');
    if (savedFilter) {
        const filterButton = document.querySelector(`.filter-btn[data-filter="${savedFilter}"]`);
        if (filterButton) {
            filterButtons.forEach(b => b.classList.remove('active'));
            filterButton.classList.add('active');
            filterTranscript('', savedFilter);
        }
    }
}

function getActiveFilter() {
    const activeBtn = document.querySelector('.filter-btn.active');
    return activeBtn ? activeBtn.getAttribute('data-filter') : 'all';
}

function filterTranscript(searchTerm, filter) {
    const segments = document.querySelectorAll('.transcript-segment');

    segments.forEach(segment => {
        const text = segment.textContent.toLowerCase();
        const type = segment.classList.contains('question') ? 'questions' :
                    segment.classList.contains('keyword') ? 'keywords' : 'all';

        const matchesSearch = !searchTerm || text.includes(searchTerm.toLowerCase());
        const matchesFilter = filter === 'all' || filter === type;

        segment.style.display = matchesSearch && matchesFilter ? 'flex' : 'none';
    });
}

// Video synchronization functions
function seekToTime(time) {
    if (videoPlayer) {
        videoPlayer.currentTime = time;
    }
}

function seekToChapter(chapterIndex) {
    if (videoMetadata.chapters && videoMetadata.chapters[chapterIndex]) {
        seekToTime(videoMetadata.chapters[chapterIndex].time);
        updateChapterHighlight(chapterIndex);
    }
}

function updateCurrentChapter() {
    if (!videoMetadata.chapters) return;

    const currentTime = videoPlayer.currentTime;
    let newChapter = 0;

    for (let i = videoMetadata.chapters.length - 1; i >= 0; i--) {
        if (currentTime >= videoMetadata.chapters[i].time) {
            newChapter = i;
            break;
        }
    }

    if (newChapter !== currentChapter) {
        currentChapter = newChapter;
        updateChapterHighlight(currentChapter);
    }
}

function updateChapterHighlight(chapterIndex) {
    const chapterItems = document.querySelectorAll('.chapter-item');
    chapterItems.forEach((item, index) => {
        item.classList.toggle('current', index === chapterIndex);
    });
}

function highlightCurrentTranscriptSegment() {
    if (!transcriptData) return;

    const currentTime = videoPlayer.currentTime;
    const segments = document.querySelectorAll('.transcript-segment');

    segments.forEach((segment, index) => {
        const startTime = parseFloat(segment.getAttribute('data-start'));
        const endTime = index < transcriptData.length - 1 ?
                      parseFloat(segments[index + 1].getAttribute('data-start')) :
                      startTime + 10;

        const isCurrent = currentTime >= startTime && currentTime < endTime;
        segment.classList.toggle('current', isCurrent);

        if (isCurrent && syncEnabled) {
            segment.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    });
}

// Add initialization on DOMContentLoaded
document.addEventListener('DOMContentLoaded', function() {
    // Cache DOM elements for better performance
    cacheElements();

    // Apply saved user preferences
    applySavedPreferences();

    // Animate stat numbers
    const statNumbers = document.querySelectorAll('.stat-number');
    statNumbers.forEach(stat => {
        const finalValue = parseInt(stat.textContent);
        if (isNaN(finalValue)) return;

        let currentValue = 0;
        const increment = Math.ceil(finalValue / 20);

        const timer = setInterval(() => {
            currentValue += increment;
            if (currentValue >= finalValue) {
                currentValue = finalValue;
                clearInterval(timer);
            }
            stat.textContent = currentValue;
        }, 50);
    });

    // Animate frequency bars
    setTimeout(() => {
        const frequencyFills = document.querySelectorAll('.frequency-fill');
        frequencyFills.forEach(fill => {
            const width = fill.style.width;
            fill.style.width = '0%';
            setTimeout(() => {
                fill.style.width = width;
            }, 100);
        });
    }, 500);

    // Check export format availability
    checkExportFormats();

    // Check if video is available
    checkVideoAvailability();
});

// Apply saved user preferences
function applySavedPreferences() {
    // Apply playback speed preference
    playbackSpeed = userPrefs.get('playbackSpeed');

    // Apply sync preference
    syncEnabled = userPrefs.get('syncEnabled');

    // Apply filter mode preference
    const filterMode = userPrefs.get('transcriptFilterMode');
    const filterButtons = document.querySelectorAll('.filter-btn');
    filterButtons.forEach(btn => {
        btn.classList.toggle('active', btn.dataset.filter === filterMode);
    });
}

// Expose these functions to be called from HTML
window.showVideoPlayer = showVideoPlayer;
window.generateExports = generateExports;
