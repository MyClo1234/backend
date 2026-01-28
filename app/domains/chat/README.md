# Chat Domain 구현 문서

## 📋 개요

멀티 에이전트 기반 채팅 시스템 구현. LangGraph를 사용한 워크플로우 기반 대화 처리 및 상태 관리.

## 🏗️ 아키텍처

### 데이터 저장 전략

**하이브리드 저장소 구조:**
- **PostgreSQL**: 세션 메타데이터 및 대화 메시지
- **Cosmos DB**: 워크플로우 실행 상태 (체크포인트)

### 데이터 분리 이유

1. **메시지 (PostgreSQL)**
   - 관계형 구조로 조회/정렬 용이
   - `created_at` 인덱스로 빠른 정렬
   - 무한 확장 가능 (페이지네이션)
   - Foreign Key로 데이터 무결성 보장

2. **상태 (Cosmos DB)**
   - 문서 구조로 복잡한 상태 저장에 적합
   - 빠른 읽기/쓰기
   - `messages` 배열 제외로 문서 크기 제한 해결

## 📁 파일 구조

```
app/domains/chat/
├── models.py              # PostgreSQL 모델 (ChatSession, ChatMessage)
├── states.py              # ChatState TypedDict 정의
├── stores.py              # Cosmos DB 상태 저장소
├── services.py            # 비즈니스 로직
├── workflows.py           # LangGraph 워크플로우 정의
├── routers.py             # FastAPI 라우터
├── schemas.py             # Pydantic 스키마
├── responses.py           # API 응답 모델
├── enums.py               # 열거형 (Intent, NodeName)
└── node/                  # 워크플로우 노드
    ├── analyze_intent_node.py
    ├── generate_guide_node.py
    ├── recommend_cody_node.py
    └── generation_todays_pick_node.py
```

## 🔄 워크플로우 구조

```
[사용자 입력]
    ↓
[analyze_intent] → 인텐트 분석
    ↓
    ├─→ [generate_guide] → 일반 대화 응답 → END
    └─→ [recommend_cody] → 코디 추천
            ↓
        [generate_todays_pick] → 이미지 생성 → END
```

### 노드 설명

| 노드 | 기능 | LLM 사용 | 메시지 저장 |
|------|------|---------|------------|
| `analyze_intent` | 사용자 의도 분석 (JSON) | ✅ | ❌ (내부 처리) |
| `generate_guide` | 일반 대화 응답 생성 | ✅ | ✅ |
| `recommend_cody` | 코디 추천 서비스 호출 | ❌ (서비스) | ✅ |
| `generate_todays_pick` | 이미지 생성 | ❌ (이미지 생성) | ✅ |

## 💾 데이터 모델

### PostgreSQL 모델

#### `ChatSession`
```python
- session_id: Integer (PK)
- user_id: UUID (FK → users.id)
- session_summary: Text (Long-term memory)
- finished_at: DateTime (세션 종료 시간)
- created_at: DateTime (자동 생성)
- messages: relationship (ChatMessage, order_by=created_at.asc())
```

#### `ChatMessage`
```python
- message_id: Integer (PK)
- session_id: Integer (FK → chat_sessions.session_id)
- sender: String ('USER' | 'AGENT')
- content: Text (메시지 내용)
- node_name: String (어떤 노드에서 생성된 메시지인지)
- metadata: JSONB (노드별 메타데이터)
- created_at: DateTime (자동 생성, 순서 보장)
```

### Cosmos DB 문서 구조

#### `chat_states` 컨테이너
```json
{
  "id": "session_id",
  "user_query": "코디 추천해줘",
  "context": {
    "user_id": "uuid",
    "intent": "recommend_cody",
    "tpo": "데이트",
    "intent_reason": "사용자가 코디 추천을 요청함",
    "is_pick_updated": true,
    "lat": 37.5665,
    "lon": 126.9780
  },
  "response": "코디를 추천해드립니다...",
  "recommendations": [...],
  "todays_pick": {
    "id": "uuid",
    "image_url": "https://...",
    "items": {...}
  },
  "current_node": "generate_todays_pick"
}
```

**주의:** `messages` 필드는 포함하지 않음 (PostgreSQL에만 저장)

## 🔧 주요 컴포넌트

### 1. `NoSqlClient` (`app/infra/clients/nosql-client.py`)

Azure Cosmos DB 클라이언트 래퍼.

```python
class NoSqlClient:
    def get_container(container_name: str, database_name: Optional[str] = None) -> ContainerProxy
    def get_db() -> DatabaseProxy
    def close() -> None
```

**특징:**
- 여러 컨테이너 사용 가능 (컬렉션 개념)
- `container_name` 필수 파라미터
- Config에서 기본 database 가져옴

### 2. `ChatStateStore` (`stores.py`)

Cosmos DB에 워크플로우 상태 저장/조회.

```python
class ChatStateStore:
    async def create_state(session_id: int, state: ChatState) -> ChatState
    async def get_state(session_id: int) -> Optional[ChatState]
    async def update_state(session_id: int, state: ChatState) -> ChatState
```

**사용 컨테이너:** `chat_states`

### 3. `ChatService` (`services.py`)

비즈니스 로직 처리.

#### 주요 메서드

**`send_message()`**
- 세션 확인/생성
- 사용자 메시지 저장
- 워크플로우 실행
- 노드별 상태 저장 (Cosmos DB)
- 노드별 메시지 저장 (PostgreSQL)

**`_save_user_message()`**
- 사용자 메시지를 PostgreSQL에 저장
- `sender='USER'`, `node_name=None`

**`_save_agent_message()`**
- 노드가 생성한 실제 응답만 저장
- `state["response"]`가 있을 때만 저장
- `metadata`에 노드별 데이터 포함

### 4. `ChatWorkflow` (`workflows.py`)

LangGraph 워크플로우 정의.

```python
class ChatWorkflow:
    def _create_compiled_chat_workflow() -> CompiledStateGraph
    @staticmethod
    def route_intent_after_analyze(state: ChatState) -> str
```

**경로 분기:**
- `intent == "RECOMMEND"` → `recommend_cody` 노드
- 그 외 → `generate_guide` 노드

## 📊 데이터 흐름

### 시나리오: 사용자가 "코디 추천해줘" 입력

#### Step 1: 세션 확인
```python
# PostgreSQL 조회
active_session = db.query(ChatSession).filter(
    user_id=user.id,
    finished_at=None
).first()
```

#### Step 2: 상태 로드
```python
# Cosmos DB에서 상태 로드
state = await get_chat_state_store().get_state(session_id)
```

#### Step 3: 사용자 메시지 저장
```python
# PostgreSQL
ChatMessage(
    session_id=1,
    sender="USER",
    content="코디 추천해줘",
    created_at="2026-01-28 10:01:00"
)
```

#### Step 4: 워크플로우 실행

**노드 1: analyze_intent**
```python
# LLM 호출 → JSON 파싱
state["context"]["intent"] = "recommend_cody"
state["context"]["intent_reason"] = "사용자가 코디 추천을 요청함"

# Cosmos DB 상태 업데이트
await update_state(session_id, state)

# 메시지 저장 안 함 (내부 처리)
```

**노드 2: recommend_cody**
```python
# 서비스 호출
result = recommend_todays_pick_v2(...)
state["response"] = "코디를 추천해드립니다...\n추천 사유: {reasoning}"
state["todays_pick"] = result

# PostgreSQL 메시지 저장
ChatMessage(
    session_id=1,
    sender="AGENT",
    content="코디를 추천해드립니다...",  # LLM이 생성한 reasoning 포함
    node_name="recommend_cody",
    metadata={
        "intent": "recommend_cody",
        "todays_pick": {...},
        "intent_reason": "..."
    }
)

# Cosmos DB 상태 업데이트
await update_state(session_id, state)
```

**노드 3: generate_todays_pick**
```python
# 이미지 생성
state["todays_pick"]["image_url"] = "https://..."
state["response"] = "오늘의 픽 이미지를 생성했습니다."

# PostgreSQL 메시지 저장
ChatMessage(
    session_id=1,
    sender="AGENT",
    content="오늘의 픽 이미지를 생성했습니다.",
    node_name="generate_todays_pick",
    metadata={"todays_pick": {...}}
)

# Cosmos DB 상태 업데이트
await update_state(session_id, state)
```

## 🔑 핵심 설계 결정

### 1. 메시지 저장 전략

**모든 중간 메시지 저장 (권장)**
- 각 노드의 LLM 응답을 모두 저장
- 사용자가 대화 내역에서 전체 흐름 확인 가능
- 디버깅 및 모니터링 용이

**구현:**
- `analyze_intent`: 저장 안 함 (내부 처리)
- `generate_guide`: LLM 응답 저장
- `recommend_cody`: LLM reasoning 포함 응답 저장
- `generate_todays_pick`: 이미지 생성 완료 메시지 저장

### 2. 상태 저장 전략

**노드 실행마다 상태 저장**
- 각 노드 실행 후 Cosmos DB에 상태 업데이트
- 워크플로우 중단 시 마지막 상태 복구 가능
- `astream`을 사용하여 노드별 이벤트 캡처

### 3. 데이터 분리

**PostgreSQL (메시지)**
- 실제 대화 메시지
- `created_at`으로 자동 정렬
- ORM relationship 활용

**Cosmos DB (상태)**
- 워크플로우 실행 상태만
- `messages` 배열 제외 (문서 크기 제한)
- 빠른 읽기/쓰기

## 🎯 노드별 LLM 응답 처리

### `analyze_intent_node`
- **LLM 응답**: JSON 형태
- **State 저장**: `context`에 모든 필드 저장 (intent, tpo, intent_reason 등)
- **메시지 저장**: 안 함

### `generate_guide_node`
- **LLM 응답**: 일반 텍스트
- **State 저장**: `state["response"]`
- **메시지 저장**: ✅ `content`에 저장

### `recommend_cody_node`
- **LLM 응답**: 없음 (서비스 호출)
- **서비스 응답**: Dict (reasoning 포함)
- **State 저장**: `state["response"]`에 reasoning 포함, `state["todays_pick"]`에 전체 데이터
- **메시지 저장**: ✅ `content` + `metadata`

### `generation_todays_pick_node`
- **LLM 응답**: 없음 (이미지 생성)
- **State 저장**: `state["todays_pick"]` 업데이트, `state["response"]` 설정
- **메시지 저장**: ✅ 이미지 생성 완료 메시지

## 🔄 API 흐름

### Request
```http
POST /chat
{
  "query": "코디 추천해줘",
  "lat": 37.5665,
  "lon": 126.9780
}
```

### Response
```json
{
  "success": true,
  "response": "코디를 추천해드립니다...",
  "is_pick_updated": true,
  "recommendations": null,
  "todays_pick": {
    "id": "uuid",
    "image_url": "https://...",
    "items": {...}
  }
}
```

## 🛠️ 환경 변수

```env
# Azure Cosmos DB
AZURE_COSMOS_ENDPOINT=https://codify-nosql.documents.azure.com:443/
AZURE_COSMOS_KEY=<PRIMARY_KEY>
AZURE_COSMOS_DATABASE=codify
```

## 📝 주요 개선 사항

1. ✅ **Cosmos DB 클라이언트 구현**
   - 여러 컨테이너 지원
   - Config 기반 설정

2. ✅ **하이브리드 저장소 구조**
   - PostgreSQL: 메시지
   - Cosmos DB: 상태

3. ✅ **노드별 메시지 저장**
   - 모든 노드의 LLM 응답 저장
   - 메타데이터 포함

4. ✅ **상태 복구 가능**
   - 노드 실행마다 상태 저장
   - 워크플로우 중단 시 복구

5. ✅ **메시지 순서 보장**
   - PostgreSQL `created_at` 정렬
   - ORM relationship 활용

## 🚀 향후 개선 사항

1. **에러 처리 강화**
   - 노드 실행 중 예외 발생 시 상태 저장 보장
   - 재시도 로직

2. **성능 최적화**
   - 메시지 페이지네이션
   - 상태 캐싱

3. **모니터링**
   - 노드별 실행 시간 추적
   - 메시지 저장 실패 알림
