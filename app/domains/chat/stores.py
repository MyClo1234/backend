from typing import Optional
import asyncio

from app.domains.chat.states import ChatState
from app.infra.clients import get_nosql_client

from azure.cosmos import ContainerProxy


class ChatStateStore:
    def __init__(self):
        self.container: ContainerProxy = get_nosql_client().get_container("chat_states")

    async def create_state(self, session_id: int, state: ChatState) -> ChatState:
        """새 상태 생성 (이미 존재하면 업데이트)"""
        item = dict(state)
        item["id"] = str(session_id)
        # upsert_item을 사용하여 이미 존재하면 업데이트, 없으면 생성
        await asyncio.to_thread(self.container.upsert_item, item)
        return state

    async def get_state(self, session_id: int) -> Optional[ChatState]:
        """상태 조회"""
        try:
            item = await asyncio.to_thread(
                self.container.read_item,
                item=str(session_id),
                partition_key=str(session_id)
            )
            # id 필드 제거하고 ChatState로 변환
            item.pop("id", None)
            return ChatState(item)
        except Exception:
            return None

    async def update_state(self, session_id: int, state: ChatState) -> ChatState:
        """상태 업데이트 (upsert)"""
        item = dict(state)
        item["id"] = str(session_id)
        await asyncio.to_thread(self.container.upsert_item, item)
        return state


chat_state_store = ChatStateStore()


def get_chat_state_store() -> ChatStateStore:
    return chat_state_store
