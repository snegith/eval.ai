export function formatDate(isoString) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(new Date(isoString));
}

export function formatDuration(durationSeconds) {
  const minutes = Math.floor(durationSeconds / 60);
  const seconds = Math.floor(durationSeconds % 60);
  return `${minutes}m ${seconds}s`;
}

export function scoreColor(score) {
  if (score >= 75) return "var(--success)";
  if (score >= 60) return "var(--warning)";
  if (score >= 45) return "#f97316";
  return "var(--danger)";
}
