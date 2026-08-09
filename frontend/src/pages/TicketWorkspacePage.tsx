import { useEffect, useState, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import {
  ArrowLeft, Send, Pencil, TriangleAlert, Ticket as TicketIcon, XCircle, RotateCcw,
  BookOpen, GitBranch, Mail, Loader2,
} from "lucide-react";
import { api } from "@/lib/api";
import type { TicketDetail } from "@/types";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { ActivityTimeline } from "@/components/ActivityTimeline";
import { ResolutionGraph } from "@/components/ResolutionGraph";
import { ConfidenceRing } from "@/components/ui/ConfidenceRing";
import { priorityColor, statusColor, decisionColor, formatRelativeTime, cn } from "@/lib/utils";

export function TicketWorkspacePage() {
  const { ticketId } = useParams<{ ticketId: string }>();
  const navigate = useNavigate();
  const [ticket, setTicket] = useState<TicketDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");
  const [toast, setToast] = useState<string | null>(null);

  const load = useCallback((rerun = false) => {
    if (!ticketId) return;
    setLoading(true);
    const call = rerun ? api.rerunAgent(ticketId) : api.getTicket(ticketId);
    call
      .then((t) => {
        setTicket(t);
        setDraft(t.latest_response?.body_text || "");
      })
      .finally(() => setLoading(false));
  }, [ticketId]);

  useEffect(() => { load(); }, [load]);

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(null), 3500);
  };

  const runAction = async (key: string, fn: () => Promise<unknown>, message: string) => {
    if (!ticketId) return;
    setBusy(key);
    try {
      await fn();
      showToast(message);
      load();
      setEditing(false);
    } catch (e) {
      showToast(`Failed: ${(e as Error).message}`);
    } finally {
      setBusy(null);
    }
  };

  if (loading && !ticket) return <div className="p-6 text-text-muted text-sm">Loading ticket…</div>;
  if (!ticket) return <div className="p-6 text-text-muted text-sm">Ticket not found.</div>;

  const email = ticket.emails[0];
  const response = ticket.latest_response;
  const canApprove = response && response.status === "pending_approval";

  return (
    <div className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <button onClick={() => navigate("/inbox")} className="flex items-center gap-1.5 text-sm text-text-muted hover:text-text-primary">
          <ArrowLeft size={15} /> Back to Inbox
        </button>
        {toast && <span className="text-xs font-mono text-signal-teal">{toast}</span>}
      </div>

      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-display text-xl font-semibold text-text-primary">{ticket.subject}</h2>
          <p className="mt-1 text-sm text-text-muted font-mono">
            {ticket.ticket_number} · {ticket.customer.full_name} · {ticket.customer.company} · {formatRelativeTime(ticket.created_at)}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge className={priorityColor[ticket.priority]}>{ticket.priority}</Badge>
          <Badge className={statusColor[ticket.status]}>{ticket.status.replace(/_/g, " ")}</Badge>
          {ticket.decision && <Badge className={decisionColor[ticket.decision]}>{ticket.decision.replace(/_/g, " ")}</Badge>}
        </div>
      </div>

      {/* Resolution Graph — innovation feature */}
      <Card>
        <CardHeader><CardTitle>Resolution graph</CardTitle></CardHeader>
        <CardContent><ResolutionGraph ticket={ticket} /></CardContent>
      </Card>

      <div className="grid grid-cols-1 xl:grid-cols-5 gap-4 items-start">
        {/* Left: evidence */}
        <div className="xl:col-span-3 space-y-4">
          <Card>
            <CardHeader><CardTitle className="flex items-center gap-2"><Mail size={14} /> Original email</CardTitle></CardHeader>
            <CardContent>
              {email ? (
                <>
                  <p className="text-xs text-text-faint font-mono mb-2">From: {email.from_address}</p>
                  <p className="text-sm text-text-primary whitespace-pre-line leading-relaxed">{email.body_text}</p>
                </>
              ) : (
                <p className="text-sm text-text-muted">No email on file for this ticket.</p>
              )}
            </CardContent>
          </Card>

          {ticket.analysis && (
            <Card>
              <CardHeader><CardTitle>AI analysis</CardTitle></CardHeader>
              <CardContent className="space-y-2 text-sm">
                <p className="text-text-primary">{ticket.analysis.summary}</p>
                <div className="flex flex-wrap gap-2 pt-1">
                  <Badge className="border-ink-border text-text-muted bg-white/5">category: {ticket.analysis.category}</Badge>
                  <Badge className="border-ink-border text-text-muted bg-white/5">intent: {ticket.analysis.intent}</Badge>
                  {ticket.analysis.key_entities.map((e) => (
                    <Badge key={e} className="border-ink-border text-text-muted bg-white/5">{e}</Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader><CardTitle className="flex items-center gap-2"><BookOpen size={14} /> Notion knowledge</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              {ticket.knowledge_sources.length === 0 && <p className="text-sm text-text-muted">No matching articles found.</p>}
              {ticket.knowledge_sources.map((k, i) => (
                <div key={i} className="rounded-lg border border-ink-border p-3">
                  <div className="flex items-center justify-between gap-2">
                    <a href={k.url || "#"} target="_blank" rel="noreferrer" className="text-sm font-medium text-signal-teal hover:underline">{k.title}</a>
                    <span className="text-[11px] font-mono text-text-faint">{Math.round(k.relevance_score * 100)}% match</span>
                  </div>
                  {k.excerpt && <p className="text-xs text-text-muted mt-1">{k.excerpt}</p>}
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle className="flex items-center gap-2"><GitBranch size={14} /> Jira & GitHub issues</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              {ticket.engineering_issues.length === 0 && <p className="text-sm text-text-muted">No related engineering issues found.</p>}
              {ticket.engineering_issues.map((issue, i) => (
                <div key={i} className="rounded-lg border border-ink-border p-3 flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <a href={issue.url || "#"} target="_blank" rel="noreferrer" className="text-sm font-medium text-signal-indigo hover:underline truncate block">
                      {issue.external_key || issue.external_id} — {issue.title}
                    </a>
                    <p className="text-xs text-text-faint font-mono mt-0.5">{issue.provider} · {issue.status} · {issue.relation}</p>
                  </div>
                </div>
              ))}
              <Button
                size="sm" variant="outline" disabled={busy === "jira"}
                onClick={() => runAction("jira", () => api.createJiraTicket(ticket.id), "Jira ticket created")}
              >
                {busy === "jira" ? <Loader2 size={13} className="animate-spin" /> : <TicketIcon size={13} />}
                Create Jira ticket
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Right: response + activity */}
        <div className="xl:col-span-2 space-y-4">
          <Card>
            <CardHeader className="flex-col items-start gap-2">
              <div className="w-full flex items-center justify-between">
                <CardTitle>Generated reply</CardTitle>
                {response && <ConfidenceRing score={response.confidence_score} size={40} />}
              </div>
              {response && <Badge className={statusColor[response.status] || "border-ink-border text-text-muted bg-white/5"}>{response.status.replace(/_/g, " ")}</Badge>}
            </CardHeader>
            <CardContent className="space-y-3">
              {response ? (
                editing ? (
                  <textarea
                    className="w-full h-40 rounded-lg bg-ink border border-ink-border p-3 text-sm text-text-primary focus:border-signal-teal/50 outline-none resize-none"
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                  />
                ) : (
                  <p className="text-sm text-text-primary whitespace-pre-line leading-relaxed">{response.body_text}</p>
                )
              ) : (
                <p className="text-sm text-text-muted">No response drafted yet.</p>
              )}

              <div className="flex flex-wrap gap-2 pt-2">
                {editing ? (
                  <>
                    <Button size="sm" variant="primary" disabled={busy === "approve"}
                      onClick={() => runAction("approve", () => api.approveAndSend(ticket.id, draft), "Response edited, approved, and sent")}>
                      {busy === "approve" ? <Loader2 size={13} className="animate-spin" /> : <Send size={13} />} Save & Send
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => { setEditing(false); setDraft(response?.body_text || ""); }}>Cancel</Button>
                  </>
                ) : (
                  <>
                    <Button size="sm" variant="primary" disabled={!canApprove || busy === "approve"}
                      onClick={() => runAction("approve", () => api.approveAndSend(ticket.id), "Approved and sent via Resend")}>
                      {busy === "approve" ? <Loader2 size={13} className="animate-spin" /> : <Send size={13} />} Approve & Send
                    </Button>
                    <Button size="sm" variant="outline" disabled={!response} onClick={() => setEditing(true)}>
                      <Pencil size={13} /> Edit Response
                    </Button>
                    <Button size="sm" variant="danger" disabled={!response || busy === "reject"}
                      onClick={() => runAction("reject", () => api.rejectResponse(ticket.id), "Response rejected")}>
                      {busy === "reject" ? <Loader2 size={13} className="animate-spin" /> : <XCircle size={13} />} Reject
                    </Button>
                    <Button size="sm" variant="secondary" disabled={busy === "escalate"}
                      onClick={() => runAction("escalate", () => api.escalate(ticket.id), "Escalated for human review")}>
                      {busy === "escalate" ? <Loader2 size={13} className="animate-spin" /> : <TriangleAlert size={13} />} Escalate
                    </Button>
                    <Button size="sm" variant="ghost" disabled={busy === "rerun"}
                      onClick={() => runAction("rerun", () => api.rerunAgent(ticket.id), "Agent re-run complete")}>
                      {busy === "rerun" ? <Loader2 size={13} className="animate-spin" /> : <RotateCcw size={13} />} Re-run AI
                    </Button>
                  </>
                )}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Agent activity timeline</CardTitle></CardHeader>
            <CardContent>
              <ActivityTimeline actions={ticket.latest_run?.actions || []} />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
