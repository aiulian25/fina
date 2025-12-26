from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
import redis
import os
from datetime import timedelta

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
redis_client = None

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///data/fina.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    app.config['UPLOAD_FOLDER'] = os.path.abspath('uploads')
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    app.config['WTF_CSRF_TIME_LIMIT'] = None
    
    # Initialize extensions
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
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
    from app.routes import auth, main, expenses, admin, documents, settings, recurring, search, budget, csv_import, income, tags
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
    
    # Initialize scheduler for recurring expenses
    from app.scheduler import init_scheduler
    init_scheduler(app)
    
    return app

from app.models import User

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
