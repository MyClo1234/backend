# Backend Testing Guide

이 디렉토리는 백엔드 서버의 테스트 코드를 포함합니다.

## 🛠️ 테스트 환경 설정

테스트를 실행하기 위해 필요한 의존성을 설치해야 합니다.

```bash
# uv 사용 시 (권장)
uv sync

# (대안) pip 사용 시
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx
```

## 🧪 테스트 실행

`pytest`를 사용하여 테스트를 실행합니다.

```bash
# 전체 테스트 실행
pytest

# 상세 출력 확인
pytest -v

# 특정 테스트 파일 실행
pytest tests/unit/test_validators.py
pytest tests/integration/test_health.py
```

## 📁 디렉토리 구조

- `unit/`: 단위 테스트 (외부 의존성 없음)
- `integration/`: 통합 테스트 (API 엔드포인트 테스트)
- `conftest.py`: 공용 픽스처 (TestClient 설정 등)
