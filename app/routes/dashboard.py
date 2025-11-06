from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy import func
from .. import db
from ..models import Customer, University, College, Country, Subject, Instructor

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    # إجماليات سريعة
    total_customers = db.session.query(func.count(Customer.id)).scalar() or 0
    total_universities = db.session.query(func.count(University.id)).scalar() or 0
    total_colleges = db.session.query(func.count(College.id)).scalar() or 0
    total_countries = db.session.query(func.count(Country.id)).scalar() or 0
    total_subjects = db.session.query(func.count(Subject.id)).scalar() or 0
    total_instructors = db.session.query(func.count(Instructor.id)).scalar() or 0

    # ✅ تجميع شهري متوافق مع Postgres (بدلاً من SQLite strftime)
    customers_over_time = (
        db.session.query(
            func.to_char(func.date_trunc('month', Customer.creation_date), 'YYYY-MM').label('month'),
            func.count(Customer.id)
        )
        .filter(Customer.creation_date.isnot(None))
        .group_by('month')
        .order_by('month')
        .all()
    )
    time_labels = [row[0] for row in customers_over_time]  # 'YYYY-MM'
    time_data   = [row[1] for row in customers_over_time]

    # توزيعات حسب الدولة
    customers_by_country = (
        db.session.query(
            Country.name,
            func.count(Customer.id)
        )
        .join(University, Country.id == University.country_id)
        .join(College, University.id == College.university_id)
        .join(Customer, College.id == Customer.college_id)
        .group_by(Country.name)
        .order_by(func.count(Customer.id).desc())
        .all()
    )

    # توزيعات حسب الجامعة
    customers_by_uni = (
        db.session.query(
            University.name,
            func.count(Customer.id)
        )
        .join(College, University.id == College.university_id)
        .join(Customer, College.id == Customer.college_id)
        .group_by(University.name)
        .order_by(func.count(Customer.id).desc())
        .all()
    )

    # توزيعات حسب السنة
    customers_by_year = (
        db.session.query(
            Customer.year,
            func.count(Customer.id)
        )
        .group_by(Customer.year)
        .order_by(Customer.year)
        .all()
    )
    customers_by_year = [(f"Year {y}" if y else "N/A", count) for y, count in customers_by_year]

    # أحدث العملاء
    recent_customers = Customer.query.order_by(Customer.creation_date.desc()).limit(5).all()

    return render_template(
        'dashboard.html',
        total_customers=total_customers,
        total_universities=total_universities,
        total_colleges=total_colleges,
        total_countries=total_countries,
        total_subjects=total_subjects,
        total_instructors=total_instructors,
        time_labels=time_labels,
        time_data=time_data,
        recent_customers=recent_customers,
        chart_data={
            'customers_by_country': {
                'labels': [i[0] for i in customers_by_country],
                'data':   [i[1] for i in customers_by_country],
            },
            'customers_by_uni': {
                'labels': [i[0] for i in customers_by_uni],
                'data':   [i[1] for i in customers_by_uni],
            },
            'customers_by_year': {
                'labels': [i[0] for i in customers_by_year],
                'data':   [i[1] for i in customers_by_year],
            },
        }
    )

@dashboard_bp.route('/dashboard')
@login_required
def dashboard():
    return index()
