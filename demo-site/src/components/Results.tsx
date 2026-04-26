import { motion } from "framer-motion";
import { BASELINES, TASKS, TRAINED } from "../data";
import { Section } from "./Section";

const POLICIES = [
  { id: "random", label: "random", color: "#475569" },
  { id: "wait", label: "wait", color: "#64748b" },
  { id: "naive_editor", label: "naive_editor", color: "#22d3ee" },
  { id: "naive_relay", label: "naive_relay", color: "#fb7185" },
  { id: "trained", label: "trained", color: "#a78bfa" },
] as const;

export function Results() {
  const showTasks = TASKS.filter((t) => t.id !== "t6");

  return (
    <Section
      id="results"
      eyebrow="Measured baselines"
      title={
        <>
          Real numbers, real gaps.{" "}
          <span className="gradient-text">8 seeds · per task · per policy.</span>
        </>
      }
      subtitle={
        <>
          The interesting baseline is{" "}
          <span className="mono text-white/85">naive_relay</span> — an "always
          forward at conf 0.85" agent. It nails the easy tasks and{" "}
          <span className="text-rose-200">collapses to 0.08 on Cascade Chain</span>{" "}
          because it confidently propagates the upstream lie.
        </>
      }
    >
      {/* legend */}
      <div className="mb-6 flex flex-wrap items-center gap-3 text-xs">
        {POLICIES.map((p) => (
          <div
            key={p.id}
            className="flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5"
          >
            <span
              className="h-2.5 w-2.5 rounded-full"
              style={{
                background: p.color,
                boxShadow: `0 0 10px ${p.color}aa`,
              }}
            />
            <span className="mono text-white/80">{p.label}</span>
          </div>
        ))}
      </div>

      <div className="panel relative overflow-hidden p-6 md:p-8">
        <div className="pointer-events-none absolute -right-32 -top-24 h-72 w-72 rounded-full bg-violet-500/15 blur-3xl" />

        <div className="grid gap-7">
          {showTasks.map((t, ti) => {
            const values: Record<string, number> = {
              random: BASELINES.random[t.id] ?? 0,
              wait: BASELINES.wait[t.id] ?? 0,
              naive_editor: BASELINES.naive_editor[t.id] ?? 0,
              naive_relay: BASELINES.naive_relay[t.id] ?? 0,
              trained: TRAINED[t.id] ?? 0,
            };
            const bestNonTrained = Math.max(
              values.random,
              values.wait,
              values.naive_editor,
              values.naive_relay
            );
            const trainedDelta = values.trained - bestNonTrained;
            return (
              <motion.div
                key={t.id}
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-10% 0%" }}
                transition={{ duration: 0.6, delay: ti * 0.07 }}
                className="grid grid-cols-1 gap-4 border-b border-white/[0.06] pb-6 last:border-b-0 last:pb-0 md:grid-cols-[200px_1fr_120px] md:items-center"
              >
                <div>
                  <div className="mono text-[10px] uppercase tracking-[0.22em] text-white/40">
                    {t.id} · {t.difficulty}
                  </div>
                  <div className="mt-1 font-display text-lg font-semibold tracking-tight text-white">
                    {t.name}
                  </div>
                </div>

                <div className="grid gap-1.5">
                  {POLICIES.map((p) => {
                    const v = values[p.id];
                    return (
                      <div
                        key={p.id}
                        className="grid grid-cols-[110px_1fr_44px] items-center gap-3"
                      >
                        <div className="mono text-[11px] text-white/55">
                          {p.label}
                        </div>
                        <div className="relative h-2.5 overflow-hidden rounded-full bg-white/[0.04]">
                          <motion.div
                            initial={{ width: 0 }}
                            whileInView={{ width: `${v * 100}%` }}
                            viewport={{ once: true, margin: "-10% 0%" }}
                            transition={{
                              duration: 1.2,
                              delay: 0.2 + ti * 0.05,
                              ease: [0.22, 1, 0.36, 1],
                            }}
                            className="absolute inset-y-0 left-0 rounded-full"
                            style={{
                              background:
                                p.id === "trained"
                                  ? "linear-gradient(90deg,#22d3ee,#a78bfa,#f472b6)"
                                  : p.color,
                              boxShadow:
                                p.id === "trained"
                                  ? "0 0 18px rgba(167,139,250,0.55)"
                                  : "none",
                            }}
                          />
                        </div>
                        <div
                          className={`mono justify-self-end text-[12px] tabular-nums ${
                            p.id === "trained" ? "text-white" : "text-white/65"
                          }`}
                        >
                          {v.toFixed(2)}
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className="md:justify-self-end md:text-right">
                  <div className="mono text-[10px] uppercase tracking-[0.18em] text-white/35">
                    Δ vs best baseline
                  </div>
                  <div
                    className={`mt-1 mono text-2xl font-semibold tabular-nums ${
                      trainedDelta >= 0 ? "text-emerald-300" : "text-rose-300"
                    }`}
                  >
                    {trainedDelta >= 0 ? "+" : ""}
                    {trainedDelta.toFixed(2)}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* cascade resistance highlight */}
      <div className="mt-10 grid gap-6 md:grid-cols-2">
        <motion.div
          initial={{ opacity: 0, x: -16 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
          className="panel relative overflow-hidden p-7"
        >
          <div className="pointer-events-none absolute -left-20 -bottom-20 h-60 w-60 rounded-full bg-rose-500/15 blur-3xl" />
          <div className="mono text-[10px] uppercase tracking-[0.22em] text-rose-300/80">
            cascade resistance · t4
          </div>
          <h3 className="mt-2 font-display text-3xl font-semibold tracking-tight text-white">
            Naive relay forwards the lie at <span className="text-rose-300">conf 0.85</span>.
            <br />
            Trained relay learns to <span className="gradient-text">refuse.</span>
          </h3>
          <div className="mt-6 grid grid-cols-2 gap-4">
            <CascadeBar label="naive_relay" frac={1.0} color="#fb7185" />
            <CascadeBar label="trained" frac={0.04} color="#a3e635" />
          </div>
          <p className="mt-5 text-sm text-white/55">
            Fraction of episodes where the agent forwarded a false claim with
            confidence &gt; 0.5. Lower is better.
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 16 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
          className="panel relative overflow-hidden p-7"
        >
          <div className="pointer-events-none absolute -right-20 -top-20 h-60 w-60 rounded-full bg-cyan-500/15 blur-3xl" />
          <div className="mono text-[10px] uppercase tracking-[0.22em] text-cyan-300/80">
            three-stage curriculum
          </div>
          <h3 className="mt-2 font-display text-3xl font-semibold tracking-tight text-white">
            t1 → t1+t2 → full mix.
          </h3>
          <p className="mt-3 text-sm leading-relaxed text-white/65">
            The A6000 trainer uses a dense multi-component reward (format +
            tool-legality + neighbour-validity + per-step shaping + 1.5×
            terminal score) to keep GRPO advantages non-zero on the harder
            tasks where raw [0,1] terminal-only collapses.
          </p>
          <div className="mt-5 grid grid-cols-3 gap-3 mono text-xs">
            {[
              { k: "Stage 1", v: "t1 only · learn relay" },
              { k: "Stage 2", v: "t1+t2 · learn calibrate" },
              { k: "Stage 3", v: "full mix · learn refuse" },
            ].map((s) => (
              <div
                key={s.k}
                className="rounded-lg border border-white/[0.07] bg-white/[0.02] p-3"
              >
                <div className="text-white/50">{s.k}</div>
                <div className="mt-1 text-white">{s.v}</div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </Section>
  );
}

function CascadeBar({
  label,
  frac,
  color,
}: {
  label: string;
  frac: number;
  color: string;
}) {
  return (
    <div className="rounded-xl border border-white/[0.07] bg-white/[0.02] p-4">
      <div className="mono text-[10px] uppercase tracking-[0.22em] text-white/45">
        {label}
      </div>
      <div className="mt-2 flex items-baseline gap-2">
        <div
          className="font-display text-4xl font-semibold tracking-tight"
          style={{ color }}
        >
          {(frac * 100).toFixed(0)}%
        </div>
        <span className="text-xs text-white/45">cascaded</span>
      </div>
      <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/10">
        <motion.div
          initial={{ width: 0 }}
          whileInView={{ width: `${frac * 100}%` }}
          viewport={{ once: true }}
          transition={{ duration: 1.2 }}
          className="h-full"
          style={{
            background: color,
            boxShadow: `0 0 12px ${color}aa`,
          }}
        />
      </div>
    </div>
  );
}
