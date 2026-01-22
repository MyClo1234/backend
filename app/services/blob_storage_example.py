"""
Azure Blob Storage 사용 예제
이 파일은 참고용 예제입니다.
"""
from app.services.blob_storage import get_blob_storage_service

# 예제 1: 이미지 업로드
def example_upload_image():
    """이미지 업로드 예제"""
    # Blob Storage 서비스 가져오기
    blob_service = get_blob_storage_service()
    
    # 이미지 바이트 데이터 (예: 파일에서 읽기)
    with open("example_image.jpg", "rb") as f:
        image_bytes = f.read()
    
    # 사용자 ID (예: 사용자 ID, 세션 ID, 또는 고유 식별자)
    user_id = "user123"
    
    # 원본 파일명 (확장자 추출용)
    original_filename = "my_photo.jpg"
    
    # 이미지 업로드
    result = blob_service.upload_image(
        image_bytes=image_bytes,
        user_id=user_id,
        original_filename=original_filename
    )
    
    # 결과 출력
    print(f"Blob Name: {result['blob_name']}")  # 예: user123_20241223143025.jpg
    print(f"Blob URL: {result['blob_url']}")     # 예: https://...blob.core.windows.net/...
    print(f"Item ID: {result['item_id']}")       # 예: user123_20241223143025


# 예제 2: FastAPI 엔드포인트에서 사용
def example_fastapi_endpoint():
    """FastAPI 엔드포인트 예제"""
    from fastapi import FastAPI, UploadFile, File
    from app.services.blob_storage import get_blob_storage_service
    
    app = FastAPI()
    
    @app.post("/api/upload-image")
    async def upload_image(
        file: UploadFile = File(...),
        user_id: str = "default_user"  # 실제로는 인증에서 가져옴
    ):
        """이미지 업로드 엔드포인트"""
        # 파일 읽기
        image_bytes = await file.read()
        
        # Blob Storage에 업로드
        blob_service = get_blob_storage_service()
        result = blob_service.upload_image(
            image_bytes=image_bytes,
            user_id=user_id,
            original_filename=file.filename
        )
        
        return {
            "success": True,
            "blob_name": result["blob_name"],
            "blob_url": result["blob_url"],
            "item_id": result["item_id"]
        }


# 예제 3: 이미지 삭제
def example_delete_image():
    """이미지 삭제 예제"""
    blob_service = get_blob_storage_service()
    
    blob_name = "user123_20241223143025.jpg"
    success = blob_service.delete_image(blob_name)
    
    if success:
        print(f"Image {blob_name} deleted successfully")
    else:
        print(f"Failed to delete {blob_name}")


# 예제 4: 이미지 URL 가져오기
def example_get_image_url():
    """이미지 URL 가져오기 예제"""
    blob_service = get_blob_storage_service()
    
    blob_name = "user123_20241223143025.jpg"
    url = blob_service.get_image_url(blob_name)
    
    print(f"Image URL: {url}")
