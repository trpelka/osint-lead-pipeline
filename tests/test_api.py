import socket

from fastapi.testclient import TestClient

from app import main
from app.main import app

client = TestClient(app)

LEAD = {
    "company": "Test Company",
    "domain": "test-example-123.com",
    "email": "test@test-example-123.com",
    "notes": "CI test",
}


def create_lead(**overrides):
    payload = dict(LEAD)
    payload.update(overrides)
    return client.post("/api/leads", json=payload)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_stats_starts_empty():
    response = client.get("/api/stats")
    assert response.status_code == 200
    assert response.json() == {"total_leads": 0}


def test_create_lead():
    response = create_lead()
    assert response.status_code == 201
    body = response.json()
    assert body["company"] == "Test Company"
    assert body["domain"] == "test-example-123.com"


def test_duplicate_domain_is_rejected():
    assert create_lead().status_code == 201
    assert create_lead(email="other@test-example-123.com").status_code == 409


def test_invalid_email():
    assert create_lead(email="not-an-email").status_code == 422


def test_invalid_domain():
    assert create_lead(domain="not a domain").status_code == 422
    assert create_lead(domain="http://example.com/path").status_code == 422


def test_missing_lead():
    assert client.get("/api/leads/999999").status_code == 404


def test_list_is_newest_first_and_paginates():
    for index in range(3):
        create_lead(domain=f"example-{index}.com", email=f"a{index}@example-{index}.com")
    first_page = client.get("/api/leads?limit=2").json()
    second_page = client.get("/api/leads?limit=2&skip=2").json()
    assert [lead["domain"] for lead in first_page] == ["example-2.com", "example-1.com"]
    assert [lead["domain"] for lead in second_page] == ["example-0.com"]


def test_search_matches_company_and_domain():
    create_lead(domain="alpha.example.com", email="a@alpha.example.com")
    create_lead(company="Beta", domain="beta.example.com", email="b@beta.example.com")
    found = client.get("/api/leads?search=beta").json()
    assert [lead["domain"] for lead in found] == ["beta.example.com"]


def test_patch_updates_allowed_fields():
    lead = create_lead().json()
    response = client.patch(f"/api/leads/{lead['id']}", json={"notes": "called"})
    assert response.status_code == 200
    assert response.json()["notes"] == "called"
    assert response.json()["domain"] == lead["domain"]


def test_patch_rejects_invalid_email():
    lead = create_lead().json()
    response = client.patch(f"/api/leads/{lead['id']}", json={"email": "broken"})
    assert response.status_code == 422


def test_delete_removes_the_lead():
    lead = create_lead().json()
    assert client.delete(f"/api/leads/{lead['id']}").status_code == 204
    assert client.get(f"/api/leads/{lead['id']}").status_code == 404


def test_scrape_rejects_ip_literals_and_localhost():
    assert client.get("/api/scrape/127.0.0.1").status_code == 400
    assert client.get("/api/scrape/localhost").status_code == 400


def test_scrape_rejects_hostnames_that_resolve_to_private_addresses(monkeypatch):
    def fake_getaddrinfo(*args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", 443))]

    monkeypatch.setattr(main.socket, "getaddrinfo", fake_getaddrinfo)
    assert client.get("/api/scrape/example.com").status_code == 400


def test_scrape_returns_the_first_email_in_sorted_order(monkeypatch):
    monkeypatch.setattr(main, "resolve_public_addresses", lambda domain: [])

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self, size):
            return b"<a href='mailto:zoe@example.com'>z</a> info@example.com"

    class FakeOpener:
        def open(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr(
        main.urllib.request, "build_opener", lambda handler: FakeOpener()
    )
    response = client.get("/api/scrape/example.com")
    assert response.status_code == 200
    assert response.json() == {
        "domain": "example.com",
        "email": "info@example.com",
    }


def test_scrape_falls_back_when_the_homepage_cannot_be_fetched(monkeypatch):
    monkeypatch.setattr(main, "resolve_public_addresses", lambda domain: [])

    class FailingOpener:
        def open(self, *args, **kwargs):
            raise OSError("blocked")

    monkeypatch.setattr(
        main.urllib.request, "build_opener", lambda handler: FailingOpener()
    )
    response = client.get("/api/scrape/example.com")
    assert response.status_code == 200
    assert response.json() == {
        "domain": "example.com",
        "email": "contact@example.com",
    }
