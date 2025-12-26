// Income Management JavaScript

let incomeData = [];
let incomeSources = [];
let currentIncomeId = null;

// Helper function for notifications
function showNotification(message, type = 'success') {
    if (typeof showToast === 'function') {
        showToast(message, type);
    } else {
        console.log(`${type.toUpperCase()}: ${message}`);
    }
}

// Load user currency from profile
async function loadUserCurrency() {
    try {
        const profile = await apiCall('/api/settings/profile');
        window.userCurrency = profile.profile.currency || 'GBP';
    } catch (error) {
        console.error('Failed to load user currency:', error);
        // Fallback to GBP if API fails
        window.userCurrency = 'GBP';
    }
}

// Load income data
async function loadIncome() {
    try {
        console.log('Loading income data...');
        const response = await apiCall('/api/income/');
        console.log('Income API response:', response);
        console.log('Response has income?', response.income);
        console.log('Income array:', response.income);
        if (response.income) {
            incomeData = response.income;
            console.log('Income data loaded:', incomeData.length, 'entries');
            console.log('Full income data:', JSON.stringify(incomeData, null, 2));
            renderIncomeTable();
        } else {
            console.warn('No income data in response');
            incomeData = [];
            renderIncomeTable();
        }
    } catch (error) {
        console.error('Error loading income:', error);
        showNotification(window.getTranslation('common.error', 'An error occurred'), 'error');
    }
}

// Load income sources
async function loadIncomeSources() {
    try {
        const response = await apiCall('/api/income/sources');
        if (response.sources) {
            incomeSources = response.sources;
            renderIncomeSourceOptions();
        }
    } catch (error) {
        console.error('Error loading income sources:', error);
    }
}

// Render income source options in select
function renderIncomeSourceOptions() {
    const selects = document.querySelectorAll('.income-source-select');
    selects.forEach(select => {
        select.innerHTML = '<option value="">' + window.getTranslation('form.selectSource', 'Select source...') + '</option>';
        incomeSources.forEach(source => {
            select.innerHTML += `<option value="${source.value}">${source.label}</option>`;
        });
    });
}

// Render income table
function renderIncomeTable() {
    console.log('Rendering income table with', incomeData.length, 'entries');
    const tbody = document.getElementById('income-table-body');
    if (!tbody) {
        console.error('Income table body not found!');
        return;
    }
    
    if (incomeData.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="px-6 py-12 text-center">
                    <span class="material-symbols-outlined text-6xl text-text-muted dark:text-[#92adc9] mb-4 block">payments</span>
                    <p class="text-text-muted dark:text-[#92adc9]" data-translate="income.noIncome">${window.getTranslation('income.noIncome', 'No income entries yet')}</p>
                    <p class="text-sm text-text-muted dark:text-[#92adc9] mt-2" data-translate="income.addFirst">${window.getTranslation('income.addFirst', 'Add your first income entry')}</p>
                </td>
            </tr>
        `;
        return;
    }
    
    tbody.innerHTML = incomeData.map(income => {
        const date = new Date(income.date);
        const formattedDate = formatDate(income.date);
        const source = incomeSources.find(s => s.value === income.source);
        const sourceLabel = source ? source.label : income.source;
        const sourceIcon = source ? source.icon : 'category';
        
        // Check if this is recurring income
        const isRecurring = income.is_recurring;
        const nextDueDate = income.next_due_date ? formatDate(income.next_due_date) : null;
        const isActive = income.is_active;
        const autoCreate = income.auto_create;
        
        // Build recurring info badge
        let recurringBadge = '';
        if (isRecurring && autoCreate) {
            const statusColor = isActive ? 'green' : 'gray';
            const statusIcon = isActive ? 'check_circle' : 'pause_circle';
            recurringBadge = `
                <div class="flex items-center gap-1 text-xs text-${statusColor}-600 dark:text-${statusColor}-400">
                    <span class="material-symbols-outlined text-[14px]">${statusIcon}</span>
                    <span>${income.frequency}</span>
                    ${nextDueDate ? `<span class="text-text-muted dark:text-[#92adc9]">• Next: ${nextDueDate}</span>` : ''}
                </div>
            `;
        }
        
        // Build action buttons
        let actionButtons = `
            <button onclick="editIncome(${income.id})" class="p-2 text-primary hover:bg-primary/10 rounded-lg transition-colors">
                <span class="material-symbols-outlined text-[20px]">edit</span>
            </button>
        `;
        
        if (isRecurring && autoCreate) {
            actionButtons += `
                <button onclick="toggleRecurringIncome(${income.id})" class="p-2 text-blue-500 hover:bg-blue-50 dark:hover:bg-blue-500/10 rounded-lg transition-colors" title="${isActive ? 'Pause' : 'Activate'}">
                    <span class="material-symbols-outlined text-[20px]">${isActive ? 'pause' : 'play_arrow'}</span>
                </button>
                <button onclick="createIncomeNow(${income.id})" class="p-2 text-green-500 hover:bg-green-50 dark:hover:bg-green-500/10 rounded-lg transition-colors" title="Create Now">
                    <span class="material-symbols-outlined text-[20px]">add_circle</span>
                </button>
            `;
        }
        
        actionButtons += `
            <button onclick="deleteIncome(${income.id})" class="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-500/10 rounded-lg transition-colors">
                <span class="material-symbols-outlined text-[20px]">delete</span>
            </button>
        `;
        
        return `
            <tr class="border-b border-border-light dark:border-[#233648] hover:bg-slate-50 dark:hover:bg-[#111a22] transition-colors">
                <td class="px-6 py-4">
                    <div class="flex items-center gap-3">
                        <div class="w-10 h-10 rounded-lg bg-green-500/10 flex items-center justify-center">
                            <span class="material-symbols-outlined text-green-500 text-[20px]">${sourceIcon}</span>
                        </div>
                        <div>
                            <p class="font-medium text-text-main dark:text-white">${income.description}</p>
                            <p class="text-sm text-text-muted dark:text-[#92adc9]">${sourceLabel}</p>
                            ${recurringBadge}
                        </div>
                    </div>
                </td>
                <td class="px-6 py-4 text-text-main dark:text-white">${formattedDate}</td>
                <td class="px-6 py-4">
                    <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-500/20 dark:text-green-400">
                        ${sourceLabel}
                    </span>
                </td>
                <td class="px-6 py-4 text-right">
                    <span class="font-semibold text-green-600 dark:text-green-400">
                        +${formatCurrency(income.amount, income.currency)}
                    </span>
                </td>
                <td class="px-6 py-4 text-right">
                    <div class="flex items-center justify-end gap-2">
                        ${actionButtons}
                    </div>
                </td>
            </tr>
        `;
    }).join('');
    console.log('Income table rendered successfully');
}

// Open income modal
function openIncomeModal() {
    const modal = document.getElementById('income-modal');
    const form = document.getElementById('income-form');
    const title = document.getElementById('income-modal-title');
    
    currentIncomeId = null;
    form.reset();
    title.textContent = window.getTranslation('income.add', 'Add Income');
    modal.classList.remove('hidden');
    
    // Set today's date as default
    const dateInput = document.getElementById('income-date');
    if (dateInput) {
        dateInput.valueAsDate = new Date();
    }
}

// Close income modal
function closeIncomeModal() {
    const modal = document.getElementById('income-modal');
    modal.classList.add('hidden');
    currentIncomeId = null;
}

// Edit income
function editIncome(id) {
    const income = incomeData.find(i => i.id === id);
    if (!income) return;
    
    currentIncomeId = id;
    
    const modal = document.getElementById('income-modal');
    const form = document.getElementById('income-form');
    const title = document.getElementById('income-modal-title');
    
    title.textContent = window.getTranslation('income.edit', 'Edit Income');
    
    document.getElementById('income-amount').value = income.amount;
    document.getElementById('income-source').value = income.source;
    document.getElementById('income-description').value = income.description;
    document.getElementById('income-date').value = income.date.split('T')[0];
    document.getElementById('income-tags').value = income.tags.join(', ');
    document.getElementById('income-frequency').value = income.frequency || 'once';
    
    // Show/hide custom frequency based on frequency value
    const customContainer = document.getElementById('custom-frequency-container');
    if (income.frequency === 'custom') {
        customContainer.classList.remove('hidden');
        document.getElementById('income-custom-days').value = income.custom_days || '';
    } else {
        customContainer.classList.add('hidden');
    }
    
    // Set auto_create checkbox
    const autoCreateCheckbox = document.getElementById('income-auto-create');
    if (autoCreateCheckbox) {
        autoCreateCheckbox.checked = income.auto_create || false;
    }
    
    modal.classList.remove('hidden');
}

// Save income
async function saveIncome(event) {
    event.preventDefault();
    console.log('Saving income...');
    
    const amount = document.getElementById('income-amount').value;
    const source = document.getElementById('income-source').value;
    const description = document.getElementById('income-description').value;
    const date = document.getElementById('income-date').value;
    const tagsInput = document.getElementById('income-tags').value;
    const frequency = document.getElementById('income-frequency').value;
    const customDays = document.getElementById('income-custom-days').value;
    const autoCreate = document.getElementById('income-auto-create')?.checked || false;
    
    if (!amount || !source || !description) {
        showNotification(window.getTranslation('common.missingFields', 'Missing required fields'), 'error');
        return;
    }
    
    // Validate custom frequency
    if (frequency === 'custom' && (!customDays || customDays < 1)) {
        showNotification(window.getTranslation('income.customDaysRequired', 'Please enter a valid number of days for custom frequency'), 'error');
        return;
    }
    
    const tags = tagsInput ? tagsInput.split(',').map(t => t.trim()).filter(t => t) : [];
    
    const data = {
        amount: parseFloat(amount),
        source: source,
        description: description,
        date: date,
        tags: tags,
        currency: window.userCurrency,
        frequency: frequency,
        custom_days: frequency === 'custom' ? parseInt(customDays) : null,
        auto_create: autoCreate
    };
    
    console.log('Income data to save:', data);
    
    try {
        let response;
        if (currentIncomeId) {
            console.log('Updating income:', currentIncomeId);
            response = await apiCall(`/api/income/${currentIncomeId}`, {
                method: 'PUT',
                body: JSON.stringify(data)
            });
            showNotification(window.getTranslation('income.updated', 'Income updated successfully'), 'success');
        } else {
            console.log('Creating new income');
            response = await apiCall('/api/income/', {
                method: 'POST',
                body: JSON.stringify(data)
            });
            console.log('Income created response:', response);
            showNotification(window.getTranslation('income.created', 'Income added successfully'), 'success');
        }
        
        closeIncomeModal();
        console.log('Reloading income list...');
        await loadIncome();
        
        // Reload dashboard if on dashboard page
        if (typeof loadDashboardData === 'function') {
            loadDashboardData();
        }
    } catch (error) {
        console.error('Error saving income:', error);
        showNotification(window.getTranslation('common.error', 'An error occurred'), 'error');
    }
}

// Delete income
async function deleteIncome(id) {
    if (!confirm(window.getTranslation('income.deleteConfirm', 'Are you sure you want to delete this income entry?'))) {
        return;
    }
    
    try {
        await apiCall(`/api/income/${id}`, {
            method: 'DELETE'
        });
        showNotification(window.getTranslation('income.deleted', 'Income deleted successfully'), 'success');
        loadIncome();
        
        // Reload dashboard if on dashboard page
        if (typeof loadDashboardData === 'function') {
            loadDashboardData();
        }
    } catch (error) {
        console.error('Error deleting income:', error);
        showNotification(window.getTranslation('common.error', 'An error occurred'), 'error');
    }
}

// Toggle recurring income active status
async function toggleRecurringIncome(id) {
    try {
        const response = await apiCall(`/api/income/${id}/toggle`, {
            method: 'PUT'
        });
        
        if (response.success) {
            showNotification(response.message, 'success');
            loadIncome();
        }
    } catch (error) {
        console.error('Error toggling recurring income:', error);
        showNotification(window.getTranslation('common.error', 'An error occurred'), 'error');
    }
}

// Create income now from recurring income
async function createIncomeNow(id) {
    if (!confirm(window.getTranslation('income.createNowConfirm', 'Create an income entry now from this recurring income?'))) {
        return;
    }
    
    try {
        const response = await apiCall(`/api/income/${id}/create-now`, {
            method: 'POST'
        });
        
        if (response.success) {
            showNotification(response.message, 'success');
            loadIncome();
            
            // Reload dashboard if on dashboard page
            if (typeof loadDashboardData === 'function') {
                loadDashboardData();
            }
        }
    } catch (error) {
        console.error('Error creating income:', error);
        showNotification(window.getTranslation('common.error', 'An error occurred'), 'error');
    }
}

// Initialize income page
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('income-table-body')) {
        loadUserCurrency(); // Load currency first
        loadIncome();
        loadIncomeSources();
        
        // Setup form submit
        const form = document.getElementById('income-form');
        if (form) {
            form.addEventListener('submit', saveIncome);
        }
        
        // Setup frequency change handler
        const frequencySelect = document.getElementById('income-frequency');
        if (frequencySelect) {
            frequencySelect.addEventListener('change', (e) => {
                const customContainer = document.getElementById('custom-frequency-container');
                if (customContainer) {
                    if (e.target.value === 'custom') {
                        customContainer.classList.remove('hidden');
                    } else {
                        customContainer.classList.add('hidden');
                    }
                }
            });
        }
    }
});

// Make functions global
window.openIncomeModal = openIncomeModal;
window.closeIncomeModal = closeIncomeModal;
window.editIncome = editIncome;
window.deleteIncome = deleteIncome;
window.saveIncome = saveIncome;
window.toggleRecurringIncome = toggleRecurringIncome;
window.createIncomeNow = createIncomeNow;
