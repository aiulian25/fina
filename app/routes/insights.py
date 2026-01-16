"""
Smart Spending Insights API Routes
Provides weekly spending digests, unusual spending alerts,
category comparisons, and money leak identification.

Security: All queries filtered by current_user.id
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import (
    Expense, Category, SpendingInsight, UserInsightPreferences, Income
)
from datetime import datetime, timedelta
from sqlalchemy import func, and_, extract
from collections import defaultdict
import json

bp = Blueprint('insights', __name__, url_prefix='/api/insights')


def get_or_create_preferences(user_id):
    """Get or create user insight preferences"""
    prefs = UserInsightPreferences.query.filter_by(user_id=user_id).first()
    if not prefs:
        prefs = UserInsightPreferences(user_id=user_id)
        db.session.add(prefs)
        db.session.commit()
    return prefs


@bp.route('/list', methods=['GET'])
@login_required
def get_insights_list():
    """Get all active insights for user"""
    include_dismissed = request.args.get('include_dismissed', 'false').lower() == 'true'
    limit = request.args.get('limit', 50, type=int)
    
    query = SpendingInsight.query.filter(
        SpendingInsight.user_id == current_user.id
    )
    
    if not include_dismissed:
        query = query.filter(SpendingInsight.is_dismissed == False)
    
    # Exclude expired insights
    query = query.filter(
        db.or_(
            SpendingInsight.expires_at == None,
            SpendingInsight.expires_at > datetime.utcnow()
        )
    )
    
    insights = query.order_by(
        SpendingInsight.is_read.asc(),  # Unread first
        SpendingInsight.created_at.desc()
    ).limit(limit).all()
    
    # Count unread
    unread_count = SpendingInsight.query.filter(
        SpendingInsight.user_id == current_user.id,
        SpendingInsight.is_read == False,
        SpendingInsight.is_dismissed == False
    ).count()
    
    return jsonify({
        'success': True,
        'insights': [i.to_dict() for i in insights],
        'unread_count': unread_count,
        'currency': current_user.currency
    })


@bp.route('/<int:insight_id>/read', methods=['POST'])
@login_required
def mark_insight_read(insight_id):
    """Mark an insight as read"""
    insight = SpendingInsight.query.filter_by(
        id=insight_id,
        user_id=current_user.id
    ).first_or_404()
    
    insight.is_read = True
    db.session.commit()
    
    return jsonify({'success': True})


@bp.route('/<int:insight_id>/dismiss', methods=['POST'])
@login_required
def dismiss_insight(insight_id):
    """Dismiss an insight"""
    insight = SpendingInsight.query.filter_by(
        id=insight_id,
        user_id=current_user.id
    ).first_or_404()
    
    insight.is_dismissed = True
    db.session.commit()
    
    return jsonify({'success': True})


@bp.route('/mark-all-read', methods=['POST'])
@login_required
def mark_all_read():
    """Mark all insights as read"""
    SpendingInsight.query.filter(
        SpendingInsight.user_id == current_user.id,
        SpendingInsight.is_read == False
    ).update({'is_read': True})
    db.session.commit()
    
    return jsonify({'success': True})


@bp.route('/preferences', methods=['GET'])
@login_required
def get_preferences():
    """Get user insight preferences"""
    prefs = get_or_create_preferences(current_user.id)
    return jsonify({
        'success': True,
        'preferences': prefs.to_dict()
    })


@bp.route('/preferences', methods=['PUT'])
@login_required
def update_preferences():
    """Update user insight preferences"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    prefs = get_or_create_preferences(current_user.id)
    
    # Update fields if provided
    updatable_fields = [
        'weekly_digest_enabled', 'weekly_digest_day',
        'unusual_spending_enabled', 'unusual_spending_threshold',
        'category_alerts_enabled', 'category_alert_threshold',
        'money_leak_detection_enabled', 'money_leak_min_occurrences',
        'push_notifications_enabled', 'email_digest_enabled'
    ]
    
    for field in updatable_fields:
        if field in data:
            setattr(prefs, field, data[field])
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'preferences': prefs.to_dict()
    })


@bp.route('/weekly-digest', methods=['GET'])
@login_required
def get_weekly_digest():
    """Get weekly spending digest data"""
    # Calculate date range (last 7 days)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    prev_start = start_date - timedelta(days=7)
    prev_end = start_date
    
    # Current week expenses
    current_expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_date,
        Expense.date < end_date
    ).all()
    
    # Previous week expenses for comparison
    prev_expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= prev_start,
        Expense.date < prev_end
    ).all()
    
    # Calculate totals
    current_total = sum(e.amount for e in current_expenses)
    prev_total = sum(e.amount for e in prev_expenses)
    
    # Calculate change
    if prev_total > 0:
        change_percentage = ((current_total - prev_total) / prev_total) * 100
    else:
        change_percentage = 100 if current_total > 0 else 0
    
    # Group by category
    category_totals = defaultdict(lambda: {'current': 0, 'previous': 0})
    
    for e in current_expenses:
        cat_name = e.category.name if e.category else 'Uncategorized'
        cat_color = e.category.color if e.category else '#666'
        category_totals[cat_name]['current'] += e.amount
        category_totals[cat_name]['color'] = cat_color
        category_totals[cat_name]['id'] = e.category_id
    
    for e in prev_expenses:
        cat_name = e.category.name if e.category else 'Uncategorized'
        category_totals[cat_name]['previous'] += e.amount
        if 'color' not in category_totals[cat_name]:
            category_totals[cat_name]['color'] = e.category.color if e.category else '#666'
            category_totals[cat_name]['id'] = e.category_id
    
    # Calculate category changes and sort by current spending
    categories_data = []
    for cat_name, data in category_totals.items():
        current = data['current']
        previous = data['previous']
        if previous > 0:
            change = ((current - previous) / previous) * 100
        else:
            change = 100 if current > 0 else 0
        
        categories_data.append({
            'name': cat_name,
            'color': data.get('color', '#666'),
            'category_id': data.get('id'),
            'current': round(current, 2),
            'previous': round(previous, 2),
            'change_percentage': round(change, 1)
        })
    
    categories_data.sort(key=lambda x: x['current'], reverse=True)
    
    # Get top spending day
    daily_spending = defaultdict(float)
    for e in current_expenses:
        day_key = e.date.strftime('%A')
        daily_spending[day_key] += e.amount
    
    top_day = max(daily_spending.items(), key=lambda x: x[1]) if daily_spending else ('', 0)
    
    # Current week income
    current_income = Income.query.filter(
        Income.user_id == current_user.id,
        Income.date >= start_date,
        Income.date < end_date
    ).all()
    
    income_total = sum(i.amount for i in current_income)
    net_flow = income_total - current_total
    
    return jsonify({
        'success': True,
        'period': {
            'start': start_date.isoformat(),
            'end': end_date.isoformat()
        },
        'summary': {
            'total_spent': round(current_total, 2),
            'previous_total': round(prev_total, 2),
            'change_percentage': round(change_percentage, 1),
            'transaction_count': len(current_expenses),
            'daily_average': round(current_total / 7, 2),
            'top_spending_day': top_day[0],
            'top_spending_day_amount': round(top_day[1], 2),
            'income_total': round(income_total, 2),
            'net_flow': round(net_flow, 2)
        },
        'categories': categories_data[:10],  # Top 10
        'currency': current_user.currency
    })


@bp.route('/unusual-spending', methods=['GET'])
@login_required
def get_unusual_spending():
    """Detect unusual spending patterns"""
    days = request.args.get('days', 7, type=int)
    
    prefs = get_or_create_preferences(current_user.id)
    threshold = prefs.unusual_spending_threshold
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    # Calculate baseline (last 30 days before current period)
    baseline_start = start_date - timedelta(days=30)
    baseline_end = start_date
    
    # Get recent expenses
    recent_expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_date,
        Expense.date < end_date
    ).all()
    
    # Get baseline expenses
    baseline_expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= baseline_start,
        Expense.date < baseline_end
    ).all()
    
    # Calculate baseline daily average
    baseline_total = sum(e.amount for e in baseline_expenses)
    baseline_daily_avg = baseline_total / 30 if baseline_expenses else 0
    
    # Calculate recent daily average
    recent_total = sum(e.amount for e in recent_expenses)
    recent_daily_avg = recent_total / days if days > 0 else 0
    
    unusual_items = []
    
    # Check if overall spending is unusual
    if baseline_daily_avg > 0 and recent_daily_avg > baseline_daily_avg * threshold:
        unusual_items.append({
            'type': 'overall_spike',
            'title_key': 'insights.unusual.overallSpike.title',
            'message_key': 'insights.unusual.overallSpike.message',
            'message_params': {
                'percentage': round(((recent_daily_avg / baseline_daily_avg) - 1) * 100),
                'current': round(recent_daily_avg, 2),
                'baseline': round(baseline_daily_avg, 2)
            },
            'amount': round(recent_total, 2),
            'icon': 'trending_up',
            'priority': 'high'
        })
    
    # Check for individual large transactions
    if baseline_expenses:
        avg_transaction = baseline_total / len(baseline_expenses)
        large_threshold = avg_transaction * 3  # 3x average
        
        for expense in recent_expenses:
            if expense.amount > large_threshold and expense.amount > 50:  # Min £50
                unusual_items.append({
                    'type': 'large_transaction',
                    'title_key': 'insights.unusual.largeTransaction.title',
                    'message_key': 'insights.unusual.largeTransaction.message',
                    'message_params': {
                        'description': expense.description,
                        'amount': expense.amount,
                        'average': round(avg_transaction, 2)
                    },
                    'amount': expense.amount,
                    'expense_id': expense.id,
                    'category': expense.category.name if expense.category else None,
                    'date': expense.date.isoformat(),
                    'icon': 'warning',
                    'priority': 'medium'
                })
    
    # Check for unusual spending by day of week
    daily_spending = defaultdict(list)
    for e in baseline_expenses:
        day_name = e.date.strftime('%A')
        daily_spending[day_name].append(e.amount)
    
    for e in recent_expenses:
        day_name = e.date.strftime('%A')
        if daily_spending[day_name]:
            day_avg = sum(daily_spending[day_name]) / len(daily_spending[day_name])
            if e.amount > day_avg * 2 and e.amount > 30:  # 2x daily average for that day
                unusual_items.append({
                    'type': 'unusual_day',
                    'title_key': 'insights.unusual.unusualDay.title',
                    'message_key': 'insights.unusual.unusualDay.message',
                    'message_params': {
                        'day': day_name,
                        'amount': e.amount,
                        'average': round(day_avg, 2)
                    },
                    'amount': e.amount,
                    'icon': 'schedule',
                    'priority': 'low'
                })
    
    return jsonify({
        'success': True,
        'unusual_items': unusual_items[:20],  # Limit to 20
        'baseline_daily_avg': round(baseline_daily_avg, 2),
        'recent_daily_avg': round(recent_daily_avg, 2),
        'threshold': threshold,
        'currency': current_user.currency
    })


@bp.route('/category-comparison', methods=['GET'])
@login_required
def get_category_comparison():
    """Compare category spending vs previous month"""
    end_date = datetime.utcnow()
    start_of_month = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Previous month
    prev_month_end = start_of_month - timedelta(days=1)
    prev_month_start = prev_month_end.replace(day=1)
    
    # Get current month expenses
    current_expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_of_month,
        Expense.date < end_date
    ).all()
    
    # Get previous month expenses
    prev_expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= prev_month_start,
        Expense.date <= prev_month_end
    ).all()
    
    # Group by category
    current_by_cat = defaultdict(float)
    prev_by_cat = defaultdict(float)
    category_info = {}
    
    for e in current_expenses:
        cat_name = e.category.name if e.category else 'Uncategorized'
        current_by_cat[cat_name] += e.amount
        if cat_name not in category_info:
            category_info[cat_name] = {
                'id': e.category_id,
                'color': e.category.color if e.category else '#666',
                'icon': e.category.icon if e.category else 'category'
            }
    
    for e in prev_expenses:
        cat_name = e.category.name if e.category else 'Uncategorized'
        prev_by_cat[cat_name] += e.amount
        if cat_name not in category_info:
            category_info[cat_name] = {
                'id': e.category_id,
                'color': e.category.color if e.category else '#666',
                'icon': e.category.icon if e.category else 'category'
            }
    
    # Build comparison data
    prefs = get_or_create_preferences(current_user.id)
    alert_threshold = prefs.category_alert_threshold
    
    comparisons = []
    spikes = []
    
    all_categories = set(current_by_cat.keys()) | set(prev_by_cat.keys())
    
    for cat_name in all_categories:
        current = current_by_cat.get(cat_name, 0)
        previous = prev_by_cat.get(cat_name, 0)
        
        if previous > 0:
            change = ((current - previous) / previous) * 100
        else:
            change = 100 if current > 0 else 0
        
        info = category_info.get(cat_name, {})
        
        comparison = {
            'category': cat_name,
            'category_id': info.get('id'),
            'color': info.get('color', '#666'),
            'icon': info.get('icon', 'category'),
            'current': round(current, 2),
            'previous': round(previous, 2),
            'change_percentage': round(change, 1),
            'change_amount': round(current - previous, 2)
        }
        
        comparisons.append(comparison)
        
        # Check for spikes
        if previous > 0 and current > previous * alert_threshold and (current - previous) > 20:
            spikes.append({
                **comparison,
                'is_spike': True,
                'title_key': 'insights.category.spike.title',
                'message_key': 'insights.category.spike.message',
                'icon': 'trending_up',
                'priority': 'high' if change > 100 else 'medium'
            })
    
    # Sort by absolute change
    comparisons.sort(key=lambda x: abs(x['change_amount']), reverse=True)
    spikes.sort(key=lambda x: x['change_percentage'], reverse=True)
    
    return jsonify({
        'success': True,
        'current_month': start_of_month.strftime('%B %Y'),
        'previous_month': prev_month_start.strftime('%B %Y'),
        'days_in_current_month': (end_date - start_of_month).days,
        'comparisons': comparisons,
        'spikes': spikes[:5],  # Top 5 spikes
        'current_total': round(sum(current_by_cat.values()), 2),
        'previous_total': round(sum(prev_by_cat.values()), 2),
        'currency': current_user.currency
    })


@bp.route('/money-leaks', methods=['GET'])
@login_required
def get_money_leaks():
    """Identify recurring small expenses that add up (money leaks)"""
    days = request.args.get('days', 90, type=int)
    
    prefs = get_or_create_preferences(current_user.id)
    min_occurrences = prefs.money_leak_min_occurrences
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_date
    ).order_by(Expense.date.desc()).all()
    
    # Group by similar description patterns
    # (normalize: lowercase, remove special chars, similar amounts)
    patterns = defaultdict(lambda: {'expenses': [], 'total': 0, 'amounts': []})
    
    for expense in expenses:
        # Normalize description
        desc = expense.description.lower().strip()
        # Remove common suffixes/numbers
        import re
        desc_clean = re.sub(r'[0-9#]+', '', desc).strip()
        desc_clean = re.sub(r'\s+', ' ', desc_clean)
        
        # Key by description pattern + approximate amount range
        amount_bucket = round(expense.amount / 5) * 5  # Round to nearest £5
        key = f"{desc_clean}_{amount_bucket}"
        
        patterns[key]['expenses'].append({
            'id': expense.id,
            'description': expense.description,
            'amount': expense.amount,
            'date': expense.date.isoformat(),
            'category': expense.category.name if expense.category else None
        })
        patterns[key]['total'] += expense.amount
        patterns[key]['amounts'].append(expense.amount)
        patterns[key]['category'] = expense.category.name if expense.category else None
        patterns[key]['category_color'] = expense.category.color if expense.category else '#666'
        patterns[key]['original_desc'] = expense.description
    
    # Filter to recurring patterns (min occurrences)
    money_leaks = []
    
    for key, data in patterns.items():
        if len(data['expenses']) >= min_occurrences:
            avg_amount = sum(data['amounts']) / len(data['amounts'])
            frequency_per_week = len(data['expenses']) / (days / 7)
            yearly_projection = (data['total'] / days) * 365
            
            money_leaks.append({
                'pattern': data['original_desc'],
                'description_clean': key.rsplit('_', 1)[0],
                'occurrence_count': len(data['expenses']),
                'total_spent': round(data['total'], 2),
                'average_amount': round(avg_amount, 2),
                'frequency_per_week': round(frequency_per_week, 1),
                'yearly_projection': round(yearly_projection, 2),
                'category': data['category'],
                'category_color': data['category_color'],
                'recent_expenses': data['expenses'][:5],
                'title_key': 'insights.moneyLeak.title',
                'message_key': 'insights.moneyLeak.message',
                'icon': 'water_drop',
                'priority': 'high' if yearly_projection > 500 else 'medium' if yearly_projection > 200 else 'low'
            })
    
    # Sort by yearly projection (biggest leaks first)
    money_leaks.sort(key=lambda x: x['yearly_projection'], reverse=True)
    
    total_leaks = sum(l['total_spent'] for l in money_leaks)
    yearly_leak_projection = sum(l['yearly_projection'] for l in money_leaks)
    
    return jsonify({
        'success': True,
        'money_leaks': money_leaks[:15],  # Top 15
        'total_leak_amount': round(total_leaks, 2),
        'yearly_projection': round(yearly_leak_projection, 2),
        'days_analyzed': days,
        'min_occurrences': min_occurrences,
        'currency': current_user.currency
    })


@bp.route('/generate', methods=['POST'])
@login_required
def generate_insights():
    """
    Manually trigger insight generation for the user.
    This creates SpendingInsight records based on current spending patterns.
    """
    generated = []
    
    prefs = get_or_create_preferences(current_user.id)
    
    # 1. Check for unusual spending
    if prefs.unusual_spending_enabled:
        unusual = check_unusual_spending(current_user.id, prefs.unusual_spending_threshold)
        for item in unusual:
            insight = create_insight(current_user.id, item)
            if insight:
                generated.append(insight.to_dict())
    
    # 2. Check for category spikes
    if prefs.category_alerts_enabled:
        spikes = check_category_spikes(current_user.id, prefs.category_alert_threshold)
        for item in spikes:
            insight = create_insight(current_user.id, item)
            if insight:
                generated.append(insight.to_dict())
    
    # 3. Check for money leaks
    if prefs.money_leak_detection_enabled:
        leaks = check_money_leaks(current_user.id, prefs.money_leak_min_occurrences)
        for item in leaks:
            insight = create_insight(current_user.id, item)
            if insight:
                generated.append(insight.to_dict())
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'generated_count': len(generated),
        'insights': generated
    })


def check_unusual_spending(user_id, threshold):
    """Check for unusual spending patterns and return insight data"""
    results = []
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    baseline_start = start_date - timedelta(days=30)
    
    recent = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.date >= start_date
    ).all()
    
    baseline = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.date >= baseline_start,
        Expense.date < start_date
    ).all()
    
    if not baseline:
        return results
    
    baseline_daily = sum(e.amount for e in baseline) / 30
    recent_daily = sum(e.amount for e in recent) / 7 if recent else 0
    
    if baseline_daily > 0 and recent_daily > baseline_daily * threshold:
        results.append({
            'insight_type': 'unusual_spending',
            'priority': 'high',
            'title_key': 'insights.unusual.overallSpike.title',
            'message_key': 'insights.unusual.overallSpike.message',
            'message_params': {
                'percentage': round(((recent_daily / baseline_daily) - 1) * 100),
                'currency': current_user.currency
            },
            'amount': round(recent_daily * 7, 2),
            'icon': 'trending_up',
            'action_key': 'insights.unusual.action.reviewSpending'
        })
    
    return results


def check_category_spikes(user_id, threshold):
    """Check for category spending spikes"""
    results = []
    
    now = datetime.utcnow()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_month_end = start_of_month - timedelta(days=1)
    prev_month_start = prev_month_end.replace(day=1)
    
    current = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.date >= start_of_month
    ).all()
    
    previous = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.date >= prev_month_start,
        Expense.date <= prev_month_end
    ).all()
    
    current_by_cat = defaultdict(float)
    prev_by_cat = defaultdict(float)
    cat_ids = {}
    
    for e in current:
        cat_name = e.category.name if e.category else 'Uncategorized'
        current_by_cat[cat_name] += e.amount
        cat_ids[cat_name] = e.category_id
    
    for e in previous:
        cat_name = e.category.name if e.category else 'Uncategorized'
        prev_by_cat[cat_name] += e.amount
    
    for cat_name, current_amount in current_by_cat.items():
        prev_amount = prev_by_cat.get(cat_name, 0)
        if prev_amount > 0 and current_amount > prev_amount * threshold and (current_amount - prev_amount) > 20:
            change = ((current_amount / prev_amount) - 1) * 100
            results.append({
                'insight_type': 'category_spike',
                'priority': 'high' if change > 100 else 'medium',
                'title_key': 'insights.category.spike.title',
                'message_key': 'insights.category.spike.message',
                'message_params': {
                    'category': cat_name,
                    'percentage': round(change),
                    'currency': current_user.currency,
                    'amount': round(current_amount - prev_amount, 2)
                },
                'category_id': cat_ids.get(cat_name),
                'amount': round(current_amount, 2),
                'comparison_data': {
                    'current': round(current_amount, 2),
                    'previous': round(prev_amount, 2)
                },
                'icon': 'trending_up',
                'action_key': 'insights.category.action.reviewCategory'
            })
    
    return results


def check_money_leaks(user_id, min_occurrences):
    """Check for money leak patterns"""
    results = []
    
    start_date = datetime.utcnow() - timedelta(days=90)
    
    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.date >= start_date
    ).all()
    
    import re
    patterns = defaultdict(lambda: {'total': 0, 'count': 0})
    
    for expense in expenses:
        desc = expense.description.lower().strip()
        desc_clean = re.sub(r'[0-9#]+', '', desc).strip()
        desc_clean = re.sub(r'\s+', ' ', desc_clean)
        amount_bucket = round(expense.amount / 5) * 5
        key = f"{desc_clean}_{amount_bucket}"
        
        patterns[key]['total'] += expense.amount
        patterns[key]['count'] += 1
        patterns[key]['desc'] = expense.description
    
    for key, data in patterns.items():
        if data['count'] >= min_occurrences:
            yearly_projection = (data['total'] / 90) * 365
            if yearly_projection > 100:  # Only flag if > £100/year
                results.append({
                    'insight_type': 'money_leak',
                    'priority': 'high' if yearly_projection > 500 else 'medium',
                    'title_key': 'insights.moneyLeak.title',
                    'message_key': 'insights.moneyLeak.message',
                    'message_params': {
                        'description': data['desc'],
                        'count': data['count'],
                        'yearly': round(yearly_projection, 2),
                        'currency': current_user.currency
                    },
                    'amount': round(data['total'], 2),
                    'comparison_data': {
                        'occurrences': data['count'],
                        'yearly_projection': round(yearly_projection, 2)
                    },
                    'icon': 'water_drop',
                    'action_key': 'insights.moneyLeak.action.reviewHabit'
                })
    
    return results[:5]  # Top 5 leaks


def create_insight(user_id, data):
    """Create a SpendingInsight record, avoiding duplicates"""
    # Check for similar recent insight (within 7 days)
    recent_similar = SpendingInsight.query.filter(
        SpendingInsight.user_id == user_id,
        SpendingInsight.insight_type == data['insight_type'],
        SpendingInsight.title_key == data['title_key'],
        SpendingInsight.created_at > datetime.utcnow() - timedelta(days=7)
    ).first()
    
    if recent_similar:
        return None  # Don't create duplicate
    
    insight = SpendingInsight(
        user_id=user_id,
        insight_type=data['insight_type'],
        priority=data.get('priority', 'medium'),
        title_key=data['title_key'],
        message_key=data['message_key'],
        icon=data.get('icon', 'insights'),
        amount=data.get('amount'),
        category_id=data.get('category_id'),
        action_key=data.get('action_key'),
        expires_at=datetime.utcnow() + timedelta(days=14)  # Expire in 2 weeks
    )
    
    insight.set_message_params(data.get('message_params', {}))
    insight.set_comparison_data(data.get('comparison_data', {}))
    
    db.session.add(insight)
    return insight


@bp.route('/summary', methods=['GET'])
@login_required
def get_insights_summary():
    """Get summary of insights for dashboard display"""
    # Count by type
    type_counts = db.session.query(
        SpendingInsight.insight_type,
        func.count(SpendingInsight.id)
    ).filter(
        SpendingInsight.user_id == current_user.id,
        SpendingInsight.is_dismissed == False,
        db.or_(
            SpendingInsight.expires_at == None,
            SpendingInsight.expires_at > datetime.utcnow()
        )
    ).group_by(SpendingInsight.insight_type).all()
    
    # Count unread
    unread_count = SpendingInsight.query.filter(
        SpendingInsight.user_id == current_user.id,
        SpendingInsight.is_read == False,
        SpendingInsight.is_dismissed == False
    ).count()
    
    # Get high priority insights
    high_priority = SpendingInsight.query.filter(
        SpendingInsight.user_id == current_user.id,
        SpendingInsight.priority == 'high',
        SpendingInsight.is_dismissed == False
    ).order_by(SpendingInsight.created_at.desc()).limit(3).all()
    
    return jsonify({
        'success': True,
        'summary': {
            'total': sum(c[1] for c in type_counts),
            'unread': unread_count,
            'by_type': {t: c for t, c in type_counts},
            'high_priority': [i.to_dict() for i in high_priority]
        }
    })
