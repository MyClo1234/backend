from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from app.services.wardrobe_manager import wardrobe_manager
from app.services.recommender import recommender
from app.models.schemas import OutfitScoreResponse, RecommendationResponse

recommendation_router = APIRouter()

@recommendation_router.get("/outfit/score", response_model=OutfitScoreResponse)
def get_outfit_score(top_id: str = Query(...), bottom_id: str = Query(...)):
    try:
        all_items = wardrobe_manager.load_items()
        
        top_item = next((item for item in all_items if item.get("id") == top_id), None)
        bottom_item = next((item for item in all_items if item.get("id") == bottom_id), None)
        
        if not top_item or not bottom_item:
            raise HTTPException(status_code=404, detail="Items not found")
        
        score, reasons = recommender.calculate_outfit_score(top_item, bottom_item)
        
        return {
            "success": True,
            "score": round(score, 3),
            "score_percent": round(score * 100),
            "reasons": reasons,
            "top": top_item,
            "bottom": bottom_item
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@recommendation_router.get("/recommend/outfit", response_model=RecommendationResponse)
def recommend_outfit(
    count: int = Query(1, ge=1),
    season: Optional[str] = Query(None),
    formality: Optional[float] = Query(None),
    use_gemini: bool = Query(True)
):
    try:
        all_items = wardrobe_manager.load_items()
        
        tops = [item for item in all_items 
                if item.get("attributes", {}).get("category", {}).get("main") == "top"]
        bottoms = [item for item in all_items 
                   if item.get("attributes", {}).get("category", {}).get("main") == "bottom"]
        
        if not tops or not bottoms:
            return {
                "success": True,
                "outfits": [],
                "count": 0,
                "method": "none",
                "message": "Not enough items in wardrobe (need at least one top and one bottom)"
            }
        
        if season:
            tops = [t for t in tops 
                   if season.lower() in t.get("attributes", {}).get("scores", {}).get("season", [])]
            bottoms = [b for b in bottoms 
                       if season.lower() in b.get("attributes", {}).get("scores", {}).get("season", [])]
        
        if formality:
            tops = [t for t in tops 
                   if abs(t.get("attributes", {}).get("scores", {}).get("formality", 0.5) - formality) <= 0.3]
            bottoms = [b for b in bottoms 
                       if abs(b.get("attributes", {}).get("scores", {}).get("formality", 0.5) - formality) <= 0.3]
        
        if not tops or not bottoms:
            return {
                "success": True,
                "outfits": [],
                "count": 0,
                "method": "none",
                "message": "No items match the filters"
            }
        
        # Use Gemini for recommendation (with optimization)
        # Note: Making this synchronous for now within async framework, could be made async later
        if use_gemini:
            recommendations = recommender.recommend_with_gemini(tops, bottoms, count, top_candidates=5)
            if recommendations:
                return {
                    "success": True,
                    "outfits": recommendations,
                    "count": len(recommendations),
                    "method": "gemini-optimized"
                }
        
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
        
        return {
            "success": True,
            "outfits": top_combinations,
            "count": len(top_combinations),
            "method": "rule-based"
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
