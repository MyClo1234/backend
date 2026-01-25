from typing import Optional
from pydantic import BaseModel, Field
from .common import AttributesSchema


class ExtractionResponse(BaseModel):
    success: bool
    attributes: AttributesSchema
    saved_to: str
    image_url: str
    item_id: str
    blob_name: Optional[str] = Field(
        None,
        description="Azure Blob Storage 경로 (예: users/{user_id}/{yyyyMMdd}/{uuid}.{ext})",
    )
    storage_type: Optional[str] = Field(
        None,
        description="저장 타입: 'blob_storage' (Azure Blob Storage) 또는 'local' (로컬 파일 시스템)",
    )


class ExtractionUrlResponse(BaseModel):
    image_url: str
    item_id: str
