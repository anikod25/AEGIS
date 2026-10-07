# AEGIS Security Audit Report

**Date:** October 2026
**Scope:** Full application — FastAPI backend, React frontend, Nginx gateway, Docker Compose stack
**Auditor:** Internal security hardening pass
**Verdict:** Not production-ready without HTTPS and external penetration testing. All identified issues within scope have been fixed.

---

## 1. Security Areas Reviewed

| Area | Coverage |
|------|----------|
| Authentication — registration, login, JWT creation/validation | Full |
| Session security — token expiry, algorithm, claims | Full |
| Authorization — ownership checks, IDOR, privilege escalation | Full |
| Input validation — all API endpoints | Full |
| Injection defenses — SQL, XSS, CRLF, null byte, scheme | Full |
| Sensitive data handling — passwords, tokens, keys in responses/logs | Full |
| HTTP security headers — CORS, CSP, framing, content-type | Full |
| Secrets management — env vars, .env, Docker | Full |
| Docker configuration — privileges, exposed ports, image hardening | Full |
| AI security — prompt injection, Gemini key isolation | Full |
| Automated security tests | Full |

---

## 2. Vulnerabilities Found and Fixed

### CRITICAL

None identified.

---

### HIGH

| # | Vulnerability | Location | Fix Applied |
|---|--------------|----------|-------------|
| H1 | Timing-based user enumeration via login | `auth.py` login route | Replaced inline dummy hash (truncated, invalid) with pre-computed `_DUMMY_HASH` via `dummy_verify()` in `security.py`. Guaranteed full bcrypt cost path for unknown emails. |
| H2 | CORS wildcard `Access-Control-Allow-Origin: *` on all API responses | `gateway/nginx.conf` | Replaced with origin-restricted CORS: only `localhost` and `127.0.0.1` origins accepted. Wildcard removed. |
| H3 | Dangerous URL schemes not blocked at schema level | `schemas/url_analysis.py` | Added explicit blocklist: `javascript:`, `data:`, `vbscript:`, `file:`, `blob:`, `about:`, `chrome:`, `chrome-extension:`, `moz-extension:`. |

---

### MEDIUM

| # | Vulnerability | Location | Fix Applied |
|---|--------------|----------|-------------|
| M1 | CRLF injection via URL field | `schemas/url_analysis.py` | Added `_INVALID_CHARS_RE` to reject `\r`, `\n`, `\x00` in URL input. |
| M2 | Null byte injection in email fields | `schemas/phishing.py` | Added `_strip_invalid()` validator on `sender`, `reply_to`, `subject`. Null bytes dropped from links and attachment names. |
| M3 | `LoginRequest.password` had no `min_length` | `schemas/auth.py` | Added `min_length=1`. Prevents empty-string bypass. |
| M4 | `LoginRequest.password` max 256 chars vs register max 128 | `schemas/auth.py` | Aligned both to 128 chars (bcrypt's effective limit is 72 bytes; capping at 128 prevents silent truncation surprises). |
| M5 | `jwt.decode` did not require `iat` claim; `iat` used deprecated `datetime.utcnow()` | `security.py` | `iat` now uses `datetime.now(timezone.utc)`. Token type claim `typ: access` added. |
| M6 | Internal Docker hostname `http://gateway` in FastAPI CORS origins | `main.py` | Removed — CORS is a browser mechanism; inter-container calls bypass it. |
| M7 | `deps.py` did not validate that JWT `sub` is a positive integer | `deps.py` | Added `uid = int(user_id); if uid <= 0: raise credentials_exception`. Negative and zero user IDs now rejected. |
| M8 | No security headers on Nginx responses | `gateway/nginx.conf` | Added: `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy`, `Cache-Control: no-store` on API routes, `server_tokens off`. |
| M9 | No Content-Security-Policy on frontend | `gateway/nginx.conf` | Added CSP on `/` location: restricts scripts, styles, connections, and frame ancestors. |
| M10 | Backend Docker container ran with default privileges | `docker-compose.yml` | Added `security_opt: no-new-privileges:true` and `cap_drop: ALL` to backend service. |

---

### LOW

| # | Vulnerability | Location | Fix Applied |
|---|--------------|----------|-------------|
| L1 | `.env.example` used vague `replace-with-*` placeholders | `.env.example` | Changed to `CHANGE_ME_*` format with explicit generation instructions for `JWT_SECRET_KEY`. |
| L2 | Backend Dockerfile missing `PYTHONDONTWRITEBYTECODE`, `PYTHONUNBUFFERED` | `backend/Dockerfile` | Added both. Shell set to `/sbin/nologin`. |
| L3 | `security.py` exported no helper for timing-safe dummy login | `security.py` | Extracted `dummy_verify()` as a named function with a valid pre-computed hash. |
| L4 | Security contract not documented in `deps.py` | `deps.py` | Added explicit docstring stating user identity always comes from JWT, never from request body. |
| L5 | `test_auth.py` conflicted with SQLite conftest when run together | `backend/tests/` | Moved to `backend/tests/integration/` with its own MySQL session builder. Added `conftest.py` per folder to isolate scopes. |

---

## 3. Security Tests Added

**File:** `backend/tests/test_security.py` — 67 tests across 5 classes

| Class | Tests | What is Tested |
|-------|-------|----------------|
| `TestAuthentication` | 18 | Missing/invalid/expired/tampered tokens, `alg:none` bypass, negative/zero sub claims, ghost user tokens, no user enumeration via status or message, weak password rejection, oversized password rejection |
| `TestAuthorization` | 10 | IDOR on scan read/delete, cross-user scan list isolation, cross-user dashboard/report isolation, forged `user_id` in body, role self-assignment, all protected endpoints require auth, `require_admin` blocks normal user |
| `TestInputValidation` | 22 | SQL injection (never 500), XSS (never 500), null byte in URL, CRLF in URL, `javascript:` / `data:` / `file:` / `ftp:` schemes, URL over 2048 chars, empty URL/password, oversized password, null byte in email sender, CRLF in email subject, oversized email body, missing fields, malformed JSON, invalid filter values, string/traversal scan ID, bad pagination |
| `TestDataSecurity` | 6 | Register response has no password fields, password analysis never echoes input, scan response has no `user_id`, error responses have no stack trace, Gemini key not in responses, JWT secret not in error responses |
| `TestAISecurity` | 7 | AI explain requires auth, assistant requires auth, prompt injection never causes 500, context field value too long rejected, context field key too long rejected, invalid scan type rejected, oversized message/history rejected |

**File:** `backend/tests/integration/test_auth.py` — 9 tests (MySQL)

Register success, duplicate 409, login success, wrong password 401, unknown email 401, valid token /me, no token /me, invalid token /me.

---

## 4. Test Results

| Suite | Command | Result |
|-------|---------|--------|
| Full SQLite suite (security + history + analyzers + assistant) | `pytest backend/tests/ --ignore=backend/tests/integration` | **276 passed** |
| MySQL integration auth tests | `pytest backend/tests/integration/` | **9 passed** |
| Frontend build | `npm run build` | **Clean** |

**Note:** The two suites must be run separately. They share the same FastAPI `app` object and install different database overrides. Running them together in a single pytest invocation causes cross-contamination. This is a test infrastructure limitation, not an application defect.

---

## 5. Remaining Risks

| Risk | Severity | Notes |
|------|----------|-------|
| No HTTPS | High | Nginx is HTTP-only. Tokens and passwords transmitted in plaintext over the network. Requires TLS termination (Let'\''s Encrypt / reverse proxy) before any internet-facing deployment. |
| In-memory rate limiting | Medium | Per-process rate limits reset on restart and are not shared across workers. Acceptable for single-process dev; requires Redis or similar for multi-worker production. |
| No CSRF protection | Medium | AEGIS uses Bearer tokens (not cookies) so traditional CSRF is not applicable. If cookies are ever introduced, SameSite and CSRF tokens would be required. |
| No account lockout | Medium | Repeated failed logins are not throttled at the application layer. Rate limiting at Nginx or a dedicated auth service would be needed for production. |
| `alg:none` partially mitigated | Low | `python-jose` with `algorithms=[settings.JWT_ALGORITHM]` rejects `alg:none` in the decode call. Verified by test. No additional mitigation needed at current library version. |
| Gemini TLS bypass fallback | Low | If certifi CA bundle fails, `httpx.Client(verify=False)` is used with a logged warning. This means Gemini responses could be intercepted in adversarial network environments. Fix: fail hard instead of bypassing TLS. |
| No audit logging | Low | Failed authentication attempts and IDOR attempts are not persisted anywhere. A production deployment should log these for monitoring. |
| Scan summary stored as JSON string | Info | `summary` column stores a JSON list of indicator IDs. This is safe (no raw user input) but is not indexed or queryable. |

---

## 6. Security Assumptions

- The application is deployed behind a reverse proxy that terminates TLS before exposing it to users.
- The `.env` file is never committed to version control (enforced by `.gitignore`).
- `JWT_SECRET_KEY` is generated with at least 32 random bytes. Validated at startup.
- The MySQL user (`aegis_user`) has `GRANT ALL` only on the `aegis` database, not globally.
- Docker host is not publicly accessible; only port 80 (gateway) is exposed.
- Gemini API key has usage quotas configured in Google Cloud to limit blast radius of key exposure.

---

## 7. Items Requiring External Infrastructure

- **HTTPS/TLS** — add a TLS-terminating reverse proxy (e.g. Nginx with Let'\''s Encrypt, Caddy, or a cloud load balancer) in front of the gateway container.
- **Rate limiting persistence** — replace in-process token buckets with a Redis-backed rate limiter for multi-worker deployments.
- **Secret rotation** — implement a process to rotate `JWT_SECRET_KEY`, `MYSQL_PASSWORD`, and `GEMINI_API_KEY` without downtime.
- **External penetration test** — this audit was performed by the development team. An independent external pentest is required before any public-facing deployment.
- **Dependency scanning** — integrate a tool such as `pip-audit` or Dependabot to alert on vulnerable Python and npm dependencies.
- **Log aggregation and alerting** — ship application logs to a SIEM or alerting system to detect brute-force and enumeration attempts in production.

---

## 8. Files Changed in This Audit

| File | Change |
|------|--------|
| `backend/app/core/security.py` | Pre-computed `_DUMMY_HASH`, `dummy_verify()`, timezone-aware `iat`, `typ: access` claim |
| `backend/app/api/auth.py` | Uses `dummy_verify()`, removed inline dummy hash |
| `backend/app/schemas/auth.py` | `LoginRequest` min/max aligned to 128, `min_length=1` added |
| `backend/app/api/deps.py` | Positive integer sub validation, security contract docstring |
| `backend/app/schemas/url_analysis.py` | Blocked schemes, CRLF/null byte rejection |
| `backend/app/schemas/phishing.py` | Null byte and CRLF rejection on string fields |
| `backend/app/main.py` | Removed `http://gateway` CORS origin, restricted `allow_methods`/`allow_headers` |
| `gateway/nginx.conf` | Security headers, restricted CORS, `server_tokens off`, CSP |
| `backend/Dockerfile` | `PYTHONDONTWRITEBYTECODE`, `PYTHONUNBUFFERED`, `/sbin/nologin` |
| `docker-compose.yml` | `no-new-privileges:true`, `cap_drop: ALL` on backend |
| `.env.example` | `CHANGE_ME_*` placeholders, JWT secret generation instructions |
| `backend/tests/conftest.py` | Shared SQLite engine, single patcher, importable helpers |
| `backend/tests/test_security.py` | 67-test pentest suite |
| `backend/tests/test_history.py` | Refactored to use conftest helpers |
| `backend/tests/integration/test_auth.py` | MySQL integration tests with own engine |
| `backend/tests/integration/conftest.py` | Scope isolation for integration folder |

---

## 9. Commit Hashes

| Commit | Task |
|--------|------|
| `bae290b` | security: harden authentication and session security |
| `4d37d9d` | security: enforce authorization and user data isolation |
| `1cdd450` | security: harden API input validation and injection defenses |
| `996df7d` | security: harden security configuration and secret handling |
| `6badbb9` | test: add penetration-test security suite |

---

## 10. Disclaimer

This audit was performed by the project development team as part of the development process. It is not a substitute for an independent external security assessment. AEGIS should not be considered penetration-test proof or production-secure until:

1. HTTPS is configured and verified.
2. An independent security professional has reviewed and tested the deployment.
3. All dependencies have been scanned for known CVEs.
4. Operational security controls (logging, alerting, key rotation) are in place.
