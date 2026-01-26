# 옷장 API (Wardrobe)

옷 아이템 관리 및 조회 API입니다.

## Base URL

```
/api/wardrobe
```

## 인증

!!! warning "인증 필요"
    모든 옷장 API는 JWT 토큰 인증이 필요합니다.

## 엔드포인트

### 내 옷장 조회

현재 로그인한 사용자의 옷장 아이템 목록을 조회합니다.

**Endpoint**
```http
GET /wardrobe/users/me/images
```

**Query Parameters**

| 파라미터 | 타입    | 필수 | 기본값 | 설명                                  |
| -------- | ------- | ---- | ------ | ------------------------------------- |
| category | string  | ❌    | -      | 카테고리 필터 (top, bottom, outer 등) |
| skip     | integer | ❌    | 0      | 건너뛸 아이템 수 (페이지네이션)       |
| limit    | integer | ❌    | 20     | 가져올 최대 아이템 수 (1-100)         |

**Request**
```bash
curl -X GET "http://localhost:7071/api/wardrobe/users/me/images?category=top&skip=0&limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response**
```json
{
  "success": true,
  "items": [
    {
      "id": "123",
      "filename": "item_123",
      "attributes": {
        "category": {
          "main": "top",
          "sub": "t-shirt",
          "confidence": 0.95
        },
        "color": {
          "primary": "blue",
          "secondary": "white"
        },
        "pattern": "solid",
        "material": "cotton"
      },
      "image_url": "https://storage.blob.core.windows.net/..."
    }
  ],
  "count": 20,
  "total_count": 150,
  "has_more": true
}
```

---

### 아이템 상세 조회

특정 옷장 아이템의 상세 정보를 조회합니다.

**Endpoint**
```http
GET /wardrobe/items/{item_id}
```

**Path Parameters**

| 파라미터 | 타입   | 설명      |
| -------- | ------ | --------- |
| item_id  | string | 아이템 ID |

**Request**
```bash
curl -X GET "http://localhost:7071/api/wardrobe/items/123" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Response**
```json
{
  "id": "123",
  "filename": "item_123.jpg",
  "attributes": {
    "category": {
      "main": "top",
      "sub": "t-shirt",
      "confidence": 0.95
    },
    "color": {
      "primary": "blue",
      "secondary": "white",
      "hex": "#0066CC"
    },
    "pattern": "solid",
    "material": "cotton",
    "thickness": 2,
    "season": ["spring", "summer"],
    "mood_tags": ["casual", "comfortable"]
  },
  "image_url": "https://storage.blob.core.windows.net/..."
}
```

---

### 옷 이미지 업로드

새로운 옷 이미지를 업로드하고 AI 분석을 수행합니다.

!!! info "이미지 분석"
    이 엔드포인트는 [Extraction API](extraction.md)를 사용합니다.

**Endpoint**
```http
POST /extraction/upload
```

**Request (multipart/form-data)**
```bash
curl -X POST "http://localhost:7071/api/extraction/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/image.jpg"
```

**Response**
```json
{
  "success": true,
  "image_url": "https://storage.blob.core.windows.net/...",
  "item_id": "456",
  "attributes": {
    "category": {
      "main": "top",
      "sub": "hoodie",
      "confidence": 0.92
    },
    "color": {
      "primary": "black",
      "secondary": "gray"
    },
    "pattern": "solid",
    "material": "cotton blend"
  }
}
```

## 카테고리 목록

### 메인 카테고리

| 카테고리    | 설명                         |
| ----------- | ---------------------------- |
| `top`       | 상의 (티셔츠, 셔츠, 후드 등) |
| `bottom`    | 하의 (바지, 치마 등)         |
| `outer`     | 아우터 (자켓, 코트 등)       |
| `dress`     | 원피스                       |
| `shoes`     | 신발                         |
| `accessory` | 액세서리                     |

### 서브 카테고리 (예시)

**Top**
- `t-shirt` - 티셔츠
- `shirt` - 셔츠
- `hoodie` - 후드티
- `sweater` - 스웨터
- `blouse` - 블라우스

**Bottom**
- `jeans` - 청바지
- `pants` - 바지
- `skirt` - 치마
- `shorts` - 반바지

**Outer**
- `jacket` - 자켓
- `coat` - 코트
- `cardigan` - 가디건
- `parka` - 파카

## 이미지 URL

!!! tip "SAS 토큰"
    이미지 URL은 **1시간 유효한 SAS 토큰**이 포함되어 있습니다. 만료 후에는 다시 API를 호출해야 합니다.

## 페이지네이션

대량의 아이템을 효율적으로 조회하기 위해 페이지네이션을 사용합니다.

**예제: 2페이지 조회 (21-40번째 아이템)**
```bash
curl -X GET "http://localhost:7071/api/wardrobe/users/me/images?skip=20&limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 에러 응답

### 404 Not Found
```json
{
  "detail": "Item not found"
}
```

### 403 Forbidden
```json
{
  "detail": "Not authorized to view this item"
}
```

## 관련 API

- [Extraction API](extraction.md) - 이미지 분석
- [Recommendation API](recommendation.md) - 코디 추천
