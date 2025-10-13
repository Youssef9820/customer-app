import io
import zipfile

import pytest
from openpyxl import Workbook

from app import create_app, db
from app.models import College, Country, Customer, University
from app.upload_utils import MAX_UPLOAD_SIZE


@pytest.fixture(autouse=True)
def reset_env(monkeypatch):
    for key in ("FLASK_ENV", "DEBUG", "SECRET_KEY", "DATABASE_URL"):
        monkeypatch.delenv(key, raising=False)
    yield
    for key in ("FLASK_ENV", "DEBUG", "SECRET_KEY", "DATABASE_URL"):
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def app(monkeypatch, tmp_path):
    db_path = tmp_path / "upload.db"
    monkeypatch.setenv("FLASK_ENV", "development")
    monkeypatch.setenv("DEBUG", "True")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)

    with app.app_context():
        country = Country(name="Egypt")
        university = University(name="Cairo University", country=country)
        college = College(name="Engineering", university=university)
        db.session.add_all([country, university, college])
        db.session.commit()

    yield app

    with app.app_context():
        db.drop_all()


@pytest.fixture
def client(app):
    client = app.test_client()
    response = client.post(
        "/signin",
        data={"username": "admin", "password": "password"},
        follow_redirects=True,
    )
    assert response.status_code in (200, 302, 303)
    return client


def build_csv_payload(content: str, filename: str = "customers.csv"):
    return {"import_file": (io.BytesIO(content.encode("utf-8")), filename)}


def build_valid_xlsx() -> io.BytesIO:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["full_name", "email", "whatsapp_number", "year", "country", "university", "college"])
    sheet.append([
        "Alice Example",
        "alice@example.com",
        "123456789",
        "1",
        "Egypt",
        "Cairo University",
        "Engineering",
    ])
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


def build_macro_xlsx() -> io.BytesIO:
    base = build_valid_xlsx()
    base.seek(0)
    macro_buffer = io.BytesIO()
    with zipfile.ZipFile(base, "r") as original_zip:
        with zipfile.ZipFile(macro_buffer, "w") as macro_zip:
            for item in original_zip.infolist():
                macro_zip.writestr(item, original_zip.read(item.filename))
            macro_zip.writestr("xl/vbaProject.bin", b"fake macro")
    macro_buffer.seek(0)
    return macro_buffer


def test_upload_rejects_files_over_size_limit(client):
    huge_payload = io.BytesIO(b"a" * (MAX_UPLOAD_SIZE + 1))
    response = client.post(
        "/import_customers",
        data={"import_file": (huge_payload, "too_big.csv")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 413
    assert "10 MB" in response.get_data(as_text=True)


def test_upload_rejects_disallowed_extension(client):
    response = client.post(
        "/import_customers",
        data={"import_file": (io.BytesIO(b"bad"), "malware.exe")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 415
    assert "Invalid file type" in response.get_data(as_text=True)


def test_upload_rejects_xlsx_with_macros(client):
    response = client.post(
        "/import_customers",
        data={"import_file": (build_macro_xlsx(), "macro.xlsx")},
        content_type="multipart/form-data",
    )
    assert response.status_code in (400, 415)
    assert "macro" in response.get_data(as_text=True).lower()


def test_valid_csv_upload_creates_customer(client, app):
    payload = (
        "full_name,email,whatsapp_number,year,country,university,college\n"
        "Bob Example,bob@example.com,555,2,Egypt,Cairo University,Engineering\n"
    )
    response = client.post(
        "/import_customers",
        data=build_csv_payload(payload),
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)
    with app.app_context():
        customer = Customer.query.filter_by(full_name="Bob Example").one()
        assert customer.email == "bob@example.com"


def test_valid_xlsx_upload_creates_customer(client, app):
    response = client.post(
        "/import_customers",
        data={"import_file": (build_valid_xlsx(), "customers.xlsx")},
        content_type="multipart/form-data",
        follow_redirects=False,
    )
    assert response.status_code in (302, 303)
    with app.app_context():
        customer = Customer.query.filter_by(full_name="Alice Example").one()
        assert customer.whatsapp_number == "123456789"