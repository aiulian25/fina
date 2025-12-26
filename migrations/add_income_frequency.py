"""
Migration to add frequency fields to Income model
Run with: python migrations/add_income_frequency.py
"""
import sqlite3
import os

def migrate():
    """Add frequency and custom_days columns to income table"""
    
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'fina.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(income)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add frequency column if it doesn't exist
        if 'frequency' not in columns:
            print("Adding frequency column to income table...")
            cursor.execute("""
                ALTER TABLE income 
                ADD COLUMN frequency VARCHAR(50) DEFAULT 'once'
            """)
            print("✓ Added frequency column")
        else:
            print("✓ Frequency column already exists")
        
        # Add custom_days column if it doesn't exist
        if 'custom_days' not in columns:
            print("Adding custom_days column to income table...")
            cursor.execute("""
                ALTER TABLE income 
                ADD COLUMN custom_days INTEGER
            """)
            print("✓ Added custom_days column")
        else:
            print("✓ Custom_days column already exists")
        
        conn.commit()
        print("\n✓ Income frequency migration completed successfully!")
        
    except Exception as e:
        conn.rollback()
        print(f"\n✗ Migration failed: {str(e)}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    print("Starting income frequency migration...")
    migrate()
