from app import db
from app.models import Category
import re
from decimal import Decimal, InvalidOperation

# Maximum allowed amount to prevent overflow attacks
MAX_AMOUNT = 999999999.99  # ~1 billion
MIN_AMOUNT = 0.01  # Minimum positive amount


def validate_amount(amount, field_name='Amount', allow_zero=False, allow_negative=False):
    """
    Validate monetary amounts to prevent negative values and overflow attacks.
    
    Args:
        amount: The amount to validate (can be string, int, or float)
        field_name: Name of the field for error messages
        allow_zero: Whether zero is a valid value
        allow_negative: Whether negative values are allowed (for adjustments)
    
    Returns:
        (is_valid, sanitized_value, error_message)
        - is_valid: Boolean indicating if validation passed
        - sanitized_value: Properly converted Decimal value (or None if invalid)
        - error_message: Error description (or None if valid)
    """
    if amount is None or amount == '':
        return False, None, f'{field_name} is required'
    
    # Convert to Decimal for precision
    try:
        if isinstance(amount, str):
            # Remove common formatting characters
            cleaned = amount.strip().replace(',', '').replace(' ', '')
            # Handle currency symbols
            cleaned = re.sub(r'^[$€£¥]|[$€£¥]$|lei$|ron$', '', cleaned, flags=re.IGNORECASE).strip()
            value = Decimal(cleaned)
        elif isinstance(amount, (int, float)):
            # Use string conversion to avoid float precision issues
            value = Decimal(str(amount))
        elif isinstance(amount, Decimal):
            value = amount
        else:
            return False, None, f'{field_name} must be a valid number'
    except (InvalidOperation, ValueError, TypeError):
        return False, None, f'{field_name} must be a valid number'
    
    # Check for special float values
    if not value.is_finite():
        return False, None, f'{field_name} must be a finite number'
    
    # Check minimum
    if not allow_negative and value < 0:
        return False, None, f'{field_name} cannot be negative'
    
    if not allow_zero and value == 0:
        return False, None, f'{field_name} cannot be zero'
    
    if allow_zero and not allow_negative and value < 0:
        return False, None, f'{field_name} cannot be negative'
    
    # Check maximum (overflow protection)
    if abs(value) > MAX_AMOUNT:
        return False, None, f'{field_name} exceeds maximum allowed value ({MAX_AMOUNT:,.2f})'
    
    # Round to 2 decimal places for currency
    sanitized = round(float(value), 2)
    
    return True, sanitized, None


def validate_positive_integer(value, field_name='Value', min_val=None, max_val=None):
    """
    Validate positive integers (for IDs, counts, etc.)
    
    Args:
        value: The value to validate
        field_name: Name of the field for error messages
        min_val: Minimum allowed value (optional)
        max_val: Maximum allowed value (optional)
    
    Returns:
        (is_valid, sanitized_value, error_message)
    """
    if value is None:
        return False, None, f'{field_name} is required'
    
    try:
        int_val = int(value)
    except (ValueError, TypeError):
        return False, None, f'{field_name} must be a valid integer'
    
    if int_val < 0:
        return False, None, f'{field_name} cannot be negative'
    
    if min_val is not None and int_val < min_val:
        return False, None, f'{field_name} must be at least {min_val}'
    
    if max_val is not None and int_val > max_val:
        return False, None, f'{field_name} cannot exceed {max_val}'
    
    return True, int_val, None


def create_default_categories(user_id):
    """Create default categories for a new user"""
    default_categories = [
        {'name': 'Food & Dining', 'color': '#ff6b6b', 'icon': 'restaurant'},
        {'name': 'Transportation', 'color': '#4ecdc4', 'icon': 'directions_car'},
        {'name': 'Shopping', 'color': '#95e1d3', 'icon': 'shopping_bag'},
        {'name': 'Entertainment', 'color': '#f38181', 'icon': 'movie'},
        {'name': 'Bills & Utilities', 'color': '#aa96da', 'icon': 'receipt'},
        {'name': 'Healthcare', 'color': '#fcbad3', 'icon': 'medical_services'},
        {'name': 'Education', 'color': '#a8d8ea', 'icon': 'school'},
        {'name': 'Other', 'color': '#92adc9', 'icon': 'category'}
    ]
    
    for index, cat_data in enumerate(default_categories):
        category = Category(
            name=cat_data['name'],
            color=cat_data['color'],
            icon=cat_data['icon'],
            display_order=index,
            user_id=user_id
        )
        db.session.add(category)
    
    db.session.commit()


def validate_password(password):
    """
    Validate password strength.
    Returns (is_valid, error_message)
    
    Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    - At least one special character
    - Not a common password
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>\-_=+\[\]\\;\'`~]', password):
        return False, "Password must contain at least one special character (!@#$%^&*...)"
    
    # Check against common passwords
    common_passwords = [
        'password', 'password1', 'password123', '12345678', 'qwerty123',
        'admin123', 'letmein', 'welcome1', 'monkey123', 'dragon123',
        'master123', 'sunshine1', 'princess1', 'football1', 'iloveyou1'
    ]
    if password.lower() in common_passwords:
        return False, "Password is too common. Please choose a stronger password"
    
    return True, None


def format_currency(amount, currency='USD'):
    """Format amount with currency symbol"""
    symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'RON': 'lei'
    }
    symbol = symbols.get(currency, currency)
    
    if currency == 'RON':
        return f"{amount:,.2f} {symbol}"
    return f"{symbol}{amount:,.2f}"


def validate_file_content(file, allowed_extensions=None):
    """
    Validate that file content matches its extension.
    Prevents attackers from uploading malicious files disguised as images/PDFs.
    
    Args:
        file: FileStorage object from request.files
        allowed_extensions: Set of allowed extensions (e.g., {'png', 'jpg', 'pdf'})
    
    Returns:
        (is_valid, error_message, detected_type)
    """
    try:
        import magic
    except ImportError:
        # If python-magic is not installed, skip content validation
        # This allows the app to work without libmagic
        return True, None, None
    
    if not file or not file.filename:
        return False, "No file provided", None
    
    # Get extension from filename
    if '.' not in file.filename:
        return False, "File has no extension", None
    
    extension = file.filename.rsplit('.', 1)[1].lower()
    
    if allowed_extensions and extension not in allowed_extensions:
        return False, f"File type .{extension} is not allowed", None
    
    # Map extensions to expected MIME types
    extension_to_mime = {
        'jpg': ['image/jpeg'],
        'jpeg': ['image/jpeg'],
        'png': ['image/png'],
        'gif': ['image/gif'],
        'pdf': ['application/pdf'],
        'csv': ['text/csv', 'text/plain', 'application/csv'],
        'xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 
                 'application/zip'],  # xlsx is a zip file
        'xls': ['application/vnd.ms-excel', 'application/octet-stream']
    }
    
    # Read file content for magic detection
    file.seek(0)
    file_header = file.read(2048)
    file.seek(0)  # Reset file pointer
    
    # Detect MIME type from content
    try:
        detected_mime = magic.from_buffer(file_header, mime=True)
    except Exception as e:
        return False, f"Could not detect file type: {str(e)}", None
    
    # Check if detected MIME matches expected for extension
    expected_mimes = extension_to_mime.get(extension, [])
    
    if expected_mimes and detected_mime not in expected_mimes:
        return False, f"File content does not match .{extension} extension (detected: {detected_mime})", detected_mime
    
    return True, None, detected_mime


def log_security_event(event_type, user_id=None, description=None, success=True, request=None):
    """
    Log a security event to the database.
    
    Args:
        event_type: Type of event (LOGIN_SUCCESS, LOGIN_FAILED, etc.)
        user_id: ID of the user (optional for failed logins)
        description: Additional details about the event
        success: Whether the action was successful
        request: Flask request object for IP/user agent extraction
    """
    from app.models import SecurityLog
    
    ip_address = None
    user_agent = None
    
    if request:
        # Get real IP (handle proxies)
        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        if ip_address and ',' in ip_address:
            ip_address = ip_address.split(',')[0].strip()
        user_agent = request.headers.get('User-Agent', '')[:500]  # Truncate to fit column
    
    try:
        SecurityLog.log(
            event_type=event_type,
            user_id=user_id,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success
        )
    except Exception as e:
        # Don't let logging failures break the app
        print(f"Security logging error: {e}")
