"""
Gamification & Challenges API Routes
Features: No-spend days, Savings streaks, 52-week challenge, Achievement system
Security: All queries filtered by user_id to ensure users only see their own data
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models import (
    Achievement, Challenge, NoSpendDay, UserGamificationStats,
    Expense, SavingsGoal, SavingsContribution
)
from datetime import datetime, timedelta, date
from sqlalchemy import func, and_

bp = Blueprint('challenges', __name__, url_prefix='/api/challenges')


# ============================================================================
# ACHIEVEMENT DEFINITIONS
# ============================================================================

ACHIEVEMENTS = {
    # No-spend achievements
    'first_no_spend': {
        'type': 'no_spend_day',
        'title_key': 'achievements.firstNoSpend.title',
        'description_key': 'achievements.firstNoSpend.description',
        'icon': 'savings',
        'badge_color': '#10b981',
        'rarity': 'common',
        'points': 10,
        'target': 1
    },
    'no_spend_streak_3': {
        'type': 'no_spend_day',
        'title_key': 'achievements.noSpendStreak3.title',
        'description_key': 'achievements.noSpendStreak3.description',
        'icon': 'local_fire_department',
        'badge_color': '#f59e0b',
        'rarity': 'common',
        'points': 25,
        'target': 3
    },
    'no_spend_streak_7': {
        'type': 'no_spend_day',
        'title_key': 'achievements.noSpendStreak7.title',
        'description_key': 'achievements.noSpendStreak7.description',
        'icon': 'local_fire_department',
        'badge_color': '#f97316',
        'rarity': 'uncommon',
        'points': 50,
        'target': 7
    },
    'no_spend_streak_14': {
        'type': 'no_spend_day',
        'title_key': 'achievements.noSpendStreak14.title',
        'description_key': 'achievements.noSpendStreak14.description',
        'icon': 'whatshot',
        'badge_color': '#ef4444',
        'rarity': 'rare',
        'points': 100,
        'target': 14
    },
    'no_spend_streak_30': {
        'type': 'no_spend_day',
        'title_key': 'achievements.noSpendStreak30.title',
        'description_key': 'achievements.noSpendStreak30.description',
        'icon': 'whatshot',
        'badge_color': '#dc2626',
        'rarity': 'epic',
        'points': 250,
        'target': 30
    },
    'no_spend_days_10': {
        'type': 'no_spend_day',
        'title_key': 'achievements.noSpendDays10.title',
        'description_key': 'achievements.noSpendDays10.description',
        'icon': 'event_available',
        'badge_color': '#3b82f6',
        'rarity': 'common',
        'points': 30,
        'target': 10
    },
    'no_spend_days_50': {
        'type': 'no_spend_day',
        'title_key': 'achievements.noSpendDays50.title',
        'description_key': 'achievements.noSpendDays50.description',
        'icon': 'event_available',
        'badge_color': '#6366f1',
        'rarity': 'rare',
        'points': 100,
        'target': 50
    },
    'no_spend_days_100': {
        'type': 'no_spend_day',
        'title_key': 'achievements.noSpendDays100.title',
        'description_key': 'achievements.noSpendDays100.description',
        'icon': 'military_tech',
        'badge_color': '#8b5cf6',
        'rarity': 'epic',
        'points': 250,
        'target': 100
    },
    
    # Savings achievements
    'first_savings_goal': {
        'type': 'savings_streak',
        'title_key': 'achievements.firstSavingsGoal.title',
        'description_key': 'achievements.firstSavingsGoal.description',
        'icon': 'flag',
        'badge_color': '#10b981',
        'rarity': 'common',
        'points': 15,
        'target': 1
    },
    'savings_goal_completed': {
        'type': 'savings_streak',
        'title_key': 'achievements.savingsGoalCompleted.title',
        'description_key': 'achievements.savingsGoalCompleted.description',
        'icon': 'emoji_events',
        'badge_color': '#f59e0b',
        'rarity': 'uncommon',
        'points': 50,
        'target': 1
    },
    'savings_streak_4': {
        'type': 'savings_streak',
        'title_key': 'achievements.savingsStreak4.title',
        'description_key': 'achievements.savingsStreak4.description',
        'icon': 'trending_up',
        'badge_color': '#10b981',
        'rarity': 'common',
        'points': 40,
        'target': 4
    },
    'savings_streak_12': {
        'type': 'savings_streak',
        'title_key': 'achievements.savingsStreak12.title',
        'description_key': 'achievements.savingsStreak12.description',
        'icon': 'trending_up',
        'badge_color': '#059669',
        'rarity': 'rare',
        'points': 150,
        'target': 12
    },
    
    # 52-week challenge achievements
    'week_52_started': {
        'type': 'weekly_challenge',
        'title_key': 'achievements.week52Started.title',
        'description_key': 'achievements.week52Started.description',
        'icon': 'rocket_launch',
        'badge_color': '#3b82f6',
        'rarity': 'common',
        'points': 10,
        'target': 1
    },
    'week_52_quarter': {
        'type': 'weekly_challenge',
        'title_key': 'achievements.week52Quarter.title',
        'description_key': 'achievements.week52Quarter.description',
        'icon': 'stars',
        'badge_color': '#6366f1',
        'rarity': 'uncommon',
        'points': 75,
        'target': 13
    },
    'week_52_half': {
        'type': 'weekly_challenge',
        'title_key': 'achievements.week52Half.title',
        'description_key': 'achievements.week52Half.description',
        'icon': 'star',
        'badge_color': '#8b5cf6',
        'rarity': 'rare',
        'points': 150,
        'target': 26
    },
    'week_52_complete': {
        'type': 'weekly_challenge',
        'title_key': 'achievements.week52Complete.title',
        'description_key': 'achievements.week52Complete.description',
        'icon': 'workspace_premium',
        'badge_color': '#eab308',
        'rarity': 'legendary',
        'points': 500,
        'target': 52
    },
    
    # Habit achievements
    'budget_master': {
        'type': 'habit',
        'title_key': 'achievements.budgetMaster.title',
        'description_key': 'achievements.budgetMaster.description',
        'icon': 'account_balance_wallet',
        'badge_color': '#10b981',
        'rarity': 'uncommon',
        'points': 50,
        'target': 3  # 3 months under budget
    },
    'expense_tracker': {
        'type': 'habit',
        'title_key': 'achievements.expenseTracker.title',
        'description_key': 'achievements.expenseTracker.description',
        'icon': 'receipt_long',
        'badge_color': '#3b82f6',
        'rarity': 'common',
        'points': 20,
        'target': 50  # 50 expenses logged
    },
    'expense_tracker_500': {
        'type': 'habit',
        'title_key': 'achievements.expenseTracker500.title',
        'description_key': 'achievements.expenseTracker500.description',
        'icon': 'receipt_long',
        'badge_color': '#6366f1',
        'rarity': 'rare',
        'points': 100,
        'target': 500
    },
    'category_organizer': {
        'type': 'habit',
        'title_key': 'achievements.categoryOrganizer.title',
        'description_key': 'achievements.categoryOrganizer.description',
        'icon': 'category',
        'badge_color': '#ec4899',
        'rarity': 'common',
        'points': 15,
        'target': 5  # 5 categories used
    },
    'early_bird': {
        'type': 'habit',
        'title_key': 'achievements.earlyBird.title',
        'description_key': 'achievements.earlyBird.description',
        'icon': 'wb_sunny',
        'badge_color': '#f59e0b',
        'rarity': 'uncommon',
        'points': 25,
        'target': 7  # 7 days logging before 9am
    }
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_or_create_stats(user_id):
    """Get or create user gamification stats"""
    stats = UserGamificationStats.query.filter_by(user_id=user_id).first()
    if not stats:
        stats = UserGamificationStats(user_id=user_id)
        db.session.add(stats)
        db.session.commit()
    return stats


def award_achievement(user_id, achievement_code, progress=1):
    """Award or update progress on an achievement"""
    if achievement_code not in ACHIEVEMENTS:
        return None
    
    achievement_def = ACHIEVEMENTS[achievement_code]
    
    # Check if achievement already exists
    achievement = Achievement.query.filter_by(
        user_id=user_id,
        code=achievement_code
    ).first()
    
    if achievement and achievement.is_completed:
        return None  # Already completed
    
    if not achievement:
        # Create new achievement
        achievement = Achievement(
            user_id=user_id,
            achievement_type=achievement_def['type'],
            code=achievement_code,
            title_key=achievement_def['title_key'],
            description_key=achievement_def['description_key'],
            icon=achievement_def['icon'],
            badge_color=achievement_def['badge_color'],
            rarity=achievement_def['rarity'],
            points=achievement_def['points'],
            target_progress=achievement_def['target'],
            current_progress=0
        )
        db.session.add(achievement)
    
    # Update progress
    achievement.current_progress = progress
    
    # Check if completed
    if achievement.current_progress >= achievement.target_progress:
        achievement.is_completed = True
        achievement.completed_at = datetime.utcnow()
        
        # Update user stats
        stats = get_or_create_stats(user_id)
        stats.total_points += achievement.points
        stats.total_achievements_earned += 1
        stats.last_achievement_at = datetime.utcnow()
        stats.add_badge(achievement_code)
        stats.calculate_level()
    
    db.session.commit()
    return achievement


def check_no_spend_day(user_id, check_date=None):
    """Check if a specific date was a no-spend day"""
    if check_date is None:
        check_date = date.today()
    
    # Get total spending for the day
    day_start = datetime.combine(check_date, datetime.min.time())
    day_end = datetime.combine(check_date, datetime.max.time())
    
    total_spent = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user_id,
        Expense.date >= day_start,
        Expense.date <= day_end
    ).scalar()
    
    return (total_spent or 0) == 0


def update_no_spend_streak(user_id):
    """Update no-spend streak and check for achievements"""
    stats = get_or_create_stats(user_id)
    
    # Count consecutive no-spend days ending yesterday
    streak = 0
    check_date = date.today() - timedelta(days=1)
    
    while True:
        no_spend = NoSpendDay.query.filter_by(
            user_id=user_id,
            date=check_date,
            status='success'
        ).first()
        
        if no_spend:
            streak += 1
            check_date -= timedelta(days=1)
        else:
            break
        
        # Limit check to 365 days
        if streak >= 365:
            break
    
    # Update stats
    stats.current_no_spend_streak = streak
    if streak > stats.best_no_spend_streak:
        stats.best_no_spend_streak = streak
    
    # Check streak achievements
    if streak >= 3:
        award_achievement(user_id, 'no_spend_streak_3', streak)
    if streak >= 7:
        award_achievement(user_id, 'no_spend_streak_7', streak)
    if streak >= 14:
        award_achievement(user_id, 'no_spend_streak_14', streak)
    if streak >= 30:
        award_achievement(user_id, 'no_spend_streak_30', streak)
    
    # Check total no-spend days achievements
    total = stats.total_no_spend_days
    if total >= 10:
        award_achievement(user_id, 'no_spend_days_10', total)
    if total >= 50:
        award_achievement(user_id, 'no_spend_days_50', total)
    if total >= 100:
        award_achievement(user_id, 'no_spend_days_100', total)
    
    db.session.commit()
    return stats


# ============================================================================
# STATS & OVERVIEW
# ============================================================================

@bp.route('/stats', methods=['GET'])
@login_required
def get_stats():
    """Get user's gamification stats and overview"""
    try:
        stats = get_or_create_stats(current_user.id)
        
        # Get recent achievements
        recent_achievements = Achievement.query.filter_by(
            user_id=current_user.id,
            is_completed=True
        ).order_by(Achievement.completed_at.desc()).limit(5).all()
        
        # Get active challenges
        active_challenges = Challenge.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).all()
        
        # Get unnotified achievements
        new_achievements = Achievement.query.filter_by(
            user_id=current_user.id,
            is_completed=True,
            notification_shown=False
        ).all()
        
        # Calculate level progress
        level_thresholds = [0, 100, 250, 500, 1000, 2000, 4000, 8000, 15000, 30000]
        current_level = stats.level
        current_threshold = level_thresholds[current_level - 1] if current_level > 0 else 0
        next_threshold = level_thresholds[current_level] if current_level < len(level_thresholds) else level_thresholds[-1]
        level_progress = ((stats.total_points - current_threshold) / (next_threshold - current_threshold) * 100) if next_threshold > current_threshold else 100
        
        return jsonify({
            'success': True,
            'stats': stats.to_dict(),
            'level_progress': round(level_progress, 1),
            'points_to_next_level': max(0, next_threshold - stats.total_points),
            'recent_achievements': [a.to_dict() for a in recent_achievements],
            'active_challenges': [c.to_dict() for c in active_challenges],
            'new_achievements': [a.to_dict() for a in new_achievements]
        })
    except Exception as e:
        current_app.logger.error(f"Error getting gamification stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/achievements', methods=['GET'])
@login_required
def get_achievements():
    """Get all achievements (earned and available)"""
    try:
        # Get user's achievements
        user_achievements = {a.code: a for a in Achievement.query.filter_by(user_id=current_user.id).all()}
        
        # Build list with all available achievements
        all_achievements = []
        for code, definition in ACHIEVEMENTS.items():
            if code in user_achievements:
                all_achievements.append(user_achievements[code].to_dict())
            else:
                all_achievements.append({
                    'code': code,
                    'achievement_type': definition['type'],
                    'title_key': definition['title_key'],
                    'description_key': definition['description_key'],
                    'icon': definition['icon'],
                    'badge_color': definition['badge_color'],
                    'rarity': definition['rarity'],
                    'points': definition['points'],
                    'current_progress': 0,
                    'target_progress': definition['target'],
                    'is_completed': False,
                    'progress_percentage': 0
                })
        
        # Sort by completed first, then by rarity
        rarity_order = {'legendary': 0, 'epic': 1, 'rare': 2, 'uncommon': 3, 'common': 4}
        all_achievements.sort(key=lambda a: (
            0 if a['is_completed'] else 1,
            rarity_order.get(a['rarity'], 5)
        ))
        
        return jsonify({
            'success': True,
            'achievements': all_achievements,
            'total_earned': len([a for a in all_achievements if a['is_completed']]),
            'total_available': len(all_achievements)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting achievements: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/achievements/<int:achievement_id>/mark-seen', methods=['POST'])
@login_required
def mark_achievement_seen(achievement_id):
    """Mark an achievement notification as seen"""
    try:
        achievement = Achievement.query.filter_by(
            id=achievement_id,
            user_id=current_user.id
        ).first()
        
        if not achievement:
            return jsonify({'success': False, 'error': 'Achievement not found'}), 404
        
        achievement.notification_shown = True
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        current_app.logger.error(f"Error marking achievement seen: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# NO-SPEND DAY CHALLENGE
# ============================================================================

@bp.route('/no-spend/today', methods=['GET'])
@login_required
def get_today_no_spend():
    """Get today's no-spend status"""
    try:
        today = date.today()
        
        # Check if there's a record for today
        no_spend = NoSpendDay.query.filter_by(
            user_id=current_user.id,
            date=today
        ).first()
        
        # Calculate today's spending
        day_start = datetime.combine(today, datetime.min.time())
        day_end = datetime.combine(today, datetime.max.time())
        
        total_spent = db.session.query(func.sum(Expense.amount)).filter(
            Expense.user_id == current_user.id,
            Expense.date >= day_start,
            Expense.date <= day_end
        ).scalar() or 0
        
        expense_count = Expense.query.filter(
            Expense.user_id == current_user.id,
            Expense.date >= day_start,
            Expense.date <= day_end
        ).count()
        
        # Get current streak
        stats = get_or_create_stats(current_user.id)
        
        return jsonify({
            'success': True,
            'date': today.isoformat(),
            'is_intentional': no_spend.is_intentional if no_spend else False,
            'amount_spent': total_spent,
            'expense_count': expense_count,
            'is_no_spend_day': total_spent == 0,
            'current_streak': stats.current_no_spend_streak,
            'best_streak': stats.best_no_spend_streak,
            'status': no_spend.status if no_spend else ('success' if total_spent == 0 else 'failed')
        })
    except Exception as e:
        current_app.logger.error(f"Error getting today's no-spend: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/no-spend/set-intentional', methods=['POST'])
@login_required
def set_intentional_no_spend():
    """Mark today as an intentional no-spend day"""
    try:
        today = date.today()
        
        no_spend = NoSpendDay.query.filter_by(
            user_id=current_user.id,
            date=today
        ).first()
        
        if not no_spend:
            no_spend = NoSpendDay(
                user_id=current_user.id,
                date=today,
                is_intentional=True,
                status='pending'
            )
            db.session.add(no_spend)
        else:
            no_spend.is_intentional = True
        
        notes = request.json.get('notes', '') if request.json else ''
        if notes:
            no_spend.notes = notes[:255]
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Today marked as intentional no-spend day'
        })
    except Exception as e:
        current_app.logger.error(f"Error setting intentional no-spend: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/no-spend/calendar', methods=['GET'])
@login_required
def get_no_spend_calendar():
    """Get no-spend day calendar for a month"""
    try:
        year = request.args.get('year', date.today().year, type=int)
        month = request.args.get('month', date.today().month, type=int)
        
        # Get first and last day of month
        first_day = date(year, month, 1)
        if month == 12:
            last_day = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            last_day = date(year, month + 1, 1) - timedelta(days=1)
        
        # Get all no-spend days for the month
        no_spend_days = NoSpendDay.query.filter(
            NoSpendDay.user_id == current_user.id,
            NoSpendDay.date >= first_day,
            NoSpendDay.date <= last_day
        ).all()
        
        # Get all expenses for the month
        month_start = datetime.combine(first_day, datetime.min.time())
        month_end = datetime.combine(last_day, datetime.max.time())
        
        expenses_by_day = db.session.query(
            func.date(Expense.date).label('day'),
            func.sum(Expense.amount).label('total')
        ).filter(
            Expense.user_id == current_user.id,
            Expense.date >= month_start,
            Expense.date <= month_end
        ).group_by(func.date(Expense.date)).all()
        
        expenses_dict = {str(e.day): e.total for e in expenses_by_day}
        no_spend_dict = {str(n.date): n for n in no_spend_days}
        
        # Build calendar data
        calendar_data = []
        current_date = first_day
        while current_date <= last_day:
            date_str = current_date.isoformat()
            spent = expenses_dict.get(date_str, 0)
            no_spend_record = no_spend_dict.get(date_str)
            
            calendar_data.append({
                'date': date_str,
                'day': current_date.day,
                'weekday': current_date.weekday(),
                'amount_spent': spent,
                'is_no_spend': spent == 0 and current_date <= date.today(),
                'is_intentional': no_spend_record.is_intentional if no_spend_record else False,
                'status': no_spend_record.status if no_spend_record else ('success' if spent == 0 and current_date < date.today() else 'pending'),
                'is_future': current_date > date.today()
            })
            current_date += timedelta(days=1)
        
        # Calculate month stats
        successful_days = len([d for d in calendar_data if d['status'] == 'success'])
        intentional_days = len([d for d in calendar_data if d['is_intentional']])
        
        return jsonify({
            'success': True,
            'year': year,
            'month': month,
            'calendar': calendar_data,
            'stats': {
                'successful_days': successful_days,
                'intentional_days': intentional_days,
                'total_days_passed': len([d for d in calendar_data if not d['is_future']])
            }
        })
    except Exception as e:
        current_app.logger.error(f"Error getting no-spend calendar: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# 52-WEEK SAVINGS CHALLENGE
# ============================================================================

@bp.route('/52-week', methods=['GET'])
@login_required
def get_52_week_challenge():
    """Get user's 52-week savings challenge progress"""
    try:
        challenge = Challenge.query.filter_by(
            user_id=current_user.id,
            challenge_type='weekly_52',
            is_active=True
        ).first()
        
        if not challenge:
            return jsonify({
                'success': True,
                'active': False,
                'message': 'No active 52-week challenge'
            })
        
        weekly_amounts = challenge.get_weekly_amounts()
        config = challenge.get_config()
        base_amount = config.get('base_amount', 1)
        increment = config.get('increment', 1)
        reverse = config.get('reverse', False)
        
        # Calculate expected and actual savings per week
        weeks_data = []
        for week in range(1, 53):
            if reverse:
                expected = base_amount + (52 - week) * increment
            else:
                expected = base_amount + (week - 1) * increment
            
            actual = weekly_amounts.get(str(week), 0)
            weeks_data.append({
                'week': week,
                'expected': expected,
                'actual': actual,
                'completed': actual >= expected
            })
        
        # Calculate totals
        total_expected = sum(w['expected'] for w in weeks_data[:challenge.current_week])
        total_saved = challenge.total_saved
        
        return jsonify({
            'success': True,
            'active': True,
            'challenge': challenge.to_dict(),
            'weeks': weeks_data,
            'current_week': challenge.current_week,
            'total_expected': total_expected,
            'total_saved': total_saved,
            'on_track': total_saved >= total_expected,
            'weeks_completed': len([w for w in weeks_data if w['completed']]),
            'final_total': sum(w['expected'] for w in weeks_data)
        })
    except Exception as e:
        current_app.logger.error(f"Error getting 52-week challenge: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/52-week/start', methods=['POST'])
@login_required
def start_52_week_challenge():
    """Start a new 52-week savings challenge"""
    try:
        # Check if already active
        existing = Challenge.query.filter_by(
            user_id=current_user.id,
            challenge_type='weekly_52',
            is_active=True
        ).first()
        
        if existing:
            return jsonify({
                'success': False,
                'error': 'You already have an active 52-week challenge'
            }), 400
        
        data = request.get_json() or {}
        base_amount = data.get('base_amount', 1)
        increment = data.get('increment', 1)
        reverse = data.get('reverse', False)  # Start with week 52 amount
        currency = data.get('currency', current_user.currency)
        
        # Calculate total
        if reverse:
            total = sum(base_amount + (52 - i) * increment for i in range(1, 53))
        else:
            total = sum(base_amount + (i - 1) * increment for i in range(1, 53))
        
        challenge = Challenge(
            user_id=current_user.id,
            challenge_type='weekly_52',
            title_key='challenges.week52.title',
            description_key='challenges.week52.description',
            current_week=1,
            start_date=datetime.utcnow()
        )
        challenge.set_config({
            'base_amount': base_amount,
            'increment': increment,
            'reverse': reverse,
            'currency': currency,
            'total_target': total
        })
        
        db.session.add(challenge)
        
        # Award started achievement
        award_achievement(current_user.id, 'week_52_started')
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'challenge': challenge.to_dict(),
            'message': '52-week challenge started!'
        })
    except Exception as e:
        current_app.logger.error(f"Error starting 52-week challenge: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/52-week/save', methods=['POST'])
@login_required
def save_for_week():
    """Save amount for current week in 52-week challenge"""
    try:
        challenge = Challenge.query.filter_by(
            user_id=current_user.id,
            challenge_type='weekly_52',
            is_active=True
        ).first()
        
        if not challenge:
            return jsonify({
                'success': False,
                'error': 'No active 52-week challenge'
            }), 404
        
        data = request.get_json() or {}
        amount = data.get('amount', 0)
        week = data.get('week', challenge.current_week)
        
        if amount <= 0:
            return jsonify({
                'success': False,
                'error': 'Amount must be positive'
            }), 400
        
        # Update weekly amounts
        weekly_amounts = challenge.get_weekly_amounts()
        current_week_amount = weekly_amounts.get(str(week), 0)
        weekly_amounts[str(week)] = current_week_amount + amount
        challenge.set_weekly_amounts(weekly_amounts)
        
        # Update total saved
        challenge.total_saved += amount
        
        # Check if week is complete and advance
        config = challenge.get_config()
        base_amount = config.get('base_amount', 1)
        increment = config.get('increment', 1)
        reverse = config.get('reverse', False)
        
        if reverse:
            expected = base_amount + (52 - week) * increment
        else:
            expected = base_amount + (week - 1) * increment
        
        week_complete = weekly_amounts[str(week)] >= expected
        
        # Advance to next week if current is complete and we saved for current week
        if week_complete and week == challenge.current_week and challenge.current_week < 52:
            challenge.current_week += 1
        
        # Update stats
        stats = get_or_create_stats(current_user.id)
        stats.week_52_progress = len([w for w in range(1, 53) if weekly_amounts.get(str(w), 0) >= (base_amount + (52 - w if reverse else w - 1) * increment)])
        stats.week_52_total_saved = challenge.total_saved
        
        # Check achievements
        weeks_completed = stats.week_52_progress
        if weeks_completed >= 13:
            award_achievement(current_user.id, 'week_52_quarter', weeks_completed)
        if weeks_completed >= 26:
            award_achievement(current_user.id, 'week_52_half', weeks_completed)
        if weeks_completed >= 52:
            award_achievement(current_user.id, 'week_52_complete', weeks_completed)
            challenge.is_completed = True
            challenge.completed_at = datetime.utcnow()
            stats.total_challenges_completed += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'week': week,
            'amount_saved': weekly_amounts[str(week)],
            'expected': expected,
            'week_complete': week_complete,
            'current_week': challenge.current_week,
            'total_saved': challenge.total_saved
        })
    except Exception as e:
        current_app.logger.error(f"Error saving for week: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/52-week/reset', methods=['POST'])
@login_required
def reset_52_week_challenge():
    """Reset/cancel the 52-week challenge"""
    try:
        challenge = Challenge.query.filter_by(
            user_id=current_user.id,
            challenge_type='weekly_52',
            is_active=True
        ).first()
        
        if not challenge:
            return jsonify({
                'success': False,
                'error': 'No active 52-week challenge'
            }), 404
        
        challenge.is_active = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '52-week challenge has been reset'
        })
    except Exception as e:
        current_app.logger.error(f"Error resetting 52-week challenge: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# GENERAL CHALLENGES
# ============================================================================

@bp.route('/active', methods=['GET'])
@login_required
def get_active_challenges():
    """Get all active challenges"""
    try:
        challenges = Challenge.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).all()
        
        return jsonify({
            'success': True,
            'challenges': [c.to_dict() for c in challenges]
        })
    except Exception as e:
        current_app.logger.error(f"Error getting active challenges: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# LEADERBOARD (Optional - for future multi-user features)
# ============================================================================

@bp.route('/leaderboard', methods=['GET'])
@login_required
def get_leaderboard():
    """Get gamification leaderboard (anonymized for privacy)"""
    try:
        # Get top users by points (anonymized)
        top_stats = UserGamificationStats.query.order_by(
            UserGamificationStats.total_points.desc()
        ).limit(10).all()
        
        # Find current user's rank
        user_stats = get_or_create_stats(current_user.id)
        user_rank = UserGamificationStats.query.filter(
            UserGamificationStats.total_points > user_stats.total_points
        ).count() + 1
        
        leaderboard = []
        for i, stats in enumerate(top_stats, 1):
            leaderboard.append({
                'rank': i,
                'level': stats.level,
                'points': stats.total_points,
                'achievements': stats.total_achievements_earned,
                'is_current_user': stats.user_id == current_user.id
            })
        
        return jsonify({
            'success': True,
            'leaderboard': leaderboard,
            'user_rank': user_rank,
            'total_users': UserGamificationStats.query.count()
        })
    except Exception as e:
        current_app.logger.error(f"Error getting leaderboard: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# DAILY CHECK (Called by scheduler)
# ============================================================================

def process_daily_no_spend_check(app):
    """Process end-of-day no-spend check for all users"""
    with app.app_context():
        try:
            yesterday = date.today() - timedelta(days=1)
            
            # Get all users
            from app.models import User
            users = User.query.all()
            
            for user in users:
                # Check if yesterday was a no-spend day
                day_start = datetime.combine(yesterday, datetime.min.time())
                day_end = datetime.combine(yesterday, datetime.max.time())
                
                total_spent = db.session.query(func.sum(Expense.amount)).filter(
                    Expense.user_id == user.id,
                    Expense.date >= day_start,
                    Expense.date <= day_end
                ).scalar() or 0
                
                # Get or create no-spend record
                no_spend = NoSpendDay.query.filter_by(
                    user_id=user.id,
                    date=yesterday
                ).first()
                
                if not no_spend:
                    no_spend = NoSpendDay(
                        user_id=user.id,
                        date=yesterday
                    )
                    db.session.add(no_spend)
                
                no_spend.amount_spent = total_spent
                no_spend.status = 'success' if total_spent == 0 else 'failed'
                
                # Update stats if successful
                if total_spent == 0:
                    stats = get_or_create_stats(user.id)
                    stats.total_no_spend_days += 1
                    
                    # Award first no-spend achievement
                    if stats.total_no_spend_days == 1:
                        award_achievement(user.id, 'first_no_spend')
                    
                    # Update streak
                    update_no_spend_streak(user.id)
                else:
                    # Reset streak if failed
                    stats = get_or_create_stats(user.id)
                    stats.current_no_spend_streak = 0
            
            db.session.commit()
            current_app.logger.info("Daily no-spend check completed")
        except Exception as e:
            current_app.logger.error(f"Error in daily no-spend check: {e}")
            db.session.rollback()


def process_weekly_52_advance(app):
    """Advance 52-week challenges (called weekly)"""
    with app.app_context():
        try:
            # Get all active 52-week challenges
            challenges = Challenge.query.filter_by(
                challenge_type='weekly_52',
                is_active=True
            ).all()
            
            for challenge in challenges:
                # Calculate weeks since start
                weeks_since_start = (datetime.utcnow() - challenge.start_date).days // 7
                
                # Update current week based on time passed
                if weeks_since_start > challenge.current_week:
                    challenge.current_week = min(52, weeks_since_start)
                    challenge.last_check_date = datetime.utcnow()
            
            db.session.commit()
            current_app.logger.info("Weekly 52-week challenge update completed")
        except Exception as e:
            current_app.logger.error(f"Error in weekly 52-week update: {e}")
            db.session.rollback()
