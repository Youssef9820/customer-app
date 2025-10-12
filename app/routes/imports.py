from flask import Blueprint, render_template

imports_bp = Blueprint('imports', __name__)

@imports_bp.route('/imports')
def imports_page():
    return "<h1>Imports page works!</h1>"
