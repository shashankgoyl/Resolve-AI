import { useEffect, useState } from "react";
import { Mail, BookOpen, GitBranch, Github, Send, Zap } from "lucide-react";
import { api } from "@/lib/api";
import type { IntegrationStatus } from "@/types";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { healthColor } from "@/lib/utils";

const META: Record<string, { label: string; icon: any; blurb: string }> = {
  gmail: { label: "Gmail", icon: Mail, blurb: "Reads customer support emails" },
  notion: { label: "Notion", icon: BookOpen, blurb: "Searches the internal knowledge base" },
  jira: { label: "Jira", icon: GitBranch, blurb: "Finds and creates engineering tickets" },
  github: { label: "GitHub", icon: Github, blurb: "Finds related open-source / repo issues" },
  resend: { label: "Resend", icon: Send, blurb: "Sends approved replies to customers" },
  swytchcode: { label: "Swytchcode", icon: Zap, blurb: "Execution layer for every integration above" },
};

export function IntegrationsPage() {
  const [items, setItems] = useState<IntegrationStatus[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.integrations().then(setItems).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="p-6 text-text-muted text-sm">Loading integrations…</div>;

  return (
    <div className="p-6">
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {items.map((item) => {
          const meta = META[item.provider];
          const Icon = meta?.icon || Zap;
          return (
            <Card key={item.provider}>
              <CardContent className="flex items-start justify-between gap-3">
                <div className="flex items-start gap-3">
                  <div className="w-9 h-9 rounded-lg border border-ink-border bg-white/5 flex items-center justify-center shrink-0">
                    <Icon size={16} className="text-text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-text-primary">{meta?.label || item.provider}</p>
                    <p className="text-xs text-text-muted mt-0.5">{meta?.blurb}</p>
                  </div>
                </div>
                <Badge className={healthColor[item.health]}>{item.health}</Badge>
              </CardContent>
            </Card>
          );
        })}
      </div>
      <p className="text-xs text-text-faint font-mono mt-4">
        All calls above route through Swytchcode's execution kernel — no direct API keys for these providers ever touch this backend.
      </p>
    </div>
  );
}
