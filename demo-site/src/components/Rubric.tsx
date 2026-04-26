import { motion } from "framer-motion";
import { RUBRIC } from "../data";
import { Section } from "./Section";

export function Rubric() {
  const total = RUBRIC.reduce(
    (acc, r) => (r.sign === "+" ? acc + r.weight : acc),
    0
  );
  return (
    <Section
      id="rubric"
      eyebrow="Reward · rubric"
      title={
        <>
          A reward function that{" "}
          <span className="gradient-text">scores like a newsroom.</span>
        </>
      }
      subtitle={
        <>
          Six composable components, calibrated by a Brier rule on the editor's
          published fields and capped to <span className="mono">[0,1]</span>.
          Trivial gaming strategies score zero by construction.
        </>
      }
    >
      <div className="grid gap-6 lg:grid-cols-[1fr_1.1fr]">
        {/* equation card */}
        <div className="panel relative overflow-hidden p-7">
          <div className="pointer-events-none absolute -right-20 -top-20 h-60 w-60 rounded-full bg-violet-500/15 blur-3xl" />
          <div className="mono text-[10px] uppercase tracking-[0.22em] text-white/45">
            episode_value =
          </div>
          <div className="mt-3 grid gap-2 mono text-[13px] leading-relaxed">
            {RUBRIC.map((r) => (
              <div
                key={r.id}
                className="flex items-center gap-3 rounded-md border border-white/[0.07] bg-white/[0.02] px-3 py-2"
              >
                <span
                  className="w-7 text-right tabular-nums"
                  style={{ color: r.sign === "+" ? "#a3e635" : "#fb7185" }}
                >
                  {r.sign}
                  {r.weight.toFixed(2)}
                </span>
                <span
                  className="h-2.5 w-2.5 flex-none rounded-full"
                  style={{
                    background: r.color,
                    boxShadow: `0 0 14px ${r.color}aa`,
                  }}
                />
                <span className="text-white/85">{r.id}</span>
              </div>
            ))}
            <div className="mt-2 rounded-md border border-white/10 bg-black/40 px-3 py-2 text-white/65">
              clamp(·, 0, 1)
            </div>
          </div>
          <p className="mt-5 text-sm text-white/55">
            Sum of <span className="mono text-white/85">+</span> weights ={" "}
            <span className="mono text-white/85">{total.toFixed(2)}</span>; the
            cascade penalty subtracts up to{" "}
            <span className="mono text-rose-300">0.15</span> proportional to a
            forwarded falsehood's stated confidence.
          </p>
        </div>

        {/* stacked bar of weights */}
        <div className="panel relative overflow-hidden p-7">
          <div className="mono text-[10px] uppercase tracking-[0.22em] text-white/45">
            Weight distribution
          </div>

          <div className="mt-5 flex h-12 w-full overflow-hidden rounded-full border border-white/10">
            {RUBRIC.filter((r) => r.sign === "+").map((r, i) => (
              <motion.div
                key={r.id}
                initial={{ width: 0 }}
                whileInView={{ width: `${(r.weight / total) * 100}%` }}
                viewport={{ once: true, margin: "-15% 0%" }}
                transition={{ duration: 1, delay: i * 0.07 }}
                className="relative h-full"
                style={{ background: r.color }}
              >
                <div className="absolute inset-0 bg-gradient-to-b from-white/20 via-transparent to-black/20" />
              </motion.div>
            ))}
          </div>

          <ul className="mt-6 grid gap-3">
            {RUBRIC.map((r, i) => (
              <motion.li
                key={r.id}
                initial={{ opacity: 0, x: 12 }}
                whileInView={{ opacity: 1, x: 0 }}
                viewport={{ once: true, margin: "-15% 0%" }}
                transition={{ duration: 0.5, delay: i * 0.06 }}
                className="grid grid-cols-[20px_1fr_72px] items-center gap-4 border-t border-white/[0.06] pt-3 text-sm"
              >
                <span
                  className="h-3 w-3 rounded-sm"
                  style={{
                    background: r.color,
                    boxShadow: `0 0 12px ${r.color}80`,
                  }}
                />
                <div>
                  <div className="text-white">
                    {r.name}{" "}
                    <span className="mono ml-1 text-[10px] text-white/40">
                      {r.sign}
                      {r.weight.toFixed(2)}
                    </span>
                  </div>
                  <div className="mt-0.5 text-xs leading-snug text-white/55">
                    {r.blurb}
                  </div>
                </div>
                <div
                  className={`mono justify-self-end text-[11px] uppercase tracking-[0.18em] ${
                    r.sign === "+" ? "text-emerald-300/80" : "text-rose-300/80"
                  }`}
                >
                  {r.sign === "+" ? "reward" : "penalty"}
                </div>
              </motion.li>
            ))}
          </ul>
        </div>
      </div>

      {/* anti-gaming guards */}
      <div className="mt-10 grid gap-4 md:grid-cols-3">
        {[
          {
            label: "Always say I don't know",
            score: "→ 0.00 truth alignment",
            tone: "violet",
          },
          {
            label: "Accuse everyone",
            score: "→ 0.00 detection F1",
            tone: "pink",
          },
          {
            label: "Spam fact_check",
            score: "→ budget capped, efficiency burned",
            tone: "cyan",
          },
        ].map((g, i) => (
          <motion.div
            key={g.label}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-10% 0%" }}
            transition={{ duration: 0.6, delay: i * 0.1 }}
            className="rounded-xl border border-white/10 bg-white/[0.02] p-5 text-sm backdrop-blur"
          >
            <div className="mono text-[10px] uppercase tracking-[0.22em] text-white/40">
              anti-gaming guard
            </div>
            <div className="mt-2 text-white/85">{g.label}</div>
            <div className="mt-1 mono text-xs text-rose-300/80">{g.score}</div>
          </motion.div>
        ))}
      </div>
    </Section>
  );
}
