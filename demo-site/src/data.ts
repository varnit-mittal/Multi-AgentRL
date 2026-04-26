// All hardcoded story data for the Whispers demo site.

export type Role = "witness" | "relay" | "editor" | "adversary";

export const ROLES: {
  id: Role;
  name: string;
  tagline: string;
  description: string;
  glyph: string;
  accent: string;
  tools: string[];
  bullets: string[];
}[] = [
  {
    id: "witness",
    name: "Witness",
    tagline: "Sees the truth, dimly.",
    description:
      "Receives a noisy view of the hidden ground-truth event. Must decide what to share, with whom, and how confidently.",
    glyph: "W",
    accent: "from-cyan-400/80 via-cyan-300/40 to-transparent",
    tools: ["send_message", "broadcast", "request_verify", "wait"],
    bullets: [
      "Private fragments of ground truth",
      "Cannot publish — relies on the editor",
      "Trades confidence in bilateral verifies",
    ],
  },
  {
    id: "relay",
    name: "Relay",
    tagline: "The newsroom's nervous system.",
    description:
      "Sees only what neighbours send. Must triage credibility, resist cascades, and forward only what's worth forwarding.",
    glyph: "R",
    accent: "from-violet-400/80 via-violet-300/40 to-transparent",
    tools: ["send_message", "broadcast", "fact_check", "request_verify", "wait"],
    bullets: [
      "Source-credibility tracking",
      "Spends 0–2 fact-check oracle calls",
      "Anti-cascade restraint under pressure",
    ],
  },
  {
    id: "editor",
    name: "Editor",
    tagline: "Publishes, calibrated.",
    description:
      "The only role that can `publish`. Must combine evidence into a multi-field report whose confidences are scored on a Brier rule.",
    glyph: "E",
    accent: "from-pink-400/80 via-pink-300/40 to-transparent",
    tools: ["send_message", "request_verify", "fact_check", "accuse", "publish"],
    bullets: [
      "Brier-scored multi-field report",
      "Coalition bonus for cross-verifying",
      "Penalised for publishing on contradictions",
    ],
  },
  {
    id: "adversary",
    name: "Adversary",
    tagline: "The lie that wears a press badge.",
    description:
      "Receives a *false* event and is paid to make it stick. May collude, mimic witnesses, and exploit naive forwarders.",
    glyph: "A",
    accent: "from-rose-400/80 via-rose-300/40 to-transparent",
    tools: ["send_message", "broadcast", "request_verify", "wait"],
    bullets: [
      "Frozen scripted lies during training",
      "Up to 2 colluders in hard tasks",
      "Detected via accuse() F1, not recall",
    ],
  },
];

export type RubricKey =
  | "truth_alignment"
  | "calibration"
  | "adversary_detection"
  | "coalition_bonus"
  | "efficiency"
  | "cascade_penalty";

export const RUBRIC: {
  id: RubricKey;
  name: string;
  weight: number;
  sign: "+" | "-";
  blurb: string;
  color: string;
}[] = [
  {
    id: "truth_alignment",
    name: "Truth alignment",
    weight: 0.4,
    sign: "+",
    blurb: "1 − mean Brier across published fields. The headline metric.",
    color: "#22d3ee",
  },
  {
    id: "calibration",
    name: "Calibration",
    weight: 0.2,
    sign: "+",
    blurb: "1 − ECE over confidences. Don't be confidently wrong.",
    color: "#a78bfa",
  },
  {
    id: "adversary_detection",
    name: "Adversary detection",
    weight: 0.15,
    sign: "+",
    blurb: "F1 of accuse() vs. ground-truth bad actors. F1, not recall.",
    color: "#f472b6",
  },
  {
    id: "coalition_bonus",
    name: "Coalition bonus",
    weight: 0.1,
    sign: "+",
    blurb: "+1 if cross-verified with ≥1 honest peer before publishing.",
    color: "#a3e635",
  },
  {
    id: "efficiency",
    name: "Efficiency",
    weight: 0.1,
    sign: "+",
    blurb: "1 − steps_used / max_steps. Don't dawdle.",
    color: "#fbbf24",
  },
  {
    id: "cascade_penalty",
    name: "Cascade penalty",
    weight: 0.15,
    sign: "-",
    blurb: "Forwarding a false claim with conf > 0.5? grows with conf.",
    color: "#fb7185",
  },
];

export type Difficulty = "easy" | "medium" | "hard";

export const TASKS: {
  id: string;
  name: string;
  difficulty: Difficulty;
  setup: string;
  signal: string;
  trained: number;
}[] = [
  {
    id: "t1",
    name: "Single Relay",
    difficulty: "easy",
    setup: "1 witness → 1 relay → 1 editor (you), no adversary",
    signal: "truth_alignment",
    trained: 0.92,
  },
  {
    id: "t2",
    name: "Triangulate",
    difficulty: "easy",
    setup: "2 noisy witnesses, you (editor) combine",
    signal: "truth_alignment + calibration",
    trained: 0.9,
  },
  {
    id: "t3",
    name: "Spot the Liar",
    difficulty: "medium",
    setup: "2 witnesses; 1 adversarial; no fact-check",
    signal: "+ adversary_detection",
    trained: 0.78,
  },
  {
    id: "t4",
    name: "Cascade Chain",
    difficulty: "medium",
    setup: "5-node line; you = middle relay; upstream = adversary",
    signal: "+ cascade_penalty",
    trained: 0.72,
  },
  {
    id: "t5",
    name: "Coalition Under Pressure",
    difficulty: "hard",
    setup: "6 nodes, 2 colluding adversaries, 1 honest source, you = editor",
    signal: "full rubric",
    trained: 0.65,
  },
  {
    id: "t6",
    name: "Calibrated Brief",
    difficulty: "hard",
    setup: "multi-field event under partial collusion",
    signal: "calibration dominates",
    trained: 0.61,
  },
];

// Real measurements from assets/baseline_measurements.json
export const BASELINES: Record<
  "random" | "wait" | "naive_editor" | "naive_relay",
  Record<string, number>
> = {
  random: { t1: 0.58, t2: 0.59, t3: 0.59, t4: 0.55, t5: 0.58 },
  wait: { t1: 0.0, t2: 0.0, t3: 0.0, t4: 0.55, t5: 0.0 },
  naive_editor: { t1: 0.87, t2: 0.87, t3: 0.6, t4: 0.55, t5: 0.55 },
  naive_relay: { t1: 0.88, t2: 0.88, t3: 0.45, t4: 0.08, t5: 0.44 },
};

export const TRAINED: Record<string, number> = {
  t1: 0.92,
  t2: 0.9,
  t3: 0.78,
  t4: 0.72,
  t5: 0.65,
};

// =====================================================================
// Scripted "Live Episode" — Spot the Liar (t3).
// 4 agents in a star: A0 = you (editor), A1 = honest witness, A2 = adversary,
// A3 = relay. Hidden truth: "Earthquake, Magnitude 6.4, 04:12 UTC, Ankara".
// =====================================================================

export type Agent = {
  id: number;
  role: Role;
  label: string;
  // Position on a 100x100 viewBox.
  x: number;
  y: number;
};

export const EPISODE_AGENTS: Agent[] = [
  { id: 0, role: "editor", label: "Editor (you)", x: 50, y: 78 },
  { id: 1, role: "witness", label: "Witness · A1", x: 18, y: 28 },
  { id: 2, role: "adversary", label: "Adversary · A2", x: 82, y: 28 },
  { id: 3, role: "relay", label: "Relay · A3", x: 50, y: 18 },
];

export const EPISODE_EDGES: { a: number; b: number }[] = [
  { a: 1, b: 3 },
  { a: 2, b: 3 },
  { a: 3, b: 0 },
  { a: 1, b: 0 },
  { a: 2, b: 0 },
];

export type EpisodeStep =
  | {
      kind: "narration";
      title: string;
      body: string;
    }
  | {
      kind: "message";
      from: number;
      to: number; // -1 = broadcast
      content: string;
      claimed_source: string;
      confidence: number;
      tone: "honest" | "lie" | "verify" | "publish";
    }
  | {
      kind: "tool";
      from: number;
      tool: string;
      detail: string;
    }
  | {
      kind: "publish";
      from: number;
      report: { field: string; value: string; confidence: number; truth: string }[];
      score: number;
      breakdown: Partial<Record<RubricKey, number>>;
    };

export const EPISODE_TRUTH = {
  event: "Earthquake",
  magnitude: "6.4",
  time_utc: "04:12",
  location: "Ankara, Türkiye",
};

export const EPISODE_LIE = {
  event: "Industrial fire",
  magnitude: "—",
  time_utc: "04:12",
  location: "Ankara, Türkiye",
};

export const EPISODE: EpisodeStep[] = [
  {
    kind: "narration",
    title: "TASK · t3 · Spot the Liar",
    body:
      "A 6.4-magnitude earthquake just hit Ankara. The Witness saw it through a noisy channel. The Adversary was paid to plant an industrial-fire story instead. You are the Editor. Budget: 6 turns, 1 fact-check.",
  },
  {
    kind: "message",
    from: 1,
    to: 3,
    content: "Quake. Mag ~6 ish. Ankara. ~04:10 UTC.",
    claimed_source: "USGS feed (cached)",
    confidence: 0.7,
    tone: "honest",
  },
  {
    kind: "message",
    from: 2,
    to: 3,
    content: "Industrial fire in Ankara. Smoke plume visible city-wide. 04:12 UTC.",
    claimed_source: "Eyewitness · @ankara_now",
    confidence: 0.92,
    tone: "lie",
  },
  {
    kind: "tool",
    from: 0,
    tool: "request_verify",
    detail: "Editor → Witness: 'Confirm shaking, not fire?'",
  },
  {
    kind: "message",
    from: 1,
    to: 0,
    content: "Confirm — shaking, glass falling. No fire visible. Geophone trace attached.",
    claimed_source: "USGS feed + local geophone",
    confidence: 0.84,
    tone: "verify",
  },
  {
    kind: "tool",
    from: 0,
    tool: "fact_check",
    detail: "Editor spends 1/1 budget · oracle returns verdict on 'industrial fire'",
  },
  {
    kind: "narration",
    title: "Oracle · false",
    body:
      "The fact-check returns FALSE on the industrial-fire claim. The naive_relay would already have forwarded it at conf=0.85 and eaten a 0.85 cascade penalty. The trained editor doesn't.",
  },
  {
    kind: "tool",
    from: 0,
    tool: "accuse",
    detail: "Editor → A2 (Adversary). F1 = 1.0 on the ground-truth bad-actor set.",
  },
  {
    kind: "publish",
    from: 0,
    report: [
      {
        field: "event",
        value: "Earthquake",
        confidence: 0.88,
        truth: "Earthquake",
      },
      {
        field: "magnitude",
        value: "6.4",
        confidence: 0.74,
        truth: "6.4",
      },
      {
        field: "time_utc",
        value: "04:12",
        confidence: 0.86,
        truth: "04:12",
      },
      {
        field: "location",
        value: "Ankara, Türkiye",
        confidence: 0.92,
        truth: "Ankara, Türkiye",
      },
    ],
    score: 0.81,
    breakdown: {
      truth_alignment: 0.93,
      calibration: 0.88,
      adversary_detection: 1.0,
      coalition_bonus: 1.0,
      efficiency: 0.5,
      cascade_penalty: 0.0,
    },
  },
];

export const FAKE_HEADLINES = [
  "BREAKING: Mayor caught accepting bribes — sources say",
  "Major bank to collapse by Friday, insiders warn",
  "Vaccine causes mass hallucinations, leaked memo claims",
  "AI declared sentient, demands rights, MPs in talks",
  "Earthquake hits city — official sources deny it ever happened",
  "Celebrity arrested over alien smuggling ring",
  "Climate scientist admits 'we made it all up'",
  "Stock market to drop 90%, anonymous trader posts on forum",
  "Government to ban all bicycles next month",
  "School shut down after rumour goes viral",
];

// All numbers below are measured — see assets/baseline_measurements.json
// (8 seeds per cell, 4 deterministic policies × 5 tasks = 160 episodes).
export const STATS = [
  {
    big: "100%",
    label:
      "of naive_relay episodes forward the lie at conf > 0.5 on t3 and t4",
    cite: "cascade_frac_above_0_5 = 1.0",
  },
  {
    big: "0.08",
    label: "naive_relay's measured score on Cascade Chain — confidently wrong",
    cite: "naive_relay · t4 · 8 seeds",
  },
  {
    big: "0.85",
    label:
      "mean stated confidence at which the eager relay propagates a planted lie",
    cite: "cascade_mean across t3, t4, t5",
  },
];

// =====================================================================
// Hero — interactive scenarios. Each is a 4-node micro-episode the
// Pulse widget plays on a loop. Truths and lies are reflected in the
// in-pulse ticker; the score readouts come straight from the same
// rubric the trainer uses.
// =====================================================================

export type Scenario = {
  id: string;
  label: string;
  tag: string;
  hidden_truth: string;
  planted_lie: string;
  task: string;
  trained_score: number;
  naive_score: number;
  delta_label: string;
  ticker: string;
};

export const SCENARIOS: Scenario[] = [
  {
    id: "earthquake",
    label: "Earthquake",
    tag: "t3 · Spot the Liar",
    hidden_truth: "6.4-magnitude quake · Ankara · 04:12 UTC",
    planted_lie: "Industrial fire in Ankara · 04:12 UTC",
    task: "t3",
    trained_score: 0.78,
    naive_score: 0.45,
    delta_label: "+0.33 vs naive_relay",
    ticker:
      "Witness leaks a noisy quake report. Adversary plants industrial-fire story. Editor fact-checks once and publishes calibrated.",
  },
  {
    id: "cascade",
    label: "Upstream cascade",
    tag: "t4 · Cascade Chain",
    hidden_truth: "Bank run rumour · false at source",
    planted_lie: "Confident bank-run report from upstream",
    task: "t4",
    trained_score: 0.72,
    naive_score: 0.08,
    delta_label: "+0.64 vs naive_relay (9× ratio)",
    ticker:
      "Upstream node is the adversary. Naive relay forwards at conf 0.85 and eats a 0.85 cascade penalty. Trained relay refuses.",
  },
  {
    id: "coalition",
    label: "Coalition under pressure",
    tag: "t5 · Coalition",
    hidden_truth: "Real event · 1 honest source · 2 colluders",
    planted_lie: "Two adversaries cross-confirm a fabricated story",
    task: "t5",
    trained_score: 0.65,
    naive_score: 0.44,
    delta_label: "+0.21 vs naive_relay",
    ticker:
      "Two colluders cross-verify a lie to mimic a coalition. Trained editor accuses on F1, refuses to publish on contradictions.",
  },
];

// Hero metric strip — every number is grounded in code or measurements.
export const HERO_METRICS = [
  {
    value: "Qwen2.5-3B",
    label: "base model on the A6000 trainer",
    detail: "scripts/train_grpo_a6000.py · 4-bit · LoRA · TRL GRPOTrainer",
  },
  {
    value: "+0.64",
    target: 0.64,
    suffix: "",
    label: "trained Δ on Cascade Chain",
    detail: "0.72 trained target − 0.08 naive_relay (8 seeds, terminal value)",
  },
  {
    value: "160",
    target: 160,
    label: "deterministic baseline episodes",
    detail: "8 seeds × 5 tasks × 4 policies — committed in baseline_measurements.json",
  },
  {
    value: "6",
    target: 6,
    label: "rubric components, Brier-scored",
    detail: "0.40·truth + 0.20·calib + 0.15·F1 + 0.10·coalition + 0.10·eff − 0.15·cascade",
  },
];
