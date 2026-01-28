from typing import Dict, Any, List
import logging
from app.domains.chat.states import ChatState
from app.ai.schemas.workflow_state import RecommendationState
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


def generate_todays_pick(state: RecommendationState) -> RecommendationState:
    """
    Todays Pick 이미지 생성 및 DB 저장 노드
    """
    try:
        recommendations = state.get("recommendations")
        context = state.get("context", {})
        user_id = context.get("user_id")

        if not recommendations or not user_id:
            logger.warning("No recommendations or user_id found for generation.")
            return state

        # 첫 번째 추천 조합 선택 (가장 높은 점수)
        best_outfit = recommendations[0]
        top_item = best_outfit.get("top")
        bottom_item = best_outfit.get("bottom")

        # 아이템 설명 구성 (프롬프트용)
        # TODO: 실제 옷 이미지 URL이나 특징을 더 자세히 반영해야 함
        top_desc = top_item.get("category", "top") if top_item else "shirt"
        bottom_desc = bottom_item.get("category", "bottom") if bottom_item else "pants"

        # 사용자 성별/체형 (Context에서 가져오거나 DB 조회 필요)
        # 여기서는 Context에 있다고 가정하거나 기본값 사용
        gender = context.get("gender", "korean man")  # Default

        # 프롬프트 생성
        prompt = f"A photo of a {gender} model wearing {top_desc} and {bottom_desc}. High quality, realistic, full body shot."

        # Nano Banana (Imagen) 호출
        client = NanoBananaClient()
        image_bytes = client.generate_image(prompt=prompt)

        if not image_bytes:
            logger.error("Failed to generate image.")
            return state

        # Blob Storage 업로드
        blob_service = get_blob_storage_service()
        upload_result = blob_service.upload_image(
            image_bytes=image_bytes,
            user_id=str(user_id),
            original_filename="todays_pick_gen.png",
            content_type="image/png",
        )

        image_url = upload_result["blob_url"]

        # DB 저장 (TodaysPick)
        db = next(get_db())
        try:
            todays_pick = TodaysPick(
                user_id=user_id,
                top_item_id=str(top_item.get("id")) if top_item else None,
                bottom_item_id=str(bottom_item.get("id")) if bottom_item else None,
                image_url=image_url,
                prompt=prompt,
            )
            db.add(todays_pick)
            db.commit()
            db.refresh(todays_pick)

            # State 업데이트
            state["todays_pick"] = {
                "id": str(todays_pick.id),
                "image_url": image_url,
                "items": best_outfit,
            }

            # 클라이언트 트리거용 플래그
            state["context"]["is_pick_updated"] = True

            # 이미지 생성 완료 메시지 (메시지 저장을 위해)
            # recommend_cody_node에서 이미 response가 있으면 덮어쓰지 않음
            if not state.get("response"):
                state["response"] = "오늘의 픽 이미지를 생성했습니다."

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error in generate_todays_pick node: {e}")

    return state


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


def generation_todays_pick_node(state: ChatState) -> ChatState:
    """
    Todays Pick 이미지 생성 및 DB 저장 노드
    """
    try:
        recommendations = state.get("recommendations")
        context = state.get("context", {})
        user_id = context.get("user_id")

        if not recommendations or not user_id:
            logger.warning("No recommendations or user_id found for generation.")
            return state

        # 첫 번째 추천 조합 선택 (가장 높은 점수)
        best_outfit = recommendations[0]
        top_item = best_outfit.get("top")
        bottom_item = best_outfit.get("bottom")

        # 아이템 설명 구성 (프롬프트용)
        # TODO: 실제 옷 이미지 URL이나 특징을 더 자세히 반영해야 함
        top_desc = top_item.get("category", "top") if top_item else "shirt"
        bottom_desc = bottom_item.get("category", "bottom") if bottom_item else "pants"

        # 사용자 성별/체형 (Context에서 가져오거나 DB 조회 필요)
        # 여기서는 Context에 있다고 가정하거나 기본값 사용
        gender = context.get("gender", "korean man")  # Default

        # 프롬프트 생성
        prompt = f"A photo of a {gender} model wearing {top_desc} and {bottom_desc}. High quality, realistic, full body shot."

        # Nano Banana (Imagen) 호출
        client = NanoBananaClient()
        image_bytes = client.generate_image(prompt=prompt)

        if not image_bytes:
            logger.error("Failed to generate image.")
            return state

        # Blob Storage 업로드
        blob_service = get_blob_storage_service()
        upload_result = blob_service.upload_image(
            image_bytes=image_bytes,
            user_id=str(user_id),
            original_filename="todays_pick_gen.png",
            content_type="image/png",
        )

        image_url = upload_result["blob_url"]

        # DB 저장 (TodaysPick)
        db = next(get_db())
        try:
            todays_pick = TodaysPick(
                user_id=user_id,
                top_item_id=str(top_item.get("id")) if top_item else None,
                bottom_item_id=str(bottom_item.get("id")) if bottom_item else None,
                image_url=image_url,
                prompt=prompt,
            )
            db.add(todays_pick)
            db.commit()
            db.refresh(todays_pick)

            # State 업데이트
            state["todays_pick"] = {
                "id": str(todays_pick.id),
                "image_url": image_url,
                "items": best_outfit,
            }

            # 클라이언트 트리거용 플래그
            state["context"]["is_pick_updated"] = True

            # 이미지 생성 완료 메시지 (메시지 저장을 위해)
            # recommend_cody_node에서 이미 response가 있으면 덮어쓰지 않음
            if not state.get("response"):
                state["response"] = "오늘의 픽 이미지를 생성했습니다."

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error in generate_todays_pick node: {e}")

    return state


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
