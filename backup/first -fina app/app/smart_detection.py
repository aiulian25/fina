"""
Smart detection algorithms for recurring expenses and subscriptions
"""
from datetime import datetime, timedelta
from collections import defaultdict
import re
import json
from sqlalchemy import and_
from app import db
from app.models.category import Expense
from app.models.subscription import RecurringPattern, Subscription


def detect_recurring_expenses(user_id, min_occurrences=3, min_confidence=70):
    """
    Detect recurring expenses for a user
    
    Args:
        user_id: User ID to analyze
        min_occurrences: Minimum number of similar transactions to consider
        min_confidence: Minimum confidence score (0-100) to suggest
    
    Returns:
        List of detected patterns
    """
    # Get all expenses for the user from the last year
    one_year_ago = datetime.now() - timedelta(days=365)
    expenses = Expense.query.filter(
        and_(
            Expense.user_id == user_id,
            Expense.date >= one_year_ago.date()
        )
    ).order_by(Expense.date).all()
    
    if len(expenses) < min_occurrences:
        return []
    
    # Group expenses by similarity
    patterns = []
    processed_ids = set()
    
    for i, expense in enumerate(expenses):
        if expense.id in processed_ids:
            continue
            
        similar_expenses = find_similar_expenses(expense, expenses[i+1:], processed_ids)
        
        if len(similar_expenses) >= min_occurrences - 1:  # -1 because we include the current expense
            similar_expenses.insert(0, expense)
            pattern = analyze_pattern(similar_expenses, user_id)
            
            if pattern and pattern['confidence_score'] >= min_confidence:
                patterns.append(pattern)
                processed_ids.update([e.id for e in similar_expenses])
    
    return patterns


def find_similar_expenses(target_expense, expenses, exclude_ids):
    """Find expenses similar to target expense"""
    similar = []
    target_amount = target_expense.amount
    target_desc = normalize_description(target_expense.description or '')
    
    # Amount tolerance: 5% or $5, whichever is larger
    amount_tolerance = max(target_amount * 0.05, 5.0)
    
    for expense in expenses:
        if expense.id in exclude_ids:
            continue
            
        # Check category match
        if expense.category_id != target_expense.category_id:
            continue
        
        # Check amount similarity
        amount_diff = abs(expense.amount - target_amount)
        if amount_diff > amount_tolerance:
            continue
        
        # Check description similarity
        expense_desc = normalize_description(expense.description or '')
        if not descriptions_similar(target_desc, expense_desc):
            continue
        
        similar.append(expense)
    
    return similar


def normalize_description(desc):
    """Normalize description for comparison"""
    # Remove common patterns like dates, numbers at end
    desc = re.sub(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', '', desc)
    desc = re.sub(r'#\d+', '', desc)
    desc = re.sub(r'\s+\d+$', '', desc)
    
    # Convert to lowercase and strip
    desc = desc.lower().strip()
    
    # Remove common words
    common_words = ['payment', 'subscription', 'monthly', 'recurring', 'auto']
    for word in common_words:
        desc = desc.replace(word, '')
    
    return desc.strip()


def descriptions_similar(desc1, desc2, threshold=0.6):
    """Check if two descriptions are similar enough"""
    if not desc1 or not desc2:
        return False
    
    # Exact match
    if desc1 == desc2:
        return True
    
    # Check if one contains the other
    if desc1 in desc2 or desc2 in desc1:
        return True
    
    # Simple word overlap check
    words1 = set(desc1.split())
    words2 = set(desc2.split())
    
    if not words1 or not words2:
        return False
    
    overlap = len(words1 & words2) / max(len(words1), len(words2))
    return overlap >= threshold


def analyze_pattern(expenses, user_id):
    """Analyze a group of similar expenses to determine pattern"""
    if len(expenses) < 2:
        return None
    
    # Sort by date
    expenses = sorted(expenses, key=lambda e: e.date)
    
    # Calculate intervals between expenses
    intervals = []
    for i in range(len(expenses) - 1):
        days = (expenses[i + 1].date - expenses[i].date).days
        intervals.append(days)
    
    if not intervals:
        return None
    
    # Determine frequency
    avg_interval = sum(intervals) / len(intervals)
    frequency, confidence = determine_frequency(intervals, avg_interval)
    
    if not frequency:
        return None
    
    # Calculate average amount
    avg_amount = sum(e.amount for e in expenses) / len(expenses)
    amount_variance = calculate_variance([e.amount for e in expenses])
    
    # Adjust confidence based on amount consistency
    if amount_variance < 0.05:  # Less than 5% variance
        confidence += 10
    elif amount_variance > 0.2:  # More than 20% variance
        confidence -= 10
    
    confidence = min(max(confidence, 0), 100)  # Clamp between 0-100
    
    # Generate suggested name
    suggested_name = generate_subscription_name(expenses[0])
    
    # Check if pattern already exists
    existing = RecurringPattern.query.filter_by(
        user_id=user_id,
        suggested_name=suggested_name,
        is_dismissed=False,
        is_converted=False
    ).first()
    
    if existing:
        return None  # Don't create duplicates
    
    return {
        'user_id': user_id,
        'category_id': expenses[0].category_id,
        'suggested_name': suggested_name,
        'average_amount': round(avg_amount, 2),
        'detected_frequency': frequency,
        'confidence_score': round(confidence, 1),
        'expense_ids': json.dumps([e.id for e in expenses]),
        'first_occurrence': expenses[0].date,
        'last_occurrence': expenses[-1].date,
        'occurrence_count': len(expenses)
    }


def determine_frequency(intervals, avg_interval):
    """Determine frequency from intervals"""
    # Check consistency of intervals
    variance = calculate_variance(intervals)
    
    # Base confidence on consistency
    base_confidence = 70 if variance < 0.15 else 50
    
    # Determine frequency based on average interval
    if 5 <= avg_interval <= 9:
        return 'weekly', base_confidence + 10
    elif 12 <= avg_interval <= 16:
        return 'biweekly', base_confidence
    elif 27 <= avg_interval <= 33:
        return 'monthly', base_confidence + 15
    elif 85 <= avg_interval <= 95:
        return 'quarterly', base_confidence
    elif 355 <= avg_interval <= 375:
        return 'yearly', base_confidence
    else:
        # Check if it's a multiple of common frequencies
        if 25 <= avg_interval <= 35:
            return 'monthly', base_confidence - 10
        elif 7 <= avg_interval <= 10:
            return 'weekly', base_confidence - 10
    
    return None, 0


def calculate_variance(values):
    """Calculate coefficient of variation"""
    if not values or len(values) < 2:
        return 0
    
    avg = sum(values) / len(values)
    if avg == 0:
        return 0
    
    variance = sum((x - avg) ** 2 for x in values) / len(values)
    std_dev = variance ** 0.5
    
    return std_dev / avg


def generate_subscription_name(expense):
    """Generate a friendly name for the subscription"""
    desc = expense.description or 'Recurring Expense'
    
    # Clean up description
    desc = re.sub(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', '', desc)
    desc = re.sub(r'#\d+', '', desc)
    desc = re.sub(r'\s+\d+$', '', desc)
    desc = desc.strip()
    
    # Capitalize first letter of each word
    desc = ' '.join(word.capitalize() for word in desc.split())
    
    # Limit length
    if len(desc) > 50:
        desc = desc[:47] + '...'
    
    return desc or 'Recurring Expense'


def save_detected_patterns(patterns):
    """Save detected patterns to database"""
    saved_count = 0
    
    for pattern_data in patterns:
        pattern = RecurringPattern(**pattern_data)
        db.session.add(pattern)
        saved_count += 1
    
    try:
        db.session.commit()
        return saved_count
    except Exception as e:
        db.session.rollback()
        print(f"Error saving patterns: {e}")
        return 0


def get_user_suggestions(user_id):
    """Get all active suggestions for a user"""
    return RecurringPattern.query.filter_by(
        user_id=user_id,
        is_dismissed=False,
        is_converted=False
    ).order_by(RecurringPattern.confidence_score.desc()).all()


def convert_pattern_to_subscription(pattern_id, user_id):
    """Convert a detected pattern to a confirmed subscription"""
    pattern = RecurringPattern.query.filter_by(
        id=pattern_id,
        user_id=user_id
    ).first()
    
    if not pattern or pattern.is_converted:
        return None
    
    # Create subscription
    subscription = Subscription(
        name=pattern.suggested_name,
        amount=pattern.average_amount,
        frequency=pattern.detected_frequency,
        category_id=pattern.category_id,
        user_id=pattern.user_id,
        next_due_date=pattern.last_occurrence + timedelta(days=get_frequency_days(pattern.detected_frequency)),
        is_active=True,
        is_confirmed=True,
        auto_detected=True,
        confidence_score=pattern.confidence_score
    )
    
    db.session.add(subscription)
    
    # Mark pattern as converted
    pattern.is_converted = True
    
    try:
        db.session.commit()
        return subscription
    except Exception as e:
        db.session.rollback()
        print(f"Error converting pattern: {e}")
        return None


def get_frequency_days(frequency):
    """Get number of days for frequency"""
    frequency_map = {
        'weekly': 7,
        'biweekly': 14,
        'monthly': 30,
        'quarterly': 90,
        'yearly': 365
    }
    return frequency_map.get(frequency, 30)


def dismiss_pattern(pattern_id, user_id):
    """Dismiss a detected pattern"""
    pattern = RecurringPattern.query.filter_by(
        id=pattern_id,
        user_id=user_id
    ).first()
    
    if pattern:
        pattern.is_dismissed = True
        try:
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error dismissing pattern: {e}")
    
    return False
