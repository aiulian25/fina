// Dashboard JavaScript

let categoryChart, monthlyChart;

// Load dashboard data
async function loadDashboardData() {
    try {
        const stats = await apiCall('/api/dashboard-stats');
        
        // Update KPI cards
        document.getElementById('total-spent').textContent = formatCurrency(stats.total_spent, stats.currency);
        document.getElementById('active-categories').textContent = stats.active_categories;
        document.getElementById('total-transactions').textContent = stats.total_transactions;
        
        // Update percent change
        const percentChange = document.getElementById('percent-change');
        const isPositive = stats.percent_change >= 0;
        percentChange.className = `${isPositive ? 'bg-red-500/10 text-red-400' : 'bg-green-500/10 text-green-400'} text-xs font-semibold px-2 py-1 rounded-full flex items-center gap-1`;
        percentChange.innerHTML = `
            <span class="material-symbols-outlined text-[14px]">${isPositive ? 'trending_up' : 'trending_down'}</span>
            ${Math.abs(stats.percent_change)}%
        `;
        
        // Load charts
        loadCategoryChart(stats.category_breakdown);
        loadMonthlyChart(stats.monthly_data);
        
        // Load recent transactions
        loadRecentTransactions();
        
    } catch (error) {
        console.error('Failed to load dashboard data:', error);
    }
}

// Category pie chart
function loadCategoryChart(data) {
    const ctx = document.getElementById('category-chart').getContext('2d');
    
    if (categoryChart) {
        categoryChart.destroy();
    }
    
    if (data.length === 0) {
        const isDark = document.documentElement.classList.contains('dark');
        ctx.fillStyle = isDark ? '#92adc9' : '#64748b';
        ctx.font = '14px Inter';
        ctx.textAlign = 'center';
        ctx.fillText('No data available', ctx.canvas.width / 2, ctx.canvas.height / 2);
        return;
    }
    
    categoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: data.map(d => d.name),
            datasets: [{
                data: data.map(d => d.amount),
                backgroundColor: data.map(d => d.color),
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: document.documentElement.classList.contains('dark') ? '#92adc9' : '#64748b',
                        padding: 15,
                        font: { size: 12 }
                    }
                }
            }
        }
    });
}

// Monthly bar chart
function loadMonthlyChart(data) {
    const ctx = document.getElementById('monthly-chart').getContext('2d');
    
    if (monthlyChart) {
        monthlyChart.destroy();
    }
    
    monthlyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.month),
            datasets: [{
                label: 'Spending',
                data: data.map(d => d.total),
                backgroundColor: '#2b8cee',
                borderRadius: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: document.documentElement.classList.contains('dark') ? '#92adc9' : '#64748b' },
                    grid: { color: document.documentElement.classList.contains('dark') ? '#233648' : '#e2e8f0' }
                },
                x: {
                    ticks: { color: document.documentElement.classList.contains('dark') ? '#92adc9' : '#64748b' },
                    grid: { display: false }
                }
            }
        }
    });
}

// Load recent transactions
async function loadRecentTransactions() {
    try {
        const data = await apiCall('/api/recent-transactions?limit=5');
        const container = document.getElementById('recent-transactions');
        
        if (data.transactions.length === 0) {
            container.innerHTML = '<p class="text-[#92adc9] text-sm text-center py-8">No transactions yet</p>';
            return;
        }
        
        container.innerHTML = data.transactions.map(tx => `
            <div class="flex items-center justify-between p-4 rounded-lg bg-slate-50 dark:bg-[#111a22] border border-border-light dark:border-[#233648] hover:border-primary/30 transition-colors">
                <div class="flex items-center gap-3 flex-1">
                    <div class="w-10 h-10 rounded-lg flex items-center justify-center" style="background: ${tx.category_color}20;">
                        <span class="material-symbols-outlined text-[20px]" style="color: ${tx.category_color};">payments</span>
                    </div>
                    <div class="flex-1">
                        <p class="text-text-main dark:text-white font-medium text-sm">${tx.description}</p>
                        <p class="text-text-muted dark:text-[#92adc9] text-xs">${tx.category_name} • ${formatDate(tx.date)}</p>
                    </div>
                </div>
                <div class="text-right">
                    <p class="text-text-main dark:text-white font-semibold">${formatCurrency(tx.amount, tx.currency)}</p>
                    ${tx.tags.length > 0 ? `<p class="text-text-muted dark:text-[#92adc9] text-xs">${tx.tags.join(', ')}</p>` : ''}
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load transactions:', error);
    }
}

// Expense modal
const expenseModal = document.getElementById('expense-modal');
const addExpenseBtn = document.getElementById('add-expense-btn');
const closeModalBtn = document.getElementById('close-modal');
const expenseForm = document.getElementById('expense-form');

// Load categories for dropdown
async function loadCategories() {
    try {
        const data = await apiCall('/api/expenses/categories');
        const select = expenseForm.querySelector('[name="category_id"]');
        
        select.innerHTML = '<option value="">Select category...</option>' +
            data.categories.map(cat => `<option value="${cat.id}">${cat.name}</option>`).join('');
    } catch (error) {
        console.error('Failed to load categories:', error);
    }
}

// Open modal
addExpenseBtn.addEventListener('click', () => {
    expenseModal.classList.remove('hidden');
    loadCategories();
    
    // Set today's date as default
    const dateInput = expenseForm.querySelector('[name="date"]');
    dateInput.value = new Date().toISOString().split('T')[0];
});

// Close modal
closeModalBtn.addEventListener('click', () => {
    expenseModal.classList.add('hidden');
    expenseForm.reset();
});

// Close modal on outside click
expenseModal.addEventListener('click', (e) => {
    if (e.target === expenseModal) {
        expenseModal.classList.add('hidden');
        expenseForm.reset();
    }
});

// Submit expense form
expenseForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData(expenseForm);
    
    // Convert tags to array
    const tagsString = formData.get('tags');
    if (tagsString) {
        const tags = tagsString.split(',').map(t => t.trim()).filter(t => t);
        formData.set('tags', JSON.stringify(tags));
    }
    
    // Convert date to ISO format
    const date = new Date(formData.get('date'));
    formData.set('date', date.toISOString());
    
    try {
        const result = await apiCall('/api/expenses/', {
            method: 'POST',
            body: formData
        });
        
        if (result.success) {
            showToast('Expense added successfully!', 'success');
            expenseModal.classList.add('hidden');
            expenseForm.reset();
            loadDashboardData();
        }
    } catch (error) {
        console.error('Failed to add expense:', error);
    }
});

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
    
    // Refresh data every 5 minutes
    setInterval(loadDashboardData, 5 * 60 * 1000);
});
