// Subscriptions page JavaScript
// Handles subscription detection, tracking, and management

let subscriptions = [];
let categories = [];
let suggestions = [];
let currentFilter = 'all';

// Initialize page
document.addEventListener('DOMContentLoaded', async () => {
    // Load user currency first
    await loadUserCurrency();
    
    // Load categories for the form
    await loadCategories();
    
    // Load subscriptions
    await loadSubscriptions();
    
    // Load summary
    await loadSummary();
    
    // Setup form handler
    document.getElementById('subscription-form').addEventListener('submit', handleSubscriptionSubmit);
    
    // Setup mobile menu
    setupMobileMenu();
    
    // Set default date to today
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('sub-next-date').value = today;
});

// Load user currency
async function loadUserCurrency() {
    try {
        const data = await apiCall('/api/settings/profile');
        window.userCurrency = data.profile?.currency || 'USD';
    } catch (error) {
        console.error('Failed to load user currency:', error);
        window.userCurrency = 'USD';
    }
}

// Load categories
async function loadCategories() {
    try {
        const data = await apiCall('/api/expenses/categories');
        categories = data.categories || [];
        
        const select = document.getElementById('sub-category');
        select.innerHTML = categories.map(cat => 
            `<option value="${cat.id}">${cat.name}</option>`
        ).join('');
    } catch (error) {
        console.error('Failed to load categories:', error);
    }
}

// Load subscriptions
async function loadSubscriptions() {
    try {
        const data = await apiCall('/api/subscriptions/');
        subscriptions = data.subscriptions || [];
        renderSubscriptions();
    } catch (error) {
        console.error('Failed to load subscriptions:', error);
        showToast(window.getTranslation('subscriptions.errorLoading', 'Failed to load subscriptions'), 'error');
    }
}

// Load summary statistics
async function loadSummary() {
    try {
        const data = await apiCall('/api/subscriptions/summary');
        
        // Update summary cards
        document.getElementById('monthly-cost').textContent = formatCurrency(data.total_monthly || 0);
        document.getElementById('yearly-cost').textContent = formatCurrency(data.total_yearly || 0);
        document.getElementById('active-count').textContent = data.active_count || 0;
        document.getElementById('unused-count').textContent = data.unused_count || 0;
        
        // Show reminders section if there are upcoming renewals
        const upcomingRenewals = data.upcoming_renewals || [];
        if (upcomingRenewals.length > 0) {
            document.getElementById('reminders-section').classList.remove('hidden');
            renderReminders(upcomingRenewals);
        } else {
            document.getElementById('reminders-section').classList.add('hidden');
        }
        
        // Show unused section if there are unused subscriptions
        const unusedSubs = data.unused_subscriptions || [];
        if (unusedSubs.length > 0) {
            document.getElementById('unused-section').classList.remove('hidden');
            document.getElementById('potential-savings').textContent = formatCurrency(
                unusedSubs.reduce((sum, s) => sum + (s.monthly_cost || 0), 0)
            );
            renderUnusedSubscriptions(unusedSubs);
        } else {
            document.getElementById('unused-section').classList.add('hidden');
        }
    } catch (error) {
        console.error('Failed to load summary:', error);
    }
}

// Render subscriptions
function renderSubscriptions() {
    const container = document.getElementById('subscriptions-container');
    const emptyState = document.getElementById('empty-state');
    
    // Filter subscriptions
    let filtered = subscriptions;
    if (currentFilter !== 'all') {
        filtered = subscriptions.filter(sub => {
            const catName = (sub.category_name || '').toLowerCase();
            if (currentFilter === 'entertainment') {
                return catName.includes('entertainment') || catName.includes('streaming') || catName.includes('media');
            } else if (currentFilter === 'software') {
                return catName.includes('software') || catName.includes('tech') || catName.includes('digital');
            } else {
                return !catName.includes('entertainment') && !catName.includes('streaming') && 
                       !catName.includes('software') && !catName.includes('tech');
            }
        });
    }
    
    if (filtered.length === 0) {
        container.innerHTML = '';
        emptyState.classList.remove('hidden');
        return;
    }
    
    emptyState.classList.add('hidden');
    
    container.innerHTML = filtered.map(sub => createSubscriptionCard(sub)).join('');
}

// Create subscription card HTML
function createSubscriptionCard(sub) {
    const serviceInfo = SERVICE_ICONS[sub.service_name] || SERVICE_ICONS['default'];
    const icon = serviceInfo.icon;
    const color = serviceInfo.color;
    
    // Days until renewal badge
    let renewalBadge = '';
    if (sub.days_until_renewal !== null) {
        if (sub.days_until_renewal < 0) {
            renewalBadge = `<span class="px-2 py-0.5 rounded-full text-xs bg-red-500/10 text-red-500 border border-red-500/20">${window.getTranslation('subscriptions.overdue', 'Overdue')}</span>`;
        } else if (sub.days_until_renewal === 0) {
            renewalBadge = `<span class="px-2 py-0.5 rounded-full text-xs bg-orange-500/10 text-orange-500 border border-orange-500/20">${window.getTranslation('subscriptions.dueToday', 'Due today')}</span>`;
        } else if (sub.days_until_renewal <= 7) {
            renewalBadge = `<span class="px-2 py-0.5 rounded-full text-xs bg-amber-500/10 text-amber-500 border border-amber-500/20">${sub.days_until_renewal} ${window.getTranslation('subscriptions.daysLeft', 'days left')}</span>`;
        }
    }
    
    // Unused badge
    const unusedBadge = sub.is_unused ? 
        `<span class="px-2 py-0.5 rounded-full text-xs bg-orange-500/10 text-orange-500 border border-orange-500/20 flex items-center gap-1">
            <span class="material-symbols-outlined text-[12px]">warning</span>
            ${window.getTranslation('subscriptions.unused', 'Unused')}
        </span>` : '';
    
    // Frequency badge
    const frequencyText = window.getTranslation(`recurring.frequency.${sub.frequency}`, sub.frequency);
    
    // Next billing date
    const nextBilling = sub.next_due_date ? new Date(sub.next_due_date).toLocaleDateString() : '-';
    
    // Inactive overlay
    const inactiveClass = sub.is_active ? '' : 'opacity-50';
    const inactiveBadge = sub.is_active ? '' : 
        `<span class="px-2 py-0.5 rounded-full text-xs bg-slate-500/10 text-slate-500 border border-slate-500/20">${window.getTranslation('subscriptions.paused', 'Paused')}</span>`;
    
    return `
        <div class="bg-white dark:bg-card-dark rounded-2xl p-5 border border-border-light dark:border-[#233648] shadow-sm hover:shadow-lg transition-all ${inactiveClass}" data-id="${sub.id}">
            <div class="flex items-start gap-4">
                <!-- Icon -->
                <div class="w-12 h-12 rounded-xl flex items-center justify-center shrink-0" style="background: ${color}15;">
                    <span class="material-symbols-outlined text-[24px]" style="color: ${color};">${icon}</span>
                </div>
                
                <!-- Content -->
                <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 mb-1 flex-wrap">
                        <h3 class="font-semibold text-text-main dark:text-white truncate">${escapeHtml(sub.name)}</h3>
                        ${renewalBadge}
                        ${unusedBadge}
                        ${inactiveBadge}
                    </div>
                    
                    <div class="flex items-center gap-2 text-sm text-text-muted dark:text-[#92adc9] mb-3">
                        <span class="px-2 py-0.5 rounded-full text-xs" style="background: ${sub.category_color}20; color: ${sub.category_color};">
                            ${escapeHtml(sub.category_name || 'Uncategorized')}
                        </span>
                        <span>•</span>
                        <span>${frequencyText}</span>
                    </div>
                    
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-lg font-bold text-text-main dark:text-white">${formatCurrency(sub.amount)}</p>
                            <p class="text-xs text-text-muted dark:text-[#92adc9]">${formatCurrency(sub.monthly_cost)}/${window.getTranslation('subscriptions.perMonth', 'mo')}</p>
                        </div>
                        <div class="text-right">
                            <p class="text-xs text-text-muted dark:text-[#92adc9]">${window.getTranslation('subscriptions.nextBilling', 'Next billing')}</p>
                            <p class="text-sm font-medium text-text-main dark:text-white">${nextBilling}</p>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Actions -->
            <div class="flex items-center justify-between mt-4 pt-4 border-t border-border-light dark:border-[#233648]">
                <div class="flex gap-1">
                    ${sub.is_unused ? `
                    <button onclick="markAsUsed(${sub.id})" class="p-2 rounded-lg hover:bg-green-500/10 text-green-500 transition-colors" title="${window.getTranslation('subscriptions.markUsed', 'Mark as used')}">
                        <span class="material-symbols-outlined text-[18px]">check_circle</span>
                    </button>
                    ` : ''}
                    <button onclick="editSubscription(${sub.id})" class="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-[#233648] text-text-muted dark:text-[#92adc9] transition-colors" title="${window.getTranslation('common.edit', 'Edit')}">
                        <span class="material-symbols-outlined text-[18px]">edit</span>
                    </button>
                    <button onclick="toggleSubscription(${sub.id}, ${!sub.is_active})" class="p-2 rounded-lg hover:bg-slate-100 dark:hover:bg-[#233648] text-text-muted dark:text-[#92adc9] transition-colors" title="${sub.is_active ? window.getTranslation('subscriptions.pause', 'Pause') : window.getTranslation('subscriptions.resume', 'Resume')}">
                        <span class="material-symbols-outlined text-[18px]">${sub.is_active ? 'pause_circle' : 'play_circle'}</span>
                    </button>
                </div>
                <button onclick="deleteSubscription(${sub.id})" class="p-2 rounded-lg hover:bg-red-500/10 text-red-500 transition-colors" title="${window.getTranslation('common.delete', 'Delete')}">
                    <span class="material-symbols-outlined text-[18px]">delete</span>
                </button>
            </div>
        </div>
    `;
}

// Render reminders
function renderReminders(renewals) {
    const container = document.getElementById('reminders-list');
    
    container.innerHTML = renewals.map(sub => {
        const serviceInfo = SERVICE_ICONS[sub.service_name] || SERVICE_ICONS['default'];
        const daysText = sub.days_until_renewal === 0 ? 
            window.getTranslation('subscriptions.dueToday', 'Due today') :
            `${sub.days_until_renewal} ${window.getTranslation('subscriptions.daysLeft', 'days left')}`;
        
        return `
            <div class="flex items-center justify-between p-3 bg-white/50 dark:bg-white/5 rounded-xl">
                <div class="flex items-center gap-3">
                    <span class="material-symbols-outlined text-[20px]" style="color: ${serviceInfo.color};">${serviceInfo.icon}</span>
                    <div>
                        <p class="font-medium text-text-main dark:text-white text-sm">${escapeHtml(sub.name)}</p>
                        <p class="text-xs text-amber-600 dark:text-amber-400">${daysText}</p>
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <span class="font-semibold text-text-main dark:text-white">${formatCurrency(sub.amount)}</span>
                    <button onclick="dismissReminder(${sub.id})" class="p-1 hover:bg-white/20 rounded transition-colors" title="${window.getTranslation('subscriptions.dismiss', 'Dismiss')}">
                        <span class="material-symbols-outlined text-[16px] text-text-muted dark:text-[#92adc9]">close</span>
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// Render unused subscriptions
function renderUnusedSubscriptions(unusedSubs) {
    const container = document.getElementById('unused-list');
    
    container.innerHTML = unusedSubs.map(sub => {
        const serviceInfo = SERVICE_ICONS[sub.service_name] || SERVICE_ICONS['default'];
        const lastUsedText = sub.last_used_date ? 
            window.getTranslation('subscriptions.lastUsed', 'Last used') + ': ' + new Date(sub.last_used_date).toLocaleDateString() :
            window.getTranslation('subscriptions.neverUsed', 'Never marked as used');
        
        return `
            <div class="flex items-center justify-between p-3 bg-white/50 dark:bg-white/5 rounded-xl">
                <div class="flex items-center gap-3">
                    <span class="material-symbols-outlined text-[20px]" style="color: ${serviceInfo.color};">${serviceInfo.icon}</span>
                    <div>
                        <p class="font-medium text-text-main dark:text-white text-sm">${escapeHtml(sub.name)}</p>
                        <p class="text-xs text-text-muted dark:text-[#92adc9]">${lastUsedText}</p>
                    </div>
                </div>
                <div class="flex items-center gap-2">
                    <span class="font-semibold text-orange-500">${formatCurrency(sub.monthly_cost)}/mo</span>
                    <button onclick="markAsUsed(${sub.id})" class="p-1.5 bg-green-500/10 hover:bg-green-500/20 rounded-lg transition-colors" title="${window.getTranslation('subscriptions.markUsed', 'Mark as used')}">
                        <span class="material-symbols-outlined text-[16px] text-green-500">check</span>
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// Detect subscriptions from expense history
async function detectSubscriptions() {
    const btn = document.getElementById('detect-btn');
    const originalText = btn.innerHTML;
    btn.innerHTML = `<span class="material-symbols-outlined animate-spin text-[20px]">refresh</span> <span>${window.getTranslation('subscriptions.detecting', 'Detecting...')}</span>`;
    btn.disabled = true;
    
    try {
        const data = await apiCall('/api/subscriptions/detect', { method: 'POST' });
        suggestions = data.suggestions || [];
        
        if (suggestions.length === 0) {
            showToast(window.getTranslation('subscriptions.noDetected', 'No subscriptions detected in your expenses'), 'info');
        } else {
            renderSuggestions(suggestions);
            document.getElementById('suggestions-section').classList.remove('hidden');
            showToast(window.getTranslation('subscriptions.detected', `Found ${suggestions.length} potential subscriptions`), 'success');
        }
    } catch (error) {
        console.error('Failed to detect subscriptions:', error);
        showToast(window.getTranslation('subscriptions.errorDetecting', 'Failed to detect subscriptions'), 'error');
    } finally {
        btn.innerHTML = originalText;
        btn.disabled = false;
    }
}

// Render suggestions
function renderSuggestions(suggestions) {
    const container = document.getElementById('suggestions-list');
    
    container.innerHTML = suggestions.map((s, index) => {
        const serviceInfo = s.service_name ? SERVICE_ICONS[s.service_name] : null;
        const icon = serviceInfo?.icon || 'subscriptions';
        const color = serviceInfo?.color || s.category_color || '#2b8cee';
        
        return `
            <div class="flex items-center justify-between p-4 bg-white/50 dark:bg-white/5 rounded-xl">
                <div class="flex items-center gap-4">
                    <div class="w-10 h-10 rounded-xl flex items-center justify-center" style="background: ${color}20;">
                        <span class="material-symbols-outlined text-[20px]" style="color: ${color};">${icon}</span>
                    </div>
                    <div>
                        <p class="font-medium text-text-main dark:text-white">${escapeHtml(s.name)}</p>
                        <div class="flex items-center gap-2 text-xs text-text-muted dark:text-[#92adc9]">
                            <span>${escapeHtml(s.category_name)}</span>
                            <span>•</span>
                            <span>${window.getTranslation(`recurring.frequency.${s.frequency}`, s.frequency)}</span>
                            <span>•</span>
                            <span class="text-blue-400">${Math.round(s.confidence_score)}% ${window.getTranslation('subscriptions.confidence', 'confidence')}</span>
                        </div>
                    </div>
                </div>
                <div class="flex items-center gap-3">
                    <span class="font-bold text-text-main dark:text-white">${formatCurrency(s.amount)}</span>
                    <button onclick="acceptSuggestion(${index})" class="px-3 py-1.5 bg-primary hover:bg-primary/90 text-white rounded-lg text-sm font-medium transition-colors">
                        ${window.getTranslation('subscriptions.accept', 'Add')}
                    </button>
                    <button onclick="dismissSuggestion(${index})" class="p-1.5 hover:bg-white/20 rounded-lg transition-colors">
                        <span class="material-symbols-outlined text-[18px] text-text-muted dark:text-[#92adc9]">close</span>
                    </button>
                </div>
            </div>
        `;
    }).join('');
}

// Accept suggestion
async function acceptSuggestion(index) {
    const suggestion = suggestions[index];
    
    try {
        await apiCall('/api/subscriptions/accept-suggestion', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(suggestion)
        });
        
        showToast(window.getTranslation('subscriptions.added', 'Subscription added'), 'success');
        
        // Remove from suggestions
        suggestions.splice(index, 1);
        if (suggestions.length === 0) {
            document.getElementById('suggestions-section').classList.add('hidden');
        } else {
            renderSuggestions(suggestions);
        }
        
        // Reload subscriptions
        await loadSubscriptions();
        await loadSummary();
    } catch (error) {
        console.error('Failed to accept suggestion:', error);
        showToast(window.getTranslation('common.error', 'An error occurred'), 'error');
    }
}

// Dismiss suggestion
function dismissSuggestion(index) {
    suggestions.splice(index, 1);
    if (suggestions.length === 0) {
        document.getElementById('suggestions-section').classList.add('hidden');
    } else {
        renderSuggestions(suggestions);
    }
}

// Hide suggestions section
function hideSuggestions() {
    document.getElementById('suggestions-section').classList.add('hidden');
}

// Open subscription modal
function openSubscriptionModal(subscriptionId = null) {
    const modal = document.getElementById('subscription-modal');
    const form = document.getElementById('subscription-form');
    const title = document.getElementById('modal-title');
    
    form.reset();
    document.getElementById('subscription-id').value = '';
    
    if (subscriptionId) {
        // Edit mode
        const sub = subscriptions.find(s => s.id === subscriptionId);
        if (sub) {
            title.textContent = window.getTranslation('subscriptions.editTitle', 'Edit Subscription');
            document.getElementById('subscription-id').value = sub.id;
            document.getElementById('sub-name').value = sub.name;
            document.getElementById('sub-amount').value = sub.amount;
            document.getElementById('sub-frequency').value = sub.frequency;
            document.getElementById('sub-category').value = sub.category_id;
            document.getElementById('sub-next-date').value = sub.next_due_date.split('T')[0];
            document.getElementById('sub-reminder').value = sub.reminder_days || 3;
            document.getElementById('sub-notes').value = sub.notes || '';
            document.getElementById('sub-auto-create').checked = sub.auto_create;
        }
    } else {
        // Add mode
        title.textContent = window.getTranslation('subscriptions.addTitle', 'Add Subscription');
        // Set default date to today
        const today = new Date().toISOString().split('T')[0];
        document.getElementById('sub-next-date').value = today;
    }
    
    modal.classList.remove('hidden');
}

// Close subscription modal
function closeSubscriptionModal() {
    document.getElementById('subscription-modal').classList.add('hidden');
}

// Handle subscription form submit
async function handleSubscriptionSubmit(e) {
    e.preventDefault();
    
    const subscriptionId = document.getElementById('subscription-id').value;
    const data = {
        name: document.getElementById('sub-name').value,
        amount: parseFloat(document.getElementById('sub-amount').value),
        frequency: document.getElementById('sub-frequency').value,
        category_id: parseInt(document.getElementById('sub-category').value),
        next_due_date: document.getElementById('sub-next-date').value,
        reminder_days: parseInt(document.getElementById('sub-reminder').value),
        notes: document.getElementById('sub-notes').value,
        auto_create: document.getElementById('sub-auto-create').checked
    };
    
    try {
        if (subscriptionId) {
            // Update
            await apiCall(`/api/subscriptions/${subscriptionId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            showToast(window.getTranslation('subscriptions.updated', 'Subscription updated'), 'success');
        } else {
            // Create
            await apiCall('/api/subscriptions/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            showToast(window.getTranslation('subscriptions.added', 'Subscription added'), 'success');
        }
        
        closeSubscriptionModal();
        await loadSubscriptions();
        await loadSummary();
    } catch (error) {
        console.error('Failed to save subscription:', error);
        showToast(window.getTranslation('common.error', 'An error occurred'), 'error');
    }
}

// Edit subscription
function editSubscription(id) {
    openSubscriptionModal(id);
}

// Toggle subscription active state
async function toggleSubscription(id, isActive) {
    try {
        await apiCall(`/api/subscriptions/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_active: isActive })
        });
        
        const statusText = isActive ? 
            window.getTranslation('subscriptions.resumed', 'Subscription resumed') : 
            window.getTranslation('subscriptions.paused', 'Subscription paused');
        showToast(statusText, 'success');
        
        await loadSubscriptions();
        await loadSummary();
    } catch (error) {
        console.error('Failed to toggle subscription:', error);
        showToast(window.getTranslation('common.error', 'An error occurred'), 'error');
    }
}

// Delete subscription
async function deleteSubscription(id) {
    const confirmText = window.getTranslation('subscriptions.deleteConfirm', 'Are you sure you want to delete this subscription?');
    if (!confirm(confirmText)) return;
    
    try {
        await apiCall(`/api/subscriptions/${id}`, { method: 'DELETE' });
        showToast(window.getTranslation('subscriptions.deleted', 'Subscription deleted'), 'success');
        await loadSubscriptions();
        await loadSummary();
    } catch (error) {
        console.error('Failed to delete subscription:', error);
        showToast(window.getTranslation('common.error', 'An error occurred'), 'error');
    }
}

// Mark subscription as used
async function markAsUsed(id) {
    try {
        await apiCall(`/api/subscriptions/${id}/mark-used`, { method: 'POST' });
        showToast(window.getTranslation('subscriptions.markedUsed', 'Marked as used'), 'success');
        await loadSubscriptions();
        await loadSummary();
    } catch (error) {
        console.error('Failed to mark as used:', error);
        showToast(window.getTranslation('common.error', 'An error occurred'), 'error');
    }
}

// Dismiss renewal reminder
async function dismissReminder(id) {
    try {
        await apiCall(`/api/subscriptions/${id}/dismiss-reminder`, { method: 'POST' });
        await loadSummary();
    } catch (error) {
        console.error('Failed to dismiss reminder:', error);
    }
}

// Select a popular service
function selectService(serviceName) {
    const serviceNames = {
        'netflix': 'Netflix',
        'spotify': 'Spotify Premium',
        'youtube_premium': 'YouTube Premium',
        'disney_plus': 'Disney+',
        'gym': 'Gym Membership',
        'chatgpt': 'ChatGPT Plus'
    };
    
    document.getElementById('sub-name').value = serviceNames[serviceName] || serviceName;
    
    // Clear other service buttons selection
    document.querySelectorAll('.service-btn').forEach(btn => {
        btn.classList.remove('ring-2', 'ring-primary');
    });
    
    // Highlight selected
    event.target.closest('.service-btn')?.classList.add('ring-2', 'ring-primary');
}

// Filter subscriptions
function filterSubscriptions(filter) {
    currentFilter = filter;
    
    // Update tab styles - toggle active class for visual feedback
    document.querySelectorAll('.filter-tab').forEach(tab => {
        if (tab.dataset.filter === filter) {
            tab.classList.add('active');
            tab.style.transform = 'scale(1.05)';
            tab.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
            tab.style.opacity = '1';
        } else {
            tab.classList.remove('active');
            tab.style.transform = 'scale(1)';
            tab.style.boxShadow = 'none';
            tab.style.opacity = '0.7';
        }
    });
    
    renderSubscriptions();
}

// Scroll to unused section
function scrollToUnused() {
    const section = document.getElementById('unused-section');
    if (!section.classList.contains('hidden')) {
        section.scrollIntoView({ behavior: 'smooth' });
    }
}

// Format currency
function formatCurrency(amount) {
    const currency = window.userCurrency || 'USD';
    return new Intl.NumberFormat(undefined, {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    }).format(amount);
}

// Escape HTML
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Mobile menu setup
function setupMobileMenu() {
    const menuToggle = document.getElementById('mobile-menu-toggle');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (menuToggle && mobileMenu) {
        menuToggle.addEventListener('click', () => {
            mobileMenu.classList.remove('hidden');
        });
    }
}

function closeMobileMenu() {
    const mobileMenu = document.getElementById('mobile-menu');
    if (mobileMenu) {
        mobileMenu.classList.add('hidden');
    }
}
