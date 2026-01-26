import os
import logging
from typing import Optional
from azure.storage.blob import BlobServiceClient, ContentSettings
from app.core.config import Config

logger = logging.getLogger(__name__)


class MannequinManager:
    def __init__(self):
        self.account_name = Config.AZURE_STORAGE_ACCOUNT_NAME
        self.account_key = Config.AZURE_STORAGE_ACCOUNT_KEY
        self.container_name = Config.AZURE_STORAGE_CONTAINER_NAME
        self.blob_service_client = None
        self.container_client = None

        if self.account_name and self.account_key:
            try:
                account_url = f"https://{self.account_name}.blob.core.windows.net"
                self.blob_service_client = BlobServiceClient(
                    account_url=account_url, credential=self.account_key
                )
                self.container_client = self.blob_service_client.get_container_client(
                    self.container_name
                )
            except Exception as e:
                logger.error(
                    f"Failed to initialize Blob Storage for MannequinManager: {e}"
                )

    def get_mannequin_bytes(self, gender: str, body_shape: str) -> Optional[bytes]:
        """
        성별과 체형에 맞는 마네킹 이미지의 바이트 데이터를 반환합니다.
        AI 모델에 직접 주입할 때 사용합니다.
        """
        gender = (gender or "MALE").lower()
        gender_folder = "man" if gender in ["man", "male", "m"] else "woman"

        shape = (body_shape or "average").lower()
        valid_shapes = ["slim", "athletic", "muscular", "average", "stocky"]
        if shape not in valid_shapes:
            shape = "average"

        filename = f"{shape}.png"
        base_path = os.path.dirname(os.path.dirname(__file__))
        local_path = os.path.join(
            base_path, "static", "images", gender_folder, filename
        )

        if not os.path.exists(local_path):
            local_path = os.path.join(
                base_path, "static", "images", gender_folder, "average.png"
            )
            if not os.path.exists(local_path):
                return None

        try:
            # Ensure it's uploaded to blob for visibility/persistence as requested
            self.get_mannequin_url(gender, body_shape)

            with open(local_path, "rb") as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading mannequin bytes: {e}")
            return None

    def get_mannequin_url(self, gender: str, body_shape: str) -> Optional[str]:
        """
        성별과 체형에 맞는 마네킹 이미지의 Azure Blob URL을 반환합니다.
        로컬 static 폴더에서 파일을 찾아 없으면 기본 마네킹을 반환하고,
        필요 시 Blob Storage에 업로드합니다.
        """
        gender = (gender or "MALE").lower()
        if gender not in ["man", "woman", "male", "female"]:
            gender = "man"

        # Normalize gender folder name
        gender_folder = "man" if gender in ["man", "male"] else "woman"

        # Normalize body shape filename
        # slim, athletic, muscular, average, stocky
        shape = (body_shape or "average").lower()
        valid_shapes = ["slim", "athletic", "muscular", "average", "stocky"]

        if shape not in valid_shapes:
            # Fallback mapping if user has different strings
            mapping = {
                "skinny": "slim",
                "fit": "athletic",
                "big": "stocky",
                "heavy": "stocky",
                "normal": "average",
            }
            shape = mapping.get(shape, "average")

        filename = f"{shape}.png"

        # 1. 로컬 경로 확인
        base_path = os.path.dirname(os.path.dirname(__file__))  # app/
        local_path = os.path.join(
            base_path, "static", "images", gender_folder, filename
        )

        if not os.path.exists(local_path):
            logger.warning(
                f"Mannequin not found at {local_path}, falling back to average.png"
            )
            filename = "average.png"
            local_path = os.path.join(
                base_path, "static", "images", gender_folder, filename
            )
            if not os.path.exists(local_path):
                logger.error("Default mannequin also missing!")
                return None

        # 2. Blob Storage에 업로드 (이미 존재하면 건너뜀)
        blob_name = f"static/mannequins/{gender_folder}/{filename}"

        try:
            if not self.container_client:
                logger.error("Blob container client not initialized")
                return None

            blob_client = self.container_client.get_blob_client(blob_name)

            # 존재 여부 확인 (매번 업로드하면 느리니까)
            if not blob_client.exists():
                logger.info(f"Uploading mannequin to blob: {blob_name}")
                with open(local_path, "rb") as data:
                    blob_client.upload_blob(
                        data,
                        overwrite=True,
                        content_settings=ContentSettings(content_type="image/png"),
                    )

            # SAS Token 없이 Public Read가 가능하게 하거나, SAS URL 반환
            # (현재 환경에서는 public access가 꺼져있을 수 있으므로 SAS URL 생성 유틸 재사용 필요)
            from app.domains.wardrobe.service import wardrobe_manager

            return wardrobe_manager.get_sas_url(blob_client.url)

        except Exception as e:
            logger.error(f"Error handling mannequin blob: {e}")
            return None


mannequin_manager = MannequinManager()
