import { useEffect, useState } from "react";
import { Bot, User, Cpu } from "lucide-react";
import { api } from "@/lib/api";
import type { AuditLogEntry } from "@/types";
import { Card } from "@/components/ui/Card";
import { formatRelativeTime, formatClock, cn } from "@/lib/utils";

const ACTOR_ICON: Record<string, any> = { ai_agent: Bot, human: User, system: Cpu };
const ACTOR_COLOR: Record<string, string> = {
  ai_agent: "text-signal-indigo bg-signal-indigo/10 border-signal-indigo/30",
  human: "text-signal-teal bg-signal-teal/10 border-signal-teal/30",
  system: "text-text-muted bg-white/5 border-ink-border",
};

export function AuditLogsPage() {
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.auditLogs().then(setLogs).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-6 text-text-muted text-sm">Loading audit log…</div>;

  return (
    <div className="p-6">
      <Card className="overflow-hidden">
        <div className="divide-y divide-ink-border">
          {logs.length === 0 && <p className="p-5 text-sm text-text-muted">No audit events yet.</p>}
          {logs.map((log) => {
            const Icon = ACTOR_ICON[log.actor_type] || Cpu;
            return (
              <div key={log.id} className="flex items-start gap-3 px-5 py-3.5">
                <div className={cn("w-7 h-7 rounded-full border flex items-center justify-center shrink-0 mt-0.5", ACTOR_COLOR[log.actor_type])}>
                  <Icon size={13} />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm text-text-primary">{log.description}</p>
                    <span className="shrink-0 font-mono text-[11px] text-text-faint">{formatClock(log.created_at)}</span>
                  </div>
                  <div className="mt-1 flex items-center gap-2 font-mono text-[11px] text-text-faint">
                    <span>{log.actor_label || log.actor_type}</span>
                    <span>·</span>
                    <span>{log.event_type}</span>
                    {log.ticket_id && (
                      <>
                        <span>·</span>
                        <span>{log.ticket_id}</span>
                      </>
                    )}
                    <span>·</span>
                    <span>{formatRelativeTime(log.created_at)}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
}
