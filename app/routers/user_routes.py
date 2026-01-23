import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserUpdate, UserResponse
from app.services import user_service
from app.core.security import ALGORITHM, SECRET_KEY
from jose import JWTError, jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])

# Bearer 토큰 인증을 위한 스키마 (Swagger UI에서 직접 토큰 입력 가능)
# auto_error=True로 설정하여 Swagger UI가 자동으로 Authorization 헤더를 요구하도록 함
bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme), 
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Azure Functions에서도 보이도록 print와 logging 모두 사용
    print("=== Authentication Started ===")
    logger.info("=== Authentication Started ===")
    print(f"Received credentials: {credentials is not None}")
    logger.info(f"Received credentials: {credentials is not None}")
    
    # HTTPBearer(auto_error=True)이면 credentials가 None일 수 없지만, 안전을 위해 체크
    if credentials is None:
        error_msg = "No credentials provided. Authorization header missing or invalid."
        print(f"ERROR: {error_msg}")
        logger.error(error_msg)
        print("Expected format: Authorization: Bearer <token>")
        logger.error("Expected format: Authorization: Bearer <token>")
        raise credentials_exception
    
    try:
        token = credentials.credentials
        token_length = len(token) if token else 0
        print(f"Token received (length: {token_length})")
        logger.info(f"Token received (length: {token_length})")
        if token and len(token) > 20:
            print(f"Token prefix: {token[:20]}...")
            logger.debug(f"Token prefix: {token[:20]}...")
        
        print("Attempting JWT decode...")
        logger.info("Attempting JWT decode...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        print(f"JWT decode successful. Payload keys: {list(payload.keys())}")
        logger.info(f"JWT decode successful. Payload keys: {list(payload.keys())}")
        
        username: str = payload.get("sub")
        print(f"Extracted username from token: {username}")
        logger.info(f"Extracted username from token: {username}")
        
        if username is None:
            error_msg = "Username (sub) is None in JWT payload"
            print(f"ERROR: {error_msg}")
            logger.error(error_msg)
            raise credentials_exception
        
        print(f"Querying database for user: {username}")
        logger.info(f"Querying database for user: {username}")
        user = db.query(User).filter(User.user_name == username).first()
        
        if user is None:
            error_msg = f"User not found in database: {username}"
            print(f"ERROR: {error_msg}")
            logger.error(error_msg)
            raise credentials_exception
        
        print(f"Authentication successful. User ID: {user.id}, Username: {user.user_name}")
        logger.info(f"Authentication successful. User ID: {user.id}, Username: {user.user_name}")
        print("=== Authentication Completed ===")
        logger.info("=== Authentication Completed ===")
        return user
        
    except JWTError as e:
        error_msg = f"JWT decode failed: {type(e).__name__}: {str(e)}"
        print(f"ERROR: {error_msg}")
        logger.error(error_msg)
        print(f"SECRET_KEY configured: {bool(SECRET_KEY)}")
        logger.error(f"SECRET_KEY configured: {bool(SECRET_KEY)}")
        print(f"SECRET_KEY length: {len(SECRET_KEY) if SECRET_KEY else 0}")
        logger.error(f"SECRET_KEY length: {len(SECRET_KEY) if SECRET_KEY else 0}")
        raise credentials_exception
    except Exception as e:
        error_msg = f"Unexpected error during authentication: {type(e).__name__}: {str(e)}"
        print(f"ERROR: {error_msg}")
        logger.error(error_msg, exc_info=True)
        raise credentials_exception


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
