import { PolarGrid, Radar, RadarChart, ResponsiveContainer } from "recharts";

export default function MiniRadarChart({ session }) {
  const data = [
    { metric: "Eye", score: session.eyeContact.score },
    { metric: "Posture", score: session.posture.score },
    { metric: "Expr", score: session.animation.expressiveness },
    { metric: "Cons", score: session.animation.consistency },
    { metric: "Stab", score: session.animation.stability },
  ];

  return (
    <div className="h-32 w-full">
      <ResponsiveContainer>
        <RadarChart data={data}>
          <PolarGrid stroke="rgba(255,255,255,0.08)" />
          <Radar dataKey="score" stroke="var(--accent-primary)" fill="rgba(99,102,241,0.24)" />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
