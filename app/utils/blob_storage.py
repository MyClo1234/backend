"""
Azure Blob Storage 서비스
이미지를 Azure Blob Storage에 저장하고 관리합니다.
"""

import os
import uuid
from datetime import datetime
from typing import Optional
from azure.storage.blob import (
    BlobServiceClient,
    BlobClient,
    ContainerClient,
    ContentSettings,
)
from azure.core.exceptions import AzureError
import logging

from app.core.config import Config
from app.utils.validators import validate_file_extension

logger = logging.getLogger(__name__)


class BlobStorageService:
    """Azure Blob Storage를 사용하여 이미지를 저장하고 관리하는 서비스"""

    def __init__(self):
        self.account_name = Config.AZURE_STORAGE_ACCOUNT_NAME
        self.account_key = Config.AZURE_STORAGE_ACCOUNT_KEY
        self.container_name = Config.AZURE_STORAGE_CONTAINER_NAME

        if not self.account_name or not self.account_key:
            # 로컬 개발 환경 등에서 설정을 건너뛸 수 있도록 로그만 남기고 pass 할 수도 있음
            # 하지만 서비스 사용 시에는 필수
            pass

        try:
            if self.account_name and self.account_key:
                account_url = f"https://{self.account_name}.blob.core.windows.net"
                self.blob_service_client = BlobServiceClient(
                    account_url=account_url, credential=self.account_key
                )
                self._ensure_container_exists()
        except Exception as e:
            logger.error(f"Failed to initialize Blob Storage client: {e}")
            # raise # 초기화 실패 시 에러를 던질지 여부

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
        self, user_id: str, original_filename: Optional[str] = None
    ) -> str:
        """
        Blob Storage에 저장할 파일명 생성
        형식: users/{user_id}/{yyyyMMdd}/{uuid}.{ext}
        """
        # 현재 날짜/시간
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")  # 경로용: yyyyMMdd

        # UUID 생성 (파일명용)
        file_uuid = str(uuid.uuid4())

        # 확장자 추출
        if original_filename:
            ext = validate_file_extension(original_filename)
        else:
            ext = ".jpg"

        # 경로 생성: users/{user_id}/{yyyyMMdd}/{uuid}.{ext}
        blob_name = f"users/{user_id}/{date_str}/{file_uuid}{ext}"

        return blob_name

    def upload_image(
        self,
        image_bytes: bytes,
        user_id: str,
        original_filename: Optional[str] = None,
        content_type: Optional[str] = None,
    ) -> dict:
        """
        이미지를 Azure Blob Storage에 업로드
        """
        try:
            # 파일명 생성
            blob_name = self.generate_blob_name(user_id, original_filename)

            # Blob 클라이언트 생성
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, blob=blob_name
            )

            # Content-Type 설정
            if not content_type:
                # 확장자 기반으로 Content-Type 추정
                ext = validate_file_extension(original_filename or blob_name)
                content_type_map = {
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".png": "image/png",
                    ".gif": "image/gif",
                    ".webp": "image/webp",
                }
                content_type = content_type_map.get(ext.lower(), "image/jpeg")

            # Blob 업로드
            blob_client.upload_blob(
                image_bytes,
                overwrite=True,
                content_settings=ContentSettings(content_type=content_type),
            )

            # Blob URL 생성
            blob_url = blob_client.url

            # Item ID는 파일명의 UUID만 사용
            file_uuid_with_ext = os.path.basename(blob_name)
            item_id = os.path.splitext(file_uuid_with_ext)[0]

            logger.info(f"Image uploaded successfully: {blob_name}")

            return {"blob_name": blob_name, "blob_url": blob_url, "item_id": item_id}

        except AzureError as e:
            logger.error(f"Failed to upload image to Blob Storage: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during image upload: {e}")
            raise


# 싱글톤 인스턴스
_blob_storage_service: Optional[BlobStorageService] = None


def get_blob_storage_service() -> BlobStorageService:
    """Blob Storage 서비스 싱글톤 인스턴스 반환"""
    global _blob_storage_service
    if _blob_storage_service is None:
        _blob_storage_service = BlobStorageService()
    return _blob_storage_service
