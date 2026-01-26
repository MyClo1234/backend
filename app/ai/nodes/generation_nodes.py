"""
패션 이미지 생성 LangGraph 노드
"""

import logging
import io
import requests
from typing import Dict, Any
from app.ai.schemas.workflow_state import RecommendationState
from app.ai.clients.azure_openai_client import azure_openai_client
from app.domains.wardrobe.service import wardrobe_manager
from app.core.config import Config

logger = logging.getLogger(__name__)


def nano_banana_node(state: RecommendationState) -> RecommendationState:
    """나노바나나가 코디의 이미지를 생성하고 스토리지에 저장하는 노드"""
    final_outfits = state.get("final_outfits", [])
    if not final_outfits:
        return state

    # 첫 번째 추천 코디에 대해 이미지 생성 (Today's Pick용)
    best_pick = final_outfits[0]
    top = best_pick.get("top", {})
    bottom = best_pick.get("bottom", {})
    style_desc = best_pick.get("style_description", "Modern fashion outfit")

    # 1. 시각화 프롬프트 구성 (나노바나나의 눈 - Vision 활용)
    try:
        images_to_analyze = []

        # 상의와 하의 이미지 다운로드
        for item in [top, bottom]:
            url = item.get("image_url")
            if url:
                # SAS 토큰 처리 등 보안 URL 확인 (wardrobe_manager 활용 가능)
                final_url = wardrobe_manager.get_sas_url(url)
                resp = requests.get(final_url)
                if resp.status_code == 200:
                    images_to_analyze.append(resp.content)

        if images_to_analyze:
            logger.info(
                f"나노바나나가 실제 옷 사진 {len(images_to_analyze)}장을 분석 중입니다..."
            )
            vision_prompt = (
                "You are a fashion expert observer. Look at the provided images of a top and a bottom. "
                "Describe them in extreme detail for an image generator. Focus on: "
                "1. Exact colors and shades. 2. Fabric and texture. 3. Small details like buttons, patterns, or logos. "
                "4. The overall fit and style. "
                "Return a concise, high-quality descriptive paragraph for DALL-E to recreate this exact coordination."
            )

            # 나노바나나의 눈(Vision)으로 분석
            visual_description = azure_openai_client.generate_content(
                prompt=vision_prompt, images=images_to_analyze, temperature=0.3
            )
            logger.info(f"시각적 분석 완료: {visual_description[:100]}...")

            prompt = (
                f"A professional fashion studio photography of a full outfit coordination. "
                f"The outfit consists of the following specific items: {visual_description}. "
                f"Style Concept: {style_desc}. "
                f"The items are arranged neatly on a clean, minimal white background. "
                f"High quality, 8k resolution, commercial fashion photography style."
            )
        else:
            # 사진을 못 불러온 경우 텍스트 속성으로 폴백
            top_attrs = top.get("attributes", {})
            bottom_attrs = bottom.get("attributes", {})
            prompt = (
                f"A professional fashion studio photography of a full outfit coordination. "
                f"Top: {top_attrs.get('color', {}).get('primary', '')} {top_attrs.get('category', {}).get('sub', 'top')}. "
                f"Bottom: {bottom_attrs.get('color', {}).get('primary', '')} {bottom_attrs.get('category', {}).get('sub', 'bottom')}. "
                f"Style: {style_desc}. "
                f"The items are arranged neatly on a clean, minimal white background. "
                f"High quality, 8k resolution, commercial fashion photography style."
            )
    except Exception as e:
        logger.warning(f"Vision analysis failed: {e}. Falling back to text prompt.")
        # 폴백 프롬프트 (기존 코드와 유사)
        prompt = f"Fashion coordination: {style_desc} style with {top.get('id')} and {bottom.get('id')}."

    try:
        # 2. 나노바나나 이미지 생성
        image_url = azure_openai_client.generate_image(prompt=prompt)

        # 3. 이미지 다운로드 및 Blob Storage 저장
        response = requests.get(image_url)
        if response.status_code == 200:
            image_bytes = response.content

            # 사용자별 고유 경로 설정 (images/users/todaypicke/)
            import uuid
            from datetime import datetime

            user_id = state.get("metadata", {}).get("user_id", "unknown")
            pick_uuid = str(uuid.uuid4())
            date_str = datetime.now().strftime("%Y%m%d")

            # 파일 경로: images/users/todaypicke/{user_id}/{date_str}_{pick_uuid}.png
            blob_path = f"images/users/todaypicke/{user_id}/{date_str}_{pick_uuid}.png"

            # WardrobeManager의 인스턴스를 사용하여 업로드 (컨테이너: codify0blob0storage)
            # NOTE: wardrobe_manager.save_item은 DB 저장까지 같이 하므로,
            # 여기서는 순수하게 Blob 업로드 기능만 필요함.
            # 임시로 wardrobe_manager의 client를 직접 사용하거나 내부 메서드 활용.

            if wardrobe_manager.container_client:
                blob_client = wardrobe_manager.container_client.get_blob_client(
                    blob_path
                )
                from azure.storage.blob import ContentSettings

                blob_client.upload_blob(
                    image_bytes,
                    overwrite=True,
                    content_settings=ContentSettings(content_type="image/png"),
                )

                final_stored_url = blob_client.url
                logger.info(f"Today's Pick image saved: {final_stored_url}")

                # 상태 업데이트
                best_pick["generated_image_url"] = final_stored_url
                state["metadata"]["generated_image_path"] = blob_path
            else:
                logger.error("Blob Storage container client not initialized")
        else:
            logger.error(f"Failed to download generated image: {response.status_code}")

    except Exception as e:
        logger.error(f"Error in nano_banana_node: {str(e)}", exc_info=True)
        state["metadata"]["generation_error"] = str(e)

    return state
