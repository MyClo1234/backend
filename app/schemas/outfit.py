from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date
from app.schemas.wardrobe import ClosetItemResponse


class OutfitBase(BaseModel):
    worn_date: date
    purpose: Optional[str] = None
    location: Optional[str] = None
    weather_snapshot: Optional[Dict[str, Any]] = None  # JSONB


class OutfitCreate(OutfitBase):
    item_ids: List[int]


class OutfitResponse(OutfitBase):
    log_id: int
    user_id: int
    items: List[ClosetItemResponse]

    class Config:
        from_attributes = True
