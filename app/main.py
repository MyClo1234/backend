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
from app.routers.weather_routes import router as weather_router


# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

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
    app.include_router(weather_router, prefix="/api", tags=["Weather"])

    app.include_router(health_router, prefix="/api", tags=["Health"])

    # Auth router (파일이 존재할 때만)
    if HAS_DB:
        app.include_router(auth_router, prefix="/api", tags=["Auth"])

    app.include_router(extraction_router, prefix="/api", tags=["Extraction"])
    app.include_router(wardrobe_router, prefix="/api", tags=["Wardrobe"])
    app.include_router(extraction_router, prefix="/api", tags=["Extraction"])
    app.include_router(wardrobe_router, prefix="/api", tags=["Wardrobe"])
    app.include_router(recommendation_router, prefix="/api", tags=["Recommendation"])

    # User router
    if HAS_DB:
        from app.routers.user_routes import router as user_router

        app.include_router(user_router, prefix="/api", tags=["Users"])

    return app


app = create_app()

if __name__ == "__main__":
    # Ensure config can only warn if generated
    import uvicorn

    Config.check_api_key()
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
