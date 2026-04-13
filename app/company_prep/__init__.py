from flask import Blueprint

company_prep_bp = Blueprint('company_prep', __name__)

from app.company_prep import routes
