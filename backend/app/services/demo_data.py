from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from app.models.schemas import Customer, EmailMessage, Sentiment, SupportTicket, TicketPriority, TicketStatus

def _now() -> datetime:
    return datetime.now(timezone.utc)


DEMO_CUSTOMERS: dict[str, Customer] = {
    "cust-1": Customer(id="cust-1", email="priya.sharma@demo.resolveai.dev", full_name="Priya Sharma", company="Northwind Retail", plan="growth"),
    "cust-2": Customer(id="cust-2", email="alex.chen@demo.resolveai.dev", full_name="Alex Chen", company="Fenwick Labs", plan="pro"),
    "cust-3": Customer(id="cust-3", email="maria.gomez@demo.resolveai.dev", full_name="Maria Gomez", company="Solstice Apps", plan="starter"),
    "cust-4": Customer(id="cust-4", email="rahul.verma@demo.resolveai.dev", full_name="Rahul Verma", company="Verma & Co", plan="growth"),
    "cust-5": Customer(id="cust-5", email="liu.wei@demo.resolveai.dev", full_name="Liu Wei", company="Orbital Freight", plan="pro"),
}

# ticket_id -> (ticket, email, category_hint)
_FIXTURES = [
    dict(
        id="tkt-1001", ticket_number="RES-1001", customer_id="cust-1",
        subject="Payment failed but money was deducted from my account",
        category_hint="billing", priority=TicketPriority.urgent, sentiment=Sentiment.frustrated,
        status=TicketStatus.escalated, hours_ago=3,
        body=(
            "Hi, I tried to upgrade to the Growth plan and the checkout showed \"payment failed\", "
            "but \u20b94,999 was deducted from my card immediately. This is the second time this has "
            "happened. I need this refunded or the upgrade completed today \u2014 my card statement shows "
            "the charge from 20 minutes ago. Order reference is missing entirely on my end. Please help urgently."
        ),
    ),
    dict(
        id="tkt-1002", ticket_number="RES-1002", customer_id="cust-2",
        subject="Password reset link not working",
        category_hint="account", priority=TicketPriority.medium, sentiment=Sentiment.negative,
        status=TicketStatus.resolved, hours_ago=24,
        body=(
            "I requested a password reset three times now and the link in the email just goes to a "
            "blank page. I'm locked out of my account and can't access my dashboard. Using Chrome on Mac. "
            "Can you help?"
        ),
    ),
    dict(
        id="tkt-1003", ticket_number="RES-1003", customer_id="cust-3",
        subject="API returning 500 on /v1/contacts since this morning",
        category_hint="technical", priority=TicketPriority.high, sentiment=Sentiment.negative,
        status=TicketStatus.in_progress, hours_ago=5,
        body=(
            "Every call to POST /v1/contacts has returned a 500 Internal Server Error since around 9am "
            "UTC today. GET requests still work fine. This is blocking our onboarding flow in production. "
            "Can someone check the API status? Happy to share request IDs if useful."
        ),
    ),
    dict(
        id="tkt-1004", ticket_number="RES-1004", customer_id="cust-4",
        subject="Upgraded my plan but still seeing old limits",
        category_hint="billing", priority=TicketPriority.medium, sentiment=Sentiment.neutral,
        status=TicketStatus.resolved, hours_ago=8,
        body=(
            "I upgraded from Starter to Growth yesterday and the payment went through, but my dashboard "
            "still shows the Starter plan limits (500 contacts). Can you refresh this on your end?"
        ),
    ),
    dict(
        id="tkt-1005", ticket_number="RES-1005", customer_id="cust-5",
        subject="CSV export keeps failing at 80%",
        category_hint="technical", priority=TicketPriority.medium, sentiment=Sentiment.neutral,
        status=TicketStatus.open, hours_ago=1,
        body=(
            "I'm trying to export our full contact list (around 42,000 rows) to CSV and the export "
            "progress bar gets to about 80% and then just shows \"Export failed\". I've tried 4 times over "
            "the last hour, including a smaller filtered export of 2,000 rows which also failed once. "
            "Not sure if this is a size issue."
        ),
    ),
]


def get_demo_tickets() -> list[SupportTicket]:
    tickets = []
    for f in _FIXTURES:
        created = _now() - timedelta(hours=f["hours_ago"])
        tickets.append(SupportTicket(
            id=f["id"], ticket_number=f["ticket_number"], customer=DEMO_CUSTOMERS[f["customer_id"]],
            subject=f["subject"], category=f["category_hint"], priority=f["priority"],
            status=f["status"], sentiment=f["sentiment"], is_demo=True, created_at=created,
            resolved_at=(created + timedelta(hours=2)) if f["status"] == TicketStatus.resolved else None,
        ))
    return tickets


def get_demo_ticket_map() -> dict[str, dict]:
    """Returns fixture dicts keyed by id, including the raw email body — used by the orchestrator."""
    return {f["id"]: f for f in _FIXTURES}


def get_demo_email(ticket_id: str) -> EmailMessage | None:
    fixtures = get_demo_ticket_map()
    f = fixtures.get(ticket_id)
    if not f:
        return None
    customer = DEMO_CUSTOMERS[f["customer_id"]]
    return EmailMessage(
        id=str(uuid.uuid4()), ticket_id=ticket_id, direction="inbound",
        from_address=customer.email, to_address="support@yourcompany.com",
        subject=f["subject"], body_text=f["body"],
        received_at=_now() - timedelta(hours=f["hours_ago"]),
    )
