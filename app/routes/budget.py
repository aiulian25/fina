"""
Budget Alerts API
Provides budget status, alerts, and notification management
Security: All queries filtered by user_id
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import Category, Expense
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func

bp = Blueprint('budget', __name__, url_prefix='/api/budget')


@bp.route('/status', methods=['GET'])
@login_required
def get_budget_status():
    """
    Get budget status for all user categories and overall monthly budget
    Security: Only returns current user's data
    
    Returns:
    - overall: Total spending vs monthly budget
    - categories: Per-category budget status
    - alerts: Active budget alerts
    """
    # Get current month date range
    now = datetime.utcnow()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Calculate overall monthly spending - Security: filter by user_id
    total_spent = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_of_month
    ).scalar() or 0.0
    
    overall_status = {
        'spent': float(total_spent),
        'budget': current_user.monthly_budget or 0,
        'remaining': (current_user.monthly_budget or 0) - float(total_spent),
        'percentage': 0 if not current_user.monthly_budget else round((float(total_spent) / current_user.monthly_budget) * 100, 1),
        'alert_level': 'none'
    }
    
    # Determine overall alert level
    if current_user.monthly_budget and current_user.monthly_budget > 0:
        if overall_status['percentage'] >= 100:
            overall_status['alert_level'] = 'exceeded'
        elif overall_status['percentage'] >= 90:
            overall_status['alert_level'] = 'danger'
        elif overall_status['percentage'] >= 80:
            overall_status['alert_level'] = 'warning'
    
    # Get category budgets - Security: filter by user_id
    categories = Category.query.filter_by(user_id=current_user.id).all()
    category_statuses = []
    active_alerts = []
    
    for category in categories:
        if category.monthly_budget and category.monthly_budget > 0:
            status = category.get_budget_status()
            category_statuses.append({
                'category_id': category.id,
                'category_name': category.name,
                'category_color': category.color,
                'category_icon': category.icon,
                **status
            })
            
            # Add to alerts if over threshold
            if status['alert_level'] in ['warning', 'danger', 'exceeded']:
                active_alerts.append({
                    'category_id': category.id,
                    'category_name': category.name,
                    'category_color': category.color,
                    'alert_level': status['alert_level'],
                    'percentage': status['percentage'],
                    'spent': status['spent'],
                    'budget': status['budget'],
                    'remaining': status['remaining']
                })
    
    # Sort alerts by severity
    alert_order = {'exceeded': 0, 'danger': 1, 'warning': 2}
    active_alerts.sort(key=lambda x: (alert_order[x['alert_level']], -x['percentage']))
    
    return jsonify({
        'success': True,
        'overall': overall_status,
        'categories': category_statuses,
        'alerts': active_alerts,
        'alert_count': len(active_alerts)
    })


@bp.route('/weekly-summary', methods=['GET'])
@login_required
def get_weekly_summary():
    """
    Get weekly spending summary for notification
    Security: Only returns current user's data
    
    Returns:
    - week_total: Total spent this week
    - daily_average: Average per day
    - top_category: Highest spending category
    - comparison: vs previous week
    """
    now = datetime.utcnow()
    week_start = now - timedelta(days=now.weekday())  # Monday
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    
    prev_week_start = week_start - timedelta(days=7)
    
    # Current week spending - Security: filter by user_id
    current_week_expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= week_start
    ).all()
    
    week_total = sum(e.amount for e in current_week_expenses)
    daily_average = week_total / max(1, (now - week_start).days + 1)
    
    # Previous week for comparison
    prev_week_expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= prev_week_start,
        Expense.date < week_start
    ).all()
    
    prev_week_total = sum(e.amount for e in prev_week_expenses)
    change_percent = 0
    if prev_week_total > 0:
        change_percent = ((week_total - prev_week_total) / prev_week_total) * 100
    
    # Find top category
    category_totals = {}
    for expense in current_week_expenses:
        if expense.category:
            category_totals[expense.category.name] = category_totals.get(expense.category.name, 0) + expense.amount
    
    top_category = max(category_totals.items(), key=lambda x: x[1]) if category_totals else (None, 0)
    
    return jsonify({
        'success': True,
        'week_total': float(week_total),
        'daily_average': float(daily_average),
        'previous_week_total': float(prev_week_total),
        'change_percent': round(change_percent, 1),
        'top_category': top_category[0] if top_category[0] else 'None',
        'top_category_amount': float(top_category[1]),
        'expense_count': len(current_week_expenses),
        'week_start': week_start.isoformat(),
        'currency': current_user.currency
    })


@bp.route('/category/<int:category_id>/budget', methods=['PUT'])
@login_required
def update_category_budget(category_id):
    """
    Update budget settings for a category
    Security: Verify category belongs to current user
    """
    # Security check: ensure category belongs to current user
    category = Category.query.filter_by(id=category_id, user_id=current_user.id).first()
    
    if not category:
        return jsonify({'success': False, 'message': 'Category not found'}), 404
    
    data = request.get_json()
    
    try:
        if 'monthly_budget' in data:
            budget = float(data['monthly_budget']) if data['monthly_budget'] else None
            if budget is not None and budget < 0:
                return jsonify({'success': False, 'message': 'Budget cannot be negative'}), 400
            category.monthly_budget = budget
        
        if 'budget_alert_threshold' in data:
            threshold = float(data['budget_alert_threshold'])
            if threshold < 0.5 or threshold > 2.0:
                return jsonify({'success': False, 'message': 'Threshold must be between 0.5 (50%) and 2.0 (200%)'}), 400
            category.budget_alert_threshold = threshold
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Budget updated successfully',
            'category': category.to_dict()
        })
    except ValueError as e:
        return jsonify({'success': False, 'message': f'Invalid data: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error updating budget: {str(e)}'}), 500
