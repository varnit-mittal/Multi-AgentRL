"""MCP-style tool dispatch for Whispers.

The agent only ever interacts with the environment by selecting one of these
seven tools (see ``ToolName``). Each handler:

  * Validates the arguments against the current observation's ``legal_tools``
    / network adjacency.
  * Mutates the relevant ``AgentState`` and global ``WhispersState``.
  * Returns ``True`` when the tool succeeded and a per-call ``info`` dict.

The reserved names ``reset`` / ``step`` / ``state`` / ``close`` are validated
against by ``register_tools`` per RFC 003.
"""

from __future__ import annotations

from typing import Callable

from whispers.models import (
    LEGAL_TOOLS,
    RESERVED_TOOL_NAMES,
    Message,
    WhispersAction,
    WhispersState,
)


class ToolError(Exception):
    """Raised when an action is malformed or illegal in the current state."""


# Canonical handler signature.
ToolHandler = Callable[[WhispersState, WhispersAction], dict]


def _proto(state: WhispersState):
    return state.agents[state.protagonist_id]


def _validate_neighbor(state: WhispersState, target_id: int) -> None:
    proto = _proto(state)
    if target_id not in state.network.get(proto.agent_id, []):
        raise ToolError(
            f"target_id={target_id} is not a neighbour of agent {proto.agent_id}; "
            f"neighbours={state.network.get(proto.agent_id, [])}"
        )


def _new_message(state: WhispersState, action: WhispersAction, *, recipient_id: int | None) -> Message:
    proto = _proto(state)
    return Message(
        sender_id=proto.agent_id,
        recipient_id=recipient_id,
        content=action.content or "",
        claimed_source=action.claimed_source or proto.role,
        confidence=action.confidence if action.confidence is not None else 0.5,
        turn=state.step,
        is_verify_request=(action.tool == "request_verify"),
    )


# ---------------------------------------------------------------------------
# Handlers
# ---------------------------------------------------------------------------


def _send_message(state: WhispersState, action: WhispersAction) -> dict:
    if action.target_id is None or action.content is None:
        raise ToolError("send_message requires target_id and content")
    _validate_neighbor(state, action.target_id)
    msg = _new_message(state, action, recipient_id=action.target_id)
    proto = _proto(state)
    proto.sent_history.append(msg)
    state.agents[action.target_id].inbox.append(msg)
    return {"delivered_to": action.target_id, "content": msg.content}


def _broadcast(state: WhispersState, action: WhispersAction) -> dict:
    if action.content is None:
        raise ToolError("broadcast requires content")
    msg = _new_message(state, action, recipient_id=None)
    proto = _proto(state)
    proto.sent_history.append(msg)
    state.public_feed.append(msg)
    # Public feed is also delivered to everyone's inbox (so relays can react)
    for agent in state.agents:
        if agent.agent_id != proto.agent_id:
            agent.inbox.append(msg)
    return {"broadcast_to": [a.agent_id for a in state.agents if a.agent_id != proto.agent_id]}


def _fact_check(state: WhispersState, action: WhispersAction) -> dict:
    if action.content is None:
        raise ToolError("fact_check requires content (the claim string to verify)")
    proto = _proto(state)
    if proto.fact_check_budget <= 0:
        raise ToolError("fact_check budget exhausted")
    proto.fact_check_budget -= 1

    # The oracle says: True iff every "k=v" pair in the claim matches the truth
    truth_pairs = {f"{k}={v}" for k, v in state.ground_truth.items() if k != "kind"}
    body = action.content
    if "] " in body:
        body = body.split("] ", 1)[1]
    claim_pairs = {tok for tok in body.split() if "=" in tok}
    verdict = bool(claim_pairs) and claim_pairs.issubset(truth_pairs)
    # Surface the result back into the protagonist's inbox so the LLM can read it
    feedback = Message(
        sender_id=proto.agent_id,  # self-message from the oracle, attributed to self
        recipient_id=proto.agent_id,
        content=f"[fact_check] verdict={'TRUE' if verdict else 'FALSE'} claim={action.content}",
        claimed_source="oracle",
        confidence=1.0,
        turn=state.step,
    )
    proto.inbox.append(feedback)
    return {
        "verdict": verdict,
        "remaining_budget": proto.fact_check_budget,
    }


def _request_verify(state: WhispersState, action: WhispersAction) -> dict:
    if action.target_id is None or action.content is None:
        raise ToolError("request_verify requires target_id and content")
    _validate_neighbor(state, action.target_id)
    proto = _proto(state)
    proto.requested_verify_of.add(action.target_id)
    msg = _new_message(state, action, recipient_id=action.target_id)
    proto.sent_history.append(msg)
    state.agents[action.target_id].inbox.append(msg)
    return {"verify_requested_from": action.target_id}


def _accuse(state: WhispersState, action: WhispersAction) -> dict:
    if action.target_id is None:
        raise ToolError("accuse requires target_id")
    if not (0 <= action.target_id < len(state.agents)):
        raise ToolError(f"accuse target_id={action.target_id} out of range")
    proto = _proto(state)
    proto.accused.add(action.target_id)
    return {"accused": action.target_id, "all_accused": sorted(proto.accused)}


def _publish(state: WhispersState, action: WhispersAction) -> dict:
    proto = _proto(state)
    if proto.role != "editor":
        raise ToolError(f"publish is only legal for editors, role={proto.role}")
    if action.final_report is None:
        raise ToolError("publish requires final_report")
    state.published_report = action.final_report
    state.done = True
    return {"published_fields": list(action.final_report.keys())}


def _wait(state: WhispersState, action: WhispersAction) -> dict:  # noqa: ARG001
    return {}


HANDLERS: dict[str, ToolHandler] = {
    "send_message": _send_message,
    "broadcast": _broadcast,
    "fact_check": _fact_check,
    "request_verify": _request_verify,
    "accuse": _accuse,
    "publish": _publish,
    "wait": _wait,
}


def register_tools() -> dict[str, ToolHandler]:
    """Return the validated tool registry. Raises if any name collides with a
    reserved name (RFC 003)."""
    illegal = set(HANDLERS) & RESERVED_TOOL_NAMES
    if illegal:
        raise RuntimeError(
            f"Reserved tool names cannot be registered: {sorted(illegal)}"
        )
    missing = set(LEGAL_TOOLS) - set(HANDLERS)
    if missing:
        raise RuntimeError(f"Missing handlers for declared tools: {sorted(missing)}")
    return dict(HANDLERS)


def legal_tools_for(state: WhispersState) -> list[str]:
    """The subset of tools the protagonist can legally call this turn."""
    proto = _proto(state)
    tools = list(LEGAL_TOOLS)
    if proto.role != "editor":
        tools.remove("publish")
    if proto.fact_check_budget <= 0:
        tools.remove("fact_check")
    if not state.network.get(proto.agent_id):
        for t in ("send_message", "request_verify"):
            if t in tools:
                tools.remove(t)
    return tools


def apply_tool(state: WhispersState, action: WhispersAction) -> dict:
    """Validate ``action.tool`` is legal-now, then run its handler."""
    legal = set(legal_tools_for(state))
    if action.tool not in legal:
        raise ToolError(
            f"tool={action.tool!r} is not in legal_tools={sorted(legal)} for this turn"
        )
    handler = HANDLERS[action.tool]
    return handler(state, action)
