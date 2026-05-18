import {
  PolarAngleAxis,
  PolarGrid,
  Radar,
  RadarChart,
  ResponsiveContainer,
} from "recharts";

const axisStyle = {
  fill: "var(--text-secondary)",
  fontSize: 12,
};

export default function PerformanceRadar({ data }) {
  const chartData = [
    { metric: "Eye Contact", score: data.eyeContact.score, target: 70 },
    { metric: "Posture", score: data.posture.score, target: 70 },
    { metric: "Expressiveness", score: data.animation.expressiveness, target: 70 },
    { metric: "Consistency", score: data.animation.consistency, target: 70 },
    { metric: "Stability", score: data.animation.stability, target: 70 },
  ];

  return (
    <div className="h-[360px] w-full">
      <ResponsiveContainer>
        <RadarChart data={chartData}>
          <PolarGrid stroke="rgba(255,255,255,0.08)" />
          <PolarAngleAxis dataKey="metric" tick={axisStyle} />
          <Radar
            dataKey="target"
            stroke="rgba(255,255,255,0.24)"
            fill="transparent"
            strokeDasharray="5 5"
          />
          <Radar
            dataKey="score"
            stroke="var(--accent-primary)"
            fill="rgba(99,102,241,0.30)"
            fillOpacity={1}
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
