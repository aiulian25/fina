// Global utility functions

// Toast notifications
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    
    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        info: 'bg-primary',
        warning: 'bg-yellow-500'
    };
    
    toast.className = `${colors[type]} text-white px-6 py-3 rounded-lg shadow-lg flex items-center gap-3 animate-slide-in`;
    toast.innerHTML = `
        <span class="material-symbols-outlined text-[20px]">
            ${type === 'success' ? 'check_circle' : type === 'error' ? 'error' : 'info'}
        </span>
        <span>${message}</span>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Format currency
function formatCurrency(amount, currency = 'USD') {
    const symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'RON': 'lei'
    };
    
    const symbol = symbols[currency] || currency;
    const formatted = parseFloat(amount).toFixed(2);
    
    if (currency === 'RON') {
        return `${formatted} ${symbol}`;
    }
    return `${symbol}${formatted}`;
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now - date;
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (days === 0) return window.getTranslation ? window.getTranslation('date.today', 'Today') : 'Today';
    if (days === 1) return window.getTranslation ? window.getTranslation('date.yesterday', 'Yesterday') : 'Yesterday';
    if (days < 7) {
        const daysAgoText = window.getTranslation ? window.getTranslation('date.daysAgo', 'days ago') : 'days ago';
        return `${days} ${daysAgoText}`;
    }
    
    const lang = window.getCurrentLanguage ? window.getCurrentLanguage() : 'en';
    const locale = lang === 'ro' ? 'ro-RO' : 'en-US';
    return date.toLocaleDateString(locale, { month: 'short', day: 'numeric', year: 'numeric' });
}

// API helper
async function apiCall(url, options = {}) {
    try {
        // Don't set Content-Type header for FormData - browser will set it automatically with boundary
        const headers = options.body instanceof FormData 
            ? { ...options.headers }
            : { ...options.headers, 'Content-Type': 'application/json' };
        
        const response = await fetch(url, {
            ...options,
            headers
        });
        
        if (!response.ok) {
            // Try to get error message from response
            let errorData;
            try {
                errorData = await response.json();
            } catch (jsonError) {
                showToast(window.getTranslation('common.error', 'An error occurred. Please try again.'), 'error');
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const errorMsg = errorData.message || window.getTranslation('common.error', 'An error occurred. Please try again.');
            
            // Only show toast if it's not a special case that needs custom handling
            if (!errorData.requires_reassignment) {
                showToast(errorMsg, 'error');
            }
            
            // Throw error with data attached for special handling (e.g., category deletion with reassignment)
            const error = new Error(`HTTP error! status: ${response.status}`);
            Object.assign(error, errorData);
            throw error;
        }
        
        return await response.json();
    } catch (error) {
        console.error('API call failed:', error);
        if (!error.message.includes('HTTP error')) {
            showToast(window.getTranslation('common.error', 'An error occurred. Please try again.'), 'error');
        }
        throw error;
    }
}

// Export apiCall to window for use by other modules
window.apiCall = apiCall;

// Theme management
function initTheme() {
    // Theme is already applied in head, just update UI
    const isDark = document.documentElement.classList.contains('dark');
    updateThemeUI(isDark);
}

function toggleTheme() {
    const isDark = document.documentElement.classList.contains('dark');
    
    if (isDark) {
        document.documentElement.classList.remove('dark');
        localStorage.setItem('theme', 'light');
        updateThemeUI(false);
    } else {
        document.documentElement.classList.add('dark');
        localStorage.setItem('theme', 'dark');
        updateThemeUI(true);
    }
    
    // Dispatch custom event for other components to react to theme change
    window.dispatchEvent(new CustomEvent('theme-changed', { detail: { isDark: !isDark } }));
}

function updateThemeUI(isDark) {
    const themeIcon = document.getElementById('theme-icon');
    const themeText = document.getElementById('theme-text');
    
    // Only update if elements exist (not all pages have theme toggle in sidebar)
    if (!themeIcon || !themeText) {
        return;
    }
    
    if (isDark) {
        themeIcon.textContent = 'dark_mode';
        const darkModeText = window.getTranslation ? window.getTranslation('dashboard.darkMode', 'Dark Mode') : 'Dark Mode';
        themeText.textContent = darkModeText;
        themeText.setAttribute('data-translate', 'dashboard.darkMode');
    } else {
        themeIcon.textContent = 'light_mode';
        const lightModeText = window.getTranslation ? window.getTranslation('dashboard.lightMode', 'Light Mode') : 'Light Mode';
        themeText.textContent = lightModeText;
        themeText.setAttribute('data-translate', 'dashboard.lightMode');
    }
}

// Mobile menu toggle
document.addEventListener('DOMContentLoaded', () => {
    // Initialize theme
    initTheme();
    
    // Theme toggle button
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
    }
    
    // Mobile menu
    const menuToggle = document.getElementById('menu-toggle');
    const sidebar = document.getElementById('sidebar');
    
    if (menuToggle && sidebar) {
        menuToggle.addEventListener('click', () => {
            sidebar.classList.toggle('hidden');
            sidebar.classList.toggle('flex');
            sidebar.classList.toggle('absolute');
            sidebar.classList.toggle('z-50');
            sidebar.style.left = '0';
        });
        
        // Close sidebar when clicking outside on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth < 1024) {
                if (!sidebar.contains(e.target) && !menuToggle.contains(e.target)) {
                    sidebar.classList.add('hidden');
                    sidebar.classList.remove('flex');
                }
            }
        });
    }
});
