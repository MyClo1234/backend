import os
from flask import Blueprint, request, jsonify
from app.core.config import Config
from app.services.extractor import extractor
from app.services.wardrobe_manager import wardrobe_manager

extraction_bp = Blueprint('extraction', __name__)

@extraction_bp.route('/extract', methods=['POST'])
def extract():
    """Extract clothing attributes from uploaded image"""
    try:
        if 'image' not in request.files:
            return jsonify({"error": "No image file provided"}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        # File size validation
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > Config.MAX_FILE_SIZE:
            return jsonify({"error": f"File size exceeds maximum allowed size. Your file is {file_size / (1024*1024):.1f}MB"}), 400
        
        # File type validation
        filename = file.filename.lower()
        file_ext = os.path.splitext(filename)[1]
        mime_type = file.content_type
        
        if file_ext not in Config.ALLOWED_EXTENSIONS:
            return jsonify({"error": f"Invalid file type. Allowed: {', '.join(Config.ALLOWED_EXTENSIONS)}"}), 400
        
        if mime_type and mime_type not in Config.ALLOWED_MIME_TYPES:
            return jsonify({"error": f"Invalid MIME type. Allowed: {', '.join(Config.ALLOWED_MIME_TYPES)}"}), 400

        image_bytes = file.read()
        attributes = extractor.extract(image_bytes)
        
        # Save results
        save_result = wardrobe_manager.save_item(image_bytes, file.filename, attributes)
        
        return jsonify({
            "success": True,
            "attributes": attributes,
            "saved_to": save_result["saved_to"],
            "image_url": save_result["image_url"],
            "item_id": save_result["item_id"]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
