"""
Silly Expense Analyzer API Routes
Identifies small frequent purchases, needs vs wants, impulse purchases,
and provides "if you saved this instead" projections.

Security: All queries filtered by current_user.id
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Expense, Category
from datetime import datetime, timedelta
from sqlalchemy import func, and_, extract
from collections import defaultdict
import re

bp = Blueprint('analyzer', __name__, url_prefix='/api/analyzer')

# Categories that are typically "wants" vs "needs"
WANTS_CATEGORIES = [
    'entertainment', 'gaming', 'streaming', 'subscriptions', 'hobbies',
    'shopping', 'fashion', 'clothing', 'accessories', 'jewelry',
    'dining out', 'restaurants', 'fast food', 'coffee', 'takeaway',
    'alcohol', 'tobacco', 'vaping', 'leisure', 'sports', 'gym',
    'beauty', 'cosmetics', 'spa', 'wellness', 'luxury',
    'gadgets', 'electronics', 'tech', 'gifts', 'donations',
    'travel', 'vacation', 'holidays'
]

NEEDS_CATEGORIES = [
    'groceries', 'food', 'supermarket', 'rent', 'mortgage', 'housing',
    'utilities', 'electricity', 'gas', 'water', 'internet', 'phone',
    'insurance', 'health', 'medical', 'healthcare', 'pharmacy',
    'transportation', 'fuel', 'petrol', 'gas station', 'public transit',
    'education', 'childcare', 'school', 'tuition', 'savings',
    'debt', 'loan', 'bills'
]

# Small purchase patterns that add up
SMALL_PURCHASE_PATTERNS = {
    'coffee': {
        'patterns': ['coffee', 'starbucks', 'costa', 'nero', 'pret', 'cafe', 'espresso', 'latte', 'cappuccino', 'tim hortons', 'dunkin'],
        'icon': 'coffee',
        'typical_yearly_key': 'analyzer.pattern.coffee.typicalYearly',
        'name_key': 'analyzer.pattern.coffee.name'
    },
    'snacks': {
        'patterns': ['snack', 'candy', 'chocolate', 'crisps', 'chips', 'sweets', 'vending', 'convenience'],
        'icon': 'cookie',
        'typical_yearly_key': 'analyzer.pattern.snacks.typicalYearly',
        'name_key': 'analyzer.pattern.snacks.name'
    },
    'takeaway': {
        'patterns': ['deliveroo', 'uber eats', 'just eat', 'doordash', 'grubhub', 'takeaway', 'takeout', 'delivery'],
        'icon': 'delivery_dining',
        'typical_yearly_key': 'analyzer.pattern.takeaway.typicalYearly',
        'name_key': 'analyzer.pattern.takeaway.name'
    },
    'fast_food': {
        'patterns': ['mcdonald', 'burger king', 'kfc', 'wendy', 'taco bell', 'subway', 'chipotle', 'five guys', 'nando', 'greggs'],
        'icon': 'fastfood',
        'typical_yearly_key': 'analyzer.pattern.fastFood.typicalYearly',
        'name_key': 'analyzer.pattern.fastFood.name'
    },
    'drinks': {
        'patterns': ['pub', 'bar', 'beer', 'wine', 'spirits', 'alcohol', 'cocktail', 'nightclub'],
        'icon': 'local_bar',
        'typical_yearly_key': 'analyzer.pattern.drinks.typicalYearly',
        'name_key': 'analyzer.pattern.drinks.name'
    },
    'lottery': {
        'patterns': ['lottery', 'lotto', 'scratch', 'betting', 'gambling', 'casino', 'bet365', 'ladbrokes', 'william hill'],
        'icon': 'casino',
        'typical_yearly_key': 'analyzer.pattern.lottery.typicalYearly',
        'name_key': 'analyzer.pattern.lottery.name'
    },
    'streaming': {
        'patterns': ['netflix', 'spotify', 'disney', 'hulu', 'prime video', 'youtube premium', 'apple music'],
        'icon': 'subscriptions',
        'typical_yearly_key': 'analyzer.pattern.streaming.typicalYearly',
        'name_key': 'analyzer.pattern.streaming.name'
    },
    'impulse_online': {
        'patterns': ['amazon', 'ebay', 'aliexpress', 'wish', 'shein', 'asos', 'zalando'],
        'icon': 'shopping_cart',
        'typical_yearly_key': 'analyzer.pattern.impulseOnline.typicalYearly',
        'name_key': 'analyzer.pattern.impulseOnline.name'
    },
    'bottled_drinks': {
        'patterns': ['water bottle', 'soft drink', 'soda', 'energy drink', 'red bull', 'monster', 'lucozade', 'coca cola'],
        'icon': 'local_drink',
        'typical_yearly_key': 'analyzer.pattern.bottledDrinks.typicalYearly',
        'name_key': 'analyzer.pattern.bottledDrinks.name'
    },
    'apps_games': {
        'patterns': ['app store', 'google play', 'in-app', 'game purchase', 'steam', 'playstation store', 'xbox'],
        'icon': 'sports_esports',
        'typical_yearly_key': 'analyzer.pattern.appsGames.typicalYearly',
        'name_key': 'analyzer.pattern.appsGames.name'
    }
}

# Investment return projections
INVESTMENT_PROJECTIONS = {
    '1_year': {'rate': 0.07, 'label': '1 Year (7% return)'},
    '5_years': {'rate': 0.07, 'years': 5, 'label': '5 Years'},
    '10_years': {'rate': 0.07, 'years': 10, 'label': '10 Years'},
    '20_years': {'rate': 0.07, 'years': 20, 'label': '20 Years'},
    '30_years': {'rate': 0.07, 'years': 30, 'label': '30 Years'}
}


def categorize_expense_type(description, category_name):
    """Determine if an expense is a 'want' or 'need'"""
    description_lower = description.lower() if description else ''
    category_lower = category_name.lower() if category_name else ''
    
    # Check against wants patterns
    for want in WANTS_CATEGORIES:
        if want in description_lower or want in category_lower:
            return 'want'
    
    # Check against needs patterns
    for need in NEEDS_CATEGORIES:
        if need in description_lower or need in category_lower:
            return 'need'
    
    # Default to neutral/need for safety
    return 'neutral'


def detect_small_purchase_type(description):
    """Detect what type of small purchase this is"""
    description_lower = description.lower() if description else ''
    
    for purchase_type, config in SMALL_PURCHASE_PATTERNS.items():
        for pattern in config['patterns']:
            if pattern in description_lower:
                return {
                    'type': purchase_type,
                    'icon': config['icon'],
                    'typical_yearly_key': config['typical_yearly_key'],
                    'name_key': config['name_key']
                }
    
    return None


def is_impulse_purchase(expense, all_expenses_in_day):
    """
    Detect if a purchase might be an impulse buy based on:
    - Multiple purchases on same day
    - Weekend purchases
    - Late night (if we had time data)
    - Common impulse categories
    """
    impulse_indicators = 0
    reasons = []
    
    # Multiple purchases on same day
    if len(all_expenses_in_day) > 3:
        impulse_indicators += 1
        reasons.append('multiple_same_day')
    
    # Weekend purchase
    if expense.date.weekday() >= 5:  # Saturday=5, Sunday=6
        impulse_indicators += 0.5
        reasons.append('weekend')
    
    # Small amount (under threshold)
    if expense.amount < 30:
        impulse_indicators += 0.5
        reasons.append('small_amount')
    
    # Common impulse categories/keywords
    impulse_keywords = ['amazon', 'ebay', 'online', 'shopping', 'fashion', 'sale', 'clearance', 'deal']
    description_lower = expense.description.lower() if expense.description else ''
    if any(keyword in description_lower for keyword in impulse_keywords):
        impulse_indicators += 1
        reasons.append('impulse_keywords')
    
    return {
        'is_impulse': impulse_indicators >= 1.5,
        'score': impulse_indicators,
        'reasons': reasons
    }


def calculate_compound_growth(monthly_savings, years, annual_rate=0.07):
    """Calculate compound growth for monthly investments"""
    months = years * 12
    monthly_rate = annual_rate / 12
    
    # Future value of annuity formula
    if monthly_rate == 0:
        return monthly_savings * months
    
    future_value = monthly_savings * (((1 + monthly_rate) ** months - 1) / monthly_rate)
    return round(future_value, 2)


@bp.route('/summary', methods=['GET'])
@login_required
def get_summary():
    """Get overall spending analysis summary"""
    # Get date range (default last 90 days for better analysis)
    days = request.args.get('days', 90, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get all expenses in range
    expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_date
    ).all()
    
    if not expenses:
        return jsonify({
            'success': True,
            'total_analyzed': 0,
            'wants_total': 0,
            'needs_total': 0,
            'wants_percentage': 0,
            'small_purchases_total': 0,
            'potential_yearly_savings': 0,
            'top_silly_expenses': [],
            'impulse_count': 0
        })
    
    wants_total = 0
    needs_total = 0
    neutral_total = 0
    small_purchases = defaultdict(lambda: {'count': 0, 'total': 0})
    impulse_count = 0
    
    # Group expenses by date for impulse detection
    expenses_by_date = defaultdict(list)
    for exp in expenses:
        date_key = exp.date.strftime('%Y-%m-%d')
        expenses_by_date[date_key].append(exp)
    
    for expense in expenses:
        category_name = expense.category.name if expense.category else ''
        
        # Categorize as want/need
        expense_type = categorize_expense_type(expense.description, category_name)
        if expense_type == 'want':
            wants_total += expense.amount
        elif expense_type == 'need':
            needs_total += expense.amount
        else:
            neutral_total += expense.amount
        
        # Detect small purchase patterns
        small_purchase = detect_small_purchase_type(expense.description)
        if small_purchase:
            small_purchases[small_purchase['type']]['count'] += 1
            small_purchases[small_purchase['type']]['total'] += expense.amount
            small_purchases[small_purchase['type']]['icon'] = small_purchase['icon']
            small_purchases[small_purchase['type']]['typical_yearly_key'] = small_purchase['typical_yearly_key']
            small_purchases[small_purchase['type']]['name_key'] = small_purchase['name_key']
        
        # Detect impulse purchases
        date_key = expense.date.strftime('%Y-%m-%d')
        impulse_result = is_impulse_purchase(expense, expenses_by_date[date_key])
        if impulse_result['is_impulse']:
            impulse_count += 1
    
    # Calculate totals and projections
    total_analyzed = len(expenses)
    total_spent = wants_total + needs_total + neutral_total
    wants_percentage = round((wants_total / total_spent * 100), 1) if total_spent > 0 else 0
    
    # Calculate small purchases total and potential yearly savings
    small_purchases_total = sum(sp['total'] for sp in small_purchases.values())
    daily_small_average = small_purchases_total / days
    potential_yearly_savings = round(daily_small_average * 365, 2)
    
    # Get top silly expenses
    top_silly = []
    for purchase_type, data in sorted(small_purchases.items(), key=lambda x: x[1]['total'], reverse=True)[:5]:
        daily_average = data['total'] / days
        yearly_projection = round(daily_average * 365, 2)
        top_silly.append({
            'type': purchase_type,
            'type_key': f'analyzer.pattern.{purchase_type.replace("_", "").title().lower()}.name',
            'icon': data['icon'],
            'count': data['count'],
            'total': round(data['total'], 2),
            'daily_average': round(daily_average, 2),
            'yearly_projection': yearly_projection,
            'typical_yearly_key': data.get('typical_yearly_key', ''),
            'name_key': data.get('name_key', ''),
            # If saved instead projections
            'if_invested_5yr': calculate_compound_growth(daily_average * 30, 5),
            'if_invested_10yr': calculate_compound_growth(daily_average * 30, 10),
            'if_invested_20yr': calculate_compound_growth(daily_average * 30, 20)
        })
    
    return jsonify({
        'success': True,
        'days_analyzed': days,
        'total_analyzed': total_analyzed,
        'total_spent': round(total_spent, 2),
        'wants_total': round(wants_total, 2),
        'needs_total': round(needs_total, 2),
        'neutral_total': round(neutral_total, 2),
        'wants_percentage': wants_percentage,
        'needs_percentage': round((needs_total / total_spent * 100), 1) if total_spent > 0 else 0,
        'small_purchases_total': round(small_purchases_total, 2),
        'potential_yearly_savings': potential_yearly_savings,
        'top_silly_expenses': top_silly,
        'impulse_count': impulse_count,
        'currency': current_user.currency
    })


@bp.route('/small-purchases', methods=['GET'])
@login_required
def get_small_purchases():
    """Get detailed breakdown of small frequent purchases"""
    days = request.args.get('days', 90, type=int)
    min_occurrences = request.args.get('min_occurrences', 3, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_date
    ).order_by(Expense.date.desc()).all()
    
    # Group by pattern
    patterns = defaultdict(lambda: {'expenses': [], 'total': 0, 'count': 0})
    
    for expense in expenses:
        small_purchase = detect_small_purchase_type(expense.description)
        if small_purchase:
            pattern_type = small_purchase['type']
            patterns[pattern_type]['expenses'].append({
                'id': expense.id,
                'description': expense.description,
                'amount': expense.amount,
                'date': expense.date.isoformat(),
                'category': expense.category.name if expense.category else None
            })
            patterns[pattern_type]['total'] += expense.amount
            patterns[pattern_type]['count'] += 1
            patterns[pattern_type]['icon'] = small_purchase['icon']
            patterns[pattern_type]['typical_yearly_key'] = small_purchase['typical_yearly_key']
            patterns[pattern_type]['name_key'] = small_purchase['name_key']
    
    # Filter by minimum occurrences and calculate projections
    result = []
    for pattern_type, data in patterns.items():
        if data['count'] >= min_occurrences:
            daily_average = data['total'] / days
            monthly_average = daily_average * 30
            yearly_projection = daily_average * 365
            
            result.append({
                'type': pattern_type,
                'type_display_key': data.get('name_key', ''),
                'icon': data['icon'],
                'count': data['count'],
                'total': round(data['total'], 2),
                'average_per_purchase': round(data['total'] / data['count'], 2),
                'frequency_per_week': round(data['count'] / (days / 7), 1),
                'daily_average': round(daily_average, 2),
                'monthly_average': round(monthly_average, 2),
                'yearly_projection': round(yearly_projection, 2),
                'typical_yearly_key': data.get('typical_yearly_key', ''),
                'recent_expenses': data['expenses'][:10],  # Last 10 for display
                'projections': {
                    '5_years': calculate_compound_growth(monthly_average, 5),
                    '10_years': calculate_compound_growth(monthly_average, 10),
                    '20_years': calculate_compound_growth(monthly_average, 20),
                    '30_years': calculate_compound_growth(monthly_average, 30)
                }
            })
    
    # Sort by total spent
    result.sort(key=lambda x: x['total'], reverse=True)
    
    return jsonify({
        'success': True,
        'days_analyzed': days,
        'patterns': result,
        'total_small_purchases': round(sum(p['total'] for p in result), 2),
        'currency': current_user.currency
    })


@bp.route('/needs-wants', methods=['GET'])
@login_required
def get_needs_wants():
    """Get breakdown of needs vs wants spending"""
    days = request.args.get('days', 90, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_date
    ).all()
    
    wants = []
    needs = []
    neutral = []
    
    for expense in expenses:
        category_name = expense.category.name if expense.category else ''
        expense_type = categorize_expense_type(expense.description, category_name)
        
        expense_data = {
            'id': expense.id,
            'description': expense.description,
            'amount': expense.amount,
            'date': expense.date.isoformat(),
            'category': category_name,
            'category_color': expense.category.color if expense.category else '#666'
        }
        
        if expense_type == 'want':
            wants.append(expense_data)
        elif expense_type == 'need':
            needs.append(expense_data)
        else:
            neutral.append(expense_data)
    
    wants_total = sum(e['amount'] for e in wants)
    needs_total = sum(e['amount'] for e in needs)
    neutral_total = sum(e['amount'] for e in neutral)
    total = wants_total + needs_total + neutral_total
    
    # Group wants by category for chart
    wants_by_category = defaultdict(float)
    for w in wants:
        wants_by_category[w['category']] += w['amount']
    
    return jsonify({
        'success': True,
        'days_analyzed': days,
        'wants': {
            'total': round(wants_total, 2),
            'count': len(wants),
            'percentage': round((wants_total / total * 100), 1) if total > 0 else 0,
            'by_category': [{'category': k, 'total': round(v, 2)} for k, v in sorted(wants_by_category.items(), key=lambda x: x[1], reverse=True)],
            'items': sorted(wants, key=lambda x: x['amount'], reverse=True)[:20]  # Top 20
        },
        'needs': {
            'total': round(needs_total, 2),
            'count': len(needs),
            'percentage': round((needs_total / total * 100), 1) if total > 0 else 0,
            'items': sorted(needs, key=lambda x: x['amount'], reverse=True)[:20]
        },
        'neutral': {
            'total': round(neutral_total, 2),
            'count': len(neutral),
            'percentage': round((neutral_total / total * 100), 1) if total > 0 else 0
        },
        'total': round(total, 2),
        'currency': current_user.currency
    })


@bp.route('/impulse', methods=['GET'])
@login_required
def get_impulse_purchases():
    """Get detected impulse purchases"""
    days = request.args.get('days', 90, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_date
    ).all()
    
    # Group by date
    expenses_by_date = defaultdict(list)
    for exp in expenses:
        date_key = exp.date.strftime('%Y-%m-%d')
        expenses_by_date[date_key].append(exp)
    
    impulse_purchases = []
    
    for expense in expenses:
        date_key = expense.date.strftime('%Y-%m-%d')
        impulse_result = is_impulse_purchase(expense, expenses_by_date[date_key])
        
        if impulse_result['is_impulse']:
            # Return translation keys instead of hardcoded strings
            reason_key_map = {
                'multiple_same_day': 'analyzer.impulse.reason.multipleSameDay',
                'weekend': 'analyzer.impulse.reason.weekend',
                'small_amount': 'analyzer.impulse.reason.smallAmount',
                'impulse_keywords': 'analyzer.impulse.reason.impulseKeywords'
            }
            
            impulse_purchases.append({
                'id': expense.id,
                'description': expense.description,
                'amount': expense.amount,
                'date': expense.date.isoformat(),
                'category': expense.category.name if expense.category else None,
                'impulse_score': impulse_result['score'],
                'reason_keys': [reason_key_map.get(r, r) for r in impulse_result['reasons']],
                'day_of_week': expense.date.strftime('%A'),
                'day_of_week_key': f"days.{expense.date.strftime('%A').lower()}"
            })
    
    # Sort by impulse score and amount
    impulse_purchases.sort(key=lambda x: (x['impulse_score'], x['amount']), reverse=True)
    
    total_impulse = sum(p['amount'] for p in impulse_purchases)
    monthly_impulse = total_impulse / (days / 30)
    
    return jsonify({
        'success': True,
        'days_analyzed': days,
        'impulse_count': len(impulse_purchases),
        'impulse_total': round(total_impulse, 2),
        'monthly_average': round(monthly_impulse, 2),
        'yearly_projection': round(monthly_impulse * 12, 2),
        'purchases': impulse_purchases[:50],  # Top 50
        'by_day_of_week': get_impulse_by_day(impulse_purchases),
        'currency': current_user.currency
    })


def get_impulse_by_day(impulse_purchases):
    """Group impulse purchases by day of week"""
    by_day = defaultdict(lambda: {'count': 0, 'total': 0})
    
    for p in impulse_purchases:
        day = p['day_of_week']
        by_day[day]['count'] += 1
        by_day[day]['total'] += p['amount']
    
    return [
        {'day': day, 'count': data['count'], 'total': round(data['total'], 2)}
        for day, data in by_day.items()
    ]


@bp.route('/projections', methods=['GET'])
@login_required
def get_savings_projections():
    """Get 'if you saved this instead' projections"""
    days = request.args.get('days', 90, type=int)
    monthly_amount = request.args.get('monthly_amount', type=float)
    
    if not monthly_amount:
        # Calculate from actual small purchases
        start_date = datetime.utcnow() - timedelta(days=days)
        expenses = Expense.query.filter(
            Expense.user_id == current_user.id,
            Expense.date >= start_date
        ).all()
        
        small_total = 0
        for expense in expenses:
            if detect_small_purchase_type(expense.description):
                small_total += expense.amount
        
        monthly_amount = (small_total / days) * 30
    
    projections = []
    for years in [1, 5, 10, 20, 30]:
        future_value = calculate_compound_growth(monthly_amount, years)
        total_invested = monthly_amount * 12 * years
        growth = future_value - total_invested
        
        projections.append({
            'years': years,
            'monthly_savings': round(monthly_amount, 2),
            'total_invested': round(total_invested, 2),
            'future_value': future_value,
            'growth': round(growth, 2),
            'growth_percentage': round((growth / total_invested * 100), 1) if total_invested > 0 else 0
        })
    
    return jsonify({
        'success': True,
        'monthly_amount': round(monthly_amount, 2),
        'annual_return_rate': '7%',
        'projections': projections,
        'currency': current_user.currency
    })


@bp.route('/category-analysis', methods=['GET'])
@login_required
def get_category_analysis():
    """Analyze spending by category with needs/wants classification"""
    days = request.args.get('days', 90, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get expenses with category info
    expenses = db.session.query(
        Category.name,
        Category.color,
        Category.icon,
        func.sum(Expense.amount).label('total'),
        func.count(Expense.id).label('count')
    ).join(Category, Expense.category_id == Category.id).filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_date
    ).group_by(Category.id).all()
    
    categories = []
    for cat_name, color, icon, total, count in expenses:
        expense_type = categorize_expense_type('', cat_name)
        daily_average = total / days
        
        categories.append({
            'name': cat_name,
            'color': color,
            'icon': icon,
            'total': round(total, 2),
            'count': count,
            'type': expense_type,  # 'want', 'need', or 'neutral'
            'daily_average': round(daily_average, 2),
            'monthly_average': round(daily_average * 30, 2),
            'yearly_projection': round(daily_average * 365, 2)
        })
    
    categories.sort(key=lambda x: x['total'], reverse=True)
    
    return jsonify({
        'success': True,
        'days_analyzed': days,
        'categories': categories,
        'currency': current_user.currency
    })


@bp.route('/insights', methods=['GET'])
@login_required  
def get_insights():
    """Get personalized spending insights and recommendations"""
    days = request.args.get('days', 90, type=int)
    start_date = datetime.utcnow() - timedelta(days=days)
    
    expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= start_date
    ).all()
    
    if not expenses:
        return jsonify({
            'success': True,
            'insights': [],
            'score': 0,
            'score_label_key': 'analyzer.score.noData'
        })
    
    insights = []
    score = 100  # Start with perfect score
    
    # Analyze spending patterns
    total_spent = sum(e.amount for e in expenses)
    
    # Check small purchases
    small_total = 0
    small_count = 0
    for expense in expenses:
        if detect_small_purchase_type(expense.description):
            small_total += expense.amount
            small_count += 1
    
    if small_count > 0:
        small_percentage = (small_total / total_spent) * 100
        daily_small = small_total / days
        yearly_projection = daily_small * 365
        
        if small_percentage > 15:
            score -= 20
            insights.append({
                'type': 'warning',
                'icon': 'coffee',
                'title_key': 'analyzer.insight.highSmallPurchases.title',
                'message_key': 'analyzer.insight.highSmallPurchases.message',
                'message_params': {'percentage': f'{small_percentage:.1f}', 'currency': current_user.currency, 'yearly': f'{yearly_projection:.0f}'},
                'action_key': 'analyzer.insight.highSmallPurchases.action',
                'potential_savings': round(yearly_projection * 0.5, 2)
            })
        elif small_percentage > 10:
            score -= 10
            insights.append({
                'type': 'info',
                'icon': 'local_cafe',
                'title_key': 'analyzer.insight.noticeableSmallPurchases.title',
                'message_key': 'analyzer.insight.noticeableSmallPurchases.message',
                'message_params': {'currency': current_user.currency, 'total': f'{small_total:.2f}', 'days': str(days)},
                'action_key': 'analyzer.insight.noticeableSmallPurchases.action',
                'potential_savings': round(yearly_projection * 0.3, 2)
            })
    
    # Check wants vs needs ratio
    wants_total = 0
    for expense in expenses:
        category_name = expense.category.name if expense.category else ''
        if categorize_expense_type(expense.description, category_name) == 'want':
            wants_total += expense.amount
    
    wants_percentage = (wants_total / total_spent) * 100 if total_spent > 0 else 0
    
    if wants_percentage > 40:
        score -= 15
        insights.append({
            'type': 'warning',
            'icon': 'shopping_bag',
            'title_key': 'analyzer.insight.highWantsSpending.title',
            'message_key': 'analyzer.insight.highWantsSpending.message',
            'message_params': {'percentage': f'{wants_percentage:.1f}'},
            'action_key': 'analyzer.insight.highWantsSpending.action',
            'potential_savings': round((wants_total - (total_spent * 0.3)) / (days / 30), 2) if wants_percentage > 30 else 0
        })
    elif wants_percentage < 20:
        insights.append({
            'type': 'success',
            'icon': 'thumb_up',
            'title_key': 'analyzer.insight.greatWantsControl.title',
            'message_key': 'analyzer.insight.greatWantsControl.message',
            'message_params': {'percentage': f'{wants_percentage:.1f}'},
            'action_key': 'analyzer.insight.greatWantsControl.action',
            'potential_savings': 0
        })
    
    # Check impulse purchases
    expenses_by_date = defaultdict(list)
    for exp in expenses:
        date_key = exp.date.strftime('%Y-%m-%d')
        expenses_by_date[date_key].append(exp)
    
    impulse_count = 0
    impulse_total = 0
    for expense in expenses:
        date_key = expense.date.strftime('%Y-%m-%d')
        if is_impulse_purchase(expense, expenses_by_date[date_key])['is_impulse']:
            impulse_count += 1
            impulse_total += expense.amount
    
    if impulse_count > len(expenses) * 0.2:
        score -= 15
        insights.append({
            'type': 'warning',
            'icon': 'bolt',
            'title_key': 'analyzer.insight.frequentImpulse.title',
            'message_key': 'analyzer.insight.frequentImpulse.message',
            'message_params': {'count': str(impulse_count), 'currency': current_user.currency, 'total': f'{impulse_total:.2f}'},
            'action_key': 'analyzer.insight.frequentImpulse.action',
            'potential_savings': round(impulse_total * 0.5 / (days / 30), 2)
        })
    
    # Weekend spending analysis
    weekend_total = sum(e.amount for e in expenses if e.date.weekday() >= 5)
    weekday_total = total_spent - weekend_total
    
    weekend_days = (days / 7) * 2
    weekday_days = days - weekend_days
    
    weekend_daily = weekend_total / weekend_days if weekend_days > 0 else 0
    weekday_daily = weekday_total / weekday_days if weekday_days > 0 else 0
    
    if weekend_daily > weekday_daily * 1.5:
        score -= 10
        weekend_increase = ((weekend_daily / weekday_daily - 1) * 100) if weekday_daily > 0 else 0
        insights.append({
            'type': 'info',
            'icon': 'weekend',
            'title_key': 'analyzer.insight.higherWeekendSpending.title',
            'message_key': 'analyzer.insight.higherWeekendSpending.message',
            'message_params': {'percentage': f'{weekend_increase:.0f}'},
            'action_key': 'analyzer.insight.higherWeekendSpending.action',
            'potential_savings': round((weekend_daily - weekday_daily) * 8, 2)  # 8 weekend days/month
        })
    
    # Positive insight if score is good
    if score >= 80:
        insights.insert(0, {
            'type': 'success',
            'icon': 'emoji_events',
            'title_key': 'analyzer.insight.excellentHabits.title',
            'message_key': 'analyzer.insight.excellentHabits.message',
            'action_key': 'analyzer.insight.excellentHabits.action',
            'potential_savings': 0
        })
    
    # Determine score label key
    if score >= 80:
        score_label_key = 'analyzer.score.excellent'
    elif score >= 60:
        score_label_key = 'analyzer.score.good'
    elif score >= 40:
        score_label_key = 'analyzer.score.needsImprovement'
    else:
        score_label_key = 'analyzer.score.critical'
    
    return jsonify({
        'success': True,
        'score': max(0, score),
        'score_label_key': score_label_key,
        'insights': insights,
        'days_analyzed': days,
        'currency': current_user.currency
    })
