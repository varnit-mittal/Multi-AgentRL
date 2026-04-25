"""Task t2 — Triangulate (easy/medium).

Setup
-----
4 nodes: 2 witnesses with overlapping but *non-identical* noisy observations,
1 relay, 1 editor (you). Noise level 0.30, so any single witness disagrees
with truth on ~30% of fields — the editor must combine them.

Grader
------
``truth_alignment`` and ``calibration`` co-dominate. We add a small
``efficiency`` bonus to discourage stalling.
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

    value = _clip01(0.55 * ta + 0.35 * cal + 0.10 * eff)

    return {
        "truth_alignment": float(ta),
        "calibration": float(cal),
        "adversary_detection": 1.0,
        "coalition_bonus": 0.0,
        "cascade_penalty": 0.0,
        "efficiency": float(eff),
        "value": float(value),
    }
