"""AEGIS FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.app.api.ai import router as ai_router
from backend.app.api.assistant import router as assistant_router
from backend.app.api.reports import router as reports_router
from backend.app.api.auth import router as auth_router
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.password import router as password_router
from backend.app.api.phishing import router as phishing_router
from backend.app.api.url_analysis import router as url_router
from backend.app.core.config import settings
from backend.app.core.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup â€” dev convenience; use Alembic in production
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="AEGIS API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://127.0.0.1:5173",
        "http://localhost:80",
        "http://localhost",        # Nginx gateway
        "http://gateway",          # inter-container
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api")
app.include_router(dashboard_router, prefix="/api")
app.include_router(password_router, prefix="/api")
app.include_router(url_router, prefix="/api")
app.include_router(phishing_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(assistant_router, prefix="/api")
app.include_router(reports_router, prefix="/api")


@app.get("/health", tags=["health"])
def health() -> dict:
    return {"status": "ok", "env": settings.APP_ENV}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    # Do not log exc details to the response â€” stack traces must not reach the client
    return JSONResponse(status_code=500, content={"detail": "An internal error occurred."})

# Note: FastAPI's default RequestValidationError handler returns 422 with field paths,
# which is acceptable for API clients. No override needed.

