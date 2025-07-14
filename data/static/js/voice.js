/**
 * Voice Input Manager for Mobile Voice Recognition
 * Handles speech-to-text for adding notes, keywords, and voice commands
 */

class VoiceInputManager {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.isInitialized = false;
        this.currentLanguage = 'en-US';
        this.activeInput = null;

        this.init();
    }

    async init() {
        this.checkVoiceSupport();
        this.setupSpeechRecognition();
        this.setupEventListeners();
        this.isInitialized = true;
    }

    checkVoiceSupport() {
        this.capabilities = {
            speechRecognition: 'webkitSpeechRecognition' in window || 'SpeechRecognition' in window,
            speechSynthesis: 'speechSynthesis' in window,
            mediaDevices: 'mediaDevices' in navigator,
            audioContext: 'AudioContext' in window || 'webkitAudioContext' in window
        };

        console.log('Voice capabilities:', this.capabilities);
    }

    setupSpeechRecognition() {
        if (!this.capabilities.speechRecognition) {
            console.warn('Speech recognition not supported');
            return;
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        this.recognition = new SpeechRecognition();

        // Configure recognition settings
        this.recognition.continuous = false;
        this.recognition.interimResults = true;
        this.recognition.maxAlternatives = 3;
        this.recognition.lang = this.currentLanguage;

        // Setup event handlers
        this.recognition.onstart = () => {
            console.log('Voice recognition started');
            this.updateVoiceUI(true);
            this.showVoiceIndicator();
        };

        this.recognition.onresult = (event) => {
            this.handleVoiceResult(event);
        };

        this.recognition.onerror = (event) => {
            console.error('Voice recognition error:', event.error);
            this.handleVoiceError(event.error);
        };

        this.recognition.onend = () => {
            console.log('Voice recognition ended');
            this.isListening = false;
            this.updateVoiceUI(false);
            this.hideVoiceIndicator();
        };
    }

    setupEventListeners() {
        // Voice button clicks
        document.addEventListener('click', (e) => {
            if (e.target.matches('.voice-input-btn, .voice-input-btn *')) {
                e.preventDefault();
                const input = e.target.closest('.voice-input-container')?.querySelector('input, textarea');
                this.toggleVoiceInput(input);
            }

            if (e.target.matches('.voice-command-btn, .voice-command-btn *')) {
                e.preventDefault();
                this.startVoiceCommand();
            }
        });

        // Focus events for input fields
        document.addEventListener('focus', (e) => {
            if (e.target.matches('input[type="text"], textarea')) {
                this.setupVoiceButton(e.target);
            }
        }, true);

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + Shift + V for voice input
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'V') {
                e.preventDefault();
                const activeElement = document.activeElement;
                if (activeElement.matches('input, textarea')) {
                    this.toggleVoiceInput(activeElement);
                }
            }
        });
    }

    setupVoiceButton(input) {
        if (!this.capabilities.speechRecognition) return;

        // Check if voice button already exists
        const container = input.closest('.voice-input-container');
        if (container && container.querySelector('.voice-input-btn')) {
            return;
        }

        // Create voice input container if it doesn't exist
        if (!container) {
            const wrapper = document.createElement('div');
            wrapper.className = 'voice-input-container';
            input.parentNode.insertBefore(wrapper, input);
            wrapper.appendChild(input);
        }

        // Create voice button
        const voiceBtn = document.createElement('button');
        voiceBtn.type = 'button';
        voiceBtn.className = 'voice-input-btn';
        voiceBtn.innerHTML = '<i class="fas fa-microphone"></i>';
        voiceBtn.title = 'Voice input (Ctrl+Shift+V)';

        // Add button to container
        const targetContainer = input.closest('.voice-input-container');
        targetContainer.appendChild(voiceBtn);
    }

    async toggleVoiceInput(input) {
        if (!input || !this.capabilities.speechRecognition) {
            this.showError('Voice input not available');
            return;
        }

        if (this.isListening) {
            this.stopVoiceInput();
        } else {
            await this.startVoiceInput(input);
        }
    }

    async startVoiceInput(input) {
        if (!this.recognition) {
            this.showError('Speech recognition not initialized');
            return;
        }

        try {
            // Store active input
            this.activeInput = input;

            // Request microphone permission
            await this.requestMicrophonePermission();

            // Set language based on input or page language
            const inputLang = input.getAttribute('lang') || document.documentElement.lang || 'en-US';
            this.setLanguage(inputLang);

            // Start recognition
            this.recognition.start();
            this.isListening = true;

        } catch (error) {
            console.error('Failed to start voice input:', error);
            this.showError('Failed to start voice input: ' + error.message);
        }
    }

    stopVoiceInput() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
        }
    }

    async startVoiceCommand() {
        // Voice commands for app control
        const commands = {
            'upload video': () => document.querySelector('.upload-btn')?.click(),
            'start recording': () => window.cameraManager?.startRecording(),
            'stop recording': () => window.cameraManager?.stopRecording(),
            'go to sessions': () => window.location.href = '/sessions',
            'go home': () => window.location.href = '/',
            'play video': () => document.querySelector('video')?.play(),
            'pause video': () => document.querySelector('video')?.pause(),
            'fullscreen': () => this.toggleFullscreen()
        };

        if (!this.recognition) {
            this.showError('Voice commands not available');
            return;
        }

        try {
            this.activeCommands = commands;
            this.recognition.start();
            this.isListening = true;
            this.showNotification('Listening for voice commands...');

        } catch (error) {
            console.error('Failed to start voice commands:', error);
            this.showError('Voice commands failed: ' + error.message);
        }
    }

    handleVoiceResult(event) {
        const results = event.results;
        let finalTranscript = '';
        let interimTranscript = '';

        // Process all results
        for (let i = event.resultIndex; i < results.length; i++) {
            const result = results[i];

            if (result.isFinal) {
                finalTranscript += result[0].transcript;
            } else {
                interimTranscript += result[0].transcript;
            }
        }

        // Handle voice commands
        if (this.activeCommands) {
            this.processVoiceCommand(finalTranscript.toLowerCase().trim());
            return;
        }

        // Handle text input
        if (this.activeInput) {
            this.updateInputWithVoice(finalTranscript, interimTranscript);
        }
    }

    processVoiceCommand(command) {
        if (!command) return;

        console.log('Voice command:', command);

        // Find matching command
        const matchedCommand = Object.keys(this.activeCommands).find(cmd =>
            command.includes(cmd) || this.fuzzyMatch(command, cmd)
        );

        if (matchedCommand) {
            this.showSuccess(`Executing: ${matchedCommand}`);
            this.activeCommands[matchedCommand]();
        } else {
            this.showError(`Command not recognized: "${command}"`);
        }

        // Clear commands after processing
        this.activeCommands = null;
    }

    fuzzyMatch(input, command) {
        // Simple fuzzy matching for voice commands
        const inputWords = input.split(' ');
        const commandWords = command.split(' ');

        const matches = commandWords.filter(word =>
            inputWords.some(inputWord =>
                inputWord.includes(word) || word.includes(inputWord)
            )
        );

        return matches.length >= commandWords.length * 0.7; // 70% match threshold
    }

    updateInputWithVoice(finalText, interimText) {
        if (!this.activeInput) return;

        const currentValue = this.activeInput.value;
        const cursorPosition = this.activeInput.selectionStart;

        if (finalText) {
            // Insert final text at cursor position
            const beforeCursor = currentValue.substring(0, cursorPosition);
            const afterCursor = currentValue.substring(this.activeInput.selectionEnd);

            // Add space before text if needed
            const needsSpace = beforeCursor.length > 0 && !beforeCursor.endsWith(' ');
            const textToInsert = (needsSpace ? ' ' : '') + finalText;

            this.activeInput.value = beforeCursor + textToInsert + afterCursor;

            // Move cursor to end of inserted text
            const newPosition = cursorPosition + textToInsert.length;
            this.activeInput.setSelectionRange(newPosition, newPosition);

            // Trigger input event
            this.activeInput.dispatchEvent(new Event('input', { bubbles: true }));

            this.showInterimText(''); // Clear interim display
        } else if (interimText) {
            // Show interim text as preview
            this.showInterimText(interimText);
        }
    }

    showInterimText(text) {
        let indicator = document.querySelector('.voice-interim-text');

        if (text) {
            if (!indicator) {
                indicator = document.createElement('div');
                indicator.className = 'voice-interim-text';
                document.body.appendChild(indicator);
            }

            indicator.textContent = text;
            indicator.style.display = 'block';

            // Position near active input
            if (this.activeInput) {
                const rect = this.activeInput.getBoundingClientRect();
                indicator.style.left = rect.left + 'px';
                indicator.style.top = (rect.bottom + 5) + 'px';
            }
        } else if (indicator) {
            indicator.style.display = 'none';
        }
    }

    handleVoiceError(error) {
        const errorMessages = {
            'no-speech': 'No speech detected. Please try again.',
            'audio-capture': 'Microphone access failed. Please check permissions.',
            'not-allowed': 'Microphone access denied. Please allow microphone permissions.',
            'network': 'Network error. Please check your connection.',
            'service-not-allowed': 'Speech recognition service not available.',
            'bad-grammar': 'Speech recognition grammar error.',
            'language-not-supported': 'Language not supported for speech recognition.'
        };

        const message = errorMessages[error] || `Speech recognition error: ${error}`;
        this.showError(message);

        // Reset state
        this.isListening = false;
        this.activeInput = null;
        this.activeCommands = null;
        this.updateVoiceUI(false);
    }

    async requestMicrophonePermission() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error('Microphone access not supported');
        }

        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            // Stop the stream immediately - we just needed permission
            stream.getTracks().forEach(track => track.stop());
            return true;
        } catch (error) {
            throw new Error('Microphone permission denied');
        }
    }

    setLanguage(languageCode) {
        if (this.recognition) {
            this.recognition.lang = languageCode;
            this.currentLanguage = languageCode;
        }
    }

    updateVoiceUI(isListening) {
        const voiceButtons = document.querySelectorAll('.voice-input-btn, .voice-command-btn');

        voiceButtons.forEach(btn => {
            if (isListening) {
                btn.classList.add('listening');
                btn.innerHTML = '<i class="fas fa-microphone-slash"></i>';
                btn.title = 'Stop voice input';
            } else {
                btn.classList.remove('listening');
                btn.innerHTML = '<i class="fas fa-microphone"></i>';
                btn.title = 'Voice input (Ctrl+Shift+V)';
            }
        });
    }

    showVoiceIndicator() {
        let indicator = document.querySelector('.voice-listening-indicator');

        if (!indicator) {
            indicator = document.createElement('div');
            indicator.className = 'voice-listening-indicator';
            indicator.innerHTML = `
                <div class="voice-wave-animation">
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                    <div class="wave-bar"></div>
                </div>
                <span>Listening...</span>
            `;
            document.body.appendChild(indicator);
        }

        indicator.style.display = 'flex';
    }

    hideVoiceIndicator() {
        const indicator = document.querySelector('.voice-listening-indicator');
        if (indicator) {
            indicator.style.display = 'none';
        }

        this.showInterimText(''); // Clear interim text
    }

    toggleFullscreen() {
        if (document.fullscreenElement) {
            document.exitFullscreen();
        } else {
            document.documentElement.requestFullscreen();
        }
    }

    showNotification(message) {
        console.log('Voice notification:', message);

        if (window.pwaApp && window.pwaApp.showNotification) {
            window.pwaApp.showNotification(message, 'info');
        }
    }

    showError(message) {
        console.error('Voice error:', message);

        if (window.pwaApp && window.pwaApp.showNotification) {
            window.pwaApp.showNotification(message, 'error');
        }
    }

    showSuccess(message) {
        console.log('Voice success:', message);

        if (window.pwaApp && window.pwaApp.showNotification) {
            window.pwaApp.showNotification(message, 'success');
        }
    }
}

// Initialize voice manager when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        window.voiceManager = new VoiceInputManager();
    } else {
        console.log('Voice recognition not supported on this device');
    }
});
