// Transactions page JavaScript

let currentPage = 1;
let filters = {
    category_id: '',
    start_date: '',
    end_date: '',
    search: ''
};

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
        container.innerHTML = `
            <tr>
                <td colspan="7" class="p-12 text-center">
                    <span class="material-symbols-outlined text-6xl text-[#92adc9] mb-4 block">receipt_long</span>
                    <p class="text-[#92adc9] text-lg">No transactions found</p>
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
        const statusTitle = isCompleted ? 'Completed' : 'Pending';
        
        return `
        <tr class="group hover:bg-gray-50 dark:hover:bg-white/[0.02] transition-colors relative border-l-2 border-transparent hover:border-primary">
            <td class="p-5">
                <div class="flex items-center gap-3">
                    <div class="size-10 rounded-full flex items-center justify-center shrink-0" style="background: ${tx.category_color}20;">
                        <span class="material-symbols-outlined text-[20px]" style="color: ${tx.category_color};">payments</span>
                    </div>
                    <div class="flex flex-col">
                        <span class="text-text-main dark:text-white font-medium group-hover:text-primary transition-colors">${tx.description}</span>
                        <span class="text-text-muted dark:text-[#92adc9] text-xs">${tx.tags.length > 0 ? tx.tags.join(', ') : 'Expense'}</span>
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
                    <span>•••• ${tx.currency}</span>
                </div>
            </td>
            <td class="p-5 text-right">
                <span class="text-text-main dark:text-white font-semibold">${formatCurrency(tx.amount, tx.currency)}</span>
            </td>
            <td class="p-5 text-center">
                <span class="inline-flex items-center justify-center size-6 rounded-full ${statusClass}" title="${statusTitle}">
                    ${statusIcon}
                </span>
            </td>
            <td class="p-5 text-right">
                <div class="flex items-center justify-end gap-1">
                    ${tx.receipt_path ? `
                    <button onclick="window.open('${tx.receipt_path}')" class="text-text-muted dark:text-[#92adc9] hover:text-text-main dark:hover:text-white p-1 rounded hover:bg-gray-100 dark:hover:bg-white/10 transition-colors" title="View Receipt">
                        <span class="material-symbols-outlined text-[18px]">attach_file</span>
                    </button>
                    ` : ''}
                    <button onclick="editTransaction(${tx.id})" class="text-text-muted dark:text-[#92adc9] hover:text-text-main dark:hover:text-white p-1 rounded hover:bg-gray-100 dark:hover:bg-white/10 transition-colors" title="Edit">
                        <span class="material-symbols-outlined text-[18px]">edit</span>
                    </button>
                    <button onclick="deleteTransaction(${tx.id})" class="text-text-muted dark:text-[#92adc9] hover:text-red-400 p-1 rounded hover:bg-red-100 dark:hover:bg-white/10 transition-colors" title="Delete">
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
    html += `
        <button 
            onclick="changePage(${current - 1})" 
            class="flex items-center gap-1 px-3 py-1.5 bg-background-light dark:bg-[#111a22] border border-border-light dark:border-[#233648] rounded-md text-text-muted dark:text-[#92adc9] hover:text-text-main dark:hover:text-white hover:border-text-muted dark:hover:border-[#92adc9] transition-colors text-sm ${prevDisabled ? 'opacity-50 cursor-not-allowed' : ''}" 
            ${prevDisabled ? 'disabled' : ''}
        >
            <span class="material-symbols-outlined text-[16px]">chevron_left</span>
            Previous
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
            Next
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

// Delete transaction
async function deleteTransaction(id) {
    if (!confirm('Are you sure you want to delete this transaction?')) {
        return;
    }
    
    try {
        await apiCall(`/api/expenses/${id}`, { method: 'DELETE' });
        showToast('Transaction deleted', 'success');
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
        
        select.innerHTML = '<option value="">Category</option>' +
            data.categories.map(cat => `<option value="${cat.id}">${cat.name}</option>`).join('');
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
        
        showToast(`Imported ${result.imported} transactions`, 'success');
        if (result.errors.length > 0) {
            console.warn('Import errors:', result.errors);
        }
        loadTransactions();
    } catch (error) {
        console.error('Failed to import CSV:', error);
    }
    
    e.target.value = ''; // Reset file input
});

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadTransactions();
    loadCategoriesFilter();
});
