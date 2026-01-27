import json
import logging
from typing import List, Dict, Any, Tuple, Optional
from uuid import UUID
from datetime import date
from sqlalchemy.orm import Session
from app.ai.workflows.recommendation_workflow import recommend_outfits
from app.core.regions import get_nearest_region
from app.core.config import Config
from app.domains.weather.service import weather_service
from app.domains.weather.utils import dfs_xy_conv
from app.domains.wardrobe.service import wardrobe_manager
from app.domains.recommendation.model import TodaysPick

logger = logging.getLogger(__name__)


class OutfitRecommender:
    def __init__(self):
        self.color_wheel = {
            "black": 0,
            "white": 0,
            "gray": 0,
            "red": 0,
            "orange": 30,
            "yellow": 60,
            "green": 120,
            "skyblue": 180,
            "blue": 210,
            "navy": 240,
            "purple": 270,
            "pink": 300,
            "beige": 45,
            "brown": 25,
            "khaki": 90,
            "cream": 50,
            "other": None,
            "unknown": None,
        }
        self.cache = {}
        self.cache_max_size = 100

    @staticmethod
    def _as_dict(value: Any) -> Dict[str, Any]:
        """None/모델/기타 타입을 안전하게 dict로 변환합니다."""
        if value is None:
            return {}
        if isinstance(value, dict):
            return value
        # Pydantic v2
        if hasattr(value, "model_dump"):
            try:
                dumped = value.model_dump()
                return dumped if isinstance(dumped, dict) else {}
            except Exception:
                return {}
        # Pydantic v1
        if hasattr(value, "dict"):
            try:
                dumped = value.dict()
                return dumped if isinstance(dumped, dict) else {}
            except Exception:
                return {}
        return {}

    @staticmethod
    def _as_list(value: Any) -> List[Any]:
        """None/단일값/튜플 등을 안전하게 list로 변환합니다."""
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, tuple):
            return list(value)
        if isinstance(value, str):
            return [value]
        return []

    def get_color_hue(self, color: str) -> Optional[float]:
        return self.color_wheel.get(color.lower(), None)

    def calculate_color_harmony(self, color1: str, color2: str) -> float:
        hue1 = self.get_color_hue(color1)
        hue2 = self.get_color_hue(color2)

        if color1.lower() in ["black", "white", "gray"] or color2.lower() in [
            "black",
            "white",
            "gray",
        ]:
            return 0.8

        if hue1 is None or hue2 is None:
            return 0.5

        if color1.lower() == color2.lower():
            return 0.9

        diff = abs(hue1 - hue2)
        if diff > 180:
            diff = 360 - diff

        if 170 <= diff <= 190:
            return 0.95
        if diff <= 60:
            return 0.85
        if 110 <= diff <= 130:
            return 0.75
        if diff <= 90:
            return 0.6
        return 0.4

    def calculate_style_match(
        self, style_tags1: List[str], style_tags2: List[str]
    ) -> float:
        if not style_tags1 or not style_tags2:
            return 0.3

        set1 = set(style_tags1)
        set2 = set(style_tags2)

        common = len(set1 & set2)
        total = len(set1 | set2)

        if total == 0:
            return 0.3

        return min(1.0, 0.3 + (common / total) * 0.7)

    def calculate_formality_match(self, formality1: float, formality2: float) -> float:
        diff = abs(formality1 - formality2)
        return max(0.0, 1.0 - diff * 2)

    def calculate_season_match(self, seasons1: List[str], seasons2: List[str]) -> float:
        if not seasons1 or not seasons2:
            return 0.5

        set1 = set(seasons1)
        set2 = set(seasons2)

        if len(set1 & set2) > 0:
            return 1.0
        return 0.3

    def calculate_outfit_score(
        self, top: Dict[str, Any], bottom: Dict[str, Any]
    ) -> Tuple[float, List[str]]:
        top_attrs = self._as_dict(top.get("attributes"))
        bottom_attrs = self._as_dict(bottom.get("attributes"))

        top_color_raw = top_attrs.get("color")
        bottom_color_raw = bottom_attrs.get("color")
        top_color = (
            top_color_raw
            if isinstance(top_color_raw, str)
            else (self._as_dict(top_color_raw).get("primary") or "unknown")
        )
        bottom_color = (
            bottom_color_raw
            if isinstance(bottom_color_raw, str)
            else (self._as_dict(bottom_color_raw).get("primary") or "unknown")
        )
        color_score = self.calculate_color_harmony(top_color, bottom_color)

        top_styles = [
            s for s in self._as_list(top_attrs.get("style_tags")) if isinstance(s, str)
        ]
        bottom_styles = [
            s
            for s in self._as_list(bottom_attrs.get("style_tags"))
            if isinstance(s, str)
        ]
        style_score = self.calculate_style_match(top_styles, bottom_styles)

        top_scores = self._as_dict(top_attrs.get("scores"))
        bottom_scores = self._as_dict(bottom_attrs.get("scores"))

        top_formality_raw = top_scores.get("formality", 0.5)
        bottom_formality_raw = bottom_scores.get("formality", 0.5)
        try:
            top_formality = (
                float(top_formality_raw) if top_formality_raw is not None else 0.5
            )
        except (TypeError, ValueError):
            top_formality = 0.5
        try:
            bottom_formality = (
                float(bottom_formality_raw) if bottom_formality_raw is not None else 0.5
            )
        except (TypeError, ValueError):
            bottom_formality = 0.5
        formality_score = self.calculate_formality_match(
            top_formality, bottom_formality
        )

        top_seasons = [
            s for s in self._as_list(top_scores.get("season")) if isinstance(s, str)
        ]
        bottom_seasons = [
            s for s in self._as_list(bottom_scores.get("season")) if isinstance(s, str)
        ]
        season_score = self.calculate_season_match(top_seasons, bottom_seasons)

        total_score = (
            color_score * 0.4
            + style_score * 0.3
            + formality_score * 0.2
            + season_score * 0.1
        )

        reasons = []
        if color_score >= 0.8:
            reasons.append("색상 조화")
        if style_score >= 0.6:
            reasons.append("스타일 일치")
        if formality_score >= 0.7:
            reasons.append("정장스러움 조화")
        if season_score >= 0.8:
            reasons.append("계절 적합")

        if not reasons:
            reasons.append("균형잡힌 조합")

        return total_score, reasons

    def _get_cache_key(self, tops: List[Dict], bottoms: List[Dict], count: int) -> str:
        top_ids = sorted([t.get("id") for t in tops])
        bottom_ids = sorted([b.get("id") for b in bottoms])
        return f"{hash(tuple(top_ids))}_{hash(tuple(bottom_ids))}_{count}"

    async def recommend_with_llm(
        self, tops: List[Dict], bottoms: List[Dict], count: int = 1
    ) -> List[Dict]:
        """
        LLM을 사용한 코디 추천 (Azure OpenAI + LangGraph)

        Args:
            tops: 상의 아이템 리스트
            bottoms: 하의 아이템 리스트
            count: 추천 개수

        Returns:
            추천 결과 리스트
        """
        # 캐시 확인
        cache_key = self._get_cache_key(tops, bottoms, count)
        if cache_key in self.cache:
            cached_result = self.cache[cache_key]
            result = []
            for cached in cached_result:
                top_item = next(
                    (t for t in tops if t.get("id") == cached["top_id"]), None
                )
                bottom_item = next(
                    (b for b in bottoms if b.get("id") == cached["bottom_id"]), None
                )
                if top_item and bottom_item:
                    result.append(
                        {
                            "top": top_item,
                            "bottom": bottom_item,
                            "score": cached["score"],
                            "reasoning": cached["reasoning"],
                            "style_description": cached["style_description"],
                            "reasons": (
                                [cached["reasoning"]] if cached.get("reasoning") else []
                            ),
                        }
                    )
            if result:
                return result[:count]

        # LangGraph 워크플로우 호출
        try:
            recommendations = await recommend_outfits(
                tops=tops, bottoms=bottoms, count=count, use_llm=True
            )

            # 캐시 저장
            if recommendations and len(self.cache) < self.cache_max_size:
                cache_data = []
                for rec in recommendations:
                    cache_data.append(
                        {
                            "top_id": rec.get("top", {}).get("id"),
                            "bottom_id": rec.get("bottom", {}).get("id"),
                            "score": rec.get("score", 0.5),
                            "reasoning": rec.get("reasoning", ""),
                            "style_description": rec.get("style_description", ""),
                        }
                    )
                if cache_data:
                    self.cache[cache_key] = cache_data

            return recommendations
        except Exception as e:
            print(f"Azure OpenAI recommendation error: {e}")
            # 폴백: 규칙 기반 추천
            candidates = []
            for top in tops:
                for bottom in bottoms:
                    score, _ = self.calculate_outfit_score(top, bottom)
                    candidates.append({"top": top, "bottom": bottom, "score": score})
            candidates.sort(key=lambda x: x["score"], reverse=True)
            return self._rule_based_recommendation(tops, bottoms, count)

    def _rule_based_recommendation(
        self, tops: List[Dict], bottoms: List[Dict], count: int
    ) -> List[Dict]:
        """
        규칙 기반 추천 (LLM 실패 시 폴백)

        Args:
            tops: 상의 아이템 리스트
            bottoms: 하의 아이템 리스트
            count: 추천 개수

        Returns:
            추천 결과 리스트
        """
        candidates = []
        for top in tops:
            for bottom in bottoms:
                score, reasons = self.calculate_outfit_score(top, bottom)
                top_cat = self._as_dict(
                    self._as_dict(top.get("attributes")).get("category")
                )
                bottom_cat = self._as_dict(
                    self._as_dict(bottom.get("attributes")).get("category")
                )
                candidates.append(
                    {
                        "top": top,
                        "bottom": bottom,
                        "score": round(score, 3),
                        "reasons": reasons,
                        "reasoning": ", ".join(reasons),
                        "style_description": (
                            f"{(top_cat.get('sub') or top_cat.get('main') or 'Top')} & "
                            f"{(bottom_cat.get('sub') or bottom_cat.get('main') or 'Bottom')}"
                        ),
                    }
                )

        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:count]

    async def recommend_with_gemini(
        self,
        tops: List[Dict],
        bottoms: List[Dict],
        count: int = 1,
        top_candidates: int = 5,
    ) -> List[Dict]:
        """
        하위 호환성을 위한 래퍼 메서드 (deprecated)

        내부적으로 recommend_with_llm을 호출합니다.
        top_candidates 파라미터는 무시됩니다.

        DEPRECATED: recommend_with_llm을 사용하세요.
        """
        return await self.recommend_with_llm(tops, bottoms, count)

    @staticmethod
    def _normalize_korea_lat_lon(lat: float, lon: float) -> Tuple[float, float, bool]:
        """
        위경도 입력이 뒤바뀌는 케이스(예: lat=126.x, lon=37.x)를 자동 보정합니다.
        - 정상 범위(대한민국 대략 범위): lat 33~39.5, lon 124~132
        """
        in_korea = 33.0 <= lat <= 39.5 and 124.0 <= lon <= 132.0
        looks_swapped = 33.0 <= lon <= 39.5 and 124.0 <= lat <= 132.0

        if in_korea:
            return lat, lon, False
        if looks_swapped:
            return lon, lat, True
        return lat, lon, False

    async def get_todays_pick(
        self, db: Session, user_id: UUID, lat: float, lon: float
    ) -> Dict[str, Any]:
        """
        오늘의 추천 코디 (Today's Pick) - 단순화된 버전
        새로운 todays_pick_service를 사용하여 LLM + 이미지 생성 필수
        """
        from fastapi import HTTPException
        from app.llm.todays_pick_service import (
            recommend_todays_pick_v2,
        )
        from app.domains.weather.service import weather_service
        from app.core.regions import get_nearest_region
        from app.domains.weather.utils import dfs_xy_conv
        from datetime import date

        # 1. 오늘 이미 생성된 추천이 있는지 확인
        today = date.today()
        existing_pick = (
            db.query(TodaysPick)
            .filter(TodaysPick.user_id == user_id)
            .order_by(TodaysPick.date.desc(), TodaysPick.created_at.desc())
            .first()
        )

        # 1. 오늘 이미 생성된 추천이 있는지 확인
        if existing_pick and existing_pick.date == today:
            logger.info(
                f"Found existing Today's Pick for user {user_id} for today ({today})"
            )
            ws = existing_pick.weather_snapshot or {}
            msg = "오늘의 추천을 불러왔습니다. (캐시됨)"

            # Ensure SAS URL for viewing
            from app.domains.wardrobe.service import wardrobe_manager

            final_image_url = wardrobe_manager.get_sas_url(existing_pick.image_url)

            return {
                "success": True,
                "pick_id": str(existing_pick.id),
                "top_id": str(existing_pick.top_item_id),
                "bottom_id": str(existing_pick.bottom_item_id),
                "image_url": final_image_url,
                "reasoning": existing_pick.reasoning,
                "score": existing_pick.score,
                "weather": ws,
                "weather_summary": ws.get("summary", ""),
                "temp_min": float(ws.get("temp_min", 0.0)),
                "temp_max": float(ws.get("temp_max", 0.0)),
                "message": msg,
            }

        # 2. 날씨 정보 가져오기 (중앙화된 함수 사용)
        weather_info = await weather_service.get_weather_info(db, lat, lon)

        if not weather_info or (
            weather_info.get("temp_min") == 0
            and weather_info.get("temp_max") == 0
            and "기온" not in weather_info.get("summary", "")
        ):
            raise HTTPException(
                status_code=500, detail="날씨 정보를 가져올 수 없습니다."
            )

        # 3. 새로운 서비스로 Today's Pick 생성 (LLM + 이미지 생성 필수)
        logger.info(f"Creating new Today's Pick for user {user_id}")

        try:
            result = recommend_todays_pick_v2(user_id, weather_info, db)

            # Ensure SAS URL for viewing
            from app.domains.wardrobe.service import wardrobe_manager

            if result.get("image_url"):
                result["image_url"] = wardrobe_manager.get_sas_url(result["image_url"])

            result["message"] = "새로운 오늘의 추천을 생성했습니다."
            return result

        except ValueError as e:
            # 옷장 부족 등 사용자 문제
            logger.warning(f"Cannot create Today's Pick: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))
        except RuntimeError as e:
            # 이미지 생성 실패 등 시스템 문제
            logger.error(f"System error creating Today's Pick: {str(e)}")
            raise HTTPException(status_code=500, detail=f"이미지 생성 실패: {str(e)}")
        except Exception as e:
            # 기타 에러
            logger.error(
                f"Unexpected error creating Today's Pick: {str(e)}", exc_info=True
            )
            raise HTTPException(status_code=500, detail=f"추천 생성 실패: {str(e)}")

    def save_todays_pick(
        self,
        db: Session,
        user_id: UUID,
        recommendation: Dict[str, Any],
        weather_info: Dict[str, Any],
    ) -> TodaysPick:
        """추천된 오늘의 코디를 DB에 저장하고 기존 활성 픽을 비활성화"""
        try:
            # 1. 기존 활성 픽 비활성화
            db.query(TodaysPick).filter(
                TodaysPick.user_id == user_id, TodaysPick.is_active == True
            ).update({"is_active": False})

            # 2. 새 픽 저장
            from datetime import date

            top_id = recommendation.get("top", {}).get("id")
            bottom_id = recommendation.get("bottom", {}).get("id")

            new_pick = TodaysPick(
                user_id=user_id,
                date=date.today(),
                top_id=int(top_id) if top_id else None,
                bottom_id=int(bottom_id) if bottom_id else None,
                image_url=recommendation.get("generated_image_url"),
                reasoning=recommendation.get("reasoning"),
                weather_snapshot=weather_info,
                is_active=True,
            )

            db.add(new_pick)
            db.commit()
            db.refresh(new_pick)
            return new_pick

        except Exception as e:
            db.rollback()
            logger.error(f"Error saving Today's Pick: {e}")
            raise e


recommender = OutfitRecommender()
