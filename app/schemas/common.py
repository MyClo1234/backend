from typing import List, Optional
from pydantic import BaseModel


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
