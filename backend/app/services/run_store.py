"""
Process-local store for everything the agent produces per ticket:
analysis, evidence, the action timeline, the generated response, and audit
log entries. Used directly in DEMO_MODE, and also as a read-through cache
in front of Supabase in live mode (writes go to both).

This is intentionally simple (module-level dict) rather than a class with
DI, because the whole backend is a single FastAPI process for this
buildathon build — see README for notes on swapping this for Supabase-only
reads in a multi-instance deployment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.models.schemas import (
    AgentAction,
    AgentRun,
    AIDecision,
    AuditLogEntry,
    EmailClassification,
    EngineeringIssue,
    KnowledgeSource,
    Response,
    ResponseStatus,
)


@dataclass
class TicketRunState:
    ticket_id: str
    run: AgentRun | None = None
    analysis: EmailClassification | None = None
    knowledge: list[KnowledgeSource] = field(default_factory=list)
    engineering: list[EngineeringIssue] = field(default_factory=list)
    response: Response | None = None


_STATE: dict[str, TicketRunState] = {}
_AUDIT_LOG: list[AuditLogEntry] = []


def get_state(ticket_id: str) -> TicketRunState:
    if ticket_id not in _STATE:
        _STATE[ticket_id] = TicketRunState(ticket_id=ticket_id)
    return _STATE[ticket_id]


def clear_state(ticket_id: str) -> None:
    _STATE.pop(ticket_id, None)


def all_states() -> dict[str, TicketRunState]:
    return _STATE


def log_audit(
    *, ticket_id: str | None, agent_run_id: str | None, actor_type: str,
    actor_label: str | None, event_type: str, description: str, metadata: dict | None = None,
) -> AuditLogEntry:
    entry = AuditLogEntry(
        id=f"audit-{len(_AUDIT_LOG) + 1}", ticket_id=ticket_id, agent_run_id=agent_run_id,
        actor_type=actor_type, actor_label=actor_label, event_type=event_type,
        description=description, metadata=metadata or {}, created_at=datetime.now(timezone.utc),
    )
    _AUDIT_LOG.append(entry)
    return entry


def get_audit_log(ticket_id: str | None = None, limit: int = 200) -> list[AuditLogEntry]:
    entries = _AUDIT_LOG if ticket_id is None else [e for e in _AUDIT_LOG if e.ticket_id == ticket_id]
    return sorted(entries, key=lambda e: e.created_at, reverse=True)[:limit]
