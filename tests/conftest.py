"""
Pytest configuration and fixtures for backend tests.
"""

import sys
from pathlib import Path
import os
from sqlalchemy import text

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

# Use Local PostgreSQL for tests by default
# This prevents accidental connections to Azure/Production DB during local testing
TEST_DB_USER = "choeseonghyeon"
TEST_DB_HOST = "localhost"
TEST_DB_PORT = "5432"
TEST_DB_NAME = "codify_test"

# Allow overriding via environment variables (e.g. for CI)
if os.getenv("CI"):
    DATABASE_URL = os.getenv(
        "DATABASE_URL", f"postgresql://postgres:postgres@localhost:5432/{TEST_DB_NAME}"
    )
else:
    # Local development default
    DATABASE_URL = (
        f"postgresql://{TEST_DB_USER}@{TEST_DB_HOST}:{TEST_DB_PORT}/{TEST_DB_NAME}"
    )


@pytest.fixture(scope="session", autouse=True)
def init_test_db():
    """
    Create tables in the test database.
    """
    engine = create_engine(DATABASE_URL)

    # Import all models to ensure they are registered with Base
    # We import the routers or models here so that Base.metadata.create_all works
    from app.domains.user.model import User
    from app.domains.wardrobe.model import ClosetItem

    # Add other models here if needed in the future

    # Ensure the database exists (optional, mostly handled by createdb manually beforehand)
    # But specifically create tables
    Base.metadata.create_all(bind=engine)

    yield

    # Optional: Drop tables after tests to clean up
    # Base.metadata.drop_all(bind=engine)


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
