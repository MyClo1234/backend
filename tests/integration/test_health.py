def test_health_check(client):
    """Health check endpoint should return 200 OK"""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
