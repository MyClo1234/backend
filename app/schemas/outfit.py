from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import date
from uuid import UUID
from app.domains.wardrobe.schema import WardrobeItemSchema


class OutfitBase(BaseModel):
    worn_date: date
    purpose: Optional[str] = None
    location: Optional[str] = None
    weather_snapshot: Optional[Dict[str, Any]] = None  # JSONB


class OutfitCreate(OutfitBase):
    item_ids: List[int]


class OutfitResponse(OutfitBase):
    log_id: int
    user_id: UUID
    items: List[WardrobeItemSchema]

    class Config:
        from_attributes = True
