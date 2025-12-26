"""
Migration: Add Smart Tags System
Creates Tag and ExpenseTag tables for smart expense tagging
"""
from app import create_app, db
from sqlalchemy import text

def upgrade():
    """Create Tag and ExpenseTag tables"""
    app = create_app()
    
    with app.app_context():
        # Create Tag table
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(50) NOT NULL,
                color VARCHAR(7) DEFAULT '#6366f1',
                icon VARCHAR(50) DEFAULT 'label',
                user_id INTEGER NOT NULL,
                is_auto BOOLEAN DEFAULT 0,
                use_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                UNIQUE (name, user_id)
            )
        """))
        
        # Create ExpenseTag junction table
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS expense_tags (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                expense_id INTEGER NOT NULL,
                tag_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (expense_id) REFERENCES expenses (id) ON DELETE CASCADE,
                FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE,
                UNIQUE (expense_id, tag_id)
            )
        """))
        
        # Create indexes for performance
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_tags_user_id ON tags(user_id)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_expense_tags_expense_id ON expense_tags(expense_id)
        """))
        
        db.session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_expense_tags_tag_id ON expense_tags(tag_id)
        """))
        
        db.session.commit()
        print("✓ Smart Tags tables created successfully")


def downgrade():
    """Remove Tag and ExpenseTag tables"""
    app = create_app()
    
    with app.app_context():
        db.session.execute(text("DROP TABLE IF EXISTS expense_tags"))
        db.session.execute(text("DROP TABLE IF EXISTS tags"))
        db.session.commit()
        print("✓ Smart Tags tables removed")


if __name__ == '__main__':
    print("Running migration: Add Smart Tags System")
    upgrade()
    print("Migration completed successfully!")
