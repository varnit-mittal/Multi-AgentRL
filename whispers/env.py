"""Whispers core environment.

Implements the gym-style ``reset / step / state`` contract from OpenEnv RFC 001
and exposes its action surface via the seven MCP tools registered in
``whispers.tools`` (per RFC 003). Reserved tool names ``reset / step / state /
close`` are explicitly excluded.

The environment is deliberately written so the *same* class powers both the
in-process training loop (`WhispersEnv()` directly) and the FastAPI wrapper
in ``whispers.server`` — there is no second source of truth.
"""

from __future__ import annotations

import importlib
import logging
import random
from typing import Optional

from whispers import sim
from whispers.models import (
    AgentState,
    LEGAL_TOOLS,
    Message,
    ToolName,
    WhispersAction,
    WhispersObservation,
    WhispersReward,
    WhispersState,
)
from whispers.reward import (
    RubricBreakdown,
    make_reward,
    per_step_shaping,
    score_episode,
)
from whispers.tools import ToolError, apply_tool, legal_tools_for, register_tools

log = logging.getLogger("whispers.env")

DEFAULT_TASK = "t1"
DEFAULT_SEED = 0


class WhispersEnv:
    """Multi-agent information-triage environment.

    Notes
    -----
    * ``step(action)`` returns ``(observation, reward, done, info)`` where
      ``observation`` is the *protagonist's* fresh view, ``reward`` is a
      ``WhispersReward`` whose scalar field is ``value``, and ``info``
      contains the per-tool dispatch result, the running per-component
      rubric (when terminal), and the executed scripted-policy actions.
    * After ``done == True``, calling ``step`` again raises ``RuntimeError``;
      callers should call ``reset`` to start a new episode.
    """

    def __init__(self, task_id: str = DEFAULT_TASK, seed: int = DEFAULT_SEED) -> None:
        self._tools = register_tools()  # validates RFC 003 reserved-name rules
        self._task_id: str = task_id
        self._seed: int = seed
        self._rng: random.Random = random.Random(seed)
        self._state: Optional[WhispersState] = None
        self._initial_budget: int = 0

    # ------------------------------------------------------------------
    # Gym-style API
    # ------------------------------------------------------------------

    def reset(
        self,
        task_id: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> WhispersObservation:
        """Build a fresh ``WhispersState`` for the given task + seed."""
        if task_id is not None:
            self._task_id = task_id
        if seed is not None:
            self._seed = seed
        self._rng = random.Random(self._seed)
        self._state = sim.build_initial_state(self._task_id, self._seed)
        proto = self._state.agents[self._state.protagonist_id]
        self._initial_budget = proto.fact_check_budget
        # Stash the initial budget so reward.per_step_shaping can recover it
        self._state.last_actions.append(
            {"kind": "init_budget", "value": self._initial_budget}
        )
        return self._build_observation()

    def step(
        self, action: WhispersAction
    ) -> tuple[WhispersObservation, WhispersReward, bool, dict]:
        if self._state is None:
            raise RuntimeError("step() called before reset(); call reset() first")
        if self._state.done:
            raise RuntimeError(
                "Episode already terminated; call reset() before stepping again"
            )

        info: dict = {"task_id": self._state.task_id, "step": self._state.step}

        # 1) Apply the protagonist's action.
        proto = self._state.agents[self._state.protagonist_id]
        try:
            tool_info = apply_tool(self._state, action)
            info["tool_info"] = tool_info
            info["tool_error"] = None
        except ToolError as exc:
            log.warning("ToolError: %s", exc)
            info["tool_info"] = {}
            info["tool_error"] = str(exc)
            # Treat illegal actions as `wait` so the simulation still advances,
            # but penalise via shaping below.
            shaping_illegal_penalty = -0.05
            info["illegal_action_penalty"] = shaping_illegal_penalty
        else:
            shaping_illegal_penalty = 0.0

        # 2) Compute per-step shaping for the protagonist's chosen action.
        shaping, shape_info = per_step_shaping(self._state, action, proto)
        shaping += shaping_illegal_penalty
        info["shaping_breakdown"] = {**shape_info, "total": shaping}

        # 3) Run scripted policies for every other seat (in id order).
        executed: list[dict] = []
        for agent in self._state.agents:
            if agent.agent_id == self._state.protagonist_id:
                continue
            ctx = sim.PolicyContext(
                state=self._state,
                agent=agent,
                rng=self._rng,
                spec=sim.get_task(self._task_id),
            )
            scripted = sim.scripted_policy(ctx)
            if scripted is None:
                continue
            try:
                exec_info = self._apply_scripted(agent, scripted)
                executed.append({"agent_id": agent.agent_id, "tool": scripted.tool, **exec_info})
            except ToolError as exc:
                log.debug("Scripted ToolError for agent %s: %s", agent.agent_id, exc)
        info["scripted_actions"] = executed

        # 4) Advance the turn counter & episode-end check.
        self._state.step += 1
        terminal = self._state.done or self._state.step >= self._state.max_steps
        if terminal:
            self._state.done = True

        # 5) Compute rewards.
        if terminal:
            breakdown = score_episode(self._state)
            reward = make_reward(breakdown, shaping=shaping, terminal=True)
            info["episode_score"] = breakdown.value
            info["rubric_breakdown"] = breakdown.as_dict()
        else:
            reward = make_reward(None, shaping=shaping, terminal=False)
        self._state.episode_rewards.append(reward.value)

        return self._build_observation(), reward, self._state.done, info

    @property
    def state(self) -> WhispersState:
        if self._state is None:
            raise RuntimeError("state requested before reset()")
        return self._state

    def get_state(self) -> WhispersState:
        """Alias used by some OpenEnv server adapters."""
        return self.state

    def close(self) -> None:
        """No external resources; included for OpenEnv interface symmetry."""
        self._state = None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _apply_scripted(self, agent: AgentState, action: WhispersAction) -> dict:
        """Apply a scripted-policy action *as if the scripted agent were the
        protagonist*. We temporarily swap the protagonist pointer so the same
        tool handlers apply uniform validation."""
        if action.tool not in LEGAL_TOOLS:
            raise ToolError(f"scripted policy emitted unknown tool {action.tool!r}")
        # Temporarily make this agent the protagonist for tool dispatch
        original_proto = self._state.protagonist_id
        self._state.protagonist_id = agent.agent_id
        try:
            # For scripted seats, ignore fact_check / publish / accuse to keep behaviour
            # deterministic and avoid leaking ground-truth oracle calls.
            if action.tool in {"fact_check", "publish", "accuse"}:
                return {}
            return apply_tool(self._state, action)
        except ToolError:
            return {}
        finally:
            self._state.protagonist_id = original_proto

    def _build_observation(self) -> WhispersObservation:
        if self._state is None:
            raise RuntimeError("Cannot build observation: state is None")
        proto = self._state.agents[self._state.protagonist_id]
        spec = sim.get_task(self._state.task_id)
        # Inbox snapshot for THIS turn (we drain it after surfacing so the LLM
        # sees only fresh messages each step). Sent_history retains the trail.
        fresh_inbox = list(proto.inbox)
        proto.inbox.clear()
        # Public feed: only show messages from previous step or this step.
        recent_feed = self._state.public_feed[-12:]
        objective = (
            f"You are agent {proto.agent_id} (role={proto.role}) in task "
            f"{self._state.task_id} ({spec.name}). {spec.description}"
        )
        return WhispersObservation(
            role=proto.role,
            agent_id=proto.agent_id,
            inbox=fresh_inbox,
            public_feed=recent_feed,
            private_facts=list(proto.private_facts),
            network_neighbors=self._state.network.get(proto.agent_id, []),
            fact_check_budget=proto.fact_check_budget,
            step=self._state.step,
            max_steps=self._state.max_steps,
            legal_tools=legal_tools_for(self._state),  # list[str]
            task_id=self._state.task_id,
            objective=objective,
        )

    # ------------------------------------------------------------------
    # Optional: external grader pass for programmatic scoring
    # ------------------------------------------------------------------

    def grade_terminal(self) -> dict:
        """Run the per-task grader on the current terminal state.

        Returns the grader's float-valued dict. Useful for the inference
        runner and the evaluation notebook.
        """
        if self._state is None:
            raise RuntimeError("grade_terminal() called before reset()")
        spec = sim.get_task(self._state.task_id)
        cfg = importlib.import_module(f"whispers.tasks.{_TASK_MODULES[spec.task_id]}")
        return cfg.grade(self._state)


# Map task_id -> module filename
_TASK_MODULES: dict[str, str] = {
    "t1": "single_relay",
    "t2": "triangulate",
    "t3": "spot_the_liar",
    "t4": "cascade_chain",
    "t5": "coalition_under_pressure",
    "t6": "calibrated_brief",
}


__all__ = ["WhispersEnv"]
