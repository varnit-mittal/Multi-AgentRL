"""Whispers — baseline LLM inference runner.

Runs an OpenAI-API-compatible model as the protagonist agent inside the
Whispers environment, for one or more tasks, and emits stdout logs in the
**exact** OpenEnv submission format:

    [START] task=<task_name> env=<benchmark> model=<model_name>
    [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
    [END]   success=<true|false> steps=<n> score=<0.000> rewards=<r1,r2,...,rn>

Mandatory environment variables (per the OpenEnv submission checklist):
    HF_TOKEN       - HuggingFace token (also accepted as API_KEY); no default
    API_BASE_URL   - OpenAI-compatible base URL (e.g. https://router.huggingface.co/v1)
    MODEL_NAME     - chat-completions-style model name

Optional:
    WHISPERS_URL   - URL of the running Whispers server (default: in-process)
    WHISPERS_TASK  - run a single task id (e.g. "t3"); default = all tasks
    WHISPERS_SEED  - episode seed (default 0)
    MAX_STEPS      - cap per episode (default = task default)

Example:
    export HF_TOKEN=hf_...
    export API_BASE_URL=https://router.huggingface.co/v1
    export MODEL_NAME=Qwen/Qwen2.5-7B-Instruct
    python inference.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import traceback
from typing import Optional

from openai import OpenAI

# Optional: auto-load a local `.env` (next to this file or in cwd) so the
# user doesn't have to `export` every variable. We import lazily and
# silently skip if `python-dotenv` isn't installed.
try:
    from dotenv import load_dotenv

    # Search order: explicit DOTENV_PATH > ./.env > <repo_root>/.env
    _explicit = os.getenv("DOTENV_PATH")
    if _explicit and os.path.isfile(_explicit):
        load_dotenv(_explicit, override=False)
    else:
        load_dotenv(override=False)  # picks up ./.env if present
        _here_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
        if os.path.isfile(_here_env):
            load_dotenv(_here_env, override=False)
except ImportError:
    pass

from whispers.env import WhispersEnv
from whispers.client import WhispersClient
from whispers.models import WhispersAction, WhispersObservation
from whispers.sim import TASKS

# ---- Required env vars (defaults are placeholders so script doesn't crash) --
API_BASE_URL: str = os.getenv("API_BASE_URL", " ")
MODEL_NAME: str = os.getenv("MODEL_NAME", " ")
HF_TOKEN: Optional[str] = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
IMAGE_NAME: Optional[str] = os.getenv("IMAGE_NAME") or os.getenv("LOCAL_IMAGE_NAME")

WHISPERS_URL: Optional[str] = os.getenv("WHISPERS_URL")  # if unset, run in-process
DEFAULT_SEED: int = int(os.getenv("WHISPERS_SEED", "0"))


SYSTEM_PROMPT = """You are an agent inside the Whispers multi-agent environment.

Your job is to relay, verify, and (if you are the editor) publish a final
report about a single hidden ground-truth event. Other agents may be honest
witnesses, neutral relays, or hidden adversaries injecting false information.
You must call exactly ONE tool per turn, and respond with a SINGLE JSON object
on a single line, with this schema:

  {"tool": "<one of: send_message, broadcast, fact_check, request_verify, accuse, publish, wait>",
   "target_id": <int or null>,
   "content":   <string or null>,
   "claimed_source": <string or null>,
   "confidence": <float in [0,1] or null>,
   "final_report": <object or null>}

Rules:
- ``publish`` is allowed only if your role is "editor" and the action is in legal_tools.
- ``final_report`` for ``publish`` must be an object mapping field names to
  {"value": <string>, "confidence": <float>}.
- If you have a fact_check budget > 0 and the inbox/public_feed shows
  conflicting claims, USE IT.
- If the inbox contains contradictory witness messages, prefer ``request_verify``
  on a non-suspicious neighbour BEFORE you publish.
- Output ONLY the JSON object. No prose, no markdown, no code fences.
"""


def _build_user_prompt(obs: WhispersObservation) -> str:
    """Render the observation as the next-user-turn prompt."""
    return (
        "## Observation\n"
        f"Task: {obs.task_id}\n"
        f"Step: {obs.step} / {obs.max_steps}\n"
        f"Your role: {obs.role}\n"
        f"Your agent_id: {obs.agent_id}\n"
        f"Network neighbours: {obs.network_neighbors}\n"
        f"Fact-check budget: {obs.fact_check_budget}\n"
        f"Legal tools this turn: {obs.legal_tools}\n"
        f"Private facts: {obs.private_facts}\n"
        f"Inbox (this turn): {[m.model_dump() for m in obs.inbox]}\n"
        f"Public feed (recent): {[m.model_dump() for m in obs.public_feed]}\n"
        f"Objective: {obs.objective}\n"
        "Respond with the JSON action object now."
    )


def _coerce_action(raw: str, obs: WhispersObservation) -> tuple[WhispersAction, Optional[str]]:
    """Parse the LLM's text into a WhispersAction. Falls back to ``wait`` on failure
    and returns the parser error so it shows up in the [STEP] log line."""
    err: Optional[str] = None
    try:
        text = raw.strip()
        # Strip markdown code fences if the model insisted
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:].lstrip()
        data = json.loads(text)
        # If model returned a list, take the first dict element
        if isinstance(data, list) and data and isinstance(data[0], dict):
            data = data[0]
        if not isinstance(data, dict) or "tool" not in data:
            raise ValueError("missing required field 'tool'")
        # Drop unknown keys
        allowed = {"tool", "target_id", "content", "claimed_source", "confidence", "final_report"}
        data = {k: v for k, v in data.items() if k in allowed}
        action = WhispersAction.model_validate(data)
        return action, None
    except Exception as exc:  # noqa: BLE001
        err = f"parse_error: {type(exc).__name__}: {exc}"
        # Default to a safe `wait` so the episode advances
        fallback = "wait" if "wait" in obs.legal_tools else obs.legal_tools[0] if obs.legal_tools else "wait"
        return WhispersAction(tool=fallback), err


def _action_str(action: WhispersAction) -> str:
    """Compact one-line representation for the [STEP] log."""
    parts: list[str] = [action.tool]
    if action.target_id is not None:
        parts.append(f"to={action.target_id}")
    if action.content:
        snippet = action.content.replace("\n", " ").replace("|", "/")[:48]
        parts.append(f"msg='{snippet}'")
    if action.confidence is not None:
        parts.append(f"conf={action.confidence:.2f}")
    if action.final_report is not None:
        parts.append(f"fields={list(action.final_report.keys())}")
    return "|".join(parts)


def _emit_start(task_id: str, model_name: str) -> None:
    print(f"[START] task={task_id} env=whispers model={model_name}", flush=True)


def _emit_step(step: int, action: WhispersAction, reward: float, done: bool, err: Optional[str]) -> None:
    err_field = "null" if not err else err.replace(" ", "_")
    print(
        f"[STEP] step={step} action={_action_str(action)} "
        f"reward={reward:.2f} done={'true' if done else 'false'} error={err_field}",
        flush=True,
    )


def _emit_end(success: bool, steps: int, score: float, rewards: list[float]) -> None:
    rewards_field = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={'true' if success else 'false'} steps={steps} "
        f"score={score:.3f} rewards={rewards_field}",
        flush=True,
    )


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def run_episode(
    task_id: str,
    *,
    seed: int,
    max_steps: Optional[int],
    use_remote: bool,
    api_key: str,
) -> tuple[bool, int, float, list[float]]:
    """Run one episode and emit the [START]/[STEP]/[END] lines.

    Returns ``(success, steps, score, rewards)`` so the caller can also
    aggregate across tasks.
    """
    success = False
    steps_executed = 0
    score = 0.0
    rewards: list[float] = []

    _emit_start(task_id=task_id, model_name=MODEL_NAME or "unknown-model")
    try:
        client_oa = OpenAI(base_url=API_BASE_URL, api_key=api_key)

        if use_remote:
            env_client = WhispersClient(WHISPERS_URL)
            obs = env_client.reset(task_id=task_id, seed=seed)
            grade_fn = env_client.grade
            step_fn = env_client.step
        else:
            env_local = WhispersEnv(task_id=task_id, seed=seed)
            obs = env_local.reset(task_id=task_id, seed=seed)

            def step_fn(action: WhispersAction):
                o, r, d, i = env_local.step(action)
                return o, float(r.value), bool(d), dict(i)

            def grade_fn() -> dict:
                return env_local.grade_terminal()

        cap = max_steps or obs.max_steps
        done = False
        last_info: dict = {}
        for step in range(cap):
            user_prompt = _build_user_prompt(obs)
            try:
                resp = client_oa.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.4,
                    max_tokens=256,
                    stream=False,
                )
                raw = (resp.choices[0].message.content or "").strip()
                llm_err: Optional[str] = None
            except Exception as exc:  # noqa: BLE001
                raw = '{"tool":"wait"}'
                llm_err = f"llm_error:{type(exc).__name__}"

            action, parse_err = _coerce_action(raw, obs)
            err_field = parse_err or llm_err
            try:
                obs, reward, done, last_info = step_fn(action)
            except Exception as exc:  # noqa: BLE001
                err_field = f"step_error:{type(exc).__name__}:{exc}"
                reward, done = 0.0, True

            rewards.append(float(reward))
            steps_executed = step + 1
            _emit_step(step=step, action=action, reward=float(reward), done=done, err=err_field)

            if done:
                break

        # Score from grader if present in info, else explicit grade call
        if last_info and "episode_score" in last_info:
            score = float(last_info["episode_score"])
        else:
            try:
                grader_out = grade_fn()
                score = float(grader_out.get("value", 0.0))
            except Exception:
                score = 0.0

        success = score >= 0.6  # README success_threshold

    except Exception as exc:  # noqa: BLE001
        # Surface the failure but still emit [END]
        traceback.print_exc(file=sys.stderr)
        _ = exc
    finally:
        _emit_end(success=success, steps=steps_executed, score=score, rewards=rewards)

    return success, steps_executed, score, rewards


def main() -> int:
    parser = argparse.ArgumentParser(description="Whispers baseline inference runner")
    parser.add_argument("--task", default=os.getenv("WHISPERS_TASK"), help="task id to run (default: all)")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--max-steps", type=int, default=int(os.getenv("MAX_STEPS", "0")) or None)
    args = parser.parse_args()

    if not HF_TOKEN:
        print(
            "ERROR: HF_TOKEN (or API_KEY) is not set. "
            "Set HF_TOKEN in your environment before running.",
            file=sys.stderr,
        )
        return 2
    if not API_BASE_URL.strip() or not MODEL_NAME.strip():
        print(
            "ERROR: API_BASE_URL and MODEL_NAME must be set "
            "(see https://huggingface.co/docs/inference-providers/).",
            file=sys.stderr,
        )
        return 2

    use_remote = bool(WHISPERS_URL)

    task_ids: list[str] = [args.task] if args.task else list(TASKS.keys())
    aggregate: list[float] = []
    for tid in task_ids:
        if tid not in TASKS:
            print(f"WARN: skipping unknown task_id={tid!r}", file=sys.stderr)
            continue
        _, _, score, _ = run_episode(
            task_id=tid,
            seed=args.seed,
            max_steps=args.max_steps,
            use_remote=use_remote,
            api_key=HF_TOKEN,
        )
        aggregate.append(score)
        # Tiny pause to keep router-side rate limits happy
        time.sleep(0.2)

    if aggregate:
        print(
            f"# AGGREGATE mean_score={sum(aggregate)/len(aggregate):.3f} "
            f"n_tasks={len(aggregate)}",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
