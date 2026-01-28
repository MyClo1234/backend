import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.domains.user.router import get_current_user
from app.domains.user.model import User
from .service import extractor
from app.domains.wardrobe.service import wardrobe_manager
from .schema import ExtractionResponse, ExtractionUrlResponse
from app.core.schemas import AttributesSchema
from app.utils.validators import validate_uploaded_file
from app.utils.response_helpers import handle_route_exception

logger = logging.getLogger(__name__)

extraction_router = APIRouter()


@extraction_router.post(
    "/extract",
    response_model=ExtractionResponse,
    summary="이미지 속성 추출 및 저장 (단일 업로드)",
    description="옷 이미지를 업로드하여 속성을 추출하고 내 옷장에 저장합니다. (로그인 필요)",
)
async def extract(
    image: UploadFile = File(..., description="업로드할 옷 이미지 파일"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Extract and save clothing attributes (Single file)

    - **image**: 업로드할 이미지 파일 (필수)
    - **Authorization**: Bearer Token (필수)
    """
    logger.info("=== Extract Request Started ===")
    logger.info(
        f"User authenticated: ID={current_user.id}, Username={current_user.user_name}"
    )
    logger.info(f"Image filename: {image.filename}, content_type: {image.content_type}")

    try:
        # Read contents first for size validation
        contents = await image.read()
        file_size_mb = len(contents) / 1024 / 1024
        logger.info(f"Image file size: {len(contents)} bytes ({file_size_mb:.2f} MB)")

        # File validation (filename, extension, MIME type, size)
        validate_uploaded_file(
            filename=image.filename,
            content_type=image.content_type,
            file_size=len(contents),
        )
        logger.info("File validation passed")

        # Async extraction call
        logger.info("Starting attribute extraction...")
        attributes = await extractor.extract(contents)
        category_main = (
            attributes.get("category", {}).get("main", "N/A")
            if isinstance(attributes.get("category"), dict)
            else "N/A"
        )
        logger.info(f"Attribute extraction completed. Category: {category_main}")
        logger.debug(f"Extracted attributes keys: {list(attributes.keys())}")

        # Save results with user_id (ORM + Blob)
        logger.info(
            f"Saving item to database and blob storage for user_id={current_user.id}..."
        )
        save_result = wardrobe_manager.save_item(
            db=db,
            image_bytes=contents,
            original_filename=image.filename,
            attributes=attributes,
            user_id=current_user.id,
        )
        logger.info(
            f"Item saved successfully. Item ID: {save_result.get('item_id')}, Image URL: {save_result.get('image_url')}"
        )

        # Determine storage type
        storage_type = "blob_storage" if save_result.get("blob_name") else "local"
        logger.info(f"Storage type: {storage_type}")

        logger.info("=== Extract Request Completed Successfully ===")
        # Return single object with attributes
        return ExtractionResponse(
            success=True,
            attributes=attributes,
            saved_to=f"db:{save_result['item_id']}",  # DB ID로 변경
            image_url=save_result["image_url"],
            item_id=str(save_result["item_id"]),
            blob_name=save_result.get("blob_name"),
            storage_type=storage_type,
        )

    except HTTPException as e:
        logger.error(f"HTTPException raised: {e.status_code} - {e.detail}")
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error during extraction: {type(e).__name__}: {str(e)}",
            exc_info=True,
        )
        raise handle_route_exception(e)
