import { useEffect, useState } from "react";
import { Ticket, CheckCircle2, Inbox, GitBranch, Timer, TrendingUp } from "lucide-react";
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from "recharts";
import { api } from "@/lib/api";
import type { DashboardStats } from "@/types";
import { StatCard } from "@/components/StatCard";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";
import { sentimentEmoji } from "@/lib/utils";

const SENTIMENT_COLORS: Record<string, string> = {
  positive: "#4FD1C5",
  neutral: "#7C8CF8",
  negative: "#F2B84B",
  frustrated: "#F2665B",
};

export function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.dashboardStats().then(setStats).finally(() => setLoading(false));
  }, []);

  if (loading || !stats) {
    return <div className="p-6 text-text-muted text-sm">Loading dashboard…</div>;
  }

  const sentimentData = Object.entries(stats.sentiment_breakdown).map(([name, value]) => ({ name, value }));

  return (
    <div className="p-6 space-y-6">
      <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        <StatCard label="Total tickets" value={stats.total_tickets} icon={Ticket} accent="indigo" />
        <StatCard label="AI resolved" value={stats.ai_resolved} icon={CheckCircle2} accent="teal" />
        <StatCard label="Open tickets" value={stats.open_tickets} icon={Inbox} accent="amber" />
        <StatCard label="Escalations" value={stats.engineering_escalations} icon={GitBranch} accent="coral" />
        <StatCard label="Avg resolution" value={stats.avg_resolution_minutes} suffix="min" icon={Timer} accent="indigo" />
        <StatCard label="Resolution rate" value={`${Math.round(stats.resolution_rate * 100)}%`} icon={TrendingUp} accent="teal" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Pipeline status</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-text-muted leading-relaxed">
              Resolve AI reads support email through Gmail, classifies and researches every ticket
              against Notion, Jira, and GitHub, then drafts a reply and either resolves the ticket,
              escalates it to engineering, or routes it to a human — every step executed and logged
              through Swytchcode. Open a ticket from the Inbox to see the full agent run and resolution graph.
            </p>
            <div className="mt-4 grid grid-cols-3 gap-3 text-center">
              <div className="rounded-lg border border-ink-border py-3">
                <p className="font-display text-lg font-semibold text-signal-teal">{stats.ai_resolved}</p>
                <p className="text-[11px] text-text-faint font-mono uppercase mt-1">Auto-resolved</p>
              </div>
              <div className="rounded-lg border border-ink-border py-3">
                <p className="font-display text-lg font-semibold text-signal-amber">{stats.engineering_escalations}</p>
                <p className="text-[11px] text-text-faint font-mono uppercase mt-1">To engineering</p>
              </div>
              <div className="rounded-lg border border-ink-border py-3">
                <p className="font-display text-lg font-semibold text-signal-indigo">{stats.open_tickets}</p>
                <p className="text-[11px] text-text-faint font-mono uppercase mt-1">Awaiting agent</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Customer sentiment</CardTitle>
          </CardHeader>
          <CardContent>
            {sentimentData.length === 0 ? (
              <p className="text-sm text-text-muted">No sentiment data yet.</p>
            ) : (
              <div className="h-52">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={sentimentData} dataKey="value" nameKey="name" innerRadius={45} outerRadius={70} paddingAngle={3}>
                      {sentimentData.map((entry) => (
                        <Cell key={entry.name} fill={SENTIMENT_COLORS[entry.name] || "#7C8CF8"} stroke="none" />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{ background: "#12161F", border: "1px solid #232A38", borderRadius: 8, fontSize: 12 }}
                      formatter={(value: number, name: string) => [value, `${sentimentEmoji[name] || ""} ${name}`]}
                    />
                    <Legend
                      formatter={(value: string) => <span className="text-xs text-text-muted">{sentimentEmoji[value]} {value}</span>}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
