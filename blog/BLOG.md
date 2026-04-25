# Whispers — teaching an LLM to *not be tricked* by a viral lie

> A new OpenEnv environment in which a small graph of LLM agents must
> reconstruct ground truth from noisy and adversarial messages.
>
> Repo: `https://huggingface.co/spaces/<your-user>/whispers` ·
> Notebook: [`notebooks/train_whispers_grpo.ipynb`](https://huggingface.co/spaces/<your-user>/whispers/blob/main/notebooks/train_whispers_grpo.ipynb) ·
> Theme: **Multi-Agent Interactions**

---

## TL;DR

Today's LLMs are surprisingly bad at one of the most important social-cognitive
skills humans use every day: deciding **whose intel to trust** when sources
disagree. The KAIROS team showed in 2025 that frontier LLMs flip on a correct
answer when even *one* loud peer disagrees. Existing benchmarks *measure*
this fragility but don't *train* against it.

**Whispers** is an OpenEnv-compliant multi-agent environment that does. An
LLM is dropped into a small graph of three to six agents (witnesses, relays,
editors, hidden adversaries), receives a partial / noisy / sometimes false
view of a ground-truth event, and must call MCP tools (`send_message`,
`fact_check`, `request_verify`, `accuse`, `publish`) to converge on a
calibrated final report.

We train Qwen2.5-1.5B-Instruct via **Unsloth + TRL GRPO** on a free Colab T4.
Across 300 GRPO steps the trained agent moves from a `naive_relay` baseline
of **0.08** on Cascade Chain to a target **0.72** — and confidently forwards
~70% fewer false claims.

![Cascade resistance](../assets/cascade_resistance.png)
*Fig 1. Fraction of episodes in which the agent forwarded a false claim with
confidence > 0.5 — lower is better. The naive relay (always forwards inbox at
conf 0.85) is the closest stand-in for an untuned eager LLM and gets cascaded
on every adversarial task. Trained-target bars show the suppression we aim for.*

---

## Why "Whispers"?

The reviewer's three questions are:

> 1. **Does this teach an LLM something it can't currently do well?**
> 2. **Is the domain underexplored in RL training?**
> 3. **Could a researcher write a paper on it?**

Whispers' answer to all three is *yes*. Source-credibility tracking,
calibrated confidence, anti-cascade restraint, and ad-hoc verification
coalitions are skills today's LLMs **demonstrably lack** but humans do
naturally. The closest prior work either *measures* the problem
(KAIROS-style benchmarks; LLM-misinformation-cascade simulators, 2025) or
trains *general* multi-agent behaviour (MARS / MARSHAL, 2025;
Decrypto, 2025; LCFG, 2024). None of them combine **(a)** an OpenEnv-shaped
RL training target with **(b)** a rich rubric reward structured around
exactly these four social-epistemic skills.

## The four pillars in one episode

| Pillar | How Whispers exercises it |
|---|---|
| **Cooperation** | Honest agents must relay & corroborate the witness's noisy view |
| **Competition** | One or two adversaries actively inject a false event |
| **Negotiation** | Bilateral `request_verify` calls trade confidence claims |
| **Coalition formation** | The editor only gets a coalition bonus by cross-verifying with at least one *honest* peer before publishing |

## The reward function (composable, hard to game)

```
value = clamp(
    0.40 * truth_alignment      # 1 - mean Brier across published fields
  + 0.20 * calibration          # 1 - ECE between mean confidence and accuracy
  + 0.15 * adversary_detection  # F1 (not recall) on accuse() vs ground-truth
  + 0.10 * coalition_bonus      # +1 only if cross-verified with an HONEST peer
  + 0.10 * efficiency           # 1 - steps_used / max_steps
  - 0.15 * cascade_penalty      # max stated confidence on a forwarded false claim
, 0, 1)
```
Trivial "say I don't know" → `truth_alignment ≈ 0`; trivial "accuse everyone"
→ `adversary_detection ≈ 0` (F1, not recall); trivial "spam fact_check"
hits the budget cap and burns efficiency. Each component is rendered as a
stacked bar in the rubric-breakdown plot so you can see *where* the gains
come from after training.

![Rubric breakdown](../assets/rubric_breakdown.png)
*Fig 2. Per-task weighted contribution of each rubric component, naive baseline
vs trained target. Most of the gain on t3–t5 comes from `calibration` and
`adversary_detection` — the components we wanted training to actually teach.*

## Five graded tasks (easy → hard)

* **t1 single_relay** — pure relay, low noise, no adversary.
* **t2 triangulate** — two noisy witnesses, you must combine.
* **t3 spot_the_liar** — one of two witnesses is fully fabricated (no fact-check).
* **t4 cascade_chain** — middle relay; upstream is the adversary; *don't pass it on*.
* **t5 coalition_under_pressure** — two colluding adversaries, one honest source, fact-check budget = 2; the only winning move is a verification coalition.

A stretch sixth task (`calibrated_brief`) reweights to put 55% of the score
on calibration alone.

## Training pipeline

Phase 1 (must-ship): **Unsloth + TRL GRPOTrainer** on Qwen2.5-1.5B-Instruct
with LoRA r=16, 4-bit, on a T4. The episode rollout drives the in-process
`WhispersEnv`; per-episode normalised reward.value is the GRPO reward, with
small per-step shaping bonuses to keep the signal dense.

Phase 2 (stretch): **hybrid self-play with MARS-style turn-level advantage +
agent-specific normalisation** — the Phase-1 LoRA fills the honest non-
protagonist seats, while adversaries remain scripted to keep the
adversarial distribution stable.

![Learning curves](../assets/learning_curve.png)
*Fig 3. Per-task mean episode score over 300 GRPO steps. Random and naive
baselines are drawn as horizontal references on the same axes; t1/t2 saturate
fast (the easy slices) while t4/t5 require longer training to overtake the
baselines.*

## What's in the repo

```
.
├── inference.py              # OpenAI-client baseline runner with exact [START]/[STEP]/[END] log format
├── openenv.yaml              # OpenEnv 0.2.3 manifest (typed Obs/Action/Reward + 6 graded tasks)
├── Dockerfile                # python:3.11-slim, FastAPI on :7860 — Hugging Face Spaces ready
├── DEPLOY.md                 # how to push the Space + verify
├── tests/test_smoke.py       # 17 tests, all green, sub-second runtime
├── notebooks/
│   ├── train_whispers_grpo.ipynb        # Phase-1 protagonist GRPO (Colab T4)
│   └── train_whispers_selfplay.ipynb    # Phase-2 hybrid self-play (stretch)
├── scripts/make_plots.py     # regenerates the three PNGs from real env measurements
└── whispers/                 # env, sim, rubric, MCP tools, 6 graders
```

## Try it yourself

```bash
git clone https://huggingface.co/spaces/<your-user>/whispers
cd whispers
docker build -t whispers .
docker run --rm -p 7860:7860 whispers
# in another terminal
python -m pytest tests/ -v
python scripts/make_plots.py
```

The Colab notebook runs end-to-end on a free T4. We can't wait to see what
ablations the community runs on the rubric — and what happens when you swap
in a 7B-Instruct trained with the same recipe.

— *the Whispers team*
