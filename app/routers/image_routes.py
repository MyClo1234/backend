from flask import Blueprint, send_from_directory, jsonify
from app.core.config import Config

image_bp = Blueprint('images', __name__)

@image_bp.route('/images/<path:filename>', methods=['GET'])
def serve_image(filename):
    """Serve images from extraction folder"""
    try:
        return send_from_directory(Config.OUTPUT_DIR, filename)
    except Exception as e:
        return jsonify({"error": str(e)}), 404
