from app import db
from app.models import Category

def create_default_categories(user_id):
    """Create default categories for a new user"""
    default_categories = [
        {'name': 'Food & Dining', 'color': '#ff6b6b', 'icon': 'restaurant'},
        {'name': 'Transportation', 'color': '#4ecdc4', 'icon': 'directions_car'},
        {'name': 'Shopping', 'color': '#95e1d3', 'icon': 'shopping_bag'},
        {'name': 'Entertainment', 'color': '#f38181', 'icon': 'movie'},
        {'name': 'Bills & Utilities', 'color': '#aa96da', 'icon': 'receipt'},
        {'name': 'Healthcare', 'color': '#fcbad3', 'icon': 'medical_services'},
        {'name': 'Education', 'color': '#a8d8ea', 'icon': 'school'},
        {'name': 'Other', 'color': '#92adc9', 'icon': 'category'}
    ]
    
    for index, cat_data in enumerate(default_categories):
        category = Category(
            name=cat_data['name'],
            color=cat_data['color'],
            icon=cat_data['icon'],
            display_order=index,
            user_id=user_id
        )
        db.session.add(category)
    
    db.session.commit()


def format_currency(amount, currency='USD'):
    """Format amount with currency symbol"""
    symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'RON': 'lei'
    }
    symbol = symbols.get(currency, currency)
    
    if currency == 'RON':
        return f"{amount:,.2f} {symbol}"
    return f"{symbol}{amount:,.2f}"
