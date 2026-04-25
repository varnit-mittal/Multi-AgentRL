"""Whispers: a multi-agent information-triage OpenEnv environment.

Public surface for client / training code:

    from whispers import (
        WhispersEnv, WhispersClient,
        WhispersAction, WhispersObservation, WhispersReward, WhispersState,
        Message,
    )
"""

from whispers.models import (
    Message,
    Role,
    ToolName,
    WhispersAction,
    WhispersObservation,
    WhispersReward,
    WhispersState,
)
from whispers.env import WhispersEnv
from whispers.client import WhispersClient

__all__ = [
    "Message",
    "Role",
    "ToolName",
    "WhispersAction",
    "WhispersObservation",
    "WhispersReward",
    "WhispersState",
    "WhispersEnv",
    "WhispersClient",
]

__version__ = "0.1.0"
