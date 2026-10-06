"""Scan history and reports API.

Routes
------
GET  /api/v1/scans                 paginated scan list (authenticated user only)
GET  /api/v1/scans/{scan_id}       single scan detail
DELETE /api/v1/scans/{scan_id}     delete own scan
GET  /api/v1/reports               aggregate report for authenticated user
GET  /api/v1/reports/{scan_id}     scan detail (alias)

Ownership is enforced on every query: user_id is always filtered to
current_user.id so a user can never read or delete another user's scan.
"""
from __future__ import annotations

import math
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.core.database import get_db
from backend.app.models.scan import RiskLevel, Scan, ScanType
from backend.app.models.user import User
from backend.app.schemas.reports import (
    ReportSummary,
    ScanDetail,
    ScanListItem,
    ScanListResponse,
)

router = APIRouter(prefix="/v1", tags=["history"])

_MAX_PER_PAGE = 100


def _owned_scan_or_404(scan_id: int, user_id: int, db: Session) -> Scan:
    """Return the scan only if it belongs to user_id, else raise 404.

    Using 404 (not 403) intentionally — we don't confirm the scan exists
    for other users.
    """
    scan = (
        db.query(Scan)
        .filter(Scan.id == scan_id, Scan.user_id == user_id)
        .first()
    )
    if scan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found.")
    return scan


# ---------------------------------------------------------------------------
# Scan history list
# ---------------------------------------------------------------------------

@router.get(
    "/scans",
    response_model=ScanListResponse,
    summary="List scans for the authenticated user",
)
def list_scans(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=_MAX_PER_PAGE),
    scan_type: str | None = Query(None),
    risk_level: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScanListResponse:
    """Return a paginated list of the current user's scans, newest first."""
    q = db.query(Scan).filter(Scan.user_id == current_user.id)

    if scan_type:
        try:
            q = q.filter(Scan.scan_type == ScanType(scan_type))
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Invalid scan_type: {scan_type}")

    if risk_level:
        try:
            q = q.filter(Scan.risk_level == RiskLevel(risk_level))
        except ValueError:
            raise HTTPException(status_code=422, detail=f"Invalid risk_level: {risk_level}")

    total: int = q.count()
    pages = max(1, math.ceil(total / per_page))
    items = (
        q.order_by(Scan.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return ScanListResponse(
        items=[ScanListItem.model_validate(s) for s in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


# ---------------------------------------------------------------------------
# Single scan detail
# ---------------------------------------------------------------------------

@router.get(
    "/scans/{scan_id}",
    response_model=ScanDetail,
    summary="Get a single scan by ID (must be owned by the authenticated user)",
)
def get_scan(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScanDetail:
    scan = _owned_scan_or_404(scan_id, current_user.id, db)
    return ScanDetail.model_validate(scan)


# ---------------------------------------------------------------------------
# Delete scan
# ---------------------------------------------------------------------------

@router.delete(
    "/scans/{scan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a scan (must be owned by the authenticated user)",
)
def delete_scan(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    scan = _owned_scan_or_404(scan_id, current_user.id, db)
    db.delete(scan)
    db.commit()


# ---------------------------------------------------------------------------
# Aggregate report
# ---------------------------------------------------------------------------

@router.get(
    "/reports",
    response_model=ReportSummary,
    summary="Get an aggregate security report for the authenticated user",
)
def get_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReportSummary:
    uid = current_user.id

    # Counts by risk level
    risk_rows = (
        db.query(Scan.risk_level, func.count(Scan.id))
        .filter(Scan.user_id == uid)
        .group_by(Scan.risk_level)
        .all()
    )
    by_risk: dict[str, int] = {lvl.value: 0 for lvl in RiskLevel}
    for risk_level, count in risk_rows:
        by_risk[risk_level.value] = count

    total = sum(by_risk.values())

    # Counts by scan type
    type_rows = (
        db.query(Scan.scan_type, func.count(Scan.id))
        .filter(Scan.user_id == uid)
        .group_by(Scan.scan_type)
        .all()
    )
    by_type: dict[str, int] = {t.value: 0 for t in ScanType}
    for scan_type, count in type_rows:
        by_type[scan_type.value] = count

    # Security score — same formula as dashboard
    score: int | None = None
    if total > 0:
        penalty = (
            by_risk.get("critical", 0) * 20
            + by_risk.get("high", 0) * 12
            + by_risk.get("medium", 0) * 5
            + by_risk.get("low", 0) * 1
        )
        score = max(0, 100 - penalty)

    return ReportSummary(
        total_scans=total,
        by_type=by_type,
        by_risk=by_risk,
        score=score,
        generated_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# Report detail — alias for scan detail
# ---------------------------------------------------------------------------

@router.get(
    "/reports/{scan_id}",
    response_model=ScanDetail,
    summary="Get scan detail via the reports path",
)
def get_report_detail(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ScanDetail:
    scan = _owned_scan_or_404(scan_id, current_user.id, db)
    return ScanDetail.model_validate(scan)
