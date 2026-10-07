"""
Shared test infrastructure for AEGIS SQLite-based backend tests.

This conftest installs a SQLite override via a session-scoped fixture so it
only activates for tests that are collected alongside this file.

Integration tests (backend/tests/integration/) have their own conftest that
prevents this one from affecting them.
"""
import os
import uuid
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-all-tests-32chars!!")

# Models must be imported before create_all
from backend.app.models import user as _um  # noqa: F401
from backend.app.models import scan as _sm  # noqa: F401
from backend.app.core.database import Base, get_db
from backend.app.main import app

# ---------------------------------------------------------------------------
# Engine — created at module level so it exists before fixtures run
# ---------------------------------------------------------------------------
_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_Session = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
Base.metadata.create_all(bind=_engine)

_patcher = patch.object(Base.metadata, "create_all")
_patcher.start()


def _override_get_db():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db

# ---------------------------------------------------------------------------
# Module-level shared client and helpers
# (imported directly by test_security.py and test_history.py)
# ---------------------------------------------------------------------------
client = TestClient(app, raise_server_exceptions=True)


def unique_email() -> str:
    return f"u{uuid.uuid4().hex[:10]}@example.com"


def register(email=None, password="TestPass99!", name="Tester") -> dict:
    if email is None:
        email = unique_email()
    r = client.post("/api/auth/register",
                    json={"name": name, "email": email, "password": password})
    assert r.status_code == 201, f"Register failed: {r.text}"
    return {"token": r.json()["access_token"], "email": email,
            "password": password, "user": r.json()["user"]}


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def url_scan(token: str, url: str = "https://example.com") -> dict:
    r = client.post("/api/v1/analysis/url", json={"url": url},
                    headers=auth_header(token))
    assert r.status_code == 200, f"Scan failed: {r.text}"
    return r.json()
