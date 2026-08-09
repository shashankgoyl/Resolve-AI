import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatRelativeTime(iso?: string | null): string {
  if (!iso) return "—";
  const date = new Date(iso);
  const diffMs = Date.now() - date.getTime();
  const diffMin = Math.round(diffMs / 60000);
  if (diffMin < 1) return "just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.round(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.round(diffHr / 24);
  return `${diffDay}d ago`;
}

export function formatClock(iso?: string | null): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export const priorityColor: Record<string, string> = {
  low: "text-text-muted bg-white/5 border-ink-border",
  medium: "text-signal-indigo bg-signal-indigo/10 border-signal-indigo/30",
  high: "text-signal-amber bg-signal-amber/10 border-signal-amber/30",
  urgent: "text-signal-coral bg-signal-coral/10 border-signal-coral/30",
};

export const statusColor: Record<string, string> = {
  open: "text-signal-indigo bg-signal-indigo/10 border-signal-indigo/30",
  in_progress: "text-signal-amber bg-signal-amber/10 border-signal-amber/30",
  resolved: "text-signal-teal bg-signal-teal/10 border-signal-teal/30",
  escalated: "text-signal-coral bg-signal-coral/10 border-signal-coral/30",
  closed: "text-text-muted bg-white/5 border-ink-border",
};

export const decisionColor: Record<string, string> = {
  RESOLVED: "text-signal-teal bg-signal-teal/10 border-signal-teal/30",
  NEEDS_ENGINEERING: "text-signal-amber bg-signal-amber/10 border-signal-amber/30",
  NEEDS_HUMAN_REVIEW: "text-signal-indigo bg-signal-indigo/10 border-signal-indigo/30",
  INSUFFICIENT_INFORMATION: "text-signal-coral bg-signal-coral/10 border-signal-coral/30",
};

export const sentimentEmoji: Record<string, string> = {
  positive: "🙂",
  neutral: "😐",
  negative: "🙁",
  frustrated: "😤",
};

export const healthColor: Record<string, string> = {
  connected: "text-signal-teal bg-signal-teal/10 border-signal-teal/30",
  degraded: "text-signal-amber bg-signal-amber/10 border-signal-amber/30",
  disconnected: "text-signal-coral bg-signal-coral/10 border-signal-coral/30",
  demo: "text-signal-indigo bg-signal-indigo/10 border-signal-indigo/30",
};
