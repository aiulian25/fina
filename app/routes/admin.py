from flask import Blueprint, request, jsonify, url_for
from flask_login import login_required, current_user
from app import db, bcrypt
from app.models import User, Expense, Category
from functools import wraps

bp = Blueprint('admin', __name__, url_prefix='/api/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            return jsonify({'success': False, 'message': 'Admin access required'}), 403
        # Require 2FA for admin operations
        if not current_user.two_factor_enabled:
            return jsonify({
                'success': False, 
                'message': 'Two-Factor Authentication required for admin operations',
                'requires_2fa_setup': True,
                'redirect': url_for('auth.setup_2fa')
            }), 403
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/users', methods=['GET'])
@login_required
@admin_required
def get_users():
    users = User.query.all()
    return jsonify({
        'users': [{
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin,
            'language': user.language,
            'currency': user.currency,
            'two_factor_enabled': user.two_factor_enabled,
            'created_at': user.created_at.isoformat()
        } for user in users]
    })


@bp.route('/users', methods=['POST'])
@login_required
@admin_required
def create_user():
    data = request.get_json()
    
    if not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    # Validate password strength
    from app.utils import validate_password
    is_valid, error_msg = validate_password(data['password'])
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400
    
    # Check if user exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'success': False, 'message': 'Email already exists'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'success': False, 'message': 'Username already exists'}), 400
    
    # Create user
    password_hash = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    user = User(
        username=data['username'],
        email=data['email'],
        password_hash=password_hash,
        is_admin=data.get('is_admin', False),
        language=data.get('language', 'en'),
        currency=data.get('currency', 'USD')
    )
    
    db.session.add(user)
    db.session.commit()
    
    # Create default categories
    from app.utils import create_default_categories
    create_default_categories(user.id)
    
    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email
        }
    }), 201


@bp.route('/users/<int:user_id>', methods=['GET'])
@login_required
@admin_required
def get_user(user_id):
    """Get a single user's details for editing"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    return jsonify({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin,
            'language': user.language,
            'currency': user.currency,
            'two_factor_enabled': user.two_factor_enabled
        }
    })


@bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
@admin_required
def update_user(user_id):
    """Update an existing user"""
    data = request.get_json()
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    # Validate required fields
    if not data.get('username') or not data.get('email'):
        return jsonify({'success': False, 'message': 'Username and email are required'}), 400
    
    # Check for duplicate username (excluding current user)
    existing_user = User.query.filter(
        User.username == data['username'],
        User.id != user_id
    ).first()
    if existing_user:
        return jsonify({'success': False, 'message': 'Username already exists'}), 400
    
    # Check for duplicate email (excluding current user)
    existing_email = User.query.filter(
        User.email == data['email'],
        User.id != user_id
    ).first()
    if existing_email:
        return jsonify({'success': False, 'message': 'Email already exists'}), 400
    
    # Prevent self-demotion if this would leave no admins
    if user_id == current_user.id and user.is_admin and not data.get('is_admin', True):
        admin_count = User.query.filter_by(is_admin=True).count()
        if admin_count <= 1:
            return jsonify({'success': False, 'message': 'Cannot remove admin role: you are the only admin'}), 400
    
    # Update user fields
    user.username = data['username']
    user.email = data['email']
    user.is_admin = data.get('is_admin', False)
    user.language = data.get('language', user.language)
    user.currency = data.get('currency', user.currency)
    
    # Only update password if provided
    if data.get('password'):
        from app.utils import validate_password
        is_valid, error_msg = validate_password(data['password'])
        if not is_valid:
            return jsonify({'success': False, 'message': error_msg}), 400
        user.password_hash = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'User updated successfully',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin,
            'language': user.language,
            'currency': user.currency
        }
    })


@bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        return jsonify({'success': False, 'message': 'Cannot delete yourself'}), 400
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': 'User not found'}), 404
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'User deleted'})


@bp.route('/stats', methods=['GET'])
@login_required
@admin_required
def get_stats():
    total_users = User.query.count()
    total_expenses = Expense.query.count()
    total_categories = Category.query.count()
    
    return jsonify({
        'total_users': total_users,
        'total_expenses': total_expenses,
        'total_categories': total_categories
    })


@bp.route('/security-logs', methods=['GET'])
@login_required
@admin_required
def get_security_logs():
    """
    Get security audit logs for admin review.
    Supports filtering and pagination.
    """
    from app.models import SecurityLog
    from app.utils import log_security_event
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    event_type = request.args.get('event_type')
    user_id = request.args.get('user_id', type=int)
    success_only = request.args.get('success')
    
    query = SecurityLog.query
    
    if event_type:
        query = query.filter(SecurityLog.event_type == event_type)
    
    if user_id:
        query = query.filter(SecurityLog.user_id == user_id)
    
    if success_only is not None:
        query = query.filter(SecurityLog.success == (success_only.lower() == 'true'))
    
    # Log admin viewing security logs
    log_security_event('ADMIN_VIEW_LOGS', current_user.id, f'Admin viewed security logs (page {page})', True, request)
    
    pagination = query.order_by(SecurityLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    logs = []
    for log in pagination.items:
        log_dict = log.to_dict()
        # Add username if user exists
        if log.user:
            log_dict['username'] = log.user.username
        logs.append(log_dict)
    
    return jsonify({
        'logs': logs,
        'pagination': {
            'page': page,
            'pages': pagination.pages,
            'total': pagination.total,
            'per_page': per_page
        },
        'event_types': [
            'LOGIN_SUCCESS', 'LOGIN_FAILED', 'LOGIN_BLOCKED', 'LOGOUT',
            'REGISTER', 'ACCOUNT_LOCKED',
            'PASSWORD_CHANGED', 'PASSWORD_CHANGE_FAILED',
            '2FA_ENABLED', '2FA_DISABLED', '2FA_USED', '2FA_FAILED',
            'ADMIN_VIEW_LOGS', 'ADMIN_ACTION'
        ]
    })
