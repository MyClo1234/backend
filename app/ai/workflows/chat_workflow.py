"""
채팅 랭그래프 워크플로우 정의
"""

from app.ai.nodes.chat_nodes import get_chat_workflow


# 래퍼 함수 (도메인 서비스에서 사용하기 편하도록)
async def process_chat(user_id: str, query: str):
    workflow = get_chat_workflow()

    # 초기 상태
    initial_state = {
        "messages": [],
        "user_query": query,
        "context": {"user_id": user_id, "is_pick_updated": False},
        "response": None,
        "recommendations": None,
    }

    return await workflow.ainvoke(initial_state)
