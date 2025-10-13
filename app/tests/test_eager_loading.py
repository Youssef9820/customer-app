import io

import pandas as pd
import pytest
from sqlalchemy import event

from app import db
from app.models import (
    College,
    Country,
    Currency,
    Customer,
    Module,
    Payment,
    PaymentMethod,
    Subject,
    Term,
    University,
)


class QueryCounter:
    def __init__(self, engine):
        self.engine = engine
        self.selects = 0

    def before_cursor_execute(self, conn, cursor, statement, parameters, context, executemany):
        if statement.lstrip().upper().startswith("SELECT"):
            self.selects += 1

    def __enter__(self):
        event.listen(self.engine, "before_cursor_execute", self.before_cursor_execute)
        return self

    def __exit__(self, exc_type, exc, tb):
        event.remove(self.engine, "before_cursor_execute", self.before_cursor_execute)

    def reset(self):
        self.selects = 0


@pytest.fixture
def seeded_data(app):
    with app.app_context():
        country = Country(name="Egypt")
        university = University(name="Cairo University", country=country)
        college = College(name="Engineering", university=university)
        db.session.add_all([country, university, college])

        customers = []
        for i in range(3):
            customer = Customer(
                full_name=f"Customer {i}",
                email=f"user{i}@example.com",
                whatsapp_number=f"0100{i}2345",
                year=1,
                college=college,
            )
            db.session.add(customer)
            customers.append(customer)

        term = Term(name="Term 1", college=college, year=1)
        module = Module(name="Module 1", college=college, year=1)
        db.session.add_all([term, module])
        db.session.flush()

        currency = Currency.query.first()
        subject = Subject(
            name="Advanced Math",
            year=1,
            college=college,
            term_info=term,
            module_info=module,
            currency=currency,
        )
        db.session.add(subject)

        payment_method = PaymentMethod.query.first()
        payment = Payment(
            customer=customers[0],
            subject=subject,
            payment_method=payment_method,
            course_price_paid=1000,
            application_price_paid=200,
        )
        db.session.add(payment)
        db.session.commit()

        return {
            "country_id": country.id,
            "university_id": university.id,
            "college_id": college.id,
            "customer_id": customers[0].id,
            "subject_name": subject.name,
        }


def login_admin(client):
    return client.post(
        "/signin",
        data={"username": "admin", "password": "password"},
        follow_redirects=False,
    )


def test_view_customers_minimises_selects(app, client, seeded_data):
    with app.app_context():
        engine = db.engine
        with QueryCounter(engine) as counter:
            login_admin(client)
            counter.reset()
            response = client.get("/view")
            assert response.status_code == 200
        assert counter.selects <= 3


def test_customer_profile_payments_loaded_eagerly(app, client, seeded_data):
    customer_id = seeded_data["customer_id"]
    with app.app_context():
        engine = db.engine
        with QueryCounter(engine) as counter:
            login_admin(client)
            counter.reset()
            response = client.get(f"/customer/{customer_id}")
            assert response.status_code == 200
        assert counter.selects <= 4
        assert seeded_data["subject_name"].encode() in response.data


def test_import_customers_college_map_single_query(app, client, seeded_data):
    with app.app_context():
        college = db.session.get(College, seeded_data["college_id"])
        other_country = Country(name="Sudan")
        other_university = University(name="Khartoum University", country=other_country)
        other_college = College(name="Medicine", university=other_university)
        db.session.add_all([other_country, other_university, other_college])
        db.session.commit()

        engine = db.engine
        csv_buffer = io.StringIO()
        df = pd.DataFrame(
            [
                {
                    "full_name": "Imported User",
                    "email": "imported@example.com",
                    "whatsapp_number": "01123456789",
                    "year": 1,
                    "country": college.university.country.name,
                    "university": college.university.name,
                    "college": college.name,
                }
            ]
        )
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        with QueryCounter(engine) as counter:
            login_admin(client)
            counter.reset()
            response = client.post(
                "/import_customers",
                data={"import_file": (io.BytesIO(csv_buffer.read().encode()), "customers.csv")},
                content_type="multipart/form-data",
                follow_redirects=False,
            )
            assert response.status_code in (302, 303)
        assert counter.selects <= 3