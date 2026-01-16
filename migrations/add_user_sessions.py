"""
Migration: Add user_sessions table for active session tracking
Run with: python migrations/add_user_sessions.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from sqlalchemy import text

def migrate():
    app = create_app()
    with app.app_context():
        # Check if table exists
        result = db.session.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='user_sessions'
        """))
        
        if result.fetchone():
            print("Table 'user_sessions' already exists")
            return
        
        # Create user_sessions table
        db.session.execute(text("""
            CREATE TABLE user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token VARCHAR(64) UNIQUE NOT NULL,
                ip_address VARCHAR(45),
                user_agent VARCHAR(500),
                device_type VARCHAR(50),
                browser VARCHAR(100),
                os VARCHAR(100),
                location VARCHAR(200),
                is_current BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME,
                is_active BOOLEAN DEFAULT 1,
                revoked_at DATETIME,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """))
        
        # Create index for faster lookups
        db.session.execute(text("""
            CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id)
        """))
        
        db.session.execute(text("""
            CREATE INDEX idx_user_sessions_token ON user_sessions(session_token)
        """))
        
        db.session.execute(text("""
            CREATE INDEX idx_user_sessions_active ON user_sessions(user_id, is_active)
        """))
        
        db.session.commit()
        print("Successfully created 'user_sessions' table with indexes")

if __name__ == '__main__':
    migrate()
