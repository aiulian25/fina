from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Expense, Category, Income
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


@bp.route('/recurring')
@login_required
def recurring():
    return render_template('recurring.html')


@bp.route('/import')
@login_required
def import_page():
    return render_template('import.html')


@bp.route('/income')
@login_required
def income():
    return render_template('income.html')


@bp.route('/goals')
@login_required
def goals():
    return render_template('goals.html')


@bp.route('/subscriptions')
@login_required
def subscriptions():
    return render_template('subscriptions.html')


@bp.route('/analyzer')
@login_required
def analyzer():
    return render_template('analyzer.html')


@bp.route('/insights')
@login_required
def insights():
    return render_template('insights.html')


@bp.route('/challenges')
@login_required
def challenges():
    return render_template('challenges.html')


@bp.route('/forecast')
@login_required
def forecast():
    return render_template('forecast.html')


@bp.route('/admin')
@login_required
def admin():
    if not current_user.is_admin:
        return render_template('404.html'), 404
    return render_template('admin.html')


@bp.route('/api/available-years')
@login_required
def available_years():
    """
    Get available years with data for current user.
    Security: Only returns years for current_user's data.
    """
    # Get distinct years from expenses
    expense_years = db.session.query(
        extract('year', Expense.date).label('year')
    ).filter(
        Expense.user_id == current_user.id
    ).distinct().all()
    
    # Get distinct years from income
    income_years = db.session.query(
        extract('year', Income.date).label('year')
    ).filter(
        Income.user_id == current_user.id
    ).distinct().all()
    
    # Combine and sort years
    all_years = set()
    for row in expense_years:
        if row.year:
            all_years.add(int(row.year))
    for row in income_years:
        if row.year:
            all_years.add(int(row.year))
    
    # Always include current year
    current_year = datetime.utcnow().year
    all_years.add(current_year)
    
    return jsonify({
        'years': sorted(list(all_years), reverse=True),
        'current_year': current_year
    })


@bp.route('/api/dashboard-stats')
@login_required
def dashboard_stats():
    now = datetime.utcnow()
    
    # Get optional year filter from query params
    filter_year = request.args.get('year', type=int)
    if filter_year is None:
        filter_year = now.year
    
    # Validate year (security: prevent extreme values)
    if filter_year < 2000 or filter_year > 2100:
        filter_year = now.year
    
    # Current month stats (always current month for KPIs)
    current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # Previous month stats
    if now.month == 1:
        prev_month_start = now.replace(year=now.year-1, month=12, day=1)
    else:
        prev_month_start = current_month_start.replace(month=current_month_start.month-1)
    
    # Total spent this month (all currencies - show user's preferred currency)
    current_month_expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= current_month_start
    ).all()
    current_month_total = sum(exp.amount for exp in current_month_expenses)
    
    # Previous month total
    prev_month_expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= prev_month_start,
        Expense.date < current_month_start
    ).all()
    prev_month_total = sum(exp.amount for exp in prev_month_expenses)
    
    # Current month income
    current_month_income = Income.query.filter(
        Income.user_id == current_user.id,
        Income.date >= current_month_start
    ).all()
    current_income_total = sum(inc.amount for inc in current_month_income)
    
    # Previous month income
    prev_month_income = Income.query.filter(
        Income.user_id == current_user.id,
        Income.date >= prev_month_start,
        Income.date < current_month_start
    ).all()
    prev_income_total = sum(inc.amount for inc in prev_month_income)
    
    # Calculate profit/loss
    current_profit = current_income_total - current_month_total
    prev_profit = prev_income_total - prev_month_total
    
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
    
    # Category breakdown for selected year (charts filter)
    selected_year_start = datetime(filter_year, 1, 1, 0, 0, 0)
    selected_year_end = datetime(filter_year + 1, 1, 1, 0, 0, 0)
    
    category_stats = db.session.query(
        Category.id,
        Category.name,
        Category.color,
        Category.icon,
        func.sum(Expense.amount).label('total'),
        func.count(Expense.id).label('count')
    ).join(Expense).filter(
        Expense.user_id == current_user.id,
        Expense.date >= selected_year_start,
        Expense.date < selected_year_end
    ).group_by(Category.id).order_by(Category.display_order, Category.created_at).all()
    
    # Monthly breakdown for selected year - including income
    monthly_data = []
    for month_num in range(1, 13):
        month_start = datetime(filter_year, month_num, 1, 0, 0, 0)
        if month_num == 12:
            month_end = datetime(filter_year + 1, 1, 1, 0, 0, 0)
        else:
            month_end = datetime(filter_year, month_num + 1, 1, 0, 0, 0)
        
        month_expenses = Expense.query.filter(
            Expense.user_id == current_user.id,
            Expense.date >= month_start,
            Expense.date < month_end
        ).all()
        month_total = sum(exp.amount for exp in month_expenses)
        
        month_income_list = Income.query.filter(
            Income.user_id == current_user.id,
            Income.date >= month_start,
            Income.date < month_end
        ).all()
        month_income = sum(inc.amount for inc in month_income_list)
        
        monthly_data.append({
            'month': month_start.strftime('%b'),
            'month_num': month_num,
            'expenses': float(month_total),
            'income': float(month_income),
            'profit': float(month_income - month_total)
        })
    
    # Add budget status to category breakdown
    category_breakdown = []
    for stat in category_stats:
        cat = Category.query.get(stat[0])
        cat_data = {
            'id': stat[0],
            'name': stat[1],
            'color': stat[2],
            'icon': stat[3],
            'total': float(stat[4]),
            'count': stat[5]
        }
        if cat:
            cat_data['budget_status'] = cat.get_budget_status()
            cat_data['monthly_budget'] = cat.monthly_budget
            cat_data['budget_alert_threshold'] = cat.budget_alert_threshold
        category_breakdown.append(cat_data)
    
    return jsonify({
        'total_spent': float(current_month_total),
        'total_income': float(current_income_total),
        'profit_loss': float(current_profit),
        'percent_change': round(percent_change, 1),
        'active_categories': active_categories,
        'total_transactions': total_transactions,
        'currency': current_user.currency,
        'category_breakdown': category_breakdown,
        'monthly_data': monthly_data,
        'selected_year': filter_year
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
    Generate comprehensive financial reports including income tracking
    Security: Only returns data for current_user (enforced by user_id filter)
    """
    period = request.args.get('period', '30')  # days
    category_filter = request.args.get('category_id', type=int)
    
    # Get year filter from query params
    filter_year = request.args.get('year', type=int)
    now = datetime.utcnow()
    
    if filter_year is None:
        filter_year = now.year
    
    # Validate year (security: prevent extreme values)
    if filter_year < 2000 or filter_year > 2100:
        filter_year = now.year
    
    try:
        days = int(period)
    except ValueError:
        days = 30
    
    # Calculate period_start and period_end based on year selection
    # If viewing current year, use relative days from now
    # If viewing past year, show data from that year based on period
    if filter_year == now.year:
        # Current year: use relative days from today
        period_end = now
        period_start = now - timedelta(days=days)
    else:
        # Past year: show data relative to end of that year
        year_end = datetime(filter_year, 12, 31, 23, 59, 59)
        period_end = year_end
        period_start = year_end - timedelta(days=days)
        # Ensure period_start doesn't go before the year starts
        year_start = datetime(filter_year, 1, 1)
        if period_start < year_start:
            period_start = year_start
    
    # Query expenses with security filter
    query = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= period_start,
        Expense.date <= period_end
    )
    
    if category_filter:
        query = query.filter_by(category_id=category_filter)
    
    expenses = query.all()
    
    # Query income for the same period
    income_query = Income.query.filter(
        Income.user_id == current_user.id,
        Income.date >= period_start,
        Income.date <= period_end
    )
    incomes = income_query.all()
    
    # Total spent and earned in period
    total_spent = sum(exp.amount for exp in expenses)
    total_income = sum(inc.amount for inc in incomes)
    
    # Previous period comparison for expenses and income
    actual_days = (period_end - period_start).days or 1
    prev_period_start = period_start - timedelta(days=actual_days)
    prev_period_end = period_start
    
    prev_expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= prev_period_start,
        Expense.date < prev_period_end
    ).all()
    prev_total = sum(exp.amount for exp in prev_expenses)
    
    prev_incomes = Income.query.filter(
        Income.user_id == current_user.id,
        Income.date >= prev_period_start,
        Income.date < prev_period_end
    ).all()
    prev_income_total = sum(inc.amount for inc in prev_incomes)
    
    # Calculate profit/loss
    current_profit = total_income - total_spent
    prev_profit = prev_income_total - prev_total
    
    percent_change = 0
    if prev_total > 0:
        percent_change = ((total_spent - prev_total) / prev_total) * 100
    elif total_spent > 0:
        percent_change = 100
    
    # Income change percentage
    income_percent_change = 0
    if prev_income_total > 0:
        income_percent_change = ((total_income - prev_income_total) / prev_income_total) * 100
    elif total_income > 0:
        income_percent_change = 100
    
    # Profit/loss change percentage
    profit_percent_change = 0
    if prev_profit != 0:
        profit_percent_change = ((current_profit - prev_profit) / abs(prev_profit)) * 100
    elif current_profit != 0:
        profit_percent_change = 100
    
    # Top category (all currencies)
    category_totals = {}
    for exp in expenses:
        cat_name = exp.category.name
        category_totals[cat_name] = category_totals.get(cat_name, 0) + exp.amount
    
    top_category = max(category_totals.items(), key=lambda x: x[1]) if category_totals else ('None', 0)
    
    # Average daily spending (use actual_days for accurate calculation)
    avg_daily = total_spent / actual_days if actual_days > 0 else 0
    prev_avg_daily = prev_total / actual_days if actual_days > 0 else 0
    avg_change = 0
    if prev_avg_daily > 0:
        avg_change = ((avg_daily - prev_avg_daily) / prev_avg_daily) * 100
    elif avg_daily > 0:
        avg_change = 100
    
    # Savings rate calculation based on income (more accurate than budget)
    if total_income > 0:
        savings_amount = total_income - total_spent
        savings_rate = (savings_amount / total_income) * 100
        savings_rate = max(-100, min(100, savings_rate))  # Clamp between -100% and 100%
    else:
        # Fallback to budget if no income data
        if current_user.monthly_budget and current_user.monthly_budget > 0:
            savings_amount = current_user.monthly_budget - total_spent
            savings_rate = (savings_amount / current_user.monthly_budget) * 100
            savings_rate = max(0, min(100, savings_rate))
        else:
            savings_rate = 0
    
    # Previous period savings rate
    if prev_income_total > 0:
        prev_savings_amount = prev_income_total - prev_total
        prev_savings_rate = (prev_savings_amount / prev_income_total) * 100
        prev_savings_rate = max(-100, min(100, prev_savings_rate))
    else:
        if current_user.monthly_budget and current_user.monthly_budget > 0:
            prev_savings_amount = current_user.monthly_budget - prev_total
            prev_savings_rate = (prev_savings_amount / current_user.monthly_budget) * 100
            prev_savings_rate = max(0, min(100, prev_savings_rate))
        else:
            prev_savings_rate = 0
    
    savings_rate_change = savings_rate - prev_savings_rate
    
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
    
    # Daily spending and income trend (last 30 days of the selected period)
    daily_trend = []
    trend_days = min(30, actual_days)
    for i in range(trend_days):
        day_date = period_end - timedelta(days=i)
        day_start = day_date.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        day_expenses = Expense.query.filter(
            Expense.user_id == current_user.id,
            Expense.date >= day_start,
            Expense.date < day_end
        ).all()
        day_total = sum(exp.amount for exp in day_expenses)
        
        day_incomes = Income.query.filter(
            Income.user_id == current_user.id,
            Income.date >= day_start,
            Income.date < day_end
        ).all()
        day_income = sum(inc.amount for inc in day_incomes)
        
        daily_trend.insert(0, {
            'date': day_date.strftime('%d %b'),
            'expenses': float(day_total),
            'income': float(day_income),
            'profit': float(day_income - day_total)
        })
    
    # Monthly comparison with income (all 12 months of selected year)
    monthly_comparison = []
    for month in range(1, 13):
        month_start = datetime(filter_year, month, 1)
        if month == 12:
            month_end = datetime(filter_year + 1, 1, 1)
        else:
            month_end = datetime(filter_year, month + 1, 1)
        
        month_expenses = Expense.query.filter(
            Expense.user_id == current_user.id,
            Expense.date >= month_start,
            Expense.date < month_end
        ).all()
        month_total = sum(exp.amount for exp in month_expenses)
        
        month_incomes = Income.query.filter(
            Income.user_id == current_user.id,
            Income.date >= month_start,
            Income.date < month_end
        ).all()
        month_income = sum(inc.amount for inc in month_incomes)
        
        monthly_comparison.append({
            'month': month_start.strftime('%b'),
            'expenses': float(month_total),
            'income': float(month_income),
            'profit': float(month_income - month_total)
        })
    
    # Income sources breakdown
    income_by_source = {}
    for inc in incomes:
        source = inc.source
        income_by_source[source] = income_by_source.get(source, 0) + inc.amount
    
    income_breakdown = [{
        'source': source,
        'amount': float(amount),
        'percentage': round((amount / total_income * 100) if total_income > 0 else 0, 1)
    } for source, amount in sorted(income_by_source.items(), key=lambda x: x[1], reverse=True)]
    
    return jsonify({
        'total_spent': float(total_spent),
        'total_income': float(total_income),
        'profit_loss': float(current_profit),
        'percent_change': round(percent_change, 1),
        'income_percent_change': round(income_percent_change, 1),
        'profit_percent_change': round(profit_percent_change, 1),
        'top_category': {'name': top_category[0], 'amount': float(top_category[1])},
        'avg_daily': float(avg_daily),
        'avg_daily_change': round(avg_change, 1),
        'savings_rate': round(savings_rate, 1),
        'savings_rate_change': round(savings_rate_change, 1),
        'category_breakdown': category_breakdown,
        'income_breakdown': income_breakdown,
        'daily_trend': daily_trend,
        'monthly_comparison': monthly_comparison,
        'currency': current_user.currency,
        'period_days': days,
        'selected_year': filter_year
    })


@bp.route('/api/smart-recommendations')
@login_required
def smart_recommendations():
    """
    Generate smart financial recommendations based on user spending patterns
    Security: Only returns recommendations for current_user
    """
    now = datetime.utcnow()
    
    # Get data for last 30 and 60 days for comparison
    period_30 = now - timedelta(days=30)
    period_60 = now - timedelta(days=60)
    period_30_start = period_60
    
    # Current period expenses (all currencies)
    current_expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= period_30
    ).all()
    
    # Previous period expenses (all currencies)
    previous_expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= period_60,
        Expense.date < period_30
    ).all()
    
    current_total = sum(exp.amount for exp in current_expenses)
    previous_total = sum(exp.amount for exp in previous_expenses)
    
    # Category analysis
    current_by_category = defaultdict(float)
    previous_by_category = defaultdict(float)
    
    for exp in current_expenses:
        current_by_category[exp.category.name] += exp.amount
    
    for exp in previous_expenses:
        previous_by_category[exp.category.name] += exp.amount
    
    recommendations = []
    
    # Recommendation 1: Budget vs Spending
    if current_user.monthly_budget and current_user.monthly_budget > 0:
        budget_used_percent = (current_total / current_user.monthly_budget) * 100
        remaining = current_user.monthly_budget - current_total
        
        if budget_used_percent > 90:
            recommendations.append({
                'type': 'warning',
                'icon': 'warning',
                'color': 'red',
                'title': 'Budget Alert' if current_user.language == 'en' else 'Alertă Buget',
                'description': f'You\'ve used {budget_used_percent:.1f}% of your monthly budget. Only {abs(remaining):.2f} {current_user.currency} remaining.' if current_user.language == 'en' else f'Ai folosit {budget_used_percent:.1f}% din bugetul lunar. Mai rămân doar {abs(remaining):.2f} {current_user.currency}.'
            })
        elif budget_used_percent < 70 and remaining > 0:
            recommendations.append({
                'type': 'success',
                'icon': 'trending_up',
                'color': 'green',
                'title': 'Great Savings Opportunity' if current_user.language == 'en' else 'Oportunitate de Economisire',
                'description': f'You have {remaining:.2f} {current_user.currency} remaining from your budget. Consider saving or investing it.' if current_user.language == 'en' else f'Mai ai {remaining:.2f} {current_user.currency} din buget. Consideră să economisești sau să investești.'
            })
    
    # Recommendation 2: Category spending changes
    for category_name, current_amount in current_by_category.items():
        if category_name in previous_by_category:
            previous_amount = previous_by_category[category_name]
            if previous_amount > 0:
                change_percent = ((current_amount - previous_amount) / previous_amount) * 100
                
                if change_percent > 50:  # 50% increase
                    recommendations.append({
                        'type': 'warning',
                        'icon': 'trending_up',
                        'color': 'yellow',
                        'title': f'{category_name} Spending Up' if current_user.language == 'en' else f'Cheltuieli {category_name} în Creștere',
                        'description': f'Your {category_name} spending increased by {change_percent:.0f}%. Review recent transactions.' if current_user.language == 'en' else f'Cheltuielile pentru {category_name} au crescut cu {change_percent:.0f}%. Revizuiește tranzacțiile recente.'
                    })
                elif change_percent < -30:  # 30% decrease
                    recommendations.append({
                        'type': 'success',
                        'icon': 'trending_down',
                        'color': 'green',
                        'title': f'{category_name} Savings' if current_user.language == 'en' else f'Economii {category_name}',
                        'description': f'Great job! You reduced {category_name} spending by {abs(change_percent):.0f}%.' if current_user.language == 'en' else f'Foarte bine! Ai redus cheltuielile pentru {category_name} cu {abs(change_percent):.0f}%.'
                    })
    
    # Recommendation 3: Unusual transactions
    if current_expenses:
        category_averages = {}
        for category_name, amount in current_by_category.items():
            count = sum(1 for exp in current_expenses if exp.category.name == category_name)
            category_averages[category_name] = amount / count if count > 0 else 0
        
        for exp in current_expenses[-10:]:  # Check last 10 transactions
            category_avg = category_averages.get(exp.category.name, 0)
            if category_avg > 0 and exp.amount > category_avg * 2:  # 200% of average
                recommendations.append({
                    'type': 'info',
                    'icon': 'info',
                    'color': 'blue',
                    'title': 'Unusual Transaction' if current_user.language == 'en' else 'Tranzacție Neobișnuită',
                    'description': f'A transaction of {exp.amount:.2f} {current_user.currency} in {exp.category.name} is higher than usual.' if current_user.language == 'en' else f'O tranzacție de {exp.amount:.2f} {current_user.currency} în {exp.category.name} este mai mare decât de obicei.'
                })
                break  # Only show one unusual transaction warning
    
    # Limit to top 3 recommendations
    recommendations = recommendations[:3]
    
    # If no recommendations, add a positive message
    if not recommendations:
        recommendations.append({
            'type': 'success',
            'icon': 'check_circle',
            'color': 'green',
            'title': 'Spending on Track' if current_user.language == 'en' else 'Cheltuieli sub Control',
            'description': 'Your spending patterns look healthy. Keep up the good work!' if current_user.language == 'en' else 'Obiceiurile tale de cheltuieli arată bine. Continuă așa!'
        })
    
    return jsonify({
        'success': True,
        'recommendations': recommendations
    })
