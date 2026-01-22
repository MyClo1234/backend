from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from app.services.wardrobe_manager import wardrobe_manager
from app.services.recommender import recommender
from app.models.schemas import OutfitScoreResponse, RecommendationResponse
from app.utils.response_helpers import create_success_response, handle_route_exception

recommendation_router = APIRouter()


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

        return create_success_response({
            "score": round(score, 3),
            "score_percent": round(score * 100),
            "reasons": reasons,
            "top": top_item,
            "bottom": bottom_item,
        })
    except HTTPException:
        raise
    except Exception as e:
        raise handle_route_exception(e)


@recommendation_router.get("/recommend/outfit", response_model=RecommendationResponse)
def recommend_outfit(
    count: int = Query(1, ge=1),
    season: Optional[str] = Query(None),
    formality: Optional[float] = Query(None),
    use_llm: bool = Query(True, description="LLM 사용 여부 (기본값: true, Azure OpenAI 사용)"),
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

        if not tops or not bottoms:
            return create_success_response(
                {"outfits": []},
                count=0,
                method="none",
                message="Not enough items in wardrobe (need at least one top and one bottom)"
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

        if not tops or not bottoms:
            return create_success_response(
                {"outfits": []},
                count=0,
                method="none",
                message="No items match the filters"
            )

        # Use Azure OpenAI (via LangGraph workflow) for recommendation
        if use_llm:
            try:
                recommendations = recommender.recommend_with_llm(tops, bottoms, count)
                if recommendations:
                    return create_success_response(
                        {"outfits": recommendations},
                        count=len(recommendations),
                        method="azure-openai-optimized"
                    )
            except Exception as e:
                print(f"LLM recommendation error: {e}")
                # Fall through to rule-based fallback

        # Fallback: rule-based recommendation
        recommendations = recommender._rule_based_recommendation(tops, bottoms, count)
        return create_success_response(
            {"outfits": recommendations},
            count=len(recommendations),
            method="rule-based"
        )

    except HTTPException:
        raise
    except Exception as e:
        raise handle_route_exception(e)
