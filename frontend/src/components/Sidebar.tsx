import { NavLink } from "react-router-dom";
import { LayoutDashboard, Inbox, Plug, ScrollText, Zap } from "lucide-react";
import { cn } from "@/lib/utils";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/inbox", label: "Inbox", icon: Inbox },
  { to: "/integrations", label: "Integrations", icon: Plug },
  { to: "/audit-logs", label: "Audit Logs", icon: ScrollText },
];

export function Sidebar() {
  return (
    <aside className="w-60 shrink-0 border-r border-ink-border bg-ink-panel/60 flex flex-col">
      <div className="h-16 flex items-center gap-2 px-5 border-b border-ink-border">
        <div className="w-7 h-7 rounded-md bg-signal-teal/15 border border-signal-teal/30 flex items-center justify-center">
          <Zap size={15} className="text-signal-teal" />
        </div>
        <span className="font-display font-semibold text-sm tracking-wide">Resolve AI</span>
      </div>

      <nav className="flex-1 px-3 py-4 flex flex-col gap-1">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors",
                isActive
                  ? "bg-signal-teal/10 text-signal-teal border border-signal-teal/20"
                  : "text-text-muted hover:text-text-primary hover:bg-white/5 border border-transparent"
              )
            }
          >
            <Icon size={16} />
            {label}
          </NavLink>
        ))}
      </nav>

      <div className="px-4 py-4 border-t border-ink-border">
        <div className="rounded-lg border border-ink-border bg-ink/40 px-3 py-2.5">
          <p className="text-[11px] text-text-faint font-mono leading-relaxed">
            Gmail → AI → Notion → Jira/GitHub
            <br />→ Decision → Approval → Resend
          </p>
        </div>
      </div>
    </aside>
  );
}
