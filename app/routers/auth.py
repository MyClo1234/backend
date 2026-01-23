from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserCreate, UserResponse  # (schemas 단계에서 만든 것)
from app.services import auth_service  # (services 단계에서 만든 것)

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signup", response_model=UserResponse, operation_id="auth_signup")
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    # 이미 존재하는 유저인지 확인
    existing_user = auth_service.get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 아이디입니다.")
    return auth_service.register_user(db, user_data)


@router.post("/login", operation_id="auth_login")
def login(user_data: UserCreate, db: Session = Depends(get_db)):
    token = auth_service.authenticate_user(db, user_data)
    if not token:
        raise HTTPException(
            status_code=401,
            detail="아이디 또는 비밀번호가 일치하지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return {"access_token": token, "token_type": "bearer"}
