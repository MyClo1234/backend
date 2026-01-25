"""
Tests for user API endpoints.
"""

import pytest


@pytest.mark.unit
def test_get_current_user(client, auth_headers):
    """Test getting current user info."""
    response = client.get("/api/users/me", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert "id" in data
    assert "username" in data
    assert data["username"].startswith("test_")
    assert data["username"].endswith("@example.com")


@pytest.mark.unit
def test_get_current_user_unauthorized(client):
    """Test getting current user without authentication."""
    response = client.get("/api/users/me")

    assert response.status_code == 401


@pytest.mark.unit
def test_update_profile(client, auth_headers):
    """Test updating user profile."""
    update_data = {
        "height": 180.0,
        "weight": 75.0,
        "gender": "male",
        "body_shape": "athletic",
    }

    response = client.put("/api/users/profile", json=update_data, headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["height"] == 180.0
    assert data["weight"] == 75.0
    assert data["gender"] == "male"
    assert data["body_shape"] == "athletic"


@pytest.mark.unit
def test_update_profile_unauthorized(client):
    """Test updating profile without authentication."""
    update_data = {"height": 180.0}

    response = client.put("/api/users/profile", json=update_data)

    assert response.status_code == 401
