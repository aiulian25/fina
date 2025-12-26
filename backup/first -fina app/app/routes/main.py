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
    from app.models.subscription import Subscription
    from datetime import timedelta, date
    
    today = date.today()
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
    
    # Get upcoming subscriptions (next 30 days)
    end_date = datetime.now().date() + timedelta(days=30)
    upcoming_subscriptions = Subscription.query.filter(
        Subscription.user_id == current_user.id,
        Subscription.is_active == True,
        Subscription.next_due_date <= end_date
    ).order_by(Subscription.next_due_date).limit(5).all()
    
    # Get suggestions count
    from app.smart_detection import get_user_suggestions
    suggestions_count = len(get_user_suggestions(current_user.id))
    
    return render_template('dashboard.html', 
                         categories=categories, 
                         total_spent=total_spent,
                         total_expenses=total_expenses,
                         chart_data=chart_data,
                         categories_json=categories_json,
                         available_years=available_years,
                         current_year=current_year,
                         upcoming_subscriptions=upcoming_subscriptions,
                         suggestions_count=suggestions_count,
                         today=today)

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
        
        # Budget settings
        monthly_budget = request.form.get('monthly_budget', '').strip()
        if monthly_budget:
            try:
                category.monthly_budget = float(monthly_budget)
                if category.monthly_budget < 0:
                    category.monthly_budget = None
            except ValueError:
                category.monthly_budget = None
        else:
            category.monthly_budget = None
        
        # Budget alert threshold (default 100%)
        threshold = request.form.get('budget_alert_threshold', '100').strip()
        try:
            category.budget_alert_threshold = float(threshold) / 100
            if category.budget_alert_threshold < 0.5 or category.budget_alert_threshold > 2.0:
                category.budget_alert_threshold = 1.0
        except ValueError:
            category.budget_alert_threshold = 1.0
        
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
        
        # Check budget after adding expense
        from app.budget_alerts import check_budget_alerts
        try:
            check_budget_alerts()
        except Exception as e:
            print(f"[Budget Check] Error: {e}")
        
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


@bp.route('/api/ocr/process', methods=['POST'])
@login_required
def process_receipt_ocr():
    """
    Process uploaded receipt image with OCR
    Returns extracted data as JSON
    """
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if not file or not file.filename:
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'success': False, 'error': 'Invalid file type'}), 400
    
    try:
        from app.ocr import extract_receipt_data, is_valid_receipt_image
        
        # Save temp file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_filename = f"temp_{current_user.id}_{timestamp}_{filename}"
        upload_folder = os.path.join(current_app.root_path, 'static', 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        temp_path = os.path.join(upload_folder, temp_filename)
        
        file.save(temp_path)
        
        # Validate image
        is_valid, message = is_valid_receipt_image(temp_path)
        if not is_valid:
            os.remove(temp_path)
            return jsonify({'success': False, 'error': message}), 400
        
        # Extract data with OCR
        extracted_data = extract_receipt_data(temp_path)
        
        # Format response
        response = {
            'success': extracted_data['success'],
            'amount': extracted_data['amount'],
            'merchant': extracted_data['merchant'],
            'confidence': extracted_data['confidence'],
            'temp_file': temp_filename
        }
        
        if extracted_data['date']:
            response['date'] = extracted_data['date'].strftime('%Y-%m-%d')
        
        # Don't delete temp file - will be used if user confirms
        
        return jsonify(response)
        
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/predictions')
@login_required
def predictions():
    """Display spending predictions dashboard"""
    from app.predictions import get_spending_predictions, generate_insights
    from datetime import datetime
    
    # Get predictions for next 3 months
    predictions_data = get_spending_predictions(current_user.id, months_ahead=3)
    
    # Generate insights
    insights = generate_insights(
        predictions_data['by_category'],
        datetime.now()
    )
    
    return render_template('predictions.html',
                         predictions=predictions_data,
                         insights=insights)


@bp.route('/api/predictions')
@login_required
def api_predictions():
    """Return JSON predictions for charts"""
    from app.predictions import get_spending_predictions
    
    months_ahead = request.args.get('months', 3, type=int)
    
    # Limit to reasonable range
    if months_ahead < 1 or months_ahead > 12:
        return jsonify({'error': 'months must be between 1 and 12'}), 400
    
    predictions = get_spending_predictions(current_user.id, months_ahead)
    
    return jsonify(predictions)


@bp.route('/api/predictions/category/<int:category_id>')
@login_required
def api_category_forecast(category_id):
    """Get detailed forecast for specific category"""
    from app.predictions import get_category_forecast
    from app.models.category import Category
    
    # Security check: ensure category belongs to user
    category = Category.query.filter_by(
        id=category_id,
        user_id=current_user.id
    ).first()
    
    if not category:
        return jsonify({'error': 'Category not found'}), 404
    
    forecast = get_category_forecast(category, months=6)
    
    return jsonify({
        'category': category.name,
        'forecast': forecast
    })


@bp.route('/api/search')
@login_required
def api_search():
    """Global search API endpoint"""
    from app.search import search_all
    
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify({
            'success': False,
            'error': 'Query must be at least 2 characters',
            'results': {
                'expenses': [],
                'categories': [],
                'subscriptions': [],
                'tags': [],
                'total': 0
            }
        })
    
    # Perform search with user isolation
    results = search_all(query, current_user.id, limit=50)
    
    return jsonify({
        'success': True,
        'results': results
    })


@bp.route('/api/search/suggestions')
@login_required
def api_search_suggestions():
    """Quick search suggestions for autocomplete"""
    from app.search import quick_search_suggestions
    
    query = request.args.get('q', '').strip()
    
    if not query or len(query) < 2:
        return jsonify({'suggestions': []})
    
    suggestions = quick_search_suggestions(query, current_user.id, limit=5)
    
    return jsonify({'suggestions': suggestions})


@bp.route('/search')
@login_required
def search_page():
    """Search results page"""
    from app.search import search_all
    
    query = request.args.get('q', '').strip()
    
    if not query:
        return render_template('search.html', results=None, query='')
    
    results = search_all(query, current_user.id, limit=100)
    
    return render_template('search.html', results=results, query=query)


@bp.route('/bank-import', methods=['GET', 'POST'])
@login_required
def bank_import():
    """Bank statement import page"""
    if request.method == 'GET':
        # Get user's categories for mapping
        categories = Category.query.filter_by(user_id=current_user.id).all()
        return render_template('bank_import.html', categories=categories)
    
    # POST: Store uploaded file temporarily and redirect to review
    if 'file' not in request.files:
        flash('No file uploaded', 'error')
        return redirect(url_for('main.bank_import'))
    
    file = request.files['file']
    if not file or not file.filename:
        flash('No file selected', 'error')
        return redirect(url_for('main.bank_import'))
    
    # Save temporarily for processing
    filename = secure_filename(file.filename)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    temp_filename = f"bank_{current_user.id}_{timestamp}_{filename}"
    temp_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'temp')
    os.makedirs(temp_folder, exist_ok=True)
    temp_path = os.path.join(temp_folder, temp_filename)
    
    file.save(temp_path)
    
    # Redirect to parse API then review
    return redirect(url_for('main.bank_import_review', filename=temp_filename))


@bp.route('/bank-import/review/<filename>')
@login_required
def bank_import_review(filename):
    """Review parsed transactions before importing"""
    from app.bank_import import parse_bank_statement
    
    # Security: Verify filename belongs to current user
    if not filename.startswith(f"bank_{current_user.id}_"):
        flash('Invalid file', 'error')
        return redirect(url_for('main.bank_import'))
    
    temp_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'temp')
    temp_path = os.path.join(temp_folder, filename)
    
    if not os.path.exists(temp_path):
        flash('File not found. Please upload again.', 'error')
        return redirect(url_for('main.bank_import'))
    
    try:
        # Read file
        with open(temp_path, 'rb') as f:
            file_content = f.read()
        
        # Parse bank statement
        result = parse_bank_statement(file_content, filename)
        
        if not result['success']:
            flash(f"Parsing failed: {result.get('error', 'Unknown error')}", 'error')
            # Clean up temp file
            try:
                os.remove(temp_path)
            except:
                pass
            return redirect(url_for('main.bank_import'))
        
        # Get user's categories
        categories = Category.query.filter_by(user_id=current_user.id).all()
        
        # Store temp filename in session for confirmation
        from flask import session
        session['bank_import_file'] = filename
        
        return render_template('bank_import_review.html',
                             transactions=result['transactions'],
                             total_found=result['total_found'],
                             categories=categories,
                             bank_format=result.get('bank_format', 'Unknown'),
                             parse_errors=result.get('parse_errors', []))
        
    except Exception as e:
        flash(f'Error processing file: {str(e)}', 'error')
        # Clean up temp file
        try:
            os.remove(temp_path)
        except:
            pass
        return redirect(url_for('main.bank_import'))


@bp.route('/bank-import/confirm', methods=['POST'])
@login_required
def bank_import_confirm():
    """Confirm and import selected transactions"""
    from flask import session
    
    # Get temp filename from session
    filename = session.get('bank_import_file')
    if not filename or not filename.startswith(f"bank_{current_user.id}_"):
        flash('Invalid session. Please try again.', 'error')
        return redirect(url_for('main.bank_import'))
    
    temp_folder = os.path.join(current_app.root_path, 'static', 'uploads', 'temp')
    temp_path = os.path.join(temp_folder, filename)
    
    # Get selected transactions from form
    selected_indices = request.form.getlist('selected_transactions')
    category_mappings = {}  # Map transaction index to category_id
    
    for idx in selected_indices:
        category_id = request.form.get(f'category_{idx}')
        if category_id:
            category_mappings[int(idx)] = int(category_id)
    
    if not selected_indices:
        flash('No transactions selected for import', 'warning')
        return redirect(url_for('main.bank_import_review', filename=filename))
    
    try:
        # Re-parse to get transactions
        with open(temp_path, 'rb') as f:
            file_content = f.read()
        
        from app.bank_import import parse_bank_statement
        result = parse_bank_statement(file_content, filename)
        
        if not result['success']:
            raise Exception('Re-parsing failed')
        
        # Import selected transactions
        imported_count = 0
        skipped_count = 0
        
        for idx_str in selected_indices:
            idx = int(idx_str)
            if idx >= len(result['transactions']):
                continue
            
            trans = result['transactions'][idx]
            category_id = category_mappings.get(idx)
            
            if not category_id:
                skipped_count += 1
                continue
            
            # Check if transaction already exists (deduplication)
            existing = Expense.query.filter_by(
                user_id=current_user.id,
                date=trans['date'],
                amount=trans['amount'],
                description=trans['description'][:50]  # Partial match
            ).first()
            
            if existing:
                skipped_count += 1
                continue
            
            # Create expense
            expense = Expense(
                description=trans['description'],
                amount=trans['amount'],
                date=datetime.combine(trans['date'], datetime.min.time()),
                category_id=category_id,
                user_id=current_user.id,
                tags='imported, bank-statement'
            )
            
            db.session.add(expense)
            imported_count += 1
        
        db.session.commit()
        
        # Clean up temp file
        try:
            os.remove(temp_path)
            session.pop('bank_import_file', None)
        except:
            pass
        
        if imported_count > 0:
            flash(f'Successfully imported {imported_count} transactions!', 'success')
            if skipped_count > 0:
                flash(f'{skipped_count} transactions were skipped (duplicates or no category)', 'info')
        else:
            flash('No transactions were imported', 'warning')
        
        return redirect(url_for('main.dashboard'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Import failed: {str(e)}', 'error')
        return redirect(url_for('main.bank_import'))


@bp.route('/api/bank-import/parse', methods=['POST'])
@login_required
def api_bank_import_parse():
    """API endpoint for parsing bank statement (AJAX)"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if not file or not file.filename:
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    try:
        from app.bank_import import parse_bank_statement
        
        # Read file content
        file_content = file.read()
        filename = secure_filename(file.filename)
        
        # Parse
        result = parse_bank_statement(file_content, filename)
        
        if not result['success']:
            return jsonify(result), 400
        
        # Convert dates to strings for JSON
        for trans in result['transactions']:
            trans['date'] = trans['date'].isoformat()
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
