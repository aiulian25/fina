from flask import Blueprint, request, jsonify
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
