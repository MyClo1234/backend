"""
Tests for wardrobe API endpoints.
"""

import pytest


@pytest.mark.wardrobe
@pytest.mark.unit
def test_get_wardrobe_items_empty(client, auth_headers):
    """Test getting wardrobe items when empty."""
    response = client.get("/api/wardrobe/users/me/images", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["items"] == []
    assert data["count"] == 0


@pytest.mark.wardrobe
@pytest.mark.unit
def test_get_wardrobe_items_unauthorized(client):
    """Test getting wardrobe items without authentication."""
    response = client.get("/api/wardrobe/users/me/images")

    assert response.status_code == 401


@pytest.mark.wardrobe
@pytest.mark.unit
def test_get_wardrobe_items_with_category_filter(client, auth_headers):
    """Test filtering wardrobe items by category."""
    response = client.get(
        "/api/wardrobe/users/me/images?category=top", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert isinstance(data["items"], list)


@pytest.mark.wardrobe
@pytest.mark.unit
def test_get_wardrobe_items_with_pagination(client, auth_headers):
    """Test pagination parameters."""
    response = client.get(
        "/api/wardrobe/users/me/images?skip=0&limit=10", headers=auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert len(data["items"]) <= 10


@pytest.mark.wardrobe
@pytest.mark.integration
def test_get_item_detail_not_found(client, auth_headers):
    """Test getting non-existent item detail."""
    response = client.get("/api/wardrobe/items/999999", headers=auth_headers)

    assert response.status_code == 404
