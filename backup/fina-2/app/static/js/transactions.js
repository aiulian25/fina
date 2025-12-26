// Transactions page JavaScript

let currentPage = 1;
let filters = {
    category_id: '',
    start_date: '',
    end_date: '',
    search: ''
};

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

// Load transactions
async function loadTransactions() {
    try {
        const params = new URLSearchParams({
            page: currentPage,
            ...filters
        });
        
        const data = await apiCall(`/api/expenses/?${params}`);
        displayTransactions(data.expenses);
        displayPagination(data.pages, data.current_page, data.total || data.expenses.length);
    } catch (error) {
        console.error('Failed to load transactions:', error);
    }
}

// Display transactions
function displayTransactions(transactions) {
    const container = document.getElementById('transactions-list');
    
    if (transactions.length === 0) {
        const noTransactionsText = window.getTranslation ? window.getTranslation('transactions.noTransactions', 'No transactions found') : 'No transactions found';
        container.innerHTML = `
            <tr>
                <td colspan="7" class="p-12 text-center">
                    <span class="material-symbols-outlined text-6xl text-[#92adc9] mb-4 block">receipt_long</span>
                    <p class="text-[#92adc9] text-lg">${noTransactionsText}</p>
                </td>
            </tr>
        `;
        return;
    }
    
    container.innerHTML = transactions.map(tx => {
        const txDate = new Date(tx.date);
        const dateStr = txDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
        const timeStr = txDate.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
        
        // Get category color
        const categoryColors = {
            'Food': { bg: 'bg-green-500/10', text: 'text-green-400', border: 'border-green-500/20', dot: 'bg-green-400' },
            'Transport': { bg: 'bg-orange-500/10', text: 'text-orange-400', border: 'border-orange-500/20', dot: 'bg-orange-400' },
            'Entertainment': { bg: 'bg-purple-500/10', text: 'text-purple-400', border: 'border-purple-500/20', dot: 'bg-purple-400' },
            'Shopping': { bg: 'bg-blue-500/10', text: 'text-blue-400', border: 'border-blue-500/20', dot: 'bg-blue-400' },
            'Healthcare': { bg: 'bg-red-500/10', text: 'text-red-400', border: 'border-red-500/20', dot: 'bg-red-400' },
            'Bills': { bg: 'bg-yellow-500/10', text: 'text-yellow-400', border: 'border-yellow-500/20', dot: 'bg-yellow-400' },
            'Education': { bg: 'bg-pink-500/10', text: 'text-pink-400', border: 'border-pink-500/20', dot: 'bg-pink-400' },
            'Other': { bg: 'bg-gray-500/10', text: 'text-gray-400', border: 'border-gray-500/20', dot: 'bg-gray-400' }
        };
        const catColor = categoryColors[tx.category_name] || categoryColors['Other'];
        
        // Status icon (completed/pending)
        const isCompleted = true; // For now, all are completed
        const statusIcon = isCompleted 
            ? '<span class="material-symbols-outlined text-[16px]">check</span>'
            : '<span class="material-symbols-outlined text-[16px]">schedule</span>';
        const statusClass = isCompleted
            ? 'bg-green-500/20 text-green-400'
            : 'bg-yellow-500/20 text-yellow-400';
        const statusTitle = isCompleted 
            ? (window.getTranslation ? window.getTranslation('transactions.completed', 'Completed') : 'Completed') 
            : (window.getTranslation ? window.getTranslation('transactions.pending', 'Pending') : 'Pending');
        
        return `
        <tr class="group hover:bg-gray-50 dark:hover:bg-white/[0.02] transition-colors relative border-l-2 border-transparent hover:border-primary">
            <td class="p-5">
                <div class="flex items-center gap-3">
                    <div class="size-10 rounded-full flex items-center justify-center shrink-0" style="background: ${tx.category_color}20;">
                        <span class="material-symbols-outlined text-[20px]" style="color: ${tx.category_color};">payments</span>
                    </div>
                    <div class="flex flex-col">
                        <span class="text-text-main dark:text-white font-medium group-hover:text-primary transition-colors">${tx.description}</span>
                        <span class="text-text-muted dark:text-[#92adc9] text-xs">${tx.tags.length > 0 ? tx.tags.join(', ') : (window.getTranslation ? window.getTranslation('transactions.expense', 'Expense') : 'Expense')}</span>
                    </div>
                </div>
            </td>
            <td class="p-5">
                <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${catColor.bg} ${catColor.text} border ${catColor.border}">
                    <span class="size-1.5 rounded-full ${catColor.dot}"></span>
                    ${tx.category_name}
                </span>
            </td>
            <td class="p-5 text-text-muted dark:text-[#92adc9]">
                ${dateStr}
                <span class="block text-xs opacity-60">${timeStr}</span>
            </td>
            <td class="p-5">
                <div class="flex items-center gap-2 text-text-main dark:text-white">
                    <span class="material-symbols-outlined text-text-muted dark:text-[#92adc9] text-[18px]">credit_card</span>
                    <span>•••• ${window.userCurrency || 'RON'}</span>
                </div>
            </td>
            <td class="p-5 text-right">
                <span class="text-text-main dark:text-white font-semibold">${formatCurrency(tx.amount, window.userCurrency || 'RON')}</span>
            </td>
            <td class="p-5 text-center">
                <span class="inline-flex items-center justify-center size-6 rounded-full ${statusClass}" title="${statusTitle}">
                    ${statusIcon}
                </span>
            </td>
            <td class="p-5 text-right">
                <div class="flex items-center justify-end gap-1">
                    ${tx.receipt_path ? `
                    <button onclick="viewReceipt('${tx.receipt_path}')" class="text-text-muted dark:text-[#92adc9] hover:text-text-main dark:hover:text-white p-1 rounded hover:bg-gray-100 dark:hover:bg-white/10 transition-colors" title="${window.getTranslation ? window.getTranslation('transactions.viewReceipt', 'View Receipt') : 'View Receipt'}">
                        <span class="material-symbols-outlined text-[18px]">attach_file</span>
                    </button>
                    ` : ''}
                    <button onclick="editTransaction(${tx.id})" class="text-text-muted dark:text-[#92adc9] hover:text-text-main dark:hover:text-white p-1 rounded hover:bg-gray-100 dark:hover:bg-white/10 transition-colors" title="${window.getTranslation ? window.getTranslation('transactions.edit', 'Edit') : 'Edit'}">
                        <span class="material-symbols-outlined text-[18px]">edit</span>
                    </button>
                    <button onclick="deleteTransaction(${tx.id})" class="text-text-muted dark:text-[#92adc9] hover:text-red-400 p-1 rounded hover:bg-red-100 dark:hover:bg-white/10 transition-colors" title="${window.getTranslation ? window.getTranslation('transactions.delete', 'Delete') : 'Delete'}">
                        <span class="material-symbols-outlined text-[18px]">delete</span>
                    </button>
                </div>
            </td>
        </tr>
        `;
    }).join('');
}

// Display pagination
function displayPagination(totalPages, current, totalItems = 0) {
    const container = document.getElementById('pagination');
    
    // Update pagination info
    const perPage = 10;
    const start = (current - 1) * perPage + 1;
    const end = Math.min(current * perPage, totalItems);
    
    document.getElementById('page-start').textContent = totalItems > 0 ? start : 0;
    document.getElementById('page-end').textContent = end;
    document.getElementById('total-count').textContent = totalItems;
    
    if (totalPages <= 1) {
        container.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Previous button
    const prevDisabled = current <= 1;
    const prevText = window.getTranslation ? window.getTranslation('transactions.previous', 'Previous') : 'Previous';
    const nextText = window.getTranslation ? window.getTranslation('transactions.next', 'Next') : 'Next';
    
    html += `
        <button 
            onclick="changePage(${current - 1})" 
            class="flex items-center gap-1 px-3 py-1.5 bg-background-light dark:bg-[#111a22] border border-border-light dark:border-[#233648] rounded-md text-text-muted dark:text-[#92adc9] hover:text-text-main dark:hover:text-white hover:border-text-muted dark:hover:border-[#92adc9] transition-colors text-sm ${prevDisabled ? 'opacity-50 cursor-not-allowed' : ''}" 
            ${prevDisabled ? 'disabled' : ''}
        >
            <span class="material-symbols-outlined text-[16px]">chevron_left</span>
            ${prevText}
        </button>
    `;
    
    // Next button
    const nextDisabled = current >= totalPages;
    html += `
        <button 
            onclick="changePage(${current + 1})" 
            class="flex items-center gap-1 px-3 py-1.5 bg-background-light dark:bg-[#111a22] border border-border-light dark:border-[#233648] rounded-md text-text-muted dark:text-[#92adc9] hover:text-text-main dark:hover:text-white hover:border-text-muted dark:hover:border-[#92adc9] transition-colors text-sm ${nextDisabled ? 'opacity-50 cursor-not-allowed' : ''}"
            ${nextDisabled ? 'disabled' : ''}
        >
            ${nextText}
            <span class="material-symbols-outlined text-[16px]">chevron_right</span>
        </button>
    `;
    
    container.innerHTML = html;
}

// Change page
function changePage(page) {
    currentPage = page;
    loadTransactions();
}

// Edit transaction
let currentExpenseId = null;
let currentReceiptPath = null;

async function editTransaction(id) {
    try {
        // Fetch expense details
        const data = await apiCall(`/api/expenses/?page=1`);
        const expense = data.expenses.find(e => e.id === id);
        
        if (!expense) {
            showToast(window.getTranslation ? window.getTranslation('transactions.notFound', 'Transaction not found') : 'Transaction not found', 'error');
            return;
        }
        
        // Store current expense data
        currentExpenseId = id;
        currentReceiptPath = expense.receipt_path;
        
        // Update modal title
        const modalTitle = document.getElementById('expense-modal-title');
        modalTitle.textContent = window.getTranslation ? window.getTranslation('modal.edit_expense', 'Edit Expense') : 'Edit Expense';
        
        // Load categories
        await loadCategoriesForModal();
        
        // Populate form fields
        const form = document.getElementById('expense-form');
        form.querySelector('[name="amount"]').value = expense.amount;
        form.querySelector('[name="description"]').value = expense.description;
        form.querySelector('[name="category_id"]').value = expense.category_id;
        
        // Format date for input (YYYY-MM-DD)
        const expenseDate = new Date(expense.date);
        const dateStr = expenseDate.toISOString().split('T')[0];
        form.querySelector('[name="date"]').value = dateStr;
        
        // Populate tags
        if (expense.tags && expense.tags.length > 0) {
            form.querySelector('[name="tags"]').value = expense.tags.join(', ');
        }
        
        // Show current receipt info if exists
        const receiptInfo = document.getElementById('current-receipt-info');
        const viewReceiptBtn = document.getElementById('view-current-receipt');
        if (expense.receipt_path) {
            receiptInfo.classList.remove('hidden');
            viewReceiptBtn.onclick = () => viewReceipt(expense.receipt_path);
        } else {
            receiptInfo.classList.add('hidden');
        }
        
        // Update submit button text
        const submitBtn = document.getElementById('expense-submit-btn');
        submitBtn.textContent = window.getTranslation ? window.getTranslation('actions.update', 'Update Expense') : 'Update Expense';
        
        // Show modal
        document.getElementById('expense-modal').classList.remove('hidden');
        
    } catch (error) {
        console.error('Failed to load transaction for editing:', error);
        showToast(window.getTranslation ? window.getTranslation('common.error', 'An error occurred') : 'An error occurred', 'error');
    }
}

// Make editTransaction global
window.editTransaction = editTransaction;

// Delete transaction
async function deleteTransaction(id) {
    const confirmMsg = window.getTranslation ? window.getTranslation('transactions.deleteConfirm', 'Are you sure you want to delete this transaction?') : 'Are you sure you want to delete this transaction?';
    const successMsg = window.getTranslation ? window.getTranslation('transactions.deleted', 'Transaction deleted') : 'Transaction deleted';
    
    if (!confirm(confirmMsg)) {
        return;
    }
    
    try {
        await apiCall(`/api/expenses/${id}`, { method: 'DELETE' });
        showToast(successMsg, 'success');
        loadTransactions();
    } catch (error) {
        console.error('Failed to delete transaction:', error);
    }
}

// Load categories for filter
async function loadCategoriesFilter() {
    try {
        const data = await apiCall('/api/expenses/categories');
        const select = document.getElementById('filter-category');
        const categoryText = window.getTranslation ? window.getTranslation('transactions.allCategories', 'Category') : 'Category';
        
        select.innerHTML = `<option value="">${categoryText}</option>` +
            data.categories.map(cat => `<option value="${cat.id}">${cat.name}</option>`).join('');
    } catch (error) {
        console.error('Failed to load categories:', error);
    }
}

// Load categories for modal
async function loadCategoriesForModal() {
    try {
        const data = await apiCall('/api/expenses/categories');
        const select = document.querySelector('#expense-form [name="category_id"]');
        const selectText = window.getTranslation ? window.getTranslation('dashboard.selectCategory', 'Select category...') : 'Select category...';
        
        // Map category names to translation keys
        const categoryTranslations = {
            'Food & Dining': 'categories.foodDining',
            'Transportation': 'categories.transportation',
            'Shopping': 'categories.shopping',
            'Entertainment': 'categories.entertainment',
            'Bills & Utilities': 'categories.billsUtilities',
            'Healthcare': 'categories.healthcare',
            'Education': 'categories.education',
            'Other': 'categories.other'
        };
        
        select.innerHTML = `<option value="">${selectText}</option>` +
            data.categories.map(cat => {
                const translationKey = categoryTranslations[cat.name];
                const translatedName = translationKey && window.getTranslation 
                    ? window.getTranslation(translationKey, cat.name) 
                    : cat.name;
                return `<option value="${cat.id}">${translatedName}</option>`;
            }).join('');
    } catch (error) {
        console.error('Failed to load categories:', error);
    }
}

// Toggle advanced filters
function toggleAdvancedFilters() {
    const advFilters = document.getElementById('advanced-filters');
    advFilters.classList.toggle('hidden');
}

// Filter event listeners
document.getElementById('filter-category').addEventListener('change', (e) => {
    filters.category_id = e.target.value;
    currentPage = 1;
    loadTransactions();
});

document.getElementById('filter-start-date').addEventListener('change', (e) => {
    filters.start_date = e.target.value;
    currentPage = 1;
    loadTransactions();
});

document.getElementById('filter-end-date').addEventListener('change', (e) => {
    filters.end_date = e.target.value;
    currentPage = 1;
    loadTransactions();
});

document.getElementById('filter-search').addEventListener('input', (e) => {
    filters.search = e.target.value;
    currentPage = 1;
    loadTransactions();
});

// More filters button
document.getElementById('more-filters-btn').addEventListener('click', toggleAdvancedFilters);

// Date filter button (same as more filters for now)
document.getElementById('date-filter-btn').addEventListener('click', toggleAdvancedFilters);

// Export CSV
document.getElementById('export-csv-btn').addEventListener('click', () => {
    window.location.href = '/api/expenses/export/csv';
});

// Import CSV
document.getElementById('import-csv-btn').addEventListener('click', () => {
    document.getElementById('csv-file-input').click();
});

document.getElementById('csv-file-input').addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const result = await apiCall('/api/expenses/import/csv', {
            method: 'POST',
            body: formData
        });
        
        const importedText = window.getTranslation ? window.getTranslation('transactions.imported', 'Imported') : 'Imported';
        const transactionsText = window.getTranslation ? window.getTranslation('transactions.importSuccess', 'transactions') : 'transactions';
        showToast(`${importedText} ${result.imported} ${transactionsText}`, 'success');
        if (result.errors.length > 0) {
            console.warn('Import errors:', result.errors);
        }
        loadTransactions();
    } catch (error) {
        console.error('Failed to import CSV:', error);
    }
    
    e.target.value = ''; // Reset file input
});

// Receipt Viewer
const receiptModal = document.getElementById('receipt-modal');
const receiptContent = document.getElementById('receipt-content');
const closeReceiptModal = document.getElementById('close-receipt-modal');

function viewReceipt(receiptPath) {
    const fileExt = receiptPath.split('.').pop().toLowerCase();
    
    if (['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(fileExt)) {
        // Display image
        receiptContent.innerHTML = `<img src="${receiptPath}" alt="Receipt" class="max-w-full h-auto rounded-lg shadow-lg">`;
    } else if (fileExt === 'pdf') {
        // Display PDF
        receiptContent.innerHTML = `<iframe src="${receiptPath}" class="w-full h-[600px] rounded-lg shadow-lg"></iframe>`;
    } else {
        // Unsupported format - provide download link
        receiptContent.innerHTML = `
            <div class="text-center">
                <span class="material-symbols-outlined text-6xl text-text-muted dark:text-[#92adc9] mb-4">description</span>
                <p class="text-text-main dark:text-white mb-4">Preview not available</p>
                <a href="${receiptPath}" download class="bg-primary hover:bg-primary/90 text-white px-6 py-3 rounded-lg font-semibold transition-colors inline-block">
                    ${window.getTranslation ? window.getTranslation('transactions.downloadReceipt', 'Download Receipt') : 'Download Receipt'}
                </a>
            </div>
        `;
    }
    
    receiptModal.classList.remove('hidden');
}

closeReceiptModal.addEventListener('click', () => {
    receiptModal.classList.add('hidden');
    receiptContent.innerHTML = '';
});

// Close modal on outside click
receiptModal.addEventListener('click', (e) => {
    if (e.target === receiptModal) {
        receiptModal.classList.add('hidden');
        receiptContent.innerHTML = '';
    }
});

// Expense Modal Event Listeners
const expenseModal = document.getElementById('expense-modal');
const addExpenseBtn = document.getElementById('add-expense-btn');
const closeExpenseModal = document.getElementById('close-expense-modal');
const expenseForm = document.getElementById('expense-form');

// Open modal for adding new expense
addExpenseBtn.addEventListener('click', () => {
    // Reset for add mode
    currentExpenseId = null;
    currentReceiptPath = null;
    expenseForm.reset();
    
    // Update modal title
    const modalTitle = document.getElementById('expense-modal-title');
    modalTitle.textContent = window.getTranslation ? window.getTranslation('modal.add_expense', 'Add Expense') : 'Add Expense';
    
    // Update submit button
    const submitBtn = document.getElementById('expense-submit-btn');
    submitBtn.textContent = window.getTranslation ? window.getTranslation('actions.save', 'Save Expense') : 'Save Expense';
    
    // Hide receipt info
    document.getElementById('current-receipt-info').classList.add('hidden');
    
    // Load categories and set today's date
    loadCategoriesForModal();
    const dateInput = expenseForm.querySelector('[name="date"]');
    dateInput.value = new Date().toISOString().split('T')[0];
    
    // Show modal
    expenseModal.classList.remove('hidden');
});

// Close modal
closeExpenseModal.addEventListener('click', () => {
    expenseModal.classList.add('hidden');
    expenseForm.reset();
    currentExpenseId = null;
    currentReceiptPath = null;
});

// Close modal on outside click
expenseModal.addEventListener('click', (e) => {
    if (e.target === expenseModal) {
        expenseModal.classList.add('hidden');
        expenseForm.reset();
        currentExpenseId = null;
        currentReceiptPath = null;
    }
});

// Submit expense form (handles both add and edit)
expenseForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(expenseForm);
    
    // Convert tags to array
    const tagsString = formData.get('tags');
    if (tagsString) {
        const tags = tagsString.split(',').map(t => t.trim()).filter(t => t);
        formData.set('tags', JSON.stringify(tags));
    } else {
        formData.set('tags', JSON.stringify([]));
    }
    
    // Convert date to ISO format
    const date = new Date(formData.get('date'));
    formData.set('date', date.toISOString());
    
    // If no file selected in edit mode, remove the empty file field
    const receiptFile = formData.get('receipt');
    if (!receiptFile || receiptFile.size === 0) {
        formData.delete('receipt');
    }
    
    try {
        let result;
        if (currentExpenseId) {
            // Edit mode - use PUT
            result = await apiCall(`/api/expenses/${currentExpenseId}`, {
                method: 'PUT',
                body: formData
            });
            const successMsg = window.getTranslation ? window.getTranslation('transactions.updated', 'Transaction updated successfully!') : 'Transaction updated successfully!';
            showToast(successMsg, 'success');
        } else {
            // Add mode - use POST
            result = await apiCall('/api/expenses/', {
                method: 'POST',
                body: formData
            });
            const successMsg = window.getTranslation ? window.getTranslation('dashboard.expenseAdded', 'Expense added successfully!') : 'Expense added successfully!';
            showToast(successMsg, 'success');
        }
        
        if (result.success) {
            expenseModal.classList.add('hidden');
            expenseForm.reset();
            currentExpenseId = null;
            currentReceiptPath = null;
            loadTransactions();
        }
    } catch (error) {
        console.error('Failed to save expense:', error);
        const errorMsg = window.getTranslation ? window.getTranslation('common.error', 'An error occurred') : 'An error occurred';
        showToast(errorMsg, 'error');
    }
});

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    await loadUserCurrency();
    loadTransactions();
    loadCategoriesFilter();
});
