"""
Backfill OCR text for existing documents and receipts
This will process all uploaded files that don't have OCR text yet
"""
import sys
import os
sys.path.insert(0, '/app')

from app import create_app, db
from app.models import Document, Expense
from app.ocr import extract_text_from_file

app = create_app()

def process_documents():
    """Process all documents without OCR text"""
    with app.app_context():
        # Find documents without OCR text
        documents = Document.query.filter(
            (Document.ocr_text == None) | (Document.ocr_text == '')
        ).all()
        
        print(f"\nFound {len(documents)} documents to process")
        
        processed = 0
        errors = 0
        
        for doc in documents:
            try:
                # Check if file type supports OCR
                if doc.file_type.lower() not in ['pdf', 'png', 'jpg', 'jpeg']:
                    print(f"⊘ Skipping {doc.original_filename} - {doc.file_type} not supported for OCR")
                    continue
                
                # Get absolute file path
                file_path = os.path.abspath(doc.file_path)
                
                if not os.path.exists(file_path):
                    print(f"✗ File not found: {doc.original_filename}")
                    errors += 1
                    continue
                
                print(f"Processing: {doc.original_filename}...", end=' ')
                
                # Extract OCR text
                ocr_text = extract_text_from_file(file_path, doc.file_type)
                
                if ocr_text:
                    doc.ocr_text = ocr_text
                    db.session.commit()
                    print(f"✓ Extracted {len(ocr_text)} characters")
                    processed += 1
                else:
                    print("⊘ No text found")
                    # Still update to empty string to mark as processed
                    doc.ocr_text = ""
                    db.session.commit()
                    
            except Exception as e:
                print(f"✗ Error: {str(e)}")
                errors += 1
        
        print(f"\n✓ Documents processed: {processed}")
        print(f"⊘ Documents with no text: {len(documents) - processed - errors}")
        print(f"✗ Errors: {errors}")


def process_receipts():
    """Process all expense receipts without OCR text"""
    with app.app_context():
        # Find expenses with receipts but no OCR text
        expenses = Expense.query.filter(
            Expense.receipt_path != None,
            (Expense.receipt_ocr_text == None) | (Expense.receipt_ocr_text == '')
        ).all()
        
        print(f"\nFound {len(expenses)} receipts to process")
        
        processed = 0
        errors = 0
        
        for expense in expenses:
            try:
                # Build absolute path
                receipt_path = expense.receipt_path.replace('/uploads/', '').lstrip('/')
                file_path = os.path.abspath(os.path.join('/app', 'uploads', receipt_path))
                
                if not os.path.exists(file_path):
                    print(f"✗ Receipt not found for: {expense.description}")
                    errors += 1
                    continue
                
                # Get file extension
                file_ext = file_path.rsplit('.', 1)[1].lower() if '.' in file_path else ''
                
                if file_ext not in ['pdf', 'png', 'jpg', 'jpeg']:
                    print(f"⊘ Skipping receipt for {expense.description} - {file_ext} not supported")
                    continue
                
                print(f"Processing receipt for: {expense.description}...", end=' ')
                
                # Extract OCR text
                ocr_text = extract_text_from_file(file_path, file_ext)
                
                if ocr_text:
                    expense.receipt_ocr_text = ocr_text
                    db.session.commit()
                    print(f"✓ Extracted {len(ocr_text)} characters")
                    processed += 1
                else:
                    print("⊘ No text found")
                    expense.receipt_ocr_text = ""
                    db.session.commit()
                    
            except Exception as e:
                print(f"✗ Error: {str(e)}")
                errors += 1
        
        print(f"\n✓ Receipts processed: {processed}")
        print(f"⊘ Receipts with no text: {len(expenses) - processed - errors}")
        print(f"✗ Errors: {errors}")


if __name__ == '__main__':
    print("=" * 60)
    print("OCR BACKFILL - Processing existing files")
    print("=" * 60)
    
    process_documents()
    process_receipts()
    
    print("\n" + "=" * 60)
    print("✓ OCR backfill completed!")
    print("=" * 60)
