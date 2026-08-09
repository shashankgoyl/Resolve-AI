import { MessageSquare, BookOpen, GitBranch, Brain, CheckCircle2, Send, ArrowRight } from "lucide-react";
import type { TicketDetail } from "@/types";
import { ConfidenceRing } from "./ui/ConfidenceRing";
import { decisionColor, cn } from "@/lib/utils";

export function ResolutionGraph({ ticket }: { ticket: TicketDetail }) {
  const nodes = [
    { icon: MessageSquare, label: "Customer Issue", detail: ticket.analysis?.category || ticket.category || "—", active: true },
    { icon: BookOpen, label: "Knowledge", detail: `${ticket.knowledge_sources.length} Notion match${ticket.knowledge_sources.length === 1 ? "" : "es"}`, active: ticket.knowledge_sources.length > 0 },
    { icon: GitBranch, label: "Eng. Evidence", detail: `${ticket.engineering_issues.length} issue${ticket.engineering_issues.length === 1 ? "" : "s"}`, active: ticket.engineering_issues.length > 0 },
    { icon: Brain, label: "AI Decision", detail: ticket.decision?.replace(/_/g, " ") || "pending", active: !!ticket.decision },
    { icon: CheckCircle2, label: "Resolution", detail: ticket.decision === "RESOLVED" ? "Resolved" : "Drafted", active: !!ticket.latest_response },
    { icon: Send, label: "Response", detail: ticket.latest_response?.status.replace(/_/g, " ") || "—", active: ticket.latest_response?.status === "sent" },
  ];

  return (
    <div className="flex items-stretch gap-1 overflow-x-auto pb-1">
      {nodes.map((n, idx) => (
        <div key={n.label} className="flex items-center">
          <div
            className={cn(
              "flex flex-col items-center gap-1.5 rounded-lg border px-3 py-3 min-w-[104px] text-center shrink-0",
              n.active ? "border-signal-teal/30 bg-signal-teal/5" : "border-ink-border bg-white/[0.02]"
            )}
          >
            <n.icon size={16} className={n.active ? "text-signal-teal" : "text-text-faint"} />
            <span className="text-[11px] font-medium text-text-primary leading-tight">{n.label}</span>
            <span className="text-[10px] font-mono text-text-faint capitalize leading-tight">{n.detail}</span>
          </div>
          {idx < nodes.length - 1 && (
            <ArrowRight size={14} className="text-ink-border mx-1 shrink-0" />
          )}
        </div>
      ))}
      {ticket.confidence_score != null && (
        <div className="flex items-center gap-2 ml-3 pl-3 border-l border-ink-border shrink-0">
          <ConfidenceRing score={ticket.confidence_score} size={48} />
          <div className="text-left">
            <p className="text-[11px] text-text-muted leading-tight">AI Confidence</p>
            {ticket.decision && (
              <span className={cn("inline-block mt-0.5 text-[10px] font-mono px-1.5 py-0.5 rounded border", decisionColor[ticket.decision])}>
                {ticket.decision.replace(/_/g, " ")}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
