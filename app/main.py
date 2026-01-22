import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import Config
from app.routers.health_routes import health_router
from app.routers.extraction_routes import extraction_router
from app.routers.wardrobe_routes import wardrobe_router
from app.routers.recommendation_routes import recommendation_router

from app.database import engine, Base
from app.models.user import User

from app.routers.auth import router as auth_router
from app.routers.health_routes import health_router

Base.metadata.create_all(bind=engine)
print(f"Base main.py: {Base}...")  # 앞부분만 출력


def create_app() -> FastAPI:
    app = FastAPI(title="Clothing Attribute Extractor", version="1.0.0")

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static files for images
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    app.mount("/api/images", StaticFiles(directory=Config.OUTPUT_DIR), name="images")

    # Include routers
    app.include_router(health_router, prefix="/api", tags=["Health"])
    app.include_router(auth_router, prefix="/api", tags=["Auth"])
    app.include_router(extraction_router, prefix="/api", tags=["Extraction"])
    app.include_router(wardrobe_router, prefix="/api", tags=["Wardrobe"])
    app.include_router(recommendation_router, prefix="/api", tags=["Recommendation"])

    return app


app = create_app()

if __name__ == "__main__":
    # Ensure config can only warn if generated
    Config.check_api_key()
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
