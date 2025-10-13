# app/__init__.py

import os
import secrets
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from flask_wtf import CSRFProtect
from dotenv import load_dotenv

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()

def create_app():
    """Construct the core application."""
    app = Flask(__name__, instance_relative_config=False, template_folder='../templates', static_folder='../static')

    # --- Configure the App ---
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///customers.db')
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    # Protect session integrity by requiring a non-default SECRET_KEY outside of development.
    flask_env = os.environ.get('FLASK_ENV', '').lower()
    debug_env = os.environ.get('DEBUG')
    debug_normalized = debug_env.lower() if debug_env else None
    is_debug_false = debug_normalized in ('0', 'false', 'no', 'off')
    is_production = flask_env == 'production' or is_debug_false

    secret = os.environ.get('SECRET_KEY')
    if secret:
        app.config['SECRET_KEY'] = secret
    else:
        if is_production:
            # Refuse to boot in production when SECRET_KEY is missing to avoid predictable session signing keys.
            raise RuntimeError("Missing SECRET_KEY environment variable. Refusing to start in production without a SECRET_KEY.")
        # Generate an ephemeral random SECRET_KEY for developer convenience while keeping production strict.
        app.config['SECRET_KEY'] = secrets.token_urlsafe(32)

    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
# Enforce CSRF tokens with a bounded lifetime to block forged form submissions.
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600


    # --- Initialize extensions with the app ---
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)


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

        from .models import User, Currency, PaymentMethod
        db.create_all()

        if not Currency.query.first():
            db.session.add(Currency(code='EGP', symbol='E£'))
            db.session.commit()

        if not PaymentMethod.query.first():
            db.session.add_all([
                PaymentMethod(name='Cash'),
                PaymentMethod(name='Visa'),
                PaymentMethod(name='Transfer'),
                PaymentMethod(name='(by app)')
            ])
            db.session.commit()

        if not User.query.filter_by(username='admin').first():
            if is_production:
                # Avoid provisioning shared credentials in production to eliminate backdoor admin accounts.
                app.logger.info("Skipping admin seeding in production environment.")
            else:
                admin = User(username='admin', email='admin@example.com')
                admin.set_password('password')
                db.session.add(admin)
                db.session.commit()
                app.logger.info("✅ Default admin user created.")


        return app

