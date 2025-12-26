from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Expense, Category
from werkzeug.utils import secure_filename
import os
import csv
import io
from datetime import datetime

bp = Blueprint('expenses', __name__, url_prefix='/api/expenses')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/', methods=['GET'])
@login_required
def get_expenses():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    category_id = request.args.get('category_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    search = request.args.get('search', '')
    
    query = Expense.query.filter_by(user_id=current_user.id)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if start_date:
        query = query.filter(Expense.date >= datetime.fromisoformat(start_date))
    
    if end_date:
        query = query.filter(Expense.date <= datetime.fromisoformat(end_date))
    
    if search:
        query = query.filter(Expense.description.ilike(f'%{search}%'))
    
    pagination = query.order_by(Expense.date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'expenses': [expense.to_dict() for expense in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    })


@bp.route('/', methods=['POST'])
@login_required
def create_expense():
    # Handle both FormData and JSON requests
    # When FormData is sent (even without files), request.form will have the data
    # When JSON is sent, request.form will be empty
    data = request.form if request.form else request.get_json()
    
    # Validate required fields
    if not data or not data.get('amount') or not data.get('category_id') or not data.get('description'):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    # Security: Verify category belongs to current user
    category = Category.query.filter_by(id=int(data.get('category_id')), user_id=current_user.id).first()
    if not category:
        return jsonify({'success': False, 'message': 'Invalid category'}), 400
    
    # Handle receipt upload
    receipt_path = None
    if 'receipt' in request.files:
        file = request.files['receipt']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"{current_user.id}_{datetime.utcnow().timestamp()}_{file.filename}")
            receipts_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'receipts')
            filepath = os.path.join(receipts_dir, filename)
            file.save(filepath)
            receipt_path = f'receipts/{filename}'
    
    # Create expense
    expense = Expense(
        amount=float(data.get('amount')),
        currency=data.get('currency', current_user.currency),
        description=data.get('description'),
        category_id=int(data.get('category_id')),
        user_id=current_user.id,
        receipt_path=receipt_path,
        date=datetime.fromisoformat(data.get('date')) if data.get('date') else datetime.utcnow()
    )
    
    # Handle tags
    if data.get('tags'):
        if isinstance(data.get('tags'), str):
            import json
            tags = json.loads(data.get('tags'))
        else:
            tags = data.get('tags')
        expense.set_tags(tags)
    
    db.session.add(expense)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'expense': expense.to_dict()
    }), 201


@bp.route('/<int:expense_id>', methods=['PUT'])
@login_required
def update_expense(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first()
    
    if not expense:
        return jsonify({'success': False, 'message': 'Expense not found'}), 404
    
    # Handle both FormData and JSON requests
    data = request.form if request.form else request.get_json()
    
    # Update fields
    if data.get('amount'):
        expense.amount = float(data.get('amount'))
    if data.get('currency'):
        expense.currency = data.get('currency')
    if data.get('description'):
        expense.description = data.get('description')
    if data.get('category_id'):
        # Security: Verify category belongs to current user
        category = Category.query.filter_by(id=int(data.get('category_id')), user_id=current_user.id).first()
        if not category:
            return jsonify({'success': False, 'message': 'Invalid category'}), 400
        expense.category_id = int(data.get('category_id'))
    if data.get('date'):
        expense.date = datetime.fromisoformat(data.get('date'))
    if data.get('tags') is not None:
        if isinstance(data.get('tags'), str):
            import json
            tags = json.loads(data.get('tags'))
        else:
            tags = data.get('tags')
        expense.set_tags(tags)
    
    # Handle receipt upload
    if 'receipt' in request.files:
        file = request.files['receipt']
        if file and file.filename and allowed_file(file.filename):
            # Delete old receipt
            if expense.receipt_path:
                clean_path = expense.receipt_path.replace('/uploads/', '').lstrip('/')
                old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], clean_path)
                if os.path.exists(old_path):
                    os.remove(old_path)
            
            filename = secure_filename(f"{current_user.id}_{datetime.utcnow().timestamp()}_{file.filename}")
            receipts_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'receipts')
            filepath = os.path.join(receipts_dir, filename)
            file.save(filepath)
            expense.receipt_path = f'receipts/{filename}'
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'expense': expense.to_dict()
    })


@bp.route('/<int:expense_id>', methods=['DELETE'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.filter_by(id=expense_id, user_id=current_user.id).first()
    
    if not expense:
        return jsonify({'success': False, 'message': 'Expense not found'}), 404
    
    # Delete receipt file
    if expense.receipt_path:
        # Remove leading slash and 'uploads/' prefix if present
        clean_path = expense.receipt_path.replace('/uploads/', '').lstrip('/')
        receipt_file = os.path.join(current_app.config['UPLOAD_FOLDER'], clean_path)
        if os.path.exists(receipt_file):
            os.remove(receipt_file)
    
    db.session.delete(expense)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Expense deleted'})


@bp.route('/categories', methods=['GET'])
@login_required
def get_categories():
    categories = Category.query.filter_by(user_id=current_user.id).order_by(Category.display_order, Category.created_at).all()
    return jsonify({
        'categories': [cat.to_dict() for cat in categories]
    })


@bp.route('/categories', methods=['POST'])
@login_required
def create_category():
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'success': False, 'message': 'Name is required'}), 400
    
    # Get max display_order for user's categories
    max_order = db.session.query(db.func.max(Category.display_order)).filter_by(user_id=current_user.id).scalar() or 0
    
    category = Category(
        name=data.get('name'),
        color=data.get('color', '#2b8cee'),
        icon=data.get('icon', 'category'),
        display_order=max_order + 1,
        user_id=current_user.id
    )
    
    db.session.add(category)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'category': category.to_dict()
    }), 201


@bp.route('/categories/<int:category_id>', methods=['PUT'])
@login_required
def update_category(category_id):
    category = Category.query.filter_by(id=category_id, user_id=current_user.id).first()
    
    if not category:
        return jsonify({'success': False, 'message': 'Category not found'}), 404
    
    data = request.get_json()
    
    if data.get('name'):
        category.name = data.get('name')
    if data.get('color'):
        category.color = data.get('color')
    if data.get('icon'):
        category.icon = data.get('icon')
    if 'display_order' in data:
        category.display_order = data.get('display_order')
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'category': category.to_dict()
    })


@bp.route('/categories/<int:category_id>', methods=['DELETE'])
@login_required
def delete_category(category_id):
    category = Category.query.filter_by(id=category_id, user_id=current_user.id).first()
    
    if not category:
        return jsonify({'success': False, 'message': 'Category not found'}), 404
    
    # Check if category has expenses
    if category.expenses.count() > 0:
        return jsonify({'success': False, 'message': 'Cannot delete category with expenses'}), 400
    
    db.session.delete(category)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Category deleted'})


@bp.route('/categories/reorder', methods=['PUT'])
@login_required
def reorder_categories():
    """
    Reorder categories for the current user
    Expects: { "categories": [{"id": 1, "display_order": 0}, {"id": 2, "display_order": 1}, ...] }
    Security: Only updates categories belonging to current_user
    """
    data = request.get_json()
    
    if not data or 'categories' not in data:
        return jsonify({'success': False, 'message': 'Categories array required'}), 400
    
    try:
        for cat_data in data['categories']:
            category = Category.query.filter_by(id=cat_data['id'], user_id=current_user.id).first()
            if category:
                category.display_order = cat_data['display_order']
        
        db.session.commit()
        return jsonify({'success': True, 'message': 'Categories reordered'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@bp.route('/export/csv', methods=['GET'])
@login_required
def export_csv():
    expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Date', 'Description', 'Amount', 'Currency', 'Category', 'Tags'])
    
    # Write data
    for expense in expenses:
        writer.writerow([
            expense.date.strftime('%Y-%m-%d %H:%M:%S'),
            expense.description,
            expense.amount,
            expense.currency,
            expense.category.name,
            ', '.join(expense.get_tags())
        ])
    
    output.seek(0)
    
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'fina_expenses_{datetime.utcnow().strftime("%Y%m%d")}.csv'
    )


@bp.route('/import/csv', methods=['POST'])
@login_required
def import_csv():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({'success': False, 'message': 'File must be CSV'}), 400
    
    try:
        stream = io.StringIO(file.stream.read().decode('utf-8'))
        reader = csv.DictReader(stream)
        
        imported_count = 0
        errors = []
        
        for row in reader:
            try:
                # Find or create category
                category_name = row.get('Category', 'Uncategorized')
                category = Category.query.filter_by(user_id=current_user.id, name=category_name).first()
                
                if not category:
                    category = Category(name=category_name, user_id=current_user.id)
                    db.session.add(category)
                    db.session.flush()
                
                # Parse date
                date_str = row.get('Date', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))
                expense_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
                
                # Create expense
                expense = Expense(
                    amount=float(row['Amount']),
                    currency=row.get('Currency', current_user.currency),
                    description=row['Description'],
                    category_id=category.id,
                    user_id=current_user.id,
                    date=expense_date
                )
                
                # Handle tags
                if row.get('Tags'):
                    tags = [tag.strip() for tag in row['Tags'].split(',')]
                    expense.set_tags(tags)
                
                db.session.add(expense)
                imported_count += 1
                
            except Exception as e:
                errors.append(f"Row error: {str(e)}")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'imported': imported_count,
            'errors': errors
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Import failed: {str(e)}'}), 500
