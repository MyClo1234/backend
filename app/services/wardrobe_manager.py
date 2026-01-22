import os
import json
import time
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
from app.core.config import Config
from app.utils.validators import validate_file_extension
from app.services.blob_storage import get_blob_storage_service

logger = logging.getLogger(__name__)

class WardrobeManager:
    def __init__(self):
        self.output_dir = Path(Config.OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Blob Storage 서비스 초기화 (환경변수가 설정되어 있을 때만)
        self.blob_storage_service = None
        try:
            if Config.AZURE_STORAGE_CONNECTION_STRING:
                self.blob_storage_service = get_blob_storage_service()
                logger.info("Blob Storage service initialized successfully")
            else:
                logger.warning("AZURE_STORAGE_CONNECTION_STRING not set, using local file storage")
        except Exception as e:
            logger.warning(f"Failed to initialize Blob Storage service: {e}. Using local file storage.")
            self.blob_storage_service = None

    def load_items(self) -> List[Dict[str, Any]]:
        items = []
        if not self.output_dir.exists():
            return items
        
        try:
            for json_file in self.output_dir.glob('*.json'):
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        attributes = json.load(f)
                        item_id = json_file.stem
                        
                        # Check if corresponding image exists
                        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
                        image_path = None
                        for ext in image_extensions:
                            potential_image = self.output_dir / f"{item_id}{ext}"
                            if potential_image.exists():
                                image_path = f"/api/images/{item_id}{ext}"
                                break
                        
                        items.append({
                            "id": item_id,
                            "filename": json_file.name,
                            "attributes": attributes,
                            "image_url": image_path
                        })
                except Exception as e:
                    print(f"Error loading {json_file.name}: {e}")
                    continue
        except Exception as e:
            print(f"Error reading wardrobe directory: {e}")
        
        return items

    def save_item(self, image_bytes: bytes, original_filename: str, attributes: dict, user_id: Optional[str] = None) -> dict:
        """
        이미지와 속성을 저장합니다.
        Blob Storage가 설정되어 있으면 Blob Storage에 저장하고, 
        그렇지 않으면 로컬 파일 시스템에 저장합니다.
        
        Args:
            image_bytes: 이미지 바이트 데이터
            original_filename: 원본 파일명
            attributes: 추출된 속성 딕셔너리
            user_id: 사용자 ID (선택사항, 기본값: "default")
        
        Returns:
            저장 결과 딕셔너리
        """
        # user_id가 없으면 기본값 사용
        if not user_id:
            user_id = "default"
        
        # Blob Storage를 사용할 수 있는 경우
        if self.blob_storage_service:
            try:
                # Blob Storage에 이미지 업로드
                blob_result = self.blob_storage_service.upload_image(
                    image_bytes=image_bytes,
                    user_id=user_id,
                    original_filename=original_filename
                )
                
                blob_name = blob_result["blob_name"]
                blob_url = blob_result["blob_url"]
                item_id = blob_result["item_id"]
                
                # JSON은 로컬에 저장 (속성 데이터는 로컬에서 관리)
                json_file = self.output_dir / f"{item_id}.json"
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(attributes, f, ensure_ascii=False, indent=2)
                
                logger.info(f"Image saved to Blob Storage: {blob_name}, item_id: {item_id}")
                
                return {
                    "saved_to": str(json_file),
                    "image_url": blob_url,  # Blob Storage URL 사용
                    "item_id": item_id,
                    "blob_name": blob_name,
                    "storage_type": "blob_storage"
                }
            except Exception as e:
                logger.error(f"Failed to save to Blob Storage: {e}. Falling back to local storage.")
                # Blob Storage 저장 실패 시 로컬 저장으로 폴백
        
        # 로컬 파일 시스템에 저장 (Blob Storage가 없거나 실패한 경우)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        milliseconds = int(time.time() * 1000) % 1000
        random_suffix = random.randint(1000, 9999)
        base_id = f"attributes_{timestamp}_{milliseconds:03d}_{random_suffix}"
        
        # Save JSON
        json_file = self.output_dir / f"{base_id}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(attributes, f, ensure_ascii=False, indent=2)
        
        # Save image file - use validator for extension
        if original_filename:
            ext = validate_file_extension(original_filename)
        else:
            ext = '.jpg'
        
        image_file = self.output_dir / f"{base_id}{ext}"
        with open(image_file, 'wb') as f:
            f.write(image_bytes)
        
        image_url = f"/api/images/{base_id}{ext}"
        
        logger.info(f"Image saved to local storage: {base_id}")
        
        return {
            "saved_to": str(json_file),
            "image_url": image_url,
            "item_id": base_id,
            "storage_type": "local"
        }

wardrobe_manager = WardrobeManager()
