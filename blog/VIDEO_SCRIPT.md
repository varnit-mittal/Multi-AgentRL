# Whispers — 90-second YouTube demo script

> Target length: 90-110 s. Capture is screen-recording + voice-over.
>
> Suggested capture tool: OBS Studio with the desktop view at 1920x1080 @ 30fps,
> mic at 48 kHz mono, music bed disabled (clarity > vibe in a 90-s pitch).

## Shot list

| t | Visual | Voice-over (≈ words) |
|---|---|---|
| 0:00 - 0:08 | Title card: "Whispers — train an LLM to not be tricked by a viral lie" + your name + one logo | *"Today's LLMs flip on a correct answer when one loud peer disagrees. We built an OpenEnv environment that trains them to stop doing that."* |
| 0:08 - 0:18 | Architecture diagram from the README (the witness → relay → editor diagram) | *"Whispers drops the agent into a small graph of witnesses, relays, editors, and hidden adversaries. The agent only sees its own inbox and a public feed; it acts via seven MCP tools."* |
| 0:18 - 0:28 | Scroll the `tasks/` directory + the table of 6 graded tasks | *"Five graded tasks plus a stretch sixth, easy to hard. Each grader returns a six-component rubric, normalised to zero-to-one — Brier-style truth alignment, ECE-style calibration, F1 adversary detection, coalition bonus, cascade penalty, efficiency."* |
| 0:28 - 0:40 | Open `inference.py` and run `python inference.py --task t3` (or paste the [START]/[STEP]/[END] log if you don't want a live LLM call) | *"This is the baseline runner. Same OpenAI-client API the OpenEnv submission scorer expects, with the exact [START][STEP][END] log format."* |
| 0:40 - 0:55 | Switch to Colab notebook, scroll the GRPO loop cell with `unsloth` + `trl.GRPOTrainer` | *"Training is one Colab notebook. Unsloth four-bit Qwen2.5-1.5B with LoRA r=16 in TRL's GRPOTrainer; about three hundred steps in forty-five minutes on a free T4."* |
| 0:55 - 1:10 | `assets/cascade_resistance.png` full-screen | *"And here's the headline. The naive relay, the closest stand-in for an untuned LLM, forwards confident lies in every adversarial episode. After training the agent suppresses that by roughly seventy percent — without losing on the easy tasks."* |
| 1:10 - 1:25 | `assets/learning_curve.png` then `assets/rubric_breakdown.png` quick cuts | *"Per-task learning curves with random and naive baselines drawn on the same axes. The rubric breakdown shows where the gains come from — calibration, coalition bonus, and adversary detection — exactly the components the rubric was designed to teach."* |
| 1:25 - 1:35 | Cursor on the GitHub / Hugging Face Space URL | *"Repo, Space, notebook, and blog are all linked in the description. Try it yourself."* |
| 1:35 - 1:40 | Outro card with the Space URL | (silence + 1 s of fade-out music) |

## Voice-over full text (for one-take recording)

> Today's LLMs flip on a correct answer when one loud peer disagrees. We
> built an OpenEnv environment that trains them to stop doing that.
>
> Whispers drops the agent into a small graph of witnesses, relays, editors,
> and hidden adversaries. The agent only sees its own inbox and a public
> feed; it acts via seven MCP tools.
>
> Five graded tasks plus a stretch sixth, easy to hard. Each grader returns
> a six-component rubric, normalised to zero-to-one — Brier-style truth
> alignment, ECE-style calibration, F1 adversary detection, coalition
> bonus, cascade penalty, efficiency.
>
> This is the baseline runner. Same OpenAI-client API the OpenEnv submission
> scorer expects, with the exact START / STEP / END log format.
>
> Training is one Colab notebook. Unsloth four-bit Qwen2.5-1.5B with LoRA
> r=16 in TRL's GRPOTrainer; about three hundred steps in forty-five minutes
> on a free T4.
>
> And here's the headline. The naive relay, the closest stand-in for an
> untuned LLM, forwards confident lies in every adversarial episode. After
> training the agent suppresses that by roughly seventy percent — without
> losing on the easy tasks.
>
> Per-task learning curves with random and naive baselines drawn on the same
> axes. The rubric breakdown shows where the gains come from — calibration,
> coalition bonus, and adversary detection — exactly the components the
> rubric was designed to teach.
>
> Repo, Space, notebook, and blog are all linked in the description. Try it
> yourself.

## Description block (paste into YouTube)

> Whispers — an OpenEnv-compliant multi-agent information-triage environment
> for LLM RL.
>
> 🤗 Space: https://huggingface.co/spaces/<your-user>/whispers
> 📝 Blog:  https://huggingface.co/blog/<your-user>/whispers
> 📓 Notebook: notebooks/train_whispers_grpo.ipynb
> 💻 Code: https://huggingface.co/spaces/<your-user>/whispers/tree/main
>
> #LLM #RL #OpenEnv #MultiAgent #HuggingFace
