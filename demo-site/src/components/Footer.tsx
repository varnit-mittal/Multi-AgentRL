import { motion } from "framer-motion";
import { ArrowRight, Code2 } from "lucide-react";
import { Section } from "./Section";

export function Footer() {
  return (
    <Section id="cta" className="pb-40">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
        className="relative overflow-hidden rounded-3xl border border-white/10 bg-gradient-to-br from-violet-500/[0.08] via-pink-500/[0.05] to-cyan-500/[0.08] p-14 text-center backdrop-blur-2xl"
      >
        <div className="pointer-events-none absolute -left-20 -top-20 h-72 w-72 rounded-full bg-cyan-500/20 blur-3xl" />
        <div className="pointer-events-none absolute -right-20 -bottom-20 h-72 w-72 rounded-full bg-pink-500/20 blur-3xl" />

        <div className="pill mx-auto mb-6">OpenEnv RFC-003 · ready</div>
        <h2 className="font-display text-4xl font-semibold leading-[1.05] tracking-[-0.02em] text-white md:text-6xl">
          Train an LLM to be the <span className="gradient-text">honest node</span>
          <br />
          inside a noisy network.
        </h2>
        <p className="mx-auto mt-5 max-w-2xl text-base leading-relaxed text-white/60 md:text-lg">
          Whispers ships as a single Hugging Face Space. Spin up the env, point
          a TRL trainer at it, watch a 3B Qwen learn to refuse cascades, accuse
          adversaries, and publish calibrated.
        </p>

        <div className="mt-10 flex flex-wrap items-center justify-center gap-3">
          <a
            href="#"
            className="group inline-flex items-center gap-2 rounded-full bg-white px-6 py-3 text-sm font-semibold text-black transition hover:bg-white/90"
          >
            Try the HF Space
            <ArrowRight className="h-4 w-4 transition group-hover:translate-x-0.5" />
          </a>
          <a
            href="#"
            className="inline-flex items-center gap-2 rounded-full border border-white/15 bg-white/[0.04] px-6 py-3 text-sm font-semibold text-white/85 backdrop-blur transition hover:bg-white/[0.07]"
          >
            <Code2 className="h-4 w-4" /> Read the source
          </a>
          <a
            href="#"
            className="inline-flex items-center gap-2 rounded-full px-4 py-3 text-sm text-white/55 transition hover:text-white"
          >
            Open the training notebook ↗
          </a>
        </div>
      </motion.div>

      <div className="mt-16 grid grid-cols-1 items-center justify-between gap-4 border-t border-white/[0.06] pt-8 text-xs text-white/40 md:grid-cols-3">
        <div>© 2026 Whispers · Apache 2.0</div>
        <div className="mono text-center md:text-center">
          OpenEnv 0.2.3 · Pydantic · FastAPI · Unsloth + TRL GRPO
        </div>
        <div className="md:text-right">
          <span className="mono">made for the openenv hackathon</span>
        </div>
      </div>
    </Section>
  );
}
