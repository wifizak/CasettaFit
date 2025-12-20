from flask import Blueprint, render_template
from flask_login import login_required, current_user

bp = Blueprint('main', __name__)


@bp.route('/')
@login_required
def index():
    """Dashboard / home page"""
    return render_template('main/dashboard.html')
