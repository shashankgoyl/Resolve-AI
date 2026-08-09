import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "@/lib/api";
import type { SupportTicket } from "@/types";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { priorityColor, statusColor, sentimentEmoji, formatRelativeTime } from "@/lib/utils";

export function InboxPage() {
  const [tickets, setTickets] = useState<SupportTicket[]>([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    api.listTickets().then(setTickets).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-6 text-text-muted text-sm">Loading inbox…</div>;

  return (
    <div className="p-6">
      <Card className="overflow-hidden">
        <div className="grid grid-cols-[1fr_auto_auto_auto_auto] gap-4 px-5 py-3 border-b border-ink-border text-[11px] font-mono uppercase tracking-wide text-text-faint">
          <span>Customer / Issue</span>
          <span>Priority</span>
          <span>Sentiment</span>
          <span>Status</span>
          <span>Received</span>
        </div>
        <div className="divide-y divide-ink-border">
          {tickets.map((t) => (
            <button
              key={t.id}
              onClick={() => navigate(`/tickets/${t.id}`)}
              className="w-full grid grid-cols-[1fr_auto_auto_auto_auto] gap-4 px-5 py-4 items-center text-left hover:bg-white/[0.03] transition-colors"
            >
              <div className="min-w-0">
                <p className="text-sm font-medium text-text-primary truncate">{t.subject}</p>
                <p className="text-xs text-text-muted mt-0.5 font-mono truncate">
                  {t.ticket_number} · {t.customer.full_name} · {t.customer.company}
                </p>
              </div>
              <Badge className={priorityColor[t.priority]}>{t.priority}</Badge>
              <span className="text-lg leading-none" title={t.sentiment || ""}>
                {t.sentiment ? sentimentEmoji[t.sentiment] : "—"}
              </span>
              <Badge className={statusColor[t.status]}>{t.status.replace(/_/g, " ")}</Badge>
              <span className="text-xs font-mono text-text-faint whitespace-nowrap">{formatRelativeTime(t.created_at)}</span>
            </button>
          ))}
        </div>
      </Card>
    </div>
  );
}
