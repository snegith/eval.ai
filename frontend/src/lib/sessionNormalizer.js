function round(value, decimals = 0) {
  if (!Number.isFinite(Number(value))) return 0;
  const factor = 10 ** decimals;
  return Math.round(Number(value) * factor) / factor;
}

export function scoreGrade(score) {
  if (score >= 80) return "Excellent";
  if (score >= 65) return "Good";
  if (score >= 50) return "Fair";
  return "Needs Improvement";
}

function buildFeedbackSummary(feedback, metadata) {
  if (feedback?.summary) return feedback.summary;
  if (feedback?.error) return feedback.error;
  if (metadata?.last_error) return metadata.last_error;
  return "Analysis is still in progress or completed with partial results. Run the remaining pipeline stages to unlock full AI feedback.";
}

function buildFramingQuality(posture, metadata) {
  if (posture?.error) {
    return {
      hasWarnings: true,
      message: posture.debug_info?.tip ?? posture.error,
    };
  }

  if (posture?.fallback_used) {
    return {
      hasWarnings: true,
      message: `Posture was computed with fallback framing for ${posture.fallback_frames ?? 0} frames. Keeping more of the upper torso visible will improve reliability.`,
    };
  }

  if (metadata?.last_error?.toLowerCase().includes("frame")) {
    return {
      hasWarnings: true,
      message: metadata.last_error,
    };
  }

  return { hasWarnings: false, message: "" };
}

function normalizeStarAnalysis(feedback) {
  const star = feedback?.star_analysis;
  if (!star) {
    return {
      applicable: false,
      situation: null,
      task: null,
      action: null,
      result: null,
      feedback: "",
    };
  }

  return {
    applicable: Boolean(star.applicable),
    situation: star.situation_score,
    task: star.task_score,
    action: star.action_score,
    result: star.result_score,
    feedback: star.feedback ?? "",
  };
}

export function normalizeSessionBundle(bundle) {
  const metadata = bundle?.metadata ?? {};
  const eye = bundle?.eye_contact ?? {};
  const posture = bundle?.posture ?? {};
  const animation = bundle?.animation ?? {};
  const derived = bundle?.derived ?? {};
  const feedback = bundle?.feedback ?? {};
  const transcript = bundle?.transcript ?? {};
  const resumeText = bundle?.resume_text ?? {};
  const resumeProfile = bundle?.resume_profile ?? {};
  const resumeReview = bundle?.resume_review ?? {};
  const generatedQuestions = bundle?.generated_questions ?? {};

  const eyeScore = round(eye.eye_contact_score ?? eye.eye_contact_percentage ?? 0);
  const postureScore = round(posture.posture_score ?? posture.posture_percentage ?? 0);
  const animationScore = round(animation.expressiveness_score ?? 0);
  const metricScores = [eyeScore, postureScore, animationScore].filter((score) => Number.isFinite(Number(score)));
  const fallbackOverall = metricScores.length
    ? round(metricScores.reduce((sum, score) => sum + Number(score), 0) / metricScores.length)
    : 0;
  const overallScore = round(feedback.overall_score ?? fallbackOverall);

  const confidence = round(derived.confidence_score ?? 0);
  const nervousness = round(derived.nervousness_score ?? 0);
  const sourceName = metadata.video_filename ?? "video.mp4";

  return {
    id: bundle.session_id,
    createdAt: metadata.created_at ?? new Date().toISOString(),
    updatedAt: metadata.updated_at ?? metadata.created_at ?? new Date().toISOString(),
    durationSeconds: round(
      metadata.duration_seconds ?? transcript.duration_sec ?? bundle?.audio_metrics?.duration_sec ?? 0,
    ),
    status: metadata.status ?? "unknown",
    source: {
      name: sourceName,
      size: 0,
      type: sourceName.includes(".") ? sourceName.split(".").pop() : "mp4",
    },
    overallScore,
    grade: scoreGrade(overallScore),
    eyeContact: {
      score: eyeScore,
      grade: eye.grade ?? scoreGrade(eyeScore),
      longestStreak: eye.longest_streak ?? 0,
      gazeStability: round(eye.gaze_stability ?? 0, 3),
      error: eye.error ?? "",
    },
    posture: {
      score: postureScore,
      grade: posture.grade ?? (posture.error ? "Unavailable" : scoreGrade(postureScore)),
      meanTorsoAngle: round(posture.mean_torso_angle_deg ?? 0, 1),
      shoulderTilt: round(posture.mean_shoulder_tilt ?? 0, 2),
      fallbackUsed: Boolean(posture.fallback_used),
      fallbackFrames: posture.fallback_frames ?? posture.debug_info?.fallback_frames ?? 0,
      error: posture.error ?? "",
    },
    animation: {
      score: animationScore,
      grade: animation.grade ?? scoreGrade(animationScore),
      expressiveness: round(animation.expressiveness_score ?? 0),
      consistency: round(animation.consistency_score ?? 0),
      stability: round(animation.stability_score ?? 0),
      peakFrequency: round(animation.expression_dynamics?.peak_frequency_per_sec ?? 0, 2),
      error: animation.error ?? "",
    },
    derived: {
      confidence,
      nervousness,
      confidenceNote: "Confidence is mathematically derived from eye contact and posture.",
      nervousnessNote: "Nervousness is mathematically derived from animation consistency and stability.",
      error: derived.error ?? "",
    },
    feedback: {
      summary: buildFeedbackSummary(feedback, metadata),
      strengths: Array.isArray(feedback.strengths) ? feedback.strengths : [],
      improvements: Array.isArray(feedback.improvements) ? feedback.improvements : [],
      recommendations: Array.isArray(feedback.recommendations) ? feedback.recommendations : [],
      star: normalizeStarAnalysis(feedback),
      error: feedback.error ?? "",
    },
    resume: {
      uploaded: Boolean(metadata.artifacts?.resume),
      parsed: Boolean(metadata.artifacts?.resume_profile),
      reviewed: Boolean(metadata.artifacts?.resume_review),
      sourceFilename: resumeText.source_filename ?? metadata.resume_filename ?? "",
      pageCount: resumeText.page_count ?? 0,
      summary: resumeProfile.summary ?? "",
      name: resumeProfile.name ?? "",
      emails: Array.isArray(resumeProfile.emails) ? resumeProfile.emails : [],
      phones: Array.isArray(resumeProfile.phones) ? resumeProfile.phones : [],
      skills: Array.isArray(resumeProfile.skills) ? resumeProfile.skills : [],
      projects: Array.isArray(resumeProfile.projects) ? resumeProfile.projects : [],
      experience: Array.isArray(resumeProfile.experience) ? resumeProfile.experience : [],
      education: Array.isArray(resumeProfile.education) ? resumeProfile.education : [],
      certifications: Array.isArray(resumeProfile.certifications) ? resumeProfile.certifications : [],
      warnings: Array.isArray(resumeProfile.parsing_warnings) ? resumeProfile.parsing_warnings : [],
      links: resumeProfile.links ?? { linkedin: [], github: [], portfolio: [] },
      review: {
        score: round(resumeReview.score ?? 0),
        label: resumeReview.label ?? "Unreviewed",
        strengths: Array.isArray(resumeReview.strengths) ? resumeReview.strengths : [],
        improvements: Array.isArray(resumeReview.improvements) ? resumeReview.improvements : [],
        recommendations: Array.isArray(resumeReview.recommendations) ? resumeReview.recommendations : [],
        summary: resumeReview.summary ?? "",
        error: resumeReview.error ?? "",
      },
      questions: {
        generated: Boolean(metadata.artifacts?.questions),
        roleFocus: generatedQuestions.role_focus ?? "",
        openingPrompt: generatedQuestions.opening_prompt ?? "",
        items: Array.isArray(generatedQuestions.questions) ? generatedQuestions.questions : [],
        error: generatedQuestions.error ?? "",
        provider: generatedQuestions._metadata?.provider ?? "",
        fallbackReason: generatedQuestions._metadata?.fallback_reason ?? "",
      },
    },
    framingQuality: buildFramingQuality(posture, metadata),
    artifacts: metadata.artifacts ?? {},
    raw: bundle,
  };
}
