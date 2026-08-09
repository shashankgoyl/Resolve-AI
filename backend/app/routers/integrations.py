from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter

from app.core.config import get_settings
from app.models.schemas import IntegrationHealth, IntegrationProvider, IntegrationStatusOut
from app.services.swytchcode_service import load_tool_map

router = APIRouter(prefix="/api/integrations", tags=["integrations"])

_ACTION_PREFIXES = {
    IntegrationProvider.gmail: "gmail.",
    IntegrationProvider.notion: "notion.",
    IntegrationProvider.jira: "jira.",
    IntegrationProvider.github: "github.",
    IntegrationProvider.resend: "resend.",
}


@router.get("", response_model=list[IntegrationStatusOut])
def integration_status():
    settings = get_settings()
    now = datetime.now(timezone.utc)
    tool_map = load_tool_map()

    live = not settings.DEMO_MODE and settings.swytchcode_configured
    results: list[IntegrationStatusOut] = []

    for provider, prefix in _ACTION_PREFIXES.items():
        registered = any(k.startswith(prefix) and v for k, v in tool_map.items())
        if not live:
            health = IntegrationHealth.demo
        elif registered:
            health = IntegrationHealth.connected
        else:
            health = IntegrationHealth.disconnected
        results.append(IntegrationStatusOut(provider=provider, health=health, last_checked_at=now))

    swytchcode_health = (
        IntegrationHealth.connected if settings.swytchcode_configured and not settings.DEMO_MODE
        else IntegrationHealth.demo
    )
    results.append(IntegrationStatusOut(provider=IntegrationProvider.swytchcode, health=swytchcode_health, last_checked_at=now))

    return results
