/**
 * Challenges & Gamification JavaScript
 * Handles no-spend days, 52-week challenge, achievements, and leaderboard
 */

// State
let userStats = null;
let achievements = [];
let week52Data = null;
let calendarYear = new Date().getFullYear();
let calendarMonth = new Date().getMonth() + 1;
let newAchievements = [];

// Tips for rotation
const TIPS = [
    'challenges.tips.noSpend',
    'challenges.tips.week52',
    'challenges.tips.streak',
    'challenges.tips.save',
    'challenges.tips.track'
];

/**
 * Initialize the page
 */
document.addEventListener('DOMContentLoaded', function() {
    initTabs();
    loadAllData();
    rotateTip();
});

/**
 * Helper function for translations - use window.getTranslation to avoid shadowing
 */
function tr(key, fallback) {
    if (typeof window.getTranslation === 'function') {
        return window.getTranslation(key, fallback);
    }
    return fallback || key;
}

/**
 * Format currency based on user settings
 */
function formatCurrency(amount, currency = null) {
    const curr = currency || (window.userCurrency || 'RON');
    return new Intl.NumberFormat('en-GB', {
        style: 'currency',
        currency: curr,
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

/**
 * Show toast notification
 */
function showToast(message, type = 'success') {
    // Check if toast container exists
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'fixed top-4 right-4 z-50 flex flex-col gap-2';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `px-4 py-3 rounded-lg shadow-lg flex items-center gap-2 transform translate-x-full transition-transform duration-300 ${
        type === 'success' ? 'bg-emerald-500 text-white' :
        type === 'error' ? 'bg-red-500 text-white' :
        'bg-blue-500 text-white'
    }`;
    
    const icon = type === 'success' ? 'check_circle' : type === 'error' ? 'error' : 'info';
    toast.innerHTML = `
        <span class="material-symbols-outlined text-lg">${icon}</span>
        <span class="text-sm font-medium">${message}</span>
    `;
    
    container.appendChild(toast);
    
    // Animate in
    requestAnimationFrame(() => {
        toast.classList.remove('translate-x-full');
    });
    
    // Remove after 3 seconds
    setTimeout(() => {
        toast.classList.add('translate-x-full');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/**
 * Initialize tab functionality
 */
function initTabs() {
    const tabs = document.querySelectorAll('.tab-btn');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active state from all tabs
            tabs.forEach(t => {
                t.classList.remove('active', 'bg-white', 'dark:bg-card-dark');
                t.classList.add('text-text-muted', 'dark:text-[#92adc9]');
            });
            
            // Add active state to clicked tab
            tab.classList.add('active', 'bg-white', 'dark:bg-card-dark');
            tab.classList.remove('text-text-muted', 'dark:text-[#92adc9]');
            
            // Hide all tab content
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.add('hidden');
            });
            
            // Show selected tab content
            const tabId = tab.dataset.tab;
            const content = document.getElementById(`tab-${tabId}`);
            if (content) {
                content.classList.remove('hidden');
            }
        });
    });
}

/**
 * Load all data
 */
async function loadAllData() {
    await Promise.all([
        loadStats(),
        loadTodayNoSpend(),
        loadCalendar(),
        load52WeekChallenge(),
        loadAchievements(),
        loadLeaderboard()
    ]);
    
    // Check for new achievements to display
    checkNewAchievements();
}

/**
 * Load user stats
 */
async function loadStats() {
    try {
        const response = await fetch('/api/challenges/stats');
        const data = await response.json();
        
        if (data.success) {
            userStats = data.stats;
            newAchievements = data.new_achievements || [];
            
            // Update UI
            document.getElementById('user-level').textContent = userStats.level;
            document.getElementById('total-points').textContent = userStats.total_points.toLocaleString();
            document.getElementById('points-to-next').textContent = `${data.points_to_next_level} pts`;
            document.getElementById('level-progress').style.width = `${data.level_progress}%`;
            document.getElementById('no-spend-streak').textContent = userStats.current_no_spend_streak;
            document.getElementById('best-no-spend-streak').textContent = userStats.best_no_spend_streak;
            document.getElementById('week-52-progress').textContent = userStats.week_52_progress;
            
            if (userStats.week_52_total_saved > 0) {
                document.getElementById('week-52-saved').textContent = 
                    `${tr('challenges.saved', 'Saved')}: ${formatCurrency(userStats.week_52_total_saved)}`;
            }
            
            // Animate streak fire if active
            if (userStats.current_no_spend_streak >= 3) {
                document.getElementById('streak-icon').classList.add('fire-animation');
            }
            
            // Render recent achievements
            renderRecentAchievements(data.recent_achievements || []);
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

/**
 * Load today's no-spend status
 */
async function loadTodayNoSpend() {
    try {
        const response = await fetch('/api/challenges/no-spend/today');
        const data = await response.json();
        
        if (data.success) {
            const statusText = document.getElementById('today-status-text');
            const spentAmount = document.getElementById('today-spent-amount');
            const intentionalBtn = document.getElementById('set-intentional-btn');
            
            if (data.is_no_spend_day) {
                statusText.textContent = tr('challenges.noSpendSoFar', 'No spending so far!');
                statusText.className = 'text-2xl font-bold text-emerald-500';
                spentAmount.textContent = '';
                
                if (data.is_intentional) {
                    intentionalBtn.textContent = tr('challenges.intentionalSet', 'Intentional day set ✓');
                    intentionalBtn.disabled = true;
                    intentionalBtn.classList.add('opacity-50');
                }
            } else {
                statusText.textContent = tr('challenges.spentToday', 'Spent today');
                statusText.className = 'text-2xl font-bold text-red-500';
                spentAmount.textContent = `${formatCurrency(data.amount_spent)} (${data.expense_count} ${tr('challenges.expenses', 'expenses')})`;
                intentionalBtn.classList.add('hidden');
            }
        }
    } catch (error) {
        console.error('Error loading today status:', error);
    }
}

/**
 * Set today as intentional no-spend day
 */
async function setIntentionalNoSpend() {
    try {
        const response = await fetch('/api/challenges/no-spend/set-intentional', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
            },
            body: JSON.stringify({})
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(tr('challenges.intentionalSuccess', 'Today marked as intentional no-spend day!'));
            loadTodayNoSpend();
        } else {
            showToast(data.error || 'Error', 'error');
        }
    } catch (error) {
        console.error('Error setting intentional:', error);
        showToast('Error setting intentional day', 'error');
    }
}

/**
 * Load calendar data
 */
async function loadCalendar() {
    try {
        const response = await fetch(`/api/challenges/no-spend/calendar?year=${calendarYear}&month=${calendarMonth}`);
        const data = await response.json();
        
        if (data.success) {
            renderCalendar(data);
        }
    } catch (error) {
        console.error('Error loading calendar:', error);
    }
}

/**
 * Render calendar
 */
function renderCalendar(data) {
    const monthNames = ['January', 'February', 'March', 'April', 'May', 'June',
                       'July', 'August', 'September', 'October', 'November', 'December'];
    
    document.getElementById('calendar-month').textContent = `${monthNames[data.month - 1]} ${data.year}`;
    
    const grid = document.getElementById('calendar-grid');
    grid.innerHTML = '';
    
    // Add empty cells for days before the first day of month
    const firstDay = data.calendar[0];
    for (let i = 0; i < firstDay.weekday; i++) {
        const emptyCell = document.createElement('div');
        emptyCell.className = 'aspect-square';
        grid.appendChild(emptyCell);
    }
    
    // Add day cells
    data.calendar.forEach(day => {
        const cell = document.createElement('div');
        cell.className = 'aspect-square rounded-lg flex items-center justify-center text-sm font-medium cursor-pointer calendar-day';
        
        if (day.is_future) {
            cell.className += ' bg-gray-100 dark:bg-[#1a2b3c] text-text-muted dark:text-[#5f7a96]';
        } else if (day.status === 'success') {
            cell.className += ' success text-white';
            if (day.is_intentional) {
                cell.className += ' ring-2 ring-amber-500 ring-offset-2 dark:ring-offset-[#111a22]';
            }
        } else if (day.status === 'failed') {
            cell.className += ' failed text-white';
        } else {
            cell.className += ' pending text-white';
        }
        
        cell.textContent = day.day;
        cell.title = day.is_no_spend ? 
            tr('challenges.noSpendDay', 'No-spend day') : 
            `${formatCurrency(day.amount_spent)}`;
        
        grid.appendChild(cell);
    });
}

/**
 * Change calendar month
 */
function changeMonth(delta) {
    calendarMonth += delta;
    
    if (calendarMonth < 1) {
        calendarMonth = 12;
        calendarYear--;
    } else if (calendarMonth > 12) {
        calendarMonth = 1;
        calendarYear++;
    }
    
    loadCalendar();
}

/**
 * Load 52-week challenge
 */
async function load52WeekChallenge() {
    try {
        const response = await fetch('/api/challenges/52-week');
        const data = await response.json();
        
        if (data.success) {
            week52Data = data;
            
            if (data.active) {
                document.getElementById('week-52-inactive').classList.add('hidden');
                document.getElementById('week-52-active').classList.remove('hidden');
                render52WeekProgress(data);
            } else {
                document.getElementById('week-52-inactive').classList.remove('hidden');
                document.getElementById('week-52-active').classList.add('hidden');
            }
        }
    } catch (error) {
        console.error('Error loading 52-week challenge:', error);
    }
}

/**
 * Render 52-week challenge progress
 */
function render52WeekProgress(data) {
    const config = data.challenge.config || {};
    const currency = config.currency || 'RON';
    
    document.getElementById('week52-current-week').textContent = data.current_week;
    document.getElementById('week52-total-saved').textContent = formatCurrency(data.total_saved, currency);
    document.getElementById('week52-expected').textContent = formatCurrency(data.total_expected, currency);
    document.getElementById('week52-final-goal').textContent = formatCurrency(data.final_total, currency);
    
    // This week's target
    const thisWeek = data.weeks[data.current_week - 1];
    if (thisWeek) {
        document.getElementById('week52-this-week-target').textContent = formatCurrency(thisWeek.expected, currency);
        document.getElementById('week52-save-amount').value = thisWeek.expected;
    }
    
    // Render week grid
    const grid = document.getElementById('week52-grid');
    grid.innerHTML = '';
    
    data.weeks.forEach(week => {
        const cell = document.createElement('div');
        cell.className = 'aspect-square rounded flex items-center justify-center text-xs font-medium cursor-pointer transition-all';
        
        if (week.completed) {
            cell.className += ' bg-emerald-500 text-white';
        } else if (week.week < data.current_week) {
            cell.className += ' bg-red-500/20 text-red-500 border border-red-500/30';
        } else if (week.week === data.current_week) {
            cell.className += ' bg-blue-500 text-white ring-2 ring-blue-300';
        } else {
            cell.className += ' bg-gray-100 dark:bg-[#1a2b3c] text-text-muted dark:text-[#5f7a96]';
        }
        
        cell.textContent = week.week;
        cell.title = `Week ${week.week}: ${formatCurrency(week.expected, currency)} (${week.completed ? 'Completed' : 'Pending'})`;
        
        grid.appendChild(cell);
    });
}

/**
 * Start 52-week challenge
 */
async function startWeek52Challenge() {
    const baseAmount = parseFloat(document.getElementById('week52-base').value) || 1;
    const increment = parseFloat(document.getElementById('week52-increment').value) || 1;
    const reverse = document.getElementById('week52-reverse').checked;
    
    try {
        const response = await fetch('/api/challenges/52-week/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
            },
            body: JSON.stringify({
                base_amount: baseAmount,
                increment: increment,
                reverse: reverse
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(tr('challenges.week52.started', '52-week challenge started! Good luck!'));
            load52WeekChallenge();
            loadStats();
        } else {
            showToast(data.error || 'Error starting challenge', 'error');
        }
    } catch (error) {
        console.error('Error starting challenge:', error);
        showToast('Error starting challenge', 'error');
    }
}

/**
 * Save for current week
 */
async function saveForWeek() {
    const amount = parseFloat(document.getElementById('week52-save-amount').value) || 0;
    
    if (amount <= 0) {
        showToast(tr('challenges.enterAmount', 'Please enter an amount'), 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/challenges/52-week/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
            },
            body: JSON.stringify({
                amount: amount
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(tr('challenges.savedSuccess', `Saved ${formatCurrency(amount)}!`));
            load52WeekChallenge();
            loadStats();
            checkNewAchievements();
        } else {
            showToast(data.error || 'Error saving', 'error');
        }
    } catch (error) {
        console.error('Error saving:', error);
        showToast('Error saving', 'error');
    }
}

/**
 * Reset 52-week challenge
 */
async function resetWeek52Challenge() {
    if (!confirm(tr('challenges.confirmReset', 'Are you sure you want to reset the 52-week challenge? All progress will be lost.'))) {
        return;
    }
    
    try {
        const response = await fetch('/api/challenges/52-week/reset', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
            }
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(tr('challenges.resetSuccess', 'Challenge reset'));
            load52WeekChallenge();
            loadStats();
        } else {
            showToast(data.error || 'Error resetting', 'error');
        }
    } catch (error) {
        console.error('Error resetting:', error);
        showToast('Error resetting challenge', 'error');
    }
}

/**
 * Load achievements
 */
async function loadAchievements() {
    try {
        const response = await fetch('/api/challenges/achievements');
        const data = await response.json();
        
        if (data.success) {
            achievements = data.achievements;
            document.getElementById('achievements-earned').textContent = data.total_earned;
            document.getElementById('achievements-total').textContent = data.total_available;
            renderAchievements();
        }
    } catch (error) {
        console.error('Error loading achievements:', error);
    }
}

/**
 * Render achievements grid
 */
function renderAchievements() {
    const grid = document.getElementById('achievements-grid');
    grid.innerHTML = '';
    
    achievements.forEach(achievement => {
        const card = document.createElement('div');
        card.className = `p-4 rounded-xl border-2 ${achievement.is_completed ? `rarity-${achievement.rarity}` : 'border-gray-200 dark:border-[#233648]'} ${achievement.is_completed ? '' : 'opacity-60'}`;
        
        const rarityColors = {
            common: '#6b7280',
            uncommon: '#10b981',
            rare: '#3b82f6',
            epic: '#8b5cf6',
            legendary: '#f59e0b'
        };
        
        card.innerHTML = `
            <div class="flex items-start gap-3">
                <div class="w-12 h-12 rounded-full flex items-center justify-center ${achievement.is_completed ? '' : 'grayscale'}" style="background-color: ${achievement.badge_color}20;">
                    <span class="material-symbols-outlined text-2xl" style="color: ${achievement.badge_color}">${achievement.icon}</span>
                </div>
                <div class="flex-1 min-w-0">
                    <h4 class="font-semibold text-text-main dark:text-white text-sm" data-translate="${achievement.title_key}">
                        ${tr(achievement.title_key, achievement.code)}
                    </h4>
                    <p class="text-xs text-text-muted dark:text-[#92adc9] mt-0.5" data-translate="${achievement.description_key}">
                        ${tr(achievement.description_key, '')}
                    </p>
                    <div class="flex items-center gap-3 mt-2">
                        <span class="text-xs font-medium px-2 py-0.5 rounded-full" style="background-color: ${rarityColors[achievement.rarity]}20; color: ${rarityColors[achievement.rarity]}">
                            ${achievement.rarity}
                        </span>
                        <span class="text-xs text-amber-500 font-medium">+${achievement.points} pts</span>
                    </div>
                    ${!achievement.is_completed && achievement.target_progress > 1 ? `
                        <div class="mt-2">
                            <div class="flex justify-between text-xs text-text-muted dark:text-[#92adc9] mb-1">
                                <span>${tr('challenges.progress', 'Progress')}</span>
                                <span>${achievement.current_progress}/${achievement.target_progress}</span>
                            </div>
                            <div class="w-full bg-gray-200 dark:bg-[#233648] rounded-full h-1.5">
                                <div class="h-1.5 rounded-full" style="width: ${achievement.progress_percentage}%; background-color: ${achievement.badge_color}"></div>
                            </div>
                        </div>
                    ` : ''}
                    ${achievement.is_completed && achievement.completed_at ? `
                        <p class="text-xs text-emerald-500 mt-2">
                            ✓ ${new Date(achievement.completed_at).toLocaleDateString()}
                        </p>
                    ` : ''}
                </div>
            </div>
        `;
        
        grid.appendChild(card);
    });
}

/**
 * Render recent achievements in sidebar
 */
function renderRecentAchievements(recentAchievements) {
    const container = document.getElementById('recent-achievements');
    
    if (!recentAchievements || recentAchievements.length === 0) {
        container.innerHTML = `<p class="text-sm text-text-muted dark:text-[#92adc9] text-center py-4" data-translate="challenges.noRecentAchievements">No achievements yet</p>`;
        return;
    }
    
    container.innerHTML = '';
    
    recentAchievements.slice(0, 3).forEach(achievement => {
        const item = document.createElement('div');
        item.className = 'flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 dark:hover:bg-[#233648] transition-colors';
        
        item.innerHTML = `
            <div class="w-10 h-10 rounded-full flex items-center justify-center" style="background-color: ${achievement.badge_color}20;">
                <span class="material-symbols-outlined" style="color: ${achievement.badge_color}">${achievement.icon}</span>
            </div>
            <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-text-main dark:text-white truncate" data-translate="${achievement.title_key}">
                    ${tr(achievement.title_key, achievement.code)}
                </p>
                <p class="text-xs text-text-muted dark:text-[#92adc9]">+${achievement.points} pts</p>
            </div>
        `;
        
        container.appendChild(item);
    });
}

/**
 * Load leaderboard
 */
async function loadLeaderboard() {
    try {
        const response = await fetch('/api/challenges/leaderboard');
        const data = await response.json();
        
        if (data.success) {
            renderLeaderboard(data);
        }
    } catch (error) {
        console.error('Error loading leaderboard:', error);
    }
}

/**
 * Render leaderboard
 */
function renderLeaderboard(data) {
    const list = document.getElementById('leaderboard-list');
    list.innerHTML = '';
    
    if (!data.leaderboard || data.leaderboard.length === 0) {
        list.innerHTML = `<p class="text-sm text-text-muted dark:text-[#92adc9] text-center py-8">No data yet</p>`;
        return;
    }
    
    data.leaderboard.forEach(entry => {
        const row = document.createElement('div');
        row.className = `flex items-center gap-4 p-4 rounded-xl ${entry.is_current_user ? 'bg-primary/10 border border-primary/20' : 'bg-gray-50 dark:bg-[#1a2b3c]'}`;
        
        const rankColors = {
            1: 'text-amber-500',
            2: 'text-slate-400',
            3: 'text-amber-600'
        };
        
        row.innerHTML = `
            <div class="w-8 h-8 flex items-center justify-center font-bold ${rankColors[entry.rank] || 'text-text-muted dark:text-[#92adc9]'}">
                ${entry.rank <= 3 ? `<span class="material-symbols-outlined text-2xl">${entry.rank === 1 ? 'trophy' : 'military_tech'}</span>` : `#${entry.rank}`}
            </div>
            <div class="flex-1">
                <div class="flex items-center gap-2">
                    <span class="font-medium text-text-main dark:text-white">
                        ${entry.is_current_user ? tr('challenges.you', 'You') : `${tr('challenges.player', 'Player')} ${entry.rank}`}
                    </span>
                    <span class="text-xs px-2 py-0.5 bg-primary/20 text-primary rounded-full">Lv.${entry.level}</span>
                </div>
                <p class="text-sm text-text-muted dark:text-[#92adc9]">${entry.achievements} ${tr('challenges.achievements', 'achievements')}</p>
            </div>
            <div class="text-right">
                <p class="text-lg font-bold text-amber-500">${entry.points.toLocaleString()}</p>
                <p class="text-xs text-text-muted dark:text-[#92adc9]">${tr('challenges.points', 'points')}</p>
            </div>
        `;
        
        list.appendChild(row);
    });
    
    // Add user rank if not in top 10
    if (data.user_rank > 10) {
        const divider = document.createElement('div');
        divider.className = 'text-center text-text-muted dark:text-[#92adc9] text-sm py-2';
        divider.textContent = '...';
        list.appendChild(divider);
        
        const userRow = document.createElement('div');
        userRow.className = 'flex items-center gap-4 p-4 rounded-xl bg-primary/10 border border-primary/20';
        userRow.innerHTML = `
            <div class="w-8 h-8 flex items-center justify-center font-bold text-text-muted dark:text-[#92adc9]">
                #${data.user_rank}
            </div>
            <div class="flex-1">
                <span class="font-medium text-text-main dark:text-white">${tr('challenges.you', 'You')}</span>
            </div>
            <div class="text-right">
                <p class="text-lg font-bold text-amber-500">${userStats?.total_points?.toLocaleString() || 0}</p>
                <p class="text-xs text-text-muted dark:text-[#92adc9]">${tr('challenges.points', 'points')}</p>
            </div>
        `;
        list.appendChild(userRow);
    }
}

/**
 * Check for new achievements and show modal
 */
async function checkNewAchievements() {
    // Reload stats to get new achievements
    const response = await fetch('/api/challenges/stats');
    const data = await response.json();
    
    if (data.success && data.new_achievements && data.new_achievements.length > 0) {
        // Show modal for first new achievement
        const achievement = data.new_achievements[0];
        showAchievementModal(achievement);
    }
}

/**
 * Show achievement unlock modal
 */
function showAchievementModal(achievement) {
    const modal = document.getElementById('achievement-modal');
    const badge = document.getElementById('achievement-badge');
    const icon = document.getElementById('achievement-icon');
    const title = document.getElementById('achievement-title');
    const description = document.getElementById('achievement-description');
    const points = document.getElementById('achievement-points');
    
    badge.style.backgroundColor = achievement.badge_color;
    icon.textContent = achievement.icon;
    title.textContent = tr(achievement.title_key, achievement.code);
    description.textContent = tr(achievement.description_key, '');
    points.textContent = achievement.points;
    
    modal.classList.remove('hidden');
    
    // Mark as seen
    markAchievementSeen(achievement.id);
}

/**
 * Close achievement modal
 */
function closeAchievementModal() {
    document.getElementById('achievement-modal').classList.add('hidden');
    // Check if there are more achievements to show
    checkNewAchievements();
}

/**
 * Mark achievement as seen
 */
async function markAchievementSeen(achievementId) {
    try {
        await fetch(`/api/challenges/achievements/${achievementId}/mark-seen`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.content || ''
            }
        });
    } catch (error) {
        console.error('Error marking achievement seen:', error);
    }
}

/**
 * Rotate tip
 */
function rotateTip() {
    const tipElement = document.getElementById('tip-text');
    if (tipElement) {
        const randomTip = TIPS[Math.floor(Math.random() * TIPS.length)];
        tipElement.setAttribute('data-translate', randomTip);
        tipElement.textContent = tr(randomTip, tipElement.textContent);
    }
}
