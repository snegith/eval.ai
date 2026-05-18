import { Menu, Sparkles } from "lucide-react";
import { useState } from "react";
import { NavLink } from "react-router-dom";

const links = [
  { label: "Dashboard", to: "/" },
  { label: "Sessions", to: "/sessions" },
  { label: "Upload", to: "/upload" },
  { label: "Results", to: "/sessions" },
];

function navClass({ isActive }) {
  return [
    "rounded-full px-3 py-2 text-sm transition-colors duration-300",
    isActive ? "bg-[var(--bg-tertiary)] text-[var(--text-primary)]" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]",
  ].join(" ");
}

export default function Navbar() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-40 border-b border-[var(--border-subtle)] bg-[rgba(10,10,15,0.75)] backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-4 sm:px-6 lg:px-8">
        <NavLink to="/" className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-glass)]">
            <Sparkles size={18} className="text-[var(--accent-primary)]" />
          </div>
          <div>
            <div className="font-mono text-sm uppercase tracking-[0.28em] text-[var(--text-secondary)]">EVAL.AI</div>
            <div className="text-sm font-medium text-[var(--text-primary)]">Interview Intelligence</div>
          </div>
        </NavLink>

        <nav className="hidden items-center gap-2 md:flex">
          {links.map((link) => (
            <NavLink key={link.to} className={navClass} to={link.to}>
              {link.label}
            </NavLink>
          ))}
        </nav>

        <button
          className="glass-panel flex h-11 w-11 items-center justify-center md:hidden"
          onClick={() => setOpen((value) => !value)}
          type="button"
        >
          <Menu size={18} />
        </button>
      </div>

      {open ? (
        <div className="border-t border-[var(--border-subtle)] px-4 pb-4 md:hidden">
          <div className="mt-3 flex flex-col gap-2">
            {links.map((link) => (
              <NavLink key={link.to} className={navClass} onClick={() => setOpen(false)} to={link.to}>
                {link.label}
              </NavLink>
            ))}
          </div>
        </div>
      ) : null}
    </header>
  );
}
