from flask import Blueprint, jsonify
from flask.logging import default_handler
import logging

coding_bp = Blueprint('coding', __name__)

@coding_bp.errorhandler(500)
def handle_500(e):
    # Retrieve app logger if applicable
    import flask
    flask.current_app.logger.error(f"Coding Blueprint Error: {str(e)}")
    # To return JSON, we can check if it's an API request, but for global 500 in this bp, we'll return a JSON format for safety
    return jsonify({"error": "Internal Server Error", "details": str(e)}), 500

from app.coding import routes
