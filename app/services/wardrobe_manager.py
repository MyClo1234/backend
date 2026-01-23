import os
import json
import uuid as uuid_lib
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID
from azure.storage.blob import BlobServiceClient, ContentSettings
from sqlalchemy.orm import Session
from app.core.config import Config
from app.utils.validators import validate_file_extension


class WardrobeManager:
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
                # Create container if it doesn't exist
                if not self.container_client.exists():
                    self.container_client.create_container()
            except Exception as e:
                print(f"Failed to initialize Blob Storage: {e}")

    def load_items(self) -> List[Dict[str, Any]]:
        items = []
        if not self.container_client:
            return items

        try:
            # List all blobs
            blobs = self.container_client.list_blobs()

            # Map items by ID to group JSON and image
            item_map = {}
            for blob in blobs:
                # blob.name e.g., "attributes_... .json" or "attributes_... .jpg"
                name_parts = os.path.splitext(blob.name)
                item_id = name_parts[0]
                ext = name_parts[1].lower()

                if item_id not in item_map:
                    item_map[item_id] = {"json": None, "image": None, "id": item_id}

                if ext == ".json":
                    item_map[item_id]["json"] = blob.name
                elif ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
                    item_map[item_id]["image"] = blob.name

            # Process valid items
            for item_id, data in item_map.items():
                if data["json"] and data["image"]:
                    try:
                        # Download JSON content
                        blob_client = self.container_client.get_blob_client(
                            data["json"]
                        )
                        json_content = blob_client.download_blob().readall()
                        attributes = json.loads(json_content)

                        image_url = self.container_client.get_blob_client(
                            data["image"]
                        ).url

                        items.append(
                            {
                                "id": item_id,
                                "filename": data["image"],  # Use blob name as filename
                                "attributes": attributes,
                                "image_url": image_url,
                            }
                        )
                    except Exception as e:
                        print(f"Error loading item {item_id}: {e}")

        except Exception as e:
            print(f"Error reading from Blob Storage: {e}")

        return items

    def save_item(
        self,
        db: Session,  # DB Session added
        image_bytes: bytes,
        original_filename: str,
        attributes: dict,
        user_id: UUID,  # Changed to UUID for FK
    ) -> dict:
        if not self.container_client:
            raise Exception("Blob Storage not initialized")

        # Generate blob path: users/{user_id}/{YMD}/{uuid}.{ext}
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")  # YYYYMMDD 형식
        file_uuid = str(uuid_lib.uuid4())  # 이미지 파일용 UUID
        
        # 확장자 추출
        if original_filename:
            ext = validate_file_extension(original_filename)
        else:
            ext = ".jpg"

        # Blob 경로 생성: users/{user_id}/{YMD}/{uuid}.{ext}
        blob_path = f"users/{user_id}/{date_str}/{file_uuid}{ext}"
        
        # JSON 파일 경로도 동일한 구조로 (확장자만 .json)
        json_blob_path = f"users/{user_id}/{date_str}/{file_uuid}.json"

        # 1. Save JSON to Blob (Legacy/Backup)
        json_client = self.container_client.get_blob_client(json_blob_path)
        json_data = json.dumps(attributes, ensure_ascii=False, indent=2)
        json_client.upload_blob(
            json_data,
            overwrite=True,
            content_settings=ContentSettings(content_type="application/json"),
        )

        # 2. Save Image to Blob
        image_client = self.container_client.get_blob_client(blob_path)

        # Determine content type
        content_type = "image/jpeg"
        if ext == ".png":
            content_type = "image/png"
        elif ext == ".gif":
            content_type = "image/gif"
        elif ext == ".webp":
            content_type = "image/webp"

        image_client.upload_blob(
            image_bytes,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type),
        )

        image_url = image_client.url

        # 3. Save to Database (ORM)
        from app.models.wardrobe import (
            ClosetItem,
        )  # Import here to avoid circular dependency

        # Create ClosetItem
        # Extract fields safely from attributes
        category_obj = attributes.get("category", {})
        if isinstance(category_obj, dict):
            category = category_obj.get("main", "UNKNOWN").upper()
            sub_category = category_obj.get("sub") or attributes.get("sub_category")
        else:
            category = str(category_obj).upper() if category_obj else "UNKNOWN"
            sub_category = attributes.get("sub_category")

        # Parse features (everything else)
        features = attributes.copy()
        if "category" in features:
            del features["category"]
        if "sub_category" in features:
            del features["sub_category"]

        # Season and Mood (if present in attributes, otherwise empty)
        season = attributes.get("season", [])
        if isinstance(season, str):  # Handle if it came as string
            season = [season]

        mood_tags = attributes.get("mood_tags", [])
        if isinstance(mood_tags, str):
            mood_tags = [mood_tags]

        # Clean features to separate season/mood if needed or keep them duplicate?
        # Let's clean them from features to avoid duplication if column exists
        if "season" in features:
            del features["season"]
        if "mood_tags" in features:
            del features["mood_tags"]

        db_item = ClosetItem(
            user_id=user_id,
            image_path=image_url,
            category=category,
            sub_category=sub_category,
            features=features,
            season=season,
            mood_tags=mood_tags,
        )
        db.add(db_item)
        db.commit()
        db.refresh(db_item)

        return {
            "saved_to": json_blob_path,
            "image_url": image_url,
            "item_id": db_item.id,  # Return DB ID
            "blob_name": blob_path,
        }


wardrobe_manager = WardrobeManager()
