from flask import Blueprint

planner_bp = Blueprint('planner', __name__)

from app.planner import routes
