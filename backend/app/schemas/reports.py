"""Pydantic schemas for scan history and reports endpoints."""
from __future__ import annotations

from datetime import datetime

from pydantic import AliasChoices, BaseModel, Field


class ScanListItem(BaseModel):
    id: int
    scan_type: str
    target: str
    risk_level: str
    risk_score: int
    scanned_at: datetime = Field(validation_alias=AliasChoices("scanned_at", "created_at"))

    model_config = {"from_attributes": True, "populate_by_name": True}


class ScanDetail(BaseModel):
    id: int
    scan_type: str
    target: str
    risk_level: str
    risk_score: int
    summary: str | None = None
    scanned_at: datetime = Field(validation_alias=AliasChoices("scanned_at", "created_at"))

    model_config = {"from_attributes": True, "populate_by_name": True}


class ScanListResponse(BaseModel):
    items: list[ScanListItem]
    total: int
    page: int
    per_page: int
    pages: int


class ReportSummary(BaseModel):
    """Aggregate report derived from scan data — no separate DB table."""
    total_scans: int
    by_type: dict[str, int]
    by_risk: dict[str, int]
    score: int | None       # None when no scans exist
    generated_at: datetime
