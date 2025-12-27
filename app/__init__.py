from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from app.config import config
from sqlalchemy import event
from sqlalchemy.engine import Engine
import json
import logging

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()


# SQLite-specific optimizations
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Enable SQLite optimizations on each connection"""
    cursor = dbapi_conn.cursor()
    
    # CRITICAL: Enable foreign key constraints (SQLite doesn't enforce by default!)
    cursor.execute("PRAGMA foreign_keys=ON")
    
    # Performance optimizations
    cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging for better concurrency
    cursor.execute("PRAGMA synchronous=NORMAL")  # Faster writes with WAL (still safe)
    cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache for better read performance
    cursor.execute("PRAGMA temp_store=MEMORY")  # Temporary tables in RAM
    
    cursor.close()


def create_app(config_name='default'):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Configure logging
    if not app.debug:
        # Production logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]',
            handlers=[
                logging.FileHandler('logs/casettafit.log'),
                logging.StreamHandler()
            ]
        )
        app.logger.setLevel(logging.INFO)
        app.logger.info('CasettaFit startup')
    else:
        # Development logging
        logging.basicConfig(level=logging.DEBUG)
        app.logger.setLevel(logging.DEBUG)
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db, directory='app/migrations')
    login_manager.init_app(app)
    
    # Configure login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.session_protection = 'strong'
    
    # Register blueprints
    from app.routes import auth, main, admin, exercises, equipment, gym, programs, calendar, workout, history, reports, goals, profile
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
    app.register_blueprint(reports.bp)
    app.register_blueprint(goals.bp)
    app.register_blueprint(profile.bp)
    
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
