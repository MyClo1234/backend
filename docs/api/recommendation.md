# 추천 API (Recommendation)

AI 기반 코디 추천 API입니다.

## Base URL

```
/api/recommendations
```

## 인증

!!! info "인증 선택"
    일부 엔드포인트는 인증 없이 사용 가능하지만, 개인화된 추천을 위해서는 로그인이 필요합니다.

## 엔드포인트

### 코디 추천

날씨와 상황을 고려한 코디를 추천합니다.

**Endpoint**
```http
GET /recommendations
```

**Query Parameters**

| 파라미터    | 타입   | 필수 | 설명                                |
| ----------- | ------ | ---- | ----------------------------------- |
| weather     | string | ❌    | 날씨 조건 (sunny, rainy, cloudy 등) |
| temperature | number | ❌    | 기온 (°C)                           |
| occasion    | string | ❌    | 상황 (casual, formal, sport 등)     |
| season      | string | ❌    | 계절 (spring, summer, fall, winter) |

**Request**
```bash
curl -X GET "http://localhost:7071/api/recommendations?weather=sunny&temperature=25&occasion=casual" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response**
```json
{
  "success": true,
  "recommendations": [
    {
      "outfit_id": "outfit_1",
      "score": 0.95,
      "items": [
        {
          "id": "123",
          "category": "top",
          "image_url": "https://...",
          "attributes": {
            "category": {
              "main": "top",
              "sub": "t-shirt"
            },
            "color": {
              "primary": "white"
            }
          }
        },
        {
          "id": "456",
          "category": "bottom",
          "image_url": "https://...",
          "attributes": {
            "category": {
              "main": "bottom",
              "sub": "jeans"
            },
            "color": {
              "primary": "blue"
            }
          }
        }
      ],
      "reason": "가벼운 티셔츠와 청바지는 25도의 화창한 날씨에 적합합니다.",
      "tags": ["casual", "comfortable", "summer"]
    }
  ],
  "count": 5,
  "weather_info": {
    "temperature": 25,
    "condition": "sunny",
    "humidity": 60
  }
}
```

---

### 코디 점수 평가

특정 아이템 조합의 적합도를 평가합니다.

**Endpoint**
```http
POST /recommendations/score
```

**Request Body**
```json
{
  "item_ids": ["123", "456", "789"],
  "weather": {
    "temperature": 20,
    "condition": "cloudy"
  },
  "occasion": "casual"
}
```

**Response**
```json
{
  "success": true,
  "score": 0.87,
  "feedback": {
    "overall": "좋은 조합입니다!",
    "color_harmony": 0.9,
    "style_consistency": 0.85,
    "weather_suitability": 0.88,
    "suggestions": [
      "아우터를 추가하면 더 완성도 높은 코디가 될 것 같습니다."
    ]
  },
  "alternative_items": [
    {
      "id": "999",
      "category": "outer",
      "reason": "날씨가 쌀쌀할 수 있어 가벼운 자켓을 추천합니다.",
      "image_url": "https://..."
    }
  ]
}
```

## 추천 알고리즘

### 고려 요소

1. **날씨 적합성**
   - 기온에 맞는 옷감 두께
   - 날씨 조건 (비, 눈, 바람 등)

2. **색상 조화**
   - 보색, 유사색 조합
   - 계절감 있는 색상

3. **스타일 일관성**
   - 캐주얼, 포멀, 스포티 등 스타일 통일
   - 무드 태그 매칭

4. **계절성**
   - 계절에 맞는 소재
   - 시즌 트렌드

### 점수 체계

| 점수      | 평가        |
| --------- | ----------- |
| 0.9 - 1.0 | 완벽한 조합 |
| 0.8 - 0.9 | 매우 좋음   |
| 0.7 - 0.8 | 좋음        |
| 0.6 - 0.7 | 괜찮음      |
| 0.0 - 0.6 | 개선 필요   |

## 상황별 추천

### Casual (캐주얼)
- 편안하고 자연스러운 스타일
- 티셔츠, 청바지, 스니커즈 등

### Formal (포멀)
- 격식 있는 자리에 적합
- 셔츠, 슬랙스, 구두 등

### Sport (스포츠)
- 활동적인 상황에 적합
- 트레이닝복, 운동화 등

### Date (데이트)
- 세련되고 깔끔한 스타일
- 상황에 맞는 적절한 복장

## AI 모델

!!! info "Azure OpenAI"
    추천 시스템은 **Azure OpenAI GPT-4**를 사용하여 개인화된 추천을 제공합니다.

## 예제 시나리오

### 시나리오 1: 여름 캐주얼

**요청**
```bash
curl -X GET "http://localhost:7071/api/recommendations?temperature=28&weather=sunny&occasion=casual&season=summer" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**추천 결과**
- 흰색 티셔츠
- 청반바지
- 샌들
- 선글라스

### 시나리오 2: 겨울 출근

**요청**
```bash
curl -X GET "http://localhost:7071/api/recommendations?temperature=5&weather=cloudy&occasion=formal&season=winter" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**추천 결과**
- 니트 스웨터
- 슬랙스
- 코트
- 구두

## 에러 응답

### 400 Bad Request
```json
{
  "detail": "Invalid temperature value"
}
```

## 관련 API

- [Wardrobe API](wardrobe.md) - 옷장 아이템 조회
- [Weather API](weather-api.md) - 날씨 정보
