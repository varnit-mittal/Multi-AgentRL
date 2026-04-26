---
title: Whispers
emoji: 📡
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
license: apache-2.0
tags:
  - openenv
  - multi-agent
  - reinforcement-learning
  - theory-of-mind
  - misinformation
  - llm
---

# Whispers — Multi-Agent Information Triage for LLMs

> **Theme**: Multi-Agent Interactions (cooperation, competition, negotiation, coalition formation)
> **Stack**: OpenEnv `0.2.3` · Pydantic · FastAPI · Unsloth + TRL GRPO · HF Spaces (Docker)

**Whispers** is a multi-agent text environment in which a small graph of LLM agents must collaboratively reconstruct ground truth from noisy, conflicting, and sometimes adversarial messages — the same problem journalists, OSINT analysts, intelligence officers, and peer-reviewers solve every day.

Each episode, a hidden ground-truth event is leaked to one or two **witnesses** through a noisy channel; **relays** can only see what their neighbours send them; one or two **adversaries** receive a *false* event and try to inject it; an **editor** must publish a final report whose confidences are scored on a Brier rule. The trained agent plays one of these roles. Success requires four interlocking skills the literature shows current LLMs lack: **source-credibility tracking, calibrated confidence, anti-cascade restraint, and ad-hoc verification-coalition formation**.

We frame the task as a *pragmatic-inference game with hidden roles*, building on Bayesian Theory of Mind (Baker et al., 2017), the KAIROS peer-pressure findings (2025), and MARS-style turn-level GRPO (2025). To our knowledge, no prior environment trains an LLM via RL to be a robust node inside such a network using OpenEnv with rubric rewards.

---

## Why Whispers (innovation)

| Pillar | Whispers |
|---|---|
| Cooperation | Honest agents must relay & corroborate facts |
| Competition | Adversaries inject false events for hidden payoffs |
| Negotiation | Bilateral `request_verify` exchanges trade confidence claims |
| Coalition formation | Editors get a bonus for cross-verifying with ≥1 honest peer before publishing |
| Theory of mind | Each agent must infer *what others have seen* and *whether they are honest* from message content + style |

---

## Environment at a glance

```
              ┌────────────┐
              │  Witness   │  noisy view of truth
              └─────┬──────┘
                    │
              ┌─────▼──────┐    ┌─────────────┐
              │   Relay    │◀──▶│ Adversary*  │  injects a false event
              └─────┬──────┘    └─────────────┘
                    │
              ┌─────▼──────┐
              │  Editor    │  must `publish` a calibrated final report
              └────────────┘
```

The agent only ever talks to the env via **MCP-style tools** (per OpenEnv RFC 003); the HTTP `reset / step / state` interface is reserved for the trainer. Other seats are filled by scripted heuristics or a fixed baseline LLM so the protagonist gets a stable curriculum.

### Observation Space — `WhispersObservation`
| Field | Type | Meaning |
|---|---|---|
| `role` | `Literal[witness, relay, editor, adversary]` | The agent's own role (it knows whether it is good or bad) |
| `agent_id` | `int` | Unique node id in the graph |
| `inbox` | `list[Message]` | DMs received this turn |
| `public_feed` | `list[Message]` | Broadcasts visible to every agent |
| `private_facts` | `list[str]` | Witness-only ground-truth fragments (or adversary's planted lies) |
| `network_neighbors` | `list[int]` | Ids reachable via `send_message` / `request_verify` |
| `fact_check_budget` | `int` | Remaining oracle queries (typically 0–2) |
| `step` / `max_steps` | `int` | Turn counter |
| `legal_tools` | `list[str]` | Subset of MCP tools allowed *this* turn (e.g. `publish` only for the editor) |

### Action Space — `WhispersAction`
A discriminated-union: a `tool` field plus optional parameters consumed by the relevant tool.

| Tool | Parameters | Effect |
|---|---|---|
| `send_message` | `target_id`, `content`, `claimed_source`, `confidence` | Direct message to a neighbour |
| `broadcast` | `content`, `claimed_source`, `confidence` | Message visible to all next turn |
| `fact_check` | `content` | Spend 1 budget; oracle returns `{"verdict": true/false}` |
| `request_verify` | `target_id`, `content` | Coalition primitive: ask peer to confirm/deny |
| `accuse` | `target_id` | Public accusation, scored by F1 vs ground-truth adversaries |
| `publish` | `final_report: dict[field, {value, confidence}]` | Editor only; ends episode |
| `wait` | — | Pass turn |

> Reserved tool names `reset`, `step`, `state`, `close` are explicitly forbidden (per OpenEnv RFC 003).

### Reward Function — composable rubric

Episode-level normalised reward in `[0, 1]`:
```
value = clamp(
    0.40 * truth_alignment      # 1 - mean Brier across published fields
  + 0.20 * calibration          # 1 - ECE over confidences
  + 0.15 * adversary_detection  # F1 on accuse() vs ground-truth bad actors
  + 0.10 * coalition_bonus      # +1 if cross-verified with ≥1 honest peer pre-publish
  + 0.10 * efficiency           # 1 - steps_used / max_steps
  - 0.15 * cascade_penalty      # forwarded a false claim with conf > 0.5? grows with conf
, 0, 1)
```

Per-step intermediate signals (returned in `reward.value` after each `step`, weighted into the running episode total):
- `+0.02` — useful `fact_check` against a contested claim
- `+0.05` — `request_verify` answered consistently
- `−0.05` — repeated identical broadcast (anti-spam)
- `−0.10` — `publish` while the inbox has unresolved contradictions and 0 fact-checks used

**Anti-gaming guards.** Trivial "always say I don't know" → `truth_alignment ≈ 0`. Trivial "accuse everyone" → `adversary_detection ≈ 0` (F1, not recall). Trivial "spam fact_check" → budget cap + efficiency burn.

> See the worked example in [`whispers/reward.py`](whispers/reward.py).

### Tasks (5 + 1 stretch)

| ID | Name | Difficulty | Setup | Headline grader signal |
|---|---|---|---|---|
| `t1` | Single Relay | easy | 1 witness → 1 relay → 1 editor (you), no adversary | `truth_alignment` |
| `t2` | Triangulate | easy | 2 noisy witnesses, you (editor) combine | `truth_alignment + calibration` |
| `t3` | Spot the Liar | medium | 2 witnesses; 1 adversarial; no fact-check | `+ adversary_detection` |
| `t4` | Cascade Chain | medium | 5-node line; you = middle relay; upstream = adversary | `+ cascade_penalty` |
| `t5` | Coalition Under Pressure | hard | 6 nodes, 2 colluding adversaries, 1 honest source, you = editor (budget = 2) | full rubric |
| `t6` | Calibrated Brief | hard (stretch) | multi-field event under partial collusion | `calibration` dominates |

---

## Setup

### Run locally (Docker)
```bash
git clone https://huggingface.co/spaces/<your-user>/whispers
cd whispers
docker build -t whispers .
docker run --rm -p 7860:7860 whispers
# Health: curl http://localhost:7860/
# Reset:  curl -X POST http://localhost:7860/reset -H 'Content-Type: application/json' -d '{"task_id":"t1","seed":0}'
```

### Run locally (Python)
```bash
pip install -e .
python -m whispers.server
```

### Validate spec
```bash
pip install openenv-cli  # provides the `openenv` CLI
openenv validate
```
Expected: `OK openenv.yaml is valid`. The captured run output is reproduced in [`assets/openenv_validate.txt`](assets/openenv_validate.txt) after first run.

---

## Inference (baseline)

`inference.py` lives at the repo root and uses the OpenAI client against an HF-hosted endpoint:

```bash
export HF_TOKEN=hf_...
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-7B-Instruct
export WHISPERS_URL=http://localhost:7860
python inference.py            # runs all 6 tasks
WHISPERS_TASK=t3 python inference.py  # run a single task
```

Emits the exact OpenEnv hackathon log format:
```
[START] task=t1 env=whispers model=Qwen/Qwen2.5-7B-Instruct
[STEP] step=0 action=send_message reward=0.05 done=false error=null
...
[END] success=true steps=6 score=0.812 rewards=0.05,0.10,...
```

### Baseline scores (real measurements via `scripts/make_plots.py`)

The numbers below are **measured**, not illustrative — they're the output of running four deterministic policies through the env across 8 seeds each and averaging the per-task `value`. The full per-task / per-policy table is committed in [`assets/baseline_measurements.json`](assets/baseline_measurements.json).

| Task | Difficulty | random | wait | naive_editor | naive_relay | trained (target) |
|---|---|---|---|---|---|---|
| t1 single_relay | easy | 0.58 | 0.00 | **0.87** | 0.88 | 0.92 |
| t2 triangulate | easy | 0.59 | 0.00 | **0.87** | 0.88 | 0.90 |
| t3 spot_the_liar | medium | 0.59 | 0.00 | 0.60 | 0.45 | **0.78** |
| t4 cascade_chain | medium | 0.55 | 0.55 | 0.55 | **0.08** | **0.72** |
| t5 coalition | hard | 0.58 | 0.00 | 0.55 | 0.44 | **0.65** |

The interesting baselines are:

* **`naive_relay`**: an "always forward inbox at conf=0.85" agent — the closest stand-in for an untuned, eager LLM. It scores **0.08 on Cascade Chain** (because it confidently propagates the upstream adversary's lie) and triggers the cascade-resistance plot below.
* **`naive_editor`**: publishes the most-confident inbox claim at the last turn — a strong baseline on the no-adversary tasks but collapses on t3+ where it can't tell signal from noise.

> Run `python scripts/make_plots.py` to reproduce all four baselines + the three plots end-to-end in ~20 s on CPU. To run a real LLM baseline against the live HF Space, use `python inference.py`.

---

## Training (Unsloth + TRL GRPO)

Three entry points, pick the one that matches your hardware:

| Hardware | Entry point | Model |
|---|---|---|
| Free Colab T4 | [`notebooks/train_whispers_grpo.ipynb`](notebooks/train_whispers_grpo.ipynb) | Qwen2.5-1.5B-Instruct |
| Free Kaggle 1×T4 | [`notebooks/train_whispers_grpo_kaggle_t4.ipynb`](notebooks/train_whispers_grpo_kaggle_t4.ipynb) | Qwen2.5-1.5B-Instruct |
| **Workstation RTX A6000 (48 GB)** | [`scripts/train_grpo_a6000.py`](scripts/train_grpo_a6000.py) | **Qwen2.5-3B-Instruct** |

All three:

1. Spin up `WhispersEnv` in-process (no HTTP overhead in the hot loop).
2. Load Qwen in 4-bit via `unsloth.FastLanguageModel`, apply LoRA.
3. Drive `trl.GRPOTrainer` with a rollout that calls `env.step()` for up to `max_steps`.
4. Log to WandB; save curves to `assets/`.

The **A6000 script** is the production trainer: it uses a **dense multi-component reward** (format + tool-legality + neighbour-validity + per-step shaping + 1.5× terminal score, max ≈ 2.25) and a **three-stage curriculum** (t1 → t1+t2 → full mix). On the T4 notebooks the raw `[0, 1]` terminal-only reward collapses to ~0 for an untrained 1.5B policy and produces zero GRPO advantages — that's why the A6000 path moves to a 3B base model and a denser signal. Run it with::

    python scripts/train_grpo_a6000.py
    # or override knobs via env vars:
    WHISPERS_MODEL=Qwen/Qwen2.5-7B-Instruct GRPO_STEPS=1000 \
        python scripts/train_grpo_a6000.py

**Phase 2 (stretch)** — hybrid self-play with **MARS-style turn-level advantage** + **agent-specific advantage normalisation**, freezing adversaries to scripted lies.

### Headline plots (regenerated by the notebook)

![Learning curves](assets/learning_curve.png)

*Mean episode reward vs GRPO step, one line per task; dashed lines are the random and untrained-Qwen baselines.*

![Cascade resistance](assets/cascade_resistance.png)

*Fraction of episodes where the agent forwarded a false claim with confidence > 0.5. Lower is better.*

![Rubric breakdown](assets/rubric_breakdown.png)

*Where the gains come from: stacked rubric components, baseline vs trained.*

> WandB run: see `notebooks/train_whispers_grpo.ipynb` output cell.

---

## Project layout
```
.
├── inference.py              # mandatory baseline runner (OpenAI client, exact log format)
├── openenv.yaml              # OpenEnv manifest
├── Dockerfile
├── requirements.txt
├── pyproject.toml
├── README.md                 # this file
├── tests/test_smoke.py
├── notebooks/train_whispers_grpo.ipynb
├── assets/                   # plots committed to repo
└── whispers/
    ├── __init__.py
    ├── models.py             # Pydantic Observation / Action / Reward / State
    ├── env.py                # WhispersEnv core (gym-style API)
    ├── server.py             # FastAPI HTTP server (reset / step / state)
    ├── client.py             # WhispersClient HTTP wrapper
    ├── tools.py              # MCP tool dispatch (send_message, fact_check, ...)
    ├── sim.py                # graph, noise model, scripted baseline policies
    ├── reward.py             # composable rubric + per-step shaping
    └── tasks/                # one file per task + grader
        ├── single_relay.py
        ├── triangulate.py
        ├── spot_the_liar.py
        ├── cascade_chain.py
        ├── coalition_under_pressure.py
        └── calibrated_brief.py
```

---

## Citation
If you use Whispers, please cite:

```
@software{whispers2026,
  title  = {Whispers: A Multi-Agent Information-Triage Environment for LLM RL},
  author = {Whispers Team},
  year   = {2026},
  url    = {https://huggingface.co/spaces/<your-user>/whispers}
}
```

Background reading: Baker et al. *Rational quantitative attribution of beliefs, desires and percepts* (2017); KAIROS — *LLMs Can't Handle Peer Pressure* (2025); MARS / MARSHAL — *Reinforcing Multi-Agent Reasoning of LLMs through Self-Play* (2025); Decrypto (2025); LCFG — *LLM Coalition Formation Game* (2024).