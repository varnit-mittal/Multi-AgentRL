"""Pydantic models for Whispers (Observation, Action, Reward, State, Message).

These types fully define the OpenEnv contract for the environment. They are
imported by `openenv.yaml` via dotted paths and round-trip cleanly through
JSON for the FastAPI HTTP layer.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# Aliases for readability
Role = Literal["witness", "relay", "editor", "adversary"]
ToolName = Literal[
    "send_message",
    "broadcast",
    "fact_check",
    "request_verify",
    "accuse",
    "publish",
    "wait",
]

LEGAL_TOOLS: tuple[ToolName, ...] = (
    "send_message",
    "broadcast",
    "fact_check",
    "request_verify",
    "accuse",
    "publish",
    "wait",
)

# Reserved names per OpenEnv RFC 003 (must NOT appear as MCP tool names)
RESERVED_TOOL_NAMES: frozenset[str] = frozenset({"reset", "step", "state", "close"})


class Message(BaseModel):
    """A single piece of communication exchanged between agents."""

    model_config = ConfigDict(extra="forbid")

    sender_id: int = Field(..., description="Agent id that emitted this message")
    recipient_id: Optional[int] = Field(
        default=None,
        description="None for broadcasts; agent id for direct messages",
    )
    content: str = Field(..., description="Free-text body")
    claimed_source: str = Field(
        default="self",
        description="Where the sender claims this came from (e.g. 'witness', 'relay 3')",
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Sender's stated confidence in the claim",
    )
    turn: int = Field(..., ge=0, description="Turn at which the message was emitted")
    is_verify_request: bool = Field(
        default=False,
        description="True if this is a request_verify call (used by graders)",
    )


class WhispersAction(BaseModel):
    """A single action: a discriminated-union over the seven MCP tool calls."""

    model_config = ConfigDict(extra="forbid")

    tool: ToolName = Field(..., description="Which MCP tool to invoke")
    target_id: Optional[int] = Field(
        default=None,
        description="Recipient id for send_message / accuse / request_verify",
    )
    content: Optional[str] = Field(
        default=None, description="Body text for messages, broadcasts, fact-checks"
    )
    claimed_source: Optional[str] = Field(
        default=None, description="Sender's attribution for the claim"
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Sender's stated confidence (for messages / broadcasts)",
    )
    final_report: Optional[dict[str, dict]] = Field(
        default=None,
        description=(
            "Editor publish payload: {field_name: {'value': str, 'confidence': float}}."
            " Required only when tool == 'publish'."
        ),
    )


class WhispersObservation(BaseModel):
    """A single agent's view of the world this turn."""

    model_config = ConfigDict(extra="forbid")

    role: Role
    agent_id: int
    inbox: list[Message] = Field(default_factory=list)
    public_feed: list[Message] = Field(default_factory=list)
    private_facts: list[str] = Field(
        default_factory=list,
        description="Witness-only ground-truth shards (or adversary's planted lies)",
    )
    network_neighbors: list[int] = Field(default_factory=list)
    fact_check_budget: int = Field(default=0, ge=0)
    step: int = Field(default=0, ge=0)
    max_steps: int = Field(default=24, ge=1)
    legal_tools: list[ToolName] = Field(default_factory=list)
    task_id: str = Field(default="t1")
    objective: str = Field(
        default="",
        description="Human-readable objective text for the current task / role",
    )


class WhispersReward(BaseModel):
    """Per-step reward, with the per-component rubric exposed for analysis."""

    model_config = ConfigDict(extra="forbid")

    truth_alignment: float = 0.0
    calibration: float = 0.0
    adversary_detection: float = 0.0
    coalition_bonus: float = 0.0
    cascade_penalty: float = 0.0
    efficiency: float = 0.0
    shaping: float = Field(
        default=0.0,
        description="Per-step shaping bonus/penalty (fact_check, repeated broadcast, etc.)",
    )
    value: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description=(
            "Normalised scalar in [-1, 1] for a single step; the *episode-level* score"
            " in [0, 1] is computed by the grader and returned in info['episode_score']."
        ),
    )


class AgentState(BaseModel):
    """Per-seat state tracked by the environment (sender + adversary plant + history)."""

    model_config = ConfigDict(extra="allow")

    agent_id: int
    role: Role
    private_facts: list[str] = Field(default_factory=list)
    inbox: list[Message] = Field(default_factory=list)
    sent_history: list[Message] = Field(default_factory=list)
    accused: set[int] = Field(default_factory=set)
    requested_verify_of: set[int] = Field(default_factory=set)
    fact_check_budget: int = 0


class WhispersState(BaseModel):
    """Full environment state — the reply to GET /state."""

    model_config = ConfigDict(extra="allow")

    task_id: str
    seed: int
    step: int
    max_steps: int
    done: bool
    protagonist_id: int
    ground_truth: dict[str, str] = Field(default_factory=dict)
    adversary_ids: list[int] = Field(default_factory=list)
    network: dict[int, list[int]] = Field(
        default_factory=dict,
        description="Adjacency list: agent_id -> list of neighbour ids",
    )
    public_feed: list[Message] = Field(default_factory=list)
    agents: list[AgentState] = Field(default_factory=list)
    published_report: Optional[dict[str, dict]] = None
    last_actions: list[dict] = Field(default_factory=list)
    episode_rewards: list[float] = Field(default_factory=list)


class ResetRequest(BaseModel):
    """HTTP body for POST /reset."""

    model_config = ConfigDict(extra="forbid")
    task_id: Optional[str] = None
    seed: Optional[int] = None


class StepRequest(BaseModel):
    """HTTP body for POST /step."""

    model_config = ConfigDict(extra="forbid")
    action: WhispersAction


class StepResponse(BaseModel):
    """HTTP response for POST /step."""

    model_config = ConfigDict(extra="forbid")
    observation: WhispersObservation
    reward: WhispersReward
    done: bool
    info: dict
