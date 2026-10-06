# AEGIS

AEGIS is a personal cybersecurity dashboard that consolidates common security analysis tasks into a single authenticated web application. It provides deterministic analysis of URLs, emails, and passwords, an AI-powered security assistant backed by Google Gemini, and a dashboard that tracks results over time.

The project was built as a semester capstone by a three-person team. It is not intended for production deployment in its current form, but it demonstrates a complete full-stack implementation with a security-conscious design.

---

## Table of Contents

- [Why AEGIS](#why-aegis)
- [Key Features](#key-features)
- [System Architecture](#system-architecture)
- [Project Structure](#project-structure)
- [Developer Setup](#developer-setup)
- [API Overview](#api-overview)
- [Security Considerations](#security-considerations)
- [Testing](#testing)
- [Development Workflow](#development-workflow)
- [Future Scope](#future-scope)
- [Contributors](#contributors)
- [License](#license)

---

## Why AEGIS

Most individuals encounter phishing links, suspicious emails, and weak passwords regularly, but have no single tool to inspect them quickly without relying on disconnected online scanners that may log submitted data. AEGIS provides:

- A self-hosted dashboard with no third-party data sharing for core analysis
- Deterministic, rule-based analysis that does not depend on external threat databases
- An AI assistant for plain-English explanations of results, without sending raw passwords or email bodies to the AI
- A persistent scan history tied to an authenticated user account

---

## Key Features

### Implemented

**Authentication**
- User registration and login with bcrypt password hashing
- JWT-based session management (Bearer token, configurable expiry)
- Role-based model (`user` / `admin`) with protected routes
- Per-request authorization; users can only access their own data

**Security Dashboard**
- Real-time summary of all scans for the authenticated user
- Computed security score based on threat distribution
- Threat breakdown by severity (critical, high, medium, low, safe)
- Recent scan list with risk level and type
- Scan counts by type and scans-this-week metric

**URL Analysis**
- Deterministic structural analysis of URLs (no external lookups)
- Detects: brand impersonation, IP-based addresses, obfuscated IPs, risky TLDs, excessive subdomains, deceptive userinfo, open redirects, homograph/punycode labels, excessive percent-encoding, suspicious keywords
- Per-indicator severity ratings with weighted scoring
- Results stored as scan records linked to the authenticated user

**Email / Phishing Analysis**
- Analyses sender, reply-to, subject, body, links, and attachment names
- Detects: sender/reply-to domain mismatch, urgency and threat language, credential and payment requests, executable and macro attachments, URL shorteners, impersonation keywords, prize scam patterns, generic greetings
- Email body is never stored or forwarded to any external service
- Results stored with subject as the scan target (body excluded)

**Password Analysis**
- Entropy calculation, character class breakdown, pattern detection
- Strength levels: very weak, weak, moderate, strong, very strong
- Password is never stored, logged, or sent to Gemini or any external service
- No scan record created (stateless by design)

**AI Security Assistant**
- Conversational interface backed by Google Gemini
- Context-aware: can receive safe scan metadata to give result-specific guidance
- Raw passwords and full email bodies are never included in prompts
- Per-user rate limiting (15 messages / 60 s)
- Graceful fallback when Gemini is unavailable or unconfigured
- Session limited to 6 questions per conversation

**AI Explanation Panel**
- Available after URL, email, and password analysis
- Sends only indicator names, severity levels, and safe metadata to Gemini
- Returns structured overview, indicator breakdown, and recommendations
- Deterministic fallback when AI is unavailable

**Scan History** *(planned — stub page)*
- UI placeholder exists; full browsable history with filters is not yet implemented

**Reports** *(planned — stub page)*
- UI placeholder exists; PDF/export generation is not yet implemented

---

## System Architecture

AEGIS uses a monolithic FastAPI backend served behind an Nginx API gateway. All service groups (auth, analysis, AI, reports) share one Python process and one database connection pool. This is appropriate for a three-person semester project; splitting into independent services would require duplicating JWT validation, DB session management, and Pydantic models without meaningful benefit at this scale.

```mermaid
graph TD
    Browser["Browser (React SPA)"]

    subgraph Docker["Docker Compose stack"]
        Gateway["Nginx gateway (port 80)"]
        Backend["FastAPI backend (port 8000, internal)"]
        DB["MySQL 8.0 (port 3306, internal)"]
    end

    Gemini["Google Gemini API (external)"]

    Browser -->|"HTTP /api/*"| Gateway
    Browser -->|"HTTP / (static)"| Gateway
    Gateway -->|"proxy /api/*"| Backend
    Backend -->|SQLAlchemy ORM| DB
    Backend -->|"HTTPS (google-genai SDK)"| Gemini
```

### Routing table

| Path prefix | Handled by | Notes |
|-------------|-----------|-------|
| `/api/auth/*` | FastAPI auth router | Register, login, me |
| `/api/v1/dashboard/*` | FastAPI dashboard router | Authenticated summary |
| `/api/v1/analysis/*` | FastAPI analysis routers | URL, email, password |
| `/api/v1/ai/*` | FastAPI AI router | Explain endpoint |
| `/api/v1/assistant/*` | FastAPI assistant router | Chat and status |
| `/api/reports/*` | FastAPI (stub) | Not yet implemented |
| `/health` | Nginx | Gateway liveness |
| `/` | Nginx static | React SPA |

### Technology stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, React Router 7, Vite 6 |
| Backend | Python 3.12, FastAPI 0.115, SQLAlchemy 2, Pydantic 2 |
| Database | MySQL 8.0 |
| AI | Google Gemini (via `google-genai` SDK) |
| Gateway | Nginx 1.27 (Alpine) |
| Auth | JWT (`python-jose`), bcrypt (`passlib`) |
| Containerisation | Docker, Docker Compose |

---

## Project Structure

```
AEGIS/
├── backend/
│   ├── app/
│   │   ├── api/          # Route handlers (auth, dashboard, analysis, ai, assistant)
│   │   ├── core/         # Config (pydantic-settings), database engine, security utils
│   │   ├── models/       # SQLAlchemy ORM models (User, Scan)
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   └── services/     # Business logic (analyzers, Gemini client, assistant)
│   ├── tests/            # pytest test suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/   # Shared UI components (Layout, Sidebar, DashboardCard, Icon, ...)
│   │   ├── context/      # AuthContext (token + user state)
│   │   ├── hooks/        # useDashboard
│   │   ├── pages/        # One file per route
│   │   └── services/     # api.js — all fetch calls centralised here
│   ├── Dockerfile
│   └── package.json
├── gateway/
│   ├── nginx.conf        # API gateway and static file config
│   └── Dockerfile
├── database/
│   ├── schema.sql        # Table definitions
│   └── seed.sql          # Optional seed data
├── docs/
│   └── architecture/     # Architecture documentation
├── scripts/
│   └── verify_stack.py   # Validates Docker stack configuration
├── docker-compose.yml
├── docker-compose.override.yml
└── .env.example
```

---

## Developer Setup

### Prerequisites

| Tool | Minimum version | Notes |
|------|----------------|-------|
| Python | 3.12 | Required for backend |
| Node.js | 18 | Required for frontend |
| npm | 9 | Bundled with Node.js |
| MySQL | 8.0 | Local install or Docker |
| Docker + Docker Compose | 24 / 2.20 | Optional — for containerised setup |

A Google Gemini API key is required for AI features. The application runs without one; AI endpoints return deterministic fallback responses instead.

---

### 1. Clone the repository

```bash
git clone <repository-url>
cd AEGIS
```

### 2. Environment variables

```bash
cp .env.example .env
```

Open `.env` and set the following values. Never commit this file.

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | SQLAlchemy connection string. For local dev: `mysql+pymysql://user:password@localhost:3306/aegis` |
| `JWT_SECRET_KEY` | Random string, minimum 32 characters |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime in minutes (default: 480) |
| `GEMINI_API_KEY` | Google Gemini API key. Leave as placeholder to disable AI features |
| `MYSQL_ROOT_PASSWORD` | Used by Docker Compose to initialise MySQL |
| `MYSQL_USER` | Application database user |
| `MYSQL_PASSWORD` | Application database user password |
| `MYSQL_DATABASE` | Database name (default: `aegis`) |
| `VITE_API_URL` | Frontend API base URL. Set to `http://localhost:8000/api` for local dev |

---

### Option A: Docker Compose (recommended)

This runs the complete stack (MySQL, backend, Nginx gateway, React build) with a single command.

```bash
# 1. Build the React frontend into the shared volume
docker compose --profile build up --build frontend

# 2. Start MySQL, backend, and gateway
docker compose up --build -d
```

The application is available at `http://localhost`.

To stop:

```bash
docker compose down
```

To stop and remove volumes (including the database):

```bash
docker compose down -v
```

**After code changes:**

```bash
docker compose up --build -d
```

---

### Option B: Local development (without Docker)

#### Database

Create a MySQL database and user:

```sql
CREATE DATABASE aegis CHARACTER SET utf8mb4;
CREATE USER 'aegis_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON aegis.* TO 'aegis_user'@'localhost';
FLUSH PRIVILEGES;
```

Run the schema:

```bash
mysql -u aegis_user -p aegis < database/schema.sql
```

Update `DATABASE_URL` in `.env`:

```
DATABASE_URL=mysql+pymysql://aegis_user:your_password@localhost:3306/aegis
```

#### Backend

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r backend/requirements.txt

uvicorn backend.app.main:app --reload
```

The API is available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

> **Note:** The backend reads `.env` from the repository root automatically via pydantic-settings.

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

The dev server runs at `http://localhost:5173` by default. Set `VITE_API_URL=http://localhost:8000/api` in `.env` (the frontend Vite config picks this up).

---

### Gemini configuration

Obtain a Gemini API key from [Google AI Studio](https://aistudio.google.com/). Set it in `.env`:

```
GEMINI_API_KEY=your_key_here
```

If the key is absent or set to the placeholder value, all AI endpoints return structured fallback responses. Core security analysis (URL, email, password) is not affected.

---

## API Overview

All API routes are prefixed with `/api`. The backend also serves interactive documentation at `/docs` (Swagger UI) and `/redoc`.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/auth/register` | No | Create a new user account |
| `POST` | `/api/auth/login` | No | Authenticate and receive a JWT |
| `GET` | `/api/auth/me` | Yes | Return the current user |
| `GET` | `/api/v1/dashboard/summary` | Yes | Threat stats, recent scans, weekly count |
| `POST` | `/api/v1/analysis/url` | Yes | Analyse a URL |
| `POST` | `/api/v1/analysis/email` | Yes | Analyse an email for phishing indicators |
| `POST` | `/api/v1/analysis/password` | Yes | Analyse password strength (no storage) |
| `POST` | `/api/v1/ai/explain` | Yes | Get an AI explanation of scan evidence |
| `GET` | `/api/v1/assistant/status` | Yes | Check AI assistant availability |
| `POST` | `/api/v1/assistant/chat` | Yes | Send a message to the AI assistant |

Rate limits are enforced per authenticated user in memory:

| Endpoint group | Limit |
|---------------|-------|
| URL analysis | 30 requests / 60 s |
| Email analysis | 20 requests / 60 s |
| AI explain | 10 requests / 60 s |
| AI assistant | 15 requests / 60 s |

> Rate limits are per-process. In a multi-worker deployment they are not shared across workers.

---

## Security Considerations

The following practices are implemented in the current codebase:

**Authentication and authorisation**
- Passwords are hashed with bcrypt before storage; plaintext is never persisted
- JWTs include `sub`, `exp`, and `iat` claims; both `sub` and `exp` are required on decode
- `JWT_SECRET_KEY` is validated to a minimum of 32 characters at startup
- All protected routes use a FastAPI `Depends` guard; user ID is taken from the verified token, never from the request body
- Database queries filter by `user_id` from the token — users cannot access other users' data

**Input validation**
- All request bodies are validated by Pydantic schemas with explicit field constraints
- URL schema rejects non-HTTP(S) schemes and hostless inputs
- Dict fields (`context_fields`, `safe_metadata`) have per-key and per-value length caps to prevent unbounded inputs
- Login password is capped at 256 characters to prevent bcrypt CPU exhaustion

**Sensitive data handling**
- Passwords are never stored, logged, or forwarded to Gemini
- Email bodies are analysed in memory and never persisted or forwarded to AI
- URL query parameter values are redacted before storage
- The Gemini API key is server-side only; it is never included in any API response
- API key is redacted from error strings and log output before they are stored or written
- `User.__repr__` omits the email address to prevent PII appearing in logs

**Transport and configuration**
- All secrets are loaded from environment variables via pydantic-settings; no secrets in source code
- `.env` and `.env.*` are excluded from Git via `.gitignore`
- TLS verification of Gemini API calls uses the system certificate store; a warning is logged if verification is disabled
- A global exception handler returns a generic 500 message without stack trace details

**AI safety**
- Gemini is used for explanation only; it is not involved in the risk determination
- All AI output is validated and sanitised before being returned to the client
- A deterministic fallback is returned if Gemini is unavailable, quota-exhausted, or returns an empty response

This application is not hardened for public internet deployment. It does not implement HTTPS termination, CSRF protection, or production-grade rate limiting.

---

## Testing

Tests are located in `backend/tests/` and use pytest.

```bash
# Run all backend tests
pytest

# Run a specific test file
pytest backend/tests/test_url_analyzer.py -v

# Run with short tracebacks
pytest --tb=short
```

### Test coverage

| File | What it covers |
|------|---------------|
| `test_auth.py` | Registration, login, JWT, `/me` endpoint (requires a running MySQL database) |
| `test_url_analyzer.py` | Deterministic URL analysis service — 40+ cases |
| `test_phishing_analyzer.py` | Deterministic email analysis service — 50+ cases |
| `test_password_analyzer.py` | Password scoring and entropy |
| `test_assistant.py` | Assistant service — prompt building, sanitisation, follow-up generation (Gemini mocked) |
| `test_security.py` | Auth hardening, data isolation, input validation (uses SQLite in-memory database) |
| `test_url_corpus.py` | Batch evaluation against a URL corpus in `backend/tests/data/` |

`test_auth.py` connects to the database specified in `.env`. All other tests run without a database or network connection.

---

## Development Workflow

### Branching

```
main          — stable, reviewed code
feature/<name> — new features
fix/<name>    — bug fixes
docs/<name>   — documentation only
```

### Commit convention

```
feat(<scope>):   new feature
fix(<scope>):    bug fix
style(<scope>):  formatting, CSS, no logic change
refactor:        code change with no behaviour change
test:            adding or updating tests
docs:            documentation only
chore:           build, config, dependency changes
```

Examples:

```
feat(auth): add JWT refresh token support
fix(url-analyzer): correct handling of punycode labels
docs: rewrite project README
```

### Verifying the Docker stack

```bash
python scripts/verify_stack.py
```

This checks that all required files exist, services are defined in `docker-compose.yml`, and configuration is consistent.

---

## Future Scope

The following capabilities are identified as next steps but are not implemented:

- **Scan History page** — browsable history with filtering by type, date, and risk level
- **Reports page** — PDF or CSV export of scan results
- **Profile page** — account settings, password change
- **HTTPS** — TLS termination at the gateway for any internet-facing deployment
- **Persistent rate limiting** — Redis-backed rate limits that work across multiple workers
- **Alembic migrations** — the schema is currently created via `create_all` on startup; a migration system is needed for schema changes in deployed environments
- **Admin interface** — user management for the admin role that is modelled but not exposed

---

## Contributors

Built by a three-person team as a university semester project.

---

## License

MIT — see [LICENSE](LICENSE) for the full text.
