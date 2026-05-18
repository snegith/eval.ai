import CountUp from "./CountUp";

function ringColor(score) {
  if (score >= 75) return "var(--success)";
  if (score >= 60) return "var(--warning)";
  if (score >= 45) return "#f97316";
  return "var(--danger)";
}

export default function ScoreRing({ score, size = 184, strokeWidth = 12, label }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference * (1 - score / 100);
  const color = ringColor(score);

  return (
    <div className="relative flex items-center justify-center">
      <svg height={size} width={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          fill="transparent"
          r={radius}
          stroke="rgba(255,255,255,0.08)"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          fill="transparent"
          r={radius}
          stroke={color}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          strokeWidth={strokeWidth}
          style={{
            transition: "stroke-dashoffset 0.45s ease-out",
            filter: `drop-shadow(0 0 10px ${color})`,
          }}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <CountUp className="font-mono text-4xl font-semibold text-[var(--text-primary)]" value={score} />
        <span className="mt-2 text-xs uppercase tracking-[0.25em] text-[var(--text-secondary)]">{label}</span>
      </div>
    </div>
  );
}
