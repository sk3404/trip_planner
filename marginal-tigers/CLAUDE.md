# CLAUDE.md — Marginal Tigers

This file is the standing context and operating rules for every Claude Code session in
this repo. Read it before doing anything. It encodes decisions already made in design;
**implement against them — do not re-litigate them.** If a decision genuinely needs to
change, say so explicitly and update this file in the same change.

---

## 1. What this is

**Marginal Tigers** is an automated content pipeline for a single Instagram account: two
plush tiger toys — **Stefan** (diligent economics-professor archetype, competent, prepared)
and **Jan** (lazy, nap-prone, food-motivated foil) — travelling the world (with a recurring
Yosemite base, but only *some* days a year), every post sealed with a deadpan economics
punchline. The comedic engine is *Stefan competent vs. Jan disaster, resolved with an econ
concept* (opportunity cost, revealed preference, deadweight loss…) — but econ is seasoning:
~2 in 3 episodes are pure character comedy (see §6). The world, characters, cast, antagonist
(Big Louis), style, and caption spec are the source of truth in `world/bible.yaml`.

**Names:** import package `marginal_tigers`; CLI command `marginal`; git repo
`marginal-tigers`. (The two-word package name keeps a clean PyPI option open if ever
published; the CLI stays short.)

This is a **static-premise daily-gag** format (sitcom "no learning" logic), NOT a
character arc. Episodes are independent and order-free, except for bounded multi-week
**arcs** (a week in Japan, a Big Louis storyline) handled as first-class blocks.

## 2. Current milestone and its boundary

**Text-only.** The deliverable is *approved episode ideas accumulating in a buffer.*
Every step from idea generation through human review is in scope.

**Explicitly OUT of scope for this milestone — do not build, even if asked in passing:**
image generation, video (Kling/fal), Instagram publishing, the ML humor reward-model, the
bandit prompt-optimizer, embedding-based dedup. These are real and planned (§14) but they
slot into seams left open here; building them now is scope creep.

## 3. Architecture at a glance

A deterministic DAG with agency confined to two spots:

```
ideate [agent-ish chain] -> (image) -> (animate) -> (score/select) ->
   (assemble) -> caption -> (publish)        # parenthesised = later milestones
```

For THIS milestone only the front holds:

```
load world (Tier 1) -> resolve slot from year plan -> fetch history (Tier 2, ALWAYS) ->
generate N candidate ideas (by slot mode; diverse) -> per candidate: critique -> revise ->
run gates -> persist survivors as pending_review -> [human reviews] -> accepted -> buffer
```

## 4. Storage — two tiers, do not mix them

| Tier | Nature | Lives in | Examples |
|------|--------|----------|----------|
| **Tier 1** | authored source-of-truth, human-edited, diffable | **git** | `world/bible.yaml`, `world/econ_concepts.yaml`, `world/year_plan.yaml`, everything in `prompts/` |
| **Tier 2** | operational, append-mostly, queried relationally | **SQLite / Turso** | episodes, review decisions, facet history, debug logs |

Rules: never put episodes in git (churn, unqueryable). Never put the bible in the DB
(loses diffability). The **year plan is Tier 1** specifically because it is generated-once,
hand-edited, then read as a prior — that is config, not operational data.

## 5. Data model

Defined in `schemas.py` (Pydantic v2). Key points:

- **`Episode`** is the persisted unit. Store it as a JSON blob with `id`, `slot_id`,
  `status`, `arc_id`, and `facets.econ_concept` lifted out as **indexed columns** so the
  facet queries in §8 are cheap. Use `sqlite-utils`; no ORM.
- **Natural key = `id`** (slot_id for standalone, slot_id+position for arc beats).
  **Upsert on it** so a double-fired run never duplicates (idempotency).
- **Lifecycle:** `draft -> pending_review -> accepted | rejected -> posted`.
  The **buffer** is `status == accepted AND not yet posted`.
- **Two-stage content:** `EpisodeIdea` (title + premise + caption + facets) is the
  reviewable thing; `econ_concept` lives ONCE inside `facets` (not duplicated) and is
  `None` for the ~2-in-3 character-led episodes. `shots: list[ShotSpec]` is **empty in
  v1** — populated only at video-decomposition time. Never generate shots in the idea call.
- **Provenance** is attached to every kept episode (prompt version, model, tokens, cost).
- **`ReviewDecision` is the seed of the future humor dataset.** Persist every verdict
  (accept/edit/reject + any edited text). It cannot be backfilled — log from day one.

## 6. Generation flow

- **Slot mode drives it (80/20 econ ratio).** Each year-plan slot is `concept_led`
  (~1 in 3) or `character_led` (~2 in 3). For `concept_led`, the slot's `target_concept`
  IS the episode (concept-first); the generator may swap to a stronger gag that still
  covers an under-covered concept. For `character_led`, write pure character comedy —
  econ is optional and usually ABSENT (`facets.econ_concept = None`). Never bolt a concept
  onto a character-led beat. GOLDEN RULE everywhere: the concept is SHOWN, not stated.
- **Prompts read the bible live.** The generator/critic/planner templates inject the raw
  `bible.yaml` (and the relevant concept entries) as context rather than duplicating the
  world in the prompt — so editing the bible immediately changes generation, no prompt edit.
  Always pass every documented context key (use `None`/`[]` for absent ones; templates use
  `StrictUndefined`).
- **History is ALWAYS injected, never optionally checked.** The caller fetches recent
  episodes + facet coverage deterministically and puts them in the prompt context.
  Freshness is a property of every run, not a step the model can skip.
- **Diversity:** ask one call for N candidates with an explicit instruction to vary
  location / activity / gag-structure. Escalate to N independent higher-temp calls only if
  mode-collapse shows in practice.
- **generate -> critique -> revise** is a **Python-controlled chain** (Reflexion-style),
  not an autonomous agent. High temperature for generation, low for the critic. Frame the
  critic adversarially ("find flaws in this episode"), not as self-improvement.

## 7. Gate taxonomy — mechanical auto, judgment human

| Check | Kind | Enforcement |
|-------|------|-------------|
| on-model (Jan has his tag, Stefan is competent) | mechanical | **auto hard-gate** |
| render-feasibility (static camera, ≤2 motions, no legible-text dependency) | mechanical | **auto hard-gate** — highest ROI; kills un-animatable ideas before any render spend |
| not-too-repetitive (§8) | mechanical | **auto hard-gate** |
| econ-correctness (concept actually illustrated, not name-dropped) | judgment | **human**, LLM surfaces a triage flag only |
| funny? | judgment | **human is the oracle.** No auto-gate. LLM humor scores lie. |

Line: *mechanical → automated; taste + correctness → the human, LLM-triaged.* A triage
flag (`WARN`) never blocks on its own.

## 8. Anti-repetition (dedup)

- **v1: facet-tracking only.** SQL over the five axes (`econ_concept`, `location`,
  `activity`, `gag_structure`, `supporting_cast`) with **recency-weighted penalties**.
  Interpretable, robust, and the flag must show *why* it fired — no black-box reject.
- **Arc siblings are EXEMPT** from the similarity penalty (they are supposed to be similar).
- **Deferred:** embedding similarity on the de-boilerplated premise text, added only if
  near-paraphrase dupes actually appear. A naive global embedding threshold WILL misfire
  here — the corpus is intentionally homogeneous (always two tigers + nature + econ).

## 9. Models, structured outputs, cost

- **Generation + year planner: `claude-opus-4-8`.** Critic / mechanical gates:
  `claude-haiku-4-5-20251001` (bump to `claude-sonnet-4-6` if econ-triage needs more
  reasoning). All configurable per role in `llm.py` (`LLMSettings`), never hardcoded —
  so models can be A/B'd on real humor labels later without code surgery.
- **Use native structured outputs**, not the tool-forcing workaround. `messages.parse(
  output_format=PydanticModel)` -> `response.parsed_output`. GA on all three models above.
  Keep LLM-generated schemas (`EpisodeIdea`, `CritiqueResult`) **small with required
  fields** — structured outputs cap optional (24) and union (16) params per request, and
  every `Optional` is a union. The full `Episode` is assembled in Python and may have any
  number of optionals.
- **Handle `stop_reason`:** `refusal` and `max_tokens` raise typed errors (see `llm.py`).
- **Cost** is computed per call from `usage` and a pricing table in `llm.py` (verify rates
  against current docs; batch API is −50%, a future optimization for bulk generation).

## 10. How this gets operated (three modes)

1. **Steady-state autonomy — no agent in the loop.** A scheduler calls the CLI on a timer
   to batch-generate and fill the buffer. This is plain cron / a scheduled Action; it does
   not need Claude Code or any operator agent.
2. **Structural changes — the human, in git.** Editing `bible.yaml`, the prompts, the
   model choice, the econ library. Deliberate, version-controlled. Claude Code may help
   make the edits, but these change the source of truth.
3. **Targeted fix-ups — conversational.** "This episode's punchline is weak; redo it
   leaning on opportunity cost." This is the ONLY place an operator role earns its keep.

**Operator = Claude Code itself for now (call it B1).** It already reads state, runs
commands, and commits to git, so fix-ups work today with zero extra code. A purpose-built
operator agent (B2) is deferred until phone-side conversational fix-ups are actually wanted.

There is **always a deterministic CLI underneath.** Natural-language operation means the
*agent types the verbs*, not that the verbs cease to exist. Same commands serve cron, the
human in a pinch, and the operator agent — that is what keeps every run reproducible.

## 11. Arcs

First-class objects (`Arc` in `schemas.py`): a contiguous block of week-slots sharing a
setting/theme (Yosemite week, Japan week), scheduled as a unit, **overriding the per-slot
`target_concept` default** across its span, with continuity carried between beats. This is
also the mechanism for "change direction of travel." Episodes carry optional `arc_id` +
`arc_position`; dedup exempts siblings (§8).

## 12. Override / regenerate seams (wired now; behaviour may come later)

- `Episode.priority` — higher jumps the buffer queue (override path sets it).
- `Episode.topical` + `topical_context` — for news-reactive gags. The topical path is also
  the first place a *real* tool-use agent (one that web-searches current events) will earn
  its place — a future extension, not v1.
- **Steerable regenerate is a v1 requirement:** episodes must be individually regenerable
  with a free-text directive plus optional overrides (force a concept, keep the location,
  lean on a trait), regenerating *that* episode idempotently and preserving its slot. This
  is what makes mode-3 fix-ups ("improve it like this") translate to a real command.

## 13. CLI surface (Typer)

The single entrypoint is the **`marginal`** CLI; cron, manual runs, and the operator agent
all call the same verbs:

- `marginal plan-year` — generate the annual `year_plan.yaml` (a prior; explicit + diffable,
  never a silent overwrite). Support targeted regeneration of a slice without clobbering hand edits.
- `marginal plan-week` / `marginal generate` — produce candidate episodes for open slots; fill the buffer.
  Flags for arc, candidate count, topical.
- `marginal regenerate` — re-do one episode with a steer (§12).
- `marginal review` — surface pending episodes; record accept/edit/reject (writes the dataset).
- `marginal backup` — dump the DB to a portable file (see §15).

## 14. Deferred — extensible-later seams (do NOT build now)

Each has a home already in the schema/seams so none requires a rewrite:
embedding dedup (§8) · ML humor reward-model trained on `ReviewDecision` + later real
engagement · contextual-bandit prompt optimizer (Neural Linear + Thompson Sampling) ·
topical/news tool-use agent (§12) · image gen · video (fal + Kling) · best-of-N take
selection + character-consistency verifier (the appearance fields in `bible.yaml` double
as its ground truth) · Instagram publishing (official Graph API only — never an unofficial
library) · Turso + scheduled GitHub Action + weekly backup for hosted autonomy · Neon
(serverless Postgres) if analytics later outgrow SQLite · B2 operator agent.

## 15. Rules for Claude Code

- **Never hand-edit operational DB rows.** Tier-2 data changes only through the CLI.
- **Tier-1 files are the only human-authored content;** changes go through git with a diff.
- **Never commit `data/` (the DB), `.env`, or secrets.** Gitignore them. The `backup` dump
  goes to its own destination/branch, never the working tree's tracked DB.
- **Run the test suite before committing.** Conventional, descriptive commit messages.
- **Do not agent-wash deterministic steps.** Retrieval and assembly are plain Python;
  reach for tool-use agency only where control flow is genuinely data-dependent (§12).
- **Use structured outputs, not tool-forcing** (§9). Keep generated schemas small.
- **Prefer markdown/inline over heavyweight formats**; this is a content+code repo.
- When product/SDK details are needed, verify against `docs.claude.com` rather than memory.

## 16. Stack & setup

Python 3.12 · **uv** (deps + lockfile) · `anthropic` SDK · **Pydantic v2** (every LLM I/O
boundary) · **Jinja2** (prompt templates) · **sqlite-utils** (Tier 2; libSQL/Turso later,
identical code) · **Typer** (CLI) · **pydantic-settings** (`.env`) ·
**sentence-transformers** (only when embedding dedup is built) · **pytest**.

Dev runs against a local SQLite file with `debug_logging` on; the hosted scheduled run
points at Turso with logging off. Code and SQL are identical across both.

**Layout:** package code in `src/marginal_tigers/`; Tier-1 content in `world/`; prompt
templates in `prompts/` (with `prompts/partials/`); operational data in `data/` (gitignored).
The `marginal` console script maps to the Typer app in `src/marginal_tigers/cli.py`.
