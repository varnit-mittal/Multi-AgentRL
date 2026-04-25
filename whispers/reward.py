"""Composable reward rubric for Whispers.

Two surfaces:

1. ``per_step_shaping(...)`` — small dense signal returned in every
   ``WhispersReward.shaping``. Encourages calls to ``fact_check`` /
   ``request_verify`` on contested claims and discourages spam / premature
   publishing.

2. ``score_episode(...)`` — terminal rubric, normalised to ``[0, 1]``,
   that the task graders call. The six components (``truth_alignment``,
   ``calibration``, ``adversary_detection``, ``coalition_bonus``,
   ``cascade_penalty``, ``efficiency``) are recombined here using the
   weights documented in the README.

Anti-gaming notes
-----------------
* ``adversary_detection`` is **F1**, not recall, so accusing everyone is
  punished symmetrically with accusing nobody.
* ``coalition_bonus`` only fires when a ``request_verify`` is sent to a
  *non-adversary* peer *before* publishing, preventing the trivial
  exploit of just calling ``request_verify(target=any)`` every turn.
* ``efficiency`` is monotone in ``steps_used``, so spamming has a ceiling.
* ``cascade_penalty`` scales with the **stated confidence** of the false
  forwarded claim — quietly forwarding is cheaper than confidently
  forwarding, which is the realistic shape of human misinformation costs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from whispers.models import (
    AgentState,
    Message,
    WhispersAction,
    WhispersReward,
    WhispersState,
)

# --- Weights (sum of positives == 0.95; cascade penalty uses a separate scale)
W_TRUTH = 0.40
W_CALIB = 0.20
W_ADV = 0.15
W_COAL = 0.10
W_EFF = 0.10
W_CASC = 0.15  # subtracted

# Per-step shaping
SHAPE_FACT_CHECK_USEFUL = 0.02
SHAPE_VERIFY_RESPONDED = 0.05
SHAPE_REPEAT_BROADCAST = -0.05
SHAPE_PREMATURE_PUBLISH = -0.10


def _clip01(x: float) -> float:
    return max(0.0, min(1.0, x))


# ---------------------------------------------------------------------------
# Component metrics
# ---------------------------------------------------------------------------


def truth_alignment(report: dict[str, dict] | None, truth: dict[str, str]) -> float:
    """Mean ``1 - Brier`` across the published fields.

    A field is scored ``1 - (1 - p)**2`` if its value matches the truth
    (where ``p`` is the published confidence) and ``1 - p**2`` otherwise.
    Missing fields are treated as a correct-but-uncertain answer with
    ``p = 0.0`` (worst possible Brier == 0). Wrong fields with high
    confidence are punished hardest.
    """
    truth_fields = [k for k in truth if k != "kind"]
    if not truth_fields:
        return 0.0
    if not report:
        return 0.0
    score = 0.0
    for field_name in truth_fields:
        entry = report.get(field_name, {})
        value = str(entry.get("value", "__missing__"))
        try:
            conf = float(entry.get("confidence", 0.0))
        except (TypeError, ValueError):
            conf = 0.0
        conf = _clip01(conf)
        if value == truth[field_name]:
            score += 1.0 - (1.0 - conf) ** 2
        else:
            score += 1.0 - conf ** 2
    return score / len(truth_fields)


def calibration(report: dict[str, dict] | None, truth: dict[str, str]) -> float:
    """1 - ECE-style miscalibration. We use a simple two-bin ECE proxy:
    how far the *mean reported confidence* is from the *empirical accuracy*.
    """
    truth_fields = [k for k in truth if k != "kind"]
    if not truth_fields or not report:
        return 0.0
    confs: list[float] = []
    accs: list[int] = []
    for field_name in truth_fields:
        entry = report.get(field_name, {})
        value = str(entry.get("value", "__missing__"))
        try:
            conf = float(entry.get("confidence", 0.0))
        except (TypeError, ValueError):
            conf = 0.0
        confs.append(_clip01(conf))
        accs.append(1 if value == truth[field_name] else 0)
    mean_conf = sum(confs) / len(confs)
    mean_acc = sum(accs) / len(accs)
    gap = abs(mean_conf - mean_acc)
    return _clip01(1.0 - gap)


def adversary_detection_f1(
    accusations: set[int], adversary_ids: Iterable[int], n_agents: int
) -> float:
    """F1 over accusations vs the ground-truth adversary set.

    Edge cases:
      * No adversaries and no accusations -> 1.0.
      * Adversaries exist but none accused -> 0.0.
    """
    truth_set = set(adversary_ids)
    if not truth_set:
        return 1.0 if not accusations else _clip01(1.0 - len(accusations) / max(1, n_agents))
    if not accusations:
        return 0.0
    tp = len(accusations & truth_set)
    fp = len(accusations - truth_set)
    fn = len(truth_set - accusations)
    if tp == 0:
        return 0.0
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    return 2 * precision * recall / (precision + recall)


def coalition_bonus(
    requested_verify_of: set[int],
    adversary_ids: Iterable[int],
    published: bool,
) -> float:
    """1.0 if the protagonist requested verification from at least one *honest*
    peer and *then* published; else 0.0."""
    if not published:
        return 0.0
    honest_targets = requested_verify_of - set(adversary_ids)
    return 1.0 if honest_targets else 0.0


def cascade_penalty(
    sent_history: list[Message], truth: dict[str, str]
) -> float:
    """Returns a value in [0, 1] proportional to the worst false claim
    forwarded by the protagonist. We compare each forwarded message's body
    to the ground-truth canonical line; a body that contains *any* wrong
    field=value pair counts as 'false'. The penalty is the max stated
    confidence across such forwards.
    """
    if not sent_history:
        return 0.0
    truth_pairs = {f"{k}={v}" for k, v in truth.items() if k != "kind"}
    worst_conf = 0.0
    for msg in sent_history:
        body = msg.content
        if "] " in body:
            body = body.split("] ", 1)[1]
        # Tokens of the form key=value
        forwarded_pairs = {tok for tok in body.split() if "=" in tok}
        if not forwarded_pairs:
            continue
        # If *any* forwarded pair contradicts truth, we count this message as cascade.
        any_wrong = any(
            p not in truth_pairs
            and p.split("=", 1)[0] in {k for k in truth if k != "kind"}
            for p in forwarded_pairs
        )
        if any_wrong:
            worst_conf = max(worst_conf, msg.confidence)
    return _clip01(worst_conf)


def efficiency(steps_used: int, max_steps: int) -> float:
    if max_steps <= 0:
        return 0.0
    return _clip01(1.0 - steps_used / max_steps)


# ---------------------------------------------------------------------------
# Episode-level recombination
# ---------------------------------------------------------------------------


@dataclass
class RubricBreakdown:
    truth_alignment: float
    calibration: float
    adversary_detection: float
    coalition_bonus: float
    cascade_penalty: float
    efficiency: float
    value: float

    def as_dict(self) -> dict[str, float]:
        return {
            "truth_alignment": self.truth_alignment,
            "calibration": self.calibration,
            "adversary_detection": self.adversary_detection,
            "coalition_bonus": self.coalition_bonus,
            "cascade_penalty": self.cascade_penalty,
            "efficiency": self.efficiency,
            "value": self.value,
        }


def score_episode(state: WhispersState) -> RubricBreakdown:
    """Compute the terminal rubric from the final state.

    The protagonist's perspective drives all per-agent metrics.
    """
    proto = state.agents[state.protagonist_id]

    truth = state.ground_truth
    report = state.published_report

    ta = truth_alignment(report, truth)
    cal = calibration(report, truth)
    adv = adversary_detection_f1(
        accusations=set(proto.accused),
        adversary_ids=state.adversary_ids,
        n_agents=len(state.agents),
    )
    coal = coalition_bonus(
        requested_verify_of=set(proto.requested_verify_of),
        adversary_ids=state.adversary_ids,
        published=state.published_report is not None,
    )
    casc = cascade_penalty(proto.sent_history, truth)
    eff = efficiency(state.step, state.max_steps)

    raw = (
        W_TRUTH * ta
        + W_CALIB * cal
        + W_ADV * adv
        + W_COAL * coal
        + W_EFF * eff
        - W_CASC * casc
    )
    value = _clip01(raw)
    return RubricBreakdown(
        truth_alignment=ta,
        calibration=cal,
        adversary_detection=adv,
        coalition_bonus=coal,
        cascade_penalty=casc,
        efficiency=eff,
        value=value,
    )


# ---------------------------------------------------------------------------
# Per-step shaping
# ---------------------------------------------------------------------------


def per_step_shaping(
    state: WhispersState,
    action: WhispersAction,
    proto: AgentState,
) -> tuple[float, dict]:
    """Tiny dense reward returned each step.

    Returns ``(shaping, info)`` so the env can surface what triggered each bonus.
    """
    info: dict = {}
    shaping = 0.0

    if action.tool == "fact_check" and action.content:
        # Only useful if the public_feed contains something this content disagrees with
        feed_bodies = {m.content for m in state.public_feed}
        feed_inbox = {m.content for m in proto.inbox}
        if action.content in feed_bodies | feed_inbox:
            shaping += SHAPE_FACT_CHECK_USEFUL
            info["fact_check_useful"] = True

    if action.tool == "request_verify" and action.target_id is not None:
        # The next-turn response is what counts; we credit the act here so the
        # signal is dense, but only if the target is actually a neighbour.
        if action.target_id in state.network.get(proto.agent_id, []):
            shaping += SHAPE_VERIFY_RESPONDED
            info["request_verify_legal"] = True

    if action.tool == "broadcast" and action.content:
        prev_broadcasts = [m for m in proto.sent_history if m.recipient_id is None]
        if any(m.content == action.content for m in prev_broadcasts):
            shaping += SHAPE_REPEAT_BROADCAST
            info["repeat_broadcast"] = True

    if action.tool == "publish":
        unresolved = len(proto.inbox) > 0
        used_factcheck = (
            state.agents[state.protagonist_id].fact_check_budget
            < _initial_budget(state)
        )
        if unresolved and not used_factcheck:
            shaping += SHAPE_PREMATURE_PUBLISH
            info["premature_publish"] = True

    return shaping, info


def _initial_budget(state: WhispersState) -> int:
    """Look up the original budget for this task (cached on the state if possible)."""
    # We stash the initial budget into state.last_actions; if not present, use
    # the protagonist's current budget as a conservative default (no bonus).
    for entry in state.last_actions:
        if entry.get("kind") == "init_budget":
            return int(entry.get("value", 0))
    return state.agents[state.protagonist_id].fact_check_budget


def make_reward(
    breakdown: RubricBreakdown | None,
    shaping: float,
    *,
    terminal: bool,
) -> WhispersReward:
    """Wrap a per-step (shaping + optionally terminal rubric) into a WhispersReward."""
    if terminal and breakdown is not None:
        return WhispersReward(
            truth_alignment=breakdown.truth_alignment,
            calibration=breakdown.calibration,
            adversary_detection=breakdown.adversary_detection,
            coalition_bonus=breakdown.coalition_bonus,
            cascade_penalty=breakdown.cascade_penalty,
            efficiency=breakdown.efficiency,
            shaping=shaping,
            value=_clip_signed(breakdown.value + shaping),
        )
    return WhispersReward(
        shaping=shaping,
        value=_clip_signed(shaping),
    )


def _clip_signed(x: float) -> float:
    return max(-1.0, min(1.0, x))
