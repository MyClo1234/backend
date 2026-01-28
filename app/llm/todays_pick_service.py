"""
Simplified Today's Pick service - Uses AI Nodes for core logic
"""

import logging
from typing import Dict, List, Optional, Tuple
from uuid import UUID
from datetime import date
from sqlalchemy.orm import Session

from app.domains.recommendation.model import TodaysPick
from app.domains.wardrobe.model import ClosetItem
from app.domains.user.model import User

# Import Logic from AI Nodes
from app.ai.nodes.recommendation_nodes import recommend_todays_pick_outfit
from app.ai.nodes.generation_nodes import generate_todays_pick_composite

logger = logging.getLogger(__name__)


def fetch_wardrobe_items(
    user_id: UUID, db: Session
) -> Tuple[List[ClosetItem], List[ClosetItem]]:
    """
    사용자 옷장에서 상의와 하의를 가져옴
    """
    logger.info(f"Fetching wardrobe items for user {user_id}")

    # 모든 아이템 조회
    all_items = db.query(ClosetItem).filter(ClosetItem.user_id == str(user_id)).all()
    tops = []
    bottoms = []

    for item in all_items:
        if not item.features:
            continue

        category_main = item.features.get("category", {}).get("main", "")

        if category_main == "top":
            tops.append(item)
        elif category_main == "bottom":
            bottoms.append(item)

    logger.info(f"Found {len(tops)} tops and {len(bottoms)} bottoms")

    if not tops or not bottoms:
        raise ValueError(
            f"Insufficient wardrobe items: {len(tops)} tops, {len(bottoms)} bottoms"
        )

    return tops, bottoms


def save_todays_pick_to_db(
    user_id: UUID, recommendation: Dict, image_url: str, weather: Dict, db: Session
) -> TodaysPick:
    """
    Today's Pick을 DB에 저장
    """
    logger.info(f"Saving Today's Pick to database for user {user_id}")

    new_pick = TodaysPick(
        user_id=str(user_id),
        date=date.today(),
        top_item_id=str(recommendation["top_id"]),
        bottom_item_id=str(recommendation["bottom_id"]),
        image_url=image_url,
        reasoning=recommendation["reasoning"],
        score=float(recommendation["score"]),
        weather_snapshot={
            "summary": weather.get("summary"),
            "temp_min": weather.get("temp_min"),
            "temp_max": weather.get("temp_max"),
        },
    )

    db.add(new_pick)
    db.commit()
    db.refresh(new_pick)

    logger.info(f"✅ Today's Pick saved with ID: {new_pick.id}")

    return new_pick


def recommend_todays_pick_v2(
    user_id: UUID, weather: Dict, db: Session, context: Optional[str] = None
) -> Dict:
    """
    Today's Pick 추천 메인 함수 (이미지 생성 필수)
    """
    logger.info(
        f"=== Starting Today's Pick recommendation for user {user_id} with context: {context} ==="
    )

    try:
        # 0. 매퍼 초기화 (지연 로드 방지)
        from app.utils.model_init import init_all_models

        init_all_models()

        # 1. User 정보 가져오기
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User not found: {user_id}")

        # 2. 옷장에서 아이템 가져오기
        tops, bottoms = fetch_wardrobe_items(user_id, db)

        # 3. LLM으로 추천 (AI Node 호출)
        recommendation = recommend_todays_pick_outfit(
            tops=tops, bottoms=bottoms, weather=weather, context=context
        )

        # 4. 이미지 생성 (AI Node 호출)
        top_item = next(
            (t for t in tops if str(t.id) == str(recommendation["top_id"])), None
        )
        bottom_item = next(
            (b for b in bottoms if str(b.id) == str(recommendation["bottom_id"])), None
        )

        if not top_item or not bottom_item:
            raise ValueError(
                f"Selected items not found in wardrobe: top={recommendation['top_id']}, bottom={recommendation['bottom_id']}"
            )

        image_url = generate_todays_pick_composite(top_item, bottom_item, user, db)

        # If generation failed, handle it
        if not image_url:
            logger.warning(
                "Image generation failed. Recommended items still being saved."
            )
            image_url = ""

        # 5. DB 저장
        saved_pick = save_todays_pick_to_db(
            user_id, recommendation, image_url, weather, db
        )

        logger.info("=== Today's Pick recommendation completed successfully ===")

        from app.domains.wardrobe.service import wardrobe_manager

        return {
            "success": True,
            "pick_id": str(saved_pick.id),
            "top_id": str(saved_pick.top_item_id),
            "bottom_id": str(saved_pick.bottom_item_id),
            "image_url": wardrobe_manager.get_sas_url(saved_pick.image_url),
            "reasoning": saved_pick.reasoning,
            "score": saved_pick.score,
            "weather": saved_pick.weather_snapshot,
            "weather_summary": weather.get("summary", ""),
            "temp_min": float(weather.get("temp_min", 0.0)),
            "temp_max": float(weather.get("temp_max", 0.0)),
            "message": "새로운 오늘의 추천을 생성했습니다.",
        }

    except Exception as e:
        logger.error(f"❌ Today's Pick recommendation failed: {str(e)}", exc_info=True)
        raise
