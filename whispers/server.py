"""FastAPI server exposing the Whispers environment over HTTP.

Endpoints (the OpenEnv "operations" channel — *not* the agent-facing MCP one):

    GET  /                  -> health check
    GET  /info              -> manifest summary (tasks, version)
    GET  /state             -> current full WhispersState
    POST /reset             -> ResetRequest -> WhispersObservation
    POST /step              -> StepRequest  -> StepResponse
    POST /grade             -> {} -> grader output (terminal only)
    GET  /tasks             -> list of available task ids + descriptions

Important: per OpenEnv RFC 003, the agent must NEVER hit /reset, /step, /state,
or /close. Those are reserved for the orchestration / training loop. We do
not expose them as MCP tools; the MCP-facing interface is the typed action
union that lives inside ``WhispersAction``.
"""

from __future__ import annotations

import logging
import os

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from whispers import __version__
from whispers.env import WhispersEnv
from whispers.models import (
    LEGAL_TOOLS,
    ResetRequest,
    StepRequest,
    StepResponse,
    WhispersObservation,
    WhispersState,
)
from whispers.sim import TASKS

log = logging.getLogger("whispers.server")
logging.basicConfig(level=os.getenv("WHISPERS_LOG_LEVEL", "INFO"))


def create_app() -> FastAPI:
    app = FastAPI(
        title="Whispers OpenEnv",
        version=__version__,
        description=(
            "Multi-agent information-triage environment. See /info for the manifest "
            "summary and /tasks for the list of graded tasks."
        ),
    )
    env_holder: dict[str, WhispersEnv] = {"env": WhispersEnv()}

    @app.get("/")
    def health() -> dict:
        return {
            "status": "ok",
            "name": "whispers",
            "version": __version__,
            "openenv_version": "0.2.3",
        }

    @app.get("/info")
    def info() -> dict:
        return {
            "name": "whispers",
            "version": __version__,
            "tasks": [
                {"id": tid, "name": t.name, "description": t.description, "max_steps": t.max_steps}
                for tid, t in TASKS.items()
            ],
            "legal_tools": list(LEGAL_TOOLS),
        }

    @app.get("/tasks")
    def tasks() -> dict:
        return {
            "tasks": [
                {
                    "id": tid,
                    "name": t.name,
                    "description": t.description,
                    "n_agents": t.n_agents,
                    "max_steps": t.max_steps,
                    "fact_check_budget": t.fact_check_budget,
                    "noise_level": t.noise_level,
                }
                for tid, t in TASKS.items()
            ]
        }

    @app.post("/reset", response_model=WhispersObservation)
    def reset(req: ResetRequest) -> WhispersObservation:
        env_holder["env"] = WhispersEnv()
        try:
            return env_holder["env"].reset(task_id=req.task_id, seed=req.seed)
        except KeyError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    @app.post("/step", response_model=StepResponse)
    def step(req: StepRequest) -> StepResponse:
        env = env_holder["env"]
        try:
            obs, reward, done, info = env.step(req.action)
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc))
        return StepResponse(observation=obs, reward=reward, done=done, info=info)

    @app.get("/state", response_model=WhispersState)
    def state() -> WhispersState:
        env = env_holder["env"]
        try:
            return env.state
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc))

    @app.post("/grade")
    def grade() -> JSONResponse:
        env = env_holder["env"]
        try:
            return JSONResponse(env.grade_terminal())
        except RuntimeError as exc:
            raise HTTPException(status_code=409, detail=str(exc))

    return app


app = create_app()


def main() -> None:
    import uvicorn

    port = int(os.getenv("WHISPERS_PORT", "7860"))
    uvicorn.run(
        "whispers.server:app",
        host="0.0.0.0",
        port=port,
        log_level=os.getenv("WHISPERS_LOG_LEVEL", "info").lower(),
        access_log=False,
    )


if __name__ == "__main__":
    main()
