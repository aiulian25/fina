#!/bin/bash

echo "Creating complete Flask app structure..."

# Ensure directories exist
mkdir -p app/models app/routes app/static/{css,js,uploads} app/templates

# Create app/__init__.py with create_app function
cat > app/__init__.py << 'EOF'
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
import os
from dotenv import load_dotenv
import redis

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
redis_client = None

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', os.urandom(32))
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///finance.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    app.config['UPLOAD_FOLDER'] = 'app/static/uploads'
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'pdf', 'gif'}
    
    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' 'unsafe-eval'; img-src 'self' data:;"
        return response
    
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    
    global redis_client
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6369/0')
    redis_client = redis.from_url(redis_url, decode_responses=True)
    
    from app.routes import auth, main
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    
    with app.app_context():
        db.create_all()
    
    return app
EOF

# Create models/__init__.py
cat > app/models/__init__.py << 'EOF'
from app.models.user import User
from app.models.category import Category, Expense
__all__ = ['User', 'Category', 'Expense']
EOF

# Create routes/__init__.py
cat > app/routes/__init__.py << 'EOF'
# Routes package
EOF

echo "✓ Core files created!"
echo ""
echo "Files created:"
find app -name "*.py" -type f
echo ""
echo "Now you need to create:"
echo "  - app/models/user.py"
echo "  - app/models/category.py"
echo "  - app/routes/auth.py"
echo "  - app/routes/main.py"
echo "  - All template files"
echo "  - CSS and JS files"
