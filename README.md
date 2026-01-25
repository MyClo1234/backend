# MyClo Backend - AI Stylist Agent

AI 기반 옷 이미지 특징 추출 및 코디 추천 백엔드 서버입니다.

## 🏗️ 아키텍처

### Domain-Driven Design (DDD)
이 프로젝트는 **도메인 중심 아키텍처**를 따릅니다. 각 기능(도메인)의 모든 코드가 하나의 폴더에 응집되어 있어 유지보수성과 확장성이 뛰어납니다.

```text
app/
├── domains/              # 도메인별 비즈니스 로직
│   ├── wardrobe/        # 옷장 관리
│   │   ├── router.py    # API 엔드포인트
│   │   ├── service.py   # 비즈니스 로직
│   │   ├── schema.py    # 데이터 스키마 (Pydantic)
│   │   └── model.py     # DB 모델 (SQLAlchemy)
│   ├── auth/            # 인증/인가
│   ├── user/            # 사용자 관리
│   ├── weather/         # 날씨 정보
│   ├── recommendation/  # AI 코디 추천
│   └── extraction/      # 이미지 분석
├── core/                # 공통 설정 및 유틸리티
├── ai/                  # AI/LLM 관련 모듈
└── main.py             # 애플리케이션 진입점
```

### 주요 특징
- ✅ **높은 응집도**: 관련 코드가 도메인별로 그룹화
- ✅ **낮은 결합도**: 도메인 간 명확한 인터페이스
- ✅ **확장 용이**: 새로운 도메인 추가 시 기존 코드 영향 최소화
- ✅ **마이크로서비스 전환 가능**: 각 도메인을 독립 서비스로 분리 가능

## 📚 문서 (Documentation)

상세 문서는 `docs/` 디렉토리에서 확인하세요:

- **[메인 문서 (Overview)](docs/index.md)**: 프로젝트 개요, 설치 및 실행 방법
- **[개발 규칙 (Project Rules)](docs/development/rules.md)**: 코딩 스타일, 네이밍 컨벤션
- **[아키텍처 (Architecture)](docs/architecture/langgraph-flows.md)**: LangGraph 워크플로우 구조
- **[API 가이드 (API Guide)](docs/api/weather-api.md)**: 날씨 API 사용 가이드

## 🚀 빠른 시작 (Quick Start)

### 필수 요구사항
- Python 3.12+
- Azure Functions Core Tools (선택사항)
- PostgreSQL (데이터베이스)

### 설치 및 실행

```bash
# 1. 가상 환경 생성
python -m venv .venv

# 2. 가상 환경 활성화
# Windows
.\.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate

# 3. 의존성 설치
uv sync  # 또는 pip install -r requirements.txt

# 4. 환경 변수 설정
cp .env.example .env
# .env 파일을 열어 필요한 값 설정

# 5. 서버 실행
python -m app.main
```

서버가 실행되면 http://localhost:8000 에서 API에 접근할 수 있습니다.

## 🔑 주요 도메인

### Wardrobe (옷장)
- 옷 이미지 업로드 및 관리
- Azure Blob Storage 연동
- 카테고리별 필터링 및 검색

### Auth & User (인증/사용자)
- JWT 기반 인증
- 회원가입/로그인
- 사용자 프로필 관리

### Weather (날씨)
- 기상청 API 연동
- 위치 기반 날씨 정보 제공
- 날씨 데이터 캐싱

### Recommendation (추천)
- AI 기반 코디 추천
- 날씨/상황 고려 알고리즘
- Azure OpenAI 연동

### Extraction (이미지 분석)
- AI 기반 옷 속성 추출
- 색상, 패턴, 소재 분석
- 자동 카테고리 분류

## 🛠️ 기술 스택

- **Framework**: FastAPI
- **Database**: PostgreSQL + SQLAlchemy
- **AI/ML**: Azure OpenAI, LangGraph
- **Storage**: Azure Blob Storage
- **Authentication**: JWT (python-jose)
- **Validation**: Pydantic

## 📖 더 알아보기

더 자세한 내용은 [docs/index.md](docs/index.md)를 참조하세요.
