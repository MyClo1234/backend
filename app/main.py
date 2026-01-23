import os
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Config
from app.routers.health_routes import health_router
from app.routers.extraction_routes import extraction_router
from app.routers.wardrobe_routes import wardrobe_router
from app.routers.recommendation_routes import recommendation_router

# 로깅 설정
# Azure Functions 환경에서는 기본 로깅 설정이 다르게 작동할 수 있음
import sys

# Azure Functions와 일반 Python 환경 모두에서 작동하도록 설정
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),  # stdout으로 출력하여 Azure Functions에서도 보이도록
    ],
    force=True,  # 기존 핸들러가 있으면 덮어쓰기
)

# SQLAlchemy 로그 레벨 조정 (너무 많은 로그 방지)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
logging.getLogger("uvicorn").setLevel(logging.INFO)
logging.getLogger("fastapi").setLevel(logging.INFO)

# 애플리케이션 로거는 DEBUG 레벨 유지
logging.getLogger("app").setLevel(logging.DEBUG)

# 데이터베이스 및 인증 관련 (파일이 존재할 때만 import)
try:
    from app.database import engine, Base
    from app.models import user
    from app.routers.auth import router as auth_router

    HAS_DB = True
except ImportError:
    HAS_DB = False
    logging.warning(
        "Database and auth modules not found. Skipping database initialization."
    )


def create_app() -> FastAPI:
    app = FastAPI(title="Clothing Attribute Extractor", version="1.0.0")

    # 데이터베이스 초기화 (파일이 존재할 때만)
    if HAS_DB:
        Base.metadata.create_all(bind=engine)

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static files for images - REMOVED for Azure Functions (using Blob Storage)
    # os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    # app.mount("/api/images", StaticFiles(directory=Config.OUTPUT_DIR), name="images")

    # Include routers
    app.include_router(health_router, prefix="/api", tags=["Health"])

    # Auth router (파일이 존재할 때만)
    if HAS_DB:
        app.include_router(auth_router, prefix="/api", tags=["Auth"])

    app.include_router(extraction_router, prefix="/api", tags=["Extraction"])
    app.include_router(wardrobe_router, prefix="/api", tags=["Wardrobe"])
    app.include_router(recommendation_router, prefix="/api", tags=["Recommendation"])

    # User router
    if HAS_DB:
        from app.routers.user_routes import router as user_router

        app.include_router(user_router, prefix="/api", tags=["Users"])

    # Swagger UI에서 Bearer 토큰 인증을 위한 OpenAPI 스키마 커스터마이징
    # 라우터를 모두 추가한 후에 설정해야 함
    logger = logging.getLogger(__name__)
    
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        try:
            from fastapi.openapi.utils import get_openapi
            
            openapi_schema = get_openapi(
                title=app.title,
                version=app.version,
                description=app.description,
                routes=app.routes,
            )
            # 보안 스키마 추가
            if "components" not in openapi_schema:
                openapi_schema["components"] = {}
            openapi_schema["components"]["securitySchemes"] = {
                "bearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                }
            }
            
            # 각 경로에 보안 요구사항 추가 (인증이 필요한 엔드포인트에만)
            auth_required_paths = ["/api/extract", "/api/users", "/api/wardrobe"]
            auth_excluded_paths = ["/api/auth/login", "/api/auth/signup", "/api/health"]
            
            for path, path_item in openapi_schema.get("paths", {}).items():
                if not isinstance(path_item, dict):
                    continue
                    
                for method, operation in path_item.items():
                    # HTTP 메서드만 처리하고, operation이 딕셔너리인지 확인
                    if method.lower() not in ["post", "put", "delete", "patch", "get"]:
                        continue
                    if not isinstance(operation, dict):
                        continue
                    
                    # 인증이 필요한 경로인지 확인
                    needs_auth = any(auth_path in path for auth_path in auth_required_paths)
                    is_excluded = any(excluded_path == path for excluded_path in auth_excluded_paths)
                    
                    if needs_auth and not is_excluded:
                        operation["security"] = [{"bearerAuth": []}]
                        logger.debug(f"Added security requirement to {method.upper()} {path}")
            
            app.openapi_schema = openapi_schema
            return app.openapi_schema
        except Exception as e:
            logger.error(f"Error generating OpenAPI schema: {type(e).__name__}: {str(e)}", exc_info=True)
            # 에러 발생 시 기본 OpenAPI 스키마 반환
            from fastapi.openapi.utils import get_openapi
            return get_openapi(
                title=app.title,
                version=app.version,
                description=app.description,
                routes=app.routes,
            )

    app.openapi = custom_openapi

    return app


app = create_app()

if __name__ == "__main__":
    # Ensure config can only warn if generated
    import uvicorn

    Config.check_api_key()
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
