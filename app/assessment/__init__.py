from flask import Blueprint

assessment_bp = Blueprint('assessment', __name__)

from app.assessment import routes
