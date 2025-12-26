"""
Scheduler for background tasks like auto-creating recurring expenses and income
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from app import db
from app.models import RecurringExpense, Expense, Income
from app.routes.recurring import calculate_next_due_date
from app.routes.income import calculate_income_next_due_date
import logging

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
    
    scheduler.start()
    logger.info("Scheduler initialized - recurring expenses and income will be processed hourly")
    
    # Shut down the scheduler when exiting the app
    import atexit
    atexit.register(lambda: scheduler.shutdown())
    
    return scheduler
