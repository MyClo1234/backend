from typing import Dict, Any, List
import logging
from app.ai.schemas.workflow_state import ChatState
from app.ai.clients.nano_banana_client import NanoBananaClient
from app.utils.blob_storage import get_blob_storage_service
from app.domains.recommendation.model import TodaysPick
from app.database import get_db
from app.domains.wardrobe.model import ClosetItem
from app.domains.user.model import User
from sqlalchemy.orm import Session
from app.utils.mannequin_manager import mannequin_manager
import os
from typing import Optional

logger = logging.getLogger(__name__)


def get_item_description_en(item: ClosetItem) -> str:
    """Generate an English description of the item for Imagen prompt"""
    features = item.features or {}

    color = features.get("color", {}).get("primary", "unknown")
    category = features.get("category", {}).get("sub", "clothing")
    material = features.get("material", {}).get("guess", "")

    desc = f"{color} {category}"
    if material:
        desc += f" made of {material}"
    return desc


def generate_todays_pick_composite(
    top: ClosetItem, bottom: ClosetItem, user: User, db: Session
) -> Optional[str]:
    """
    Nano Banana를 사용하여 composite 이미지 생성
    """
    logger.info(f"Generating composite image for top={top.id}, bottom={bottom.id}")

    # Get descriptions
    top_desc = get_item_description_en(top)
    bottom_desc = get_item_description_en(bottom)

    try:
        client = NanoBananaClient()

        if not client.model:
            raise RuntimeError("Nano Banana client not initialized")

        # Get mannequin bytes
        man_bytes = mannequin_manager.get_mannequin_bytes(user.gender, user.body_shape)

        # Generate and Upload (Client handles logic)
        image_url = client.generate_mannequin_composite(
            top_description=top_desc,
            bottom_description=bottom_desc,
            mannequin_bytes=man_bytes,
            gender=user.gender,
            body_shape=user.body_shape,
            user_id=str(user.id),
        )

        if image_url:
            logger.info(f"✅ Composite image generated: {image_url}")
            return image_url
        else:
            logger.warning("Nano Banana returned None")
            return None

    except Exception as e:
        logger.error(f"Image generation error: {e}", exc_info=True)
        return None
