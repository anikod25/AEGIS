# AEGIS Architecture

## Overview

AEGIS uses a single FastAPI backend served behind an Nginx API gateway.
All four logical service groups (auth, analysis, AI, reports) live in one
FastAPI process sharing one database connection pool — appropriate for a
3-person semester project.

## Service Graph

```
Browser / curl
     │
     ▼
  Nginx gateway  (port 80)
  gateway container
     │
     ├── /api/*  ──────────────►  backend:8000  (FastAPI)
     │                                │
     │                                ├── /api/auth/*
     │                                ├── /api/v1/analysis/*
     │                                ├── /api/v1/dashboard/*
     │                                ├── /api/v1/ai/*
     │                                ├── /api/v1/assistant/*
     │                                └── /api/reports/*
     │                                         │
     │                                         ▼
     │                                  mysql:3306
     │                                  (MySQL 8.0)
     │
     └── /  ────────────────────►  /usr/share/nginx/html
                                   (React static build)
```

## Gateway Routing Table

| Path prefix         | Proxied to          | Notes                        |
|---------------------|---------------------|------------------------------|
| `/api/`             | `http://backend:8000` | All API calls               |
| `/health`           | (local Nginx)       | Gateway liveness check       |
| `/`                 | static files        | React SPA, try_files to index.html |

## Docker Compose Services

| Service    | Image / Build        | Exposed | Purpose                        |
|------------|----------------------|---------|--------------------------------|
| `mysql`    | `mysql:8.0`          | internal| Database                       |
| `backend`  | `./backend/Dockerfile`| 8000 (internal) | FastAPI app      |
| `gateway`  | `./gateway/Dockerfile`| 80→host | Nginx gateway + static files   |
| `frontend` | `./frontend/Dockerfile`| —      | Build-only, populates volume   |

## How to Run

### Production (full stack)
```bash
# 1. Copy and fill in .env
cp .env.example .env
# edit .env with real secrets

# 2. Build frontend and populate the shared volume
docker compose --profile build up --build frontend

# 3. Start the stack
docker compose up --build -d
```

### After code changes
```bash
docker compose up --build -d
```

### Local dev (without Docker)
```bash
# Backend
cd backend && uvicorn app.main:app --reload

# Frontend  
cd frontend && VITE_API_URL=http://localhost:8000/api npm run dev
```

## Environment Variable Flow

```
.env file
  └──► docker compose (env_file: .env)
          ├──► backend container  (DATABASE_URL, JWT_SECRET_KEY, GEMINI_API_KEY, …)
          ├──► mysql container    (MYSQL_ROOT_PASSWORD, MYSQL_DATABASE, …)
          └──► gateway container  (GATEWAY_PORT via ports mapping)
```

`VITE_API_URL` is a **build-time** variable passed as `ARG` in `frontend/Dockerfile`.
In Docker it is baked as `/api`; in local dev set it to `http://localhost:8000/api`.

## Dev vs Docker Mode

| Concern              | Local dev                        | Docker                        |
|----------------------|----------------------------------|-------------------------------|
| Frontend URL         | `http://localhost:5173`          | `http://localhost`            |
| API base URL         | `http://localhost:8000/api`      | `/api` (same-origin via Nginx)|
| DB host              | `localhost` (or Docker MySQL)    | `mysql` (Docker network name) |
| CORS handled by      | FastAPI middleware               | Nginx gateway headers         |
