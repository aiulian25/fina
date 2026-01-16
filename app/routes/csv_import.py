"""
CSV/Bank Statement Import Routes for FINA
Handles file upload, parsing, duplicate detection, and category mapping
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import Expense, Category
from datetime import datetime, timedelta
from sqlalchemy import and_, or_
import csv
import io
import re
import json
from decimal import Decimal

bp = Blueprint('csv_import', __name__, url_prefix='/api/import')


class CSVParser:
    """Parse CSV files with auto-detection of format"""
    
    def __init__(self):
        self.errors = []
        
    def detect_delimiter(self, sample):
        """Auto-detect CSV delimiter"""
        delimiters = [',', ';', '\t', '|']
        counts = {d: sample.count(d) for d in delimiters}
        return max(counts, key=counts.get)
    
    def detect_encoding(self, file_bytes):
        """Detect file encoding"""
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252', 'iso-8859-1']
        for encoding in encodings:
            try:
                file_bytes.decode(encoding)
                return encoding
            except UnicodeDecodeError:
                continue
        return 'utf-8'
    
    def detect_columns(self, headers):
        """Auto-detect which columns contain date, description, amount"""
        headers_lower = [h.lower().strip() if h else '' for h in headers]
        
        mapping = {
            'date': None,
            'description': None,
            'amount': None,
            'debit': None,
            'credit': None,
            'category': None
        }
        
        # Date column keywords
        date_keywords = ['date', 'data', 'fecha', 'datum', 'transaction date', 'trans date', 'posting date']
        for idx, name in enumerate(headers_lower):
            if any(keyword in name for keyword in date_keywords):
                mapping['date'] = idx
                break
        
        # Description column keywords - prioritize "name" for merchant/payee names
        # First try to find "name" column (commonly used for merchant/payee)
        for idx, name in enumerate(headers_lower):
            if name == 'name' or 'payee' in name or 'merchant name' in name:
                mapping['description'] = idx
                break
        
        # If no "name" column, look for other description columns
        if mapping['description'] is None:
            desc_keywords = ['description', 'descriere', 'descripción', 'details', 'detalii', 'merchant', 
                            'comerciant', 'narrative', 'memo', 'particulars', 'transaction details']
            for idx, name in enumerate(headers_lower):
                if any(keyword in name for keyword in desc_keywords):
                    mapping['description'] = idx
                    break
        
        # Category column keywords (optional) - avoid generic "type" column that contains payment types
        # Only use "category" explicitly, not "type" which often contains payment methods
        for idx, name in enumerate(headers_lower):
            if name == 'category' or 'categorie' in name or 'categoría' in name:
                mapping['category'] = idx
                break
        
        # Amount columns
        amount_keywords = ['amount', 'suma', 'monto', 'valoare', 'value']
        debit_keywords = ['debit', 'withdrawal', 'retragere', 'spent', 'expense', 'cheltuială', 'out']
        credit_keywords = ['credit', 'deposit', 'depunere', 'income', 'venit', 'in']
        
        for idx, name in enumerate(headers_lower):
            if any(keyword in name for keyword in debit_keywords):
                mapping['debit'] = idx
            elif any(keyword in name for keyword in credit_keywords):
                mapping['credit'] = idx
            elif any(keyword in name for keyword in amount_keywords) and mapping['amount'] is None:
                mapping['amount'] = idx
        
        return mapping
    
    def parse_date(self, date_str):
        """Parse date string in various formats"""
        if not date_str or not isinstance(date_str, str):
            return None
            
        date_str = date_str.strip()
        if not date_str:
            return None
        
        # Common date formats
        formats = [
            '%d/%m/%Y', '%d-%m-%Y', '%Y-%m-%d', '%Y/%m/%d',
            '%d.%m.%Y', '%m/%d/%Y', '%d %b %Y', '%d %B %Y',
            '%Y%m%d', '%d-%b-%Y', '%d-%B-%Y', '%b %d, %Y',
            '%B %d, %Y', '%Y-%m-%d %H:%M:%S', '%d/%m/%Y %H:%M:%S'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        return None
    
    def parse_amount(self, amount_str):
        """Parse amount string to float"""
        if not amount_str:
            return 0.0
        
        if isinstance(amount_str, (int, float)):
            return float(amount_str)
        
        # Remove currency symbols and spaces
        amount_str = str(amount_str).strip()
        amount_str = re.sub(r'[^\d.,\-+]', '', amount_str)
        
        if not amount_str or amount_str == '-':
            return 0.0
        
        try:
            # Handle European format (1.234,56)
            if ',' in amount_str and '.' in amount_str:
                if amount_str.rfind(',') > amount_str.rfind('.'):
                    # European format: 1.234,56
                    amount_str = amount_str.replace('.', '').replace(',', '.')
                else:
                    # US format: 1,234.56
                    amount_str = amount_str.replace(',', '')
            elif ',' in amount_str:
                # Could be European (1,56) or US thousands (1,234)
                parts = amount_str.split(',')
                if len(parts[-1]) == 2:  # Likely European decimal
                    amount_str = amount_str.replace(',', '.')
                else:  # Likely US thousands
                    amount_str = amount_str.replace(',', '')
            
            return abs(float(amount_str))
        except (ValueError, AttributeError):
            return 0.0
    
    def parse_csv(self, file_bytes):
        """Parse CSV file and extract transactions"""
        try:
            # Detect encoding
            encoding = self.detect_encoding(file_bytes)
            content = file_bytes.decode(encoding)
            
            # Detect delimiter
            first_line = content.split('\n')[0]
            delimiter = self.detect_delimiter(first_line)
            
            # Parse CSV
            stream = io.StringIO(content)
            reader = csv.reader(stream, delimiter=delimiter)
            
            # Read headers
            headers = next(reader, None)
            if not headers:
                return {'success': False, 'error': 'CSV file is empty'}
            
            # Detect column mapping
            column_map = self.detect_columns(headers)
            
            if column_map['date'] is None:
                return {'success': False, 'error': 'Could not detect date column. Please ensure your CSV has a date column.'}
            
            if column_map['description'] is None:
                column_map['description'] = 1 if len(headers) > 1 else 0
            
            # Parse transactions
            transactions = []
            row_num = 0
            
            for row in reader:
                row_num += 1
                
                if not row or len(row) == 0:
                    continue
                
                try:
                    transaction = self.extract_transaction(row, column_map)
                    if transaction:
                        transactions.append(transaction)
                except Exception as e:
                    self.errors.append(f"Row {row_num}: {str(e)}")
            
            return {
                'success': True,
                'transactions': transactions,
                'total_found': len(transactions),
                'column_mapping': {k: headers[v] if v is not None else None for k, v in column_map.items()},
                'errors': self.errors
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Failed to parse CSV: {str(e)}'}
    
    def extract_transaction(self, row, column_map):
        """Extract transaction data from CSV row"""
        if len(row) <= max(v for v in column_map.values() if v is not None):
            return None
        
        # Parse date
        date_idx = column_map['date']
        trans_date = self.parse_date(row[date_idx])
        if not trans_date:
            return None
        
        # Parse description
        desc_idx = column_map['description']
        description = row[desc_idx].strip() if desc_idx is not None and desc_idx < len(row) else 'Transaction'
        if not description:
            description = 'Transaction'
        
        # Parse amount (handle debit/credit or single amount column)
        amount = 0.0
        trans_type = 'expense'
        
        if column_map['debit'] is not None and column_map['credit'] is not None:
            debit_val = self.parse_amount(row[column_map['debit']] if column_map['debit'] < len(row) else '0')
            credit_val = self.parse_amount(row[column_map['credit']] if column_map['credit'] < len(row) else '0')
            
            if debit_val > 0:
                amount = debit_val
                trans_type = 'expense'
            elif credit_val > 0:
                amount = credit_val
                trans_type = 'income'
        elif column_map['amount'] is not None:
            amount_val = self.parse_amount(row[column_map['amount']] if column_map['amount'] < len(row) else '0')
            amount = abs(amount_val)
            # Negative amounts are expenses, positive are income
            trans_type = 'expense' if amount_val < 0 or amount_val == 0 else 'income'
        
        if amount == 0:
            return None
        
        # Get bank category if available
        bank_category = None
        if column_map['category'] is not None and column_map['category'] < len(row):
            bank_category = row[column_map['category']].strip()
        
        return {
            'date': trans_date.isoformat(),
            'description': description[:200],  # Limit description length
            'amount': round(amount, 2),
            'type': trans_type,
            'bank_category': bank_category
        }


@bp.route('/parse-csv', methods=['POST'])
@login_required
def parse_csv():
    """
    Parse uploaded CSV file and return transactions for review
    Security: User must be authenticated, file size limited
    """
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    
    if not file or not file.filename:
        return jsonify({'success': False, 'error': 'No file selected'}), 400
    
    # Security: Validate filename
    filename = secure_filename(file.filename)
    if not filename.lower().endswith('.csv'):
        return jsonify({'success': False, 'error': 'Only CSV files are supported'}), 400
    
    # Security: Check file size (max 10MB)
    file_bytes = file.read()
    if len(file_bytes) > 10 * 1024 * 1024:
        return jsonify({'success': False, 'error': 'File too large. Maximum size is 10MB'}), 400
    
    # Parse CSV
    parser = CSVParser()
    result = parser.parse_csv(file_bytes)
    
    if not result['success']:
        return jsonify(result), 400
    
    return jsonify(result)


@bp.route('/detect-duplicates', methods=['POST'])
@login_required
def detect_duplicates():
    """
    Check for duplicate transactions in the database
    Security: Only checks current user's expenses
    """
    data = request.get_json()
    transactions = data.get('transactions', [])
    
    if not transactions:
        return jsonify({'success': False, 'error': 'No transactions provided'}), 400
    
    duplicates = []
    
    for trans in transactions:
        try:
            trans_date = datetime.fromisoformat(trans['date']).date()
            amount = float(trans['amount'])
            description = trans['description']
            
            # Look for potential duplicates within ±2 days and exact amount
            date_start = trans_date - timedelta(days=2)
            date_end = trans_date + timedelta(days=2)
            
            # Security: Filter by current user only
            existing = Expense.query.filter(
                Expense.user_id == current_user.id,
                Expense.date >= date_start,
                Expense.date <= date_end,
                Expense.amount == amount
            ).all()
            
            # Check for similar descriptions
            for exp in existing:
                # Simple similarity: check if descriptions overlap significantly
                desc_lower = description.lower()
                exp_desc_lower = exp.description.lower()
                
                # Check if at least 50% of words match
                desc_words = set(desc_lower.split())
                exp_words = set(exp_desc_lower.split())
                
                if len(desc_words) > 0:
                    overlap = len(desc_words.intersection(exp_words)) / len(desc_words)
                    if overlap >= 0.5:
                        duplicates.append({
                            'transaction': trans,
                            'existing': {
                                'id': exp.id,
                                'date': exp.date.isoformat(),
                                'description': exp.description,
                                'amount': float(exp.amount),
                                'category': exp.category.name if exp.category else None
                            },
                            'similarity': round(overlap * 100, 0)
                        })
                        break
        except Exception as e:
            continue
    
    return jsonify({
        'success': True,
        'duplicates': duplicates,
        'duplicate_count': len(duplicates)
    })


@bp.route('/import', methods=['POST'])
@login_required
def import_transactions():
    """
    Import selected transactions into the database
    Security: Only imports to current user's account, validates all data
    """
    data = request.get_json()
    transactions = data.get('transactions', [])
    category_mapping = data.get('category_mapping', {})
    skip_duplicates = data.get('skip_duplicates', False)
    
    if not transactions:
        return jsonify({'success': False, 'error': 'No transactions to import'}), 400
    
    imported = []
    skipped = []
    errors = []
    
    # Security: Get user's categories
    user_categories = {cat.id: cat for cat in Category.query.filter_by(user_id=current_user.id).all()}
    
    if not user_categories:
        return jsonify({'success': False, 'error': 'No categories found. Please create categories first.'}), 400
    
    # Get default category
    default_category_id = list(user_categories.keys())[0]
    
    for idx, trans in enumerate(transactions):
        try:
            # Skip if marked as duplicate
            if skip_duplicates and trans.get('is_duplicate'):
                skipped.append({'transaction': trans, 'reason': 'Duplicate'})
                continue
            
            # Parse and validate data
            try:
                trans_date = datetime.fromisoformat(trans['date']).date()
            except (ValueError, KeyError) as e:
                errors.append({'transaction': trans, 'error': f'Invalid date: {trans.get("date", "missing")}'})
                continue
                
            try:
                amount = float(trans['amount'])
            except (ValueError, KeyError, TypeError) as e:
                errors.append({'transaction': trans, 'error': f'Invalid amount: {trans.get("amount", "missing")}'})
                continue
                
            description = trans.get('description', 'Transaction')
            
            # Security: Validate amount to prevent negative values and overflow attacks
            from app.utils import validate_amount
            is_valid, validated_amount, error_msg = validate_amount(amount, 'Amount')
            if not is_valid:
                errors.append({'transaction': trans, 'error': error_msg})
                continue
            amount = validated_amount
            
            # Get category ID from mapping or bank category
            category_id = None
            bank_category = trans.get('bank_category')
            
            # Try to get from explicit mapping
            if bank_category and bank_category in category_mapping:
                category_id = int(category_mapping[bank_category])
            elif str(idx) in category_mapping:
                category_id = int(category_mapping[str(idx)])
            else:
                category_id = default_category_id
            
            # Security: Verify category belongs to user
            if category_id not in user_categories:
                errors.append({'transaction': trans, 'error': f'Invalid category ID: {category_id}'})
                continue
            
            # Prepare tags with bank category if available
            tags = []
            if bank_category:
                tags.append(f'Import: {bank_category}')
            
            # Create expense
            expense = Expense(
                user_id=current_user.id,
                category_id=category_id,
                amount=amount,
                description=description,
                date=trans_date,
                currency=current_user.currency,
                tags=json.dumps(tags)
            )
            
            db.session.add(expense)
            imported.append({
                'date': trans_date.isoformat(),
                'description': description,
                'amount': amount,
                'category': user_categories[category_id].name
            })
            
        except Exception as e:
            errors.append({'transaction': trans, 'error': str(e)})
    
    # Commit all imports
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'imported_count': len(imported),
            'skipped_count': len(skipped),
            'error_count': len(errors),
            'imported': imported,
            'skipped': skipped,
            'errors': errors
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Database error: {str(e)}'}), 500


@bp.route('/create-categories', methods=['POST'])
@login_required
def create_categories():
    """
    Create missing categories from CSV bank categories
    Security: Only creates for current user
    """
    data = request.get_json()
    bank_categories = data.get('bank_categories', [])
    
    if not bank_categories:
        return jsonify({'success': False, 'error': 'No categories provided'}), 400
    
    # Get existing categories for user
    existing_cats = {cat.name.lower(): cat for cat in Category.query.filter_by(user_id=current_user.id).all()}
    
    created = []
    mapping = {}
    
    for bank_cat in bank_categories:
        if not bank_cat or not bank_cat.strip():
            continue
            
        bank_cat_clean = bank_cat.strip()
        bank_cat_lower = bank_cat_clean.lower()
        
        # Check if category already exists
        if bank_cat_lower in existing_cats:
            mapping[bank_cat] = existing_cats[bank_cat_lower].id
        else:
            # Create new category
            max_order = db.session.query(db.func.max(Category.display_order)).filter_by(user_id=current_user.id).scalar() or 0
            new_cat = Category(
                user_id=current_user.id,
                name=bank_cat_clean,
                icon='category',
                color='#' + format(hash(bank_cat_clean) % 0xFFFFFF, '06x'),  # Generate color from name
                display_order=max_order + 1
            )
            db.session.add(new_cat)
            db.session.flush()  # Get ID without committing
            
            created.append({
                'name': bank_cat_clean,
                'id': new_cat.id
            })
            mapping[bank_cat] = new_cat.id
            existing_cats[bank_cat_lower] = new_cat
    
    try:
        db.session.commit()
        return jsonify({
            'success': True,
            'created': created,
            'mapping': mapping,
            'message': f'Created {len(created)} new categories'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Failed to create categories: {str(e)}'}), 500


@bp.route('/suggest-category', methods=['POST'])
@login_required
def suggest_category():
    """
    Suggest category mapping based on description and existing expenses
    Uses simple keyword matching and historical patterns
    """
    data = request.get_json()
    description = data.get('description', '').lower()
    bank_category = data.get('bank_category', '').lower()
    
    if not description:
        return jsonify({'success': False, 'error': 'No description provided'}), 400
    
    # Security: Get only user's categories
    user_categories = Category.query.filter_by(user_id=current_user.id).all()
    
    # Look for similar expenses in user's history
    similar_expenses = Expense.query.filter(
        Expense.user_id == current_user.id
    ).order_by(Expense.date.desc()).limit(100).all()
    
    # Score categories based on keyword matching
    category_scores = {cat.id: 0 for cat in user_categories}
    
    for expense in similar_expenses:
        exp_desc = expense.description.lower()
        
        # Simple word matching
        desc_words = set(description.split())
        exp_words = set(exp_desc.split())
        overlap = len(desc_words.intersection(exp_words))
        
        if overlap > 0:
            category_scores[expense.category_id] += overlap
    
    # Get best match
    if max(category_scores.values()) > 0:
        best_category_id = max(category_scores, key=category_scores.get)
        best_category = next(cat for cat in user_categories if cat.id == best_category_id)
        
        return jsonify({
            'success': True,
            'suggested_category_id': best_category.id,
            'suggested_category_name': best_category.name,
            'confidence': min(100, category_scores[best_category_id] * 20)
        })
    
    # No match found, return first category
    return jsonify({
        'success': True,
        'suggested_category_id': user_categories[0].id,
        'suggested_category_name': user_categories[0].name,
        'confidence': 0
    })
