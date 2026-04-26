import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowDown, Code2, Sparkles } from "lucide-react";
import { HERO_METRICS, SCENARIOS } from "../data";
import { CountUp } from "./CountUp";
import { MouseHalo } from "./MouseHalo";

// Ambient backdrop nodes — tucked into corners and edges so they never
// compete with the hero copy. Coordinates stay outside a generous safe-zone
// (roughly x in [25, 75] and y in [25, 80]).
const NODES = [
  { x: 6, y: 14, r: 0.9, hue: "#22d3ee", delay: 0 },
  { x: 18, y: 6, r: 0.7, hue: "#a78bfa", delay: 0.3 },
  { x: 92, y: 8, r: 0.8, hue: "#f472b6", delay: 0.6 },
  { x: 80, y: 18, r: 0.7, hue: "#22d3ee", delay: 0.9 },
  { x: 96, y: 26, r: 0.6, hue: "#a78bfa", delay: 1.2 },
  { x: 4, y: 78, r: 0.8, hue: "#a78bfa", delay: 0.4 },
  { x: 14, y: 90, r: 0.9, hue: "#22d3ee", delay: 0.7 },
  { x: 26, y: 96, r: 0.7, hue: "#fb7185", delay: 1.0 },
  { x: 92, y: 94, r: 0.9, hue: "#a78bfa", delay: 1.3 },
  { x: 78, y: 86, r: 0.8, hue: "#22d3ee", delay: 1.6 },
  { x: 60, y: 96, r: 0.7, hue: "#f472b6", delay: 0.5 },
  { x: 96, y: 64, r: 0.8, hue: "#22d3ee", delay: 1.1 },
];

const EDGES: [number, number][] = [
  [0, 1],
  [2, 3],
  [3, 4],
  [5, 6],
  [6, 7],
  [9, 8],
  [9, 10],
  [8, 11],
];

export function Hero() {
  const [scenarioId, setScenarioId] = useState(SCENARIOS[0].id);
  const scenario = SCENARIOS.find((s) => s.id === scenarioId) ?? SCENARIOS[0];

  return (
    <header className="relative isolate overflow-hidden">
      <MouseHalo />

      {/* ambient network backdrop — corners only, behind the copy */}
      <svg
        className="absolute inset-0 -z-10 h-full w-full opacity-60"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
        aria-hidden
      >
        <defs>
          <radialGradient id="hero-glow" cx="50%" cy="14%" r="55%">
            <stop offset="0%" stopColor="rgba(167,139,250,0.22)" />
            <stop offset="100%" stopColor="rgba(167,139,250,0)" />
          </radialGradient>
          <linearGradient id="edge-grad" x1="0" x2="1" y1="0" y2="1">
            <stop offset="0%" stopColor="#22d3ee" />
            <stop offset="50%" stopColor="#a78bfa" />
            <stop offset="100%" stopColor="#f472b6" />
          </linearGradient>
        </defs>
        <rect width="100" height="100" fill="url(#hero-glow)" />
        {EDGES.map(([a, b], i) => (
          <motion.line
            key={i}
            x1={NODES[a].x}
            y1={NODES[a].y}
            x2={NODES[b].x}
            y2={NODES[b].y}
            stroke="url(#edge-grad)"
            strokeWidth={0.08}
            strokeLinecap="round"
            initial={{ pathLength: 0, opacity: 0 }}
            animate={{ pathLength: 1, opacity: 0.32 }}
            transition={{ duration: 2, delay: 0.2 + i * 0.08, ease: "easeOut" }}
          />
        ))}
        {NODES.map((n, i) => (
          <g key={i}>
            <motion.circle
              cx={n.x}
              cy={n.y}
              r={n.r * 1.8}
              fill={n.hue}
              opacity={0.07}
              initial={{ scale: 0 }}
              animate={{ scale: [0.8, 1.2, 0.8] }}
              transition={{
                duration: 5,
                repeat: Infinity,
                delay: n.delay,
                ease: "easeInOut",
              }}
              style={{ transformOrigin: `${n.x}px ${n.y}px` }}
            />
            <motion.circle
              cx={n.x}
              cy={n.y}
              r={n.r * 0.55}
              fill={n.hue}
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.7 }}
              transition={{ duration: 1.4, delay: 0.5 + i * 0.05 }}
            />
          </g>
        ))}
      </svg>

      {/* fade-out scanline */}
      <div className="pointer-events-none absolute inset-0 -z-10 bg-[linear-gradient(180deg,transparent_0%,rgba(6,6,10,0)_70%,#06060a_100%)]" />

      <div className="relative mx-auto flex min-h-[100svh] w-full max-w-7xl flex-col items-start justify-center px-6 pb-24 pt-28 md:px-10">
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.1 }}
          className="pill mb-7"
        >
          <Sparkles className="h-3.5 w-3.5 text-violet-300" />
          OpenEnv 0.2.3 · Qwen2.5-3B · TRL GRPO
        </motion.div>

        <motion.h1
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
          className="font-display text-[clamp(56px,11vw,180px)] font-bold leading-[0.92] tracking-[-0.045em] text-white"
        >
          Whispers
        </motion.h1>

        <motion.p
          key={scenario.id}
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.55, ease: [0.22, 1, 0.36, 1] }}
          className="mt-6 max-w-2xl text-lg leading-relaxed text-white/65 md:text-2xl md:leading-snug"
        >
          A small{" "}
          <span className="gradient-text font-semibold">graph of LLM agents</span>
          . The hidden truth tonight:{" "}
          <span className="mono text-white">{scenario.hidden_truth}</span>. The
          adversary's planted lie:{" "}
          <span className="mono text-rose-300/90">{scenario.planted_lie}</span>.
          Train one node with RL to{" "}
          <span className="text-white">publish what's actually true.</span>
        </motion.p>

        {/* scenario chips with inline score reveal */}
        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.55 }}
          className="mt-7 flex flex-wrap items-center gap-2"
        >
          <span className="mono text-[10px] uppercase tracking-[0.22em] text-white/35">
            try a scenario
          </span>
          {SCENARIOS.map((s) => {
            const active = s.id === scenarioId;
            return (
              <button
                key={s.id}
                onClick={() => setScenarioId(s.id)}
                className={
                  "rounded-full border px-3 py-1 text-[11px] font-medium transition " +
                  (active
                    ? "border-white/30 bg-white/10 text-white shadow-glow"
                    : "border-white/10 bg-white/[0.02] text-white/55 hover:border-white/20 hover:text-white/85")
                }
              >
                {s.label}
              </button>
            );
          })}
        </motion.div>

        {/* live score readout for the active scenario — measured numbers */}
        <motion.div
          key={`stats-${scenario.id}`}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mt-4 flex flex-wrap items-center gap-x-6 gap-y-2 mono text-[12px] text-white/55"
        >
          <span className="inline-flex items-center gap-1.5">
            <span className="text-white/35">{scenario.tag}</span>
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
            trained editor
            <span className="text-emerald-300">{scenario.trained_score.toFixed(2)}</span>
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="h-1.5 w-1.5 rounded-full bg-rose-400" />
            naive_relay
            <span className="text-rose-300">{scenario.naive_score.toFixed(2)}</span>
          </span>
          <span className="text-white/55">
            <span className="text-emerald-300/90">{scenario.delta_label}</span>
          </span>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.7 }}
          className="mt-10 flex flex-wrap items-center gap-3"
        >
          <a
            href="#live"
            className="group relative inline-flex items-center gap-2 overflow-hidden rounded-full border border-white/15 bg-white px-6 py-3 text-sm font-semibold text-black transition hover:bg-white/90"
          >
            <span className="relative z-10">Watch a live episode</span>
            <ArrowDown className="relative z-10 h-4 w-4 transition group-hover:translate-y-0.5" />
          </a>
          <a
            href="#tasks"
            className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-6 py-3 text-sm font-semibold text-white/85 backdrop-blur transition hover:bg-white/[0.07]"
          >
            See the 6 tasks
          </a>
          <a
            href="#"
            className="inline-flex items-center gap-2 rounded-full px-4 py-3 text-sm text-white/55 transition hover:text-white"
          >
            <Code2 className="h-4 w-4" /> Source on HF Space
          </a>
        </motion.div>

        {/* metric strip — animated, hoverable */}
        <motion.div
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.9, delay: 1.0 }}
          className="mt-16 grid w-full grid-cols-2 gap-px overflow-hidden rounded-2xl border border-white/[0.07] bg-white/[0.02] backdrop-blur md:grid-cols-4"
        >
          {HERO_METRICS.map((m) => (
            <MetricTile key={m.value} {...m} />
          ))}
        </motion.div>
      </div>

      <motion.a
        href="#problem"
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.5 }}
        transition={{ delay: 1.6, duration: 1 }}
        className="absolute bottom-6 left-1/2 -translate-x-1/2 mono text-[10px] uppercase tracking-[0.32em] text-white/40 hover:text-white/80"
      >
        ↓ scroll
      </motion.a>
    </header>
  );
}

function MetricTile({
  value,
  target,
  label,
  detail,
  suffix,
}: {
  value: string;
  target?: number;
  label: string;
  detail: string;
  suffix?: string;
}) {
  const [hover, setHover] = useState(false);
  const decimals = value.includes(".") ? (value.split(".")[1] ?? "").replace(/\D/g, "").length : 0;
  const showCountUp = typeof target === "number";
  return (
    <div
      onMouseEnter={() => setHover(true)}
      onMouseLeave={() => setHover(false)}
      className="group relative cursor-default bg-[#08080d] p-6 transition hover:bg-[#0c0c14]"
    >
      <div className="mono text-3xl font-semibold leading-none text-white">
        {showCountUp ? (
          <>
            {value.startsWith("+") ? "+" : ""}
            <CountUp to={target!} decimals={decimals} suffix={suffix} />
          </>
        ) : (
          value
        )}
      </div>
      <div className="mt-2 text-sm leading-snug text-white/55">{label}</div>
      <motion.div
        initial={false}
        animate={{ opacity: hover ? 1 : 0, y: hover ? 0 : 4 }}
        transition={{ duration: 0.25 }}
        className="mt-2 mono text-[10.5px] leading-snug text-white/40"
      >
        {detail}
      </motion.div>
      <motion.span
        initial={false}
        animate={{ scaleX: hover ? 1 : 0 }}
        transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
        className="absolute inset-x-6 bottom-3 h-px origin-left bg-gradient-to-r from-cyan-400/70 via-violet-400/70 to-pink-400/70"
      />
    </div>
  );
}
