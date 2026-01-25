import os
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID
from azure.storage.blob import (
    BlobServiceClient,
    ContentSettings,
    generate_blob_sas,
    BlobSasPermissions,
)
from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.core.config import Config
from app.utils.validators import validate_file_extension

# Import models inside methods to avoid circular imports where possible,
# or use TYPE_CHECKING pattern. For simplicity in this file scope:
from app.models.schemas import WardrobeItemSchema, AttributesSchema


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

    def generate_sas_token(self, blob_name: str, container_name: str = None) -> str:
        """Generate a read-only SAS token for a specific blob"""
        try:
            if not self.account_name or not self.account_key:
                return ""

            target_container = container_name or self.container_name

            sas_token = generate_blob_sas(
                account_name=self.account_name,
                container_name=target_container,
                blob_name=blob_name,
                account_key=self.account_key,
                permission=BlobSasPermissions(read=True),
                start=datetime.utcnow() - timedelta(minutes=15),  # Clock skew buffer
                expiry=datetime.utcnow() + timedelta(hours=1),
            )
            return sas_token
        except Exception as e:
            print(f"Error generating SAS token: {e}")
            return ""

    def get_sas_url(self, image_path: str) -> str:
        """Helper to append SAS token to a blob URL, handling dynamic containers"""
        if not ".blob.core.windows.net/" in image_path:
            return image_path

        try:
            # Extract blob name from URL
            parts = image_path.split(".blob.core.windows.net/")
            if len(parts) > 1:
                # e.g. "images/users/..." or "codify0blob0storage/users/..."
                container_and_blob = parts[1]

                # Split container and blob path dynamically
                if "/" in container_and_blob:
                    container_name, blob_name = container_and_blob.split("/", 1)

                    sas_token = self.generate_sas_token(
                        blob_name, container_name=container_name
                    )
                    if sas_token:
                        return f"{image_path}?{sas_token}"
        except Exception:
            pass

        return image_path

    def load_items(self) -> List[Dict[str, Any]]:
        # ... (Legacy logic kept if needed, but we focusing on new methods)
        items = []
        if not self.container_client:
            return items
        # ... (Keeping existing implementation or placeholder if it's unused now.
        # User only asked to move get_user_wardrobe_images_internal.
        # I will leave load_items as is for safety of other endpoints.)
        try:
            blobs = self.container_client.list_blobs()
            item_map = {}
            for blob in blobs:
                name_parts = os.path.splitext(blob.name)
                item_id = name_parts[0]
                ext = name_parts[1].lower()
                if item_id not in item_map:
                    item_map[item_id] = {"json": None, "image": None, "id": item_id}
                if ext == ".json":
                    item_map[item_id]["json"] = blob.name
                elif ext in [".jpg", ".jpeg", ".png", ".gif", ".webp"]:
                    item_map[item_id]["image"] = blob.name

            for item_id, data in item_map.items():
                if data["json"] and data["image"]:
                    try:
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
                                "filename": data["image"],
                                "attributes": attributes,
                                "image_url": image_url,
                            }
                        )
                    except Exception as e:
                        print(f"Error loading item {item_id}: {e}")
        except Exception as e:
            print(f"Error reading from Blob Storage: {e}")
        return items

    def get_user_wardrobe_items(
        self,
        db: Session,
        user_id: UUID,
        category: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Dict[str, Any]:
        """Get paginated wardrobe items from DB (optimized for feed)"""
        from app.models.wardrobe import ClosetItem

        try:
            # 1. Base Query
            query = db.query(ClosetItem).filter(ClosetItem.user_id == user_id)

            # 2. Filter by Category
            if category:
                query = query.filter(ClosetItem.category == category.lower())

            # 3. Total Count
            total_count = query.count()

            if total_count == 0:
                return {"items": [], "count": 0, "total_count": 0, "has_more": False}

            # 4. Apply Pagination
            closet_items = (
                query.order_by(ClosetItem.id.desc()).offset(skip).limit(limit).all()
            )

            # 5. Determine has_more
            has_more = (skip + len(closet_items)) < total_count

            # 6. Convert to Schema (OPTIMIZED: No Blob Reading)
            items: List[WardrobeItemSchema] = []

            for item in closet_items:
                # Minimal Attributes from DB only
                attributes_schema = AttributesSchema(
                    category={
                        "main": item.category.lower() if item.category else "unknown",
                        "sub": item.sub_category.lower() if item.sub_category else "",
                        "confidence": 1.0,
                    },
                )

                # Generate SAS URL
                final_image_url = self.get_sas_url(item.image_path)

                wardrobe_item = WardrobeItemSchema(
                    id=str(item.id),
                    filename=f"item_{item.id}",
                    attributes=attributes_schema,
                    image_url=final_image_url,
                )
                items.append(wardrobe_item)

            return {
                "items": items,
                "count": len(items),
                "total_count": total_count,
                "has_more": has_more,
            }
        except Exception as e:
            print(f"Error in get_user_wardrobe_items: {e}")
            raise e

    def get_item_detail(
        self, db: Session, item_id: str, user_id: UUID
    ) -> WardrobeItemSchema:
        """Get detailed item info including Blob metadata"""
        from app.models.wardrobe import ClosetItem

        # 1. Fetch from DB
        item = db.query(ClosetItem).filter(ClosetItem.id == item_id).first()
        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        # 2. Check ownership
        if str(item.user_id) != str(user_id):
            raise HTTPException(
                status_code=403, detail="Not authorized to view this item"
            )

        # 3. Load full attributes
        image_path = item.image_path
        blob_name = None

        if ".blob.core.windows.net/" in image_path:
            parts = image_path.split(".blob.core.windows.net/")
            if len(parts) > 1:
                container_and_blob = parts[1]
                container_prefix = f"{self.container_name}/"
                if container_and_blob.startswith(container_prefix):
                    blob_name = container_and_blob[len(container_prefix) :]

        attributes: Dict[str, Any] = {}
        if blob_name and self.container_client:
            try:
                base_id = os.path.splitext(blob_name)[0]
                json_blob_name = f"{base_id}.json"
                json_client = self.container_client.get_blob_client(json_blob_name)
                if json_client.exists():
                    json_content = json_client.download_blob().readall()
                    attributes = json.loads(json_content)
            except Exception as e:
                print(f"Warning: Could not load JSON for item {item.id}: {e}")
                attributes = item.features or {}
        else:
            attributes = item.features or {}

        # Merge DB fields
        if "category" not in attributes:
            attributes["category"] = {
                "main": item.category.lower() if item.category else "unknown",
                "sub": item.sub_category.lower() if item.sub_category else "",
                "confidence": 1.0,
            }
        if item.season:
            attributes["season"] = item.season
        if item.mood_tags:
            attributes["mood_tags"] = item.mood_tags

        # Create Schema
        attributes_schema = AttributesSchema(**attributes)

        # Generate SAS URL
        final_image_url = self.get_sas_url(image_path)

        return WardrobeItemSchema(
            id=str(item.id),
            filename=blob_name.split("/")[-1] if blob_name else f"item_{item.id}",
            attributes=attributes_schema,
            image_url=final_image_url,
        )

    def save_item(
        self,
        db: Session,
        image_bytes: bytes,
        original_filename: str,
        attributes: dict,
        user_id: UUID,
    ) -> dict:
        if not self.container_client:
            raise Exception("Blob Storage not initialized")

        # 1. Save Image to Blob
        namespace_uuid = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")
        user_uuid = str(uuid.uuid5(namespace_uuid, f"user_{user_id}"))

        now = datetime.now()
        date_str = now.strftime("%Y%m%d")
        image_uuid = str(uuid.uuid4())

        if original_filename:
            ext = validate_file_extension(original_filename)
        else:
            ext = ".jpg"

        image_filename = f"users/{user_uuid}/{date_str}/{image_uuid}{ext}"
        image_client = self.container_client.get_blob_client(image_filename)

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

        # 2. Save to Database
        from app.models.wardrobe import ClosetItem

        category_raw = attributes.get("category", {})
        if isinstance(category_raw, dict):
            category = category_raw.get("main", "UNKNOWN")
            sub_category = category_raw.get("sub") or attributes.get("sub_category")
        else:
            category = str(category_raw) if category_raw else "UNKNOWN"
            sub_category = attributes.get("sub_category")

        features = attributes.copy()
        for key in ["category", "sub_category", "season", "mood_tags"]:
            if key in features:
                del features[key]

        season = attributes.get("season", [])
        if isinstance(season, str):
            season = [season]

        mood_tags = attributes.get("mood_tags", [])
        if isinstance(mood_tags, str):
            mood_tags = [mood_tags]

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
