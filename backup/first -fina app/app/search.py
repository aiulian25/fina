"""
Global Search Module for FINA Finance Tracker
Provides comprehensive search across all user data with security isolation
"""
from app.models.category import Category, Expense
from app.models.subscription import Subscription
from app.models.user import User, Tag
from sqlalchemy import or_, and_, func, cast, String
from datetime import datetime
import re


def search_all(query, user_id, limit=50):
    """
    Comprehensive search across all user data
    
    Args:
        query: Search string
        user_id: Current user ID for security filtering
        limit: Maximum results per category
    
    Returns:
        Dictionary with categorized results
    """
    if not query or not query.strip():
        return {
            'expenses': [],
            'categories': [],
            'subscriptions': [],
            'tags': [],
            'total': 0
        }
    
    query = query.strip()
    search_term = f'%{query}%'
    
    # Try to parse as amount (e.g., "45.99", "45", "45.9")
    amount_value = None
    try:
        amount_value = float(query.replace(',', '.'))
    except ValueError:
        pass
    
    # Try to parse as date (YYYY-MM-DD, DD/MM/YYYY, etc.)
    date_value = None
    date_patterns = [
        r'(\d{4})-(\d{1,2})-(\d{1,2})',  # YYYY-MM-DD
        r'(\d{1,2})/(\d{1,2})/(\d{4})',  # DD/MM/YYYY
        r'(\d{1,2})-(\d{1,2})-(\d{4})',  # DD-MM-YYYY
    ]
    for pattern in date_patterns:
        match = re.search(pattern, query)
        if match:
            try:
                groups = match.groups()
                if len(groups[0]) == 4:  # YYYY-MM-DD
                    date_value = datetime(int(groups[0]), int(groups[1]), int(groups[2])).date()
                else:  # DD/MM/YYYY or DD-MM-YYYY
                    date_value = datetime(int(groups[2]), int(groups[1]), int(groups[0])).date()
                break
            except (ValueError, IndexError):
                pass
    
    # Search Expenses
    expense_conditions = [
        Expense.user_id == user_id,
        or_(
            Expense.description.ilike(search_term),
            Expense.paid_by.ilike(search_term),
            Expense.tags.ilike(search_term),
        )
    ]
    
    # Add amount search if valid number
    if amount_value is not None:
        expense_conditions[1] = or_(
            expense_conditions[1],
            Expense.amount == amount_value,
            # Also search for amounts close to the value (±0.01)
            and_(Expense.amount >= amount_value - 0.01, Expense.amount <= amount_value + 0.01)
        )
    
    # Add date search if valid date
    if date_value:
        expense_conditions[1] = or_(
            expense_conditions[1],
            func.date(Expense.date) == date_value
        )
    
    expenses = Expense.query.filter(
        and_(*expense_conditions)
    ).order_by(Expense.date.desc()).limit(limit).all()
    
    # Search Categories
    categories = Category.query.filter(
        Category.user_id == user_id,
        or_(
            Category.name.ilike(search_term),
            Category.description.ilike(search_term)
        )
    ).limit(limit).all()
    
    # Search Subscriptions
    subscription_conditions = [
        Subscription.user_id == user_id,
        or_(
            Subscription.name.ilike(search_term),
            Subscription.notes.ilike(search_term),
        )
    ]
    
    # Add amount search for subscriptions
    if amount_value is not None:
        subscription_conditions[1] = or_(
            subscription_conditions[1],
            Subscription.amount == amount_value,
            and_(Subscription.amount >= amount_value - 0.01, Subscription.amount <= amount_value + 0.01)
        )
    
    subscriptions = Subscription.query.filter(
        and_(*subscription_conditions)
    ).limit(limit).all()
    
    # Search Tags
    tags = Tag.query.filter(
        Tag.user_id == user_id,
        Tag.name.ilike(search_term)
    ).limit(limit).all()
    
    # Format results
    expense_results = []
    for exp in expenses:
        expense_results.append({
            'id': exp.id,
            'type': 'expense',
            'description': exp.description,
            'amount': float(exp.amount),
            'date': exp.date.strftime('%Y-%m-%d'),
            'category_name': exp.category.name if exp.category else '',
            'category_id': exp.category_id,
            'category_color': exp.category.color if exp.category else '#6366f1',
            'paid_by': exp.paid_by or '',
            'tags': exp.tags or '',
            'has_receipt': bool(exp.file_path),
            'url': f'/expense/{exp.id}/edit'
        })
    
    category_results = []
    for cat in categories:
        spent = cat.get_total_spent()
        category_results.append({
            'id': cat.id,
            'type': 'category',
            'name': cat.name,
            'description': cat.description or '',
            'color': cat.color,
            'total_spent': float(spent),
            'expense_count': len(cat.expenses),
            'url': f'/category/{cat.id}'
        })
    
    subscription_results = []
    for sub in subscriptions:
        subscription_results.append({
            'id': sub.id,
            'type': 'subscription',
            'name': sub.name,
            'amount': float(sub.amount),
            'frequency': sub.frequency,
            'next_due': sub.next_due_date.strftime('%Y-%m-%d') if sub.next_due_date else None,
            'is_active': sub.is_active,
            'category_name': Category.query.get(sub.category_id).name if sub.category_id else '',
            'url': f'/subscriptions/edit/{sub.id}'
        })
    
    tag_results = []
    for tag in tags:
        # Count expenses with this tag
        tag_expense_count = Expense.query.filter(
            Expense.user_id == user_id,
            Expense.tags.ilike(f'%{tag.name}%')
        ).count()
        
        tag_results.append({
            'id': tag.id,
            'type': 'tag',
            'name': tag.name,
            'color': tag.color,
            'expense_count': tag_expense_count,
            'url': f'/settings'  # Tags management is in settings
        })
    
    total = len(expense_results) + len(category_results) + len(subscription_results) + len(tag_results)
    
    return {
        'expenses': expense_results,
        'categories': category_results,
        'subscriptions': subscription_results,
        'tags': tag_results,
        'total': total,
        'query': query
    }


def search_expenses_by_filters(user_id, category_id=None, date_from=None, date_to=None, 
                               min_amount=None, max_amount=None, tags=None, paid_by=None):
    """
    Advanced expense filtering with multiple criteria
    
    Args:
        user_id: Current user ID
        category_id: Filter by category
        date_from: Start date (datetime object)
        date_to: End date (datetime object)
        min_amount: Minimum amount
        max_amount: Maximum amount
        tags: Tag string to search for
        paid_by: Person who paid
    
    Returns:
        List of matching expenses
    """
    conditions = [Expense.user_id == user_id]
    
    if category_id:
        conditions.append(Expense.category_id == category_id)
    
    if date_from:
        conditions.append(Expense.date >= date_from)
    
    if date_to:
        conditions.append(Expense.date <= date_to)
    
    if min_amount is not None:
        conditions.append(Expense.amount >= min_amount)
    
    if max_amount is not None:
        conditions.append(Expense.amount <= max_amount)
    
    if tags:
        conditions.append(Expense.tags.ilike(f'%{tags}%'))
    
    if paid_by:
        conditions.append(Expense.paid_by.ilike(f'%{paid_by}%'))
    
    expenses = Expense.query.filter(and_(*conditions)).order_by(Expense.date.desc()).all()
    
    return expenses


def quick_search_suggestions(query, user_id, limit=5):
    """
    Quick search for autocomplete suggestions
    Returns top matches across all types
    
    Args:
        query: Search string
        user_id: Current user ID
        limit: Maximum suggestions
    
    Returns:
        List of suggestion objects
    """
    if not query or len(query) < 2:
        return []
    
    search_term = f'%{query}%'
    suggestions = []
    
    # Recent expenses
    recent_expenses = Expense.query.filter(
        Expense.user_id == user_id,
        Expense.description.ilike(search_term)
    ).order_by(Expense.date.desc()).limit(limit).all()
    
    for exp in recent_expenses:
        suggestions.append({
            'text': exp.description,
            'type': 'expense',
            'amount': float(exp.amount),
            'date': exp.date.strftime('%Y-%m-%d'),
            'icon': '💸'
        })
    
    # Categories
    cats = Category.query.filter(
        Category.user_id == user_id,
        Category.name.ilike(search_term)
    ).limit(limit).all()
    
    for cat in cats:
        suggestions.append({
            'text': cat.name,
            'type': 'category',
            'icon': '📁',
            'color': cat.color
        })
    
    # Subscriptions
    subs = Subscription.query.filter(
        Subscription.user_id == user_id,
        Subscription.name.ilike(search_term)
    ).limit(limit).all()
    
    for sub in subs:
        suggestions.append({
            'text': sub.name,
            'type': 'subscription',
            'amount': float(sub.amount),
            'icon': '🔄'
        })
    
    return suggestions[:limit * 2]
