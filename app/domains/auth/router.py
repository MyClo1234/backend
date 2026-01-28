from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.domains.user.schema import UserCreate, UserResponse
from .schema import UserLogin, AuthResponse
from .service import register_user, authenticate_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post(
    "/signup",
    response_model=AuthResponse,
    summary="회원가입",
    description="새로운 사용자를 등록합니다. 사용자 정보(아이디, 비밀번호, 나이, 신체 사이즈 등)를 입력받아 DB에 저장하고, 바로 사용할 수 있는 JWT 토큰을 반환합니다.",
)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    # auth_service에서 처리하고 결과 반환
    return register_user(db, user_data)


@router.post(
    "/login",
    response_model=AuthResponse,
    summary="로그인",
    description="아이디와 비밀번호를 검증하여 유효한 JWT 액세스 토큰을 발급합니다. 토큰은 이후 인증이 필요한 요청 헤더에 포함되어야 합니다.",
)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    result = authenticate_user(db, user_data)
    if not result:
        raise HTTPException(
            status_code=401, detail="아이디 또는 비밀번호가 잘못되었습니다."
        )
    return result


@router.post(
    "/logout",
    summary="로그아웃",
    description="현재 사용자를 로그아웃 처리합니다. 서버 측에서는 특별한 작업이 없으며, 클라이언트가 가지고 있는 토큰을 삭제하면 됩니다.",
)
def logout():
    return {"success": True, "message": "Successfully logged out"}
