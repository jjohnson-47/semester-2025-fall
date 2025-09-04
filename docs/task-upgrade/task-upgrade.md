
# Big wins you can ship first (1–2 days each)

1. **Replace file I/O with SQLite (WAL) + JSON export**

* Keep `tasks.json` as import/export, but run live off SQLite (cross-platform, safe concurrency, no daemon).
* Tables: `tasks`, `deps(task_id→blocks_id)`, `events`, `now_queue`.
* Benefits: atomic updates, FTS5 search, simple migrations, no brittle fcntl edge cases.

2. **Explainable scores (per-factor breakdown)**

* Store the *contribution vector* for each task each time you score it.
* Show “why this is in Now Queue” as a mini waterfall (alpha/beta/… deltas). Trust ↑, debugging ↑.

3. **Constraint solver for the Now Queue**

* Instead of “top-K by score,” use a tiny CP-SAT/ILP (OR-Tools) to enforce rules:

  * max 3 items, ≤1 “heavy” item, honor per-course fairness, exclude blocked, fit the next 90 minutes, etc.
* Deterministic, fast (<5ms for 100 tasks). The score becomes the objective; constraints enforce sanity.

4. **Phase auto-detection**

* Derive phase (“pre-launch”, “launch week”, …) from 1–2 anchor dates (semester\_start, add/drop).
* Avoid manual toggles; keep the `zeta_phase` weights but compute phase automatically each day.

5. **Energy & timebox aware picking**

* Let you set: *time slice* (e.g., 25/45/90 min), *energy* (low/medium/high), *context window* (home/campus).
* Filter candidates by estimated effort & context, then run the solver. You’ll actually finish what it picks.

6. **Cycle guard + “why blocked?”**

* On every run, assert the DAG is acyclic; if not, surface a tiny diff that shows the shortest cycle.
* For blocked items, show the *minimal unblocking cut* (the 1–2 tasks that free the most downstream work).

---

# Architecture upgrades (clean, fast, boring)

* **Keep Flask** if you like; add WebSockets (Flask-Sock) for live updates. If you ever want typed routes + ASGI, migrate to FastAPI later; don’t churn now.
* **Data**: SQLite (WAL=on, `PRAGMA busy_timeout=2000`) + **FTS5** virtual table `tasks_fts(title, notes, tags)`.
* **Schema (suggestion)**:

  ```sql
  create table tasks(
    id text primary key,
    course text,
    title text not null,
    status text check(status in ('todo','doing','review','done','blocked')) not null,
    due_at text,            -- ISO8601
    est_minutes integer,    -- effort estimate
    weight real default 1.0,-- user tweak
    category text,          -- content/materials/assessment/technical/communication/setup
    anchor integer default 0, -- boolean-ish
    notes text,
    created_at text not null,
    updated_at text not null
  );
  create table deps(task_id text, blocks_id text, primary key(task_id, blocks_id));
  create table events(id integer primary key, at text, task_id text, field text, from_val text, to_val text);
  create table scores(task_id text primary key, score real, factors json, computed_at text);
  create table now_queue(pos integer primary key, task_id text);
  ```
* **Event log is source-of-truth for history.** Derive stats from it; don’t smear timestamps across files.

---

# Scoring v2 (deterministic + tunable)

Keep your factors, but make them *explicit functions* with bounded ranges and store their raw values. Example:

```yaml
# tools/priority_contracts.yaml (v2)
factors:
  due_urgency:        {weight: 1.0,  clamp: [0, 10]}
  critical_path:      {weight: 2.5,  clamp: [0, 10]}
  unblock_impact:     {weight: 3.0,  clamp: [0, 10]}
  anchor_proximity:   {weight: 1.5,  clamp: [0, 10]}
  chain_head_boost:   {weight: 10.0, clamp: [0, 10]}
  phase_category:     {weight: 0.5,  clamp: [-3, 3]}
  cost_of_delay:      {weight: 2.0,  clamp: [0, 10]}   # NEW
  freshness_decay:    {weight: 1.0,  clamp: [-3, 0]}   # NEW (stale tasks lose points)
  momentum_bonus:     {weight: 0.8,  clamp: [0, 3]}    # NEW (recent wins)
constraints:
  now_queue:
    k: 3
    max_heavy: 1            # est_minutes >= 60
    min_courses: 2          # fairness
    exclude_status: [done, blocked]
    fit_minutes: 90         # timebox
    require_chain_heads: true
phase:
  pre_launch:   {assessment: 1.0, communication: 1.0, content: 1.2, materials: 1.3, technical: 1.5, setup: 1.7}
  launch_week:  {assessment: 1.5, communication: 1.4, content: 1.2, materials: 1.0, technical: 1.0, setup: 1.0}
  week_one:     {assessment: 1.7, communication: 1.5, content: 1.2, materials: 1.0, technical: 1.0, setup: 0.8}
  in_term:      {assessment: 3.0, communication: 2.5, content: 2.0, materials: 1.5, technical: 1.0, setup: 0.5}
```

**New factors that help you:**

* **cost\_of\_delay**: convex penalty as due date nears (captures “it hurts more every day you delay”).
* **freshness\_decay**: subtract points for tasks untouched in N days (prevents fossils).
* **momentum\_bonus**: small boost after a streak (keeps you in flow without gimmicky gamification).

Return a record like:

```json
{
  "task_id": "MATH251-SYLL-UPDATE-CONTENT",
  "score": 162.5,
  "factors": {
    "due_urgency": 12.0, "critical_path": 8.0, ...
  },
  "explain": [
    {"factor":"chain_head_boost","contrib":+40.0},
    {"factor":"unblock_impact","contrib":+27.0},
    {"factor":"cost_of_delay","contrib":+22.5},
    {"factor":"freshness_decay","contrib":-6.0}
  ]
}
```

---

# Solver-based Now Queue (tiny but mighty)

Use OR-Tools CP-SAT to *select* the 3 items. Objective: maximize Σ(score\_i) with constraints:

* Sum(est\_minutes) ≤ timebox
* Count(heavy) ≤ 1
* Distinct courses ≥ 2 (if available)
* Only chain heads unless queue would be empty
* No `blocked` or `done`

This stops “three shiny, impossible tasks” from crowding the queue.

---

# UI/UX that actually reduces friction

* **Keyboard-first command palette** (`/` to search, `.` to mark done, `,` to block, `a` to add).
* **Inline reason panel**: click the score → see factor breakdown, deps graph slice, and “*If you finish this, you unlock X tasks worth Y points*”.
* **DAG chip** on each card: tiny “◀ 3 | ▶ 7” (3 blockers upstream, 7 downstream).
* **Focus mode**: pick timebox+energy; the app hides everything except the three chosen tasks and their checklists.
* **Cycle banner**: if a cycle appears, a red strip with the exact cycle path and one-click “break by deferring X”.

---

# Where LLMs help (and where they don’t)

LLMs = **optional arbitration layer**, never the main engine.

**Use LLM for:**

* **Ambiguity arbitration**: tie-breakers within ±5% score, producing a *rationale string* you can accept/reject.
* **Capture → structure**: free-text “quick add” → JSON task (id, est\_minutes, category, deps inferred from text). Always validate against a JSON Schema; never accept invalid fields.
* **Renaming/dedup**: detect near-duplicate tasks via local embeddings first (e.g., small e5 on CPU); ask LLM only when conflict score is close.

**Never use LLM for:**

* Hard scheduling, constraints, or math. Keep those deterministic.

*Safety rails:* cache prompts, cap token spend, show “AI nudge” badge with a toggle to disable per decision.

---

# Analytics & feedback loops (use your event log)

* **Velocity**: tasks/week by category.
* **WIP**: number in `doing`; enforce WIP cap in solver (e.g., ≤3 total doing).
* **Aging**: highlight tasks aging > X days in `todo` or `review`.
* **Retro card** (weekly): “You finished 14 tasks. 4 were high unblock impact. Top blocker theme: ‘rubric updates’.”

Use DuckDB on the event log for ad-hoc analysis without touching production tables.

---

# Reliability & ops (simple + robust)

* **APScheduler** in-process jobs: hourly rescoring; morning Now Queue refresh; weekly retro.
* **OpenTelemetry** traces around scoring & solver calls; logs include task counts and duration.
* **Snapshotting**: before each reprioritize, dump a gzipped SQLite backup + JSON export (rotate 7).

---

# API extensions (minimal, useful)

* `POST /api/quick_add` → unstructured text → structured task (with schema validation).
* `GET /api/explain/<id>` → factor breakdown + minimal-cut unblock set.
* `POST /api/now_queue/refresh?timebox=90&energy=medium` → returns new queue (plus rationale text).
* `GET /api/health` → db/readiness, last scoring time, DAG ok/cycle path.

---

# Concrete code stubs (drop-in)

**Scoring (Python, Pydantic v2 style):**

```python
# tools/scoring.py
from datetime import datetime, timezone
from pydantic import BaseModel
from math import exp

class Factors(BaseModel):
    due_urgency: float = 0
    critical_path: float = 0
    unblock_impact: float = 0
    anchor_proximity: float = 0
    chain_head_boost: float = 0
    phase_category: float = 0
    cost_of_delay: float = 0
    freshness_decay: float = 0
    momentum_bonus: float = 0

def sigmoid(x): return 1/(1+exp(-x))

def cost_of_delay(due_ts: datetime, now: datetime) -> float:
    # convex as we approach due
    days = (due_ts - now).total_seconds()/86400
    return max(0.0, 10.0 * (1 - sigmoid((days-3)/2)))

def freshness_decay(last_touched: datetime, now: datetime) -> float:
    days = (now - last_touched).total_seconds()/86400
    return -min(3.0, days/7.0)  # -1 per week, capped at -3

def score_task(t, ctx, weights) -> tuple[float, dict]:
    now = datetime.now(timezone.utc)
    f = Factors()
    # Compute raw factor values
    if t.due_at: f.due_urgency = min(10, max(0, 10 - ( (datetime.fromisoformat(t.due_at)-now).days )))
    f.critical_path   = min(10, t.critical_depth or 0)
    f.unblock_impact  = min(10, t.downstream_unlocked or 0)
    f.anchor_proximity= 10 if t.anchor else 0
    f.chain_head_boost= 10 if t.is_chain_head else 0
    f.phase_category  = ctx.phase_weights.get(t.category, 1.0) - 1.0  # center ~0
    if t.due_at: f.cost_of_delay = cost_of_delay(datetime.fromisoformat(t.due_at), now)
    if t.last_touched: f.freshness_decay = freshness_decay(datetime.fromisoformat(t.last_touched), now)
    f.momentum_bonus  = min(3, ctx.recent_completions/5)

    contrib = {k: getattr(f, k)*weights[k] for k in f.model_fields}
    total = sum(contrib.values())
    return total, contrib
```

**Now Queue via CP-SAT:**

```python
# tools/queue_select.py
from ortools.sat.python import cp_model

def select_now_queue(candidates, timebox=90, max_k=3):
    m = cp_model.CpModel()
    x = {t.id: m.NewBoolVar(t.id) for t in candidates}
    # K items
    m.Add(sum(x.values()) <= max_k)
    # Timebox
    m.Add(sum(int(t.est_minutes)*x[t.id] for t in candidates) <= timebox)
    # ≤1 heavy
    m.Add(sum(x[t.id] for t in candidates if (t.est_minutes or 0) >= 60) <= 1)
    # Distinct courses ≥ 2 if possible
    courses = {}
    for t in candidates:
        courses.setdefault(t.course, []).append(x[t.id])
    possible_courses = sum(1 for v in courses.values() if len(v)>0)
    if possible_courses >= 2:
        # boolean reification for selected course
        csel = [m.NewBoolVar(f"course_{c}") for c in courses]
        for sel, (c, vars_) in zip(csel, courses.items()):
            m.Add(sum(vars_) >= 1).OnlyEnforceIf(sel)
            m.Add(sum(vars_) == 0).OnlyEnforceIf(sel.Not())
        m.Add(sum(csel) >= 2)
    # Only chain heads unless nothing else exists
    if any(t.is_chain_head for t in candidates):
        for t in candidates:
            if not t.is_chain_head:
                m.Add(x[t.id] == 0)
    # Objective
    m.Maximize(sum(int(round(t.score*100))*x[t.id] for t in candidates))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 0.05
    solver.parameters.num_search_workers = 8
    res = solver.Solve(m)
    return [t for t in candidates if res == cp_model.OPTIMAL and solver.Value(x[t.id]) == 1]
```

---

# Integrations that help *you* (not vendor lock-in)

* **Calendar ingest (read-only .ics)** for anchor dates + timebox windows. No OAuth sprawl; just a URL/file.
* **GitHub Issues (optional)**: one-way import to a “backlog” course; never write back unless you ask.
* **Local embeddings** (small model, CPU) for duplicate detection and fuzzy find across tasks/notes.

---

# Security & privacy (practical)

* Keep it LAN-only. No auth needed if behind your reverse proxy.
* Sanitize LLM prompts: *never* include secrets; redact URLs/tokens.
* Log LLM decisions with hashes (input/output) so you can audit later without storing full text.

---

# Your next 10 steps (in order)

1. Add SQLite + migration that imports existing `tasks.json`.
2. Implement scoring v2 with stored per-factor contributions.
3. Introduce CP-SAT selection for Now Queue (keep a feature flag).
4. Add phase auto-detection from semester\_start (+ YAML override).
5. Add energy/timebox inputs → feed into solver.
6. Build “Explain” endpoint & UI panel (factor waterfall + minimal cut).
7. Add cycle detection + banner with “break suggestion”.
8. Implement weekly retro using DuckDB over `events`.
9. Add `/quick_add` with schema-validated LLM structuring (toggleable).
10. Snapshot DB+JSON before each reprioritize; rotate 7.

If you want, I can draft the SQLite DDL migration, the Flask endpoints (`/api/explain`, `/api/now_queue/refresh`, `/api/quick_add`), and the exact JSON Schema for `quick_add` tasks so you can paste them in.

