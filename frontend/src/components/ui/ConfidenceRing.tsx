import { cn } from "@/lib/utils";

export function ConfidenceRing({ score, size = 56 }: { score: number; size?: number }) {
  const pct = Math.max(0, Math.min(1, score));
  const radius = (size - 8) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - pct);
  const color = pct >= 0.85 ? "#4FD1C5" : pct >= 0.6 ? "#F2B84B" : "#F2665B";

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} stroke="#232A38" strokeWidth={5} fill="none" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={5}
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
      </svg>
      <span className={cn("absolute font-mono text-xs font-medium")} style={{ color }}>
        {Math.round(pct * 100)}%
      </span>
    </div>
  );
}
