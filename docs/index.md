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

##  빠른 실행 가이드 (Azure Functions)

이 프로젝트는 Azure Functions 기반으로 실행됩니다.

**1. 필수 도구 설치**

**macOS:**
```bash
brew tap azure/functions
brew install azure-functions-core-tools@4
```

**Windows:**
```powershell
winget install Microsoft.Azure.FunctionsCoreTools
# 또는 npm 사용 시: npm i -g azure-functions-core-tools@4 --unsafe-perm true
```

**2. 실행 (로컬)**

**macOS/Linux:**
```bash
# 가상 환경 활성화
source .venv/bin/activate

# 함수 실행
func start
```

**Windows (PowerShell):**
```powershell
# 가상 환경 활성화
.\.venv\Scripts\Activate.ps1

# 함수 실행
func start
```

- **서버 주소**: http://localhost:7071
- **API 문서**: http://localhost:7071/docs

## 📋 목차

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

- **프레임워크**: FastAPI (>= 0.110)
- **Python 버전**: >= 3.12 (권장: 3.12.10)
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
├── alembic/                     # DB 마이그레이션
├── alembic.ini
├── function_app.py              # Azure Functions 엔트리
├── host.json                    # Azure Functions 설정
├── local.settings.json          # (로컬) Functions 설정 (gitignore)
├── reset_db.py                  # (로컬) DB 초기화 스크립트
├── .env                        # 환경 변수 파일 (gitignore)
├── .env.example                # 환경 변수 예제 파일
├── .gitignore
├── pyproject.toml              # 프로젝트 메타데이터 및 의존성
├── uv.lock                     # uv lockfile
├── requirements.txt            # 프로덕션 의존성
└── docs/                       # 프로젝트 문서
    ├── index.md                # 메인 문서
    ├── development/
    │   └── rules.md            # 개발 규칙
    ├── architecture/
    │   └── langgraph-flows.md  # LangGraph 구조
    └── api/
        └── weather-api.md      # 날씨 API 가이드
```

## 시작하기

### 필수 요구사항

- Python 3.12 이상 (권장: 3.12.10)
- Azure OpenAI API 키 및 엔드포인트

### 설치 방법

1. **저장소 클론**
   ```bash
   git clone <repository-url>
   cd backend
   ```

2. **가상 환경 생성 및 활성화**
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # macOS/Linux
   python -m venv .venv
   source .venv/bin/activate
   ```

3. **의존성 설치**

   **pip 사용:**
   ```bash
   pip install -r requirements.txt
   ```

   **uv 사용 (권장):**
   ```bash
   # uv 설치 (아직 설치하지 않은 경우)
   # Windows (PowerShell)
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # 의존성 설치
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

#### 방법 1: FastAPI 서버 실행

**표준 Python 사용:**
```bash
python -m app.main
```

또는:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**uv 사용:**
```bash
# uv로 서버 실행 (의존성 자동 관리)
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

또는:

```bash
uv run python -m app.main
```

서버가 실행되면 다음 주소에서 접근할 수 있습니다:
- **API 서버**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs (Swagger UI)
- **대체 문서**: http://localhost:8000/redoc (ReDoc)

#### 방법 2: Azure Functions 실행

이 프로젝트는 Azure Functions 기반으로도 실행할 수 있습니다.

**1. 필수 도구 설치**

Azure Functions Core Tools를 설치해야 합니다:

**Windows:**
```powershell
winget install Microsoft.Azure.FunctionsCoreTools
# 또는 npm 사용 시:
npm i -g azure-functions-core-tools@4 --unsafe-perm true
```

**macOS:**
```bash
brew tap azure/functions
brew install azure-functions-core-tools@4
```

**Linux:**
```bash
# Ubuntu/Debian
wget -q https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb
sudo dpkg -i packages-microsoft-prod.deb
sudo apt-get update
sudo apt-get install azure-functions-core-tools-4
```

**2. uv를 사용한 실행 (권장)**

**Windows (PowerShell):**
```powershell
# uv로 의존성 설치 (가상 환경 자동 생성)
uv sync

# 가상 환경 활성화
.\.venv\Scripts\Activate.ps1

# Azure Functions 실행
func start
```

**macOS/Linux:**
```bash
# uv로 의존성 설치 (가상 환경 자동 생성)
uv sync

# 가상 환경 활성화
source .venv/bin/activate

# Azure Functions 실행
func start
```

**또는 uv run을 사용하여 한 번에 실행:**
```bash
# uv run을 사용하여 가상 환경 내에서 func 실행
uv run func start
```

**3. 기존 방식 (venv + pip)**

**Windows (PowerShell):**
```powershell
# 가상 환경 생성 및 활성화
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 의존성 설치
pip install -r requirements.txt

# 함수 실행
func start
```

**macOS/Linux:**
```bash
# 가상 환경 활성화
source .venv/bin/activate

# 함수 실행
func start
```

**서버 주소:**
- **API 서버**: http://localhost:7071
- **API 문서**: http://localhost:7071/docs

> **참고**: Azure Functions 실행 시 `local.settings.json` 파일의 환경 변수가 자동으로 로드됩니다.

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
    # ... 중략 ...
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

(상세 내용은 [docs/architecture/langgraph-flows.md](architecture/langgraph-flows.md) 참조)

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

(중략... 더 많은 문제 해결 정보는 [docs/index.md](index.md)를 참조하세요)

## Swagger UI 사용

브라우저에서 http://localhost:8000/docs 를 열면:
- 모든 API 엔드포인트 확인
- 직접 테스트 가능
- 요청/응답 스키마 확인

## 개발 가이드 및 규칙

- 상세한 개발 규칙은 [docs/development/rules.md](development/rules.md)를 참조하세요.
