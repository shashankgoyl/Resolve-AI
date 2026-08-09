export type TicketPriority = "low" | "medium" | "high" | "urgent";
export type TicketStatus = "open" | "in_progress" | "resolved" | "escalated" | "closed";
export type Sentiment = "positive" | "neutral" | "negative" | "frustrated";
export type AIDecision = "RESOLVED" | "NEEDS_ENGINEERING" | "NEEDS_HUMAN_REVIEW" | "INSUFFICIENT_INFORMATION";
export type ResponseStatus = "draft" | "pending_approval" | "approved" | "sent" | "rejected";
export type IntegrationProvider = "gmail" | "notion" | "jira" | "github" | "resend" | "swytchcode";
export type IntegrationHealth = "connected" | "degraded" | "disconnected" | "demo";
export type ActionStatus = "success" | "error" | "skipped" | "pending";

export interface Customer {
  id: string;
  email: string;
  full_name?: string | null;
  company?: string | null;
  plan?: string | null;
}

export interface SupportTicket {
  id: string;
  ticket_number: string;
  customer: Customer;
  subject: string;
  category?: string | null;
  priority: TicketPriority;
  status: TicketStatus;
  sentiment?: Sentiment | null;
  is_demo: boolean;
  created_at: string;
  resolved_at?: string | null;
}

export interface EmailMessage {
  id?: string;
  ticket_id: string;
  direction: "inbound" | "outbound";
  from_address: string;
  to_address: string;
  subject?: string | null;
  body_text: string;
  received_at?: string;
}

export interface EmailClassification {
  category: string;
  priority: TicketPriority;
  sentiment: Sentiment;
  intent: string;
  summary: string;
  key_entities: string[];
  confidence_score: number;
}

export interface KnowledgeSource {
  id?: string | null;
  source_type: string;
  title: string;
  excerpt?: string | null;
  url?: string | null;
  relevance_score: number;
}

export interface EngineeringIssue {
  id?: string | null;
  provider: "jira" | "github";
  external_id?: string | null;
  external_key?: string | null;
  url?: string | null;
  title: string;
  status?: string | null;
  relation: "related" | "created";
  relevance_score: number;
}

export interface AgentAction {
  id?: string;
  agent_run_id: string;
  ticket_id: string;
  step_order: number;
  action_type: string;
  integration?: IntegrationProvider | null;
  swytchcode_canonical_id?: string | null;
  status: ActionStatus;
  summary?: string | null;
  duration_ms?: number | null;
  created_at?: string;
}

export interface AgentRun {
  id: string;
  ticket_id: string;
  status: string;
  decision?: AIDecision | null;
  confidence_score?: number | null;
  started_at: string;
  completed_at?: string | null;
  error_message?: string | null;
  is_demo: boolean;
  actions: AgentAction[];
}

export interface ResponseRecord {
  id?: string;
  ticket_id: string;
  agent_run_id?: string | null;
  body_text: string;
  status: ResponseStatus;
  confidence_score: number;
  decision: AIDecision;
  reviewed_by?: string | null;
  sent_at?: string | null;
  created_at?: string;
}

export interface TicketDetail extends SupportTicket {
  emails: EmailMessage[];
  analysis?: EmailClassification | null;
  knowledge_sources: KnowledgeSource[];
  engineering_issues: EngineeringIssue[];
  latest_response?: ResponseRecord | null;
  latest_run?: AgentRun | null;
  decision?: AIDecision | null;
  confidence_score?: number | null;
}

export interface DashboardStats {
  total_tickets: number;
  ai_resolved: number;
  open_tickets: number;
  engineering_escalations: number;
  avg_resolution_minutes: number;
  resolution_rate: number;
  sentiment_breakdown: Record<string, number>;
}

export interface IntegrationStatus {
  provider: IntegrationProvider;
  health: IntegrationHealth;
  last_checked_at?: string | null;
  last_success_at?: string | null;
  last_error?: string | null;
}

export interface AuditLogEntry {
  id: string;
  ticket_id?: string | null;
  agent_run_id?: string | null;
  actor_type: "ai_agent" | "human" | "system";
  actor_label?: string | null;
  event_type: string;
  description: string;
  metadata: Record<string, unknown>;
  created_at: string;
}
