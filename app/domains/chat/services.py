from uuid import UUID
from typing import Optional

from fastapi import Depends
from sqlalchemy.orm import Session

from app.domains.chat.states import ChatState
from app.domains.chat.workflows import get_chat_workflow
from app.domains.chat.schemas import ChatRequest
from langgraph.graph.state import CompiledStateGraph
from app.domains.chat.models import ChatSession, ChatMessage
from app.domains.user.model import User
from app.domains.chat.stores import get_chat_state_store
from app.utils.langsmith_helper import get_langsmith_config

from app.database import get_db


class ChatService:
    def __init__(self, workflow: CompiledStateGraph, db: Session):
        self.workflow = workflow
        # LangSmith 기본 설정 (공통 부분만)
        self._base_langsmith_config = get_langsmith_config(
            project_name="My First App",
            tags=["chat", "workflow"],
        )
        self.db = db

    async def send_message(
        self,
        request: ChatRequest,
        current_user: User,
    ) -> ChatState:
        # 진행중인 채팅 세션이 있는지 확인
        active_session = self._get_active_chat_session(current_user.id)

        # 기존 채팅 세션이 있으면
        if active_session:
            session_id = active_session.session_id
            state = await get_chat_state_store().get_state(session_id=session_id)
            if state is None:
                # Cosmos에 상태가 없으면 새로 생성
                state = self._create_initial_state(request, current_user)
                await get_chat_state_store().create_state(session_id, state)
        else:
            # 기존 채팅 세션이 없으면
            # 새 상태 정의
            state = self._create_initial_state(request, current_user)
            # 새 채팅 세션 생성 (session_id는 DB에서 자동 생성)
            new_session = ChatSession(
                user_id=current_user.id,
                session_summary=None,
                finished_at=None,
            )
            self.db.add(new_session)
            self.db.commit()  # session_id 자동 생성됨
            session_id = new_session.session_id
            # 상태 저장
            await get_chat_state_store().create_state(session_id, state)

        # 사용자 메시지 저장 (PostgreSQL)
        self._save_user_message(self.db, session_id, request.query)

        # LangSmith tracing 설정 (동적 값 추가)
        langsmith_config = {
            **self._base_langsmith_config,
            "configurable": {
                **self._base_langsmith_config.get("configurable", {}),
                "thread_id": f"session-{session_id}",
            },
            "metadata": {
                "session_id": session_id,
                "user_id": str(current_user.id),
                "query": request.query,
            },
        }

        # workflow를 실행할 때 마다 State를 업데이트하고 메시지 저장
        # astream은 {node_name: state} 형태의 딕셔너리를 yield
        final_state = state
        async for event_dict in self.workflow.astream(state, config=langsmith_config):
            # event_dict는 {node_name: state} 형태
            for node_name, node_state in event_dict.items():
                final_state = node_state
                final_state["current_node"] = node_name

                # 노드별 응답 메시지 저장 (PostgreSQL)
                self._save_agent_message(self.db, session_id, final_state, node_name)

                # 상태 업데이트 (Cosmos DB - messages 제외, 워크플로우 상태만)
                await get_chat_state_store().update_state(session_id, final_state)

        return final_state

    def _get_active_chat_session(self, user_id: UUID) -> Optional[ChatSession]:
        return (
            self.db.query(ChatSession)
            .filter(
                ChatSession.user_id == user_id,
                ChatSession.finished_at.is_(None),
            )
            .order_by(ChatSession.created_at.desc())
            .first()
        )

    def _create_initial_state(
        self, request: ChatRequest, current_user: User
    ) -> ChatState:
        return ChatState(
            user_query=request.query,
            response=None,
            recommendations=None,
            todays_pick=None,
            current_node=None,
            context={
                "user_id": str(current_user.id),
                "is_pick_updated": False,
                "lat": request.lat,
                "lon": request.lon,
            },
        )

    def _save_user_message(self, db: Session, session_id: int, content: str) -> None:
        """사용자 메시지 저장"""
        message = ChatMessage(
            session_id=session_id,
            sender="USER",
            content=content,
            node_name=None,
            message_metadata=None,
        )
        db.add(message)
        db.commit()

    def _save_agent_message(
        self, db: Session, session_id: int, state: ChatState, node_name: str
    ) -> None:
        """에이전트(노드) 메시지 저장 - 노드가 생성한 실제 데이터만 저장"""
        # 내부 처리 노드는 메시지 저장 안 함
        if node_name == "analyze_intent":
            return

        # 노드가 실제로 생성한 response만 사용 (임의 메시지 생성 안 함)
        content = state.get("response")
        if not content:
            # response가 없으면 메시지 저장 안 함 (노드가 생성한 데이터가 없음)
            return

        # 노드가 생성한 실제 데이터를 메타데이터로 저장
        metadata = {}
        context = state.get("context", {})

        # 공통 메타데이터 (노드가 설정한 값만)
        if context.get("intent"):
            metadata["intent"] = context.get("intent")
        if context.get("tpo"):
            metadata["tpo"] = context.get("tpo")
        if context.get("intent_reason"):
            metadata["intent_reason"] = context.get("intent_reason")

        # 노드가 생성한 실제 데이터
        if state.get("todays_pick"):
            metadata["todays_pick"] = state.get("todays_pick")

        if state.get("recommendations"):
            metadata["recommendations"] = state.get("recommendations")

        # 노드가 생성한 실제 응답만 저장
        message = ChatMessage(
            session_id=session_id,
            sender="AGENT",
            content=content,  # 노드가 생성한 response
            node_name=node_name,
            message_metadata=metadata if metadata else None,
        )
        db.add(message)
        db.commit()


async def get_chat_service(
    workflow: CompiledStateGraph = Depends(get_chat_workflow),
    db: Session = Depends(get_db),
) -> ChatService:
    return ChatService(workflow=workflow, db=db)
