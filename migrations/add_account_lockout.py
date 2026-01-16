"""
Migration: Add account lockout fields to users table
Security feature to prevent brute force attacks
"""

def run_migration(db, inspector):
    """Add failed_login_attempts, locked_until, and last_failed_login columns to users table"""
    
    if 'users' not in inspector.get_table_names():
        return
    
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    with db.engine.connect() as conn:
        if 'failed_login_attempts' not in columns:
            print("Migration: Adding 'failed_login_attempts' column to users table...")
            conn.execute(db.text("ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0"))
            conn.commit()
            print("Migration: 'failed_login_attempts' column added successfully")
        
        if 'locked_until' not in columns:
            print("Migration: Adding 'locked_until' column to users table...")
            conn.execute(db.text("ALTER TABLE users ADD COLUMN locked_until DATETIME"))
            conn.commit()
            print("Migration: 'locked_until' column added successfully")
        
        if 'last_failed_login' not in columns:
            print("Migration: Adding 'last_failed_login' column to users table...")
            conn.execute(db.text("ALTER TABLE users ADD COLUMN last_failed_login DATETIME"))
            conn.commit()
            print("Migration: 'last_failed_login' column added successfully")
