"""
Subscription Detector API Routes
Features:
- Auto-detect recurring subscription charges
- Show total monthly subscription cost
- Flag unused/forgotten subscriptions
- Renewal date reminders
Security: All queries filtered by current_user.id
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import RecurringExpense, Expense, Category
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict
import re

bp = Blueprint('subscriptions', __name__, url_prefix='/api/subscriptions')

# Known subscription services with their patterns and icons
SUBSCRIPTION_SERVICES = {
    'netflix': {
        'patterns': ['netflix', 'nflx'],
        'icon': 'movie',
        'color': '#E50914',
        'category': 'Entertainment'
    },
    'spotify': {
        'patterns': ['spotify'],
        'icon': 'music_note',
        'color': '#1DB954',
        'category': 'Entertainment'
    },
    'amazon_prime': {
        'patterns': ['amazon prime', 'prime video', 'prime membership', 'amzn prime'],
        'icon': 'shopping_bag',
        'color': '#FF9900',
        'category': 'Entertainment'
    },
    'disney_plus': {
        'patterns': ['disney+', 'disney plus', 'disneyplus'],
        'icon': 'castle',
        'color': '#113CCF',
        'category': 'Entertainment'
    },
    'hbo_max': {
        'patterns': ['hbo max', 'hbo', 'max streaming'],
        'icon': 'live_tv',
        'color': '#5822B4',
        'category': 'Entertainment'
    },
    'apple_music': {
        'patterns': ['apple music', 'itunes music'],
        'icon': 'music_note',
        'color': '#FA243C',
        'category': 'Entertainment'
    },
    'apple_tv': {
        'patterns': ['apple tv', 'apple tv+'],
        'icon': 'tv',
        'color': '#000000',
        'category': 'Entertainment'
    },
    'apple_one': {
        'patterns': ['apple one'],
        'icon': 'apps',
        'color': '#000000',
        'category': 'Entertainment'
    },
    'youtube_premium': {
        'patterns': ['youtube premium', 'youtube music', 'yt premium'],
        'icon': 'play_circle',
        'color': '#FF0000',
        'category': 'Entertainment'
    },
    'hulu': {
        'patterns': ['hulu'],
        'icon': 'smart_display',
        'color': '#1CE783',
        'category': 'Entertainment'
    },
    'paramount_plus': {
        'patterns': ['paramount+', 'paramount plus', 'cbs all access'],
        'icon': 'movie',
        'color': '#0064FF',
        'category': 'Entertainment'
    },
    'peacock': {
        'patterns': ['peacock', 'nbc peacock'],
        'icon': 'smart_display',
        'color': '#000000',
        'category': 'Entertainment'
    },
    'crunchyroll': {
        'patterns': ['crunchyroll'],
        'icon': 'animation',
        'color': '#F47521',
        'category': 'Entertainment'
    },
    'xbox_game_pass': {
        'patterns': ['xbox game pass', 'game pass', 'xbox live'],
        'icon': 'sports_esports',
        'color': '#107C10',
        'category': 'Entertainment'
    },
    'playstation_plus': {
        'patterns': ['playstation plus', 'ps plus', 'psn', 'playstation network'],
        'icon': 'sports_esports',
        'color': '#003791',
        'category': 'Entertainment'
    },
    'nintendo_online': {
        'patterns': ['nintendo online', 'nintendo switch online'],
        'icon': 'sports_esports',
        'color': '#E60012',
        'category': 'Entertainment'
    },
    'adobe': {
        'patterns': ['adobe', 'creative cloud', 'photoshop', 'illustrator', 'premiere'],
        'icon': 'design_services',
        'color': '#FF0000',
        'category': 'Software'
    },
    'microsoft_365': {
        'patterns': ['microsoft 365', 'office 365', 'microsoft office', 'ms office'],
        'icon': 'description',
        'color': '#D83B01',
        'category': 'Software'
    },
    'google_one': {
        'patterns': ['google one', 'google storage', 'google drive storage'],
        'icon': 'cloud',
        'color': '#4285F4',
        'category': 'Software'
    },
    'dropbox': {
        'patterns': ['dropbox'],
        'icon': 'cloud',
        'color': '#0061FF',
        'category': 'Software'
    },
    'icloud': {
        'patterns': ['icloud', 'icloud storage', 'icloud+'],
        'icon': 'cloud',
        'color': '#3693F3',
        'category': 'Software'
    },
    'notion': {
        'patterns': ['notion'],
        'icon': 'edit_note',
        'color': '#000000',
        'category': 'Software'
    },
    'slack': {
        'patterns': ['slack'],
        'icon': 'chat',
        'color': '#4A154B',
        'category': 'Software'
    },
    'zoom': {
        'patterns': ['zoom'],
        'icon': 'videocam',
        'color': '#2D8CFF',
        'category': 'Software'
    },
    'github': {
        'patterns': ['github'],
        'icon': 'code',
        'color': '#181717',
        'category': 'Software'
    },
    'chatgpt': {
        'patterns': ['chatgpt', 'openai'],
        'icon': 'smart_toy',
        'color': '#10A37F',
        'category': 'Software'
    },
    'gym': {
        'patterns': ['gym', 'fitness', 'planet fitness', 'la fitness', 'anytime fitness', 'gold gym', 'crossfit', 'puregym'],
        'icon': 'fitness_center',
        'color': '#FF5722',
        'category': 'Health'
    },
    'headspace': {
        'patterns': ['headspace'],
        'icon': 'self_improvement',
        'color': '#F47D31',
        'category': 'Health'
    },
    'calm': {
        'patterns': ['calm app', 'calm.com'],
        'icon': 'self_improvement',
        'color': '#5B93FF',
        'category': 'Health'
    },
    'nytimes': {
        'patterns': ['new york times', 'nytimes', 'nyt'],
        'icon': 'newspaper',
        'color': '#000000',
        'category': 'News'
    },
    'wsj': {
        'patterns': ['wall street journal', 'wsj'],
        'icon': 'newspaper',
        'color': '#000000',
        'category': 'News'
    },
    'medium': {
        'patterns': ['medium'],
        'icon': 'article',
        'color': '#000000',
        'category': 'News'
    },
    'linkedin_premium': {
        'patterns': ['linkedin premium', 'linkedin'],
        'icon': 'badge',
        'color': '#0A66C2',
        'category': 'Career'
    },
    'skillshare': {
        'patterns': ['skillshare'],
        'icon': 'school',
        'color': '#00FF84',
        'category': 'Education'
    },
    'masterclass': {
        'patterns': ['masterclass'],
        'icon': 'school',
        'color': '#000000',
        'category': 'Education'
    },
    'duolingo': {
        'patterns': ['duolingo'],
        'icon': 'translate',
        'color': '#58CC02',
        'category': 'Education'
    },
    'vpn': {
        'patterns': ['vpn', 'nordvpn', 'expressvpn', 'surfshark', 'protonvpn'],
        'icon': 'vpn_key',
        'color': '#4687FF',
        'category': 'Security'
    },
    'password_manager': {
        'patterns': ['1password', 'lastpass', 'bitwarden', 'dashlane'],
        'icon': 'password',
        'color': '#0094F5',
        'category': 'Security'
    },
    'antivirus': {
        'patterns': ['norton', 'mcafee', 'kaspersky', 'bitdefender', 'avast'],
        'icon': 'security',
        'color': '#FFE500',
        'category': 'Security'
    },
    'dating': {
        'patterns': ['tinder', 'bumble', 'hinge', 'match.com', 'okcupid', 'eharmony'],
        'icon': 'favorite',
        'color': '#FE3C72',
        'category': 'Lifestyle'
    },
    'meal_kit': {
        'patterns': ['hello fresh', 'blue apron', 'home chef', 'factor', 'freshly'],
        'icon': 'restaurant',
        'color': '#91C11E',
        'category': 'Food'
    },
    'audible': {
        'patterns': ['audible'],
        'icon': 'headphones',
        'color': '#F8991C',
        'category': 'Entertainment'
    },
    'kindle': {
        'patterns': ['kindle unlimited'],
        'icon': 'menu_book',
        'color': '#FF9900',
        'category': 'Entertainment'
    },
    'dazn': {
        'patterns': ['dazn'],
        'icon': 'sports',
        'color': '#F8F8F5',
        'category': 'Entertainment'
    },
    'espn': {
        'patterns': ['espn+', 'espn plus'],
        'icon': 'sports',
        'color': '#D00000',
        'category': 'Entertainment'
    },
    'patreon': {
        'patterns': ['patreon'],
        'icon': 'volunteer_activism',
        'color': '#FF424D',
        'category': 'Entertainment'
    },
    'twitch': {
        'patterns': ['twitch'],
        'icon': 'live_tv',
        'color': '#9146FF',
        'category': 'Entertainment'
    },
    'figma': {
        'patterns': ['figma'],
        'icon': 'design_services',
        'color': '#F24E1E',
        'category': 'Software'
    },
    'canva': {
        'patterns': ['canva'],
        'icon': 'design_services',
        'color': '#00C4CC',
        'category': 'Software'
    },
    'grammarly': {
        'patterns': ['grammarly'],
        'icon': 'spellcheck',
        'color': '#15C39A',
        'category': 'Software'
    }
}


def detect_subscription_service(description):
    """
    Detect if an expense description matches a known subscription service
    Returns service info if found, None otherwise
    """
    desc_lower = description.lower()
    
    for service_key, service_info in SUBSCRIPTION_SERVICES.items():
        for pattern in service_info['patterns']:
            if pattern in desc_lower:
                return {
                    'service_name': service_key,
                    'icon': service_info['icon'],
                    'color': service_info['color'],
                    'category': service_info['category']
                }
    return None


@bp.route('/', methods=['GET'])
@login_required
def get_subscriptions():
    """Get all subscriptions for current user"""
    # Security: Filter by user_id
    subscriptions = RecurringExpense.query.filter_by(
        user_id=current_user.id,
        is_subscription=True
    ).order_by(
        RecurringExpense.is_active.desc(),
        RecurringExpense.next_due_date.asc()
    ).all()
    
    return jsonify({
        'subscriptions': [s.to_dict() for s in subscriptions]
    })


@bp.route('/summary', methods=['GET'])
@login_required
def get_subscription_summary():
    """Get subscription summary statistics"""
    # Security: Filter by user_id
    subscriptions = RecurringExpense.query.filter_by(
        user_id=current_user.id,
        is_subscription=True,
        is_active=True
    ).all()
    
    total_monthly = sum(s.get_monthly_cost() for s in subscriptions)
    total_yearly = sum(s.get_yearly_cost() for s in subscriptions)
    
    # Group by category
    by_category = defaultdict(float)
    for s in subscriptions:
        cat_name = s.category.name if s.category else 'Uncategorized'
        by_category[cat_name] += s.get_monthly_cost()
    
    # Find unused subscriptions
    unused = [s.to_dict() for s in subscriptions if s.is_unused()]
    
    # Find upcoming renewals (next 7 days)
    upcoming = [s.to_dict() for s in subscriptions if s.days_until_renewal() is not None and 0 <= s.days_until_renewal() <= 7]
    
    # Find subscriptions needing reminders
    reminders = [s.to_dict() for s in subscriptions if s.needs_reminder()]
    
    return jsonify({
        'total_monthly': round(total_monthly, 2),
        'total_yearly': round(total_yearly, 2),
        'active_count': len(subscriptions),
        'unused_count': len(unused),
        'unused_subscriptions': unused,
        'upcoming_renewals': upcoming,
        'reminders': reminders,
        'by_category': dict(by_category)
    })


@bp.route('/', methods=['POST'])
@login_required
def create_subscription():
    """Create a new subscription"""
    data = request.get_json()
    
    # Validate required fields
    if not data or not data.get('name') or not data.get('amount') or not data.get('category_id'):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    # Security: Validate amount to prevent negative values and overflow attacks
    from app.utils import validate_amount, validate_positive_integer
    is_valid, validated_amount, error_msg = validate_amount(data.get('amount'), 'Amount')
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400
    
    # Security: Validate category_id
    is_valid, validated_category_id, error_msg = validate_positive_integer(data.get('category_id'), 'Category ID', min_val=1)
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400
    
    # Security: Verify category belongs to current user
    category = Category.query.filter_by(id=validated_category_id, user_id=current_user.id).first()
    if not category:
        return jsonify({'success': False, 'message': 'Invalid category'}), 400
    
    # Detect if this matches a known service
    service_info = detect_subscription_service(data.get('name', ''))
    
    # Calculate next due date
    frequency = data.get('frequency', 'monthly')
    next_due_date = data.get('next_due_date')
    
    if next_due_date:
        next_due_date = datetime.fromisoformat(next_due_date)
    else:
        # Default to today + 1 month for monthly
        from app.routes.recurring import calculate_next_due_date
        next_due_date = calculate_next_due_date(frequency, data.get('day_of_period'))
    
    # Create subscription
    subscription = RecurringExpense(
        name=data.get('name'),
        amount=validated_amount,
        currency=data.get('currency', current_user.currency),
        category_id=validated_category_id,
        frequency=frequency,
        day_of_period=data.get('day_of_period'),
        next_due_date=next_due_date,
        auto_create=data.get('auto_create', False),
        is_active=data.get('is_active', True),
        notes=data.get('notes'),
        detected=False,
        is_subscription=True,
        service_name=service_info['service_name'] if service_info else data.get('service_name'),
        reminder_days=data.get('reminder_days', 3),
        user_id=current_user.id
    )
    
    db.session.add(subscription)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'subscription': subscription.to_dict()
    }), 201


@bp.route('/<int:subscription_id>', methods=['PUT'])
@login_required
def update_subscription(subscription_id):
    """Update a subscription"""
    # Security: Filter by user_id
    subscription = RecurringExpense.query.filter_by(
        id=subscription_id,
        user_id=current_user.id,
        is_subscription=True
    ).first()
    
    if not subscription:
        return jsonify({'success': False, 'message': 'Subscription not found'}), 404
    
    data = request.get_json()
    
    # Security: Import validation functions
    from app.utils import validate_amount, validate_positive_integer
    
    # Update fields
    if data.get('name'):
        subscription.name = data.get('name')
        # Re-detect service
        service_info = detect_subscription_service(data.get('name'))
        if service_info:
            subscription.service_name = service_info['service_name']
    if data.get('amount'):
        is_valid, validated_amount, error_msg = validate_amount(data.get('amount'), 'Amount')
        if not is_valid:
            return jsonify({'success': False, 'message': error_msg}), 400
        subscription.amount = validated_amount
    if data.get('currency'):
        subscription.currency = data.get('currency')
    if data.get('category_id'):
        is_valid, validated_category_id, error_msg = validate_positive_integer(data.get('category_id'), 'Category ID', min_val=1)
        if not is_valid:
            return jsonify({'success': False, 'message': error_msg}), 400
        # Security: Verify category belongs to current user
        category = Category.query.filter_by(id=validated_category_id, user_id=current_user.id).first()
        if not category:
            return jsonify({'success': False, 'message': 'Invalid category'}), 400
        subscription.category_id = validated_category_id
    if data.get('frequency'):
        subscription.frequency = data.get('frequency')
    if 'day_of_period' in data:
        subscription.day_of_period = data.get('day_of_period')
    if data.get('next_due_date'):
        subscription.next_due_date = datetime.fromisoformat(data.get('next_due_date'))
        subscription.reminder_sent = False  # Reset reminder flag
    if 'auto_create' in data:
        subscription.auto_create = data.get('auto_create')
    if 'is_active' in data:
        subscription.is_active = data.get('is_active')
    if 'notes' in data:
        subscription.notes = data.get('notes')
    if 'reminder_days' in data:
        subscription.reminder_days = data.get('reminder_days')
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'subscription': subscription.to_dict()
    })


@bp.route('/<int:subscription_id>', methods=['DELETE'])
@login_required
def delete_subscription(subscription_id):
    """Delete a subscription"""
    # Security: Filter by user_id
    subscription = RecurringExpense.query.filter_by(
        id=subscription_id,
        user_id=current_user.id,
        is_subscription=True
    ).first()
    
    if not subscription:
        return jsonify({'success': False, 'message': 'Subscription not found'}), 404
    
    db.session.delete(subscription)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Subscription deleted'})


@bp.route('/<int:subscription_id>/mark-used', methods=['POST'])
@login_required
def mark_subscription_used(subscription_id):
    """Mark a subscription as used (update last_used_date)"""
    # Security: Filter by user_id
    subscription = RecurringExpense.query.filter_by(
        id=subscription_id,
        user_id=current_user.id,
        is_subscription=True
    ).first()
    
    if not subscription:
        return jsonify({'success': False, 'message': 'Subscription not found'}), 404
    
    subscription.last_used_date = datetime.utcnow()
    db.session.commit()
    
    return jsonify({
        'success': True,
        'subscription': subscription.to_dict()
    })


@bp.route('/<int:subscription_id>/dismiss-reminder', methods=['POST'])
@login_required
def dismiss_reminder(subscription_id):
    """Dismiss a renewal reminder for current cycle"""
    # Security: Filter by user_id
    subscription = RecurringExpense.query.filter_by(
        id=subscription_id,
        user_id=current_user.id,
        is_subscription=True
    ).first()
    
    if not subscription:
        return jsonify({'success': False, 'message': 'Subscription not found'}), 404
    
    subscription.reminder_sent = True
    db.session.commit()
    
    return jsonify({
        'success': True,
        'subscription': subscription.to_dict()
    })


@bp.route('/detect', methods=['POST'])
@login_required
def detect_subscriptions():
    """
    Auto-detect potential subscriptions from expense history
    Enhanced detection using known subscription patterns
    """
    # Get user's expenses from last 6 months
    six_months_ago = datetime.utcnow() - relativedelta(months=6)
    expenses = Expense.query.filter(
        Expense.user_id == current_user.id,
        Expense.date >= six_months_ago
    ).order_by(Expense.date.asc()).all()
    
    if len(expenses) < 5:
        return jsonify({
            'suggestions': [],
            'message': 'Not enough expense history to detect subscriptions'
        })
    
    # Group expenses by similar descriptions and amounts
    patterns = defaultdict(list)
    
    for expense in expenses:
        # First check if this matches a known subscription service
        service_info = detect_subscription_service(expense.description)
        
        # Normalize description
        normalized_desc = re.sub(r'[^a-z\s]', '', expense.description.lower()).strip()
        
        # Create a key based on normalized description and approximate amount
        amount_bucket = round(expense.amount / 5) * 5  # Group by 5 currency units for subscriptions
        key = f"{normalized_desc}_{amount_bucket}_{expense.category_id}"
        
        patterns[key].append({
            'expense': expense,
            'service_info': service_info
        })
    
    suggestions = []
    existing_services = set()
    
    # Get existing subscriptions to avoid duplicates
    existing_subs = RecurringExpense.query.filter_by(
        user_id=current_user.id,
        is_subscription=True
    ).all()
    for sub in existing_subs:
        if sub.service_name:
            existing_services.add(sub.service_name)
        existing_services.add(sub.name.lower())
    
    # Analyze patterns
    for key, expense_data_list in patterns.items():
        if len(expense_data_list) < 2:  # Need at least 2 occurrences for subscriptions
            continue
        
        expense_list = [ed['expense'] for ed in expense_data_list]
        service_infos = [ed['service_info'] for ed in expense_data_list if ed['service_info']]
        
        # If any expense matched a known service, prioritize that
        service_info = service_infos[0] if service_infos else None
        
        # Calculate intervals between expenses
        intervals = []
        for i in range(1, len(expense_list)):
            days_diff = (expense_list[i].date - expense_list[i-1].date).days
            intervals.append(days_diff)
        
        if not intervals:
            continue
        
        avg_interval = sum(intervals) / len(intervals)
        variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
        std_dev = variance ** 0.5
        
        # For subscriptions, we're more lenient with variance
        if avg_interval > 0 and std_dev / avg_interval > 0.4:
            continue
        
        # Determine frequency
        frequency = None
        day_of_period = None
        confidence = 0
        
        if 25 <= avg_interval <= 35:  # Monthly
            frequency = 'monthly'
            days = [e.date.day for e in expense_list]
            day_of_period = max(set(days), key=days.count)
            confidence = 85 - (std_dev / max(avg_interval, 1) * 50)
        elif 6 <= avg_interval <= 8:  # Weekly
            frequency = 'weekly'
            days = [e.date.weekday() for e in expense_list]
            day_of_period = max(set(days), key=days.count)
            confidence = 80 - (std_dev / max(avg_interval, 1) * 50)
        elif 360 <= avg_interval <= 375:  # Yearly
            frequency = 'yearly'
            confidence = 75 - (std_dev / max(avg_interval, 1) * 50)
        elif 85 <= avg_interval <= 95:  # Quarterly
            frequency = 'monthly'  # Treat as monthly with higher amount
            day_of_period = expense_list[-1].date.day
            confidence = 70
        
        # If known service detected, boost confidence
        if service_info:
            confidence = min(confidence + 15, 98)
        
        if frequency and confidence > 50:
            latest = expense_list[-1]
            avg_amount = sum(e.amount for e in expense_list) / len(expense_list)
            
            # Check if already exists
            if service_info and service_info['service_name'] in existing_services:
                continue
            if latest.description.lower() in existing_services:
                continue
            
            # Check if already exists as a regular recurring expense
            existing = RecurringExpense.query.filter_by(
                user_id=current_user.id,
                name=latest.description,
                category_id=latest.category_id
            ).first()
            
            if not existing:
                suggestion = {
                    'name': latest.description,
                    'amount': round(avg_amount, 2),
                    'currency': latest.currency,
                    'category_id': latest.category_id,
                    'category_name': latest.category.name,
                    'category_color': latest.category.color,
                    'frequency': frequency,
                    'day_of_period': day_of_period,
                    'confidence_score': round(confidence, 1),
                    'occurrences': len(expense_list),
                    'is_subscription': True,
                    'detected': True
                }
                
                if service_info:
                    suggestion['service_name'] = service_info['service_name']
                    suggestion['service_icon'] = service_info['icon']
                    suggestion['service_color'] = service_info['color']
                
                suggestions.append(suggestion)
    
    # Sort by confidence score
    suggestions.sort(key=lambda x: x['confidence_score'], reverse=True)
    
    return jsonify({
        'suggestions': suggestions[:15],
        'message': f'Found {len(suggestions)} potential subscriptions'
    })


@bp.route('/accept-suggestion', methods=['POST'])
@login_required
def accept_subscription_suggestion():
    """Accept a detected subscription suggestion"""
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('amount') or not data.get('category_id'):
        return jsonify({'success': False, 'message': 'Missing required fields'}), 400
    
    # Security: Validate amount to prevent negative values and overflow attacks
    from app.utils import validate_amount, validate_positive_integer
    is_valid, validated_amount, error_msg = validate_amount(data.get('amount'), 'Amount')
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400
    
    # Security: Validate category_id
    is_valid, validated_category_id, error_msg = validate_positive_integer(data.get('category_id'), 'Category ID', min_val=1)
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400
    
    # Security: Verify category belongs to current user
    category = Category.query.filter_by(id=validated_category_id, user_id=current_user.id).first()
    if not category:
        return jsonify({'success': False, 'message': 'Invalid category'}), 400
    
    # Calculate next due date
    frequency = data.get('frequency', 'monthly')
    day_of_period = data.get('day_of_period')
    
    from app.routes.recurring import calculate_next_due_date
    next_due_date = calculate_next_due_date(frequency, day_of_period)
    
    # Create subscription
    subscription = RecurringExpense(
        name=data.get('name'),
        amount=validated_amount,
        currency=data.get('currency', current_user.currency),
        category_id=validated_category_id,
        frequency=frequency,
        day_of_period=day_of_period,
        next_due_date=next_due_date,
        auto_create=data.get('auto_create', False),
        is_active=True,
        detected=True,
        confidence_score=data.get('confidence_score', 0),
        is_subscription=True,
        service_name=data.get('service_name'),
        user_id=current_user.id
    )
    
    db.session.add(subscription)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'subscription': subscription.to_dict()
    }), 201


@bp.route('/convert/<int:recurring_id>', methods=['POST'])
@login_required
def convert_to_subscription(recurring_id):
    """Convert an existing recurring expense to a subscription"""
    # Security: Filter by user_id
    recurring = RecurringExpense.query.filter_by(
        id=recurring_id,
        user_id=current_user.id
    ).first()
    
    if not recurring:
        return jsonify({'success': False, 'message': 'Recurring expense not found'}), 404
    
    # Detect service
    service_info = detect_subscription_service(recurring.name)
    
    recurring.is_subscription = True
    if service_info:
        recurring.service_name = service_info['service_name']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'subscription': recurring.to_dict()
    })


@bp.route('/services', methods=['GET'])
@login_required
def get_known_services():
    """Get list of known subscription services for autocomplete"""
    services = []
    for key, info in SUBSCRIPTION_SERVICES.items():
        services.append({
            'id': key,
            'name': key.replace('_', ' ').title(),
            'icon': info['icon'],
            'color': info['color'],
            'category': info['category']
        })
    
    return jsonify({
        'services': sorted(services, key=lambda x: x['name'])
    })


@bp.route('/upcoming', methods=['GET'])
@login_required
def get_upcoming_renewals():
    """Get subscriptions with upcoming renewals"""
    days = request.args.get('days', 30, type=int)
    
    # Security: Filter by user_id
    cutoff_date = datetime.utcnow() + timedelta(days=days)
    
    subscriptions = RecurringExpense.query.filter(
        RecurringExpense.user_id == current_user.id,
        RecurringExpense.is_subscription == True,
        RecurringExpense.is_active == True,
        RecurringExpense.next_due_date <= cutoff_date
    ).order_by(RecurringExpense.next_due_date.asc()).all()
    
    return jsonify({
        'upcoming': [s.to_dict() for s in subscriptions]
    })


@bp.route('/unused', methods=['GET'])
@login_required
def get_unused_subscriptions():
    """Get subscriptions that appear unused"""
    days = request.args.get('days', 60, type=int)
    
    # Security: Filter by user_id
    subscriptions = RecurringExpense.query.filter_by(
        user_id=current_user.id,
        is_subscription=True,
        is_active=True
    ).all()
    
    unused = [s.to_dict() for s in subscriptions if s.is_unused(days)]
    
    # Calculate potential savings
    monthly_savings = sum(s.get_monthly_cost() for s in subscriptions if s.is_unused(days))
    
    return jsonify({
        'unused': unused,
        'potential_monthly_savings': round(monthly_savings, 2),
        'potential_yearly_savings': round(monthly_savings * 12, 2)
    })
