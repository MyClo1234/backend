from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserUpdate, UserResponse
from app.services import user_service
from app.core.security import ALGORITHM, SECRET_KEY, verify_password
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from app.models.user import User

router = APIRouter(prefix="/users", tags=["Users"])

# 토큰 인증을 위한 스키마
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.user_name == username).first()
    if user is None:
        raise credentials_exception
    return user


@router.put(
    "/profile",
    response_model=UserResponse,
    summary="회원정보 수정",
    description="로그인한 사용자의 프로필(키, 몸무게, 성별, 체형)을 수정합니다.",
)
def update_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    updated_user = user_service.update_user_profile(db, current_user.id, update_data)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user


@router.get(
    "/me",
    response_model=UserResponse,
    summary="내 정보 조회",
    description="현재 로그인한 사용자의 정보를 조회합니다.",
)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user
