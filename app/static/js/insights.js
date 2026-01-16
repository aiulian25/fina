// Smart Spending Insights JavaScript
'use strict';

// State
let insightsData = [];
let preferences = {};
let currentTab = 'all';

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    loadData();
});

// Tab Navigation
function initTabs() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            switchTab(tab);
        });
    });
}

function switchTab(tab) {
    currentTab = tab;
    
    // Update tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tab);
    });
    
    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.add('hidden');
    });
    document.getElementById(`tab-${tab}`).classList.remove('hidden');
    
    // Load tab-specific data
    switch(tab) {
        case 'digest':
            loadWeeklyDigest();
            break;
        case 'unusual':
            loadUnusualSpending();
            break;
        case 'categories':
            loadCategoryComparison();
            break;
        case 'leaks':
            loadMoneyLeaks();
            break;
    }
}

// Load All Data
async function loadData() {
    try {
        await Promise.all([
            loadInsights(),
            loadSummary(),
            loadPreferences()
        ]);
    } catch (error) {
        console.error('Error loading data:', error);
    }
}

// Load Insights List
async function loadInsights() {
    try {
        const response = await fetch('/api/insights/list');
        const data = await response.json();
        
        if (data.success) {
            insightsData = data.insights;
            renderInsights();
            updateUnreadCount(data.unread_count);
        }
    } catch (error) {
        console.error('Error loading insights:', error);
        showEmptyState('insights-list', 'error');
    }
}

// Render Insights List
function renderInsights() {
    const container = document.getElementById('insights-list');
    if (!container) return;
    
    if (insightsData.length === 0) {
        showEmptyState('insights-list', 'empty');
        return;
    }
    
    container.innerHTML = insightsData.map(insight => `
        <div class="insight-card ${insight.is_read ? '' : 'unread'} priority-${insight.priority} p-4 hover:bg-gray-50 dark:hover:bg-[#1a2b3c] transition-colors cursor-pointer" onclick="openInsight(${insight.id})">
            <div class="flex items-start gap-3">
                <div class="p-2 rounded-lg ${getInsightIconBg(insight.insight_type)}">
                    <span class="material-symbols-outlined ${getInsightIconColor(insight.insight_type)}">${getInsightIcon(insight.insight_type)}</span>
                </div>
                <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2">
                        <h4 class="font-medium text-text-main dark:text-white truncate">
                            ${translateInsightTitle(insight)}
                        </h4>
                        ${!insight.is_read ? '<span class="w-2 h-2 bg-primary rounded-full pulse-dot"></span>' : ''}
                    </div>
                    <p class="text-sm text-text-muted dark:text-[#92adc9] mt-1 line-clamp-2">
                        ${translateInsightMessage(insight)}
                    </p>
                    <div class="flex items-center gap-3 mt-2">
                        <span class="text-xs text-text-muted dark:text-[#92adc9]">
                            ${formatTimeAgo(insight.created_at)}
                        </span>
                        <span class="text-xs px-2 py-0.5 rounded-full ${getPriorityBadge(insight.priority)}">
                            ${t(`insights.priority.${insight.priority}`)}
                        </span>
                    </div>
                </div>
                <button onclick="event.stopPropagation(); dismissInsight(${insight.id})" class="p-1 text-text-muted hover:text-red-500 transition-colors" title="${t('insights.dismiss')}">
                    <span class="material-symbols-outlined text-lg">close</span>
                </button>
            </div>
        </div>
    `).join('');
}

// Load Summary Stats
async function loadSummary() {
    try {
        const response = await fetch('/api/insights/summary');
        const data = await response.json();
        
        if (data.success) {
            const summary = data.summary || {};
            
            // Update stats - with null checks
            const unreadEl = document.getElementById('unread-count');
            const weeklySpentEl = document.getElementById('weekly-spent');
            const leakCountEl = document.getElementById('leak-count');
            const spikeCountEl = document.getElementById('spike-count');
            
            if (unreadEl) unreadEl.textContent = summary.unread_insights || 0;
            if (weeklySpentEl) weeklySpentEl.textContent = formatCurrency(summary.weekly_spending || 0);
            if (leakCountEl) leakCountEl.textContent = summary.money_leaks_count || 0;
            if (spikeCountEl) spikeCountEl.textContent = summary.category_spikes_count || 0;
            
            // Weekly change
            if (summary.weekly_change_percent !== undefined) {
                const change = summary.weekly_change_percent;
                const changeEl = document.getElementById('weekly-change');
                if (changeEl) {
                    if (change > 0) {
                        changeEl.innerHTML = `<span class="text-red-500">↑ ${change.toFixed(1)}%</span> ${t('insights.vsLastWeek')}`;
                    } else if (change < 0) {
                        changeEl.innerHTML = `<span class="text-emerald-500">↓ ${Math.abs(change).toFixed(1)}%</span> ${t('insights.vsLastWeek')}`;
                    } else {
                        changeEl.innerHTML = `${t('insights.sameAsLastWeek')}`;
                    }
                }
            }
            
            // Money leaks yearly
            if (summary.money_leaks_yearly) {
                const leakYearlyEl = document.getElementById('leak-yearly');
                if (leakYearlyEl) leakYearlyEl.textContent = `${formatCurrency(summary.money_leaks_yearly)} / ${t('insights.year')}`;
            }
            
            // Cash flow
            if (summary.weekly_income !== undefined) {
                const incomeEl = document.getElementById('cashflow-income');
                const expensesEl = document.getElementById('cashflow-expenses');
                const netEl = document.getElementById('cashflow-net');
                
                if (incomeEl) incomeEl.textContent = formatCurrency(summary.weekly_income);
                if (expensesEl) expensesEl.textContent = formatCurrency(summary.weekly_spending || 0);
                
                const net = (summary.weekly_income || 0) - (summary.weekly_spending || 0);
                if (netEl) {
                    netEl.textContent = formatCurrency(net);
                    netEl.className = `text-lg font-bold ${net >= 0 ? 'text-emerald-500' : 'text-red-500'}`;
                }
            }
            
            // Top spending day
            if (summary.top_spending_day) {
                const dayNameEl = document.getElementById('top-day-name');
                const dayAmountEl = document.getElementById('top-day-amount');
                if (dayNameEl) dayNameEl.textContent = summary.top_spending_day.day;
                if (dayAmountEl) dayAmountEl.textContent = formatCurrency(summary.top_spending_day.amount);
            }
        }
    } catch (error) {
        console.error('Error loading summary:', error);
    }
}

// Load Preferences
async function loadPreferences() {
    try {
        const response = await fetch('/api/insights/preferences');
        const data = await response.json();
        
        if (data.success) {
            preferences = data.preferences;
            updatePreferencesUI();
        }
    } catch (error) {
        console.error('Error loading preferences:', error);
    }
}

function updatePreferencesUI() {
    const weeklyDigestEl = document.getElementById('pref-weekly-digest');
    const unusualEl = document.getElementById('pref-unusual');
    const thresholdEl = document.getElementById('pref-unusual-threshold');
    const categoryEl = document.getElementById('pref-category');
    const leaksEl = document.getElementById('pref-leaks');
    const pushEl = document.getElementById('pref-push');
    
    if (weeklyDigestEl) weeklyDigestEl.checked = preferences.weekly_digest_enabled !== false;
    if (unusualEl) unusualEl.checked = preferences.unusual_spending_alerts !== false;
    if (thresholdEl) thresholdEl.value = preferences.unusual_spending_threshold || '1.5';
    if (categoryEl) categoryEl.checked = preferences.category_alerts !== false;
    if (leaksEl) leaksEl.checked = preferences.money_leak_alerts !== false;
    if (pushEl) pushEl.checked = preferences.push_notifications_enabled !== false;
}

// Load Weekly Digest
async function loadWeeklyDigest() {
    const container = document.getElementById('digest-content');
    if (!container) return;
    
    container.innerHTML = `<div class="flex items-center justify-center p-8"><span class="material-symbols-outlined animate-spin text-primary">progress_activity</span></div>`;
    
    try {
        const response = await fetch('/api/insights/weekly-digest');
        const data = await response.json();
        
        if (data.success) {
            const digest = data.digest;
            
            // Update period
            const periodEl = document.getElementById('digest-period');
            if (periodEl) periodEl.textContent = `${formatDate(digest.period_start)} - ${formatDate(digest.period_end)}`;
            
            container.innerHTML = `
                <div class="space-y-6">
                    <!-- Total Spending -->
                    <div class="bg-gray-50 dark:bg-[#1a2b3c] rounded-xl p-4">
                        <div class="flex items-center justify-between mb-3">
                            <span class="text-text-muted dark:text-[#92adc9]" data-translate="insights.totalSpending">Total Spending</span>
                            <span class="text-2xl font-bold text-text-main dark:text-white">${formatCurrency(digest.total_spending)}</span>
                        </div>
                        <div class="flex items-center gap-2 text-sm">
                            ${getChangeIndicator(digest.vs_last_week_percent, t('insights.vsLastWeek'))}
                        </div>
                    </div>
                    
                    <!-- Category Breakdown -->
                    <div>
                        <h4 class="font-medium text-text-main dark:text-white mb-3" data-translate="insights.categoryBreakdown">Category Breakdown</h4>
                        <div class="space-y-3">
                            ${digest.category_breakdown.map(cat => `
                                <div class="flex items-center gap-3">
                                    <span class="w-24 text-sm text-text-muted dark:text-[#92adc9] truncate">${t('categories.' + cat.category.toLowerCase()) || cat.category}</span>
                                    <div class="flex-1 h-3 bg-gray-200 dark:bg-[#233648] rounded-full overflow-hidden">
                                        <div class="h-full bg-primary rounded-full" style="width: ${cat.percentage}%"></div>
                                    </div>
                                    <span class="text-sm font-medium text-text-main dark:text-white w-20 text-right">${formatCurrency(cat.amount)}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    
                    <!-- Transaction Count -->
                    <div class="grid grid-cols-2 gap-4">
                        <div class="bg-gray-50 dark:bg-[#1a2b3c] rounded-lg p-3 text-center">
                            <p class="text-2xl font-bold text-primary">${digest.transaction_count}</p>
                            <p class="text-sm text-text-muted dark:text-[#92adc9]" data-translate="insights.transactions">Transactions</p>
                        </div>
                        <div class="bg-gray-50 dark:bg-[#1a2b3c] rounded-lg p-3 text-center">
                            <p class="text-2xl font-bold text-amber-500">${formatCurrency(digest.average_transaction)}</p>
                            <p class="text-sm text-text-muted dark:text-[#92adc9]" data-translate="insights.avgTransaction">Avg Transaction</p>
                        </div>
                    </div>
                    
                    <!-- Top Merchants -->
                    ${digest.top_merchants && digest.top_merchants.length > 0 ? `
                        <div>
                            <h4 class="font-medium text-text-main dark:text-white mb-3" data-translate="insights.topMerchants">Top Merchants</h4>
                            <div class="space-y-2">
                                ${digest.top_merchants.slice(0, 5).map((m, i) => `
                                    <div class="flex items-center justify-between p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-[#1a2b3c]">
                                        <span class="text-sm text-text-main dark:text-white">${i + 1}. ${m.merchant}</span>
                                        <span class="text-sm font-medium text-text-muted dark:text-[#92adc9]">${formatCurrency(m.amount)}</span>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    ` : ''}
                </div>
            `;
        } else {
            showEmptyState('digest-content', 'empty', t('insights.noDigestData'));
        }
    } catch (error) {
        console.error('Error loading digest:', error);
        showEmptyState('digest-content', 'error');
    }
}

// Load Unusual Spending
async function loadUnusualSpending() {
    const container = document.getElementById('unusual-content');
    container.innerHTML = `<div class="flex items-center justify-center p-8"><span class="material-symbols-outlined animate-spin text-primary">progress_activity</span></div>`;
    
    try {
        const response = await fetch('/api/insights/unusual-spending');
        const data = await response.json();
        
        if (data.success && data.unusual_spending && data.unusual_spending.length > 0) {
            container.innerHTML = `
                <div class="space-y-4">
                    ${data.unusual_spending.map(item => `
                        <div class="border border-amber-500/30 bg-amber-500/5 rounded-xl p-4">
                            <div class="flex items-start justify-between">
                                <div>
                                    <h4 class="font-medium text-text-main dark:text-white">${item.description}</h4>
                                    <p class="text-sm text-text-muted dark:text-[#92adc9] mt-1">
                                        ${t('categories.' + item.category.toLowerCase()) || item.category}
                                    </p>
                                </div>
                                <span class="text-xl font-bold text-amber-500">${formatCurrency(item.amount)}</span>
                            </div>
                            <div class="mt-3 flex items-center gap-4 text-sm">
                                <span class="text-text-muted dark:text-[#92adc9]">${formatDate(item.date)}</span>
                                <span class="text-red-500">
                                    ${item.times_average.toFixed(1)}x ${t('insights.aboveAverage')}
                                </span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            showEmptyState('unusual-content', 'success', t('insights.noUnusualSpending'));
        }
    } catch (error) {
        console.error('Error loading unusual spending:', error);
        showEmptyState('unusual-content', 'error');
    }
}

// Load Category Comparison
async function loadCategoryComparison() {
    const container = document.getElementById('categories-content');
    container.innerHTML = `<div class="flex items-center justify-center p-8"><span class="material-symbols-outlined animate-spin text-primary">progress_activity</span></div>`;
    
    try {
        const response = await fetch('/api/insights/category-comparison');
        const data = await response.json();
        
        if (data.success && data.comparison && data.comparison.length > 0) {
            container.innerHTML = `
                <div class="space-y-4">
                    ${data.comparison.map(cat => `
                        <div class="border border-gray-200 dark:border-[#233648] rounded-xl p-4">
                            <div class="flex items-center justify-between mb-3">
                                <span class="font-medium text-text-main dark:text-white">
                                    ${t('categories.' + cat.category.toLowerCase()) || cat.category}
                                </span>
                                ${getChangeIndicator(cat.change_percent)}
                            </div>
                            <div class="grid grid-cols-2 gap-4">
                                <div>
                                    <p class="text-xs text-text-muted dark:text-[#92adc9] mb-1" data-translate="insights.thisMonth">This Month</p>
                                    <p class="text-lg font-bold text-text-main dark:text-white">${formatCurrency(cat.current_month)}</p>
                                </div>
                                <div>
                                    <p class="text-xs text-text-muted dark:text-[#92adc9] mb-1" data-translate="insights.lastMonth">Last Month</p>
                                    <p class="text-lg font-medium text-text-muted dark:text-[#92adc9]">${formatCurrency(cat.last_month)}</p>
                                </div>
                            </div>
                            <div class="mt-3 h-2 bg-gray-200 dark:bg-[#233648] rounded-full overflow-hidden">
                                <div class="h-full transition-all duration-500 ${cat.change_percent > 0 ? 'bg-red-500' : 'bg-emerald-500'}" 
                                     style="width: ${Math.min(100, (cat.current_month / Math.max(cat.last_month, 1)) * 100)}%"></div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            showEmptyState('categories-content', 'empty', t('insights.noCategoryData'));
        }
    } catch (error) {
        console.error('Error loading category comparison:', error);
        showEmptyState('categories-content', 'error');
    }
}

// Load Money Leaks
async function loadMoneyLeaks() {
    const container = document.getElementById('leaks-content');
    container.innerHTML = `<div class="flex items-center justify-center p-8"><span class="material-symbols-outlined animate-spin text-primary">progress_activity</span></div>`;
    
    try {
        const response = await fetch('/api/insights/money-leaks');
        const data = await response.json();
        
        if (data.success && data.leaks && data.leaks.length > 0) {
            const totalYearly = data.leaks.reduce((sum, leak) => sum + leak.yearly_cost, 0);
            
            container.innerHTML = `
                <div class="space-y-4">
                    <!-- Total Impact -->
                    <div class="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-center">
                        <p class="text-sm text-text-muted dark:text-[#92adc9]" data-translate="insights.yearlyLeakage">Total Yearly Leakage</p>
                        <p class="text-3xl font-bold text-red-500 mt-1">${formatCurrency(totalYearly)}</p>
                    </div>
                    
                    <!-- Leak Items -->
                    ${data.leaks.map(leak => `
                        <div class="border border-gray-200 dark:border-[#233648] rounded-xl p-4">
                            <div class="flex items-start justify-between">
                                <div>
                                    <h4 class="font-medium text-text-main dark:text-white">${leak.description}</h4>
                                    <p class="text-sm text-text-muted dark:text-[#92adc9] mt-1">
                                        ${leak.occurrences}x ${t('insights.occurrences')} • ${t('categories.' + leak.category.toLowerCase()) || leak.category}
                                    </p>
                                </div>
                                <div class="text-right">
                                    <p class="text-lg font-bold text-red-500">${formatCurrency(leak.yearly_cost)}</p>
                                    <p class="text-xs text-text-muted dark:text-[#92adc9]">/ ${t('insights.year')}</p>
                                </div>
                            </div>
                            <div class="mt-3">
                                <div class="flex items-center justify-between text-xs text-text-muted dark:text-[#92adc9] mb-1">
                                    <span>${formatCurrency(leak.amount_per_occurrence)} ${t('insights.each')}</span>
                                    <span>${leak.frequency}</span>
                                </div>
                                <div class="h-2 bg-gray-200 dark:bg-[#233648] rounded-full overflow-hidden">
                                    <div class="leak-progress h-full rounded-full" style="width: ${Math.min(100, (leak.yearly_cost / totalYearly) * 100)}%"></div>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        } else {
            showEmptyState('leaks-content', 'success', t('insights.noLeaksFound'));
        }
    } catch (error) {
        console.error('Error loading money leaks:', error);
        showEmptyState('leaks-content', 'error');
    }
}

// Generate Insights
async function generateInsights() {
    const btn = document.getElementById('generate-btn');
    btn.disabled = true;
    btn.innerHTML = `<span class="material-symbols-outlined animate-spin text-lg">progress_activity</span><span>${t('insights.generating')}</span>`;
    
    try {
        const response = await fetch('/api/insights/generate', { 
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
            }
        });
        const data = await response.json();
        
        if (data.success) {
            showToast(t('insights.generatedSuccess'), 'success');
            await loadData();
        } else {
            showToast(data.error || t('insights.generatedError'), 'error');
        }
    } catch (error) {
        console.error('Error generating insights:', error);
        showToast(t('insights.generatedError'), 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<span class="material-symbols-outlined text-lg">auto_awesome</span><span>${t('insights.generate')}</span>`;
    }
}

// Mark Insight as Read
async function openInsight(id) {
    try {
        await fetch(`/api/insights/${id}/read`, { 
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
            }
        });
        
        // Update UI
        const card = document.querySelector(`.insight-card[onclick*="${id}"]`);
        if (card) {
            card.classList.remove('unread');
            const dot = card.querySelector('.pulse-dot');
            if (dot) dot.remove();
        }
        
        updateUnreadCount(Math.max(0, parseInt(document.getElementById('unread-count').textContent) - 1));
    } catch (error) {
        console.error('Error marking insight read:', error);
    }
}

// Dismiss Insight
async function dismissInsight(id) {
    try {
        const response = await fetch(`/api/insights/${id}/dismiss`, { 
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
            }
        });
        const data = await response.json();
        
        if (data.success) {
            insightsData = insightsData.filter(i => i.id !== id);
            renderInsights();
            showToast(t('insights.dismissed'), 'success');
        }
    } catch (error) {
        console.error('Error dismissing insight:', error);
    }
}

// Mark All Read
async function markAllRead() {
    try {
        const response = await fetch('/api/insights/mark-all-read', { 
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
            }
        });
        const data = await response.json();
        
        if (data.success) {
            insightsData.forEach(i => i.is_read = true);
            renderInsights();
            updateUnreadCount(0);
            showToast(t('insights.allMarkedRead'), 'success');
        }
    } catch (error) {
        console.error('Error marking all read:', error);
    }
}

// Preferences Modal
function openPreferencesModal() {
    document.getElementById('preferences-modal').classList.remove('hidden');
}

function closePreferencesModal() {
    document.getElementById('preferences-modal').classList.add('hidden');
}

async function savePreferences() {
    const newPrefs = {
        weekly_digest_enabled: document.getElementById('pref-weekly-digest').checked,
        unusual_spending_alerts: document.getElementById('pref-unusual').checked,
        unusual_spending_threshold: parseFloat(document.getElementById('pref-unusual-threshold').value),
        category_alerts: document.getElementById('pref-category').checked,
        money_leak_alerts: document.getElementById('pref-leaks').checked,
        push_notifications_enabled: document.getElementById('pref-push').checked
    };
    
    try {
        const response = await fetch('/api/insights/preferences', {
            method: 'PUT',
            headers: { 
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
            },
            body: JSON.stringify(newPrefs)
        });
        const data = await response.json();
        
        if (data.success) {
            preferences = { ...preferences, ...newPrefs };
            closePreferencesModal();
            showToast(t('insights.preferencesSaved'), 'success');
        }
    } catch (error) {
        console.error('Error saving preferences:', error);
        showToast(t('insights.preferencesError'), 'error');
    }
}

// Helper Functions
function updateUnreadCount(count) {
    document.getElementById('unread-count').textContent = count;
}

function translateInsightTitle(insight) {
    if (insight.title_key) {
        return t(insight.title_key, insight.message_params || {});
    }
    return insight.title || '';
}

function translateInsightMessage(insight) {
    if (insight.message_key) {
        return t(insight.message_key, insight.message_params || {});
    }
    return insight.message || '';
}

function getInsightIcon(type) {
    const icons = {
        'weekly_digest': 'summarize',
        'unusual_spending': 'warning',
        'category_spike': 'trending_up',
        'money_leak': 'water_drop',
        'budget_alert': 'account_balance_wallet',
        'savings_tip': 'lightbulb',
        'general': 'insights'
    };
    return icons[type] || 'insights';
}

function getInsightIconColor(type) {
    const colors = {
        'weekly_digest': 'text-primary',
        'unusual_spending': 'text-amber-500',
        'category_spike': 'text-red-500',
        'money_leak': 'text-red-500',
        'budget_alert': 'text-amber-500',
        'savings_tip': 'text-emerald-500',
        'general': 'text-primary'
    };
    return colors[type] || 'text-primary';
}

function getInsightIconBg(type) {
    const bgs = {
        'weekly_digest': 'bg-primary/10',
        'unusual_spending': 'bg-amber-500/10',
        'category_spike': 'bg-red-500/10',
        'money_leak': 'bg-red-500/10',
        'budget_alert': 'bg-amber-500/10',
        'savings_tip': 'bg-emerald-500/10',
        'general': 'bg-primary/10'
    };
    return bgs[type] || 'bg-primary/10';
}

function getPriorityBadge(priority) {
    const badges = {
        'high': 'bg-red-100 text-red-600 dark:bg-red-500/20 dark:text-red-400',
        'medium': 'bg-amber-100 text-amber-600 dark:bg-amber-500/20 dark:text-amber-400',
        'low': 'bg-emerald-100 text-emerald-600 dark:bg-emerald-500/20 dark:text-emerald-400'
    };
    return badges[priority] || badges['low'];
}

function getChangeIndicator(percent, suffix = '') {
    if (percent === undefined || percent === null) return '';
    
    if (percent > 0) {
        return `<span class="text-red-500 flex items-center gap-1">
            <span class="material-symbols-outlined text-sm">arrow_upward</span>
            ${percent.toFixed(1)}% ${suffix}
        </span>`;
    } else if (percent < 0) {
        return `<span class="text-emerald-500 flex items-center gap-1">
            <span class="material-symbols-outlined text-sm">arrow_downward</span>
            ${Math.abs(percent).toFixed(1)}% ${suffix}
        </span>`;
    }
    return `<span class="text-text-muted dark:text-[#92adc9]">${t('insights.noChange')}</span>`;
}

function formatTimeAgo(dateStr) {
    const date = new Date(dateStr);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);
    
    if (diff < 60) return t('insights.justNow');
    if (diff < 3600) return `${Math.floor(diff / 60)} ${t('insights.minutesAgo')}`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} ${t('insights.hoursAgo')}`;
    if (diff < 604800) return `${Math.floor(diff / 86400)} ${t('insights.daysAgo')}`;
    return formatDate(dateStr);
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
}

function formatCurrency(amount) {
    return new Intl.NumberFormat(undefined, {
        style: 'currency',
        currency: window.userCurrency || 'RON',
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
    }).format(amount);
}

function showEmptyState(containerId, type, message) {
    const container = document.getElementById(containerId);
    if (!container) return;
    
    const icons = {
        'empty': 'inbox',
        'success': 'check_circle',
        'error': 'error'
    };
    const colors = {
        'empty': 'text-text-muted dark:text-[#92adc9]',
        'success': 'text-emerald-500',
        'error': 'text-red-500'
    };
    const messages = {
        'empty': t('insights.noData'),
        'success': message || t('insights.allGood'),
        'error': t('insights.loadError')
    };
    
    container.innerHTML = `
        <div class="p-8 text-center">
            <span class="material-symbols-outlined text-5xl ${colors[type] || colors['empty']} mb-3 block">${icons[type] || icons['empty']}</span>
            <p class="${colors[type] || colors['empty']}">${message || messages[type] || messages['empty']}</p>
        </div>
    `;
}

function showToast(message, type = 'info') {
    // Check if toast function exists globally
    if (typeof window.showToast === 'function') {
        window.showToast(message, type);
    } else {
        // Fallback simple toast
        const toast = document.createElement('div');
        toast.className = `fixed bottom-4 right-4 px-4 py-3 rounded-lg shadow-lg z-50 ${
            type === 'success' ? 'bg-emerald-500' : 
            type === 'error' ? 'bg-red-500' : 'bg-primary'
        } text-white`;
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }
}

// Translation helper - fallback if not defined globally
if (typeof t !== 'function') {
    window.t = function(key, params = {}) {
        // Simple fallback - just return the key or last part of it
        let text = key.split('.').pop().replace(/_/g, ' ');
        // Replace params
        Object.keys(params).forEach(k => {
            text = text.replace(`{${k}}`, params[k]);
        });
        return text;
    };
}
