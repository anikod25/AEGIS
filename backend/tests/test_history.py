"""
Ownership and scan history tests.

Uses SQLite in-memory with StaticPool so all connections share the same
database instance — required for in-memory SQLite to work with SQLAlchemy.
"""
import uuid
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Import models before Base so metadata is fully populated before create_all
from backend.app.models import user as _user_model   # noqa: F401
from backend.app.models import scan as _scan_model   # noqa: F401
from backend.app.core.database import Base, get_db
from backend.app.main import app

# ---------------------------------------------------------------------------
# Single shared in-memory SQLite engine
# ---------------------------------------------------------------------------
_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,   # all connections share the same in-memory DB
)
_Session = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
Base.metadata.create_all(bind=_engine)


def _override_get_db():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db

# Suppress lifespan create_all so it doesn't attempt the real MySQL engine
_patcher = patch.object(Base.metadata, "create_all")
_patcher.start()

client = TestClient(app, raise_server_exceptions=True)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _unique_email() -> str:
    return f"u{uuid.uuid4().hex[:10]}@example.com"


def _register_and_login(email: str | None = None, password: str = "TestPass123!") -> str:
    if email is None:
        email = _unique_email()
    r = client.post(
        "/api/auth/register",
        json={"name": "Test User", "email": email, "password": password},
    )
    assert r.status_code == 201, f"Register failed: {r.text}"
    return r.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _run_url_scan(token: str, url: str = "https://example.com/test") -> dict:
    r = client.post("/api/v1/analysis/url", json={"url": url}, headers=_auth(token))
    assert r.status_code == 200, f"URL scan failed: {r.text}"
    return r.json()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_scan_history_empty_for_new_user():
    token = _register_and_login()
    r = client.get("/api/v1/scans", headers=_auth(token))
    assert r.status_code == 200
    body = r.json()
    assert body["items"] == []
    assert body["total"] == 0


def test_scan_appears_after_url_analysis():
    token = _register_and_login()
    _run_url_scan(token)
    r = client.get("/api/v1/scans", headers=_auth(token))
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["scan_type"] == "url"


def test_user_cannot_access_other_users_scan():
    alice_token = _register_and_login()
    bob_token   = _register_and_login()
    scan    = _run_url_scan(alice_token)
    scan_id = scan["scan_id"]
    r = client.get(f"/api/v1/scans/{scan_id}", headers=_auth(bob_token))
    assert r.status_code == 404


def test_user_cannot_list_other_users_scans():
    alice_token = _register_and_login()
    bob_token   = _register_and_login()
    _run_url_scan(alice_token)
    _run_url_scan(alice_token)
    r = client.get("/api/v1/scans", headers=_auth(bob_token))
    assert r.status_code == 200
    assert r.json()["total"] == 0


def test_delete_own_scan():
    token   = _register_and_login()
    scan    = _run_url_scan(token)
    scan_id = scan["scan_id"]
    r = client.delete(f"/api/v1/scans/{scan_id}", headers=_auth(token))
    assert r.status_code == 204
    r2 = client.get("/api/v1/scans", headers=_auth(token))
    assert r2.json()["total"] == 0


def test_cannot_delete_other_users_scan():
    alice_token = _register_and_login()
    bob_token   = _register_and_login()
    scan    = _run_url_scan(bob_token)
    scan_id = scan["scan_id"]
    r = client.delete(f"/api/v1/scans/{scan_id}", headers=_auth(alice_token))
    assert r.status_code == 404
    r2 = client.get(f"/api/v1/scans/{scan_id}", headers=_auth(bob_token))
    assert r2.status_code == 200


def test_reports_reflects_user_scans():
    token = _register_and_login()
    _run_url_scan(token)
    r = client.get("/api/v1/reports", headers=_auth(token))
    assert r.status_code == 200
    body = r.json()
    assert body["total_scans"] == 1
    assert body["by_type"]["url"] == 1


def test_pagination():
    token = _register_and_login()
    for i in range(3):
        _run_url_scan(token, f"https://example.com/page{i}")
    r = client.get("/api/v1/scans?page=1&per_page=2", headers=_auth(token))
    assert r.status_code == 200
    body = r.json()
    assert len(body["items"]) == 2
    assert body["total"] == 3
    assert body["pages"] == 2


def test_filter_by_scan_type():
    token = _register_and_login()
    _run_url_scan(token, "https://example.com/filter-test")
    client.post(
        "/api/v1/analysis/email",
        json={"sender": "test@example.com", "body": "Hello, this is a test email."},
        headers=_auth(token),
    )
    r = client.get("/api/v1/scans?scan_type=url", headers=_auth(token))
    assert r.status_code == 200
    items = r.json()["items"]
    assert all(i["scan_type"] == "url" for i in items)


def test_scan_history_requires_auth():
    r = client.get("/api/v1/scans")
    assert r.status_code in (401, 403)


def test_reports_requires_auth():
    r = client.get("/api/v1/reports")
    assert r.status_code in (401, 403)


def test_get_scan_detail():
    token   = _register_and_login()
    scan    = _run_url_scan(token)
    scan_id = scan["scan_id"]
    r = client.get(f"/api/v1/scans/{scan_id}", headers=_auth(token))
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == scan_id
    assert body["scan_type"] == "url"
    assert "target" in body
    assert "risk_score" in body
