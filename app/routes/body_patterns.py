from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
import json
from app import db
from app.models import BodyPattern
from app.forms import BodyPatternForm

bp = Blueprint('body_patterns', __name__, url_prefix='/body-patterns')


@bp.route('/')
@login_required
def index():
    """List body patterns"""
    user_patterns = BodyPattern.query.filter_by(user_id=current_user.id).order_by(BodyPattern.name).all()
    shared_patterns = BodyPattern.query.filter_by(user_id=None).order_by(BodyPattern.name).all()
    
    # Parse JSON for display
    for pattern in user_patterns + shared_patterns:
        pattern.days = json.loads(pattern.pattern_json)
    
    return render_template('body_patterns/index.html', 
                         user_patterns=user_patterns,
                         shared_patterns=shared_patterns)


@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create new body pattern"""
    form = BodyPatternForm()
    
    if form.validate_on_submit():
        # Parse day labels from textarea (one per line)
        day_labels = [line.strip() for line in form.pattern_days.data.split('\n') if line.strip()]
        
        if len(day_labels) < 1:
            flash('Please enter at least one day label.', 'danger')
            return render_template('body_patterns/create.html', form=form)
        
        pattern = BodyPattern(
            name=form.name.data,
            user_id=current_user.id,
            pattern_json=json.dumps(day_labels)
        )
        
        db.session.add(pattern)
        db.session.commit()
        
        flash(f'Body pattern "{pattern.name}" created successfully!', 'success')
        return redirect(url_for('body_patterns.index'))
    
    return render_template('body_patterns/create.html', form=form)


@bp.route('/<int:pattern_id>/delete', methods=['POST'])
@login_required
def delete(pattern_id):
    """Delete body pattern"""
    pattern = BodyPattern.query.get_or_404(pattern_id)
    
    # Check permissions
    if pattern.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to delete this pattern.', 'danger')
        return redirect(url_for('body_patterns.index'))
    
    name = pattern.name
    db.session.delete(pattern)
    db.session.commit()
    
    flash(f'Body pattern "{name}" deleted successfully.', 'success')
    return redirect(url_for('body_patterns.index'))
