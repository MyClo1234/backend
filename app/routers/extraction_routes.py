import uuid
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from app.services.extractor import extractor
from app.services.wardrobe_manager import wardrobe_manager
from app.models.schemas import ExtractionResponse
from app.utils.validators import validate_uploaded_file
from app.utils.response_helpers import create_success_response, handle_route_exception

extraction_router = APIRouter()


@extraction_router.post(
    "/extract",
    response_model=ExtractionResponse,
    summary="이미지 속성 추출",
    description="옷 이미지를 업로드하여 카테고리, 색상, 패턴, 소재 등의 속성을 자동으로 추출합니다. "
                "이미지는 Azure Blob Storage에 저장되며, 경로 형식은 `users/{user_id}/{yyyyMMdd}/{uuid}.{ext}`입니다."
)
async def extract(
    image: UploadFile = File(..., description="업로드할 옷 이미지 파일 (jpg, png, gif, webp)"),
    user_id: str = Form(..., description="사용자 UUID (예: 550e8400-e29b-41d4-a716-446655440000)")
):
    """Extract clothing attributes from uploaded image
    
    - **image**: 업로드할 이미지 파일 (필수)
    - **user_id**: 사용자 UUID 형식의 고유 식별자 (필수)
    
    이미지는 Azure Blob Storage에 저장되며, 저장 경로는 `users/{user_id}/{yyyyMMdd}/{uuid}.{ext}` 형식입니다.
    """

    try:
        # UUID 형식 검증
        try:
            uuid.UUID(user_id)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid UUID format for user_id: {user_id}"
            )
        
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

        # Save results with user_id
        save_result = wardrobe_manager.save_item(contents, image.filename, attributes, user_id=user_id)

        return create_success_response(
            {
                "attributes": attributes,
                "saved_to": save_result["saved_to"],
                "image_url": save_result["image_url"],
                "item_id": save_result["item_id"],
                "blob_name": save_result.get("blob_name"),  # Azure Blob Storage 경로
                "storage_type": save_result.get("storage_type", "local"),  # 저장 타입
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise handle_route_exception(e)
