from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field


# -----------------------------
# Shared/Nested Models
# -----------------------------
class CategoryModel(BaseModel):
    main: Optional[str] = None
    sub: Optional[str] = None
    confidence: Optional[float] = None


class ColorModel(BaseModel):
    primary: Optional[str] = None
    secondary: Optional[List[str]] = None
    tone: Optional[str] = None
    confidence: Optional[float] = None


class PatternModel(BaseModel):
    type: Optional[str] = None
    confidence: Optional[float] = None


class MaterialModel(BaseModel):
    guess: Optional[str] = None
    confidence: Optional[float] = None


class FitModel(BaseModel):
    type: Optional[str] = None
    confidence: Optional[float] = None


class DetailsModel(BaseModel):
    neckline: Optional[str] = None
    sleeve: Optional[str] = None
    length: Optional[str] = None
    closure: Optional[List[str]] = None
    print_or_logo: Optional[bool] = None


class ScoresModel(BaseModel):
    formality: Optional[float] = None
    warmth: Optional[float] = None
    season: Optional[List[str]] = None
    versatility: Optional[float] = None


class MetaModel(BaseModel):
    is_layering_piece: Optional[bool] = None
    notes: Optional[str] = None


class AttributesSchema(BaseModel):
    category: Optional[CategoryModel] = None
    color: Optional[ColorModel] = None
    pattern: Optional[PatternModel] = None
    material: Optional[MaterialModel] = None
    fit: Optional[FitModel] = None
    details: Optional[DetailsModel] = None
    style_tags: Optional[List[str]] = None
    scores: Optional[ScoresModel] = None
    meta: Optional[MetaModel] = None
    confidence: Optional[float] = None


# -----------------------------
# Response Models
# -----------------------------
class ExtractionResponse(BaseModel):
    success: bool
    attributes: AttributesSchema
    saved_to: str
    image_url: str
    item_id: str
    blob_name: Optional[str] = Field(
        None,
        description="Azure Blob Storage 경로 (예: users/{user_id}/{yyyyMMdd}/{uuid}.{ext})",
    )
    storage_type: Optional[str] = Field(
        None,
        description="저장 타입: 'blob_storage' (Azure Blob Storage) 또는 'local' (로컬 파일 시스템)",
    )


class ExtractionUrlResponse(BaseModel):
    image_url: str
    item_id: str


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
