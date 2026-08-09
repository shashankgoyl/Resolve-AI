import { useEffect, useState } from "react";
import { Circle } from "lucide-react";
import { api } from "@/lib/api";

export function Topbar({ title }: { title: string }) {
  const [demoMode, setDemoMode] = useState<boolean | null>(null);

  useEffect(() => {
    api.health().then((h) => setDemoMode(h.demo_mode)).catch(() => setDemoMode(null));
  }, []);

  return (
    <header className="h-16 border-b border-ink-border flex items-center justify-between px-6 bg-ink/60 backdrop-blur">
      <h1 className="font-display text-base font-semibold">{title}</h1>
      {demoMode !== null && (
        <div
          className={
            demoMode
              ? "flex items-center gap-1.5 text-[11px] font-mono uppercase tracking-wide px-2.5 py-1 rounded-full border border-signal-indigo/30 text-signal-indigo bg-signal-indigo/10"
              : "flex items-center gap-1.5 text-[11px] font-mono uppercase tracking-wide px-2.5 py-1 rounded-full border border-signal-teal/30 text-signal-teal bg-signal-teal/10"
          }
        >
          <Circle size={7} className="fill-current" />
          {demoMode ? "Demo mode" : "Live via Swytchcode"}
        </div>
      )}
    </header>
  );
}
