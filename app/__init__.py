from flask import Flask, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis
import os
from datetime import timedelta

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])
redis_client = None

def create_app():
    app = Flask(__name__)
    
    # Secure SECRET_KEY configuration
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        if os.environ.get('FLASK_ENV') == 'production':
            raise ValueError("CRITICAL: SECRET_KEY environment variable must be set in production!")
        # Use a development-only key (will be different each restart if not set)
        import secrets as sec
        secret_key = sec.token_hex(32)
        print("WARNING: Using randomly generated SECRET_KEY. Set SECRET_KEY environment variable for persistent sessions.")
    
    # Configuration
    app.config['SECRET_KEY'] = secret_key
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///data/fina.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['UPLOAD_FOLDER'] = os.path.abspath('uploads')
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    app.config['WTF_CSRF_TIME_LIMIT'] = None
    
    # Secure session cookie configuration
    # SESSION_COOKIE_SECURE should only be True when using HTTPS
    # Set HTTPS_ENABLED=true when you have HTTPS configured (via reverse proxy, etc.)
    https_enabled = os.environ.get('HTTPS_ENABLED', 'false').lower() == 'true'
    app.config['SESSION_COOKIE_SECURE'] = https_enabled
    app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
    
    # Rate limiting storage (use Redis if available, fallback to memory)
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    app.config['RATELIMIT_STORAGE_URI'] = redis_url
    app.config['RATELIMIT_STRATEGY'] = 'fixed-window'
    app.config['RATELIMIT_HEADERS_ENABLED'] = True
    
    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Redis connection
    global redis_client
    try:
        redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        redis_client = redis.from_url(redis_url, decode_responses=True)
    except Exception as e:
        print(f"Redis connection failed: {e}")
        redis_client = None
    
    # Create upload directories
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'documents'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'avatars'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'receipts'), exist_ok=True)
    os.makedirs('data', exist_ok=True)
    
    # Register blueprints
    from app.routes import auth, main, expenses, admin, documents, settings, recurring, search, budget, csv_import, income, tags, goals, subscriptions, analyzer, insights, challenges, forecast, backup
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(expenses.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(documents.bp)
    app.register_blueprint(settings.bp)
    app.register_blueprint(recurring.bp)
    app.register_blueprint(search.bp)
    app.register_blueprint(budget.bp)
    app.register_blueprint(csv_import.bp)
    app.register_blueprint(income.bp)
    app.register_blueprint(tags.bp)
    app.register_blueprint(goals.bp)
    app.register_blueprint(subscriptions.bp)
    app.register_blueprint(analyzer.bp)
    app.register_blueprint(insights.bp)
    app.register_blueprint(challenges.bp)
    app.register_blueprint(forecast.bp)
    app.register_blueprint(backup.bp)
    
    # Security headers middleware
    @app.after_request
    def add_security_headers(response):
        # Prevent clickjacking
        response.headers['X-Frame-Options'] = 'DENY'
        
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Enable XSS filter
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Referrer policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions policy (disable unnecessary features)
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Content Security Policy
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob:; "
            "connect-src 'self';"
        )
        
        # Strict Transport Security (only in production with HTTPS)
        if os.environ.get('FLASK_ENV') == 'production':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        return response
    
    # Session inactivity timeout (30 minutes)
    SESSION_TIMEOUT_MINUTES = int(os.environ.get('SESSION_TIMEOUT_MINUTES', 30))
    
    @app.before_request
    def check_session_timeout():
        """Check for session inactivity and logout if exceeded"""
        from flask_login import current_user, logout_user
        from datetime import datetime, timedelta
        
        # Skip for static files, login/logout routes, and unauthenticated users
        if (request.endpoint and 'static' in request.endpoint or
            request.path.startswith('/auth/login') or
            request.path.startswith('/auth/register') or
            request.path.startswith('/auth/logout') or
            not current_user.is_authenticated):
            return
        
        now = datetime.utcnow()
        last_activity = session.get('last_activity')
        
        if last_activity:
            last_activity_time = datetime.fromisoformat(last_activity)
            inactive_time = now - last_activity_time
            
            if inactive_time > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
                # Session expired due to inactivity
                from app.utils import log_security_event
                log_security_event('SESSION_TIMEOUT', current_user.id, 
                    f'Session expired after {SESSION_TIMEOUT_MINUTES} minutes of inactivity', True, request)
                
                logout_user()
                session.clear()
                
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({
                        'error': 'Session expired due to inactivity',
                        'session_expired': True,
                        'redirect': '/auth/login'
                    }), 401
                
                flash('Your session has expired due to inactivity. Please log in again.', 'warning')
                return redirect(url_for('auth.login'))
        
        # Update last activity timestamp
        session['last_activity'] = now.isoformat()
        
        # Update session record in database (throttled to reduce DB writes)
        session_token = session.get('session_token')
        last_db_update = session.get('last_db_activity_update')
        
        # Only update DB every 60 seconds to reduce load
        should_update_db = True
        if last_db_update:
            last_update_time = datetime.fromisoformat(last_db_update)
            if (now - last_update_time).seconds < 60:
                should_update_db = False
        
        if session_token and should_update_db:
            try:
                from app.models import UserSession
                user_session = UserSession.query.filter_by(
                    session_token=session_token, 
                    is_active=True
                ).first()
                if user_session:
                    user_session.last_activity = now
                    db.session.commit()
                    session['last_db_activity_update'] = now.isoformat()
            except Exception:
                pass  # Don't break request on session tracking failure
    
    # Secure error handlers - don't leak sensitive info
    from flask import jsonify, request
    
    @app.errorhandler(400)
    def bad_request(error):
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({'error': 'Bad request'}), 400
        return 'Bad Request', 400
    
    @app.errorhandler(403)
    def forbidden(error):
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({'error': 'Forbidden'}), 403
        return 'Forbidden', 403
    
    @app.errorhandler(404)
    def not_found(error):
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({'error': 'Resource not found'}), 404
        return 'Not Found', 404
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({'error': 'Rate limit exceeded. Please slow down.'}), 429
        return 'Rate limit exceeded. Please slow down.', 429
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        # Log the actual error for debugging (server-side only)
        app.logger.error(f'Internal server error: {str(error)}')
        # Return generic message to client
        if request.is_json or request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        return 'Internal Server Error', 500
    
    # Serve uploaded files
    from flask import send_from_directory, url_for
    
    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        """Serve uploaded files (avatars, documents)"""
        upload_dir = os.path.join(app.root_path, '..', app.config['UPLOAD_FOLDER'])
        return send_from_directory(upload_dir, filename)
    
    # Add avatar_url filter for templates
    @app.template_filter('avatar_url')
    def avatar_url_filter(avatar_path):
        """Generate correct URL for avatar (either static or uploaded)"""
        if avatar_path.startswith('icons/'):
            # Default avatar in static folder
            return url_for('static', filename=avatar_path)
        else:
            # Uploaded avatar
            return '/' + avatar_path
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Run migrations for existing databases
        run_migrations()
    
    # Initialize scheduler for recurring expenses
    from app.scheduler import init_scheduler
    init_scheduler(app)
    
    return app


def run_migrations():
    """Run database migrations for adding new columns to existing tables"""
    import sqlite3
    from sqlalchemy import inspect
    
    # Get the database path from the engine
    engine = db.engine
    
    # Only run for SQLite
    if 'sqlite' not in str(engine.url):
        return
    
    inspector = inspect(engine)
    
    # Check if users table exists
    if 'users' not in inspector.get_table_names():
        return
    
    # Get existing columns
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    # Add missing columns to users table
    with engine.connect() as conn:
        if 'theme' not in columns:
            print("Migration: Adding 'theme' column to users table...")
            conn.execute(db.text("ALTER TABLE users ADD COLUMN theme VARCHAR(10) DEFAULT 'dark'"))
            conn.commit()
            print("Migration: 'theme' column added successfully")
        
        if 'notifications_enabled' not in columns:
            print("Migration: Adding 'notifications_enabled' column to users table...")
            conn.execute(db.text("ALTER TABLE users ADD COLUMN notifications_enabled BOOLEAN DEFAULT 1"))
            conn.commit()
            print("Migration: 'notifications_enabled' column added successfully")
    
    # Add subscription fields to recurring_expenses table
    if 'recurring_expenses' in inspector.get_table_names():
        recurring_columns = [col['name'] for col in inspector.get_columns('recurring_expenses')]
        
        with engine.connect() as conn:
            if 'is_subscription' not in recurring_columns:
                print("Migration: Adding subscription fields to recurring_expenses table...")
                conn.execute(db.text("ALTER TABLE recurring_expenses ADD COLUMN is_subscription BOOLEAN DEFAULT 0"))
                conn.commit()
            if 'service_name' not in recurring_columns:
                conn.execute(db.text("ALTER TABLE recurring_expenses ADD COLUMN service_name VARCHAR(100)"))
                conn.commit()
            if 'last_used_date' not in recurring_columns:
                conn.execute(db.text("ALTER TABLE recurring_expenses ADD COLUMN last_used_date DATETIME"))
                conn.commit()
            if 'reminder_days' not in recurring_columns:
                conn.execute(db.text("ALTER TABLE recurring_expenses ADD COLUMN reminder_days INTEGER DEFAULT 3"))
                conn.commit()
            if 'reminder_sent' not in recurring_columns:
                conn.execute(db.text("ALTER TABLE recurring_expenses ADD COLUMN reminder_sent BOOLEAN DEFAULT 0"))
                conn.commit()
                print("Migration: Subscription fields added successfully")
    
    # Add account lockout fields to users table
    columns = [col['name'] for col in inspector.get_columns('users')]
    with engine.connect() as conn:
        if 'failed_login_attempts' not in columns:
            print("Migration: Adding 'failed_login_attempts' column to users table...")
            conn.execute(db.text("ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0"))
            conn.commit()
        if 'locked_until' not in columns:
            print("Migration: Adding 'locked_until' column to users table...")
            conn.execute(db.text("ALTER TABLE users ADD COLUMN locked_until DATETIME"))
            conn.commit()
        if 'last_failed_login' not in columns:
            print("Migration: Adding 'last_failed_login' column to users table...")
            conn.execute(db.text("ALTER TABLE users ADD COLUMN last_failed_login DATETIME"))
            conn.commit()
            print("Migration: Account lockout fields added successfully")
        if 'security_notifications' not in columns:
            print("Migration: Adding 'security_notifications' column to users table...")
            conn.execute(db.text("ALTER TABLE users ADD COLUMN security_notifications BOOLEAN DEFAULT 1"))
            conn.commit()
            print("Migration: Security notifications preference added successfully")


from app.models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
