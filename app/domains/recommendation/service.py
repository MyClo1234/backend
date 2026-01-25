import json
from typing import List, Dict, Any, Tuple, Optional
from app.ai.workflows.recommendation_workflow import recommend_outfits

class OutfitRecommender:
    def __init__(self):
        self.color_wheel = {
            "black": 0, "white": 0, "gray": 0,
            "red": 0, "orange": 30, "yellow": 60,
            "green": 120, "skyblue": 180, "blue": 210,
            "navy": 240, "purple": 270, "pink": 300,
            "beige": 45, "brown": 25, "khaki": 90,
            "cream": 50, "other": None, "unknown": None
        }
        self.cache = {}
        self.cache_max_size = 100

    def get_color_hue(self, color: str) -> Optional[float]:
        return self.color_wheel.get(color.lower(), None)

    def calculate_color_harmony(self, color1: str, color2: str) -> float:
        hue1 = self.get_color_hue(color1)
        hue2 = self.get_color_hue(color2)
        
        if color1.lower() in ["black", "white", "gray"] or color2.lower() in ["black", "white", "gray"]:
            return 0.8
        
        if hue1 is None or hue2 is None:
            return 0.5
        
        if color1.lower() == color2.lower():
            return 0.9
        
        diff = abs(hue1 - hue2)
        if diff > 180:
            diff = 360 - diff
        
        if 170 <= diff <= 190: return 0.95
        if diff <= 60: return 0.85
        if 110 <= diff <= 130: return 0.75
        if diff <= 90: return 0.6
        return 0.4

    def calculate_style_match(self, style_tags1: List[str], style_tags2: List[str]) -> float:
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

    def calculate_outfit_score(self, top: Dict[str, Any], bottom: Dict[str, Any]) -> Tuple[float, List[str]]:
        top_attrs = top.get("attributes", {})
        bottom_attrs = bottom.get("attributes", {})
        
        top_color = top_attrs.get("color", {}).get("primary", "unknown")
        bottom_color = bottom_attrs.get("color", {}).get("primary", "unknown")
        color_score = self.calculate_color_harmony(top_color, bottom_color)
        
        top_styles = top_attrs.get("style_tags", [])
        bottom_styles = bottom_attrs.get("style_tags", [])
        style_score = self.calculate_style_match(top_styles, bottom_styles)
        
        top_formality = top_attrs.get("scores", {}).get("formality", 0.5)
        bottom_formality = bottom_attrs.get("scores", {}).get("formality", 0.5)
        formality_score = self.calculate_formality_match(top_formality, bottom_formality)
        
        top_seasons = top_attrs.get("scores", {}).get("season", [])
        bottom_seasons = bottom_attrs.get("scores", {}).get("season", [])
        season_score = self.calculate_season_match(top_seasons, bottom_seasons)
        
        total_score = (
            color_score * 0.4 +
            style_score * 0.3 +
            formality_score * 0.2 +
            season_score * 0.1
        )
        
        reasons = []
        if color_score >= 0.8: reasons.append("색상 조화")
        if style_score >= 0.6: reasons.append("스타일 일치")
        if formality_score >= 0.7: reasons.append("정장스러움 조화")
        if season_score >= 0.8: reasons.append("계절 적합")
        
        if not reasons:
            reasons.append("균형잡힌 조합")
        
        return total_score, reasons

    def _get_cache_key(self, tops: List[Dict], bottoms: List[Dict], count: int) -> str:
        top_ids = sorted([t.get("id") for t in tops])
        bottom_ids = sorted([b.get("id") for b in bottoms])
        return f"{hash(tuple(top_ids))}_{hash(tuple(bottom_ids))}_{count}"

    def recommend_with_llm(self, tops: List[Dict], bottoms: List[Dict], count: int = 1) -> List[Dict]:
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
                top_item = next((t for t in tops if t.get("id") == cached["top_id"]), None)
                bottom_item = next((b for b in bottoms if b.get("id") == cached["bottom_id"]), None)
                if top_item and bottom_item:
                    result.append({
                        "top": top_item,
                        "bottom": bottom_item,
                        "score": cached["score"],
                        "reasoning": cached["reasoning"],
                        "style_description": cached["style_description"],
                        "reasons": [cached["reasoning"]] if cached.get("reasoning") else []
                    })
            if result:
                return result[:count]
        
        # LangGraph 워크플로우 호출
        try:
            recommendations = recommend_outfits(
                tops=tops,
                bottoms=bottoms,
                count=count,
                use_llm=True
            )
            
            # 캐시 저장
            if recommendations and len(self.cache) < self.cache_max_size:
                cache_data = []
                for rec in recommendations:
                    cache_data.append({
                        "top_id": rec.get("top", {}).get("id"),
                        "bottom_id": rec.get("bottom", {}).get("id"),
                        "score": rec.get("score", 0.5),
                        "reasoning": rec.get("reasoning", ""),
                        "style_description": rec.get("style_description", "")
                    })
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

    def _rule_based_recommendation(self, tops: List[Dict], bottoms: List[Dict], count: int) -> List[Dict]:
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
                candidates.append({
                    "top": top,
                    "bottom": bottom,
                    "score": round(score, 3),
                    "reasons": reasons,
                    "reasoning": ", ".join(reasons),
                    "style_description": (
                        f"{top.get('attributes', {}).get('category', {}).get('sub', 'Top')} & "
                        f"{bottom.get('attributes', {}).get('category', {}).get('sub', 'Bottom')}"
                    ),
                })
        
        candidates.sort(key=lambda x: x["score"], reverse=True)
        return candidates[:count]
    
    def recommend_with_gemini(self, tops: List[Dict], bottoms: List[Dict], count: int = 1, top_candidates: int = 5) -> List[Dict]:
        """
        하위 호환성을 위한 래퍼 메서드 (deprecated)
        
        내부적으로 recommend_with_llm을 호출합니다.
        top_candidates 파라미터는 무시됩니다.
        
        DEPRECATED: recommend_with_llm을 사용하세요.
        """
        return self.recommend_with_llm(tops, bottoms, count)

recommender = OutfitRecommender()
