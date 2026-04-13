from flask import Blueprint

ml_bp = Blueprint('ml', __name__)

from app.ml import routes
