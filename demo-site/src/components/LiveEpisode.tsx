import { AnimatePresence, motion } from "framer-motion";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  EPISODE,
  EPISODE_AGENTS,
  EPISODE_EDGES,
  EPISODE_LIE,
  EPISODE_TRUTH,
  type Agent,
  type EpisodeStep,
} from "../data";
import { Section } from "./Section";
import {
  AlertOctagon,
  CheckCircle2,
  Pause,
  Play,
  RotateCcw,
  ShieldAlert,
  Wand2,
} from "lucide-react";
import clsx from "clsx";

const ROLE_COLORS: Record<string, string> = {
  witness: "#22d3ee",
  relay: "#a78bfa",
  editor: "#f472b6",
  adversary: "#fb7185",
};

const TONE_COLORS: Record<string, string> = {
  honest: "#22d3ee",
  lie: "#fb7185",
  verify: "#a3e635",
  publish: "#a78bfa",
};

function agentById(id: number): Agent {
  return EPISODE_AGENTS[id];
}

export function LiveEpisode() {
  const [stepIdx, setStepIdx] = useState(-1);
  const [playing, setPlaying] = useState(false);
  const [showOracle, setShowOracle] = useState(false);
  const tRef = useRef<number | null>(null);

  const advance = useCallback(() => {
    setStepIdx((i) => {
      const next = i + 1;
      if (next >= EPISODE.length) {
        setPlaying(false);
        return i;
      }
      return next;
    });
  }, []);

  useEffect(() => {
    if (!playing) return;
    const step = EPISODE[stepIdx];
    let delay = 2400;
    if (step?.kind === "narration") delay = 3500;
    if (step?.kind === "publish") delay = 5200;
    if (stepIdx === -1) delay = 800;
    tRef.current = window.setTimeout(advance, delay);
    return () => {
      if (tRef.current) window.clearTimeout(tRef.current);
    };
  }, [playing, stepIdx, advance]);

  const reset = () => {
    setPlaying(false);
    setStepIdx(-1);
    setShowOracle(false);
    if (tRef.current) window.clearTimeout(tRef.current);
  };

  // Detect oracle reveal at narration "Oracle · false"
  useEffect(() => {
    const step = EPISODE[stepIdx];
    if (step?.kind === "narration" && step.title.startsWith("Oracle")) {
      setShowOracle(true);
    }
  }, [stepIdx]);

  const visibleSteps = useMemo(
    () => EPISODE.slice(0, Math.max(0, stepIdx + 1)),
    [stepIdx]
  );

  const currentMessage = useMemo(() => {
    const step = EPISODE[stepIdx];
    return step?.kind === "message" ? step : null;
  }, [stepIdx]);

  const publishStep = useMemo(() => {
    return visibleSteps.find((s) => s.kind === "publish");
  }, [visibleSteps]) as Extract<EpisodeStep, { kind: "publish" }> | undefined;

  // collect inboxes
  const inboxes = useMemo(() => {
    const map: Record<number, { from: number; content: string; tone: string; conf: number }[]> = {
      0: [],
      1: [],
      2: [],
      3: [],
    };
    for (const s of visibleSteps) {
      if (s.kind === "message") {
        const targets = s.to === -1 ? [0, 1, 2, 3].filter((id) => id !== s.from) : [s.to];
        for (const t of targets) {
          map[t].push({
            from: s.from,
            content: s.content,
            tone: s.tone,
            conf: s.confidence,
          });
        }
      }
    }
    return map;
  }, [visibleSteps]);

  return (
    <Section
      id="live"
      eyebrow="Live episode · t3"
      title={
        <>
          Watch one round play out.{" "}
          <span className="gradient-text">Hit play.</span>
        </>
      }
      subtitle={
        <>
          A scripted run of <span className="mono text-white/85">Spot the Liar</span>{" "}
          on the trained editor. Every message, tool call, and confidence is
          drawn from the same rubric the trainer uses.
        </>
      }
    >
      {/* Controls + truth/lie + score */}
      <div className="mb-6 flex flex-wrap items-center justify-between gap-4">
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => {
              if (stepIdx === -1) setStepIdx(0);
              setPlaying((p) => !p);
            }}
            className="group inline-flex items-center gap-2 rounded-full bg-white px-5 py-2.5 text-sm font-semibold text-black shadow-glow transition hover:bg-white/90"
          >
            {playing ? (
              <>
                <Pause className="h-4 w-4" /> Pause
              </>
            ) : (
              <>
                <Play className="h-4 w-4 fill-black" /> {stepIdx === -1 ? "Play episode" : "Resume"}
              </>
            )}
          </button>
          <button
            onClick={reset}
            className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-4 py-2.5 text-sm font-medium text-white/80 backdrop-blur transition hover:bg-white/[0.07]"
          >
            <RotateCcw className="h-4 w-4" />
            Reset
          </button>
          <button
            onClick={advance}
            className="inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-4 py-2.5 text-sm font-medium text-white/80 backdrop-blur transition hover:bg-white/[0.07]"
          >
            Step ▸
          </button>
          <span className="mono ml-2 hidden text-xs text-white/50 md:inline">
            turn {Math.max(0, stepIdx + 1)}/{EPISODE.length}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="flex items-center gap-2 rounded-xl border border-cyan-400/20 bg-cyan-400/[0.05] px-3 py-2">
            <CheckCircle2 className="h-4 w-4 text-cyan-300" />
            <span className="mono text-cyan-200/90">truth</span>
            <span className="ml-1 hidden md:inline text-white/75">
              {EPISODE_TRUTH.event} · {EPISODE_TRUTH.magnitude} · {EPISODE_TRUTH.location}
            </span>
          </div>
          <div className="flex items-center gap-2 rounded-xl border border-rose-400/20 bg-rose-400/[0.05] px-3 py-2">
            <ShieldAlert className="h-4 w-4 text-rose-300" />
            <span className="mono text-rose-200/90">planted lie</span>
            <span className="ml-1 hidden md:inline text-white/75">
              {EPISODE_LIE.event}
            </span>
          </div>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        {/* Network graph + narration */}
        <div className="panel relative overflow-hidden p-6">
          <NetworkGraph
            currentStep={stepIdx}
            currentMessage={currentMessage}
            visibleSteps={visibleSteps}
          />

          <div className="pointer-events-none absolute left-1/2 top-6 -translate-x-1/2">
            <AnimatePresence mode="wait">
              {EPISODE[stepIdx]?.kind === "narration" && (
                <motion.div
                  key={stepIdx}
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  transition={{ duration: 0.5 }}
                  className="max-w-md rounded-2xl border border-white/10 bg-black/70 px-5 py-4 text-center backdrop-blur"
                >
                  <div className="mono text-[10px] uppercase tracking-[0.28em] text-violet-300/80">
                    {(EPISODE[stepIdx] as any).title}
                  </div>
                  <div className="mt-2 text-sm leading-relaxed text-white/85">
                    {(EPISODE[stepIdx] as any).body}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <AnimatePresence>
            {showOracle && stepIdx >= 6 && (
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.4 }}
                className="pointer-events-none absolute right-6 top-6 flex items-center gap-2 rounded-xl border border-rose-400/30 bg-rose-500/10 px-3 py-2 mono text-xs text-rose-200 backdrop-blur"
              >
                <AlertOctagon className="h-4 w-4" />
                oracle · 'industrial fire' = false
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Right column: transcript + inboxes */}
        <div className="grid gap-4">
          <Transcript steps={visibleSteps} />
          <Inboxes inboxes={inboxes} />
        </div>
      </div>

      {/* Publish reveal */}
      <AnimatePresence>
        {publishStep && publishStep.kind === "publish" && (
          <PublishReveal step={publishStep} />
        )}
      </AnimatePresence>
    </Section>
  );
}

function NetworkGraph({
  currentStep,
  currentMessage,
  visibleSteps,
}: {
  currentStep: number;
  currentMessage: Extract<EpisodeStep, { kind: "message" }> | null;
  visibleSteps: EpisodeStep[];
}) {
  // Track which agents have been "active" so we can dim/brighten them.
  const activeAgentIds = new Set<number>();
  for (const s of visibleSteps) {
    if (s.kind === "message") {
      activeAgentIds.add(s.from);
      if (s.to !== -1) activeAgentIds.add(s.to);
    }
    if (s.kind === "tool" || s.kind === "publish") activeAgentIds.add(s.from);
  }
  return (
    <div className="aspect-[16/12] w-full">
      <svg viewBox="0 0 100 100" className="h-full w-full">
        <defs>
          <radialGradient id="nodeGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="white" stopOpacity="0.6" />
            <stop offset="100%" stopColor="white" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="msgGrad" x1="0" x2="1" y1="0" y2="0">
            <stop
              offset="0%"
              stopColor={currentMessage ? TONE_COLORS[currentMessage.tone] : "#22d3ee"}
            />
            <stop offset="100%" stopColor="white" stopOpacity={0} />
          </linearGradient>
        </defs>

        {/* edges */}
        {EPISODE_EDGES.map((e, i) => {
          const A = agentById(e.a);
          const B = agentById(e.b);
          return (
            <line
              key={i}
              x1={A.x}
              y1={A.y}
              x2={B.x}
              y2={B.y}
              stroke="white"
              strokeOpacity={0.08}
              strokeWidth={0.18}
              strokeDasharray="0.6 0.6"
            />
          );
        })}

        {/* active message: animated travelling dot + label */}
        {currentMessage && (
          <MessageBeam
            from={agentById(currentMessage.from)}
            to={
              currentMessage.to === -1
                ? { x: 50, y: 50, role: "editor", id: -1, label: "" } as any
                : agentById(currentMessage.to)
            }
            tone={currentMessage.tone}
            stepKey={currentStep}
          />
        )}

        {/* nodes */}
        {EPISODE_AGENTS.map((a) => {
          const isActive = activeAgentIds.has(a.id);
          const c = ROLE_COLORS[a.role];
          return (
            <g key={a.id}>
              {/* halo */}
              <motion.circle
                cx={a.x}
                cy={a.y}
                r={9}
                fill={c}
                opacity={isActive ? 0.18 : 0.05}
                animate={{
                  r: isActive ? [8, 11, 8] : 8,
                }}
                transition={{
                  duration: 2.4,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
              />
              <circle
                cx={a.x}
                cy={a.y}
                r={5.6}
                fill="#0c0c14"
                stroke={c}
                strokeWidth={0.5}
                opacity={isActive ? 1 : 0.55}
              />
              <text
                x={a.x}
                y={a.y + 1.3}
                textAnchor="middle"
                fontSize={3.2}
                fontWeight={700}
                fill={c}
                fontFamily="JetBrains Mono, monospace"
              >
                {a.role[0].toUpperCase()}
              </text>
              <text
                x={a.x}
                y={a.y + 11.5}
                textAnchor="middle"
                fontSize={2.4}
                fill="rgba(255,255,255,0.7)"
                fontFamily="Inter, sans-serif"
                fontWeight={500}
              >
                {a.label}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function MessageBeam({
  from,
  to,
  tone,
  stepKey,
}: {
  from: Agent;
  to: Agent;
  tone: "honest" | "lie" | "verify" | "publish";
  stepKey: number;
}) {
  const color = TONE_COLORS[tone];
  return (
    <motion.g
      key={stepKey + "-" + from.id + "-" + to.id}
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <line
        x1={from.x}
        y1={from.y}
        x2={to.x}
        y2={to.y}
        stroke={color}
        strokeOpacity={0.55}
        strokeWidth={0.35}
      />
      <motion.circle
        r={1.2}
        fill={color}
        initial={{ cx: from.x, cy: from.y }}
        animate={{ cx: to.x, cy: to.y }}
        transition={{ duration: 1.2, ease: "easeInOut" }}
      />
      <motion.circle
        r={2.2}
        fill={color}
        opacity={0.35}
        initial={{ cx: from.x, cy: from.y }}
        animate={{ cx: to.x, cy: to.y }}
        transition={{ duration: 1.2, ease: "easeInOut" }}
      />
    </motion.g>
  );
}

function Transcript({ steps }: { steps: EpisodeStep[] }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (ref.current) ref.current.scrollTop = ref.current.scrollHeight;
  }, [steps.length]);
  return (
    <div className="panel relative flex h-[280px] flex-col overflow-hidden p-5">
      <div className="mb-3 flex items-center justify-between">
        <div className="mono text-xs uppercase tracking-[0.22em] text-white/45">
          Transcript
        </div>
        <div className="mono text-[10px] text-white/30">live · t3</div>
      </div>
      <div ref={ref} className="flex-1 overflow-y-auto pr-1">
        <ul className="space-y-2.5">
          <AnimatePresence initial={false}>
            {steps.map((s, i) => (
              <motion.li
                key={i}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.4 }}
              >
                <TranscriptLine step={s} />
              </motion.li>
            ))}
          </AnimatePresence>
        </ul>
      </div>
    </div>
  );
}

function TranscriptLine({ step }: { step: EpisodeStep }) {
  if (step.kind === "narration") {
    return (
      <div className="rounded-lg border border-violet-400/20 bg-violet-400/5 px-3 py-2 text-xs text-violet-200/80">
        <span className="mono mr-2 text-violet-300/80">▸ {step.title}</span>
      </div>
    );
  }
  if (step.kind === "tool") {
    return (
      <div className="rounded-lg border border-white/10 bg-white/[0.03] px-3 py-2 text-xs text-white/75">
        <span className="mono mr-2 text-amber-200/90">tool · {step.tool}</span>
        <span>{step.detail}</span>
      </div>
    );
  }
  if (step.kind === "message") {
    const fromAgent = agentById(step.from);
    const toLabel = step.to === -1 ? "broadcast" : agentById(step.to).label;
    const color = TONE_COLORS[step.tone];
    return (
      <div
        className="rounded-lg border px-3 py-2.5 text-xs"
        style={{
          borderColor: `${color}33`,
          background: `${color}0d`,
        }}
      >
        <div className="mono flex items-center justify-between text-[10px] uppercase tracking-[0.18em]">
          <span style={{ color }}>{fromAgent.label} → {toLabel}</span>
          <span className="text-white/45">conf {step.confidence.toFixed(2)}</span>
        </div>
        <div className="mt-1 text-white/85">"{step.content}"</div>
        <div className="mt-1 mono text-[10px] text-white/45">
          src: {step.claimed_source}
        </div>
      </div>
    );
  }
  if (step.kind === "publish") {
    return (
      <div className="rounded-lg border border-pink-400/30 bg-pink-400/[0.06] px-3 py-2 text-xs text-pink-100/90">
        <span className="mono mr-2 uppercase tracking-[0.2em] text-pink-300/90">
          ✦ publish
        </span>
        Editor publishes the final report. Episode score{" "}
        <span className="mono text-white">{step.score.toFixed(2)}</span>.
      </div>
    );
  }
  return null;
}

function Inboxes({
  inboxes,
}: {
  inboxes: Record<number, { from: number; content: string; tone: string; conf: number }[]>;
}) {
  return (
    <div className="panel grid grid-cols-2 gap-3 p-4">
      {EPISODE_AGENTS.map((a) => (
        <div
          key={a.id}
          className="rounded-xl border border-white/[0.07] bg-white/[0.02] p-3"
        >
          <div className="mb-2 flex items-center justify-between">
            <div
              className="mono text-[10px] uppercase tracking-[0.2em]"
              style={{ color: ROLE_COLORS[a.role] }}
            >
              {a.label}
            </div>
            <div className="mono text-[10px] text-white/35">
              inbox · {inboxes[a.id].length}
            </div>
          </div>
          <ul className="space-y-1.5">
            {inboxes[a.id].length === 0 && (
              <li className="text-[11px] italic text-white/30">empty</li>
            )}
            {inboxes[a.id].slice(-3).map((m, i) => (
              <li
                key={i}
                className="rounded-md border border-white/10 bg-white/[0.02] px-2 py-1.5 text-[11px] text-white/80"
              >
                <div
                  className="mono text-[9px] uppercase tracking-[0.18em]"
                  style={{ color: TONE_COLORS[m.tone] }}
                >
                  ← from {agentById(m.from).label} · conf {m.conf.toFixed(2)}
                </div>
                <div className="line-clamp-2 leading-snug">"{m.content}"</div>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  );
}

function PublishReveal({
  step,
}: {
  step: Extract<EpisodeStep, { kind: "publish" }>;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
      className="relative mt-10 overflow-hidden rounded-2xl border border-white/10 bg-gradient-to-br from-pink-500/[0.06] via-violet-500/[0.04] to-cyan-500/[0.05] p-8 backdrop-blur-xl"
    >
      <div className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full bg-pink-400/20 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-24 -left-24 h-72 w-72 rounded-full bg-cyan-400/20 blur-3xl" />

      <div className="relative grid gap-8 md:grid-cols-[1.2fr_1fr]">
        <div>
          <div className="pill mb-4">
            <Wand2 className="h-3.5 w-3.5 text-pink-300" />
            publish · final report
          </div>
          <h3 className="font-display text-3xl font-semibold tracking-tight text-white">
            Calibrated, cross-verified, on time.
          </h3>
          <p className="mt-3 max-w-md text-sm text-white/65">
            Each field is scored on a Brier rule. The trained editor publishes
            confidences that match its evidence — not the loudest source.
          </p>

          <div className="mt-6 space-y-3">
            {step.report.map((r) => {
              const correct = r.value === r.truth;
              return (
                <div
                  key={r.field}
                  className="grid grid-cols-[110px_1fr_72px] items-center gap-3 rounded-xl border border-white/10 bg-black/30 px-4 py-3"
                >
                  <div className="mono text-[11px] uppercase tracking-[0.18em] text-white/45">
                    {r.field}
                  </div>
                  <div className="flex items-center gap-2">
                    <span
                      className={clsx(
                        "text-sm font-medium",
                        correct ? "text-white" : "text-rose-200"
                      )}
                    >
                      {r.value}
                    </span>
                    {correct ? (
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                    ) : (
                      <AlertOctagon className="h-3.5 w-3.5 text-rose-400" />
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-white/10">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${r.confidence * 100}%` }}
                        transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
                        className="h-full rounded-full bg-gradient-to-r from-cyan-400 via-violet-400 to-pink-400"
                      />
                    </div>
                    <span className="mono text-[11px] tabular-nums text-white/65">
                      {r.confidence.toFixed(2)}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="relative flex flex-col justify-between">
          <div>
            <div className="mono text-[10px] uppercase tracking-[0.22em] text-white/45">
              Episode score
            </div>
            <div className="mt-1 flex items-baseline gap-3">
              <motion.div
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.7, delay: 0.4 }}
                className="font-display text-7xl font-bold tracking-tight text-white"
              >
                {step.score.toFixed(2)}
              </motion.div>
              <div className="mono text-sm text-white/55">/ 1.00</div>
            </div>
            <div className="mt-2 text-xs text-white/55">
              Composite of the rubric weights, on the trained agent.
            </div>
          </div>

          <ul className="mt-6 space-y-2">
            {Object.entries(step.breakdown).map(([k, v]) => (
              <li
                key={k}
                className="flex items-center justify-between gap-3 rounded-lg border border-white/10 bg-white/[0.02] px-3 py-2"
              >
                <span className="mono text-[11px] uppercase tracking-[0.18em] text-white/55">
                  {k.replaceAll("_", " ")}
                </span>
                <div className="flex flex-1 items-center gap-3">
                  <div className="h-1 flex-1 overflow-hidden rounded-full bg-white/10">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${(v as number) * 100}%` }}
                      transition={{ duration: 1, delay: 0.4 }}
                      className={clsx(
                        "h-full rounded-full",
                        k === "cascade_penalty"
                          ? "bg-rose-400"
                          : "bg-gradient-to-r from-cyan-400 to-violet-400"
                      )}
                    />
                  </div>
                  <span className="mono w-10 text-right text-[11px] tabular-nums text-white/75">
                    {(v as number).toFixed(2)}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </motion.div>
  );
}
