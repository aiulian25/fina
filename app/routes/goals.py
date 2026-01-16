"""
Savings Goals API Routes
Security: All queries filtered by user_id to ensure users only see their own goals
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models import SavingsGoal, SavingsContribution
from datetime import datetime
from sqlalchemy import func

bp = Blueprint('goals', __name__, url_prefix='/api/goals')

# Predefined goal categories with icons and colors
GOAL_CATEGORIES = {
    'vacation': {'icon': 'flight_takeoff', 'color': '#f59e0b', 'name_en': 'Vacation', 'name_ro': 'Vacanță'},
    'emergency': {'icon': 'health_and_safety', 'color': '#ef4444', 'name_en': 'Emergency Fund', 'name_ro': 'Fond de Urgență'},
    'car': {'icon': 'directions_car', 'color': '#3b82f6', 'name_en': 'New Car', 'name_ro': 'Mașină Nouă'},
    'house': {'icon': 'home', 'color': '#10b981', 'name_en': 'House/Apartment', 'name_ro': 'Casă/Apartament'},
    'education': {'icon': 'school', 'color': '#8b5cf6', 'name_en': 'Education', 'name_ro': 'Educație'},
    'wedding': {'icon': 'favorite', 'color': '#ec4899', 'name_en': 'Wedding', 'name_ro': 'Nuntă'},
    'retirement': {'icon': 'elderly', 'color': '#6366f1', 'name_en': 'Retirement', 'name_ro': 'Pensie'},
    'gadget': {'icon': 'devices', 'color': '#14b8a6', 'name_en': 'Gadget/Tech', 'name_ro': 'Gadget/Tech'},
    'custom': {'icon': 'savings', 'color': '#2b8cee', 'name_en': 'Custom Goal', 'name_ro': 'Obiectiv Personal'}
}


@bp.route('/categories', methods=['GET'])
@login_required
def get_categories():
    """Get predefined goal categories with icons and colors"""
    return jsonify({
        'success': True,
        'categories': GOAL_CATEGORIES
    })


@bp.route('/', methods=['GET'])
@login_required
def get_goals():
    """Get all savings goals for current user
    Security: Only returns goals for current_user
    """
    current_app.logger.info(f"Getting savings goals for user {current_user.id}")
    
    # Query parameters
    show_completed = request.args.get('show_completed', 'false').lower() == 'true'
    category = request.args.get('category')
    
    # Security: Filter by current user
    query = SavingsGoal.query.filter_by(user_id=current_user.id)
    
    if not show_completed:
        query = query.filter_by(is_completed=False)
    
    if category:
        query = query.filter_by(category=category)
    
    goals = query.order_by(SavingsGoal.created_at.desc()).all()
    
    # Calculate summary stats
    total_saved = sum(g.current_amount for g in goals if not g.is_completed)
    total_target = sum(g.target_amount for g in goals if not g.is_completed)
    active_goals = len([g for g in goals if not g.is_completed])
    completed_goals = SavingsGoal.query.filter_by(user_id=current_user.id, is_completed=True).count()
    
    return jsonify({
        'success': True,
        'goals': [goal.to_dict() for goal in goals],
        'summary': {
            'total_saved': total_saved,
            'total_target': total_target,
            'overall_progress': round((total_saved / total_target * 100), 1) if total_target > 0 else 0,
            'active_goals': active_goals,
            'completed_goals': completed_goals
        }
    })


@bp.route('/<int:goal_id>', methods=['GET'])
@login_required
def get_goal(goal_id):
    """Get a specific savings goal with contribution history
    Security: Only allows viewing user's own goals
    """
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=current_user.id).first()
    
    if not goal:
        return jsonify({'success': False, 'message': 'Goal not found'}), 404
    
    # Get contribution history
    contributions = SavingsContribution.query.filter_by(goal_id=goal_id)\
        .order_by(SavingsContribution.date.desc()).limit(50).all()
    
    goal_data = goal.to_dict()
    goal_data['contributions'] = [c.to_dict() for c in contributions]
    
    return jsonify({
        'success': True,
        'goal': goal_data
    })


@bp.route('/', methods=['POST'])
@login_required
def create_goal():
    """Create a new savings goal
    Security: Only creates goals for current_user
    """
    data = request.get_json()
    current_app.logger.info(f"Creating savings goal for user {current_user.id}, data: {data}")
    
    # Validate required fields
    if not data or not data.get('name') or not data.get('target_amount'):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    # Security: Validate amounts to prevent negative values and overflow attacks
    from app.utils import validate_amount
    is_valid, target_amount, error_msg = validate_amount(data.get('target_amount'), 'Target amount')
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400
    
    # Validate current_amount if provided
    current_amount = 0
    if data.get('current_amount'):
        is_valid, current_amount, error_msg = validate_amount(data.get('current_amount'), 'Current amount', allow_zero=True)
        if not is_valid:
            return jsonify({'success': False, 'message': error_msg}), 400
    
    try:
        
        # Parse target date if provided
        target_date = None
        if data.get('target_date'):
            target_date = datetime.fromisoformat(data.get('target_date').replace('Z', '+00:00'))
        
        # Get category defaults or use custom
        category = data.get('category', 'custom')
        category_defaults = GOAL_CATEGORIES.get(category, GOAL_CATEGORIES['custom'])
        
        goal = SavingsGoal(
            name=data.get('name'),
            description=data.get('description', ''),
            target_amount=target_amount,
            current_amount=current_amount,
            currency=data.get('currency', current_user.currency),
            icon=data.get('icon', category_defaults['icon']),
            color=data.get('color', category_defaults['color']),
            category=category,
            target_date=target_date,
            user_id=current_user.id
        )
        
        db.session.add(goal)
        db.session.commit()
        
        current_app.logger.info(f"Savings goal created with ID: {goal.id}")
        
        return jsonify({
            'success': True,
            'message': 'Savings goal created successfully',
            'goal': goal.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'success': False, 'message': 'Invalid amount value'}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating savings goal: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to create goal'}), 500


@bp.route('/<int:goal_id>', methods=['PUT'])
@login_required
def update_goal(goal_id):
    """Update a savings goal
    Security: Only allows updating user's own goals
    """
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=current_user.id).first()
    
    if not goal:
        return jsonify({'success': False, 'message': 'Goal not found'}), 404
    
    data = request.get_json()
    
    try:
        if data.get('name'):
            goal.name = data.get('name')
        if 'description' in data:
            goal.description = data.get('description')
        if data.get('target_amount'):
            goal.target_amount = float(data.get('target_amount'))
        if data.get('icon'):
            goal.icon = data.get('icon')
        if data.get('color'):
            goal.color = data.get('color')
        if data.get('category'):
            goal.category = data.get('category')
        if 'target_date' in data:
            if data.get('target_date'):
                goal.target_date = datetime.fromisoformat(data.get('target_date').replace('Z', '+00:00'))
            else:
                goal.target_date = None
        if 'is_active' in data:
            goal.is_active = data.get('is_active')
        
        goal.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Goal updated successfully',
            'goal': goal.to_dict()
        })
        
    except ValueError as e:
        return jsonify({'success': False, 'message': 'Invalid value provided'}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error updating goal: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to update goal'}), 500


@bp.route('/<int:goal_id>', methods=['DELETE'])
@login_required
def delete_goal(goal_id):
    """Delete a savings goal
    Security: Only allows deleting user's own goals
    """
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=current_user.id).first()
    
    if not goal:
        return jsonify({'success': False, 'message': 'Goal not found'}), 404
    
    try:
        db.session.delete(goal)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Goal deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting goal: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to delete goal'}), 500


@bp.route('/<int:goal_id>/contribute', methods=['POST'])
@login_required
def add_contribution(goal_id):
    """Add a contribution to a savings goal
    Security: Only allows contributing to user's own goals
    """
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=current_user.id).first()
    
    if not goal:
        return jsonify({'success': False, 'message': 'Goal not found'}), 404
    
    if goal.is_completed:
        return jsonify({'success': False, 'message': 'Goal is already completed'}), 400
    
    data = request.get_json()
    
    if not data or not data.get('amount'):
        return jsonify({'success': False, 'message': 'Amount is required'}), 400
    
    # Security: Validate amount to prevent negative values and overflow attacks
    from app.utils import validate_amount
    is_valid, amount, error_msg = validate_amount(data.get('amount'), 'Contribution amount')
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400
    
    try:
        # Create contribution record
        contribution = SavingsContribution(
            goal_id=goal_id,
            amount=amount,
            note=data.get('note', ''),
            date=datetime.fromisoformat(data.get('date')) if data.get('date') else datetime.utcnow()
        )
        
        # Update goal's current amount
        old_amount = goal.current_amount
        goal.current_amount += amount
        
        # Check if goal is now completed
        milestone_reached = None
        if goal.current_amount >= goal.target_amount:
            goal.is_completed = True
            goal.completed_at = datetime.utcnow()
            milestone_reached = 100
        else:
            # Check for milestone achievements
            old_milestone = goal.check_milestone()
            if goal.get_progress_percentage() >= 25 and old_milestone < 25:
                milestone_reached = 25
            elif goal.get_progress_percentage() >= 50 and old_milestone < 50:
                milestone_reached = 50
            elif goal.get_progress_percentage() >= 75 and old_milestone < 75:
                milestone_reached = 75
        
        goal.updated_at = datetime.utcnow()
        
        db.session.add(contribution)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Contribution added successfully',
            'contribution': contribution.to_dict(),
            'goal': goal.to_dict(),
            'milestone_reached': milestone_reached
        }), 201
        
    except ValueError as e:
        return jsonify({'success': False, 'message': 'Invalid amount value'}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error adding contribution: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to add contribution'}), 500


@bp.route('/<int:goal_id>/withdraw', methods=['POST'])
@login_required
def withdraw_contribution(goal_id):
    """Withdraw from a savings goal (negative contribution)
    Security: Only allows withdrawing from user's own goals
    """
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=current_user.id).first()
    
    if not goal:
        return jsonify({'success': False, 'message': 'Goal not found'}), 404
    
    data = request.get_json()
    
    if not data or not data.get('amount'):
        return jsonify({'success': False, 'message': 'Amount is required'}), 400
    
    try:
        amount = float(data.get('amount'))
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Amount must be positive'}), 400
        
        if amount > goal.current_amount:
            return jsonify({'success': False, 'message': 'Cannot withdraw more than current amount'}), 400
        
        # Create negative contribution record
        contribution = SavingsContribution(
            goal_id=goal_id,
            amount=-amount,
            note=data.get('note', 'Withdrawal'),
            date=datetime.fromisoformat(data.get('date')) if data.get('date') else datetime.utcnow()
        )
        
        # Update goal's current amount
        goal.current_amount -= amount
        
        # If goal was completed, mark as incomplete
        if goal.is_completed and goal.current_amount < goal.target_amount:
            goal.is_completed = False
            goal.completed_at = None
        
        goal.updated_at = datetime.utcnow()
        
        db.session.add(contribution)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Withdrawal successful',
            'contribution': contribution.to_dict(),
            'goal': goal.to_dict()
        }), 201
        
    except ValueError as e:
        return jsonify({'success': False, 'message': 'Invalid amount value'}), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error withdrawing from goal: {str(e)}", exc_info=True)
        return jsonify({'success': False, 'message': 'Failed to withdraw'}), 500


@bp.route('/<int:goal_id>/contributions', methods=['GET'])
@login_required
def get_contributions(goal_id):
    """Get contribution history for a goal
    Security: Only returns contributions for user's own goals
    """
    goal = SavingsGoal.query.filter_by(id=goal_id, user_id=current_user.id).first()
    
    if not goal:
        return jsonify({'success': False, 'message': 'Goal not found'}), 404
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    pagination = SavingsContribution.query.filter_by(goal_id=goal_id)\
        .order_by(SavingsContribution.date.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'contributions': [c.to_dict() for c in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@bp.route('/summary', methods=['GET'])
@login_required
def get_summary():
    """Get savings goals summary for dashboard
    Security: Only returns data for current_user
    """
    # Active goals with highest progress
    active_goals = SavingsGoal.query.filter_by(
        user_id=current_user.id,
        is_completed=False,
        is_active=True
    ).all()
    
    # Sort by progress percentage
    active_goals.sort(key=lambda g: g.get_progress_percentage(), reverse=True)
    
    # Recently completed goals
    completed_goals = SavingsGoal.query.filter_by(
        user_id=current_user.id,
        is_completed=True
    ).order_by(SavingsGoal.completed_at.desc()).limit(3).all()
    
    # Total stats
    total_saved = sum(g.current_amount for g in active_goals)
    total_target = sum(g.target_amount for g in active_goals)
    
    # Recent contributions across all goals
    recent_contributions = db.session.query(SavingsContribution)\
        .join(SavingsGoal)\
        .filter(SavingsGoal.user_id == current_user.id)\
        .order_by(SavingsContribution.date.desc())\
        .limit(5).all()
    
    return jsonify({
        'success': True,
        'active_goals': [g.to_dict() for g in active_goals[:5]],
        'completed_goals': [g.to_dict() for g in completed_goals],
        'recent_contributions': [c.to_dict() for c in recent_contributions],
        'stats': {
            'total_saved': total_saved,
            'total_target': total_target,
            'overall_progress': round((total_saved / total_target * 100), 1) if total_target > 0 else 0,
            'active_count': len(active_goals),
            'completed_count': SavingsGoal.query.filter_by(user_id=current_user.id, is_completed=True).count()
        }
    })
