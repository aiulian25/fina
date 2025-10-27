from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.user import User, Tag
from app.models.category import Category, Expense
from werkzeug.security import generate_password_hash
import csv
import io
from datetime import datetime
import json

bp = Blueprint('settings', __name__, url_prefix='/settings')

def admin_required(f):
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Admin access required', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
def index():
    users = User.query.all() if current_user.is_admin else []
    tags = Tag.query.filter_by(user_id=current_user.id).all()
    return render_template('settings/index.html', users=users, tags=tags)

# USER MANAGEMENT
@bp.route('/profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.username = request.form.get('username')
        current_user.email = request.form.get('email')
        current_user.currency = request.form.get('currency', 'USD')
        
        new_password = request.form.get('new_password')
        if new_password:
            current_user.set_password(new_password)
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('settings.index'))
    
    return render_template('settings/edit_profile.html')

@bp.route('/users/create', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        is_admin = request.form.get('is_admin') == 'on'
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'error')
            return redirect(url_for('settings.create_user'))
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('settings.create_user'))
        
        user = User(username=username, email=email, is_admin=is_admin)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        flash(f'User {username} created successfully!', 'success')
        return redirect(url_for('settings.index'))
    
    return render_template('settings/create_user.html')

@bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.is_admin = request.form.get('is_admin') == 'on'
        
        new_password = request.form.get('new_password')
        if new_password:
            user.set_password(new_password)
        
        db.session.commit()
        flash(f'User {user.username} updated!', 'success')
        return redirect(url_for('settings.index'))
    
    return render_template('settings/edit_user.html', user=user)

@bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    if user_id == current_user.id:
        flash('Cannot delete your own account', 'error')
        return redirect(url_for('settings.index'))
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {user.username} deleted', 'success')
    return redirect(url_for('settings.index'))

# TAG MANAGEMENT
@bp.route('/tags/create', methods=['GET', 'POST'])
@login_required
def create_tag():
    if request.method == 'POST':
        name = request.form.get('name')
        color = request.form.get('color', '#6366f1')
        
        tag = Tag(name=name, color=color, user_id=current_user.id)
        db.session.add(tag)
        db.session.commit()
        
        flash(f'Tag "{name}" created!', 'success')
        return redirect(url_for('settings.index'))
    
    return render_template('settings/create_tag.html')

@bp.route('/tags/<int:tag_id>/delete', methods=['POST'])
@login_required
def delete_tag(tag_id):
    tag = Tag.query.filter_by(id=tag_id, user_id=current_user.id).first_or_404()
    db.session.delete(tag)
    db.session.commit()
    
    flash(f'Tag "{tag.name}" deleted', 'success')
    return redirect(url_for('settings.index'))

# IMPORT/EXPORT
@bp.route('/export')
@login_required
def export_data():
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow(['Category', 'Description', 'Amount', 'Date', 'Paid By', 'Tags'])
    
    expenses = Expense.query.filter_by(user_id=current_user.id).all()
    for expense in expenses:
        writer.writerow([
            expense.category.name,
            expense.description,
            expense.amount,
            expense.date.strftime('%Y-%m-%d'),
            expense.paid_by or '',
            expense.tags or ''
        ])
    
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'expenses_{datetime.now().strftime("%Y%m%d")}.csv'
    )

@bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_data():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file uploaded', 'error')
            return redirect(url_for('settings.import_data'))
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(url_for('settings.import_data'))
        
        if not file.filename.endswith('.csv'):
            flash('Only CSV files are supported', 'error')
            return redirect(url_for('settings.import_data'))
        
        try:
            stream = io.StringIO(file.stream.read().decode('UTF8'), newline=None)
            csv_reader = csv.DictReader(stream)
            
            imported = 0
            for row in csv_reader:
                category_name = row.get('Category')
                category = Category.query.filter_by(name=category_name, user_id=current_user.id).first()
                
                if not category:
                    category = Category(name=category_name, user_id=current_user.id)
                    db.session.add(category)
                    db.session.flush()
                
                expense = Expense(
                    description=row.get('Description'),
                    amount=float(row.get('Amount', 0)),
                    date=datetime.strptime(row.get('Date'), '%Y-%m-%d'),
                    paid_by=row.get('Paid By'),
                    tags=row.get('Tags'),
                    category_id=category.id,
                    user_id=current_user.id
                )
                db.session.add(expense)
                imported += 1
            
            db.session.commit()
            flash(f'Successfully imported {imported} expenses!', 'success')
            return redirect(url_for('main.dashboard'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Import failed: {str(e)}', 'error')
            return redirect(url_for('settings.import_data'))
    
    return render_template('settings/import.html')

# 2FA Management
@bp.route('/2fa/setup', methods=['GET', 'POST'])
@login_required
def setup_2fa():
    if request.method == 'POST':
        token = request.form.get('token')
        
        if not current_user.totp_secret:
            flash('2FA setup not initiated', 'error')
            return redirect(url_for('settings.setup_2fa'))
        
        if current_user.verify_totp(token):
            current_user.is_2fa_enabled = True
            db.session.commit()
            flash('2FA enabled successfully!', 'success')
            return redirect(url_for('settings.index'))
        else:
            flash('Invalid code. Please try again.', 'error')
    
    # Generate QR code
    if not current_user.totp_secret:
        current_user.generate_totp_secret()
        db.session.commit()
    
    import qrcode
    import io
    import base64
    
    uri = current_user.get_totp_uri()
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return render_template('settings/setup_2fa.html', 
                         qr_code=qr_base64,
                         secret=current_user.totp_secret)

@bp.route('/2fa/disable', methods=['POST'])
@login_required
def disable_2fa():
    current_user.is_2fa_enabled = False
    current_user.totp_secret = None
    db.session.commit()
    flash('2FA disabled successfully', 'success')
    return redirect(url_for('settings.index'))
