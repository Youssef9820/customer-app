import pytest

from app import create_app
from app.models import User


@pytest.fixture(autouse=True)
def reset_env(monkeypatch):
    """Ensure environment variables are isolated per test."""
    for key in ("FLASK_ENV", "DEBUG", "SECRET_KEY", "DATABASE_URL"):
        monkeypatch.delenv(key, raising=False)
    yield
    for key in ("FLASK_ENV", "DEBUG", "SECRET_KEY", "DATABASE_URL"):
        monkeypatch.delenv(key, raising=False)


def test_production_requires_secret(monkeypatch):
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")

    with pytest.raises(RuntimeError):
        create_app()


def test_admin_seed_runs_in_non_production(monkeypatch, tmp_path):
    db_path = tmp_path / "dev.db"
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.setenv("DEBUG", "True")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    app = create_app()

    with app.app_context():
        admin = User.query.filter_by(username="admin").first()
        assert admin is not None


def test_admin_seeding_skipped_in_production(monkeypatch, tmp_path, caplog):
    db_path = tmp_path / "prod.db"
    monkeypatch.setenv("FLASK_ENV", "production")
    monkeypatch.setenv("SECRET_KEY", "prod-secret")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    caplog.set_level("INFO")
    app = create_app()

    with app.app_context():
        admin = User.query.filter_by(username="admin").first()
        assert admin is None

    assert "Skipping admin seeding in production environment." in caplog.text