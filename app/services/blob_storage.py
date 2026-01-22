"""
Azure Blob Storage 서비스
이미지를 Azure Blob Storage에 저장하고 관리합니다.
"""
import os
import uuid
from datetime import datetime
from typing import Optional
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, ContentSettings
from azure.core.exceptions import AzureError
import logging

from app.core.config import Config
from app.utils.validators import validate_file_extension

logger = logging.getLogger(__name__)


class BlobStorageService:
    """Azure Blob Storage를 사용하여 이미지를 저장하고 관리하는 서비스"""
    
    def __init__(self):
        self.connection_string = Config.AZURE_STORAGE_CONNECTION_STRING
        self.container_name = Config.AZURE_STORAGE_CONTAINER_NAME
        
        if not self.connection_string:
            raise ValueError("AZURE_STORAGE_CONNECTION_STRING is not set")
        
        try:
            self.blob_service_client = BlobServiceClient.from_connection_string(
                self.connection_string
            )
            self._ensure_container_exists()
        except Exception as e:
            logger.error(f"Failed to initialize Blob Storage client: {e}")
            raise
    
    def _ensure_container_exists(self):
        """컨테이너가 존재하는지 확인하고, 없으면 생성"""
        try:
            container_client = self.blob_service_client.get_container_client(
                self.container_name
            )
            if not container_client.exists():
                container_client.create_container()
                logger.info(f"Container '{self.container_name}' created successfully")
        except AzureError as e:
            logger.error(f"Failed to ensure container exists: {e}")
            raise
    
    def generate_blob_name(
        self, 
        user_id: str, 
        original_filename: Optional[str] = None
    ) -> str:
        """
        Blob Storage에 저장할 파일명 생성
        형식: users/{user_id}/{yyyyMMdd}/{uuid}.{ext}
        
        Args:
            user_id: 사용자 UUID
            original_filename: 원본 파일명 (확장자 추출용)
        
        Returns:
            생성된 Blob 경로 (예: users/550e8400-e29b-41d4-a716-446655440000/20241223/a1b2c3d4-e5f6-7890-abcd-ef1234567890.jpg)
        """
        # 현재 날짜/시간
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")  # 경로용: yyyyMMdd
        timestamp = now.strftime("%Y%m%d%H%M%S")  # 날짜 정보: yyyyMMddHHmmss
        
        # UUID 생성 (파일명용)
        file_uuid = str(uuid.uuid4())
        
        # 확장자 추출
        if original_filename:
            ext = validate_file_extension(original_filename)
        else:
            ext = '.jpg'
        
        # 경로 생성: users/{user_id}/{yyyyMMdd}/{uuid}.{ext}
        blob_name = f"users/{user_id}/{date_str}/{file_uuid}{ext}"
        
        return blob_name
    
    def upload_image(
        self, 
        image_bytes: bytes, 
        user_id: str,
        original_filename: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> dict:
        """
        이미지를 Azure Blob Storage에 업로드
        
        Args:
            image_bytes: 이미지 바이트 데이터
            user_id: 사용자 ID 또는 고유 식별자
            original_filename: 원본 파일명 (확장자 추출용)
            content_type: MIME 타입 (선택사항, 자동 감지 가능)
        
        Returns:
            {
                "blob_name": 저장된 파일명,
                "blob_url": Blob Storage URL,
                "item_id": 아이템 ID (파일명에서 확장자 제거)
            }
        
        Raises:
            AzureError: 업로드 실패 시
        """
        try:
            # 파일명 생성
            blob_name = self.generate_blob_name(user_id, original_filename)
            
            # Blob 클라이언트 생성
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            
            # Content-Type 설정
            if not content_type:
                # 확장자 기반으로 Content-Type 추정
                ext = validate_file_extension(original_filename or blob_name)
                content_type_map = {
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.png': 'image/png',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp'
                }
                content_type = content_type_map.get(ext.lower(), 'image/jpeg')
            
            # Blob 업로드
            blob_client.upload_blob(
                image_bytes,
                overwrite=True,
                content_settings=ContentSettings(content_type=content_type)
            )
            
            # Blob URL 생성
            blob_url = blob_client.url
            
            # Item ID는 파일명의 UUID만 사용 (확장자 제거)
            # blob_name: users/{user_id}/{yyyyMMdd}/{uuid}.{ext}
            # item_id: {uuid}만 추출
            file_uuid_with_ext = os.path.basename(blob_name)  # {uuid}.{ext}
            item_id = os.path.splitext(file_uuid_with_ext)[0]  # {uuid}만
            
            logger.info(f"Image uploaded successfully: {blob_name}")
            
            return {
                "blob_name": blob_name,
                "blob_url": blob_url,
                "item_id": item_id
            }
            
        except AzureError as e:
            logger.error(f"Failed to upload image to Blob Storage: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during image upload: {e}")
            raise
    
    def delete_image(self, blob_name: str) -> bool:
        """
        Blob Storage에서 이미지 삭제
        
        Args:
            blob_name: 삭제할 Blob 이름
        
        Returns:
            삭제 성공 여부
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )
            blob_client.delete_blob()
            logger.info(f"Image deleted successfully: {blob_name}")
            return True
        except AzureError as e:
            logger.error(f"Failed to delete image from Blob Storage: {e}")
            return False
    
    def get_image_url(self, blob_name: str) -> str:
        """
        Blob Storage의 이미지 URL 가져오기
        
        Args:
            blob_name: Blob 이름
        
        Returns:
            Blob Storage URL
        """
        blob_client = self.blob_service_client.get_blob_client(
            container=self.container_name,
            blob=blob_name
        )
        return blob_client.url


# 싱글톤 인스턴스 (선택사항)
_blob_storage_service: Optional[BlobStorageService] = None


def get_blob_storage_service() -> BlobStorageService:
    """Blob Storage 서비스 싱글톤 인스턴스 반환"""
    global _blob_storage_service
    if _blob_storage_service is None:
        _blob_storage_service = BlobStorageService()
    return _blob_storage_service
