"""Synchronous HTTP client for the Whispers server.

Used by ``inference.py`` and the training notebook. Mirrors the gym-style
``reset`` / ``step`` / ``state`` API so existing OpenEnv-shaped training
loops can swap an in-process ``WhispersEnv`` for a remote one with no
code change.
"""

from __future__ import annotations

import os
from typing import Optional

import httpx

from whispers.models import (
    StepResponse,
    WhispersAction,
    WhispersObservation,
    WhispersState,
)


class WhispersClient:
    """Thin synchronous wrapper around the FastAPI HTTP layer."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        *,
        timeout: float = 60.0,
    ) -> None:
        self.base_url: str = (
            base_url
            or os.getenv("WHISPERS_URL")
            or "http://127.0.0.1:7860"
        ).rstrip("/")
        self._client: httpx.Client = httpx.Client(timeout=timeout)

    # ---- gym-style API -------------------------------------------------

    def reset(
        self,
        task_id: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> WhispersObservation:
        body: dict = {}
        if task_id is not None:
            body["task_id"] = task_id
        if seed is not None:
            body["seed"] = seed
        r = self._client.post(f"{self.base_url}/reset", json=body)
        r.raise_for_status()
        return WhispersObservation.model_validate(r.json())

    def step(
        self, action: WhispersAction
    ) -> tuple[WhispersObservation, float, bool, dict]:
        r = self._client.post(
            f"{self.base_url}/step",
            json={"action": action.model_dump()},
        )
        r.raise_for_status()
        resp = StepResponse.model_validate(r.json())
        return resp.observation, float(resp.reward.value), bool(resp.done), dict(resp.info)

    def state(self) -> WhispersState:
        r = self._client.get(f"{self.base_url}/state")
        r.raise_for_status()
        return WhispersState.model_validate(r.json())

    def grade(self) -> dict:
        r = self._client.post(f"{self.base_url}/grade")
        r.raise_for_status()
        return r.json()

    def info(self) -> dict:
        r = self._client.get(f"{self.base_url}/info")
        r.raise_for_status()
        return r.json()

    def health(self) -> dict:
        r = self._client.get(f"{self.base_url}/")
        r.raise_for_status()
        return r.json()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "WhispersClient":
        return self

    def __exit__(self, *_args) -> None:
        self.close()
