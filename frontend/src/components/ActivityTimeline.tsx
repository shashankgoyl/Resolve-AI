import { Check, X, Clock, Mail, BookOpen, GitBranch, Ticket, Bot, Send, Hourglass } from "lucide-react";
import type { AgentAction } from "@/types";
import { cn, formatClock } from "@/lib/utils";

const ICONS: Record<string, any> = {
  "gmail.fetch_thread": Mail,
  "ai.classify": Bot,
  "notion.search": BookOpen,
  "jira.search": GitBranch,
  "github.search": GitBranch,
  "ai.decide": Bot,
  "ai.generate_reply": Bot,
  "jira.create": Ticket,
  "approval.awaiting": Hourglass,
  "resend.send": Send,
};

const STATUS_STYLES: Record<string, string> = {
  success: "border-signal-teal/40 bg-signal-teal/10 text-signal-teal",
  error: "border-signal-coral/40 bg-signal-coral/10 text-signal-coral",
  pending: "border-signal-amber/40 bg-signal-amber/10 text-signal-amber",
  skipped: "border-ink-border bg-white/5 text-text-faint",
};

function StatusIcon({ status }: { status: string }) {
  if (status === "success") return <Check size={12} />;
  if (status === "error") return <X size={12} />;
  if (status === "pending") return <Clock size={12} />;
  return <Clock size={12} />;
}

export function ActivityTimeline({ actions }: { actions: AgentAction[] }) {
  if (!actions.length) {
    return <p className="text-sm text-text-muted py-6 text-center">No agent activity yet.</p>;
  }

  return (
    <div className="relative pl-2">
      {actions.map((action, idx) => {
        const Icon = ICONS[action.action_type] || Bot;
        const isLast = idx === actions.length - 1;
        return (
          <div key={action.id || idx} className="relative flex gap-3 pb-5 last:pb-0">
            {!isLast && (
              <span className="absolute left-[15px] top-8 bottom-0 w-px bg-ink-border" aria-hidden />
            )}
            <div
              className={cn(
                "relative z-10 shrink-0 w-8 h-8 rounded-full border flex items-center justify-center",
                STATUS_STYLES[action.status]
              )}
            >
              <Icon size={14} />
            </div>
            <div className="flex-1 min-w-0 pt-0.5">
              <div className="flex items-center justify-between gap-3">
                <span className="text-sm text-text-primary font-medium">{action.summary}</span>
                <span className="shrink-0 font-mono text-[11px] text-text-faint">{formatClock(action.created_at)}</span>
              </div>
              <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 font-mono text-[11px] text-text-faint">
                {action.swytchcode_canonical_id && (
                  <span className="px-1.5 py-0.5 rounded bg-white/5 border border-ink-border">
                    swytchcode exec {action.swytchcode_canonical_id}
                  </span>
                )}
                {action.integration && (
                  <span className="uppercase tracking-wide">{action.integration}</span>
                )}
                {typeof action.duration_ms === "number" && action.duration_ms > 0 && (
                  <span>{action.duration_ms}ms</span>
                )}
                <span
                  className={cn(
                    "inline-flex items-center gap-1 px-1.5 py-0.5 rounded border",
                    STATUS_STYLES[action.status]
                  )}
                >
                  <StatusIcon status={action.status} />
                  {action.status}
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
