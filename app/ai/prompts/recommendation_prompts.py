"""
코디 추천 프롬프트 템플릿
"""

import json
from typing import List, Dict, Any


def build_recommendation_prompt(
    tops_summary: List[Dict[str, Any]],
    bottoms_summary: List[Dict[str, Any]],
    count: int = 1,
) -> str:
    """기본 상/하의 조합 추천 (단순 버전)"""
    return f"""Recommend {count} best outfit(s) from these pre-filtered combinations.

Tops: {json.dumps(tops_summary, ensure_ascii=False)}
Bottoms: {json.dumps(bottoms_summary, ensure_ascii=False)}

Consider color harmony, style match, formality balance.

Return JSON array with {count} object(s):
{{
  "top_id": "string",
  "bottom_id": "string",
  "score": 0.0-1.0,
  "reasoning": "한국어 100자 이내",
  "style_description": "한국어 50자 이내"
}}

JSON only, no markdown, no code blocks."""


def build_tpo_recommendation_prompt(
    user_request: str,
    weather_info: Dict[str, Any],
    tops_summary: List[Dict[str, Any]],  # 원본 인자 유지
    bottoms_summary: List[Dict[str, Any]],  # 원본 인자 유지
    outer_summary: List[Dict[str, Any]] = None,  # 아우터 추가 (선택사항)
    count: int = 1,
) -> str:
    """
    원본의 인자 구조를 유지하면서 상세 속성(소재, 레이어링 등) 로직을 결합한 버전
    """

    # 데이터를 AI가 읽기 좋게 카테고리별로 묶어줌
    wardrobe_context = {
        "top": tops_summary,
        "bottom": bottoms_summary,
        "outer": outer_summary if outer_summary else [],
    }

    weather_text = ""
    if weather_info:
        weather_text = f"""
Current Weather:
- Temp: {weather_info.get('temperature', 'N/A')}°C
- Condition: {weather_info.get('condition', 'N/A')}
- Precipitation: {weather_info.get('precipitation', 'N/A')}
"""

    return f"""Recommend {count} outfit(s) based on the context.

[Context]
User Request: {user_request}
{weather_text}

[Available Items]
{json.dumps(wardrobe_context, ensure_ascii=False)}

[Styling Rules]
1. Weather: Combine 'scores.warmth' and 'thickness' to match the Temp. 
2. Safety: If precipitation is not "none", avoid "suede", "silk", "leather".
3. Layering: Follow 'meta.layering_rank' (1:Inner, 2:Mid, 3:Outer).
4. Category: Must include (1 Top + 1 Bottom). Add 1 Outer if Temp < 15°C.

Return ONLY a JSON array of {count} objects:
{{
  "outfit_id": "outfit_n",
  "combination": {{
    "outer_id": "string|null",
    "top_id": "string",
    "bottom_id": "string"
  }},
  "score": 0.0-1.0,
  "reasoning": "한국어 100자 이내 (날씨/TPO/소재 고려)",
  "style_description": "한국어 50자 이내"
}}

JSON only, no markdown."""
