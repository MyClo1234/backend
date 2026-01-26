"""
LangGraph workflow nodes for Today's Pick auto-generation.
"""

import json
import logging
from typing import Dict
from datetime import date
from sqlalchemy.orm import Session

from langchain_openai import AzureChatOpenAI
from app.core.config import Config
from app.ai.clients.nano_banana_client import NanoBananaClient
from app.llm.todays_pick_state import TodaysPickState
from app.llm.todays_pick_prompts import RECOMMENDATION_PROMPT, format_item_list
from app.domains.recommendation.model import TodaysPick

logger = logging.getLogger(__name__)


def recommend_outfit_node(state: TodaysPickState) -> TodaysPickState:
    """
    LLM을 사용하여 최적 조합 추천.
    """
    logger.info(f"Starting outfit recommendation for user {state['user_id']}")

    try:
        # Prepare prompt
        weather = state["weather"]
        tops_list = format_item_list(state["tops"])
        bottoms_list = format_item_list(state["bottoms"])

        prompt = RECOMMENDATION_PROMPT.format(
            weather_summary=weather.get("summary", "정보 없음"),
            temp_min=weather.get("temp_min", "?"),
            temp_max=weather.get("temp_max", "?"),
            tops_list=tops_list,
            bottoms_list=bottoms_list,
        )

        # Call LLM
        llm = AzureChatOpenAI(
            azure_deployment=Config.AZURE_OPENAI_DEPLOYMENT_NAME,
            api_version=Config.AZURE_OPENAI_API_VERSION,
            temperature=0.7,
            max_tokens=500,
        )

        response = llm.invoke(prompt)
        result_text = response.content.strip()

        # Parse JSON
        # Remove markdown code blocks if present
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        result = json.loads(result_text)

        # Find selected items
        top_id = result["top_id"]
        bottom_id = result["bottom_id"]

        selected_top = next(
            (t for t in state["tops"] if str(t["id"]) == str(top_id)), None
        )
        selected_bottom = next(
            (b for b in state["bottoms"] if str(b["id"]) == str(bottom_id)), None
        )

        if not selected_top or not selected_bottom:
            raise ValueError(
                f"Selected items not found in wardrobe: top={top_id}, bottom={bottom_id}"
            )

        # Update state
        return {
            **state,
            "selected_top": selected_top,
            "selected_bottom": selected_bottom,
            "reasoning": result["reasoning"],
            "score": float(result["score"]),
        }

    except Exception as e:
        logger.error(f"Recommendation error: {e}")
        return {
            **state,
            "error": f"Recommendation failed: {str(e)}",
        }


def generate_composite_image_node(state: TodaysPickState) -> TodaysPickState:
    """
    Nano Banana API를 사용하여 마네킹 합성 이미지 생성.
    """
    logger.info("Starting image composite generation")

    if state.get("error"):
        logger.warning("Skipping image generation due to previous error")
        return state

    try:
        top = state["selected_top"]
        bottom = state["selected_bottom"]

        # Get image URLs
        top_url = top.get("image_url") or top.get("image_path")
        bottom_url = bottom.get("image_url") or bottom.get("image_path")

        if not top_url or not bottom_url:
            raise ValueError("Missing image URLs for selected items")

        # Call Nano Banana
        client = NanoBananaClient()
        composite_url = client.generate_mannequin_composite(
            top_image_url=top_url, bottom_image_url=bottom_url
        )

        return {
            **state,
            "composite_image_url": composite_url,
        }

    except Exception as e:
        logger.error(f"Image generation error: {e}")
        return {
            **state,
            "error": f"Image generation failed: {str(e)}",
        }


def save_to_db_node(state: TodaysPickState, db: Session) -> TodaysPickState:
    """
    생성된 추천 데이터를 DB에 저장.
    """
    logger.info("Saving Today's Pick to database")

    if state.get("error"):
        logger.warning("Skipping DB save due to previous error")
        return state

    try:
        from uuid import UUID

        user_id = UUID(state["user_id"])

        # Deactivate existing picks for today
        today = date.today()
        db.query(TodaysPick).filter(
            TodaysPick.user_id == user_id,
            TodaysPick.date == today,
            TodaysPick.is_active == True,
        ).update({"is_active": False})

        # Create new pick
        new_pick = TodaysPick(
            user_id=user_id,
            date=today,
            top_item_id=str(state["selected_top"]["id"]),
            bottom_item_id=str(state["selected_bottom"]["id"]),
            image_url=state["composite_image_url"],
            reasoning=state["reasoning"],
            score=state["score"],
            weather_snapshot=state["weather"],
            is_active=True,
        )

        db.add(new_pick)
        db.commit()
        db.refresh(new_pick)

        logger.info(f"Saved Today's Pick with ID: {new_pick.id}")

        return state

    except Exception as e:
        db.rollback()
        logger.error(f"DB save error: {e}")
        return {
            **state,
            "error": f"DB save failed: {str(e)}",
        }
