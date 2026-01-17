from flask import Blueprint, request, jsonify, send_file, current_app
from flask_login import login_required, current_user
from app import db
from app.models import Document
from werkzeug.utils import secure_filename
import os
import mimetypes
from datetime import datetime
from app.ocr import extract_text_from_file

bp = Blueprint('documents', __name__, url_prefix='/api/documents')

# Max file size: 10MB
MAX_FILE_SIZE = 10 * 1024 * 1024

# Allowed file types for documents
ALLOWED_DOCUMENT_TYPES = {
    'pdf': 'application/pdf',
    'csv': 'text/csv',
    'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'xls': 'application/vnd.ms-excel',
    'png': 'image/png',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg'
}

def allowed_document(filename):
    """Check if file type is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_DOCUMENT_TYPES.keys()


def resolve_file_path(stored_path):
    """
    Resolve stored file path to actual file location.
    Handles both absolute paths and relative paths (from backup imports).
    """
    # If it's already an absolute path and exists, use it
    if os.path.isabs(stored_path) and os.path.exists(stored_path):
        return stored_path
    
    # Try relative to upload folder
    upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
    
    # Try as-is relative to upload folder (e.g., "documents/file.pdf")
    full_path = os.path.join(upload_folder, stored_path)
    if os.path.exists(full_path):
        return full_path
    
    # Try just the basename in the appropriate subfolder
    basename = os.path.basename(stored_path)
    
    # Check in documents subfolder
    doc_path = os.path.join(upload_folder, 'documents', basename)
    if os.path.exists(doc_path):
        return doc_path
    
    # Return original path (will fail with "file not found")
    return stored_path

def get_file_type_icon(file_type):
    """Get material icon name for file type"""
    icons = {
        'pdf': 'picture_as_pdf',
        'csv': 'table_view',
        'xlsx': 'table_view',
        'xls': 'table_view',
        'png': 'image',
        'jpg': 'image',
        'jpeg': 'image'
    }
    return icons.get(file_type.lower(), 'description')

@bp.route('/', methods=['GET'])
@login_required
def get_documents():
    """
    Get all documents for current user
    Security: Filters by current_user.id
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search = request.args.get('search', '')
    
    # Security: Only get documents for current user
    query = Document.query.filter_by(user_id=current_user.id)
    
    if search:
        query = query.filter(Document.original_filename.ilike(f'%{search}%'))
    
    pagination = query.order_by(Document.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'documents': [doc.to_dict() for doc in pagination.items],
        'pagination': {
            'page': page,
            'pages': pagination.pages,
            'total': pagination.total,
            'per_page': per_page
        }
    })


@bp.route('/', methods=['POST'])
@login_required
def upload_document():
    """
    Upload a new document
    Security: Associates document with current_user.id
    Security: Validates file content matches extension
    """
    from app.utils import validate_file_content
    
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file provided'}), 400
    
    file = request.files['file']
    
    if not file or not file.filename:
        return jsonify({'success': False, 'message': 'No file selected'}), 400
    
    if not allowed_document(file.filename):
        return jsonify({
            'success': False, 
            'message': 'Invalid file type. Allowed: PDF, CSV, XLS, XLSX, PNG, JPG'
        }), 400
    
    # Security: Validate file content matches extension
    is_valid, error_msg, detected_type = validate_file_content(
        file, 
        allowed_extensions=set(ALLOWED_DOCUMENT_TYPES.keys())
    )
    if not is_valid:
        return jsonify({'success': False, 'message': error_msg}), 400
    
    # Check file size
    file.seek(0, os.SEEK_END)
    file_size = file.tell()
    file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        return jsonify({
            'success': False, 
            'message': f'File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB'
        }), 400
    
    # Generate secure filename
    original_filename = secure_filename(file.filename)
    file_ext = original_filename.rsplit('.', 1)[1].lower()
    timestamp = datetime.utcnow().timestamp()
    filename = f"{current_user.id}_{timestamp}_{original_filename}"
    
    # Create documents directory if it doesn't exist
    documents_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'documents')
    os.makedirs(documents_dir, exist_ok=True)
    
    # Save file
    file_path = os.path.join(documents_dir, filename)
    file.save(file_path)
    
    # Get document category from form data
    document_category = request.form.get('category', 'Other')
    
    # Process OCR for supported file types (PDF, PNG, JPG, JPEG)
    ocr_text = ""
    if file_ext in ['pdf', 'png', 'jpg', 'jpeg']:
        try:
            # Get absolute path for OCR processing
            abs_file_path = os.path.abspath(file_path)
            ocr_text = extract_text_from_file(abs_file_path, file_ext)
            print(f"OCR extracted {len(ocr_text)} characters from {original_filename}")
        except Exception as e:
            print(f"OCR processing failed for {original_filename}: {str(e)}")
            # Continue without OCR text - non-critical failure
    
    # Create document record - Security: user_id is current_user.id
    document = Document(
        filename=filename,
        original_filename=original_filename,
        file_path=file_path,
        file_size=file_size,
        file_type=file_ext.upper(),
        mime_type=ALLOWED_DOCUMENT_TYPES.get(file_ext, 'application/octet-stream'),
        document_category=document_category,
        status='uploaded',
        ocr_text=ocr_text,
        user_id=current_user.id
    )
    
    db.session.add(document)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Document uploaded successfully',
        'document': document.to_dict()
    }), 201


@bp.route('/<int:document_id>/view', methods=['GET'])
@login_required
def view_document(document_id):
    """
    View/preview a document (inline, not download)
    Security: Checks document belongs to current_user
    """
    # Security: Filter by user_id
    document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
    
    if not document:
        return jsonify({'success': False, 'message': 'Document not found'}), 404
    
    # Resolve path (handles both absolute and relative paths from backups)
    actual_path = resolve_file_path(document.file_path)
    
    if not os.path.exists(actual_path):
        return jsonify({'success': False, 'message': 'File not found on server'}), 404
    
    return send_file(
        actual_path,
        mimetype=document.mime_type,
        as_attachment=False
    )


@bp.route('/<int:document_id>/download', methods=['GET'])
@login_required
def download_document(document_id):
    """
    Download a document
    Security: Checks document belongs to current_user
    """
    # Security: Filter by user_id
    document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
    
    if not document:
        return jsonify({'success': False, 'message': 'Document not found'}), 404
    
    # Resolve path (handles both absolute and relative paths from backups)
    actual_path = resolve_file_path(document.file_path)
    
    if not os.path.exists(actual_path):
        return jsonify({'success': False, 'message': 'File not found on server'}), 404
    
    return send_file(
        actual_path,
        mimetype=document.mime_type,
        as_attachment=True,
        download_name=document.original_filename
    )


@bp.route('/<int:document_id>', methods=['DELETE'])
@login_required
def delete_document(document_id):
    """
    Delete a document
    Security: Checks document belongs to current_user
    """
    # Security: Filter by user_id
    document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
    
    if not document:
        return jsonify({'success': False, 'message': 'Document not found'}), 404
    
    # Resolve and delete physical file
    actual_path = resolve_file_path(document.file_path)
    if os.path.exists(actual_path):
        try:
            os.remove(actual_path)
        except Exception as e:
            print(f"Error deleting file: {e}")
    
    # Delete database record
    db.session.delete(document)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Document deleted successfully'})


@bp.route('/<int:document_id>/status', methods=['PUT'])
@login_required
def update_document_status(document_id):
    """
    Update document status (e.g., mark as analyzed)
    Security: Checks document belongs to current_user
    """
    # Security: Filter by user_id
    document = Document.query.filter_by(id=document_id, user_id=current_user.id).first()
    
    if not document:
        return jsonify({'success': False, 'message': 'Document not found'}), 404
    
    data = request.get_json()
    new_status = data.get('status')
    
    if new_status not in ['uploaded', 'processing', 'analyzed', 'error']:
        return jsonify({'success': False, 'message': 'Invalid status'}), 400
    
    document.status = new_status
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Document status updated',
        'document': document.to_dict()
    })
