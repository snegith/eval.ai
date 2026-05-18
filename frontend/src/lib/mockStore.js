import { defaultSessions } from "../data/mockData";

const STORAGE_KEY = "eval-ai-sessions-v1";

export function loadSessions() {
  if (typeof window === "undefined") return defaultSessions;
  const raw = window.localStorage.getItem(STORAGE_KEY);
  if (!raw) {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(defaultSessions));
    return defaultSessions;
  }
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) && parsed.length ? parsed : defaultSessions;
  } catch {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(defaultSessions));
    return defaultSessions;
  }
}

export function persistSessions(sessions) {
  if (typeof window !== "undefined") {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
  }
}

function scoreGrade(score) {
  if (score >= 80) return "Excellent";
  if (score >= 65) return "Good";
  if (score >= 50) return "Fair";
  return "Needs Improvement";
}

function randomBetween(min, max) {
  return Math.round(min + Math.random() * (max - min));
}

export function buildGeneratedSession(file) {
  const overallScore = randomBetween(58, 89);
  const eyeScore = Math.max(32, Math.min(94, overallScore + randomBetween(-8, 6)));
  const postureScore = Math.max(30, Math.min(92, overallScore + randomBetween(-10, 4)));
  const animationScore = Math.max(34, Math.min(90, overallScore + randomBetween(-7, 8)));
  const consistency = Math.max(40, Math.min(92, animationScore + randomBetween(-4, 11)));
  const stability = Math.max(45, Math.min(93, animationScore + randomBetween(0, 14)));
  const confidence = Math.min(100, Math.round((eyeScore * 0.6 + postureScore * 0.4) * 0.95));
  const nervousness = Math.max(12, Math.min(82, 100 - Math.round(consistency * 0.6 + stability * 0.4)));
  const includeWarning = postureScore < 60 || Math.random() > 0.65;

  return {
    id: `session_${Math.random().toString(16).slice(2, 10)}`,
    createdAt: new Date().toISOString(),
    durationSeconds: randomBetween(180, 360),
    source: { name: file.name, size: file.size, type: file.type },
    overallScore,
    grade: scoreGrade(overallScore),
    eyeContact: {
      score: eyeScore,
      grade: scoreGrade(eyeScore),
      longestStreak: randomBetween(18, 72),
      gazeStability: Number((0.55 + Math.random() * 0.35).toFixed(2)),
    },
    posture: {
      score: postureScore,
      grade: scoreGrade(postureScore),
      meanTorsoAngle: Number((4 + Math.random() * 11).toFixed(1)),
      shoulderTilt: Number((0.05 + Math.random() * 0.14).toFixed(2)),
      fallbackUsed: includeWarning,
      fallbackFrames: includeWarning ? randomBetween(22, 96) : 0,
    },
    animation: {
      score: animationScore,
      grade: scoreGrade(animationScore),
      expressiveness: animationScore,
      consistency,
      stability,
    },
    derived: {
      confidence,
      nervousness,
      confidenceNote: "Confidence is mathematically derived from eye contact and posture.",
      nervousnessNote: "Nervousness is inferred from animation consistency and stability.",
    },
    feedback: {
      summary:
        "This simulated session shows a balanced delivery profile with a few high-leverage opportunities to improve executive presence and answer impact.",
      strengths: [
        "Maintained a credible baseline of engagement throughout the interview.",
        "Delivered answers with enough structure to stay understandable and relevant.",
        "Showed visible momentum in the stronger examples, especially when describing decisions and outcomes.",
      ],
      improvements: [
        "A bit more consistency in eye contact would make the delivery feel more assured.",
        "Posture dipped during longer moments, which softened perceived confidence.",
        "Stronger emotional emphasis on the outcome of examples would improve memorability.",
      ],
      recommendations: [
        "Practice a camera-focused mock response and review gaze drift at the 30-second mark.",
        "Anchor your shoulders before answering to keep posture consistent across the full response.",
        "Finish each example with a short, quantifiable result statement.",
      ],
      star: {
        applicable: true,
        situation: randomBetween(3, 5),
        task: randomBetween(3, 5),
        action: randomBetween(3, 5),
        result: randomBetween(2, 5),
      },
    },
    framingQuality: {
      hasWarnings: includeWarning,
      message: includeWarning
        ? "Camera framing reduced posture confidence in part of the session. Keep both shoulders and more of the upper torso visible."
        : "",
    },
  };
}
