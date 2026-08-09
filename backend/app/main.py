from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers import audit, dashboard, integrations, tickets
from app.services import demo_data, run_store

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    description="AI Customer Support Knowledge Agent — Gmail -> AI -> Notion -> Jira/GitHub -> Decision -> Approval -> Resend, executed through Swytchcode.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tickets.router)
app.include_router(dashboard.router)
app.include_router(integrations.router)
app.include_router(audit.router)


@app.on_event("startup")
def seed_audit_trail_for_demo() -> None:
    if not (settings.DEMO_MODE or not settings.supabase_configured):
        return
    for t in demo_data.get_demo_tickets():
        run_store.log_audit(
            ticket_id=t.id, agent_run_id=None, actor_type="system", actor_label="Gmail (via Swytchcode)",
            event_type="ticket.created",
            description=f'New support email received: "{t.subject}"',
            metadata={"channel": "email", "customer": t.customer.email},
        )


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "app": settings.APP_NAME,
        "demo_mode": settings.DEMO_MODE or not settings.supabase_configured,
        "supabase_configured": settings.supabase_configured,
        "gemini_configured": settings.gemini_configured,
        "swytchcode_configured": settings.swytchcode_configured,
    }


@app.get("/")
def root():
    return {"message": f"{settings.APP_NAME} backend is running. See /docs for the API."}
