// Global Search Component
// Provides unified search across all app content and features
let searchTimeout;
let currentSearchQuery = '';

// Initialize global search
document.addEventListener('DOMContentLoaded', () => {
    initGlobalSearch();
});

function initGlobalSearch() {
    const searchBtn = document.getElementById('global-search-btn');
    const searchModal = document.getElementById('global-search-modal');
    const searchInput = document.getElementById('global-search-input');
    const searchResults = document.getElementById('global-search-results');
    const searchClose = document.getElementById('global-search-close');
    
    if (!searchBtn || !searchModal) return;
    
    // Open search modal
    searchBtn?.addEventListener('click', () => {
        searchModal.classList.remove('hidden');
        setTimeout(() => {
            searchModal.classList.add('opacity-100');
            searchInput?.focus();
        }, 10);
    });
    
    // Close search modal
    searchClose?.addEventListener('click', closeSearchModal);
    
    // Close on escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && !searchModal.classList.contains('hidden')) {
            closeSearchModal();
        }
        
        // Open search with Ctrl+K or Cmd+K
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            searchBtn?.click();
        }
    });
    
    // Close on backdrop click
    searchModal?.addEventListener('click', (e) => {
        if (e.target === searchModal) {
            closeSearchModal();
        }
    });
    
    // Handle search input
    searchInput?.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        
        // Clear previous timeout
        clearTimeout(searchTimeout);
        
        // Show loading state
        if (query.length >= 2) {
            searchResults.innerHTML = '<div class="p-4 text-center text-text-muted dark:text-[#92adc9]">Searching...</div>';
            
            // Debounce search
            searchTimeout = setTimeout(() => {
                performSearch(query);
            }, 300);
        } else if (query.length === 0) {
            showSearchPlaceholder();
        } else {
            searchResults.innerHTML = '<div class="p-4 text-center text-text-muted dark:text-[#92adc9]" data-translate="search.minChars">Type at least 2 characters to search</div>';
        }
    });
    
    // Handle keyboard navigation
    searchInput?.addEventListener('keydown', (e) => {
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            const firstResult = searchResults.querySelector('[data-search-result]');
            firstResult?.focus();
        }
    });
}

function closeSearchModal() {
    const searchModal = document.getElementById('global-search-modal');
    const searchInput = document.getElementById('global-search-input');
    
    searchModal?.classList.remove('opacity-100');
    setTimeout(() => {
        searchModal?.classList.add('hidden');
        searchInput.value = '';
        showSearchPlaceholder();
    }, 200);
}

function showSearchPlaceholder() {
    const searchResults = document.getElementById('global-search-results');
    searchResults.innerHTML = `
        <div class="p-8 text-center">
            <span class="material-symbols-outlined text-5xl text-text-muted dark:text-[#92adc9] opacity-50 mb-3">search</span>
            <p class="text-text-muted dark:text-[#92adc9] text-sm" data-translate="search.placeholder">Search for transactions, documents, categories, or features</p>
            <p class="text-text-muted dark:text-[#92adc9] text-xs mt-2" data-translate="search.hint">Press Ctrl+K to open search</p>
        </div>
    `;
}

async function performSearch(query) {
    currentSearchQuery = query;
    const searchResults = document.getElementById('global-search-results');
    
    try {
        const response = await apiCall(`/api/search/?q=${encodeURIComponent(query)}`, {
            method: 'GET'
        });
        
        if (response.success) {
            displaySearchResults(response);
        } else {
            searchResults.innerHTML = `<div class="p-4 text-center text-red-500">${response.message}</div>`;
        }
    } catch (error) {
        console.error('Search error:', error);
        searchResults.innerHTML = '<div class="p-4 text-center text-red-500" data-translate="search.error">Search failed. Please try again.</div>';
    }
}

function displaySearchResults(response) {
    const searchResults = document.getElementById('global-search-results');
    const results = response.results;
    const userLang = localStorage.getItem('language') || 'en';
    
    if (response.total_results === 0) {
        searchResults.innerHTML = `
            <div class="p-8 text-center">
                <span class="material-symbols-outlined text-5xl text-text-muted dark:text-[#92adc9] opacity-50 mb-3">search_off</span>
                <p class="text-text-muted dark:text-[#92adc9]" data-translate="search.noResults">No results found for "${response.query}"</p>
            </div>
        `;
        return;
    }
    
    let html = '<div class="flex flex-col divide-y divide-border-light dark:divide-[#233648]">';
    
    // Features
    if (results.features && results.features.length > 0) {
        html += '<div class="p-4"><h3 class="text-xs font-semibold text-text-muted dark:text-[#92adc9] uppercase mb-3" data-translate="search.features">Features</h3><div class="flex flex-col gap-2">';
        results.features.forEach(feature => {
            const name = userLang === 'ro' ? feature.name_ro : feature.name;
            const desc = userLang === 'ro' ? feature.description_ro : feature.description;
            html += `
                <a href="${feature.url}" data-search-result tabindex="0" class="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-[#233648] transition-colors focus:outline-none focus:ring-2 focus:ring-primary">
                    <span class="material-symbols-outlined text-primary text-xl">${feature.icon}</span>
                    <div class="flex-1 min-w-0">
                        <div class="text-sm font-medium text-text-main dark:text-white">${name}</div>
                        <div class="text-xs text-text-muted dark:text-[#92adc9]">${desc}</div>
                    </div>
                    <span class="material-symbols-outlined text-text-muted text-sm">arrow_forward</span>
                </a>
            `;
        });
        html += '</div></div>';
    }
    
    // Expenses
    if (results.expenses && results.expenses.length > 0) {
        html += '<div class="p-4"><h3 class="text-xs font-semibold text-text-muted dark:text-[#92adc9] uppercase mb-3" data-translate="search.expenses">Expenses</h3><div class="flex flex-col gap-2">';
        results.expenses.forEach(expense => {
            const date = new Date(expense.date).toLocaleDateString(userLang === 'ro' ? 'ro-RO' : 'en-US', { month: 'short', day: 'numeric' });
            const ocrBadge = expense.ocr_match ? '<span class="text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 px-2 py-0.5 rounded" data-translate="search.ocrMatch">OCR Match</span>' : '';
            html += `
                <a href="${expense.url}" data-search-result tabindex="0" class="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-[#233648] transition-colors focus:outline-none focus:ring-2 focus:ring-primary">
                    <div class="size-10 rounded-lg flex items-center justify-center" style="background-color: ${expense.category_color}20">
                        <span class="material-symbols-outlined text-lg" style="color: ${expense.category_color}">receipt</span>
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="text-sm font-medium text-text-main dark:text-white">${expense.description}</div>
                        <div class="flex items-center gap-2 text-xs text-text-muted dark:text-[#92adc9] mt-1">
                            <span>${expense.category_name}</span>
                            <span>•</span>
                            <span>${date}</span>
                            ${ocrBadge}
                        </div>
                    </div>
                    <div class="text-sm font-semibold text-text-main dark:text-white">${formatCurrency(expense.amount, expense.currency)}</div>
                </a>
            `;
        });
        html += '</div></div>';
    }
    
    // Documents
    if (results.documents && results.documents.length > 0) {
        html += '<div class="p-4"><h3 class="text-xs font-semibold text-text-muted dark:text-[#92adc9] uppercase mb-3" data-translate="search.documents">Documents</h3><div class="flex flex-col gap-2">';
        results.documents.forEach(doc => {
            const date = new Date(doc.created_at).toLocaleDateString(userLang === 'ro' ? 'ro-RO' : 'en-US', { month: 'short', day: 'numeric' });
            const ocrBadge = doc.ocr_match ? '<span class="text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 px-2 py-0.5 rounded" data-translate="search.ocrMatch">OCR Match</span>' : '';
            const fileIcon = doc.file_type === 'PDF' ? 'picture_as_pdf' : 'image';
            html += `
                <button onclick="openDocumentFromSearch(${doc.id}, '${doc.file_type}', '${escapeHtml(doc.filename)}')" data-search-result tabindex="0" class="w-full flex items-center gap-3 p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-[#233648] transition-colors focus:outline-none focus:ring-2 focus:ring-primary text-left">
                    <span class="material-symbols-outlined text-primary text-xl">${fileIcon}</span>
                    <div class="flex-1 min-w-0">
                        <div class="text-sm font-medium text-text-main dark:text-white truncate">${doc.filename}</div>
                        <div class="flex items-center gap-2 text-xs text-text-muted dark:text-[#92adc9] mt-1">
                            <span>${doc.file_type}</span>
                            <span>•</span>
                            <span>${date}</span>
                            ${ocrBadge}
                        </div>
                    </div>
                    <span class="material-symbols-outlined text-text-muted text-sm">visibility</span>
                </button>
            `;
        });
        html += '</div></div>';
    }
    
    // Categories
    if (results.categories && results.categories.length > 0) {
        html += '<div class="p-4"><h3 class="text-xs font-semibold text-text-muted dark:text-[#92adc9] uppercase mb-3" data-translate="search.categories">Categories</h3><div class="flex flex-col gap-2">';
        results.categories.forEach(category => {
            html += `
                <a href="${category.url}" data-search-result tabindex="0" class="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-[#233648] transition-colors focus:outline-none focus:ring-2 focus:ring-primary">
                    <div class="size-10 rounded-lg flex items-center justify-center" style="background-color: ${category.color}20">
                        <span class="material-symbols-outlined text-lg" style="color: ${category.color}">${category.icon}</span>
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="text-sm font-medium text-text-main dark:text-white">${category.name}</div>
                    </div>
                    <span class="material-symbols-outlined text-text-muted text-sm">arrow_forward</span>
                </a>
            `;
        });
        html += '</div></div>';
    }
    
    // Recurring Expenses
    if (results.recurring && results.recurring.length > 0) {
        html += '<div class="p-4"><h3 class="text-xs font-semibold text-text-muted dark:text-[#92adc9] uppercase mb-3" data-translate="search.recurring">Recurring</h3><div class="flex flex-col gap-2">';
        results.recurring.forEach(rec => {
            const nextDue = new Date(rec.next_due_date).toLocaleDateString(userLang === 'ro' ? 'ro-RO' : 'en-US', { month: 'short', day: 'numeric' });
            const statusBadge = rec.is_active 
                ? '<span class="text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 px-2 py-0.5 rounded" data-translate="recurring.active">Active</span>'
                : '<span class="text-xs bg-gray-100 dark:bg-gray-800/30 text-gray-600 dark:text-gray-400 px-2 py-0.5 rounded" data-translate="recurring.inactive">Inactive</span>';
            html += `
                <a href="${rec.url}" data-search-result tabindex="0" class="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-50 dark:hover:bg-[#233648] transition-colors focus:outline-none focus:ring-2 focus:ring-primary">
                    <div class="size-10 rounded-lg flex items-center justify-center" style="background-color: ${rec.category_color}20">
                        <span class="material-symbols-outlined text-lg" style="color: ${rec.category_color}">repeat</span>
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="text-sm font-medium text-text-main dark:text-white">${rec.name}</div>
                        <div class="flex items-center gap-2 text-xs text-text-muted dark:text-[#92adc9] mt-1">
                            <span>${rec.category_name}</span>
                            <span>•</span>
                            <span data-translate="recurring.nextDue">Next:</span>
                            <span>${nextDue}</span>
                            ${statusBadge}
                        </div>
                    </div>
                    <div class="text-sm font-semibold text-text-main dark:text-white">${formatCurrency(rec.amount, rec.currency)}</div>
                </a>
            `;
        });
        html += '</div></div>';
    }
    
    html += '</div>';
    searchResults.innerHTML = html;
    
    // Apply translations
    if (window.applyTranslations) {
        window.applyTranslations();
    }
    
    // Handle keyboard navigation between results
    const resultElements = searchResults.querySelectorAll('[data-search-result]');
    resultElements.forEach((element, index) => {
        element.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                resultElements[index + 1]?.focus();
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                if (index === 0) {
                    document.getElementById('global-search-input')?.focus();
                } else {
                    resultElements[index - 1]?.focus();
                }
            }
        });
    });
}

// Open document viewer from search
function openDocumentFromSearch(docId, fileType, filename) {
    // Close search modal
    closeSearchModal();
    
    // Navigate to documents page and open viewer
    if (window.location.pathname !== '/documents') {
        // Store document to open after navigation
        sessionStorage.setItem('openDocumentId', docId);
        sessionStorage.setItem('openDocumentType', fileType);
        sessionStorage.setItem('openDocumentName', filename);
        window.location.href = '/documents';
    } else {
        // Already on documents page, open directly
        if (typeof viewDocument === 'function') {
            viewDocument(docId, fileType, filename);
        }
    }
}

// Helper to escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
