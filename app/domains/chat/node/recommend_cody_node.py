import logging
from app.domains.chat.states import ChatState
from app.llm.todays_pick_service import recommend_todays_pick_v2
from app.domains.weather.service import weather_service

logger = logging.getLogger(__name__)


async def recommend_cody_node(state: ChatState) -> ChatState:
    """추천 의도가 감지되었을 때 추천 서비스를 호출하는 노드"""
    from app.database import SessionLocal
    from uuid import UUID

    user_id = state["context"].get("user_id")
    tpo = state["context"].get("tpo")
    special_request = state["context"].get("special_request")

    # 위치 정보 (Flutter에서 전달받은 값 또는 기본값 서울)
    lat = state["context"].get("lat", 37.5665)
    lon = state["context"].get("lon", 126.9780)

    try:
        with SessionLocal() as db:
            # 0. 이전 추천 확인 (다른 옷 추천 시 제외하기 위해)
            from app.domains.recommendation.model import TodaysPick

            user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
            previous_pick = (
                db.query(TodaysPick)
                .filter(TodaysPick.user_id == user_uuid)
                .order_by(TodaysPick.created_at.desc())
                .first()
            )
            
            # 1. 중앙화된 날씨 정보 가져오기 (비동기 처리)
            weather_data = await weather_service.get_weather_info(db, lat, lon)
            
            # 2. 문맥 생성 (이전 추천 정보 포함)
            context_parts = []
            if tpo:
                context_parts.append(f"TPO: {tpo}")
            if special_request:
                context_parts.append(f"요청사항: {special_request}")
            
            # 이전 추천이 있고, "다른 옷" 요청이 있으면 제외 지시 추가
            if previous_pick and previous_pick.top_item_id and previous_pick.bottom_item_id:
                if special_request and ("다른" in special_request or "다시" in special_request or "새로운" in special_request):
                    context_parts.append(
                        f"이전에 추천한 조합(상의 ID: {previous_pick.top_item_id}, 하의 ID: {previous_pick.bottom_item_id})은 제외하고 다른 조합을 추천해주세요."
                    )
            
            context = ", ".join(context_parts) if context_parts else None

            # 2. Today's Pick 추천 엔진 호출 (문맥 포함)
            result = recommend_todays_pick_v2(
                user_id=user_uuid,
                weather=weather_data,
                db=db,
                context=context,
            )

            if result.get("success"):
                state["todays_pick"] = result
                state["context"]["is_pick_updated"] = True

                # AI 응답 생성
                weather_summary = result.get("weather_summary", "날씨 정보 없음")
                reasoning = result.get("reasoning", "코디를 추천해 드립니다.")

                response_parts = []
                if tpo:
                    response_parts.append(f"오늘 {tpo} 일정이 있으시군요!")

                response_parts.append(
                    f"현재 날씨({weather_summary})와 요청하신 내용을 바탕으로 새로운 '오늘의 추천'을 준비했습니다."
                )
                response_parts.append(f"\n추천 사유: {reasoning}")
                response_parts.append(
                    "\n홈 화면에서 나노바나나가 생성한 마네킹 이미지를 바로 확인하실 수 있어요!"
                )

                state["response"] = "\n".join(response_parts)
            else:
                state["response"] = (
                    "죄송합니다, 현재 옷장 정보를 바탕으로 적절한 코디를 찾지 못했습니다."
                )

    except ValueError as ve:
        logger.warning("Recommendation validation error: %s", ve)
        state["response"] = (
            str(ve)
            if "Insufficient wardrobe items" in str(ve)
            else "죄송합니다, 옷장에 추천할 만한 옷이 충분하지 않아요. 상의와 하의를 더 등록해 주세요!"
        )

    except Exception as e:
        logger.error("Error in handle_recommendation_node: %s", e, exc_info=True)
        state["response"] = (
            "코디를 추천하는 중에 문제가 발생했습니다. 잠시 후 다시 시도해 주세요."
        )

    return state
