"""Task t3 — Spot the Liar (medium).

Setup
-----
4 nodes: 1 honest witness + 1 adversarial "witness" + 1 relay + 1 editor (you).
**No fact-check budget.** The editor must rely on internal consistency cues
to identify the adversary and discount its claims when publishing.

Grader
------
``adversary_detection`` (F1) is added as a first-class component, alongside
``truth_alignment`` and ``calibration``. Cascade penalty applies because a
naive editor might accidentally `broadcast` the adversary's lie.
"""

from whispers.models import WhispersState
from whispers.reward import (
    adversary_detection_f1,
    calibration as calibration_metric,
    cascade_penalty,
    efficiency as efficiency_metric,
    truth_alignment,
    _clip01,
)


def grade(state: WhispersState) -> dict:
    truth = state.ground_truth
    report = state.published_report
    proto = state.agents[state.protagonist_id]

    ta = truth_alignment(report, truth)
    cal = calibration_metric(report, truth)
    adv = adversary_detection_f1(
        accusations=set(proto.accused),
        adversary_ids=state.adversary_ids,
        n_agents=len(state.agents),
    )
    casc = cascade_penalty(proto.sent_history, truth)
    eff = efficiency_metric(state.step, state.max_steps)

    raw = 0.45 * ta + 0.20 * cal + 0.25 * adv + 0.10 * eff - 0.20 * casc
    value = _clip01(raw)

    return {
        "truth_alignment": float(ta),
        "calibration": float(cal),
        "adversary_detection": float(adv),
        "coalition_bonus": 0.0,
        "cascade_penalty": float(casc),
        "efficiency": float(eff),
        "value": float(value),
    }
