# app/routes/settings.py

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required
from app.models import Country, University, College, Instructor, Subject, Currency, Term, Module
from app import db

settings_bp = Blueprint('settings', __name__, url_prefix='')
@settings_bp.route('/settings/test')
@login_required
def settings_test():
    return "✅ Test route from settings_bp"


@settings_bp.route('/settings')
@login_required
def settings_redirect():
    print("✅ settings_bp.route('/settings') اشتغل فعلاً")
    return redirect(url_for('settings.academic_settings'))

@settings_bp.route('/settings/academic')
@login_required
def academic_settings():
    countries = Country.query.order_by(Country.name).all()
    universities = University.query.order_by(University.name).all()
    colleges = College.query.order_by(College.name).all()
    return render_template('settings/academic.html',
                           countries=countries,
                           universities=universities,
                           colleges=colleges)

@settings_bp.route('/settings/financial')
@login_required
def financial_settings():
    return render_template('settings/financial.html')


@settings_bp.route('/settings/structure')
@login_required
def structure_settings():
    return render_template('settings/structure.html')


@settings_bp.route('/settings/instructors')
@login_required
def instructors_settings():
    return render_template('settings/instructors.html')


@settings_bp.route('/settings/import')
@login_required
def import_settings():
    return render_template('settings/import.html')
