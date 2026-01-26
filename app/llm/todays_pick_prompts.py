"""
LLM prompts for Today's Pick recommendation workflow.
"""

RECOMMENDATION_PROMPT = """당신은 전문 패션 스타일리스트입니다.

## 현재 날씨 정보
{weather_summary}
온도 범위: {temp_min}°C ~ {temp_max}°C

## 사용 가능한 상의
{tops_list}

## 사용 가능한 하의
{bottoms_list}

## 임무
위 옷장 아이템들 중에서 오늘 날씨에 가장 적합한 상의와 하의 조합을 **하나만** 선택하세요.

선택 기준:
1. 날씨와 온도에 적합한 소재와 두께
2. 색상 조화
3. 스타일 일관성
4. 전반적인 패션 감각

반드시 다음 JSON 형식으로 응답하세요:
```json
{{
  "top_id": "선택한 상의 ID",
  "bottom_id": "선택한 하의 ID",
  "reasoning": "이 조합을 선택한 이유를 한국어로 2-3문장으로 설명",
  "score": 0.0에서 1.0 사이의 자신감 점수
}}
```

JSON 외의 다른 텍스트는 출력하지 마세요.
"""


def format_item_list(items: list) -> str:
    """Format a list of wardrobe items for the LLM prompt."""
    result = []
    for idx, item in enumerate(items, 1):
        attrs = item.get("attributes", {})
        category = attrs.get("category", {})
        color = attrs.get("color", {})
        material = attrs.get("material", {})

        item_str = f"{idx}. ID: {item.get('id')}"
        if category:
            item_str += f" | 카테고리: {category.get('sub') or category.get('main')}"
        if color:
            item_str += f" | 색상: {color.get('primary')}"
        if material:
            item_str += f" | 소재: {material.get('guess')}"

        result.append(item_str)

    return "\n".join(result)
