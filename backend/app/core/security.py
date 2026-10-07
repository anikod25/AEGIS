"""Password hashing and JWT utilities."""

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from backend.app.core.config import settings

# ---------------------------------------------------------------------------
# bcrypt cost factor — 12 rounds is the current recommended minimum
# ---------------------------------------------------------------------------
_BCRYPT_ROUNDS = 12

# Pre-computed dummy hash used for timing-safe login rejection.
# A valid 60-character bcrypt hash produced with an unused random password.
# Purpose: ensure the rejection path for unknown email addresses takes the
# same wall-clock time as the rejection path for wrong passwords, preventing
# user enumeration via timing difference.
_DUMMY_HASH = bcrypt.hashpw(b"__aegis_dummy__", bcrypt.gensalt(_BCRYPT_ROUNDS)).decode()


# ---------------------------------------------------------------------------
# Password helpers
# ---------------------------------------------------------------------------

def hash_password(plain: str) -> str:
    """Return a bcrypt hash of *plain*. Never call this with an already-hashed value."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt(_BCRYPT_ROUNDS)).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Return True when *plain* matches *hashed*.

    Always constant-time relative to the hash being checked.
    Never raises — returns False on malformed input.
    """
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def dummy_verify() -> None:
    """Run a full bcrypt verify against a known dummy hash.

    Call this when a login attempt targets a non-existent email to prevent
    timing-based user enumeration. The result is intentionally discarded.
    """
    # Always False — we discard the result
    try:
        bcrypt.checkpw(b"__aegis_dummy_probe__", _DUMMY_HASH.encode())
    except Exception:
        pass


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------

def create_access_token(subject: Any, expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token.

    Args:
        subject: Value stored in the 'sub' claim (typically user id as str).
        expires_delta: Custom expiry; falls back to the configured default.

    The 'iat' (issued-at) and 'exp' (expiry) claims use UTC-aware datetimes.
    The 'typ' claim is set to 'access' to prevent token-type confusion.
    """
    now    = datetime.now(timezone.utc)
    expire = now + (
        expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": str(subject),
        "exp": expire,
        "iat": now,
        "typ": "access",
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and verify a JWT. Raises JWTError on failure.

    Enforces:
    - Correct algorithm (no algorithm confusion)
    - 'sub' and 'exp' claims present
    - Signature valid
    - Not expired
    """
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        options={"require": ["sub", "exp"]},
    )
