import CountUp from "./CountUp";

export default function CircularGauge({ value, title, note, color, trackColor = "rgba(255,255,255,0.08)" }) {
  const size = 164;
  const strokeWidth = 10;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.max(0, Math.min(100, value));
  const offset = circumference * (1 - clamped / 100);

  return (
    <div className="surface-card surface-elevated p-6">
      <div className="mb-6 flex items-center justify-between">
        <h3 className="text-lg font-semibold tracking-tight">{title}</h3>
        <span className="rounded-full border border-[var(--border-subtle)] px-3 py-1 font-mono text-xs text-[var(--text-secondary)]">
          Derived
        </span>
      </div>
      <div className="flex flex-col items-center gap-4">
        <div className="relative flex items-center justify-center">
          <svg className="-rotate-90" height={size} width={size}>
            <circle
              cx={size / 2}
              cy={size / 2}
              fill="transparent"
              r={radius}
              stroke={trackColor}
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
                filter: `drop-shadow(0 0 12px ${color})`,
              }}
            />
          </svg>
          <div className="absolute flex flex-col items-center">
            <CountUp className="font-mono text-3xl font-semibold" value={clamped} />
            <span className="text-xs uppercase tracking-[0.24em] text-[var(--text-secondary)]">/100</span>
          </div>
        </div>
        <p className="text-center text-sm text-[var(--text-secondary)]">{note}</p>
      </div>
    </div>
  );
}
