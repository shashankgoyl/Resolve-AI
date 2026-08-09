from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Enums (mirror Postgres enum types in supabase/schema.sql)
# ============================================================================

class TicketPriority(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class TicketStatus(str, Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    escalated = "escalated"
    closed = "closed"


class Sentiment(str, Enum):
    positive = "positive"
    neutral = "neutral"
    negative = "negative"
    frustrated = "frustrated"


class AIDecision(str, Enum):
    RESOLVED = "RESOLVED"
    NEEDS_ENGINEERING = "NEEDS_ENGINEERING"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"
    INSUFFICIENT_INFORMATION = "INSUFFICIENT_INFORMATION"


class ResponseStatus(str, Enum):
    draft = "draft"
    pending_approval = "pending_approval"
    approved = "approved"
    sent = "sent"
    rejected = "rejected"


class IntegrationProvider(str, Enum):
    gmail = "gmail"
    notion = "notion"
    jira = "jira"
    github = "github"
    resend = "resend"
    swytchcode = "swytchcode"


class IntegrationHealth(str, Enum):
    connected = "connected"
    degraded = "degraded"
    disconnected = "disconnected"
    demo = "demo"


class ActionStatus(str, Enum):
    success = "success"
    error = "error"
    skipped = "skipped"
    pending = "pending"


# ============================================================================
# Gemini structured-output models — these are the exact response_schema
# passed to the Gemini API so classification/decision output is typed,
# not parsed out of free text.
# ============================================================================

class EmailClassification(BaseModel):
    category: str = Field(description="One of: billing, technical, account, feature_request, other")
    priority: TicketPriority
    sentiment: Sentiment
    intent: str = Field(description="Short phrase describing what the customer wants")
    summary: str = Field(description="1-2 sentence neutral summary of the issue")
    key_entities: list[str] = Field(default_factory=list, description="Order IDs, error codes, endpoints, etc. mentioned")
    confidence_score: float = Field(ge=0, le=1)


class ResolutionDecision(BaseModel):
    decision: AIDecision
    reasoning: str = Field(description="Why this decision, referencing the evidence gathered")
    confidence_score: float = Field(ge=0, le=1)
    needs_jira_ticket: bool = False
    suggested_jira_summary: Optional[str] = None
    suggested_jira_priority: Optional[str] = None


class GeneratedResponse(BaseModel):
    body_text: str
    tone: str = Field(description="e.g. empathetic, neutral, apologetic")
    confidence_score: float = Field(ge=0, le=1)


# ============================================================================
# Evidence models (Notion / Jira / GitHub search results surfaced via Swytchcode)
# ============================================================================

class KnowledgeSource(BaseModel):
    id: Optional[str] = None
    source_type: str = "notion"
    title: str
    excerpt: Optional[str] = None
    url: Optional[str] = None
    relevance_score: float = 0.0


class EngineeringIssue(BaseModel):
    id: Optional[str] = None
    provider: str  # jira | github
    external_id: Optional[str] = None
    external_key: Optional[str] = None
    url: Optional[str] = None
    title: str
    status: Optional[str] = None
    relation: str = "related"  # related | created
    relevance_score: float = 0.0


# ============================================================================
# Agent activity timeline
# ============================================================================

class AgentAction(BaseModel):
    id: Optional[str] = None
    agent_run_id: str
    ticket_id: str
    step_order: int
    action_type: str
    integration: Optional[IntegrationProvider] = None
    swytchcode_canonical_id: Optional[str] = None
    status: ActionStatus = ActionStatus.success
    summary: Optional[str] = None
    input_payload: dict[str, Any] = Field(default_factory=dict)
    output_payload: dict[str, Any] = Field(default_factory=dict)
    duration_ms: Optional[int] = None
    created_at: Optional[datetime] = None


class AgentRun(BaseModel):
    id: str
    ticket_id: str
    status: str
    decision: Optional[AIDecision] = None
    confidence_score: Optional[float] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    is_demo: bool = False
    actions: list[AgentAction] = Field(default_factory=list)


# ============================================================================
# Core entities
# ============================================================================

class Customer(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    company: Optional[str] = None
    plan: Optional[str] = "free"


class EmailMessage(BaseModel):
    id: Optional[str] = None
    ticket_id: str
    direction: str
    from_address: str
    to_address: str
    subject: Optional[str] = None
    body_text: str
    received_at: Optional[datetime] = None


class Response(BaseModel):
    id: Optional[str] = None
    ticket_id: str
    agent_run_id: Optional[str] = None
    body_text: str
    status: ResponseStatus = ResponseStatus.draft
    confidence_score: float = 0.0
    decision: AIDecision = AIDecision.NEEDS_HUMAN_REVIEW
    reviewed_by: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class SupportTicket(BaseModel):
    id: str
    ticket_number: str
    customer: Customer
    subject: str
    category: Optional[str] = None
    priority: TicketPriority
    status: TicketStatus
    sentiment: Optional[Sentiment] = None
    is_demo: bool = False
    created_at: datetime
    resolved_at: Optional[datetime] = None


class TicketDetail(SupportTicket):
    emails: list[EmailMessage] = Field(default_factory=list)
    analysis: Optional[EmailClassification] = None
    knowledge_sources: list[KnowledgeSource] = Field(default_factory=list)
    engineering_issues: list[EngineeringIssue] = Field(default_factory=list)
    latest_response: Optional[Response] = None
    latest_run: Optional[AgentRun] = None
    decision: Optional[AIDecision] = None
    confidence_score: Optional[float] = None


# ============================================================================
# Dashboard
# ============================================================================

class DashboardStats(BaseModel):
    total_tickets: int
    ai_resolved: int
    open_tickets: int
    engineering_escalations: int
    avg_resolution_minutes: float
    resolution_rate: float
    sentiment_breakdown: dict[str, int]


# ============================================================================
# Integrations / Audit
# ============================================================================

class IntegrationStatusOut(BaseModel):
    provider: IntegrationProvider
    health: IntegrationHealth
    last_checked_at: Optional[datetime] = None
    last_success_at: Optional[datetime] = None
    last_error: Optional[str] = None


class AuditLogEntry(BaseModel):
    id: str
    ticket_id: Optional[str] = None
    agent_run_id: Optional[str] = None
    actor_type: str
    actor_label: Optional[str] = None
    event_type: str
    description: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


# ============================================================================
# Request bodies
# ============================================================================

class ApproveResponseRequest(BaseModel):
    reviewer_id: Optional[str] = None
    edited_body_text: Optional[str] = None


class RejectResponseRequest(BaseModel):
    reviewer_id: Optional[str] = None
    reason: Optional[str] = None


class EscalateRequest(BaseModel):
    reviewer_id: Optional[str] = None
    note: Optional[str] = None


class CreateJiraTicketRequest(BaseModel):
    summary: Optional[str] = None
    priority: Optional[str] = None
