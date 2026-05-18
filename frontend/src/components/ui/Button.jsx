export default function Button({
  children,
  variant = "primary",
  className = "",
  loading = false,
  disabled = false,
  ...props
}) {
  const styles = {
    primary:
      "premium-button bg-[var(--accent-primary)] text-[var(--text-primary)] hover:bg-[var(--accent-secondary)]",
    secondary:
      "premium-button border border-[var(--border-subtle)] bg-[var(--bg-tertiary)] text-[var(--text-primary)] hover:border-[var(--border-active)]",
    ghost:
      "premium-button border border-[var(--border-subtle)] bg-transparent text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-active)]",
  };

  return (
    <button
      className={`${styles[variant]} ${className} ${disabled || loading ? "cursor-not-allowed opacity-60" : ""}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? (
        <span className="inline-flex items-center gap-2">
          <span>Processing</span>
          <span className="dot-wave inline-flex gap-1">
            <span className="h-1.5 w-1.5 rounded-full bg-current" />
            <span className="h-1.5 w-1.5 rounded-full bg-current" />
            <span className="h-1.5 w-1.5 rounded-full bg-current" />
          </span>
        </span>
      ) : (
        children
      )}
    </button>
  );
}
