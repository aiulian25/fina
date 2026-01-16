/**
 * Expense Analyzer JavaScript
 * Handles the "Silly Expense" analyzer functionality
 */

let currentDays = 90;
let summaryData = null;
let currency = 'USD';

// Currency symbols
const currencySymbols = {
    'USD': '$', 'EUR': '€', 'GBP': '£', 'RON': 'lei', 'JPY': '¥',
    'CAD': 'C$', 'AUD': 'A$', 'CHF': 'Fr', 'CNY': '¥', 'INR': '₹'
};

document.addEventListener('DOMContentLoaded', function() {
    initAnalyzer();
});

function initAnalyzer() {
    // Set up days filter
    const daysFilter = document.getElementById('days-filter');
    if (daysFilter) {
        daysFilter.addEventListener('change', function() {
            currentDays = parseInt(this.value);
            loadAllData();
        });
    }
    
    // Set up tab navigation
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            switchTab(this.dataset.tab);
        });
    });
    
    // Load initial data
    loadAllData();
}

function switchTab(tabId) {
    // Update button states with smooth visual feedback
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        btn.style.transform = 'scale(1)';
        btn.style.boxShadow = 'none';
        btn.style.opacity = '0.7';
    });
    const activeBtn = document.querySelector(`[data-tab="${tabId}"]`);
    activeBtn.classList.add('active');
    activeBtn.style.transform = 'scale(1.05)';
    activeBtn.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
    activeBtn.style.opacity = '1';
    
    // Show/hide content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.add('hidden');
    });
    document.getElementById(`tab-${tabId}`).classList.remove('hidden');
    
    // Load tab-specific data if needed
    if (tabId === 'needs-wants' && !document.getElementById('wants-categories-list').querySelector('.category-item')) {
        loadNeedsWants();
    } else if (tabId === 'impulse' && !document.getElementById('impulse-list').querySelector('.impulse-item')) {
        loadImpulsePurchases();
    } else if (tabId === 'projections') {
        loadProjections();
    }
}

async function loadAllData() {
    try {
        // Load summary and insights in parallel
        const [summary, insights, smallPurchases] = await Promise.all([
            fetchAPI('/api/analyzer/summary', { days: currentDays }),
            fetchAPI('/api/analyzer/insights', { days: currentDays }),
            fetchAPI('/api/analyzer/small-purchases', { days: currentDays })
        ]);
        
        summaryData = summary;
        currency = summary.currency || 'USD';
        
        // Update currency symbol
        const symbol = currencySymbols[currency] || currency;
        document.getElementById('currency-symbol').textContent = symbol;
        
        updateScoreCard(summary, insights);
        updateInsights(insights);
        updateSillyExpenses(smallPurchases);
        
        // Update projection amount based on small purchases
        if (smallPurchases.total_small_purchases > 0) {
            const monthlySmall = smallPurchases.total_small_purchases / (currentDays / 30);
            document.getElementById('projection-amount').value = Math.round(monthlySmall);
        }
        
    } catch (error) {
        console.error('Error loading analyzer data:', error);
        showToast(t('analyzer.errorLoading'), 'error');
    }
}

async function fetchAPI(endpoint, params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const url = queryString ? `${endpoint}?${queryString}` : endpoint;
    
    const response = await fetch(url);
    if (!response.ok) throw new Error('API request failed');
    return response.json();
}

function updateScoreCard(summary, insights) {
    // Update score circle
    const score = insights.score || 0;
    const circle = document.getElementById('score-circle');
    const circumference = 226.2; // 2 * PI * 36
    const offset = circumference - (score / 100) * circumference;
    
    setTimeout(() => {
        circle.style.strokeDashoffset = offset;
        
        // Update color based on score
        if (score >= 80) {
            circle.classList.remove('text-amber-500', 'text-red-500');
            circle.classList.add('text-emerald-500');
        } else if (score >= 50) {
            circle.classList.remove('text-emerald-500', 'text-red-500');
            circle.classList.add('text-amber-500');
        } else {
            circle.classList.remove('text-emerald-500', 'text-amber-500');
            circle.classList.add('text-red-500');
        }
    }, 100);
    
    document.getElementById('score-value').textContent = score;
    // Use translation key for score label
    const scoreLabelKey = insights.score_label_key || 'analyzer.score.noData';
    document.getElementById('score-label').textContent = t(scoreLabelKey);
    
    // Update stats
    document.getElementById('total-analyzed').textContent = summary.total_analyzed || 0;
    document.getElementById('wants-percentage').textContent = (summary.wants_percentage || 0) + '%';
    document.getElementById('impulse-count').textContent = summary.impulse_count || 0;
    document.getElementById('potential-savings').textContent = formatCurrency(summary.potential_yearly_savings || 0);
}

function updateInsights(insights) {
    const container = document.getElementById('insights-container');
    
    if (!insights.insights || insights.insights.length === 0) {
        container.innerHTML = `
            <div class="col-span-2 text-center py-8 text-text-muted dark:text-[#92adc9]">
                <span class="material-symbols-outlined text-4xl mb-2 block">insights</span>
                <p data-translate="analyzer.noInsights">${t('analyzer.noInsights')}</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = insights.insights.map(insight => {
        const bgClass = insight.type === 'warning' ? 'bg-amber-500/10 border-amber-500/20' :
                       insight.type === 'success' ? 'bg-emerald-500/10 border-emerald-500/20' :
                       'bg-primary/10 border-primary/20';
        const iconClass = insight.type === 'warning' ? 'text-amber-500' :
                         insight.type === 'success' ? 'text-emerald-500' :
                         'text-primary';
        
        // Translate title, message, and action using keys
        const title = t(insight.title_key);
        let message = t(insight.message_key);
        const action = insight.action_key ? t(insight.action_key) : '';
        
        // Replace placeholders in message
        if (insight.message_params) {
            Object.entries(insight.message_params).forEach(([key, value]) => {
                message = message.replace(`{${key}}`, value);
            });
        }
        
        return `
            <div class="insight-card ${bgClass} border rounded-xl p-4">
                <div class="flex items-start gap-3">
                    <div class="p-2 bg-white/50 dark:bg-card-dark/50 rounded-lg shrink-0">
                        <span class="material-symbols-outlined ${iconClass}">${insight.icon}</span>
                    </div>
                    <div class="flex-1 min-w-0">
                        <h4 class="font-semibold text-text-main dark:text-white text-sm">${title}</h4>
                        <p class="text-xs text-text-muted dark:text-[#92adc9] mt-1">${message}</p>
                        ${action ? `<p class="text-xs text-primary mt-2">💡 ${action}</p>` : ''}
                        ${insight.potential_savings > 0 ? `
                            <p class="text-xs text-emerald-500 mt-1 font-medium">
                                ${t('analyzer.potentialSavings')}: ${formatCurrency(insight.potential_savings)}${t('analyzer.perMonth')}
                            </p>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }).join('');
}

function updateSillyExpenses(data) {
    const container = document.getElementById('silly-expenses-list');
    const totalElement = document.getElementById('silly-total');
    
    totalElement.textContent = formatCurrency(data.total_small_purchases || 0);
    
    if (!data.patterns || data.patterns.length === 0) {
        container.innerHTML = `
            <div class="text-center py-8 text-text-muted dark:text-[#92adc9]">
                <span class="material-symbols-outlined text-4xl mb-2 block text-emerald-500">check_circle</span>
                <p data-translate="analyzer.noSillyExpenses">${t('analyzer.noSillyExpenses')}</p>
                <p class="text-sm mt-1" data-translate="analyzer.greatJob">${t('analyzer.greatJob')}</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = data.patterns.map(pattern => {
        // Use translation key for type display and typical yearly
        const typeDisplay = pattern.type_display_key ? t(pattern.type_display_key) : pattern.type.replace('_', ' ');
        const typicalYearly = pattern.typical_yearly_key ? t(pattern.typical_yearly_key) : '';
        
        return `
        <div class="silly-expense-card bg-gradient-to-r from-amber-500/5 to-transparent border border-amber-500/20 rounded-xl p-4 hover:border-amber-500/40 transition-colors">
            <div class="flex items-start gap-4">
                <div class="p-3 bg-amber-500/10 rounded-xl shrink-0">
                    <span class="material-symbols-outlined text-amber-500 text-2xl">${pattern.icon}</span>
                </div>
                <div class="flex-1 min-w-0">
                    <div class="flex items-center justify-between mb-2">
                        <h4 class="font-semibold text-text-main dark:text-white">${typeDisplay}</h4>
                        <span class="text-lg font-bold text-amber-500">${formatCurrency(pattern.total)}</span>
                    </div>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs text-text-muted dark:text-[#92adc9] mb-3">
                        <div>
                            <span class="font-medium">${pattern.count}</span> ${t('analyzer.purchases')}
                        </div>
                        <div>
                            ${formatCurrency(pattern.average_per_purchase)} ${t('analyzer.avgEach')}
                        </div>
                        <div>
                            ${pattern.frequency_per_week}x/${t('analyzer.week')}
                        </div>
                        <div class="text-amber-500 font-medium">
                            ${formatCurrency(pattern.yearly_projection)}/${t('analyzer.year')}
                        </div>
                    </div>
                    ${typicalYearly ? `<p class="text-xs text-text-muted dark:text-[#92adc9] italic mb-3">${typicalYearly}</p>` : ''}
                    
                    <!-- If invested projections -->
                    <div class="bg-emerald-500/10 rounded-lg p-3 border border-emerald-500/20">
                        <p class="text-xs text-emerald-600 dark:text-emerald-400 font-medium mb-2">
                            💰 ${t('analyzer.ifInvested')}:
                        </p>
                        <div class="flex gap-4 text-xs">
                            <div>
                                <span class="font-bold text-emerald-500">${formatCurrency(pattern.projections['5_years'])}</span>
                                <span class="text-text-muted dark:text-[#92adc9]"> ${t('analyzer.in5Years')}</span>
                            </div>
                            <div>
                                <span class="font-bold text-emerald-500">${formatCurrency(pattern.projections['10_years'])}</span>
                                <span class="text-text-muted dark:text-[#92adc9]"> ${t('analyzer.in10Years')}</span>
                            </div>
                            <div>
                                <span class="font-bold text-emerald-500">${formatCurrency(pattern.projections['20_years'])}</span>
                                <span class="text-text-muted dark:text-[#92adc9]"> ${t('analyzer.in20Years')}</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `}).join('');
}

async function loadNeedsWants() {
    try {
        const data = await fetchAPI('/api/analyzer/needs-wants', { days: currentDays });
        
        // Update totals
        document.getElementById('needs-total').textContent = formatCurrency(data.needs.total);
        document.getElementById('wants-total').textContent = formatCurrency(data.wants.total);
        document.getElementById('needs-percentage').textContent = data.needs.percentage;
        document.getElementById('wants-percentage-bar').textContent = data.wants.percentage;
        
        // Update bars
        document.getElementById('needs-bar').style.width = `${data.needs.percentage}%`;
        document.getElementById('wants-bar').style.width = `${data.wants.percentage}%`;
        
        // Update 50/30/20 rule visualization
        const needsRatio = Math.min(data.needs.percentage / 50, 2) * 50; // Cap at 100%
        const wantsRatio = Math.min(data.wants.percentage / 30, 2) * 50;
        const savingsRatio = Math.min((100 - data.needs.percentage - data.wants.percentage) / 20, 2) * 50;
        
        document.getElementById('rule-needs-bar').style.height = `${needsRatio}%`;
        document.getElementById('rule-wants-bar').style.height = `${wantsRatio}%`;
        document.getElementById('rule-savings-bar').style.height = `${savingsRatio}%`;
        
        // Update wants categories
        const categoriesContainer = document.getElementById('wants-categories-list');
        if (data.wants.by_category && data.wants.by_category.length > 0) {
            const maxTotal = data.wants.by_category[0].total;
            categoriesContainer.innerHTML = data.wants.by_category.slice(0, 5).map(cat => `
                <div class="category-item flex items-center gap-3 p-3 bg-gray-50 dark:bg-[#233648] rounded-lg">
                    <div class="flex-1">
                        <div class="flex justify-between items-center mb-1">
                            <span class="text-sm font-medium text-text-main dark:text-white">${cat.category}</span>
                            <span class="text-sm font-bold text-amber-500">${formatCurrency(cat.total)}</span>
                        </div>
                        <div class="h-2 bg-gray-200 dark:bg-[#1a2b3c] rounded-full overflow-hidden">
                            <div class="h-full bg-amber-500 rounded-full transition-all duration-500" style="width: ${(cat.total / maxTotal) * 100}%"></div>
                        </div>
                    </div>
                </div>
            `).join('');
        } else {
            categoriesContainer.innerHTML = `
                <div class="text-center py-4 text-text-muted dark:text-[#92adc9]">
                    ${t('analyzer.noWantsCategories')}
                </div>
            `;
        }
        
    } catch (error) {
        console.error('Error loading needs/wants data:', error);
    }
}

async function loadImpulsePurchases() {
    try {
        const data = await fetchAPI('/api/analyzer/impulse', { days: currentDays });
        
        // Update stats
        document.getElementById('impulse-total-amount').textContent = formatCurrency(data.impulse_total);
        document.getElementById('impulse-monthly').textContent = formatCurrency(data.monthly_average);
        document.getElementById('impulse-yearly').textContent = formatCurrency(data.yearly_projection);
        
        // Update by day chart
        const dayContainer = document.getElementById('impulse-by-day');
        const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
        const dayData = {};
        
        // Initialize all days
        days.forEach(d => dayData[d] = { count: 0, total: 0 });
        
        // Fill in actual data
        if (data.by_day_of_week) {
            data.by_day_of_week.forEach(d => {
                dayData[d.day] = d;
            });
        }
        
        const maxCount = Math.max(...Object.values(dayData).map(d => d.count), 1);
        
        dayContainer.innerHTML = days.map(day => {
            const d = dayData[day];
            const height = (d.count / maxCount) * 100;
            const isWeekend = day === 'Saturday' || day === 'Sunday';
            const dayKey = `days.${day.toLowerCase()}`;
            const dayLabel = t(dayKey).slice(0, 3);
            
            return `
                <div class="text-center">
                    <div class="h-20 bg-gray-100 dark:bg-[#233648] rounded-lg flex items-end justify-center relative overflow-hidden mb-1">
                        <div class="absolute bottom-0 w-full ${isWeekend ? 'bg-red-500' : 'bg-amber-500'} transition-all duration-500" style="height: ${height}%"></div>
                        <span class="relative z-10 text-xs font-bold ${height > 50 ? 'text-white' : 'text-text-muted dark:text-[#92adc9]'} pb-1">${d.count}</span>
                    </div>
                    <p class="text-xs text-text-muted dark:text-[#92adc9]">${dayLabel}</p>
                </div>
            `;
        }).join('');
        
        // Update purchase list
        const listContainer = document.getElementById('impulse-list');
        if (data.purchases && data.purchases.length > 0) {
            listContainer.innerHTML = data.purchases.slice(0, 20).map(purchase => {
                // Translate day of week and reasons
                const dayOfWeek = purchase.day_of_week_key ? t(purchase.day_of_week_key) : purchase.day_of_week;
                const reasons = purchase.reason_keys ? purchase.reason_keys.map(key => t(key)) : (purchase.reasons || []);
                
                return `
                <div class="impulse-item flex items-center gap-3 p-3 bg-gray-50 dark:bg-[#233648] rounded-lg hover:bg-gray-100 dark:hover:bg-[#2d4a61] transition-colors">
                    <div class="p-2 bg-red-500/10 rounded-lg shrink-0">
                        <span class="material-symbols-outlined text-red-500">bolt</span>
                    </div>
                    <div class="flex-1 min-w-0">
                        <div class="flex justify-between items-start">
                            <div>
                                <p class="text-sm font-medium text-text-main dark:text-white truncate">${purchase.description}</p>
                                <p class="text-xs text-text-muted dark:text-[#92adc9]">${dayOfWeek} • ${formatDate(purchase.date)}</p>
                            </div>
                            <span class="text-sm font-bold text-red-500 shrink-0">${formatCurrency(purchase.amount)}</span>
                        </div>
                        <div class="flex flex-wrap gap-1 mt-1">
                            ${reasons.map(reason => `
                                <span class="text-xs bg-red-500/10 text-red-500 px-2 py-0.5 rounded-full">${reason}</span>
                            `).join('')}
                        </div>
                    </div>
                </div>
            `}).join('');
        } else {
            listContainer.innerHTML = `
                <div class="text-center py-8 text-text-muted dark:text-[#92adc9]">
                    <span class="material-symbols-outlined text-4xl mb-2 block text-emerald-500">thumb_up</span>
                    <p>${t('analyzer.noImpulsePurchases')}</p>
                </div>
            `;
        }
        
    } catch (error) {
        console.error('Error loading impulse data:', error);
    }
}

async function loadProjections() {
    const monthlyAmount = parseFloat(document.getElementById('projection-amount').value) || 100;
    await recalculateProjections(monthlyAmount);
}

async function recalculateProjections(amount) {
    const monthlyAmount = amount || parseFloat(document.getElementById('projection-amount').value) || 100;
    
    try {
        const data = await fetchAPI('/api/analyzer/projections', { 
            days: currentDays,
            monthly_amount: monthlyAmount
        });
        
        // Update projection cards
        data.projections.forEach(proj => {
            const yearKey = proj.years;
            document.getElementById(`proj-${yearKey}yr`).textContent = formatCurrency(proj.future_value);
            document.getElementById(`proj-${yearKey}yr-growth`).textContent = `+${formatCurrency(proj.growth)}`;
        });
        
        // Update chart
        const chartContainer = document.getElementById('projection-chart');
        const maxValue = data.projections[data.projections.length - 1].future_value;
        
        chartContainer.innerHTML = data.projections.map((proj, index) => {
            const height = (proj.future_value / maxValue) * 100;
            const invested = proj.total_invested;
            const growth = proj.growth;
            
            return `
                <div class="flex-1 flex flex-col items-center gap-1">
                    <div class="w-full bg-gray-100 dark:bg-[#233648] rounded-t-lg flex flex-col items-stretch relative" style="height: ${height}%">
                        <div class="absolute bottom-0 w-full bg-primary/50 rounded-t-lg transition-all duration-500" style="height: ${(invested / proj.future_value) * 100}%"></div>
                        <div class="absolute bottom-0 w-full flex flex-col justify-end">
                            <div class="bg-emerald-500 rounded-t-lg transition-all duration-500" style="height: ${(growth / proj.future_value) * 100}%"></div>
                        </div>
                    </div>
                    <div class="text-center">
                        <p class="text-xs font-bold text-text-main dark:text-white">${formatCurrency(proj.future_value, true)}</p>
                    </div>
                </div>
            `;
        }).join('');
        
    } catch (error) {
        console.error('Error loading projections:', error);
    }
}

// Helper functions
function formatCurrency(amount, compact = false) {
    const symbol = currencySymbols[currency] || currency;
    
    if (compact && amount >= 1000) {
        if (amount >= 1000000) {
            return `${symbol}${(amount / 1000000).toFixed(1)}M`;
        }
        return `${symbol}${(amount / 1000).toFixed(1)}K`;
    }
    
    return `${symbol}${amount.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 2 })}`;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

function t(key) {
    // Use the global translate function if available
    if (typeof translate === 'function') {
        return translate(key);
    }
    // Fallback to key
    return key.split('.').pop().replace(/([A-Z])/g, ' $1').trim();
}

function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `fixed bottom-24 left-1/2 -translate-x-1/2 px-4 py-2 rounded-lg text-white text-sm z-50 transition-all duration-300 ${
        type === 'error' ? 'bg-red-500' : type === 'success' ? 'bg-emerald-500' : 'bg-primary'
    }`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => toast.classList.add('opacity-100'), 10);
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.classList.remove('opacity-100');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
