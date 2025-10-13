# app/routes/settings.py

from flask import Blueprint, render_template, redirect, url_for, request , flash
from flask_login import login_required
from app.models import Country, University, College, Instructor, Subject, Currency, Term, Module
from app import db


settings_bp = Blueprint('settings', __name__, url_prefix='')


# ✅ Test route (to confirm blueprint works)
@settings_bp.route('/settings/test')
@login_required
def settings_test():
    return "✅ Test route from settings_bp"


# ✅ Redirect main /settings to academic by default
@settings_bp.route('/settings')
@login_required
def settings_redirect():
    print("✅ settings_bp.route('/settings') اشتغل فعلاً")
    return redirect(url_for('settings.academic_settings'))


#Academic Settings
@settings_bp.route('/settings/academic', methods=['GET'])
@login_required
def academic_settings():
    countries = Country.query.order_by(Country.name).all()
    universities = University.query.order_by(University.name).all()
    colleges = College.query.order_by(College.name).all()

    return render_template('settings/academic.html',
                           countries=countries,
                           universities=universities,
                           colleges=colleges,
                           active_tab='academic')

# ✅ Financial Settings
@settings_bp.route('/settings/financial')
@login_required
def financial_settings():
    from app.models import Subject, College, Instructor, Currency
    subjects = Subject.query.order_by(Subject.name).all()
    colleges = College.query.order_by(College.name).all()
    instructors = Instructor.query.order_by(Instructor.name).all()
    currencies = Currency.query.order_by(Currency.code).all()

    return render_template(
        'settings/financial.html',
        subjects=subjects,
        colleges=colleges,
        instructors=instructors,
        currencies=currencies,
        active_tab='financial'
    )



# ✅ Structure Settings
@settings_bp.route('/settings/structure')
@login_required
def structure_settings():
    from app.models import College, Term, Module
    colleges = College.query.order_by(College.name).all()
    all_terms = Term.query.order_by(Term.name).all()
    all_modules = Module.query.order_by(Module.name).all()

    return render_template(
        'settings/structure.html',
        colleges=colleges,
        all_terms=all_terms,
        all_modules=all_modules,
        active_tab='structure'
    )



# ✅ Instructors Settings
@settings_bp.route('/settings/instructors')
@login_required
def instructors_settings():
    from app.models import Instructor
    instructors = Instructor.query.order_by(Instructor.name).all()
    return render_template(
        'settings/instructors.html',
        instructors=instructors,
        active_tab='instructors'
    )



# ✅ Import Settings
@settings_bp.route('/settings/import')
@login_required
def import_settings():
    return render_template(
        'settings/import.html',
        active_tab='import'
    )

