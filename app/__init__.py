from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from app.config import config
import json

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


def create_app(config_name='default'):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db, directory='app/migrations')
    login_manager.init_app(app)
    
    # Configure login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.session_protection = 'strong'
    
    # Register blueprints
    from app.routes import auth, main, admin, exercises, equipment, gym, programs, calendar, workout, history
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(exercises.bp)
    app.register_blueprint(equipment.bp)
    app.register_blueprint(gym.bp)
    app.register_blueprint(programs.bp)
    app.register_blueprint(calendar.bp)
    app.register_blueprint(workout.bp)
    app.register_blueprint(history.bp)
    
    # Register custom Jinja filters
    @app.template_filter('from_json')
    def from_json_filter(s):
        """Convert JSON string to Python object"""
        if s:
            try:
                return json.loads(s)
            except (json.JSONDecodeError, TypeError):
                return []
        return []
    
    return app
