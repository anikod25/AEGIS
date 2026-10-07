"""
Ownership and scan history tests.

Uses the shared SQLite engine from conftest.py.
"""
from backend.tests.conftest import client, register, auth_header, url_scan, unique_email


def _login(email: str, password: str) -> str:
    r = client.post("/api/auth/login", json={"email": email, "password": password})
    assert r.status_code == 200
    return r.json()["access_token"]


def test_scan_history_empty_for_new_user():
    u = register()
    r = client.get("/api/v1/scans", headers=auth_header(u["token"]))
    assert r.status_code == 200
    assert r.json()["items"] == []
    assert r.json()["total"] == 0


def test_scan_appears_after_url_analysis():
    u = register()
    url_scan(u["token"])
    r = client.get("/api/v1/scans", headers=auth_header(u["token"]))
    assert r.json()["total"] == 1
    assert r.json()["items"][0]["scan_type"] == "url"


def test_user_cannot_access_other_users_scan():
    a = register(); b = register()
    scan = url_scan(a["token"])
    r = client.get(f"/api/v1/scans/{scan['scan_id']}", headers=auth_header(b["token"]))
    assert r.status_code == 404


def test_user_cannot_list_other_users_scans():
    a = register(); b = register()
    url_scan(a["token"]); url_scan(a["token"])
    r = client.get("/api/v1/scans", headers=auth_header(b["token"]))
    assert r.json()["total"] == 0


def test_delete_own_scan():
    u = register()
    scan = url_scan(u["token"])
    r = client.delete(f"/api/v1/scans/{scan['scan_id']}", headers=auth_header(u["token"]))
    assert r.status_code == 204
    r2 = client.get("/api/v1/scans", headers=auth_header(u["token"]))
    assert r2.json()["total"] == 0


def test_cannot_delete_other_users_scan():
    a = register(); b = register()
    scan = url_scan(b["token"])
    r = client.delete(f"/api/v1/scans/{scan['scan_id']}", headers=auth_header(a["token"]))
    assert r.status_code == 404
    r2 = client.get(f"/api/v1/scans/{scan['scan_id']}", headers=auth_header(b["token"]))
    assert r2.status_code == 200


def test_reports_reflects_user_scans():
    u = register()
    url_scan(u["token"])
    r = client.get("/api/v1/reports", headers=auth_header(u["token"]))
    assert r.status_code == 200
    body = r.json()
    assert body["total_scans"] == 1
    assert body["by_type"]["url"] == 1


def test_pagination():
    u = register()
    for i in range(3):
        url_scan(u["token"], f"https://example.com/page{i}")
    r = client.get("/api/v1/scans?page=1&per_page=2", headers=auth_header(u["token"]))
    body = r.json()
    assert len(body["items"]) == 2
    assert body["total"] == 3
    assert body["pages"] == 2


def test_filter_by_scan_type():
    u = register()
    url_scan(u["token"], "https://example.com/filter-test")
    client.post("/api/v1/analysis/email",
                json={"sender": "test@example.com", "body": "Hello test email."},
                headers=auth_header(u["token"]))
    r = client.get("/api/v1/scans?scan_type=url", headers=auth_header(u["token"]))
    items = r.json()["items"]
    assert all(i["scan_type"] == "url" for i in items)


def test_scan_history_requires_auth():
    r = client.get("/api/v1/scans")
    assert r.status_code in (401, 403)


def test_reports_requires_auth():
    r = client.get("/api/v1/reports")
    assert r.status_code in (401, 403)


def test_get_scan_detail():
    u = register()
    scan = url_scan(u["token"])
    r = client.get(f"/api/v1/scans/{scan['scan_id']}", headers=auth_header(u["token"]))
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == scan["scan_id"]
    assert body["scan_type"] == "url"
    assert "target" in body
    assert "risk_score" in body
