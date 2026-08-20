from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200


def test_stats():
    response = client.get("/api/stats")
    assert response.status_code == 200
    assert "total_leads" in response.json()


def test_create_lead():
    response = client.post(
        "/api/leads",
        json={
            "company": "Test Company",
            "domain": "test-example-123.com",
            "email": "test@test-example-123.com",
            "notes": "CI test"
        }
    )

    assert response.status_code == 201
    assert response.json()["company"] == "Test Company"


def test_invalid_email():
    response = client.post(
        "/api/leads",
        json={
            "company": "Bad Company",
            "domain": "bad-example.com",
            "email": "not-an-email"
        }
    )

    assert response.status_code == 422


def test_missing_lead():
    response = client.get("/api/leads/999999")
    assert response.status_code == 404