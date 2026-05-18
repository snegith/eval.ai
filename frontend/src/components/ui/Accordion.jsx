import { AnimatePresence, motion } from "framer-motion";
import { ChevronDown } from "lucide-react";

export default function Accordion({ title, open, onToggle, children }) {
  return (
    <div className="rounded-2xl border border-[var(--border-subtle)] bg-[rgba(255,255,255,0.02)]">
      <button
        className="flex w-full items-center justify-between px-4 py-3 text-left"
        onClick={onToggle}
        type="button"
      >
        <span className="text-sm font-medium text-[var(--text-primary)]">{title}</span>
        <ChevronDown
          size={16}
          className={`transition-transform duration-300 ${open ? "rotate-180" : ""} text-[var(--text-secondary)]`}
        />
      </button>
      <AnimatePresence initial={false}>
        {open ? (
          <motion.div
            animate={{ height: "auto", opacity: 1 }}
            className="overflow-hidden"
            exit={{ height: 0, opacity: 0 }}
            initial={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
          >
            <div className="border-t border-[var(--border-subtle)] px-4 py-4 text-sm text-[var(--text-secondary)]">
              {children}
            </div>
          </motion.div>
        ) : null}
      </AnimatePresence>
    </div>
  );
}
