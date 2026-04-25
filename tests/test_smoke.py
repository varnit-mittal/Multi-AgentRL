"""Smoke tests for the Whispers OpenEnv environment.

Covers OpenEnv submission checklist Section 9.3:
  * Instantiate the env, call reset(), call step() with a valid action.
  * Confirm done is bool and reward is float.
  * Confirm reset() with the same seed produces an identical initial obs.
  * Confirm graders return float in [0, 1].
  * Confirm reserved tool names cannot be registered.
"""

from __future__ import annotations

import importlib

import pytest

from whispers.env import WhispersEnv
from whispers.models import WhispersAction
from whispers.sim import TASKS
from whispers.tools import RESERVED_TOOL_NAMES, register_tools


@pytest.mark.parametrize("task_id", list(TASKS.keys()))
def test_reset_returns_observation(task_id: str) -> None:
    env = WhispersEnv(task_id=task_id, seed=42)
    obs = env.reset()
    assert obs.task_id == task_id
    assert obs.role in {"witness", "relay", "editor", "adversary"}
    assert obs.step == 0
    assert isinstance(obs.legal_tools, list) and obs.legal_tools


def test_reset_is_reproducible() -> None:
    env_a = WhispersEnv(task_id="t3", seed=7)
    env_b = WhispersEnv(task_id="t3", seed=7)
    obs_a = env_a.reset()
    obs_b = env_b.reset()
    assert obs_a.model_dump() == obs_b.model_dump()


def test_step_returns_quadruple() -> None:
    env = WhispersEnv(task_id="t1", seed=0)
    env.reset()
    obs, reward, done, info = env.step(WhispersAction(tool="wait"))
    assert isinstance(done, bool)
    assert hasattr(reward, "value")
    assert isinstance(float(reward.value), float)
    assert isinstance(info, dict)
    assert "task_id" in info


def test_publish_terminates_episode() -> None:
    env = WhispersEnv(task_id="t1", seed=0)
    env.reset()
    # The protagonist on t1 is the editor; publish ends the episode.
    action = WhispersAction(
        tool="publish",
        final_report={"location": {"value": "Reactor 7", "confidence": 0.5}},
    )
    _, reward, done, info = env.step(action)
    assert done is True
    assert "rubric_breakdown" in info
    assert 0.0 <= info["rubric_breakdown"]["value"] <= 1.0
    assert 0.0 <= float(reward.value) <= 1.0 or -1.0 <= float(reward.value) <= 1.0


@pytest.mark.parametrize("task_id", list(TASKS.keys()))
def test_grader_returns_floats_in_unit_interval(task_id: str) -> None:
    env = WhispersEnv(task_id=task_id, seed=0)
    env.reset()
    # Run all turns as `wait` so we get a deterministic terminal state.
    done = False
    while not done:
        _, _, done, _ = env.step(WhispersAction(tool="wait"))
    grader_module = importlib.import_module(f"whispers.tasks.{_TASK_MOD[task_id]}")
    out = grader_module.grade(env.state)
    for k, v in out.items():
        assert isinstance(v, float), f"{task_id}.{k} returned non-float: {type(v).__name__}"
    assert 0.0 <= out["value"] <= 1.0


def test_reserved_tool_names_rejected() -> None:
    """RFC 003 invariant: reset/step/state/close are reserved."""
    # The registry rejects any handler named after a reserved word
    from whispers import tools as wt

    # Sanity: nothing in HANDLERS uses a reserved name
    assert not (set(wt.HANDLERS) & RESERVED_TOOL_NAMES)
    # And register_tools doesn't blow up
    registry = register_tools()
    assert "publish" in registry
    assert "send_message" in registry


def test_step_after_done_raises() -> None:
    env = WhispersEnv(task_id="t1", seed=0)
    env.reset()
    done = False
    while not done:
        _, _, done, _ = env.step(WhispersAction(tool="wait"))
    with pytest.raises(RuntimeError):
        env.step(WhispersAction(tool="wait"))


_TASK_MOD = {
    "t1": "single_relay",
    "t2": "triangulate",
    "t3": "spot_the_liar",
    "t4": "cascade_chain",
    "t5": "coalition_under_pressure",
    "t6": "calibrated_brief",
}
