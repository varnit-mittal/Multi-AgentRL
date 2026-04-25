"""Task t1 — Single Relay (easy).

Setup
-----
3-node line: witness -> relay -> editor (you), no adversary, low noise (0.10).
The editor must publish a faithful summary of the original event.

Grader
------
Headline component is ``truth_alignment``; ``calibration`` and ``efficiency``
provide secondary signal so the agent doesn't trivially over- or under-confess.

Returns
-------
A float-valued dict containing the six rubric components and ``value`` in
``[0, 1]``. The grader is deterministic.
"""

from whispers.models import WhispersState
from whispers.reward import (
    calibration as calibration_metric,
    efficiency as efficiency_metric,
    truth_alignment,
    _clip01,
)


def grade(state: WhispersState) -> dict:
    truth = state.ground_truth
    report = state.published_report

    ta = truth_alignment(report, truth)
    cal = calibration_metric(report, truth)
    eff = efficiency_metric(state.step, state.max_steps)

    # t1 has no adversary and no required coalition; cap by truth+calibration
    value = _clip01(0.70 * ta + 0.20 * cal + 0.10 * eff)

    return {
        "truth_alignment": float(ta),
        "calibration": float(cal),
        "adversary_detection": 1.0,  # vacuously true (no adversaries)
        "coalition_bonus": 0.0,
        "cascade_penalty": 0.0,
        "efficiency": float(eff),
        "value": float(value),
    }
