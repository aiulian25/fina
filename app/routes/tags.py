"""
Tags API Routes
Manage smart tags for expenses with auto-tagging capabilities
Security: All operations filtered by user_id
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import Tag, Expense, ExpenseTag
from sqlalchemy import func, desc
import re

bp = Blueprint('tags', __name__, url_prefix='/api/tags')


@bp.route('/', methods=['GET'])
@login_required
def get_tags():
    """
    Get all tags for current user
    Security: Filtered by user_id
    """
    # Get sort and filter parameters
    sort_by = request.args.get('sort_by', 'use_count')  # use_count, name, created_at
    order = request.args.get('order', 'desc')  # asc, desc
    
    # Base query filtered by user
    query = Tag.query.filter_by(user_id=current_user.id)
    
    # Apply sorting
    if sort_by == 'use_count':
        query = query.order_by(Tag.use_count.desc() if order == 'desc' else Tag.use_count.asc())
    elif sort_by == 'name':
        query = query.order_by(Tag.name.asc() if order == 'asc' else Tag.name.desc())
    else:  # created_at
        query = query.order_by(Tag.created_at.desc() if order == 'desc' else Tag.created_at.asc())
    
    tags = query.all()
    
    return jsonify({
        'success': True,
        'tags': [tag.to_dict() for tag in tags]
    })


@bp.route('/', methods=['POST'])
@login_required
def create_tag():
    """
    Create a new tag
    Security: Only creates for current_user
    """
    data = request.get_json()
    
    if not data.get('name'):
        return jsonify({'success': False, 'message': 'Tag name is required'}), 400
    
    # Sanitize and validate input
    name = str(data.get('name')).strip().lower()[:50]
    
    # Validate name format (alphanumeric, hyphens, underscores only)
    if not re.match(r'^[a-z0-9\-_]+$', name):
        return jsonify({
            'success': False, 
            'message': 'Tag name can only contain letters, numbers, hyphens, and underscores'
        }), 400
    
    # Check if tag already exists for this user
    existing_tag = Tag.query.filter_by(user_id=current_user.id, name=name).first()
    if existing_tag:
        return jsonify({
            'success': False,
            'message': 'Tag already exists',
            'tag': existing_tag.to_dict()
        }), 409
    
    # Sanitize color and icon
    color = str(data.get('color', '#6366f1')).strip()[:7]
    if not re.match(r'^#[0-9a-fA-F]{6}$', color):
        color = '#6366f1'
    
    icon = str(data.get('icon', 'label')).strip()[:50]
    if not re.match(r'^[a-z0-9_]+$', icon):
        icon = 'label'
    
    # Create tag
    tag = Tag(
        name=name,
        color=color,
        icon=icon,
        user_id=current_user.id,
        is_auto=False
    )
    
    db.session.add(tag)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'tag': tag.to_dict()
    }), 201


@bp.route('/<int:tag_id>', methods=['PUT'])
@login_required
def update_tag(tag_id):
    """
    Update a tag
    Security: Only owner can update
    """
    tag = Tag.query.filter_by(id=tag_id, user_id=current_user.id).first()
    
    if not tag:
        return jsonify({'success': False, 'message': 'Tag not found'}), 404
    
    data = request.get_json()
    
    # Update name if provided
    if data.get('name'):
        name = str(data.get('name')).strip().lower()[:50]
        if not re.match(r'^[a-z0-9\-_]+$', name):
            return jsonify({
                'success': False,
                'message': 'Tag name can only contain letters, numbers, hyphens, and underscores'
            }), 400
        
        # Check for duplicate name (excluding current tag)
        existing = Tag.query.filter(
            Tag.user_id == current_user.id,
            Tag.name == name,
            Tag.id != tag_id
        ).first()
        
        if existing:
            return jsonify({'success': False, 'message': 'Tag name already exists'}), 409
        
        tag.name = name
    
    # Update color if provided
    if data.get('color'):
        color = str(data.get('color')).strip()[:7]
        if re.match(r'^#[0-9a-fA-F]{6}$', color):
            tag.color = color
    
    # Update icon if provided
    if data.get('icon'):
        icon = str(data.get('icon')).strip()[:50]
        if re.match(r'^[a-z0-9_]+$', icon):
            tag.icon = icon
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'tag': tag.to_dict()
    })


@bp.route('/<int:tag_id>', methods=['DELETE'])
@login_required
def delete_tag(tag_id):
    """
    Delete a tag
    Security: Only owner can delete
    Note: This will also remove all associations with expenses (CASCADE)
    """
    tag = Tag.query.filter_by(id=tag_id, user_id=current_user.id).first()
    
    if not tag:
        return jsonify({'success': False, 'message': 'Tag not found'}), 404
    
    db.session.delete(tag)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Tag deleted successfully'
    })


@bp.route('/suggest', methods=['POST'])
@login_required
def suggest_tags():
    """
    Suggest tags based on text (description, OCR, etc.)
    Security: Only processes for current user
    """
    data = request.get_json()
    
    if not data or not data.get('text'):
        return jsonify({'success': False, 'message': 'Text is required'}), 400
    
    from app.utils.auto_tagger import extract_tags_from_text
    
    text = str(data.get('text'))
    max_tags = data.get('max_tags', 5)
    
    suggested_tags = extract_tags_from_text(text, max_tags=max_tags)
    
    return jsonify({
        'success': True,
        'suggested_tags': suggested_tags
    })


@bp.route('/popular', methods=['GET'])
@login_required
def get_popular_tags():
    """
    Get most popular tags for current user
    Security: Filtered by user_id
    """
    limit = request.args.get('limit', 10, type=int)
    
    tags = Tag.query.filter_by(user_id=current_user.id)\
        .filter(Tag.use_count > 0)\
        .order_by(Tag.use_count.desc())\
        .limit(limit)\
        .all()
    
    return jsonify({
        'success': True,
        'tags': [tag.to_dict() for tag in tags]
    })


@bp.route('/stats', methods=['GET'])
@login_required
def get_tag_stats():
    """
    Get tag usage statistics
    Security: Filtered by user_id
    """
    # Total tags count
    total_tags = Tag.query.filter_by(user_id=current_user.id).count()
    
    # Auto-generated tags count
    auto_tags = Tag.query.filter_by(user_id=current_user.id, is_auto=True).count()
    
    # Total tag uses across all expenses
    total_uses = db.session.query(func.sum(Tag.use_count))\
        .filter(Tag.user_id == current_user.id)\
        .scalar() or 0
    
    # Most used tag
    most_used_tag = Tag.query.filter_by(user_id=current_user.id)\
        .filter(Tag.use_count > 0)\
        .order_by(Tag.use_count.desc())\
        .first()
    
    return jsonify({
        'success': True,
        'stats': {
            'total_tags': total_tags,
            'auto_generated_tags': auto_tags,
            'manual_tags': total_tags - auto_tags,
            'total_uses': int(total_uses),
            'most_used_tag': most_used_tag.to_dict() if most_used_tag else None
        }
    })


@bp.route('/bulk-create', methods=['POST'])
@login_required
def bulk_create_tags():
    """
    Create multiple tags at once
    Security: Only creates for current_user
    """
    data = request.get_json()
    
    if not data or not data.get('tags') or not isinstance(data.get('tags'), list):
        return jsonify({'success': False, 'message': 'Tags array is required'}), 400
    
    created_tags = []
    errors = []
    
    for tag_data in data.get('tags'):
        try:
            name = str(tag_data.get('name', '')).strip().lower()[:50]
            
            if not name or not re.match(r'^[a-z0-9\-_]+$', name):
                errors.append(f"Invalid tag name: {tag_data.get('name')}")
                continue
            
            # Check if already exists
            existing = Tag.query.filter_by(user_id=current_user.id, name=name).first()
            if existing:
                created_tags.append(existing.to_dict())
                continue
            
            # Validate color and icon
            color = str(tag_data.get('color', '#6366f1')).strip()[:7]
            if not re.match(r'^#[0-9a-fA-F]{6}$', color):
                color = '#6366f1'
            
            icon = str(tag_data.get('icon', 'label')).strip()[:50]
            if not re.match(r'^[a-z0-9_]+$', icon):
                icon = 'label'
            
            tag = Tag(
                name=name,
                color=color,
                icon=icon,
                user_id=current_user.id,
                is_auto=tag_data.get('is_auto', False)
            )
            
            db.session.add(tag)
            created_tags.append(tag.to_dict())
            
        except Exception as e:
            errors.append(f"Error creating tag {tag_data.get('name')}: {str(e)}")
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'created': len(created_tags),
        'tags': created_tags,
        'errors': errors
    })
