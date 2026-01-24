# VS Code 디버깅 가이드 (backend)

이 문서는 VS Code에서 `backend`를 실행/디버깅하는 방법을 정리합니다.

## 준비물

- Python 3.12+
- VS Code 확장
  - Python (`ms-python.python`)
  - Azure Functions (`ms-azuretools.vscode-azurefunctions`) (Functions 디버깅/실행 시)
- (권장) `uv` 설치 및 `uv sync`로 의존성 설치

## 인터프리터 설정

`backend/.vscode/settings.json`에 기본 인터프리터가 `.venv`로 지정되어 있습니다.

- VS Code → `Python: Select Interpreter`에서 `${workspaceFolder}\\.venv\\Scripts\\python.exe` 선택

## FastAPI 디버깅 (Uvicorn)

`backend/.vscode/launch.json`에 아래 구성이 포함되어 있습니다.

- **FastAPI: Uvicorn (no reload)**: reload 없이 안정적으로 브레이크포인트가 걸립니다.
- **FastAPI: Uvicorn (reload + subProcess)**: 파일 변경 시 자동 재시작이 필요하면 이 구성을 사용합니다.

### 실행 방법

1. VS Code 좌측 `Run and Debug`(실행/디버그) 탭 열기
2. 디버그 구성 선택
3. `F5` 실행

기본 주소:
- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

### 브레이크포인트가 안 걸릴 때

- `--reload`는 내부적으로 서브프로세스를 띄웁니다.
- 이 경우 `FastAPI: Uvicorn (reload + subProcess)`를 사용하거나, `no reload` 구성으로 디버깅하세요.

## 테스트 디버깅 (pytest)

디버그 구성 **Pytest: All tests**를 선택하고 `F5` 실행하면 됩니다.

CLI로는 아래도 동일합니다:

```bash
uv run pytest
```

## 환경변수(.env)

디버그 구성은 `${workspaceFolder}/.env`를 `envFile`로 읽도록 되어 있습니다.

- `.env`는 보통 Git에 올리지 않고(`.gitignore`), 로컬에서만 관리합니다.

## Azure Functions 실행/디버깅 (참고)

이 프로젝트는 `function_app.py`를 통해 Azure Functions(ASGI)로도 실행됩니다.

- 로컬 실행:

```bash
func start
```

Functions 디버깅은 VS Code의 Azure Functions 확장을 통해 “Run/Debug” 구성을 별도로 잡는 경우가 많습니다(프로젝트 형태/호스트 설정에 따라 방식이 달라질 수 있음).

