// Dashboard JavaScript

let categoryChart, monthlyChart;

// Load dashboard data
async function loadDashboardData() {
    try {
        const stats = await apiCall('/api/dashboard-stats');
        
        // Store user currency globally for use across functions
        window.userCurrency = stats.currency || 'RON';
        
        // Ensure we have valid data with defaults
        const totalSpent = parseFloat(stats.total_spent || 0);
        const activeCategories = parseInt(stats.active_categories || 0);
        const totalTransactions = parseInt(stats.total_transactions || 0);
        const categoryBreakdown = stats.category_breakdown || [];
        const monthlyData = stats.monthly_data || [];
        
        // Update KPI cards
        document.getElementById('total-spent').textContent = formatCurrency(totalSpent, window.userCurrency);
        document.getElementById('active-categories').textContent = activeCategories;
        document.getElementById('total-transactions').textContent = totalTransactions;
        
        // Update percent change
        const percentChange = document.getElementById('percent-change');
        const percentChangeValue = parseFloat(stats.percent_change || 0);
        const isPositive = percentChangeValue >= 0;
        percentChange.className = `${isPositive ? 'bg-red-500/10 text-red-400' : 'bg-green-500/10 text-green-400'} text-xs font-semibold px-2 py-1 rounded-full flex items-center gap-1`;
        percentChange.innerHTML = `
            <span class="material-symbols-outlined text-[14px]">${isPositive ? 'trending_up' : 'trending_down'}</span>
            ${Math.abs(percentChangeValue).toFixed(1)}%
        `;
        
        // Load charts with validated data
        loadCategoryChart(categoryBreakdown);
        loadMonthlyChart(monthlyData);
        
        // Load category cards
        loadCategoryCards(categoryBreakdown, totalSpent);
        
        // Load recent transactions
        loadRecentTransactions();
        
    } catch (error) {
        console.error('Failed to load dashboard data:', error);
    }
}

// Category pie chart with CSS conic-gradient (beautiful & lightweight)
function loadCategoryChart(data) {
    const pieChart = document.getElementById('pie-chart');
    const pieTotal = document.getElementById('pie-total');
    const pieLegend = document.getElementById('pie-legend');
    
    if (!pieChart || !pieTotal || !pieLegend) return;
    
    if (!data || data.length === 0) {
        pieChart.style.background = 'conic-gradient(#233648 0% 100%)';
        pieTotal.textContent = '0 lei';
        pieLegend.innerHTML = '<p class="col-span-2 text-center text-text-muted dark:text-[#92adc9] text-sm">' + 
            (window.getTranslation ? window.getTranslation('dashboard.noData', 'No data available') : 'No data available') + '</p>';
        return;
    }
    
    // Calculate total and get user currency from API response (stored globally)
    const total = data.reduce((sum, cat) => sum + parseFloat(cat.total || 0), 0);
    const userCurrency = window.userCurrency || 'RON';
    pieTotal.textContent = formatCurrency(total, userCurrency);
    
    // Generate conic gradient segments
    let currentPercent = 0;
    const gradientSegments = data.map(cat => {
        const percent = total > 0 ? (parseFloat(cat.total || 0) / total) * 100 : 0;
        const segment = `${cat.color} ${currentPercent}% ${currentPercent + percent}%`;
        currentPercent += percent;
        return segment;
    });
    
    // Apply gradient with smooth transitions
    pieChart.style.background = `conic-gradient(${gradientSegments.join(', ')})`;
    
    // Generate compact legend for 12-14 categories
    pieLegend.innerHTML = data.map(cat => {
        const percent = total > 0 ? ((parseFloat(cat.total || 0) / total) * 100).toFixed(1) : 0;
        return `
            <div class="flex items-center gap-1.5 group cursor-pointer hover:opacity-80 transition-opacity py-0.5">
                <span class="size-2 rounded-full flex-shrink-0" style="background: ${cat.color};"></span>
                <span class="text-text-muted dark:text-[#92adc9] text-[10px] truncate flex-1 leading-tight">${cat.name}</span>
                <span class="text-text-muted dark:text-[#92adc9] text-[10px] font-medium">${percent}%</span>
            </div>
        `;
    }).join('');
}

// Monthly bar chart - slim & elegant for 12 months PWA design
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
                label: window.getTranslation ? window.getTranslation('dashboard.spending', 'Spending') : 'Spending',
                data: data.map(d => d.total),
                backgroundColor: '#2b8cee',
                borderRadius: 6,
                barPercentage: 0.5,  // Make bars slimmer
                categoryPercentage: 0.7  // Tighter spacing between bars
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: document.documentElement.classList.contains('dark') ? '#1a2632' : '#ffffff',
                    titleColor: document.documentElement.classList.contains('dark') ? '#ffffff' : '#1a2632',
                    bodyColor: document.documentElement.classList.contains('dark') ? '#92adc9' : '#64748b',
                    borderColor: document.documentElement.classList.contains('dark') ? '#233648' : '#e2e8f0',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            const userCurrency = window.userCurrency || 'RON';
                            return formatCurrency(context.parsed.y, userCurrency);
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { 
                        color: document.documentElement.classList.contains('dark') ? '#92adc9' : '#64748b',
                        font: { size: 11 },
                        maxTicksLimit: 6
                    },
                    grid: { 
                        color: document.documentElement.classList.contains('dark') ? '#233648' : '#e2e8f0',
                        drawBorder: false
                    },
                    border: { display: false }
                },
                x: {
                    ticks: { 
                        color: document.documentElement.classList.contains('dark') ? '#92adc9' : '#64748b',
                        font: { size: 10 },
                        autoSkip: false,  // Show all 12 months
                        maxRotation: 0,
                        minRotation: 0
                    },
                    grid: { display: false },
                    border: { display: false }
                }
            },
            layout: {
                padding: {
                    left: 5,
                    right: 5,
                    top: 5,
                    bottom: 0
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
            const noTransText = window.getTranslation ? window.getTranslation('dashboard.noTransactions', 'No transactions yet') : 'No transactions yet';
            container.innerHTML = `<p class="text-[#92adc9] text-sm text-center py-8">${noTransText}</p>`;
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
                    <p class="text-text-main dark:text-white font-semibold">${formatCurrency(tx.amount, window.userCurrency || 'RON')}</p>
                    ${tx.tags.length > 0 ? `<p class="text-text-muted dark:text-[#92adc9] text-xs">${tx.tags.join(', ')}</p>` : ''}
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load transactions:', error);
    }
}

// Format currency helper
function formatCurrency(amount, currency) {
    const symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'RON': 'lei'
    };
    const symbol = symbols[currency] || currency;
    const formattedAmount = parseFloat(amount || 0).toFixed(2);
    
    if (currency === 'RON') {
        return `${formattedAmount} ${symbol}`;
    }
    return `${symbol}${formattedAmount}`;
}

// Load category cards with drag and drop (with NaN prevention)
function loadCategoryCards(categoryBreakdown, totalSpent) {
    const container = document.getElementById('category-cards');
    if (!container) return;
    
    // Validate data
    if (!categoryBreakdown || !Array.isArray(categoryBreakdown) || categoryBreakdown.length === 0) {
        container.innerHTML = '<p class="col-span-3 text-center text-text-muted dark:text-[#92adc9] py-8">' + 
            (window.getTranslation ? window.getTranslation('dashboard.noCategories', 'No categories yet') : 'No categories yet') + '</p>';
        return;
    }

    // Icon mapping
    const categoryIcons = {
        'Food & Dining': 'restaurant',
        'Transportation': 'directions_car',
        'Shopping': 'shopping_cart',
        'Entertainment': 'movie',
        'Bills & Utilities': 'receipt',
        'Healthcare': 'medical_services',
        'Education': 'school',
        'Other': 'category'
    };

    // Ensure totalSpent is a valid number
    const validTotalSpent = parseFloat(totalSpent || 0);

    container.innerHTML = categoryBreakdown.map(cat => {
        const total = parseFloat(cat.total || 0);
        const count = parseInt(cat.count || 0);
        const percentage = validTotalSpent > 0 ? ((total / validTotalSpent) * 100).toFixed(1) : 0;
        const icon = categoryIcons[cat.name] || 'category';
        
        return `
            <div class="category-card bg-white dark:bg-[#0f1921] rounded-xl p-5 border border-border-light dark:border-[#233648] hover:border-primary/30 transition-all hover:shadow-lg cursor-move touch-manipulation" 
                 draggable="true" 
                 data-category-id="${cat.id}">
                <div class="flex items-start justify-between mb-4">
                    <div class="flex items-center gap-3">
                        <div class="w-12 h-12 rounded-xl flex items-center justify-center" style="background: ${cat.color};">
                            <span class="material-symbols-outlined text-white text-[24px]">${icon}</span>
                        </div>
                        <div>
                            <h3 class="font-semibold text-text-main dark:text-white">${cat.name}</h3>
                            <p class="text-xs text-text-muted dark:text-[#92adc9]">${count} ${count === 1 ? (window.getTranslation ? window.getTranslation('transactions.transaction', 'transaction') : 'transaction') : (window.getTranslation ? window.getTranslation('transactions.transactions', 'transactions') : 'transactions')}</p>
                        </div>
                    </div>
                    <span class="text-xs font-medium text-text-muted dark:text-[#92adc9] bg-slate-100 dark:bg-[#111a22] px-2 py-1 rounded-full">${percentage}%</span>
                </div>
                <div class="mb-2">
                    <p class="text-2xl font-bold text-text-main dark:text-white">${formatCurrency(total, window.userCurrency || 'RON')}</p>
                </div>
                <div class="w-full bg-slate-200 dark:bg-[#111a22] rounded-full h-2">
                    <div class="h-2 rounded-full transition-all duration-500" style="width: ${percentage}%; background: ${cat.color};"></div>
                </div>
            </div>
        `;
    }).join('');
    
    // Enable drag and drop on category cards
    enableCategoryCardsDragDrop();
}

// Enable drag and drop for category cards on dashboard
let draggedCard = null;

function enableCategoryCardsDragDrop() {
    const cards = document.querySelectorAll('.category-card');
    
    cards.forEach(card => {
        // Drag start
        card.addEventListener('dragstart', function(e) {
            draggedCard = this;
            this.style.opacity = '0.5';
            e.dataTransfer.effectAllowed = 'move';
            e.dataTransfer.setData('text/html', this.innerHTML);
        });
        
        // Drag over
        card.addEventListener('dragover', function(e) {
            if (e.preventDefault) {
                e.preventDefault();
            }
            e.dataTransfer.dropEffect = 'move';
            
            if (draggedCard !== this) {
                const container = document.getElementById('category-cards');
                const allCards = [...container.querySelectorAll('.category-card')];
                const draggedIndex = allCards.indexOf(draggedCard);
                const targetIndex = allCards.indexOf(this);
                
                if (draggedIndex < targetIndex) {
                    this.parentNode.insertBefore(draggedCard, this.nextSibling);
                } else {
                    this.parentNode.insertBefore(draggedCard, this);
                }
            }
            
            return false;
        });
        
        // Drag enter
        card.addEventListener('dragenter', function(e) {
            if (draggedCard !== this) {
                this.style.borderColor = '#2b8cee';
            }
        });
        
        // Drag leave
        card.addEventListener('dragleave', function(e) {
            this.style.borderColor = '';
        });
        
        // Drop
        card.addEventListener('drop', function(e) {
            if (e.stopPropagation) {
                e.stopPropagation();
            }
            this.style.borderColor = '';
            return false;
        });
        
        // Drag end
        card.addEventListener('dragend', function(e) {
            this.style.opacity = '1';
            
            // Reset all borders
            const allCards = document.querySelectorAll('.category-card');
            allCards.forEach(c => c.style.borderColor = '');
            
            // Save new order
            saveDashboardCategoryOrder();
        });
        
        // Touch support for mobile
        card.addEventListener('touchstart', handleTouchStart, {passive: false});
        card.addEventListener('touchmove', handleTouchMove, {passive: false});
        card.addEventListener('touchend', handleTouchEnd, {passive: false});
    });
}

// Touch event handlers for mobile drag and drop with hold-to-drag
let touchStartPos = null;
let touchedCard = null;
let holdTimer = null;
let isDraggingEnabled = false;
const HOLD_DURATION = 500; // 500ms hold required to start dragging

function handleTouchStart(e) {
    // Don't interfere with scrolling initially
    touchedCard = this;
    touchStartPos = {
        x: e.touches[0].clientX,
        y: e.touches[0].clientY
    };
    isDraggingEnabled = false;
    
    // Start hold timer
    holdTimer = setTimeout(() => {
        // After holding, enable dragging
        isDraggingEnabled = true;
        if (touchedCard) {
            touchedCard.style.opacity = '0.5';
            touchedCard.style.transform = 'scale(1.05)';
            // Haptic feedback if available
            if (navigator.vibrate) {
                navigator.vibrate(50);
            }
        }
    }, HOLD_DURATION);
}

function handleTouchMove(e) {
    if (!touchedCard || !touchStartPos) return;
    
    const touch = e.touches[0];
    const deltaX = Math.abs(touch.clientX - touchStartPos.x);
    const deltaY = Math.abs(touch.clientY - touchStartPos.y);
    
    // If moved too much before hold timer completes, cancel hold
    if (!isDraggingEnabled && (deltaX > 10 || deltaY > 10)) {
        clearTimeout(holdTimer);
        touchedCard = null;
        touchStartPos = null;
        return;
    }
    
    // Only allow dragging if hold timer completed
    if (!isDraggingEnabled) return;
    
    // Prevent scrolling when dragging
    e.preventDefault();
    
    const elementBelow = document.elementFromPoint(touch.clientX, touch.clientY);
    const targetCard = elementBelow?.closest('.category-card');
    
    if (targetCard && targetCard !== touchedCard) {
        const container = document.getElementById('category-cards');
        const allCards = [...container.querySelectorAll('.category-card')];
        const touchedIndex = allCards.indexOf(touchedCard);
        const targetIndex = allCards.indexOf(targetCard);
        
        if (touchedIndex < targetIndex) {
            targetCard.parentNode.insertBefore(touchedCard, targetCard.nextSibling);
        } else {
            targetCard.parentNode.insertBefore(touchedCard, targetCard);
        }
    }
}

function handleTouchEnd(e) {
    // Clear hold timer if touch ended early
    clearTimeout(holdTimer);
    
    if (touchedCard) {
        touchedCard.style.opacity = '1';
        touchedCard.style.transform = '';
        
        // Only save if dragging actually happened
        if (isDraggingEnabled) {
            saveDashboardCategoryOrder();
        }
        
        touchedCard = null;
        touchStartPos = null;
        isDraggingEnabled = false;
    }
}

// Save dashboard category card order
async function saveDashboardCategoryOrder() {
    const cards = document.querySelectorAll('.category-card');
    const reorderedCategories = Array.from(cards).map((card, index) => ({
        id: parseInt(card.dataset.categoryId),
        display_order: index
    }));
    
    try {
        await apiCall('/api/expenses/categories/reorder', {
            method: 'PUT',
            body: JSON.stringify({ categories: reorderedCategories })
        });
        // Silently save - no notification to avoid disrupting UX during drag
    } catch (error) {
        console.error('Failed to save category order:', error);
        showToast(getTranslation('common.error', 'Failed to save order'), 'error');
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
            const successMsg = window.getTranslation ? window.getTranslation('dashboard.expenseAdded', 'Expense added successfully!') : 'Expense added successfully!';
            showToast(successMsg, 'success');
            expenseModal.classList.add('hidden');
            expenseForm.reset();
            loadDashboardData();
        }
    } catch (error) {
        console.error('Failed to add expense:', error);
    }
});

// Category Management Modal
const categoryModal = document.getElementById('category-modal');
const manageCategoriesBtn = document.getElementById('manage-categories-btn');
const closeCategoryModal = document.getElementById('close-category-modal');
const addCategoryForm = document.getElementById('add-category-form');
const categoriesList = document.getElementById('categories-list');

let allCategories = [];
let draggedElement = null;

// Open category modal
manageCategoriesBtn.addEventListener('click', async () => {
    categoryModal.classList.remove('hidden');
    await loadCategoriesManagement();
});

// Close category modal
closeCategoryModal.addEventListener('click', () => {
    categoryModal.classList.add('hidden');
    loadDashboardData(); // Refresh dashboard
});

categoryModal.addEventListener('click', (e) => {
    if (e.target === categoryModal) {
        categoryModal.classList.add('hidden');
        loadDashboardData();
    }
});

// Add new category
addCategoryForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(addCategoryForm);
    const data = {
        name: formData.get('name'),
        color: formData.get('color'),
        icon: formData.get('icon') || 'category'
    };
    
    try {
        const result = await apiCall('/api/expenses/categories', {
            method: 'POST',
            body: JSON.stringify(data)
        });
        
        if (result.success) {
            showToast(getTranslation('categories.created', 'Category created successfully'), 'success');
            addCategoryForm.reset();
            await loadCategoriesManagement();
        }
    } catch (error) {
        console.error('Failed to create category:', error);
        showToast(getTranslation('common.error', 'An error occurred'), 'error');
    }
});

// Load categories for management
async function loadCategoriesManagement() {
    try {
        const data = await apiCall('/api/expenses/categories');
        allCategories = data.categories;
        renderCategoriesList();
    } catch (error) {
        console.error('Failed to load categories:', error);
    }
}

// Render categories list with drag and drop
function renderCategoriesList() {
    categoriesList.innerHTML = allCategories.map((cat, index) => `
        <div class="category-item bg-white dark:bg-card-dark border border-border-light dark:border-[#233648] rounded-lg p-4 flex items-center justify-between hover:border-primary/30 transition-all cursor-move" 
             draggable="true" 
             data-id="${cat.id}"
             data-order="${index}">
            <div class="flex items-center gap-3">
                <span class="material-symbols-outlined text-[24px] drag-handle cursor-move" style="color: ${cat.color};">drag_indicator</span>
                <div class="w-10 h-10 rounded-lg flex items-center justify-center" style="background: ${cat.color};">
                    <span class="material-symbols-outlined text-white text-[20px]">${cat.icon}</span>
                </div>
                <div>
                    <p class="text-text-main dark:text-white font-medium">${cat.name}</p>
                    <p class="text-text-muted dark:text-[#92adc9] text-xs">${cat.color} • ${cat.icon}</p>
                </div>
            </div>
            <div class="flex items-center gap-2">
                <button onclick="deleteCategory(${cat.id})" class="text-red-500 hover:text-red-600 p-2 rounded-lg hover:bg-red-50 dark:hover:bg-red-500/10 transition-colors">
                    <span class="material-symbols-outlined text-[20px]">delete</span>
                </button>
            </div>
        </div>
    `).join('');
    
    // Add drag and drop event listeners
    const items = categoriesList.querySelectorAll('.category-item');
    items.forEach(item => {
        item.addEventListener('dragstart', handleDragStart);
        item.addEventListener('dragover', handleDragOver);
        item.addEventListener('drop', handleDrop);
        item.addEventListener('dragend', handleDragEnd);
    });
}

// Drag and drop handlers
function handleDragStart(e) {
    draggedElement = this;
    this.style.opacity = '0.4';
    e.dataTransfer.effectAllowed = 'move';
}

function handleDragOver(e) {
    if (e.preventDefault) {
        e.preventDefault();
    }
    e.dataTransfer.dropEffect = 'move';
    
    const afterElement = getDragAfterElement(categoriesList, e.clientY);
    if (afterElement == null) {
        categoriesList.appendChild(draggedElement);
    } else {
        categoriesList.insertBefore(draggedElement, afterElement);
    }
    
    return false;
}

function handleDrop(e) {
    if (e.stopPropagation) {
        e.stopPropagation();
    }
    return false;
}

function handleDragEnd(e) {
    this.style.opacity = '1';
    
    // Update order in backend
    const items = categoriesList.querySelectorAll('.category-item');
    const reorderedCategories = Array.from(items).map((item, index) => ({
        id: parseInt(item.dataset.id),
        display_order: index
    }));
    
    saveCategoriesOrder(reorderedCategories);
}

function getDragAfterElement(container, y) {
    const draggableElements = [...container.querySelectorAll('.category-item:not([style*="opacity: 0.4"])')];
    
    return draggableElements.reduce((closest, child) => {
        const box = child.getBoundingClientRect();
        const offset = y - box.top - box.height / 2;
        
        if (offset < 0 && offset > closest.offset) {
            return { offset: offset, element: child };
        } else {
            return closest;
        }
    }, { offset: Number.NEGATIVE_INFINITY }).element;
}

// Save category order
async function saveCategoriesOrder(categories) {
    try {
        await apiCall('/api/expenses/categories/reorder', {
            method: 'PUT',
            body: JSON.stringify({ categories })
        });
        showToast(getTranslation('categories.reordered', 'Categories reordered successfully'), 'success');
    } catch (error) {
        console.error('Failed to reorder categories:', error);
        showToast(getTranslation('common.error', 'An error occurred'), 'error');
    }
}

// Delete category
async function deleteCategory(id) {
    if (!confirm(getTranslation('common.delete', 'Are you sure?'))) {
        return;
    }
    
    try {
        const result = await apiCall(`/api/expenses/categories/${id}`, {
            method: 'DELETE'
        });
        
        if (result.success) {
            showToast(getTranslation('categories.deleted', 'Category deleted successfully'), 'success');
            await loadCategoriesManagement();
        }
    } catch (error) {
        console.error('Failed to delete category:', error);
        if (error.message && error.message.includes('expenses')) {
            showToast(getTranslation('categories.hasExpenses', 'Cannot delete category with expenses'), 'error');
        } else {
            showToast(getTranslation('common.error', 'An error occurred'), 'error');
        }
    }
}

// Make deleteCategory global
window.deleteCategory = deleteCategory;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
    
    // Refresh data every 5 minutes
    setInterval(loadDashboardData, 5 * 60 * 1000);
});
