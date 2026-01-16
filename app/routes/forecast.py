"""
Spending Forecast API Routes
Features:
- "At this rate" end-of-month predictions
- Cash flow forecasting
- Bill due date calendar
- Category-wise spending projections

Security: All queries filtered by current_user.id
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Expense, Income, RecurringExpense, Category, User
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy import func, and_, extract
from collections import defaultdict
import calendar

bp = Blueprint('forecast', __name__, url_prefix='/api/forecast')


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_month_days_info(year, month):
    """Get information about a month"""
    _, days_in_month = calendar.monthrange(year, month)
    today = datetime.utcnow().date()
    
    if year == today.year and month == today.month:
        days_passed = today.day
        days_remaining = days_in_month - today.day
        is_current_month = True
    elif datetime(year, month, 1).date() < today:
        days_passed = days_in_month
        days_remaining = 0
        is_current_month = False
    else:
        days_passed = 0
        days_remaining = days_in_month
        is_current_month = False
    
    return {
        'days_in_month': days_in_month,
        'days_passed': days_passed,
        'days_remaining': days_remaining,
        'is_current_month': is_current_month
    }


def get_historical_spending(user_id, months=6):
    """Get historical monthly spending data"""
    today = datetime.utcnow()
    start_date = today - relativedelta(months=months)
    
    expenses = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.date >= start_date
    ).all()
    
    monthly_totals = defaultdict(float)
    for expense in expenses:
        key = expense.date.strftime('%Y-%m')
        monthly_totals[key] += expense.amount
    
    return dict(monthly_totals)


def get_category_spending_history(user_id, months=3):
    """Get historical category spending for predictions"""
    today = datetime.utcnow()
    start_date = today - relativedelta(months=months)
    
    expenses = db.session.query(
        Category.id,
        Category.name,
        Category.color,
        Category.icon,
        func.sum(Expense.amount).label('total'),
        func.count(Expense.id).label('count')
    ).join(Expense).filter(
        Expense.user_id == user_id,
        Expense.date >= start_date
    ).group_by(Category.id).all()
    
    return [
        {
            'id': e.id,
            'name': e.name,
            'color': e.color,
            'icon': e.icon,
            'total': float(e.total) if e.total else 0,
            'count': e.count,
            'monthly_avg': float(e.total) / months if e.total else 0
        }
        for e in expenses
    ]


def calculate_daily_average(user_id, days=30):
    """Calculate daily spending average over a period"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    total = db.session.query(func.sum(Expense.amount)).filter(
        Expense.user_id == user_id,
        Expense.date >= start_date,
        Expense.date <= end_date
    ).scalar() or 0
    
    return float(total) / days


# ============================================================================
# MAIN FORECAST ENDPOINTS
# ============================================================================

@bp.route('/summary', methods=['GET'])
@login_required
def get_forecast_summary():
    """Get spending forecast summary for current month"""
    try:
        today = datetime.utcnow()
        month_info = get_month_days_info(today.year, today.month)
        
        # Get current month spending
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        current_spending = db.session.query(func.sum(Expense.amount)).filter(
            Expense.user_id == current_user.id,
            Expense.date >= start_of_month
        ).scalar() or 0
        current_spending = float(current_spending)
        
        # Calculate daily average (so far this month)
        daily_avg_this_month = current_spending / max(month_info['days_passed'], 1)
        
        # Get last 30 days average for better prediction
        daily_avg_30_days = calculate_daily_average(current_user.id, 30)
        
        # Use weighted average (70% recent, 30% this month)
        if month_info['days_passed'] >= 7:
            predicted_daily = (daily_avg_this_month * 0.5) + (daily_avg_30_days * 0.5)
        else:
            predicted_daily = daily_avg_30_days
        
        # Calculate predicted end-of-month total
        predicted_total = current_spending + (predicted_daily * month_info['days_remaining'])
        
        # Get user's monthly budget
        monthly_budget = current_user.monthly_budget or 0
        
        # Calculate budget status
        if monthly_budget > 0:
            current_percentage = (current_spending / monthly_budget) * 100
            predicted_percentage = (predicted_total / monthly_budget) * 100
            predicted_over = predicted_total > monthly_budget
            predicted_difference = predicted_total - monthly_budget
        else:
            current_percentage = 0
            predicted_percentage = 0
            predicted_over = False
            predicted_difference = 0
        
        # Get upcoming bills (next 30 days)
        upcoming_bills_total = get_upcoming_bills_total(current_user.id, 30)
        upcoming_bills_this_month = get_upcoming_bills_total(
            current_user.id, 
            month_info['days_remaining']
        )
        
        # Adjust prediction with known upcoming bills
        adjusted_prediction = current_spending + (predicted_daily * month_info['days_remaining'])
        
        # Get historical comparison
        last_month_start = start_of_month - relativedelta(months=1)
        last_month_end = start_of_month - timedelta(seconds=1)
        
        last_month_total = db.session.query(func.sum(Expense.amount)).filter(
            Expense.user_id == current_user.id,
            Expense.date >= last_month_start,
            Expense.date <= last_month_end
        ).scalar() or 0
        last_month_total = float(last_month_total)
        
        # Same point last month comparison
        last_month_same_point = last_month_start.replace(day=min(month_info['days_passed'], 28))
        spending_at_same_point = db.session.query(func.sum(Expense.amount)).filter(
            Expense.user_id == current_user.id,
            Expense.date >= last_month_start,
            Expense.date <= last_month_same_point
        ).scalar() or 0
        spending_at_same_point = float(spending_at_same_point)
        
        if spending_at_same_point > 0:
            vs_last_month_percentage = ((current_spending - spending_at_same_point) / spending_at_same_point) * 100
        else:
            vs_last_month_percentage = 0
        
        return jsonify({
            'success': True,
            'forecast': {
                'current_spending': round(current_spending, 2),
                'predicted_total': round(predicted_total, 2),
                'adjusted_prediction': round(adjusted_prediction, 2),
                'daily_average': round(predicted_daily, 2),
                'days_remaining': month_info['days_remaining'],
                'days_passed': month_info['days_passed'],
                'days_in_month': month_info['days_in_month'],
                
                'budget': {
                    'amount': monthly_budget,
                    'current_percentage': round(current_percentage, 1),
                    'predicted_percentage': round(predicted_percentage, 1),
                    'predicted_over': predicted_over,
                    'predicted_difference': round(abs(predicted_difference), 2),
                    'status': 'over' if predicted_over else 'under'
                },
                
                'upcoming_bills': {
                    'total_30_days': round(upcoming_bills_total, 2),
                    'remaining_this_month': round(upcoming_bills_this_month, 2)
                },
                
                'comparison': {
                    'last_month_total': round(last_month_total, 2),
                    'last_month_same_point': round(spending_at_same_point, 2),
                    'vs_last_month_percentage': round(vs_last_month_percentage, 1)
                }
            },
            'currency': current_user.currency
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def get_upcoming_bills_total(user_id, days):
    """Get total of upcoming recurring bills"""
    cutoff_date = datetime.utcnow() + timedelta(days=days)
    
    bills = RecurringExpense.query.filter(
        RecurringExpense.user_id == user_id,
        RecurringExpense.is_active == True,
        RecurringExpense.next_due_date <= cutoff_date,
        RecurringExpense.next_due_date >= datetime.utcnow()
    ).all()
    
    return sum(bill.amount for bill in bills)


@bp.route('/cash-flow', methods=['GET'])
@login_required
def get_cash_flow_forecast():
    """Get cash flow forecast for the next 30 days"""
    try:
        days = request.args.get('days', 30, type=int)
        today = datetime.utcnow().date()
        
        # Initialize daily cash flow
        daily_flow = {}
        for i in range(days):
            date = today + timedelta(days=i)
            date_str = date.isoformat()
            daily_flow[date_str] = {
                'date': date_str,
                'day_name': date.strftime('%A'),
                'income': 0,
                'expenses': 0,
                'recurring_expenses': [],
                'recurring_income': [],
                'net_flow': 0
            }
        
        # Get upcoming recurring expenses
        cutoff_date = datetime.utcnow() + timedelta(days=days)
        
        recurring_expenses = RecurringExpense.query.filter(
            RecurringExpense.user_id == current_user.id,
            RecurringExpense.is_active == True,
            RecurringExpense.next_due_date >= datetime.utcnow(),
            RecurringExpense.next_due_date <= cutoff_date
        ).all()
        
        for expense in recurring_expenses:
            date_str = expense.next_due_date.date().isoformat()
            if date_str in daily_flow:
                daily_flow[date_str]['expenses'] += expense.amount
                daily_flow[date_str]['recurring_expenses'].append({
                    'id': expense.id,
                    'name': expense.name,
                    'amount': expense.amount,
                    'category': expense.category.name if expense.category else None,
                    'is_subscription': expense.is_subscription
                })
        
        # Get upcoming recurring income
        recurring_income = Income.query.filter(
            Income.user_id == current_user.id,
            Income.is_active == True,
            Income.next_due_date.isnot(None),
            Income.next_due_date >= datetime.utcnow(),
            Income.next_due_date <= cutoff_date
        ).all()
        
        for income in recurring_income:
            date_str = income.next_due_date.date().isoformat()
            if date_str in daily_flow:
                daily_flow[date_str]['income'] += income.amount
                daily_flow[date_str]['recurring_income'].append({
                    'id': income.id,
                    'description': income.description,
                    'source': income.source,
                    'amount': income.amount
                })
        
        # Calculate daily average spending (for non-scheduled days)
        daily_avg = calculate_daily_average(current_user.id, 30)
        
        # Add estimated daily spending and calculate net flow
        running_balance = 0
        flow_list = []
        
        for date_str in sorted(daily_flow.keys()):
            day = daily_flow[date_str]
            
            # Add estimated daily spending if no specific expenses
            if day['expenses'] == 0:
                day['estimated_expenses'] = round(daily_avg, 2)
            else:
                day['estimated_expenses'] = 0
            
            total_expenses = day['expenses'] + day['estimated_expenses']
            day['net_flow'] = round(day['income'] - total_expenses, 2)
            
            running_balance += day['net_flow']
            day['running_balance'] = round(running_balance, 2)
            
            flow_list.append(day)
        
        # Summary statistics
        total_income = sum(d['income'] for d in flow_list)
        total_expenses = sum(d['expenses'] + d['estimated_expenses'] for d in flow_list)
        
        return jsonify({
            'success': True,
            'cash_flow': flow_list,
            'summary': {
                'total_income': round(total_income, 2),
                'total_expenses': round(total_expenses, 2),
                'net_flow': round(total_income - total_expenses, 2),
                'daily_average_expense': round(daily_avg, 2)
            },
            'currency': current_user.currency
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/bills-calendar', methods=['GET'])
@login_required
def get_bills_calendar():
    """Get bill due date calendar data"""
    try:
        year = request.args.get('year', datetime.utcnow().year, type=int)
        month = request.args.get('month', datetime.utcnow().month, type=int)
        
        # Get start and end of month
        start_date = datetime(year, month, 1)
        _, days_in_month = calendar.monthrange(year, month)
        end_date = datetime(year, month, days_in_month, 23, 59, 59)
        
        # Get all recurring expenses due this month
        recurring_expenses = RecurringExpense.query.filter(
            RecurringExpense.user_id == current_user.id,
            RecurringExpense.is_active == True,
            RecurringExpense.next_due_date >= start_date,
            RecurringExpense.next_due_date <= end_date
        ).order_by(RecurringExpense.next_due_date).all()
        
        # Get recurring income due this month
        recurring_income = Income.query.filter(
            Income.user_id == current_user.id,
            Income.is_active == True,
            Income.next_due_date.isnot(None),
            Income.next_due_date >= start_date,
            Income.next_due_date <= end_date
        ).order_by(Income.next_due_date).all()
        
        # Build calendar data
        calendar_data = []
        today = datetime.utcnow().date()
        
        for day in range(1, days_in_month + 1):
            current_date = datetime(year, month, day).date()
            day_data = {
                'day': day,
                'date': current_date.isoformat(),
                'weekday': current_date.weekday(),
                'is_today': current_date == today,
                'is_past': current_date < today,
                'bills': [],
                'income': [],
                'total_due': 0,
                'total_income': 0
            }
            
            # Add bills due on this day
            for expense in recurring_expenses:
                if expense.next_due_date.date() == current_date:
                    day_data['bills'].append({
                        'id': expense.id,
                        'name': expense.name,
                        'amount': expense.amount,
                        'category': expense.category.name if expense.category else None,
                        'category_color': expense.category.color if expense.category else '#6b7280',
                        'is_subscription': expense.is_subscription,
                        'auto_create': expense.auto_create
                    })
                    day_data['total_due'] += expense.amount
            
            # Add income due on this day
            for income in recurring_income:
                if income.next_due_date.date() == current_date:
                    day_data['income'].append({
                        'id': income.id,
                        'description': income.description,
                        'source': income.source,
                        'amount': income.amount
                    })
                    day_data['total_income'] += income.amount
            
            calendar_data.append(day_data)
        
        # Calculate month summary
        total_bills = sum(d['total_due'] for d in calendar_data)
        total_income = sum(d['total_income'] for d in calendar_data)
        bills_count = sum(len(d['bills']) for d in calendar_data)
        income_count = sum(len(d['income']) for d in calendar_data)
        
        # Get overdue bills
        overdue_bills = RecurringExpense.query.filter(
            RecurringExpense.user_id == current_user.id,
            RecurringExpense.is_active == True,
            RecurringExpense.next_due_date < datetime.utcnow()
        ).all()
        
        return jsonify({
            'success': True,
            'calendar': calendar_data,
            'summary': {
                'year': year,
                'month': month,
                'month_name': calendar.month_name[month],
                'total_bills': round(total_bills, 2),
                'total_income': round(total_income, 2),
                'net_expected': round(total_income - total_bills, 2),
                'bills_count': bills_count,
                'income_count': income_count
            },
            'overdue': [{
                'id': b.id,
                'name': b.name,
                'amount': b.amount,
                'due_date': b.next_due_date.isoformat(),
                'days_overdue': (datetime.utcnow() - b.next_due_date).days
            } for b in overdue_bills],
            'currency': current_user.currency
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/category-forecast', methods=['GET'])
@login_required
def get_category_forecast():
    """Get spending forecast by category"""
    try:
        today = datetime.utcnow()
        month_info = get_month_days_info(today.year, today.month)
        start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        # Get current month spending by category
        category_spending = db.session.query(
            Category.id,
            Category.name,
            Category.color,
            Category.icon,
            Category.monthly_budget,
            func.sum(Expense.amount).label('current_spending'),
            func.count(Expense.id).label('transaction_count')
        ).join(Expense).filter(
            Expense.user_id == current_user.id,
            Expense.date >= start_of_month
        ).group_by(Category.id).all()
        
        # Get historical averages (last 3 months)
        historical = get_category_spending_history(current_user.id, 3)
        historical_map = {h['id']: h for h in historical}
        
        forecasts = []
        for cat in category_spending:
            current = float(cat.current_spending) if cat.current_spending else 0
            
            # Get historical average for this category
            hist = historical_map.get(cat.id, {})
            monthly_avg = hist.get('monthly_avg', 0)
            
            # Calculate daily rate and projection
            if month_info['days_passed'] > 0:
                daily_rate = current / month_info['days_passed']
                projected = current + (daily_rate * month_info['days_remaining'])
            else:
                projected = monthly_avg
            
            # Budget comparison
            budget = cat.monthly_budget or 0
            if budget > 0:
                current_pct = (current / budget) * 100
                projected_pct = (projected / budget) * 100
                over_budget = projected > budget
            else:
                current_pct = 0
                projected_pct = 0
                over_budget = False
            
            forecasts.append({
                'id': cat.id,
                'name': cat.name,
                'color': cat.color,
                'icon': cat.icon,
                'current_spending': round(current, 2),
                'projected_total': round(projected, 2),
                'monthly_average': round(monthly_avg, 2),
                'transaction_count': cat.transaction_count,
                'budget': budget,
                'current_percentage': round(current_pct, 1),
                'projected_percentage': round(projected_pct, 1),
                'over_budget': over_budget,
                'vs_average': round(projected - monthly_avg, 2) if monthly_avg > 0 else 0
            })
        
        # Sort by projected spending
        forecasts.sort(key=lambda x: x['projected_total'], reverse=True)
        
        return jsonify({
            'success': True,
            'forecasts': forecasts,
            'month_info': month_info,
            'currency': current_user.currency
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/trends', methods=['GET'])
@login_required
def get_spending_trends():
    """Get spending trends for forecasting"""
    try:
        months = request.args.get('months', 6, type=int)
        
        # Get historical spending
        historical = get_historical_spending(current_user.id, months)
        
        # Calculate trend
        if len(historical) >= 2:
            values = list(historical.values())
            avg = sum(values) / len(values)
            
            # Simple linear trend
            recent_avg = sum(values[-3:]) / min(3, len(values))
            older_avg = sum(values[:-3]) / max(1, len(values) - 3) if len(values) > 3 else avg
            
            if older_avg > 0:
                trend_direction = 'increasing' if recent_avg > older_avg else 'decreasing'
                trend_percentage = ((recent_avg - older_avg) / older_avg) * 100
            else:
                trend_direction = 'stable'
                trend_percentage = 0
        else:
            avg = sum(historical.values()) / len(historical) if historical else 0
            trend_direction = 'stable'
            trend_percentage = 0
        
        # Next month prediction
        if trend_percentage > 10:
            next_month_prediction = avg * (1 + min(trend_percentage / 100, 0.2))
        elif trend_percentage < -10:
            next_month_prediction = avg * (1 + max(trend_percentage / 100, -0.2))
        else:
            next_month_prediction = avg
        
        # Format monthly data
        monthly_data = [
            {
                'month': month,
                'total': round(total, 2),
                'month_name': datetime.strptime(month, '%Y-%m').strftime('%b %Y')
            }
            for month, total in sorted(historical.items())
        ]
        
        return jsonify({
            'success': True,
            'trends': {
                'monthly_data': monthly_data,
                'average': round(avg, 2),
                'trend_direction': trend_direction,
                'trend_percentage': round(trend_percentage, 1),
                'next_month_prediction': round(next_month_prediction, 2)
            },
            'currency': current_user.currency
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/upcoming-bills', methods=['GET'])
@login_required  
def get_upcoming_bills():
    """Get list of upcoming bills"""
    try:
        days = request.args.get('days', 30, type=int)
        cutoff_date = datetime.utcnow() + timedelta(days=days)
        
        # Get recurring expenses due within the period
        bills = RecurringExpense.query.filter(
            RecurringExpense.user_id == current_user.id,
            RecurringExpense.is_active == True,
            RecurringExpense.next_due_date >= datetime.utcnow(),
            RecurringExpense.next_due_date <= cutoff_date
        ).order_by(RecurringExpense.next_due_date).all()
        
        bills_list = []
        for bill in bills:
            days_until = (bill.next_due_date.date() - datetime.utcnow().date()).days
            
            bills_list.append({
                'id': bill.id,
                'name': bill.name,
                'amount': bill.amount,
                'due_date': bill.next_due_date.isoformat(),
                'days_until': days_until,
                'category': bill.category.name if bill.category else None,
                'category_color': bill.category.color if bill.category else '#6b7280',
                'frequency': bill.frequency,
                'is_subscription': bill.is_subscription,
                'auto_create': bill.auto_create,
                'urgency': 'overdue' if days_until < 0 else 
                          'today' if days_until == 0 else
                          'soon' if days_until <= 3 else
                          'upcoming' if days_until <= 7 else 'later'
            })
        
        # Get overdue bills
        overdue = RecurringExpense.query.filter(
            RecurringExpense.user_id == current_user.id,
            RecurringExpense.is_active == True,
            RecurringExpense.next_due_date < datetime.utcnow()
        ).order_by(RecurringExpense.next_due_date).all()
        
        overdue_list = [{
            'id': b.id,
            'name': b.name,
            'amount': b.amount,
            'due_date': b.next_due_date.isoformat(),
            'days_overdue': (datetime.utcnow() - b.next_due_date).days,
            'category': b.category.name if b.category else None,
            'category_color': b.category.color if b.category else '#6b7280'
        } for b in overdue]
        
        total_upcoming = sum(b['amount'] for b in bills_list)
        total_overdue = sum(b['amount'] for b in overdue_list)
        
        return jsonify({
            'success': True,
            'bills': bills_list,
            'overdue': overdue_list,
            'summary': {
                'total_upcoming': round(total_upcoming, 2),
                'total_overdue': round(total_overdue, 2),
                'count_upcoming': len(bills_list),
                'count_overdue': len(overdue_list)
            },
            'currency': current_user.currency
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/income-forecast', methods=['GET'])
@login_required
def get_income_forecast():
    """Get upcoming income forecast"""
    try:
        days = request.args.get('days', 30, type=int)
        cutoff_date = datetime.utcnow() + timedelta(days=days)
        
        # Get recurring income due within the period
        income_items = Income.query.filter(
            Income.user_id == current_user.id,
            Income.is_active == True,
            Income.next_due_date.isnot(None),
            Income.next_due_date >= datetime.utcnow(),
            Income.next_due_date <= cutoff_date
        ).order_by(Income.next_due_date).all()
        
        income_list = []
        for income in income_items:
            days_until = (income.next_due_date.date() - datetime.utcnow().date()).days
            
            income_list.append({
                'id': income.id,
                'description': income.description,
                'source': income.source,
                'amount': income.amount,
                'due_date': income.next_due_date.isoformat(),
                'days_until': days_until,
                'frequency': income.frequency
            })
        
        total_expected = sum(i['amount'] for i in income_list)
        
        return jsonify({
            'success': True,
            'income': income_list,
            'summary': {
                'total_expected': round(total_expected, 2),
                'count': len(income_list)
            },
            'currency': current_user.currency
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
