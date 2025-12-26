"""
Migration script to add recurring_expenses table to the database
Run this script to update the database schema
"""
from app import create_app, db
from app.models import RecurringExpense

def migrate():
    app = create_app()
    with app.app_context():
        # Create the recurring_expenses table
        db.create_all()
        print("✓ Migration complete: recurring_expenses table created")

if __name__ == '__main__':
    migrate()
