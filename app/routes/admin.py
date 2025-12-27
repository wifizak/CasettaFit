from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.models import User, UserProfile
from app.forms import CreateUserForm, EditUserForm
from app.utils import save_uploaded_file, delete_uploaded_file

bp = Blueprint('admin', __name__, url_prefix='/admin')

# File upload configuration
UPLOAD_FOLDER = 'app/static/uploads/profiles'


def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/users')
@admin_required
def users():
    """User management page"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    users_query = User.query.order_by(User.created_at.desc())
    pagination = users_query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/users.html', users=pagination.items, pagination=pagination)


@bp.route('/users/create', methods=['GET', 'POST'])
@admin_required
def create_user():
    """Create new user"""
    form = CreateUserForm()
    
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            is_admin=form.is_admin.data
        )
        user.set_password(form.password.data)
        
        db.session.add(user)
        db.session.flush()  # Get user.id
        
        # Create user profile
        profile = UserProfile(user_id=user.id)
        
        # Handle profile picture upload
        if form.profile_picture.data:
            filename = save_uploaded_file(form.profile_picture.data, UPLOAD_FOLDER)
            if filename:
                profile.profile_picture = filename
        
        db.session.add(profile)
        db.session.commit()
        
        flash(f'User {user.username} created successfully!', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/create_user.html', form=form)


@bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """Edit existing user"""
    user = User.query.get_or_404(user_id)
    form = EditUserForm(user)
    
    if form.validate_on_submit():
        user.username = form.username.data
        user.is_admin = form.is_admin.data
        user.is_active = form.is_active.data
        
        if form.password.data:
            user.set_password(form.password.data)
        
        # Handle profile picture upload
        if form.profile_picture.data:
            # Get or create profile
            if not user.profile:
                profile = UserProfile(user_id=user.id)
                db.session.add(profile)
                db.session.flush()
            else:
                profile = user.profile
            
            # Delete old picture if exists
            if profile.profile_picture:
                delete_uploaded_file(profile.profile_picture, UPLOAD_FOLDER)
            
            # Save new picture using shared utility
            filename = save_uploaded_file(form.profile_picture.data, UPLOAD_FOLDER)
            if filename:
                profile.profile_picture = filename
        
        db.session.commit()
        flash(f'User {user.username} updated successfully!', 'success')
        return redirect(url_for('admin.users'))
    
    elif request.method == 'GET':
        form.username.data = user.username
        form.is_admin.data = user.is_admin
        form.is_active.data = user.is_active
    
    return render_template('admin/edit_user.html', form=form, user=user)


@bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Delete user"""
    user = User.query.get_or_404(user_id)
    
    if user.id == current_user.id:
        flash('You cannot delete your own account!', 'danger')
        return redirect(url_for('admin.users'))
    
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    flash(f'User {username} deleted successfully.', 'success')
    return redirect(url_for('admin.users'))
