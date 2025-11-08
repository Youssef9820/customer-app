from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash, abort, current_app
from flask_login import login_required, current_user
from sqlalchemy import func
from sqlalchemy.orm import joinedload
import pandas as pd
import io
import csv
from flask import Response

# Import models and db instance from the main application package
from .models import Customer, University, College, Country, Subject, Instructor, Term, Module, Payment, CommunicationLog, Currency, PaymentMethod, CollegeYear
from . import db
from .upload_utils import parse_import_file, UploadError


# Create the blueprint
main_bp = Blueprint('main', __name__)



@main_bp.route('/segmentation')
@login_required
def segmentation():
    # Fetch all possible filter options for the dropdowns
    countries = Country.query.order_by(Country.name).all()
    subjects = Subject.query.order_by(Subject.name).all()
    instructors = Instructor.query.order_by(Instructor.name).all()
    
    return render_template('segmentation.html',
                           countries=countries,
                           subjects=subjects,
                           instructors=instructors)





@main_bp.route('/reports')
@login_required
def reports_hub():
    # Fetch data for all report panels on the page
    all_instructors = Instructor.query.order_by(Instructor.name).all()
    all_universities = University.query.order_by(University.name).all()
    # Eagerly load the university relationship to prevent extra queries in the template
    all_colleges = College.query.options(joinedload(College.university)).order_by(College.name).all()
    
    return render_template('reports_hub.html', 
                           instructors=all_instructors,
                           all_universities=all_universities,
                           all_colleges=all_colleges)


@main_bp.route('/add_country', methods=['POST'])
@login_required
def add_country():
    name = request.form.get('country_name')
    if name:
        new_country = Country(name=name)
        db.session.add(new_country)
        db.session.commit()
        flash(f"Country '{name}' added successfully.", 'success')
    # This redirect will now trigger the chatbot
    return redirect(url_for('settings.academic_settings', message=f"Country '{name}' added.", type='success', active_tab='academic'))



@main_bp.route('/add_university', methods=['POST'])
@login_required
def add_university():
    
    name = request.form.get('university_name')
    country_id = request.form.get('country_id')
    if name and country_id:
        new_university = University(name=name, country_id=country_id)
        db.session.add(new_university)
        db.session.commit()
    return redirect(url_for('settings.academic_settings', message=f"University '{name}' added.", type='success', active_tab='academic'))


@main_bp.route('/add_college', methods=['POST'])
@login_required
def add_college():
    name = request.form.get('college_name')
    university_id = request.form.get('university_id')
    # Get the value from the radio buttons ('term' or 'module')
    structure_type = request.form.get('structure_type') 

    if name and university_id and structure_type:
        # Add the new structure_type when creating the College object
        new_college = College(
            name=name, 
            university_id=university_id,
            structure_type=structure_type
        )
        db.session.add(new_college)
        db.session.commit()
        
    return redirect(url_for('settings.academic_settings', message=f"College '{name}' added.", type='success', active_tab='academic'))

@main_bp.route('/add_college_year', methods=['POST'])
@login_required
def add_college_year():
    college_id = request.form.get('college_id')
    year_number = request.form.get('year_number', type=int)

    if college_id and year_number:
        # Check if this year already exists for this college
        existing_year = CollegeYear.query.filter_by(college_id=college_id, year_number=year_number).first()
        if not existing_year:
            new_year = CollegeYear(college_id=college_id, year_number=year_number)
            db.session.add(new_year)
            db.session.commit()
            flash(f"Year {year_number} added successfully.", 'success')
        else:
            flash(f"Year {year_number} already exists for this college.", 'warning')
    else:
        flash("Both college and year number are required.", 'danger')
    return redirect(url_for('settings.structure_settings', active_tab='structure'))

@main_bp.route('/add_instructor', methods=['POST'])
@login_required
def add_instructor():
    name = request.form.get('instructor_name')
    # THIS IS THE CRITICAL CHANGE:
    # If the email from the form is an empty string, set it to None.
    email = request.form.get('instructor_email') or None
    
    if not name:
        flash('Instructor name is required.', 'danger')
        return redirect(url_for('settings.instructors_settings', message=f"Instructor '{name}' added.", type='success', active_tab='instructors'))


    # Now, if the email was empty, we are saving None, which works with the UNIQUE constraint.
    new_instructor = Instructor(name=name, email=email)
    db.session.add(new_instructor)
    db.session.commit()
    flash(f"Instructor '{name}' added successfully.", 'success')
    return redirect(url_for('settings.instructors_settings', message=f"Instructor '{name}' added.", type='success', active_tab='instructors'))


@main_bp.route('/add_term', methods=['POST'])
@login_required
def add_term():
    name = request.form.get('term_name')
    college_id = request.form.get('college_id')
    year = request.form.get('year', type=int) # Get the year from the form as an integer

    if name and college_id and year:
        # Check if this term name already exists for this specific college AND year
        existing_term = Term.query.filter_by(name=name, college_id=college_id, year=year).first()
        if not existing_term:
            new_term = Term(name=name, college_id=college_id, year=year) # Save all three fields
            db.session.add(new_term)
            db.session.commit()
            flash(f"Term '{name}' for Year {year} added successfully.", 'success')
        else:
            flash(f"Term '{name}' already exists for this college and year.", 'warning')
    else:
        flash("College, term name, and year are all required.", 'danger')
    return redirect(url_for('settings.structure_settings', active_tab='structure'))

@main_bp.route('/add_module', methods=['POST'])
@login_required
def add_module():
    name = request.form.get('module_name')
    college_id = request.form.get('college_id')
    year = request.form.get('year', type=int) # Get the year from the form as an integer

    if name and college_id and year:
        # Check if this module name already exists for this specific college AND year
        existing_module = Module.query.filter_by(name=name, college_id=college_id, year=year).first()
        if not existing_module:
            new_module = Module(name=name, college_id=college_id, year=year) # Save all three fields
            db.session.add(new_module)
            db.session.commit()
            flash(f"Module '{name}' for Year {year} added successfully.", 'success')
        else:
            flash(f"Module '{name}' already exists for this college and year.", 'warning')
    else:
        flash("College, module name, and year are all required.", 'danger')
    return redirect(url_for('settings.structure_settings', active_tab='structure'))

@main_bp.route('/add_subject', methods=['POST'])
@login_required
def add_subject():
    try:
        new_subject = Subject(
            name=request.form['subject_name'],
            year=request.form['year'],
            college_id=request.form['college_id'],
            
            # === NEW LOGIC FOR TERM/MODULE ID ===
            term_id=request.form.get('term_id', type=int) or None,
            module_id=request.form.get('module_id', type=int) or None,
            # ====================================

            default_course_price=request.form['course_price'],
            default_application_price=request.form['app_price'],
            instructor_id=request.form.get('instructor_id') or None,
            currency_id=request.form['currency_id']
        )
        db.session.add(new_subject)
        db.session.commit()
        flash(f"Subject '{new_subject.name}' added successfully.", 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Error adding subject: {e}", 'danger')
        
    return redirect(url_for('settings.financial_settings', active_tab='financial'))

@main_bp.route('/import_customers', methods=['POST'])
@login_required
def import_customers():
    if 'import_file' not in request.files:
        flash('No file part in the request.', 'danger')
        current_app.logger.warning(
            "Customer import rejected: user_id=%s reason=no file part",
            getattr(current_user, 'id', 'anonymous'),
        )
        return render_template('settings/import.html', active_tab='import'), 400

    file = request.files['import_file']

    if not file or file.filename == '':
        flash('No file selected for uploading.', 'danger')
        current_app.logger.warning(
            "Customer import rejected: user_id=%s reason=empty filename",
            getattr(current_user, 'id', 'anonymous'),
        )
        return render_template('settings/import.html', active_tab='import'), 400

    try:
        parsed_upload = parse_import_file(file)
    except UploadError as err:
        current_app.logger.warning(
            "Customer import rejected: user_id=%s filename=%s reason=%s",
            getattr(current_user, 'id', 'anonymous'),
            err.filename or file.filename,
            err.log_message,
        )
        flash(err.user_message, 'danger')
        return render_template('settings/import.html', active_tab='import'), err.status_code

    df = parsed_upload.dataframe
    sanitized_filename = parsed_upload.filename
    file_size = parsed_upload.file_size
    row_count = parsed_upload.row_count

    if df.empty:
        flash('Uploaded file does not contain any rows to import.', 'warning')
        current_app.logger.info(
            "Customer import empty: user_id=%s filename=%s size=%s bytes",
            getattr(current_user, 'id', 'anonymous'),
            sanitized_filename,
            file_size,
        )
        return render_template('settings/import.html', active_tab='import'), 400

    def normalise_text(value):
        if value is None:
            return ''
        if isinstance(value, str):
            return value.strip()
        if pd.isna(value):
            return ''
        return str(value).strip()

    def optional_value(value):
        if value is None:
            return None
        if isinstance(value, str):
            text = value.strip()
            return text or None
        if pd.isna(value):
            return None
        return value

    new_customers = []
    errors = []

    all_colleges = College.query.options(
        joinedload(College.university).joinedload(University.country)
    ).all()

    college_map = {
        (c.university.country.name.lower(), c.university.name.lower(), c.name.lower()): c.id
        for c in all_colleges
    }
    for index, row in df.iterrows():
        country_name = normalise_text(row.get('country')).lower()
        university_name = normalise_text(row.get('university')).lower()
        college_name = normalise_text(row.get('college')).lower()
        full_name = normalise_text(row.get('full_name'))

        if not full_name:
            errors.append(f"Row {index + 2}: Missing required full_name value.")
            continue

        college_id = college_map.get((country_name, university_name, college_name))

        if not college_id:
            errors.append(
                f"Row {index + 2}: Could not find College '{row.get('college')}' in University '{row.get('university')}' / Country '{row.get('country')}'."
            )
            continue

        customer = Customer(
            full_name=full_name,
            email=optional_value(row.get('email')),
            whatsapp_number=optional_value(row.get('whatsapp_number')),
            year=optional_value(row.get('year')),
            college_id=college_id
        )
        new_customers.append(customer)

    if not new_customers:
        for error in errors:
            flash(error, 'danger')
        current_app.logger.warning(
            "Customer import rejected: user_id=%s filename=%s reason=no valid rows",
            getattr(current_user, 'id', 'anonymous'),
            sanitized_filename,
        )
        return render_template('settings/import.html', active_tab='import'), 400

    if errors:
        for error in errors:
            flash(error, 'warning')

    try:
        db.session.bulk_save_objects(new_customers)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception(
            "Customer import failed during database commit: user_id=%s filename=%s error=%s",
            getattr(current_user, 'id', 'anonymous'),
            sanitized_filename,
             str(e)  # ADD THIS to see the actual error
        )
        flash(f'Database error: {str(e)}', 'danger')  # SHOW the error to help debug
        return render_template('settings/import.html', active_tab='import'), 500

    success_message = f"Successfully imported {len(new_customers)} customers."
    if errors:
        success_message += f" Skipped {len(errors)} rows with validation errors."

    flash(success_message, 'success')
    current_app.logger.info(
        "Customer import succeeded: user_id=%s filename=%s size=%s bytes rows=%s inserted=%s skipped=%s",
        getattr(current_user, 'id', 'anonymous'),
        sanitized_filename,
        file_size,
        row_count,
        len(new_customers),
        len(errors),
    )
    return redirect(url_for('settings.import_settings', active_tab='import'))




@main_bp.route('/record_payment', methods=['GET'])
@login_required
def record_payment_page():
    # Fetch all the data needed for the dropdowns on the form
    
    # === UPDATED: Eagerly load customer's college and university info ===
    all_customers = Customer.query.options(
        joinedload(Customer.college).joinedload(College.university)
    ).order_by(Customer.full_name).all()

    all_payment_methods = PaymentMethod.query.all()
    
    # Get all colleges for the dropdown
    all_colleges = College.query.options(joinedload(College.university)).order_by(College.name).all()
    
    return render_template('record_payment.html',
                           all_customers=all_customers,
                           all_payment_methods=all_payment_methods,
                           all_colleges=all_colleges)



@main_bp.route('/record_payment', methods=['POST'])
@login_required
def record_payment():
    try:
        new_payment = Payment(
            customer_id=request.form['customer_id'],
            subject_id=request.form['subject_id'],
            course_price_paid=request.form['course_price_paid'],
            application_price_paid=request.form['app_price_paid'],
            payment_method_id=request.form['payment_method_id'],
            notes=request.form.get('notes')
        )
        db.session.add(new_payment)
        db.session.commit()
        flash('Payment recorded successfully!', 'success')
        # Redirect to a future customer profile page, or back to the form for now
        return redirect(url_for('main.record_payment_page')) 
    except Exception as e:
        db.session.rollback()
        flash(f"Error recording payment: {e}", 'danger')
        return redirect(url_for('main.record_payment_page'))

# In app.py, add this new function

@main_bp.route('/view_payments')
@login_required
def view_payments():
    # Query all payments, ordering by the most recent first.
    # We use joinedload to efficiently fetch related data (customer, subject, method)
    # to avoid many small queries in the template, which is much faster.
    all_payments = Payment.query.options(
        joinedload(Payment.customer),
        joinedload(Payment.subject),
        joinedload(Payment.payment_method)
    ).order_by(Payment.payment_date.desc()).all()
    
    return render_template('view_payments.html', payments=all_payments)

@main_bp.route('/add')
@login_required
def add_customer_page():
    countries = Country.query.order_by(Country.name).all()
    return render_template('add_customer.html', countries=countries)

@main_bp.route('/add_customer', methods=['POST'])
@login_required
def add_customer():
    # This route saves the new customer to the database
    new_customer = Customer(
        full_name=request.form['full_name'],
        email=request.form.get('email'),  # Use .get() for optional fields
        whatsapp_number=request.form.get('whatsapp_number'),
        year=request.form.get('year', type=int), # Get year as an integer
        college_id=request.form['college_id']
    )
    db.session.add(new_customer)
    db.session.commit()
    # After adding, we'll redirect back to the homepage for now
    return redirect(url_for('main.view_customers', message=f"Customer '{new_customer.full_name}' was added.", type='success'))

@main_bp.route('/view')
@login_required
def view_customers():
    # This query joins all the tables to get all the data we need
    all_customers = Customer.query.options(
        joinedload(Customer.college)
        .joinedload(College.university)
        .joinedload(University.country)
    ).all()

    # We also need to get all countries for the filter dropdown
    all_countries = Country.query.order_by(Country.name).all()
    return render_template('view_customers.html', customers=all_customers, countries=all_countries)


@main_bp.route('/customer/<int:customer_id>')
@login_required
def customer_profile(customer_id):
    customer = db.session.get(Customer, customer_id)
    if customer is None:
        abort(404)
    
    # Eagerly load all necessary related data in one go for performance
    all_payments = customer.payments.options(
        joinedload(Payment.subject).joinedload(Subject.term_info),
        joinedload(Payment.subject).joinedload(Subject.module_info),
        joinedload(Payment.subject)
        .joinedload(Subject.college)
        .joinedload(College.university)
        .joinedload(University.country)
    ).order_by(Payment.payment_date.desc()).all()
    
    # --- 1. Calculate KPI Stat Card data (this part remains the same) ---
    total_paid = sum(p.course_price_paid + p.application_price_paid for p in all_payments)
    total_payments_count = len(all_payments)
    first_payment_date = min((p.payment_date for p in all_payments), default=None)

    # --- 2. NEW: Organize Payment History by Year -> Term/Module -> Subject ---
    # The new structure will be: { year: { 'terms': { term_name: { 'subjects': { ... } } }, 'modules': { ... } } }
    payment_history = {}
    for payment in all_payments:
        subject = payment.subject
        if not subject: continue

        year = subject.year
        structure_name = ""
        structure_type = ""

        if subject.term_info:
            structure_name = subject.term_info.name
            structure_type = 'terms'
        elif subject.module_info:
            structure_name = subject.module_info.name
            structure_type = 'modules'
        else:
            structure_name = "General" # Fallback for older data
            structure_type = 'terms'

        # Create dictionaries if they don't exist
        if year not in payment_history:
            payment_history[year] = {'total': 0, 'terms': {}, 'modules': {}}
        
        if structure_name not in payment_history[year][structure_type]:
            payment_history[year][structure_type][structure_name] = {'total': 0, 'subjects': {}}

        if subject.id not in payment_history[year][structure_type][structure_name]['subjects']:
            payment_history[year][structure_type][structure_name]['subjects'][subject.id] = {
                'details': subject,
                'total': 0,
                'payments': []
            }

        # Add the payment and update totals
        payment_amount = payment.course_price_paid + payment.application_price_paid
        payment_history[year]['total'] += payment_amount
        payment_history[year][structure_type][structure_name]['total'] += payment_amount
        payment_history[year][structure_type][structure_name]['subjects'][subject.id]['total'] += payment_amount
        payment_history[year][structure_type][structure_name]['subjects'][subject.id]['payments'].append(payment)

    # Get the total number of unique subjects they've paid for
    total_subjects_enrolled = len(set(p.subject_id for p in all_payments))

    return render_template('customer_profile.html', 
                           customer=customer,
                           total_paid=total_paid,
                           total_payments_count=total_payments_count,
                           total_subjects_enrolled=total_subjects_enrolled,
                           first_payment_date=first_payment_date,
                           # Pass the NEW hierarchical history
                           payment_history=payment_history,
                           CommunicationLog=CommunicationLog)


@main_bp.route('/customer/<int:customer_id>/add_note', methods=['POST'])
@login_required
def add_note(customer_id):
    # Check if the customer exists
    customer = Customer.query.get_or_404(customer_id)
    note_content = request.form.get('note_content')

    if note_content:
        # Create a new log entry and link it to the customer
        new_log = CommunicationLog(content=note_content, customer_id=customer.id)
        db.session.add(new_log)
        db.session.commit()
        flash('Note added successfully.', 'success')
    else:
        flash('Note content cannot be empty.', 'danger')

    # Redirect back to the same customer's profile page
    return redirect(url_for('main.customer_profile', customer_id=customer_id))


@main_bp.route('/delete_note/<int:note_id>', methods=['POST'])
@login_required
def delete_note(note_id):
    # Find the note by its own ID
    note_to_delete = CommunicationLog.query.get_or_404(note_id)
    customer_id = note_to_delete.customer_id # Save the customer_id before deleting

    db.session.delete(note_to_delete)
    db.session.commit()
    flash('Note deleted.', 'danger')

    # Redirect back to the original customer's profile page
    return redirect(url_for('main.customer_profile', customer_id=customer_id))

@main_bp.route('/instructor_report/<int:instructor_id>')
@login_required
def instructor_report(instructor_id):
    instructor = Instructor.query.get_or_404(instructor_id)

    subject_ids = [s.id for s in instructor.subjects]
    if not subject_ids:
        return render_template('instructor_report.html', instructor=instructor, report_data={}, location_revenue_data={}, total_instructor_revenue=0, total_unique_students=0, total_paid_subjects=0)

    # --- UPDATED: Eagerly load all the new relationships ---
    all_payments = Payment.query.filter(Payment.subject_id.in_(subject_ids)).options(
        joinedload(Payment.subject).joinedload(Subject.college).joinedload(College.university).joinedload(University.country),
        joinedload(Payment.subject).joinedload(Subject.term_info),
        joinedload(Payment.subject).joinedload(Subject.module_info),
        joinedload(Payment.customer)
    ).all()

    # --- 1. Calculate Overall Summary Stats (remains the same) ---
    total_instructor_revenue = sum(p.course_price_paid for p in all_payments)
    total_unique_students = len(set(p.customer_id for p in all_payments))
    total_paid_subjects = len(set(p.subject_id for p in all_payments))

    # --- 2. Build Data for "Revenue by Subject" Tab (remains the same) ---
    report_data = {}
    for payment in all_payments:
        if not payment.subject: continue
        if payment.subject_id not in report_data:
            report_data[payment.subject_id] = {'subject_details': payment.subject, 'subject_revenue': 0, 'payments': []}
        report_data[payment.subject_id]['subject_revenue'] += payment.course_price_paid
        report_data[payment.subject_id]['payments'].append(payment)

    # --- 3. NEW: Build Data for "Revenue by Location" with correct hierarchy ---
    location_revenue_data = {}
    for payment in all_payments:
        subject = payment.subject
        if not (subject and subject.college and subject.college.university and subject.college.university.country):
            continue

        price = payment.course_price_paid
        country = subject.college.university.country.name
        university = subject.college.university.name
        college = subject.college.name
        year = subject.year
        
        # Determine the structure (Term or Module)
        structure_name = "General"
        structure_type = 'terms'
        if subject.term_info:
            structure_name = subject.term_info.name
            structure_type = 'terms'
        elif subject.module_info:
            structure_name = subject.module_info.name
            structure_type = 'modules'

        # Levels 1-3 (Country, University, College)
        if country not in location_revenue_data: location_revenue_data[country] = {'total': 0, 'universities': {}}
        location_revenue_data[country]['total'] += price
        uni_dict = location_revenue_data[country]['universities']
        if university not in uni_dict: uni_dict[university] = {'total': 0, 'colleges': {}}
        uni_dict[university]['total'] += price
        coll_dict = uni_dict[university]['colleges']
        if college not in coll_dict: coll_dict[college] = {'total': 0, 'years': {}}
        coll_dict[college]['total'] += price

        # Level 4: Year
        year_dict = coll_dict[college]['years']
        if year not in year_dict: year_dict[year] = {'total': 0, 'terms': {}, 'modules': {}}
        year_dict[year]['total'] += price

        # Level 5: Term/Module
        structure_dict = year_dict[year][structure_type]
        if structure_name not in structure_dict: structure_dict[structure_name] = {'total': 0, 'subjects': {}}
        structure_dict[structure_name]['total'] += price

        # Level 6: Subject
        subj_dict = structure_dict[structure_name]['subjects']
        if subject.name not in subj_dict: subj_dict[subject.name] = {'total': 0, 'payments': []}
        subj_dict[subject.name]['total'] += price
        subj_dict[subject.name]['payments'].append(payment)

    return render_template('instructor_report.html',
                           instructor=instructor,
                           report_data=report_data,
                           total_instructor_revenue=total_instructor_revenue,
                           total_unique_students=total_unique_students,
                           total_paid_subjects=total_paid_subjects,
                           location_revenue_data=location_revenue_data)


@main_bp.route('/application_report')
@login_required
def application_report():
    # --- 1. Start with a base query for all payments with an application fee ---
    query = Payment.query.filter(Payment.application_price_paid > 0).options(
        joinedload(Payment.subject).joinedload(Subject.college).joinedload(College.university),
        joinedload(Payment.subject).joinedload(Subject.term_info),
        joinedload(Payment.subject).joinedload(Subject.module_info),
        joinedload(Payment.customer)
    )

    # --- 2. Get and Apply Filters from the URL ---
    year_filter = request.args.get('year', type=int)
    university_id_filter = request.args.get('university_id', type=int)
    college_id_filter = request.args.get('college_id', type=int)

    if college_id_filter:
        query = query.join(Subject).filter(Subject.college_id == college_id_filter)
    elif university_id_filter:
        query = query.join(Subject).join(College).filter(College.university_id == university_id_filter)
    
    if year_filter:
        query = query.join(Subject).filter(Subject.year == year_filter)

    all_payments = query.all()

    # --- 3. Calculate Overall Summary Stats ---
    total_app_revenue = sum(p.application_price_paid for p in all_payments)
    total_applications = len(all_payments)
    total_unique_students = len(set(p.customer_id for p in all_payments))

    # --- 4. NEW: Build Hierarchical Data with correct structure ---
    report_data = {}
    for payment in all_payments:
        subject = payment.subject
        if not (subject and subject.college and subject.college.university):
            continue

        price = payment.application_price_paid
        pay_year = subject.year
        uni_name = subject.college.university.name
        coll_name = subject.college.name
        
        structure_name = "General"
        structure_type = 'terms'
        if subject.term_info:
            structure_name = subject.term_info.name
            structure_type = 'terms'
        elif subject.module_info:
            structure_name = subject.module_info.name
            structure_type = 'modules'

        # Level 1: Year
        if pay_year not in report_data:
            report_data[pay_year] = {'total': 0, 'universities': {}}
        report_data[pay_year]['total'] += price
        
        # Level 2: University
        uni_dict = report_data[pay_year]['universities']
        if uni_name not in uni_dict:
            uni_dict[uni_name] = {'total': 0, 'colleges': {}}
        uni_dict[uni_name]['total'] += price
        
        # Level 3: College
        coll_dict = uni_dict[uni_name]['colleges']
        if coll_name not in coll_dict:
            coll_dict[coll_name] = {'total': 0, 'terms': {}, 'modules': {}}
        coll_dict[coll_name]['total'] += price
        
        # Level 4: Term/Module
        structure_dict = coll_dict[coll_name][structure_type]
        if structure_name not in structure_dict:
            structure_dict[structure_name] = {'total': 0, 'subjects': {}}
        structure_dict[structure_name]['total'] += price
        
        # Level 5: Subject
        subj_dict = structure_dict[structure_name]['subjects']
        if subject.name not in subj_dict:
            subj_dict[subject.name] = {'total': 0, 'payments': []}
        subj_dict[subject.name]['total'] += price
        
        # Level 6: Individual Payment
        subj_dict[subject.name]['payments'].append(payment)

    # --- 5. Pass all the processed data to the template ---
    return render_template('application_report.html',
                           report_data=report_data,
                           total_app_revenue=total_app_revenue,
                           total_applications=total_applications,
                           total_unique_students=total_unique_students,
                           year_filter=year_filter,
                           university_id_filter=university_id_filter,
                           college_id_filter=college_id_filter)

@main_bp.route('/delete_customer/<int:customer_id>', methods=['POST'])
@login_required
def delete_customer(customer_id):
    customer_to_delete = Customer.query.get_or_404(customer_id)
    db.session.delete(customer_to_delete)
    db.session.commit()
    # We will add a flash message here later to confirm deletion
    return redirect(url_for('main.view_customers', message='Customer has been deleted.', type='danger'))

@main_bp.route('/edit_customer/<int:customer_id>', methods=['GET', 'POST'])
@login_required
def edit_customer(customer_id):
    customer_to_edit = Customer.query.get_or_404(customer_id)
    
    if request.method == 'POST':
        # This is the logic to UPDATE the customer in the database
        customer_to_edit.full_name = request.form['full_name']
        customer_to_edit.email = request.form.get('email')
        customer_to_edit.whatsapp_number = request.form.get('whatsapp_number')
        customer_to_edit.year = request.form.get('year', type=int)
        customer_to_edit.college_id = request.form['college_id']
        db.session.commit()
        # We'll add a flash message here later
        return redirect(url_for('main.view_customers', message=f"Customer '{customer_to_edit.full_name}' was updated.", type='success'))

    # This is the logic to DISPLAY the pre-filled form (GET request)
    all_countries = Country.query.order_by(Country.name).all()
    return render_template('edit_customer.html', customer=customer_to_edit, countries=all_countries)

@main_bp.route('/delete_country/<int:country_id>', methods=['POST'])
@login_required
def delete_country(country_id):
    country_to_delete = Country.query.get_or_404(country_id)
    
    # This check prevents the app from crashing
    if country_to_delete.universities:
        message = f"Cannot delete '{country_to_delete.name}' because it has universities linked to it."
        return redirect(url_for('settings.academic_settings', message=f"Country '{country_to_delete.name}' has been deleted.", type='danger', active_tab='academic'))

        
    db.session.delete(country_to_delete)
    db.session.commit()
    message = f"Country '{country_to_delete.name}' has been deleted."
    return redirect(url_for('settings.academic_settings', message=message, type='success'))


@main_bp.route('/delete_university/<int:university_id>', methods=['POST'])
@login_required
def delete_university(university_id):
    university_to_delete = University.query.get_or_404(university_id)
    db.session.delete(university_to_delete)
    db.session.commit()
    return redirect(url_for('settings.academic_settings', message=f"University '{university_to_delete.name}' has been deleted.", type='danger', active_tab='academic'))


@main_bp.route('/delete_college/<int:college_id>', methods=['POST'])
@login_required
def delete_college(college_id):
    college_to_delete = College.query.get_or_404(college_id)
    db.session.delete(college_to_delete)
    db.session.commit()
    return redirect(url_for('settings.academic_settings', message=f"College '{college_to_delete.name}' has been deleted.", type='danger', active_tab='academic'))


@main_bp.route('/delete_college_year/<int:year_id>', methods=['POST'])
@login_required
def delete_college_year(year_id):
    year_to_delete = CollegeYear.query.get_or_404(year_id)
    db.session.delete(year_to_delete)
    db.session.commit()
    flash(f"Year {year_to_delete.year_number} has been deleted.", 'danger')
    return redirect(url_for('settings.structure_settings', active_tab='structure'))

@main_bp.route('/edit_country/<int:country_id>', methods=['GET', 'POST'])
@login_required
def edit_country(country_id):
    country = Country.query.get_or_404(country_id)
    if request.method == 'POST':
        country.name = request.form['name']
        db.session.commit()
        return redirect(url_for('settings.academic_settings', message='Country updated.', type='success', active_tab='academic'))

    return render_template('edit_item.html', item=country, item_type='Country')

@main_bp.route('/edit_university/<int:university_id>', methods=['GET', 'POST'])
@login_required
def edit_university(university_id):
    university = University.query.get_or_404(university_id)
    if request.method == 'POST':
        university.name = request.form['name']
        university.country_id = request.form['country_id'] 
        db.session.commit()
        return redirect(url_for('settings.academic_settings', message='University updated.', type='success', active_tab='academic'))

    
    all_countries = Country.query.order_by(Country.name).all()
    return render_template('edit_item.html', item=university, item_type='University', all_countries=all_countries)



@main_bp.route('/edit_college/<int:college_id>', methods=['GET', 'POST'])
@login_required
def edit_college(college_id):
    college = College.query.get_or_404(college_id)
    
    if request.method == 'POST':
        college.name = request.form['name']
        college.university_id = request.form['university_id']
        db.session.commit()
        return redirect(url_for('settings.academic_settings', message='College updated.', type='success', active_tab='academic'))

    
    all_universities = University.query.order_by(University.name).all()
    return render_template('edit_item.html', 
                           item=college, 
                           item_type='College', 
                           all_universities=all_universities)


@main_bp.route('/delete_instructor/<int:instructor_id>', methods=['POST'])
@login_required
def delete_instructor(instructor_id):
    instructor = Instructor.query.get_or_404(instructor_id)
    db.session.delete(instructor)
    db.session.commit()
    flash(f"Instructor '{instructor.name}' has been deleted.", 'danger')
    return redirect(url_for('settings.instructors_settings', message=f"Instructor '{instructor.name}' has been deleted.", type='danger', active_tab='instructors'))


@main_bp.route('/edit_instructor/<int:instructor_id>', methods=['GET', 'POST'])
@login_required
def edit_instructor(instructor_id):
    instructor = Instructor.query.get_or_404(instructor_id)
    if request.method == 'POST':
        instructor.name = request.form['name']
        instructor.email = request.form.get('email')
        db.session.commit()
        flash(f"Instructor '{instructor.name}' updated.", 'success')
        return redirect(url_for('settings.instructors_settings', message=f"Instructor '{instructor.name}' updated.", type='success', active_tab='instructors'))

    
    return render_template('edit_item.html', item=instructor, item_type='Instructor')

@main_bp.route('/delete_subject/<int:subject_id>', methods=['POST'])
@login_required
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    db.session.delete(subject)
    db.session.commit()
    flash(f"Subject '{subject.name}' has been deleted.", 'danger')
    return redirect(url_for('settings.financial_settings', message=f"Subject '{subject.name}' has been deleted.", type='danger', active_tab='financial'))


@main_bp.route('/api/get_college_structure/<int:college_id>')
@login_required
def get_college_structure(college_id):
    college = College.query.get(college_id)
    if college:
        return jsonify({'structure_type': college.structure_type})
    else:
        return jsonify({'error': 'College not found'}), 404



@main_bp.route('/api/get_college_years/<int:college_id>')
@login_required
def get_college_years(college_id):
    years = CollegeYear.query.filter_by(college_id=college_id).order_by(CollegeYear.year_number).all()
    year_list = [{'id': year.id, 'year_number': year.year_number} for year in years]
    return jsonify({'years': year_list})

@main_bp.route('/api/get_terms/<int:college_id>/<int:year>')
@login_required
def get_terms(college_id, year):
    terms = Term.query.filter_by(college_id=college_id, year=year).order_by(Term.name).all()
    term_list = [{'id': term.id, 'name': term.name} for term in terms]
    return jsonify({'terms': term_list})

@main_bp.route('/api/get_modules/<int:college_id>/<int:year>')
@login_required
def get_modules(college_id, year):
    modules = Module.query.filter_by(college_id=college_id, year=year).order_by(Module.name).all()
    module_list = [{'id': module.id, 'name': module.name} for module in modules]
    return jsonify({'modules': module_list})

@main_bp.route('/api/get_subjects')
@login_required
def get_subjects():
    # Get the filter criteria from the URL query parameters
    college_id = request.args.get('college_id', type=int)
    year = request.args.get('year', type=int)
    term_id = request.args.get('term_id', type=int)
    module_id = request.args.get('module_id', type=int)

    # Start with a base query for all subjects
    query = Subject.query

    # Apply filters if they are provided
    if college_id:
        query = query.filter_by(college_id=college_id)
    if year:
        query = query.filter_by(year=year)
    if term_id:
        query = query.filter_by(term_id=term_id)
    if module_id:
        query = query.filter_by(module_id=module_id)

    # Execute the final query
    subjects = query.order_by(Subject.name).all()

    # Convert the results into a list of dictionaries
    subject_list = [{
        'id': sub.id, 
        'name': sub.name,
        'course_price': sub.default_course_price,
        'app_price': sub.default_application_price
    } for sub in subjects]
    
    return jsonify({'subjects': subject_list})


@main_bp.route('/api/filter_customers')
@login_required
def filter_customers():
    # Start with a query for all customers
    query = Customer.query.join(College).join(University).join(Country)

    # Get filter values from the request arguments
    country_id = request.args.get('country_id')
    university_id = request.args.get('university_id')
    college_id = request.args.get('college_id')
    name_search = request.args.get('name')
    email_search = request.args.get('email')
    phone_search = request.args.get('phone')

    # Apply filters to the query if they exist
    if country_id:
        query = query.filter(Country.id == country_id)
    if university_id:
        query = query.filter(University.id == university_id)
    if college_id:
        query = query.filter(College.id == college_id)
    
    # Apply search filters using 'ilike' for case-insensitive partial matching
    if name_search:
        query = query.filter(Customer.full_name.ilike(f'%{name_search}%'))
    if email_search:
        query = query.filter(Customer.email.ilike(f'%{email_search}%'))
    if phone_search:
        query = query.filter(Customer.whatsapp_number.ilike(f'%{phone_search}%'))

    # Execute the final query
    filtered_customers = query.all()

    # Convert the results into a list of dictionaries to send as JSON
    customer_list = []
    for customer in filtered_customers:
        customer_list.append({
            'id': customer.id,
            'full_name': customer.full_name,
            'email': customer.email or 'N/A',
            'whatsapp_number': customer.whatsapp_number or 'N/A',
            'year': customer.year or 'N/A',
            'college_name': customer.college.name,
            'university_name': customer.college.university.name
        })
    
    return jsonify({'customers': customer_list})

@main_bp.route('/api/segment_students', methods=['POST'])
@login_required
def segment_students():
    try:
        filters = request.get_json()

        # Start with a base query joining all necessary tables for filtering
        query = Customer.query.join(College).join(University).join(Country)

        # --- Apply Location Filters ---
        if filters.get('college_id'):
            query = query.filter(Customer.college_id == filters['college_id'])
        elif filters.get('university_id'):
            query = query.filter(College.university_id == filters['university_id'])
        elif filters.get('country_id'):
            query = query.filter(University.country_id == filters['country_id'])

        # --- Apply Academic Filters ---
        if filters.get('year'):
            query = query.filter(Customer.year == filters['year'])
        
        # --- NEW: Logic to filter by Term or Module ---
        # This is the most complex part. We need to find subjects that match the term/module
        # and then find customers who have paid for those subjects.
        subject_ids_to_filter = None

        if filters.get('term_id'):
            subject_ids_to_filter = [s.id for s in Subject.query.filter_by(term_id=filters['term_id']).all()]
        elif filters.get('module_id'):
            subject_ids_to_filter = [s.id for s in Subject.query.filter_by(module_id=filters['module_id']).all()]
        
        # If a specific subject is chosen, it overrides the term/module filter
        if filters.get('subject_id'):
             subject_ids_to_filter = [int(filters['subject_id'])]

        if subject_ids_to_filter is not None:
            if subject_ids_to_filter:
                query = query.filter(Customer.payments.any(Payment.subject_id.in_(subject_ids_to_filter)))
            else: # If a term/module was selected but it has no subjects, return no customers
                query = query.filter(False)
        # --- END OF NEW LOGIC ---

        if filters.get('instructor_id'):
            instructor_subject_ids = [s.id for s in Subject.query.filter_by(instructor_id=filters['instructor_id']).all()]
            if instructor_subject_ids:
                query = query.filter(Customer.payments.any(Payment.subject_id.in_(instructor_subject_ids)))
            else:
                query = query.filter(False)

        # --- Apply Payment Filters ---
        if filters.get('payment_status') == 'has_paid':
            query = query.filter(Customer.payments.any())
        elif filters.get('payment_status') == 'no_payment':
            query = query.filter(~Customer.payments.any())

        matching_students = query.all()

        results = []
        for student in matching_students:
            results.append({
                'id': student.id,
                'full_name': student.full_name,
                'college_name': student.college.name,
                'year': student.year or 'N/A',
                'whatsapp_number': student.whatsapp_number or 'N/A'
            })
        
        return jsonify({'students': results})

    except Exception as e:
        print(f"Error in /api/segment_students: {e}")
        return jsonify({'error': 'An internal error occurred.'}), 500

@main_bp.route('/edit_subject/<int:subject_id>', methods=['GET', 'POST'])
@login_required
def edit_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    if request.method == 'POST':
        # Update all fields from the form
        subject.name = request.form['name']
        subject.year = request.form['year']
        subject.term = request.form.get('term')
        subject.module = request.form.get('module')
        subject.default_course_price = request.form['course_price']
        subject.default_application_price = request.form['app_price']
        # This is where we allow changing the "route" (i.e., the linked items)
        subject.college_id = request.form['college_id']
        subject.instructor_id = request.form.get('instructor_id') or None
        subject.currency_id = request.form['currency_id']
        db.session.commit()
        flash(f"Subject '{subject.name}' updated.", 'success')
        return redirect(url_for('settings.financial_settings', message=f"Subject '{subject.name}' updated.", type='success', active_tab='financial'))


    # For GET request, we need to pass all the dropdown options to the template
    all_colleges = College.query.order_by(College.name).all()
    all_instructors = Instructor.query.order_by(Instructor.name).all()
    all_currencies = Currency.query.all()
    
    return render_template('edit_item.html', 
                           item=subject, 
                           item_type='Subject',
                           all_colleges=all_colleges,
                           all_instructors=all_instructors,
                           all_currencies=all_currencies)
@main_bp.route('/api/export_segment_csv')
@login_required
def export_segment_csv():
    query = Customer.query.join(College).join(University).join(Country)
    # --- Apply Location Filters ---
    if request.args.get('college_id'):
        query = query.filter(Customer.college_id == request.args.get('college_id'))
    elif request.args.get('university_id'):
        query = query.filter(College.university_id == request.args.get('university_id'))
    elif request.args.get('country_id'):
        query = query.filter(University.country_id == request.args.get('country_id'))

    # --- Apply Academic Filters ---
    if request.args.get('year'):
        query = query.filter(Customer.year == request.args.get('year'))
    
    if request.args.get('subject_id'):
        query = query.filter(Customer.payments.any(Payment.subject_id == request.args.get('subject_id')))
    
    if request.args.get('instructor_id'):
        instructor_subject_ids = [s.id for s in Subject.query.filter_by(instructor_id=request.args.get('instructor_id')).all()]
        if instructor_subject_ids:
            query = query.filter(Customer.payments.any(Payment.subject_id.in_(instructor_subject_ids)))
        else:
            query = query.filter(False)

    # --- Apply Payment Filters ---
    if request.args.get('payment_status') == 'has_paid':
        query = query.filter(Customer.payments.any())
    elif request.args.get('payment_status') == 'no_payment':
        query = query.filter(~Customer.payments.any())

    students = query.all()

    # --- CSV Generation Logic ---
    output = io.StringIO()
    output.write('\ufeff') # This writes the BOM hint for Excel
    writer = csv.writer(output)


    # Write the header row
    header = ['ID', 'Full Name', 'WhatsApp Number', 'Email', 'Year', 'College', 'University', 'Country']
    writer.writerow(header)

    # Write data rows
    for student in students:
        row = [
            student.id,
            student.full_name,
            student.whatsapp_number,
            student.email,
            student.year,
            student.college.name,
            student.college.university.name,
            student.college.university.country.name
        ]
        writer.writerow(row)

    output.seek(0)
    
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=student_segment.csv"}
    )

# DELETE TERM
@main_bp.route('/delete_term/<int:term_id>', methods=['POST'])
@login_required
def delete_term(term_id):
    from app.models import Term
    term = Term.query.get_or_404(term_id)
    db.session.delete(term)
    db.session.commit()
    return redirect(url_for('settings.structure_settings', message=f"Term '{term.name}' deleted successfully.", type='success', active_tab='structure'))


# DELETE MODULE
@main_bp.route('/delete_module/<int:module_id>', methods=['POST'])
@login_required
def delete_module(module_id):
    from app.models import Module
    module = Module.query.get_or_404(module_id)
    db.session.delete(module)
    db.session.commit()
    return redirect(url_for('settings.structure_settings', message=f"Module '{module.name}' deleted successfully.", type='success', active_tab='structure'))


# API ENDPOINT: Get Universities by Country
@main_bp.route('/api_get_universities/<int:country_id>', methods=['GET'])
@login_required
def api_get_universities(country_id):
    from app.models import University
    universities = University.query.filter_by(country_id=country_id).all()
    return {
        "universities": [
            {"id": u.id, "name": u.name} for u in universities
        ]
    }


@main_bp.route('/api_get_colleges/<int:university_id>', methods=['GET'])
@login_required
def api_get_colleges(university_id):
    from app.models import College
    colleges = College.query.filter_by(university_id=university_id).all()
    return {
        "colleges": [
            {"id": c.id, "name": c.name} for c in colleges
        ]
    }

@main_bp.route('/api_get_years/<int:college_id>', methods=['GET'])
@login_required
def api_get_years(college_id):
    from app.models import CollegeYear
    years = CollegeYear.query.filter_by(college_id=college_id).all()
    return {
        "years": [
            {"id": y.id, "year_number": y.year_number} for y in years
        ]
    }