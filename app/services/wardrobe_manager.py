import os
import json
import time
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.core.config import Config

class WardrobeManager:
    def __init__(self):
        self.output_dir = Config.OUTPUT_DIR
        os.makedirs(self.output_dir, exist_ok=True)

    def load_items(self) -> List[Dict[str, Any]]:
        items = []
        if not os.path.exists(self.output_dir):
            return items
        
        try:
            for filename in os.listdir(self.output_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.output_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            attributes = json.load(f)
                            item_id = filename.replace('.json', '')
                            
                            # Check if corresponding image exists
                            image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
                            image_path = None
                            for ext in image_extensions:
                                potential_image = os.path.join(self.output_dir, f"{item_id}{ext}")
                                if os.path.exists(potential_image):
                                    image_path = f"/api/images/{item_id}{ext}"
                                    break
                            
                            items.append({
                                "id": item_id,
                                "filename": filename,
                                "attributes": attributes,
                                "image_url": image_path
                            })
                    except Exception as e:
                        print(f"Error loading {filename}: {e}")
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
        json_filename = f"{self.output_dir}/{base_id}.json"
        with open(json_filename, 'w', encoding='utf-8') as f:
            json.dump(attributes, f, ensure_ascii=False, indent=2)
        
        # Save image file
        if original_filename:
            _, ext = os.path.splitext(original_filename)
            if ext.lower() not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                ext = '.jpg'
        else:
            ext = '.jpg'
        
        image_filename = f"{self.output_dir}/{base_id}{ext}"
        with open(image_filename, 'wb') as f:
            f.write(image_bytes)
        
        image_url = f"/api/images/{base_id}{ext}"
        
        return {
            "saved_to": json_filename,
            "image_url": image_url,
            "item_id": base_id
        }

wardrobe_manager = WardrobeManager()
