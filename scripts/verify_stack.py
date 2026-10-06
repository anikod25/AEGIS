#!/usr/bin/env python3
"""
AEGIS stack verification script.
Verifies that all required Docker/gateway files exist and contain expected content.
Runs without the Docker stack running.
Exit 0 = all checks pass. Exit 1 = one or more checks failed.
"""
import sys
import os

WORKDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

results = []

def check(label, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    msg = f"[{status}] {label}"
    if detail and not passed:
        msg += f"\n       {detail}"
    results.append((passed, msg))
    print(msg)

# ── 1. Required files exist ────────────────────────────────────────────────
required_files = [
    "docker-compose.yml",
    "gateway/nginx.conf",
    "gateway/Dockerfile",
    "backend/Dockerfile",
    "frontend/Dockerfile",
    ".env.example",
]
for rel in required_files:
    path = os.path.join(WORKDIR, rel)
    check(f"File exists: {rel}", os.path.isfile(path))

# ── 2. docker-compose.yml defines required services ───────────────────────
try:
    import yaml
    with open(os.path.join(WORKDIR, "docker-compose.yml")) as f:
        dc = yaml.safe_load(f)
    services = dc.get("services", {})
    for svc in ["mysql", "backend", "gateway", "frontend"]:
        check(f"docker-compose.yml: service '{svc}' defined", svc in services)
except ImportError:
    with open(os.path.join(WORKDIR, "docker-compose.yml")) as f:
        raw = f.read()
    for svc in ["mysql", "backend", "gateway", "frontend"]:
        check(f"docker-compose.yml: service '{svc}' defined",
              f"  {svc}:" in raw or f"\n{svc}:" in raw,
              "Service keyword not found in compose file")
except Exception as e:
    check("docker-compose.yml: parse", False, str(e))

# ── 3. nginx.conf proxies /api/ to backend ────────────────────────────────
try:
    with open(os.path.join(WORKDIR, "gateway", "nginx.conf")) as f:
        nginx = f.read()
    check(
        "nginx.conf: proxy_pass to backend for /api/",
        "proxy_pass" in nginx and "backend" in nginx and "/api/" in nginx,
        "Expected proxy_pass with backend and /api/ in nginx.conf"
    )
except Exception as e:
    check("nginx.conf: readable", False, str(e))

# ── 4. frontend api.js uses /api as default BASE_URL ─────────────────────
try:
    api_js = os.path.join(WORKDIR, "frontend", "src", "services", "api.js")
    with open(api_js) as f:
        js = f.read()
    check(
        "api.js: default BASE_URL is /api (not hardcoded localhost)",
        "'/api'" in js or '"/api"' in js,
        "Expected '/api' as the fallback BASE_URL"
    )
    check(
        "api.js: VITE_API_URL env var still used",
        "VITE_API_URL" in js,
        "Expected import.meta.env.VITE_API_URL reference"
    )
except Exception as e:
    check("api.js: readable", False, str(e))

# ── 5. config.py has DATABASE_URL field ───────────────────────────────────
try:
    cfg = os.path.join(WORKDIR, "backend", "app", "core", "config.py")
    with open(cfg) as f:
        cfg_text = f.read()
    check(
        "config.py: DATABASE_URL field present",
        "DATABASE_URL" in cfg_text,
        "Expected DATABASE_URL in Settings class"
    )
except Exception as e:
    check("config.py: readable", False, str(e))

# ── 6. .env.example has MySQL vars ────────────────────────────────────────
try:
    with open(os.path.join(WORKDIR, ".env.example")) as f:
        env_ex = f.read()
    for key in ["MYSQL_ROOT_PASSWORD", "MYSQL_USER", "MYSQL_PASSWORD"]:
        check(f".env.example: {key} present", key in env_ex)
except Exception as e:
    check(".env.example: readable", False, str(e))

# ── Summary ───────────────────────────────────────────────────────────────
print()
passed = sum(1 for ok, _ in results if ok)
failed = sum(1 for ok, _ in results if not ok)
total  = len(results)
print(f"Results: {passed}/{total} checks passed, {failed} failed.")
if failed == 0:
    print("All checks PASSED — stack configuration looks good.")
    sys.exit(0)
else:
    print(f"{failed} check(s) FAILED — review the output above.")
    sys.exit(1)
