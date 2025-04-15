import os
import logging
from datetime import datetime

from flask import Flask, session, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect  # Import CSRFProtect

# Configure logging
logging.basicConfig(level=logging.INFO)  # Alterado para INFO em produção
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

# Initialize extensions
db = SQLAlchemy(model_class=Base)
login_manager = LoginManager()
csrf = CSRFProtect()  # Inicializa CSRFProtect

# Create the app
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///ac_maintenance.db")
app.config["SECRET_KEY"] = os.environ.get("SESSION_SECRET", os.urandom(24).hex())  # Gera uma chave segura
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Desativa totalmente o CSRF (temporariamente)
app.config["WTF_CSRF_ENABLED"] = True  # DESATIVA O CSRF GLOBALMENTE
app.config["WTF_CSRF_CHECK_DEFAULT"] = True  # DESATIVA A VERIFICAÇÃO PADRÃO DE CSRF
# Para reativar o CSRF no futuro:
# - Altere "WTF_CSRF_ENABLED" para True
# - Remova ou comente "WTF_CSRF_CHECK_DEFAULT"

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
csrf.init_app(app)  # Inicializa CSRFProtect (não será usado enquanto CSRF estiver desativado)
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

@app.template_filter('nl2br')
def nl2br(value):
    """Converte quebras de linha em tags <br>"""
    if not value:
        return ""
    return value.replace('\n', '<br>\n')

with app.app_context():
    # Import models to ensure they're registered with SQLAlchemy
    from models import User, Equipment, MaintenancePlan, MaintenanceSchedule, Notification, ChecklistItem, ChecklistTemplate, MaintenanceRecord, DiarioManutencao

    # Import and register blueprints
    from controllers.users import users_bp
    from controllers.equipment import equipment_bp
    from controllers.maintenance import maintenance_bp
    from controllers.reports import reports_bp
    from controllers.diario import diario_bp

    app.register_blueprint(users_bp, url_prefix='/users')  # Adiciona prefixos explícitos
    app.register_blueprint(equipment_bp, url_prefix='/equipment')
    app.register_blueprint(maintenance_bp, url_prefix='/maintenance')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(diario_bp, url_prefix='/diario')

    # Create all database tables
    db.create_all()

    # Set up user loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))