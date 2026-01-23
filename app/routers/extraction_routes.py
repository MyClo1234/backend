from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.routers.user_routes import get_current_user
from app.models.user import User
from app.services.extractor import extractor
from app.services.wardrobe_manager import wardrobe_manager
from app.models.schemas import ExtractionResponse, ExtractionUrlResponse
from app.utils.validators import validate_uploaded_file
from app.utils.response_helpers import create_success_response, handle_route_exception

extraction_router = APIRouter()


from typing import List


@extraction_router.post(
    "/extract",
    response_model=List[ExtractionUrlResponse],
    summary="이미지 속성 추출 및 저장 (다중 업로드)",
    description="여러 장의 옷 이미지를 한 번에 업로드하여 속성을 추출하고 내 옷장에 저장합니다. (로그인 필요)",
)
async def extract(
    images: List[UploadFile] = File(..., description="업로드할 옷 이미지 파일 목록"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Extract and save clothing attributes (Batch)

    - **images**: 업로드할 이미지 파일 목록 (필수)
    - **Authorization**: Bearer Token (필수)
    """
    results = []

    try:
        for image in images:
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

            # Save results with user_id (ORM + Blob)
            save_result = wardrobe_manager.save_item(
                db=db,
                image_bytes=contents,
                original_filename=image.filename,
                attributes=attributes,
                user_id=current_user.id,
            )

            results.append(
                ExtractionUrlResponse(
                    image_url=save_result["image_url"],
                    item_id=str(save_result["item_id"]),
                )
            )

        return results

    except HTTPException:
        raise
    except Exception as e:
        raise handle_route_exception(e)
