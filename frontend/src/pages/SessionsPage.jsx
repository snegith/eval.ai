import { motion } from "framer-motion";
import { Search } from "lucide-react";
import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import CountUp from "../components/ui/CountUp";
import EmptyState from "../components/ui/EmptyState";
import ProgressBar from "../components/ui/ProgressBar";
import Skeleton from "../components/ui/Skeleton";
import { useSessionStore } from "../hooks/useSessionStore";
import { formatDate, formatDuration, scoreColor } from "../lib/formatters";

export default function SessionsPage() {
  const { sessions, loading, error, mode } = useSessionStore();
  const [query, setQuery] = useState("");
  const [sortBy, setSortBy] = useState("newest");

  const filteredSessions = useMemo(() => {
    const base = sessions.filter((session) =>
      [session.id, session.feedback.summary, session.status].join(" ").toLowerCase().includes(query.toLowerCase()),
    );

    const sorted = [...base];
    if (sortBy === "highest") sorted.sort((a, b) => b.overallScore - a.overallScore);
    else if (sortBy === "lowest") sorted.sort((a, b) => a.overallScore - b.overallScore);
    else sorted.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
    return sorted;
  }, [query, sessions, sortBy]);

  return (
    <div className="space-y-8">
      <div>
        <p className="font-mono text-xs uppercase tracking-[0.28em] text-[var(--accent-primary)]">History</p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight">Sessions</h1>
      </div>

      <Card className="p-4 sm:p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center">
          <div className="relative flex-1">
            <Search size={18} className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
            <input
              className="w-full rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-tertiary)] py-3 pl-11 pr-4 text-[var(--text-primary)] outline-none transition-all focus:border-[var(--border-active)] focus:ring-2 focus:ring-[rgba(99,102,241,0.18)]"
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search by session ID, summary, or status"
              value={query}
            />
          </div>
          <select
            className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-tertiary)] px-4 py-3 text-[var(--text-primary)] outline-none focus:border-[var(--border-active)]"
            onChange={(event) => setSortBy(event.target.value)}
            value={sortBy}
          >
            <option value="newest">Newest</option>
            <option value="highest">Highest Score</option>
            <option value="lowest">Lowest Score</option>
          </select>
        </div>
      </Card>

      {mode === "mock" && error ? (
        <Card className="border-[rgba(245,158,11,0.24)] bg-[rgba(245,158,11,0.08)] p-4">
          <p className="text-sm text-[var(--warning)]">Showing locally cached mock sessions because the backend could not be reached.</p>
          <p className="mt-1 text-xs text-[var(--text-secondary)]">{error}</p>
        </Card>
      ) : null}

      {loading ? (
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, index) => (
            <Card key={index} className="p-6">
              <Skeleton className="h-5 w-28" />
              <Skeleton className="mt-4 h-10 w-24" />
              <Skeleton className="mt-6 h-24 w-full" />
            </Card>
          ))}
        </div>
      ) : filteredSessions.length === 0 ? (
        <EmptyState
          title="No sessions yet"
          description="Upload a video to start generating interview intelligence, behavioral metrics, and AI feedback."
        />
      ) : (
        <motion.div
          className="grid gap-5 md:grid-cols-2 xl:grid-cols-3"
          initial="hidden"
          animate="visible"
          variants={{ hidden: {}, visible: { transition: { staggerChildren: 0.05 } } }}
        >
          {filteredSessions.map((session) => (
            <motion.div
              key={session.id}
              variants={{ hidden: { opacity: 0, y: 20 }, visible: { opacity: 1, y: 0 } }}
            >
              <Card className="flex h-full flex-col p-6">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="font-mono text-sm text-[var(--text-secondary)]">{session.id}</div>
                    <div className="mt-1 text-sm text-[var(--text-secondary)]">
                      {formatDate(session.createdAt)} · {formatDuration(session.durationSeconds)}
                    </div>
                    <div className="mt-2 text-xs uppercase tracking-[0.2em] text-[var(--text-muted)]">{session.status}</div>
                  </div>
                  <div className="font-mono text-4xl font-semibold" style={{ color: scoreColor(session.overallScore) }}>
                    <CountUp value={session.overallScore} />
                  </div>
                </div>

                <div className="mt-6 space-y-4">
                  {[
                    ["Eye Contact", session.eyeContact.score],
                    ["Posture", session.posture.score],
                    ["Animation", session.animation.score],
                  ].map(([label, value]) => (
                    <div key={label}>
                      <div className="mb-2 flex items-center justify-between text-sm">
                        <span className="text-[var(--text-secondary)]">{label}</span>
                        <span className="font-mono text-[var(--text-primary)]">{value}</span>
                      </div>
                      <ProgressBar value={value} />
                    </div>
                  ))}
                </div>

                <div className="mt-6">
                  <Link to={`/results/${session.id}`}>
                    <Button variant="secondary" className="w-full">
                      View Results
                    </Button>
                  </Link>
                </div>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      )}
    </div>
  );
}
