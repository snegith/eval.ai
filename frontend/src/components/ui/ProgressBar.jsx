import { motion } from "framer-motion";

export default function ProgressBar({ value, color = "var(--accent-primary)" }) {
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-[rgba(255,255,255,0.06)]">
      <motion.div
        className="h-full rounded-full"
        animate={{ width: `${Math.max(0, Math.min(100, value))}%` }}
        initial={{ width: 0 }}
        transition={{ duration: 0.45, ease: "easeOut" }}
        style={{
          background: color,
          boxShadow: `0 0 12px ${color}`,
        }}
      />
    </div>
  );
}
