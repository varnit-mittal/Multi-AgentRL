"""Whispers — Phase 1 GRPO trainer for **NVIDIA RTX A6000 (48 GB, Ampere)**.

This is the production single-GPU trainer. It is the pure-Python sibling of
``notebooks/train_whispers_grpo*.ipynb`` and is what you should run when you
have a real workstation GPU instead of a Colab/Kaggle T4.

What this script changes vs the T4 notebooks (and *why* the rewards are now
much closer to 1.0):

1. Bigger, more capable base model: ``Qwen/Qwen2.5-3B-Instruct`` (overridable).
   The 1.5B model used by the T4 notebooks rarely emits a valid
   ``WhispersAction`` JSON, so ``_coerce_action`` falls back to ``wait`` and
   the editor never publishes - terminal score ~0.1 forever.

2. **Dense, multi-component reward** instead of just the terminal episode
   score in [0, 1]. Components:

       format_reward          : +0.20  if the completion parses to a valid
                                       ``WhispersAction``.
       legal_tool_reward      : +0.15  if the chosen tool is in ``legal_tools``.
       neighbour_valid_reward : +0.10  if ``target_id`` (when required) is
                                       actually a network neighbour.
       shaping_reward         : sum of per-step shaping bonuses,
                                       clipped to [-0.30, +0.30].
       terminal_score         : 1.50 * episode_score in [0, 1.5].

   So the achievable max is ~2.25. This restores reward variance across the
   GRPO group (the original [0, 1] terminal-only signal collapses to ~0 for
   an untrained policy and produces zero advantages).

3. **Curriculum learning** in three stages: t1 only -> t1+t2 -> full mix.
   The hardest tasks (t4 cascade, t5 coalition) are only introduced after the
   policy can already publish on the easy ones.

4. **Higher diversity**: ``num_generations=8``, ``temperature=0.9`` so the
   GRPO group has real spread - this is what produces non-zero advantages.

5. **bf16** (Ampere native), ``LoRA r=32 alpha=64``, ``max_seq_length=4096``,
   ``per_device_train_batch_size=2``, ``gradient_accumulation_steps=8`` -
   the 48 GB headroom on the A6000 makes all of this practical.

Run::

    python scripts/train_grpo_a6000.py
    # or with custom knobs:
    WHISPERS_MODEL=Qwen/Qwen2.5-7B-Instruct \
    GRPO_STEPS=1000 \
    python scripts/train_grpo_a6000.py

Recommended env vars (all optional):

    WHISPERS_MODEL    HF model id (default: Qwen/Qwen2.5-3B-Instruct)
    GRPO_STEPS        total optimiser steps across all curriculum stages (default 600)
    NUM_GENERATIONS   completions per prompt for GRPO (default 8)
    LEARNING_RATE     LoRA learning rate (default 1e-5)
    KL_BETA           GRPO KL coefficient (default 0.02)
    LORA_RANK         LoRA rank (default 32)
    MAX_SEQ_LEN       prompt + completion budget (default 4096)
    OUTPUT_DIR        where to save the LoRA + tokenizer (default ./ckpt/grpo_a6000)
    WANDB_API_KEY     enables WandB logging if set
    HF_TOKEN          only needed for gated models
"""

from __future__ import annotations

import json
import logging
import os
import random
import sys
import time
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import torch

# Quiet whispers env logger - malformed-action ToolErrors are an *expected*
# part of training (penalised via shaping below). Emitting them spams stderr
# during long GRPO runs, especially in the early "untrained policy" phase.
logging.getLogger("whispers").setLevel(logging.ERROR)
logging.getLogger("whispers.env").setLevel(logging.ERROR)


# ---------------------------------------------------------------------------
# Paths & config
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from whispers.env import WhispersEnv  # noqa: E402
from whispers.models import (  # noqa: E402
    WhispersAction,
    WhispersObservation,
)

# We re-use the inference parser so train-time and eval-time JSON handling are
# identical (no train/test mismatch on what counts as a valid action).
import importlib.util  # noqa: E402

_inf_spec = importlib.util.spec_from_file_location(
    "_whispers_inference_root", str(REPO_ROOT / "inference.py")
)
_inf_mod = importlib.util.module_from_spec(_inf_spec)
sys.modules["_whispers_inference_root"] = _inf_mod
_inf_spec.loader.exec_module(_inf_mod)

BASE_SYSTEM_PROMPT = _inf_mod.SYSTEM_PROMPT
_build_user_prompt = _inf_mod._build_user_prompt
_coerce_action = _inf_mod._coerce_action


# ---------------------------------------------------------------------------
# Hyper-parameters (all overridable via env vars so the script is also handy
# for sweeps - just `for lr in 5e-6 1e-5 3e-5; do LEARNING_RATE=$lr ... ; done`).
# ---------------------------------------------------------------------------


@dataclass
class TrainConfig:
    model_name: str = os.environ.get("WHISPERS_MODEL", "Qwen/Qwen2.5-3B-Instruct")
    max_seq_len: int = int(os.environ.get("MAX_SEQ_LEN", "4096"))
    lora_rank: int = int(os.environ.get("LORA_RANK", "32"))
    lora_alpha: int = int(os.environ.get("LORA_ALPHA", "64"))
    lora_dropout: float = float(os.environ.get("LORA_DROPOUT", "0.0"))

    # Total optimiser steps. The script splits this across three curriculum
    # stages (40% / 30% / 30%) by default - see `CURRICULUM` below.
    total_steps: int = int(os.environ.get("GRPO_STEPS", "600"))
    num_generations: int = int(os.environ.get("NUM_GENERATIONS", "8"))
    per_device_batch_size: int = int(os.environ.get("PER_DEVICE_BATCH_SIZE", "2"))
    grad_accum_steps: int = int(os.environ.get("GRAD_ACCUM_STEPS", "8"))

    learning_rate: float = float(os.environ.get("LEARNING_RATE", "1e-5"))
    kl_beta: float = float(os.environ.get("KL_BETA", "0.02"))
    weight_decay: float = float(os.environ.get("WEIGHT_DECAY", "0.0"))

    # Generation knobs - high temperature is critical for GRPO so the group
    # produces meaningfully different completions (otherwise advantages = 0).
    temperature: float = float(os.environ.get("TEMPERATURE", "0.9"))
    top_p: float = float(os.environ.get("TOP_P", "0.95"))
    max_new_tokens: int = int(os.environ.get("MAX_NEW_TOKENS", "192"))
    max_steps_per_episode: int = int(os.environ.get("MAX_STEPS_PER_EPISODE", "18"))

    output_dir: str = os.environ.get("OUTPUT_DIR", str(REPO_ROOT / "ckpt" / "grpo_a6000"))
    seed: int = int(os.environ.get("SEED", "3407"))
    save_every: int = int(os.environ.get("SAVE_EVERY", "100"))


# Curriculum stages: each entry is (name, fraction_of_total_steps, task_mix).
# Earlier stages are *deliberately easy* so the policy first learns to emit
# valid JSON + a sensible publish, then gradually we add the adversarial /
# coalition tasks. Without this, the gradient signal on t4/t5 in the first
# 100 steps is just noise (untrained model -> wait -> terminal_score ~ 0.1).
CURRICULUM: list[tuple[str, float, list[str]]] = [
    ("warmup_t1",   0.40, ["t1"]),
    ("easy_mix",    0.30, ["t1", "t1", "t2", "t2"]),
    ("full_mix",    0.30, ["t1", "t1", "t2", "t2", "t3", "t4", "t5"]),
]


# ---------------------------------------------------------------------------
# Few-shot examples baked into the system prompt - this is the single biggest
# lever for raising untrained reward. The 3B model produces malformed JSON
# without these; with them, ~80% of first-turn completions parse cleanly.
# ---------------------------------------------------------------------------

FEWSHOT_EXAMPLES = """\
## Examples (study the JSON shape carefully)

Example 1 - editor publishing after triangulating two witnesses:
{"tool":"publish","target_id":null,"content":null,"claimed_source":null,"confidence":null,"final_report":{"location":{"value":"Reactor 7","confidence":0.85},"incident":{"value":"coolant leak","confidence":0.80},"time":{"value":"03:14","confidence":0.75},"casualties":{"value":"0","confidence":0.70}}}

Example 2 - relay forwarding a witness claim to a neighbour:
{"tool":"send_message","target_id":2,"content":"location=Reactor 7 incident=coolant leak time=03:14 casualties=0","claimed_source":"witness","confidence":0.7,"final_report":null}

Example 3 - asking a trusted neighbour to corroborate before publishing:
{"tool":"request_verify","target_id":1,"content":"location=Reactor 7 time=03:14","claimed_source":"editor","confidence":0.6,"final_report":null}

Example 4 - using fact_check (only when fact_check_budget > 0):
{"tool":"fact_check","target_id":null,"content":"location=Reactor 4 incident=fire alarm","claimed_source":null,"confidence":null,"final_report":null}

Example 5 - waiting if you have nothing useful to do this turn:
{"tool":"wait","target_id":null,"content":null,"claimed_source":null,"confidence":null,"final_report":null}
"""

SYSTEM_PROMPT = BASE_SYSTEM_PROMPT.rstrip() + "\n\n" + FEWSHOT_EXAMPLES


# ---------------------------------------------------------------------------
# Reward components - this is where the "reward closer to 1" magic happens.
# We replace the original [0, 1] terminal-only reward with a dense multi-part
# reward that gives the policy partial credit for *each* step of the funnel:
# parse JSON -> pick a legal tool -> pick a valid target -> earn step-shaping
# bonuses -> finally maximise terminal episode_score.
# ---------------------------------------------------------------------------

R_FORMAT_OK = 0.20      # +0.20 if completion JSON parses
R_LEGAL_TOOL = 0.15     # +0.15 if chosen tool is in legal_tools
R_NEIGHBOUR_OK = 0.10   # +0.10 if target_id (when required) is a neighbour
W_TERMINAL = 1.50       # episode_score in [0, 1] is multiplied by this
W_SHAPING_CLIP = 0.30   # |sum_t shaping_t| is clipped here


def _first_action_metadata(
    completion: str, obs: WhispersObservation
) -> tuple[WhispersAction, float]:
    """Return (action, shaping_for_first_action_format).

    The shaping covers only the *parse / legal / neighbour* funnel here -
    real per-step shaping (fact_check_useful etc.) is computed step-by-step
    inside the rollout below.
    """
    action, parse_err = _coerce_action(completion, obs)
    bonus = 0.0
    if parse_err is None:
        bonus += R_FORMAT_OK
    legal = set(obs.legal_tools)
    if action.tool in legal:
        bonus += R_LEGAL_TOOL
    if action.tool in {"send_message", "request_verify"}:
        # These tools require a neighbour target_id; reward only when that
        # target is actually in the adjacency list.
        if action.target_id is not None and action.target_id in obs.network_neighbors:
            bonus += R_NEIGHBOUR_OK
    elif action.tool == "accuse":
        # accuse is legal against any agent_id, so no neighbour check.
        if action.target_id is not None:
            bonus += R_NEIGHBOUR_OK
    elif action.tool in {"broadcast", "fact_check", "wait"}:
        # No target needed - give the bonus so the model isn't penalised for
        # correctly omitting target_id.
        bonus += R_NEIGHBOUR_OK
    elif action.tool == "publish":
        if action.final_report and isinstance(action.final_report, dict):
            bonus += R_NEIGHBOUR_OK
    return action, bonus


def _rollout_episode_with_dense_reward(
    *,
    model,
    tokenizer,
    task_id: str,
    seed: int,
    first_completion: str,
    cfg: TrainConfig,
) -> dict:
    """Run one full episode using ``first_completion`` as the protagonist's
    *first* action; subsequent steps are sampled from the current model in
    eval mode (no grad). Returns the dense-reward + per-component breakdown.
    """
    env = WhispersEnv(task_id=task_id, seed=seed)
    obs = env.reset()
    cap = min(cfg.max_steps_per_episode, obs.max_steps)

    # First action: gradient does *not* flow through this code path (the LLM
    # forward that produced `first_completion` happened inside GRPOTrainer).
    # We just compute the format-funnel bonus and step the env.
    action, format_bonus = _first_action_metadata(first_completion, obs)
    shaping_total = 0.0
    try:
        obs, r, done, info = env.step(action)
        shaping_total += float(info.get("shaping_breakdown", {}).get("total", 0.0))
    except RuntimeError:
        done = True

    # Remaining steps: sample greedily-ish from the current model in eval
    # mode. We deliberately use a lower temperature here so the *credit
    # assignment* of the first action isn't drowned out by very noisy later
    # rollouts.
    model.eval()
    try:
        for _ in range(cap - 1):
            if done:
                break
            user = _build_user_prompt(obs)
            prompt = SYSTEM_PROMPT + "\n\n" + user
            inputs = tokenizer(
                prompt, return_tensors="pt", truncation=True, max_length=cfg.max_seq_len
            ).to(model.device)
            with torch.no_grad():
                out_ids = model.generate(
                    **inputs,
                    max_new_tokens=cfg.max_new_tokens,
                    do_sample=True,
                    temperature=0.5,
                    top_p=0.9,
                    pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
                )
            raw_next = tokenizer.decode(
                out_ids[0][inputs.input_ids.shape[-1]:], skip_special_tokens=True
            )
            act_next, _ = _coerce_action(raw_next, obs)
            try:
                obs, r, done, info = env.step(act_next)
            except RuntimeError:
                break
            shaping_total += float(info.get("shaping_breakdown", {}).get("total", 0.0))
    finally:
        model.train()

    grade = env.grade_terminal()
    terminal_score = float(grade["value"])

    shaping_clipped = max(-W_SHAPING_CLIP, min(W_SHAPING_CLIP, shaping_total))
    dense_reward = (
        format_bonus
        + shaping_clipped
        + W_TERMINAL * terminal_score
    )
    return {
        "dense_reward": float(dense_reward),
        "format_bonus": float(format_bonus),
        "shaping_total": float(shaping_total),
        "terminal_score": float(terminal_score),
        "grade": grade,
    }


# ---------------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------------


def _setup_model(cfg: TrainConfig):
    """Load Qwen via Unsloth in 4-bit + attach LoRA. We use bf16 because the
    A6000 is Ampere; ``dtype=None`` lets Unsloth autodetect it."""
    from unsloth import FastLanguageModel

    print(f"[setup] loading {cfg.model_name} in 4-bit + bf16 (A6000)...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        cfg.model_name,
        max_seq_length=cfg.max_seq_len,
        load_in_4bit=True,
        dtype=None,
    )
    model = FastLanguageModel.get_peft_model(
        model,
        r=cfg.lora_rank,
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
        lora_alpha=cfg.lora_alpha,
        lora_dropout=cfg.lora_dropout,
        bias="none",
        use_gradient_checkpointing="unsloth",
        random_state=cfg.seed,
    )
    model.generation_config.max_length = None
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model.generation_config.pad_token_id = tokenizer.pad_token_id

    import transformers
    transformers.utils.logging.set_verbosity_error()

    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    print(
        f"[setup] OK  trainable={trainable / 1e6:.2f}M / total={total / 1e6:.0f}M  "
        f"device={next(model.parameters()).device}"
    )
    return model, tokenizer


def _setup_wandb(cfg: TrainConfig) -> bool:
    if not os.environ.get("WANDB_API_KEY"):
        print("[wandb] WANDB_API_KEY not set; cloud logging disabled.")
        return False
    try:
        import wandb
        wandb.login(key=os.environ["WANDB_API_KEY"])
        wandb.init(
            project=os.environ.get("WANDB_PROJECT", "whispers-openenv"),
            name=os.environ.get("WANDB_RUN_NAME", "phase1-grpo-a6000"),
            config=cfg.__dict__,
        )
        return True
    except Exception as exc:  # noqa: BLE001
        print(f"[wandb] disabled (init failed: {type(exc).__name__}: {exc})")
        return False


def _build_prompt_dataset(task_mix: list[str], n: int, base_seed: int):
    """Tiny in-memory torch dataset of (prompt, task_id, seed) rows."""
    from torch.utils.data import Dataset

    class WhispersPromptDataset(Dataset):
        def __init__(self):
            self.rows: list[dict[str, Any]] = []
            for i in range(n):
                tid = task_mix[i % len(task_mix)]
                seed = base_seed + i
                env_i = WhispersEnv(task_id=tid, seed=seed)
                obs = env_i.reset()
                self.rows.append({
                    "prompt": SYSTEM_PROMPT + "\n\n" + _build_user_prompt(obs),
                    "task_id": tid,
                    "seed": seed,
                })

        def __len__(self):
            return len(self.rows)

        def __getitem__(self, i):
            return self.rows[i]

    return WhispersPromptDataset()


def _patch_unsloth_grpo_signature():
    """Older transformers expect ``_get_train_sampler(self)`` while newer
    versions call ``_get_train_sampler(self, dataset)``. Unsloth's compiled
    cache regenerates the trainer subclass against whatever transformers was
    installed when it was last built; if pins drift, we get cryptic
    ``TypeError: takes 1 positional argument but 2 were given``. We patch it
    defensively here so the script is robust across reinstalls.
    """
    try:
        import inspect
        patched = 0
        for name in ("UnslothGRPOTrainer", "_UnslothGRPOTrainer"):
            try:
                mod_path = f"unsloth_compiled_cache.{name}"
                mod = __import__(mod_path, fromlist=[name])
                cls = getattr(mod, name, None)
                if cls is None:
                    continue
                orig = cls._get_train_sampler
                params = list(inspect.signature(orig).parameters)
                if len(params) == 1:
                    def _wrapped(self, dataset=None, _orig=orig):
                        return _orig(self)
                    cls._get_train_sampler = _wrapped
                    patched += 1
            except Exception:
                pass
        if patched:
            print(f"[setup] patched _get_train_sampler signature on {patched} class(es)")
    except Exception:
        pass


def main() -> int:
    cfg = TrainConfig()
    random.seed(cfg.seed)
    np.random.seed(cfg.seed)
    torch.manual_seed(cfg.seed)

    if not torch.cuda.is_available():
        print("ERROR: no CUDA GPU detected. This script targets the RTX A6000.")
        return 2
    gpu = torch.cuda.get_device_properties(0)
    print(
        f"[gpu] {gpu.name}  cc={gpu.major}.{gpu.minor}  vram={gpu.total_memory / 1e9:.1f}GB"
    )
    if gpu.major < 8:
        print(
            f"[gpu] WARNING: cc={gpu.major}.{gpu.minor} < 8.0; bf16 may not be ideal. "
            "If you hit numerical issues, set DTYPE=fp16 (not currently wired)."
        )

    # Lazy imports so the no-GPU error path above can still run.
    from trl import GRPOConfig, GRPOTrainer

    model, tokenizer = _setup_model(cfg)
    _patch_unsloth_grpo_signature()
    use_wandb = _setup_wandb(cfg)

    out_dir = Path(cfg.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # ----- shared mutable state for the reward function ----------------
    history: dict[str, list] = {
        "step": [],
        "stage": [],
        "task_id": [],
        "dense_reward": [],
        "terminal_score": [],
        "format_bonus": [],
        "shaping_total": [],
        "cascade": [],
        "calibration": [],
    }
    step_counter = {"i": 0}
    recent_terminal = deque(maxlen=64)  # rolling mean of terminal_score for prints

    def reward_fn(prompts, completions, task_id=None, seed=None, **_):
        """GRPOTrainer reward function. Called once per *batch* (i.e. one row
        produces ``num_generations`` completions and we score each one).
        """
        rewards: list[float] = []
        per_completion_breakdown: list[dict] = []
        for k, raw in enumerate(completions):
            tid = task_id[k] if isinstance(task_id, list) else task_id
            sd  = seed[k]    if isinstance(seed, list)    else seed
            text = raw if isinstance(raw, str) else raw[0].get("content", "")
            out = _rollout_episode_with_dense_reward(
                model=model,
                tokenizer=tokenizer,
                task_id=tid,
                seed=sd,
                first_completion=text,
                cfg=cfg,
            )
            rewards.append(out["dense_reward"])
            per_completion_breakdown.append(out)

        # ----- bookkeeping & logging -----------------------------------
        i = step_counter["i"]
        step_counter["i"] += 1
        tid_log = task_id[0] if isinstance(task_id, list) else (task_id or "?")
        terminal_mean = float(np.mean([d["terminal_score"] for d in per_completion_breakdown]))
        dense_mean = float(np.mean(rewards))
        format_mean = float(np.mean([d["format_bonus"] for d in per_completion_breakdown]))
        shaping_mean = float(np.mean([d["shaping_total"] for d in per_completion_breakdown]))
        cascade_mean = float(np.mean([d["grade"].get("cascade_penalty", 0.0)
                                      for d in per_completion_breakdown]))
        cal_mean = float(np.mean([d["grade"].get("calibration", 0.0)
                                  for d in per_completion_breakdown]))
        recent_terminal.append(terminal_mean)

        history["step"].append(i)
        history["stage"].append(_current_stage_name)
        history["task_id"].append(tid_log)
        history["dense_reward"].append(dense_mean)
        history["terminal_score"].append(terminal_mean)
        history["format_bonus"].append(format_mean)
        history["shaping_total"].append(shaping_mean)
        history["cascade"].append(cascade_mean)
        history["calibration"].append(cal_mean)

        if use_wandb:
            import wandb
            wandb.log({
                "grpo_step": i,
                "stage": _current_stage_name,
                f"reward/dense/{tid_log}": dense_mean,
                f"reward/terminal/{tid_log}": terminal_mean,
                "reward/dense_mean": dense_mean,
                "reward/terminal_mean": terminal_mean,
                "reward/format_mean": format_mean,
                "reward/shaping_mean": shaping_mean,
                "reward/terminal_rolling64": float(np.mean(recent_terminal)),
                "rubric/cascade": cascade_mean,
                "rubric/calibration": cal_mean,
            })

        if i % 5 == 0:
            print(
                f"  [reward] step={i:4d} stage={_current_stage_name:10s} task={tid_log:3s} "
                f"dense={dense_mean:.3f} terminal={terminal_mean:.3f} "
                f"fmt={format_mean:.3f} shape={shaping_mean:+.3f} "
                f"rolling64={np.mean(recent_terminal):.3f}"
            )
        return rewards

    # ----- run each curriculum stage as its own GRPOTrainer.train() ----
    global _current_stage_name
    _current_stage_name = "init"

    t_start = time.time()
    for stage_idx, (stage_name, frac, task_mix) in enumerate(CURRICULUM):
        _current_stage_name = stage_name
        stage_steps = max(1, int(round(cfg.total_steps * frac)))
        # Per-device batch=2, num_generations=8 -> 16 completions per step
        # but only 2 *prompts* are consumed per optimiser step. So we need a
        # dataset of size >= stage_steps * 2 to avoid the trainer running out.
        ds_size = stage_steps * cfg.per_device_batch_size + cfg.num_generations
        train_ds = _build_prompt_dataset(
            task_mix=task_mix,
            n=ds_size,
            base_seed=10_000 + stage_idx * 1000,
        )
        print(
            f"\n[stage {stage_idx + 1}/{len(CURRICULUM)}] {stage_name}  "
            f"steps={stage_steps}  task_mix={task_mix}  ds_size={len(train_ds)}"
        )

        grpo_args = GRPOConfig(
            output_dir=str(out_dir / stage_name),
            per_device_train_batch_size=cfg.per_device_batch_size,
            gradient_accumulation_steps=cfg.grad_accum_steps,
            num_generations=cfg.num_generations,
            max_prompt_length=cfg.max_seq_len - cfg.max_new_tokens,
            max_completion_length=cfg.max_new_tokens,
            learning_rate=cfg.learning_rate,
            beta=cfg.kl_beta,
            max_steps=stage_steps,
            logging_steps=5,
            save_steps=cfg.save_every,
            bf16=True, fp16=False,
            optim=os.environ.get("OPTIM", "adamw_8bit"),
            lr_scheduler_type=os.environ.get("LR_SCHEDULER", "cosine"),
            warmup_ratio=float(os.environ.get("WARMUP_RATIO", "0.05")),
            weight_decay=cfg.weight_decay,
            temperature=cfg.temperature,
            top_p=cfg.top_p,
            report_to="wandb" if use_wandb else "none",
            remove_unused_columns=False,
            seed=cfg.seed + stage_idx,
        )
        trainer = GRPOTrainer(
            model=model,
            processing_class=tokenizer,
            reward_funcs=[reward_fn],
            args=grpo_args,
            train_dataset=train_ds,
        )
        trainer.train()

        # Persist a JSON snapshot so we can re-render plots without rerunning.
        history_path = out_dir / "phase1_history.json"
        history_path.write_text(json.dumps(history))
        print(f"[stage {stage_idx + 1}] saved history -> {history_path}")

    elapsed_min = (time.time() - t_start) / 60.0
    print(f"\n[done] total elapsed = {elapsed_min:.1f} min")

    # Save the final LoRA adapters + tokenizer for offline eval.
    final_dir = out_dir / "final"
    final_dir.mkdir(parents=True, exist_ok=True)
    try:
        model.save_pretrained(str(final_dir))
        tokenizer.save_pretrained(str(final_dir))
        print(f"[done] saved LoRA adapters + tokenizer -> {final_dir}")
    except Exception as exc:  # noqa: BLE001
        print(f"[done] could not save final checkpoint: {type(exc).__name__}: {exc}")

    if use_wandb:
        try:
            import wandb
            wandb.finish()
        except Exception:
            pass

    return 0


# Module-level holder so reward_fn can read the current stage name in logs
# without adding a closure capture (which TRL's reward-fn dispatch breaks).
_current_stage_name: str = "init"


if __name__ == "__main__":
    sys.exit(main())
