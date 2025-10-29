# run.py
# This file's only job is to create and run the app.

import os
from app import create_app, db
from app.models import User, Currency, PaymentMethod

app = create_app()

def add_initial_data():
    """Adds initial data like currencies and payment methods if they don't exist."""
    if Currency.query.first() is None:
        print("Adding initial currency data...")
        db.session.add(Currency(code='EGP', symbol='E£'))
        db.session.commit()

    if PaymentMethod.query.first() is None:
        print("Adding initial payment method data...")
        db.session.add_all([
            PaymentMethod(name='Cash'),
            PaymentMethod(name='Visa'),
            PaymentMethod(name='Transfer'),
            PaymentMethod(name='(by app)')
        ])
        db.session.commit()

# ✅ نفّذ التهيئة والـseeding عند الاستيراد (علشان Gunicorn)
with app.app_context():
    db.create_all()
    add_initial_data()
    if os.getenv('FLASK_ENV', '').lower() != 'production':
        if not User.query.filter_by(username='admin').first():
            print("Creating default admin user...")
            user = User(username='admin', email='admin@example.com')
            user.set_password('Admin@1234!')
            db.session.add(user)
            db.session.commit()
            print("Admin user created.")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
