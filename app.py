import os
import logging
from datetime import datetime

from flask import Flask, session, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager, current_user

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()

# Create the app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///ac_maintenance.db")
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'

@app.before_request
def before_request():
    if current_user.is_authenticated:
        session.permanent = True
        g.user = current_user
    else:
        g.user = None

@app.template_filter('format_date')
def format_date(value):
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d')
    return value

@app.template_filter('format_datetime')
def format_datetime(value):
    if isinstance(value, datetime):
        return value.strftime('%Y-%m-%d %H:%M')
    return value

with app.app_context():
    # Import models to ensure they're registered with SQLAlchemy
    from models import User, Equipment, MaintenancePlan, MaintenanceSchedule, Notification, ChecklistItem, ChecklistTemplate, MaintenanceRecord

    # Import and register blueprints
    from controllers.users import users_bp
    from controllers.equipment import equipment_bp
    from controllers.maintenance import maintenance_bp
    from controllers.reports import reports_bp

    app.register_blueprint(users_bp)
    app.register_blueprint(equipment_bp)
    app.register_blueprint(maintenance_bp)
    app.register_blueprint(reports_bp)

    # Create all database tables
    db.create_all()

    # Set up user loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
