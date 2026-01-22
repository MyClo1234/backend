import os
import json
import time
import random
from datetime import datetime
from typing import List, Dict, Any
from azure.storage.blob import BlobServiceClient, ContentSettings
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
        self, image_bytes: bytes, original_filename: str, attributes: dict
    ) -> dict:
        if not self.container_client:
            raise Exception("Blob Storage not initialized")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        milliseconds = int(time.time() * 1000) % 1000
        random_suffix = random.randint(1000, 9999)
        base_id = f"attributes_{timestamp}_{milliseconds:03d}_{random_suffix}"

        # Save JSON
        json_filename = f"{base_id}.json"
        json_client = self.container_client.get_blob_client(json_filename)
        json_data = json.dumps(attributes, ensure_ascii=False, indent=2)
        json_client.upload_blob(
            json_data,
            overwrite=True,
            content_settings=ContentSettings(content_type="application/json"),
        )

        # Save image file
        if original_filename:
            ext = validate_file_extension(original_filename)
        else:
            ext = ".jpg"

        image_filename = f"{base_id}{ext}"
        image_client = self.container_client.get_blob_client(image_filename)

        # Determine content type based on extension
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

        return {
            "saved_to": json_filename,  # Return blob name
            "image_url": image_client.url,
            "item_id": base_id,
        }


wardrobe_manager = WardrobeManager()
