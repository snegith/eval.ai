import { motion } from "framer-motion";
import { CheckCircle2, FileText, FileVideo, MessageSquareQuote, UploadCloud } from "lucide-react";
import { useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import EmptyState from "../components/ui/EmptyState";
import Stepper from "../components/ui/Stepper";
import { useSessionStore } from "../hooks/useSessionStore";
import {
  createSession,
  generateQuestions,
  getSessionResults,
  parseResume,
  processSession,
  uploadResume,
  uploadVideo,
} from "../lib/api";
import { normalizeSessionBundle } from "../lib/sessionNormalizer";

const acceptedTypes = [".mp4", ".mov", ".webm"];
const acceptedResumeTypes = [".pdf", ".txt", ".md"];
const stepTemplate = [
  {
    label: "Uploading video",
    description: "Creating the session artifact and storing the source recording.",
  },
  {
    label: "Extracting landmarks",
    description: "Running FaceMesh and Pose analysis across interview frames.",
  },
  {
    label: "Analysing behaviour",
    description: "Scoring eye contact, posture, and facial animation metrics.",
  },
  {
    label: "Generating feedback",
    description: "Synthesizing behavioral metrics into AI coaching feedback.",
  },
];

function ReviewList({ items, color, emptyCopy }) {
  if (!items.length) {
    return <p className="text-sm text-[var(--text-secondary)]">{emptyCopy}</p>;
  }

  return (
    <div className="space-y-3">
      {items.map((item) => (
        <div key={item} className="flex gap-3">
          <span className="mt-2 h-2.5 w-2.5 rounded-full" style={{ background: color }} />
          <p className="text-sm text-[var(--text-secondary)]">{item}</p>
        </div>
      ))}
    </div>
  );
}

function QuestionsGrid({ questions }) {
  if (!questions.length) {
    return <p className="text-sm text-[var(--text-secondary)]">No questions are available yet.</p>;
  }

  return (
    <div className="grid gap-4 xl:grid-cols-2">
      {questions.map((item, index) => (
        <Card key={`${item.question}-${index}`} className="p-5">
          <div className="mb-3 flex items-center justify-between gap-3">
            <span className="rounded-full border border-[var(--border-subtle)] bg-[var(--bg-tertiary)] px-3 py-1 text-xs uppercase tracking-[0.2em] text-[var(--text-secondary)]">
              {(item.category ?? "question").replace("_", " ")}
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

export default function UploadPage() {
  const inputRef = useRef(null);
  const resumeInputRef = useRef(null);
  const navigate = useNavigate();
  const { error, mode, refreshSessions } = useSessionStore();
  const [file, setFile] = useState(null);
  const [resumeFile, setResumeFile] = useState(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isResumeDragging, setIsResumeDragging] = useState(false);
  const [currentStep, setCurrentStep] = useState(-1);
  const [processing, setProcessing] = useState(false);
  const [resumeProcessing, setResumeProcessing] = useState(false);
  const [questionProcessing, setQuestionProcessing] = useState(false);
  const [actionError, setActionError] = useState("");
  const [draftSessionId, setDraftSessionId] = useState("");
  const [resumeSession, setResumeSession] = useState(null);

  const steps = useMemo(
    () =>
      stepTemplate.map((step, index) => ({
        ...step,
        state: currentStep > index ? "complete" : currentStep === index ? "active" : "pending",
      })),
    [currentStep],
  );

  const handleFile = (selectedFile) => {
    if (selectedFile) setFile(selectedFile);
  };

  const handleResumeFile = (selectedFile) => {
    if (selectedFile) setResumeFile(selectedFile);
  };

  const loadSessionBundle = async (sessionId) => {
    const bundle = await getSessionResults(sessionId);
    const normalized = normalizeSessionBundle(bundle);
    setResumeSession(normalized);
    await refreshSessions();
    return normalized;
  };

  const startResumeStage = async () => {
    if (!resumeFile || resumeProcessing) return;

    setResumeProcessing(true);
    setActionError("");

    try {
      const created = draftSessionId ? { session_id: draftSessionId } : await createSession();
      const sessionId = created.session_id;
      setDraftSessionId(sessionId);
      await uploadResume(sessionId, resumeFile);
      await parseResume(sessionId);
      await loadSessionBundle(sessionId);
    } catch (resumeError) {
      setActionError(resumeError.message);
    } finally {
      setResumeProcessing(false);
    }
  };

  const startQuestionStage = async () => {
    if (!draftSessionId || questionProcessing) return;

    setQuestionProcessing(true);
    setActionError("");

    try {
      await generateQuestions(draftSessionId);
      await loadSessionBundle(draftSessionId);
    } catch (questionError) {
      setActionError(questionError.message);
    } finally {
      setQuestionProcessing(false);
    }
  };

  const startInterviewAnalysis = async () => {
    if (!file || processing) return;

    setProcessing(true);
    setActionError("");
    setCurrentStep(0);

    const intervalId = window.setInterval(() => {
      setCurrentStep((previous) => (previous < stepTemplate.length - 1 ? previous + 1 : previous));
    }, 900);

    try {
      const created = draftSessionId ? { session_id: draftSessionId } : await createSession();
      const sessionId = created.session_id;
      setDraftSessionId(sessionId);
      await uploadVideo(sessionId, file);
      await processSession(sessionId, { parseResume: false, generateQuestions: false });
      window.clearInterval(intervalId);
      setCurrentStep(stepTemplate.length);
      await refreshSessions();
      window.setTimeout(() => navigate(`/results/${sessionId}`), 450);
    } catch (processingError) {
      window.clearInterval(intervalId);
      setCurrentStep(-1);
      setActionError(processingError.message);
    } finally {
      setProcessing(false);
    }
  };

  const resumeParsed = Boolean(resumeSession?.resume.parsed);
  const questionsReady = Boolean(resumeSession?.resume.questions.generated);
  const reviewAvailable = Boolean(resumeSession?.resume.reviewed && !resumeSession?.resume.review.error);

  return (
    <div className="space-y-8">
      <div>
        <p className="font-mono text-xs uppercase tracking-[0.28em] text-[var(--accent-primary)]">Session Creation</p>
        <h1 className="mt-3 text-4xl font-semibold tracking-tight">New Session</h1>
        <p className="mt-3 max-w-3xl text-[var(--text-secondary)]">
          Resume parsing and question generation are available here, but you can also jump straight to interview evaluation whenever you need to test the video pipeline.
        </p>
      </div>

      {mode === "mock" ? (
        <Card className="border-[rgba(245,158,11,0.24)] bg-[rgba(245,158,11,0.08)] p-5">
          <p className="text-sm text-[var(--warning)]">
            The FastAPI backend is currently unreachable, so the resume-to-questions flow needs the API running before it can work end to end.
          </p>
          {error ? <p className="mt-2 text-xs text-[var(--text-secondary)]">{error}</p> : null}
        </Card>
      ) : null}

      <Card className="p-6 sm:p-8">
        <div className="mb-4 flex items-center justify-between gap-4">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.24em] text-[var(--accent-secondary)]">Step 1</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight">Upload and parse the resume</h2>
            <p className="mt-2 text-[var(--text-secondary)]">
              This gives the system the structured profile it needs to generate relevant interview questions.
            </p>
          </div>
          {resumeParsed ? (
            <div className="inline-flex items-center gap-2 rounded-full border border-[rgba(16,185,129,0.2)] bg-[rgba(16,185,129,0.1)] px-3 py-1 text-sm text-[var(--success)]">
              <CheckCircle2 size={16} />
              Resume Parsed
            </div>
          ) : null}
        </div>

        <div
          className={`flex min-h-[240px] cursor-pointer flex-col items-center justify-center rounded-[24px] border-2 border-dashed px-6 text-center transition-all duration-300 ${
            isResumeDragging
              ? "border-[var(--accent-secondary)] bg-[rgba(139,92,246,0.09)]"
              : "border-[var(--border-subtle)] bg-[rgba(255,255,255,0.02)]"
          }`}
          onClick={() => resumeInputRef.current?.click()}
          onDragEnter={(event) => {
            event.preventDefault();
            setIsResumeDragging(true);
          }}
          onDragLeave={(event) => {
            event.preventDefault();
            setIsResumeDragging(false);
          }}
          onDragOver={(event) => event.preventDefault()}
          onDrop={(event) => {
            event.preventDefault();
            setIsResumeDragging(false);
            handleResumeFile(event.dataTransfer.files?.[0]);
          }}
          role="button"
          tabIndex={0}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              resumeInputRef.current?.click();
            }
          }}
        >
          <div className="mb-5 flex h-16 w-16 items-center justify-center rounded-[1.6rem] border border-[rgba(139,92,246,0.35)] bg-[radial-gradient(circle,rgba(139,92,246,0.18),transparent_65%)]">
            <FileText size={26} className="text-[var(--accent-secondary)]" />
          </div>
          <h3 className="text-xl font-semibold tracking-tight">Drop your resume here</h3>
          <p className="mt-3 max-w-lg text-[var(--text-secondary)]">
            Accepted formats: {acceptedResumeTypes.join(", ")}.
          </p>

          {resumeFile ? (
            <div className="mt-6 flex items-center gap-4 rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-tertiary)] px-5 py-4">
              <FileText size={18} className="text-[var(--accent-secondary)]" />
              <div className="text-left">
                <div className="font-medium text-[var(--text-primary)]">{resumeFile.name}</div>
                <div className="font-mono text-xs text-[var(--text-secondary)]">
                  {(resumeFile.size / 1024).toFixed(1)} KB
                </div>
              </div>
            </div>
          ) : null}

          <input
            ref={resumeInputRef}
            accept={acceptedResumeTypes.join(",")}
            className="hidden"
            onChange={(event) => handleResumeFile(event.target.files?.[0])}
            type="file"
          />
        </div>

        <div className="mt-6 flex justify-end">
          <Button disabled={!resumeFile || mode === "mock"} loading={resumeProcessing} onClick={startResumeStage}>
            Parse Resume
          </Button>
        </div>
      </Card>

      {resumeParsed ? (
        <Card className="space-y-6 p-6 sm:p-8">
          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
            <div>
              <p className="font-mono text-xs uppercase tracking-[0.24em] text-[var(--accent-secondary)]">Resume Snapshot</p>
              <h2 className="mt-2 text-2xl font-semibold tracking-tight">
                {resumeSession.resume.name || "Parsed Resume"}
              </h2>
              <p className="mt-2 max-w-3xl text-[var(--text-secondary)]">
                {resumeSession.resume.summary || "The resume has been parsed and is ready for question generation."}
              </p>
            </div>
            {reviewAvailable ? (
              <div className="rounded-3xl border border-[var(--border-subtle)] bg-[var(--bg-tertiary)] px-5 py-4 text-center">
                <div className="font-mono text-xs uppercase tracking-[0.24em] text-[var(--text-secondary)]">Resume Score</div>
                <div className="mt-2 font-mono text-4xl font-semibold">{resumeSession.resume.review.score}</div>
                <div className="mt-1 text-sm text-[var(--accent-secondary)]">{resumeSession.resume.review.label}</div>
              </div>
            ) : null}
          </div>

          {resumeSession.resume.review.error ? (
            <Card className="border-[rgba(245,158,11,0.24)] bg-[rgba(245,158,11,0.08)] p-4">
              <p className="text-sm text-[var(--warning)]">
                Resume review is currently unstable, so the flow is continuing with parsed resume data only.
              </p>
              <p className="mt-2 text-xs text-[var(--text-secondary)]">{resumeSession.resume.review.error}</p>
            </Card>
          ) : null}

          {reviewAvailable ? (
            <div className="grid gap-5 xl:grid-cols-3">
              <Card className="p-5">
                <h3 className="mb-4 text-lg font-semibold tracking-tight">Good Parts</h3>
                <ReviewList items={resumeSession.resume.review.strengths} color="var(--success)" emptyCopy="No strengths available." />
              </Card>
              <Card className="p-5">
                <h3 className="mb-4 text-lg font-semibold tracking-tight">Weak Parts</h3>
                <ReviewList items={resumeSession.resume.review.improvements} color="var(--warning)" emptyCopy="No weak points available." />
              </Card>
              <Card className="p-5">
                <h3 className="mb-4 text-lg font-semibold tracking-tight">How To Improve</h3>
                <ReviewList items={resumeSession.resume.review.recommendations} color="var(--accent-primary)" emptyCopy="No recommendations available." />
              </Card>
            </div>
          ) : null}
        </Card>
      ) : null}

      <Card className={`p-6 sm:p-8 ${resumeParsed ? "" : "opacity-70"}`}>
        <div className="mb-4 flex items-center justify-between gap-4">
          <div>
            <p className="font-mono text-xs uppercase tracking-[0.24em] text-[var(--accent-secondary)]">Step 2</p>
            <h2 className="mt-2 text-2xl font-semibold tracking-tight">Generate resume-based interview questions</h2>
            <p className="mt-2 text-[var(--text-secondary)]">
              Use the parsed resume to create tailored technical, project, and behavioral prompts before the interview starts. This step is optional if you only want to test evaluation.
            </p>
          </div>
          {questionsReady ? (
            <div className="inline-flex items-center gap-2 rounded-full border border-[rgba(16,185,129,0.2)] bg-[rgba(16,185,129,0.1)] px-3 py-1 text-sm text-[var(--success)]">
              <CheckCircle2 size={16} />
              Questions Ready
            </div>
          ) : null}
        </div>

        {questionsReady ? (
          <div className="space-y-5">
            {resumeSession?.resume.questions.provider === "fallback" ? (
              <Card className="border-[rgba(245,158,11,0.24)] bg-[rgba(245,158,11,0.08)] p-4">
                <p className="text-sm text-[var(--warning)]">
                  The AI provider hit a limit, so these questions were generated from the parsed resume using a local fallback.
                </p>
              </Card>
            ) : null}
            <Card className="p-5">
              <div className="mb-3 flex items-center gap-3">
                <MessageSquareQuote size={18} className="text-[var(--accent-primary)]" />
                <h3 className="text-lg font-semibold tracking-tight">{resumeSession.resume.questions.roleFocus || "Interview Focus"}</h3>
              </div>
              <p className="text-[var(--text-secondary)]">
                {resumeSession.resume.questions.openingPrompt || "Walk me through the strongest parts of your resume and the work you are most proud of."}
              </p>
            </Card>
            <QuestionsGrid questions={resumeSession.resume.questions.items} />
          </div>
        ) : (
          <Card className="border-dashed p-5">
            <p className="text-[var(--text-secondary)]">
              Generate questions after resume parsing to preview the interview flow the candidate is likely to face.
            </p>
          </Card>
        )}

        {resumeSession?.resume.questions.error ? (
          <Card className="mt-5 border-[rgba(239,68,68,0.2)] bg-[rgba(239,68,68,0.08)] p-4">
            <p className="text-sm text-[var(--danger)]">{resumeSession.resume.questions.error}</p>
          </Card>
        ) : null}

        <div className="mt-6 flex justify-end">
          <Button disabled={!resumeParsed || questionsReady || mode === "mock"} loading={questionProcessing} onClick={startQuestionStage}>
            Generate Questions
          </Button>
        </div>
      </Card>

      <Card className="p-6 sm:p-8">
        <div className="mb-4">
          <p className="font-mono text-xs uppercase tracking-[0.24em] text-[var(--accent-primary)]">Step 3</p>
          <h2 className="mt-2 text-2xl font-semibold tracking-tight">Continue to interview evaluation</h2>
          <p className="mt-2 text-[var(--text-secondary)]">
            Upload the interview recording whenever you are ready. Resume parsing and question generation can happen before this step, but they are not required for testing the evaluator.
          </p>
        </div>

        <div
          className={`flex min-h-[320px] cursor-pointer flex-col items-center justify-center rounded-[28px] border-2 border-dashed px-6 text-center transition-all duration-300 ${
            isDragging
              ? "border-[var(--accent-primary)] bg-[rgba(99,102,241,0.09)]"
              : "border-[var(--border-subtle)] bg-[rgba(255,255,255,0.02)]"
          }`}
          onClick={() => inputRef.current?.click()}
          onDragEnter={(event) => {
            event.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={(event) => {
            event.preventDefault();
            setIsDragging(false);
          }}
          onDragOver={(event) => event.preventDefault()}
          onDrop={(event) => {
            event.preventDefault();
            setIsDragging(false);
            handleFile(event.dataTransfer.files?.[0]);
          }}
          role="button"
          tabIndex={0}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              inputRef.current?.click();
            }
          }}
        >
          <div className="mb-5 flex h-20 w-20 items-center justify-center rounded-[2rem] border border-[var(--border-active)] bg-[radial-gradient(circle,rgba(99,102,241,0.18),transparent_65%)]">
            <UploadCloud size={30} className="text-[var(--accent-primary)]" />
          </div>
          <h2 className="text-2xl font-semibold tracking-tight">Drop your interview video here</h2>
          <p className="mt-3 max-w-lg text-[var(--text-secondary)]">
            Click to browse or drag-and-drop an interview recording. Accepted formats: {acceptedTypes.join(", ")}.
          </p>

          {file ? (
            <div className="mt-8 flex items-center gap-4 rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-tertiary)] px-5 py-4">
              <FileVideo size={18} className="text-[var(--accent-primary)]" />
              <div className="text-left">
                <div className="font-medium text-[var(--text-primary)]">{file.name}</div>
                <div className="font-mono text-xs text-[var(--text-secondary)]">
                  {(file.size / (1024 * 1024)).toFixed(2)} MB
                </div>
              </div>
            </div>
          ) : null}

          <input
            ref={inputRef}
            accept={acceptedTypes.join(",")}
            className="hidden"
            onChange={(event) => handleFile(event.target.files?.[0])}
            type="file"
          />
        </div>

        {!resumeParsed ? (
          <p className="mt-4 text-sm text-[var(--text-secondary)]">
            No resume attached yet. That is fine if you only want to test the interview evaluation flow.
          </p>
        ) : null}
        {resumeParsed && !questionsReady ? (
          <p className="mt-4 text-sm text-[var(--text-secondary)]">
            Resume parsing is complete. You can generate questions first, or continue directly into interview evaluation.
          </p>
        ) : null}

        <div className="mt-6 flex justify-end">
          <Button disabled={!file || mode === "mock"} loading={processing} onClick={startInterviewAnalysis}>
            Start Interview Analysis
          </Button>
        </div>
      </Card>

      {actionError ? (
        <EmptyState title="This step could not be completed" description={actionError} />
      ) : null}

      {processing || currentStep >= 0 ? (
        <motion.div animate={{ opacity: 1, y: 0 }} initial={{ opacity: 0, y: 18 }} transition={{ duration: 0.35 }}>
          <Stepper steps={steps} />
        </motion.div>
      ) : null}
    </div>
  );
}
