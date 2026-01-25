from typing import List, Optional
from pydantic import BaseModel
from app.domains.wardrobe.schema import WardrobeItemSchema


class OutfitRecommendationSchema(BaseModel):
    top: WardrobeItemSchema
    bottom: WardrobeItemSchema
    score: float
    reasons: List[str]
    reasoning: Optional[str] = None
    style_description: Optional[str] = None


class OutfitScoreResponse(BaseModel):
    success: bool
    score: float
    score_percent: float
    reasons: List[str]
    top: WardrobeItemSchema
    bottom: WardrobeItemSchema


class RecommendationResponse(BaseModel):
    success: bool
    outfits: List[OutfitRecommendationSchema]
    count: int
    method: str
    message: Optional[str] = None
