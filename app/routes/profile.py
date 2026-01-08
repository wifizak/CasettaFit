from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import UserProfile, User
from app.forms import UserProfileForm
from app.utils import save_uploaded_file, delete_uploaded_file

bp = Blueprint('profile', __name__, url_prefix='/profile')

# File upload configuration
UPLOAD_FOLDER = 'app/static/uploads/profiles'


@bp.route('/')
@login_required
def index():
    """View user profile"""
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()
    
    return render_template('profile/index.html', profile=profile, user=current_user)


@bp.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
    """Edit user profile"""
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.flush()
    
    form = UserProfileForm()
    
    if form.validate_on_submit():
        # Handle profile picture upload
        if form.profile_picture.data:
            # Delete old picture if exists
            if profile.profile_picture:
                delete_uploaded_file(profile.profile_picture, UPLOAD_FOLDER)
            
            # Save new picture using shared utility
            filename = save_uploaded_file(form.profile_picture.data, UPLOAD_FOLDER)
            if filename:
                profile.profile_picture = filename
        
        # Update weight unit
        profile.weight_unit = form.weight_unit.data
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile.index'))
    
    elif request.method == 'GET':
        form.weight_unit.data = profile.weight_unit
    
    return render_template('profile/edit.html', form=form, profile=profile)


@bp.route('/remove-picture', methods=['POST'])
@login_required
def remove_picture():
    """Remove profile picture"""
    profile = UserProfile.query.filter_by(user_id=current_user.id).first()
    
    if profile and profile.profile_picture:
        # Delete file using shared utility
        delete_uploaded_file(profile.profile_picture, UPLOAD_FOLDER)
        
        # Update database
        profile.profile_picture = None
        db.session.commit()
        flash('Profile picture removed.', 'success')
    
    return redirect(url_for('profile.edit'))
