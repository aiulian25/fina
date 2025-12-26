#!/usr/bin/env python3
"""
Migration Script: Add Budget Alert Support
Created: 2024
Description: Adds budget tracking and email alert functionality to categories and users
"""

from sqlalchemy import create_engine, Column, Integer, Float, Boolean, String, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import sys

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.user import User
from app.models.category import Category

def migrate():
    """Run the migration to add budget alert columns"""
    app = create_app()
    
    with app.app_context():
        print("🔧 Starting budget alerts migration...")
        
        # Get database engine
        engine = db.engine
        
        try:
            # Check if columns already exist
            inspector = db.inspect(engine)
            category_columns = [col['name'] for col in inspector.get_columns('categories')]
            user_columns = [col['name'] for col in inspector.get_columns('users')]
            
            # Add columns to Category if they don't exist
            print("\n📊 Migrating categories table...")
            if 'monthly_budget' not in category_columns:
                print("  ✓ Adding monthly_budget column")
                engine.execute('ALTER TABLE categories ADD COLUMN monthly_budget REAL')
            else:
                print("  ⊙ monthly_budget already exists")
                
            if 'budget_alert_sent' not in category_columns:
                print("  ✓ Adding budget_alert_sent column")
                engine.execute('ALTER TABLE categories ADD COLUMN budget_alert_sent BOOLEAN DEFAULT FALSE')
            else:
                print("  ⊙ budget_alert_sent already exists")
                
            if 'budget_alert_threshold' not in category_columns:
                print("  ✓ Adding budget_alert_threshold column")
                engine.execute('ALTER TABLE categories ADD COLUMN budget_alert_threshold INTEGER DEFAULT 100')
            else:
                print("  ⊙ budget_alert_threshold already exists")
                
            if 'last_budget_check' not in category_columns:
                print("  ✓ Adding last_budget_check column")
                engine.execute('ALTER TABLE categories ADD COLUMN last_budget_check DATE')
            else:
                print("  ⊙ last_budget_check already exists")
            
            # Add columns to User if they don't exist
            print("\n👤 Migrating users table...")
            if 'budget_alerts_enabled' not in user_columns:
                print("  ✓ Adding budget_alerts_enabled column")
                engine.execute('ALTER TABLE users ADD COLUMN budget_alerts_enabled BOOLEAN DEFAULT TRUE')
            else:
                print("  ⊙ budget_alerts_enabled already exists")
                
            if 'alert_email' not in user_columns:
                print("  ✓ Adding alert_email column")
                engine.execute('ALTER TABLE users ADD COLUMN alert_email VARCHAR(120)')
            else:
                print("  ⊙ alert_email already exists")
            
            # Set default values for existing records
            print("\n🔄 Setting default values...")
            from sqlalchemy import text
            db.session.execute(
                text('UPDATE categories SET budget_alert_sent = FALSE WHERE budget_alert_sent IS NULL')
            )
            db.session.execute(
                text('UPDATE categories SET budget_alert_threshold = 100 WHERE budget_alert_threshold IS NULL')
            )
            db.session.execute(
                text('UPDATE users SET budget_alerts_enabled = TRUE WHERE budget_alerts_enabled IS NULL')
            )
            db.session.commit()
            print("  ✓ Default values set")
            
            # Create indexes
            print("\n📇 Creating indexes...")
            try:
                engine.execute('CREATE INDEX IF NOT EXISTS idx_category_budget_check ON categories(monthly_budget, budget_alert_sent)')
                print("  ✓ Index on categories budget fields")
            except:
                print("  ⊙ Categories index already exists")
                
            try:
                engine.execute('CREATE INDEX IF NOT EXISTS idx_user_budget_alerts ON users(budget_alerts_enabled)')
                print("  ✓ Index on users budget alerts")
            except:
                print("  ⊙ Users index already exists")
            
            print("\n✅ Migration completed successfully!")
            print("\n📧 Next steps:")
            print("  1. Configure SMTP settings in your environment:")
            print("     - MAIL_SERVER (e.g., smtp.gmail.com)")
            print("     - MAIL_PORT (e.g., 587)")
            print("     - MAIL_USERNAME")
            print("     - MAIL_PASSWORD")
            print("     - MAIL_DEFAULT_SENDER")
            print("  2. Restart your application")
            print("  3. Test by setting a budget on a category in Settings")
            
        except Exception as e:
            print(f"\n❌ Migration failed: {str(e)}")
            db.session.rollback()
            raise

if __name__ == '__main__':
    migrate()
