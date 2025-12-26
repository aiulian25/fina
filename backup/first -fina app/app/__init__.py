from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import redis
import os

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
redis_client = None

def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///finance.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    @app.after_request
    def set_csp(response):
        response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; img-src 'self' data: https://cdn.jsdelivr.net"
        return response
    
    db.init_app(app)
    csrf.init_app(app)
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    global redis_client
    redis_host = os.environ.get('REDIS_HOST', 'redis')
    redis_port = int(os.environ.get('REDIS_PORT', 6369))
    redis_client = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
    
    from app.models.user import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register currency filter for templates
    from app.utils import format_currency
    from app.translations import get_translation
    
    @app.template_filter('currency')
    def currency_filter(amount, currency_code=None):
        from flask_login import current_user
        if currency_code is None and current_user.is_authenticated:
            currency_code = current_user.currency
        return format_currency(amount, currency_code or 'USD')
    
    # Register translation function for templates
    @app.template_global('_')
    def translate(key):
        from flask_login import current_user
        lang = 'en'
        if current_user.is_authenticated and hasattr(current_user, 'language'):
            lang = current_user.language or 'en'
        return get_translation(key, lang)
    
    # Make get_translation available in templates
    @app.context_processor
    def utility_processor():
        from flask_login import current_user
        def get_lang():
            if current_user.is_authenticated and hasattr(current_user, 'language'):
                return current_user.language or 'en'
            return 'en'
        return dict(get_lang=get_lang)
    
    from app.routes import auth, main, settings, language, subscriptions
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(settings.bp)
    app.register_blueprint(language.bp)
    app.register_blueprint(subscriptions.bp)
    
    # Register PWA routes
    from app.pwa import register_pwa_routes
    register_pwa_routes(app)
    
    # Initialize budget alert system
    from app.budget_alerts import init_mail
    init_mail(app)
    
    with app.app_context():
        db.create_all()
    
    return app
