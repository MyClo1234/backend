from pydantic import BaseModel
from typing import List, Optional, Dict, Any


class ClosetItemBase(BaseModel):
    category: str
    sub_category: Optional[str] = None
    season: Optional[List[str]] = None
    mood_tags: Optional[List[str]] = None
    features: Optional[Dict[str, Any]] = None  # JSONB


class ClosetItemCreate(ClosetItemBase):
    pass


class ClosetItemUpdate(BaseModel):
    category: Optional[str] = None
    sub_category: Optional[str] = None
    season: Optional[List[str]] = None
    mood_tags: Optional[List[str]] = None
    features: Optional[Dict[str, Any]] = None


class ClosetItemResponse(ClosetItemBase):
    id: int
    user_id: int
    image_path: str

    class Config:
        from_attributes = True
