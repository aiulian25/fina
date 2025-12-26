"""
Global Search API
Provides unified search across all app content and features
Security: All searches filtered by user_id to prevent data leakage
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.models import Expense, Document, Category, RecurringExpense, Tag
from sqlalchemy import or_, func
from datetime import datetime

bp = Blueprint('search', __name__, url_prefix='/api/search')

# App features/pages for navigation
APP_FEATURES = [
    {
        'id': 'dashboard',
        'name': 'Dashboard',
        'name_ro': 'Tablou de bord',
        'description': 'View your financial overview',
        'description_ro': 'Vezi prezentarea generală financiară',
        'icon': 'dashboard',
        'url': '/dashboard',
        'keywords': ['dashboard', 'tablou', 'bord', 'overview', 'home', 'start']
    },
    {
        'id': 'transactions',
        'name': 'Transactions',
        'name_ro': 'Tranzacții',
        'description': 'Manage your expenses and transactions',
        'description_ro': 'Gestionează cheltuielile și tranzacțiile',
        'icon': 'receipt_long',
        'url': '/transactions',
        'keywords': ['transactions', 'tranzactii', 'expenses', 'cheltuieli', 'spending']
    },
    {
        'id': 'recurring',
        'name': 'Recurring Expenses',
        'name_ro': 'Cheltuieli recurente',
        'description': 'Manage subscriptions and recurring bills',
        'description_ro': 'Gestionează abonamente și facturi recurente',
        'icon': 'repeat',
        'url': '/recurring',
        'keywords': ['recurring', 'recurente', 'subscriptions', 'abonamente', 'bills', 'facturi', 'monthly']
    },
    {
        'id': 'reports',
        'name': 'Reports',
        'name_ro': 'Rapoarte',
        'description': 'View detailed financial reports',
        'description_ro': 'Vezi rapoarte financiare detaliate',
        'icon': 'analytics',
        'url': '/reports',
        'keywords': ['reports', 'rapoarte', 'analytics', 'analize', 'statistics', 'statistici']
    },
    {
        'id': 'documents',
        'name': 'Documents',
        'name_ro': 'Documente',
        'description': 'Upload and manage your documents',
        'description_ro': 'Încarcă și gestionează documentele',
        'icon': 'description',
        'url': '/documents',
        'keywords': ['documents', 'documente', 'files', 'fisiere', 'upload', 'receipts', 'chitante']
    },
    {
        'id': 'settings',
        'name': 'Settings',
        'name_ro': 'Setări',
        'description': 'Configure your account settings',
        'description_ro': 'Configurează setările contului',
        'icon': 'settings',
        'url': '/settings',
        'keywords': ['settings', 'setari', 'preferences', 'preferinte', 'account', 'cont', 'profile', 'profil']
    }
]

# Admin-only features
ADMIN_FEATURES = [
    {
        'id': 'admin',
        'name': 'Admin Panel',
        'name_ro': 'Panou Admin',
        'description': 'Manage users and system settings',
        'description_ro': 'Gestionează utilizatori și setări sistem',
        'icon': 'admin_panel_settings',
        'url': '/admin',
        'keywords': ['admin', 'administration', 'users', 'utilizatori', 'system', 'sistem']
    }
]


@bp.route('/', methods=['GET'])
@login_required
def global_search():
    """
    Global search across all content and app features
    Security: All data searches filtered by current_user.id
    
    Query params:
    - q: Search query string
    - limit: Max results per category (default 5)
    
    Returns:
    - features: Matching app features/pages
    - expenses: Matching expenses (by description or OCR text)
    - documents: Matching documents (by filename or OCR text)
    - categories: Matching categories
    - recurring: Matching recurring expenses
    """
    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 5, type=int)
    
    if not query or len(query) < 2:
        return jsonify({
            'success': False,
            'message': 'Query must be at least 2 characters'
        }), 400
    
    results = {
        'features': [],
        'expenses': [],
        'documents': [],
        'categories': [],
        'recurring': [],
        'tags': []
    }
    
    # Search app features
    query_lower = query.lower()
    for feature in APP_FEATURES:
        # Check if query matches any keyword
        if any(query_lower in keyword.lower() for keyword in feature['keywords']):
            results['features'].append({
                'id': feature['id'],
                'type': 'feature',
                'name': feature['name'],
                'name_ro': feature['name_ro'],
                'description': feature['description'],
                'description_ro': feature['description_ro'],
                'icon': feature['icon'],
                'url': feature['url']
            })
    
    # Add admin features if user is admin
    if current_user.is_admin:
        for feature in ADMIN_FEATURES:
            if any(query_lower in keyword.lower() for keyword in feature['keywords']):
                results['features'].append({
                    'id': feature['id'],
                    'type': 'feature',
                    'name': feature['name'],
                    'name_ro': feature['name_ro'],
                    'description': feature['description'],
                    'description_ro': feature['description_ro'],
                    'icon': feature['icon'],
                    'url': feature['url']
                })
    
    # Search expenses - Security: filter by user_id
    expense_query = Expense.query.filter_by(user_id=current_user.id)
    expense_query = expense_query.filter(
        or_(
            Expense.description.ilike(f'%{query}%'),
            Expense.receipt_ocr_text.ilike(f'%{query}%')
        )
    )
    expenses = expense_query.order_by(Expense.date.desc()).limit(limit).all()
    
    for expense in expenses:
        # Check if match is from OCR text
        ocr_match = expense.receipt_ocr_text and query_lower in expense.receipt_ocr_text.lower()
        
        results['expenses'].append({
            'id': expense.id,
            'type': 'expense',
            'description': expense.description,
            'amount': expense.amount,
            'currency': expense.currency,
            'category_name': expense.category.name if expense.category else None,
            'category_color': expense.category.color if expense.category else None,
            'date': expense.date.isoformat(),
            'has_receipt': bool(expense.receipt_path),
            'ocr_match': ocr_match,
            'url': '/transactions'
        })
    
    # Search documents - Security: filter by user_id
    doc_query = Document.query.filter_by(user_id=current_user.id)
    doc_query = doc_query.filter(
        or_(
            Document.original_filename.ilike(f'%{query}%'),
            Document.ocr_text.ilike(f'%{query}%')
        )
    )
    documents = doc_query.order_by(Document.created_at.desc()).limit(limit).all()
    
    for doc in documents:
        # Check if match is from OCR text
        ocr_match = doc.ocr_text and query_lower in doc.ocr_text.lower()
        
        results['documents'].append({
            'id': doc.id,
            'type': 'document',
            'filename': doc.original_filename,
            'file_type': doc.file_type,
            'file_size': doc.file_size,
            'category': doc.document_category,
            'created_at': doc.created_at.isoformat(),
            'ocr_match': ocr_match,
            'url': '/documents'
        })
    
    # Search categories - Security: filter by user_id
    categories = Category.query.filter_by(user_id=current_user.id).filter(
        Category.name.ilike(f'%{query}%')
    ).order_by(Category.display_order).limit(limit).all()
    
    for category in categories:
        results['categories'].append({
            'id': category.id,
            'type': 'category',
            'name': category.name,
            'color': category.color,
            'icon': category.icon,
            'url': '/transactions'
        })
    
    # Search recurring expenses - Security: filter by user_id
    recurring = RecurringExpense.query.filter_by(user_id=current_user.id).filter(
        or_(
            RecurringExpense.name.ilike(f'%{query}%'),
            RecurringExpense.notes.ilike(f'%{query}%')
        )
    ).order_by(RecurringExpense.next_due_date).limit(limit).all()
    
    for rec in recurring:
        results['recurring'].append({
            'id': rec.id,
            'type': 'recurring',
            'name': rec.name,
            'amount': rec.amount,
            'currency': rec.currency,
            'frequency': rec.frequency,
            'category_name': rec.category.name if rec.category else None,
            'category_color': rec.category.color if rec.category else None,
            'next_due_date': rec.next_due_date.isoformat(),
            'is_active': rec.is_active,
            'url': '/recurring'
        })
    
    # Search tags
    # Security: Filtered by user_id
    tags = Tag.query.filter(
        Tag.user_id == current_user.id,
        Tag.name.ilike(f'%{query}%')
    ).limit(limit).all()
    
    for tag in tags:
        results['tags'].append({
            'id': tag.id,
            'type': 'tag',
            'name': tag.name,
            'color': tag.color,
            'icon': tag.icon,
            'use_count': tag.use_count,
            'is_auto': tag.is_auto
        })
    
    # Calculate total results
    total_results = sum([
        len(results['features']),
        len(results['expenses']),
        len(results['documents']),
        len(results['categories']),
        len(results['recurring']),
        len(results['tags'])
    ])
    
    return jsonify({
        'success': True,
        'query': query,
        'total_results': total_results,
        'results': results
    })
