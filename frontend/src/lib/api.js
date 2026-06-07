const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE_URL}${path}`, options);
  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;
    try {
      const payload = await response.json();
      message = payload.detail ?? payload.message ?? message;
    } catch {
      // Ignore parsing failures and keep the fallback message.
    }
    throw new Error(message);
  }
  return response.json();
}

function collectStageErrors(value, messages = []) {
  if (!value || typeof value !== "object") {
    return messages;
  }

  if (typeof value.error === "string" && value.error.trim()) {
    messages.push(value.error);
  }

  for (const nested of Object.values(value)) {
    if (nested && typeof nested === "object") {
      collectStageErrors(nested, messages);
    }
  }

  return messages;
}

function extractStageError(payload) {
  const data = payload?.data;
  if (!data) {
    return null;
  }

  const directCandidates = [
    data.error,
    data.summary?.last_error,
    data.landmarks?.error,
    data.audio?.error,
    data.metrics?.error,
    data.feedback?.error,
    data.feedback?.feedback?.error,
    data.resume?.error,
    data.questions?.error,
  ];

  for (const message of directCandidates) {
    if (typeof message === "string" && message.trim()) {
      return message;
    }
  }

  const nestedMessages = collectStageErrors(data.metrics?.metrics ?? data.metrics, []);
  if (nestedMessages.length) {
    return nestedMessages[0];
  }

  return null;
}

function ensureStageSuccess(payload) {
  if (payload?.status && payload.status !== "ok") {
    throw new Error(extractStageError(payload) ?? "Pipeline stage failed.");
  }
  return payload;
}

export function listSessions() {
  return request("/api/sessions");
}

export function createSession() {
  return request("/api/sessions", { method: "POST" });
}

export function getSessionResults(sessionId) {
  return request(`/api/sessions/${sessionId}/results`);
}

export function uploadResume(sessionId, file) {
  const formData = new FormData();
  formData.append("file", file);
  return request(`/api/sessions/${sessionId}/resume`, {
    method: "POST",
    body: formData,
  }).then(ensureStageSuccess);
}

export function parseResume(sessionId) {
  return request(`/api/sessions/${sessionId}/resume/parse`, {
    method: "POST",
  }).then(ensureStageSuccess);
}

export function generateQuestions(sessionId) {
  return request(`/api/sessions/${sessionId}/questions/generate`, {
    method: "POST",
  }).then(ensureStageSuccess);
}

export function uploadVideo(sessionId, file) {
  const formData = new FormData();
  formData.append("file", file);
  return request(`/api/sessions/${sessionId}/video`, {
    method: "POST",
    body: formData,
  }).then(ensureStageSuccess);
}

export function processSession(sessionId, options = {}) {
  return request(`/api/sessions/${sessionId}/process`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      run_audio: options.runAudio ?? true,
      model_name: options.modelName ?? "base",
      pause_threshold: options.pauseThreshold ?? 2,
      generate_feedback: options.generateFeedback ?? true,
      parse_resume: options.parseResume ?? false,
      generate_questions: options.generateQuestions ?? false,
    }),
  }).then(ensureStageSuccess);
}

export function processUpload(file, options = {}) {
  const formData = new FormData();
  formData.append("file", file);
  if (options.resumeFile) {
    formData.append("resume", options.resumeFile);
  }
  formData.append("run_audio", String(options.runAudio ?? true));
  formData.append("model_name", options.modelName ?? "base");
  formData.append("pause_threshold", String(options.pauseThreshold ?? 2.0));
  formData.append("generate_feedback", String(options.generateFeedback ?? true));
  formData.append("parse_resume", String(options.parseResume ?? true));
  formData.append("generate_questions", String(options.generateQuestions ?? true));

  return request("/api/sessions/process-upload", {
    method: "POST",
    body: formData,
  }).then(ensureStageSuccess);
}

export { API_BASE_URL };
