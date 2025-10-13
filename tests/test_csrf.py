import re

import pytest

from app import create_app


@pytest.fixture(autouse=True)
def reset_env(monkeypatch):
    """Ensure environment variables are isolated per test."""
    for key in ("FLASK_ENV", "DEBUG", "SECRET_KEY", "DATABASE_URL"):
        monkeypatch.delenv(key, raising=False)
    yield
    for key in ("FLASK_ENV", "DEBUG", "SECRET_KEY", "DATABASE_URL"):
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def app(monkeypatch, tmp_path):
    db_path = tmp_path / "csrf.db"
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.setenv("DEBUG", "True")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=True)
    return app


@pytest.fixture
def client(app):
    return app.test_client()


def extract_csrf_token(html: str) -> str:
    match = re.search(r'name="csrf_token" value="([^"]+)"', html)
    assert match, "CSRF token not found in form"
    return match.group(1)


def test_post_without_csrf_token_is_rejected(client):
    response = client.post("/signin", data={"username": "admin", "password": "password"})
    assert response.status_code == 400


def test_post_with_valid_csrf_token_succeeds(client):
    get_response = client.get("/signin")
    token = extract_csrf_token(get_response.get_data(as_text=True))

    response = client.post(
        "/signin",
        data={
            "username": "admin",
            "password": "password",
            "csrf_token": token,
        },
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)