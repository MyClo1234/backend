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

    # 색상 추출 (features.color.primary 또는 features.color)
    color_raw = features.get("color")
    if isinstance(color_raw, dict):
        color = color_raw.get("primary", "unknown")
    elif isinstance(color_raw, str):
        color = color_raw
    else:
        color = "unknown"

    # 카테고리 추출 (features.category.sub 또는 item.category)
    category_raw = features.get("category")
    if isinstance(category_raw, dict):
        category = category_raw.get("sub", "clothing")
    elif isinstance(category_raw, str):
        category = category_raw
    else:
        # features에 없으면 DB의 category/sub_category 사용
        category = item.sub_category or item.category or "clothing"

    # 소재 추출
    material_raw = features.get("material")
    if isinstance(material_raw, dict):
        material = material_raw.get("guess", "")
    elif isinstance(material_raw, str):
        material = material_raw
    else:
        material = ""

    desc = f"{color} {category}"
    if material:
        desc += f" made of {material}"
    
    logger.debug(f"Item description for {item.id}: {desc}")
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
    Nano Banana를 사용하여 composite 이미지 생성 (마네킹 기반)
    """
    logger.info(
        f"Generating composite image for top={top.id} (category={top.category}), "
        f"bottom={bottom.id} (category={bottom.category}), "
        f"user={user.id} (gender={user.gender}, body_shape={user.body_shape})"
    )

    # Get descriptions
    top_desc = get_item_description_en(top)
    bottom_desc = get_item_description_en(bottom)
    logger.info(f"Item descriptions - Top: {top_desc}, Bottom: {bottom_desc}")

    try:
        client = NanoBananaClient()

        if not client.client:
            error_msg = "Nano Banana client not initialized. Check Google Cloud credentials."
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        # Get mannequin bytes (base mannequin preserving body shape)
        man_bytes = mannequin_manager.get_mannequin_bytes(user.gender, user.body_shape)
        if not man_bytes:
            error_msg = f"Failed to load mannequin image for gender={user.gender}, body_shape={user.body_shape}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        logger.info(f"Loaded mannequin bytes: {len(man_bytes)} bytes")

        # Generate and Upload (Client handles logic)
        # 1:1 비율로 정사각형 이미지 생성 (Flutter 컨테이너에 맞춤)
        image_url = client.generate_mannequin_composite(
            top_description=top_desc,
            bottom_description=bottom_desc,
            mannequin_bytes=man_bytes,
            gender=user.gender,
            body_shape=user.body_shape,
            user_id=str(user.id),
            reference_images=None,  # 레퍼런스 이미지 사용 안 함
            aspect_ratio="1:1",  # 정사각형 비율
        )

        if image_url:
            logger.info(f"[SUCCESS] Composite image generated successfully: {image_url}")
            return image_url
        else:
            logger.warning("[FAILED] Nano Banana returned None - image generation failed")
            return None

    except RuntimeError as e:
        # 명시적인 RuntimeError는 그대로 전파 (호출자가 처리)
        logger.error(f"Runtime error in image generation: {e}", exc_info=True)
        raise
    except Exception as e:
        logger.error(f"Unexpected error in image generation: {e}", exc_info=True)
        return None
