# 프로젝트 규칙 (Project Rules)

## 📋 목차
1. [프로젝트 개요](#프로젝트-개요)
2. [디렉토리 구조](#디렉토리-구조)
3. [코딩 스타일](#코딩-스타일)
4. [네이밍 컨벤션](#네이밍-컨벤션)
5. [파일 구조 규칙](#파일-구조-규칙)
6. [API 설계 규칙](#api-설계-규칙)
7. [에러 처리](#에러-처리)
8. [의존성 관리](#의존성-관리)
9. [환경 변수 관리](#환경-변수-관리)
10. [코드 리뷰 가이드라인](#코드-리뷰-가이드라인)

---

## 프로젝트 개요

- **프로젝트명**: AI Stylist Agent Backend
- **프레임워크**: FastAPI
- **Python 버전**: >= 3.12 (권장: 3.12.10)
- **주요 기능**: 옷 이미지 특징 추출 및 코디 추천

---

## 디렉토리 구조

```
backend/
├── app/
│   ├── ai/               # AI 관련 코드 통합
│   │   ├── clients/      # LLM 클라이언트
│   │   │   └── azure_openai_client.py
│   │   ├── workflows/    # LangGraph 워크플로우
│   │   │   ├── extraction_workflow.py
│   │   │   └── recommendation_workflow.py
│   │   ├── nodes/        # LangGraph 노드
│   │   │   ├── extraction_nodes.py
│   │   │   └── recommendation_nodes.py
│   │   ├── prompts/      # 프롬프트 템플릿
│   │   │   ├── extraction_prompts.py
│   │   │   └── recommendation_prompts.py
│   │   └── schemas/      # AI 관련 스키마
│   │       └── workflow_state.py
│   ├── core/             # 핵심 설정 및 상수
│   │   ├── config.py     # 환경 설정
│   │   └── constants.py  # 상수 정의 (레거시)
│   ├── models/           # 데이터 모델 (Pydantic 스키마)
│   │   └── schemas.py    # API 요청/응답 스키마
│   ├── routers/          # API 라우터
│   │   ├── health_routes.py
│   │   ├── extraction_routes.py
│   │   ├── wardrobe_routes.py
│   │   └── recommendation_routes.py
│   ├── services/         # 비즈니스 로직
│   │   ├── extractor.py  # 속성 추출 서비스 (LangGraph 래퍼)
│   │   ├── recommender.py # 코디 추천 서비스 (LangGraph 래퍼)
│   │   └── wardrobe_manager.py
│   ├── utils/            # 유틸리티 함수
│   │   ├── helpers.py
│   │   ├── json_parser.py
│   │   └── validators.py
│   └── main.py           # 애플리케이션 진입점
├── docs/                 # 프로젝트 문서
│   ├── index.md
│   ├── development/
│   ├── architecture/
│   └── api/
├── extracted_attributes/  # 추출된 이미지 저장 디렉토리
├── .env                  # 환경 변수 (gitignore)
├── .env.example          # 환경 변수 예제
├── .gitignore
├── pyproject.toml
├── requirements.txt
└── README.md
```

### 디렉토리 역할

- **`app/core/`**: 애플리케이션 전역 설정 및 상수
- **`app/models/`**: Pydantic 기반 데이터 모델 및 스키마
- **`app/routers/`**: FastAPI 라우터 정의 (엔드포인트)
- **`app/services/`**: 비즈니스 로직 및 외부 API 통신
- **`app/utils/`**: 재사용 가능한 유틸리티 함수

---

## 코딩 스타일

### Python 스타일 가이드
- **PEP 8** 준수
- **타입 힌팅** 필수 사용
- **Docstring** 작성 권장 (Google 스타일)

### 예시

```python
from typing import List, Optional, Dict
from pydantic import BaseModel

def process_image(image_bytes: bytes, options: Optional[Dict[str, any]] = None) -> Dict[str, any]:
    """
    이미지를 처리하여 속성을 추출합니다.
    
    Args:
        image_bytes: 이미지 바이트 데이터
        options: 선택적 처리 옵션
        
    Returns:
        추출된 속성 딕셔너리
    """
    # 구현
    pass
```

### 코드 포맷팅
- 들여쓰기: **4 spaces** (탭 사용 금지)
- 최대 줄 길이: **120자**
- 문자열 따옴표: **작은따옴표(')** 또는 **큰따옴표(")** 일관성 유지

---

## 네이밍 컨벤션

### 변수 및 함수
- **snake_case** 사용
- 의미 있는 이름 사용
- 약어 사용 지양

```python
# ✅ 좋은 예
def extract_clothing_attributes(image_data: bytes) -> dict:
    pass

# ❌ 나쁜 예
def ext_attr(img: bytes) -> dict:
    pass
```

### 클래스
- **PascalCase** 사용
- 명사 사용

```python
# ✅ 좋은 예
class AttributeExtractor:
    pass

class ExtractionResponse(BaseModel):
    pass
```

### 상수
- **UPPER_SNAKE_CASE** 사용
- `app/core/constants.py`에 정의

```python
# ✅ 좋은 예
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png'}
```

### 모듈/파일명
- **snake_case** 사용
- 짧고 명확한 이름

```python
# ✅ 좋은 예
extraction_routes.py
wardrobe_manager.py

# ❌ 나쁜 예
extractionRoutes.py
wardrobe-manager.py
```

---

## 파일 구조 규칙

### 라우터 파일 (`app/routers/`)
- 각 도메인별로 분리된 라우터 파일
- `APIRouter` 인스턴스 생성 및 엔드포인트 정의
- 파일명: `{domain}_routes.py`

```python
from fastapi import APIRouter
from app.models.schemas import SomeResponse

router = APIRouter()

@router.post("/endpoint", response_model=SomeResponse)
async def endpoint_handler():
    pass
```

### 서비스 파일 (`app/services/`)
- 비즈니스 로직 구현
- 싱글톤 패턴 사용 (인스턴스 생성 후 export)
- 파일명: `{service_name}.py`

```python
class SomeService:
    def method(self, param: str) -> dict:
        pass

service = SomeService()  # 싱글톤 인스턴스
```

### 모델 파일 (`app/models/`)
- Pydantic `BaseModel` 상속
- 모든 API 요청/응답 스키마 정의
- 중첩 모델은 상단에 정의

```python
from pydantic import BaseModel

class NestedModel(BaseModel):
    field: str

class ResponseModel(BaseModel):
    nested: NestedModel
```

---

## API 설계 규칙

### 엔드포인트 네이밍
- **RESTful** 원칙 준수
- 리소스 중심 네이밍
- 동사 사용 지양

```python
# ✅ 좋은 예
GET    /api/wardrobe/items
POST   /api/extract
DELETE /api/wardrobe/items/{item_id}

# ❌ 나쁜 예
GET    /api/getWardrobeItems
POST   /api/extractImage
DELETE /api/removeItem/{item_id}
```

### API 응답 형식
- 성공 시: `{"success": True, ...}`
- 실패 시: HTTP 상태 코드와 에러 메시지

```python
# 성공 응답
{
    "success": True,
    "data": {...}
}

# 에러 응답 (FastAPI 자동 처리)
HTTPException(status_code=400, detail="에러 메시지")
```

### 라우터 등록
- `app/main.py`의 `create_app()` 함수에서 모든 라우터 등록
- `prefix="/api"` 사용
- 태그 지정으로 API 문서 그룹화

```python
app.include_router(
    extraction_router, 
    prefix="/api", 
    tags=["Extraction"]
)
```

---

## 에러 처리

### HTTP 예외 사용
- FastAPI의 `HTTPException` 사용
- 적절한 HTTP 상태 코드 사용

```python
from fastapi import HTTPException

if not file:
    raise HTTPException(status_code=400, detail="파일이 필요합니다.")
```

### 예외 처리 패턴
- 라우터에서 try-except로 감싸기
- HTTPException은 재발생
- 일반 예외는 500 에러로 변환

```python
try:
    result = service.process()
    return {"success": True, "data": result}
except HTTPException:
    raise
except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))
```

### 로깅
- 중요한 에러는 로깅 (향후 구현)
- 사용자에게는 안전한 에러 메시지 제공

---

## 의존성 관리

### 패키지 관리
- `requirements.txt`에 프로덕션 의존성 명시
- `pyproject.toml`에 프로젝트 메타데이터 및 의존성 정의
- 버전 고정 권장 (예: `fastapi>=3.0.0`)

### 의존성 추가 시
1. `requirements.txt`에 추가
2. `pyproject.toml`의 `dependencies`에 추가
3. 버전 명시

```txt
# requirements.txt
fastapi>=3.0.0
pydantic>=2.0.0
```

---

## 환경 변수 관리

### 환경 변수 파일
- `.env` 파일 사용 (gitignore에 포함)
- `python-dotenv`로 로드
- `app/core/config.py`에서 중앙 관리

### 설정 클래스 패턴
```python
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_KEY = os.getenv("API_KEY", "")
    MAX_SIZE = int(os.getenv("MAX_SIZE", "10485760"))
    
    @staticmethod
    def check_api_key():
        if not Config.API_KEY:
            print("Warning: API_KEY not set")
```

### 필수 환경 변수
- `AZURE_OPENAI_API_KEY`: Azure OpenAI API 키
- `AZURE_OPENAI_ENDPOINT`: Azure OpenAI 엔드포인트 URL
- 기타 필요한 환경 변수는 `Config` 클래스에 정의

---

## 코드 리뷰 가이드라인

### 체크리스트
- [ ] 타입 힌팅이 모든 함수/메서드에 적용되었는가?
- [ ] PEP 8 스타일 가이드를 준수하는가?
- [ ] 적절한 에러 처리가 되어 있는가?
- [ ] API 응답 스키마가 `app/models/schemas.py`에 정의되어 있는가?
- [ ] 비즈니스 로직이 `app/services/`에 분리되어 있는가?
- [ ] 환경 변수는 `app/core/config.py`에서 관리되는가?
- [ ] 불필요한 주석이나 디버그 코드가 없는가?
- [ ] 함수/클래스에 의미 있는 이름이 사용되었는가?
- [ ] 상수/스키마가 중복 정의되지 않았는가? (단일 소스 원칙)
- [ ] 파일 검증 로직이 `validators.py`의 공용 함수를 사용하는가?
- [ ] 라우터 응답이 `response_helpers.py`를 사용하는가?
- [ ] 객체 복사에 `copy.deepcopy()`를 사용하는가?
- [ ] 경로 처리가 `pathlib.Path` 또는 `os.path.join()`을 사용하는가?
- [ ] 중복된 비즈니스 로직이 서비스 레이어로 통합되었는가?

### 커밋 메시지 규칙
- 형식: `[타입] 간단한 설명`
- 타입: `feat`, `fix`, `refactor`, `docs`, `style`, `test`

```
예시:
[feat] 이미지 추출 기능 추가
[fix] 에러 처리 로직 수정
[refactor] 서비스 레이어 리팩토링
```

---

## 추가 규칙

### 이미지 처리
- 업로드된 이미지는 `extracted_attributes/` 디렉토리에 저장
- 파일 크기 및 확장자 검증 필수
- `Config` 클래스에서 허용된 형식 관리
- 파일 검증은 `app/utils/validators.py`의 `validate_uploaded_file()` 사용

### 외부 API 통신
- 외부 API 클라이언트는 `app/services/`에 분리
- 재시도 로직 구현 권장
- API 키는 환경 변수로 관리

### 코드 중복 방지

#### 상수 및 스키마 정의
- **단일 소스 원칙**: 상수와 스키마는 한 곳에만 정의
- AI 관련 상수는 `app/ai/prompts/extraction_prompts.py`에 통합
- `app/core/constants.py`는 레거시 파일 (하위 호환성용 재export만 제공)

#### 검증 로직 통합
- 파일 업로드 검증은 `app/utils/validators.py`의 공용 함수 사용
- `validate_uploaded_file()`: 파일명, 확장자, MIME 타입, 크기 검증
- `validate_file_extension()`: 확장자 검증 및 정규화

#### 응답 패턴 통합
- 라우터 응답은 `app/utils/response_helpers.py`의 헬퍼 함수 사용
- `create_success_response()`: 성공 응답 생성
- `handle_route_exception()`: 예외 처리 통합
- 모든 라우터에서 동일한 응답 형식 유지

#### 객체 복사
- 딕셔너리/객체 복사는 `json.loads(json.dumps())` 대신 `copy.deepcopy()` 사용
- 의도 명확성과 성능 향상

#### 경로 처리
- 파일 경로 조합은 `os.path.join()` 또는 `pathlib.Path` 사용
- `pathlib.Path` 권장 (Python 3.4+)
- OS 의존성 제거 및 가독성 향상

#### 네이밍 일관성
- 메서드/함수명은 실제 구현과 일치해야 함
- 하위 호환성이 필요한 경우 deprecated 래퍼 제공
- 예: `recommend_with_gemini()` → `recommend_with_llm()` (deprecated 래퍼 유지)

#### 비즈니스 로직 통합
- 중복된 비즈니스 로직은 서비스 레이어로 통합
- 라우터는 최소한의 로직만 포함 (검증, 호출, 응답 변환)
- 예: 규칙 기반 추천 로직은 `recommender._rule_based_recommendation()`으로 통합

### 테스트
- 단위 테스트 작성 권장
- 테스트 파일은 `tests/` 디렉토리에 배치
- 테스트 파일명: `test_{module_name}.py`

---

## 참고 자료
- [FastAPI 공식 문서](https://fastapi.tiangolo.com/)
- [PEP 8 스타일 가이드](https://pep8.org/)
- [Pydantic 문서](https://docs.pydantic.dev/)

---

**마지막 업데이트**: 2024년
