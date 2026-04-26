import { motion } from "framer-motion";
import type { ReactElement } from "react";
import { ROLES } from "../data";
import { Section } from "./Section";

const ROLE_ICON: Record<string, ReactElement> = {
  witness: (
    <svg viewBox="0 0 64 64" className="h-9 w-9">
      <circle cx="32" cy="32" r="20" stroke="currentColor" strokeWidth="2" fill="none" />
      <circle cx="32" cy="32" r="6" fill="currentColor" />
      <path d="M4 32 Q32 4 60 32 Q32 60 4 32 Z" stroke="currentColor" strokeWidth="2" fill="none" />
    </svg>
  ),
  relay: (
    <svg viewBox="0 0 64 64" className="h-9 w-9">
      <circle cx="14" cy="32" r="6" stroke="currentColor" strokeWidth="2" fill="none" />
      <circle cx="50" cy="32" r="6" stroke="currentColor" strokeWidth="2" fill="none" />
      <circle cx="32" cy="32" r="4" fill="currentColor" />
      <path d="M20 32 H28 M36 32 H44" stroke="currentColor" strokeWidth="2" />
      <path d="M32 14 V20 M32 44 V50" stroke="currentColor" strokeWidth="2" />
    </svg>
  ),
  editor: (
    <svg viewBox="0 0 64 64" className="h-9 w-9">
      <rect x="10" y="14" width="44" height="36" rx="4" stroke="currentColor" strokeWidth="2" fill="none" />
      <path d="M16 22 H48 M16 30 H40 M16 38 H44" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <circle cx="50" cy="50" r="6" fill="currentColor" />
    </svg>
  ),
  adversary: (
    <svg viewBox="0 0 64 64" className="h-9 w-9">
      <path d="M32 8 L56 24 L48 56 H16 L8 24 Z" stroke="currentColor" strokeWidth="2" fill="none" />
      <circle cx="24" cy="32" r="3" fill="currentColor" />
      <circle cx="40" cy="32" r="3" fill="currentColor" />
      <path d="M22 44 Q32 38 42 44" stroke="currentColor" strokeWidth="2" fill="none" />
    </svg>
  ),
};

export function Roles() {
  return (
    <Section
      id="roles"
      eyebrow="The cast"
      title={
        <>
          Four roles. <span className="gradient-text">One hidden truth.</span>
        </>
      }
      subtitle={
        <>
          Every episode is a pragmatic-inference game with hidden roles. The
          trained agent plays one of these four — and only ever talks to the
          environment via MCP-style tools, per OpenEnv RFC 003.
        </>
      }
    >
      <div className="grid gap-5 md:grid-cols-2">
        {ROLES.map((r, i) => (
          <motion.div
            key={r.id}
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-15% 0%" }}
            transition={{
              duration: 0.7,
              delay: i * 0.08,
              ease: [0.22, 1, 0.36, 1],
            }}
            className="group relative overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.04] to-white/[0.01] p-7 backdrop-blur-xl transition hover:border-white/20"
          >
            <div
              className={`pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-gradient-to-br ${r.accent} opacity-30 blur-3xl transition-opacity group-hover:opacity-60`}
            />
            <div className="relative flex items-start justify-between gap-4">
              <div className="flex items-center gap-4">
                <div
                  className={`flex h-14 w-14 items-center justify-center rounded-xl border border-white/10 bg-white/[0.04] text-white shadow-glow`}
                >
                  {ROLE_ICON[r.id]}
                </div>
                <div>
                  <div className="text-xs uppercase tracking-[0.22em] text-white/45">
                    Role · {r.id}
                  </div>
                  <h3 className="mt-1 font-display text-2xl font-semibold tracking-tight text-white">
                    {r.name}
                  </h3>
                </div>
              </div>
              <span className="mono rounded-md border border-white/10 bg-black/40 px-2 py-1 text-[10px] uppercase tracking-[0.18em] text-white/55">
                A · {r.glyph}
              </span>
            </div>

            <p className="relative mt-5 text-base leading-relaxed text-white/65">
              <span className="text-white/85">{r.tagline}</span> {r.description}
            </p>

            <div className="relative mt-6 grid gap-2 border-t border-white/10 pt-5">
              <div className="text-xs uppercase tracking-[0.18em] text-white/40">
                Legal tools
              </div>
              <div className="flex flex-wrap gap-1.5">
                {r.tools.map((t) => (
                  <span
                    key={t}
                    className="mono rounded-md border border-white/10 bg-white/[0.03] px-2.5 py-1 text-[11px] text-white/75"
                  >
                    {t}
                  </span>
                ))}
              </div>
            </div>

            <ul className="relative mt-6 grid gap-2 text-sm text-white/65">
              {r.bullets.map((b) => (
                <li key={b} className="flex items-start gap-2.5">
                  <span className="mt-[7px] h-1 w-1 flex-none rounded-full bg-white/40" />
                  {b}
                </li>
              ))}
            </ul>
          </motion.div>
        ))}
      </div>
    </Section>
  );
}
