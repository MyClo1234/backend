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


def get_user_id_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> UUID:
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
                item_category = item.get("attributes", {}).get("category", {}).get("main", "")
                if item_category == category.lower():
                    filtered.append(item)
            items = filtered
        
        return create_success_response(
            {"items": items},
            count=len(items)
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
    user_id: UUID = Depends(get_user_id_from_token),
    db: Session = Depends(get_db),
):
    """
    Get all wardrobe images for the current user (from token)
    
    - **Authorization**: Bearer Token (필수) - 토큰에서 자동으로 user_id 추출
    """
    return get_user_wardrobe_images_internal(user_id, db)


@wardrobe_router.get(
    "/wardrobe/users/{user_id}/images",
    response_model=WardrobeResponse,
    summary="사용자별 옷장 이미지 목록 조회",
    description="특정 사용자의 모든 옷장 아이템 이미지 목록을 조회합니다. Azure Blob Storage에서 이미지 URL을 가져옵니다.",
)
def get_user_wardrobe_images(
    user_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Get all wardrobe images for a specific user
    
    - **user_id**: 조회할 사용자 ID (UUID 형식, 예: 550e8400-e29b-41d4-a716-446655440000)
    """
    return get_user_wardrobe_images_internal(user_id, db)


def get_user_wardrobe_images_internal(
    user_id: UUID,
    db: Session,
) -> dict:
    """내부 함수: 사용자별 옷장 이미지 목록 조회 로직"""
    try:
        # 데이터베이스에서 해당 사용자의 모든 ClosetItem 조회
        closet_items = db.query(ClosetItem).filter(ClosetItem.user_id == user_id).all()
        
        if not closet_items:
            # 사용자는 있지만 옷장이 비어있는 경우 빈 배열 반환
            return create_success_response(
                {"items": []},
                count=0
            )
        
        # ClosetItem을 WardrobeItemSchema 형식으로 변환
        items: List[WardrobeItemSchema] = []
        
        for item in closet_items:
            # image_path에서 blob_name 추출
            # image_path 형식: https://{account}.blob.core.windows.net/{container}/{blob_name}
            image_path = item.image_path
            blob_name = None
            
            # URL에서 blob_name 추출
            if ".blob.core.windows.net/" in image_path:
                # URL 형식인 경우
                parts = image_path.split(".blob.core.windows.net/")
                if len(parts) > 1:
                    container_and_blob = parts[1]
                    # container_name/ 이후 부분이 blob_name
                    container_prefix = f"{wardrobe_manager.container_name}/"
                    if container_and_blob.startswith(container_prefix):
                        blob_name = container_and_blob[len(container_prefix):]
            
            # Blob Storage에서 JSON 파일 읽기 시도
            attributes: Dict[str, Any] = {}
            
            if blob_name and wardrobe_manager.container_client:
                try:
                    # blob_name에서 확장자 제거하여 base_id 얻기
                    # 예: "attributes_20241223_123456_7890.jpg" -> "attributes_20241223_123456_7890"
                    base_id = os.path.splitext(blob_name)[0]
                    json_blob_name = f"{base_id}.json"
                    
                    # JSON 파일 다운로드
                    json_client = wardrobe_manager.container_client.get_blob_client(json_blob_name)
                    if json_client.exists():
                        json_content = json_client.download_blob().readall()
                        attributes = json.loads(json_content)
                except Exception as e:
                    # JSON 파일을 읽을 수 없는 경우 features 사용
                    print(f"Warning: Could not load JSON for item {item.id}: {e}")
                    attributes = item.features or {}
            else:
                # blob_name을 추출할 수 없거나 container_client가 없는 경우 features 사용
                attributes = item.features or {}
            
            # features에 category, sub_category, season, mood_tags 추가 (DB 컬럼에서)
            if not attributes.get("category"):
                # category가 없으면 DB의 category 사용
                attributes["category"] = {
                    "main": item.category.lower() if item.category else "unknown",
                    "sub": item.sub_category.lower() if item.sub_category else "",
                    "confidence": 1.0
                }
            
            if item.season:
                attributes["season"] = item.season
            
            if item.mood_tags:
                attributes["mood_tags"] = item.mood_tags
            
            # AttributesSchema로 변환 시도 (필요한 필드가 없으면 기본값 사용)
            try:
                # 필수 필드가 있는지 확인하고 없으면 기본값 추가
                if "category" not in attributes or not isinstance(attributes["category"], dict):
                    attributes["category"] = {
                        "main": item.category.lower() if item.category else "unknown",
                        "sub": item.sub_category.lower() if item.sub_category else "",
                        "confidence": 1.0
                    }
                
                # 다른 필수 필드들도 확인
                required_fields = ["color", "pattern", "material", "fit", "details", "scores", "meta"]
                for field in required_fields:
                    if field not in attributes:
                        # 기본값 설정
                        if field == "color":
                            attributes[field] = {"primary": "unknown", "secondary": [], "tone": "neutral", "confidence": 0.0}
                        elif field == "pattern":
                            attributes[field] = {"type": "solid", "confidence": 0.0}
                        elif field == "material":
                            attributes[field] = {"guess": "unknown", "confidence": 0.0}
                        elif field == "fit":
                            attributes[field] = {"type": "regular", "confidence": 0.0}
                        elif field == "details":
                            attributes[field] = {"neckline": "", "sleeve": "", "length": "", "closure": [], "print_or_logo": False}
                        elif field == "scores":
                            attributes[field] = {"formality": 0.5, "warmth": 0.5, "season": item.season or [], "versatility": 0.5}
                        elif field == "meta":
                            attributes[field] = {"is_layering_piece": False, "notes": None}
                
                if "style_tags" not in attributes:
                    attributes["style_tags"] = []
                
                if "confidence" not in attributes:
                    attributes["confidence"] = 0.0
                
                # AttributesSchema 생성
                attributes_schema = AttributesSchema(**attributes)
            except Exception as e:
                # AttributesSchema 변환 실패 시 features를 그대로 사용 (Dict)
                print(f"Warning: Could not convert attributes to AttributesSchema for item {item.id}: {e}")
                # 기본 구조로 재시도
                attributes_schema = AttributesSchema(
                    category={"main": item.category.lower() if item.category else "unknown", "sub": item.sub_category.lower() if item.sub_category else "", "confidence": 1.0},
                    color=attributes.get("color", {"primary": "unknown", "secondary": [], "tone": "neutral", "confidence": 0.0}),
                    pattern=attributes.get("pattern", {"type": "solid", "confidence": 0.0}),
                    material=attributes.get("material", {"guess": "unknown", "confidence": 0.0}),
                    fit=attributes.get("fit", {"type": "regular", "confidence": 0.0}),
                    details=attributes.get("details", {"neckline": "", "sleeve": "", "length": "", "closure": [], "print_or_logo": False}),
                    style_tags=attributes.get("style_tags", []),
                    scores=attributes.get("scores", {"formality": 0.5, "warmth": 0.5, "season": item.season or [], "versatility": 0.5}),
                    meta=attributes.get("meta", {"is_layering_piece": False, "notes": None}),
                    confidence=attributes.get("confidence", 0.0)
                )
            
            # WardrobeItemSchema 생성
            wardrobe_item = WardrobeItemSchema(
                id=str(item.id),
                filename=blob_name.split("/")[-1] if blob_name and "/" in blob_name else (image_path.split("/")[-1] if "/" in image_path else f"item_{item.id}"),
                attributes=attributes_schema,
                image_url=image_path,  # 이미 Blob Storage URL
            )
            items.append(wardrobe_item)
        
        return create_success_response(
            {"items": items},
            count=len(items)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise handle_route_exception(e)
