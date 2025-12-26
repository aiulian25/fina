"""
Migration: Add monthly_budget column to users table
Run this with: python migrations/add_monthly_budget.py
"""

from app import create_app, db

def migrate():
    app = create_app()
    with app.app_context():
        try:
            # Check if column exists
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            if 'monthly_budget' not in columns:
                db.engine.execute('ALTER TABLE users ADD COLUMN monthly_budget FLOAT DEFAULT 0.0')
                print("✅ Successfully added monthly_budget column to users table")
            else:
                print("ℹ️  Column monthly_budget already exists")
                
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            raise

if __name__ == '__main__':
    migrate()
