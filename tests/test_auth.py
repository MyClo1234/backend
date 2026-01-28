"""
Tests for authentication API endpoints.
"""

import pytest


@pytest.mark.auth
@pytest.mark.unit
def test_signup_success(client, test_user_data):
    """Test successful user signup."""
    response = client.post("/api/auth/signup", json=test_user_data)

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "token" in data
    assert "user" in data
    assert data["user"]["username"] == test_user_data["username"]


@pytest.mark.auth
@pytest.mark.unit
def test_signup_duplicate_username(client, test_user_data):
    """Test signup with duplicate username."""
    # First signup
    client.post("/api/auth/signup", json=test_user_data)

    # Try to signup again with same username
    response = client.post("/api/auth/signup", json=test_user_data)

    assert response.status_code == 400
    assert "already registered" in response.json()["detail"].lower()


@pytest.mark.auth
@pytest.mark.unit
def test_login_success(client, test_user_data):
    """Test successful login."""
    # First signup
    client.post("/api/auth/signup", json=test_user_data)

    # Then login
    login_data = {
        "username": test_user_data["username"],
        "password": test_user_data["password"],
    }
    response = client.post("/api/auth/login", json=login_data)

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "token" in data
    assert "user" in data


@pytest.mark.auth
@pytest.mark.unit
def test_login_wrong_password(client, test_user_data):
    """Test login with wrong password."""
    # First signup
    client.post("/api/auth/signup", json=test_user_data)

    # Try to login with wrong password
    login_data = {"username": test_user_data["username"], "password": "wrongpassword"}
    response = client.post("/api/auth/login", json=login_data)

    assert response.status_code == 401


@pytest.mark.auth
@pytest.mark.unit
def test_login_nonexistent_user(client):
    """Test login with non-existent user."""
    login_data = {"username": "nonexistent@example.com", "password": "password123"}
    response = client.post("/api/auth/login", json=login_data)

    assert response.status_code == 401


@pytest.mark.auth
@pytest.mark.unit
def test_logout(client):
    """Test logout endpoint."""
    response = client.post("/api/auth/logout")

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "logged out" in data["message"].lower()
