from flask import Blueprint, request, redirect, url_for
from flask_login import login_required, current_user
from app import db

bp = Blueprint('language', __name__, url_prefix='/language')

@bp.route('/switch/<lang>')
@login_required
def switch_language(lang):
    """Switch user's language preference"""
    allowed_languages = ['en', 'ro', 'es']
    
    if lang in allowed_languages:
        current_user.language = lang
        db.session.commit()
    
    # Redirect back to the referring page or dashboard
    return redirect(request.referrer or url_for('main.dashboard'))
