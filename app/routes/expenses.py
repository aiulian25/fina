from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Expense, Category, Tag
from werkzeug.utils import secure_filename
import os
import csv
import io
from datetime import datetime
from app.ocr import extract_text_from_file
from app.auto_tagger import suggest_tags_for_expense

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
    tag_ids = request.args.get('tag_ids', '')  # Comma-separated tag IDs
    
    query = Expense.query.filter_by(user_id=current_user.id)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if start_date:
        query = query.filter(Expense.date >= datetime.fromisoformat(start_date))
    
    if end_date:
        query = query.filter(Expense.date <= datetime.fromisoformat(end_date))
    
    if search:
        query = query.filter(Expense.description.ilike(f'%{search}%'))
    
    # Filter by tags
    if tag_ids:
        try:
            tag_id_list = [int(tid.strip()) for tid in tag_ids.split(',') if tid.strip()]
            if tag_id_list:
                # Join with expense_tags to filter by tag IDs
                # Security: Tags are already filtered by user through Tag.user_id
                from app.models import ExpenseTag
                query = query.join(ExpenseTag).filter(ExpenseTag.tag_id.in_(tag_id_list))
        except ValueError:
            pass  # Invalid tag IDs, ignore filter
    
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
    
    # Security: Validate amount to prevent negative values and overflow attacks
    from app.utils import validate_amount, validate_positive_integer
    is_valid, validated_amount, error_msg = validate_amount(data.get('amount'), 'Amount')
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400
    
    # Security: Validate category_id is a positive integer
    is_valid, validated_category_id, error_msg = validate_positive_integer(data.get('category_id'), 'Category ID', min_val=1)
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400
    
    # Security: Verify category belongs to current user
    category = Category.query.filter_by(id=validated_category_id, user_id=current_user.id).first()
    if not category:
        return jsonify({'success': False, 'message': 'Invalid category'}), 400
    
    # Handle receipt upload
    receipt_path = None
    receipt_ocr_text = ""
    if 'receipt' in request.files:
        file = request.files['receipt']
        if file and file.filename and allowed_file(file.filename):
            # Security: Validate file content matches extension
            from app.utils import validate_file_content
            is_valid, error_msg, _ = validate_file_content(file, allowed_extensions=ALLOWED_EXTENSIONS)
            if not is_valid:
                return jsonify({'success': False, 'message': f'Receipt upload failed: {error_msg}'}), 400
            
            filename = secure_filename(f"{current_user.id}_{datetime.utcnow().timestamp()}_{file.filename}")
            receipts_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'receipts')
            filepath = os.path.join(receipts_dir, filename)
            file.save(filepath)
            receipt_path = f'receipts/{filename}'
            
            # Process OCR for image receipts
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            if file_ext in ['png', 'jpg', 'jpeg', 'pdf']:
                try:
                    abs_filepath = os.path.abspath(filepath)
                    receipt_ocr_text = extract_text_from_file(abs_filepath, file_ext)
                    print(f"OCR extracted {len(receipt_ocr_text)} characters from receipt {filename}")
                except Exception as e:
                    print(f"OCR processing failed for receipt {filename}: {str(e)}")
    
    # Create expense
    expense = Expense(
        amount=validated_amount,
        currency=data.get('currency', current_user.currency),
        description=data.get('description'),
        category_id=validated_category_id,
        user_id=current_user.id,
        receipt_path=receipt_path,
        receipt_ocr_text=receipt_ocr_text,
        date=datetime.fromisoformat(data.get('date')) if data.get('date') else datetime.utcnow()
    )
    
    # Handle legacy JSON tags
    if data.get('tags'):
        if isinstance(data.get('tags'), str):
            import json
            tags = json.loads(data.get('tags'))
        else:
            tags = data.get('tags')
        expense.set_tags(tags)
    
    db.session.add(expense)
    db.session.flush()  # Get expense ID before handling tag objects
    
    # Auto-suggest tags based on description and OCR text
    enable_auto_tags = data.get('enable_auto_tags', True)  # Default to True
    if enable_auto_tags:
        suggested_tags = suggest_tags_for_expense(
            description=data.get('description'),
            ocr_text=receipt_ocr_text,
            category_name=category.name
        )
        
        # Create or get tags and associate with expense
        for tag_data in suggested_tags:
            # Check if tag exists for user
            tag = Tag.query.filter_by(
                user_id=current_user.id,
                name=tag_data['name']
            ).first()
            
            if not tag:
                # Create new auto-generated tag
                tag = Tag(
                    name=tag_data['name'],
                    color=tag_data['color'],
                    icon=tag_data['icon'],
                    user_id=current_user.id,
                    is_auto=True,
                    use_count=0
                )
                db.session.add(tag)
                db.session.flush()
            
            # Associate tag with expense
            expense.add_tag(tag)
    
    # Handle manual tag associations (tag IDs passed from frontend)
    if data.get('tag_ids'):
        tag_ids = data.get('tag_ids')
        if isinstance(tag_ids, str):
            import json
            tag_ids = json.loads(tag_ids)
        
        for tag_id in tag_ids:
            # Security: Verify tag belongs to user
            tag = Tag.query.filter_by(id=tag_id, user_id=current_user.id).first()
            if tag:
                expense.add_tag(tag)
    
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
    
    # Security: Import validation functions
    from app.utils import validate_amount, validate_positive_integer
    
    # Update fields
    if data.get('amount'):
        is_valid, validated_amount, error_msg = validate_amount(data.get('amount'), 'Amount')
        if not is_valid:
            return jsonify({'success': False, 'message': error_msg}), 400
        expense.amount = validated_amount
    if data.get('currency'):
        expense.currency = data.get('currency')
    if data.get('description'):
        expense.description = data.get('description')
    if data.get('category_id'):
        is_valid, validated_category_id, error_msg = validate_positive_integer(data.get('category_id'), 'Category ID', min_val=1)
        if not is_valid:
            return jsonify({'success': False, 'message': error_msg}), 400
        # Security: Verify category belongs to current user
        category = Category.query.filter_by(id=validated_category_id, user_id=current_user.id).first()
        if not category:
            return jsonify({'success': False, 'message': 'Invalid category'}), 400
        expense.category_id = validated_category_id
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
            # Security: Validate file content matches extension
            from app.utils import validate_file_content
            is_valid, error_msg, _ = validate_file_content(file, allowed_extensions=ALLOWED_EXTENSIONS)
            if not is_valid:
                return jsonify({'success': False, 'message': f'Receipt upload failed: {error_msg}'}), 400
            
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
            
            # Process OCR for new receipt
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            if file_ext in ['png', 'jpg', 'jpeg', 'pdf']:
                try:
                    abs_filepath = os.path.abspath(filepath)
                    expense.receipt_ocr_text = extract_text_from_file(abs_filepath, file_ext)
                    print(f"OCR extracted {len(expense.receipt_ocr_text)} characters from receipt {filename}")
                except Exception as e:
                    print(f"OCR processing failed for receipt {filename}: {str(e)}")
    
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
    
    # Also return popular tags for quick selection
    popular_tags = Tag.query.filter_by(user_id=current_user.id)\
        .filter(Tag.use_count > 0)\
        .order_by(Tag.use_count.desc())\
        .limit(10)\
        .all()
    
    return jsonify({
        'categories': [cat.to_dict() for cat in categories],
        'popular_tags': [tag.to_dict() for tag in popular_tags]
    })


@bp.route('/suggest-tags', methods=['POST'])
@login_required
def suggest_tags():
    """
    Get tag suggestions for an expense based on description and category
    """
    data = request.get_json()
    
    description = data.get('description', '')
    category_id = data.get('category_id')
    ocr_text = data.get('ocr_text', '')
    
    category_name = None
    if category_id:
        category = Category.query.filter_by(id=category_id, user_id=current_user.id).first()
        if category:
            category_name = category.name
    
    # Get suggestions from auto-tagger
    suggestions = suggest_tags_for_expense(description, ocr_text, category_name)
    
    # Check which tags already exist for this user
    existing_tags = []
    if suggestions:
        tag_names = [s['name'] for s in suggestions]
        existing = Tag.query.filter(
            Tag.user_id == current_user.id,
            Tag.name.in_(tag_names)
        ).all()
        existing_tags = [tag.to_dict() for tag in existing]
    
    return jsonify({
        'success': True,
        'suggested_tags': suggestions,
        'existing_tags': existing_tags
    })


@bp.route('/categories', methods=['POST'])
@login_required
def create_category():
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'success': False, 'message': 'Name is required'}), 400
    
    # Sanitize inputs
    name = str(data.get('name')).strip()[:50]  # Limit to 50 chars
    color = str(data.get('color', '#2b8cee')).strip()[:7]  # Hex color format
    icon = str(data.get('icon', 'category')).strip()[:50]  # Limit to 50 chars, alphanumeric and underscore only
    
    # Validate color format (must be hex)
    if not color.startswith('#') or len(color) != 7:
        color = '#2b8cee'
    
    # Validate icon (alphanumeric and underscore only for security)
    if not all(c.isalnum() or c == '_' for c in icon):
        icon = 'category'
    
    # Get max display_order for user's categories
    max_order = db.session.query(db.func.max(Category.display_order)).filter_by(user_id=current_user.id).scalar() or 0
    
    category = Category(
        name=name,
        color=color,
        icon=icon,
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
        category.name = str(data.get('name')).strip()[:50]
    if data.get('color'):
        color = str(data.get('color')).strip()[:7]
        if color.startswith('#') and len(color) == 7:
            category.color = color
    if data.get('icon'):
        icon = str(data.get('icon')).strip()[:50]
        # Validate icon (alphanumeric and underscore only for security)
        if all(c.isalnum() or c == '_' for c in icon):
            category.icon = icon
    if 'display_order' in data:
        category.display_order = int(data.get('display_order'))
    
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
    
    data = request.get_json(silent=True) or {}
    move_to_category_id = data.get('move_to_category_id')
    
    # Count expenses in this category
    expense_count = category.expenses.count()
    
    # If category has expenses and no move_to_category_id specified, return error with count
    if expense_count > 0 and not move_to_category_id:
        return jsonify({
            'success': False, 
            'message': 'Category has expenses',
            'expense_count': expense_count,
            'requires_reassignment': True
        }), 400
    
    # If move_to_category_id specified, reassign expenses
    if expense_count > 0 and move_to_category_id:
        move_to_category = Category.query.filter_by(id=move_to_category_id, user_id=current_user.id).first()
        if not move_to_category:
            return jsonify({'success': False, 'message': 'Target category not found'}), 404
        
        # Reassign all expenses to the new category
        for expense in category.expenses:
            expense.category_id = move_to_category_id
    
    db.session.delete(category)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Category deleted', 'expenses_moved': expense_count})


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
