"""
Gemini service — every call here uses response_schema (structured output)
against a Pydantic model, so the orchestrator never has to regex-parse
free-form model text. If GEMINI_API_KEY is unset or DEMO_MODE is on, these
functions return deterministic, clearly-labeled demo output instead of
calling the API — that's what lets `demo mode` run with zero external
credentials, per the spec.
"""

from __future__ import annotations

import json
from typing import Optional

import google.generativeai as genai

from app.core.config import get_settings
from app.models.schemas import (
    EmailClassification,
    GeneratedResponse,
    KnowledgeSource,
    EngineeringIssue,
    ResolutionDecision,
    Sentiment,
    TicketPriority,
    AIDecision,
)

_configured = False


def _ensure_configured() -> bool:
    global _configured
    settings = get_settings()
    if not settings.gemini_configured:
        return False
    if not _configured:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        _configured = True
    return True


async def _generate_structured(prompt: str, schema: type, model_name: Optional[str] = None):
    settings = get_settings()
    model = genai.GenerativeModel(model_name or settings.GEMINI_MODEL)
    result = await model.generate_content_async(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=schema,
            temperature=0.2,
        ),
    )
    return schema.model_validate(json.loads(result.text))


# ============================================================================
# 1. Classification
# ============================================================================

CLASSIFY_PROMPT = """You are a customer support triage analyst. Read the customer's email
below and classify it precisely. Be conservative with confidence_score — only
score above 0.85 if the issue is unambiguous.

CUSTOMER EMAIL:
Subject: {subject}
Body: {body}

Respond with the classification only, matching the required schema."""


async def classify_email(subject: str, body: str) -> EmailClassification:
    if not _ensure_configured():
        return _demo_classification(subject, body)
    prompt = CLASSIFY_PROMPT.format(subject=subject, body=body)
    return await _generate_structured(prompt, EmailClassification)


def _demo_classification(subject: str, body: str) -> EmailClassification:
    text = f"{subject} {body}".lower()
    if "payment" in text or "charged" in text or "deducted" in text or "refund" in text:
        return EmailClassification(
            category="billing", priority=TicketPriority.urgent, sentiment=Sentiment.frustrated,
            intent="Get a duplicate/failed charge resolved", summary="Customer was charged but the transaction shows as failed.",
            key_entities=["payment", "charge"], confidence_score=0.9,
        )
    if "password" in text or "reset" in text or "locked out" in text:
        return EmailClassification(
            category="account", priority=TicketPriority.medium, sentiment=Sentiment.negative,
            intent="Regain access to their account", summary="Password reset link is not working, customer is locked out.",
            key_entities=["password reset"], confidence_score=0.88,
        )
    if "500" in text or "api" in text or "error" in text:
        return EmailClassification(
            category="technical", priority=TicketPriority.high, sentiment=Sentiment.negative,
            intent="Restore API functionality", summary="Customer is seeing server errors from the API in production.",
            key_entities=["500 error", "API"], confidence_score=0.85,
        )
    if "plan" in text or "subscription" in text or "upgrade" in text or "limits" in text:
        return EmailClassification(
            category="billing", priority=TicketPriority.medium, sentiment=Sentiment.neutral,
            intent="Have their new plan reflected in the product", summary="Plan upgrade paid for but limits not yet updated.",
            key_entities=["subscription", "plan limits"], confidence_score=0.83,
        )
    return EmailClassification(
        category="technical", priority=TicketPriority.medium, sentiment=Sentiment.neutral,
        intent="Get a failing export working", summary="A data export is failing partway through.",
        key_entities=["CSV export"], confidence_score=0.78,
    )


# ============================================================================
# 2. Resolution decision (given classification + evidence gathered)
# ============================================================================

DECIDE_PROMPT = """You are the decision-making step of a support automation agent.
Given the classified issue and the evidence gathered from internal knowledge base,
Jira, and GitHub, decide how to proceed.

Rules:
- If a knowledge base article directly and confidently answers the issue -> RESOLVED
- If it looks like a product bug and no fix/workaround exists in the evidence -> NEEDS_ENGINEERING
- If the evidence is contradictory, sensitive (e.g. money/refunds), or ambiguous -> NEEDS_HUMAN_REVIEW
- If there is not enough evidence to say anything useful -> INSUFFICIENT_INFORMATION
Never hallucinate a fix that isn't backed by the evidence.

ISSUE: {summary} (category={category}, priority={priority})

KNOWLEDGE BASE MATCHES:
{knowledge}

RELATED ENGINEERING ISSUES:
{engineering}

Respond with the decision only, matching the required schema."""


async def decide_resolution(
    summary: str, category: str, priority: str,
    knowledge: list[KnowledgeSource], engineering: list[EngineeringIssue],
) -> ResolutionDecision:
    if not _ensure_configured():
        return _demo_decision(category, knowledge, engineering)
    prompt = DECIDE_PROMPT.format(
        summary=summary, category=category, priority=priority,
        knowledge="\n".join(f"- {k.title}: {k.excerpt}" for k in knowledge) or "(none found)",
        engineering="\n".join(f"- [{e.provider}] {e.title} ({e.status})" for e in engineering) or "(none found)",
    )
    return await _generate_structured(prompt, ResolutionDecision)


def _demo_decision(category: str, knowledge: list[KnowledgeSource], engineering: list[EngineeringIssue]) -> ResolutionDecision:
    if category == "billing":
        return ResolutionDecision(
            decision=AIDecision.NEEDS_HUMAN_REVIEW,
            reasoning="Billing issues involving a discrepancy between a charge and order status touch real money — routing to a human for verification before any refund or confirmation is sent.",
            confidence_score=0.72, needs_jira_ticket=False,
        )
    if category == "account":
        return ResolutionDecision(
            decision=AIDecision.RESOLVED,
            reasoning="Knowledge base has a confirmed workaround for reset links opening blank (stale session cookie) that matches this report exactly.",
            confidence_score=0.91, needs_jira_ticket=False,
        )
    if engineering and any(e.status not in ("Closed", "Done", "closed") for e in engineering):
        return ResolutionDecision(
            decision=AIDecision.NEEDS_ENGINEERING,
            reasoning="This matches an already-open, unresolved engineering issue — no customer-facing fix exists yet, so this needs to be linked to engineering rather than answered as resolved.",
            confidence_score=0.87, needs_jira_ticket=True,
            suggested_jira_summary="Investigate: recurring failure pattern reported by customer",
            suggested_jira_priority="High",
        )
    return ResolutionDecision(
        decision=AIDecision.NEEDS_ENGINEERING,
        reasoning="No existing knowledge base article or resolved engineering ticket covers this exact failure; it looks like a genuine product bug that needs investigation.",
        confidence_score=0.68, needs_jira_ticket=True,
        suggested_jira_summary="Export fails partway through for large contact lists",
        suggested_jira_priority="Medium",
    )


# ============================================================================
# 3. Reply generation
# ============================================================================

REPLY_PROMPT = """Write a customer support reply. Be warm, concise, and specific —
reference what you found, don't be generic. Do not promise things not
supported by the evidence. Sign off as "The Support Team".

ISSUE SUMMARY: {summary}
DECISION: {decision}
DECISION REASONING: {reasoning}
KNOWLEDGE BASE EVIDENCE:
{knowledge}

Respond with the reply only, matching the required schema."""


async def generate_reply(summary: str, decision: AIDecision, reasoning: str, knowledge: list[KnowledgeSource]) -> GeneratedResponse:
    if not _ensure_configured():
        return _demo_reply(decision)
    prompt = REPLY_PROMPT.format(
        summary=summary, decision=decision.value, reasoning=reasoning,
        knowledge="\n".join(f"- {k.title}: {k.excerpt}" for k in knowledge) or "(none)",
    )
    return await _generate_structured(prompt, GeneratedResponse)


def _demo_reply(decision: AIDecision) -> GeneratedResponse:
    if decision == AIDecision.RESOLVED:
        body = (
            "Thanks for flagging this, and sorry for the trouble logging in.\n\n"
            "This happens when an old session cookie sticks around after a password reset "
            "request. Could you try opening the reset link in a private/incognito window, "
            "or clear cookies for this site and request a new link? That resolves it for the "
            "vast majority of cases we've seen.\n\n"
            "Let us know if the link still doesn't work after that and we'll dig in further.\n\n"
            "— The Support Team"
        )
    elif decision == AIDecision.NEEDS_ENGINEERING:
        body = (
            "Thanks for the detailed report, and I'm sorry this is blocking you.\n\n"
            "I've confirmed this looks like a genuine issue on our end rather than something "
            "on your side, and I've filed it with our engineering team so they can investigate. "
            "I'll follow up here as soon as we have an update or a fix — you shouldn't need to "
            "do anything further for now.\n\n"
            "— The Support Team"
        )
    else:
        body = (
            "Thanks for reaching out — I want to make sure this is handled correctly, so I've "
            "flagged it for a member of our team to take a closer look before we respond in "
            "detail. We'll get back to you shortly.\n\n"
            "— The Support Team"
        )
    return GeneratedResponse(body_text=body, tone="empathetic", confidence_score=0.8)
