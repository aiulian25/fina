// Recurring expenses page JavaScript

let currentRecurring = [];
let detectedSuggestions = [];

// Load user profile to get currency
async function loadUserCurrency() {
    try {
        const profile = await apiCall('/api/settings/profile');
        window.userCurrency = profile.profile.currency || 'RON';
    } catch (error) {
        console.error('Failed to load user currency:', error);
        window.userCurrency = 'RON';
    }
}

// Load recurring expenses
async function loadRecurringExpenses() {
    try {
        const data = await apiCall('/api/recurring/');
        currentRecurring = data.recurring_expenses || [];
        displayRecurringExpenses(currentRecurring);
    } catch (error) {
        console.error('Failed to load recurring expenses:', error);
        showToast(window.getTranslation('recurring.errorLoading', 'Failed to load recurring expenses'), 'error');
    }
}

// Display recurring expenses
function displayRecurringExpenses(recurring) {
    const container = document.getElementById('recurring-list');
    
    if (!recurring || recurring.length === 0) {
        const noRecurringText = window.getTranslation('recurring.noRecurring', 'No recurring expenses yet');
        const addFirstText = window.getTranslation('recurring.addFirst', 'Add your first recurring expense or detect patterns from existing expenses');
        container.innerHTML = `
            <div class="p-12 text-center">
                <span class="material-symbols-outlined text-6xl text-[#92adc9] mb-4 block">repeat</span>
                <p class="text-[#92adc9] text-lg mb-2">${noRecurringText}</p>
                <p class="text-[#92adc9] text-sm">${addFirstText}</p>
            </div>
        `;
        return;
    }
    
    // Group by active status
    const active = recurring.filter(r => r.is_active);
    const inactive = recurring.filter(r => !r.is_active);
    
    let html = '';
    
    if (active.length > 0) {
        html += '<div class="mb-6"><h3 class="text-lg font-semibold text-text-main dark:text-white mb-4">' + 
                window.getTranslation('recurring.active', 'Active Recurring Expenses') + '</h3>';
        html += '<div class="space-y-3">' + active.map(r => renderRecurringCard(r)).join('') + '</div></div>';
    }
    
    if (inactive.length > 0) {
        html += '<div><h3 class="text-lg font-semibold text-text-muted dark:text-[#92adc9] mb-4">' + 
                window.getTranslation('recurring.inactive', 'Inactive') + '</h3>';
        html += '<div class="space-y-3 opacity-60">' + inactive.map(r => renderRecurringCard(r)).join('') + '</div></div>';
    }
    
    container.innerHTML = html;
}

// Render individual recurring expense card
function renderRecurringCard(recurring) {
    const nextDue = new Date(recurring.next_due_date);
    const today = new Date();
    const daysUntil = Math.ceil((nextDue - today) / (1000 * 60 * 60 * 24));
    
    let dueDateClass = 'text-text-muted dark:text-[#92adc9]';
    let dueDateText = '';
    
    if (daysUntil < 0) {
        dueDateClass = 'text-red-400';
        dueDateText = window.getTranslation('recurring.overdue', 'Overdue');
    } else if (daysUntil === 0) {
        dueDateClass = 'text-orange-400';
        dueDateText = window.getTranslation('recurring.dueToday', 'Due today');
    } else if (daysUntil <= 7) {
        dueDateClass = 'text-yellow-400';
        dueDateText = window.getTranslation('recurring.dueIn', 'Due in') + ` ${daysUntil} ` + 
                     (daysUntil === 1 ? window.getTranslation('recurring.day', 'day') : window.getTranslation('recurring.days', 'days'));
    } else {
        dueDateText = nextDue.toLocaleDateString();
    }
    
    const frequencyText = window.getTranslation(`recurring.frequency.${recurring.frequency}`, recurring.frequency);
    const autoCreateBadge = recurring.auto_create ? 
        `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-green-500/10 text-green-400 border border-green-500/20">
            <span class="material-symbols-outlined text-[14px]">check_circle</span>
            ${window.getTranslation('recurring.autoCreate', 'Auto-create')}
        </span>` : '';
    
    const detectedBadge = recurring.detected ? 
        `<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-blue-500/10 text-blue-400 border border-blue-500/20">
            <span class="material-symbols-outlined text-[14px]">auto_awesome</span>
            ${window.getTranslation('recurring.detected', 'Auto-detected')} ${Math.round(recurring.confidence_score)}%
        </span>` : '';
    
    return `
        <div class="bg-white dark:bg-[#0f1419] border border-gray-200 dark:border-white/10 rounded-xl p-5 hover:shadow-lg transition-shadow">
            <div class="flex items-start justify-between gap-4">
                <div class="flex items-start gap-4 flex-1">
                    <div class="size-12 rounded-full flex items-center justify-center shrink-0" style="background: ${recurring.category_color}20;">
                        <span class="material-symbols-outlined text-[24px]" style="color: ${recurring.category_color};">repeat</span>
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center gap-2 mb-1">
                            <h4 class="text-text-main dark:text-white font-semibold truncate">${recurring.name}</h4>
                            ${autoCreateBadge}
                            ${detectedBadge}
                        </div>
                        <div class="flex flex-wrap items-center gap-2 text-sm text-text-muted dark:text-[#92adc9] mb-2">
                            <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs" style="background: ${recurring.category_color}20; color: ${recurring.category_color};">
                                ${recurring.category_name}
                            </span>
                            <span>•</span>
                            <span>${frequencyText}</span>
                            ${recurring.notes ? `<span>•</span><span class="truncate">${recurring.notes}</span>` : ''}
                        </div>
                        <div class="flex items-center gap-3 text-sm flex-wrap">
                            <div class="${dueDateClass} font-medium">
                                <span class="material-symbols-outlined text-[16px] align-middle mr-1">schedule</span>
                                ${dueDateText}
                            </div>
                            <div class="text-text-main dark:text-white font-semibold">
                                ${formatCurrency(recurring.amount, window.userCurrency || recurring.currency)}
                            </div>
                            ${recurring.last_created_date ? `
                            <div class="text-text-muted dark:text-[#92adc9] text-xs">
                                <span class="material-symbols-outlined text-[14px] align-middle mr-1">check_circle</span>
                                ${window.getTranslation('recurring.lastCreated', 'Last created')}: ${new Date(recurring.last_created_date).toLocaleDateString()}
                            </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
                <div class="flex items-center gap-1 shrink-0">
                    ${daysUntil <= 7 && recurring.is_active ? `
                    <button onclick="createExpenseFromRecurring(${recurring.id})" 
                            class="p-2 rounded-lg hover:bg-green-500/10 text-green-400 transition-colors"
                            title="${window.getTranslation('recurring.createExpense', 'Create expense now')}">
                        <span class="material-symbols-outlined text-[20px]">add_circle</span>
                    </button>
                    ` : ''}
                    <button onclick="editRecurring(${recurring.id})" 
                            class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-white/10 text-text-muted dark:text-[#92adc9] transition-colors"
                            title="${window.getTranslation('common.edit', 'Edit')}">
                        <span class="material-symbols-outlined text-[20px]">edit</span>
                    </button>
                    <button onclick="toggleRecurringActive(${recurring.id}, ${!recurring.is_active})" 
                            class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-white/10 text-text-muted dark:text-[#92adc9] transition-colors"
                            title="${recurring.is_active ? window.getTranslation('recurring.deactivate', 'Deactivate') : window.getTranslation('recurring.activate', 'Activate')}">
                        <span class="material-symbols-outlined text-[20px]">${recurring.is_active ? 'pause_circle' : 'play_circle'}</span>
                    </button>
                    <button onclick="deleteRecurring(${recurring.id})" 
                            class="p-2 rounded-lg hover:bg-red-100 dark:hover:bg-red-500/10 text-red-400 transition-colors"
                            title="${window.getTranslation('common.delete', 'Delete')}">
                        <span class="material-symbols-outlined text-[20px]">delete</span>
                    </button>
                </div>
            </div>
        </div>
    `;
}

// Create expense from recurring
async function createExpenseFromRecurring(recurringId) {
    try {
        const data = await apiCall(`/api/recurring/${recurringId}/create-expense`, {
            method: 'POST'
        });
        
        showToast(window.getTranslation('recurring.expenseCreated', 'Expense created successfully!'), 'success');
        loadRecurringExpenses();
    } catch (error) {
        console.error('Failed to create expense:', error);
        showToast(window.getTranslation('recurring.errorCreating', 'Failed to create expense'), 'error');
    }
}

// Toggle recurring active status
async function toggleRecurringActive(recurringId, isActive) {
    try {
        await apiCall(`/api/recurring/${recurringId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ is_active: isActive })
        });
        
        const statusText = isActive ? 
            window.getTranslation('recurring.activated', 'Recurring expense activated') : 
            window.getTranslation('recurring.deactivated', 'Recurring expense deactivated');
        showToast(statusText, 'success');
        loadRecurringExpenses();
    } catch (error) {
        console.error('Failed to toggle recurring status:', error);
        showToast(window.getTranslation('common.error', 'An error occurred'), 'error');
    }
}

// Delete recurring expense
async function deleteRecurring(recurringId) {
    const confirmText = window.getTranslation('recurring.deleteConfirm', 'Are you sure you want to delete this recurring expense?');
    if (!confirm(confirmText)) return;
    
    try {
        await apiCall(`/api/recurring/${recurringId}`, {
            method: 'DELETE'
        });
        
        showToast(window.getTranslation('recurring.deleted', 'Recurring expense deleted'), 'success');
        loadRecurringExpenses();
    } catch (error) {
        console.error('Failed to delete recurring expense:', error);
        showToast(window.getTranslation('common.error', 'An error occurred'), 'error');
    }
}

// Edit recurring expense
function editRecurring(recurringId) {
    const recurring = currentRecurring.find(r => r.id === recurringId);
    if (!recurring) return;
    
    // Populate form
    document.getElementById('recurring-id').value = recurring.id;
    document.getElementById('recurring-name').value = recurring.name;
    document.getElementById('recurring-amount').value = recurring.amount;
    document.getElementById('recurring-category').value = recurring.category_id;
    document.getElementById('recurring-frequency').value = recurring.frequency;
    document.getElementById('recurring-day').value = recurring.day_of_period || '';
    document.getElementById('recurring-next-due').value = recurring.next_due_date.split('T')[0];
    document.getElementById('recurring-auto-create').checked = recurring.auto_create;
    document.getElementById('recurring-notes').value = recurring.notes || '';
    
    // Update modal title
    document.getElementById('modal-title').textContent = window.getTranslation('recurring.edit', 'Edit Recurring Expense');
    document.getElementById('recurring-submit-btn').textContent = window.getTranslation('actions.update', 'Update');
    
    // Show modal
    document.getElementById('add-recurring-modal').classList.remove('hidden');
}

// Show add recurring modal
function showAddRecurringModal() {
    document.getElementById('recurring-form').reset();
    document.getElementById('recurring-id').value = '';
    document.getElementById('modal-title').textContent = window.getTranslation('recurring.add', 'Add Recurring Expense');
    document.getElementById('recurring-submit-btn').textContent = window.getTranslation('actions.save', 'Save');
    document.getElementById('add-recurring-modal').classList.remove('hidden');
}

// Close modal
function closeRecurringModal() {
    document.getElementById('add-recurring-modal').classList.add('hidden');
}

// Save recurring expense
async function saveRecurringExpense(event) {
    event.preventDefault();
    
    const recurringId = document.getElementById('recurring-id').value;
    const formData = {
        name: document.getElementById('recurring-name').value,
        amount: parseFloat(document.getElementById('recurring-amount').value),
        // Don't send currency - let backend use current_user.currency from settings
        category_id: parseInt(document.getElementById('recurring-category').value),
        frequency: document.getElementById('recurring-frequency').value,
        day_of_period: parseInt(document.getElementById('recurring-day').value) || null,
        next_due_date: document.getElementById('recurring-next-due').value,
        auto_create: document.getElementById('recurring-auto-create').checked,
        notes: document.getElementById('recurring-notes').value
    };
    
    try {
        if (recurringId) {
            // Update
            await apiCall(`/api/recurring/${recurringId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            showToast(window.getTranslation('recurring.updated', 'Recurring expense updated'), 'success');
        } else {
            // Create
            await apiCall('/api/recurring/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formData)
            });
            showToast(window.getTranslation('recurring.created', 'Recurring expense created'), 'success');
        }
        
        closeRecurringModal();
        loadRecurringExpenses();
    } catch (error) {
        console.error('Failed to save recurring expense:', error);
        showToast(window.getTranslation('common.error', 'An error occurred'), 'error');
    }
}

// Detect recurring patterns
async function detectRecurringPatterns() {
    const detectBtn = document.getElementById('detect-btn');
    const originalText = detectBtn.innerHTML;
    detectBtn.innerHTML = '<span class="material-symbols-outlined animate-spin">refresh</span> ' + 
                         window.getTranslation('recurring.detecting', 'Detecting...');
    detectBtn.disabled = true;
    
    try {
        const data = await apiCall('/api/recurring/detect', {
            method: 'POST'
        });
        
        detectedSuggestions = data.suggestions || [];
        
        if (detectedSuggestions.length === 0) {
            showToast(window.getTranslation('recurring.noPatterns', 'No recurring patterns detected'), 'info');
        } else {
            displaySuggestions(detectedSuggestions);
            document.getElementById('suggestions-section').classList.remove('hidden');
            showToast(window.getTranslation('recurring.patternsFound', `Found ${detectedSuggestions.length} potential recurring expenses`), 'success');
        }
    } catch (error) {
        console.error('Failed to detect patterns:', error);
        showToast(window.getTranslation('recurring.errorDetecting', 'Failed to detect patterns'), 'error');
    } finally {
        detectBtn.innerHTML = originalText;
        detectBtn.disabled = false;
    }
}

// Display suggestions
function displaySuggestions(suggestions) {
    const container = document.getElementById('suggestions-list');
    
    container.innerHTML = suggestions.map((s, index) => `
        <div class="bg-white dark:bg-[#0f1419] border border-blue-500/30 dark:border-blue-500/30 rounded-xl p-5">
            <div class="flex items-start justify-between gap-4">
                <div class="flex items-start gap-4 flex-1">
                    <div class="size-12 rounded-full flex items-center justify-center shrink-0 bg-blue-500/10">
                        <span class="material-symbols-outlined text-[24px] text-blue-400">auto_awesome</span>
                    </div>
                    <div class="flex-1 min-w-0">
                        <h4 class="text-text-main dark:text-white font-semibold mb-1">${s.name}</h4>
                        <div class="flex flex-wrap items-center gap-2 text-sm text-text-muted dark:text-[#92adc9] mb-2">
                            <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs" style="background: ${s.category_color}20; color: ${s.category_color};">
                                ${s.category_name}
                            </span>
                            <span>•</span>
                            <span>${window.getTranslation(`recurring.frequency.${s.frequency}`, s.frequency)}</span>
                            <span>•</span>
                            <span>${s.occurrences} ${window.getTranslation('recurring.occurrences', 'occurrences')}</span>
                        </div>
                        <div class="flex items-center gap-3 text-sm">
                            <div class="text-text-main dark:text-white font-semibold">
                                ${formatCurrency(s.amount, window.userCurrency || s.currency)}
                            </div>
                            <div class="text-blue-400">
                                <span class="material-symbols-outlined text-[16px] align-middle mr-1">verified</span>
                                ${Math.round(s.confidence_score)}% ${window.getTranslation('recurring.confidence', 'confidence')}
                            </div>
                        </div>
                    </div>
                </div>
                <div class="flex items-center gap-2 shrink-0">
                    <button onclick="acceptSuggestion(${index})" 
                            class="px-4 py-2 bg-primary hover:bg-primary-dark text-white rounded-lg transition-colors flex items-center gap-2">
                        <span class="material-symbols-outlined text-[18px]">add</span>
                        ${window.getTranslation('recurring.accept', 'Accept')}
                    </button>
                    <button onclick="dismissSuggestion(${index})" 
                            class="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-white/10 text-text-muted dark:text-[#92adc9] transition-colors"
                            title="${window.getTranslation('recurring.dismiss', 'Dismiss')}">
                        <span class="material-symbols-outlined text-[20px]">close</span>
                    </button>
                </div>
            </div>
        </div>
    `).join('');
}

// Accept suggestion
async function acceptSuggestion(index) {
    const suggestion = detectedSuggestions[index];
    
    try {
        await apiCall('/api/recurring/accept-suggestion', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(suggestion)
        });
        
        showToast(window.getTranslation('recurring.suggestionAccepted', 'Recurring expense added'), 'success');
        
        // Remove suggestion
        detectedSuggestions.splice(index, 1);
        if (detectedSuggestions.length === 0) {
            document.getElementById('suggestions-section').classList.add('hidden');
        } else {
            displaySuggestions(detectedSuggestions);
        }
        
        loadRecurringExpenses();
    } catch (error) {
        console.error('Failed to accept suggestion:', error);
        showToast(window.getTranslation('common.error', 'An error occurred'), 'error');
    }
}

// Dismiss suggestion
function dismissSuggestion(index) {
    detectedSuggestions.splice(index, 1);
    if (detectedSuggestions.length === 0) {
        document.getElementById('suggestions-section').classList.add('hidden');
    } else {
        displaySuggestions(detectedSuggestions);
    }
}

// Load categories for dropdown
async function loadCategories() {
    try {
        const data = await apiCall('/api/expenses/categories');
        const select = document.getElementById('recurring-category');
        select.innerHTML = data.categories.map(cat => 
            `<option value="${cat.id}">${cat.name}</option>`
        ).join('');
    } catch (error) {
        console.error('Failed to load categories:', error);
    }
}

// Update day field based on frequency
function updateDayField() {
    const frequency = document.getElementById('recurring-frequency').value;
    const dayContainer = document.getElementById('day-container');
    const dayInput = document.getElementById('recurring-day');
    const dayLabel = document.getElementById('day-label');
    
    if (frequency === 'weekly') {
        dayContainer.classList.remove('hidden');
        dayLabel.textContent = window.getTranslation('recurring.dayOfWeek', 'Day of week');
        dayInput.type = 'select';
        dayInput.innerHTML = `
            <option value="0">${window.getTranslation('days.monday', 'Monday')}</option>
            <option value="1">${window.getTranslation('days.tuesday', 'Tuesday')}</option>
            <option value="2">${window.getTranslation('days.wednesday', 'Wednesday')}</option>
            <option value="3">${window.getTranslation('days.thursday', 'Thursday')}</option>
            <option value="4">${window.getTranslation('days.friday', 'Friday')}</option>
            <option value="5">${window.getTranslation('days.saturday', 'Saturday')}</option>
            <option value="6">${window.getTranslation('days.sunday', 'Sunday')}</option>
        `;
    } else if (frequency === 'monthly') {
        dayContainer.classList.remove('hidden');
        dayLabel.textContent = window.getTranslation('recurring.dayOfMonth', 'Day of month');
        dayInput.type = 'number';
        dayInput.min = '1';
        dayInput.max = '28';
    } else {
        dayContainer.classList.add('hidden');
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    if (document.getElementById('recurring-list')) {
        await loadUserCurrency();
        
        // Sync all recurring expenses to user's current currency
        await syncRecurringCurrency();
        
        loadRecurringExpenses();
        loadCategories();
        
        // Set default next due date to tomorrow
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        document.getElementById('recurring-next-due').valueAsDate = tomorrow;
        
        // Event listeners
        document.getElementById('recurring-form')?.addEventListener('submit', saveRecurringExpense);
        document.getElementById('recurring-frequency')?.addEventListener('change', updateDayField);
    }
});

// Sync recurring expenses currency with user profile
async function syncRecurringCurrency() {
    try {
        await apiCall('/api/recurring/sync-currency', {
            method: 'POST'
        });
    } catch (error) {
        console.error('Failed to sync currency:', error);
    }
}
