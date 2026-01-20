from flask import Blueprint, request, jsonify
from app.services.wardrobe_manager import wardrobe_manager

wardrobe_bp = Blueprint('wardrobe', __name__)

@wardrobe_bp.route('/wardrobe/items', methods=['GET'])
def get_wardrobe_items():
    """Get all wardrobe items"""
    try:
        category = request.args.get('category', None)
        
        items = wardrobe_manager.load_items()
        
        if category:
            filtered = []
            for item in items:
                item_category = item.get("attributes", {}).get("category", {}).get("main", "")
                if item_category == category.lower():
                    filtered.append(item)
            items = filtered
        
        return jsonify({
            "success": True,
            "items": items,
            "count": len(items)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
