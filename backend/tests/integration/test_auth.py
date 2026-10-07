"""
Auth endpoint tests against the real MySQL database.
Run with: pytest backend/tests/integration/
"""
import os
import re
import uuid
import pytest
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient


def _read_mysql_url() -> str:
    """Read DATABASE_URL directly from the repo root .env file, bypassing
    the singleton Settings instance (which may have been overridden to sqlite://)."""
    env_path = Path(__file__).resolve().parents[3] / ".env"
    text = env_path.read_text(encoding="utf-8")
    m = re.search(r"^DATABASE_URL\s*=\s*(.+)$", text, re.MULTILINE)
    if not m:
        raise RuntimeError(".env has no DATABASE_URL")
    url = m.group(1).strip()
    if url.startswith("sqlite"):
        raise RuntimeError("DATABASE_URL in .env is sqlite — set it to MySQL for integration tests")
    return url


MYSQL_URL = _read_mysql_url()

from backend.app.main import app
from backend.app.core.database import get_db, Base

_engine  = create_engine(MYSQL_URL, pool_pre_ping=True)
_Session = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
Base.metadata.create_all(bind=_engine)


def _mysql_get_db():
    db = _Session()
    try:
        yield db
    finally:
        db.close()


# Always override with our MySQL session regardless of conftest
app.dependency_overrides[get_db] = _mysql_get_db

client = TestClient(app, raise_server_exceptions=True)

_RUN  = uuid.uuid4().hex[:8]
ALICE = {"name": "Alice Test", "email": f"alice_{_RUN}@example.com", "password": "SecurePass1"}
BOB   = {"name": "Bob Test",   "email": f"bob_{_RUN}@example.com",   "password": "BobPass99!"}


@pytest.fixture(autouse=True, scope="module")
def cleanup_users():
    yield
    db = _Session()
    try:
        from backend.app.models.user import User
        for email in [ALICE["email"], BOB["email"]]:
            u = db.query(User).filter(User.email == email).first()
            if u:
                db.delete(u)
        db.commit()
    finally:
        db.close()


def _reg(p):       return client.post("/api/auth/register", json=p)
def _login(e, pw): return client.post("/api/auth/login", json={"email": e, "password": pw})


def test_register_success():
    r = _reg(ALICE)
    assert r.status_code == 201, r.text
    b = r.json()
    assert "access_token" in b
    assert b["user"]["email"] == ALICE["email"]
    assert b["user"]["role"] == "user"
    assert "password_hash" not in b["user"]

def test_register_second_user():
    r = _reg(BOB); assert r.status_code == 201, r.text

def test_register_duplicate_returns_409():
    r = _reg(ALICE); assert r.status_code == 409

def test_login_success():
    r = _login(ALICE["email"], ALICE["password"]); assert r.status_code == 200, r.text

def test_login_wrong_password_returns_401():
    assert _login(ALICE["email"], "WrongPassword99").status_code == 401

def test_login_unknown_email_returns_401():
    assert _login("nobody@example.com", "Whatever123").status_code == 401

def test_me_with_valid_token():
    token = _login(ALICE["email"], ALICE["password"]).json()["access_token"]
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == ALICE["email"]

def test_me_without_token():
    assert client.get("/api/auth/me").status_code in (401, 403)

def test_me_invalid_token():
    r = client.get("/api/auth/me", headers={"Authorization": "Bearer badtoken"})
    assert r.status_code == 401

