"""
채팅 도메인 라우터
"""

import logging
from fastapi import APIRouter, Depends

from app.domains.user.router import get_current_user
from app.domains.user.model import User
from app.domains.chat.services import get_chat_service
from app.domains.chat.workflows import get_chat_workflow
from app.domains.chat.responses import SendMessageResponse
from app.domains.chat.schemas import ChatRequest

logger = logging.getLogger(__name__)

chat_router = APIRouter()


@chat_router.post("/chat", response_model=SendMessageResponse)
async def send_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    service=Depends(get_chat_service),
    workflow=Depends(get_chat_workflow),
):
    """사용자 메시지를 처리하고 응답을 반환합니다."""
    result = await service.send_message(request, current_user, workflow)

    return SendMessageResponse(
        success=True,
        response=result.get("response"),
        is_pick_updated=result.get("context", {}).get("is_pick_updated", False),
        recommendations=result.get("recommendations"),
        todays_pick=result.get("todays_pick"),
    )
