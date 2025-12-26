// Reports page JavaScript

let currentPeriod = 30;
let categoryFilter = '';
let trendChart = null;
let categoryChart = null;
let monthlyChart = null;

// Load reports data
async function loadReportsData() {
    try {
        const params = new URLSearchParams({
            period: currentPeriod,
            ...(categoryFilter && { category_id: categoryFilter })
        });
        
        const data = await apiCall(`/api/reports-stats?${params}`);
        displayReportsData(data);
    } catch (error) {
        console.error('Failed to load reports data:', error);
        showToast('Failed to load reports', 'error');
    }
}

// Display reports data
function displayReportsData(data) {
    // Update KPI cards
    document.getElementById('total-spent').textContent = formatCurrency(data.total_spent, data.currency);
    
    // Spending change indicator
    const spentChange = document.getElementById('spent-change');
    const changeValue = data.percent_change;
    const isIncrease = changeValue > 0;
    spentChange.className = `flex items-center font-medium px-1.5 py-0.5 rounded ${
        isIncrease 
            ? 'text-red-500 dark:text-red-400 bg-red-500/10' 
            : 'text-green-500 dark:text-green-400 bg-green-500/10'
    }`;
    spentChange.innerHTML = `
        <span class="material-symbols-outlined text-[14px] mr-0.5">${isIncrease ? 'trending_up' : 'trending_down'}</span>
        ${Math.abs(changeValue).toFixed(1)}%
    `;
    
    // Top category
    document.getElementById('top-category').textContent = data.top_category.name;
    document.getElementById('top-category-amount').textContent = formatCurrency(data.top_category.amount, data.currency);
    
    // Average daily
    document.getElementById('avg-daily').textContent = formatCurrency(data.avg_daily, data.currency);
    
    // Average change indicator
    const avgChange = document.getElementById('avg-change');
    const avgChangeValue = data.avg_daily_change;
    const isAvgIncrease = avgChangeValue > 0;
    avgChange.className = `flex items-center font-medium px-1.5 py-0.5 rounded ${
        isAvgIncrease 
            ? 'text-red-500 dark:text-red-400 bg-red-500/10' 
            : 'text-green-500 dark:text-green-400 bg-green-500/10'
    }`;
    avgChange.innerHTML = `
        <span class="material-symbols-outlined text-[14px] mr-0.5">${isAvgIncrease ? 'trending_up' : 'trending_down'}</span>
        ${Math.abs(avgChangeValue).toFixed(1)}%
    `;
    
    // Savings rate
    document.getElementById('savings-rate').textContent = `${data.savings_rate}%`;
    
    // Update charts
    updateTrendChart(data.daily_trend);
    updateCategoryChart(data.category_breakdown);
    updateMonthlyChart(data.monthly_comparison);
}

// Update trend chart
function updateTrendChart(dailyData) {
    const ctx = document.getElementById('trend-chart');
    if (!ctx) return;
    
    // Get theme
    const isDark = document.documentElement.classList.contains('dark');
    const textColor = isDark ? '#94a3b8' : '#64748b';
    const gridColor = isDark ? '#334155' : '#e2e8f0';
    
    if (trendChart) {
        trendChart.destroy();
    }
    
    trendChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: dailyData.map(d => d.date),
            datasets: [{
                label: 'Daily Spending',
                data: dailyData.map(d => d.amount),
                borderColor: '#3b82f6',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointBackgroundColor: isDark ? '#1e293b' : '#ffffff',
                pointBorderColor: '#3b82f6',
                pointBorderWidth: 2,
                pointHoverRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: isDark ? '#1e293b' : '#ffffff',
                    titleColor: isDark ? '#f8fafc' : '#0f172a',
                    bodyColor: isDark ? '#94a3b8' : '#64748b',
                    borderColor: isDark ? '#334155' : '#e2e8f0',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return formatCurrency(context.parsed.y, 'USD');
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        color: gridColor,
                        drawBorder: false
                    },
                    ticks: {
                        color: textColor,
                        maxRotation: 45,
                        minRotation: 0
                    }
                },
                y: {
                    grid: {
                        color: gridColor,
                        drawBorder: false
                    },
                    ticks: {
                        color: textColor,
                        callback: function(value) {
                            return '$' + value.toFixed(0);
                        }
                    }
                }
            }
        }
    });
}

// Update category pie chart
function updateCategoryChart(categories) {
    const ctx = document.getElementById('category-pie-chart');
    if (!ctx) return;
    
    const isDark = document.documentElement.classList.contains('dark');
    
    if (categoryChart) {
        categoryChart.destroy();
    }
    
    if (categories.length === 0) {
        categoryChart = null;
        document.getElementById('category-legend').innerHTML = '<p class="col-span-2 text-center text-text-muted dark:text-[#92adc9]">No data available</p>';
        return;
    }
    
    categoryChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: categories.map(c => c.name),
            datasets: [{
                data: categories.map(c => c.amount),
                backgroundColor: categories.map(c => c.color),
                borderWidth: 2,
                borderColor: isDark ? '#1a2632' : '#ffffff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: isDark ? '#1e293b' : '#ffffff',
                    titleColor: isDark ? '#f8fafc' : '#0f172a',
                    bodyColor: isDark ? '#94a3b8' : '#64748b',
                    borderColor: isDark ? '#334155' : '#e2e8f0',
                    borderWidth: 1,
                    padding: 12,
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = formatCurrency(context.parsed, 'USD');
                            const percentage = categories[context.dataIndex].percentage;
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
    
    // Update legend
    const legendHTML = categories.slice(0, 6).map(cat => `
        <div class="flex items-center gap-2">
            <span class="size-3 rounded-full" style="background-color: ${cat.color}"></span>
            <span class="text-text-muted dark:text-[#92adc9] flex-1 truncate">${cat.name}</span>
            <span class="font-semibold text-text-main dark:text-white">${cat.percentage}%</span>
        </div>
    `).join('');
    
    document.getElementById('category-legend').innerHTML = legendHTML;
}

// Update monthly chart
function updateMonthlyChart(monthlyData) {
    const ctx = document.getElementById('monthly-chart');
    if (!ctx) return;
    
    const isDark = document.documentElement.classList.contains('dark');
    const textColor = isDark ? '#94a3b8' : '#64748b';
    const gridColor = isDark ? '#334155' : '#e2e8f0';
    
    if (monthlyChart) {
        monthlyChart.destroy();
    }
    
    monthlyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: monthlyData.map(d => d.month),
            datasets: [{
                label: 'Monthly Spending',
                data: monthlyData.map(d => d.amount),
                backgroundColor: '#3b82f6',
                borderRadius: 6,
                hoverBackgroundColor: '#2563eb'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    backgroundColor: isDark ? '#1e293b' : '#ffffff',
                    titleColor: isDark ? '#f8fafc' : '#0f172a',
                    bodyColor: isDark ? '#94a3b8' : '#64748b',
                    borderColor: isDark ? '#334155' : '#e2e8f0',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return formatCurrency(context.parsed.y, 'USD');
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: textColor
                    }
                },
                y: {
                    grid: {
                        color: gridColor,
                        drawBorder: false
                    },
                    ticks: {
                        color: textColor,
                        callback: function(value) {
                            return '$' + value.toFixed(0);
                        }
                    }
                }
            }
        }
    });
}

// Load categories for filter
async function loadCategoriesFilter() {
    try {
        const data = await apiCall('/api/expenses/categories');
        const select = document.getElementById('category-filter');
        
        const categoriesHTML = data.categories.map(cat => 
            `<option value="${cat.id}">${cat.name}</option>`
        ).join('');
        
        select.innerHTML = '<option value="">All Categories</option>' + categoriesHTML;
    } catch (error) {
        console.error('Failed to load categories:', error);
    }
}

// Period button handlers
document.querySelectorAll('.period-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        // Remove active class from all buttons
        document.querySelectorAll('.period-btn').forEach(b => {
            b.classList.remove('active', 'text-white', 'dark:text-white', 'bg-white/10', 'shadow-sm');
            b.classList.add('text-text-muted', 'dark:text-[#92adc9]', 'hover:text-text-main', 'dark:hover:text-white', 'hover:bg-white/5');
        });
        
        // Add active class to clicked button
        btn.classList.add('active', 'text-white', 'dark:text-white', 'bg-white/10', 'shadow-sm');
        btn.classList.remove('text-text-muted', 'dark:text-[#92adc9]', 'hover:text-text-main', 'dark:hover:text-white', 'hover:bg-white/5');
        
        currentPeriod = btn.dataset.period;
        loadReportsData();
    });
});

// Category filter handler
document.getElementById('category-filter').addEventListener('change', (e) => {
    categoryFilter = e.target.value;
});

// Generate report button
document.getElementById('generate-report-btn').addEventListener('click', () => {
    loadReportsData();
});

// Export report button
document.getElementById('export-report-btn').addEventListener('click', () => {
    window.location.href = '/api/expenses/export/csv';
});

// Handle theme changes - reload charts with new theme colors
function handleThemeChange() {
    if (trendChart || categoryChart || monthlyChart) {
        loadReportsData();
    }
}

// Listen for theme toggle events
window.addEventListener('theme-changed', handleThemeChange);

// Listen for storage changes (for multi-tab sync)
window.addEventListener('storage', (e) => {
    if (e.key === 'theme') {
        handleThemeChange();
    }
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadReportsData();
    loadCategoriesFilter();
});
