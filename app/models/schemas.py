from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field


# -----------------------------
# Shared/Nested Models
# -----------------------------
class CategoryModel(BaseModel):
    main: str
    sub: str
    confidence: float


class ColorModel(BaseModel):
    primary: str
    secondary: List[str]
    tone: str
    confidence: float


class PatternModel(BaseModel):
    type: str
    confidence: float


class MaterialModel(BaseModel):
    guess: str
    confidence: float


class FitModel(BaseModel):
    type: str
    confidence: float


class DetailsModel(BaseModel):
    neckline: str
    sleeve: str
    length: str
    closure: List[str]
    print_or_logo: bool


class ScoresModel(BaseModel):
    formality: float
    warmth: float
    season: List[str]
    versatility: float


class MetaModel(BaseModel):
    is_layering_piece: bool
    notes: Optional[str] = None


class AttributesSchema(BaseModel):
    category: CategoryModel
    color: ColorModel
    pattern: PatternModel
    material: MaterialModel
    fit: FitModel
    details: DetailsModel
    style_tags: List[str]
    scores: ScoresModel
    meta: MetaModel
    confidence: float


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
