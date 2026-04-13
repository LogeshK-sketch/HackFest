from flask import Blueprint

coding_bp = Blueprint('coding', __name__)

from app.coding import routes
