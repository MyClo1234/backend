from typing import List, Optional, Dict, Any
from uuid import UUID
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


class TodaysPickRequest(BaseModel):
    lat: float
    lon: float


class TodaysPickResponse(BaseModel):
    success: bool
    pick_id: Optional[UUID] = None
    top_id: Optional[str] = None
    bottom_id: Optional[str] = None
    image_url: Optional[str] = None
    reasoning: Optional[str] = None
    score: Optional[float] = None
    weather: Optional[Dict[str, Any]] = None
    # Legacy fields required by current implementation/tests
    weather_summary: str
    temp_min: float
    temp_max: float
    outfit: Optional[OutfitRecommendationSchema] = None
    message: Optional[str] = None
