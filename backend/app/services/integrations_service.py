"""
One function per integration action the agent needs. Every function is a
thin, logged wrapper that calls SwytchcodeService.exec() with a logical
action name — it never talks to Gmail/Notion/Jira/GitHub/Resend directly.
This is what "Swytchcode as the primary integration layer" means in
practice: this file has zero `requests`/`httpx` calls to those providers.

Demo payloads below are what's returned when running without a live
Swytchcode connection (DEMO_MODE=true or no SWYTCHCODE_API_KEY) — they're
shaped like what the real canonical IDs would return, so the rest of the
app (parsing, UI) is identical in both modes.
"""

from __future__ import annotations

from app.models.schemas import EngineeringIssue, KnowledgeSource
from app.services.swytchcode_service import SwytchcodeResult, swytchcode_service

# ----------------------------------------------------------------------------
# Demo knowledge base — keyed by ticket category, used only when not live
# ----------------------------------------------------------------------------
_DEMO_NOTION: dict[str, list[dict]] = {
    "account": [
        {"title": "Password reset link opens a blank page", "excerpt": "Caused by a stale session cookie persisting through the reset flow. Fix: open the link in a private window or clear cookies, then request a new link.", "url": "https://notion.so/kb/password-reset-blank-page", "relevance_score": 0.94},
        {"title": "Account lockout policy", "excerpt": "Accounts lock after 5 failed logins within 15 minutes; auto-unlocks after 30 minutes.", "url": "https://notion.so/kb/account-lockout-policy", "relevance_score": 0.41},
    ],
    "billing": [
        {"title": "Failed payment still shows a pending charge", "excerpt": "Card networks can hold funds for a 'failed' authorization for up to 5 business days before auto-releasing; if the order isn't visible, escalate to billing ops rather than confirm a refund.", "url": "https://notion.so/kb/failed-payment-pending-hold", "relevance_score": 0.86},
        {"title": "Plan upgrade not reflected immediately", "excerpt": "Entitlements sync runs every 15 minutes; if still stale after 30 minutes, a manual entitlement refresh is needed.", "url": "https://notion.so/kb/plan-upgrade-sync-delay", "relevance_score": 0.9},
    ],
    "technical": [
        {"title": "CSV export size limits", "excerpt": "Exports above ~35,000 rows can time out on the synchronous export path; large exports should use the async export job instead.", "url": "https://notion.so/kb/csv-export-limits", "relevance_score": 0.79},
    ],
}

_DEMO_JIRA: dict[str, list[dict]] = {
    "technical": [
        {"external_key": "ENG-4821", "title": "POST /v1/contacts intermittent 500s under load", "status": "In Progress", "url": "https://yourteam.atlassian.net/browse/ENG-4821", "relevance_score": 0.88},
    ],
    "billing": [
        {"external_key": "ENG-4790", "title": "Entitlement sync worker lag during peak hours", "status": "Backlog", "url": "https://yourteam.atlassian.net/browse/ENG-4790", "relevance_score": 0.55},
    ],
}

_DEMO_GITHUB: dict[str, list[dict]] = {
    "technical": [
        {"external_id": "1932", "title": "Async export job fails silently above 40k rows", "status": "open", "url": "https://github.com/yourorg/platform/issues/1932", "relevance_score": 0.83},
    ],
}


async def search_notion(query: str, category: str) -> tuple[SwytchcodeResult, list[KnowledgeSource]]:
    result = await swytchcode_service.exec(
        "notion.search", {"query": query},
        demo_fallback={"results": _DEMO_NOTION.get(category, [])},
    )
    items = result.output.get("results", [])
    sources = [KnowledgeSource(source_type="notion", **item) for item in items]
    return result, sources


async def search_jira(query: str, category: str) -> tuple[SwytchcodeResult, list[EngineeringIssue]]:
    result = await swytchcode_service.exec(
        "jira.search_issues", {"jql": query},
        demo_fallback={"results": _DEMO_JIRA.get(category, [])},
    )
    items = result.output.get("results", [])
    issues = [EngineeringIssue(provider="jira", relation="related", **item) for item in items]
    return result, issues


async def search_github(query: str, category: str) -> tuple[SwytchcodeResult, list[EngineeringIssue]]:
    result = await swytchcode_service.exec(
        "github.search_issues", {"query": query},
        demo_fallback={"results": _DEMO_GITHUB.get(category, [])},
    )
    items = result.output.get("results", [])
    issues = [EngineeringIssue(provider="github", relation="related", **item) for item in items]
    return result, issues


async def create_jira_ticket(summary: str, priority: str, description: str) -> tuple[SwytchcodeResult, EngineeringIssue | None]:
    result = await swytchcode_service.exec(
        "jira.create_issue",
        {"summary": summary, "priority": priority, "description": description, "issue_type": "Bug"},
        demo_fallback={
            "external_key": "ENG-4901",
            "title": summary,
            "status": "To Do",
            "url": "https://yourteam.atlassian.net/browse/ENG-4901",
        },
    )
    if not result.ok:
        return result, None
    data = result.output if result.mode != "demo" else result.output
    issue = EngineeringIssue(
        provider="jira",
        relation="created",
        title=data.get("title", summary),
        external_key=data.get("external_key"),
        url=data.get("url"),
        status=data.get("status", "To Do"),
        relevance_score=1.0,
    )
    return result, issue


async def send_customer_email(to_address: str, subject: str, body_text: str) -> SwytchcodeResult:
    return await swytchcode_service.exec(
        "resend.send_email",
        {"to": to_address, "subject": subject, "text": body_text},
        demo_fallback={"id": "demo-email-id", "status": "sent"},
    )


async def fetch_gmail_thread(thread_hint: str) -> SwytchcodeResult:
    return await swytchcode_service.exec(
        "gmail.get_message",
        {"query": thread_hint},
        demo_fallback={"fetched": True},
    )
