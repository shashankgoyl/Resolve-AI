import { LucideIcon } from "lucide-react";
import { Card } from "./ui/Card";
import { cn } from "@/lib/utils";

export function StatCard({
  label, value, icon: Icon, accent = "teal", suffix,
}: {
  label: string; value: string | number; icon: LucideIcon; accent?: "teal" | "amber" | "coral" | "indigo"; suffix?: string;
}) {
  const colors = {
    teal: "text-signal-teal bg-signal-teal/10 border-signal-teal/25",
    amber: "text-signal-amber bg-signal-amber/10 border-signal-amber/25",
    coral: "text-signal-coral bg-signal-coral/10 border-signal-coral/25",
    indigo: "text-signal-indigo bg-signal-indigo/10 border-signal-indigo/25",
  }[accent];

  return (
    <Card className="px-5 py-4 flex items-center justify-between">
      <div>
        <p className="text-[11px] uppercase tracking-wide font-mono text-text-faint">{label}</p>
        <p className="mt-1.5 font-display text-2xl font-semibold text-text-primary">
          {value}
          {suffix && <span className="text-sm text-text-muted ml-1 font-body">{suffix}</span>}
        </p>
      </div>
      <div className={cn("w-9 h-9 rounded-lg border flex items-center justify-center shrink-0", colors)}>
        <Icon size={16} />
      </div>
    </Card>
  );
}
