# Deploying Whispers to Hugging Face Spaces

Whispers is shipped as a **Docker SDK** Space. The HF Spaces build runner
will pick up the `Dockerfile` at the repo root and the YAML header at the
top of `README.md` to provision the Space.

## 1. Create the Space

1. Visit https://huggingface.co/new-space.
2. **Owner**: your user / org.
3. **Space name**: `whispers` (slug must match `openenv.yaml`'s `name:`).
4. **License**: Apache-2.0 (matches `pyproject.toml`).
5. **Space SDK**: **Docker** (do *not* pick Gradio / Streamlit).
6. **Hardware**: `CPU basic` is sufficient (the env runs in pure Python).
7. **Visibility**: **Public** (HF Spaces submission rule D17).
8. After creation, add `openenv` and `multi-agent` as repository tags
   in the Space settings.

## 2. Push the code

Spaces are git repos. Add HF as a remote and push:

```bash
# Once, in the project root
git remote add space https://huggingface.co/spaces/<your-user>/whispers
git lfs install            # only needed if you commit large files (we don't)
git push space main
```

The HF builder will:
1. Detect `Dockerfile`, build the image, install `requirements.txt` + `pip install -e .`.
2. Run `python -m whispers.server` (the Dockerfile `CMD`).
3. Bind to port 7860 (declared via `EXPOSE` and the `app_port: 7860` field
   in the README YAML header).
4. After ~60 s, `https://<your-user>-whispers.hf.space/` should return
   the JSON health payload.

## 3. Verify

```bash
SPACE=https://<your-user>-whispers.hf.space
curl -s ${SPACE}/                                                     # 200, version JSON
curl -s -X POST ${SPACE}/reset -H 'Content-Type: application/json' \
  -d '{"task_id":"t1","seed":0}'                                      # observation JSON
curl -s -X POST ${SPACE}/step  -H 'Content-Type: application/json' \
  -d '{"action":{"tool":"wait"}}'                                     # step JSON
curl -s ${SPACE}/state                                                # state JSON
```

All four must return HTTP 200, each within ~5 s of the cold start.

## 4. (Optional) Local container parity check

If you have Docker locally:

```bash
docker build -t whispers .
docker run --rm -p 7860:7860 whispers
# in another shell
curl -s http://localhost:7860/
```

Image size target: < 500 MB. Cold-start target: < 60 s.

## 5. Wire up the inference script

```bash
export HF_TOKEN=hf_...                      # required, no default
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-7B-Instruct
export WHISPERS_URL=https://<your-user>-whispers.hf.space
python inference.py                         # runs all 6 tasks
```

The `[START]` / `[STEP]` / `[END]` log lines are emitted in the exact
format the OpenEnv hackathon scorer expects.

## Submission hygiene

- Confirm the Space tags include `openenv`.
- Confirm `Dockerfile`, `openenv.yaml`, `README.md`, `inference.py`,
  `requirements.txt`, `pyproject.toml` are all in the **repo root**.
- Confirm Space remains live for 10+ minutes before submitting (per the
  OpenEnv submission checklist Section 7.2).
