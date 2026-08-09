from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

from app.models.schemas import (
    ActionStatus,
    AgentAction,
    AgentRun,
    AIDecision,
    IntegrationProvider,
    Response,
    ResponseStatus,
    SupportTicket,
)
from app.services import demo_data, gemini_service, integrations_service, run_store
from app.services.swytchcode_service import SwytchcodeResult


async def _step(
    run_id: str, ticket_id: str, order: int, action_type: str,
    integration: IntegrationProvider | None, canonical_id: str | None,
    fn, *, summary_ok: str, summary_fail: str = "Step failed",
) -> tuple[AgentAction, object]:
    """Runs one pipeline step, times it, and records an AgentAction."""
    start = time.perf_counter()
    try:
        value = await fn()
        duration_ms = int((time.perf_counter() - start) * 1000)
        action = AgentAction(
            id=str(uuid.uuid4()), agent_run_id=run_id, ticket_id=ticket_id, step_order=order,
            action_type=action_type, integration=integration, swytchcode_canonical_id=canonical_id,
            status=ActionStatus.success, summary=summary_ok, duration_ms=duration_ms,
            created_at=datetime.now(timezone.utc),
        )
        return action, value
    except Exception as exc:  # noqa: BLE001
        duration_ms = int((time.perf_counter() - start) * 1000)
        action = AgentAction(
            id=str(uuid.uuid4()), agent_run_id=run_id, ticket_id=ticket_id, step_order=order,
            action_type=action_type, integration=integration, swytchcode_canonical_id=canonical_id,
            status=ActionStatus.error, summary=f"{summary_fail}: {exc}", duration_ms=duration_ms,
            created_at=datetime.now(timezone.utc),
        )
        return action, None


async def run_agent_for_ticket(ticket: SupportTicket, email_body: str, email_subject: str) -> AgentRun:
    """
    Executes the full pipeline for one ticket and stores the result in
    run_store (the in-memory/cache layer). Returns the completed AgentRun
    with its ordered list of actions attached.
    """
    run_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc)
    actions: list[AgentAction] = []
    order = 0

    state = run_store.get_state(ticket.id)

    # -- Step 1: Gmail fetch (context step — we already have the email body,
    #    this represents the agent pulling the thread via Swytchcode) -------
    order += 1
    a, _ = await _step(
        run_id, ticket.id, order, "gmail.fetch_thread", IntegrationProvider.gmail, "gmail.get_message",
        lambda: integrations_service.fetch_gmail_thread(email_subject),
        summary_ok=f"Fetched email thread for \"{email_subject}\" via Gmail",
    )
    actions.append(a)

    # -- Step 2: AI classification -------------------------------------
    order += 1
    classify_holder = {}
    async def _classify():
        result = await gemini_service.classify_email(email_subject, email_body)
        classify_holder["v"] = result
        return result
    a, analysis = await _step(
        run_id, ticket.id, order, "ai.classify", None, None, _classify,
        summary_ok="Classified issue",
    )
    if analysis:
        a.summary = f"Classified as {analysis.category} / {analysis.priority.value} (confidence {analysis.confidence_score:.0%})"
    actions.append(a)
    state.analysis = analysis

    category = analysis.category if analysis else (ticket.category or "technical")

    # -- Step 3: Notion search -------------------------------------------
    order += 1
    a, notion_pair = await _step(
        run_id, ticket.id, order, "notion.search", IntegrationProvider.notion, "notion.search",
        lambda: integrations_service.search_notion(analysis.summary if analysis else ticket.subject, category),
        summary_ok="Searched Notion knowledge base",
    )
    knowledge = notion_pair[1] if notion_pair else []
    if knowledge:
        a.summary = f"Found {len(knowledge)} relevant Notion article(s)"
    else:
        a.summary = "No relevant Notion articles found"
    actions.append(a)
    state.knowledge = knowledge

    # -- Step 4: Jira search ----------------------------------------------
    order += 1
    a, jira_pair = await _step(
        run_id, ticket.id, order, "jira.search", IntegrationProvider.jira, "jira.search_issues",
        lambda: integrations_service.search_jira(analysis.summary if analysis else ticket.subject, category),
        summary_ok="Searched Jira for related issues",
    )
    jira_issues = jira_pair[1] if jira_pair else []
    a.summary = f"Found {len(jira_issues)} related Jira issue(s)" if jira_issues else "No related Jira issues found"
    actions.append(a)

    # -- Step 5: GitHub search ----------------------------------------------
    order += 1
    a, gh_pair = await _step(
        run_id, ticket.id, order, "github.search", IntegrationProvider.github, "github.search_issues",
        lambda: integrations_service.search_github(analysis.summary if analysis else ticket.subject, category),
        summary_ok="Searched GitHub for related issues",
    )
    gh_issues = gh_pair[1] if gh_pair else []
    a.summary = f"Found {len(gh_issues)} related GitHub issue(s)" if gh_issues else "No related GitHub issues found"
    actions.append(a)

    engineering = jira_issues + gh_issues
    state.engineering = engineering

    # -- Step 6: AI decision -------------------------------------------
    order += 1
    decision_holder = {}
    async def _decide():
        d = await gemini_service.decide_resolution(
            analysis.summary if analysis else ticket.subject,
            category, (analysis.priority.value if analysis else ticket.priority.value),
            knowledge, engineering,
        )
        decision_holder["v"] = d
        return d
    a, decision = await _step(
        run_id, ticket.id, order, "ai.decide", None, None, _decide,
        summary_ok="Reached a resolution decision",
    )
    if decision:
        a.summary = f"Decision: {decision.decision.value} (confidence {decision.confidence_score:.0%})"
    actions.append(a)

    # -- Step 7: Generate customer reply -------------------------------
    order += 1
    reply_holder = {}
    async def _reply():
        r = await gemini_service.generate_reply(
            analysis.summary if analysis else ticket.subject,
            decision.decision if decision else AIDecision.NEEDS_HUMAN_REVIEW,
            decision.reasoning if decision else "",
            knowledge,
        )
        reply_holder["v"] = r
        return r
    a, generated = await _step(
        run_id, ticket.id, order, "ai.generate_reply", None, None, _reply,
        summary_ok="Drafted customer reply",
    )
    actions.append(a)

    # -- Step 8: Create Jira ticket if the decision calls for it ---------
    if decision and decision.needs_jira_ticket:
        order += 1
        a, created_pair = await _step(
            run_id, ticket.id, order, "jira.create", IntegrationProvider.jira, "jira.create_issue",
            lambda: integrations_service.create_jira_ticket(
                decision.suggested_jira_summary or ticket.subject,
                decision.suggested_jira_priority or "Medium",
                analysis.summary if analysis else ticket.subject,
            ),
            summary_ok="Created Jira engineering ticket",
        )
        created_issue = created_pair[1] if created_pair else None
        if created_issue:
            a.summary = f"Created Jira ticket {created_issue.external_key}"
            engineering.append(created_issue)
            state.engineering = engineering
        actions.append(a)

    # -- Step 9: Await human approval (explicit gate — never auto-sends) --
    order += 1
    actions.append(AgentAction(
        id=str(uuid.uuid4()), agent_run_id=run_id, ticket_id=ticket.id, step_order=order,
        action_type="approval.awaiting", integration=None, swytchcode_canonical_id=None,
        status=ActionStatus.pending, summary="Queued for human approval before sending to customer",
        duration_ms=0, created_at=datetime.now(timezone.utc),
    ))

    completed_at = datetime.now(timezone.utc)
    run = AgentRun(
        id=run_id, ticket_id=ticket.id, status="awaiting_approval",
        decision=decision.decision if decision else AIDecision.NEEDS_HUMAN_REVIEW,
        confidence_score=decision.confidence_score if decision else 0.5,
        started_at=started_at, completed_at=completed_at, is_demo=ticket.is_demo, actions=actions,
    )
    state.run = run

    response = Response(
        id=str(uuid.uuid4()), ticket_id=ticket.id, agent_run_id=run_id,
        body_text=generated.body_text if generated else "Unable to draft a response automatically — needs manual reply.",
        status=ResponseStatus.pending_approval,
        confidence_score=decision.confidence_score if decision else 0.4,
        decision=decision.decision if decision else AIDecision.NEEDS_HUMAN_REVIEW,
        created_at=completed_at,
    )
    state.response = response

    run_store.log_audit(
        ticket_id=ticket.id, agent_run_id=run_id, actor_type="ai_agent", actor_label="Resolve AI Agent",
        event_type="agent_run.completed",
        description=f"Agent run completed with decision {run.decision.value if run.decision else 'n/a'}, drafted response awaiting approval.",
        metadata={"decision": run.decision.value if run.decision else None, "confidence": run.confidence_score},
    )

    return run
