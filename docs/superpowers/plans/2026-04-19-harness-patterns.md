# Harness Patterns Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the agent-harness artifacts specified in `docs/superpowers/specs/2026-04-19-harness-patterns-design.md` to the repo: session checklists, `init.sh`, graph-freshness warning, 5 ADRs.

**Architecture:** All changes are docs/config. No runtime code is touched. Work happens on branch `chore/harness-patterns` (already checked out). Each task creates or edits exactly one file and leaves staging untouched; a single final commit bundles everything. Verification does a real fresh-clone smoke via `git clone` from the local branch. One commit → squash-merge to `master` per repo policy.

**Tech Stack:** bash, markdown, git. Python tooling already present (`uv`, `ruff`, `mypy`, `pytest`, `detect-secrets`, `pre-commit`).

**Spec reference:** `docs/superpowers/specs/2026-04-19-harness-patterns-design.md`

---

## Pre-flight

Before starting: confirm branch and clean working tree (other than the spec commit already on this branch).

- [ ] **Step 0.1: Confirm branch and state**

```bash
git branch --show-current
git status
```

Expected output: branch is `chore/harness-patterns`; only untracked files are `AGENTS.md`, `graphify-out/`, and nothing else modified.

---

## Task 1: Prepend session checklists to AGENTS.md

**Files:**
- Modify: `AGENTS.md` (insert a new section between the intro paragraph ending at line ~5 and the heading `## What this repo does`)

The existing `AGENTS.md` is untracked but already contains the architecture content. We prepend the checklist section; everything else stays.

- [ ] **Step 1.1: Insert Session start / Session end checklists after the header's `---` divider**

Open `AGENTS.md`. Find this region (around lines 5–9):

```markdown
> Architectural facts here were derived by graphifying the codebase (`graphify-out/GRAPH_REPORT.md`), then verified against source. Known LLM-inferred edge mistakes have been corrected by `graphify-out/postprocess.py` — re-run it after any `/graphify` rebuild.

---

## What this repo does
```

Replace the `---` + `## What this repo does` with:

```markdown
---

## Session start checklist

1. `pwd` — confirm you're in the repo root (`C:\Users\cooper\braves`).
2. `git log --oneline -20` and `git status`.
3. Check `docs/superpowers/specs/` and `docs/plans/` for the newest spec or plan touching your task. If you were mid-task when context cleared, the spec is the source of truth — re-read it before resuming.
4. `bash init.sh` — idempotent; safe to re-run.
5. `bash check.sh` — if red, fix before starting new work.

## Session end checklist

1. `bash check.sh` passes (or failures are documented in-repo, not in a memory scratchpad).
2. If work is mid-flight, make sure the active spec/plan in `docs/superpowers/specs/` or `docs/plans/` reflects reality — update it in the same commit as the code, not in a side log.
3. Branch pushed, PR open, CI green before merge (see `CLAUDE.md` — squash-only).

---

## What this repo does
```

- [ ] **Step 1.2: Verify the file still reads coherently**

Run:

```bash
head -40 AGENTS.md
```

Expected: the intro paragraph, then the two checklists, then `## What this repo does`. No duplicated headings. No broken markdown.

- [ ] **Step 1.3: Do NOT commit yet**

This task's changes will be bundled into the single final commit (Task 10). Leave the file edited and unstaged.

---

## Task 2: Create `init.sh`

**Files:**
- Create: `init.sh`

- [ ] **Step 2.1: Write `init.sh` verbatim**

Create `init.sh` at the repo root with exactly this content:

```bash
#!/usr/bin/env bash
# Fresh clone → runnable. Idempotent; safe to re-run.
set -euo pipefail

# Always run from the script's own directory (the repo root).
cd "$(dirname "$0")"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is not installed. Install: https://docs.astral.sh/uv/getting-started/installation/"
  exit 1
fi

uv sync

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example. Fill in ANTHROPIC_API_KEY, GMAIL_ADDRESS, GMAIL_APP_PASSWORD, EMAIL_RECIPIENTS before running."
fi

uv run pre-commit install

echo "Ready. Next: fill in .env, then 'bash check.sh' to verify."
```

- [ ] **Step 2.2: Verify `init.sh` runs idempotently on the already-initialised repo**

Run:

```bash
bash init.sh
```

Expected: `uv sync` reports "Resolved ... packages" and "Audited ..."; no new `.env` message (the file already exists); `pre-commit` hook install completes; script ends with the "Ready." line. Exit 0.

---

## Task 3: Un-ignore `graphify-out/.last-sha`

**Files:**
- Modify: `.gitignore`

Current contents (verified):

```
.env
__pycache__/
*.pyc
*.egg-info/
dist/
build/
.venv/
.pytest_cache/
.ruff_cache/
.coverage
mockups/
```

Note: `graphify-out/` is not currently in the repo's `.gitignore` (it shows as untracked). We're adding it now and un-ignoring the single `.last-sha` marker via a negation rule.

**Important gitignore detail:** a directory rule like `graphify-out/` (trailing slash) causes git to stop descending; negations inside never trigger. Use `graphify-out/*` instead — that matches files inside the directory but allows negation to re-include specific files.

- [ ] **Step 3.1: Append `graphify-out/*` + negation to `.gitignore`**

Replace the file's contents with:

```
.env
__pycache__/
*.pyc
*.egg-info/
dist/
build/
.venv/
.pytest_cache/
.ruff_cache/
.coverage
mockups/
graphify-out/*
!graphify-out/.last-sha
```

- [ ] **Step 3.2: Verify git would honour the negation**

Run:

```bash
git check-ignore -v graphify-out/GRAPH_REPORT.md graphify-out/.last-sha 2>&1 || true
```

Expected: `graphify-out/GRAPH_REPORT.md` is ignored (prints a line starting with `.gitignore:<n>:`); `graphify-out/.last-sha` is NOT ignored (no output for that path, `git check-ignore` exits non-zero for un-ignored paths). The `|| true` keeps the test runner happy.

---

## Task 4: Seed `graphify-out/.last-sha`

**Files:**
- Create: `graphify-out/.last-sha`

The staleness warning in `check.sh` compares HEAD against this SHA. Seeding it to the current HEAD means the counter starts at 0 rather than dumping a scary "stale" message on first run.

- [ ] **Step 4.1: Write current HEAD SHA into `graphify-out/.last-sha`**

Run:

```bash
mkdir -p graphify-out
git rev-parse HEAD > graphify-out/.last-sha
```

Then verify:

```bash
cat graphify-out/.last-sha
```

Expected: a 40-char hex SHA matching `git rev-parse HEAD`.

- [ ] **Step 4.2: Verify git sees the file as tracked-able**

```bash
git check-ignore -v graphify-out/.last-sha 2>&1 || true
git status --short graphify-out/
```

Expected: `git check-ignore` produces no output (file is NOT ignored). `git status --short` shows `?? graphify-out/.last-sha` (untracked but visible — rest of `graphify-out/` remains hidden).

---

## Task 5: Append graph-freshness warning to `check.sh`

**Files:**
- Modify: `check.sh` (append a new section before `echo "=== All checks passed ==="`)

Current `check.sh` ends:

```bash
echo "=== Tests ==="
uv run pytest tests/ -v

echo "=== All checks passed ==="
```

- [ ] **Step 5.1: Insert the freshness step before the final echo**

Replace the tail of `check.sh` so the file ends like this (everything above `echo "=== Tests ==="` is unchanged):

```bash
echo "=== Tests ==="
uv run pytest tests/ -v

echo "=== Graph Freshness ==="
# Non-blocking. Surfaces graphify-out staleness so AGENTS.md architecture
# facts don't silently diverge from src/.
if [ -f graphify-out/.last-sha ]; then
    LAST_SHA=$(cat graphify-out/.last-sha)
    STALE=$(git rev-list --count "${LAST_SHA}..HEAD" -- src/ 2>/dev/null || echo 0)
    if [ "${STALE}" -gt 10 ]; then
        echo "⚠ graphify-out is ${STALE} src/ commits stale — run /graphify after your next feature"
    else
        echo "graphify-out is ${STALE} src/ commits old (threshold: 10)"
    fi
else
    echo "no graphify-out/.last-sha — skipping freshness check"
fi

echo "=== All checks passed ==="
```

- [ ] **Step 5.2: Run `bash check.sh` and verify the freshness section prints "0 src/ commits old"**

```bash
bash check.sh
```

Expected: all existing steps pass (secrets baseline, lint, type check, architecture, tests), then `=== Graph Freshness ===` prints `graphify-out is 0 src/ commits old (threshold: 10)`, then `=== All checks passed ===`. Exit 0.

Note: if `ruff` or `mypy` errors appear from unrelated pre-existing debt, stop and report — do not patch unrelated files in this task.

---

## Task 6: Create `docs/decisions/README.md`

**Files:**
- Create: `docs/decisions/README.md`

- [ ] **Step 6.1: Write the ADR index/readme**

```markdown
# Architecture Decision Records

One file per significant decision.

- Filename: `NNNN-kebab-case-title.md` (zero-padded, monotonically increasing).
- Sections: **Context**, **Decision**, **Consequences**, **Status** (Proposed / Accepted / Superseded by NNNN).
- Date the decision in the body, not the filename.

To change a decision, write a new ADR that supersedes the old one (set the old ADR's **Status** to "Superseded by NNNN"). Editing an accepted ADR in place is discouraged — the audit trail is the point.

## Index

- [0001 — Teams as a typed Python module, not a data file](0001-teams-as-typed-python-module.md)
- [0002 — Gmail iOS dark-mode defenses](0002-gmail-ios-dark-mode-blend-mode-hack.md)
- [0003 — Architecture tests as enforcement layer](0003-architecture-tests-as-enforcement-layer.md)
- [0004 — `docs/plans/` is read-only history](0004-docs-plans-is-read-only-history.md)
- [0005 — Agent-harness sizing](0005-agent-harness-sizing.md)
```

---

## Task 7: Create ADR 0001 — Teams as a typed Python module

**Files:**
- Create: `docs/decisions/0001-teams-as-typed-python-module.md`

- [ ] **Step 7.1: Write ADR 0001 verbatim**

```markdown
# 0001 — Teams as a typed Python module, not a data file

**Date:** 2026-04-19
**Status:** Accepted

## Context

MLB Digest supports all 30 MLB teams. Each team has several pieces of structured metadata: `team_id`, league/division, three theme colors, RSS feed URLs, an emoji, a narrator-personality one-liner, and identity strings (abbreviation, short name, full name). That payload is typed, tightly coupled to code that consumes it (narrator prompt, email template, CLI resolvers), and essentially static — MLB doesn't reshuffle teams often.

The choice was between holding this data in a plain Python module (`src/mlb_digest/teams_registry.py`) or in a data file (TOML, YAML, JSON) loaded at runtime.

## Decision

Hold the registry as a Python module. Export a `@dataclass(frozen=True)` `TeamInfo` and lookup helpers (`get_team`, `get_team_or_raise`, `list_teams`) that accept short name, abbreviation, or full name. Consumers import `TeamInfo` and receive a typed object; there is no string-keyed dict access in application code.

## Consequences

**Positive**

- Runtime type safety: mypy catches misspelled field names and wrong types before they reach the narrator or email template.
- IDE autocomplete on `team.primary_color`, `team.team_feed_urls`, etc.
- Refactor-safe: renaming a field propagates via editor rename, not search-and-replace across YAML.
- Colocation with the code that consumes it (`narrator.py`, `templates.py`, `config.py`).
- No runtime parsing cost, no file-not-found failure mode.

**Negative / trade-offs**

- Adding a team requires a code change, not a config edit. For a closed 30-team set this is fine; if the registry were user-extensible this choice would flip.
- The module is large (>300 lines) and is the single exemption from the 300-line cap enforced by `tests/test_architecture.py`. The exemption is documented in the test itself.

## Refs

- `src/mlb_digest/teams_registry.py`
- PR #1 (multi-team support)
- `AGENTS.md` — "Where to make common changes"
```

---

## Task 8: Create ADR 0002 — Gmail iOS dark-mode defenses

**Files:**
- Create: `docs/decisions/0002-gmail-ios-dark-mode-blend-mode-hack.md`

- [ ] **Step 8.1: Write ADR 0002 verbatim**

```markdown
# 0002 — Gmail iOS dark-mode defenses

**Date:** 2026-04-19
**Status:** Accepted

## Context

The Dugout Digest email template is intentionally dark-themed and team-branded. Gmail iOS applies three independent transformations to incoming HTML emails in dark mode, each of which breaks the branding unless defended against:

1. **Background-color inversion** — flat hex backgrounds (`background: #0d0d1a`) are auto-inverted to light colors.
2. **Text-color dimming** — even when backgrounds are preserved, text colors are dimmed/muted.
3. **`<style>` block stripping** — Gmail strips all but the first `<style>` element in the document.

## Decision

`src/mlb_digest/templates.py` stacks three targeted defenses, one per transformation:

1. **`linear-gradient(bg, bg)` backgrounds** (see `_dark_bg`) — Gmail inverts flat hex colors but leaves CSS gradients alone. Declaring a "gradient" between the same color forces Gmail to keep our palette.
2. **`mix-blend-mode` wrappers** (`gfix-screen` + `gfix-diff`, see `GFIX_OPEN` / `GFIX_CLOSE` / `_gfix`) — rehydrate the intended text color on top of whatever Gmail has decided the background is. The two blend modes (screen + difference) are layered because each handles a different dimming mode.
3. **Single leading `<style>` block** (see `GMAIL_BLEND_CSS`, first element in the rendered HTML) — holds all Gmail-targeted CSS. Uses the `u + .body` selector so only Gmail applies the blend rules (Gmail injects a `<u>` before the body wrapper); other clients ignore them.

## Consequences

**Positive**

- Template renders with the intended dark palette and text contrast in Gmail iOS.
- Other clients are unaffected — `linear-gradient` collapses visually to the underlying color, and `mix-blend-mode` wrappers are invisible without the Gmail-targeted selector.

**Negative / trade-offs**

- The CSS reads as cargo-cult without this ADR. Three defenses, three rationales, one file — easy to strip one out thinking it's redundant.
- Any future change to `templates.py` must preserve all three defenses, or at least knowingly opt out of one.
- Fragile if Gmail changes its dark-mode heuristics; breakage is detected only by sending a test email and opening it on iOS. There is no unit test for rendering fidelity.

## Refs

- `src/mlb_digest/templates.py` module docstring + `GFIX_OPEN`, `GFIX_CLOSE`, `GMAIL_BLEND_CSS`, `_dark_bg`
- Commits: `57d296f` (blend-mode fix for text), `999b629` (linear-gradient for backgrounds)
```

---

## Task 9: Create ADR 0003 — Architecture tests as enforcement layer

**Files:**
- Create: `docs/decisions/0003-architecture-tests-as-enforcement-layer.md`

- [ ] **Step 9.1: Write ADR 0003 verbatim**

```markdown
# 0003 — Architecture tests as enforcement layer

**Date:** 2026-04-19
**Status:** Accepted

## Context

The codebase has several invariants that are load-bearing but not expressed in the language itself:

- Layer dependency direction (`teams_registry`/`config` → `mlb_api`/`feeds` → `narrator` → `templates` → `emailer` → `cli`, no upward imports).
- Public functions in `mlb_api`, `feeds`, `config` must return dataclasses, not dicts.
- Public function signatures must declare return types (Click-decorated commands exempt).
- Custom exceptions end in `Error`, not `Exception`.
- No wildcard imports.
- Logging uses `%`-formatting, not f-strings (lazy + parseable).
- Non-data modules cap at 300 lines (`teams_registry` exempt — it's data).

These cannot be expressed in ruff alone without custom plugins, and putting them only in docs means they rot.

## Decision

Enforce via Python tests in `tests/test_architecture.py`. The tests use AST inspection and import analysis. They run as part of `bash check.sh` and in CI.

## Consequences

**Positive**

- Runs in CI and locally with zero new tooling.
- Failure messages can be specific and actionable ("module X imports Y but Y is at a higher layer — fix by moving X up or inverting the dependency").
- No dependency on custom ruff plugins (which would have to be written, packaged, and maintained).
- Tests are first-class code: refactor-safe, type-checked, easy to extend.

**Negative / trade-offs**

- Marginally slower than pure lint because of pytest startup overhead.
- Readers may be momentarily surprised that "tests" enforce style, not behavior. The test names are descriptive enough that the surprise is self-documenting.
- Test logic itself must be correct; a false negative silently erodes enforcement. The tests have their own review standard.

## Refs

- `tests/test_architecture.py`
- `AGENTS.md` — "Module layers (enforced by tests)"
- `check.sh` — `=== Architecture ===` step
```

---

## Task 10: Create ADR 0004 — `docs/plans/` is read-only history

**Files:**
- Create: `docs/decisions/0004-docs-plans-is-read-only-history.md`

- [ ] **Step 10.1: Write ADR 0004 verbatim**

```markdown
# 0004 — `docs/plans/` is read-only history

**Date:** 2026-04-19
**Status:** Accepted

## Context

`docs/plans/multi-team-files/` contains a snapshot of pre-merge design artifacts from the multi-team-support work: draft versions of `cli.py`, `config.py`, `teams_registry.py`, `narrator.py`, `templates.py`, example per-team TOML configs, and a draft test file. These files intentionally diverge from the current source tree. They are preserved as an audit trail of what was proposed vs. what shipped.

The directory is ruff-excluded in `pyproject.toml` (`extend-exclude = ["docs/plans/multi-team-files"]`), so it does not participate in lint. An agent or contributor discovering the directory without context could mistake it for a reference implementation and either edit the frozen files or copy outdated patterns into current code.

## Decision

Treat `docs/plans/multi-team-files/` (and anything else under `docs/plans/` of similar nature) as read-only history.

**Agents and contributors must NOT:**

- Edit files under `docs/plans/multi-team-files/`.
- Copy patterns from it into current source (patterns may be outdated; the current source is authoritative).
- Reference its files as examples of current conventions.

**Agents and contributors MAY:**

- Read it to understand design intent at the time of the PR.
- Reference it for historical context when explicitly asked.

## Consequences

**Positive**

- Design history preserved for audit and learning.
- Ruff exclusion prevents lint churn against frozen code.
- Explicit rules mean an agent discovering the directory has the context to avoid the trap.

**Negative / trade-offs**

- The directory will drift further from current source over time; that drift is expected and does not constitute a bug.
- An agent who skips this ADR and ignores `AGENTS.md` line 104 could still mistakenly treat the directory as current.

## Refs

- `docs/plans/multi-team-files/`
- `pyproject.toml:38` (`extend-exclude`)
- `AGENTS.md` — "Non-obvious things the graph (and source) reveal" bullet 8
```

---

## Task 11: Create ADR 0005 — Agent-harness sizing

**Files:**
- Create: `docs/decisions/0005-agent-harness-sizing.md`

- [ ] **Step 11.1: Write ADR 0005 verbatim**

```markdown
# 0005 — Agent-harness sizing

**Date:** 2026-04-19
**Status:** Accepted

## Context

The "Adding Harness Patterns to a Repo" ultraplan defines eight phases (0–7) of agent harness work: audit, repo-as-source-of-truth, session continuity, startup discipline, feedback loops, mechanical enforcement, isolation, and throughput policy. Not every repo needs every phase; the plan itself has explicit skip criteria.

This repo is:

- Single-user (one human runs all agents).
- Single-agent at a time (no parallel orchestration).
- CLI-only (no UI, no long-lived service).
- Python, with pre-existing CI (`check.sh`, GitHub Actions), architecture tests, `detect-secrets` baseline, and pre-commit hooks.

## Decision

Adopt phases 0–5 pragmatically. Skip phases 6 and 7.

- **Phase 0 — Audit.** This ADR is the audit.
- **Phase 1 — Repo as source of truth.** Already satisfied by `CLAUDE.md` (rules/style/commit policy), `AGENTS.md` (architecture facts), `README.md` (user-facing commands), and `docs/decisions/` (rationale). No separate `docs/architecture.md` or `docs/conventions.md` — they would duplicate existing docs.
- **Phase 2 — Session continuity.** Satisfied by `docs/superpowers/specs/` and `docs/plans/`, which persist through context clears. Spec-driven work is the continuity mechanism; a separate `claude-progress.txt` would duplicate what git history + committed specs already provide.
- **Phase 3 — Startup discipline.** Session start/end checklists prepended to `AGENTS.md`.
- **Phase 4 — Feedback loops.** `bash check.sh` bundles secrets baseline, lint (ruff), type check (mypy), architecture tests, and the full pytest suite. A non-blocking graph-freshness warning in `check.sh` surfaces `graphify-out/` staleness so `AGENTS.md`'s architecture facts do not silently diverge from `src/`. `/graphify` regeneration remains manual because it is an LLM call — too expensive to gate every commit.
- **Phase 5 — Mechanical enforcement.** `tests/test_architecture.py` (see ADR 0003) enforces layer direction, return-type rules, naming conventions, module-size caps.
- **Phase 6 — Isolation / worktrees.** Skipped. Single agent at a time; no parallel-agent contention to isolate against.
- **Phase 7 — Throughput policy.** Skipped. Single user; automerge and minimal-review gates would create risk without throughput benefit.

## Consequences

**Positive**

- The harness is sized to observed needs, not speculative ones.
- Skipped phases are named and justified, not silently absent.
- Future revisits have a decision matrix to update rather than starting from scratch.

**Negative / trade-offs**

- If any of the "triggers for revisit" fire, some harness work will be retrofitted under time pressure rather than put in place proactively.

## Triggers for revisit

Write a new ADR that supersedes this one if any of the following become true:

- Multi-agent orchestration is introduced (revisit Phase 6).
- A UI is added (revisit Phase 4 — browser feedback loop).
- A long-lived service is deployed (revisit Phase 4 — observability hooks).
- More than one concurrent contributor (revisit Phase 7).

## Refs

- `docs/superpowers/specs/2026-04-19-harness-patterns-design.md`
- `CLAUDE.md`, `AGENTS.md`, `README.md`
- `tests/test_architecture.py`
- `check.sh`
```

---

## Task 12: Local verification (pre-commit)

- [ ] **Step 12.1: Confirm staged + unstaged state**

```bash
git status
```

Expected: `AGENTS.md`, `check.sh`, `.gitignore` modified; `init.sh`, `graphify-out/.last-sha`, and all of `docs/decisions/*.md` untracked. Nothing staged yet.

- [ ] **Step 12.2: Run `bash check.sh` on the current checkout**

```bash
bash check.sh
```

Expected: all sections pass, including the new `=== Graph Freshness ===` section reporting `0 src/ commits old (threshold: 10)`, then `=== All checks passed ===`. Exit 0.

If any section fails: stop and diagnose. Do NOT patch unrelated debt in this plan.

---

## Task 13: Stage and commit everything

**Files:**
- Commit: all files changed or created by tasks 1–11.

- [ ] **Step 13.1: Stage the changes**

```bash
git add AGENTS.md init.sh check.sh .gitignore \
        graphify-out/.last-sha \
        docs/decisions/README.md \
        docs/decisions/0001-teams-as-typed-python-module.md \
        docs/decisions/0002-gmail-ios-dark-mode-blend-mode-hack.md \
        docs/decisions/0003-architecture-tests-as-enforcement-layer.md \
        docs/decisions/0004-docs-plans-is-read-only-history.md \
        docs/decisions/0005-agent-harness-sizing.md
```

Verify nothing unexpected staged:

```bash
git status
```

Expected: 11 files staged. `graphify-out/GRAPH_REPORT.md` and the rest of `graphify-out/` remain untracked (the `.gitignore` rule keeps them hidden; only `.last-sha` is un-ignored).

- [ ] **Step 13.2: Commit with HEREDOC message**

```bash
git commit -m "$(cat <<'EOF'
chore: add agent harness (checklists, init.sh, ADRs)

Implements docs/superpowers/specs/2026-04-19-harness-patterns-design.md
(approach A: fill gaps, skip phases 6-7).

- AGENTS.md: prepend Session start / Session end checklists
- init.sh: fresh-clone -> runnable (uv sync, .env scaffold, pre-commit)
- check.sh: append non-blocking graph-freshness warning
- .gitignore: un-ignore graphify-out/.last-sha
- graphify-out/.last-sha: seed staleness tracker at current HEAD
- docs/decisions/: README + ADRs 0001-0005
    0001 teams as typed python module, not a data file
    0002 gmail ios dark-mode defenses (three mechanisms)
    0003 architecture tests as enforcement layer
    0004 docs/plans/ is read-only history
    0005 agent-harness sizing (why 0-5 adopted, 6-7 skipped)

Companion (out-of-repo): /graphify skill at ~/.claude/skills/graphify/
must be updated to auto-run postprocess.py and write HEAD to
graphify-out/.last-sha. Without that the staleness counter only resets
when the SHA is manually bumped.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 13.3: Verify commit landed and pre-commit hook passed**

```bash
git log --oneline -3
git show --stat HEAD
```

Expected: new commit on top of `chore/harness-patterns`, all 11 files listed. Pre-commit hook output in the commit step shows `Detect secrets Passed` and `architecture & taste enforcement Passed`.

If `detect-secrets` warns about baseline drift: run `uv run detect-secrets scan --baseline .secrets.baseline`, then `git add .secrets.baseline`, then amend with `git commit --amend --no-edit` (per `CLAUDE.md`, this is the one allowed amend case — before push).

---

## Task 14: Fresh-clone smoke test

This is the step the spec's Verification section calls out: exercise `init.sh` on a true fresh clone, not the warm repo. Runs against the local branch — no push required because `git clone` accepts a local path.

- [ ] **Step 14.1: Clone the branch into a temp dir and run init.sh + check.sh**

```bash
WORK=$(mktemp -d)
echo "smoke dir: $WORK"
git clone -b chore/harness-patterns "$(pwd)" "$WORK/braves"
pushd "$WORK/braves"
bash init.sh
[ -f .env ] || { echo "FAIL: init.sh did not create .env"; exit 1; }
[ -d .venv ] || { echo "FAIL: uv sync did not create .venv"; exit 1; }
# .env was created from .env.example and has placeholder values — check.sh
# does not require real secrets (it only scans the baseline, doesn't send email).
bash check.sh
popd
echo "smoke clone still at: $WORK  (remove when done)"
```

Expected output (abridged):
- `Cloning into '…/braves'...` with no errors.
- `init.sh` prints `Created .env from .env.example.` (this is a fresh clone, so `.env` is absent), then `Ready.`.
- `.env` and `.venv` exist after `init.sh`.
- `check.sh` runs end-to-end: secrets baseline passes, ruff passes, mypy passes, architecture tests pass, pytest suite passes, graph freshness prints `0 src/ commits old`, `=== All checks passed ===`.

- [ ] **Step 14.2: Clean up the smoke clone**

```bash
rm -rf "$WORK"
```

If `check.sh` fails in the fresh clone but passes in the warm repo, STOP — that divergence is a real bug in `init.sh` or a missed dependency, and it's exactly what the smoke test exists to catch.

---

## Task 15: Push and open PR

- [ ] **Step 15.1: Push the branch**

```bash
git push -u origin chore/harness-patterns
```

Expected: push succeeds; remote prints a "Create pull request" hint with a URL.

- [ ] **Step 15.2: Open PR against `master` via `gh`**

```bash
gh pr create --base master --title "chore: add agent harness (checklists, init.sh, ADRs)" --body "$(cat <<'EOF'
## Summary
- Implements `docs/superpowers/specs/2026-04-19-harness-patterns-design.md` (approach A).
- Adds session start/end checklists to `AGENTS.md`, `init.sh` for fresh-clone bootstrapping, non-blocking graph-freshness warning in `check.sh`, and five backfilled ADRs.
- Phases 6 (worktree isolation) and 7 (throughput policy) are explicitly skipped per ADR 0005.

## Test plan
- [x] `bash check.sh` passes on the warm repo
- [x] Fresh-clone smoke: `git clone` to temp dir, `bash init.sh`, `bash check.sh` — all pass
- [ ] CI `check` job green
- [ ] CI `smoke-test` job green

## Companion change (out of repo)
The `/graphify` skill at `~/.claude/skills/graphify/SKILL.md` must be updated to auto-run `graphify-out/postprocess.py` and write the current `git rev-parse HEAD` to `graphify-out/.last-sha`. Without that change the staleness counter in `check.sh` only resets when the SHA is manually bumped. Tracking the skill change separately because the skill dir isn't part of this repo.

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Expected: `gh` returns the PR URL. Paste it into the session output.

- [ ] **Step 15.3: Wait for CI, then squash-merge**

- Poll with `gh pr checks --watch` or view in the browser.
- Both `check` and `smoke-test` jobs must be green before merge (per `CLAUDE.md` — merge policy).
- Merge via `gh pr merge --squash --delete-branch` once green.

Stop here if a CI job fails — diagnose before merging.

---

## Post-merge (informational, not a coded step)

The companion update to `~/.claude/skills/graphify/SKILL.md` is user-scoped and out of this repo. Once merged, the skill should be updated so that every `/graphify` run:

1. Executes `py graphify-out/postprocess.py` automatically after graph generation.
2. Writes the current `git rev-parse HEAD` to `graphify-out/.last-sha` and stages it for the next commit.

Without that update the `check.sh` staleness counter never resets on its own.

---

## Spec coverage self-check

| Spec deliverable | Task |
|---|---|
| `AGENTS.md` checklist prepend | Task 1 |
| `init.sh` | Task 2 |
| `check.sh` edit (freshness warning) | Task 5 |
| `.gitignore` edit (un-ignore `.last-sha`) | Task 3 |
| `graphify-out/.last-sha` seed | Task 4 |
| `docs/decisions/README.md` | Task 6 |
| ADR 0001 (teams as typed module) | Task 7 |
| ADR 0002 (Gmail iOS defenses) | Task 8 |
| ADR 0003 (architecture tests) | Task 9 |
| ADR 0004 (`docs/plans/` read-only) | Task 10 |
| ADR 0005 (harness sizing) | Task 11 |
| Warm-repo + fresh-clone verification | Tasks 12, 14 |
| Single commit on `chore/harness-patterns` | Task 13 |
| PR against `master`, squash-merge | Task 15 |
