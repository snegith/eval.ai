import { Check, Dot } from "lucide-react";
import { motion } from "framer-motion";

export default function Stepper({ steps }) {
  return (
    <div className="surface-card surface-elevated p-6">
      <div className="mb-5">
        <h3 className="text-lg font-semibold tracking-tight">Analysis Pipeline</h3>
        <p className="text-sm text-[var(--text-secondary)]">Each stage advances as the upload moves through the interview analysis pipeline.</p>
      </div>
      <div className="space-y-5">
        {steps.map((step, index) => {
          const isComplete = step.state === "complete";
          const isActive = step.state === "active";
          return (
            <div key={step.label} className="relative flex gap-4">
              {index !== steps.length - 1 ? (
                <div className="absolute left-[15px] top-10 h-[calc(100%+8px)] w-px bg-[rgba(255,255,255,0.08)]" />
              ) : null}
              <div
                className={`relative z-10 flex h-8 w-8 items-center justify-center rounded-full border ${
                  isComplete
                    ? "border-[var(--success)] bg-[rgba(16,185,129,0.14)] text-[var(--success)]"
                    : isActive
                      ? "border-[var(--accent-primary)] bg-[rgba(99,102,241,0.18)] text-[var(--accent-primary)]"
                      : "border-[var(--border-subtle)] bg-[var(--bg-tertiary)] text-[var(--text-muted)]"
                }`}
              >
                {isComplete ? (
                  <Check size={16} />
                ) : isActive ? (
                  <motion.div animate={{ scale: [1, 1.18, 1] }} transition={{ duration: 0.8, repeat: Number.POSITIVE_INFINITY }}>
                    <Dot size={22} />
                  </motion.div>
                ) : (
                  <span className="font-mono text-xs">{index + 1}</span>
                )}
              </div>
              <div className="pb-3">
                <p className="font-medium text-[var(--text-primary)]">{step.label}</p>
                <p className="text-sm text-[var(--text-secondary)]">{step.description}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
