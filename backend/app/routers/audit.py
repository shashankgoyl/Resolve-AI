from __future__ import annotations

from fastapi import APIRouter, Query

from app.models.schemas import AuditLogEntry
from app.services import run_store

router = APIRouter(prefix="/api/audit-logs", tags=["audit"])


@router.get("", response_model=list[AuditLogEntry])
def list_audit_logs(ticket_id: str | None = Query(default=None), limit: int = Query(default=200, le=500)):
    return run_store.get_audit_log(ticket_id=ticket_id, limit=limit)
