"""
Pytest configuration and fixtures for backend tests.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db


# Test database URL (in-memory SQLite)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def test_db():
    """
    Create a fresh test database for each test function.
    Uses in-memory SQLite for speed.
    Only creates User table to avoid JSONB compatibility issues.
    """
    engine = create_engine(
        SQLALCHEMY_TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Import only User model to avoid JSONB issues with ClosetItem
    from app.domains.user.model import User

    # Create only User table
    User.__table__.create(bind=engine, checkfirst=True)

    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop User table after test
        User.__table__.drop(bind=engine, checkfirst=True)


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
    signup_data = {
        "username": "test@example.com",
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
    return {
        "username": "testuser@example.com",
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
