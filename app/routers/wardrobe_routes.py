from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from app.services.wardrobe_manager import wardrobe_manager
from app.models.schemas import WardrobeResponse
from app.utils.response_helpers import create_success_response, handle_route_exception

wardrobe_router = APIRouter()

@wardrobe_router.get("/wardrobe/items", response_model=WardrobeResponse)
def get_wardrobe_items(category: Optional[str] = Query(None)):
    """Get all wardrobe items"""
    try:
        items = wardrobe_manager.load_items()
        
        if category:
            filtered = []
            for item in items:
                item_category = item.get("attributes", {}).get("category", {}).get("main", "")
                if item_category == category.lower():
                    filtered.append(item)
            items = filtered
        
        return create_success_response(
            {"items": items},
            count=len(items)
        )
    except Exception as e:
        raise handle_route_exception(e)
