from __future__ import annotations

import uuid
from datetime import datetime, timezone

from app.core.config import get_settings
from app.core.database import get_supabase
from app.models.schemas import (
    AIDecision,
    Customer,
    EmailMessage,
    Response,
    ResponseStatus,
    SupportTicket,
    TicketDetail,
    TicketPriority,
    TicketStatus,
)
from app.services import demo_data, orchestrator, run_store


def _use_demo() -> bool:
    settings = get_settings()
    return settings.DEMO_MODE or not settings.supabase_configured


def list_tickets() -> list[SupportTicket]:
    if _use_demo():
        return demo_data.get_demo_tickets()

    sb = get_supabase()
    rows = sb.table("support_tickets").select("*, customers(*)").order("created_at", desc=True).execute()
    tickets = []
    for row in rows.data:
        c = row.get("customers") or {}
        tickets.append(SupportTicket(
            id=row["id"], ticket_number=row["ticket_number"],
            customer=Customer(id=c.get("id", ""), email=c.get("email", ""), full_name=c.get("full_name"), company=c.get("company"), plan=c.get("plan")),
            subject=row["subject"], category=row.get("category"), priority=row["priority"], status=row["status"],
            sentiment=row.get("sentiment"), is_demo=row.get("is_demo", False), created_at=row["created_at"],
            resolved_at=row.get("resolved_at"),
        ))
    return tickets


def _find_ticket(ticket_id: str) -> SupportTicket | None:
    for t in list_tickets():
        if t.id == ticket_id:
            return t
    return None


def _get_email(ticket_id: str) -> EmailMessage | None:
    if _use_demo():
        return demo_data.get_demo_email(ticket_id)
    sb = get_supabase()
    rows = sb.table("emails").select("*").eq("ticket_id", ticket_id).eq("direction", "inbound").order("received_at", desc=True).limit(1).execute()
    if not rows.data:
        return None
    row = rows.data[0]
    return EmailMessage(**row)


async def get_ticket_detail(ticket_id: str, force_rerun: bool = False) -> TicketDetail | None:
    ticket = _find_ticket(ticket_id)
    if not ticket:
        return None

    email = _get_email(ticket_id)
    state = run_store.get_state(ticket_id)

    if force_rerun:
        run_store.clear_state(ticket_id)
        state = run_store.get_state(ticket_id)

    if state.run is None and email is not None:
        await orchestrator.run_agent_for_ticket(ticket, email.body_text, email.subject or ticket.subject)
        state = run_store.get_state(ticket_id)

    return TicketDetail(
        **ticket.model_dump(),
        emails=[email] if email else [],
        analysis=state.analysis,
        knowledge_sources=state.knowledge,
        engineering_issues=state.engineering,
        latest_response=state.response,
        latest_run=state.run,
        decision=state.run.decision if state.run else None,
        confidence_score=state.run.confidence_score if state.run else None,
    )


def approve_and_prepare_send(ticket_id: str, edited_body: str | None, reviewer_id: str | None) -> Response | None:
    state = run_store.get_state(ticket_id)
    if not state.response:
        return None
    if edited_body:
        state.response.body_text = edited_body
    state.response.status = ResponseStatus.approved
    state.response.reviewed_by = reviewer_id
    run_store.log_audit(
        ticket_id=ticket_id, agent_run_id=state.run.id if state.run else None,
        actor_type="human", actor_label=reviewer_id or "Support agent",
        event_type="response.approved", description="Response approved for sending" + (" (edited)" if edited_body else ""),
    )
    return state.response


def mark_sent(ticket_id: str, provider_message_id: str | None) -> Response | None:
    state = run_store.get_state(ticket_id)
    if not state.response:
        return None
    state.response.status = ResponseStatus.sent
    state.response.sent_at = datetime.now(timezone.utc)
    run_store.log_audit(
        ticket_id=ticket_id, agent_run_id=state.run.id if state.run else None,
        actor_type="system", actor_label="Resend (via Swytchcode)",
        event_type="response.sent", description="Response sent to customer via Resend",
        metadata={"provider_message_id": provider_message_id},
    )
    return state.response


def reject_response(ticket_id: str, reviewer_id: str | None, reason: str | None) -> Response | None:
    state = run_store.get_state(ticket_id)
    if not state.response:
        return None
    state.response.status = ResponseStatus.rejected
    state.response.reviewed_by = reviewer_id
    run_store.log_audit(
        ticket_id=ticket_id, agent_run_id=state.run.id if state.run else None,
        actor_type="human", actor_label=reviewer_id or "Support agent",
        event_type="response.rejected", description=reason or "Response rejected by reviewer",
    )
    return state.response


def escalate(ticket_id: str, reviewer_id: str | None, note: str | None) -> None:
    state = run_store.get_state(ticket_id)
    if state.run:
        state.run.decision = AIDecision.NEEDS_HUMAN_REVIEW
    run_store.log_audit(
        ticket_id=ticket_id, agent_run_id=state.run.id if state.run else None,
        actor_type="human", actor_label=reviewer_id or "Support agent",
        event_type="ticket.escalated", description=note or "Ticket escalated for human handling",
    )
