import { motion } from "framer-motion";
import { FAKE_HEADLINES, STATS } from "../data";
import { Section } from "./Section";

export function Problem() {
  return (
    <Section
      id="problem"
      eyebrow="The problem"
      title={
        <>
          LLMs are{" "}
          <span className="gradient-text">brilliant talkers</span>, terrible
          witnesses.
        </>
      }
      subtitle={
        <>
          Drop a frontier model into a noisy graph of competing claims and it
          becomes a confident megaphone for whatever it heard last. Cascades
          form. Confidences inflate. The wrong story wins.
        </>
      }
    >
      <div className="relative mt-4 grid gap-10 lg:grid-cols-[1.1fr_0.9fr]">
        {/* falling headlines column */}
        <div className="relative h-[460px] overflow-hidden rounded-2xl border border-white/10 bg-[#08080d]/70 backdrop-blur">
          <div className="pointer-events-none absolute inset-0 z-10 bg-[radial-gradient(ellipse_at_center,transparent_30%,#08080d_85%)]" />
          <div className="absolute inset-0 z-0">
            {FAKE_HEADLINES.map((h, i) => (
              <motion.div
                key={h}
                initial={{ y: -50 - (i % 4) * 60, opacity: 0 }}
                animate={{ y: 540, opacity: [0, 1, 1, 0] }}
                transition={{
                  duration: 14 + (i % 5) * 2,
                  delay: i * 0.6,
                  repeat: Infinity,
                  ease: "linear",
                }}
                style={{
                  left: `${(i * 53) % 90}%`,
                }}
                className="absolute whitespace-nowrap"
              >
                <span className="rounded-md border border-rose-400/20 bg-rose-500/[0.06] px-3 py-1.5 mono text-[11px] tracking-wide text-rose-200/70">
                  ▲ {h}
                </span>
              </motion.div>
            ))}
          </div>

          {/* center label */}
          <div className="absolute inset-0 z-20 flex items-center justify-center">
            <div className="rounded-full border border-white/10 bg-black/60 px-5 py-2 mono text-[11px] uppercase tracking-[0.3em] text-white/60 backdrop-blur">
              the feed · 24/7
            </div>
          </div>
        </div>

        {/* stats column */}
        <div className="grid grid-cols-1 gap-4">
          {STATS.map((s, i) => (
            <motion.div
              key={s.cite}
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true, margin: "-20% 0%" }}
              transition={{ duration: 0.6, delay: i * 0.1 }}
              className="panel relative overflow-hidden p-7"
            >
              <div className="pointer-events-none absolute -right-20 -top-20 h-48 w-48 rounded-full bg-violet-500/10 blur-3xl" />
              <div className="font-display text-5xl font-semibold leading-none tracking-tight text-white">
                {s.big}
              </div>
              <div className="mt-3 max-w-md text-base leading-relaxed text-white/65">
                {s.label}
              </div>
              <div className="mt-4 mono text-[11px] uppercase tracking-[0.18em] text-white/35">
                — {s.cite}
              </div>
            </motion.div>
          ))}
          <div className="mt-2 text-sm leading-relaxed text-white/45">
            What's missing isn't a bigger model. It's an{" "}
            <span className="text-white/75">environment</span> that pays the
            agent to verify, calibrate, refuse, and accuse — and an{" "}
            <span className="text-white/75">RL signal</span> calibrated like a
            newsroom, not a leaderboard.
          </div>
        </div>
      </div>
    </Section>
  );
}
