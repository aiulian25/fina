// Dashboard JavaScript

let categoryChart, monthlyChart;

// Comprehensive category icons list (Material Symbols)
const CATEGORY_ICONS = {
    // Finance & Money
    'wallet': 'Wallet',
    'savings': 'Savings',
    'account_balance': 'Bank',
    'credit_card': 'Credit Card',
    'payments': 'Payments',
    'currency_exchange': 'Exchange',
    'attach_money': 'Money',
    'price_check': 'Price Check',
    'receipt': 'Receipt',
    'receipt_long': 'Receipt Long',
    
    // Housing & Home
    'home': 'Home',
    'apartment': 'Apartment',
    'house': 'House',
    'real_estate_agent': 'Mortgage',
    'cottage': 'Cottage',
    'roofing': 'Roofing',
    'foundation': 'Foundation',
    'construction': 'Construction',
    'home_repair_service': 'Home Repair',
    'plumbing': 'Plumbing',
    'electrical_services': 'Electrical',
    'hvac': 'HVAC',
    'carpenter': 'Carpenter',
    
    // Transportation
    'directions_car': 'Car',
    'local_gas_station': 'Gas Station',
    'local_taxi': 'Taxi',
    'commute': 'Commute',
    'directions_bus': 'Bus',
    'train': 'Train',
    'subway': 'Subway',
    'directions_bike': 'Bike',
    'two_wheeler': 'Motorcycle',
    'flight': 'Flight',
    'local_shipping': 'Delivery',
    'local_parking': 'Parking',
    'car_repair': 'Car Repair',
    'oil_barrel': 'Oil/Fuel',
    'tire_repair': 'Tire Repair',
    
    // Food & Dining
    'restaurant': 'Restaurant',
    'local_dining': 'Dining',
    'fastfood': 'Fast Food',
    'local_pizza': 'Pizza',
    'local_cafe': 'Cafe',
    'local_bar': 'Bar',
    'liquor': 'Liquor',
    'dinner_dining': 'Dinner',
    'lunch_dining': 'Lunch',
    'breakfast_dining': 'Breakfast',
    'ramen_dining': 'Ramen',
    'set_meal': 'Set Meal',
    'takeout_dining': 'Takeout',
    'room_service': 'Room Service',
    'bakery_dining': 'Bakery',
    'icecream': 'Ice Cream',
    'cake': 'Cake',
    
    // Shopping & Retail
    'shopping_cart': 'Shopping',
    'shopping_bag': 'Shopping Bag',
    'store': 'Store',
    'storefront': 'Shop',
    'local_grocery_store': 'Grocery',
    'local_mall': 'Mall',
    'local_convenience_store': 'Convenience',
    'checkroom': 'Clothing',
    'dry_cleaning': 'Dry Cleaning',
    'laundry': 'Laundry',
    
    // Entertainment & Leisure
    'movie': 'Movies',
    'theaters': 'Theater',
    'sports_esports': 'Gaming',
    'casino': 'Casino',
    'nightlife': 'Nightlife',
    'sports_bar': 'Sports Bar',
    'pool': 'Pool',
    'sports': 'Sports',
    'sports_soccer': 'Soccer',
    'sports_basketball': 'Basketball',
    'sports_tennis': 'Tennis',
    'golf_course': 'Golf',
    'fitness_center': 'Gym',
    'hiking': 'Hiking',
    'kayaking': 'Kayaking',
    'surfing': 'Surfing',
    'sailing': 'Sailing',
    'downhill_skiing': 'Skiing',
    'snowboarding': 'Snowboarding',
    'music_note': 'Music',
    'headphones': 'Headphones',
    'videogame_asset': 'Video Games',
    'toys': 'Toys',
    'celebration': 'Celebration',
    'festival': 'Festival',
    
    // Health & Medical
    'medical_services': 'Medical',
    'local_hospital': 'Hospital',
    'local_pharmacy': 'Pharmacy',
    'medication': 'Medication',
    'vaccines': 'Vaccines',
    'health_and_safety': 'Health',
    'psychology': 'Mental Health',
    'dental_services': 'Dental',
    'ophthalmology': 'Eye Care',
    'healing': 'Healing',
    'monitor_heart': 'Heart Health',
    
    // Personal Care & Beauty
    'spa': 'Spa',
    'self_improvement': 'Self Care',
    'face': 'Face Care',
    'hair_dryer': 'Hair Dryer',
    'content_cut': 'Haircut',
    'cosmetics': 'Cosmetics',
    'perfume': 'Perfume',
    
    // Education & Work
    'school': 'Education',
    'work': 'Work',
    'business': 'Business',
    'laptop': 'Laptop',
    'computer': 'Computer',
    'book': 'Books',
    'menu_book': 'Study',
    'library_books': 'Library',
    'article': 'Article',
    'science': 'Science',
    'engineering': 'Engineering',
    
    // Utilities & Bills
    'bolt': 'Electricity',
    'water_drop': 'Water',
    'cell_tower': 'Internet',
    'phone': 'Phone',
    'wifi': 'WiFi',
    'router': 'Router',
    'tv': 'TV/Cable',
    'satellite': 'Satellite',
    'propane_tank': 'Propane',
    'heat': 'Heating',
    'ac_unit': 'Air Conditioning',
    
    // Insurance & Financial Services
    'shield': 'Insurance',
    'health_and_safety': 'Health Insurance',
    'verified_user': 'Life Insurance',
    'lock': 'Security',
    'gavel': 'Legal',
    'balance': 'Accounting',
    
    // Pets & Animals
    'pets': 'Pets',
    'cruelty_free': 'Pet Care',
    
    // Tobacco & Vices
    'smoking_rooms': 'Smoking',
    'vaping_rooms': 'Vaping',
    
    // Family & Children
    'family_restroom': 'Family',
    'child_care': 'Childcare',
    'baby_changing_station': 'Baby Care',
    'toys': 'Kids Toys',
    'school': 'School',
    'backpack': 'School Supplies',
    
    // Gifts & Donations
    'redeem': 'Gifts',
    'card_giftcard': 'Gift Card',
    'volunteer_activism': 'Donations',
    'favorite': 'Charity',
    
    // Tech & Electronics
    'phone_iphone': 'Smartphone',
    'tablet': 'Tablet',
    'watch': 'Watch',
    'headset': 'Headset',
    'speaker': 'Speaker',
    'keyboard': 'Keyboard',
    'mouse': 'Mouse',
    'print': 'Printer',
    'camera': 'Camera',
    'videocam': 'Video Camera',
    
    // Travel & Vacation
    'luggage': 'Luggage',
    'hotel': 'Hotel',
    'beach_access': 'Beach',
    'park': 'Park',
    'nature': 'Nature',
    'explore': 'Explore',
    'tour': 'Tour',
    'map': 'Map',
    'travel_explore': 'Travel',
    
    // Miscellaneous
    'category': 'General',
    'folder': 'Category',
    'label': 'Label',
    'sell': 'Sale',
    'new_releases': 'New',
    'star': 'Favorite',
    'grade': 'Premium',
    'workspace_premium': 'Premium',
    'diamond': 'Luxury',
    'emergency': 'Emergency',
    'priority_high': 'Priority',
    'tips_and_updates': 'Tips',
    'lightbulb': 'Idea',
    'eco': 'Eco/Green',
    'recycling': 'Recycling',
    'compost': 'Compost',
    'local_florist': 'Flowers',
    'pets': 'Pets',
    'bug_report': 'Misc'
};

let currentIconTarget = null;

// Helper function to validate and sanitize icon names
function getValidIcon(iconName) {
    // If the icon exists in our CATEGORY_ICONS list, return it
    if (iconName && CATEGORY_ICONS[iconName]) {
        return iconName;
    }
    // If it's a string, try converting to lowercase
    if (iconName && typeof iconName === 'string') {
        const lowerIcon = iconName.toLowerCase();
        if (CATEGORY_ICONS[lowerIcon]) {
            return lowerIcon;
        }
    }
    // Default fallback
    return 'category';
}

// Store selected year globally
let selectedChartYear = new Date().getFullYear();

// Load available years for charts
async function loadAvailableYears() {
    try {
        const data = await apiCall('/api/available-years');
        const selector = document.getElementById('chart-year-selector');
        if (!selector) return;
        
        // Store current year
        const currentYear = data.current_year || new Date().getFullYear();
        
        // Populate dropdown
        selector.innerHTML = data.years.map(year => 
            `<option value="${year}" ${year === currentYear ? 'selected' : ''}>${year}</option>`
        ).join('');
        
        // Set initial year
        selectedChartYear = currentYear;
        
        // Add change listener
        selector.addEventListener('change', (e) => {
            selectedChartYear = parseInt(e.target.value);
            loadChartsForYear(selectedChartYear);
        });
    } catch (error) {
        console.error('Failed to load available years:', error);
    }
}

// Load chart data for a specific year
async function loadChartsForYear(year) {
    try {
        const stats = await apiCall(`/api/dashboard-stats?year=${year}`);
        
        const categoryBreakdown = stats.category_breakdown || [];
        const monthlyData = stats.monthly_data || [];
        
        // Update pie chart year label
        const pieYearLabel = document.getElementById('pie-year-label');
        if (pieYearLabel) {
            const yearText = window.getTranslation ? window.getTranslation('dashboard.totalFor', 'Total for') : 'Total for';
            pieYearLabel.textContent = `${yearText} ${year}`;
        }
        
        // Reload charts with new data
        loadCategoryChart(categoryBreakdown);
        loadMonthlyChart(monthlyData);
        
    } catch (error) {
        console.error('Failed to load chart data:', error);
    }
}

// Load dashboard data
async function loadDashboardData() {
    try {
        // Load available years first
        await loadAvailableYears();
        
        const stats = await apiCall(`/api/dashboard-stats?year=${selectedChartYear}`);
        
        // Store user currency globally for use across functions
        window.userCurrency = stats.currency || 'RON';
        
        // Ensure we have valid data with defaults
        const totalSpent = parseFloat(stats.total_spent || 0);
        const totalIncome = parseFloat(stats.total_income || 0);
        const profitLoss = parseFloat(stats.profit_loss || 0);
        const activeCategories = parseInt(stats.active_categories || 0);
        const totalTransactions = parseInt(stats.total_transactions || 0);
        const categoryBreakdown = stats.category_breakdown || [];
        const monthlyData = stats.monthly_data || [];
        
        // Update KPI cards
        document.getElementById('total-spent').textContent = formatCurrency(totalSpent, window.userCurrency);
        
        // Update income card if exists
        const incomeElement = document.getElementById('total-income');
        if (incomeElement) {
            incomeElement.textContent = formatCurrency(totalIncome, window.userCurrency);
        }
        
        // Update profit/loss card if exists
        const profitElement = document.getElementById('profit-loss');
        if (profitElement) {
            profitElement.textContent = formatCurrency(Math.abs(profitLoss), window.userCurrency);
            const profitCard = profitElement.closest('.bg-white, .dark\\:bg-card-dark');
            if (profitCard) {
                if (profitLoss >= 0) {
                    profitCard.classList.add('border-green-500/20');
                    profitCard.classList.remove('border-red-500/20');
                } else {
                    profitCard.classList.add('border-red-500/20');
                    profitCard.classList.remove('border-green-500/20');
                }
            }
        }
        
        // Update total transactions (active-categories element no longer exists)
        const totalTransactionsEl = document.getElementById('total-transactions');
        if (totalTransactionsEl) {
            totalTransactionsEl.textContent = totalTransactions;
        }
        
        // Update percent change
        const percentChange = document.getElementById('percent-change');
        const percentChangeValue = parseFloat(stats.percent_change || 0);
        const isPositive = percentChangeValue >= 0;
        percentChange.className = `${isPositive ? 'bg-red-500/10 text-red-400' : 'bg-green-500/10 text-green-400'} text-xs font-semibold px-2 py-1 rounded-full flex items-center gap-1`;
        percentChange.innerHTML = `
            <span class="material-symbols-outlined text-[14px]">${isPositive ? 'trending_up' : 'trending_down'}</span>
            ${Math.abs(percentChangeValue).toFixed(1)}%
        `;
        
        // Update pie chart year label
        const pieYearLabel = document.getElementById('pie-year-label');
        if (pieYearLabel) {
            const yearText = window.getTranslation ? window.getTranslation('dashboard.totalFor', 'Total for') : 'Total for';
            pieYearLabel.textContent = `${yearText} ${selectedChartYear}`;
        }
        
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
        pieTotal.textContent = formatCurrency(0);
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

// Monthly bar chart - with income vs expenses comparison
function loadMonthlyChart(data) {
    const ctx = document.getElementById('monthly-chart').getContext('2d');
    
    if (monthlyChart) {
        monthlyChart.destroy();
    }
    
    // Check if we have income data (new format)
    const hasIncome = data.length > 0 && data[0].hasOwnProperty('income');
    
    const datasets = hasIncome ? [
        {
            label: window.getTranslation ? window.getTranslation('nav.income', 'Income') : 'Income',
            data: data.map(d => d.income || 0),
            backgroundColor: '#10b981',
            borderRadius: 6,
            barPercentage: 0.5,
            categoryPercentage: 0.7
        },
        {
            label: window.getTranslation ? window.getTranslation('dashboard.spending', 'Expenses') : 'Expenses',
            data: data.map(d => d.expenses || d.total || 0),
            backgroundColor: '#ef4444',
            borderRadius: 6,
            barPercentage: 0.5,
            categoryPercentage: 0.7
        }
    ] : [{
        label: window.getTranslation ? window.getTranslation('dashboard.spending', 'Spending') : 'Spending',
        data: data.map(d => d.total || d.expenses || 0),
        backgroundColor: '#2b8cee',
        borderRadius: 6,
        barPercentage: 0.5,
        categoryPercentage: 0.7
    }];
    
    monthlyChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: data.map(d => d.month),
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { 
                    display: hasIncome,
                    position: 'top',
                    align: 'end',
                    labels: {
                        color: document.documentElement.classList.contains('dark') ? '#ffffff' : '#1a2632',
                        font: { size: 11 },
                        boxWidth: 12,
                        boxHeight: 12,
                        padding: 10
                    }
                },
                tooltip: {
                    backgroundColor: document.documentElement.classList.contains('dark') ? '#1a2632' : '#ffffff',
                    titleColor: document.documentElement.classList.contains('dark') ? '#ffffff' : '#1a2632',
                    bodyColor: document.documentElement.classList.contains('dark') ? '#92adc9' : '#64748b',
                    borderColor: document.documentElement.classList.contains('dark') ? '#233648' : '#e2e8f0',
                    borderWidth: 1,
                    padding: 12,
                    displayColors: true,
                    callbacks: {
                        label: function(context) {
                            const userCurrency = window.userCurrency || 'RON';
                            return context.dataset.label + ': ' + formatCurrency(context.parsed.y, userCurrency);
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
                        autoSkip: false,
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

    // Ensure totalSpent is a valid number
    const validTotalSpent = parseFloat(totalSpent || 0);

    container.innerHTML = categoryBreakdown.map(cat => {
        const total = parseFloat(cat.total || 0);
        const count = parseInt(cat.count || 0);
        const percentage = validTotalSpent > 0 ? ((total / validTotalSpent) * 100).toFixed(1) : 0;
        const percentageCapped = Math.min(parseFloat(percentage), 100); // Cap at 100% for display
        const icon = getValidIcon(cat.icon); // Validate and sanitize icon from database
        
        // Budget status if available
        let budgetDisplay = '';
        let mainProgressColor = cat.color; // Default to category color
        
        if (cat.budget_status && cat.budget_status.budget) {
            const budgetStatus = cat.budget_status;
            const budgetPercentage = Math.min(budgetStatus.percentage, 100);
            let budgetColor = '#10b981'; // green by default
            
            if (budgetStatus.alert_level === 'warning') {
                budgetColor = '#eab308'; // yellow
                mainProgressColor = '#eab308'; // Update main bar too
            } else if (budgetStatus.alert_level === 'danger') {
                budgetColor = '#f97316'; // orange
                mainProgressColor = '#f97316'; // Update main bar too
            } else if (budgetStatus.alert_level === 'exceeded') {
                budgetColor = '#ef4444'; // red
                mainProgressColor = '#ef4444'; // Update main bar too
            }
            
            budgetDisplay = `
                <div class="mt-3 pt-3 border-t border-border-light dark:border-[#233648]">
                    <div class="flex justify-between items-center mb-2 text-xs">
                        <span class="text-text-muted dark:text-[#92adc9]">${window.getTranslation('budget.budgetAmount', 'Budget')}</span>
                        <span class="font-medium text-text-main dark:text-white">${formatCurrency(budgetStatus.spent, window.userCurrency)} / ${formatCurrency(budgetStatus.budget, window.userCurrency)}</span>
                    </div>
                    <div class="w-full bg-slate-200 dark:bg-[#111a22] rounded-full h-2">
                        <div class="h-2 rounded-full transition-all duration-500" style="width: ${budgetPercentage}%; background: ${budgetColor};"></div>
                    </div>
                    <div class="text-xs text-right mt-1 font-medium" style="color: ${budgetColor}">${budgetStatus.percentage.toFixed(0)}%</div>
                </div>
            `;
        }
        
        return `
            <div class="category-card bg-white dark:bg-[#0f1921] rounded-xl p-5 border border-border-light dark:border-[#233648] hover:border-primary/30 transition-all hover:shadow-lg cursor-pointer touch-manipulation" 
                 draggable="true" 
                 data-category-id="${cat.id}"
                 onclick="event.stopPropagation(); if (!event.target.closest('button')) { showCategoryExpenses(${cat.id}, '${cat.name.replace(/'/g, "\\'")}', '${cat.color}', '${icon}'); }"
                 title="${window.getTranslation('categories.viewExpenses', 'Click to view expenses')}">
                <div class="flex items-start justify-between mb-4">
                    <div class="flex items-center gap-3">
                        <div class="w-12 h-12 rounded-xl flex items-center justify-center" style="background: ${cat.color};">
                            <span class="material-symbols-outlined text-white text-[24px]">${getValidIcon(icon)}</span>
                        </div>
                        <div>
                            <h3 class="font-semibold text-text-main dark:text-white">${cat.name}</h3>
                            <p class="text-xs text-text-muted dark:text-[#92adc9]">${count} ${count === 1 ? (window.getTranslation ? window.getTranslation('transactions.transaction', 'transaction') : 'transaction') : (window.getTranslation ? window.getTranslation('transactions.transactions', 'transactions') : 'transactions')}</p>
                        </div>
                    </div>
                    <div class="flex items-center gap-2">
                        <span class="text-xs font-medium text-text-muted dark:text-[#92adc9] bg-slate-100 dark:bg-[#111a22] px-2 py-1 rounded-full">${percentage}%</span>
                        <button onclick="event.stopPropagation(); showCategoryBudgetModal(${cat.id}, '${cat.name.replace(/'/g, "\\'")}', ${cat.monthly_budget || 'null'}, ${cat.budget_alert_threshold || 0.9})" 
                                class="p-1 hover:bg-slate-100 dark:hover:bg-[#111a22] rounded-lg transition-colors"
                                title="${window.getTranslation('budget.setBudget', 'Set Budget')}">
                            <span class="material-symbols-outlined text-[18px] text-text-muted dark:text-[#92adc9]">settings</span>
                        </button>
                    </div>
                </div>
                <div class="mb-2">
                    <p class="text-2xl font-bold text-text-main dark:text-white">${formatCurrency(total, window.userCurrency || 'RON')}</p>
                </div>
                <div class="w-full bg-slate-200 dark:bg-[#111a22] rounded-full h-2 overflow-hidden">
                    <div class="h-2 rounded-full transition-all duration-500" style="width: ${percentageCapped}%; background: ${mainProgressColor};"></div>
                </div>
                ${budgetDisplay}
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

// Add tag suggestion container after description field
const descInput = document.getElementById('expense-description');
if (descInput && !document.getElementById('tagSuggestionsContainer')) {
    const suggestionsDiv = document.createElement('div');
    suggestionsDiv.id = 'tagSuggestionsContainer';
    suggestionsDiv.className = 'mt-2 hidden';
    suggestionsDiv.innerHTML = `
        <div class="text-xs text-text-muted dark:text-[#92adc9] mb-1">
            <span class="material-symbols-outlined text-[14px] align-middle">lightbulb</span>
            <span data-translate="tags.suggestedTags">Suggested Tags</span>
        </div>
        <div id="suggestedTagsList" class="flex flex-wrap gap-2"></div>
    `;
    descInput.parentElement.appendChild(suggestionsDiv);
    
    // Add event listener for real-time suggestions
    let suggestionTimeout;
    descInput.addEventListener('input', async (e) => {
        clearTimeout(suggestionTimeout);
        const description = e.target.value;
        
        if (description.length < 3) {
            document.getElementById('tagSuggestionsContainer').classList.add('hidden');
            return;
        }
        
        suggestionTimeout = setTimeout(async () => {
            try {
                const categoryId = categorySelect.value;
                const response = await apiCall('/api/expenses/suggest-tags', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ description, category_id: categoryId })
                });
                
                if (response.success && response.suggested_tags.length > 0) {
                    const container = document.getElementById('tagSuggestionsContainer');
                    const list = document.getElementById('suggestedTagsList');
                    list.innerHTML = '';
                    
                    response.suggested_tags.forEach(tag => {
                        const badge = document.createElement('span');
                        badge.className = 'inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs cursor-pointer transition-all hover:brightness-110';
                        badge.style.backgroundColor = `${tag.color}20`;
                        badge.style.borderColor = `${tag.color}40`;
                        badge.style.color = tag.color;
                        badge.classList.add('border');
                        badge.innerHTML = `
                            <span class="material-symbols-outlined" style="font-size: 14px;">${tag.icon}</span>
                            <span>#${tag.name}</span>
                        `;
                        badge.addEventListener('click', () => {
                            // Add to tags field
                            const tagsInput = document.getElementById('expense-tags');
                            const currentTags = tagsInput.value.split(',').map(t => t.trim()).filter(t => t);
                            if (!currentTags.includes(tag.name)) {
                                currentTags.push(tag.name);
                                tagsInput.value = currentTags.join(', ');
                            }
                            badge.style.opacity = '0.5';
                        });
                        list.appendChild(badge);
                    });
                    
                    container.classList.remove('hidden');
                }
            } catch (error) {
                console.error('Failed to get tag suggestions:', error);
            }
        }, 500);
    });
}

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
            document.getElementById('tagSuggestionsContainer')?.classList.add('hidden');
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
            <div class="flex items-center gap-3 flex-1">
                <span class="material-symbols-outlined text-[24px] drag-handle cursor-move" style="color: ${cat.color};">drag_indicator</span>
                <button type="button" onclick="openIconPicker('edit-${cat.id}')" 
                        class="w-10 h-10 rounded-lg flex items-center justify-center hover:opacity-80 transition-opacity" 
                        style="background: ${cat.color};"
                        title="Click to change icon">
                    <span class="material-symbols-outlined text-white text-[20px]">${getValidIcon(cat.icon)}</span>
                </button>
                <div class="flex-1">
                    <p class="text-text-main dark:text-white font-medium">${cat.name}</p>
                    <p class="text-text-muted dark:text-[#92adc9] text-xs">${cat.color} • ${CATEGORY_ICONS[getValidIcon(cat.icon)] || 'General'}</p>
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

// Show category budget settings modal
function showCategoryBudgetModal(categoryId, categoryName, currentBudget, currentThreshold) {
    const modal = document.createElement('div');
    modal.id = 'categoryBudgetModal';
    modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
    
    // Handle null/undefined values properly
    const budgetValue = currentBudget && currentBudget !== 'null' ? parseFloat(currentBudget) : '';
    const threshold = currentThreshold && currentThreshold !== 'null' ? parseFloat(currentThreshold) : 0.9;
    const thresholdPercent = (threshold * 100).toFixed(0);
    
    modal.innerHTML = `
        <div class="bg-white dark:bg-[#0f1921] rounded-lg shadow-xl max-w-md w-full">
            <div class="p-6 border-b border-border-light dark:border-[#233648]">
                <div class="flex justify-between items-center">
                    <h2 class="text-2xl font-bold text-text-main dark:text-white">${categoryName}</h2>
                    <button onclick="document.getElementById('categoryBudgetModal').remove()" class="text-text-muted dark:text-[#92adc9] hover:text-text-main dark:hover:text-white">
                        <span class="material-symbols-outlined">close</span>
                    </button>
                </div>
                <p class="text-sm text-text-muted dark:text-[#92adc9] mt-2">${window.getTranslation('budget.editBudget', 'Edit Budget')}</p>
            </div>
            <form id="budgetForm" class="p-6 space-y-4">
                <div>
                    <label class="block text-sm font-medium text-text-main dark:text-white mb-2">
                        ${window.getTranslation('budget.budgetAmount', 'Budget Amount')}
                    </label>
                    <input type="number" 
                           id="budgetAmount" 
                           step="0.01" 
                           min="0"
                           value="${budgetValue}"
                           placeholder="0.00"
                           class="w-full px-4 py-2 border border-border-light dark:border-[#233648] rounded-lg bg-white dark:bg-[#111a22] text-text-main dark:text-white focus:ring-2 focus:ring-primary/50">
                </div>
                <div>
                    <label class="block text-sm font-medium text-text-main dark:text-white mb-2">
                        ${window.getTranslation('budget.alertThreshold', 'Alert Threshold')} (${thresholdPercent}%)
                    </label>
                    <input type="range" 
                           id="budgetThreshold" 
                           min="50" 
                           max="200" 
                           value="${thresholdPercent}"
                           oninput="document.getElementById('thresholdValue').textContent = this.value + '%'"
                           class="w-full">
                    <div class="flex justify-between text-xs text-text-muted dark:text-[#92adc9] mt-2">
                        <span>50%</span>
                        <span id="thresholdValue" class="font-semibold text-text-main dark:text-white">${thresholdPercent}%</span>
                        <span>200%</span>
                    </div>
                    <p class="text-xs text-text-muted dark:text-[#92adc9] mt-2">${window.getTranslation('budget.alertThresholdHelp', 'Get notified when spending reaches this percentage')}</p>
                </div>
                <div class="flex gap-3 pt-4">
                    <button type="button" 
                            onclick="document.getElementById('categoryBudgetModal').remove()"
                            class="flex-1 px-4 py-2 border border-border-light dark:border-[#233648] rounded-lg text-text-main dark:text-white hover:bg-slate-100 dark:hover:bg-[#111a22]">
                        ${window.getTranslation('budget.cancel', 'Cancel')}
                    </button>
                    <button type="submit"
                            class="flex-1 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90">
                        ${window.getTranslation('budget.save', 'Save Budget')}
                    </button>
                </div>
            </form>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close on backdrop click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.remove();
        }
    });
    
    // Handle form submission
    document.getElementById('budgetForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const budgetAmount = parseFloat(document.getElementById('budgetAmount').value) || null;
        const thresholdValue = parseFloat(document.getElementById('budgetThreshold').value) / 100;
        
        try {
            await apiCall(`/api/budget/category/${categoryId}/budget`, {
                method: 'PUT',
                body: JSON.stringify({
                    monthly_budget: budgetAmount,
                    budget_alert_threshold: thresholdValue
                })
            });
            
            showToast(window.getTranslation('budget.budgetUpdated', 'Budget updated successfully'), 'success');
            modal.remove();
            
            // Reload dashboard to show updated budget
            loadDashboardData();
            
            // Refresh budget status
            if (window.budgetDashboard) {
                window.budgetDashboard.loadBudgetStatus();
            }
        } catch (error) {
            console.error('Failed to update budget:', error);
            showToast(window.getTranslation('budget.budgetError', 'Failed to update budget'), 'error');
        }
    });
}

// Delete category
async function deleteCategory(id) {
    try {
        // Try to delete without reassignment first
        const result = await apiCall(`/api/expenses/categories/${id}`, {
            method: 'DELETE'
        });
        
        if (result.success) {
            showToast(getTranslation('categories.deleted', 'Category deleted successfully'), 'success');
            await loadCategoriesManagement();
            await loadDashboardData();
        }
    } catch (error) {
        console.error('Failed to delete category:', error);
        
        // If category has expenses, show reassignment options
        if (error.expense_count && error.requires_reassignment) {
            const category = allCategories.find(c => c.id === id);
            const otherCategories = allCategories.filter(c => c.id !== id);
            
            if (otherCategories.length === 0) {
                showToast('Cannot delete the only category with expenses', 'error');
                return;
            }
            
            // Create options for select
            const options = otherCategories.map(cat => 
                `<option value="${cat.id}">${cat.name}</option>`
            ).join('');
            
            // Create custom confirmation dialog with category selection
            const dialog = document.createElement('div');
            dialog.className = 'fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4';
            dialog.innerHTML = `
                <div class="bg-card-light dark:bg-card-dark rounded-2xl shadow-2xl max-w-md w-full border border-border-light dark:border-[#233648]">
                    <div class="p-6">
                        <div class="flex items-center gap-3 mb-4">
                            <div class="p-2 bg-red-500/10 rounded-lg">
                                <span class="material-symbols-outlined text-red-500">warning</span>
                            </div>
                            <h3 class="text-lg font-bold text-text-main dark:text-white">Delete Category</h3>
                        </div>
                        
                        <p class="text-text-muted dark:text-[#92adc9] mb-4">
                            This category has ${error.expense_count} expense${error.expense_count > 1 ? 's' : ''}. 
                            Where would you like to move ${error.expense_count > 1 ? 'them' : 'it'}?
                        </p>
                        
                        <div class="mb-4">
                            <label class="block text-sm font-medium text-text-main dark:text-white mb-2">Move expenses to:</label>
                            <select id="move-to-category-select" 
                                    class="w-full px-3 py-2 bg-white dark:bg-card-dark border border-border-light dark:border-[#233648] rounded-lg text-text-main dark:text-white text-sm focus:outline-none focus:ring-2 focus:ring-primary">
                                <option value="">Select category...</option>
                                ${options}
                            </select>
                        </div>

                        <div class="flex gap-3 justify-end">
                            <button id="cancel-delete-btn" 
                                    class="px-4 py-2 bg-background-light dark:bg-background-dark text-text-main dark:text-white rounded-lg hover:bg-slate-200 dark:hover:bg-[#233648] transition-colors font-medium text-sm">
                                Cancel
                            </button>
                            <button id="confirm-delete-btn" 
                                    class="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors font-medium text-sm">
                                Delete
                            </button>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.appendChild(dialog);
            
            // Handle cancel
            dialog.querySelector('#cancel-delete-btn').addEventListener('click', () => {
                document.body.removeChild(dialog);
            });
            
            // Handle confirm
            dialog.querySelector('#confirm-delete-btn').addEventListener('click', async () => {
                const moveToId = dialog.querySelector('#move-to-category-select').value;
                
                if (!moveToId) {
                    showToast('Please select a category to move expenses to', 'error');
                    return;
                }
                
                try {
                    const deleteResult = await apiCall(`/api/expenses/categories/${id}`, {
                        method: 'DELETE',
                        body: JSON.stringify({ move_to_category_id: parseInt(moveToId) })
                    });
                    
                    if (deleteResult.success) {
                        showToast(`Category deleted and ${deleteResult.expenses_moved} expense${deleteResult.expenses_moved > 1 ? 's' : ''} moved`, 'success');
                        document.body.removeChild(dialog);
                        await loadCategoriesManagement();
                        await loadDashboardData();
                    }
                } catch (deleteError) {
                    console.error('Failed to delete category:', deleteError);
                    showToast(deleteError.message || 'Failed to delete category', 'error');
                }
            });
            
        } else {
            showToast(error.message || getTranslation('common.error', 'An error occurred'), 'error');
        }
    }
}

// Make deleteCategory global
window.deleteCategory = deleteCategory;

// ============== Icon Picker Functions ==============

// Open icon picker modal
function openIconPicker(target) {
    currentIconTarget = target;
    const modal = document.getElementById('icon-picker-modal');
    modal.classList.remove('hidden');
    
    // Populate icon grid
    renderIconGrid();
    
    // Setup search
    const searchInput = document.getElementById('icon-search');
    searchInput.value = '';
    searchInput.focus();
    searchInput.addEventListener('input', filterIcons);
}

// Close icon picker modal
function closeIconPicker() {
    const modal = document.getElementById('icon-picker-modal');
    modal.classList.add('hidden');
    currentIconTarget = null;
    
    const searchInput = document.getElementById('icon-search');
    searchInput.removeEventListener('input', filterIcons);
}

// Render icon grid
function renderIconGrid(filter = '') {
    const grid = document.getElementById('icon-grid');
    const icons = Object.entries(CATEGORY_ICONS);
    
    // Sort icons alphabetically by label
    const sortedIcons = icons.sort((a, b) => a[1].localeCompare(b[1]));
    
    const filteredIcons = filter 
        ? sortedIcons.filter(([icon, label]) => 
            icon.toLowerCase().includes(filter.toLowerCase()) || 
            label.toLowerCase().includes(filter.toLowerCase())
          )
        : sortedIcons;
    
    grid.innerHTML = filteredIcons.map(([icon, label]) => `
        <button type="button" 
                onclick="selectIcon('${icon}')" 
                class="flex flex-col items-center justify-center p-2 rounded-lg border border-border-light dark:border-[#233648] hover:border-primary hover:bg-primary/5 transition-all group min-h-[60px]"
                title="${label}">
            <span class="material-symbols-outlined text-text-main dark:text-white">${icon}</span>
            <span class="text-[8px] text-text-muted dark:text-[#92adc9] text-center leading-tight mt-1 max-w-full overflow-hidden text-ellipsis whitespace-nowrap px-1">${label}</span>
        </button>
    `).join('');
}

// Filter icons based on search
function filterIcons(e) {
    renderIconGrid(e.target.value);
}

// Select icon
function selectIcon(iconName) {
    if (!currentIconTarget) return;
    
    // Update add form
    if (currentIconTarget === 'add-form') {
        document.querySelector('#add-category-form input[name="icon"]').value = iconName;
        document.getElementById('add-form-icon-preview').textContent = iconName;
        document.getElementById('add-form-icon-name').textContent = CATEGORY_ICONS[iconName] || iconName;
    }
    // Update edit in category list (dynamic)
    else if (currentIconTarget.startsWith('edit-')) {
        const categoryId = currentIconTarget.replace('edit-', '');
        updateCategoryIcon(categoryId, iconName);
    }
    
    closeIconPicker();
}

// Update category icon (inline edit)
async function updateCategoryIcon(categoryId, iconName) {
    try {
        await apiCall(`/api/expenses/categories/${categoryId}`, {
            method: 'PUT',
            body: JSON.stringify({ icon: iconName })
        });
        
        showToast('Icon updated successfully', 'success');
        await loadCategoriesManagement();
        await loadDashboardData();
    } catch (error) {
        console.error('Failed to update icon:', error);
        showToast('Failed to update icon', 'error');
    }
}

// Make icon picker functions global
window.openIconPicker = openIconPicker;
window.closeIconPicker = closeIconPicker;
window.selectIcon = selectIcon;
window.updateCategoryIcon = updateCategoryIcon;

// ============== Category Expenses Modal ==============

// Show category expenses modal
async function showCategoryExpenses(categoryId, categoryName, categoryColor, categoryIcon) {
    const modal = document.getElementById('category-expenses-modal');
    const iconContainer = document.getElementById('modal-category-icon-container');
    const icon = document.getElementById('modal-category-icon');
    const name = document.getElementById('modal-category-name');
    const count = document.getElementById('modal-category-count');
    const list = document.getElementById('modal-expenses-list');
    const empty = document.getElementById('modal-expenses-empty');
    const loading = document.getElementById('modal-expenses-loading');
    
    // Set category info
    iconContainer.style.background = categoryColor;
    icon.textContent = getValidIcon(categoryIcon);
    name.textContent = categoryName;
    
    // Show modal and loading
    modal.classList.remove('hidden');
    list.classList.add('hidden');
    empty.classList.add('hidden');
    loading.classList.remove('hidden');
    
    try {
        // Fetch expenses for this category
        const data = await apiCall(`/api/expenses/?category_id=${categoryId}&per_page=100`);
        
        loading.classList.add('hidden');
        
        if (!data.expenses || data.expenses.length === 0) {
            empty.classList.remove('hidden');
            count.textContent = window.getTranslation('categories.noExpenses', 'No expenses in this category');
            return;
        }
        
        // Update count
        const total = data.total || data.expenses.length;
        count.textContent = `${total} ${total === 1 ? (window.getTranslation('transactions.transaction', 'transaction')) : (window.getTranslation('transactions.transactions', 'transactions'))}`;
        
        // Render expenses
        list.innerHTML = data.expenses.map(exp => {
            const expDate = new Date(exp.date);
            const formattedDate = formatDate(exp.date);
            
            return `
                <div class="flex items-center justify-between p-4 rounded-lg bg-slate-50 dark:bg-[#111a22] border border-border-light dark:border-[#233648] hover:border-primary/30 transition-colors">
                    <div class="flex items-center gap-3 flex-1">
                        <div class="w-10 h-10 rounded-lg flex items-center justify-center" style="background: ${categoryColor}20;">
                            <span class="material-symbols-outlined text-[20px]" style="color: ${categoryColor};">${getValidIcon(categoryIcon)}</span>
                        </div>
                        <div class="flex-1">
                            <p class="text-text-main dark:text-white font-medium text-sm">${exp.description}</p>
                            <div class="flex items-center gap-2 mt-1">
                                <p class="text-text-muted dark:text-[#92adc9] text-xs">${formattedDate}</p>
                                ${exp.tags && exp.tags.length > 0 ? `
                                    <span class="text-text-muted dark:text-[#92adc9] text-xs">•</span>
                                    <div class="flex gap-1 flex-wrap">
                                        ${exp.tags.map(tag => `<span class="px-1.5 py-0.5 bg-primary/10 text-primary text-[10px] rounded">${tag}</span>`).join('')}
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                    <div class="text-right ml-3">
                        <p class="text-text-main dark:text-white font-semibold whitespace-nowrap">${formatCurrency(exp.amount, exp.currency || window.userCurrency)}</p>
                        ${exp.receipt_path ? `<span class="material-symbols-outlined text-[16px] text-text-muted dark:text-[#92adc9]" title="Has receipt">receipt</span>` : ''}
                    </div>
                </div>
            `;
        }).join('');
        
        list.classList.remove('hidden');
        
    } catch (error) {
        console.error('Failed to load category expenses:', error);
        loading.classList.add('hidden');
        list.innerHTML = `
            <div class="text-center py-12">
                <span class="material-symbols-outlined text-[48px] text-red-500 mb-3">error</span>
                <p class="text-text-muted dark:text-[#92adc9]">${window.getTranslation('common.error', 'Failed to load expenses')}</p>
            </div>
        `;
        list.classList.remove('hidden');
    }
}

// Close category expenses modal
function closeCategoryExpensesModal() {
    const modal = document.getElementById('category-expenses-modal');
    modal.classList.add('hidden');
}

// Make functions global
window.showCategoryExpenses = showCategoryExpenses;
window.closeCategoryExpensesModal = closeCategoryExpensesModal;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', () => {
    loadDashboardData();
    
    // Refresh data every 5 minutes
    setInterval(loadDashboardData, 5 * 60 * 1000);
});

