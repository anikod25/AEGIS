<div align="center">

# AEGIS

**A personal cybersecurity dashboard for analysing URLs, emails, and passwords — in one authenticated place.**

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

[Features](#key-features) · [Architecture](#system-architecture) · [Setup](#developer-setup) · [API](#api-overview) · [Security](#security-considerations) · [Roadmap](#future-scope)

</div>

---

## Overview

AEGIS consolidates common security analysis tasks into a single web application. It provides deterministic analysis of URLs, emails, and passwords, an AI-powered security assistant backed by Google Gemini, and a dashboard that tracks results over time.

Built as a semester capstone by a three-person team, AEGIS demonstrates a complete full-stack implementation with a security-conscious design. It is not intended for production deployment in its current form.

## Why AEGIS

Most people run into phishing links, suspicious emails, and weak passwords regularly, yet have no single tool to inspect them without relying on disconnected online scanners that may log submitted data. AEGIS offers:

- **Self-hosted analysis** — no third-party data sharing for core features
- **Deterministic, rule-based detection** — no dependence on external threat databases
- **Plain-English AI explanations** — raw passwords and email bodies are never sent to the AI
- **Persistent scan history** — tied to an authenticated user account

---

## Key Features

| Feature | Status | Summary |
|---------|:------:|---------|
| [Authentication](#authentication) | Implemented | Registration, login, JWT sessions, role-based access |
| [Security Dashboard](#security-dashboard) | Implemented | Security score, threat breakdown, recent scans |
| [URL Analysis](#url-analysis) | Implemented | Structural analysis with weighted indicator scoring |
| [Email / Phishing Analysis](#email--phishing-analysis) | Implemented | Sender, content, link, and attachment checks |
| [Password Analysis](#password-analysis) | Implemented | Entropy, character classes, pattern detection |
| [AI Security Assistant](#ai-security-assistant) | Implemented | Context-aware chat powered by Google Gemini |
| [AI Explanation Panel](#ai-explanation-panel) | Implemented | Structured explanations of scan evidence |
| [Scan History](#scan-history) | Implemented | Browsable scan history with filtering |
| [Reports](#reports) | Implemented | Scan-result report generation and export |

### Authentication
- Registration and login with bcrypt password hashing
- JWT-based sessions (Bearer token, configurable expiry)
- Role-based model (`user` / `admin`) with protected routes
- Per-request authorisation — users can only access their own data

### Security Dashboard
- Real-time summary of all scans for the authenticated user
- Computed security score based on threat distribution
- Threat breakdown by severity: critical, high, medium, low, safe
- Recent scan list with risk level and type
- Scan counts by type and a scans-this-week metric

### URL Analysis
- Deterministic structural analysis with no external lookups
- Detects brand impersonation, IP-based and obfuscated addresses, risky TLDs, excessive subdomains, deceptive userinfo, open redirects, homograph/punycode labels, excessive percent-encoding, and suspicious keywords
- Per-indicator severity ratings with weighted scoring
- Results stored as scan records linked to the user

### Email / Phishing Analysis
- Analyses sender, reply-to, subject, body, links, and attachment names
- Detects sender/reply-to domain mismatch, urgency and threat language, credential and payment requests, executable and macro attachments, URL shorteners, impersonation keywords, prize-scam patterns, and generic greetings
- The email body is **never stored or forwarded** to any external service
- Results are stored with the subject as the scan target (body excluded)

### Password Analysis
- Entropy calculation, character class breakdown, and pattern detection
- Five strength levels: very weak, weak, moderate, strong, very strong
- The password is **never stored, logged, or sent** to Gemini or any external service
- Stateless by design — no scan record is created

### AI Security Assistant
- Conversational interface backed by Google Gemini
- Context-aware: accepts safe scan metadata for result-specific guidance
- Raw passwords and full email bodies are never included in prompts
- Per-user rate limiting (15 messages / 60 s) and a 6-question limit per conversation
- Graceful fallback when Gemini is unavailable or unconfigured

### AI Explanation Panel
- Available after URL, email, and password analysis
- Sends only indicator names, severity levels, and safe metadata to Gemini
- Returns a structured overview, indicator breakdown, and recommendations
- Deterministic fallback when AI is unavailable

### Scan History

- Browse previously generated scan records
- View scan results tied to the authenticated user
- Filter and review historical scans by relevant scan attributes
- Maintains user-level data isolation

### Reports

- Generate reports from scan results
- Export security analysis results for later reference
- Report functionality is integrated with the authenticated application

---

## System Architecture

AEGIS uses a monolithic FastAPI backend served behind an Nginx API gateway. All service groups (auth, analysis, AI, reports) share one Python process and one database connection pool. For a three-person semester project this is the pragmatic choice: splitting into independent services would mean duplicating JWT validation, DB session management, and Pydantic models without meaningful benefit at this scale.

```mermaid
flowchart LR

    Browser["Browser<br/>(React SPA)"]

    subgraph Docker["Docker Compose stack"]
        direction LR

        Gateway["Nginx"]
        Backend["FastAPI"]
        DB[("MySQL")]

        Gateway -->|"proxy /api/*"| Backend
        Backend -->|"SQLAlchemy ORM"| DB
    end

    Gemini["Google Gemini<br/>(external)"]

    Browser -->|"HTTP"| Gateway
    Backend -->|"HTTPS<br/>google-genai SDK"| Gemini
```

### Routing

| Path prefix | Handled by | Notes |
|-------------|-----------|-------|
| `/api/auth/*` | FastAPI auth router | Register, login, me |
| `/api/v1/dashboard/*` | FastAPI dashboard router | Authenticated summary |
| `/api/v1/analysis/*` | FastAPI analysis routers | URL, email, password |
| `/api/v1/ai/*` | FastAPI AI router | Explain endpoint |
| `/api/v1/assistant/*` | FastAPI assistant router | Chat and status |
| `/api/reports/*` | FastAPI reports router | Report generation and export |
| `/health` | Nginx | Gateway liveness |
| `/` | Nginx static | React SPA |

### Technology Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, React Router 7, Vite 6 |
| Backend | Python 3.12, FastAPI 0.115, SQLAlchemy 2, Pydantic 2 |
| Database | MySQL 8.0 |
| AI | Google Gemini (`google-genai` SDK) |
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

> **Note:** A Google Gemini API key is required for AI features. The application runs without one; AI endpoints return deterministic fallback responses instead.

### 1. Clone the repository

```bash
git clone <repository-url>
cd AEGIS
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and set the values below. **Never commit this file.**

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | SQLAlchemy connection string. Local dev: `mysql+pymysql://user:password@localhost:3306/aegis` |
| `JWT_SECRET_KEY` | Random string, minimum 32 characters |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime in minutes (default: `480`) |
| `GEMINI_API_KEY` | Google Gemini API key. Leave as placeholder to disable AI features |
| `MYSQL_ROOT_PASSWORD` | Used by Docker Compose to initialise MySQL |
| `MYSQL_USER` | Application database user |
| `MYSQL_PASSWORD` | Application database user password |
| `MYSQL_DATABASE` | Database name (default: `aegis`) |
| `VITE_API_URL` | Frontend API base URL. Set to `http://localhost:8000/api` for local dev |

### 3. Run the application

#### Option A — Docker Compose (recommended)

Runs the complete stack (MySQL, backend, Nginx gateway, React build) with two commands.

```bash
# 1. Build the React frontend into the shared volume
docker compose --profile build up --build frontend

# 2. Start MySQL, backend, and gateway
docker compose up --build -d
```

The application is available at **http://localhost**.

```bash
# Stop the stack
docker compose down

# Stop and remove volumes (including the database)
docker compose down -v

# Rebuild after code changes
docker compose up --build -d
```

#### Option B — Local development (without Docker)

<details>
<summary><strong>Database</strong></summary>

Create a MySQL database and user:

```sql
CREATE DATABASE aegis CHARACTER SET utf8mb4;
CREATE USER 'aegis_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON aegis.* TO 'aegis_user'@'localhost';
FLUSH PRIVILEGES;
```

Load the schema:

```bash
mysql -u aegis_user -p aegis < database/schema.sql
```

Update `DATABASE_URL` in `.env`:

```
DATABASE_URL=mysql+pymysql://aegis_user:your_password@localhost:3306/aegis
```

</details>

<details>
<summary><strong>Backend</strong></summary>

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r backend/requirements.txt

uvicorn backend.app.main:app --reload
```

The API is available at `http://localhost:8000`, with interactive docs at `http://localhost:8000/docs`.

> The backend reads `.env` from the repository root automatically via pydantic-settings.

</details>

<details>
<summary><strong>Frontend</strong></summary>

```bash
cd frontend
npm install
npm run dev
```

The dev server runs at `http://localhost:5173` by default. Set `VITE_API_URL=http://localhost:8000/api` in `.env`; the Vite config picks it up.

</details>

### Gemini configuration

Obtain a key from [Google AI Studio](https://aistudio.google.com/) and set it in `.env`:

```
GEMINI_API_KEY=your_key_here
```

If the key is absent or left as the placeholder, all AI endpoints return structured fallback responses. Core security analysis (URL, email, password) is unaffected.

---

## API Overview

All routes are prefixed with `/api`. Interactive documentation is served at `/docs` (Swagger UI) and `/redoc`.

| Method | Path | Auth | Description |
|--------|------|:---:|-------------|
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

### Rate limits

Limits are enforced per authenticated user, in memory.

| Endpoint group | Limit |
|---------------|-------|
| URL analysis | 30 requests / 60 s |
| Email analysis | 20 requests / 60 s |
| AI explain | 10 requests / 60 s |
| AI assistant | 15 requests / 60 s |

> Rate limits are per-process. In a multi-worker deployment they are not shared across workers.

---

## Security Considerations

The following practices are implemented in the current codebase.

**Authentication and authorisation**
- Passwords are hashed with bcrypt; plaintext is never persisted
- JWTs include `sub`, `exp`, and `iat` claims; both `sub` and `exp` are required on decode
- `JWT_SECRET_KEY` is validated to a minimum of 32 characters at startup
- Protected routes use a FastAPI `Depends` guard; the user ID comes from the verified token, never the request body
- Database queries filter by `user_id` from the token, so users cannot access other users' data

**Input validation**
- All request bodies are validated by Pydantic schemas with explicit field constraints
- The URL schema rejects non-HTTP(S) schemes and hostless inputs
- Dict fields (`context_fields`, `safe_metadata`) have per-key and per-value length caps to prevent unbounded input
- Login passwords are capped at 256 characters to prevent bcrypt CPU exhaustion

**Sensitive data handling**
- Passwords are never stored, logged, or forwarded to Gemini
- Email bodies are analysed in memory and never persisted or forwarded to AI
- URL query parameter values are redacted before storage
- The Gemini API key is server-side only and never appears in any API response
- The API key is redacted from error strings and log output before they are stored or written
- `User.__repr__` omits the email address to keep PII out of logs

**Transport and configuration**
- All secrets are loaded from environment variables via pydantic-settings; none live in source code
- `.env` and `.env.*` are excluded from Git via `.gitignore`
- Gemini API calls verify TLS using the system certificate store; a warning is logged if verification is disabled
- A global exception handler returns a generic 500 message without stack trace details

**AI safety**
- Gemini is used for explanation only; it plays no part in risk determination
- All AI output is validated and sanitised before being returned to the client
- A deterministic fallback is returned if Gemini is unavailable, quota-exhausted, or returns an empty response

> **Warning: not hardened for public internet deployment.** AEGIS does not implement HTTPS termination, CSRF protection, or production-grade rate limiting.

---

## Testing

Tests live in `backend/tests/` and use pytest.

```bash
# Run all backend tests
pytest

# Run a specific test file
pytest backend/tests/test_url_analyzer.py -v

# Run with short tracebacks
pytest --tb=short
```

| File | Coverage |
|------|----------|
| `test_auth.py` | Registration, login, JWT, `/me` endpoint (requires a running MySQL database) |
| `test_url_analyzer.py` | Deterministic URL analysis — 40+ cases |
| `test_phishing_analyzer.py` | Deterministic email analysis — 50+ cases |
| `test_password_analyzer.py` | Password scoring and entropy |
| `test_assistant.py` | Prompt building, sanitisation, follow-up generation (Gemini mocked) |
| `test_security.py` | Auth hardening, data isolation, input validation (in-memory SQLite) |
| `test_url_corpus.py` | Batch evaluation against a URL corpus in `backend/tests/data/` |

`test_auth.py` connects to the database specified in `.env`. All other tests run without a database or network connection.

---

## Development Workflow

### Branching

| Branch | Purpose |
|--------|---------|
| `main` | Stable, reviewed code |
| `feature/<name>` | New features |
| `fix/<name>` | Bug fixes |
| `docs/<name>` | Documentation only |

### Commit convention

| Prefix | Use for |
|--------|---------|
| `feat(<scope>)` | New feature |
| `fix(<scope>)` | Bug fix |
| `style(<scope>)` | Formatting or CSS, no logic change |
| `refactor` | Code change with no behaviour change |
| `test` | Adding or updating tests |
| `docs` | Documentation only |
| `chore` | Build, config, or dependency changes |

```
feat(auth): add JWT refresh token support
fix(url-analyzer): correct handling of punycode labels
docs: rewrite project README
```

### Verifying the Docker stack

```bash
python scripts/verify_stack.py
```

Checks that all required files exist, services are defined in `docker-compose.yml`, and configuration is consistent.

---

## Future Scope

The following improvements remain as potential next steps:

- [ ] **Profile page** — account settings and password change
- [ ] **HTTPS** — TLS termination at the gateway for any internet-facing deployment
- [ ] **Persistent rate limiting** — Redis-backed limits that work across multiple workers
- [ ] **Alembic migrations** — the schema is currently created via `create_all` on startup; a migration system is needed for schema changes in deployed environments
- [ ] **Admin interface** — user management for the modelled-but-unexposed admin role

---

## Contributors

Built by a three-person team as a university semester project.

## License

Released under the MIT License — see [LICENSE](LICENSE) for the full text.
