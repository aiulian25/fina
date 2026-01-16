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
            'theme': getattr(current_user, 'theme', 'dark'),
            'notifications_enabled': getattr(current_user, 'notifications_enabled', True),
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
        
        # Update theme
        if 'theme' in data:
            if data['theme'] in ['light', 'dark']:
                current_user.theme = data['theme']
            else:
                return jsonify({'success': False, 'error': 'Invalid theme'}), 400
        
        # Update notifications preference
        if 'notifications_enabled' in data:
            current_user.notifications_enabled = bool(data['notifications_enabled'])
        
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
                'theme': getattr(current_user, 'theme', 'dark'),
                'notifications_enabled': getattr(current_user, 'notifications_enabled', True),
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
    Security: Requires current password verification and strong password validation
    """
    from app.utils import log_security_event
    data = request.get_json()
    
    if not data:
        return jsonify({'success': False, 'error': 'No data provided'}), 400
    
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    
    if not current_password or not new_password:
        return jsonify({'success': False, 'error': 'Current and new password required'}), 400
    
    # Verify current password
    if not bcrypt.check_password_hash(current_user.password_hash, current_password):
        log_security_event('PASSWORD_CHANGE_FAILED', current_user.id, 'Invalid current password', False, request)
        return jsonify({'success': False, 'error': 'Current password is incorrect'}), 400
    
    # Validate new password strength
    from app.utils import validate_password
    is_valid, error_msg = validate_password(new_password)
    if not is_valid:
        return jsonify({'success': False, 'error': error_msg}), 400
    
    try:
        current_user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
        db.session.commit()
        
        log_security_event('PASSWORD_CHANGED', current_user.id, 'Password changed successfully', True, request)
        
        # Security: Regenerate session after password change
        csrf_token = session.get('csrf_token')
        session.clear()
        if csrf_token:
            session['csrf_token'] = csrf_token
        
        # Re-establish session
        from datetime import datetime
        session['last_activity'] = datetime.utcnow().isoformat()
        session['login_time'] = datetime.utcnow().isoformat()
        
        # Create notification for password change
        from app.models import UserNotification
        UserNotification.create(
            user_id=current_user.id,
            notification_type='security',
            title='Password Changed',
            message='Your password was changed successfully. If you did not make this change, please contact support immediately.'
        )
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/notifications', methods=['GET'])
@login_required
def get_notifications():
    """Get user's notifications with pagination"""
    from app.models import UserNotification
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    
    query = UserNotification.query.filter_by(user_id=current_user.id)
    
    if unread_only:
        query = query.filter_by(is_read=False)
    
    pagination = query.order_by(UserNotification.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    unread_count = UserNotification.query.filter_by(
        user_id=current_user.id, is_read=False
    ).count()
    
    return jsonify({
        'notifications': [n.to_dict() for n in pagination.items],
        'unread_count': unread_count,
        'pagination': {
            'page': page,
            'pages': pagination.pages,
            'total': pagination.total
        }
    })


@bp.route('/notifications/<int:notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    """Mark a notification as read"""
    from app.models import UserNotification
    
    notif = UserNotification.query.filter_by(
        id=notification_id, user_id=current_user.id
    ).first()
    
    if not notif:
        return jsonify({'success': False, 'error': 'Notification not found'}), 404
    
    notif.mark_read()
    
    return jsonify({'success': True})


@bp.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Mark all notifications as read"""
    from app.models import UserNotification
    
    UserNotification.query.filter_by(
        user_id=current_user.id, is_read=False
    ).update({'is_read': True, 'read_at': datetime.utcnow()})
    
    db.session.commit()
    
    return jsonify({'success': True})


@bp.route('/security-preferences', methods=['GET'])
@login_required
def get_security_preferences():
    """Get user's security notification preferences"""
    return jsonify({
        'security_notifications': getattr(current_user, 'security_notifications', True),
        'two_factor_enabled': current_user.two_factor_enabled
    })


@bp.route('/security-preferences', methods=['PUT'])
@login_required
def update_security_preferences():
    """Update user's security notification preferences"""
    data = request.get_json()
    
    if 'security_notifications' in data:
        current_user.security_notifications = bool(data['security_notifications'])
        db.session.commit()
    
    return jsonify({'success': True})


@bp.route('/session-info', methods=['GET'])
@login_required
def get_session_info():
    """Get current session information including timeout status"""
    from flask import session, current_app
    from datetime import datetime, timedelta
    import os
    
    timeout_minutes = int(os.environ.get('SESSION_TIMEOUT_MINUTES', 30))
    last_activity = session.get('last_activity')
    login_time = session.get('login_time')
    
    now = datetime.utcnow()
    
    session_info = {
        'timeout_minutes': timeout_minutes,
        'login_time': login_time,
        'last_activity': last_activity,
    }
    
    if last_activity:
        last_activity_time = datetime.fromisoformat(last_activity)
        inactive_seconds = (now - last_activity_time).total_seconds()
        remaining_seconds = max(0, (timeout_minutes * 60) - inactive_seconds)
        
        session_info['inactive_seconds'] = int(inactive_seconds)
        session_info['remaining_seconds'] = int(remaining_seconds)
        session_info['remaining_minutes'] = int(remaining_seconds / 60)
    
    return jsonify(session_info)


@bp.route('/extend-session', methods=['POST'])
@login_required
def extend_session():
    """Manually extend the session (reset inactivity timer)"""
    from flask import session
    from datetime import datetime
    
    session['last_activity'] = datetime.utcnow().isoformat()
    
    return jsonify({'success': True, 'message': 'Session extended'})


@bp.route('/sessions', methods=['GET'])
@login_required
def get_active_sessions():
    """
    Get list of active sessions for the current user
    Security: Only returns sessions belonging to current user
    """
    from flask import session
    from app.models import UserSession
    
    current_session_token = session.get('session_token')
    
    # Get all active sessions for user
    sessions = UserSession.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).order_by(UserSession.last_activity.desc()).all()
    
    sessions_list = []
    for sess in sessions:
        is_current = (sess.session_token == current_session_token)
        session_dict = sess.to_dict(is_current=is_current)
        sessions_list.append(session_dict)
    
    return jsonify({
        'success': True,
        'sessions': sessions_list,
        'count': len(sessions_list)
    })


@bp.route('/sessions/<int:session_id>', methods=['DELETE'])
@login_required
def revoke_session(session_id):
    """
    Revoke/terminate a specific session
    Security: Only allows revoking user's own sessions
    """
    from flask import session
    from app.models import UserSession
    from app.utils import log_security_event
    
    current_session_token = session.get('session_token')
    
    # Security: Ensure session belongs to current user
    user_session = UserSession.query.filter_by(
        id=session_id,
        user_id=current_user.id,
        is_active=True
    ).first()
    
    if not user_session:
        return jsonify({'success': False, 'message': 'Session not found'}), 404
    
    # Check if trying to revoke current session
    if user_session.session_token == current_session_token:
        return jsonify({'success': False, 'message': 'Cannot revoke current session. Use logout instead.'}), 400
    
    user_session.revoke()
    
    log_security_event('SESSION_REVOKED', current_user.id, 
        f'Session revoked: {user_session.browser} on {user_session.os} from {user_session.ip_address}', 
        True, request)
    
    # Notify user
    from app.models import UserNotification
    if getattr(current_user, 'security_notifications', True):
        UserNotification.create(
            user_id=current_user.id,
            notification_type='security',
            title='Session Terminated',
            message=f'A session was terminated: {user_session.browser} on {user_session.os} from IP {user_session.ip_address}'
        )
    
    return jsonify({
        'success': True,
        'message': 'Session revoked successfully'
    })


@bp.route('/sessions/revoke-all', methods=['POST'])
@login_required
def revoke_all_sessions():
    """
    Revoke all sessions except the current one
    Security: Only affects current user's sessions
    """
    from flask import session
    from app.models import UserSession
    from app.utils import log_security_event
    
    current_session_token = session.get('session_token')
    
    if not current_session_token:
        return jsonify({'success': False, 'message': 'Current session not found'}), 400
    
    count = UserSession.revoke_all_except(current_user.id, current_session_token)
    
    log_security_event('ALL_SESSIONS_REVOKED', current_user.id, 
        f'Revoked {count} other sessions', True, request)
    
    # Notify user
    from app.models import UserNotification
    if getattr(current_user, 'security_notifications', True) and count > 0:
        UserNotification.create(
            user_id=current_user.id,
            notification_type='security',
            title='All Other Sessions Terminated',
            message=f'{count} active session(s) were terminated from all other devices.'
        )
    
    return jsonify({
        'success': True,
        'message': f'Revoked {count} session(s)',
        'revoked_count': count
    })
