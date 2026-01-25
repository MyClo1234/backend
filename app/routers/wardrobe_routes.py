from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session
import json
import os
from uuid import UUID
from jose import JWTError, jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.security import ALGORITHM, SECRET_KEY
from app.services.wardrobe_manager import wardrobe_manager
from app.models.schemas import WardrobeResponse, WardrobeItemSchema, AttributesSchema
from app.models.wardrobe import ClosetItem
from app.database import get_db
from app.utils.response_helpers import create_success_response, handle_route_exception

wardrobe_router = APIRouter()
security = HTTPBearer()


def get_user_id_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UUID:
    """JWT 토큰에서 user_id를 추출하는 헬퍼 함수"""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id_str = payload.get("user_id")
        if user_id_str is None:
            raise credentials_exception
        return UUID(user_id_str)
    except (JWTError, ValueError) as e:
        raise credentials_exception


@wardrobe_router.get("/wardrobe/items", response_model=WardrobeResponse)
def get_wardrobe_items(category: Optional[str] = Query(None)):
    """Get all wardrobe items"""
    try:
        items = wardrobe_manager.load_items()

        if category:
            filtered = []
            for item in items:
                item_category = (
                    item.get("attributes", {}).get("category", {}).get("main", "")
                )
                if item_category == category.lower():
                    filtered.append(item)
            items = filtered

        return create_success_response(
            {"items": items},
            count=len(items),
            total_count=total_count,
            has_more=has_more,
        )
    except Exception as e:
        raise handle_route_exception(e)


@wardrobe_router.get(
    "/wardrobe/users/me/images",
    response_model=WardrobeResponse,
    summary="내 옷장 이미지 목록 조회",
    description="현재 로그인한 사용자의 모든 옷장 아이템 이미지 목록을 조회합니다. 토큰에서 자동으로 user_id를 추출합니다.",
)
def get_my_wardrobe_images(
    category: Optional[str] = Query(
        None, description="Category filter (e.g. top, bottom)"
    ),
    skip: int = Query(0, ge=0, description="Number of items to skip (pagination)"),
    limit: int = Query(20, ge=1, le=100, description="Max number of items to return"),
    user_id: UUID = Depends(get_user_id_from_token),
    db: Session = Depends(get_db),
):
    """
    Get all wardrobe images for the current user (from token)
    """
    try:
        result = wardrobe_manager.get_user_wardrobe_items(
            db=db, user_id=user_id, category=category, skip=skip, limit=limit
        )
        return create_success_response(
            {"items": result["items"]},
            count=result["count"],
            total_count=result["total_count"],
            has_more=result["has_more"],
        )
    except Exception as e:
        raise handle_route_exception(e)


@wardrobe_router.get(
    "/wardrobe/items/{item_id}",
    response_model=WardrobeItemSchema,
    summary="옷장 아이템 상세 조회",
    description="옷장 아이템의 상세 정보를 조회합니다. Blob Storage의 JSON 메타데이터를 포함합니다.",
)
def get_wardrobe_item_detail(
    item_id: str,
    user_id: UUID = Depends(get_user_id_from_token),
    db: Session = Depends(get_db),
):
    """
    Get generic wardrobe item details
    """
    try:
        return wardrobe_manager.get_item_detail(db=db, item_id=item_id, user_id=user_id)
    except HTTPException:
        raise
    except Exception as e:
        raise handle_route_exception(e)
