import os
from datetime import datetime
import pandas as pd
# ADD 'flash' TO THIS LINE
from flask import Flask, render_template, request, redirect, url_for, jsonify, flash 
from sqlalchemy import func
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import joinedload
import io
import csv
from flask import Response # Add Response to the flask import
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash


# 1. Initialize the Flask App
app = Flask(__name__)

# 2. Configure the App (Consolidated)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///customers.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# ADD THE SECRET KEY HERE
app.config['SECRET_KEY'] = 'a-super-secret-key-that-you-should-change' 

# 3. Initialize the Database
db = SQLAlchemy(app)

# 2. INITIALIZE FLASK-LOGIN
login_manager = LoginManager()
login_manager.init_app(app)
# If a user tries to access a protected page without being logged in,
# redirect them to the 'signin' page.
login_manager.login_view = 'signin'


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        """Create a hashed password."""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        """Check a hashed password."""
        return check_password_hash(self.password_hash, password)
    
# 4. CREATE THE USER LOADER FUNCTION
# This function is required by Flask-Login to load a user from the database.
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 4. Define Database Models (The blueprint for our tables)
class Country(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    universities = db.relationship('University', backref='country', lazy=True)

class University(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'), nullable=False)
    colleges = db.relationship('College', backref='university', lazy=True)

class College(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    university_id = db.Column(db.Integer, db.ForeignKey('university.id'), nullable=False)
    customers = db.relationship('Customer', backref='college', lazy=True)
    
    # --- ADD THIS NEW LINE INSTEAD ---
    structure_type = db.Column(db.String(50), default='term', nullable=False) # Will store 'term' or 'module'
    # ----------------------------------



class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    whatsapp_number = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)  # <-- FIXED: Now optional
    year = db.Column(db.Integer, nullable=True)      # <-- NEW: Year added
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False)
    creation_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

# In app.py, add this new model class after the Payment class definition

class CommunicationLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    creation_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Foreign Key to link this log entry to a specific customer
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)

    # --- Relationship ---
    # This allows us to easily access the customer from a log entry, e.g., my_log.customer
    customer = db.relationship('Customer', backref=db.backref('comm_logs', lazy='dynamic', cascade="all, delete-orphan"))


# =====================================================================
# NEW MODELS FOR FINANCIALS AND ACADEMICS
# =====================================================================

class Currency(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(10), unique=True, nullable=False) # e.g., 'EGP', 'USD'
    symbol = db.Column(db.String(5), nullable=False) # e.g., '£', '$'
    subjects = db.relationship('Subject', backref='currency', lazy=True)

class PaymentMethod(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False) # e.g., 'Cash', 'Credit Card', '(by app)'
    payments = db.relationship('Payment', backref='payment_method', lazy=True)

class Instructor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=True)
    subjects = db.relationship('Subject', backref='instructor', lazy=True)

class Term(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False)
    
    # === ADD THIS RELATIONSHIP ===
    college = db.relationship('College', backref=db.backref('terms', lazy=True))
    
    subjects = db.relationship('Subject', backref='term_info', lazy=True)
    __table_args__ = (db.UniqueConstraint('name', 'college_id', 'year', name='_term_college_year_uc'),)

class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False)

    # === ADD THIS RELATIONSHIP ===
    college = db.relationship('College', backref=db.backref('modules', lazy=True))

    subjects = db.relationship('Subject', backref='module_info', lazy=True)
    __table_args__ = (db.UniqueConstraint('name', 'college_id', 'year', name='_module_college_year_uc'),)



class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    
    # === THESE TWO LINES ARE CHANGED ===
    term_id = db.Column(db.Integer, db.ForeignKey('term.id'), nullable=True)
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'), nullable=True)
    # ==================================
    
    # Default pricing structure
    default_course_price = db.Column(db.Float, nullable=False, default=0)
    default_application_price = db.Column(db.Float, nullable=False, default=0)

    # --- Foreign Keys to link everything ---
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False)
    instructor_id = db.Column(db.Integer, db.ForeignKey('instructor.id'), nullable=True) # Can be optional
    currency_id = db.Column(db.Integer, db.ForeignKey('currency.id'), nullable=False)
    
    # --- Relationships ---
    college = db.relationship('College', backref='subjects', lazy=True)
    payments = db.relationship('Payment', backref='subject', lazy=True)


class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # The actual amounts paid in this specific transaction
    course_price_paid = db.Column(db.Float, nullable=False, default=0)
    application_price_paid = db.Column(db.Float, nullable=False, default=0)
    
    payment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)
    
    # --- Foreign Keys ---
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    payment_method_id = db.Column(db.Integer, db.ForeignKey('payment_method.id'), nullable=False)

    # --- Relationships ---
    customer = db.relationship('Customer', backref=db.backref('payments', lazy='dynamic'))

# =====================================================================
# END OF NEW MODELS
# =====================================================================



# ... (imports remain the same) ...

# In app.py, replace the existing index() function

# In app.py, replace the entire index() function

@app.route('/')
@login_required
def index():
    # --- 1. Data for ORIGINAL Stat Cards ---
    total_customers = db.session.query(func.count(Customer.id)).scalar() or 0
    total_universities = db.session.query(func.count(University.id)).scalar() or 0
    total_colleges = db.session.query(func.count(College.id)).scalar() or 0
    total_countries = db.session.query(func.count(Country.id)).scalar() or 0

    # --- 2. Data for NEW Stat Cards (Non-Financial) ---
    total_subjects = db.session.query(func.count(Subject.id)).scalar() or 0
    total_instructors = db.session.query(func.count(Instructor.id)).scalar() or 0

    # --- 3. Data for ORIGINAL Growth Chart ---
    customers_over_time = db.session.query(
        func.strftime('%Y-%m', Customer.creation_date),
        func.count(Customer.id)
    ).group_by(func.strftime('%Y-%m', Customer.creation_date))\
     .order_by(func.strftime('%Y-%m', Customer.creation_date))\
     .all()

    # --- 4. Data for NEW Switchable Distribution Chart (Non-Financial) ---
    # Chart Option 1: Customers by Country
    customers_by_country = db.session.query(
        Country.name, 
        func.count(Customer.id)
    ).join(University, Country.id == University.country_id)\
     .join(College, University.id == College.university_id)\
     .join(Customer, College.id == Customer.college_id)\
     .group_by(Country.name)\
     .order_by(func.count(Customer.id).desc()).all()

    # Chart Option 2: Customers by University
    customers_by_uni = db.session.query(
        University.name,
        func.count(Customer.id)
    ).join(College, University.id == College.university_id)\
     .join(Customer, College.id == Customer.college_id)\
     .group_by(University.name)\
     .order_by(func.count(Customer.id).desc()).all()

    # Chart Option 3: Customers by Year
    customers_by_year = db.session.query(
        Customer.year,
        func.count(Customer.id)
    ).group_by(Customer.year).order_by(Customer.year).all()
    customers_by_year = [(f"Year {y}" if y else "N/A", count) for y, count in customers_by_year]

    # --- 5. Data for ORIGINAL Recent Customers Table ---
    recent_customers = Customer.query.order_by(Customer.creation_date.desc()).limit(5).all()

    # --- 6. Pass ALL data to the template ---
    return render_template('dashboard.html',
                           # Original stat card data
                           total_customers=total_customers,
                           total_universities=total_universities,
                           total_colleges=total_colleges,
                           total_countries=total_countries,
                           # New stat card data
                           total_subjects=total_subjects,
                           total_instructors=total_instructors,
                           # Original growth chart data
                           time_labels=[item[0] for item in customers_over_time],
                           time_data=[item[1] for item in customers_over_time],
                           # Original recent customers data
                           recent_customers=recent_customers,
                           # New switchable chart data
                           chart_data={
                               'customers_by_country': {'labels': [i[0] for i in customers_by_country], 'data': [i[1] for i in customers_by_country]},
                               'customers_by_uni': {'labels': [i[0] for i in customers_by_uni], 'data': [i[1] for i in customers_by_uni]},
                               'customers_by_year': {'labels': [i[0] for i in customers_by_year], 'data': [i[1] for i in customers_by_year]}
                           })

# In app.py, add this new route somewhere after the index() route

@app.route('/segmentation')
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

@app.route('/settings')
@login_required
def settings():
    active_tab = request.args.get('active_tab', 'academic')
    countries = Country.query.order_by(Country.name).all()
    universities = University.query.order_by(University.name).all()
    colleges = College.query.order_by(College.name).all()
    instructors = Instructor.query.order_by(Instructor.name).all()
    subjects = Subject.query.order_by(Subject.name).all()
    currencies = Currency.query.all()
    
    # === ADD THESE TWO LINES TO GET TERMS AND MODULES ===
    all_terms = Term.query.order_by(Term.name).all()
    all_modules = Module.query.order_by(Module.name).all()
    # =====================================================

    return render_template('settings.html', 
                           countries=countries, 
                           universities=universities, 
                           colleges=colleges,
                           instructors=instructors,
                           subjects=subjects,
                           currencies=currencies,
                           
                           # === PASS THE NEW LISTS TO THE TEMPLATE ===
                           all_terms=all_terms,
                           all_modules=all_modules,
                           # ==========================================

                           active_tab=active_tab)



@app.route('/add_country', methods=['POST'])
@login_required
def add_country():
    name = request.form.get('country_name')
    if name:
        new_country = Country(name=name)
        db.session.add(new_country)
        db.session.commit()
        flash(f"Country '{name}' added successfully.", 'success')
    # This redirect will now trigger the chatbot
    return redirect(url_for('settings', message=f"Country '{name}' added.", type='success', active_tab='academic'))



@app.route('/add_university', methods=['POST'])
@login_required
def add_university():
    
    name = request.form.get('university_name')
    country_id = request.form.get('country_id')
    if name and country_id:
        new_university = University(name=name, country_id=country_id)
        db.session.add(new_university)
        db.session.commit()
    return redirect(url_for('settings', message=f"University '{name}' added.", type='success', active_tab='academic'))



@app.route('/add_college', methods=['POST'])
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
        
    return redirect(url_for('settings', message=f"College '{name}' added.", type='success', active_tab='academic'))


# In app.py, after the College model

class CollegeYear(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year_number = db.Column(db.Integer, nullable=False)
    
    # Foreign Key to link to a specific college
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False)
    
    # Relationship to easily access the college from a year object
    college = db.relationship('College', backref=db.backref('defined_years', lazy='dynamic', cascade="all, delete-orphan"))

    # This ensures a year number is unique *within* a specific college
    __table_args__ = (db.UniqueConstraint('year_number', 'college_id', name='_year_college_uc'),)

@app.route('/api/get_college_structure/<int:college_id>')
@login_required
def get_college_structure(college_id):
    college = College.query.get(college_id)
    if college:
        return jsonify({'structure_type': college.structure_type})
    else:
        return jsonify({'error': 'College not found'}), 404

# In app.py, add these two new functions

@app.route('/add_college_year', methods=['POST'])
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
    return redirect(url_for('settings', active_tab='structure'))


@app.route('/delete_college_year/<int:year_id>', methods=['POST'])
@login_required
def delete_college_year(year_id):
    year_to_delete = CollegeYear.query.get_or_404(year_id)
    # Optional: Add a check here to prevent deleting a year that has terms/modules
    db.session.delete(year_to_delete)
    db.session.commit()
    flash(f"Year {year_to_delete.year_number} has been deleted.", 'danger')
    return redirect(url_for('settings', active_tab='structure'))

# In app.py, add this new function

@app.route('/api/get_college_years/<int:college_id>')
@login_required
def get_college_years(college_id):
    years = CollegeYear.query.filter_by(college_id=college_id).order_by(CollegeYear.year_number).all()
    year_list = [{'id': year.id, 'year_number': year.year_number} for year in years]
    return jsonify({'years': year_list})


@app.route('/add_instructor', methods=['POST'])
@login_required
def add_instructor():
    name = request.form.get('instructor_name')
    # THIS IS THE CRITICAL CHANGE:
    # If the email from the form is an empty string, set it to None.
    email = request.form.get('instructor_email') or None
    
    if not name:
        flash('Instructor name is required.', 'danger')
        return redirect(url_for('settings', message=f"Instructor '{name}' added.", type='success', active_tab='instructors'))


    # Now, if the email was empty, we are saving None, which works with the UNIQUE constraint.
    new_instructor = Instructor(name=name, email=email)
    db.session.add(new_instructor)
    db.session.commit()
    flash(f"Instructor '{name}' added successfully.", 'success')
    return redirect(url_for('settings', message=f"Instructor '{name}' added.", type='success', active_tab='instructors'))

# In app.py

@app.route('/add_term', methods=['POST'])
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
    return redirect(url_for('settings', active_tab='structure'))

@app.route('/delete_term/<int:term_id>', methods=['POST'])
@login_required
def delete_term(term_id):
    term_to_delete = Term.query.get_or_404(term_id)
    # Optional: Add a check here to prevent deleting a term that is in use by subjects
    db.session.delete(term_to_delete)
    db.session.commit()
    flash(f"Term '{term_to_delete.name}' has been deleted.", 'danger')
    return redirect(url_for('settings', active_tab='structure'))

@app.route('/add_module', methods=['POST'])
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
    return redirect(url_for('settings', active_tab='structure'))

@app.route('/delete_module/<int:module_id>', methods=['POST'])
@login_required
def delete_module(module_id):
    module_to_delete = Module.query.get_or_404(module_id)
    # Optional: Add a check here to prevent deleting a module that is in use
    db.session.delete(module_to_delete)
    db.session.commit()
    flash(f"Module '{module_to_delete.name}' has been deleted.", 'danger')
    return redirect(url_for('settings', active_tab='structure'))
# In app.py, add these two new functions

@app.route('/api/get_terms/<int:college_id>/<int:year>')
@login_required
def get_terms(college_id, year):
    terms = Term.query.filter_by(college_id=college_id, year=year).order_by(Term.name).all()
    term_list = [{'id': term.id, 'name': term.name} for term in terms]
    return jsonify({'terms': term_list})

@app.route('/api/get_modules/<int:college_id>/<int:year>')
@login_required
def get_modules(college_id, year):
    modules = Module.query.filter_by(college_id=college_id, year=year).order_by(Module.name).all()
    module_list = [{'id': module.id, 'name': module.name} for module in modules]
    return jsonify({'modules': module_list})



@app.route('/add_subject', methods=['POST'])
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
        
    return redirect(url_for('settings', active_tab='financial'))




@app.route('/import_customers', methods=['POST'])
@login_required
def import_customers():
    if 'import_file' not in request.files:
        flash('No file part in the request.', 'danger')
        return redirect(url_for('settings', message=success_message, type='success', active_tab='import'))


    file = request.files['import_file']

    if file.filename == '':
        flash('No file selected for uploading.', 'danger')
        return redirect(url_for('settings', active_tab='import'))

    if file:
        try:
            # Read the file using pandas
            if file.filename.endswith('.csv'):
                df = pd.read_csv(file)
            elif file.filename.endswith('.xlsx'):
                df = pd.read_excel(file)
            else:
                flash('Invalid file type. Please upload a .csv or .xlsx file.', 'danger')
                return redirect(url_for('settings', active_tab='import'))

            new_customers = []
            errors = []
            
            # Pre-load all colleges with their relationships to avoid many small queries
            all_colleges = College.query.join(University).join(Country).all()
            college_map = {
                (c.university.country.name.lower(), c.university.name.lower(), c.name.lower()): c.id
                for c in all_colleges
            }

            for index, row in df.iterrows():
                # Normalize names from the file for matching
                country_name = str(row['country']).lower().strip()
                university_name = str(row['university']).lower().strip()
                college_name = str(row['college']).lower().strip()

                # Find the college_id from our pre-built map
                college_id = college_map.get((country_name, university_name, college_name))

                if not college_id:
                    errors.append(f"Row {index + 2}: Could not find College '{row['college']}' in University '{row['university']}' / Country '{row['country']}'.")
                    continue

                # Create the new customer object
                customer = Customer(
                    full_name=row['full_name'],
                    email=row.get('email'),
                    whatsapp_number=row.get('whatsapp_number'),
                    year=row.get('year'),
                    college_id=college_id
                )
                new_customers.append(customer)

            if errors:
                for error in errors:
                    flash(error, 'danger')
                if not new_customers: # If all rows had errors
                    return redirect(url_for('settings', active_tab='import'))

            # Add all valid new customers to the database
            db.session.bulk_save_objects(new_customers)
            db.session.commit()
            
            success_message = f"Successfully imported {len(new_customers)} customers."
            if errors:
                 success_message += f" Skipped {len(errors)} rows with errors."

            flash(success_message, 'success')

        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {e}", 'danger')

    return redirect(url_for('settings', active_tab='import'))
# ... after the import_customers route ...

@app.route('/record_payment', methods=['GET'])
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



@app.route('/record_payment', methods=['POST'])
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
        return redirect(url_for('record_payment_page')) 
    except Exception as e:
        db.session.rollback()
        flash(f"Error recording payment: {e}", 'danger')
        return redirect(url_for('record_payment_page'))

# In app.py, add this new function

@app.route('/view_payments')
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

@app.route('/add')
@login_required
def add_customer_page():
    countries = Country.query.order_by(Country.name).all()
    return render_template('add_customer.html', countries=countries)

@app.route('/add_customer', methods=['POST'])
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
    return redirect(url_for('view_customers', message=f"Customer '{new_customer.full_name}' was added.", type='success'))

@app.route('/view')
@login_required
def view_customers():
    # This query joins all the tables to get all the data we need
    all_customers = Customer.query.join(College).join(University).all()
    # We also need to get all countries for the filter dropdown
    all_countries = Country.query.order_by(Country.name).all()
    return render_template('view_customers.html', customers=all_customers, countries=all_countries)

# In app.py, add this new function

@app.route('/api/get_subjects')
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


@app.route('/customer/<int:customer_id>')
@login_required
def customer_profile(customer_id):
    customer = Customer.query.get_or_404(customer_id)
    
    # Eagerly load all necessary related data in one go for performance
    all_payments = customer.payments.options(
        joinedload(Payment.subject).joinedload(Subject.term_info),
        joinedload(Payment.subject).joinedload(Subject.module_info)
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


@app.route('/customer/<int:customer_id>/add_note', methods=['POST'])
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
    return redirect(url_for('customer_profile', customer_id=customer_id))


@app.route('/delete_note/<int:note_id>', methods=['POST'])
@login_required
def delete_note(note_id):
    # Find the note by its own ID
    note_to_delete = CommunicationLog.query.get_or_404(note_id)
    customer_id = note_to_delete.customer_id # Save the customer_id before deleting

    db.session.delete(note_to_delete)
    db.session.commit()
    flash('Note deleted.', 'danger')

    # Redirect back to the original customer's profile page
    return redirect(url_for('customer_profile', customer_id=customer_id))

@app.route('/reports')
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


@app.route('/instructor_report/<int:instructor_id>')
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


@app.route('/application_report')
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


@app.route('/get_colleges/<int:university_id>')
@login_required
def get_colleges(university_id):
    colleges = College.query.filter_by(university_id=university_id).order_by(College.name).all()
    college_list = [{'id': col.id, 'name': col.name} for col in colleges]
    return jsonify({'colleges': college_list})

@app.route('/api/filter_customers')
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
@app.route('/delete_customer/<int:customer_id>', methods=['POST'])
@login_required
def delete_customer(customer_id):
    customer_to_delete = Customer.query.get_or_404(customer_id)
    db.session.delete(customer_to_delete)
    db.session.commit()
    # We will add a flash message here later to confirm deletion
    return redirect(url_for('view_customers', message='Customer has been deleted.', type='danger'))
@app.route('/edit_customer/<int:customer_id>', methods=['GET', 'POST'])
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
        return redirect(url_for('view_customers', message=f"Customer '{customer_to_edit.full_name}' was updated.", type='success'))

    # This is the logic to DISPLAY the pre-filled form (GET request)
    all_countries = Country.query.order_by(Country.name).all()
    return render_template('edit_customer.html', customer=customer_to_edit, countries=all_countries)

@app.route('/delete_country/<int:country_id>', methods=['POST'])
@login_required
def delete_country(country_id):
    country_to_delete = Country.query.get_or_404(country_id)
    
    # This check prevents the app from crashing
    if country_to_delete.universities:
        message = f"Cannot delete '{country_to_delete.name}' because it has universities linked to it."
        return redirect(url_for('settings', message=f"Country '{country_to_delete.name}' has been deleted.", type='danger', active_tab='academic'))

        
    db.session.delete(country_to_delete)
    db.session.commit()
    message = f"Country '{country_to_delete.name}' has been deleted."
    return redirect(url_for('settings', message=message, type='success'))


@app.route('/delete_university/<int:university_id>', methods=['POST'])
@login_required
def delete_university(university_id):
    university_to_delete = University.query.get_or_404(university_id)
    db.session.delete(university_to_delete)
    db.session.commit()
    return redirect(url_for('settings', message=f"University '{university_to_delete.name}' has been deleted.", type='danger', active_tab='academic'))


@app.route('/delete_college/<int:college_id>', methods=['POST'])
@login_required
def delete_college(college_id):
    college_to_delete = College.query.get_or_404(college_id)
    db.session.delete(college_to_delete)
    db.session.commit()
    return redirect(url_for('settings', message=f"College '{college_to_delete.name}' has been deleted.", type='danger', active_tab='academic'))

@app.route('/edit_country/<int:country_id>', methods=['GET', 'POST'])
@login_required
def edit_country(country_id):
    country = Country.query.get_or_404(country_id)
    if request.method == 'POST':
        country.name = request.form['name']
        db.session.commit()
        return redirect(url_for('settings', message='Country updated.', type='success', active_tab='academic'))

    return render_template('edit_item.html', item=country, item_type='Country')

@app.route('/edit_university/<int:university_id>', methods=['GET', 'POST'])
@login_required
def edit_university(university_id):
    university = University.query.get_or_404(university_id)
    if request.method == 'POST':
        university.name = request.form['name']
        # THIS IS THE CRITICAL FIX: It now reads the country_id from the form
        university.country_id = request.form['country_id'] 
        db.session.commit()
        # This now correctly passes the message to the URL for the chatbot
        return redirect(url_for('settings', message='University updated.', type='success', active_tab='academic'))

    
    # This part for showing the form is also needed
    all_countries = Country.query.order_by(Country.name).all()
    return render_template('edit_item.html', item=university, item_type='University', all_countries=all_countries)


# REPLACE the existing edit_college function with this one

@app.route('/edit_college/<int:college_id>', methods=['GET', 'POST'])
@login_required
def edit_college(college_id):
    college = College.query.get_or_404(college_id)
    
    if request.method == 'POST':
        college.name = request.form['name']
        college.university_id = request.form['university_id']
        db.session.commit()
        return redirect(url_for('settings', message='College updated.', type='success', active_tab='academic'))

    
    # This is the part that was missing the return statement
    all_universities = University.query.order_by(University.name).all()
    # The print statement is removed, and the essential return is here.
    return render_template('edit_item.html', 
                           item=college, 
                           item_type='College', 
                           all_universities=all_universities)


@app.route('/delete_instructor/<int:instructor_id>', methods=['POST'])
@login_required
def delete_instructor(instructor_id):
    instructor = Instructor.query.get_or_404(instructor_id)
    # Optional: Add a check here to prevent deleting an instructor who is assigned to subjects
    db.session.delete(instructor)
    db.session.commit()
    flash(f"Instructor '{instructor.name}' has been deleted.", 'danger')
    return redirect(url_for('settings', message=f"Instructor '{instructor.name}' has been deleted.", type='danger', active_tab='instructors'))


@app.route('/edit_instructor/<int:instructor_id>', methods=['GET', 'POST'])
@login_required
def edit_instructor(instructor_id):
    instructor = Instructor.query.get_or_404(instructor_id)
    if request.method == 'POST':
        instructor.name = request.form['name']
        instructor.email = request.form.get('email')
        db.session.commit()
        flash(f"Instructor '{instructor.name}' updated.", 'success')
        return redirect(url_for('settings', message=f"Instructor '{instructor.name}' updated.", type='success', active_tab='instructors'))

    
    # For GET request, we re-use the generic edit_item.html template
    return render_template('edit_item.html', item=instructor, item_type='Instructor')

# In app.py, add this new route at the end of the file, before the main run block.

@app.route('/api/segment_students', methods=['POST'])
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


@app.route('/delete_subject/<int:subject_id>', methods=['POST'])
@login_required
def delete_subject(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    db.session.delete(subject)
    db.session.commit()
    flash(f"Subject '{subject.name}' has been deleted.", 'danger')
    return redirect(url_for('settings', message=f"Subject '{subject.name}' has been deleted.", type='danger', active_tab='financial'))


@app.route('/edit_subject/<int:subject_id>', methods=['GET', 'POST'])
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
        return redirect(url_for('settings', message=f"Subject '{subject.name}' updated.", type='success', active_tab='financial'))


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
@app.route('/api/export_segment_csv')
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

# ... at the very end of the file

def add_initial_data():
    # Check if data already exists to prevent duplicates
    if Currency.query.first() is None:
        print("Adding initial currency data...")
        egp = Currency(code='EGP', symbol='E£')
        db.session.add(egp)
        db.session.commit()

    if PaymentMethod.query.first() is None:
        print("Adding initial payment method data...")
        cash = PaymentMethod(name='Cash')
        # --- THIS LINE IS CHANGED ---
        visa = PaymentMethod(name='Visa') 
        # --- THIS LINE IS CHANGED ---
        transfer = PaymentMethod(name='Transfer')
        by_app = PaymentMethod(name='(by app)')
        # --- THIS LINE IS CHANGED ---
        db.session.add_all([cash, visa, transfer, by_app])
        db.session.commit()

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        # Check if user or email already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.', 'danger')
            return redirect(url_for('signup'))
        if User.query.filter_by(email=email).first():
            flash('Email address already registered. Please use a different one.', 'danger')
            return redirect(url_for('signup'))

        # Create new user with a hashed password
        new_user = User(username=username, email=email)
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()

        flash('Account created successfully! You can now sign in.', 'success')
        return redirect(url_for('signin'))

    return render_template('signup.html')


@app.route('/signin', methods=['GET', 'POST'])
def signin():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        user = User.query.filter_by(username=username).first()

        # Check if user exists and password is correct
        if not user or not user.check_password(password):
            flash('Invalid username or password. Please try again.', 'danger')
            return redirect(url_for('signin'))

        # Log the user in
        login_user(user, remember=remember)
        flash(f'Welcome back, {user.username}!', 'success')
        
        # Redirect to the dashboard after successful login
        return redirect(url_for('index'))

    return render_template('signin.html')


@app.route('/signout')
@login_required # Only a logged-in user can sign out
def signout():
    logout_user()
    flash('You have been signed out.', 'info')
    return redirect(url_for('signin'))


@app.route('/profile', methods=['GET', 'POST'])
@login_required # This page is protected
def profile():
    if request.method == 'POST':
        # Logic to update user profile
        current_user.username = request.form.get('username')
        current_user.email = request.form.get('email')
        
        # Optional: Update password
        password = request.form.get('password')
        if password:
            current_user.set_password(password)
            
        db.session.commit()
        flash('Your profile has been updated successfully.', 'success')
        return redirect(url_for('profile'))

    return render_template('profile.html', user=current_user)

# 6. Main entry point to run the app
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # === ADD THIS LINE TO RE-POPULATE THE DATA ===
        add_initial_data()
        # ============================================

        # Optional: Create a default admin user if one doesn't exist
        if not User.query.filter_by(username='admin').first():
            print("Creating default admin user...")
            admin_user = User(username='admin', email='admin@example.com')
            admin_user.set_password('password') # CHANGE THIS in a real app!
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created with username 'admin' and password 'password'")
    app.run(debug=True)
