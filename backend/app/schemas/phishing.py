"""Pydantic schemas for phishing email analysis."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from backend.app.schemas.url_analysis import Indicator

# Null bytes and CRLF sequences are never valid in submitted email metadata.
_INVALID_CHARS_RE = re.compile(r"[\x00\r\n]")


def _strip_invalid(value: str, field: str) -> str:
    """Raise ValueError if *value* contains null bytes or CRLF sequences."""
    if _INVALID_CHARS_RE.search(value):
        raise ValueError(f"{field} contains invalid control characters.")
    return value


class EmailAnalysisRequest(BaseModel):
    sender:          str = Field(default="", max_length=500)
    reply_to:        str = Field(default="", max_length=500)
    subject:         str = Field(default="", max_length=1000)
    body:            str = Field(min_length=1, max_length=50_000)
    links:           list[str] = Field(default_factory=list, max_length=50)
    attachment_names:list[str] = Field(default_factory=list, max_length=20)

    @field_validator("sender", "reply_to", "subject")
    @classmethod
    def no_control_chars(cls, v: str) -> str:
        return _strip_invalid(v, "Field")

    @field_validator("body")
    @classmethod
    def body_not_blank(cls, v: str) -> str:
        # Null bytes in body are suspicious but we accept CRLF (email convention)
        if "\x00" in v:
            raise ValueError("body contains invalid null bytes.")
        if not v.strip():
            raise ValueError("body must contain non-whitespace content")
        return v

    @field_validator("links", mode="before")
    @classmethod
    def trim_links(cls, v: list) -> list:
        cleaned = []
        for link in v:
            s = str(link)[:2048].strip()
            # Drop links containing null bytes
            if "\x00" not in s and s:
                cleaned.append(s)
        return cleaned

    @field_validator("attachment_names", mode="before")
    @classmethod
    def trim_attachment_names(cls, v: list) -> list:
        cleaned = []
        for name in v:
            s = str(name)[:255].strip()
            if "\x00" not in s and s:
                cleaned.append(s)
        return cleaned


class EmailAnalysisResult(BaseModel):
    scan_id: int
    risk_score: int
    risk_level: Literal["safe", "low", "medium", "high", "critical"]
    indicators: list[Indicator]
    recommendations: list[str]
    scanned_at: datetime
    analysis_version: str | None = None
