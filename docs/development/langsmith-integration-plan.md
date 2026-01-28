# LangSmith 통합 플랜

## 📋 개요

LangSmith를 사용하여 LangGraph 워크플로우의 실행 상태를 모니터링하고 디버깅합니다.

## 🎯 목표

1. 모든 LangGraph 워크플로우에 LangSmith tracing 활성화
2. 워크플로우 실행 상태 시각화 및 분석
3. 노드별 실행 시간, 입력/출력, 에러 추적
4. 테스트 시나리오를 통한 워크플로우 검증

## 📦 현재 상태

- ✅ `langsmith` 패키지 이미 설치됨 (requirements.txt)
- ✅ LangGraph 워크플로우 3개:
    - `recommendation_workflow.py` - 코디 추천
    - `extraction_workflow.py` - 이미지 속성 추출 (직접 함수 호출)
    - `chat/workflows.py` - 채팅 워크플로우

## 🔧 단계별 구현 계획

### 1단계: 환경 변수 설정

**파일**: `.env.example`, `app/core/config.py`

```python
# .env.example에 추가
LANGCHAIN_API_KEY=your_langsmith_api_key
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=backend-workflows  # 프로젝트 이름
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com  # 기본값
```

**작업**:

- [ ] `.env.example`에 LangSmith 환경 변수 추가
- [ ] `app/core/config.py`에 LangSmith 설정 추가
- [ ] 로컬 `.env` 파일에 실제 API 키 설정

### 2단계: LangSmith 헬퍼 모듈 생성

**파일**: `app/utils/langsmith_helper.py` (신규)afasdfsdaf

**기능**:

- LangSmith 설정 초기화
- 환경 변수 기반 자동 활성화/비활성화
- 프로젝트별 태깅 지원

**작업**:

- [ ] `langsmith_helper.py` 생성
- [ ] 환경 변수 확인 및 설정 함수
- [ ] 프로젝트 이름, 태그 설정

### 3단계: 워크플로우에 Tracing 통합

#### 3-1. Recommendation Workflow

**파일**: `app/ai/workflows/recommendation_workflow.py`

**변경사항**:

- `workflow.compile()` 시 `config`에 LangSmith 설정 추가
- `workflow.invoke()` 또는 `workflow.ainvoke()` 호출 시 tracing 활성화

**작업**:

- [ ] `create_recommendation_workflow()` 수정
- [ ] `recommend_outfits()` 함수에 tracing config 추가

#### 3-2. Chat Workflow

**파일**: `app/domains/chat/workflows.py`

**변경사항**:

- `ChatWorkflow` 클래스에 LangSmith 설정 통합
- `get_chat_workflow()` 반환 시 config 포함

**작업**:

- [ ] `ChatWorkflow._create_compiled_chat_workflow()` 수정
- [ ] `get_chat_workflow()` 함수에 tracing 지원

#### 3-3. Extraction Workflow (선택사항)

**파일**: `app/ai/workflows/extraction_workflow.py`

**참고**: 현재는 LangGraph를 사용하지 않고 직접 함수 호출

- 향후 LangGraph로 전환 시 tracing 추가

### 4단계: 테스트 스크립트 작성

**파일**: `scripts/test_langsmith_workflows.py` (신규)

**기능**:

- 각 워크플로우별 테스트 시나리오
- 더미 데이터로 실행
- 실행 결과 및 LangSmith 링크 출력

**테스트 시나리오**:

1. **Recommendation Workflow**
    - 입력: 상의/하의 리스트, 날씨 정보
    - 검증: `final_outfits` 반환 확인
    - LangSmith에서 노드 실행 순서 확인

2. **Chat Workflow**
    - 입력: 사용자 쿼리, 컨텍스트
    - 검증: 인텐트 분석 → 분기 → 응답 생성
    - LangSmith에서 조건부 분기 확인

3. **Extraction Workflow** (향후)
    - 입력: 이미지 바이트
    - 검증: 속성 딕셔너리 반환

**작업**:

- [ ] 테스트 스크립트 작성
- [ ] 더미 데이터 생성 함수
- [ ] 실행 결과 검증 로직

### 5단계: 통합 테스트 및 검증

**작업**:

- [ ] 각 워크플로우 실행
- [ ] LangSmith UI에서 trace 확인
- [ ] 노드별 실행 시간 분석
- [ ] 에러 발생 시 trace 확인
- [ ] 성능 병목 지점 식별

## 📝 구현 세부사항

### LangSmith 설정 방법

```python
# app/utils/langsmith_helper.py
import os
from typing import Optional, Dict, Any

def get_langsmith_config(
    project_name: str = "backend-workflows",
    tags: Optional[list] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """LangSmith tracing 설정 반환"""
    api_key = os.getenv("LANGCHAIN_API_KEY")
    tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"

    if not tracing_enabled or not api_key:
        return {}

    config = {
        "configurable": {
            "thread_id": "test-run",  # 또는 고유 ID
        },
        "tags": tags or [],
        "metadata": metadata or {},
    }

    # 프로젝트 이름 설정
    if project_name:
        os.environ["LANGCHAIN_PROJECT"] = project_name

    return config
```

### 워크플로우 통합 예시

```python
# recommendation_workflow.py 수정 예시
from app.utils.langsmith_helper import get_langsmith_config

def recommend_outfits(...):
    # ... 기존 코드 ...

    workflow = get_recommendation_workflow()

    # LangSmith tracing 활성화
    config = get_langsmith_config(
        project_name="recommendation-workflow",
        tags=["recommendation", "outfit"],
        metadata={"user_request": user_request, "count": count}
    )

    final_state = workflow.invoke(initial_state, config=config)

    return final_state.get("final_outfits", [])
```

## 🧪 테스트 실행 방법

### 1. 환경 변수 설정

```bash
# .env 파일에 추가
export LANGCHAIN_API_KEY="your-api-key-here"
export LANGCHAIN_TRACING_V2="true"
export LANGCHAIN_PROJECT="backend-workflows"
```

### 2. 테스트 스크립트 실행

```bash
# 전체 워크플로우 테스트
python scripts/test_langsmith_workflows.py

# 특정 워크플로우만 테스트
python scripts/test_langsmith_workflows.py --workflow recommendation
python scripts/test_langsmith_workflows.py --workflow chat
```

### 3. LangSmith UI에서 확인

1. https://smith.langchain.com 접속
2. 프로젝트 선택: `backend-workflows`
3. 최근 실행된 trace 확인
4. 각 노드의 입력/출력, 실행 시간 분석

## 📊 확인 사항

### 각 워크플로우에서 확인할 항목

1. **노드 실행 순서**
    - 예상된 순서대로 실행되는지
    - 조건부 분기가 올바르게 작동하는지

2. **입력/출력 데이터**
    - 각 노드의 입력 state 확인
    - 출력 state 변경 사항 확인

3. **실행 시간**
    - 각 노드별 소요 시간
    - 병목 지점 식별

4. **에러 처리**
    - 에러 발생 시 trace에서 확인
    - 에러가 발생한 노드와 원인 파악

5. **LLM 호출**
    - LLM 호출 노드의 프롬프트 확인
    - 응답 내용 확인

## 🔍 디버깅 팁

1. **특정 실행 추적**
    - `thread_id`를 고유하게 설정하여 특정 실행만 필터링

2. **태그 활용**
    - 워크플로우별, 환경별 태그 설정
    - 예: `["production", "recommendation"]`, `["test", "chat"]`

3. **메타데이터 활용**
    - 사용자 ID, 요청 ID 등 추가 정보 저장

4. **비교 분석**
    - 성공한 실행 vs 실패한 실행 비교
    - 다른 입력에 대한 실행 비교

## ⚠️ 주의사항

1. **프로덕션 환경**
    - 민감한 데이터는 메타데이터에 포함하지 않기
    - API 키는 환경 변수로 관리

2. **성능 영향**
    - Tracing은 약간의 오버헤드가 있음
    - 프로덕션에서는 선택적으로 활성화

3. **비용**
    - LangSmith는 유료 서비스일 수 있음
    - 사용량 모니터링 필요

## 📚 참고 자료

- [LangSmith Documentation](https://docs.smith.langchain.com/)
- [LangGraph Tracing](https://langchain-ai.github.io/langgraph/how-tos/tracing/)
- [LangSmith Python SDK](https://github.com/langchain-ai/langsmith-sdk)

## ✅ 체크리스트

### 설정

- [ ] LangSmith API 키 발급
- [ ] 환경 변수 설정
- [ ] Config 클래스에 LangSmith 설정 추가

### 구현

- [ ] `langsmith_helper.py` 생성
- [ ] Recommendation Workflow 통합
- [ ] Chat Workflow 통합
- [ ] 테스트 스크립트 작성

### 테스트

- [ ] Recommendation Workflow 테스트
- [ ] Chat Workflow 테스트
- [ ] LangSmith UI에서 trace 확인
- [ ] 노드별 실행 분석
- [ ] 에러 시나리오 테스트

### 문서화

- [ ] README에 LangSmith 사용법 추가
- [ ] 개발 가이드 업데이트
