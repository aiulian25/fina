/**
 * Spending Forecast JavaScript
 * Handles predictions, cash flow, and bill calendar
 */

// State
let currentCalendarMonth = new Date();
let calendarData = null;
let forecastData = null;

// Helper function for translations
function tr(key, fallback = '') {
    return window.getTranslation ? window.getTranslation(key, fallback) : fallback;
}

// Format currency
function formatCurrency(amount) {
    const currency = window.userCurrency || 'RON';
    const locale = window.userLocale || 'en-GB';
    return new Intl.NumberFormat(locale, {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2
    }).format(amount);
}

// Format date
function formatDate(dateStr) {
    const date = new Date(dateStr);
    const locale = window.userLocale || 'en-GB';
    return date.toLocaleDateString(locale, { 
        month: 'short', 
        day: 'numeric' 
    });
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', function() {
    initTabs();
    initMobileNav();
    initThemeToggle();
    loadForecastData();
});

// Tab functionality
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tab = this.dataset.tab;
            
            // Update button states
            tabBtns.forEach(b => {
                b.classList.remove('active', 'bg-white', 'dark:bg-card-dark');
                b.classList.add('text-text-muted', 'dark:text-[#92adc9]');
            });
            this.classList.add('active', 'bg-white', 'dark:bg-card-dark');
            this.classList.remove('text-text-muted', 'dark:text-[#92adc9]');
            
            // Show/hide content
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.add('hidden');
            });
            const tabContent = document.getElementById(`tab-${tab}`);
            if (tabContent) {
                tabContent.classList.remove('hidden');
            }
            
            // Load tab-specific data
            if (tab === 'cashflow') {
                loadCashFlowData();
            } else if (tab === 'calendar') {
                loadCalendarData();
            } else if (tab === 'trends') {
                loadTrendsData();
            }
        });
    });
}

// Mobile navigation
function initMobileNav() {
    const menuToggle = document.getElementById('menu-toggle');
    const mobileNav = document.getElementById('mobile-nav');
    const mobileNavOverlay = document.getElementById('mobile-nav-overlay');
    const closeMobileNav = document.getElementById('close-mobile-nav');
    
    if (menuToggle && mobileNav) {
        menuToggle.addEventListener('click', () => {
            mobileNav.classList.remove('-translate-x-full');
            mobileNavOverlay.classList.remove('hidden');
        });
    }
    
    if (closeMobileNav) {
        closeMobileNav.addEventListener('click', closeMobileNavFn);
    }
    
    if (mobileNavOverlay) {
        mobileNavOverlay.addEventListener('click', closeMobileNavFn);
    }
}

function closeMobileNavFn() {
    const mobileNav = document.getElementById('mobile-nav');
    const mobileNavOverlay = document.getElementById('mobile-nav-overlay');
    if (mobileNav) mobileNav.classList.add('-translate-x-full');
    if (mobileNavOverlay) mobileNavOverlay.classList.add('hidden');
}

// Theme toggle
function initThemeToggle() {
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    const themeText = document.getElementById('theme-text');
    
    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            document.documentElement.classList.toggle('dark');
            const isDark = document.documentElement.classList.contains('dark');
            localStorage.setItem('theme', isDark ? 'dark' : 'light');
            
            if (themeIcon) {
                themeIcon.textContent = isDark ? 'dark_mode' : 'light_mode';
            }
            if (themeText) {
                themeText.textContent = isDark ? 
                    tr('dashboard.darkMode', 'Dark Mode') : 
                    tr('dashboard.lightMode', 'Light Mode');
            }
        });
    }
}

// Load main forecast data
async function loadForecastData() {
    try {
        const [summaryRes, billsRes, incomeRes, categoryRes] = await Promise.all([
            fetch('/api/forecast/summary'),
            fetch('/api/forecast/upcoming-bills'),
            fetch('/api/forecast/income-forecast'),
            fetch('/api/forecast/category-forecast')
        ]);
        
        const summary = await summaryRes.json();
        const bills = await billsRes.json();
        const income = await incomeRes.json();
        const categoryForecast = await categoryRes.json();
        
        forecastData = { summary, bills, income, categoryForecast };
        
        updateSummaryCards(summary);
        updateUpcomingBills(bills);
        updateExpectedIncome(income);
        updateCategoryForecasts(categoryForecast);
        updateQuickStats(summary);
        
    } catch (error) {
        console.error('Error loading forecast data:', error);
        showError(tr('forecast.errorLoading', 'Error loading forecast data'));
    }
}

// Update summary cards
function updateSummaryCards(data) {
    // Predicted total
    const predictedTotal = document.getElementById('predicted-total');
    if (predictedTotal) {
        predictedTotal.textContent = formatCurrency(data.predicted_total || 0);
    }
    
    // Spent so far
    const spentSoFar = document.getElementById('spent-so-far');
    if (spentSoFar) {
        spentSoFar.textContent = formatCurrency(data.current_spent || 0);
    }
    
    // Days left
    const daysLeft = document.getElementById('days-left');
    if (daysLeft) {
        daysLeft.textContent = `${data.days_remaining || 0} ${tr('forecast.daysText', 'days')}`;
    }
    
    // Month progress
    const monthProgress = document.getElementById('month-progress');
    if (monthProgress) {
        const progress = data.days_elapsed && data.total_days ? 
            (data.days_elapsed / data.total_days) * 100 : 0;
        monthProgress.style.width = `${Math.min(progress, 100)}%`;
    }
    
    // Upcoming bills total
    const upcomingBillsTotal = document.getElementById('upcoming-bills-total');
    if (upcomingBillsTotal) {
        upcomingBillsTotal.textContent = formatCurrency(data.upcoming_bills_total || 0);
    }
    
    // Bills count
    const billsCount = document.getElementById('bills-count');
    if (billsCount) {
        const count = data.upcoming_bills_count || 0;
        billsCount.textContent = `${count} ${count === 1 ? 
            tr('forecast.bill', 'bill') : 
            tr('forecast.bills', 'bills')} ${tr('forecast.thisMonth', 'this month')}`;
    }
    
    // Budget comparison
    updateBudgetComparison(data);
    
    // Daily average and projection
    const dailyAverage = document.getElementById('daily-average');
    if (dailyAverage) {
        dailyAverage.textContent = formatCurrency(data.daily_average || 0);
    }
    
    const projectedMonthly = document.getElementById('projected-monthly');
    if (projectedMonthly) {
        projectedMonthly.textContent = formatCurrency(data.predicted_total || 0);
    }
}

// Update budget comparison section
function updateBudgetComparison(data) {
    const budgetComparison = document.getElementById('budget-comparison');
    const vsBudgetIcon = document.getElementById('vs-budget-icon');
    const vsBudgetText = document.getElementById('vs-budget-text');
    const budgetDiff = document.getElementById('budget-diff');
    const budgetProgressBar = document.getElementById('budget-progress-bar');
    const budgetAdvice = document.getElementById('budget-advice');
    
    if (!data.monthly_budget || data.monthly_budget <= 0) {
        if (budgetComparison) budgetComparison.classList.add('hidden');
        if (vsBudgetIcon) vsBudgetIcon.textContent = '';
        if (vsBudgetText) vsBudgetText.textContent = tr('forecast.noBudgetSet', 'No budget set');
        return;
    }
    
    if (budgetComparison) budgetComparison.classList.remove('hidden');
    
    const budget = data.monthly_budget;
    const predicted = data.predicted_total || 0;
    const diff = predicted - budget;
    const percentage = (predicted / budget) * 100;
    
    if (vsBudgetIcon && vsBudgetText) {
        if (diff <= 0) {
            vsBudgetIcon.textContent = 'check_circle';
            vsBudgetIcon.className = 'material-symbols-outlined text-sm text-emerald-500';
            vsBudgetText.textContent = tr('forecast.onTrack', 'On track to stay within budget');
            vsBudgetText.className = 'text-xs text-emerald-500';
        } else {
            vsBudgetIcon.textContent = 'warning';
            vsBudgetIcon.className = 'material-symbols-outlined text-sm text-red-500';
            vsBudgetText.textContent = tr('forecast.overBudget', 'Projected to exceed budget');
            vsBudgetText.className = 'text-xs text-red-500';
        }
    }
    
    if (budgetDiff) {
        if (diff <= 0) {
            budgetDiff.textContent = `${formatCurrency(Math.abs(diff))} ${tr('forecast.underBudget', 'under budget')}`;
            budgetDiff.className = 'font-bold text-emerald-500';
        } else {
            budgetDiff.textContent = `${formatCurrency(diff)} ${tr('forecast.over', 'over budget')}`;
            budgetDiff.className = 'font-bold text-red-500';
        }
    }
    
    if (budgetProgressBar) {
        budgetProgressBar.style.width = `${Math.min(percentage, 100)}%`;
        if (percentage <= 80) {
            budgetProgressBar.className = 'h-3 rounded-full transition-all duration-500 bg-emerald-500';
            budgetComparison.className = 'p-4 rounded-lg confidence-high';
        } else if (percentage <= 100) {
            budgetProgressBar.className = 'h-3 rounded-full transition-all duration-500 bg-amber-500';
            budgetComparison.className = 'p-4 rounded-lg confidence-medium';
        } else {
            budgetProgressBar.className = 'h-3 rounded-full transition-all duration-500 bg-red-500';
            budgetComparison.className = 'p-4 rounded-lg confidence-low';
        }
    }
    
    if (budgetAdvice) {
        const daysRemaining = data.days_remaining || 1;
        const safeDaily = Math.max(0, (budget - (data.current_spent || 0)) / daysRemaining);
        budgetAdvice.textContent = `${tr('forecast.toStayOnTrack', 'To stay on track, spend no more than')} ${formatCurrency(safeDaily)} ${tr('forecast.perDay', 'per day')}`;
    }
}

// Update upcoming bills list
function updateUpcomingBills(data) {
    const container = document.getElementById('upcoming-bills-list');
    if (!container) return;
    
    const bills = data.bills || [];
    
    if (bills.length === 0) {
        container.innerHTML = `
            <div class="text-center py-4">
                <span class="material-symbols-outlined text-4xl text-text-muted dark:text-[#92adc9] mb-2">event_available</span>
                <p class="text-sm text-text-muted dark:text-[#92adc9]">${tr('forecast.noBillsUpcoming', 'No upcoming bills')}</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = bills.slice(0, 5).map(bill => {
        const urgencyClass = bill.urgency === 'high' ? 'urgency-high' : 
                            bill.urgency === 'medium' ? 'urgency-medium' : 'urgency-low';
        return `
            <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-[#1a2b3c] rounded-lg border-l-4 ${urgencyClass}">
                <div>
                    <p class="font-medium text-text-main dark:text-white text-sm">${escapeHtml(bill.name)}</p>
                    <p class="text-xs text-text-muted dark:text-[#92adc9]">
                        ${formatDate(bill.due_date)} • ${bill.days_until} ${bill.days_until === 1 ? 
                            tr('forecast.day', 'day') : 
                            tr('forecast.daysText', 'days')}
                    </p>
                </div>
                <span class="font-bold text-red-500">${formatCurrency(bill.amount)}</span>
            </div>
        `;
    }).join('');
    
    if (bills.length > 5) {
        container.innerHTML += `
            <button onclick="switchToCalendarTab()" class="w-full py-2 text-sm text-primary hover:text-primary/80 font-medium">
                ${tr('forecast.viewAll', 'View all')} ${bills.length} ${tr('forecast.bills', 'bills')} →
            </button>
        `;
    }
}

// Update expected income list
function updateExpectedIncome(data) {
    const container = document.getElementById('expected-income-list');
    if (!container) return;
    
    const incomeItems = data.income || [];
    
    if (incomeItems.length === 0) {
        container.innerHTML = `
            <div class="text-center py-4">
                <span class="material-symbols-outlined text-4xl text-text-muted dark:text-[#92adc9] mb-2">payments</span>
                <p class="text-sm text-text-muted dark:text-[#92adc9]">${tr('forecast.noIncomeExpected', 'No expected income')}</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = incomeItems.slice(0, 4).map(income => `
        <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-[#1a2b3c] rounded-lg border-l-4 border-l-emerald-500">
            <div>
                <p class="font-medium text-text-main dark:text-white text-sm">${escapeHtml(income.source)}</p>
                <p class="text-xs text-text-muted dark:text-[#92adc9]">${formatDate(income.expected_date)}</p>
            </div>
            <span class="font-bold text-emerald-500">+${formatCurrency(income.amount)}</span>
        </div>
    `).join('');
}

// Update category forecasts
function updateCategoryForecasts(data) {
    const container = document.getElementById('category-forecasts');
    if (!container) return;
    
    const categories = data.categories || [];
    
    if (categories.length === 0) {
        container.innerHTML = `
            <div class="text-center py-8">
                <span class="material-symbols-outlined text-4xl text-text-muted dark:text-[#92adc9] mb-2">category</span>
                <p class="text-sm text-text-muted dark:text-[#92adc9]">${tr('forecast.noCategories', 'No spending data yet')}</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = categories.slice(0, 6).map(cat => {
        const trendIcon = cat.trend === 'up' ? 'trending_up' : 
                         cat.trend === 'down' ? 'trending_down' : 'trending_flat';
        const trendClass = cat.trend === 'up' ? 'trend-up' : 
                          cat.trend === 'down' ? 'trend-down' : 'trend-stable';
        const budgetPercent = cat.category_budget > 0 ? 
            Math.min((cat.predicted / cat.category_budget) * 100, 100) : 0;
        
        return `
            <div class="p-4 bg-gray-50 dark:bg-[#1a2b3c] rounded-lg">
                <div class="flex items-center justify-between mb-2">
                    <div class="flex items-center gap-2">
                        <span class="text-2xl">${cat.icon || '📦'}</span>
                        <span class="font-medium text-text-main dark:text-white">${escapeHtml(cat.name)}</span>
                    </div>
                    <div class="flex items-center gap-1">
                        <span class="material-symbols-outlined text-sm ${trendClass}">${trendIcon}</span>
                        <span class="font-bold text-text-main dark:text-white">${formatCurrency(cat.predicted)}</span>
                    </div>
                </div>
                <div class="flex items-center justify-between text-xs text-text-muted dark:text-[#92adc9] mb-1">
                    <span>${tr('forecast.spentSoFar', 'Spent')}: ${formatCurrency(cat.current)}</span>
                    ${cat.category_budget > 0 ? `
                        <span>${tr('forecast.budget', 'Budget')}: ${formatCurrency(cat.category_budget)}</span>
                    ` : ''}
                </div>
                ${cat.category_budget > 0 ? `
                    <div class="w-full bg-gray-200 dark:bg-[#233648] rounded-full h-1.5">
                        <div class="h-1.5 rounded-full ${budgetPercent > 100 ? 'bg-red-500' : budgetPercent > 80 ? 'bg-amber-500' : 'bg-emerald-500'}" style="width: ${budgetPercent}%"></div>
                    </div>
                ` : ''}
            </div>
        `;
    }).join('');
}

// Update quick stats
function updateQuickStats(data) {
    const statAvgDaily = document.getElementById('stat-avg-daily');
    const statHighestDay = document.getElementById('stat-highest-day');
    const statVsLast = document.getElementById('stat-vs-last');
    const statTopCategory = document.getElementById('stat-top-category');
    
    if (statAvgDaily) {
        statAvgDaily.textContent = formatCurrency(data.daily_average || 0);
    }
    
    if (statHighestDay && data.highest_day) {
        statHighestDay.textContent = formatCurrency(data.highest_day.amount || 0);
    }
    
    if (statVsLast) {
        const change = data.vs_last_month_percent || 0;
        if (change > 0) {
            statVsLast.textContent = `+${change.toFixed(1)}%`;
            statVsLast.className = 'font-medium text-red-500';
        } else if (change < 0) {
            statVsLast.textContent = `${change.toFixed(1)}%`;
            statVsLast.className = 'font-medium text-emerald-500';
        } else {
            statVsLast.textContent = '0%';
            statVsLast.className = 'font-medium text-text-main dark:text-white';
        }
    }
    
    if (statTopCategory && data.top_category) {
        statTopCategory.textContent = data.top_category.name || '--';
    }
}

// Load cash flow data
async function loadCashFlowData() {
    try {
        const res = await fetch('/api/forecast/cash-flow');
        const data = await res.json();
        
        renderCashFlowChart(data.daily_flow || []);
        renderBalanceTimeline(data.daily_flow || []);
        
    } catch (error) {
        console.error('Error loading cash flow data:', error);
    }
}

// Render cash flow chart
function renderCashFlowChart(dailyFlow) {
    const container = document.getElementById('cashflow-chart');
    if (!container) return;
    
    if (dailyFlow.length === 0) {
        container.innerHTML = `
            <div class="flex items-center justify-center w-full h-full">
                <p class="text-sm text-text-muted dark:text-[#92adc9]">${tr('forecast.noDataAvailable', 'No data available')}</p>
            </div>
        `;
        return;
    }
    
    // Find max values for scaling
    const maxIncome = Math.max(...dailyFlow.map(d => d.income || 0), 1);
    const maxExpense = Math.max(...dailyFlow.map(d => d.expenses || 0), 1);
    const maxValue = Math.max(maxIncome, maxExpense);
    
    container.innerHTML = dailyFlow.map((day, index) => {
        const incomeHeight = ((day.income || 0) / maxValue) * 100;
        const expenseHeight = ((day.expenses || 0) / maxValue) * 100;
        const date = new Date(day.date);
        const isToday = date.toDateString() === new Date().toDateString();
        
        return `
            <div class="flex flex-col items-center flex-1 min-w-0 group relative">
                <div class="flex gap-0.5 items-end h-48 w-full">
                    <div class="flex-1 bg-emerald-500 cashflow-bar rounded-t" style="height: ${incomeHeight}%"></div>
                    <div class="flex-1 bg-red-500 cashflow-bar rounded-t" style="height: ${expenseHeight}%"></div>
                </div>
                <div class="text-[10px] text-text-muted dark:text-[#92adc9] mt-1 ${isToday ? 'font-bold text-purple-500' : ''}">
                    ${date.getDate()}
                </div>
                <div class="absolute bottom-full mb-2 hidden group-hover:block bg-white dark:bg-card-dark p-2 rounded shadow-lg border border-gray-200 dark:border-[#233648] z-10 whitespace-nowrap text-xs">
                    <p class="font-medium">${formatDate(day.date)}</p>
                    <p class="text-emerald-500">+${formatCurrency(day.income || 0)}</p>
                    <p class="text-red-500">-${formatCurrency(day.expenses || 0)}</p>
                    <p class="text-blue-500">${tr('forecast.balance', 'Balance')}: ${formatCurrency(day.running_balance || 0)}</p>
                </div>
            </div>
        `;
    }).join('');
}

// Render balance timeline
function renderBalanceTimeline(dailyFlow) {
    const container = document.getElementById('balance-timeline');
    if (!container) return;
    
    const keyDays = dailyFlow.filter((day, index) => 
        index === 0 || 
        index === dailyFlow.length - 1 || 
        day.income > 0 || 
        day.expenses > 100
    ).slice(0, 8);
    
    if (keyDays.length === 0) {
        container.innerHTML = `
            <p class="text-sm text-text-muted dark:text-[#92adc9] text-center py-4">${tr('forecast.noDataAvailable', 'No data available')}</p>
        `;
        return;
    }
    
    container.innerHTML = keyDays.map(day => {
        const balance = day.running_balance || 0;
        const balanceClass = balance >= 0 ? 'text-emerald-500' : 'text-red-500';
        
        return `
            <div class="flex items-center justify-between p-2 hover:bg-gray-50 dark:hover:bg-[#233648] rounded-lg">
                <div class="flex items-center gap-3">
                    <div class="w-2 h-2 rounded-full ${balance >= 0 ? 'bg-emerald-500' : 'bg-red-500'}"></div>
                    <span class="text-sm text-text-muted dark:text-[#92adc9]">${formatDate(day.date)}</span>
                </div>
                <span class="font-medium ${balanceClass}">${formatCurrency(balance)}</span>
            </div>
        `;
    }).join('');
}

// Load calendar data
async function loadCalendarData() {
    try {
        const year = currentCalendarMonth.getFullYear();
        const month = currentCalendarMonth.getMonth() + 1;
        
        const res = await fetch(`/api/forecast/bills-calendar?year=${year}&month=${month}`);
        calendarData = await res.json();
        
        renderBillsCalendar();
        updateCalendarMonthLabel();
        
    } catch (error) {
        console.error('Error loading calendar data:', error);
    }
}

// Render bills calendar
function renderBillsCalendar() {
    const container = document.getElementById('bills-calendar-grid');
    if (!container || !calendarData) return;
    
    const calendar = calendarData.calendar || [];
    const today = new Date();
    
    container.innerHTML = calendar.map(day => {
        if (!day.day) {
            return '<div class="h-10"></div>';
        }
        
        const hasBills = day.bills && day.bills.length > 0;
        const hasIncome = day.income && day.income.length > 0;
        const isToday = day.is_today;
        const isPast = new Date(day.date) < today && !isToday;
        
        let classes = 'calendar-day h-10 flex items-center justify-center rounded-lg text-sm cursor-pointer relative ';
        
        if (isToday) {
            classes += 'bg-purple-500/20 border-2 border-purple-500 font-bold text-purple-500 ';
        } else if (isPast) {
            classes += 'text-text-muted dark:text-[#92adc9] opacity-50 ';
        } else {
            classes += 'hover:bg-gray-100 dark:hover:bg-[#233648] text-text-main dark:text-white ';
        }
        
        if (hasBills) classes += 'has-bills ';
        if (hasIncome) classes += 'has-income ';
        
        return `
            <div class="${classes}" onclick="showDayDetails('${day.date}')" data-date="${day.date}">
                ${day.day}
                ${hasBills && hasIncome ? '<span class="absolute top-0.5 right-0.5 text-[8px]">💰</span>' : ''}
            </div>
        `;
    }).join('');
}

// Change calendar month
function changeCalendarMonth(delta) {
    currentCalendarMonth.setMonth(currentCalendarMonth.getMonth() + delta);
    loadCalendarData();
}

// Update calendar month label
function updateCalendarMonthLabel() {
    const label = document.getElementById('calendar-month-label');
    if (label) {
        const locale = window.userLocale || 'en-GB';
        label.textContent = currentCalendarMonth.toLocaleDateString(locale, { 
            month: 'long', 
            year: 'numeric' 
        });
    }
}

// Show day details
function showDayDetails(dateStr) {
    const panel = document.getElementById('day-details-panel');
    const title = document.getElementById('day-details-title');
    const content = document.getElementById('day-details-content');
    
    if (!panel || !calendarData) return;
    
    const dayData = calendarData.calendar.find(d => d.date === dateStr);
    if (!dayData || (!dayData.bills?.length && !dayData.income?.length)) {
        panel.classList.add('hidden');
        return;
    }
    
    panel.classList.remove('hidden');
    title.textContent = formatDate(dateStr);
    
    let html = '';
    
    if (dayData.bills && dayData.bills.length > 0) {
        html += `<h5 class="font-medium text-red-500 mb-2 text-sm">${tr('forecast.billsDue', 'Bills Due')}</h5>`;
        html += dayData.bills.map(bill => `
            <div class="flex items-center justify-between p-2 bg-red-50 dark:bg-red-900/20 rounded-lg mb-1">
                <span class="text-sm text-text-main dark:text-white">${escapeHtml(bill.name)}</span>
                <span class="font-medium text-red-500">${formatCurrency(bill.amount)}</span>
            </div>
        `).join('');
    }
    
    if (dayData.income && dayData.income.length > 0) {
        html += `<h5 class="font-medium text-emerald-500 mb-2 mt-3 text-sm">${tr('forecast.incomeExpected', 'Income Expected')}</h5>`;
        html += dayData.income.map(inc => `
            <div class="flex items-center justify-between p-2 bg-emerald-50 dark:bg-emerald-900/20 rounded-lg mb-1">
                <span class="text-sm text-text-main dark:text-white">${escapeHtml(inc.source)}</span>
                <span class="font-medium text-emerald-500">+${formatCurrency(inc.amount)}</span>
            </div>
        `).join('');
    }
    
    content.innerHTML = html;
}

// Load trends data
async function loadTrendsData() {
    try {
        const res = await fetch('/api/forecast/trends');
        const data = await res.json();
        
        renderTrendsChart(data.monthly_totals || []);
        renderCategoryTrends(data.category_trends || []);
        
    } catch (error) {
        console.error('Error loading trends data:', error);
    }
}

// Render trends chart
function renderTrendsChart(monthlyTotals) {
    const container = document.getElementById('trends-chart');
    if (!container) return;
    
    if (monthlyTotals.length === 0) {
        container.innerHTML = `
            <div class="flex items-center justify-center w-full h-full">
                <p class="text-sm text-text-muted dark:text-[#92adc9]">${tr('forecast.noHistoricalData', 'No historical data')}</p>
            </div>
        `;
        return;
    }
    
    const maxAmount = Math.max(...monthlyTotals.map(m => m.total || 0), 1);
    
    container.innerHTML = monthlyTotals.map((month, index) => {
        const height = ((month.total || 0) / maxAmount) * 100;
        const isCurrentMonth = index === monthlyTotals.length - 1;
        const locale = window.userLocale || 'en-GB';
        const monthName = new Date(month.year, month.month - 1).toLocaleDateString(locale, { month: 'short' });
        
        return `
            <div class="flex flex-col items-center flex-1 group relative">
                <div class="w-full px-1">
                    <div class="w-full ${isCurrentMonth ? 'bg-purple-500' : 'bg-blue-500'} rounded-t transition-all hover:brightness-110" style="height: ${height * 2}px"></div>
                </div>
                <div class="text-xs text-text-muted dark:text-[#92adc9] mt-2 ${isCurrentMonth ? 'font-bold text-purple-500' : ''}">
                    ${monthName}
                </div>
                <div class="absolute bottom-full mb-2 hidden group-hover:block bg-white dark:bg-card-dark p-2 rounded shadow-lg border border-gray-200 dark:border-[#233648] z-10 whitespace-nowrap text-xs">
                    <p class="font-medium">${monthName} ${month.year}</p>
                    <p>${formatCurrency(month.total || 0)}</p>
                </div>
            </div>
        `;
    }).join('');
}

// Render category trends
function renderCategoryTrends(categoryTrends) {
    const container = document.getElementById('category-trends');
    if (!container) return;
    
    if (categoryTrends.length === 0) {
        container.innerHTML = `
            <p class="text-sm text-text-muted dark:text-[#92adc9] text-center py-4">${tr('forecast.noCategoryTrends', 'No category trends available')}</p>
        `;
        return;
    }
    
    container.innerHTML = categoryTrends.slice(0, 5).map(cat => {
        const change = cat.change_percent || 0;
        const trendIcon = change > 0 ? 'trending_up' : change < 0 ? 'trending_down' : 'trending_flat';
        const trendClass = change > 0 ? 'text-red-500' : change < 0 ? 'text-emerald-500' : 'text-amber-500';
        
        return `
            <div class="flex items-center justify-between p-3 bg-gray-50 dark:bg-[#1a2b3c] rounded-lg">
                <div class="flex items-center gap-3">
                    <span class="text-xl">${cat.icon || '📦'}</span>
                    <div>
                        <p class="font-medium text-text-main dark:text-white text-sm">${escapeHtml(cat.name)}</p>
                        <p class="text-xs text-text-muted dark:text-[#92adc9]">${formatCurrency(cat.current_month || 0)} ${tr('forecast.thisMonth', 'this month')}</p>
                    </div>
                </div>
                <div class="flex items-center gap-1 ${trendClass}">
                    <span class="material-symbols-outlined text-sm">${trendIcon}</span>
                    <span class="font-medium text-sm">${change > 0 ? '+' : ''}${change.toFixed(1)}%</span>
                </div>
            </div>
        `;
    }).join('');
}

// Switch to calendar tab
function switchToCalendarTab() {
    const calendarBtn = document.querySelector('[data-tab="calendar"]');
    if (calendarBtn) {
        calendarBtn.click();
    }
}

// Show error message
function showError(message) {
    // Could implement a toast notification here
    console.error(message);
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
