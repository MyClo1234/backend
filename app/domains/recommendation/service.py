import json
from typing import List, Dict, Any, Tuple, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.ai.workflows.recommendation_workflow import recommend_outfits
from app.core.regions import get_nearest_region
from app.domains.weather.service import weather_service
from app.domains.weather.utils import dfs_xy_conv
from app.domains.wardrobe.service import wardrobe_manager
from app.domains.recommendation.model import TodaysPick


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

    def recommend_with_llm(
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
            recommendations = recommend_outfits(
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

    def recommend_with_gemini(
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
        return self.recommend_with_llm(tops, bottoms, count)

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

    def get_todays_pick(
        self, db: Session, user_id: UUID, lat: float, lon: float
    ) -> Dict[str, Any]:
        """
        오늘의 추천 코디 (Today's Pick)
        1. 위치 기반 날씨 조회
        2. 날씨에 맞는 옷장 아이템 필터링
        3. 추천 알고리즘 수행
        """
        # 1. 위치 -> 격자 변환 및 날씨 조회
        lat_norm, lon_norm, swapped = self._normalize_korea_lat_lon(lat, lon)
        if swapped:
            print("Warning: lat/lon appeared swapped; auto-corrected for Korea grid.")

        # 우선 가장 가까운 대표 지역(캐싱/폴백용)
        region_name, region_data = get_nearest_region(lat_norm, lon_norm)

        # 실제 격자 변환 시도 (정확 위치)
        grid = dfs_xy_conv("toGRID", lat_norm, lon_norm)
        nx, ny = grid.get("x"), grid.get("y")

        # 변환 결과가 비정상일 경우 대표 지역 격자로 폴백
        if not isinstance(nx, (int, float)) or not isinstance(ny, (int, float)):
            nx, ny = region_data["nx"], region_data["ny"]
        elif nx < 0 or ny < 0 or nx > 300 or ny > 300:
            nx, ny = region_data["nx"], region_data["ny"]
        else:
            nx, ny = int(nx), int(ny)

        daily_weather, msg = weather_service.get_daily_weather_summary(
            db, nx, ny, region_name
        )

        if not daily_weather:
            # 날씨 조회 실패 시 기본값 (서울 기준 등) 혹은 에러 처리
            # 여기서는 편의상 계절 추론을 위해 임의값 설정하거나 에러 반환
            raise Exception(f"Failed to fetch weather: {msg}")

        min_temp = daily_weather.min_temp
        max_temp = daily_weather.max_temp

        # 2. 계절 및 날씨 조건 판단
        target_seasons = []
        weather_summary = (
            f"{daily_weather.region or '현위치'} 기온 {min_temp}°C ~ {max_temp}°C"
        )

        if max_temp >= 24:
            target_seasons = ["SUMMER"]
            weather_summary += " (여름 날씨)"
        elif max_temp <= 12:
            target_seasons = ["WINTER"]
            weather_summary += " (겨울 날씨)"
        else:
            target_seasons = ["SPRING", "FALL"]
            weather_summary += " (선선한 날씨)"

        # 3. 사용자 옷장 조회 (DB)
        # 상/하의 각각 충분히 가져옴
        tops_data = wardrobe_manager.get_user_wardrobe_items(
            db, user_id, category="top", limit=100
        )
        bottoms_data = wardrobe_manager.get_user_wardrobe_items(
            db, user_id, category="bottom", limit=100
        )

        raw_tops = [item.dict() for item in tops_data.get("items", [])]
        raw_bottoms = [item.dict() for item in bottoms_data.get("items", [])]

        # 4. 날씨/계절 기반 필터링
        # 아이템의 'season' 속성이 있으면 그것을 우선, 없으면 통과
        filtered_tops = []
        for t in raw_tops:
            item_seasons = t.get("attributes", {}).get("season", [])
            # 계절 태그가 없으면 모든 계절 허용으로 간주 or 스킵? -> 허용으로 간주
            if not item_seasons:
                filtered_tops.append(t)
                continue

            # 교집합이 있으면 추가
            if any(
                s.upper() in [ts.upper() for ts in target_seasons] for s in item_seasons
            ):
                filtered_tops.append(t)

        filtered_bottoms = []
        for b in raw_bottoms:
            item_seasons = b.get("attributes", {}).get("season", [])
            if not item_seasons:
                filtered_bottoms.append(b)
                continue
            if any(
                s.upper() in [ts.upper() for ts in target_seasons] for s in item_seasons
            ):
                filtered_bottoms.append(b)

        # 필터링 결과가 너무 적으면 필터 해제 (폴백)
        if not filtered_tops:
            filtered_tops = raw_tops
        if not filtered_bottoms:
            filtered_bottoms = raw_bottoms

        if not filtered_tops or not filtered_bottoms:
            return {
                "success": False,
                "weather_summary": weather_summary,
                "temp_min": min_temp,
                "temp_max": max_temp,
                "outfit": None,
                "message": "옷장에 상의 또는 하의가 충분하지 않습니다.",
            }

        # 5. 추천 실행 (LLM 사용)
        # recommend_with_llm returns List[Dict]
        recommendations = self.recommend_with_llm(
            filtered_tops, filtered_bottoms, count=1
        )

        if not recommendations:
            return {
                "success": False,
                "weather_summary": weather_summary,
                "temp_min": min_temp,
                "temp_max": max_temp,
                "outfit": None,
                "message": "적절한 코디를 찾지 못했습니다.",
            }

        best_pick = recommendations[0]

        return {
            "success": True,
            "weather_summary": weather_summary,
            "temp_min": min_temp,
            "temp_max": max_temp,
            "outfit": best_pick,
            "message": "추천이 완료되었습니다.",
        }

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
