from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models.category import Category, Expense
from app.models.user import Tag
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from sqlalchemy import extract, func
import json

bp = Blueprint('main', __name__)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@bp.route('/dashboard')
@login_required
def dashboard():
    categories = Category.query.filter_by(user_id=current_user.id).all()
    total_spent = sum(cat.get_total_spent() for cat in categories)
    
    total_expenses = Expense.query.filter_by(user_id=current_user.id).count()
    
    years_query = db.session.query(
        extract('year', Expense.date).label('year')
    ).filter(
        Expense.user_id == current_user.id
    ).distinct().all()
    
    available_years = sorted([int(year[0]) for year in years_query if year[0]], reverse=True)
    if not available_years:
        available_years = [datetime.now().year]
    
    current_year = datetime.now().year
    
    chart_data = []
    for cat in categories:
        spent = cat.get_total_spent()
        if spent > 0:
            chart_data.append({
                'name': cat.name,
                'value': spent,
                'color': cat.color
            })
    
    categories_json = [
        {
            'id': cat.id,
            'name': cat.name,
            'color': cat.color
        }
        for cat in categories
    ]
    
    return render_template('dashboard.html', 
                         categories=categories, 
                         total_spent=total_spent,
                         total_expenses=total_expenses,
                         chart_data=chart_data,
                         categories_json=categories_json,
                         available_years=available_years,
                         current_year=current_year)

@bp.route('/api/metrics')
@login_required
def get_metrics():
    category_id = request.args.get('category', 'all')
    year = int(request.args.get('year', datetime.now().year))
    
    if category_id == 'all':
        categories = Category.query.filter_by(user_id=current_user.id).all()
        
        monthly_data = [0] * 12
        for cat in categories:
            cat_monthly = cat.get_monthly_totals(year)
            monthly_data = [monthly_data[i] + cat_monthly[i] for i in range(12)]
        
        pie_data = [cat.get_yearly_total(year) for cat in categories]
        pie_labels = [cat.name for cat in categories]
        pie_colors = [cat.color for cat in categories]
        
        return jsonify({
            'category_name': 'All Categories',
            'monthly_data': monthly_data,
            'color': '#6366f1',
            'pie_data': pie_data,
            'pie_labels': pie_labels,
            'pie_colors': pie_colors
        })
    else:
        category = Category.query.filter_by(
            id=int(category_id), 
            user_id=current_user.id
        ).first_or_404()
        
        monthly_data = category.get_monthly_totals(year)
        
        categories = Category.query.filter_by(user_id=current_user.id).all()
        pie_data = [cat.get_yearly_total(year) for cat in categories]
        pie_labels = [cat.name for cat in categories]
        pie_colors = [cat.color for cat in categories]
        
        return jsonify({
            'category_name': category.name,
            'monthly_data': monthly_data,
            'color': category.color,
            'pie_data': pie_data,
            'pie_labels': pie_labels,
            'pie_colors': pie_colors
        })

@bp.route('/category/create', methods=['GET', 'POST'])
@login_required
def create_category():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        color = request.form.get('color', '#6366f1')
        
        if not name:
            flash('Category name is required', 'error')
            return redirect(url_for('main.create_category'))
        
        category = Category(
            name=name,
            description=description,
            color=color,
            user_id=current_user.id
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash('Category created successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('create_category.html')

@bp.route('/category/<int:category_id>')
@login_required
def view_category(category_id):
    category = Category.query.filter_by(id=category_id, user_id=current_user.id).first_or_404()
    expenses = Expense.query.filter_by(category_id=category_id, user_id=current_user.id).order_by(Expense.date.desc()).all()
    
    total_spent = category.get_total_spent()
    
    return render_template('view_category.html', 
                         category=category, 
                         expenses=expenses,
                         total_spent=total_spent)

@bp.route('/category/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(category_id):
    category = Category.query.filter_by(id=category_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        category.name = request.form.get('name')
        category.description = request.form.get('description')
        category.color = request.form.get('color')
        
        db.session.commit()
        flash('Category updated successfully!', 'success')
        return redirect(url_for('main.view_category', category_id=category.id))
    
    return render_template('edit_category.html', category=category)

@bp.route('/category/<int:category_id>/delete', methods=['POST'])
@login_required
def delete_category(category_id):
    category = Category.query.filter_by(id=category_id, user_id=current_user.id).first_or_404()
    
    for expense in category.expenses:
        if expense.file_path:
            file_path = os.path.join(current_app.root_path, 'static', expense.file_path)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except:
                    pass
    
    db.session.delete(category)
    db.session.commit()
    
    flash('Category deleted successfully!', 'success')
    return redirect(url_for('main.dashboard'))

@bp.route('/expense/create/<int:category_id>', methods=['GET', 'POST'])
@login_required
def create_expense(category_id):
    category = Category.query.filter_by(id=category_id, user_id=current_user.id).first_or_404()
    user_tags = Tag.query.filter_by(user_id=current_user.id).all()
    
    if request.method == 'POST':
        description = request.form.get('description')
        amount = request.form.get('amount')
        date_str = request.form.get('date')
        paid_by = request.form.get('paid_by')
        tags = request.form.get('tags')
        
        if not all([description, amount]):
            flash('Description and amount are required', 'error')
            return redirect(url_for('main.create_expense', category_id=category_id))
        
        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError()
        except ValueError:
            flash('Please enter a valid amount', 'error')
            return redirect(url_for('main.create_expense', category_id=category_id))
        
        file_path = None
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{current_user.id}_{timestamp}_{filename}"
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join('uploads', filename)
                file.save(os.path.join(current_app.root_path, 'static', file_path))
        
        expense_date = datetime.strptime(date_str, '%Y-%m-%d') if date_str else datetime.utcnow()
        
        expense = Expense(
            description=description,
            amount=amount,
            date=expense_date,
            paid_by=paid_by,
            tags=tags,
            file_path=file_path,
            category_id=category_id,
            user_id=current_user.id
        )
        
        db.session.add(expense)
        db.session.commit()
        
        flash('Expense added successfully!', 'success')
        return redirect(url_for('main.view_category', category_id=category_id))
    
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('create_expense.html', category=category, today=today, user_tags=user_tags)

@bp.route('/expense/<int:expense_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_expense(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    user_tags = Tag.query.filter_by(user_id=current_user.id).all()
    
    if request.method == 'POST':
        expense.description = request.form.get('description')
        expense.amount = float(request.form.get('amount'))
        expense.date = datetime.strptime(request.form.get('date'), '%Y-%m-%d')
        expense.paid_by = request.form.get('paid_by')
        expense.tags = request.form.get('tags')
        
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename and allowed_file(file.filename):
                if expense.file_path:
                    old_file = os.path.join(current_app.root_path, 'static', expense.file_path)
                    if os.path.exists(old_file):
                        try:
                            os.remove(old_file)
                        except:
                            pass
                
                filename = secure_filename(file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"{current_user.id}_{timestamp}_{filename}"
                upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join('uploads', filename)
                file.save(os.path.join(current_app.root_path, 'static', file_path))
                expense.file_path = file_path
        
        db.session.commit()
        flash('Expense updated successfully!', 'success')
        return redirect(url_for('main.view_category', category_id=expense.category_id))
    
    return render_template('edit_expense.html', expense=expense, user_tags=user_tags)

@bp.route('/expense/<int:expense_id>/delete', methods=['POST'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    category_id = expense.category_id
    
    if expense.file_path:
        file_path = os.path.join(current_app.root_path, 'static', expense.file_path)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
    
    db.session.delete(expense)
    db.session.commit()
    
    flash('Expense deleted successfully!', 'success')
    return redirect(url_for('main.view_category', category_id=category_id))

@bp.route('/expense/<int:expense_id>/download')
@login_required
def download_file(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    
    if not expense.file_path:
        flash('No file attached to this expense', 'error')
        return redirect(url_for('main.view_category', category_id=expense.category_id))
    
    # Use current_app.root_path to get correct path
    file_path = os.path.join(current_app.root_path, 'static', expense.file_path)
    
    if not os.path.exists(file_path):
        flash('File not found', 'error')
        return redirect(url_for('main.view_category', category_id=expense.category_id))
    
    return send_file(file_path, as_attachment=True)

@bp.route('/expense/<int:expense_id>/view')
@login_required
def view_file(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first_or_404()
    
    if not expense.file_path:
        flash('No file attached to this expense', 'error')
        return redirect(url_for('main.view_category', category_id=expense.category_id))
    
    file_path = os.path.join(current_app.root_path, 'static', expense.file_path)
    
    if not os.path.exists(file_path):
        flash('File not found', 'error')
        return redirect(url_for('main.view_category', category_id=expense.category_id))
    
    # Return file for inline viewing
    return send_file(file_path, as_attachment=False)
