import { motion } from "framer-motion";
import { ArrowRight, BarChart3, Trophy, Video } from "lucide-react";
import { Link } from "react-router-dom";
import MiniRadarChart from "../components/charts/MiniRadarChart";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import CountUp from "../components/ui/CountUp";
import EmptyState from "../components/ui/EmptyState";
import Skeleton from "../components/ui/Skeleton";
import { useSessionStore } from "../hooks/useSessionStore";
import { formatDate } from "../lib/formatters";

const statCards = [
  { key: "totalSessions", label: "Total Sessions", icon: Video },
  { key: "averageScore", label: "Average Score", icon: BarChart3 },
  { key: "bestScore", label: "Best Score", icon: Trophy },
];

export default function HomePage() {
  const { stats, loading, error, mode } = useSessionStore();
  const hasRecentSession = Boolean(stats.recentSession);

  return (
    <div className="space-y-8">
      <Card className="overflow-hidden p-8 sm:p-10" glass>
        <motion.div
          className="grid gap-10 lg:grid-cols-[1.3fr_0.7fr]"
          initial="hidden"
          animate="visible"
          variants={{ hidden: {}, visible: { transition: { staggerChildren: 0.05 } } }}
        >
          <motion.div variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}>
            <div className="mb-4 font-mono text-xs uppercase tracking-[0.28em] text-[var(--accent-primary)]">
              Mission Control for Interview Performance
            </div>
            <h1 className="max-w-2xl text-4xl font-semibold tracking-tight sm:text-5xl">
              Your Interview Intelligence Platform
            </h1>
            <p className="mt-4 max-w-2xl text-lg text-[var(--text-secondary)]">
              Review behavioral metrics, session trends, and AI coaching feedback in one premium analysis workspace.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link to="/upload">
                <Button className="w-full sm:w-auto">
                  Start New Session
                  <ArrowRight size={16} className="ml-2" />
                </Button>
              </Link>
              <Link to="/sessions">
                <Button variant="secondary" className="w-full sm:w-auto">
                  View Results
                </Button>
              </Link>
            </div>
          </motion.div>

          <motion.div variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}>
            <Card className="h-full p-6">
              <div className="mb-4 flex items-center justify-between">
                <div>
                  <p className="font-mono text-xs uppercase tracking-[0.22em] text-[var(--text-secondary)]">Latest Session</p>
                  <h2 className="mt-2 text-xl font-semibold tracking-tight">{stats.recentSession?.grade ?? "No Data"}</h2>
                </div>
                <div className="rounded-full border border-[var(--border-subtle)] px-3 py-1 font-mono text-sm text-[var(--text-secondary)]">
                  {stats.recentSession ? formatDate(stats.recentSession.createdAt) : "--"}
                </div>
              </div>
              {loading ? (
                <Skeleton className="h-32 w-full" />
              ) : hasRecentSession ? (
                <>
                  <MiniRadarChart session={stats.recentSession} />
                  <div className="mt-4 grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm text-[var(--text-secondary)]">Overall Score</div>
                      <div className="mt-1 font-mono text-3xl font-semibold">{stats.recentSession?.overallScore ?? "--"}</div>
                    </div>
                    <div>
                      <div className="text-sm text-[var(--text-secondary)]">Session ID</div>
                      <div className="mt-1 truncate font-mono text-sm text-[var(--text-primary)]">
                        {stats.recentSession?.id ?? "No session available"}
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                <EmptyState
                  title="No sessions yet"
                  description="Run your first interview analysis to populate the dashboard with recent metrics and AI feedback."
                />
              )}
            </Card>
          </motion.div>
        </motion.div>
      </Card>

      {mode === "mock" && error ? (
        <Card className="border-[rgba(245,158,11,0.24)] bg-[rgba(245,158,11,0.08)] p-4">
          <p className="text-sm text-[var(--warning)]">Showing mock data because the FastAPI backend is unavailable.</p>
          <p className="mt-1 text-xs text-[var(--text-secondary)]">{error}</p>
        </Card>
      ) : null}

      <div className="grid gap-4 md:grid-cols-3">
        {statCards.map((item, index) => {
          const Icon = item.icon;
          return (
            <motion.div
              key={item.key}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1 + index * 0.05, duration: 0.4 }}
            >
              <Card className="p-6">
                <div className="mb-5 flex items-center justify-between">
                  <div className="rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-tertiary)] p-3">
                    <Icon size={18} className="text-[var(--accent-primary)]" />
                  </div>
                  <span className="text-sm text-[var(--text-muted)]">Aggregate</span>
                </div>
                <div className="text-sm text-[var(--text-secondary)]">{item.label}</div>
                <div className="mt-2 font-mono text-4xl font-semibold">
                  {loading ? <Skeleton className="h-11 w-24" /> : <CountUp value={stats[item.key]} />}
                </div>
              </Card>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
