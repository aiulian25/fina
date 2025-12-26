from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.subscription import Subscription, RecurringPattern
from app.models.category import Category
from app.smart_detection import (
    detect_recurring_expenses, 
    save_detected_patterns, 
    get_user_suggestions,
    convert_pattern_to_subscription,
    dismiss_pattern
)
from datetime import datetime, timedelta

bp = Blueprint('subscriptions', __name__, url_prefix='/subscriptions')

@bp.route('/')
@login_required
def index():
    """View all subscriptions and suggestions"""
    subscriptions = Subscription.query.filter_by(
        user_id=current_user.id,
        is_active=True
    ).order_by(Subscription.next_due_date).all()
    
    suggestions = get_user_suggestions(current_user.id)
    
    # Calculate total monthly cost
    monthly_cost = sum(
        sub.amount if sub.frequency == 'monthly' else
        sub.amount / 4 if sub.frequency == 'quarterly' else
        sub.amount / 12 if sub.frequency == 'yearly' else
        sub.amount * 4 if sub.frequency == 'weekly' else
        sub.amount * 2 if sub.frequency == 'biweekly' else
        sub.amount
        for sub in subscriptions
    )
    
    yearly_cost = sum(sub.get_annual_cost() for sub in subscriptions)
    
    return render_template('subscriptions/index.html',
                         subscriptions=subscriptions,
                         suggestions=suggestions,
                         monthly_cost=monthly_cost,
                         yearly_cost=yearly_cost)


@bp.route('/detect', methods=['POST'])
@login_required
def detect():
    """Run detection algorithm to find recurring expenses"""
    patterns = detect_recurring_expenses(current_user.id)
    
    if patterns:
        saved = save_detected_patterns(patterns)
        flash(f'Found {saved} potential subscription(s)!', 'success')
    else:
        flash('No recurring patterns detected. Add more expenses to improve detection.', 'info')
    
    return redirect(url_for('subscriptions.index'))


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Manually create a subscription"""
    if request.method == 'POST':
        name = request.form.get('name')
        amount = float(request.form.get('amount', 0))
        frequency = request.form.get('frequency')
        custom_interval_days = request.form.get('custom_interval_days')
        category_id = request.form.get('category_id')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')
        total_occurrences = request.form.get('total_occurrences')
        auto_create_expense = request.form.get('auto_create_expense') == 'on'
        notes = request.form.get('notes')
        
        # Validate custom interval
        if frequency == 'custom':
            if not custom_interval_days:
                flash('Custom interval is required when using custom frequency', 'error')
                categories = Category.query.filter_by(user_id=current_user.id).all()
                return render_template('subscriptions/create.html', categories=categories)
            
            interval_value = int(custom_interval_days)
            if interval_value < 1 or interval_value > 365:
                flash('Custom interval must be between 1 and 365 days', 'error')
                categories = Category.query.filter_by(user_id=current_user.id).all()
                return render_template('subscriptions/create.html', categories=categories)
        
        # Parse dates
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else datetime.now().date()
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        
        subscription = Subscription(
            name=name,
            amount=amount,
            frequency=frequency,
            custom_interval_days=int(custom_interval_days) if custom_interval_days and frequency == 'custom' else None,
            category_id=category_id,
            user_id=current_user.id,
            start_date=start_date_obj,
            next_due_date=start_date_obj,
            end_date=end_date_obj,
            total_occurrences=int(total_occurrences) if total_occurrences else None,
            auto_create_expense=auto_create_expense,
            notes=notes,
            is_confirmed=True,
            auto_detected=False
        )
        
        db.session.add(subscription)
        db.session.commit()
        
        flash(f'Subscription "{name}" added successfully!', 'success')
        return redirect(url_for('subscriptions.index'))
    
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('subscriptions/create.html', categories=categories)


@bp.route('/<int:subscription_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(subscription_id):
    """Edit a subscription"""
    subscription = Subscription.query.filter_by(
        id=subscription_id,
        user_id=current_user.id
    ).first_or_404()
    
    if request.method == 'POST':
        frequency = request.form.get('frequency')
        custom_interval_days = request.form.get('custom_interval_days')
        
        # Validate custom interval
        if frequency == 'custom':
            if not custom_interval_days:
                flash('Custom interval is required when using custom frequency', 'error')
                categories = Category.query.filter_by(user_id=current_user.id).all()
                return render_template('subscriptions/edit.html', subscription=subscription, categories=categories)
            
            interval_value = int(custom_interval_days)
            if interval_value < 1 or interval_value > 365:
                flash('Custom interval must be between 1 and 365 days', 'error')
                categories = Category.query.filter_by(user_id=current_user.id).all()
                return render_template('subscriptions/edit.html', subscription=subscription, categories=categories)
        
        subscription.name = request.form.get('name')
        subscription.amount = float(request.form.get('amount', 0))
        subscription.frequency = frequency
        subscription.custom_interval_days = int(custom_interval_days) if custom_interval_days and frequency == 'custom' else None
        subscription.category_id = request.form.get('category_id')
        subscription.auto_create_expense = request.form.get('auto_create_expense') == 'on'
        subscription.notes = request.form.get('notes')
        
        next_due_date = request.form.get('next_due_date')
        if next_due_date:
            subscription.next_due_date = datetime.strptime(next_due_date, '%Y-%m-%d').date()
        
        end_date = request.form.get('end_date')
        subscription.end_date = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        
        total_occurrences = request.form.get('total_occurrences')
        subscription.total_occurrences = int(total_occurrences) if total_occurrences else None
        
        db.session.commit()
        
        flash(f'Subscription "{subscription.name}" updated!', 'success')
        return redirect(url_for('subscriptions.index'))
    
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('subscriptions/edit.html', 
                         subscription=subscription, 
                         categories=categories)


@bp.route('/<int:subscription_id>/delete', methods=['POST'])
@login_required
def delete(subscription_id):
    """Delete a subscription"""
    subscription = Subscription.query.filter_by(
        id=subscription_id,
        user_id=current_user.id
    ).first_or_404()
    
    name = subscription.name
    db.session.delete(subscription)
    db.session.commit()
    
    flash(f'Subscription "{name}" deleted!', 'success')
    return redirect(url_for('subscriptions.index'))


@bp.route('/<int:subscription_id>/toggle', methods=['POST'])
@login_required
def toggle(subscription_id):
    """Toggle subscription active status"""
    subscription = Subscription.query.filter_by(
        id=subscription_id,
        user_id=current_user.id
    ).first_or_404()
    
    subscription.is_active = not subscription.is_active
    db.session.commit()
    
    status = 'activated' if subscription.is_active else 'paused'
    flash(f'Subscription "{subscription.name}" {status}!', 'success')
    
    return redirect(url_for('subscriptions.index'))


@bp.route('/suggestion/<int:pattern_id>/accept', methods=['POST'])
@login_required
def accept_suggestion(pattern_id):
    """Accept a detected pattern and convert to subscription"""
    subscription = convert_pattern_to_subscription(pattern_id, current_user.id)
    
    if subscription:
        flash(f'Subscription "{subscription.name}" added!', 'success')
    else:
        flash('Could not add subscription.', 'error')
    
    return redirect(url_for('subscriptions.index'))


@bp.route('/suggestion/<int:pattern_id>/dismiss', methods=['POST'])
@login_required
def dismiss_suggestion(pattern_id):
    """Dismiss a detected pattern"""
    if dismiss_pattern(pattern_id, current_user.id):
        flash('Suggestion dismissed.', 'info')
    else:
        flash('Could not dismiss suggestion.', 'error')
    
    return redirect(url_for('subscriptions.index'))


@bp.route('/api/upcoming')
@login_required
def api_upcoming():
    """API endpoint for upcoming subscriptions"""
    days = int(request.args.get('days', 30))
    
    end_date = datetime.now().date() + timedelta(days=days)
    
    upcoming = Subscription.query.filter(
        Subscription.user_id == current_user.id,
        Subscription.is_active == True,
        Subscription.next_due_date <= end_date
    ).order_by(Subscription.next_due_date).all()
    
    return jsonify({
        'subscriptions': [{
            'id': sub.id,
            'name': sub.name,
            'amount': float(sub.amount),
            'next_due_date': sub.next_due_date.isoformat(),
            'days_until': (sub.next_due_date - datetime.now().date()).days
        } for sub in upcoming]
    })


@bp.route('/auto-create', methods=['POST'])
@login_required
def auto_create_expenses():
    """Auto-create expenses for due subscriptions (can be run via cron)"""
    from app.models.category import Expense
    
    subscriptions = Subscription.query.filter_by(
        user_id=current_user.id,
        is_active=True,
        auto_create_expense=True
    ).all()
    
    created_count = 0
    
    for sub in subscriptions:
        if sub.should_create_expense_today():
            # Create the expense
            expense = Expense(
                amount=sub.amount,
                description=f"{sub.name} (Auto-created)",
                date=datetime.now().date(),
                category_id=sub.category_id,
                user_id=current_user.id
            )
            
            db.session.add(expense)
            
            # Update subscription
            sub.last_auto_created = datetime.now().date()
            sub.advance_next_due_date()
            
            created_count += 1
    
    db.session.commit()
    
    if created_count > 0:
        flash(f'Auto-created {created_count} expense(s) from subscriptions!', 'success')
    else:
        flash('No expenses due for auto-creation today.', 'info')
    
    return redirect(url_for('subscriptions.index'))
