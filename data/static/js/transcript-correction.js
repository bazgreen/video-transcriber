/**
 * Transcript Correction Client
 * Handles UI interactions for automated transcript correction and quality assurance
 */

class TranscriptCorrectionClient {
    constructor() {
        this.currentSuggestions = [];
        this.currentSessionId = null;
        this.customDictionary = new Map();
        this.originalTranscript = '';
        this.isAnalyzing = false;
        
        this.initializeEventListeners();
        this.loadStoredData();
    }
    
    initializeEventListeners() {
        // Auto-save transcript changes
        const editor = document.getElementById('transcriptEditor');
        if (editor) {
            editor.addEventListener('input', this.debounce(() => {
                this.saveTranscriptToStorage();
            }, 1000));
        }
    }
    
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    loadStoredData() {
        // Load custom dictionary from localStorage
        const stored = localStorage.getItem('transcriptCorrection_customDict');
        if (stored) {
            this.customDictionary = new Map(JSON.parse(stored));
            this.updateCustomTermsDisplay();
        }
        
        // Load saved transcript
        const savedTranscript = localStorage.getItem('transcriptCorrection_current');
        if (savedTranscript) {
            document.getElementById('transcriptEditor').innerText = savedTranscript;
        }
    }
    
    saveTranscriptToStorage() {
        const transcript = document.getElementById('transcriptEditor').innerText;
        localStorage.setItem('transcriptCorrection_current', transcript);
    }
    
    async analyzeQuality() {
        const transcript = this.getTranscriptContent();
        if (!transcript.trim()) {
            this.showAlert('Please enter a transcript to analyze.', 'warning');
            return;
        }
        
        this.setAnalyzing(true);
        
        try {
            const response = await fetch('/api/correction/quality-analysis', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    transcript: transcript,
                    session_id: this.currentSessionId 
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            if (result.success) {
                this.displayQualityMetrics(result.quality_metrics);
                this.currentSessionId = result.session_id;
            } else {
                throw new Error(result.error || 'Failed to analyze transcript quality');
            }
        } catch (error) {
            console.error('Quality analysis error:', error);
            this.showAlert('Failed to analyze transcript quality: ' + error.message, 'danger');
        } finally {
            this.setAnalyzing(false);
        }
    }
    
    async generateSuggestions() {
        const transcript = this.getTranscriptContent();
        if (!transcript.trim()) {
            this.showAlert('Please enter a transcript to correct.', 'warning');
            return;
        }
        
        this.setAnalyzing(true);
        
        try {
            const industryDict = document.getElementById('industrySelect').value;
            const customDict = Object.fromEntries(this.customDictionary);
            
            const response = await fetch('/api/correction/suggestions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    transcript: transcript,
                    session_id: this.currentSessionId,
                    industry_dictionary: industryDict || null,
                    custom_dictionary: customDict
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const result = await response.json();
            if (result.success) {
                this.currentSuggestions = result.suggestions;
                this.displaySuggestions(result.suggestions);
                this.enableApplyAllButton();
                
                // Auto-apply high-confidence corrections if enabled
                if (document.getElementById('autoApplyCheck').checked) {
                    this.autoApplyHighConfidenceCorrections();
                }
            } else {
                throw new Error(result.error || 'Failed to generate suggestions');
            }
        } catch (error) {
            console.error('Suggestion generation error:', error);
            this.showAlert('Failed to generate suggestions: ' + error.message, 'danger');
        } finally {
            this.setAnalyzing(false);
        }
    }
    
    async applyCorrection(index) {
        const suggestion = this.currentSuggestions[index];
        if (!suggestion) return;
        
        const editor = document.getElementById('transcriptEditor');
        let content = editor.innerText;
        
        // Apply the correction
        content = content.replace(suggestion.original_text, suggestion.suggested_text);
        editor.innerText = content;
        
        // Mark suggestion as applied
        suggestion.applied = true;
        
        // Update the suggestion display
        this.updateSuggestionDisplay(index);
        
        // Save to storage
        this.saveTranscriptToStorage();
        
        // Learn from this correction
        await this.learnFromCorrection(suggestion);
    }
    
    async applyAllCorrections() {
        if (!this.currentSuggestions.length) return;
        
        let applied = 0;
        for (let i = 0; i < this.currentSuggestions.length; i++) {
            if (!this.currentSuggestions[i].applied) {
                await this.applyCorrection(i);
                applied++;
            }
        }
        
        this.showAlert(`Applied ${applied} corrections successfully.`, 'success');
        
        // Re-analyze quality after corrections
        setTimeout(() => this.analyzeQuality(), 1000);
    }
    
    async learnFromCorrection(suggestion) {
        try {
            await fetch('/api/correction/learn', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    original_text: suggestion.original_text,
                    corrected_text: suggestion.suggested_text,
                    correction_type: suggestion.type,
                    confidence: suggestion.confidence,
                    session_id: this.currentSessionId
                })
            });
        } catch (error) {
            console.error('Learning error:', error);
        }
    }
    
    async autoApplyHighConfidenceCorrections() {
        const highConfidenceThreshold = 0.9;
        let applied = 0;
        
        for (let i = 0; i < this.currentSuggestions.length; i++) {
            const suggestion = this.currentSuggestions[i];
            if (suggestion.confidence >= highConfidenceThreshold && !suggestion.applied) {
                await this.applyCorrection(i);
                applied++;
            }
        }
        
        if (applied > 0) {
            this.showAlert(`Auto-applied ${applied} high-confidence corrections.`, 'info');
        }
    }
    
    displayQualityMetrics(metrics) {
        // Update score displays
        this.updateScoreDisplay('overallScore', metrics.overall_score);
        this.updateScoreDisplay('grammarScore', metrics.grammar_score);
        this.updateScoreDisplay('spellingScore', metrics.spelling_score);
        this.updateScoreDisplay('readabilityScore', metrics.readability_score);
        this.updateScoreDisplay('confidenceScore', metrics.confidence_score);
        
        document.getElementById('issuesCount').textContent = metrics.issues_found;
        document.getElementById('issuesCount').className = 'quality-score score-' + 
            (metrics.issues_found === 0 ? 'excellent' : metrics.issues_found < 5 ? 'good' : 'poor');
        
        // Show recommendations
        if (metrics.recommendations && metrics.recommendations.length > 0) {
            const recommendationsEl = document.getElementById('recommendations');
            const listEl = document.getElementById('recommendationsList');
            
            listEl.innerHTML = '';
            metrics.recommendations.forEach(rec => {
                const li = document.createElement('li');
                li.textContent = rec;
                listEl.appendChild(li);
            });
            
            recommendationsEl.style.display = 'block';
        }
    }
    
    updateScoreDisplay(elementId, score) {
        const element = document.getElementById(elementId);
        element.textContent = (score * 100).toFixed(1) + '%';
        
        // Color coding
        element.className = 'quality-score score-' + 
            (score >= 0.8 ? 'excellent' : score >= 0.6 ? 'good' : 'poor');
    }
    
    displaySuggestions(suggestions) {
        const container = document.getElementById('suggestionsContainer');
        
        if (!suggestions || suggestions.length === 0) {
            container.innerHTML = `
                <div class="text-muted text-center py-4">
                    <i class="fas fa-check-circle fa-2x mb-2 text-success"></i>
                    <p>No corrections needed! Your transcript looks great.</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = '';
        
        suggestions.forEach((suggestion, index) => {
            const suggestionEl = this.createSuggestionElement(suggestion, index);
            container.appendChild(suggestionEl);
        });
    }
    
    createSuggestionElement(suggestion, index) {
        const div = document.createElement('div');
        div.className = `correction-suggestion ${suggestion.type}`;
        
        const confidence = (suggestion.confidence * 100).toFixed(1);
        const badgeClass = suggestion.confidence >= 0.8 ? 'success' : 
                          suggestion.confidence >= 0.6 ? 'warning' : 'secondary';
        
        div.innerHTML = `
            <div class="d-flex justify-content-between align-items-start mb-2">
                <span class="badge bg-${badgeClass}">${confidence}% confidence</span>
                <span class="badge bg-outline-secondary">${suggestion.type}</span>
            </div>
            
            <div class="mb-2">
                <strong>Original:</strong>
                <span class="diff-highlight">${this.escapeHtml(suggestion.original_text)}</span>
            </div>
            
            <div class="mb-2">
                <strong>Suggested:</strong>
                <span class="text-success">${this.escapeHtml(suggestion.suggested_text)}</span>
            </div>
            
            ${suggestion.explanation ? `
                <div class="mb-2 text-muted small">
                    <i class="fas fa-info-circle me-1"></i>
                    ${this.escapeHtml(suggestion.explanation)}
                </div>
            ` : ''}
            
            <div class="d-flex justify-content-end gap-2">
                <button class="btn btn-sm btn-outline-secondary" onclick="correctionClient.dismissSuggestion(${index})">
                    <i class="fas fa-times me-1"></i>Dismiss
                </button>
                <button class="btn btn-sm btn-primary" onclick="correctionClient.applyCorrection(${index})" 
                        ${suggestion.applied ? 'disabled' : ''}>
                    <i class="fas fa-check me-1"></i>${suggestion.applied ? 'Applied' : 'Apply'}
                </button>
            </div>
        `;
        
        return div;
    }
    
    updateSuggestionDisplay(index) {
        const suggestions = document.querySelectorAll('.correction-suggestion');
        if (suggestions[index]) {
            const button = suggestions[index].querySelector('button:last-child');
            button.disabled = true;
            button.innerHTML = '<i class="fas fa-check me-1"></i>Applied';
            button.className = 'btn btn-sm btn-success';
        }
    }
    
    dismissSuggestion(index) {
        this.currentSuggestions[index].dismissed = true;
        const suggestions = document.querySelectorAll('.correction-suggestion');
        if (suggestions[index]) {
            suggestions[index].style.opacity = '0.5';
            suggestions[index].style.pointerEvents = 'none';
        }
    }
    
    loadSampleTranscript() {
        const sampleTranscript = `Hello, welcome to today's meating about artifical inteligence and machine lerning. We're going to discus the latest advancements in AI technolgy and how they effect our bussiness operations.

First, lets talk about natural language procesing. NLP has become incredibley powerfull in recent years, allowing us to analayze large amounts of text data very efectively. However, there are still some chalenges we need to adress.

One major issue is the acuracy of speech recognishion systems. Sometimes they missinterpret words, especialy when dealing with technicle terminology or proper nouns. For example, the system might transcribe "machine learning" as "masheen lerning" or "AI" as "eye".

In conclustion, while AI has made remarkabel progress, we stil need to be carefull about data quality and acuracy. Thank you for your atention, and let's move on to the Q&A sesion.`;
        
        document.getElementById('transcriptEditor').innerText = sampleTranscript;
        this.originalTranscript = sampleTranscript;
        this.saveTranscriptToStorage();
    }
    
    resetTranscript() {
        if (this.originalTranscript) {
            document.getElementById('transcriptEditor').innerText = this.originalTranscript;
        } else {
            document.getElementById('transcriptEditor').innerText = '';
        }
        
        this.currentSuggestions = [];
        this.currentSessionId = null;
        
        // Clear displays
        document.getElementById('suggestionsContainer').innerHTML = `
            <div class="text-muted text-center py-4">
                <i class="fas fa-info-circle fa-2x mb-2"></i>
                <p>Analyze your transcript to see correction suggestions here.</p>
            </div>
        `;
        
        this.clearQualityMetrics();
        this.saveTranscriptToStorage();
    }
    
    clearQualityMetrics() {
        ['overallScore', 'grammarScore', 'spellingScore', 'readabilityScore', 'confidenceScore', 'issuesCount']
            .forEach(id => {
                const element = document.getElementById(id);
                element.textContent = '--';
                element.className = 'quality-score';
            });
        
        document.getElementById('recommendations').style.display = 'none';
    }
    
    async exportCorrected() {
        const transcript = this.getTranscriptContent();
        if (!transcript.trim()) {
            this.showAlert('No transcript to export.', 'warning');
            return;
        }
        
        try {
            const response = await fetch('/api/correction/export', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    transcript: transcript,
                    session_id: this.currentSessionId,
                    format: 'txt'
                })
            });
            
            if (!response.ok) {
                throw new Error('Export failed');
            }
            
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `corrected_transcript_${new Date().toISOString().slice(0, 10)}.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
            
            this.showAlert('Transcript exported successfully!', 'success');
        } catch (error) {
            console.error('Export error:', error);
            this.showAlert('Failed to export transcript: ' + error.message, 'danger');
        }
    }
    
    showCustomDictionary() {
        const modal = new bootstrap.Modal(document.getElementById('customDictionaryModal'));
        modal.show();
        this.updateCustomTermsDisplay();
    }
    
    addCustomTerm() {
        const original = document.getElementById('originalTerm').value.trim();
        const replacement = document.getElementById('replacementTerm').value.trim();
        
        if (!original || !replacement) {
            this.showAlert('Please enter both original term and replacement.', 'warning');
            return;
        }
        
        this.customDictionary.set(original, replacement);
        this.updateCustomTermsDisplay();
        
        // Clear inputs
        document.getElementById('originalTerm').value = '';
        document.getElementById('replacementTerm').value = '';
    }
    
    updateCustomTermsDisplay() {
        const container = document.getElementById('customTermsList');
        
        if (this.customDictionary.size === 0) {
            container.innerHTML = '<div class="text-muted">No custom terms added yet.</div>';
            return;
        }
        
        container.innerHTML = '';
        
        this.customDictionary.forEach((replacement, original) => {
            const termEl = document.createElement('div');
            termEl.className = 'border-bottom pb-2 mb-2 d-flex justify-content-between align-items-center';
            termEl.innerHTML = `
                <div>
                    <strong>${this.escapeHtml(original)}</strong> → 
                    <span class="text-success">${this.escapeHtml(replacement)}</span>
                </div>
                <button class="btn btn-sm btn-outline-danger" onclick="correctionClient.removeCustomTerm('${original}')">
                    <i class="fas fa-trash"></i>
                </button>
            `;
            container.appendChild(termEl);
        });
    }
    
    removeCustomTerm(original) {
        this.customDictionary.delete(original);
        this.updateCustomTermsDisplay();
    }
    
    saveCustomDictionary() {
        localStorage.setItem('transcriptCorrection_customDict', 
            JSON.stringify([...this.customDictionary]));
        
        const modal = bootstrap.Modal.getInstance(document.getElementById('customDictionaryModal'));
        modal.hide();
        
        this.showAlert('Custom dictionary saved successfully!', 'success');
    }
    
    async loadIndustryDictionary() {
        const industry = document.getElementById('industrySelect').value;
        if (!industry) return;
        
        try {
            const response = await fetch(`/api/correction/dictionary/${industry}`);
            if (response.ok) {
                const result = await response.json();
                this.showAlert(`Loaded ${result.term_count} ${industry} terms.`, 'info');
            }
        } catch (error) {
            console.error('Dictionary load error:', error);
        }
    }
    
    getTranscriptContent() {
        return document.getElementById('transcriptEditor').innerText.trim();
    }
    
    setAnalyzing(analyzing) {
        this.isAnalyzing = analyzing;
        const buttons = ['generateBtn', 'applyAllBtn'];
        
        buttons.forEach(id => {
            const btn = document.getElementById(id);
            if (btn) {
                btn.disabled = analyzing;
                if (analyzing) {
                    btn.innerHTML = btn.innerHTML.replace(/fas fa-\w+/, 'fas fa-spinner fa-spin');
                }
            }
        });
        
        if (analyzing) {
            this.showProgressBar();
        } else {
            this.hideProgressBar();
            // Restore button icons
            document.getElementById('generateBtn').innerHTML = 
                '<i class="fas fa-magic me-1"></i>Generate Suggestions';
        }
    }
    
    showProgressBar() {
        const progressBar = document.getElementById('progressBar');
        progressBar.style.display = 'block';
        
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 30;
            if (progress > 90) progress = 90;
            
            const bar = progressBar.querySelector('.progress-bar');
            bar.style.width = progress + '%';
            
            if (!this.isAnalyzing) {
                clearInterval(interval);
                bar.style.width = '100%';
                setTimeout(() => {
                    progressBar.style.display = 'none';
                    bar.style.width = '0%';
                }, 500);
            }
        }, 200);
    }
    
    hideProgressBar() {
        const progressBar = document.getElementById('progressBar');
        progressBar.style.display = 'none';
        progressBar.querySelector('.progress-bar').style.width = '0%';
    }
    
    enableApplyAllButton() {
        const btn = document.getElementById('applyAllBtn');
        if (btn && this.currentSuggestions.length > 0) {
            btn.disabled = false;
        }
    }
    
    showAlert(message, type) {
        // Create a temporary alert
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        alert.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alert);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.parentNode.removeChild(alert);
            }
        }, 5000);
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Global functions for onclick handlers
let correctionClient;

document.addEventListener('DOMContentLoaded', function() {
    correctionClient = new TranscriptCorrectionClient();
});

function loadSampleTranscript() {
    correctionClient.loadSampleTranscript();
}

function analyzeQuality() {
    correctionClient.analyzeQuality();
}

function generateSuggestions() {
    correctionClient.generateSuggestions();
}

function applyAllCorrections() {
    correctionClient.applyAllCorrections();
}

function resetTranscript() {
    correctionClient.resetTranscript();
}

function exportCorrected() {
    correctionClient.exportCorrected();
}

function showCustomDictionary() {
    correctionClient.showCustomDictionary();
}

function addCustomTerm() {
    correctionClient.addCustomTerm();
}

function saveCustomDictionary() {
    correctionClient.saveCustomDictionary();
}

function loadIndustryDictionary() {
    correctionClient.loadIndustryDictionary();
}
