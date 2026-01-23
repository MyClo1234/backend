# AI Stylist Agent Backend

AI 기반 옷 이미지 특징 추출 및 코디 추천 백엔드 서버입니다. Azure OpenAI (GPT-4o)와 LangGraph를 활용하여 업로드된 옷 이미지에서 카테고리, 색상, 패턴, 소재 등의 속성을 자동으로 추출하고, 저장된 옷 아이템들을 기반으로 코디 추천을 제공합니다.

## GitHub Workflow

이 프로젝트는 다음과 같은 전형적인 GitHub 워크플로우를 권장합니다.

### 1. 이슈 생성 (Issue Creation)

새로운 작업(기능 추가, 버그 수정 등)을 시작하기 전에 반드시 GitHub 이슈를 생성합니다. 작업 성격에 따라 다음과 같이 카테고리를 분류하여 생성합니다.

- **[Feature]**: 새로운 기능 추가 또는 기존 기능 고도화
- **[Bug]**: 예상치 못한 오류 또는 문제 해결
- **[Refactor]**: 코드 구조 개선 (기능 변화 없음)
- **[Chore]**: 빌드 설정, 패키지 매니저 설정, 문서 수정 등
- **[Test]**: 테스트 코드 추가 및 수정

**작성 가이드:**

- 제목은 `[카테고리] 작업 내용` 형식으로 명확히 기술합니다. (예: `[Feature] 로그인 API 구현`)
- 관련 라벨(Labels)을 지정합니다. (예: enhancement, bug, documentation)

### 2. 브랜치 생성 (Branching)

이슈가 생성되면 해당 이슈 번호를 포함하여 새로운 브랜치를 생성합니다.

**브랜치 네이밍 컨벤션:** `type/#이슈번호-간략한설명`

예: `feat/#12-login-api`, `fix/#45-auth-token-error`

**명령어:**

```bash
git checkout -b feat/#이슈번호-설명
```

### 3. 변경 사항 커밋 (Committing Changes)

작업 내용을 논리적인 단위로 나누어 커밋합니다.

- 커밋 메시지에 이슈 번호를 포함하면 관리하기 좋습니다.
- 예: `feat: 로그인 API 구현 (#12)`

### 4. 풀 리퀘스트 생성 (Pull Request)

작업이 완료되면 main 브랜치로 Pull Request(PR)를 생성합니다.

- PR 설명란에 `Closes #이슈번호` 형식을 사용하여 관련 이슈를 자동으로 종료하도록 설정합니다.
- 리뷰어(Reviewers)를 지정하고 피드백을 반영한 후 머지(Merge)합니다.

## � 빠른 실행 가이드 (Azure Functions)

이 프로젝트는 Azure Functions 기반으로 실행됩니다.

**1. 필수 도구 설치**

- **Python 3.12.10** (필수)
- **Azure Functions Core Tools v4 (func)**
- **uv** (Python 패키지 매니저)

**2. 실행 (로컬 - uv 사용 권장)**

이 프로젝트는 `uv`를 통해 의존성을 관리합니다.

```bash
# 1. 저장소 클론 및 이동
git clone <repository-url>
cd backend

# 2. 가상환경 생성 (Python 3.12.10)
# .python-version 파일에 명시된 버전을 사용하여 .venv를 생성합니다.
uv venv

# 3. 의존성 설치
# 생성된 가상환경에 필요한 패키지들을 동기화합니다.
uv sync

# 4. Azure Function 실행
# uv run을 사용하면 가상환경을 자동으로 활성화하여 실행합니다.
uv run func start
```

**서버 주소**: http://localhost:7071

- **서버 주소**: http://localhost:7071
- **API 문서**: http://localhost:7071/docs

## �📋 목차

- [주요 기능](#주요-기능)
- [기술 스택](#기술-스택)
- [프로젝트 구조](#프로젝트-구조)
- [시작하기](#시작하기)
- [환경 변수 설정](#환경-변수-설정)
- [API 엔드포인트](#api-엔드포인트)
- [LangGraph 워크플로우 구조](#langgraph-워크플로우-구조)
- [Python 코드에서 직접 사용](#python-코드에서-직접-사용)
- [문제 해결](#문제-해결)
- [개발 가이드](#개발-가이드)
- [프로젝트 규칙](#프로젝트-규칙)

## 주요 기능

### 1. 이미지 속성 추출 (`/api/extract`)
- 옷 이미지를 업로드하여 자동으로 속성 추출
- **Azure Blob Storage**에 이미지 자동 저장 (설정된 경우)
- 저장 경로: `users/{user_id}/{yyyyMMdd}/{uuid}.{ext}`
- 추출되는 속성:
  - 카테고리 (상의/하의, 세부 카테고리)
  - 색상 (주색상, 보조색상, 톤)
  - 패턴 (무늬 유형)
  - 소재 (추정 소재)
  - 핏 (핏 타입)
  - 디테일 (넥라인, 소매, 길이, 클로저 등)
  - 스타일 태그
  - 점수 (정장도, 따뜻함, 계절성, 활용도)
  - 메타 정보 (레이어링 여부 등)

### 2. 옷장 관리 (`/api/wardrobe`)
- 추출된 옷 아이템을 옷장에 저장
- 저장된 아이템 목록 조회
- 아이템 삭제

### 3. 코디 추천 (`/api/recommend`)
- 저장된 옷 아이템들을 기반으로 코디 추천
- 상의와 하의의 조합 점수 계산
- 추천 이유 및 스타일 설명 제공

### 4. 헬스 체크 (`/api/health`)
- 서버 상태 확인

## 기술 스택

- **프레임워크**: FastAPI 3.0+
- **Python 버전**: >= 3.11
- **AI 모델**: Azure OpenAI (GPT-4o)
- **워크플로우**: LangGraph
- **이미지 처리**: Pillow (PIL)
- **스토리지**: Azure Blob Storage (선택사항)
- **데이터 검증**: Pydantic 2.0+
- **환경 변수 관리**: python-dotenv
- **CORS**: FastAPI CORS Middleware

## 프로젝트 구조

```
backend/
├── app/
│   ├── ai/                     # AI 관련 코드 통합
│   │   ├── clients/            # LLM 클라이언트
│   │   │   └── azure_openai_client.py
│   │   ├── workflows/          # LangGraph 워크플로우
│   │   │   ├── extraction_workflow.py
│   │   │   └── recommendation_workflow.py
│   │   ├── nodes/              # LangGraph 노드
│   │   │   ├── extraction_nodes.py
│   │   │   └── recommendation_nodes.py
│   │   ├── prompts/            # 프롬프트 템플릿
│   │   │   ├── extraction_prompts.py
│   │   │   └── recommendation_prompts.py
│   │   └── schemas/            # AI 관련 스키마
│   │       └── workflow_state.py
│   ├── core/                   # 핵심 설정 및 상수
│   │   ├── config.py           # 환경 설정 (API 키, 파일 크기 제한 등)
│   │   └── constants.py        # 상수 정의 (레거시)
│   ├── models/                 # 데이터 모델 (Pydantic 스키마)
│   │   └── schemas.py          # API 요청/응답 스키마
│   ├── routers/                # API 라우터
│   │   ├── health_routes.py    # 헬스 체크 엔드포인트
│   │   ├── extraction_routes.py # 이미지 추출 엔드포인트
│   │   ├── wardrobe_routes.py  # 옷장 관리 엔드포인트
│   │   └── recommendation_routes.py # 코디 추천 엔드포인트
│   ├── services/               # 비즈니스 로직
│   │   ├── extractor.py        # 속성 추출 서비스 (LangGraph 래퍼)
│   │   ├── recommender.py      # 코디 추천 서비스 (LangGraph 래퍼)
│   │   ├── wardrobe_manager.py  # 옷장 관리 서비스
│   │   └── blob_storage.py     # Azure Blob Storage 서비스
│   ├── utils/                  # 유틸리티 함수
│   │   ├── helpers.py          # 헬퍼 함수
│   │   ├── json_parser.py      # JSON 파싱 유틸리티
│   │   ├── validators.py       # 스키마 검증 및 파일 검증 유틸리티
│   │   └── response_helpers.py # 공용 응답 헬퍼 함수
│   └── main.py                 # 애플리케이션 진입점
├── extracted_attributes/        # 추출된 이미지 저장 디렉토리 (자동 생성)
├── .env                        # 환경 변수 파일 (gitignore)
├── .env.example                # 환경 변수 예제 파일
├── .gitignore
├── pyproject.toml              # 프로젝트 메타데이터 및 의존성
├── requirements.txt            # 프로덕션 의존성
├── verify_endpoints.py         # 엔드포인트 검증 스크립트
├── PROJECT_RULES.md            # 프로젝트 개발 규칙
└── README.md                   # 프로젝트 문서
```

## 시작하기

### 필수 요구사항

- **Python 3.12.10** (필수: `.python-version` 파일 참조)
- Azure OpenAI API 키 및 엔드포인트
- Azure Functions Core Tools

### 설치 방법 (uv 사용 권장)

1. **저장소 클론**
   ```bash
   git clone <repository-url>
   cd backend
   ```

2. **uv 설치** (아직 설치하지 않은 경우)
   ```bash
   # Windows (PowerShell)
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```
   
3. **환경 설정 및 의존성 설치**
   ```bash
   # uv가 Python 3.12.10을 다운로드하고 가상환경을 구성합니다.
   uv sync
   ```

### 환경 변수 설정

`.env` 파일을 프로젝트 루트에 생성하고 다음 내용을 추가하세요:

```env
# Azure OpenAI 설정
AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-02-15-preview
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o
AZURE_OPENAI_MODEL_NAME=gpt-4o

# Azure Blob Storage 설정 (선택사항)
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=your_account_name;AccountKey=your_account_key;EndpointSuffix=core.windows.net
AZURE_STORAGE_CONTAINER_NAME=images
```

> **참고**: `.env` 파일은 `.gitignore`에 포함되어 있어 Git에 커밋되지 않습니다. `.env.example` 파일을 참고하세요.

**Azure OpenAI 설정 방법:**
1. Azure Portal에서 Azure OpenAI 리소스 생성
2. API 키와 엔드포인트 URL 확인
3. GPT-4o 모델 배포 (Deployment)

**Azure Blob Storage 설정 방법 (선택사항):**
1. Azure Portal에서 Storage Account 생성
2. Access Keys에서 Connection String 복사
3. Container 생성 (기본값: `images`)
4. Connection String을 `.env` 파일에 설정
   - 설정하지 않으면 로컬 파일 시스템에 저장됩니다

### 서버 실행

**Azure Functions 실행 (권장):**
```bash
uv run func start
```

**표준 Uvicorn 실행 (FastAPI 개발 모드):**
Azure Functions 환경이 아닌 순수 FastAPI로 테스트할 때:
```bash
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

서버가 실행되면 다음 주소에서 접근할 수 있습니다:
- **API 서버**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs (Swagger UI)
- **대체 문서**: http://localhost:8000/redoc (ReDoc)

## 환경 변수 설정

### 필수 환경 변수

| 변수명                  | 설명                        | 예시                                      |
| ----------------------- | --------------------------- | ----------------------------------------- |
| `AZURE_OPENAI_API_KEY`  | Azure OpenAI API 키         | `your_key_here`                           |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI 엔드포인트 URL | `https://your-resource.openai.azure.com/` |

### 선택적 환경 변수

환경 변수를 설정하지 않으면 `app/core/config.py`의 기본값이 사용됩니다.

**Azure OpenAI 설정:**
- `AZURE_OPENAI_API_VERSION`: API 버전 (기본값: `2024-02-15-preview`)
- `AZURE_OPENAI_DEPLOYMENT_NAME`: 배포 이름 (기본값: `gpt-4o`)
- `AZURE_OPENAI_MODEL_NAME`: 모델 이름 (기본값: `gpt-4o`)

**Azure Blob Storage 설정 (선택사항):**
- `AZURE_STORAGE_CONNECTION_STRING`: Azure Storage 연결 문자열
  - 설정하지 않으면 로컬 파일 시스템에 저장됩니다
- `AZURE_STORAGE_CONTAINER_NAME`: Blob 컨테이너 이름 (기본값: `images`)

**기타 설정:**
- `MAX_FILE_SIZE`: 최대 파일 크기 (기본값: 10MB)
- `OUTPUT_DIR`: 추출된 이미지 저장 디렉토리 (기본값: `extracted_attributes`)

## API 엔드포인트

### 1. 헬스 체크

```http
GET /api/health
```

**응답 예시:**
```json
{
  "status": "ok"
}
```

### 2. 이미지 속성 추출 (LangGraph 워크플로우 사용)

```http
POST /api/extract
Content-Type: multipart/form-data
```

**요청:**
- `image`: 이미지 파일 (multipart/form-data) - **필수**
- `user_id`: 사용자 UUID (예: `550e8400-e29b-41d4-a716-446655440000`) - **필수**

**curl 예시:**
```bash
curl -X POST "http://localhost:8000/api/extract" \
  -F "image=@/path/to/your/clothing_image.jpg" \
  -F "user_id=550e8400-e29b-41d4-a716-446655440000"
```

**Python 예시:**
```python
import requests

url = "http://localhost:8000/api/extract"
with open("shirt.jpg", "rb") as f:
    files = {"image": f}
    data = {"user_id": "550e8400-e29b-41d4-a716-446655440000"}
    response = requests.post(url, files=files, data=data)
    print(response.json())
```

**응답 예시:**
```json
{
  "success": true,
  "attributes": {
    "category": {
      "main": "top",
      "sub": "t-shirt",
      "confidence": 0.95
    },
    "color": {
      "primary": "blue",
      "secondary": ["white"],
      "tone": "cool",
      "confidence": 0.92
    },
    "pattern": {
      "type": "solid",
      "confidence": 0.88
    },
    ...
  },
  "saved_to": "extracted_attributes/048ed381-450b-4f9c-9cf7-9d2f4674938e.json",
  "image_url": "https://yourstorage.blob.core.windows.net/images/users/550e8400-e29b-41d4-a716-446655440000/20241223/048ed381-450b-4f9c-9cf7-9d2f4674938e.jpg",
  "item_id": "048ed381-450b-4f9c-9cf7-9d2f4674938e",
  "blob_name": "users/550e8400-e29b-41d4-a716-446655440000/20241223/048ed381-450b-4f9c-9cf7-9d2f4674938e.jpg",
  "storage_type": "blob_storage"
}
```

**저장 위치:**
- **Azure Blob Storage** (설정된 경우):
  - 경로: `users/{user_id}/{yyyyMMdd}/{uuid}.{ext}`
  - 예: `users/550e8400-e29b-41d4-a716-446655440000/20241223/048ed381-450b-4f9c-9cf7-9d2f4674938e.jpg`
  - `blob_url`로 직접 접근 가능
- **로컬 파일 시스템** (Blob Storage 미설정 시):
  - 경로: `extracted_attributes/{item_id}.json` (속성 데이터)
  - `image_url`로 접근 가능

### 3. 옷장에 아이템 추가

```http
POST /api/wardrobe/items
Content-Type: multipart/form-data
```

**curl 예시:**
```bash
curl -X POST "http://localhost:8000/api/wardrobe/items" \
  -F "image=@/path/to/image.jpg" \
  -F "attributes={\"category\":{\"main\":\"top\"}}"
```

### 4. 옷장 아이템 조회

```http
GET /api/wardrobe/items
```

**curl 예시:**
```bash
curl http://localhost:8000/api/wardrobe/items
```

**응답 예시:**
```json
{
  "success": true,
  "items": [
    {
      "id": "uuid-here",
      "filename": "shirt.jpg",
      "attributes": {...},
      "image_url": "/api/images/..."
    }
  ],
  "count": 1
}
```

### 5. 옷장 아이템 삭제

```http
DELETE /api/wardrobe/items/{item_id}
```

### 6. 코디 추천 (LangGraph 워크플로우 사용)

```http
GET /api/recommend/outfit
```

**curl 예시:**
```bash
curl "http://localhost:8000/api/recommend/outfit?count=3"
```

**쿼리 파라미터:**
- `count`: 추천할 코디 개수 (기본값: 1)
- `season`: 계절 필터 (선택사항)
- `formality`: 정장도 필터 0.0~1.0 (선택사항)
- `use_llm`: LLM 사용 여부 (기본값: true, Azure OpenAI 사용)

**응답 예시:**
```json
{
  "success": true,
  "outfits": [
    {
      "top": {...},
      "bottom": {...},
      "score": 0.85,
      "reasons": ["색상 조화", "스타일 일치"],
      "reasoning": "파란색 티셔츠와 청바지의 조화로운 조합입니다.",
      "style_description": "캐주얼한 데일리 룩"
    }
  ],
  "count": 1,
  "method": "azure-openai-optimized"
}
```

### 7. 코디 점수 계산

```http
GET /api/outfit/score
```

**쿼리 파라미터:**
- `top_id`: 상의 아이템 ID (필수)
- `bottom_id`: 하의 아이템 ID (필수)

**curl 예시:**
```bash
curl "http://localhost:8000/api/outfit/score?top_id=uuid-1&bottom_id=uuid-2"
```

**응답 예시:**
```json
{
  "success": true,
  "score": 0.85,
  "score_percent": 85,
  "reasons": ["색상 조화", "스타일 일치"],
  "top": {...},
  "bottom": {...}
}
```

자세한 API 문서는 서버 실행 후 http://localhost:8000/docs 에서 확인할 수 있습니다.

## LangGraph 워크플로우 구조

이 프로젝트는 LangGraph를 사용하여 AI 워크플로우를 구조화했습니다.

### 이미지 추출 워크플로우

```
이미지 입력
  ↓
[전처리] → [Azure OpenAI Vision API 호출] → [JSON 파싱] → [스키마 검증]
                                                              ↓
                                                      [성공?]
                                                      ↙      ↘
                                              [정규화]    [재시도]
                                                      ↓
                                                  [최종 결과]
```

### 코디 추천 워크플로우

```
상의/하의 리스트
  ↓
[후보 조합 생성] → [LLM 입력 준비] → [Azure OpenAI 호출] → [결과 처리]
                                                              ↓
                                                          [최종 추천]
```

## Python 코드에서 직접 사용

### 이미지 속성 추출

```python
from app.ai.workflows.extraction_workflow import extract_attributes

# 이미지 파일 읽기
with open("shirt.jpg", "rb") as f:
    image_bytes = f.read()

# 속성 추출 (LangGraph 워크플로우 실행)
attributes = extract_attributes(image_bytes)
print(attributes)
```

### 코디 추천

```python
from app.ai.workflows.recommendation_workflow import recommend_outfits

# 옷장에서 상의/하의 가져오기
tops = [...]  # 상의 아이템 리스트
bottoms = [...]  # 하의 아이템 리스트

# 코디 추천 (LangGraph 워크플로우 실행)
recommendations = recommend_outfits(
    tops=tops,
    bottoms=bottoms,
    count=3,
    user_request="격식 있는 저녁 식사",
    weather_info={"temperature": 20, "condition": "sunny"}
)

for outfit in recommendations:
    print(f"Score: {outfit['score']}")
    print(f"Reasoning: {outfit['reasoning']}")
```

## 문제 해결

### 1. Azure OpenAI API 키 오류

**에러:**
```
Warning: AZURE_OPENAI_API_KEY environment variable is not set.
```

**해결:**
- `.env` 파일이 `backend` 폴더에 있는지 확인
- 환경 변수 이름이 정확한지 확인 (`AZURE_OPENAI_API_KEY`)

### 2. 엔드포인트 오류

**에러:**
```
Azure OpenAI API error: Invalid endpoint
```

**해결:**
- `AZURE_OPENAI_ENDPOINT`가 올바른 형식인지 확인
- 엔드포인트 URL 끝에 `/`가 있는지 확인
- 예: `https://your-resource.openai.azure.com/`

### 3. 모델 배포 오류

**에러:**
```
Model deployment not found
```

**해결:**
- Azure Portal에서 GPT-4o 모델이 배포되어 있는지 확인
- `AZURE_OPENAI_DEPLOYMENT_NAME`이 배포 이름과 일치하는지 확인

### 4. 의존성 설치 오류

**에러:**
```
ModuleNotFoundError: No module named 'langgraph'
```

**해결:**
```bash
pip install -r requirements.txt
```

또는 개별 설치:
```bash
pip install openai langgraph langchain langchain-openai azure-storage-blob
```

### 5. Azure Blob Storage 연결 오류

**에러:**
```
Failed to initialize Blob Storage client
```

**해결:**
- `.env` 파일에 `AZURE_STORAGE_CONNECTION_STRING`이 올바르게 설정되었는지 확인
- Azure Portal에서 Storage Account의 Access Keys 확인
- Connection String 형식이 올바른지 확인:
  ```
  DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net
  ```
- Blob Storage가 설정되지 않은 경우, 로컬 파일 시스템에 자동으로 저장됩니다

### 6. 이미지 저장 위치 확인

**Azure Blob Storage에 저장된 경우:**
- API 응답의 `blob_name` 필드에서 경로 확인
- `blob_url`로 이미지 직접 접근
- Azure Portal → Storage Account → Containers → `images` 컨테이너에서 확인

**로컬에 저장된 경우:**
- `extracted_attributes/` 폴더에서 JSON 파일 확인
- `image_url`로 이미지 접근

## Swagger UI 사용

브라우저에서 http://localhost:8000/docs 를 열면:
- 모든 API 엔드포인트 확인
- 직접 테스트 가능
- 요청/응답 스키마 확인

## 개발 가이드

### 코드 스타일

- **PEP 8** 준수
- **타입 힌팅** 필수 사용
- **Docstring** 작성 권장 (Google 스타일)
- 들여쓰기: **4 spaces** (탭 사용 금지)
- 최대 줄 길이: **120자**

### 네이밍 컨벤션

- 변수 및 함수: `snake_case`
- 클래스: `PascalCase`
- 상수: `UPPER_SNAKE_CASE`
- 모듈/파일명: `snake_case`

### 프로젝트 규칙

자세한 개발 규칙은 [PROJECT_RULES.md](./PROJECT_RULES.md)를 참고하세요.

주요 규칙:
- 라우터는 `app/routers/`에 도메인별로 분리
- 비즈니스 로직은 `app/services/`에 구현
- AI 관련 코드는 `app/ai/`에 통합
  - LangGraph 워크플로우: `app/ai/workflows/`
  - LangGraph 노드: `app/ai/nodes/`
  - 프롬프트 템플릿: `app/ai/prompts/`
  - 워크플로우 스키마: `app/ai/schemas/`
- API 스키마는 `app/models/schemas.py`에 정의
- 환경 변수는 `app/core/config.py`에서 중앙 관리

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

### 엔드포인트 검증

프로젝트에 포함된 `verify_endpoints.py` 스크립트를 사용하여 기본 엔드포인트를 검증할 수 있습니다:

```bash
python verify_endpoints.py
```

## 의존성 관리

### 프로덕션 의존성

주요 의존성은 `requirements.txt`와 `pyproject.toml`에 명시되어 있습니다:

- `fastapi>=3.0.0`: 웹 프레임워크
- `uvicorn`: ASGI 서버
- `openai>=1.0.0`: Azure OpenAI SDK
- `langgraph>=0.0.1`: LangGraph 워크플로우
- `langchain>=0.1.0`: LangChain (LangGraph 의존성)
- `langchain-openai>=0.0.5`: LangChain Azure OpenAI 통합
- `azure-storage-blob>=12.0.0`: Azure Blob Storage SDK
- `Pillow>=10.0.0`: 이미지 처리
- `pydantic>=2.0.0`: 데이터 검증
- `python-dotenv>=1.0.0`: 환경 변수 관리

### uv 사용 가이드

**uv**는 빠른 Python 패키지 관리자입니다. pip보다 빠르고 효율적입니다.

**주요 명령어:**

```bash
# 의존성 설치 (requirements.txt 및 pyproject.toml 기반)
uv sync

# 특정 패키지 추가
uv add package-name

# 개발 의존성 추가
uv add --dev package-name

# 패키지 제거
uv remove package-name

# 스크립트 실행 (가상 환경 자동 활성화)
uv run python script.py
uv run uvicorn app.main:app --reload

# 가상 환경 활성화 (수동)
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# 의존성 업데이트
uv sync --upgrade

# 의존성 목록 확인
uv pip list
```

**uv vs pip 비교:**

| 작업          | pip                               | uv                 |
| ------------- | --------------------------------- | ------------------ |
| 의존성 설치   | `pip install -r requirements.txt` | `uv sync`          |
| 패키지 추가   | `pip install package`             | `uv add package`   |
| 스크립트 실행 | `python script.py`                | `uv run script.py` |
| 속도          | 보통                              | 매우 빠름          |

### 의존성 추가 시

**pip 사용 시:**
1. `requirements.txt`에 추가
2. `pyproject.toml`의 `dependencies`에 추가
3. `pip install -r requirements.txt` 실행

**uv 사용 시:**
1. `uv add package-name` 실행 (자동으로 requirements.txt와 pyproject.toml 업데이트)
2. 또는 수동으로 `pyproject.toml`에 추가 후 `uv sync` 실행

## 라이선스

이 프로젝트의 라이선스 정보는 저장소의 LICENSE 파일을 참고하세요.

## 다음 단계

1. **옷장에 아이템 추가**: 여러 옷 이미지를 업로드하여 옷장 구성
2. **코디 추천 테스트**: 다양한 조건으로 추천 테스트
3. **워크플로우 커스터마이징**: `app/ai/nodes/`에서 노드 수정
4. **프롬프트 최적화**: `app/ai/prompts/`에서 프롬프트 조정

## 참고 자료

- [FastAPI 문서](https://fastapi.tiangolo.com/)
- [LangGraph 문서](https://langchain-ai.github.io/langgraph/)
- [Azure OpenAI 문서](https://learn.microsoft.com/azure/ai-services/openai/)

## 기여하기

이슈나 개선 사항이 있으면 이슈를 생성하거나 Pull Request를 제출해주세요.

---

**마지막 업데이트**: 2026년 1월

## 변경 이력

### 2026-01-22
- Azure Blob Storage 지원 추가
- 이미지 저장 경로 형식: `users/{user_id}/{yyyyMMdd}/{uuid}.{ext}`
- API 엔드포인트에 `user_id` (UUID) 파라미터 추가
- 응답에 `blob_name`, `storage_type` 필드 추가
