"""Pydantic schemas for URL analysis — v2."""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from urllib.parse import urlsplit
import re

from pydantic import BaseModel, Field, field_validator

# Schemes that are structurally valid but must never be analysed —
# they could be used for injection or to trick the analyser.
_BLOCKED_SCHEMES = frozenset({
    "javascript", "data", "vbscript", "file", "blob",
    "about", "chrome", "chrome-extension", "moz-extension",
})

# Characters that should never appear in a URL submitted for analysis.
# Null bytes and CRLF sequences are canonically invalid and indicate
# an injection attempt.
_INVALID_CHARS_RE = re.compile(r"[\x00\r\n]")


class UrlAnalysisRequest(BaseModel):
    url: str = Field(min_length=4, max_length=2048)

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()

        # Reject null bytes and CRLF injection attempts
        if _INVALID_CHARS_RE.search(v):
            raise ValueError("URL contains invalid characters.")

        # Scheme check — case-insensitive, handles mixed-case bypasses
        if not re.match(r"^https?://", v, re.IGNORECASE):
            # Before raising, check whether a blocked scheme was supplied
            scheme_match = re.match(r"^([a-zA-Z][a-zA-Z0-9+\-.]*):\/\/", v)
            if scheme_match:
                scheme = scheme_match.group(1).lower()
                if scheme in _BLOCKED_SCHEMES:
                    raise ValueError(f"URL scheme '{scheme}' is not permitted.")
            raise ValueError("URL must start with http:// or https://")

        # Double-check after normalization that the scheme isn't blocked
        parsed = urlsplit(v.replace("\\", "/"))
        if parsed.scheme.lower() in _BLOCKED_SCHEMES:
            raise ValueError(f"URL scheme '{parsed.scheme}' is not permitted.")

        # Reject empty or whitespace-only host
        if not parsed.netloc or not parsed.netloc.replace("@", "").strip("/"):
            raise ValueError("URL must contain a valid host.")

        return v


class Indicator(BaseModel):
    id: str | None = None
    name: str
    detail: str
    severity: Literal["info", "low", "medium", "high"]
    weight: int | None = None


class UrlAnalysisResult(BaseModel):
    scan_id: int
    normalized_url: str
    risk_score: int
    risk_level: Literal["safe", "low", "medium", "high", "critical"]
    indicators: list[Indicator]
    recommendations: list[str]
    scanned_at: datetime
    analysis_version: str | None = None
