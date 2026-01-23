from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password, create_access_token


def get_user_by_username(db: Session, username: str):
    """아이디로 유저 찾기"""
    return db.query(User).filter(User.username == username).first()


def register_user(db: Session, user_data: UserCreate):
    """회원가입 로직"""
    print(f"Registering user with password: {user_data.password}")
    hashed_pw = hash_password(user_data.password)
    new_user = User(username=user_data.username, hashed_password=hashed_pw)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def authenticate_user(db: Session, user_data: UserCreate):
    """로그인 인증 로직"""
    user = get_user_by_username(db, user_data.username)
    if not user:
        return False
    if not verify_password(user_data.password, user.hashed_password):
        return False
    return user


def authenticate_user(db: Session, user_data: UserCreate):
    """로그인 인증 및 토큰 발급 로직"""
    user = get_user_by_username(db, user_data.username)
    if not user:
        return False
    if not verify_password(user_data.password, user.hashed_password):
        return False
    token = create_access_token(data={"sub": user.username})
    return token
