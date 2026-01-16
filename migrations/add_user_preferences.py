"""
Migration to add theme and notifications_enabled columns to users table
for persistent user preferences across sessions and devices.
"""
import sqlite3
import os

def migrate():
    """Add theme and notifications_enabled columns to users table"""
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'fina.db')
    
    if not os.path.exists(db_path):
        # Try data directory (Docker volume mount)
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'fina.db')
    
    if not os.path.exists(db_path):
        print("Database not found, skipping migration")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if theme column exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'theme' not in columns:
            print("Adding 'theme' column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN theme VARCHAR(10) DEFAULT 'dark'")
            print("Added 'theme' column successfully")
        else:
            print("'theme' column already exists")
        
        if 'notifications_enabled' not in columns:
            print("Adding 'notifications_enabled' column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN notifications_enabled BOOLEAN DEFAULT 1")
            print("Added 'notifications_enabled' column successfully")
        else:
            print("'notifications_enabled' column already exists")
        
        conn.commit()
        print("Migration completed successfully!")
        
    except Exception as e:
        print(f"Migration error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()
