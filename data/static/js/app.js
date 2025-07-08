/**
 * Video Transcriber - Shared JavaScript Utilities
 *
 * Common functions and utilities used across the application
 */

// Global utilities
window.VideoTranscriber = window.VideoTranscriber || {};

// Toast notification functions
function dismissToast(toastElement) {
    if (toastElement) {
        toastElement.style.animation = 'slideOutRight 0.3s ease-in';
        setTimeout(() => {
            if (toastElement.parentNode) {
                toastElement.remove();
            }
        }, 300);
    }
}

// Auto-dismiss toasts after 5 seconds
document.addEventListener('DOMContentLoaded', function() {
    const toasts = document.querySelectorAll('.toast[data-auto-dismiss="true"]');
    toasts.forEach(function(toast) {
        // Auto-dismiss after 5 seconds
        setTimeout(function() {
            dismissToast(toast);
        }, 5000);

        // Add click-to-dismiss functionality
        toast.addEventListener('click', function(e) {
            if (!e.target.matches('.toast-close, .toast-close *')) {
                dismissToast(toast);
            }
        });
    });
});

// Create toast programmatically
VideoTranscriber.showToast = function(message, type = 'info', duration = 5000) {
    const container = document.getElementById('toast-container') || createToastContainer();

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.setAttribute('data-auto-dismiss', 'true');

    const icon = type === 'success' ? '✅' :
                 type === 'error' ? '❌' :
                 type === 'warning' ? '⚠️' : 'ℹ️';

    toast.innerHTML = `
        <div class="toast-icon">
            <span>${icon}</span>
        </div>
        <div class="toast-content">
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="dismissToast(this.parentElement)">
            <span>×</span>
        </button>
    `;

    container.appendChild(toast);

    // Auto-dismiss
    if (duration > 0) {
        setTimeout(() => dismissToast(toast), duration);
    }

    // Click to dismiss
    toast.addEventListener('click', function(e) {
        if (!e.target.matches('.toast-close, .toast-close *')) {
            dismissToast(toast);
        }
    });

    return toast;
};

function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container';
    container.id = 'toast-container';
    document.body.appendChild(container);
    return container;
}

// Message/Alert system (legacy support)
VideoTranscriber.showMessage = function(message, type = 'info', duration = 5000) {
    // Use the new toast system
    return VideoTranscriber.showToast(message, type, duration);
};

// File size formatting
VideoTranscriber.formatFileSize = function(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Time formatting
VideoTranscriber.formatDuration = function(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);

    if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
    }
};

// API helpers
VideoTranscriber.api = {
    // Generic API call wrapper
    call: async function(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        const mergedOptions = { ...defaultOptions, ...options };

        try {
            const response = await fetch(url, mergedOptions);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP ${response.status}: ${response.statusText}`);
            }

            return data;
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    },

    // Get method
    get: function(url) {
        return this.call(url, { method: 'GET' });
    },

    // Post method
    post: function(url, data) {
        return this.call(url, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    // Put method
    put: function(url, data) {
        return this.call(url, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    },

    // Delete method
    delete: function(url) {
        return this.call(url, { method: 'DELETE' });
    }
};

// Loading states
VideoTranscriber.loading = {
    show: function(element, text = 'Loading...') {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        if (!element) return;

        element.setAttribute('data-original-content', element.innerHTML);
        element.innerHTML = `<span class="loading-spinner"></span> ${text}`;
        element.disabled = true;
        element.classList.add('loading');
    },

    hide: function(element) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        if (!element) return;

        const originalContent = element.getAttribute('data-original-content');
        if (originalContent) {
            element.innerHTML = originalContent;
            element.removeAttribute('data-original-content');
        }
        element.disabled = false;
        element.classList.remove('loading');
    }
};

// Form helpers
VideoTranscriber.forms = {
    // Serialize form data to object
    serialize: function(form) {
        const formData = new FormData(form);
        const data = {};

        for (let [key, value] of formData.entries()) {
            if (data[key]) {
                // Handle multiple values (checkboxes, etc.)
                if (Array.isArray(data[key])) {
                    data[key].push(value);
                } else {
                    data[key] = [data[key], value];
                }
            } else {
                data[key] = value;
            }
        }

        return data;
    },

    // Clear form
    clear: function(form) {
        if (typeof form === 'string') {
            form = document.getElementById(form);
        }
        if (form) {
            form.reset();
        }
    },

    // Validate form
    validate: function(form) {
        if (typeof form === 'string') {
            form = document.getElementById(form);
        }
        if (!form) return false;

        return form.checkValidity();
    }
};

// Local storage helpers
VideoTranscriber.storage = {
    set: function(key, value) {
        try {
            localStorage.setItem(`vt_${key}`, JSON.stringify(value));
            return true;
        } catch (error) {
            console.warn('Failed to save to localStorage:', error);
            return false;
        }
    },

    get: function(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(`vt_${key}`);
            return item ? JSON.parse(item) : defaultValue;
        } catch (error) {
            console.warn('Failed to read from localStorage:', error);
            return defaultValue;
        }
    },

    remove: function(key) {
        try {
            localStorage.removeItem(`vt_${key}`);
            return true;
        } catch (error) {
            console.warn('Failed to remove from localStorage:', error);
            return false;
        }
    },

    clear: function() {
        try {
            // Only clear our app's keys
            const keys = Object.keys(localStorage).filter(key => key.startsWith('vt_'));
            keys.forEach(key => localStorage.removeItem(key));
            return true;
        } catch (error) {
            console.warn('Failed to clear localStorage:', error);
            return false;
        }
    }
};

// DOM helpers
VideoTranscriber.dom = {
    // Wait for DOM to be ready
    ready: function(callback) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', callback);
        } else {
            callback();
        }
    },

    // Create element with attributes
    create: function(tag, attributes = {}, children = []) {
        const element = document.createElement(tag);

        Object.entries(attributes).forEach(([key, value]) => {
            if (key === 'className') {
                element.className = value;
            } else if (key === 'innerHTML') {
                element.innerHTML = value;
            } else if (key === 'textContent') {
                element.textContent = value;
            } else {
                element.setAttribute(key, value);
            }
        });

        children.forEach(child => {
            if (typeof child === 'string') {
                element.appendChild(document.createTextNode(child));
            } else {
                element.appendChild(child);
            }
        });

        return element;
    },

    // Show/hide elements
    show: function(element) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        if (element) {
            element.style.display = '';
        }
    },

    hide: function(element) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        if (element) {
            element.style.display = 'none';
        }
    },

    toggle: function(element) {
        if (typeof element === 'string') {
            element = document.getElementById(element);
        }
        if (element) {
            element.style.display = element.style.display === 'none' ? '' : 'none';
        }
    }
};

// Debounce function
VideoTranscriber.debounce = function(func, wait, immediate) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
};

// Throttle function
VideoTranscriber.throttle = function(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
};

// Copy to clipboard
VideoTranscriber.copyToClipboard = async function(text) {
    try {
        await navigator.clipboard.writeText(text);
        VideoTranscriber.showMessage('Copied to clipboard!', 'success', 2000);
        return true;
    } catch (error) {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();

        try {
            document.execCommand('copy');
            textArea.remove();
            VideoTranscriber.showMessage('Copied to clipboard!', 'success', 2000);
            return true;
        } catch (err) {
            textArea.remove();
            VideoTranscriber.showMessage('Failed to copy to clipboard', 'error');
            return false;
        }
    }
};

// Download file
VideoTranscriber.downloadFile = function(data, filename, type = 'application/octet-stream') {
    const blob = new Blob([data], { type });
    const url = URL.createObjectURL(blob);

    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.style.display = 'none';

    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    URL.revokeObjectURL(url);
};

// Initialize common functionality when DOM is ready
VideoTranscriber.dom.ready(function() {
    // Add keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K for global search (if search input exists)
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            const searchInput = document.querySelector('input[type="search"], #searchInput, .search-input');
            if (searchInput) {
                e.preventDefault();
                searchInput.focus();
            }
        }

        // Escape to close modals or clear focus
        if (e.key === 'Escape') {
            const activeElement = document.activeElement;
            if (activeElement && activeElement.blur) {
                activeElement.blur();
            }

            // Close any visible modals
            const modals = document.querySelectorAll('.modal.visible, .modal.show');
            modals.forEach(modal => {
                modal.classList.remove('visible', 'show');
            });
        }
    });

    // Auto-hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(message => {
        setTimeout(() => {
            if (message.parentNode) {
                message.style.transition = 'opacity 0.3s ease';
                message.style.opacity = '0';
                setTimeout(() => message.remove(), 300);
            }
        }, 5000);
    });

    // Add loading states to forms
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
            if (submitBtn) {
                VideoTranscriber.loading.show(submitBtn, 'Please wait...');
            }
        });
    });
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = VideoTranscriber;
}
