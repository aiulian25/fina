from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db, bcrypt
from app.models import User
import os
from datetime import datetime

bp = Blueprint('settings', __name__, url_prefix='/api/settings')

# Allowed avatar image types
ALLOWED_AVATAR_TYPES = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_AVATAR_SIZE = 20 * 1024 * 1024  # 20MB

def allowed_avatar(filename):
    """Check if file extension is allowed for avatars"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_AVATAR_TYPES


@bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """
    Get current user profile information
    Security: Returns only current user's data
    """
    return jsonify({
        'success': True,
        'profile': {
            'username': current_user.username,
            'email': current_user.email,
            'language': current_user.language,
            'currency': current_user.currency,
            'monthly_budget': current_user.monthly_budget or 0,
            'avatar': current_user.avatar,
            'is_admin': current_user.is_admin,
            'two_factor_enabled': current_user.two_factor_enabled,
            'created_at': current_user.created_at.isoformat()
        }
    })


@bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """
    Update user profile information
    Security: Updates only current user's profile
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    try:
        # Update language
        if 'language' in data:
            if data['language'] in ['en', 'ro']:
                current_user.language = data['language']
            else:
                return jsonify({'success': False, 'error': 'Invalid language'}), 400
        
        # Update currency
        if 'currency' in data:
            current_user.currency = data['currency']
        
        # Update monthly budget
        if 'monthly_budget' in data:
            try:
                budget = float(data['monthly_budget'])
                if budget < 0:
                    return jsonify({'success': False, 'error': 'Budget must be positive'}), 400
                current_user.monthly_budget = budget
            except (ValueError, TypeError):
                return jsonify({'success': False, 'error': 'Invalid budget value'}), 400
        
        # Update username (check uniqueness)
        if 'username' in data and data['username'] != current_user.username:
            existing = User.query.filter_by(username=data['username']).first()
            if existing:
                return jsonify({'success': False, 'error': 'Username already taken'}), 400
            current_user.username = data['username']
        
        # Update email (check uniqueness)
        if 'email' in data and data['email'] != current_user.email:
            existing = User.query.filter_by(email=data['email']).first()
            if existing:
                return jsonify({'success': False, 'error': 'Email already taken'}), 400
            current_user.email = data['email']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'profile': {
                'username': current_user.username,
                'email': current_user.email,
                'language': current_user.language,
                'currency': current_user.currency,
                'monthly_budget': current_user.monthly_budget,
                'avatar': current_user.avatar
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/avatar', methods=['POST'])
@login_required
def upload_avatar():
    """
    Upload custom avatar image
    Security: Associates avatar with current_user.id, validates file type and size
    """
    if 'avatar' not in request.files:
        return jsonify({'success': False, 'error': 'No file provided'}), 400
    
    file = request.files['avatar']
    
    if not file or not file.filename:
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if not allowed_avatar(file.filename):
        return jsonify({
            'success': False,
            'error': 'Invalid file type. Allowed: PNG, JPG, JPEG, GIF, WEBP'
        }), 400
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_AVATAR_SIZE:
        return jsonify({
            'success': False,
            'error': f'File too large. Maximum size: {MAX_AVATAR_SIZE // (1024*1024)}MB'
        }), 400
    
    try:
        # Delete old custom avatar if exists (not default avatars)
        if current_user.avatar and not current_user.avatar.startswith('icons/avatars/'):
            old_path = os.path.join(current_app.root_path, 'static', current_user.avatar)
            if os.path.exists(old_path):
                os.remove(old_path)
        
        # Generate secure filename
        file_ext = file.filename.rsplit('.', 1)[1].lower()
        timestamp = int(datetime.utcnow().timestamp())
        filename = f"user_{current_user.id}_{timestamp}.{file_ext}"
        
        # Create avatars directory in uploads
        avatars_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars')
        os.makedirs(avatars_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(avatars_dir, filename)
        file.save(file_path)
        
        # Update user avatar (store relative path from static folder)
        current_user.avatar = f"uploads/avatars/{filename}"
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Avatar uploaded successfully',
            'avatar': current_user.avatar
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/avatar/default', methods=['PUT'])
@login_required
def set_default_avatar():
    """
    Set avatar to one of the default avatars
    Security: Updates only current user's avatar
    """
    data = request.get_json()
    
    if not data or 'avatar' not in data:
        return jsonify({'success': False, 'error': 'Avatar path required'}), 400
    
    avatar_path = data['avatar']
    
    # Validate it's a default avatar
    if not avatar_path.startswith('icons/avatars/avatar-'):
        return jsonify({'success': False, 'error': 'Invalid avatar selection'}), 400
    
    try:
        # Delete old custom avatar if exists (not default avatars)
        if current_user.avatar and not current_user.avatar.startswith('icons/avatars/'):
            old_path = os.path.join(current_app.root_path, 'static', current_user.avatar)
            if os.path.exists(old_path):
                os.remove(old_path)
        
        current_user.avatar = avatar_path
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Avatar updated successfully',
            'avatar': current_user.avatar
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/password', methods=['PUT'])
@login_required
def change_password():
    """
    Change user password
    Security: Requires current password verification
    """
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'success': False, 'error': 'Current and new password required'}), 400
    
    # Verify current password
    if not bcrypt.check_password_hash(current_user.password_hash, current_password):
        return jsonify({'success': False, 'error': 'Current password is incorrect'}), 400
    
    if len(new_password) < 6:
        return jsonify({'success': False, 'error': 'Password must be at least 6 characters'}), 400
    
    try:
        current_user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
