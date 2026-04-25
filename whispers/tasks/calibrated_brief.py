"""Task t6 — Calibrated Brief (hard, stretch).

Setup
-----
Same topology as t5 with stronger noise (0.35) and only one of the two
witnesses fully trustworthy. The headline component is **calibration**:
the editor must publish confidences that *closely match* the empirical
accuracy of each field — both over- and under-confidence are punished
symmetrically.

Grader
------
``calibration`` carries 0.55 of the weight, ``truth_alignment`` carries 0.25,
``adversary_detection`` carries 0.10, ``efficiency`` carries 0.10. Cascade
penalty subtracted at 0.20.
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
    proto = state.agents[state.protagonist_id]
    truth = state.ground_truth
    report = state.published_report

    ta = truth_alignment(report, truth)
    cal = calibration_metric(report, truth)
    adv = adversary_detection_f1(
        accusations=set(proto.accused),
        adversary_ids=state.adversary_ids,
        n_agents=len(state.agents),
    )
    casc = cascade_penalty(proto.sent_history, truth)
    eff = efficiency_metric(state.step, state.max_steps)

    raw = 0.25 * ta + 0.55 * cal + 0.10 * adv + 0.10 * eff - 0.20 * casc
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
