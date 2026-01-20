import os
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.core.config import Config
from app.services.extractor import extractor
from app.services.wardrobe_manager import wardrobe_manager
from app.models.schemas import ExtractionResponse

extraction_router = APIRouter()

@extraction_router.post("/extract", response_model=ExtractionResponse)
async def extract(image: UploadFile = File(...)):
    """Extract clothing attributes from uploaded image"""
    try:
        # File type validation
        filename = image.filename.lower()
        file_ext = os.path.splitext(filename)[1]
        mime_type = image.content_type
        
        if file_ext not in Config.ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail=f"Invalid file type. Allowed: {', '.join(Config.ALLOWED_EXTENSIONS)}")
        
        if mime_type and mime_type not in Config.ALLOWED_MIME_TYPES:
            raise HTTPException(status_code=400, detail=f"Invalid MIME type. Allowed: {', '.join(Config.ALLOWED_MIME_TYPES)}")

        # Read contents
        contents = await image.read()
        
        # Size validation
        if len(contents) > Config.MAX_FILE_SIZE:
             raise HTTPException(status_code=400, detail=f"File size exceeds maximum allowed size.")

        # Sync extraction call
        attributes = extractor.extract(contents)
        
        # Save results
        save_result = wardrobe_manager.save_item(contents, image.filename, attributes)
        
        return {
            "success": True,
            "attributes": attributes,
            "saved_to": save_result["saved_to"],
            "image_url": save_result["image_url"],
            "item_id": save_result["item_id"]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
