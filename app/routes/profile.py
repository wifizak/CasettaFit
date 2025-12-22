from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import uuid
import os
from app import db
from app.models import UserProfile, User
from app.forms import UserProfileForm

bp = Blueprint('profile', __name__, url_prefix='/profile')

# File upload configuration
UPLOAD_FOLDER = 'app/static/uploads/profiles'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_profile_picture(file):
    """Save uploaded profile picture and return the filename"""
    if file and allowed_file(file.filename):
        # Generate unique filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{uuid.uuid4().hex}.{ext}"
        
        # Ensure upload directory exists
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
        # Save file
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        return filename
    return None


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
                old_path = os.path.join(UPLOAD_FOLDER, profile.profile_picture)
                if os.path.exists(old_path):
                    os.remove(old_path)
            
            # Save new picture
            filename = save_profile_picture(form.profile_picture.data)
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
        # Delete file
        filepath = os.path.join(UPLOAD_FOLDER, profile.profile_picture)
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # Update database
        profile.profile_picture = None
        db.session.commit()
        flash('Profile picture removed.', 'success')
    
    return redirect(url_for('profile.edit'))
