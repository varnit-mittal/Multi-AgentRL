import { motion } from "framer-motion";
import type { ReactElement } from "react";
import { TASKS, type Difficulty } from "../data";
import { Section } from "./Section";

const DIFF_STYLES: Record<Difficulty, string> = {
  easy: "border-emerald-400/30 text-emerald-200 bg-emerald-400/10",
  medium: "border-amber-400/30 text-amber-200 bg-amber-400/10",
  hard: "border-rose-400/30 text-rose-200 bg-rose-400/10",
};

const TASK_GLYPHS: Record<string, ReactElement> = {
  t1: (
    <svg viewBox="0 0 100 60" className="h-full w-full">
      <line x1="10" y1="30" x2="90" y2="30" stroke="white" strokeOpacity="0.1" />
      {[15, 50, 85].map((x, i) => (
        <circle
          key={x}
          cx={x}
          cy={30}
          r="6"
          fill={i === 0 ? "#22d3ee" : i === 1 ? "#a78bfa" : "#f472b6"}
          opacity="0.85"
        />
      ))}
    </svg>
  ),
  t2: (
    <svg viewBox="0 0 100 60" className="h-full w-full">
      <line x1="15" y1="20" x2="80" y2="40" stroke="white" strokeOpacity="0.1" />
      <line x1="15" y1="40" x2="80" y2="40" stroke="white" strokeOpacity="0.1" />
      <circle cx="15" cy="20" r="5.5" fill="#22d3ee" />
      <circle cx="15" cy="40" r="5.5" fill="#22d3ee" />
      <circle cx="80" cy="40" r="6" fill="#f472b6" />
    </svg>
  ),
  t3: (
    <svg viewBox="0 0 100 60" className="h-full w-full">
      <line x1="15" y1="18" x2="80" y2="40" stroke="white" strokeOpacity="0.1" />
      <line x1="15" y1="42" x2="80" y2="40" stroke="white" strokeOpacity="0.1" />
      <circle cx="15" cy="18" r="5.5" fill="#22d3ee" />
      <circle cx="15" cy="42" r="5.5" fill="#fb7185" />
      <circle cx="80" cy="40" r="6" fill="#f472b6" />
    </svg>
  ),
  t4: (
    <svg viewBox="0 0 100 60" className="h-full w-full">
      <line x1="6" y1="30" x2="94" y2="30" stroke="white" strokeOpacity="0.1" />
      {[10, 30, 50, 70, 90].map((x, i) => (
        <circle
          key={x}
          cx={x}
          cy={30}
          r={i === 2 ? 6 : 4.5}
          fill={
            i === 0 ? "#fb7185" : i === 4 ? "#f472b6" : "#a78bfa"
          }
          opacity={i === 2 ? 1 : 0.75}
        />
      ))}
    </svg>
  ),
  t5: (
    <svg viewBox="0 0 100 60" className="h-full w-full">
      <g stroke="white" strokeOpacity="0.08">
        <line x1="50" y1="30" x2="20" y2="14" />
        <line x1="50" y1="30" x2="80" y2="14" />
        <line x1="50" y1="30" x2="14" y2="44" />
        <line x1="50" y1="30" x2="86" y2="44" />
        <line x1="50" y1="30" x2="50" y2="52" />
      </g>
      <circle cx="20" cy="14" r="4" fill="#fb7185" />
      <circle cx="80" cy="14" r="4" fill="#fb7185" />
      <circle cx="14" cy="44" r="4" fill="#22d3ee" />
      <circle cx="86" cy="44" r="4" fill="#a78bfa" />
      <circle cx="50" cy="52" r="4" fill="#a78bfa" />
      <circle cx="50" cy="30" r="6" fill="#f472b6" />
    </svg>
  ),
  t6: (
    <svg viewBox="0 0 100 60" className="h-full w-full">
      <rect x="10" y="14" width="80" height="6" rx="2" fill="#22d3ee" opacity="0.55" />
      <rect x="10" y="26" width="64" height="6" rx="2" fill="#a78bfa" opacity="0.55" />
      <rect x="10" y="38" width="50" height="6" rx="2" fill="#f472b6" opacity="0.55" />
    </svg>
  ),
};

export function Tasks() {
  return (
    <Section
      id="tasks"
      eyebrow="Curriculum"
      title={
        <>
          Five tasks plus a stretch.{" "}
          <span className="gradient-text">Easy → impossible-for-baselines.</span>
        </>
      }
      subtitle={
        <>
          The trainer walks the agent up a curriculum: simple relays, then
          triangulation, then liars, then cascades, then full coalitions. The
          rubric shifts weight as it climbs.
        </>
      }
    >
      <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
        {TASKS.map((t, i) => (
          <motion.div
            key={t.id}
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-10% 0%" }}
            transition={{
              duration: 0.6,
              delay: i * 0.06,
              ease: [0.22, 1, 0.36, 1],
            }}
            className="group relative overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-b from-white/[0.04] to-white/[0.005] p-6 backdrop-blur transition hover:border-white/25 hover:from-white/[0.07]"
          >
            <div className="pointer-events-none absolute -right-16 -top-16 h-40 w-40 rounded-full bg-violet-500/10 blur-2xl transition-opacity group-hover:opacity-100" />

            <div className="flex items-center justify-between">
              <span className="mono text-[10px] uppercase tracking-[0.24em] text-white/35">
                {t.id}
              </span>
              <span
                className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.18em] ${
                  DIFF_STYLES[t.difficulty]
                }`}
              >
                {t.difficulty}
              </span>
            </div>

            <h3 className="mt-3 font-display text-2xl font-semibold tracking-tight text-white">
              {t.name}
            </h3>

            <div className="mt-4 h-16 w-full rounded-xl border border-white/[0.06] bg-black/40 p-1.5">
              {TASK_GLYPHS[t.id]}
            </div>

            <p className="mt-4 text-sm leading-relaxed text-white/65">
              {t.setup}
            </p>

            <div className="mt-5 grid grid-cols-2 gap-3 border-t border-white/[0.07] pt-4">
              <div>
                <div className="mono text-[10px] uppercase tracking-[0.18em] text-white/40">
                  signal
                </div>
                <div className="mt-1 text-xs text-white/80">{t.signal}</div>
              </div>
              <div>
                <div className="mono text-[10px] uppercase tracking-[0.18em] text-white/40">
                  trained target
                </div>
                <div className="mt-1 mono text-base font-semibold tabular-nums text-white">
                  {t.trained.toFixed(2)}
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </Section>
  );
}
