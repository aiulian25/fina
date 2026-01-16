/**
 * Budget Notifications Module
 * Handles PWA push notifications for budget alerts
 */

class BudgetNotifications {
    constructor() {
        this.notificationPermission = 'default';
        this.checkPermission();
    }

    /**
     * Check current notification permission status
     */
    checkPermission() {
        if ('Notification' in window) {
            this.notificationPermission = Notification.permission;
        }
    }

    /**
     * Request notification permission from user
     */
    async requestPermission() {
        if (!('Notification' in window)) {
            console.warn('This browser does not support notifications');
            return false;
        }

        if (this.notificationPermission === 'granted') {
            return true;
        }

        try {
            const permission = await Notification.requestPermission();
            this.notificationPermission = permission;
            
            if (permission === 'granted') {
                // Store permission preference
                localStorage.setItem('budgetNotificationsEnabled', 'true');
                return true;
            }
            return false;
        } catch (error) {
            console.error('Error requesting notification permission:', error);
            return false;
        }
    }

    /**
     * Show a budget alert notification
     */
    async showBudgetAlert(alert) {
        if (this.notificationPermission !== 'granted') {
            return;
        }

        try {
            const icon = '/static/icons/icon-192x192.png';
            const badge = '/static/icons/icon-72x72.png';
            
            let title = '';
            let body = '';
            let tag = `budget-alert-${alert.type}`;

            switch (alert.type) {
                case 'category':
                    title = window.getTranslation('budget.categoryAlert');
                    body = window.getTranslation('budget.categoryAlertMessage')
                        .replace('{category}', alert.category_name)
                        .replace('{percentage}', alert.percentage.toFixed(0));
                    tag = `budget-category-${alert.category_id}`;
                    break;
                
                case 'overall':
                    title = window.getTranslation('budget.overallAlert');
                    body = window.getTranslation('budget.overallAlertMessage')
                        .replace('{percentage}', alert.percentage.toFixed(0));
                    break;
                
                case 'exceeded':
                    title = window.getTranslation('budget.exceededAlert');
                    body = window.getTranslation('budget.exceededAlertMessage')
                        .replace('{category}', alert.category_name);
                    tag = `budget-exceeded-${alert.category_id}`;
                    break;
            }

            const options = {
                body: body,
                icon: icon,
                badge: badge,
                tag: tag, // Prevents duplicate notifications
                renotify: true,
                requireInteraction: alert.level === 'danger' || alert.level === 'exceeded',
                data: {
                    url: alert.type === 'overall' ? '/dashboard' : '/transactions',
                    categoryId: alert.category_id
                }
            };

            // Use service worker for better notification handling
            if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
                navigator.serviceWorker.ready.then(registration => {
                    registration.showNotification(title, options);
                });
            } else {
                // Fallback to regular notification
                const notification = new Notification(title, options);
                
                notification.onclick = function(event) {
                    event.preventDefault();
                    window.focus();
                    if (options.data.url) {
                        window.location.href = options.data.url;
                    }
                    notification.close();
                };
            }
        } catch (error) {
            console.error('Error showing notification:', error);
        }
    }

    /**
     * Show weekly spending summary notification
     */
    async showWeeklySummary(summary) {
        if (this.notificationPermission !== 'granted') {
            return;
        }

        try {
            const icon = '/static/icons/icon-192x192.png';
            const badge = '/static/icons/icon-72x72.png';
            
            const title = window.getTranslation('budget.weeklySummary');
            const spent = window.formatCurrency(summary.current_week_spent);
            const change = summary.percentage_change > 0 ? '+' : '';
            const changeText = `${change}${summary.percentage_change.toFixed(0)}%`;
            
            const body = window.getTranslation('budget.weeklySummaryMessage')
                .replace('{spent}', spent)
                .replace('{change}', changeText)
                .replace('{category}', summary.top_category);

            const options = {
                body: body,
                icon: icon,
                badge: badge,
                tag: 'weekly-summary',
                data: {
                    url: '/reports'
                }
            };

            if ('serviceWorker' in navigator && navigator.serviceWorker.controller) {
                navigator.serviceWorker.ready.then(registration => {
                    registration.showNotification(title, options);
                });
            } else {
                const notification = new Notification(title, options);
                
                notification.onclick = function(event) {
                    event.preventDefault();
                    window.focus();
                    window.location.href = '/reports';
                    notification.close();
                };
            }
        } catch (error) {
            console.error('Error showing weekly summary:', error);
        }
    }

    /**
     * Check if notifications are enabled in settings
     */
    isEnabled() {
        return localStorage.getItem('budgetNotificationsEnabled') === 'true';
    }

    /**
     * Enable/disable budget notifications
     */
    async setEnabled(enabled) {
        if (enabled) {
            const granted = await this.requestPermission();
            if (granted) {
                localStorage.setItem('budgetNotificationsEnabled', 'true');
                // Save to server for persistence
                this.saveToServer(true);
                return true;
            }
            return false;
        } else {
            localStorage.setItem('budgetNotificationsEnabled', 'false');
            // Save to server for persistence
            this.saveToServer(false);
            return true;
        }
    }
    
    /**
     * Save notification preference to server
     */
    async saveToServer(enabled) {
        try {
            await fetch('/api/settings/profile', {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ notifications_enabled: enabled })
            });
        } catch (error) {
            console.debug('Could not save notification preference to server:', error);
        }
    }
}

// Create global instance
window.budgetNotifications = new BudgetNotifications();

/**
 * Check budget status and show alerts if needed
 */
async function checkBudgetAlerts() {
    if (!window.budgetNotifications.isEnabled()) {
        return;
    }

    try {
        const data = await window.apiCall('/api/budget/status', 'GET');
        
        if (data.active_alerts && data.active_alerts.length > 0) {
            // Show only the most severe alert to avoid spam
            const mostSevereAlert = data.active_alerts[0];
            await window.budgetNotifications.showBudgetAlert(mostSevereAlert);
        }
    } catch (error) {
        console.error('Error checking budget alerts:', error);
    }
}

/**
 * Check if it's time to show weekly summary
 * Shows on Monday morning if not shown this week
 */
async function checkWeeklySummary() {
    if (!window.budgetNotifications.isEnabled()) {
        return;
    }

    const lastShown = localStorage.getItem('lastWeeklySummaryShown');
    const now = new Date();
    const dayOfWeek = now.getDay(); // 0 = Sunday, 1 = Monday
    
    // Show on Monday (1) between 9 AM and 11 AM
    if (dayOfWeek === 1 && now.getHours() >= 9 && now.getHours() < 11) {
        const today = now.toDateString();
        
        if (lastShown !== today) {
            try {
                const data = await window.apiCall('/api/budget/weekly-summary', 'GET');
                await window.budgetNotifications.showWeeklySummary(data);
                localStorage.setItem('lastWeeklySummaryShown', today);
            } catch (error) {
                console.error('Error showing weekly summary:', error);
            }
        }
    }
}

// Check budget alerts every 30 minutes
if (window.budgetNotifications.isEnabled()) {
    setInterval(checkBudgetAlerts, 30 * 60 * 1000);
    
    // Check immediately on load
    setTimeout(checkBudgetAlerts, 5000);
}

// Check weekly summary once per hour
setInterval(checkWeeklySummary, 60 * 60 * 1000);
setTimeout(checkWeeklySummary, 10000);
