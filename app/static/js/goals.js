/**
 * Savings Goals JavaScript
 * Handles all savings goal operations including CRUD, contributions, and UI updates
 */

// Goal categories with their settings
const goalCategories = {
    vacation: { icon: 'flight_takeoff', color: '#f59e0b' },
    emergency: { icon: 'health_and_safety', color: '#ef4444' },
    car: { icon: 'directions_car', color: '#3b82f6' },
    house: { icon: 'home', color: '#10b981' },
    education: { icon: 'school', color: '#8b5cf6' },
    wedding: { icon: 'favorite', color: '#ec4899' },
    retirement: { icon: 'elderly', color: '#6366f1' },
    gadget: { icon: 'devices', color: '#14b8a6' },
    custom: { icon: 'savings', color: '#2b8cee' }
};

// State
let goals = [];
let currentFilter = 'all';
let selectedCategory = 'custom';
let selectedColor = '#2b8cee';
let editingGoalId = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadGoals();
    initializeCategoryGrid();
    initializeFormHandlers();
});

/**
 * Load all goals from API
 */
async function loadGoals() {
    try {
        const showCompleted = currentFilter === 'completed' || currentFilter === 'all';
        const response = await fetch(`/api/goals/?show_completed=${showCompleted}`);
        const data = await response.json();
        
        if (data.success) {
            goals = data.goals;
            updateSummary(data.summary);
            renderGoals();
        } else {
            showToast(getTranslation('goals.errorLoading', 'Failed to load goals'), 'error');
        }
    } catch (error) {
        console.error('Error loading goals:', error);
        showToast(getTranslation('goals.errorLoading', 'Failed to load goals'), 'error');
    }
}

/**
 * Update summary cards
 */
function updateSummary(summary) {
    document.getElementById('total-saved').textContent = formatCurrency(summary.total_saved);
    document.getElementById('total-target').textContent = formatCurrency(summary.total_target);
    document.getElementById('active-goals-count').textContent = summary.active_goals;
    document.getElementById('completed-goals-count').textContent = summary.completed_goals;
}

/**
 * Render goals based on current filter
 */
function renderGoals() {
    const container = document.getElementById('goals-container');
    const emptyState = document.getElementById('empty-state');
    const suggestionsSection = document.getElementById('suggestions-section');
    
    // Filter goals
    let filteredGoals = goals;
    if (currentFilter === 'active') {
        filteredGoals = goals.filter(g => !g.is_completed);
    } else if (currentFilter === 'completed') {
        filteredGoals = goals.filter(g => g.is_completed);
    }
    
    // Show/hide empty state
    if (filteredGoals.length === 0) {
        container.classList.add('hidden');
        emptyState.classList.remove('hidden');
        suggestionsSection.classList.remove('hidden');
    } else {
        container.classList.remove('hidden');
        emptyState.classList.add('hidden');
        suggestionsSection.classList.add('hidden');
    }
    
    // Render goal cards
    container.innerHTML = filteredGoals.map(goal => createGoalCard(goal)).join('');
}

/**
 * Create a goal card HTML
 */
function createGoalCard(goal) {
    const categoryInfo = goalCategories[goal.category] || goalCategories.custom;
    const progressColor = goal.progress_percentage >= 100 ? '#10b981' : goal.color;
    
    // Format target date and days remaining
    let dateInfo = '';
    if (goal.target_date) {
        const targetDate = new Date(goal.target_date);
        const formattedDate = targetDate.toLocaleDateString(getCurrentLanguage(), { 
            month: 'short', 
            day: 'numeric', 
            year: 'numeric' 
        });
        if (goal.days_remaining !== null) {
            if (goal.days_remaining === 0) {
                dateInfo = `<span class="text-amber-500">${getTranslation('goals.dueToday', 'Due today')}</span>`;
            } else if (goal.days_remaining < 0) {
                dateInfo = `<span class="text-red-500">${getTranslation('goals.overdue', 'Overdue')}</span>`;
            } else {
                dateInfo = `<span class="text-text-muted dark:text-[#92adc9]">${goal.days_remaining} ${getTranslation('goals.daysLeft', 'days left')}</span>`;
            }
        }
    }
    
    // Monthly target suggestion
    let monthlyTarget = '';
    if (goal.monthly_target && !goal.is_completed) {
        monthlyTarget = `
            <div class="text-xs text-text-muted dark:text-[#92adc9] mt-2">
                <span class="material-symbols-outlined text-[14px] align-middle">tips_and_updates</span>
                ${getTranslation('goals.saveMonthly', 'Save')} <strong>${formatCurrency(goal.monthly_target)}</strong> ${getTranslation('goals.perMonth', '/month to reach goal')}
            </div>
        `;
    }
    
    // Completed badge
    const completedBadge = goal.is_completed ? `
        <div class="absolute top-3 right-3 flex items-center gap-1 bg-emerald-100 dark:bg-emerald-900/30 text-emerald-600 dark:text-emerald-400 px-2 py-1 rounded-full text-xs font-medium">
            <span class="material-symbols-outlined text-[14px]">check_circle</span>
            ${getTranslation('goals.completed', 'Completed')}
        </div>
    ` : '';
    
    // Milestone indicator
    let milestoneIndicator = '';
    if (goal.milestone >= 25 && goal.milestone < 100 && !goal.is_completed) {
        milestoneIndicator = `
            <div class="flex items-center gap-1 text-amber-500 text-xs mt-2">
                <span class="material-symbols-outlined text-[14px]">star</span>
                ${goal.milestone}% ${getTranslation('goals.milestoneReached', 'milestone reached!')}
            </div>
        `;
    }
    
    return `
        <div class="goal-card bg-white dark:bg-card-dark rounded-2xl border border-border-light dark:border-[#233648] overflow-hidden shadow-sm hover:shadow-md transition-shadow relative ${goal.is_completed ? 'opacity-80' : ''}">
            ${completedBadge}
            
            <!-- Header -->
            <div class="p-5 border-b border-border-light dark:border-[#233648]">
                <div class="flex items-start gap-3">
                    <div class="p-3 rounded-xl" style="background-color: ${goal.color}20;">
                        <span class="material-symbols-outlined text-[24px]" style="color: ${goal.color};">${goal.icon}</span>
                    </div>
                    <div class="flex-1 min-w-0">
                        <h3 class="font-bold text-text-main dark:text-white truncate">${escapeHtml(goal.name)}</h3>
                        ${goal.description ? `<p class="text-xs text-text-muted dark:text-[#92adc9] truncate mt-1">${escapeHtml(goal.description)}</p>` : ''}
                    </div>
                </div>
            </div>
            
            <!-- Progress Section -->
            <div class="p-5">
                <!-- Amount Progress -->
                <div class="flex justify-between items-end mb-2">
                    <div>
                        <span class="text-2xl font-bold text-text-main dark:text-white">${formatCurrency(goal.current_amount)}</span>
                        <span class="text-sm text-text-muted dark:text-[#92adc9]"> / ${formatCurrency(goal.target_amount)}</span>
                    </div>
                    <span class="text-lg font-bold" style="color: ${progressColor};">${goal.progress_percentage}%</span>
                </div>
                
                <!-- Progress Bar -->
                <div class="relative h-3 bg-slate-100 dark:bg-[#233648] rounded-full overflow-hidden">
                    <div class="absolute left-0 top-0 h-full rounded-full transition-all duration-500 ease-out" 
                         style="width: ${Math.min(goal.progress_percentage, 100)}%; background-color: ${progressColor};">
                    </div>
                    <!-- Milestone markers -->
                    <div class="absolute left-1/4 top-0 w-0.5 h-full bg-white/30"></div>
                    <div class="absolute left-1/2 top-0 w-0.5 h-full bg-white/30"></div>
                    <div class="absolute left-3/4 top-0 w-0.5 h-full bg-white/30"></div>
                </div>
                
                <!-- Info Row -->
                <div class="flex justify-between items-center mt-3">
                    <div class="text-xs text-text-muted dark:text-[#92adc9]">
                        ${goal.remaining_amount > 0 ? `${formatCurrency(goal.remaining_amount)} ${getTranslation('goals.remaining', 'remaining')}` : getTranslation('goals.goalReached', 'Goal reached! 🎉')}
                    </div>
                    ${dateInfo}
                </div>
                
                ${monthlyTarget}
                ${milestoneIndicator}
            </div>
            
            <!-- Actions -->
            <div class="px-5 pb-5 flex gap-2">
                ${!goal.is_completed ? `
                    <button onclick="openContributeModal(${goal.id})" class="flex-1 flex items-center justify-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2.5 rounded-xl font-medium transition-all text-sm">
                        <span class="material-symbols-outlined text-[18px]">add</span>
                        ${getTranslation('goals.addMoney', 'Add Money')}
                    </button>
                ` : ''}
                <button onclick="openGoalDetail(${goal.id})" class="flex items-center justify-center gap-1 px-4 py-2.5 bg-slate-100 dark:bg-[#233648] hover:bg-slate-200 dark:hover:bg-[#2d4559] text-text-main dark:text-white rounded-xl font-medium transition-all text-sm">
                    <span class="material-symbols-outlined text-[18px]">visibility</span>
                </button>
                <div class="relative group">
                    <button class="flex items-center justify-center px-3 py-2.5 bg-slate-100 dark:bg-[#233648] hover:bg-slate-200 dark:hover:bg-[#2d4559] text-text-main dark:text-white rounded-xl transition-all">
                        <span class="material-symbols-outlined text-[18px]">more_vert</span>
                    </button>
                    <div class="absolute right-0 top-full mt-1 w-40 bg-white dark:bg-card-dark rounded-lg shadow-lg border border-border-light dark:border-[#233648] hidden group-hover:block z-10">
                        <button onclick="editGoal(${goal.id})" class="w-full flex items-center gap-2 px-4 py-2 text-sm text-text-main dark:text-white hover:bg-slate-50 dark:hover:bg-[#233648] transition-colors">
                            <span class="material-symbols-outlined text-[18px]">edit</span>
                            ${getTranslation('common.edit', 'Edit')}
                        </button>
                        <button onclick="deleteGoal(${goal.id})" class="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors">
                            <span class="material-symbols-outlined text-[18px]">delete</span>
                            ${getTranslation('common.delete', 'Delete')}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Initialize category selection grid
 */
function initializeCategoryGrid() {
    const grid = document.getElementById('category-grid');
    if (!grid) return;
    
    let html = '';
    for (const [key, value] of Object.entries(goalCategories)) {
        html += `
            <button type="button" onclick="selectCategory('${key}')" 
                    class="category-btn flex flex-col items-center gap-1 p-3 rounded-lg border-2 transition-all ${key === 'custom' ? 'border-primary bg-primary/10' : 'border-transparent bg-slate-50 dark:bg-[#233648] hover:border-primary/50'}"
                    data-category="${key}">
                <span class="material-symbols-outlined text-[24px]" style="color: ${value.color};">${value.icon}</span>
                <span class="text-xs text-text-main dark:text-white font-medium">${getTranslation('goals.category.' + key, key)}</span>
            </button>
        `;
    }
    grid.innerHTML = html;
}

/**
 * Select a category
 */
function selectCategory(category) {
    selectedCategory = category;
    document.getElementById('goal-category').value = category;
    
    // Update category buttons
    document.querySelectorAll('.category-btn').forEach(btn => {
        if (btn.dataset.category === category) {
            btn.classList.remove('border-transparent', 'bg-slate-50', 'dark:bg-[#233648]');
            btn.classList.add('border-primary', 'bg-primary/10');
        } else {
            btn.classList.add('border-transparent', 'bg-slate-50', 'dark:bg-[#233648]');
            btn.classList.remove('border-primary', 'bg-primary/10');
        }
    });
    
    // Update color based on category
    const categoryInfo = goalCategories[category];
    if (categoryInfo) {
        selectColor(categoryInfo.color);
    }
}

/**
 * Select a color
 */
function selectColor(color) {
    selectedColor = color;
    document.getElementById('goal-color').value = color;
    
    // Update color buttons
    document.querySelectorAll('.color-btn').forEach(btn => {
        if (btn.dataset.color === color) {
            btn.classList.add('ring-2', 'ring-offset-2', 'ring-primary');
        } else {
            btn.classList.remove('ring-2', 'ring-offset-2', 'ring-primary');
        }
    });
}

/**
 * Initialize form handlers
 */
function initializeFormHandlers() {
    // Goal form submission
    const goalForm = document.getElementById('goal-form');
    if (goalForm) {
        goalForm.addEventListener('submit', handleGoalSubmit);
    }
    
    // Contribute form submission
    const contributeForm = document.getElementById('contribute-form');
    if (contributeForm) {
        contributeForm.addEventListener('submit', handleContributeSubmit);
    }
}

/**
 * Handle goal form submission
 */
async function handleGoalSubmit(e) {
    e.preventDefault();
    
    const goalId = document.getElementById('goal-id').value;
    const name = document.getElementById('goal-name').value.trim();
    const targetAmount = parseFloat(document.getElementById('goal-target').value);
    const currentAmount = parseFloat(document.getElementById('goal-current').value) || 0;
    const targetDate = document.getElementById('goal-date').value || null;
    const description = document.getElementById('goal-description').value.trim();
    const category = document.getElementById('goal-category').value;
    const color = document.getElementById('goal-color').value;
    const categoryInfo = goalCategories[category] || goalCategories.custom;
    
    if (!name || !targetAmount) {
        showToast(getTranslation('common.missingFields', 'Missing required fields'), 'error');
        return;
    }
    
    const goalData = {
        name,
        target_amount: targetAmount,
        current_amount: currentAmount,
        target_date: targetDate,
        description,
        category,
        color,
        icon: categoryInfo.icon
    };
    
    try {
        let response;
        if (goalId) {
            // Update existing goal
            response = await fetch(`/api/goals/${goalId}`, {
                method: 'PUT',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
                },
                body: JSON.stringify(goalData)
            });
        } else {
            // Create new goal
            response = await fetch('/api/goals/', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
                },
                body: JSON.stringify(goalData)
            });
        }
        
        const data = await response.json();
        
        if (data.success) {
            showToast(goalId ? getTranslation('goals.updated', 'Goal updated successfully') : getTranslation('goals.created', 'Goal created successfully'), 'success');
            closeGoalModal();
            loadGoals();
        } else {
            showToast(data.message || getTranslation('goals.error', 'Failed to save goal'), 'error');
        }
    } catch (error) {
        console.error('Error saving goal:', error);
        showToast(getTranslation('goals.error', 'Failed to save goal'), 'error');
    }
}

/**
 * Handle contribution form submission
 */
async function handleContributeSubmit(e) {
    e.preventDefault();
    
    const goalId = document.getElementById('contribute-goal-id').value;
    const amount = parseFloat(document.getElementById('contribute-amount').value);
    const note = document.getElementById('contribute-note').value.trim();
    
    if (!goalId || !amount || amount <= 0) {
        showToast(getTranslation('common.missingFields', 'Missing required fields'), 'error');
        return;
    }
    
    try {
        const response = await fetch(`/api/goals/${goalId}/contribute`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
            },
            body: JSON.stringify({ amount, note })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(getTranslation('goals.contributionAdded', 'Money added successfully! 💰'), 'success');
            closeContributeModal();
            
            // Check for milestone
            if (data.milestone_reached) {
                showMilestoneModal(data.goal, data.milestone_reached);
            }
            
            loadGoals();
        } else {
            showToast(data.message || getTranslation('goals.contributionError', 'Failed to add money'), 'error');
        }
    } catch (error) {
        console.error('Error adding contribution:', error);
        showToast(getTranslation('goals.contributionError', 'Failed to add money'), 'error');
    }
}

/**
 * Filter goals
 */
function filterGoals(filter) {
    currentFilter = filter;
    
    // Update filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
        if (btn.id === `filter-${filter}`) {
            btn.classList.remove('bg-slate-100', 'dark:bg-[#233648]', 'text-text-muted', 'dark:text-[#92adc9]');
            btn.classList.add('bg-primary', 'text-white');
        } else {
            btn.classList.add('bg-slate-100', 'dark:bg-[#233648]', 'text-text-muted', 'dark:text-[#92adc9]');
            btn.classList.remove('bg-primary', 'text-white');
        }
    });
    
    loadGoals();
}

/**
 * Open goal modal
 */
function openGoalModal() {
    editingGoalId = null;
    document.getElementById('goal-id').value = '';
    document.getElementById('goal-form').reset();
    document.getElementById('goal-modal-title').textContent = getTranslation('goals.addGoal', 'Add Savings Goal');
    
    // Reset category and color
    selectCategory('custom');
    selectColor('#2b8cee');
    
    // Set minimum date to today
    const dateInput = document.getElementById('goal-date');
    if (dateInput) {
        dateInput.min = new Date().toISOString().split('T')[0];
    }
    
    document.getElementById('goal-modal').classList.remove('hidden');
}

/**
 * Open goal modal with a specific category
 */
function openGoalModalWithCategory(category) {
    openGoalModal();
    selectCategory(category);
    
    // Set suggested name based on category
    const categoryNames = {
        vacation: getTranslation('goals.vacationName', 'Dream Vacation'),
        emergency: getTranslation('goals.emergencyName', 'Emergency Fund'),
        car: getTranslation('goals.carName', 'New Car'),
        house: getTranslation('goals.houseName', 'Home Down Payment'),
        education: getTranslation('goals.educationName', 'Education Fund'),
        wedding: getTranslation('goals.weddingName', 'Wedding Fund'),
        retirement: getTranslation('goals.retirementName', 'Retirement Savings'),
        gadget: getTranslation('goals.gadgetName', 'New Gadget')
    };
    
    if (categoryNames[category]) {
        document.getElementById('goal-name').value = categoryNames[category];
    }
}

/**
 * Close goal modal
 */
function closeGoalModal() {
    document.getElementById('goal-modal').classList.add('hidden');
    editingGoalId = null;
}

/**
 * Edit a goal
 */
function editGoal(goalId) {
    const goal = goals.find(g => g.id === goalId);
    if (!goal) return;
    
    editingGoalId = goalId;
    document.getElementById('goal-id').value = goalId;
    document.getElementById('goal-name').value = goal.name;
    document.getElementById('goal-target').value = goal.target_amount;
    document.getElementById('goal-current').value = goal.current_amount;
    document.getElementById('goal-date').value = goal.target_date ? goal.target_date.split('T')[0] : '';
    document.getElementById('goal-description').value = goal.description || '';
    document.getElementById('goal-modal-title').textContent = getTranslation('goals.editGoal', 'Edit Savings Goal');
    
    selectCategory(goal.category);
    selectColor(goal.color);
    
    document.getElementById('goal-modal').classList.remove('hidden');
}

/**
 * Delete a goal
 */
async function deleteGoal(goalId) {
    if (!confirm(getTranslation('goals.deleteConfirm', 'Are you sure you want to delete this goal?'))) {
        return;
    }
    
    try {
        const response = await fetch(`/api/goals/${goalId}`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(getTranslation('goals.deleted', 'Goal deleted successfully'), 'success');
            loadGoals();
        } else {
            showToast(data.message || getTranslation('goals.deleteError', 'Failed to delete goal'), 'error');
        }
    } catch (error) {
        console.error('Error deleting goal:', error);
        showToast(getTranslation('goals.deleteError', 'Failed to delete goal'), 'error');
    }
}

/**
 * Open contribute modal
 */
function openContributeModal(goalId) {
    const goal = goals.find(g => g.id === goalId);
    if (!goal) return;
    
    document.getElementById('contribute-goal-id').value = goalId;
    document.getElementById('contribute-goal-name').textContent = goal.name;
    document.getElementById('contribute-amount').value = '';
    document.getElementById('contribute-note').value = '';
    
    document.getElementById('contribute-modal').classList.remove('hidden');
}

/**
 * Close contribute modal
 */
function closeContributeModal() {
    document.getElementById('contribute-modal').classList.add('hidden');
}

/**
 * Set contribution amount from quick add buttons
 */
function setContributeAmount(amount) {
    const input = document.getElementById('contribute-amount');
    const currentValue = parseFloat(input.value) || 0;
    input.value = currentValue + amount;
}

/**
 * Show milestone celebration modal
 */
function showMilestoneModal(goal, milestone) {
    const modal = document.getElementById('milestone-modal');
    const title = document.getElementById('milestone-title');
    const message = document.getElementById('milestone-message');
    
    if (milestone === 100) {
        title.textContent = '🎉 ' + getTranslation('goals.goalCompleted', 'Goal Completed!');
        message.textContent = getTranslation('goals.goalCompletedMessage', `Congratulations! You've reached your "${goal.name}" goal!`).replace('{goal}', goal.name);
    } else {
        title.textContent = '🎉 ' + getTranslation('goals.milestoneReached', 'Milestone Reached!');
        message.textContent = getTranslation('goals.milestoneMessage', `You've reached ${milestone}% of your "${goal.name}" goal!`).replace('{percentage}', milestone).replace('{goal}', goal.name);
    }
    
    modal.classList.remove('hidden');
    
    // Auto-close after 5 seconds
    setTimeout(() => {
        if (!modal.classList.contains('hidden')) {
            closeMilestoneModal();
        }
    }, 5000);
}

/**
 * Close milestone modal
 */
function closeMilestoneModal() {
    document.getElementById('milestone-modal').classList.add('hidden');
}

/**
 * Open goal detail view
 */
async function openGoalDetail(goalId) {
    // For now, just edit - can expand to full detail view later
    editGoal(goalId);
}

/**
 * Format currency
 */
function formatCurrency(amount) {
    const currency = window.userCurrency || 'USD';
    const locale = getCurrentLanguage() === 'ro' ? 'ro-RO' : 'en-US';
    
    return new Intl.NumberFormat(locale, {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    }).format(amount);
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `flex items-center gap-3 px-4 py-3 rounded-xl shadow-lg transform transition-all duration-300 translate-x-full ${
        type === 'success' ? 'bg-emerald-500 text-white' :
        type === 'error' ? 'bg-red-500 text-white' :
        'bg-blue-500 text-white'
    }`;
    
    const icon = type === 'success' ? 'check_circle' : type === 'error' ? 'error' : 'info';
    toast.innerHTML = `
        <span class="material-symbols-outlined">${icon}</span>
        <span>${message}</span>
    `;
    
    container.appendChild(toast);
    
    // Animate in
    requestAnimationFrame(() => {
        toast.classList.remove('translate-x-full');
    });
    
    // Remove after delay
    setTimeout(() => {
        toast.classList.add('translate-x-full', 'opacity-0');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
