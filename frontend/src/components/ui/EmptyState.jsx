export default function EmptyState({ title, description }) {
  return (
    <div className="surface-card surface-elevated flex min-h-[280px] flex-col items-center justify-center p-10 text-center">
      <div className="mb-6 flex h-24 w-24 items-center justify-center rounded-[2rem] border border-[var(--border-subtle)] bg-[radial-gradient(circle,rgba(99,102,241,0.14),transparent_65%)]">
        <div className="h-10 w-10 rounded-full border border-[var(--border-active)] bg-[var(--bg-glass)]" />
      </div>
      <h3 className="text-2xl font-semibold tracking-tight">{title}</h3>
      <p className="mt-3 max-w-md text-[var(--text-secondary)]">{description}</p>
    </div>
  );
}
