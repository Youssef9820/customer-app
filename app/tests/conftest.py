import os
import sys
import types
from pathlib import Path

import pytest
from werkzeug.security import check_password_hash as _check_password_hash
from werkzeug.security import generate_password_hash as _generate_password_hash

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

bcrypt_stub = types.ModuleType("flask_bcrypt")


class _Bcrypt:
    def __init__(self, app=None):
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        self.app = app

    def generate_password_hash(self, password):
        hashed = _generate_password_hash(password)
        if isinstance(hashed, str):
            hashed = hashed.encode("utf-8")
        return hashed

    def check_password_hash(self, pw_hash, password):
        if isinstance(pw_hash, bytes):
            pw_hash = pw_hash.decode("utf-8")
        return _check_password_hash(pw_hash, password)


def _get_bcrypt(app=None):
    return _Bcrypt(app)


bcrypt_stub.Bcrypt = _get_bcrypt
sys.modules.setdefault("flask_bcrypt", bcrypt_stub)

dotenv_stub = types.ModuleType("dotenv")


def _load_dotenv(*args, **kwargs):
    return False


dotenv_stub.load_dotenv = _load_dotenv
sys.modules.setdefault("dotenv", dotenv_stub)

from app import create_app, db


@pytest.fixture
def app(tmp_path):
    db_path = tmp_path / "test.db"
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

    application = create_app()
    application.config.update(
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )

    yield application

    with application.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()