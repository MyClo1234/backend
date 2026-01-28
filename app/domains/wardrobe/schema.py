from typing import List, Optional
from pydantic import BaseModel
from app.core.schemas import AttributesSchema


class WardrobeItemSchema(BaseModel):
    id: str
    filename: str
    attributes: AttributesSchema
    image_url: Optional[str] = None


class WardrobeResponse(BaseModel):
    success: bool
    items: List[WardrobeItemSchema]
    count: int
    total_count: Optional[int] = None
    has_more: Optional[bool] = None
