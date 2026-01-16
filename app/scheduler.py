"""
Scheduler for background tasks like auto-creating recurring expenses and income,
and generating spending insights
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
from app import db
from app.models import RecurringExpense, Expense, Income, User, SpendingInsight, UserInsightPreferences
from app.routes.recurring import calculate_next_due_date
from app.routes.income import calculate_income_next_due_date
from collections import defaultdict
import logging
import re

logger = logging.getLogger(__name__)

def process_due_recurring_expenses():
    """
    Process all due recurring expenses and create actual expenses for them
    Security: User isolation is maintained through foreign keys
    """
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            today = datetime.utcnow().date()
            
            # Find all active recurring expenses that are due today or overdue and have auto_create enabled
            due_recurring = RecurringExpense.query.filter(
                RecurringExpense.is_active == True,
                RecurringExpense.auto_create == True,
                RecurringExpense.next_due_date <= datetime.utcnow()
            ).all()
            
            created_count = 0
            
            for recurring in due_recurring:
                try:
                    # Check if we already created an expense today for this recurring expense
                    # to avoid duplicates
                    existing_today = Expense.query.filter(
                        Expense.user_id == recurring.user_id,
                        Expense.description == recurring.name,
                        Expense.category_id == recurring.category_id,
                        db.func.date(Expense.date) == today
                    ).first()
                    
                    if existing_today:
                        logger.info(f"Expense already exists for recurring ID {recurring.id} today, skipping")
                        continue
                    
                    # Create the expense
                    expense = Expense(
                        amount=recurring.amount,
                        currency=recurring.currency,
                        description=recurring.name,
                        category_id=recurring.category_id,
                        user_id=recurring.user_id,
                        tags=['recurring', recurring.frequency, 'auto-created'],
                        date=datetime.utcnow()
                    )
                    expense.set_tags(['recurring', recurring.frequency, 'auto-created'])
                    
                    db.session.add(expense)
                    
                    # Update recurring expense
                    recurring.last_created_date = datetime.utcnow()
                    recurring.next_due_date = calculate_next_due_date(
                        recurring.frequency,
                        recurring.day_of_period,
                        recurring.next_due_date
                    )
                    
                    created_count += 1
                    logger.info(f"Created expense from recurring ID {recurring.id} for user {recurring.user_id}")
                    
                except Exception as e:
                    logger.error(f"Error processing recurring expense ID {recurring.id}: {str(e)}")
                    db.session.rollback()
                    continue
            
            if created_count > 0:
                db.session.commit()
                logger.info(f"Successfully created {created_count} expenses from recurring expenses")
            else:
                logger.info("No recurring expenses due for processing")
                
    except Exception as e:
        logger.error(f"Error in process_due_recurring_expenses: {str(e)}")


def process_due_recurring_income():
    """
    Process all due recurring income and create actual income entries for them
    Security: User isolation is maintained through foreign keys
    """
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            today = datetime.utcnow().date()
            
            # Find all active recurring income that are due today or overdue and have auto_create enabled
            due_recurring = Income.query.filter(
                Income.is_active == True,
                Income.auto_create == True,
                Income.frequency != 'once',
                Income.next_due_date <= datetime.utcnow()
            ).all()
            
            created_count = 0
            
            for recurring in due_recurring:
                try:
                    # Check if we already created income today for this recurring income
                    # to avoid duplicates
                    existing_today = Income.query.filter(
                        Income.user_id == recurring.user_id,
                        Income.description == recurring.description,
                        Income.source == recurring.source,
                        Income.frequency == 'once',  # Only check one-time income entries
                        db.func.date(Income.date) == today
                    ).first()
                    
                    if existing_today:
                        logger.info(f"Income already exists for recurring ID {recurring.id} today, skipping")
                        continue
                    
                    # Create the income entry
                    income = Income(
                        amount=recurring.amount,
                        currency=recurring.currency,
                        description=recurring.description,
                        source=recurring.source,
                        user_id=recurring.user_id,
                        tags=recurring.tags,
                        frequency='once',  # Created income is one-time
                        date=datetime.utcnow()
                    )
                    
                    db.session.add(income)
                    
                    # Update recurring income
                    recurring.last_created_date = datetime.utcnow()
                    recurring.next_due_date = calculate_income_next_due_date(
                        recurring.frequency,
                        recurring.custom_days,
                        recurring.last_created_date
                    )
                    
                    created_count += 1
                    logger.info(f"Created income from recurring ID {recurring.id} for user {recurring.user_id}")
                    
                except Exception as e:
                    logger.error(f"Error processing recurring income ID {recurring.id}: {str(e)}")
                    db.session.rollback()
                    continue
            
            if created_count > 0:
                db.session.commit()
                logger.info(f"Successfully created {created_count} income entries from recurring income")
            else:
                logger.info("No recurring income due for processing")
                
    except Exception as e:
        logger.error(f"Error in process_due_recurring_income: {str(e)}")


def init_scheduler(app):
    """Initialize the background scheduler"""
    scheduler = BackgroundScheduler()
    
    # Run every hour to check for due recurring expenses
    scheduler.add_job(
        func=process_due_recurring_expenses,
        trigger=CronTrigger(minute=0),  # Run at the start of every hour
        id='process_recurring_expenses',
        name='Process due recurring expenses',
        replace_existing=True
    )
    
    # Run every hour to check for due recurring income
    scheduler.add_job(
        func=process_due_recurring_income,
        trigger=CronTrigger(minute=5),  # Run 5 minutes past every hour
        id='process_recurring_income',
        name='Process due recurring income',
        replace_existing=True
    )
    
    # Run daily at 8 AM to generate spending insights
    scheduler.add_job(
        func=process_daily_insights,
        trigger=CronTrigger(hour=8, minute=0),  # Run at 8:00 AM
        id='process_daily_insights',
        name='Generate daily spending insights',
        replace_existing=True
    )
    
    # Run weekly on Monday at 8 AM to generate weekly digests
    scheduler.add_job(
        func=process_weekly_digests,
        trigger=CronTrigger(day_of_week='mon', hour=8, minute=30),  # Monday 8:30 AM
        id='process_weekly_digests',
        name='Generate weekly spending digests',
        replace_existing=True
    )
    
    # Run daily at 11:59 PM to process no-spend day checks
    scheduler.add_job(
        func=process_no_spend_checks,
        trigger=CronTrigger(hour=23, minute=59),  # 11:59 PM
        id='process_no_spend_checks',
        name='Process daily no-spend day checks',
        replace_existing=True
    )
    
    # Run weekly on Sunday to advance 52-week challenges
    scheduler.add_job(
        func=process_52_week_advance,
        trigger=CronTrigger(day_of_week='sun', hour=23, minute=30),  # Sunday 11:30 PM
        id='process_52_week_advance',
        name='Advance 52-week challenges',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Scheduler initialized - recurring expenses, income, insights, and challenges will be processed")
    
    # Shut down the scheduler when exiting the app
    import atexit
    atexit.register(lambda: scheduler.shutdown())
    
    return scheduler


def process_daily_insights():
    """
    Process daily spending insights for all users
    Checks for unusual spending patterns and category spikes
    """
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            users = User.query.all()
            
            for user in users:
                try:
                    process_user_insights(user)
                except Exception as e:
                    logger.error(f"Error processing insights for user {user.id}: {str(e)}")
                    continue
            
            db.session.commit()
            logger.info(f"Daily insights processed for {len(users)} users")
            
    except Exception as e:
        logger.error(f"Error in process_daily_insights: {str(e)}")


def process_user_insights(user):
    """Process insights for a single user"""
    prefs = UserInsightPreferences.query.filter_by(user_id=user.id).first()
    if not prefs:
        prefs = UserInsightPreferences(user_id=user.id)
        db.session.add(prefs)
    
    # Check unusual spending
    if prefs.unusual_spending_enabled:
        check_and_create_unusual_spending_insight(user, prefs.unusual_spending_threshold)
    
    # Check category spikes
    if prefs.category_alerts_enabled:
        check_and_create_category_spike_insights(user, prefs.category_alert_threshold)
    
    # Check money leaks (less frequent - weekly)
    # This is handled in weekly digests


def check_and_create_unusual_spending_insight(user, threshold):
    """Check for unusual spending and create insight if detected"""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    baseline_start = start_date - timedelta(days=30)
    
    recent = Expense.query.filter(
        Expense.user_id == user.id,
        Expense.date >= start_date
    ).all()
    
    baseline = Expense.query.filter(
        Expense.user_id == user.id,
        Expense.date >= baseline_start,
        Expense.date < start_date
    ).all()
    
    if not baseline:
        return
    
    baseline_daily = sum(e.amount for e in baseline) / 30
    recent_daily = sum(e.amount for e in recent) / 7 if recent else 0
    
    if baseline_daily > 0 and recent_daily > baseline_daily * threshold:
        # Check for existing similar insight
        existing = SpendingInsight.query.filter(
            SpendingInsight.user_id == user.id,
            SpendingInsight.insight_type == 'unusual_spending',
            SpendingInsight.created_at > datetime.utcnow() - timedelta(days=3)
        ).first()
        
        if not existing:
            insight = SpendingInsight(
                user_id=user.id,
                insight_type='unusual_spending',
                priority='high',
                title_key='insights.unusual.overallSpike.title',
                message_key='insights.unusual.overallSpike.message',
                icon='trending_up',
                amount=round(recent_daily * 7, 2),
                action_key='insights.unusual.action.reviewSpending',
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            insight.set_message_params({
                'percentage': round(((recent_daily / baseline_daily) - 1) * 100),
                'currency': user.currency
            })
            db.session.add(insight)
            logger.info(f"Created unusual spending insight for user {user.id}")


def check_and_create_category_spike_insights(user, threshold):
    """Check for category spending spikes"""
    now = datetime.utcnow()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    prev_month_end = start_of_month - timedelta(days=1)
    prev_month_start = prev_month_end.replace(day=1)
    
    current = Expense.query.filter(
        Expense.user_id == user.id,
        Expense.date >= start_of_month
    ).all()
    
    previous = Expense.query.filter(
        Expense.user_id == user.id,
        Expense.date >= prev_month_start,
        Expense.date <= prev_month_end
    ).all()
    
    current_by_cat = defaultdict(float)
    prev_by_cat = defaultdict(float)
    cat_ids = {}
    
    for e in current:
        cat_name = e.category.name if e.category else 'Uncategorized'
        current_by_cat[cat_name] += e.amount
        cat_ids[cat_name] = e.category_id
    
    for e in previous:
        cat_name = e.category.name if e.category else 'Uncategorized'
        prev_by_cat[cat_name] += e.amount
    
    for cat_name, current_amount in current_by_cat.items():
        prev_amount = prev_by_cat.get(cat_name, 0)
        if prev_amount > 0 and current_amount > prev_amount * threshold and (current_amount - prev_amount) > 20:
            # Check for existing similar insight
            existing = SpendingInsight.query.filter(
                SpendingInsight.user_id == user.id,
                SpendingInsight.insight_type == 'category_spike',
                SpendingInsight.category_id == cat_ids.get(cat_name),
                SpendingInsight.created_at > datetime.utcnow() - timedelta(days=7)
            ).first()
            
            if not existing:
                change = ((current_amount / prev_amount) - 1) * 100
                insight = SpendingInsight(
                    user_id=user.id,
                    insight_type='category_spike',
                    priority='high' if change > 100 else 'medium',
                    title_key='insights.category.spike.title',
                    message_key='insights.category.spike.message',
                    category_id=cat_ids.get(cat_name),
                    amount=round(current_amount, 2),
                    icon='trending_up',
                    action_key='insights.category.action.reviewCategory',
                    expires_at=datetime.utcnow() + timedelta(days=14)
                )
                insight.set_message_params({
                    'category': cat_name,
                    'percentage': round(change),
                    'currency': user.currency,
                    'amount': round(current_amount - prev_amount, 2)
                })
                insight.set_comparison_data({
                    'current': round(current_amount, 2),
                    'previous': round(prev_amount, 2)
                })
                db.session.add(insight)
                logger.info(f"Created category spike insight for user {user.id}, category: {cat_name}")


def process_weekly_digests():
    """
    Process weekly spending digests for all users
    Creates weekly summary insights
    """
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            users = User.query.all()
            
            for user in users:
                try:
                    create_weekly_digest_insight(user)
                    check_and_create_money_leak_insights(user)
                except Exception as e:
                    logger.error(f"Error creating weekly digest for user {user.id}: {str(e)}")
                    continue
            
            db.session.commit()
            logger.info(f"Weekly digests processed for {len(users)} users")
            
    except Exception as e:
        logger.error(f"Error in process_weekly_digests: {str(e)}")


def create_weekly_digest_insight(user):
    """Create weekly digest summary insight"""
    prefs = UserInsightPreferences.query.filter_by(user_id=user.id).first()
    if prefs and not prefs.weekly_digest_enabled:
        return
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    prev_start = start_date - timedelta(days=7)
    
    current = Expense.query.filter(
        Expense.user_id == user.id,
        Expense.date >= start_date
    ).all()
    
    previous = Expense.query.filter(
        Expense.user_id == user.id,
        Expense.date >= prev_start,
        Expense.date < start_date
    ).all()
    
    current_total = sum(e.amount for e in current)
    prev_total = sum(e.amount for e in previous)
    
    if prev_total > 0:
        change = ((current_total - prev_total) / prev_total) * 100
    else:
        change = 0
    
    # Find top category
    category_totals = defaultdict(float)
    for e in current:
        cat_name = e.category.name if e.category else 'Uncategorized'
        category_totals[cat_name] += e.amount
    
    top_category = max(category_totals.items(), key=lambda x: x[1])[0] if category_totals else 'None'
    
    insight = SpendingInsight(
        user_id=user.id,
        insight_type='weekly_digest',
        priority='low',
        title_key='insights.weeklyDigest.title',
        message_key='insights.weeklyDigest.message',
        amount=round(current_total, 2),
        icon='summarize',
        period_start=start_date,
        period_end=end_date,
        expires_at=datetime.utcnow() + timedelta(days=14)
    )
    insight.set_message_params({
        'total': round(current_total, 2),
        'change': round(change, 1),
        'top_category': top_category,
        'transaction_count': len(current),
        'currency': user.currency
    })
    insight.set_comparison_data({
        'current': round(current_total, 2),
        'previous': round(prev_total, 2),
        'change_percentage': round(change, 1)
    })
    db.session.add(insight)
    logger.info(f"Created weekly digest for user {user.id}")


def check_and_create_money_leak_insights(user):
    """Check for recurring small expenses (money leaks)"""
    prefs = UserInsightPreferences.query.filter_by(user_id=user.id).first()
    if prefs and not prefs.money_leak_detection_enabled:
        return
    
    min_occurrences = prefs.money_leak_min_occurrences if prefs else 3
    start_date = datetime.utcnow() - timedelta(days=90)
    
    expenses = Expense.query.filter(
        Expense.user_id == user.id,
        Expense.date >= start_date
    ).all()
    
    patterns = defaultdict(lambda: {'total': 0, 'count': 0})
    
    for expense in expenses:
        desc = expense.description.lower().strip()
        desc_clean = re.sub(r'[0-9#]+', '', desc).strip()
        desc_clean = re.sub(r'\s+', ' ', desc_clean)
        amount_bucket = round(expense.amount / 5) * 5
        key = f"{desc_clean}_{amount_bucket}"
        
        patterns[key]['total'] += expense.amount
        patterns[key]['count'] += 1
        patterns[key]['desc'] = expense.description
    
    for key, data in patterns.items():
        if data['count'] >= min_occurrences:
            yearly_projection = (data['total'] / 90) * 365
            if yearly_projection > 200:  # Only flag significant leaks
                # Check for existing
                existing = SpendingInsight.query.filter(
                    SpendingInsight.user_id == user.id,
                    SpendingInsight.insight_type == 'money_leak',
                    SpendingInsight.created_at > datetime.utcnow() - timedelta(days=30)
                ).count()
                
                if existing < 3:  # Max 3 leak insights at a time
                    insight = SpendingInsight(
                        user_id=user.id,
                        insight_type='money_leak',
                        priority='medium',
                        title_key='insights.moneyLeak.title',
                        message_key='insights.moneyLeak.message',
                        amount=round(data['total'], 2),
                        icon='water_drop',
                        action_key='insights.moneyLeak.action.reviewHabit',
                        expires_at=datetime.utcnow() + timedelta(days=30)
                    )
                    insight.set_message_params({
                        'description': data['desc'],
                        'count': data['count'],
                        'yearly': round(yearly_projection, 2),
                        'currency': user.currency
                    })
                    insight.set_comparison_data({
                        'occurrences': data['count'],
                        'yearly_projection': round(yearly_projection, 2)
                    })
                    db.session.add(insight)
                    logger.info(f"Created money leak insight for user {user.id}: {data['desc']}")

def process_no_spend_checks():
    """
    Process end-of-day no-spend checks for all users
    Runs at 11:59 PM to determine if each day was a no-spend day
    """
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from app.routes.challenges import process_daily_no_spend_check
            process_daily_no_spend_check(app)
            logger.info("Daily no-spend checks completed")
    except Exception as e:
        logger.error(f"Error in process_no_spend_checks: {str(e)}")


def process_52_week_advance():
    """
    Advance 52-week challenges on Sunday nights
    """
    try:
        from app import create_app
        app = create_app()
        
        with app.app_context():
            from app.routes.challenges import process_weekly_52_advance
            process_weekly_52_advance(app)
            logger.info("52-week challenge advancement completed")
    except Exception as e:
        logger.error(f"Error in process_52_week_advance: {str(e)}")