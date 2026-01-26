from typing import Optional, List
from pydantic import BaseModel
from app.domains.wardrobe.schema import WardrobeItemSchema


class OutfitGenerationRequest(BaseModel):
    """
    Request schema for generating an outfit image.
    Uses existing WardrobeItemSchema to reuse attribute definitions.
    """

    top: WardrobeItemSchema
    bottom: WardrobeItemSchema
    style_description: Optional[str] = "Casual everyday look"
    gender: Optional[str] = "unisex"


class OutfitGenerationResponse(BaseModel):
    """
    Response schema for generated image.
    Returns the URL of the image stored in Azure Blob Storage.
    """

    success: bool
    image_url: str
    message: Optional[str] = None
