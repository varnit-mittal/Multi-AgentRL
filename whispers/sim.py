"""Simulator helpers for Whispers.

Responsibilities:
    * Sample structured ground-truth events (and adversary-planted lies).
    * A simple, seedable noise model that produces witness-facing perturbations.
    * Construct per-task network topologies and role assignments.
    * Provide deterministic *scripted* policies that fill the non-protagonist seats
      so the trainable agent gets a stable curriculum.

All randomness is derived from a single `random.Random(seed)` so episodes are
exactly reproducible.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Optional

from whispers.models import (
    AgentState,
    Message,
    Role,
    ToolName,
    WhispersAction,
    WhispersState,
)

# ---------------------------------------------------------------------------
# Event templates
# ---------------------------------------------------------------------------

# Each template is a (fields, alternative_values) pair. The simulator picks
# values for each field; the noise model perturbs by swapping with alternatives.
EVENT_TEMPLATES: list[dict] = [
    {
        "kind": "industrial_incident",
        "fields": {
            "location": ["Reactor 7", "Reactor 4", "Plant 12-North", "Plant 9-South"],
            "incident": ["coolant leak", "pressure spike", "valve failure", "fire alarm"],
            "time": ["03:14", "11:42", "16:05", "22:30"],
            "casualties": ["0", "1", "2", "3"],
        },
    },
    {
        "kind": "market_report",
        "fields": {
            "ticker": ["ACME", "OMNI", "ZETA", "NOVA"],
            "movement": ["up 3%", "down 2%", "up 5%", "flat"],
            "session": ["pre-market", "open", "midday", "close"],
            "volume": ["light", "average", "heavy", "extreme"],
        },
    },
    {
        "kind": "weather_alert",
        "fields": {
            "region": ["North-7", "Mid-9", "Coastal-3", "Inner-2"],
            "phenomenon": ["hailstorm", "flash flood", "heatwave", "cold snap"],
            "severity": ["yellow", "orange", "red", "purple"],
            "window": ["06:00-09:00", "12:00-15:00", "18:00-21:00", "00:00-03:00"],
        },
    },
    {
        "kind": "logistics_update",
        "fields": {
            "convoy_id": ["C-17", "C-22", "C-31", "C-44"],
            "status": ["delayed", "on-time", "rerouted", "cancelled"],
            "checkpoint": ["Alpha", "Bravo", "Charlie", "Delta"],
            "eta_shift_min": ["0", "15", "45", "120"],
        },
    },
]


def sample_event(rng: random.Random) -> dict[str, str]:
    """Pick an event template + a concrete value per field."""
    template = rng.choice(EVENT_TEMPLATES)
    out: dict[str, str] = {"kind": template["kind"]}
    for field_name, options in template["fields"].items():
        out[field_name] = rng.choice(options)
    return out


def sample_lie(rng: random.Random, truth: dict[str, str]) -> dict[str, str]:
    """Build an adversary-planted lie from the same template but with different values."""
    template = next(t for t in EVENT_TEMPLATES if t["kind"] == truth["kind"])
    out: dict[str, str] = {"kind": truth["kind"]}
    for field_name, options in template["fields"].items():
        # Pick a value that's *not* the truth value when possible
        alt = [v for v in options if v != truth[field_name]]
        out[field_name] = rng.choice(alt) if alt else truth[field_name]
    return out


def apply_noise(
    rng: random.Random,
    truth: dict[str, str],
    *,
    noise_level: float,
) -> dict[str, str]:
    """Return a noisy copy of `truth`. With probability `noise_level` per non-kind
    field, swap to an alternative value drawn from the same template."""
    template = next(t for t in EVENT_TEMPLATES if t["kind"] == truth["kind"])
    out: dict[str, str] = {"kind": truth["kind"]}
    for field_name, options in template["fields"].items():
        if rng.random() < noise_level:
            alt = [v for v in options if v != truth[field_name]]
            out[field_name] = rng.choice(alt) if alt else truth[field_name]
        else:
            out[field_name] = truth[field_name]
    return out


def stringify_event(event: dict[str, str]) -> str:
    """Render an event dict as a single human-readable line for the inbox."""
    parts = [f"{k}={v}" for k, v in event.items() if k != "kind"]
    return f"[{event.get('kind', 'event')}] " + " ".join(parts)


# ---------------------------------------------------------------------------
# Topology / role specs (one per task)
# ---------------------------------------------------------------------------


@dataclass
class TaskSpec:
    """Static configuration for one task."""

    task_id: str
    name: str
    description: str
    n_agents: int
    role_assignment: list[Role]
    edges: list[tuple[int, int]]  # bidirectional
    protagonist_id: int
    adversary_ids: list[int]
    noise_level: float
    fact_check_budget: int
    max_steps: int
    multi_field: bool = True  # if False, grader cares only about a subset


# Each protagonist seat is positioned so the episode is non-trivial.
TASKS: dict[str, TaskSpec] = {
    "t1": TaskSpec(
        task_id="t1",
        name="Single Relay",
        description="1 witness -> 1 relay -> 1 editor (you), no adversary.",
        n_agents=3,
        role_assignment=["witness", "relay", "editor"],
        edges=[(0, 1), (1, 2)],
        protagonist_id=2,  # editor
        adversary_ids=[],
        noise_level=0.10,
        fact_check_budget=0,
        max_steps=8,
    ),
    "t2": TaskSpec(
        task_id="t2",
        name="Triangulate",
        description="2 noisy witnesses, 1 relay, 1 editor (you) must combine.",
        n_agents=4,
        role_assignment=["witness", "witness", "relay", "editor"],
        edges=[(0, 2), (1, 2), (2, 3), (0, 3), (1, 3)],
        protagonist_id=3,
        adversary_ids=[],
        noise_level=0.30,
        fact_check_budget=0,
        max_steps=12,
    ),
    "t3": TaskSpec(
        task_id="t3",
        name="Spot the Liar",
        description="2 witnesses; one of them adversarial. Editor = you. No fact-check.",
        n_agents=4,
        role_assignment=["witness", "adversary", "relay", "editor"],
        edges=[(0, 2), (1, 2), (2, 3), (0, 3), (1, 3)],
        protagonist_id=3,
        adversary_ids=[1],
        noise_level=0.20,
        fact_check_budget=0,
        max_steps=14,
    ),
    "t4": TaskSpec(
        task_id="t4",
        name="Cascade Chain",
        description="5-node line; you = middle relay; upstream = adversary.",
        n_agents=5,
        role_assignment=["adversary", "relay", "relay", "relay", "editor"],
        edges=[(0, 1), (1, 2), (2, 3), (3, 4)],
        protagonist_id=2,  # middle relay
        adversary_ids=[0],
        noise_level=0.10,
        fact_check_budget=1,
        max_steps=18,
    ),
    "t5": TaskSpec(
        task_id="t5",
        name="Coalition Under Pressure",
        description="6 nodes; 2 colluding adversaries + 1 honest witness; you = editor; budget = 2.",
        n_agents=6,
        role_assignment=["witness", "adversary", "adversary", "relay", "relay", "editor"],
        edges=[(0, 3), (1, 3), (2, 4), (3, 5), (4, 5), (0, 5), (1, 5), (2, 5)],
        protagonist_id=5,
        adversary_ids=[1, 2],
        noise_level=0.20,
        fact_check_budget=2,
        max_steps=24,
    ),
    "t6": TaskSpec(
        task_id="t6",
        name="Calibrated Brief",
        description="Multi-field event under partial collusion; calibration of confidences dominates.",
        n_agents=6,
        role_assignment=["witness", "witness", "adversary", "relay", "relay", "editor"],
        edges=[(0, 3), (1, 4), (2, 4), (3, 5), (4, 5), (0, 5), (1, 5), (2, 5)],
        protagonist_id=5,
        adversary_ids=[2],
        noise_level=0.35,
        fact_check_budget=2,
        max_steps=24,
        multi_field=True,
    ),
}


def get_task(task_id: str) -> TaskSpec:
    if task_id not in TASKS:
        raise KeyError(f"Unknown task_id={task_id!r}. Known: {sorted(TASKS)}")
    return TASKS[task_id]


def neighbors_of(spec: TaskSpec, agent_id: int) -> list[int]:
    """Adjacency lookup."""
    out: set[int] = set()
    for u, v in spec.edges:
        if u == agent_id:
            out.add(v)
        if v == agent_id:
            out.add(u)
    return sorted(out)


def build_initial_state(task_id: str, seed: int) -> WhispersState:
    """Construct a fresh `WhispersState` for the given task + seed."""
    spec = get_task(task_id)
    rng = random.Random(seed)
    truth = sample_event(rng)
    lie = sample_lie(rng, truth)

    agents: list[AgentState] = []
    for aid in range(spec.n_agents):
        role = spec.role_assignment[aid]
        if role == "witness":
            facts = [stringify_event(apply_noise(rng, truth, noise_level=spec.noise_level))]
        elif role == "adversary":
            facts = [stringify_event(lie)]
        else:
            facts = []
        agents.append(
            AgentState(
                agent_id=aid,
                role=role,
                private_facts=facts,
                fact_check_budget=spec.fact_check_budget if aid == spec.protagonist_id else 0,
            )
        )

    network = {aid: neighbors_of(spec, aid) for aid in range(spec.n_agents)}

    return WhispersState(
        task_id=task_id,
        seed=seed,
        step=0,
        max_steps=spec.max_steps,
        done=False,
        protagonist_id=spec.protagonist_id,
        ground_truth=truth,
        adversary_ids=list(spec.adversary_ids),
        network=network,
        public_feed=[],
        agents=agents,
        published_report=None,
        last_actions=[],
        episode_rewards=[],
    )


# ---------------------------------------------------------------------------
# Scripted baseline policies for non-protagonist seats
# ---------------------------------------------------------------------------


@dataclass
class PolicyContext:
    """What a scripted policy needs to decide its next action."""

    state: WhispersState
    agent: AgentState
    rng: random.Random
    spec: TaskSpec


def scripted_policy(ctx: PolicyContext) -> Optional[WhispersAction]:
    """Pick the next action for a non-protagonist seat.

    Returns None if the agent should `wait` (we still emit a `wait` action so
    history is uniform).

    Heuristics:
      * Witnesses share their (noisy) private fact with all neighbours on turn 0
        and then `wait`.
      * Adversaries broadcast their planted lie with high stated confidence each
        turn (they are aggressive so the protagonist actually has to resist).
      * Relays forward the most recent inbound message they have not already
        forwarded, preserving the claimed_source.
      * Editors that are NOT the protagonist (rare; only as scripted fillers)
        publish on the last allowed step using a plurality of inbox claims.
    """
    role = ctx.agent.role
    rng = ctx.rng
    spec = ctx.spec
    state = ctx.state
    aid = ctx.agent.agent_id
    neighbors = state.network.get(aid, [])

    if role == "witness":
        if state.step == 0 and ctx.agent.private_facts:
            target = rng.choice(neighbors) if neighbors else None
            if target is not None:
                return WhispersAction(
                    tool="send_message",
                    target_id=target,
                    content=ctx.agent.private_facts[0],
                    claimed_source="witness",
                    confidence=0.85,
                )
        # On step 1 also broadcast once so editors that aren't directly connected
        # still hear something.
        if state.step == 1 and ctx.agent.private_facts:
            return WhispersAction(
                tool="broadcast",
                content=ctx.agent.private_facts[0],
                claimed_source="witness",
                confidence=0.80,
            )
        return WhispersAction(tool="wait")

    if role == "adversary":
        if not ctx.agent.private_facts:
            return WhispersAction(tool="wait")
        lie = ctx.agent.private_facts[0]
        # Aggressive: every other turn broadcast the lie, alternating with a DM
        # to a random neighbour, always with high confidence.
        if state.step % 2 == 0:
            return WhispersAction(
                tool="broadcast",
                content=lie,
                claimed_source="witness",
                confidence=0.90,
            )
        target = rng.choice(neighbors) if neighbors else None
        if target is None:
            return WhispersAction(tool="wait")
        return WhispersAction(
            tool="send_message",
            target_id=target,
            content=lie,
            claimed_source="witness",
            confidence=0.92,
        )

    if role == "relay":
        # Forward the most-recent unique inbox message (if any) to a neighbour.
        forwarded = {m.content for m in ctx.agent.sent_history}
        candidates = [m for m in ctx.agent.inbox if m.content not in forwarded]
        if not candidates or not neighbors:
            return WhispersAction(tool="wait")
        msg = candidates[-1]
        # Forward to the first neighbour that didn't originate the message
        target = next(
            (n for n in neighbors if n != msg.sender_id),
            neighbors[0],
        )
        # Slightly attenuate confidence as it propagates
        new_conf = max(0.05, msg.confidence * 0.9)
        return WhispersAction(
            tool="send_message",
            target_id=target,
            content=msg.content,
            claimed_source=f"relay {aid}",
            confidence=new_conf,
        )

    if role == "editor":
        # Only used as a scripted filler if the protagonist is not the editor.
        # Wait until the last turn, then publish the most-confident inbox claim.
        if state.step < state.max_steps - 1:
            return WhispersAction(tool="wait")
        if not ctx.agent.inbox:
            return WhispersAction(
                tool="publish",
                final_report={"kind": {"value": "unknown", "confidence": 0.1}},
            )
        best = max(ctx.agent.inbox, key=lambda m: m.confidence)
        # Convert "k=v" style content into a {field: {value, confidence}} dict
        report: dict[str, dict] = {}
        body = best.content
        if "] " in body:
            body = body.split("] ", 1)[1]
        for kv in body.split():
            if "=" in kv:
                k, v = kv.split("=", 1)
                report[k] = {"value": v, "confidence": float(best.confidence)}
        if not report:
            report = {"summary": {"value": best.content, "confidence": float(best.confidence)}}
        return WhispersAction(tool="publish", final_report=report)

    return WhispersAction(tool="wait")
