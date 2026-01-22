from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.extractor import extractor
from app.services.wardrobe_manager import wardrobe_manager
from app.models.schemas import ExtractionResponse
from app.utils.validators import validate_uploaded_file
from app.utils.response_helpers import create_success_response, handle_route_exception

extraction_router = APIRouter()


@extraction_router.post("/extract", response_model=ExtractionResponse)
async def extract(image: UploadFile = File(...)):
    """Extract clothing attributes from uploaded image"""

    try:
        # Read contents first for size validation
        contents = await image.read()

        # File validation (filename, extension, MIME type, size)
        validate_uploaded_file(
            filename=image.filename,
            content_type=image.content_type,
            file_size=len(contents),
        )

        # Sync extraction call
        attributes = extractor.extract(contents)

        # Save results
        save_result = wardrobe_manager.save_item(contents, image.filename, attributes)

        return create_success_response(
            {
                "attributes": attributes,
                "saved_to": save_result["saved_to"],
                "image_url": save_result["image_url"],
                "item_id": save_result["item_id"],
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise handle_route_exception(e)
