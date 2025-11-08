# app/__init__.py

import os
import secrets
from flask import Flask, abort, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
import importlib
import importlib.util
from dotenv import load_dotenv
_flask_wtf_spec = importlib.util.find_spec("flask_wtf")
if _flask_wtf_spec is not None:
    CSRFProtect = importlib.import_module("flask_wtf").CSRFProtect
else:
    class CSRFProtect:  # type: ignore
        """Lightweight fallback used during testing when Flask-WTF is unavailable."""

        def __init__(self, app=None):
            self.app = None
            if app is not None:
                self.init_app(app)

        def init_app(self, app):
            self.app = app
            app.extensions.setdefault("csrf", self)
            app.before_request(self._protect)
            app.jinja_env.globals.setdefault("csrf_token", self.generate_csrf_token)

        def generate_csrf_token(self):
            token = session.get("_csrf_token")
            if not token:
                token = secrets.token_urlsafe(32)
                session["_csrf_token"] = token
            return token

        def _protect(self):
            if request.method in ("GET", "HEAD", "OPTIONS", "TRACE"):
                # Ensure a token is generated for subsequent POSTs.
                self.generate_csrf_token()
                return

            if not self.app or not self.app.config.get("WTF_CSRF_ENABLED", True):
                return

            session_token = session.get("_csrf_token")
            submitted_token = request.form.get("csrf_token") or request.headers.get("X-CSRFToken")
            if not session_token or session_token != submitted_token:
                abort(400)

_flask_limiter_spec = importlib.util.find_spec("flask_limiter")
if _flask_limiter_spec is not None:
    Limiter = importlib.import_module("flask_limiter").Limiter
    get_remote_address = importlib.import_module("flask_limiter.util").get_remote_address
else:
    class Limiter:  # type: ignore
        """Minimal rate-limiter stub for test environments without Flask-Limiter."""

        def __init__(self, key_func=None, default_limits=None):
            self.key_func = key_func
            self.default_limits = default_limits or []
            self.app = None
            self.enabled = True

        def init_app(self, app):
            self.app = app

        def limit(self, _limit_value):
            def decorator(func):
                return func

            return decorator

    def get_remote_address():  # type: ignore
        return "127.0.0.1"



load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()
csrf = CSRFProtect()
# Throttle inbound requests globally so brute-force bursts are capped across the app.
limiter = Limiter(get_remote_address, default_limits=["200 per day", "50 per hour"])


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
    
    # Ensure secure cookies in production while keeping local development usable
    # over plain HTTP (for example when accessing the app via a LAN IP).
    app.config['SESSION_COOKIE_SECURE'] = is_production
    app.config['SESSION_COOKIE_HTTPONLY'] = True

# Enforce CSRF tokens with a bounded lifetime to block forged form submissions.
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600

    if not is_production:
        # --- Allow session cookies over local network (192.168.x.x) ---
          app.config['SESSION_COOKIE_DOMAIN'] = None
          app.config['SESSION_COOKIE_SECURE'] = False  # Allow HTTP
          app.config['SESSION_COOKIE_SAMESITE'] = None  # Allow LAN IPs like 192.168.x.x
          app.config['WTF_CSRF_SSL_STRICT'] = False
    else:
        app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Protect against CSRF
        app.config['WTF_CSRF_SSL_STRICT'] = True  # Require HTTPS for CSRF



    # --- Initialize extensions with the app ---
    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    csrf.init_app(app)
    # Enforce rate limiting after CSRF is ready to slow down credential stuffing attempts.
    limiter.init_app(app)

    if app.config.get("TESTING"):
        limiter.enabled = False

    @app.before_request
    def _disable_limiter_during_tests():
        if app.config.get("TESTING"):
            limiter.enabled = False



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





        return app

