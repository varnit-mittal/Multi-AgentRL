# OpenEnv submission checklist — Whispers

This file audits every disqualifying item from the OpenEnv hackathon
submission checklist against the Whispers repo, with the file/path or
command that proves each item.

| # | Requirement | Status | Evidence |
|---|---|---|---|
| 1 | Typed `Observation`, `Action`, `Reward` Pydantic models | ✅ | `whispers/models.py` — `WhispersObservation`, `WhispersAction`, `WhispersReward`, all `BaseModel` with `extra="forbid"` and field constraints |
| 2 | Gym-style API: `reset()`, `step()`, `state` | ✅ | `whispers/env.py` — class `WhispersEnv` exposes `reset`, `step`, `state` (property + `get_state` alias) and `close` |
| 3 | `step` returns `(observation, reward, done, info)` | ✅ | `whispers/env.py` lines 88-130; smoke test `tests/test_smoke.py::test_step_returns_quadruple` |
| 4 | `reset` returns initial observation | ✅ | `whispers/env.py::reset`; smoke test `test_reset_returns_observation` parametrised over all 6 tasks |
| 5 | Reproducible (same seed → same state) | ✅ | smoke test `test_reset_is_reproducible`; passes (sub-second) |
| 6 | `openenv.yaml` manifest, valid YAML | ✅ | `openenv.yaml` (parses with `yaml.safe_load`; see `assets/openenv_validate.txt`) |
| 7 | Manifest declares Pydantic types via dotted path | ✅ | `openenv.yaml`: `observation_type: whispers.models.WhispersObservation` etc. |
| 8 | At least 5 tasks with deterministic graders | ✅ | `whispers/tasks/{single_relay,triangulate,spot_the_liar,cascade_chain,coalition_under_pressure,calibrated_brief}.py` — six total, each with `grade(state) -> dict` |
| 9 | Graders return float-valued dict in [0, 1] | ✅ | smoke test `test_grader_returns_floats_in_unit_interval` parametrised over all 6 tasks; all pass |
| 10 | Reward function is a composable rubric, not 0/1 | ✅ | `whispers/reward.py::score_episode` combines six per-component metrics with documented weights; per-step shaping in `per_step_shaping` |
| 11 | Reward is hard to game | ✅ | Anti-gaming guards documented in `whispers/reward.py` (F1 not recall for accuse, coalition_bonus requires honest peer, fact_check budget cap, efficiency burns spam) |
| 12 | `inference.py` at repo root, OpenAI client | ✅ | `inference.py` uses `openai.OpenAI` against `API_BASE_URL` / `MODEL_NAME` / `HF_TOKEN` env vars; no hardcoded keys |
| 13 | Exact `[START]` / `[STEP]` / `[END]` log format | ✅ | `inference.py::_emit_start/_emit_step/_emit_end` produce the lines verbatim per the checklist |
| 14 | `Dockerfile` builds, image runs on port 7860 | ✅ | `Dockerfile`: `python:3.11-slim`, `EXPOSE 7860`, `CMD ["python","-m","whispers.server"]`, `HEALTHCHECK` against `/` |
| 15 | HF Space hosts the env (Docker SDK) | 🔧 | Manifest + `Dockerfile` ready. Push instructions in `DEPLOY.md`; Space header is in `README.md` |
| 16 | `GET /` and `POST /reset` return 200 | ✅ | Verified live (Apr 2026) — see `assets/openenv_validate.txt` for the four-endpoint smoke transcript |
| 17 | Public Space, tags include `openenv` | 🔧 | README YAML header includes `tags: [openenv, multi-agent, ...]`; Space owner sets visibility=public per `DEPLOY.md` step 1 |
| 18 | Reserved tool names not used | ✅ | `whispers/tools.py::register_tools()` raises if any handler collides with `{reset, step, state, close}`; smoke test `test_reserved_tool_names_rejected` |
| ✚ | Engineering: client/server separation | ✅ | `whispers/client.py` only imports Pydantic models, never the env / server internals |
| ✚ | Engineering: training script connects to env (not static dataset) | ✅ | `notebooks/train_whispers_grpo.ipynb` calls `WhispersEnv.reset/step` per rollout |
| ✚ | Engineering: training shows improvement | ✅ | `assets/learning_curve.png` shows trained > baselines on the same axes for all 5 main tasks |
| ✚ | Plots: labelled axes + units, committed PNGs | ✅ | All three plots have explicit x/y labels with units, multiple curves on the same axes, and are committed to `assets/` (not Wandb-only) |
| ✚ | Plots: baseline + trained on same axes | ✅ | `learning_curve.png` overlays random + naive_editor + naive_relay; `cascade_resistance.png` and `rubric_breakdown.png` are baseline-vs-trained side by side |
| ✚ | README with HF Space header + docs | ✅ | `README.md` opens with the `--- title/sdk/app_port ---` HF header and embeds the three plots inline |
| ✚ | Mini-blog + 90-s video script | ✅ | `blog/BLOG.md` + `blog/VIDEO_SCRIPT.md` |

Legend: ✅ = code-level evidence in repo · 🔧 = ready to push (requires
deploy step on the user's HF / YouTube account)

## Verification commands

```bash
# 1. Manifest valid
python -c "import yaml; print('OK', yaml.safe_load(open('openenv.yaml'))['name'])"

# 2. Tests
python -m pytest tests/ -v

# 3. Plots regenerate from real env measurements
python scripts/make_plots.py

# 4. Server + endpoints (in two terminals)
python -m whispers.server &
curl -s http://127.0.0.1:7860/
curl -s -X POST http://127.0.0.1:7860/reset -H 'Content-Type: application/json' -d '{"task_id":"t1","seed":0}'

# 5. Inference (requires HF_TOKEN + API_BASE_URL + MODEL_NAME env vars)
python inference.py --task t1
```

All five commands return exit code 0 on a clean `pip install -r requirements.txt`
checkout.
