from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Expense, Category
from sqlalchemy import func, extract
from datetime import datetime, timedelta
from collections import defaultdict

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('dashboard.html')
    return render_template('landing.html')


@bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@bp.route('/transactions')
@login_required
def transactions():
    return render_template('transactions.html')


@bp.route('/reports')
@login_required
def reports():
    return render_template('reports.html')


@bp.route('/settings')
@login_required
def settings():
    return render_template('settings.html')


@bp.route('/documents')
@login_required
def documents():
    return render_template('documents.html')


@bp.route('/api/dashboard-stats')
@login_required
def dashboard_stats():
    now = datetime.utcnow()
    
    # Current month stats
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Previous month stats
    if now.month == 1:
        prev_month_start = now.replace(year=now.year-1, month=12, day=1)
    else:
        prev_month_start = current_month_start.replace(month=current_month_start.month-1)
    
    # Total spent this month
    current_month_total = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == current_user.id,
        Expense.date >= current_month_start,
        Expense.currency == current_user.currency
    ).scalar() or 0
    
    # Previous month total
    prev_month_total = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == current_user.id,
        Expense.date >= prev_month_start,
        Expense.date < current_month_start,
        Expense.currency == current_user.currency
    ).scalar() or 0
    
    # Calculate percentage change
    if prev_month_total > 0:
        percent_change = ((current_month_total - prev_month_total) / prev_month_total) * 100
    else:
        percent_change = 100 if current_month_total > 0 else 0
    
    # Active categories
    active_categories = Category.query.filter_by(user_id=current_user.id).count()
    
    # Total transactions this month
    total_transactions = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= current_month_start
    ).count()
    
    # Category breakdown
    category_stats = db.session.query(
        Category.name,
        Category.color,
        func.sum(Expense.amount).label('total')
    ).join(Expense).filter(
        Expense.user_id == current_user.id,
        Expense.date >= current_month_start,
        Expense.currency == current_user.currency
    ).group_by(Category.id).all()
    
    # Monthly breakdown (last 6 months)
    monthly_data = []
    for i in range(5, -1, -1):
        month_date = now - timedelta(days=30*i)
        month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if month_date.month == 12:
            month_end = month_date.replace(year=month_date.year+1, month=1, day=1)
        else:
            month_end = month_date.replace(month=month_date.month+1, day=1)
        
        month_total = db.session.query(func.sum(Expense.amount)).filter(
            Expense.user_id == current_user.id,
            Expense.date >= month_start,
            Expense.date < month_end,
            Expense.currency == current_user.currency
        ).scalar() or 0
        
        monthly_data.append({
            'month': month_start.strftime('%b'),
            'total': float(month_total)
        })
    
    return jsonify({
        'total_spent': float(current_month_total),
        'percent_change': round(percent_change, 1),
        'active_categories': active_categories,
        'total_transactions': total_transactions,
        'currency': current_user.currency,
        'category_breakdown': [
            {'name': stat[0], 'color': stat[1], 'amount': float(stat[2])}
            for stat in category_stats
        ],
        'monthly_data': monthly_data
    })


@bp.route('/api/recent-transactions')
@login_required
def recent_transactions():
    limit = request.args.get('limit', 10, type=int)
    
    expenses = Expense.query.filter_by(user_id=current_user.id)\
        .order_by(Expense.date.desc())\
        .limit(limit)\
        .all()
    
    return jsonify({
        'transactions': [expense.to_dict() for expense in expenses]
    })


@bp.route('/api/reports-stats')
@login_required
def reports_stats():
    """
    Generate comprehensive financial reports
    Security: Only returns data for current_user (enforced by user_id filter)
    """
    period = request.args.get('period', '30')  # days
    category_filter = request.args.get('category_id', type=int)
    
    try:
        days = int(period)
    except ValueError:
        days = 30
    
    now = datetime.utcnow()
    period_start = now - timedelta(days=days)
    
    # Query with security filter
    query = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= period_start
    )
    
    if category_filter:
        query = query.filter_by(category_id=category_filter)
    
    expenses = query.all()
    
    # Total spent in period
    total_spent = sum(exp.amount for exp in expenses if exp.currency == current_user.currency)
    
    # Previous period comparison
    prev_period_start = period_start - timedelta(days=days)
    prev_expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= prev_period_start,
        Expense.date < period_start,
        Expense.currency == current_user.currency
    ).all()
    prev_total = sum(exp.amount for exp in prev_expenses)
    
    percent_change = 0
    if prev_total > 0:
        percent_change = ((total_spent - prev_total) / prev_total) * 100
    elif total_spent > 0:
        percent_change = 100
    
    # Top category
    category_totals = {}
    for exp in expenses:
        if exp.currency == current_user.currency:
            cat_name = exp.category.name
            category_totals[cat_name] = category_totals.get(cat_name, 0) + exp.amount
    
    top_category = max(category_totals.items(), key=lambda x: x[1]) if category_totals else ('None', 0)
    
    # Average daily spending
    avg_daily = total_spent / days if days > 0 else 0
    prev_avg_daily = prev_total / days if days > 0 else 0
    avg_change = 0
    if prev_avg_daily > 0:
        avg_change = ((avg_daily - prev_avg_daily) / prev_avg_daily) * 100
    elif avg_daily > 0:
        avg_change = 100
    
    # Savings rate (placeholder - would need income data)
    savings_rate = 18.5  # Placeholder
    
    # Category breakdown for pie chart
    category_breakdown = []
    for cat_name, amount in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
        category = Category.query.filter_by(user_id=current_user.id, name=cat_name).first()
        if category:
            percentage = (amount / total_spent * 100) if total_spent > 0 else 0
            category_breakdown.append({
                'name': cat_name,
                'color': category.color,
                'amount': float(amount),
                'percentage': round(percentage, 1)
            })
    
    # Daily spending trend (last 30 days)
    daily_trend = []
    for i in range(min(30, days)):
        day_date = now - timedelta(days=i)
        day_start = day_date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        day_total = db.session.query(func.sum(Expense.amount)).filter(
            Expense.user_id == current_user.id,
            Expense.date >= day_start,
            Expense.date < day_end,
            Expense.currency == current_user.currency
        ).scalar() or 0
        
        daily_trend.insert(0, {
            'date': day_date.strftime('%d %b'),
            'amount': float(day_total)
        })
    
    # Monthly comparison (last 6 months)
    monthly_comparison = []
    for i in range(5, -1, -1):
        month_date = now - timedelta(days=30*i)
        month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if month_date.month == 12:
            month_end = month_date.replace(year=month_date.year+1, month=1, day=1)
        else:
            month_end = month_date.replace(month=month_date.month+1, day=1)
        
        month_total = db.session.query(func.sum(Expense.amount)).filter(
            Expense.user_id == current_user.id,
            Expense.date >= month_start,
            Expense.date < month_end,
            Expense.currency == current_user.currency
        ).scalar() or 0
        
        monthly_comparison.append({
            'month': month_start.strftime('%b'),
            'amount': float(month_total)
        })
    
    return jsonify({
        'total_spent': float(total_spent),
        'percent_change': round(percent_change, 1),
        'top_category': {'name': top_category[0], 'amount': float(top_category[1])},
        'avg_daily': float(avg_daily),
        'avg_daily_change': round(avg_change, 1),
        'savings_rate': savings_rate,
        'category_breakdown': category_breakdown,
        'daily_trend': daily_trend,
        'monthly_comparison': monthly_comparison,
        'currency': current_user.currency,
        'period_days': days
    })
