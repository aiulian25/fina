from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models.user import User

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        totp_token = request.form.get('totp_token')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Check if 2FA is enabled
            if user.is_2fa_enabled:
                if not totp_token:
                    # Store user ID in session for 2FA verification
                    session['2fa_user_id'] = user.id
                    return render_template('auth/verify_2fa.html')
                else:
                    # Verify 2FA token
                    if user.verify_totp(totp_token):
                        login_user(user)
                        session.pop('2fa_user_id', None)
                        flash('Login successful!', 'success')
                        return redirect(url_for('main.dashboard'))
                    else:
                        flash('Invalid 2FA code', 'error')
                        return render_template('auth/verify_2fa.html')
            else:
                # No 2FA, login directly
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('main.dashboard'))
        
        flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html')

@bp.route('/verify-2fa', methods=['POST'])
def verify_2fa():
    user_id = session.get('2fa_user_id')
    if not user_id:
        flash('Session expired. Please login again.', 'error')
        return redirect(url_for('auth.login'))
    
    user = User.query.get(user_id)
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('auth.login'))
    
    token = request.form.get('token')
    
    if user.verify_totp(token):
        login_user(user)
        session.pop('2fa_user_id', None)
        flash('Login successful!', 'success')
        return redirect(url_for('main.dashboard'))
    else:
        flash('Invalid 2FA code. Please try again.', 'error')
        return render_template('auth/verify_2fa.html')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('auth.register'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('auth.register'))
        
        is_first_user = User.query.count() == 0
        
        user = User(
            username=username, 
            email=email,
            is_admin=is_first_user
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('auth.login'))
