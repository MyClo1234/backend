from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from app.core.config import Config
from app.core.security import ALGORITHM, SECRET_KEY
from app.domains.generation.schema import (
    OutfitGenerationRequest,
    OutfitGenerationResponse,
)
from app.domains.generation.service import generation_service
from app.utils.response_helpers import create_success_response, handle_route_exception

generation_router = APIRouter()
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


@generation_router.post("/generation/outfit", response_model=OutfitGenerationResponse)
async def generate_outfit_image(
    request: OutfitGenerationRequest,
    user_id: UUID = Depends(get_user_id_from_token),
):
    """
    Generate an AI image of the outfit.
    """
    try:
        image_url = await generation_service.create_outfit_image(request, user_id)

        return create_success_response(
            {"image_url": image_url, "message": "Image generated successfully"}
        )
    except Exception as e:
        raise handle_route_exception(e)
