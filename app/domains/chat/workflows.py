"""
채팅 랭그래프 워크플로우 정의
"""

from langgraph.graph import StateGraph, END
from langgraph.graph.state import CompiledStateGraph

from app.domains.chat.states import ChatState
from app.domains.chat.node.analyze_intent_node import analyze_intent_node
from app.domains.chat.node.generate_guide_node import generate_guide_node
from app.domains.chat.node.recommend_cody_node import recommend_cody_node
from app.domains.chat.node.generation_todays_pick_node import (
    generation_todays_pick_node,
)
from app.domains.chat.enums import Intent


class ChatWorkflow:
    def __init__(self):
        self._compiled_workflow = self._create_compiled_chat_workflow()

    def get_compiled_workflow(self):
        return self._compiled_workflow

    def _create_compiled_chat_workflow(
        self,
    ) -> CompiledStateGraph[ChatState, None, ChatState, ChatState]:
        """채팅 워크플로우 생성"""
        workflow = StateGraph(ChatState)

        # workflow 노드 추가
        workflow.add_node("analyze_intent", analyze_intent_node)
        workflow.add_node("generate_guide", generate_guide_node)
        workflow.add_node("recommend_cody", recommend_cody_node)
        workflow.add_node("generate_todays_pick", generation_todays_pick_node)

        # analyze intent 노드 이후 흐름 설정
        workflow.set_entry_point("analyze_intent")
        workflow.add_conditional_edges(
            "analyze_intent",  # 분기 시작점
            ChatWorkflow.route_intent_after_analyze,  # 분기 시작점 노드의 결과를 받아서 경로 결정하는 함수
            # 분기 경로 매핑
            {
                "generate_guide": "generate_guide",  # 분기 1번 경로
                "recommend_cody": "recommend_cody",  # 분기 2번 경로
            },
        )

        # 1. Guide flow: Generate Guide -> End
        workflow.add_edge("generate_guide", END)

        # 2. Recommendation flow: Recommend -> Generate Today's Pick -> End
        workflow.add_edge("recommend_cody", "generate_todays_pick")
        workflow.add_edge("generate_todays_pick", END)

        return workflow.compile()

    @staticmethod
    def route_intent_after_analyze(state: ChatState) -> str:
        """인텐트에 따라 경로 결정"""
        if state["context"].get("intent") == Intent.RECOMMEND_CODY.value:
            return "recommend_cody"
        return "generate_guide"


chatWorkflow = ChatWorkflow()


async def get_chat_workflow():
    return chatWorkflow.get_compiled_workflow()
