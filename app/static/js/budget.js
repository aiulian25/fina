/**
 * Budget Alerts Dashboard Module
 * Displays budget warnings, progress bars, and alerts
 */

class BudgetDashboard {
    constructor() {
        this.budgetData = null;
        this.refreshInterval = null;
    }

    /**
     * Initialize budget dashboard
     */
    async init() {
        await this.loadBudgetStatus();
        this.renderBudgetBanner();
        this.attachEventListeners();
        
        // Refresh every 5 minutes
        this.refreshInterval = setInterval(() => {
            this.loadBudgetStatus();
        }, 5 * 60 * 1000);
    }

    /**
     * Load budget status from API
     */
    async loadBudgetStatus() {
        try {
            this.budgetData = await window.apiCall('/api/budget/status', 'GET');
            this.renderBudgetBanner();
            this.updateCategoryBudgets();
        } catch (error) {
            console.error('Error loading budget status:', error);
        }
    }

    /**
     * Render budget alert banner at top of dashboard
     */
    renderBudgetBanner() {
        const existingBanner = document.getElementById('budgetAlertBanner');
        if (existingBanner) {
            existingBanner.remove();
        }

        if (!this.budgetData || !this.budgetData.active_alerts || this.budgetData.active_alerts.length === 0) {
            return;
        }

        const mostSevere = this.budgetData.active_alerts[0];
        const banner = document.createElement('div');
        banner.id = 'budgetAlertBanner';
        banner.className = `mb-6 rounded-lg p-4 ${this.getBannerClass(mostSevere.level)}`;
        
        let message = '';
        let icon = '';
        
        switch (mostSevere.level) {
            case 'warning':
                icon = '<span class="material-symbols-outlined">warning</span>';
                break;
            case 'danger':
            case 'exceeded':
                icon = '<span class="material-symbols-outlined">error</span>';
                break;
        }

        if (mostSevere.type === 'overall') {
            message = window.getTranslation('budget.overallWarning')
                .replace('{percentage}', mostSevere.percentage.toFixed(0))
                .replace('{spent}', window.formatCurrency(mostSevere.spent))
                .replace('{budget}', window.formatCurrency(mostSevere.budget));
        } else if (mostSevere.type === 'category') {
            message = window.getTranslation('budget.categoryWarning')
                .replace('{category}', mostSevere.category_name)
                .replace('{percentage}', mostSevere.percentage.toFixed(0))
                .replace('{spent}', window.formatCurrency(mostSevere.spent))
                .replace('{budget}', window.formatCurrency(mostSevere.budget));
        }

        banner.innerHTML = `
            <div class="flex items-start">
                <div class="flex-shrink-0 text-2xl mr-3">
                    ${icon}
                </div>
                <div class="flex-1">
                    <h3 class="font-semibold mb-1">${window.getTranslation('budget.alert')}</h3>
                    <p class="text-sm">${message}</p>
                    ${this.budgetData.active_alerts.length > 1 ? `
                        <button onclick="budgetDashboard.showAllAlerts()" class="mt-2 text-sm underline">
                            ${window.getTranslation('budget.viewAllAlerts')} (${this.budgetData.active_alerts.length})
                        </button>
                    ` : ''}
                </div>
                <button onclick="budgetDashboard.dismissBanner()" class="flex-shrink-0 ml-3">
                    <span class="material-symbols-outlined">close</span>
                </button>
            </div>
        `;

        // Insert at the top of main content
        const mainContent = document.querySelector('main') || document.querySelector('.container');
        if (mainContent && mainContent.firstChild) {
            mainContent.insertBefore(banner, mainContent.firstChild);
        }
    }

    /**
     * Get banner CSS classes based on alert level
     */
    getBannerClass(level) {
        switch (level) {
            case 'warning':
                return 'bg-yellow-100 text-yellow-800 border border-yellow-300';
            case 'danger':
                return 'bg-orange-100 text-orange-800 border border-orange-300';
            case 'exceeded':
                return 'bg-red-100 text-red-800 border border-red-300';
            default:
                return 'bg-blue-100 text-blue-800 border border-blue-300';
        }
    }

    /**
     * Dismiss budget banner (hide for 1 hour)
     */
    dismissBanner() {
        const banner = document.getElementById('budgetAlertBanner');
        if (banner) {
            banner.remove();
        }
        
        // Store dismissal timestamp
        localStorage.setItem('budgetBannerDismissed', Date.now().toString());
    }

    /**
     * Check if banner should be shown (not dismissed in last hour)
     */
    shouldShowBanner() {
        const dismissed = localStorage.getItem('budgetBannerDismissed');
        if (!dismissed) return true;
        
        const dismissedTime = parseInt(dismissed);
        const oneHour = 60 * 60 * 1000;
        
        return Date.now() - dismissedTime > oneHour;
    }

    /**
     * Show modal with all active alerts
     */
    showAllAlerts() {
        if (!this.budgetData || !this.budgetData.active_alerts) return;

        const modal = document.createElement('div');
        modal.id = 'allAlertsModal';
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
        
        const alertsList = this.budgetData.active_alerts.map(alert => {
            let message = '';
            if (alert.type === 'overall') {
                message = window.getTranslation('budget.overallWarning')
                    .replace('{percentage}', alert.percentage.toFixed(0))
                    .replace('{spent}', window.formatCurrency(alert.spent))
                    .replace('{budget}', window.formatCurrency(alert.budget));
            } else {
                message = window.getTranslation('budget.categoryWarning')
                    .replace('{category}', alert.category_name)
                    .replace('{percentage}', alert.percentage.toFixed(0))
                    .replace('{spent}', window.formatCurrency(alert.spent))
                    .replace('{budget}', window.formatCurrency(alert.budget));
            }

            return `
                <div class="p-3 rounded-lg mb-3 ${this.getBannerClass(alert.level)}">
                    <div class="font-semibold mb-1">${alert.category_name || window.getTranslation('budget.monthlyBudget')}</div>
                    <div class="text-sm">${message}</div>
                    <div class="mt-2">
                        ${this.renderProgressBar(alert.percentage, alert.level)}
                    </div>
                </div>
            `;
        }).join('');

        modal.innerHTML = `
            <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
                <div class="p-6">
                    <div class="flex justify-between items-center mb-4">
                        <h2 class="text-2xl font-bold">${window.getTranslation('budget.activeAlerts')}</h2>
                        <button onclick="document.getElementById('allAlertsModal').remove()" class="text-gray-500 hover:text-gray-700">
                            <span class="material-symbols-outlined">close</span>
                        </button>
                    </div>
                    <div>
                        ${alertsList}
                    </div>
                    <div class="mt-6 flex justify-end">
                        <button onclick="document.getElementById('allAlertsModal').remove()" 
                                class="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300">
                            ${window.getTranslation('common.close')}
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Close on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    /**
     * Render a progress bar for budget percentage
     */
    renderProgressBar(percentage, level) {
        const cappedPercentage = Math.min(percentage, 100);
        let colorClass = 'bg-green-500';
        
        switch (level) {
            case 'warning':
                colorClass = 'bg-yellow-500';
                break;
            case 'danger':
                colorClass = 'bg-orange-500';
                break;
            case 'exceeded':
                colorClass = 'bg-red-500';
                break;
        }

        return `
            <div class="w-full bg-gray-200 rounded-full h-2.5">
                <div class="${colorClass} h-2.5 rounded-full transition-all duration-300" 
                     style="width: ${cappedPercentage}%"></div>
            </div>
            <div class="text-xs mt-1 text-right">${percentage.toFixed(0)}%</div>
        `;
    }

    /**
     * Update category cards with budget information
     */
    updateCategoryBudgets() {
        if (!this.budgetData || !this.budgetData.categories) return;

        this.budgetData.categories.forEach(category => {
            const categoryCard = document.querySelector(`[data-category-id="${category.id}"]`);
            if (!categoryCard) return;

            // Check if budget info already exists
            let budgetInfo = categoryCard.querySelector('.budget-info');
            if (!budgetInfo) {
                budgetInfo = document.createElement('div');
                budgetInfo.className = 'budget-info mt-2';
                categoryCard.appendChild(budgetInfo);
            }

            if (category.budget_status && category.budget_status.budget) {
                const status = category.budget_status;
                budgetInfo.innerHTML = `
                    <div class="text-xs text-gray-600 mb-1">
                        ${window.formatCurrency(status.spent)} / ${window.formatCurrency(status.budget)}
                    </div>
                    ${this.renderProgressBar(status.percentage, status.alert_level)}
                `;
            } else {
                budgetInfo.innerHTML = '';
            }
        });
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Listen for expense changes to refresh budget
        document.addEventListener('expenseCreated', () => {
            this.loadBudgetStatus();
        });
        
        document.addEventListener('expenseUpdated', () => {
            this.loadBudgetStatus();
        });
        
        document.addEventListener('expenseDeleted', () => {
            this.loadBudgetStatus();
        });
    }

    /**
     * Cleanup on destroy
     */
    destroy() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
    }
}

// Create global instance
window.budgetDashboard = new BudgetDashboard();

// Initialize on dashboard page
if (window.location.pathname === '/dashboard' || window.location.pathname === '/') {
    document.addEventListener('DOMContentLoaded', () => {
        window.budgetDashboard.init();
    });
}
