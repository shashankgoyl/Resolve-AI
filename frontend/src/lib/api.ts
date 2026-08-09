import type {
  AuditLogEntry,
  DashboardStats,
  IntegrationStatus,
  ResponseRecord,
  SupportTicket,
  TicketDetail,
} from "@/types";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string; demo_mode: boolean }>("/api/health"),

  listTickets: () => request<SupportTicket[]>("/api/tickets"),
  getTicket: (id: string) => request<TicketDetail>(`/api/tickets/${id}`),
  rerunAgent: (id: string) => request<TicketDetail>(`/api/tickets/${id}/rerun`, { method: "POST" }),

  approveAndSend: (id: string, editedBodyText?: string, reviewerId = "you") =>
    request<ResponseRecord>(`/api/tickets/${id}/approve`, {
      method: "POST",
      body: JSON.stringify({ reviewer_id: reviewerId, edited_body_text: editedBodyText || undefined }),
    }),

  rejectResponse: (id: string, reason?: string, reviewerId = "you") =>
    request<ResponseRecord>(`/api/tickets/${id}/reject`, {
      method: "POST",
      body: JSON.stringify({ reviewer_id: reviewerId, reason }),
    }),

  escalate: (id: string, note?: string, reviewerId = "you") =>
    request<{ ok: boolean }>(`/api/tickets/${id}/escalate`, {
      method: "POST",
      body: JSON.stringify({ reviewer_id: reviewerId, note }),
    }),

  createJiraTicket: (id: string, summary?: string, priority?: string) =>
    request(`/api/tickets/${id}/jira-ticket`, {
      method: "POST",
      body: JSON.stringify({ summary, priority }),
    }),

  dashboardStats: () => request<DashboardStats>("/api/dashboard/stats"),
  integrations: () => request<IntegrationStatus[]>("/api/integrations"),
  auditLogs: (ticketId?: string) =>
    request<AuditLogEntry[]>(`/api/audit-logs${ticketId ? `?ticket_id=${ticketId}` : ""}`),
};
