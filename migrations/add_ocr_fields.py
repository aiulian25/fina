"""
Migration: Add OCR text fields to expenses and documents tables
Run this after updating models to add OCR support
"""
import sqlite3
import os

def migrate():
    """Add ocr_text columns to documents and expenses tables"""
    
    # Connect to database
    db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'fina.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Add ocr_text to documents table
        print("Adding ocr_text column to documents table...")
        cursor.execute("""
            ALTER TABLE documents 
            ADD COLUMN ocr_text TEXT
        """)
        print("✓ Added ocr_text to documents")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("✓ ocr_text column already exists in documents")
        else:
            print(f"Error adding ocr_text to documents: {e}")
    
    try:
        # Add receipt_ocr_text to expenses table
        print("Adding receipt_ocr_text column to expenses table...")
        cursor.execute("""
            ALTER TABLE expenses 
            ADD COLUMN receipt_ocr_text TEXT
        """)
        print("✓ Added receipt_ocr_text to expenses")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("✓ receipt_ocr_text column already exists in expenses")
        else:
            print(f"Error adding receipt_ocr_text to expenses: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n✓ Migration completed successfully!")
    print("OCR functionality is now enabled for documents and receipts.")

if __name__ == '__main__':
    migrate()
