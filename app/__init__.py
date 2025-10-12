# app/__init__.py

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()

def create_app():
    """Construct the core application."""
    app = Flask(__name__, instance_relative_config=False, template_folder='../templates', static_folder='../static')

    # --- Configure the App ---
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///customers.db')
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-fallback-key-change-me')
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True

    # --- Initialize extensions with the app ---
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)

    login_manager.login_view = 'auth.signin'
    login_manager.login_next = 'main.index'

    with app.app_context():
        # --- Import parts of our application ---
        from . import models
        from .auth import auth_bp
        from .main import main_bp
        from .routes.dashboard import dashboard_bp
        from .routes.reports import reports_bp
        from .routes.imports import imports_bp
        from .routes.settings import settings_bp  

        # --- Register Blueprints ---
        app.register_blueprint(auth_bp)
        app.register_blueprint(main_bp)
        app.register_blueprint(dashboard_bp)
        app.register_blueprint(reports_bp)
        app.register_blueprint(imports_bp)
        app.register_blueprint(settings_bp)

        @login_manager.user_loader
        def load_user(user_id):
            return models.User.query.get(int(user_id))

        return app
