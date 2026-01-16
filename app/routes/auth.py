from flask import Blueprint, render_template, redirect, url_for, flash, request, session, send_file, make_response
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt, limiter
from app.models import User
import pyotp
import qrcode
import io
import base64
import secrets
import json
from datetime import datetime

bp = Blueprint('auth', __name__, url_prefix='/auth')


def generate_backup_codes(count=10):
    """Generate backup codes for 2FA"""
    codes = []
    for _ in range(count):
        # Generate 8-character alphanumeric code
        code = ''.join(secrets.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789') for _ in range(8))
        # Format as XXXX-XXXX for readability
        formatted_code = f"{code[:4]}-{code[4:]}"
        codes.append(formatted_code)
    return codes


def hash_backup_codes(codes):
    """Hash backup codes for secure storage"""
    return [bcrypt.generate_password_hash(code).decode('utf-8') for code in codes]


def verify_backup_code(user, code):
    """Verify a backup code and mark it as used"""
    if not user.backup_codes:
        return False
    
    stored_codes = json.loads(user.backup_codes)
    
    for i, hashed_code in enumerate(stored_codes):
        if bcrypt.check_password_hash(hashed_code, code):
            # Remove used code
            stored_codes.pop(i)
            user.backup_codes = json.dumps(stored_codes)
            db.session.commit()
            return True
    
    return False

@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=["POST"])  # Rate limit login attempts
@limiter.limit("20 per hour", methods=["POST"])   # Additional hourly limit
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        from app.utils import log_security_event
        
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        password = data.get('password')
        two_factor_code = data.get('two_factor_code')
        remember = data.get('remember', False)
        
        # Accept both username and email
        user = User.query.filter((User.username == username) | (User.email == username)).first()
        
        # Check if account is locked
        if user and user.is_locked():
            remaining = user.get_lockout_remaining_minutes()
            error_msg = f'Account locked due to too many failed attempts. Try again in {remaining} minutes.'
            log_security_event('LOGIN_BLOCKED', user.id, f'Account locked - {remaining} mins remaining', False, request)
            if request.is_json:
                return {'success': False, 'message': error_msg, 'locked': True, 'remaining_minutes': remaining}, 429
            flash(error_msg, 'error')
            return render_template('auth/login.html')
        
        if user and bcrypt.check_password_hash(user.password_hash, password):
            # Check 2FA if enabled
            if user.two_factor_enabled:
                if not two_factor_code:
                    if request.is_json:
                        return {'success': False, 'requires_2fa': True}, 200
                    session['pending_user_id'] = user.id
                    return render_template('auth/two_factor.html')
                
                # Try TOTP code first
                totp = pyotp.TOTP(user.totp_secret)
                is_valid = totp.verify(two_factor_code)
                
                # If TOTP fails, try backup code (format: XXXX-XXXX or XXXXXXXX)
                if not is_valid:
                    is_valid = verify_backup_code(user, two_factor_code)
                
                if not is_valid:
                    log_security_event('2FA_FAILED', user.id, 'Invalid 2FA code', False, request)
                    if request.is_json:
                        return {'success': False, 'message': 'Invalid 2FA code'}, 401
                    flash('Invalid 2FA code', 'error')
                    return render_template('auth/login.html')
                
                log_security_event('2FA_USED', user.id, 'Successful 2FA verification', True, request)
            
            # Successful login - reset failed attempts
            user.reset_failed_attempts()
            
            # Security: Regenerate session to prevent session fixation attacks
            # Preserve CSRF token during session regeneration
            csrf_token = session.get('csrf_token')
            session.clear()
            if csrf_token:
                session['csrf_token'] = csrf_token
            
            login_user(user, remember=remember)
            session.permanent = remember
            
            # Generate unique session token for tracking
            session_token = secrets.token_hex(32)
            session['session_token'] = session_token
            
            # Initialize session activity tracking
            from datetime import datetime
            session['last_activity'] = datetime.utcnow().isoformat()
            session['login_time'] = datetime.utcnow().isoformat()
            
            # Create session record in database
            from app.models import UserSession
            try:
                user_session = UserSession.create_session(user.id, request, session_token)
                session['session_id'] = user_session.id
            except Exception as e:
                print(f"Failed to create session record: {e}")
            
            # Get IP for logging and notification
            ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
            if ip_address and ',' in ip_address:
                ip_address = ip_address.split(',')[0].strip()
            
            log_security_event('LOGIN_SUCCESS', user.id, f'Login via {"remember me" if remember else "session"}', True, request)
            
            # Create login notification if security notifications enabled
            if getattr(user, 'security_notifications', True):
                from app.models import UserNotification
                user_agent = request.headers.get('User-Agent', 'Unknown device')[:100]
                UserNotification.create(
                    user_id=user.id,
                    notification_type='security',
                    title='New Login Detected',
                    message=f'New login from IP: {ip_address}. Device: {user_agent}'
                )
            
            # Check if admin without 2FA - redirect to setup
            redirect_url = url_for('main.dashboard')
            if user.is_admin and not user.two_factor_enabled:
                # Admin must set up 2FA
                session['2fa_setup_required'] = True
                redirect_url = url_for('auth.setup_2fa')
                if getattr(user, 'security_notifications', True):
                    from app.models import UserNotification
                    UserNotification.create(
                        user_id=user.id,
                        notification_type='warning',
                        title='2FA Required for Admin Accounts',
                        message='As an admin, you are required to enable Two-Factor Authentication for security purposes.'
                    )
            
            if request.is_json:
                return {'success': True, 'redirect': redirect_url, 'requires_2fa_setup': user.is_admin and not user.two_factor_enabled}
            
            next_page = request.args.get('next')
            return redirect(next_page if next_page else redirect_url)
        
        # Failed login - record attempt if user exists
        if user:
            user.record_failed_login()
            log_security_event('LOGIN_FAILED', user.id, f'Failed attempt #{user.failed_login_attempts}', False, request)
            
            # Notify user of failed attempt if they have security notifications on
            if getattr(user, 'security_notifications', True) and user.failed_login_attempts >= 3:
                ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
                if ip_address and ',' in ip_address:
                    ip_address = ip_address.split(',')[0].strip()
                from app.models import UserNotification
                UserNotification.create(
                    user_id=user.id,
                    notification_type='warning',
                    title='Failed Login Attempts Detected',
                    message=f'{user.failed_login_attempts} failed login attempts from IP: {ip_address}. If this wasn\'t you, consider changing your password.'
                )
            
            # Check if account just got locked
            if user.is_locked():
                remaining = user.get_lockout_remaining_minutes()
                log_security_event('ACCOUNT_LOCKED', user.id, f'Locked for {remaining} minutes after {user.MAX_FAILED_ATTEMPTS} failed attempts', False, request)
                
                # Notify user of account lockout
                if getattr(user, 'security_notifications', True):
                    from app.models import UserNotification
                    UserNotification.create(
                        user_id=user.id,
                        notification_type='security',
                        title='Account Locked',
                        message=f'Your account has been locked for {remaining} minutes due to {user.MAX_FAILED_ATTEMPTS} failed login attempts.'
                    )
                
                error_msg = f'Too many failed attempts. Account locked for {remaining} minutes.'
                if request.is_json:
                    return {'success': False, 'message': error_msg, 'locked': True, 'remaining_minutes': remaining}, 429
                flash(error_msg, 'error')
                return render_template('auth/login.html')
        else:
            # Log failed attempt for non-existent user (don't reveal user doesn't exist)
            log_security_event('LOGIN_FAILED', None, f'Attempt for unknown user: {username}', False, request)
        
        if request.is_json:
            return {'success': False, 'message': 'Invalid username or password'}, 401
        
        flash('Invalid username or password', 'error')
    
    return render_template('auth/login.html')


@bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per hour", methods=["POST"])  # Prevent mass account creation
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        language = data.get('language', 'en')
        currency = data.get('currency', 'USD')
        
        # Validate password strength
        from app.utils import validate_password
        is_valid, error_msg = validate_password(password)
        if not is_valid:
            if request.is_json:
                return {'success': False, 'message': error_msg}, 400
            flash(error_msg, 'error')
            return render_template('auth/register.html')
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            if request.is_json:
                return {'success': False, 'message': 'Email already registered'}, 400
            flash('Email already registered', 'error')
            return render_template('auth/register.html')
        
        if User.query.filter_by(username=username).first():
            if request.is_json:
                return {'success': False, 'message': 'Username already taken'}, 400
            flash('Username already taken', 'error')
            return render_template('auth/register.html')
        
        # Check if this is the first user (make them admin)
        is_first_user = User.query.count() == 0
        
        # Create user
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            is_admin=is_first_user,
            language=language,
            currency=currency
        )
        
        db.session.add(user)
        db.session.commit()
        
        # Create default categories
        from app.utils import create_default_categories
        create_default_categories(user.id)
        
        # Log registration
        from app.utils import log_security_event
        log_security_event('REGISTER', user.id, f'New user registered (admin={is_first_user})', True, request)
        
        # Security: Regenerate session to prevent session fixation
        csrf_token = session.get('csrf_token')
        session.clear()
        if csrf_token:
            session['csrf_token'] = csrf_token
        
        login_user(user)
        
        # Initialize session tracking
        session['last_activity'] = datetime.utcnow().isoformat()
        session['login_time'] = datetime.utcnow().isoformat()
        
        log_security_event('LOGIN_SUCCESS', user.id, 'Auto-login after registration', True, request)
        
        if request.is_json:
            return {'success': True, 'redirect': url_for('main.dashboard')}
        
        flash('Registration successful!', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('auth/register.html')


@bp.route('/logout')
@login_required
def logout():
    from app.utils import log_security_event
    from app.models import UserSession
    
    user_id = current_user.id
    session_token = session.get('session_token')
    
    # Mark session as revoked in database
    if session_token:
        try:
            user_session = UserSession.query.filter_by(session_token=session_token).first()
            if user_session:
                user_session.revoke()
        except Exception as e:
            print(f"Failed to revoke session: {e}")
    
    log_security_event('LOGOUT', user_id, 'User logged out', True, request)
    logout_user()
    
    # Security: Completely clear session on logout to prevent session reuse
    session.clear()
    
    return redirect(url_for('auth.login'))


@bp.route('/setup-2fa', methods=['GET', 'POST'])
@login_required
def setup_2fa():
    if request.method == 'POST':
        data = request.get_json() if request.is_json else request.form
        code = data.get('code')
        
        if not current_user.totp_secret:
            secret = pyotp.random_base32()
            current_user.totp_secret = secret
        
        totp = pyotp.TOTP(current_user.totp_secret)
        
        if totp.verify(code):
            # Generate backup codes
            backup_codes_plain = generate_backup_codes(10)
            backup_codes_hashed = hash_backup_codes(backup_codes_plain)
            
            current_user.two_factor_enabled = True
            current_user.backup_codes = json.dumps(backup_codes_hashed)
            db.session.commit()
            
            # Log 2FA enabled
            from app.utils import log_security_event
            log_security_event('2FA_ENABLED', current_user.id, '2FA enabled with backup codes generated', True, request)
            
            # Security: Regenerate session after 2FA setup (security level increased)
            csrf_token = session.get('csrf_token')
            session.clear()
            if csrf_token:
                session['csrf_token'] = csrf_token
            
            # Re-establish session tracking
            session['last_activity'] = datetime.utcnow().isoformat()
            session['login_time'] = datetime.utcnow().isoformat()
            
            # Store plain backup codes in session for display
            session['backup_codes'] = backup_codes_plain
            
            if request.is_json:
                return {'success': True, 'message': '2FA enabled successfully', 'backup_codes': backup_codes_plain}
            
            flash('2FA enabled successfully', 'success')
            return redirect(url_for('auth.show_backup_codes'))
        
        if request.is_json:
            return {'success': False, 'message': 'Invalid code'}, 400
        
        flash('Invalid code', 'error')
    
    # Generate QR code
    if not current_user.totp_secret:
        current_user.totp_secret = pyotp.random_base32()
        db.session.commit()
    
    totp = pyotp.TOTP(current_user.totp_secret)
    provisioning_uri = totp.provisioning_uri(
        name=current_user.email,
        issuer_name='FINA'
    )
    
    # Generate QR code image
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    qr_code_base64 = base64.b64encode(buf.getvalue()).decode()
    
    return render_template('auth/setup_2fa.html', 
                         qr_code=qr_code_base64,
                         secret=current_user.totp_secret)


@bp.route('/backup-codes', methods=['GET'])
@login_required
def show_backup_codes():
    """Display backup codes after 2FA setup"""
    backup_codes = session.get('backup_codes', [])
    
    if not backup_codes:
        flash('No backup codes available', 'error')
        return redirect(url_for('main.settings'))
    
    return render_template('auth/backup_codes.html', 
                         backup_codes=backup_codes,
                         username=current_user.username)


@bp.route('/backup-codes/download', methods=['GET'])
@login_required
def download_backup_codes_pdf():
    """Download backup codes as PDF"""
    backup_codes = session.get('backup_codes', [])
    
    if not backup_codes:
        flash('No backup codes available', 'error')
        return redirect(url_for('main.settings'))
    
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        from reportlab.pdfgen import canvas
        from reportlab.lib import colors
        
        # Create PDF in memory
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Title
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(width/2, height - 1*inch, "FINA")
        
        c.setFont("Helvetica-Bold", 18)
        c.drawCentredString(width/2, height - 1.5*inch, "Two-Factor Authentication")
        c.drawCentredString(width/2, height - 1.9*inch, "Backup Codes")
        
        # User info
        c.setFont("Helvetica", 12)
        c.drawString(1*inch, height - 2.5*inch, f"User: {current_user.username}")
        c.drawString(1*inch, height - 2.8*inch, f"Email: {current_user.email}")
        c.drawString(1*inch, height - 3.1*inch, f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        
        # Warning message
        c.setFillColorRGB(0.8, 0.2, 0.2)
        c.setFont("Helvetica-Bold", 11)
        c.drawString(1*inch, height - 3.7*inch, "IMPORTANT: Store these codes in a secure location!")
        c.setFillColorRGB(0, 0, 0)
        c.setFont("Helvetica", 10)
        c.drawString(1*inch, height - 4.0*inch, "Each code can only be used once. Use them if you lose access to your authenticator app.")
        
        # Backup codes in two columns
        c.setFont("Courier-Bold", 14)
        y_position = height - 4.8*inch
        x_left = 1.5*inch
        x_right = 4.5*inch
        
        for i, code in enumerate(backup_codes):
            if i % 2 == 0:
                c.drawString(x_left, y_position, f"{i+1:2d}. {code}")
            else:
                c.drawString(x_right, y_position, f"{i+1:2d}. {code}")
                y_position -= 0.4*inch
        
        # Footer
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawCentredString(width/2, 0.5*inch, "Keep this document secure and do not share these codes with anyone.")
        
        c.save()
        buffer.seek(0)
        
        # Clear backup codes from session after download
        session.pop('backup_codes', None)
        
        # Create response with PDF
        response = make_response(buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=FINA_BackupCodes_{current_user.username}_{datetime.utcnow().strftime("%Y%m%d")}.pdf'
        
        return response
        
    except ImportError:
        # If reportlab is not installed, return codes as text file
        text_content = f"FINA - Two-Factor Authentication Backup Codes\n\n"
        text_content += f"User: {current_user.username}\n"
        text_content += f"Email: {current_user.email}\n"
        text_content += f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        text_content += "IMPORTANT: Store these codes in a secure location!\n"
        text_content += "Each code can only be used once.\n\n"
        text_content += "Backup Codes:\n"
        text_content += "-" * 40 + "\n"
        
        for i, code in enumerate(backup_codes, 1):
            text_content += f"{i:2d}. {code}\n"
        
        text_content += "-" * 40 + "\n"
        text_content += "\nKeep this document secure and do not share these codes with anyone."
        
        # Clear backup codes from session
        session.pop('backup_codes', None)
        
        response = make_response(text_content)
        response.headers['Content-Type'] = 'text/plain'
        response.headers['Content-Disposition'] = f'attachment; filename=FINA_BackupCodes_{current_user.username}_{datetime.utcnow().strftime("%Y%m%d")}.txt'
        
        return response


@bp.route('/disable-2fa', methods=['POST'])
@login_required
def disable_2fa():
    from app.utils import log_security_event
    
    current_user.two_factor_enabled = False
    current_user.backup_codes = None
    db.session.commit()
    
    log_security_event('2FA_DISABLED', current_user.id, '2FA has been disabled', True, request)
    
    if request.is_json:
        return {'success': True, 'message': '2FA disabled'}
    
    flash('2FA disabled', 'success')
    return redirect(url_for('main.settings'))
