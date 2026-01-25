"""
Pytest configuration and fixtures for backend tests.
"""

import sys
from pathlib import Path
import os

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

# Use Azure PostgreSQL for tests
# Create a test database URL from environment variables
POSTGRES_USER = os.getenv("POSTGRES_USER", "codify_admin")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_SERVER = os.getenv(
    "POSTGRES_SERVER", "codify-postgres.postgres.database.azure.com"
)
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "codify")

DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_SERVER}:{POSTGRES_PORT}/{POSTGRES_DB}"


@pytest.fixture(scope="function")
def test_db():
    """
    Create a test database session using Azure PostgreSQL.
    Uses the same database as production but with transaction rollback.
    """
    engine = create_engine(DATABASE_URL)

    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        # Rollback any changes made during the test
        db.rollback()
        db.close()


@pytest.fixture(scope="function")
def client(test_db):
    """
    Create a test client with test database dependency override.
    Creates a fresh FastAPI app with all routers for testing.
    """
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    # Create test app
    test_app = FastAPI(title="Test API")

    # Add CORS
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register all routers
    from app.routers.health_routes import health_router
    from app.domains.auth.router import router as auth_router
    from app.domains.user.router import router as user_router

    test_app.include_router(health_router, prefix="/api", tags=["Health"])
    test_app.include_router(auth_router, prefix="/api", tags=["Auth"])
    test_app.include_router(user_router, prefix="/api", tags=["Users"])

    from app.domains.wardrobe.router import wardrobe_router

    test_app.include_router(wardrobe_router, prefix="/api", tags=["Wardrobe"])

    # Override database dependency
    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    test_app.dependency_overrides[get_db] = override_get_db

    with TestClient(test_app) as test_client:
        yield test_client

    # Clear overrides after test
    test_app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """
    Create a test user and return authentication headers.
    """
    # Create test user
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    signup_data = {
        "username": f"test_{unique_id}@example.com",
        "password": "testpassword123",
        "age": 25,
        "height": 175.0,
        "weight": 70.0,
        "gender": "male",
        "body_shape": "normal",
    }

    response = client.post("/api/auth/signup", json=signup_data)
    assert response.status_code == 200

    token = response.json()["token"]

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_user_data():
    """
    Provide test user data.
    """
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    return {
        "username": f"testuser_{unique_id}@example.com",
        "password": "securepassword123",
        "age": 30,
        "height": 170.0,
        "weight": 65.0,
        "gender": "female",
        "body_shape": "slim",
    }


@pytest.fixture
def test_wardrobe_item():
    """
    Provide test wardrobe item data.
    """
    return {
        "category": {"main": "top", "sub": "t-shirt", "confidence": 0.95},
        "color": {"primary": "blue", "secondary": "white"},
        "pattern": "solid",
        "material": "cotton",
    }
