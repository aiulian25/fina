"""
Backup and Restore Routes for FINA
Allows users to export all their data and import from a backup
"""
from flask import Blueprint, request, jsonify, Response
from flask_login import login_required, current_user
from app import db
from app.models import (
    User, Category, Expense, Income, Document, RecurringExpense,
    Tag, SavingsGoal, Challenge
)
from datetime import datetime
import json

bp = Blueprint('backup', __name__, url_prefix='/api/backup')


def serialize_datetime(obj):
    """JSON serializer for datetime objects"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


@bp.route('/export', methods=['GET'])
@login_required
def export_data():
    """
    Export all user data as JSON file
    Includes: categories, expenses, income, recurring expenses, tags, goals, challenges
    """
    try:
        # Collect all user data
        backup_data = {
            'version': '1.0',
            'app': 'FINA',
            'exported_at': datetime.utcnow().isoformat(),
            'user': {
                'username': current_user.username,
                'email': current_user.email,
                'currency': current_user.currency,
                'language': current_user.language,
                'monthly_budget': current_user.monthly_budget
            },
            'categories': [],
            'expenses': [],
            'income': [],
            'recurring_expenses': [],
            'tags': [],
            'savings_goals': [],
            'challenges': []
        }
        
        # Export categories
        categories = Category.query.filter_by(user_id=current_user.id).all()
        category_map = {}  # Map old IDs to category names for reference
        for cat in categories:
            category_map[cat.id] = cat.name
            backup_data['categories'].append({
                'name': cat.name,
                'color': cat.color,
                'icon': cat.icon,
                'display_order': cat.display_order,
                'monthly_budget': cat.monthly_budget,
                'budget_alert_threshold': cat.budget_alert_threshold,
                'created_at': cat.created_at.isoformat() if cat.created_at else None
            })
        
        # Export expenses
        expenses = Expense.query.filter_by(user_id=current_user.id).all()
        for exp in expenses:
            expense_data = {
                'amount': exp.amount,
                'currency': exp.currency,
                'description': exp.description,
                'category_name': category_map.get(exp.category_id, 'Uncategorized'),
                'tags': exp.get_tags(),
                'date': exp.date.isoformat() if exp.date else None,
                'created_at': exp.created_at.isoformat() if exp.created_at else None
            }
            # Get tag names from tag objects
            try:
                tag_names = [t.name for t in exp.get_tag_objects()]
                if tag_names:
                    expense_data['tag_names'] = tag_names
            except:
                pass
            backup_data['expenses'].append(expense_data)
        
        # Export income
        income_records = Income.query.filter_by(user_id=current_user.id).all()
        for inc in income_records:
            backup_data['income'].append({
                'amount': inc.amount,
                'currency': inc.currency,
                'description': inc.description,
                'source': inc.source,
                'tags': inc.get_tags(),
                'frequency': inc.frequency,
                'custom_days': inc.custom_days,
                'next_due_date': inc.next_due_date.isoformat() if inc.next_due_date else None,
                'is_active': inc.is_active,
                'auto_create': inc.auto_create,
                'date': inc.date.isoformat() if inc.date else None,
                'created_at': inc.created_at.isoformat() if inc.created_at else None
            })
        
        # Export recurring expenses
        recurring = RecurringExpense.query.filter_by(user_id=current_user.id).all()
        for rec in recurring:
            backup_data['recurring_expenses'].append({
                'name': rec.name,
                'amount': rec.amount,
                'currency': rec.currency,
                'category_name': category_map.get(rec.category_id, 'Uncategorized'),
                'frequency': rec.frequency,
                'day_of_period': rec.day_of_period,
                'next_due_date': rec.next_due_date.isoformat() if rec.next_due_date else None,
                'auto_create': rec.auto_create,
                'is_active': rec.is_active,
                'notes': rec.notes,
                'is_subscription': rec.is_subscription,
                'service_name': rec.service_name,
                'reminder_days': rec.reminder_days,
                'created_at': rec.created_at.isoformat() if rec.created_at else None
            })
        
        # Export tags
        try:
            tags = Tag.query.filter_by(user_id=current_user.id).all()
            for tag in tags:
                backup_data['tags'].append({
                    'name': tag.name,
                    'color': tag.color,
                    'icon': tag.icon,
                    'use_count': tag.use_count,
                    'auto_apply_keywords': tag.auto_apply_keywords,
                    'created_at': tag.created_at.isoformat() if tag.created_at else None
                })
        except Exception:
            pass  # Tags might not exist
        
        # Export savings goals
        try:
            goals = SavingsGoal.query.filter_by(user_id=current_user.id).all()
            for goal in goals:
                backup_data['savings_goals'].append({
                    'name': goal.name,
                    'target_amount': goal.target_amount,
                    'current_amount': goal.current_amount,
                    'currency': goal.currency,
                    'deadline': goal.deadline.isoformat() if goal.deadline else None,
                    'icon': goal.icon,
                    'color': goal.color,
                    'notes': goal.notes,
                    'is_completed': goal.is_completed,
                    'created_at': goal.created_at.isoformat() if goal.created_at else None
                })
        except Exception:
            pass  # Goals might not exist
        
        # Generate filename
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        filename = f"fina_backup_{current_user.username}_{timestamp}.json"
        
        # Return as downloadable file
        json_data = json.dumps(backup_data, indent=2, default=serialize_datetime)
        
        return Response(
            json_data,
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment; filename={filename}',
                'Content-Type': 'application/json'
            }
        )
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/import', methods=['POST'])
@login_required
def import_data():
    """
    Import user data from a backup JSON file
    Options: 
    - merge: Add new data without deleting existing
    - replace: Delete existing data and replace with backup
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if not file.filename.endswith('.json'):
            return jsonify({'success': False, 'error': 'File must be a JSON file'}), 400
        
        # Get import mode (merge or replace)
        mode = request.form.get('mode', 'merge')
        if mode not in ['merge', 'replace']:
            mode = 'merge'
        
        # Parse JSON file
        try:
            backup_data = json.loads(file.read().decode('utf-8'))
        except json.JSONDecodeError as e:
            return jsonify({'success': False, 'error': f'Invalid JSON file: {str(e)}'}), 400
        
        # Validate backup file
        if backup_data.get('app') != 'FINA':
            return jsonify({'success': False, 'error': 'Invalid backup file format'}), 400
        
        stats = {
            'categories': 0,
            'expenses': 0,
            'income': 0,
            'recurring_expenses': 0,
            'tags': 0,
            'savings_goals': 0,
            'skipped': 0
        }
        
        # If replace mode, delete existing data
        if mode == 'replace':
            # Delete in order to respect foreign keys
            Expense.query.filter_by(user_id=current_user.id).delete()
            Income.query.filter_by(user_id=current_user.id).delete()
            RecurringExpense.query.filter_by(user_id=current_user.id).delete()
            try:
                Tag.query.filter_by(user_id=current_user.id).delete()
            except:
                pass
            try:
                SavingsGoal.query.filter_by(user_id=current_user.id).delete()
            except:
                pass
            Category.query.filter_by(user_id=current_user.id).delete()
            db.session.commit()
        
        # Import categories first (needed for expense references)
        category_name_to_id = {}
        existing_categories = {c.name.lower(): c for c in Category.query.filter_by(user_id=current_user.id).all()}
        
        for cat_data in backup_data.get('categories', []):
            cat_name = cat_data.get('name', '').strip()
            if not cat_name:
                continue
            
            # Check if category exists (case-insensitive)
            if cat_name.lower() in existing_categories:
                category_name_to_id[cat_name] = existing_categories[cat_name.lower()].id
                stats['skipped'] += 1
                continue
            
            # Create new category
            cat = Category(
                name=cat_name,
                color=cat_data.get('color', '#2b8cee'),
                icon=cat_data.get('icon', 'category'),
                display_order=cat_data.get('display_order', 0),
                monthly_budget=cat_data.get('monthly_budget'),
                budget_alert_threshold=cat_data.get('budget_alert_threshold', 0.9),
                user_id=current_user.id
            )
            db.session.add(cat)
            db.session.flush()  # Get the ID
            category_name_to_id[cat_name] = cat.id
            existing_categories[cat_name.lower()] = cat
            stats['categories'] += 1
        
        # Import tags
        tag_name_to_id = {}
        try:
            existing_tags = {t.name.lower(): t for t in Tag.query.filter_by(user_id=current_user.id).all()}
            
            for tag_data in backup_data.get('tags', []):
                tag_name = tag_data.get('name', '').strip()
                if not tag_name:
                    continue
                
                if tag_name.lower() in existing_tags:
                    tag_name_to_id[tag_name] = existing_tags[tag_name.lower()].id
                    stats['skipped'] += 1
                    continue
                
                tag = Tag(
                    name=tag_name,
                    color=tag_data.get('color', '#2b8cee'),
                    icon=tag_data.get('icon'),
                    use_count=tag_data.get('use_count', 0),
                    auto_apply_keywords=tag_data.get('auto_apply_keywords'),
                    user_id=current_user.id
                )
                db.session.add(tag)
                db.session.flush()
                tag_name_to_id[tag_name] = tag.id
                existing_tags[tag_name.lower()] = tag
                stats['tags'] += 1
        except Exception:
            pass  # Tags model might not exist
        
        # Get default category for uncategorized items
        default_category = Category.query.filter_by(user_id=current_user.id).first()
        if not default_category:
            default_category = Category(
                name='Uncategorized',
                color='#6b7280',
                icon='category',
                user_id=current_user.id
            )
            db.session.add(default_category)
            db.session.flush()
            category_name_to_id['Uncategorized'] = default_category.id
        
        # Import expenses
        for exp_data in backup_data.get('expenses', []):
            cat_name = exp_data.get('category_name', 'Uncategorized')
            cat_id = category_name_to_id.get(cat_name) or existing_categories.get(cat_name.lower(), {})
            if isinstance(cat_id, Category):
                cat_id = cat_id.id
            if not cat_id:
                cat_id = default_category.id
            
            exp = Expense(
                amount=float(exp_data.get('amount', 0)),
                currency=exp_data.get('currency', current_user.currency),
                description=exp_data.get('description', 'Imported expense'),
                category_id=cat_id,
                user_id=current_user.id,
                tags=json.dumps(exp_data.get('tags', [])),
                date=datetime.fromisoformat(exp_data['date']) if exp_data.get('date') else datetime.utcnow()
            )
            db.session.add(exp)
            stats['expenses'] += 1
        
        # Import income
        for inc_data in backup_data.get('income', []):
            inc = Income(
                amount=float(inc_data.get('amount', 0)),
                currency=inc_data.get('currency', current_user.currency),
                description=inc_data.get('description', 'Imported income'),
                source=inc_data.get('source', 'Other'),
                user_id=current_user.id,
                tags=json.dumps(inc_data.get('tags', [])),
                frequency=inc_data.get('frequency', 'once'),
                custom_days=inc_data.get('custom_days'),
                is_active=inc_data.get('is_active', True),
                auto_create=inc_data.get('auto_create', False),
                date=datetime.fromisoformat(inc_data['date']) if inc_data.get('date') else datetime.utcnow()
            )
            if inc_data.get('next_due_date'):
                inc.next_due_date = datetime.fromisoformat(inc_data['next_due_date'])
            db.session.add(inc)
            stats['income'] += 1
        
        # Import recurring expenses
        for rec_data in backup_data.get('recurring_expenses', []):
            cat_name = rec_data.get('category_name', 'Uncategorized')
            cat_id = category_name_to_id.get(cat_name) or existing_categories.get(cat_name.lower(), {})
            if isinstance(cat_id, Category):
                cat_id = cat_id.id
            if not cat_id:
                cat_id = default_category.id
            
            rec = RecurringExpense(
                name=rec_data.get('name', 'Imported recurring'),
                amount=float(rec_data.get('amount', 0)),
                currency=rec_data.get('currency', current_user.currency),
                category_id=cat_id,
                frequency=rec_data.get('frequency', 'monthly'),
                day_of_period=rec_data.get('day_of_period'),
                next_due_date=datetime.fromisoformat(rec_data['next_due_date']) if rec_data.get('next_due_date') else datetime.utcnow(),
                auto_create=rec_data.get('auto_create', False),
                is_active=rec_data.get('is_active', True),
                notes=rec_data.get('notes'),
                is_subscription=rec_data.get('is_subscription', False),
                service_name=rec_data.get('service_name'),
                reminder_days=rec_data.get('reminder_days', 3),
                user_id=current_user.id
            )
            db.session.add(rec)
            stats['recurring_expenses'] += 1
        
        # Import savings goals
        try:
            for goal_data in backup_data.get('savings_goals', []):
                goal = SavingsGoal(
                    name=goal_data.get('name', 'Imported goal'),
                    target_amount=float(goal_data.get('target_amount', 0)),
                    current_amount=float(goal_data.get('current_amount', 0)),
                    currency=goal_data.get('currency', current_user.currency),
                    icon=goal_data.get('icon', 'savings'),
                    color=goal_data.get('color', '#2b8cee'),
                    notes=goal_data.get('notes'),
                    is_completed=goal_data.get('is_completed', False),
                    user_id=current_user.id
                )
                if goal_data.get('deadline'):
                    goal.deadline = datetime.fromisoformat(goal_data['deadline'])
                db.session.add(goal)
                stats['savings_goals'] += 1
        except Exception:
            pass  # Goals model might not exist
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Backup imported successfully',
            'stats': stats
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route('/preview', methods=['POST'])
@login_required
def preview_import():
    """
    Preview what will be imported from a backup file without actually importing
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400
        
        file = request.files['file']
        if not file.filename.endswith('.json'):
            return jsonify({'success': False, 'error': 'File must be a JSON file'}), 400
        
        # Parse JSON file
        try:
            backup_data = json.loads(file.read().decode('utf-8'))
        except json.JSONDecodeError as e:
            return jsonify({'success': False, 'error': f'Invalid JSON file: {str(e)}'}), 400
        
        # Validate backup file
        if backup_data.get('app') != 'FINA':
            return jsonify({'success': False, 'error': 'Invalid backup file format'}), 400
        
        # Gather preview info
        preview = {
            'version': backup_data.get('version', 'Unknown'),
            'exported_at': backup_data.get('exported_at', 'Unknown'),
            'original_user': backup_data.get('user', {}).get('username', 'Unknown'),
            'counts': {
                'categories': len(backup_data.get('categories', [])),
                'expenses': len(backup_data.get('expenses', [])),
                'income': len(backup_data.get('income', [])),
                'recurring_expenses': len(backup_data.get('recurring_expenses', [])),
                'tags': len(backup_data.get('tags', [])),
                'savings_goals': len(backup_data.get('savings_goals', [])),
                'challenges': len(backup_data.get('challenges', []))
            },
            'totals': {
                'expenses': sum(e.get('amount', 0) for e in backup_data.get('expenses', [])),
                'income': sum(i.get('amount', 0) for i in backup_data.get('income', []))
            }
        }
        
        return jsonify({
            'success': True,
            'preview': preview
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
