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
    // Store user currency globally
    window.userCurrency = data.currency || 'RON';
    
    // Update KPI cards
    document.getElementById('total-spent').textContent = formatCurrency(data.total_spent, window.userCurrency);
    
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
                            return formatCurrency(context.parsed.y, window.userCurrency || 'RON');
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

// Update category pie chart - Beautiful CSS conic-gradient design
function updateCategoryChart(categories) {
    const pieChart = document.getElementById('category-pie-chart');
    const pieTotal = document.getElementById('category-pie-total');
    const pieLegend = document.getElementById('category-legend');
    
    if (!pieChart || !pieLegend) return;
    
    const userCurrency = window.userCurrency || 'RON';
    
    if (categories.length === 0) {
        pieChart.style.background = 'conic-gradient(#233648 0% 100%)';
        if (pieTotal) pieTotal.textContent = formatCurrency(0, userCurrency);
        pieLegend.innerHTML = '<p class="col-span-2 text-center text-text-muted dark:text-[#92adc9] text-sm">No data available</p>';
        return;
    }
    
    // Calculate total
    const total = categories.reduce((sum, cat) => sum + parseFloat(cat.amount || 0), 0);
    if (pieTotal) pieTotal.textContent = formatCurrency(total, userCurrency);
    
    // Generate conic gradient segments
    let currentPercent = 0;
    const gradientSegments = categories.map(cat => {
        const percent = total > 0 ? (parseFloat(cat.amount || 0) / total) * 100 : 0;
        const segment = `${cat.color} ${currentPercent}% ${currentPercent + percent}%`;
        currentPercent += percent;
        return segment;
    });
    
    // Apply gradient
    pieChart.style.background = `conic-gradient(${gradientSegments.join(', ')})`;
    
    // Generate compact legend
    const legendHTML = categories.map(cat => {
        const percent = total > 0 ? ((parseFloat(cat.amount || 0) / total) * 100).toFixed(1) : 0;
        return `
            <div class="flex items-center gap-1.5 group cursor-pointer hover:opacity-80 transition-opacity py-0.5">
                <span class="size-2 rounded-full flex-shrink-0" style="background: ${cat.color};"></span>
                <span class="text-text-muted dark:text-[#92adc9] text-[10px] truncate flex-1 leading-tight">${cat.name}</span>
                <span class="text-text-muted dark:text-[#92adc9] text-[10px] font-medium">${percent}%</span>
            </div>
        `;
    }).join('');
    
    pieLegend.innerHTML = legendHTML;
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
                backgroundColor: '#2b8cee',
                borderRadius: 6,
                barPercentage: 0.5,  // Slim bars
                categoryPercentage: 0.7,  // Tighter spacing
                hoverBackgroundColor: '#1d7ad9'
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
                    backgroundColor: isDark ? '#1a2632' : '#ffffff',
                    titleColor: isDark ? '#ffffff' : '#1a2632',
                    bodyColor: isDark ? '#92adc9' : '#64748b',
                    borderColor: isDark ? '#233648' : '#e2e8f0',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: false,
                    callbacks: {
                        label: function(context) {
                            return formatCurrency(context.parsed.y, window.userCurrency || 'RON');
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
                        color: textColor,
                        font: { size: 10 },
                        autoSkip: false,
                        maxRotation: 0,
                        minRotation: 0
                    },
                    border: { display: false }
                },
                y: {
                    grid: {
                        color: gridColor,
                        drawBorder: false
                    },
                    ticks: {
                        color: textColor,
                        font: { size: 11 },
                        maxTicksLimit: 6,
                        callback: function(value) {
                            return formatCurrency(value, window.userCurrency || 'RON');
                        }
                    },
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

// Load smart recommendations
async function loadRecommendations() {
    const container = document.getElementById('recommendations-container');
    if (!container) return;
    
    try {
        const data = await apiCall('/api/smart-recommendations');
        
        if (!data.success || !data.recommendations || data.recommendations.length === 0) {
            container.innerHTML = `
                <div class="flex items-center justify-center py-8">
                    <div class="flex flex-col items-center gap-2">
                        <span class="material-symbols-outlined text-text-muted dark:text-[#92adc9] text-[32px]">lightbulb</span>
                        <p class="text-sm text-text-muted dark:text-[#92adc9]" data-translate="reports.noRecommendations">No recommendations at this time</p>
                    </div>
                </div>
            `;
            return;
        }
        
        const recommendationsHTML = data.recommendations.map(rec => {
            // Type-based colors
            const colorClasses = {
                'warning': 'border-yellow-500/20 bg-yellow-500/5 hover:bg-yellow-500/10',
                'success': 'border-green-500/20 bg-green-500/5 hover:bg-green-500/10',
                'info': 'border-blue-500/20 bg-blue-500/5 hover:bg-blue-500/10',
                'danger': 'border-red-500/20 bg-red-500/5 hover:bg-red-500/10'
            };
            
            const iconColors = {
                'warning': 'text-yellow-500',
                'success': 'text-green-500',
                'info': 'text-blue-500',
                'danger': 'text-red-500'
            };
            
            return `
                <div class="flex items-start gap-4 p-4 rounded-lg border ${colorClasses[rec.type] || 'border-border-light dark:border-[#233648]'} transition-all">
                    <span class="material-symbols-outlined ${iconColors[rec.type] || 'text-primary'} text-[28px] flex-shrink-0 mt-0.5">${rec.icon}</span>
                    <div class="flex-1 min-w-0">
                        <h4 class="text-sm font-semibold text-text-main dark:text-white mb-1">${rec.title}</h4>
                        <p class="text-xs text-text-muted dark:text-[#92adc9] leading-relaxed">${rec.description}</p>
                    </div>
                </div>
            `;
        }).join('');
        
        container.innerHTML = recommendationsHTML;
        
    } catch (error) {
        console.error('Failed to load recommendations:', error);
        container.innerHTML = `
            <div class="flex items-center justify-center py-8">
                <p class="text-sm text-red-500">Failed to load recommendations</p>
            </div>
        `;
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
    loadRecommendations();
});
