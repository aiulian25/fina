"""
Migration: Add subscription-specific fields to recurring_expenses table
"""
import sqlite3
import os

def run_migration():
    """Add subscription fields to recurring_expenses table"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'fina.db')
    
    if not os.path.exists(db_path):
        print("Database not found, skipping migration")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check existing columns
    cursor.execute("PRAGMA table_info(recurring_expenses)")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Add new subscription columns if they don't exist
    new_columns = [
        ('is_subscription', 'BOOLEAN DEFAULT 0'),
        ('service_name', 'VARCHAR(100)'),
        ('last_used_date', 'DATETIME'),
        ('reminder_days', 'INTEGER DEFAULT 3'),
        ('reminder_sent', 'BOOLEAN DEFAULT 0')
    ]
    
    for col_name, col_type in new_columns:
        if col_name not in columns:
            try:
                cursor.execute(f"ALTER TABLE recurring_expenses ADD COLUMN {col_name} {col_type}")
                print(f"Added column {col_name} to recurring_expenses")
            except sqlite3.OperationalError as e:
                if "duplicate column name" not in str(e).lower():
                    print(f"Error adding column {col_name}: {e}")
    
    conn.commit()
    conn.close()
    print("Subscription migration completed")

if __name__ == '__main__':
    run_migration()
