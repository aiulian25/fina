from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Income
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json

bp = Blueprint('income', __name__, url_prefix='/api/income')


def calculate_income_next_due_date(frequency, custom_days=None, from_date=None):
    """Calculate next due date for recurring income based on frequency
    Args:
        frequency: 'once', 'weekly', 'biweekly', 'every4weeks', 'monthly', 'custom'
        custom_days: Number of days for custom frequency
        from_date: Starting date (default: today)
    Returns:
        Next due date or None for one-time income
    """
    if frequency == 'once':
        return None
    
    if from_date is None:
        from_date = datetime.utcnow()
    
    if frequency == 'weekly':
        return from_date + timedelta(days=7)
    elif frequency == 'biweekly':
        return from_date + timedelta(days=14)
    elif frequency == 'every4weeks':
        return from_date + timedelta(days=28)
    elif frequency == 'monthly':
        return from_date + relativedelta(months=1)
    elif frequency == 'custom' and custom_days:
        return from_date + timedelta(days=custom_days)
    
    return None


@bp.route('/', methods=['GET'])
@login_required
def get_income():
    """Get income entries with filtering and pagination
    Security: Only returns income for current_user
    """
    current_app.logger.info(f"Getting income for user {current_user.id}")
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    source = request.args.get('source')
    search = request.args.get('search', '')
    
    # Security: Filter by current user
    query = Income.query.filter_by(user_id=current_user.id)
    
    if source:
        query = query.filter_by(source=source)
    
    if start_date:
        query = query.filter(Income.date >= datetime.fromisoformat(start_date))
    
    if end_date:
        query = query.filter(Income.date <= datetime.fromisoformat(end_date))
    
    if search:
        query = query.filter(Income.description.ilike(f'%{search}%'))
    
    pagination = query.order_by(Income.date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    current_app.logger.info(f"Found {pagination.total} income entries for user {current_user.id}")
    
    return jsonify({
        'income': [inc.to_dict() for inc in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@bp.route('/', methods=['POST'])
@login_required
def create_income():
    """Create new income entry
    Security: Only creates income for current_user
    """
    data = request.get_json()
    current_app.logger.info(f"Creating income for user {current_user.id}, data: {data}")
    
    # Validate required fields
    if not data or not data.get('amount') or not data.get('source') or not data.get('description'):
        current_app.logger.warning(f"Missing required fields: {data}")
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    # Security: Validate amount to prevent negative values and overflow attacks
    from app.utils import validate_amount
    is_valid, validated_amount, error_msg = validate_amount(data.get('amount'), 'Amount')
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400
    
    try:
        income_date = datetime.fromisoformat(data.get('date')) if data.get('date') else datetime.utcnow()
        frequency = data.get('frequency', 'once')
        custom_days = data.get('custom_days')
        auto_create = data.get('auto_create', False)
        
        # Calculate next due date for recurring income
        next_due_date = None
        if frequency != 'once' and auto_create:
            next_due_date = calculate_income_next_due_date(frequency, custom_days, income_date)
        
        # Create income entry
        income = Income(
            amount=validated_amount,
            currency=data.get('currency', current_user.currency),
            description=data.get('description'),
            source=data.get('source'),
            user_id=current_user.id,
            tags=json.dumps(data.get('tags', [])) if isinstance(data.get('tags'), list) else data.get('tags', '[]'),
            frequency=frequency,
            custom_days=custom_days,
            next_due_date=next_due_date,
            is_active=True,
            auto_create=auto_create,
            date=income_date
        )
        
        current_app.logger.info(f"Adding income to session: {income.description}")
        db.session.add(income)
        db.session.commit()
        current_app.logger.info(f"Income committed with ID: {income.id}")
        
        # Verify it was saved
        saved_income = Income.query.filter_by(id=income.id).first()
        current_app.logger.info(f"Verification - Income exists: {saved_income is not None}")
        
        return jsonify({
            'success': True,
            'message': 'Income added successfully',
            'income': income.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating income: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to create income'}), 500


@bp.route('/<int:income_id>', methods=['PUT'])
@login_required
def update_income(income_id):
    """Update income entry
    Security: Only allows updating user's own income
    """
    # Security check: verify income belongs to current user
    income = Income.query.filter_by(id=income_id, user_id=current_user.id).first()
    if not income:
        return jsonify({'success': False, 'message': 'Income not found'}), 404
    
    data = request.get_json()
    
    # Security: Import validation function
    from app.utils import validate_amount
    
    try:
        # Update fields
        if 'amount' in data:
            is_valid, validated_amount, error_msg = validate_amount(data['amount'], 'Amount')
            if not is_valid:
                return jsonify({'success': False, 'message': error_msg}), 400
            income.amount = validated_amount
        if 'currency' in data:
            income.currency = data['currency']
        if 'description' in data:
            income.description = data['description']
        if 'source' in data:
            income.source = data['source']
        if 'tags' in data:
            income.tags = json.dumps(data['tags']) if isinstance(data['tags'], list) else data['tags']
        if 'date' in data:
            income.date = datetime.fromisoformat(data['date'])
        
        # Handle frequency changes
        frequency_changed = False
        if 'frequency' in data and data['frequency'] != income.frequency:
            income.frequency = data['frequency']
            frequency_changed = True
        
        if 'custom_days' in data:
            income.custom_days = data['custom_days']
            frequency_changed = True
        
        if 'auto_create' in data:
            income.auto_create = data['auto_create']
        
        if 'is_active' in data:
            income.is_active = data['is_active']
        
        # Recalculate next_due_date if frequency changed or auto_create enabled
        if (frequency_changed or 'auto_create' in data) and income.auto_create and income.is_active:
            if income.frequency != 'once':
                from_date = income.last_created_date if income.last_created_date else income.date
                income.next_due_date = calculate_income_next_due_date(
                    income.frequency, 
                    income.custom_days, 
                    from_date
                )
            else:
                income.next_due_date = None
        elif not income.auto_create or not income.is_active:
            income.next_due_date = None
        
        income.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Income updated successfully',
            'income': income.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating income: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to update income'}), 500


@bp.route('/<int:income_id>', methods=['DELETE'])
@login_required
def delete_income(income_id):
    """Delete income entry
    Security: Only allows deleting user's own income
    """
    # Security check: verify income belongs to current user
    income = Income.query.filter_by(id=income_id, user_id=current_user.id).first()
    if not income:
        return jsonify({'success': False, 'message': 'Income not found'}), 404
    
    try:
        db.session.delete(income)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Income deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting income: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to delete income'}), 500


@bp.route('/<int:income_id>/toggle', methods=['PUT'])
@login_required
def toggle_recurring_income(income_id):
    """Toggle recurring income active status
    Security: Only allows toggling user's own income
    """
    # Security check: verify income belongs to current user
    income = Income.query.filter_by(id=income_id, user_id=current_user.id).first()
    if not income:
        return jsonify({'success': False, 'message': 'Income not found'}), 404
    
    try:
        income.is_active = not income.is_active
        
        # Clear next_due_date if deactivated
        if not income.is_active:
            income.next_due_date = None
        elif income.auto_create and income.frequency != 'once':
            # Recalculate next_due_date when reactivated
            from_date = income.last_created_date if income.last_created_date else income.date
            income.next_due_date = calculate_income_next_due_date(
                income.frequency, 
                income.custom_days, 
                from_date
            )
        
        income.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Income {"activated" if income.is_active else "deactivated"}',
            'income': income.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error toggling income: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to toggle income'}), 500


@bp.route('/<int:income_id>/create-now', methods=['POST'])
@login_required
def create_income_now(income_id):
    """Manually create income entry from recurring income
    Security: Only allows creating from user's own recurring income
    """
    # Security check: verify income belongs to current user
    recurring_income = Income.query.filter_by(id=income_id, user_id=current_user.id).first()
    if not recurring_income:
        return jsonify({'success': False, 'message': 'Recurring income not found'}), 404
    
    if recurring_income.frequency == 'once':
        return jsonify({'success': False, 'message': 'This is not a recurring income'}), 400
    
    try:
        # Create new income entry based on recurring income
        new_income = Income(
            amount=recurring_income.amount,
            currency=recurring_income.currency,
            description=recurring_income.description,
            source=recurring_income.source,
            user_id=current_user.id,
            tags=recurring_income.tags,
            frequency='once',  # Created income is one-time
            date=datetime.utcnow()
        )
        
        db.session.add(new_income)
        
        # Update recurring income's next due date and last created date
        recurring_income.last_created_date = datetime.utcnow()
        if recurring_income.auto_create and recurring_income.is_active:
            recurring_income.next_due_date = calculate_income_next_due_date(
                recurring_income.frequency,
                recurring_income.custom_days,
                recurring_income.last_created_date
            )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Income created successfully',
            'income': new_income.to_dict(),
            'recurring_income': recurring_income.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating income from recurring: {str(e)}")
        return jsonify({'success': False, 'message': 'Failed to create income'}), 500


@bp.route('/sources', methods=['GET'])
@login_required
def get_income_sources():
    """Get list of income sources
    Returns predefined sources for consistency
    """
    sources = [
        {'value': 'Salary', 'label': 'Salary', 'icon': 'payments'},
        {'value': 'Freelance', 'label': 'Freelance', 'icon': 'work'},
        {'value': 'Investment', 'label': 'Investment', 'icon': 'trending_up'},
        {'value': 'Rental', 'label': 'Rental Income', 'icon': 'home'},
        {'value': 'Gift', 'label': 'Gift', 'icon': 'card_giftcard'},
        {'value': 'Bonus', 'label': 'Bonus', 'icon': 'star'},
        {'value': 'Refund', 'label': 'Refund', 'icon': 'refresh'},
        {'value': 'Other', 'label': 'Other', 'icon': 'category'}
    ]
    
    return jsonify({'sources': sources})


@bp.route('/summary', methods=['GET'])
@login_required
def get_income_summary():
    """Get income summary for dashboard
    Security: Only returns data for current_user
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    # Security: Filter by current user
    query = Income.query.filter_by(user_id=current_user.id)
    
    if start_date:
        query = query.filter(Income.date >= datetime.fromisoformat(start_date))
    
    if end_date:
        query = query.filter(Income.date <= datetime.fromisoformat(end_date))
    
    # Calculate totals by source
    income_by_source = db.session.query(
        Income.source,
        db.func.sum(Income.amount).label('total'),
        db.func.count(Income.id).label('count')
    ).filter_by(user_id=current_user.id)
    
    if start_date:
        income_by_source = income_by_source.filter(Income.date >= datetime.fromisoformat(start_date))
    if end_date:
        income_by_source = income_by_source.filter(Income.date <= datetime.fromisoformat(end_date))
    
    income_by_source = income_by_source.group_by(Income.source).all()
    
    total_income = sum(item.total for item in income_by_source)
    
    breakdown = [
        {
            'source': item.source,
            'total': float(item.total),
            'count': item.count,
            'percentage': (float(item.total) / total_income * 100) if total_income > 0 else 0
        }
        for item in income_by_source
    ]
    
    return jsonify({
        'total_income': total_income,
        'count': sum(item.count for item in income_by_source),
        'breakdown': breakdown
    })
