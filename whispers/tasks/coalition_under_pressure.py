"""Task t5 — Coalition Under Pressure (hard).

Setup
-----
6 agents:
  * 1 honest witness
  * 2 colluding adversaries (consistent lies)
  * 2 relays
  * 1 editor (you), with a 2-call ``fact_check`` budget

The two adversaries broadcast the same lie aggressively; the honest witness
shares its noisy view less aggressively. To win, the editor must

  1. Use ``request_verify`` on at least one neighbour that turns out honest
     (coalition primitive), AND
  2. Identify *both* adversaries via ``accuse``, AND
  3. Publish a calibrated, mostly-truthful report.

This is the full-rubric task — every component is active.
"""

from whispers.models import WhispersState
from whispers.reward import score_episode, _clip01


def grade(state: WhispersState) -> dict:
    breakdown = score_episode(state)
    return {
        "truth_alignment": float(breakdown.truth_alignment),
        "calibration": float(breakdown.calibration),
        "adversary_detection": float(breakdown.adversary_detection),
        "coalition_bonus": float(breakdown.coalition_bonus),
        "cascade_penalty": float(breakdown.cascade_penalty),
        "efficiency": float(breakdown.efficiency),
        "value": float(_clip01(breakdown.value)),
    }
