from flask import Blueprint, request, jsonify
from app.services.wardrobe_manager import wardrobe_manager
from app.services.recommender import recommender

recommendation_bp = Blueprint('recommendation', __name__)

@recommendation_bp.route('/outfit/score', methods=['GET'])
def get_outfit_score():
    try:
        top_id = request.args.get('top_id')
        bottom_id = request.args.get('bottom_id')
        
        if not top_id or not bottom_id:
            return jsonify({"error": "top_id and bottom_id are required"}), 400
        
        all_items = wardrobe_manager.load_items()
        
        top_item = next((item for item in all_items if item.get("id") == top_id), None)
        bottom_item = next((item for item in all_items if item.get("id") == bottom_id), None)
        
        if not top_item or not bottom_item:
            return jsonify({"error": "Items not found"}), 404
        
        score, reasons = recommender.calculate_outfit_score(top_item, bottom_item)
        
        return jsonify({
            "success": True,
            "score": round(score, 3),
            "score_percent": round(score * 100),
            "reasons": reasons,
            "top": top_item,
            "bottom": bottom_item
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@recommendation_bp.route('/recommend/outfit', methods=['GET'])
def recommend_outfit():
    try:
        count = int(request.args.get('count', 1))
        season = request.args.get('season', None)
        formality = request.args.get('formality', None)
        use_gemini = request.args.get('use_gemini', 'true').lower() == 'true'
        
        all_items = wardrobe_manager.load_items()
        
        tops = [item for item in all_items 
                if item.get("attributes", {}).get("category", {}).get("main") == "top"]
        bottoms = [item for item in all_items 
                   if item.get("attributes", {}).get("category", {}).get("main") == "bottom"]
        
        if not tops or not bottoms:
            return jsonify({
                "success": True,
                "outfits": [],
                "message": "Not enough items in wardrobe (need at least one top and one bottom)"
            })
        
        if season:
            tops = [t for t in tops 
                   if season.lower() in t.get("attributes", {}).get("scores", {}).get("season", [])]
            bottoms = [b for b in bottoms 
                       if season.lower() in b.get("attributes", {}).get("scores", {}).get("season", [])]
        
        if formality:
            target_formality = float(formality)
            tops = [t for t in tops 
                   if abs(t.get("attributes", {}).get("scores", {}).get("formality", 0.5) - target_formality) <= 0.3]
            bottoms = [b for b in bottoms 
                       if abs(b.get("attributes", {}).get("scores", {}).get("formality", 0.5) - target_formality) <= 0.3]
        
        if not tops or not bottoms:
            return jsonify({
                "success": True,
                "outfits": [],
                "message": "No items match the filters"
            })
        
        if use_gemini:
            recommendations = recommender.recommend_with_gemini(tops, bottoms, count, top_candidates=5)
            if recommendations:
                return jsonify({
                    "success": True,
                    "outfits": recommendations,
                    "count": len(recommendations),
                    "method": "gemini-optimized"
                })
        
        # Fallback
        combinations = []
        for top in tops:
            for bottom in bottoms:
                score, reasons = recommender.calculate_outfit_score(top, bottom)
                combinations.append({
                    "top": top,
                    "bottom": bottom,
                    "score": round(score, 3),
                    "reasons": reasons,
                    "reasoning": ", ".join(reasons),
                    "style_description": f"{top.get('attributes', {}).get('category', {}).get('sub', 'Top')} & {bottom.get('attributes', {}).get('category', {}).get('sub', 'Bottom')}"
                })
        
        combinations.sort(key=lambda x: x["score"], reverse=True)
        top_combinations = combinations[:count]
        
        return jsonify({
            "success": True,
            "outfits": top_combinations,
            "count": len(top_combinations),
            "method": "rule-based"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500
