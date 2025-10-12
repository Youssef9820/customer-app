import os
import sys

# This line points to your project's directory
sys.path.insert(0, os.path.dirname(__file__))

# This line imports your Flask app object from your app.py file
from run import app as application
