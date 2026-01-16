# FINA Security Audit Report

**Date**: January 16, 2026  
**Auditor**: GitHub Copilot  
**App Version**: Current  

---

## Executive Summary

This security audit identified several vulnerabilities in the FINA expense tracking application. The most critical issues relate to missing CSRF protection, lack of rate limiting, and potential session security concerns.

---

## 🔴 CRITICAL - Easy to Exploit

### 1. No CSRF Protection

**Risk Level**: CRITICAL  
**Ease of Exploit**: Very Easy  
**Location**: `app/__init__.py`, all forms and API endpoints

**Description**:  
The application has no Cross-Site Request Forgery (CSRF) protection. An attacker can create a malicious webpage that submits requests to the app while the victim is logged in.

**Proof of Concept**:
```html
<!-- Attacker hosts this page -->
<html>
<body onload="document.forms[0].submit()">
  <form action="http://target-app:5103/api/expenses/" method="POST">
    <input name="amount" value="9999">
    <input name="description" value="Hacked">
    <input name="category_id" value="1">
    <input name="date" value="2026-01-16">
  </form>
</body>
</html>
```

**Impact**:
- Create/delete expenses on behalf of user
- Change user settings
- Delete user data
- Any action the logged-in user can perform

**Fix**:
```python
# app/__init__.py
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    # ... existing config ...
    csrf.init_app(app)
    
    # Exempt API routes if using token auth, otherwise include CSRF token in AJAX
    # csrf.exempt(api_blueprint)
```

```javascript
// For AJAX requests, include CSRF token in headers
// In base.html or app.js
const csrfToken = document.querySelector('meta[name="csrf-token"]').content;
fetch('/api/endpoint', {
    method: 'POST',
    headers: {
        'X-CSRFToken': csrfToken,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
});
```

**Dependencies to Add**:
```
Flask-WTF>=1.2.0
```

---

### 2. No Rate Limiting on Login

**Risk Level**: CRITICAL  
**Ease of Exploit**: Very Easy  
**Location**: `app/routes/auth.py`

**Description**:  
The login endpoint has no rate limiting, allowing unlimited password attempts. An attacker can brute force passwords at thousands of attempts per minute.

**Current Code**:
```python
@bp.route('/login', methods=['GET', 'POST'])
def login():
    # No rate limiting!
```

**Fix**:
```python
# app/__init__.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="redis://redis:6379/1"  # Use Redis for distributed limiting
)

def create_app():
    app = Flask(__name__)
    limiter.init_app(app)
    # ...

# app/routes/auth.py
from app import limiter

@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")  # Only 5 login attempts per minute
@limiter.limit("20 per hour")   # Only 20 per hour
def login():
    # ...

@bp.route('/register', methods=['GET', 'POST'])
@limiter.limit("3 per hour")  # Prevent mass account creation
def register():
    # ...
```

**Dependencies to Add**:
```
Flask-Limiter>=3.5.0
```

---

### 3. Default SECRET_KEY in Production

**Risk Level**: CRITICAL  
**Ease of Exploit**: Easy (if default is used)  
**Location**: `app/__init__.py`

**Description**:  
The SECRET_KEY falls back to a hardcoded default if the environment variable is not set. If deployed without setting this, session cookies can be forged.

**Current Code**:
```python
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
```

**Fix**:
```python
# Option 1: Fail if not set in production
secret_key = os.environ.get('SECRET_KEY')
if not secret_key:
    if os.environ.get('FLASK_ENV') == 'production':
        raise ValueError("SECRET_KEY must be set in production!")
    secret_key = 'dev-secret-key-for-development-only'
app.config['SECRET_KEY'] = secret_key

# Option 2: Generate random key (sessions invalidate on restart)
import secrets
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
```

**Production Setup**:
```bash
# Generate a secure key
python -c "import secrets; print(secrets.token_hex(32))"

# Set in .env or docker-compose.yml
SECRET_KEY=your-64-character-hex-string-here
```

---

## 🟠 HIGH - Moderate Effort

### 4. No Account Lockout After Failed Attempts

**Risk Level**: HIGH  
**Ease of Exploit**: Moderate  
**Location**: `app/routes/auth.py`

**Description**:  
Combined with no rate limiting, accounts are never locked after multiple failed login attempts, making brute force attacks trivial.

**Fix**:
```python
# app/models.py - Add fields to User model
class User(db.Model, UserMixin):
    # ... existing fields ...
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    last_failed_login = db.Column(db.DateTime, nullable=True)

# app/routes/auth.py
from datetime import datetime, timedelta

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION = timedelta(minutes=15)

@bp.route('/login', methods=['POST'])
def login():
    user = User.query.filter_by(username=username).first()
    
    if user:
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            remaining = (user.locked_until - datetime.utcnow()).seconds // 60
            return jsonify({
                'success': False, 
                'message': f'Account locked. Try again in {remaining} minutes.'
            }), 429
        
        if bcrypt.check_password_hash(user.password_hash, password):
            # Reset failed attempts on successful login
            user.failed_login_attempts = 0
            user.locked_until = None
            db.session.commit()
            login_user(user)
            return jsonify({'success': True})
        else:
            # Increment failed attempts
            user.failed_login_attempts += 1
            user.last_failed_login = datetime.utcnow()
            
            if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                user.locked_until = datetime.utcnow() + LOCKOUT_DURATION
            
            db.session.commit()
    
    return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
```

---

### 5. Missing HTTP Security Headers

**Risk Level**: HIGH  
**Ease of Exploit**: Varies  
**Location**: `app/__init__.py`

**Description**:  
The application doesn't set security headers that protect against XSS, clickjacking, and content type sniffing attacks.

**Fix**:
```python
# app/__init__.py
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
    
    # Content Security Policy (adjust as needed)
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: blob:; "
        "connect-src 'self';"
    )
    
    # Strict Transport Security (HTTPS only)
    # Only enable if using HTTPS
    # response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    return response
```

---

### 6. Potential IDOR Vulnerabilities

**Risk Level**: HIGH  
**Ease of Exploit**: Moderate  
**Location**: Various API endpoints

**Description**:  
Insecure Direct Object Reference (IDOR) occurs when an attacker can access another user's data by manipulating IDs in requests.

**Areas to Check**:
```python
# GOOD - Always filter by user_id
expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first()

# BAD - Attacker can access any expense
expense = Expense.query.get(expense_id)
```

**Audit Checklist**:
- [ ] `GET /api/expenses/<id>` - Verify user ownership
- [ ] `PUT /api/expenses/<id>` - Verify user ownership  
- [ ] `DELETE /api/expenses/<id>` - Verify user ownership
- [ ] `GET /api/documents/<id>` - Verify user ownership
- [ ] `GET /api/categories/<id>` - Verify user ownership
- [ ] `GET /api/goals/<id>` - Verify user ownership
- [ ] `GET /api/recurring/<id>` - Verify user ownership
- [ ] File download endpoints - Verify user ownership

**Fix Pattern**:
```python
@bp.route('/<int:id>', methods=['GET'])
@login_required
def get_resource(id):
    # ALWAYS include user_id filter
    resource = Resource.query.filter_by(
        id=id, 
        user_id=current_user.id
    ).first_or_404()
    return jsonify(resource.to_dict())
```

---

## 🟡 MEDIUM

### 7. Session Configuration

**Risk Level**: MEDIUM  
**Location**: `app/__init__.py`

**Description**:  
Session cookies should be configured for maximum security.

**Fix**:
```python
# app/__init__.py
app.config['SESSION_COOKIE_SECURE'] = True  # Only send over HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
```

---

### 8. Password Policy

**Risk Level**: MEDIUM  
**Location**: `app/routes/auth.py`

**Description**:  
No password strength requirements are enforced.

**Fix**:
```python
# app/utils.py
import re

def validate_password(password):
    """
    Validate password strength.
    Returns (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    # Check against common passwords
    common_passwords = ['password', '12345678', 'qwerty123']
    if password.lower() in common_passwords:
        return False, "Password is too common"
    
    return True, None

# app/routes/auth.py
from app.utils import validate_password

@bp.route('/register', methods=['POST'])
def register():
    password = data.get('password')
    
    is_valid, error = validate_password(password)
    if not is_valid:
        return jsonify({'success': False, 'message': error}), 400
    
    # ... continue registration
```

---

### 9. SQL Injection Prevention Audit

**Risk Level**: MEDIUM  
**Location**: Various

**Description**:  
While SQLAlchemy ORM provides protection, raw SQL queries could be vulnerable.

**Areas Found Using Raw SQL** (in `__init__.py` migrations):
```python
conn.execute(db.text("ALTER TABLE users ADD COLUMN theme VARCHAR(10) DEFAULT 'dark'"))
```

**These are safe** because they don't use user input. However, ensure:
- Never use `.format()` or f-strings with user input in SQL
- Always use parameterized queries
- Use ORM methods when possible

**Dangerous Pattern to Avoid**:
```python
# NEVER DO THIS
query = f"SELECT * FROM users WHERE username = '{username}'"
db.engine.execute(query)

# ALWAYS DO THIS
user = User.query.filter_by(username=username).first()
```

---

### 10. File Upload Security

**Risk Level**: MEDIUM  
**Location**: `app/routes/expenses.py`, `app/routes/documents.py`

**Description**:  
File uploads need careful validation to prevent malicious file uploads.

**Current Good Practices**:
- ✅ Using `secure_filename()`
- ✅ File extension checking with `allowed_file()`

**Additional Recommendations**:
```python
# app/routes/expenses.py or documents.py

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file_content(file):
    """Validate file content matches extension"""
    import magic
    
    file.seek(0)
    mime = magic.from_buffer(file.read(2048), mime=True)
    file.seek(0)
    
    allowed_mimes = {
        'image/jpeg', 'image/png', 'image/gif', 'application/pdf'
    }
    
    return mime in allowed_mimes

# In upload handler
if file and allowed_file(file.filename):
    if not validate_file_content(file):
        return jsonify({'error': 'Invalid file content'}), 400
```

---

## 🟢 LOW

### 11. Debug Mode Check

**Risk Level**: LOW  
**Location**: `run.py`

**Ensure debug mode is disabled in production**:
```python
# run.py
if __name__ == '__main__':
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    app.run(host='0.0.0.0', port=5103, debug=debug_mode)
```

---

### 12. Error Handling

**Risk Level**: LOW  
**Location**: Various

**Description**:  
Detailed error messages could leak information to attackers.

**Fix**:
```python
# app/__init__.py
@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    if app.debug:
        return str(error), 500
    return jsonify({'error': 'Internal server error'}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found'}), 404
```

---

## 📋 Implementation Checklist

### Priority 1 - Critical (Do First)
- [ ] Add CSRF protection with Flask-WTF
- [ ] Implement rate limiting with Flask-Limiter
- [ ] Ensure SECRET_KEY is set in production
- [ ] Add account lockout mechanism

### Priority 2 - High
- [ ] Add security headers
- [ ] Audit all endpoints for IDOR vulnerabilities
- [ ] Configure secure session cookies

### Priority 3 - Medium
- [ ] Implement password strength validation
- [ ] Add file content validation
- [ ] Review all raw SQL queries

### Priority 4 - Low
- [ ] Verify debug mode is off in production
- [ ] Improve error handling
- [ ] Add security logging

---

## 📦 Dependencies to Add

```txt
# requirements.txt additions
Flask-WTF>=1.2.0
Flask-Limiter>=3.5.0
python-magic>=0.4.27  # For file content validation
```

---

## 🔗 References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/2.0.x/security/)
- [Flask-WTF CSRF Protection](https://flask-wtf.readthedocs.io/en/1.0.x/csrf/)
- [Flask-Limiter Documentation](https://flask-limiter.readthedocs.io/)

---

*This audit was performed on the current codebase. Re-audit after significant changes.*
