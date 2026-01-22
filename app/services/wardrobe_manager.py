import os
import json
import time
import random
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.core.config import Config
from app.utils.validators import validate_file_extension

class WardrobeManager:
    def __init__(self):
        self.output_dir = Path(Config.OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

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

    def save_item(self, image_bytes: bytes, original_filename: str, attributes: dict) -> dict:
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
        
        return {
            "saved_to": str(json_file),
            "image_url": image_url,
            "item_id": base_id
        }

wardrobe_manager = WardrobeManager()
