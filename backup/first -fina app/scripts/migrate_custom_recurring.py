#!/usr/bin/env python3
"""
Database migration for custom recurring expenses feature
Adds new columns to subscriptions table for advanced scheduling
"""

import sqlite3
import sys

def migrate_database(db_path='instance/finance.db'):
    """Add new columns to subscriptions table"""
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Adding custom recurring expense fields...")
        
        # Check which columns already exist
        cursor.execute("PRAGMA table_info(subscriptions)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        # Define new columns with their SQL types
        new_columns = [
            ('custom_interval_days', 'INTEGER'),
            ('start_date', 'DATE'),
            ('end_date', 'DATE'),
            ('total_occurrences', 'INTEGER'),
            ('occurrences_count', 'INTEGER DEFAULT 0'),
            ('auto_create_expense', 'BOOLEAN DEFAULT 0'),
            ('last_auto_created', 'DATE'),
        ]
        
        # Add each column if it doesn't exist
        for column_name, column_type in new_columns:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f'ALTER TABLE subscriptions ADD COLUMN {column_name} {column_type}')
                    print(f"  ✅ Added column: {column_name}")
                except sqlite3.OperationalError as e:
                    print(f"  ⚠️  Column {column_name} may already exist: {e}")
            else:
                print(f"  ℹ️  Column {column_name} already exists")
        
        # Update existing subscriptions with start dates
        cursor.execute("""
            UPDATE subscriptions 
            SET start_date = next_due_date 
            WHERE start_date IS NULL AND next_due_date IS NOT NULL
        """)
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        print("\nNew features:")
        print("  • Custom frequency intervals (any number of days)")
        print("  • Start and end dates for subscriptions")
        print("  • Limit total number of payments")
        print("  • Auto-create expenses on due date")
        print("  • Track occurrence count")
        
        return True
        
    except sqlite3.Error as e:
        print(f"\n❌ Database error: {e}")
        return False
        
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'instance/finance.db'
    success = migrate_database(db_path)
    sys.exit(0 if success else 1)
