import os
import json
import uuid
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

        # 1. Save Image to Blob with folder structure: users/{user_uuid}/{yyyyMMdd}/{uuid}.{ext}
        # Convert user_id to UUID (deterministic UUID based on user_id)
        # Using UUID5 with a fixed namespace to generate consistent UUID for each user_id
        namespace_uuid = uuid.UUID(
            "6ba7b810-9dad-11d1-80b4-00c04fd430c8"
        )  # Standard namespace
        user_uuid = str(uuid.uuid5(namespace_uuid, f"user_{user_id}"))

        # Get current date for folder structure
        now = datetime.now()
        date_str = now.strftime("%Y%m%d")  # yyyyMMdd

        # Generate UUID for image filename
        image_uuid = str(uuid.uuid4())

        # Get file extension
        if original_filename:
            ext = validate_file_extension(original_filename)
        else:
            ext = ".jpg"

        # Create blob path: users/{user_uuid}/{yyyyMMdd}/{uuid}.{ext}
        image_filename = f"users/{user_uuid}/{date_str}/{image_uuid}{ext}"
        image_client = self.container_client.get_blob_client(image_filename)

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

        # 2. Save to Database (ORM)
        from app.models.wardrobe import (
            ClosetItem,
        )  # Import here to avoid circular dependency

        # Create ClosetItem
        # Extract fields safely from attributes
        # Handle category as dict or string
        category_raw = attributes.get("category", {})
        if isinstance(category_raw, dict):
            category = category_raw.get("main", "UNKNOWN")
            sub_category = category_raw.get("sub") or attributes.get("sub_category")
        else:
            category = str(category_raw) if category_raw else "UNKNOWN"
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
            "success": "success",
            "image_url": image_url,
            "item_id": db_item.id,
            "blob_name": image_filename,
        }


wardrobe_manager = WardrobeManager()
