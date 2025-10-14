from flask_login import UserMixin
from datetime import datetime, UTC
from . import db, bcrypt


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True) # Changed to nullable=True
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        """Hash and store the provided password using bcrypt."""
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        """Check a hashed password using bcrypt."""
        return bcrypt.check_password_hash(self.password_hash, password)


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

class CollegeYear(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year_number = db.Column(db.Integer, nullable=False)
    
    # Foreign Key to link to a specific college
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False)
    
    # Relationship to easily access the college from a year object
    college = db.relationship('College', backref=db.backref('defined_years', lazy='dynamic', cascade="all, delete-orphan"))

    # This ensures a year number is unique *within* a specific college
    __table_args__ = (db.UniqueConstraint('year_number', 'college_id', name='_year_college_uc'),)


class Customer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    whatsapp_number = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(120), nullable=True)  # <-- FIXED: Now optional
    year = db.Column(db.Integer, nullable=True)      # <-- NEW: Year added
    college_id = db.Column(db.Integer, db.ForeignKey('college.id'), nullable=False)
    creation_date = db.Column(db.DateTime, nullable=False, default=datetime.now(UTC))
    last_updated = db.Column(db.DateTime, nullable=False, default=datetime.now(UTC), onupdate=datetime.now(UTC))

# In app.py, add this new model class after the Payment class definition

class CommunicationLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    creation_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))

    
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
    
    payment_date = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    notes = db.Column(db.Text, nullable=True)
    
    # --- Foreign Keys ---
    customer_id = db.Column(db.Integer, db.ForeignKey('customer.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'), nullable=False)
    payment_method_id = db.Column(db.Integer, db.ForeignKey('payment_method.id'), nullable=False)

    # --- Relationships ---
    customer = db.relationship('Customer', backref=db.backref('payments', lazy='dynamic'))