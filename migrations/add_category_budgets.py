"""
Migration: Add budget tracking fields to categories
"""
import sqlite3
import os

def migrate():
    """Add budget fields to categories table"""
    
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'fina.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Add monthly_budget to categories
        print("Adding monthly_budget column to categories table...")
        cursor.execute("""
            ALTER TABLE categories 
            ADD COLUMN monthly_budget REAL
        """)
        print("✓ Added monthly_budget to categories")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("✓ monthly_budget column already exists in categories")
        else:
            print(f"Error adding monthly_budget to categories: {e}")
    
    try:
        # Add budget_alert_threshold to categories
        print("Adding budget_alert_threshold column to categories table...")
        cursor.execute("""
            ALTER TABLE categories 
            ADD COLUMN budget_alert_threshold REAL DEFAULT 0.9
        """)
        print("✓ Added budget_alert_threshold to categories")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("✓ budget_alert_threshold column already exists in categories")
        else:
            print(f"Error adding budget_alert_threshold to categories: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n✓ Budget tracking migration completed successfully!")
    print("Categories can now have monthly budgets with customizable alert thresholds.")

if __name__ == '__main__':
    migrate()
