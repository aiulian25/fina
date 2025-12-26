"""
Migration to add Income model for tracking income sources
Run with: python migrations/add_income.py
"""
import sqlite3
import os

def migrate():
    """Add income table"""
    
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'fina.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='income'")
        if cursor.fetchone():
            print("✓ Income table already exists")
            conn.close()
            return
        
        # Create income table
        cursor.execute("""
            CREATE TABLE income (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                currency VARCHAR(3) DEFAULT 'USD',
                description VARCHAR(200) NOT NULL,
                source VARCHAR(100) NOT NULL,
                user_id INTEGER NOT NULL,
                tags TEXT DEFAULT '[]',
                date DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        conn.commit()
        print("✓ Created income table")
        print("✓ Migration completed successfully")
        
    except sqlite3.Error as e:
        print(f"✗ Migration failed: {e}")
        conn.rollback()
    finally:
        conn.close()


if __name__ == '__main__':
    print("Starting income migration...")
    migrate()
