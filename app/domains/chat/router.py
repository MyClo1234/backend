"""
채팅 도메인 라우터
"""

import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.domains.user.router import get_current_user
from app.domains.user.model import User
from app.ai.workflows.chat_workflow import get_chat_workflow
from app.ai.schemas.workflow_state import ChatState
from .schema import ChatRequest

logger = logging.getLogger(__name__)

chat_router = APIRouter()


@chat_router.post("/chat")
async def send_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """사용자 메시지를 처리하고 응답을 반환합니다."""

    # 초기 상태 설정
    initial_state: ChatState = {
        "messages": [],  # 히스토리는 나중에 구현
        "user_query": request.query,
        "context": {
            "user_id": str(current_user.id),
            "is_pick_updated": False,
            "lat": request.lat,
            "lon": request.lon,
        },
        "response": None,
        "recommendations": None,
        "todays_pick": None,
    }

    try:
        workflow = get_chat_workflow()
        final_state = await workflow.ainvoke(initial_state)

        return {
            "success": True,
            "response": final_state.get("response"),
            "is_pick_updated": final_state.get("context", {}).get(
                "is_pick_updated", False
            ),
            "recommendations": final_state.get("recommendations"),
            "todays_pick": final_state.get("todays_pick"),
        }

    except Exception as e:
        logger.error(f"Chat processing error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="메시지를 처리하는 중 오류가 발생했습니다."
        )
