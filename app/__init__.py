# app/__init__.py
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
import os

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()

# Initialize Flask-Limiter without default limits
limiter = Limiter(
    key_func=get_remote_address,  # Use the client's IP address for rate limiting
    storage_uri="memory://"  # Use in-memory storage (for development)
)

def create_app():
    app = Flask(__name__)
    
    # Set configuration from environment variables
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'your_secret_key_here'
    
    # Fix the SQLAlchemy postgres vs postgresql issue
    DATABASE_URL = os.environ.get("DATABASE_URL")
    if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    
    # Register Blueprints
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.employee import employee_bp
    from app.routes.worktime import worktime_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(employee_bp)
    app.register_blueprint(worktime_bp)
    
    # Error handler for rate limiting
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return render_template('errors/429.html'), 429
    
    return app
