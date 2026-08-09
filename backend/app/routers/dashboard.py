from __future__ import annotations

from fastapi import APIRouter

from app.models.schemas import DashboardStats, TicketStatus
from app.services import run_store, ticket_service

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
def stats():
    tickets = ticket_service.list_tickets()
    total = len(tickets)
    open_count = sum(1 for t in tickets if t.status in (TicketStatus.open, TicketStatus.in_progress))

    resolutions_minutes: list[float] = []
    ai_resolved = 0
    escalations = 0
    sentiment_counts: dict[str, int] = {}

    for t in tickets:
        if t.sentiment:
            sentiment_counts[t.sentiment.value] = sentiment_counts.get(t.sentiment.value, 0) + 1
        if t.status == TicketStatus.resolved and t.resolved_at:
            resolutions_minutes.append((t.resolved_at - t.created_at).total_seconds() / 60)

        state = run_store.get_state(t.id)
        if state.run and state.run.decision:
            if state.run.decision.value == "RESOLVED":
                ai_resolved += 1
            if state.run.decision.value == "NEEDS_ENGINEERING":
                escalations += 1
        if t.status == TicketStatus.escalated:
            escalations += 1

    avg_resolution = sum(resolutions_minutes) / len(resolutions_minutes) if resolutions_minutes else 0.0
    resolution_rate = (ai_resolved / total) if total else 0.0

    return DashboardStats(
        total_tickets=total, ai_resolved=ai_resolved, open_tickets=open_count,
        engineering_escalations=escalations, avg_resolution_minutes=round(avg_resolution, 1),
        resolution_rate=round(resolution_rate, 3), sentiment_breakdown=sentiment_counts,
    )
