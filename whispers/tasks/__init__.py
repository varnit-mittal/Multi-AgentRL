"""Task graders for Whispers.

Every task module exposes a single ``grade(state: WhispersState) -> dict``
function. The dict contains the six rubric components plus a final ``value``
in ``[0.0, 1.0]`` (per OpenEnv's grader contract).

Each grader is deterministic: given the same ``state`` it returns the same
dict, with no calls to system time / external APIs / private RNGs.
"""
