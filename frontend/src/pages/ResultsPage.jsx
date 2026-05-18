import { motion } from "framer-motion";
import { ArrowLeft, Camera, Eye, ScanFace, Sparkles, UserRound } from "lucide-react";
import { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import PerformanceRadar from "../components/charts/PerformanceRadar";
import Accordion from "../components/ui/Accordion";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import CircularGauge from "../components/ui/CircularGauge";
import CountUp from "../components/ui/CountUp";
import EmptyState from "../components/ui/EmptyState";
import ProgressBar from "../components/ui/ProgressBar";
import ScoreRing from "../components/ui/ScoreRing";
import Skeleton from "../components/ui/Skeleton";
import { useSessionStore } from "../hooks/useSessionStore";
import { formatDate, formatDuration, scoreColor } from "../lib/formatters";

const metricCards = [
  { key: "eyeContact", title: "Eye Contact", icon: Eye },
  { key: "posture", title: "Posture", icon: UserRound },
  { key: "animation", title: "Facial Animation", icon: ScanFace },
];

function FeedbackList({ items, emptyCopy, color, numbered = false }) {
  if (!items.length) {
    return <p className="text-[var(--text-secondary)]">{emptyCopy}</p>;
  }

  return (
    <div className="space-y-3">
      {items.map((item, index) => (
        <motion.div
          key={`${item}-${index}`}
          animate={{ opacity: 1, x: 0 }}
          className="flex gap-3"
          initial={{ opacity: 0, x: -12 }}
          transition={{ delay: 0.05 * index, duration: 0.3 }}
        >
          {numbered ? (
            <span className="font-mono text-lg text-[var(--accent-primary)]">{index + 1}</span>
          ) : (
            <span className="mt-2 h-2.5 w-2.5 rounded-full" style={{ background: color }} />
          )}
          <p className="text-[var(--text-secondary)]">{item}</p>
        </motion.div>
      ))}
    </div>
  );
}

function ResumeReviewList({ items, color }) {
  if (!items.length) {
    return <p className="text-[var(--text-secondary)]">No review items available.</p>;
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item} className="flex gap-3">
          <span className="mt-2 h-2.5 w-2.5 rounded-full" style={{ background: color }} />
          <p className="text-[var(--text-secondary)]">{item}</p>
        </div>
      ))}
    </div>
  );
}

function QuestionCards({ questions }) {
  if (!questions.length) {
    return <p className="text-[var(--text-secondary)]">No generated questions are available for this session yet.</p>;
  }

  return (
    <div className="grid gap-4 xl:grid-cols-2">
      {questions.map((item, index) => (
        <Card key={`${item.question}-${index}`} className="p-5">
          <div className="mb-3 flex items-center justify-between gap-3">
            <span className="rounded-full border border-[var(--border-subtle)] bg-[var(--bg-tertiary)] px-3 py-1 text-xs uppercase tracking-[0.2em] text-[var(--text-secondary)]">
              {item.category.replace("_", " ")}
            </span>
            <span className="font-mono text-xs text-[var(--text-muted)]">Q{index + 1}</span>
          </div>
          <h4 className="text-lg font-semibold tracking-tight text-[var(--text-primary)]">{item.question}</h4>
          <p className="mt-3 text-sm text-[var(--text-secondary)]">{item.rationale}</p>
        </Card>
      ))}
    </div>
  );
}

export default function ResultsPage() {
  const { sessionId } = useParams();
  const navigate = useNavigate();
  const { getSessionById, loading } = useSessionStore();
  const session = getSessionById(sessionId);
  const [openSections, setOpenSections] = useState({
    eyeContact: true,
    posture: false,
    animation: false,
  });

  const starCards = useMemo(() => {
    if (!session?.feedback.star?.applicable) return [];
    return [
      ["Situation", session.feedback.star.situation],
      ["Task", session.feedback.star.task],
      ["Action", session.feedback.star.action],
      ["Result", session.feedback.star.result],
    ];
  }, [session]);

  if (!session && !loading) {
    return (
      <EmptyState
        title="Session not found"
        description="The requested results could not be loaded. Return to sessions and choose another analysis run."
      />
    );
  }

  const exportJson = () => {
    const blob = new Blob([JSON.stringify(session.raw ?? session, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${session.id}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const exportReport = () => {
    const report = `
EVAL.AI REPORT
Session: ${session.id}
Date: ${formatDate(session.createdAt)}
Duration: ${formatDuration(session.durationSeconds)}

Overall Score: ${session.overallScore}
Eye Contact: ${session.eyeContact.score}
Posture: ${session.posture.score}
Animation: ${session.animation.score}

Summary:
${session.feedback.summary}
`;
    const blob = new Blob([report.trim()], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${session.id}-report.txt`;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-6 lg:flex-row lg:items-start lg:justify-between">
        <div className="space-y-3">
          <button
            className="inline-flex items-center gap-2 text-sm text-[var(--text-secondary)] transition-colors hover:text-[var(--text-primary)]"
            onClick={() => navigate(-1)}
            type="button"
          >
            <ArrowLeft size={16} />
            Back
          </button>
          <div className="font-mono text-sm text-[var(--text-secondary)]">{loading ? <Skeleton className="h-5 w-52" /> : session.id}</div>
          <h1 className="text-4xl font-semibold tracking-tight">Results Dashboard</h1>
        </div>
        <div className="text-sm text-[var(--text-secondary)] lg:text-right">
          {loading ? (
            <Skeleton className="h-16 w-48" />
          ) : (
            <>
              <div>{formatDate(session.createdAt)}</div>
              <div>{formatDuration(session.durationSeconds)}</div>
            </>
          )}
        </div>
      </div>

      {session?.framingQuality?.hasWarnings ? (
        <Card className="flex items-start gap-4 border-[rgba(245,158,11,0.28)] bg-[rgba(245,158,11,0.08)] p-5">
          <div className="rounded-2xl bg-[rgba(245,158,11,0.15)] p-3 text-[var(--warning)]">
            <Camera size={18} />
          </div>
          <div>
            <p className="font-semibold tracking-tight text-[var(--text-primary)]">Framing warning detected</p>
            <p className="mt-1 text-sm text-[var(--text-secondary)]">{session.framingQuality.message}</p>
          </div>
        </Card>
      ) : null}

      <Card className="p-8">
        <div className="flex flex-col gap-8 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-center justify-center">
            {loading ? <Skeleton className="h-[184px] w-[184px] rounded-full" /> : <ScoreRing label={session.grade} score={session.overallScore} />}
          </div>
          <div className="max-w-2xl">
            <p className="font-mono text-xs uppercase tracking-[0.28em] text-[var(--text-secondary)]">Overall Assessment</p>
            <h2 className="mt-3 text-3xl font-semibold tracking-tight">{loading ? <Skeleton className="h-10 w-48" /> : session.grade}</h2>
            <p className="mt-4 text-[var(--text-secondary)]">
              {loading ? <Skeleton className="h-20 w-full" /> : session.feedback.summary}
            </p>
          </div>
        </div>
      </Card>

      <div className="grid gap-5 xl:grid-cols-3">
        {metricCards.map(({ key, title, icon: Icon }, index) => {
          const metric = session?.[key];
          const value = metric?.score ?? 0;
          return (
            <motion.div
              key={key}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.05 * index, duration: 0.35 }}
            >
              <Card className="p-6">
                <div className="mb-5 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-tertiary)] p-3 text-[var(--accent-primary)]">
                      <Icon size={18} />
                    </div>
                    <h3 className="text-xl font-semibold tracking-tight">{title}</h3>
                  </div>
                  <span
                    className="rounded-full px-3 py-1 text-xs font-medium"
                    style={{ color: scoreColor(value), background: `${scoreColor(value)}20` }}
                  >
                    {metric?.grade}
                  </span>
                </div>

                <div className="mb-4 font-mono text-4xl font-semibold">
                  {loading ? <Skeleton className="h-11 w-24" /> : <CountUp value={value} />}
                </div>
                <ProgressBar value={value} color={scoreColor(value)} />

                <div className="mt-5">
                  <Accordion
                    open={openSections[key]}
                    onToggle={() => setOpenSections((prev) => ({ ...prev, [key]: !prev[key] }))}
                    title="View details"
                  >
                    {key === "eyeContact" ? (
                      <div className="space-y-2">
                        <div>Longest streak: <span className="font-mono text-[var(--text-primary)]">{metric.longestStreak} frames</span></div>
                        <div>Gaze stability: <span className="font-mono text-[var(--text-primary)]">{metric.gazeStability}</span></div>
                        {metric.error ? <div className="text-[var(--danger)]">{metric.error}</div> : null}
                      </div>
                    ) : null}
                    {key === "posture" ? (
                      <div className="space-y-2">
                        <div>Mean torso angle: <span className="font-mono text-[var(--text-primary)]">{metric.meanTorsoAngle}°</span></div>
                        <div>Shoulder tilt: <span className="font-mono text-[var(--text-primary)]">{metric.shoulderTilt}</span></div>
                        {metric.fallbackUsed ? (
                          <div className="rounded-xl border border-[rgba(245,158,11,0.2)] bg-[rgba(245,158,11,0.08)] px-3 py-2 text-[var(--warning)]">
                            Fallback posture framing used for {metric.fallbackFrames} frames.
                          </div>
                        ) : null}
                        {metric.error ? (
                          <div className="rounded-xl border border-[rgba(239,68,68,0.2)] bg-[rgba(239,68,68,0.08)] px-3 py-2 text-[var(--danger)]">
                            {metric.error}
                          </div>
                        ) : null}
                      </div>
                    ) : null}
                    {key === "animation" ? (
                      <div className="space-y-2">
                        <div>Expressiveness: <span className="font-mono text-[var(--text-primary)]">{metric.expressiveness}</span></div>
                        <div>Consistency: <span className="font-mono text-[var(--text-primary)]">{metric.consistency}</span></div>
                        <div>Stability: <span className="font-mono text-[var(--text-primary)]">{metric.stability}</span></div>
                        {metric.error ? <div className="text-[var(--danger)]">{metric.error}</div> : null}
                      </div>
                    ) : null}
                  </Accordion>
                </div>
              </Card>
            </motion.div>
          );
        })}
      </div>

      <Card className="p-6">
        <div className="mb-4">
          <p className="font-mono text-xs uppercase tracking-[0.25em] text-[var(--text-secondary)]">Section C</p>
          <h3 className="mt-2 text-2xl font-semibold tracking-tight">Performance Overview</h3>
        </div>
        {loading ? <Skeleton className="h-[360px] w-full" /> : <PerformanceRadar data={session} />}
      </Card>

      <Card className="space-y-6 p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.24em] text-[var(--accent-secondary)]">Resume Profile</p>
            <h3 className="mt-2 text-2xl font-semibold tracking-tight">
              {session?.resume.parsed ? session.resume.name || "Parsed Resume" : "No resume attached"}
            </h3>
            <p className="mt-2 text-[var(--text-secondary)]">
              {session?.resume.parsed
                ? session.resume.summary || "The resume was parsed successfully, but no summary section was detected."
                : "Attach a PDF resume during upload to extract skills, projects, and experience for future personalized question generation."}
            </p>
          </div>
          {session?.resume.uploaded ? (
            <div className="rounded-full border border-[var(--border-subtle)] px-3 py-1 font-mono text-xs text-[var(--text-secondary)]">
              {session.resume.sourceFilename || "resume.pdf"}
            </div>
          ) : null}
        </div>

        {session?.resume.parsed ? (
          <>
            {session.resume.reviewed ? (
              <div className="grid gap-5 xl:grid-cols-3">
                <Card className="p-5">
                  <div className="font-mono text-xs uppercase tracking-[0.22em] text-[var(--accent-secondary)]">Resume Score</div>
                  <div className="mt-3 font-mono text-4xl font-semibold">{session.resume.review.score}</div>
                  <div className="mt-2 text-sm text-[var(--text-secondary)]">{session.resume.review.label}</div>
                  <p className="mt-4 text-sm text-[var(--text-secondary)]">{session.resume.review.summary}</p>
                </Card>
                <Card className="p-5">
                  <h4 className="mb-4 text-lg font-semibold tracking-tight">Good Parts</h4>
                  <ResumeReviewList items={session.resume.review.strengths} color="var(--success)" />
                </Card>
                <Card className="p-5">
                  <h4 className="mb-4 text-lg font-semibold tracking-tight">Weak Parts</h4>
                  <ResumeReviewList items={session.resume.review.improvements} color="var(--warning)" />
                </Card>
              </div>
            ) : null}

            {session.resume.warnings.length ? (
              <div className="rounded-2xl border border-[rgba(245,158,11,0.2)] bg-[rgba(245,158,11,0.08)] p-4 text-sm text-[var(--warning)]">
                {session.resume.warnings.join(" ")}
              </div>
            ) : null}
            <div className="grid gap-5 lg:grid-cols-2">
              <Card className="p-5">
                <div className="text-sm text-[var(--text-secondary)]">Skills</div>
                <div className="mt-4 flex flex-wrap gap-2">
                  {session.resume.skills.length ? (
                    session.resume.skills.map((skill) => (
                      <span key={skill} className="rounded-full border border-[var(--border-subtle)] bg-[var(--bg-tertiary)] px-3 py-1 text-sm text-[var(--text-primary)]">
                        {skill}
                      </span>
                    ))
                  ) : (
                    <p className="text-[var(--text-secondary)]">No skills were extracted.</p>
                  )}
                </div>
              </Card>
              <Card className="p-5">
                <div className="text-sm text-[var(--text-secondary)]">Contact & Links</div>
                <div className="mt-4 space-y-2 text-sm text-[var(--text-secondary)]">
                  <div>Email: <span className="text-[var(--text-primary)]">{session.resume.emails[0] ?? "Not found"}</span></div>
                  <div>Phone: <span className="text-[var(--text-primary)]">{session.resume.phones[0] ?? "Not found"}</span></div>
                  <div>LinkedIn: <span className="text-[var(--text-primary)]">{session.resume.links.linkedin?.[0] ?? "Not found"}</span></div>
                  <div>GitHub: <span className="text-[var(--text-primary)]">{session.resume.links.github?.[0] ?? "Not found"}</span></div>
                </div>
              </Card>
            </div>
            <div className="grid gap-5 lg:grid-cols-3">
              <Card className="p-5">
                <div className="mb-3 text-sm text-[var(--text-secondary)]">Experience</div>
                <div className="space-y-3 text-sm text-[var(--text-secondary)]">
                  {(session.resume.experience.length ? session.resume.experience : ["No experience entries were extracted."]).slice(0, 3).map((item) => (
                    <p key={item}>{item}</p>
                  ))}
                </div>
              </Card>
              <Card className="p-5">
                <div className="mb-3 text-sm text-[var(--text-secondary)]">Projects</div>
                <div className="space-y-3 text-sm text-[var(--text-secondary)]">
                  {(session.resume.projects.length ? session.resume.projects : ["No projects were extracted."]).slice(0, 3).map((item) => (
                    <p key={item}>{item}</p>
                  ))}
                </div>
              </Card>
              <Card className="p-5">
                <div className="mb-3 text-sm text-[var(--text-secondary)]">Education</div>
                <div className="space-y-3 text-sm text-[var(--text-secondary)]">
                  {(session.resume.education.length ? session.resume.education : ["No education entries were extracted."]).slice(0, 3).map((item) => (
                    <p key={item}>{item}</p>
                  ))}
                </div>
              </Card>
            </div>
          </>
        ) : (
          <Card className="border-dashed p-5">
            <p className="text-[var(--text-secondary)]">Resume insights will appear here after you upload a resume with a new session.</p>
          </Card>
        )}
      </Card>

      <Card className="space-y-6 p-6">
        <div className="flex items-start justify-between gap-4">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.24em] text-[var(--accent-secondary)]">Generated Questions</p>
            <h3 className="mt-2 text-2xl font-semibold tracking-tight">
              {session?.resume.questions.roleFocus || "Question Set"}
            </h3>
            <p className="mt-2 text-[var(--text-secondary)]">
              {session?.resume.questions.openingPrompt || "Question generation is available once a parsed resume is present."}
            </p>
          </div>
        </div>

        {session?.resume.questions.error ? (
          <Card className="border-[rgba(239,68,68,0.2)] bg-[rgba(239,68,68,0.08)] p-4">
            <p className="text-sm text-[var(--danger)]">{session.resume.questions.error}</p>
          </Card>
        ) : (
          <QuestionCards questions={session?.resume.questions.items ?? []} />
        )}
      </Card>

      <div className="grid gap-5 lg:grid-cols-2">
        <CircularGauge
          color="var(--accent-primary)"
          note={session?.derived.confidenceNote}
          title="Confidence"
          value={session?.derived.confidence ?? 0}
        />
        <CircularGauge
          color={session?.derived.nervousness > 50 ? "var(--warning)" : "var(--success)"}
          note={session?.derived.nervousnessNote}
          title="Nervousness"
          value={session?.derived.nervousness ?? 0}
        />
      </div>

      <Card className="space-y-8 p-6 sm:p-8">
        <div className="rounded-2xl border-l-4 border-[var(--accent-primary)] bg-[rgba(99,102,241,0.08)] p-5">
          <p className="font-mono text-xs uppercase tracking-[0.24em] text-[var(--accent-primary)]">AI Summary</p>
          <blockquote className="mt-3 text-lg text-[var(--text-primary)]">{session?.feedback.summary}</blockquote>
        </div>

        <div className="grid gap-8 xl:grid-cols-3">
          <div>
            <h3 className="mb-4 text-xl font-semibold tracking-tight">Strengths</h3>
            <FeedbackList
              items={session?.feedback.strengths ?? []}
              emptyCopy="No strengths were generated because the feedback stage did not complete."
              color="var(--success)"
            />
          </div>

          <div>
            <h3 className="mb-4 text-xl font-semibold tracking-tight">Areas for Improvement</h3>
            <FeedbackList
              items={session?.feedback.improvements ?? []}
              emptyCopy="No improvement breakdown is available for this session yet."
              color="var(--warning)"
            />
          </div>

          <div>
            <h3 className="mb-4 text-xl font-semibold tracking-tight">Recommendations</h3>
            <FeedbackList
              items={session?.feedback.recommendations ?? []}
              emptyCopy="No recommendations were produced because the AI feedback stage did not finish successfully."
              numbered
            />
          </div>
        </div>

        {starCards.length ? (
          <div>
            <div className="mb-4 flex items-center gap-3">
              <Sparkles size={18} className="text-[var(--accent-primary)]" />
              <h3 className="text-xl font-semibold tracking-tight">STAR Analysis</h3>
            </div>
            <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
              {starCards.map(([label, value]) => (
                <Card key={label} className="p-5">
                  <div className="text-sm text-[var(--text-secondary)]">{label}</div>
                  <div className="mt-3 font-mono text-3xl font-semibold">{value}/5</div>
                </Card>
              ))}
            </div>
          </div>
        ) : (
          <Card className="border-dashed p-5">
            <p className="text-[var(--text-secondary)]">STAR analysis was not applicable for this session.</p>
          </Card>
        )}
      </Card>

      <Card className="p-6">
        <div className="mb-5">
          <h3 className="text-2xl font-semibold tracking-tight">Export</h3>
          <p className="text-sm text-[var(--text-secondary)]">Download either the raw JSON session artifact or a lightweight text report.</p>
        </div>
        <div className="flex flex-col gap-3 sm:flex-row">
          <Button onClick={exportJson} variant="secondary">
            Export JSON
          </Button>
          <Button onClick={exportReport} variant="ghost">
            Export Report
          </Button>
          <Link to="/sessions" className="sm:ml-auto">
            <Button variant="ghost">Back to Sessions</Button>
          </Link>
        </div>
      </Card>
    </div>
  );
}
