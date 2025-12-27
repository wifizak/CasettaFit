/**
 * CasettaFit Common JavaScript Utilities
 * Shared functions for fetch requests, loading indicators, and form validation
 */

// ============================================
// FETCH WRAPPER WITH ERROR HANDLING
// ============================================

/**
 * Enhanced fetch wrapper with consistent error handling and loading indicators
 * @param {string} url - The URL to fetch from
 * @param {Object} options - Fetch options (method, headers, body, etc.)
 * @param {Object} config - Additional config for loading indicators
 * @returns {Promise} - Resolves with data or rejects with error
 */
async function apiFetch(url, options = {}, config = {}) {
    // Set default options
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
        ...options
    };

    // Show loading indicator if configured
    if (config.loadingElement) {
        showLoading(config.loadingElement);
    }

    try {
        const response = await fetch(url, defaultOptions);
        
        // Check if response is ok (status 200-299)
        if (!response.ok) {
            // Try to parse error message from response
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.error || `HTTP Error: ${response.status} ${response.statusText}`);
        }

        // Parse JSON response
        const data = await response.json();
        
        // Hide loading indicator
        if (config.loadingElement) {
            hideLoading(config.loadingElement);
        }

        // Show success message if configured
        if (config.successMessage) {
            showAlert(config.successMessage, 'success');
        }

        return data;
    } catch (error) {
        // Hide loading indicator
        if (config.loadingElement) {
            hideLoading(config.loadingElement);
        }

        // Show error message
        const errorMessage = config.errorMessage || error.message || 'An error occurred';
        showAlert(errorMessage, 'danger');

        // Log to console for debugging
        console.error('API Fetch Error:', error);

        // Re-throw the error for further handling
        throw error;
    }
}

/**
 * Simplified GET request
 * @param {string} url - The URL to fetch from
 * @param {Object} config - Additional config for loading indicators
 * @returns {Promise} - Resolves with data
 */
async function apiGet(url, config = {}) {
    return apiFetch(url, { method: 'GET' }, config);
}

/**
 * Simplified POST request
 * @param {string} url - The URL to post to
 * @param {Object} data - Data to send in the body
 * @param {Object} config - Additional config for loading indicators
 * @returns {Promise} - Resolves with data
 */
async function apiPost(url, data, config = {}) {
    return apiFetch(url, {
        method: 'POST',
        body: JSON.stringify(data)
    }, config);
}

/**
 * Simplified PUT request
 * @param {string} url - The URL to put to
 * @param {Object} data - Data to send in the body
 * @param {Object} config - Additional config for loading indicators
 * @returns {Promise} - Resolves with data
 */
async function apiPut(url, data, config = {}) {
    return apiFetch(url, {
        method: 'PUT',
        body: JSON.stringify(data)
    }, config);
}

/**
 * Simplified DELETE request
 * @param {string} url - The URL to delete
 * @param {Object} config - Additional config for loading indicators
 * @returns {Promise} - Resolves with data
 */
async function apiDelete(url, config = {}) {
    return apiFetch(url, { method: 'DELETE' }, config);
}

// ============================================
// LOADING INDICATORS
// ============================================

/**
 * Show loading spinner on an element
 * @param {HTMLElement|string} element - The element or selector to show loading on
 */
function showLoading(element) {
    const el = typeof element === 'string' ? document.querySelector(element) : element;
    if (!el) return;

    // Disable if it's a button or input
    if (el.tagName === 'BUTTON' || el.tagName === 'INPUT') {
        el.disabled = true;
        el.dataset.originalText = el.textContent || el.value;
        
        if (el.tagName === 'BUTTON') {
            el.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Loading...';
        }
    } else {
        // Add spinner overlay for other elements
        el.style.position = 'relative';
        const spinner = document.createElement('div');
        spinner.className = 'loading-overlay';
        spinner.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">Loading...</span></div>';
        el.appendChild(spinner);
    }
}

/**
 * Hide loading spinner from an element
 * @param {HTMLElement|string} element - The element or selector to hide loading from
 */
function hideLoading(element) {
    const el = typeof element === 'string' ? document.querySelector(element) : element;
    if (!el) return;

    // Re-enable if it's a button or input
    if (el.tagName === 'BUTTON' || el.tagName === 'INPUT') {
        el.disabled = false;
        if (el.dataset.originalText) {
            if (el.tagName === 'BUTTON') {
                el.textContent = el.dataset.originalText;
            } else {
                el.value = el.dataset.originalText;
            }
            delete el.dataset.originalText;
        }
    } else {
        // Remove spinner overlay
        const spinner = el.querySelector('.loading-overlay');
        if (spinner) {
            spinner.remove();
        }
    }
}

/**
 * Show a loading spinner in a container
 * @param {string} containerId - The ID of the container
 */
function showContainerLoading(containerId) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    container.innerHTML = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            <p class="mt-2 text-muted">Loading...</p>
        </div>
    `;
}

// ============================================
// ALERT/FLASH MESSAGES
// ============================================

/**
 * Show an alert message (similar to Flask flash)
 * @param {string} message - The message to display
 * @param {string} type - Alert type: success, danger, warning, info
 * @param {number} duration - Auto-dismiss duration in ms (0 = no auto-dismiss)
 */
function showAlert(message, type = 'info', duration = 5000) {
    // Create alert element
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.setAttribute('role', 'alert');
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-coreui-dismiss="alert" aria-label="Close"></button>
    `;

    // Find or create alerts container
    let container = document.getElementById('flash-messages-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'flash-messages-container';
        container.className = 'container mt-3';
        
        // Insert after the main content area or at the top
        const main = document.querySelector('main') || document.body;
        main.insertBefore(container, main.firstChild);
    }

    // Add alert to container
    container.appendChild(alert);

    // Auto-dismiss after duration
    if (duration > 0) {
        setTimeout(() => {
            alert.classList.remove('show');
            setTimeout(() => alert.remove(), 150);
        }, duration);
    }
}

// ============================================
// FORM HELPERS
// ============================================

/**
 * Disable all form inputs and buttons
 * @param {HTMLFormElement|string} form - The form element or selector
 */
function disableForm(form) {
    const formEl = typeof form === 'string' ? document.querySelector(form) : form;
    if (!formEl) return;

    const elements = formEl.querySelectorAll('input, textarea, select, button');
    elements.forEach(el => {
        el.disabled = true;
    });
}

/**
 * Enable all form inputs and buttons
 * @param {HTMLFormElement|string} form - The form element or selector
 */
function enableForm(form) {
    const formEl = typeof form === 'string' ? document.querySelector(form) : form;
    if (!formEl) return;

    const elements = formEl.querySelectorAll('input, textarea, select, button');
    elements.forEach(el => {
        el.disabled = false;
    });
}

/**
 * Serialize form data to JSON object
 * @param {HTMLFormElement|string} form - The form element or selector
 * @returns {Object} - Form data as JSON object
 */
function serializeForm(form) {
    const formEl = typeof form === 'string' ? document.querySelector(form) : form;
    if (!formEl) return {};

    const formData = new FormData(formEl);
    const data = {};
    
    for (const [key, value] of formData.entries()) {
        // Handle multiple values for the same key (like checkboxes)
        if (data[key]) {
            if (!Array.isArray(data[key])) {
                data[key] = [data[key]];
            }
            data[key].push(value);
        } else {
            data[key] = value;
        }
    }
    
    return data;
}

/**
 * Confirm action with a dialog
 * @param {string} message - The confirmation message
 * @returns {boolean} - True if confirmed, false otherwise
 */
function confirmAction(message) {
    return confirm(message);
}

// ============================================
// AUTOCOMPLETE HELPERS
// ============================================

/**
 * Setup autocomplete on an input field
 * @param {HTMLInputElement} input - The input element
 * @param {Function|Array} dataSource - Function that returns array of suggestions or array directly
 * @param {Object} options - Configuration options
 */
function setupAutocomplete(input, dataSource, options = {}) {
    const config = {
        minLength: 1,
        maxResults: 10,
        onSelect: null,
        ...options
    };

    let datalistId = input.getAttribute('list');
    let datalist;

    if (!datalistId) {
        datalistId = `autocomplete-${Math.random().toString(36).substr(2, 9)}`;
        datalist = document.createElement('datalist');
        datalist.id = datalistId;
        document.body.appendChild(datalist);
        input.setAttribute('list', datalistId);
    } else {
        datalist = document.getElementById(datalistId);
    }

    input.addEventListener('input', function() {
        const value = this.value.toLowerCase();
        
        if (value.length < config.minLength) {
            datalist.innerHTML = '';
            return;
        }

        // Get data from source
        const data = typeof dataSource === 'function' ? dataSource() : dataSource;
        
        // Filter and limit results
        const filtered = data
            .filter(item => item.toLowerCase().includes(value))
            .slice(0, config.maxResults);

        // Update datalist
        datalist.innerHTML = filtered
            .map(item => `<option value="${item}">`)
            .join('');
    });

    if (config.onSelect) {
        input.addEventListener('change', config.onSelect);
    }
}

// ============================================
// MODAL HELPERS
// ============================================

/**
 * Show a Bootstrap/CoreUI modal
 * @param {string} modalId - The ID of the modal
 */
function showModal(modalId) {
    const modalElement = document.getElementById(modalId);
    if (modalElement) {
        const modal = new coreui.Modal(modalElement);
        modal.show();
    }
}

/**
 * Hide a Bootstrap/CoreUI modal
 * @param {string} modalId - The ID of the modal
 */
function hideModal(modalId) {
    const modalElement = document.getElementById(modalId);
    if (modalElement) {
        const modal = coreui.Modal.getInstance(modalElement);
        if (modal) {
            modal.hide();
        }
    }
}

// ============================================
// UTILITY FUNCTIONS
// ============================================

/**
 * Debounce function to limit how often a function is called
 * @param {Function} func - The function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} - Debounced function
 */
function debounce(func, wait = 300) {
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

/**
 * Format date to YYYY-MM-DD
 * @param {Date} date - The date to format
 * @returns {string} - Formatted date string
 */
function formatDate(date) {
    const d = new Date(date);
    const year = d.getFullYear();
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - The text to escape
 * @returns {string} - Escaped text
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================
// CSS FOR LOADING OVERLAYS
// ============================================

// Inject CSS for loading overlays if not already present
if (!document.getElementById('common-js-styles')) {
    const style = document.createElement('style');
    style.id = 'common-js-styles';
    style.textContent = `
        .loading-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(255, 255, 255, 0.8);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 1000;
        }
    `;
    document.head.appendChild(style);
}

// Export for ES6 modules (if needed in future)
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        apiFetch,
        apiGet,
        apiPost,
        apiPut,
        apiDelete,
        showLoading,
        hideLoading,
        showContainerLoading,
        showAlert,
        disableForm,
        enableForm,
        serializeForm,
        confirmAction,
        setupAutocomplete,
        showModal,
        hideModal,
        debounce,
        formatDate,
        escapeHtml
    };
}

// ============================================
// UNIVERSAL FORM SUBMISSION HANDLER
// ============================================

/**
 * Automatically handle form submissions with loading states
 * Activates on page load for all forms (can be disabled with data-no-auto-loading attribute)
 */
document.addEventListener('DOMContentLoaded', function() {
    // Handle all forms that don't have data-no-auto-loading attribute
    document.querySelectorAll('form:not([data-no-auto-loading])').forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled && !submitBtn.dataset.loading) {
                // Mark as loading to prevent double-processing
                submitBtn.dataset.loading = 'true';
                
                // Store original content
                const originalHtml = submitBtn.innerHTML;
                submitBtn.dataset.originalHtml = originalHtml;
                
                // Disable button and show loading spinner
                submitBtn.disabled = true;
                
                // Check if button already has text content we can preserve
                let loadingText = 'Processing...';
                const buttonText = submitBtn.textContent.trim();
                
                if (buttonText) {
                    // Use context-aware loading text
                    if (buttonText.toLowerCase().includes('sign in') || buttonText.toLowerCase().includes('login')) {
                        loadingText = 'Signing in...';
                    } else if (buttonText.toLowerCase().includes('save')) {
                        loadingText = 'Saving...';
                    } else if (buttonText.toLowerCase().includes('create')) {
                        loadingText = 'Creating...';
                    } else if (buttonText.toLowerCase().includes('update')) {
                        loadingText = 'Updating...';
                    } else if (buttonText.toLowerCase().includes('delete')) {
                        loadingText = 'Deleting...';
                    } else if (buttonText.toLowerCase().includes('upload')) {
                        loadingText = 'Uploading...';
                    }
                }
                
                submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>${loadingText}`;
                
                // Safety mechanism: Re-enable after 30 seconds in case of network issues
                const timeoutId = setTimeout(() => {
                    if (submitBtn.dataset.loading === 'true') {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = originalHtml;
                        delete submitBtn.dataset.loading;
                        delete submitBtn.dataset.originalHtml;
                        
                        // Show error message
                        showAlert('Request timed out. Please try again.', 'warning');
                    }
                }, 30000);
                
                // Store timeout ID so we can clear it if form succeeds
                submitBtn.dataset.timeoutId = timeoutId;
            }
        });
        
        // Listen for page unload to clean up
        window.addEventListener('beforeunload', function() {
            const submitBtn = form.querySelector('button[type="submit"]');
            if (submitBtn && submitBtn.dataset.timeoutId) {
                clearTimeout(parseInt(submitBtn.dataset.timeoutId));
            }
        });
    });
});

/**
 * Manually restore a submit button to its original state
 * Useful for AJAX forms that don't reload the page
 * @param {HTMLElement|string} button - The button element or selector
 */
function restoreSubmitButton(button) {
    const btn = typeof button === 'string' ? document.querySelector(button) : button;
    if (!btn) return;
    
    // Clear timeout if exists
    if (btn.dataset.timeoutId) {
        clearTimeout(parseInt(btn.dataset.timeoutId));
        delete btn.dataset.timeoutId;
    }
    
    // Restore original state
    btn.disabled = false;
    if (btn.dataset.originalHtml) {
        btn.innerHTML = btn.dataset.originalHtml;
        delete btn.dataset.originalHtml;
    }
    delete btn.dataset.loading;
}
