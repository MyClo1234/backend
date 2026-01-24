# AI Stylist Agent Backend

AI 기반 옷 이미지 특징 추출 및 코디 추천 백엔드 서버입니다.

## 📚 문서 (Documentation)

이 프로젝트의 상세 문서는 `docs/` 디렉토리로 이동되었습니다.

- **[메인 문서 (Overview)](docs/index.md)**: 프로젝트 개요, 설치 및 실행 방법.
- **[개발 규칙 (Project Rules)](docs/development/rules.md)**: 코딩 스타일, 네이밍 컨벤션 등.
- **[아키텍처 (Architecture)](docs/architecture/langgraph-flows.md)**: LangGraph 워크플로우 구조.
- **[API 가이드 (API Guide)](docs/api/weather-api.md)**: 날씨 API 사용 가이드.

## 🚀 빠른 시작 (Quick Start)

**필수 도구**: Python 3.12+, Azure Functions Core Tools

```bash
# 가상 환경 생성
python -m venv .venv

# 활성화 (Windows)
.\.venv\Scripts\Activate.ps1

# 의존성 설치
uv sync  # 또는 pip install -r requirements.txt

# 서버 실행 (FastAPI)
python -m app.main
```

더 자세한 내용은 [docs/index.md](docs/index.md)를 참조하세요.
