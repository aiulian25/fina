from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models import RecurringExpense, Expense, Category
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict
import re

bp = Blueprint('recurring', __name__, url_prefix='/api/recurring')


def calculate_next_due_date(frequency, day_of_period=None, from_date=None):
    """Calculate next due date based on frequency"""
    base_date = from_date or datetime.utcnow()
    
    if frequency == 'daily':
        return base_date + timedelta(days=1)
    elif frequency == 'weekly':
        # day_of_period is day of week (0=Monday, 6=Sunday)
        target_day = day_of_period if day_of_period is not None else base_date.weekday()
        days_ahead = target_day - base_date.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return base_date + timedelta(days=days_ahead)
    elif frequency == 'monthly':
        # day_of_period is day of month (1-31)
        target_day = day_of_period if day_of_period is not None else base_date.day
        next_month = base_date + relativedelta(months=1)
        try:
            return next_month.replace(day=min(target_day, 28))  # Safe day
        except ValueError:
            # Handle months with fewer days
            return next_month.replace(day=28)
    elif frequency == 'yearly':
        return base_date + relativedelta(years=1)
    else:
        return base_date + timedelta(days=30)


@bp.route('/', methods=['GET'])
@login_required
def get_recurring_expenses():
    """Get all recurring expenses for current user"""
    # Security: Filter by user_id
    recurring = RecurringExpense.query.filter_by(user_id=current_user.id).order_by(
        RecurringExpense.is_active.desc(),
        RecurringExpense.next_due_date.asc()
    ).all()
    
    return jsonify({
        'recurring_expenses': [r.to_dict() for r in recurring]
    })


@bp.route('/', methods=['POST'])
@login_required
def create_recurring_expense():
    """Create a new recurring expense"""
    data = request.get_json()
    
    # Validate required fields
    if not data or not data.get('name') or not data.get('amount') or not data.get('category_id') or not data.get('frequency'):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    # Security: Validate amount to prevent negative values and overflow attacks
    from app.utils import validate_amount, validate_positive_integer
    is_valid, validated_amount, error_msg = validate_amount(data.get('amount'), 'Amount')
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400
    
    # Security: Validate category_id
    is_valid, validated_category_id, error_msg = validate_positive_integer(data.get('category_id'), 'Category ID', min_val=1)
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400
    
    # Security: Verify category belongs to current user
    category = Category.query.filter_by(id=validated_category_id, user_id=current_user.id).first()
    if not category:
        return jsonify({'success': False, 'message': 'Invalid category'}), 400
    
    # Validate frequency
    valid_frequencies = ['daily', 'weekly', 'monthly', 'yearly']
    frequency = data.get('frequency')
    if frequency not in valid_frequencies:
        return jsonify({'success': False, 'message': 'Invalid frequency'}), 400
    
    # Calculate next due date
    day_of_period = data.get('day_of_period')
    next_due_date = data.get('next_due_date')
    
    if next_due_date:
        next_due_date = datetime.fromisoformat(next_due_date)
    else:
        next_due_date = calculate_next_due_date(frequency, day_of_period)
    
    # Create recurring expense
    recurring = RecurringExpense(
        name=data.get('name'),
        amount=float(data.get('amount')),
        currency=data.get('currency', current_user.currency),
        category_id=int(data.get('category_id')),
        frequency=frequency,
        day_of_period=day_of_period,
        next_due_date=next_due_date,
        auto_create=data.get('auto_create', False),
        is_active=data.get('is_active', True),
        notes=data.get('notes'),
        detected=False,  # Manually created
        user_id=current_user.id
    )
    
    db.session.add(recurring)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'recurring_expense': recurring.to_dict()
    }), 201


@bp.route('/<int:recurring_id>', methods=['PUT'])
@login_required
def update_recurring_expense(recurring_id):
    """Update a recurring expense"""
    # Security: Filter by user_id
    recurring = RecurringExpense.query.filter_by(id=recurring_id, user_id=current_user.id).first()
    
    if not recurring:
        return jsonify({'success': False, 'message': 'Recurring expense not found'}), 404
    
    data = request.get_json()
    
    # Security: Import validation functions
    from app.utils import validate_amount, validate_positive_integer
    
    # Update fields
    if data.get('name'):
        recurring.name = data.get('name')
    if data.get('amount'):
        is_valid, validated_amount, error_msg = validate_amount(data.get('amount'), 'Amount')
        if not is_valid:
            return jsonify({'success': False, 'message': error_msg}), 400
        recurring.amount = validated_amount
    if data.get('currency'):
        recurring.currency = data.get('currency')
    if data.get('category_id'):
        is_valid, validated_category_id, error_msg = validate_positive_integer(data.get('category_id'), 'Category ID', min_val=1)
        if not is_valid:
            return jsonify({'success': False, 'message': error_msg}), 400
        # Security: Verify category belongs to current user
        category = Category.query.filter_by(id=validated_category_id, user_id=current_user.id).first()
        if not category:
            return jsonify({'success': False, 'message': 'Invalid category'}), 400
        recurring.category_id = validated_category_id
    if data.get('frequency'):
        valid_frequencies = ['daily', 'weekly', 'monthly', 'yearly']
        if data.get('frequency') not in valid_frequencies:
            return jsonify({'success': False, 'message': 'Invalid frequency'}), 400
        recurring.frequency = data.get('frequency')
    if 'day_of_period' in data:
        recurring.day_of_period = data.get('day_of_period')
    if data.get('next_due_date'):
        recurring.next_due_date = datetime.fromisoformat(data.get('next_due_date'))
    if 'auto_create' in data:
        recurring.auto_create = data.get('auto_create')
    if 'is_active' in data:
        recurring.is_active = data.get('is_active')
    if 'notes' in data:
        recurring.notes = data.get('notes')
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'recurring_expense': recurring.to_dict()
    })


@bp.route('/<int:recurring_id>', methods=['DELETE'])
@login_required
def delete_recurring_expense(recurring_id):
    """Delete a recurring expense"""
    # Security: Filter by user_id
    recurring = RecurringExpense.query.filter_by(id=recurring_id, user_id=current_user.id).first()
    
    if not recurring:
        return jsonify({'success': False, 'message': 'Recurring expense not found'}), 404
    
    db.session.delete(recurring)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Recurring expense deleted'})


@bp.route('/<int:recurring_id>/create-expense', methods=['POST'])
@login_required
def create_expense_from_recurring(recurring_id):
    """Manually create an expense from a recurring expense"""
    # Security: Filter by user_id
    recurring = RecurringExpense.query.filter_by(id=recurring_id, user_id=current_user.id).first()
    
    if not recurring:
        return jsonify({'success': False, 'message': 'Recurring expense not found'}), 404
    
    # Create expense
    expense = Expense(
        amount=recurring.amount,
        currency=recurring.currency,
        description=recurring.name,
        category_id=recurring.category_id,
        user_id=current_user.id,
        tags=['recurring', recurring.frequency],
        date=datetime.utcnow()
    )
    expense.set_tags(['recurring', recurring.frequency])
    
    # Update recurring expense
    recurring.last_created_date = datetime.utcnow()
    recurring.next_due_date = calculate_next_due_date(
        recurring.frequency,
        recurring.day_of_period,
        recurring.next_due_date
    )
    
    db.session.add(expense)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'expense': expense.to_dict(),
        'recurring_expense': recurring.to_dict()
    }), 201


@bp.route('/detect', methods=['POST'])
@login_required
def detect_recurring_patterns():
    """
    Detect recurring expense patterns from historical expenses
    Returns suggestions for potential recurring expenses
    """
    # Get user's expenses from last 6 months
    six_months_ago = datetime.utcnow() - relativedelta(months=6)
    expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= six_months_ago
    ).order_by(Expense.date.asc()).all()
    
    if len(expenses) < 10:
        return jsonify({
            'suggestions': [],
            'message': 'Not enough expense history to detect patterns'
        })
    
    # Group expenses by similar descriptions and amounts
    patterns = defaultdict(list)
    
    for expense in expenses:
        # Normalize description (lowercase, remove numbers/special chars)
        normalized_desc = re.sub(r'[^a-z\s]', '', expense.description.lower()).strip()
        
        # Create a key based on normalized description and approximate amount
        amount_bucket = round(expense.amount / 10) * 10  # Group by 10 currency units
        key = f"{normalized_desc}_{amount_bucket}_{expense.category_id}"
        
        patterns[key].append(expense)
    
    suggestions = []
    
    # Analyze patterns
    for key, expense_list in patterns.items():
        if len(expense_list) < 3:  # Need at least 3 occurrences
            continue
        
        # Calculate intervals between expenses
        intervals = []
        for i in range(1, len(expense_list)):
            days_diff = (expense_list[i].date - expense_list[i-1].date).days
            intervals.append(days_diff)
        
        if not intervals:
            continue
        
        avg_interval = sum(intervals) / len(intervals)
        # Check variance to ensure consistency
        variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
        std_dev = variance ** 0.5
        
        # Determine if pattern is consistent
        if std_dev / avg_interval > 0.3:  # More than 30% variance
            continue
        
        # Determine frequency
        frequency = None
        day_of_period = None
        confidence = 0
        
        if 25 <= avg_interval <= 35:  # Monthly
            frequency = 'monthly'
            # Get most common day of month
            days = [e.date.day for e in expense_list]
            day_of_period = max(set(days), key=days.count)
            confidence = 90 - (std_dev / avg_interval * 100)
        elif 6 <= avg_interval <= 8:  # Weekly
            frequency = 'weekly'
            days = [e.date.weekday() for e in expense_list]
            day_of_period = max(set(days), key=days.count)
            confidence = 85 - (std_dev / avg_interval * 100)
        elif 360 <= avg_interval <= 370:  # Yearly
            frequency = 'yearly'
            confidence = 80 - (std_dev / avg_interval * 100)
        
        if frequency and confidence > 60:  # Only suggest if confidence > 60%
            # Use most recent expense data
            latest = expense_list[-1]
            avg_amount = sum(e.amount for e in expense_list) / len(expense_list)
            
            # Check if already exists as recurring expense
            existing = RecurringExpense.query.filter_by(
                user_id=current_user.id,
                name=latest.description,
                category_id=latest.category_id
            ).first()
            
            if not existing:
                suggestions.append({
                    'name': latest.description,
                    'amount': round(avg_amount, 2),
                    'currency': latest.currency,
                    'category_id': latest.category_id,
                    'category_name': latest.category.name,
                    'category_color': latest.category.color,
                    'frequency': frequency,
                    'day_of_period': day_of_period,
                    'confidence_score': round(confidence, 1),
                    'occurrences': len(expense_list),
                    'detected': True
                })
    
    # Sort by confidence score
    suggestions.sort(key=lambda x: x['confidence_score'], reverse=True)
    
    return jsonify({
        'suggestions': suggestions[:10],  # Return top 10
        'message': f'Found {len(suggestions)} potential recurring expenses'
    })


@bp.route('/accept-suggestion', methods=['POST'])
@login_required
def accept_suggestion():
    """Accept a detected recurring expense suggestion and create it"""
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('amount') or not data.get('category_id') or not data.get('frequency'):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    # Security: Validate amount to prevent negative values and overflow attacks
    from app.utils import validate_amount, validate_positive_integer
    is_valid, validated_amount, error_msg = validate_amount(data.get('amount'), 'Amount')
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400
    
    # Security: Validate category_id
    is_valid, validated_category_id, error_msg = validate_positive_integer(data.get('category_id'), 'Category ID', min_val=1)
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400
    
    # Security: Verify category belongs to current user
    category = Category.query.filter_by(id=validated_category_id, user_id=current_user.id).first()
    if not category:
        return jsonify({'success': False, 'message': 'Invalid category'}), 400
    
    # Calculate next due date
    day_of_period = data.get('day_of_period')
    next_due_date = calculate_next_due_date(data.get('frequency'), day_of_period)
    
    # Create recurring expense
    recurring = RecurringExpense(
        name=data.get('name'),
        amount=validated_amount,
        currency=data.get('currency', current_user.currency),
        category_id=validated_category_id,
        frequency=data.get('frequency'),
        day_of_period=day_of_period,
        next_due_date=next_due_date,
        auto_create=data.get('auto_create', False),
        is_active=True,
        detected=True,  # Auto-detected
        confidence_score=data.get('confidence_score', 0),
        user_id=current_user.id
    )
    
    db.session.add(recurring)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'recurring_expense': recurring.to_dict()
    }), 201


@bp.route('/upcoming', methods=['GET'])
@login_required
def get_upcoming_recurring():
    """Get upcoming recurring expenses (next 30 days)"""
    # Security: Filter by user_id
    thirty_days_later = datetime.utcnow() + timedelta(days=30)
    
    recurring = RecurringExpense.query.filter(
        RecurringExpense.user_id == current_user.id,
        RecurringExpense.is_active == True,
        RecurringExpense.next_due_date <= thirty_days_later
    ).order_by(RecurringExpense.next_due_date.asc()).all()
    
    return jsonify({
        'upcoming': [r.to_dict() for r in recurring]
    })


@bp.route('/process-due', methods=['POST'])
@login_required
def process_due_manual():
    """
    Manually trigger processing of due recurring expenses
    Admin only for security - prevents users from spamming expense creation
    """
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        from app.scheduler import process_due_recurring_expenses
        process_due_recurring_expenses()
        return jsonify({
            'success': True,
            'message': 'Recurring expenses processed successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error processing recurring expenses: {str(e)}'
        }), 500


@bp.route('/sync-currency', methods=['POST'])
@login_required
def sync_currency():
    """
    Sync all user's recurring expenses to use their current profile currency
    Security: Only updates current user's recurring expenses
    """
    try:
        # Update all recurring expenses to match user's current currency
        RecurringExpense.query.filter_by(user_id=current_user.id).update(
            {'currency': current_user.currency}
        )
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'All recurring expenses synced to your current currency'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error syncing currency: {str(e)}'
        }), 500
