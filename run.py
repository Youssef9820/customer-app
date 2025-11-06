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
  
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
