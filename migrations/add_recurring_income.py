#!/usr/bin/env python3
"""
Migration script to add recurring income fields to Income table
Adds: next_due_date, last_created_date, is_active, auto_create
Idempotent: Can be run multiple times safely
"""
import sqlite3
from datetime import datetime

def migrate():
    """Add recurring fields to income table"""
    # Try both possible database locations
    db_paths = ['data/fina.db', 'instance/fina.db']
    conn = None
    
    for db_path in db_paths:
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            # Test if we can access the database
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            if 'income' in tables:
                print(f"Using database at: {db_path}")
                break
            else:
                conn.close()
                conn = None
        except:
            if conn:
                conn.close()
            conn = None
            continue
    
    if not conn:
        print("Error: Could not find fina.db with income table")
        return
    
    cursor = conn.cursor()
    
    # Check what columns exist
    cursor.execute("PRAGMA table_info(income)")
    existing_columns = [row[1] for row in cursor.fetchall()]
    print(f"Existing columns in income table: {existing_columns}")
    
    # Add next_due_date column if it doesn't exist
    if 'next_due_date' not in existing_columns:
        print("Adding next_due_date column...")
        cursor.execute('''
            ALTER TABLE income ADD COLUMN next_due_date DATETIME
        ''')
        print("✓ Added next_due_date column")
    else:
        print("✓ next_due_date column already exists")
    
    # Add last_created_date column if it doesn't exist
    if 'last_created_date' not in existing_columns:
        print("Adding last_created_date column...")
        cursor.execute('''
            ALTER TABLE income ADD COLUMN last_created_date DATETIME
        ''')
        print("✓ Added last_created_date column")
    else:
        print("✓ last_created_date column already exists")
    
    # Add is_active column if it doesn't exist
    if 'is_active' not in existing_columns:
        print("Adding is_active column...")
        cursor.execute('''
            ALTER TABLE income ADD COLUMN is_active BOOLEAN DEFAULT 1
        ''')
        print("✓ Added is_active column")
    else:
        print("✓ is_active column already exists")
    
    # Add auto_create column if it doesn't exist
    if 'auto_create' not in existing_columns:
        print("Adding auto_create column...")
        cursor.execute('''
            ALTER TABLE income ADD COLUMN auto_create BOOLEAN DEFAULT 0
        ''')
        print("✓ Added auto_create column")
    else:
        print("✓ auto_create column already exists")
    
    conn.commit()
    conn.close()
    
    print("\n✓ Migration completed successfully!")
    print("Recurring income fields added to Income table")

if __name__ == '__main__':
    print("Starting migration: add_recurring_income.py")
    print("=" * 60)
    migrate()
