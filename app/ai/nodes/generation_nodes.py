from typing import Dict, Any, List
import logging
from app.ai.schemas.workflow_state import ChatState
from app.ai.clients.nano_banana_client import NanoBananaClient
from app.utils.blob_storage import get_blob_storage_service
from app.domains.recommendation.model import TodaysPick
from app.database import get_db

logger = logging.getLogger(__name__)


def generate_todays_pick(state: ChatState) -> ChatState:
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

        finally:
            db.close()

    except Exception as e:
        logger.error(f"Error in generate_todays_pick node: {e}")

    return state
