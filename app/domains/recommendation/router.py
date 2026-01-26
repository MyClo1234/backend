from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Query, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import ALGORITHM, SECRET_KEY
from app.domains.wardrobe.service import wardrobe_manager
from .service import recommender
from .schema import (
    RecommendationResponse,
    OutfitScoreResponse,
    TodaysPickRequest,
    TodaysPickResponse,
)
from app.domains.wardrobe.schema import WardrobeItemSchema
from app.core.schemas import AttributesSchema
from app.utils.response_helpers import create_success_response, handle_route_exception

recommendation_router = APIRouter()
security = HTTPBearer()


def get_user_id_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UUID:
    """JWT 토큰에서 user_id를 추출하는 헬퍼 함수"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str = payload.get("user_id")
        if user_id_str is None:
            raise credentials_exception
        return UUID(user_id_str)
    except (JWTError, ValueError) as e:
        raise credentials_exception


@recommendation_router.post("/recommend/todays-pick", response_model=TodaysPickResponse)
def recommend_todays_pick(
    request: TodaysPickRequest,
    user_id: UUID = Depends(get_user_id_from_token),
    db: Session = Depends(get_db),
):
    """
    오늘의 추천 코디 (Today's Pick)

    사용자의 위치(위도, 경도)를 기반으로 날씨를 조회하고,
    사용자의 옷장에서 현재 날씨/계절에 적합한 옷을 찾아 추천합니다.
    """
    try:
        result = recommender.get_todays_pick(db, user_id, request.lat, request.lon)
        return result
    except Exception as e:
        raise handle_route_exception(e)


@recommendation_router.get("/outfit/score", response_model=OutfitScoreResponse)
def get_outfit_score(top_id: str = Query(...), bottom_id: str = Query(...)):
    try:
        all_items = wardrobe_manager.load_items()

        top_item = next((item for item in all_items if item.get("id") == top_id), None)
        bottom_item = next(
            (item for item in all_items if item.get("id") == bottom_id), None
        )

        if not top_item or not bottom_item:
            raise HTTPException(status_code=404, detail="Items not found")

        score, reasons = recommender.calculate_outfit_score(top_item, bottom_item)

        return create_success_response(
            {
                "score": round(score, 3),
                "score_percent": round(score * 100),
                "reasons": reasons,
                "top": top_item,
                "bottom": bottom_item,
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise handle_route_exception(e)


@recommendation_router.get("/recommend/outfit", response_model=RecommendationResponse)
def recommend_outfit(
    count: int = Query(1, ge=1),
    season: Optional[str] = Query(None),
    formality: Optional[float] = Query(None),
    use_llm: bool = Query(
        True, description="LLM 사용 여부 (기본값: true, Azure OpenAI 사용)"
    ),
):
    try:
        all_items = wardrobe_manager.load_items()

        tops = [
            item
            for item in all_items
            if item.get("attributes", {}).get("category", {}).get("main") == "top"
        ]
        bottoms = [
            item
            for item in all_items
            if item.get("attributes", {}).get("category", {}).get("main") == "bottom"
        ]
        outers = [
            item
            for item in all_items
            if item.get("attributes", {}).get("category", {}).get("main") == "outer"
        ]

        if not tops or not bottoms:
            return create_success_response(
                {"outfits": []},
                count=0,
                method="none",
                message="Not enough items in wardrobe (need at least one top and one bottom)",
            )

        if season:
            tops = [
                t
                for t in tops
                if season.lower()
                in t.get("attributes", {}).get("scores", {}).get("season", [])
            ]
            bottoms = [
                b
                for b in bottoms
                if season.lower()
                in b.get("attributes", {}).get("scores", {}).get("season", [])
            ]
            outers = [
                o
                for o in outers
                if season.lower()
                in o.get("attributes", {}).get("scores", {}).get("season", [])
            ]

        if formality is not None:
            tops = [
                t
                for t in tops
                if abs(
                    t.get("attributes", {}).get("scores", {}).get("formality", 0.5)
                    - formality
                )
                <= 0.3
            ]
            bottoms = [
                b
                for b in bottoms
                if abs(
                    b.get("attributes", {}).get("scores", {}).get("formality", 0.5)
                    - formality
                )
                <= 0.3
            ]
            outers = [
                o
                for o in outers
                if abs(
                    o.get("attributes", {}).get("scores", {}).get("formality", 0.5)
                    - formality
                )
                <= 0.3
            ]

        if not tops or not bottoms:
            return create_success_response(
                {"outfits": []},
                count=0,
                method="none",
                message="No items match the filters",
            )

        # Use Azure OpenAI (via LangGraph workflow) for recommendation
        if use_llm:
            try:
                # Modifying this call to pass outers.
                # Note: recommender.recommend_with_llm needs to be updated too.
                recommendations = recommender.recommend_with_llm(
                    tops, bottoms, count, outers=outers
                )
                if recommendations:
                    return create_success_response(
                        {"outfits": recommendations},
                        count=len(recommendations),
                        method="azure-openai-optimized",
                    )
            except Exception as e:
                print(f"LLM recommendation error: {e}")
                import traceback

                traceback.print_exc()
                # Fall through to rule-based fallback

        # Fallback: rule-based recommendation
        # rule based currently ignores outers or needs update?
        # For now, keep as is (Top/Bottom only)
        recommendations = recommender._rule_based_recommendation(tops, bottoms, count)
        return create_success_response(
            {"outfits": recommendations},
            count=len(recommendations),
            method="rule-based",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise handle_route_exception(e)
