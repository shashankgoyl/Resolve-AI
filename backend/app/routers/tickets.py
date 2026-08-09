from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    ApproveResponseRequest,
    CreateJiraTicketRequest,
    EscalateRequest,
    RejectResponseRequest,
    Response,
    SupportTicket,
    TicketDetail,
)
from app.services import integrations_service, run_store, ticket_service

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.get("", response_model=list[SupportTicket])
def list_tickets():
    return ticket_service.list_tickets()


@router.get("/{ticket_id}", response_model=TicketDetail)
async def get_ticket(ticket_id: str):
    detail = await ticket_service.get_ticket_detail(ticket_id)
    if not detail:
        raise HTTPException(404, "Ticket not found")
    return detail


@router.post("/{ticket_id}/rerun", response_model=TicketDetail)
async def rerun_agent(ticket_id: str):
    detail = await ticket_service.get_ticket_detail(ticket_id, force_rerun=True)
    if not detail:
        raise HTTPException(404, "Ticket not found")
    run_store.log_audit(
        ticket_id=ticket_id, agent_run_id=detail.latest_run.id if detail.latest_run else None,
        actor_type="human", actor_label="Support agent", event_type="agent_run.rerun_requested",
        description="Agent re-run requested",
    )
    return detail


@router.post("/{ticket_id}/approve", response_model=Response)
async def approve_and_send(ticket_id: str, body: ApproveResponseRequest):
    response = ticket_service.approve_and_prepare_send(ticket_id, body.edited_body_text, body.reviewer_id)
    if not response:
        raise HTTPException(404, "No response to approve for this ticket")

    detail = await ticket_service.get_ticket_detail(ticket_id)
    to_address = detail.emails[0].from_address if detail and detail.emails else detail.customer.email
    subject = f"Re: {detail.subject}" if detail else "Re: your support request"

    result = await integrations_service.send_customer_email(to_address, subject, response.body_text)
    if not result.ok:
        raise HTTPException(502, f"Failed to send via Resend/Swytchcode: {result.error}")

    provider_id = result.output.get("id")
    updated = ticket_service.mark_sent(ticket_id, provider_id)
    return updated


@router.post("/{ticket_id}/reject", response_model=Response)
def reject(ticket_id: str, body: RejectResponseRequest):
    response = ticket_service.reject_response(ticket_id, body.reviewer_id, body.reason)
    if not response:
        raise HTTPException(404, "No response to reject for this ticket")
    return response


@router.post("/{ticket_id}/escalate")
def escalate(ticket_id: str, body: EscalateRequest):
    ticket_service.escalate(ticket_id, body.reviewer_id, body.note)
    return {"ok": True}


@router.post("/{ticket_id}/jira-ticket")
async def create_jira_ticket(ticket_id: str, body: CreateJiraTicketRequest):
    detail = await ticket_service.get_ticket_detail(ticket_id)
    if not detail:
        raise HTTPException(404, "Ticket not found")
    summary = body.summary or f"Investigate: {detail.subject}"
    priority = body.priority or "Medium"
    result, issue = await integrations_service.create_jira_ticket(summary, priority, detail.subject)
    if not result.ok or not issue:
        raise HTTPException(502, f"Failed to create Jira ticket via Swytchcode: {result.error}")

    state = run_store.get_state(ticket_id)
    state.engineering.append(issue)
    run_store.log_audit(
        ticket_id=ticket_id, agent_run_id=state.run.id if state.run else None,
        actor_type="human", actor_label="Support agent", event_type="jira.created_manually",
        description=f"Jira ticket {issue.external_key} created manually",
    )
    return issue
