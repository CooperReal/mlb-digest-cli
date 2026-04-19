# Harness Patterns — Design

**Date:** 2026-04-19
**Status:** Approved
**Scope:** MLB Digest CLI (single-user, single-agent, CLI/no-UI)

Adapted application of the "Adding Harness Patterns to a Repo" ultraplan. Approach A: fill real gaps, skip phases whose skip criteria apply, note what's already covered. Phases 6 (isolation) and 7 (throughput) are skipped per the plan's own skip criteria for single-agent workflows.

## Goals

1. Close the gaps in the repo's agent harness that are not already covered by `CLAUDE.md`, `AGENTS.md` (untracked), `check.sh`, `tests/test_architecture.py`, or CI.
2. Capture *why* this harness is sized the way it is (ADR 0005) so a future agent can tell which phases were deliberate skips vs. oversights.
3. Keep the additions small and load-bearing — no cargo-culting.

## Non-goals

- Replacing or duplicating `CLAUDE.md` / existing `AGENTS.md` content.
- Adding `docs/architecture.md` — `AGENTS.md` already serves that role.
- Adding `docs/conventions.md` — `CLAUDE.md` already serves that role.
- Isolation tooling (git worktree per task) — single-agent repo.
- Throughput-shaped policy (automerge, minimal review gates) — single-user repo.

## Deliverables

| File | Status | Purpose |
|---|---|---|
| `AGENTS.md` | edit (untracked → tracked) | Prepend **Session start** / **Session end** checklists |
| `init.sh` | new | Fresh-clone → runnable in one command; idempotent |
| `check.sh` | edit | Append non-blocking graph-freshness warning |
| `.gitignore` | edit | Un-ignore `graphify-out/.last-sha` only |
| `docs/decisions/README.md` | new | ADR template + numbering + append-only rule |
| `docs/decisions/0001-teams-as-typed-python-module.md` | new | Backfill ADR |
| `docs/decisions/0002-gmail-ios-dark-mode-blend-mode-hack.md` | new | Backfill ADR |
| `docs/decisions/0003-architecture-tests-as-enforcement-layer.md` | new | Backfill ADR |
| `docs/decisions/0004-docs-plans-is-read-only-history.md` | new | Backfill ADR — flag the legacy-plans trap |
| `docs/decisions/0005-agent-harness-sizing.md` | new | Why phases 6–7 of the ultraplan are skipped; how to know when to revisit |

**Explicitly not adding:** `docs/architecture.md`, `docs/conventions.md`, worktree tooling, automerge policy.

## Component details

### 1. `AGENTS.md` checklist prepend

Inserted immediately after the intro paragraph, before "What this repo does":

```
## Session start checklist

1. `pwd` — confirm you're in the repo root (C:\Users\cooper\braves)
2. `git log --oneline -20` and `git status`
3. Check `docs/superpowers/specs/` and `docs/plans/` for the newest spec or plan touching your task. If you were mid-task when context cleared, the spec is the source of truth — re-read it before resuming.
4. `bash init.sh` (idempotent — safe to re-run)
5. `bash check.sh` — if red, fix before starting new work

## Session end checklist

1. `bash check.sh` passes (or failures are documented somewhere in-repo, not in a memory scratchpad)
2. If work is mid-flight, make sure the active spec/plan in `docs/superpowers/specs/` or `docs/plans/` reflects reality — update it in the same commit as the code, not in a side log
3. Branch pushed, PR open, CI green before merge (see CLAUDE.md — squash-only)
```

Rest of `AGENTS.md` unchanged. The file transitions from untracked to tracked in the same commit.

### 2. `init.sh`

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

Invoked as `bash init.sh` (matches the repo's `bash check.sh` convention — no reliance on Windows exec-bit preservation). **Not** in `init.sh`: running the test suite (that's `check.sh`), touching `.secrets.baseline` (pre-commit handles it), anything requiring network beyond `uv sync`.

### 3. Graph-freshness warning

**Problem.** `graphify-out/` is the backing store for `AGENTS.md`'s architecture facts. It gets stale as `src/` evolves, but regenerating (`/graphify`) is an LLM call — too expensive to gate every commit. Current state: staleness is invisible until someone spot-checks `AGENTS.md` against the code.

**Fix.** Make staleness visible, let the human/agent decide when to refresh.

**`check.sh` append (last step, warning only):**

```bash
# Graph freshness — warn only, never fail.
if [ -f graphify-out/.last-sha ]; then
  LAST_SHA=$(cat graphify-out/.last-sha)
  STALE=$(git rev-list --count "${LAST_SHA}..HEAD" -- src/ 2>/dev/null || echo 0)
  if [ "${STALE}" -gt 10 ]; then
    echo "⚠ graphify-out is ${STALE} src/ commits stale — run /graphify after your next feature"
  fi
fi
```

**`.gitignore` edit.** Add a negation line so the marker file is tracked:

```
graphify-out/
!graphify-out/.last-sha
```

**Seed content.** Commit `graphify-out/.last-sha` containing the current HEAD SHA (the SHA of the last known-good graph, which is now). This way the staleness counter starts at 0, not at a missing file.

**Out-of-repo companion (required but not in this commit).** The `/graphify` skill at `~/.claude/skills/graphify/SKILL.md` must be updated so every run:
1. Auto-invokes `py graphify-out/postprocess.py` after graph generation.
2. Writes the current `git rev-parse HEAD` to `graphify-out/.last-sha` and stages it.

Without that companion update the staleness counter only ever resets when you manually bump `.last-sha`. The spec calls out this dependency; the skill change is tracked separately because `~/.claude/skills/` isn't part of this repo.

### 4. ADRs

**`docs/decisions/README.md`**

```md
# Architecture Decision Records

One file per significant decision.

- Filename: `NNNN-kebab-case-title.md` (zero-padded, monotonically increasing)
- Sections: **Context**, **Decision**, **Consequences**, **Status** (Proposed / Accepted / Superseded by NNNN)
- Date the decision in the body, not the filename

To change a decision, write a new ADR that supersedes the old one (set the old ADR's **Status** to "Superseded by NNNN"). Editing an accepted ADR in place is discouraged — the audit trail is the point.
```

**Four backfill ADRs** — written as full prose, not skeletons:

1. **0001 — Teams as a typed Python module, not a data file.** Why `teams_registry.py` (a Python module exporting `TeamInfo` dataclass instances) instead of TOML/YAML/JSON. Rationale: runtime type safety, IDE autocomplete on field access, symbol-not-string references (refactor-safe), colocation with the code that consumes it. Source-of-truth-ness follows from the choice — it isn't the decision. Ref: multi-team support PR #1.
2. **0002 — Gmail iOS dark-mode defenses.** Three independent mechanisms in `templates.py`, each with its own cause:
   - `linear-gradient` backgrounds — Gmail iOS inverts flat hex backgrounds but leaves gradients alone; using a "gradient" between the same colour forces Gmail to keep our palette.
   - `mix-blend-mode` wrappers (`gfix-screen`, `gfix-diff`) — Gmail dims text colours even when it leaves backgrounds alone; blend-mode wrappers rehydrate the intended text colour on top of whatever Gmail has decided the background is.
   - Single leading `<style>` block — Gmail strips all but the first `<style>` element, so every selector has to live together at the top of the document.
   Refs commits `57d296f`, `999b629`. Without this ADR the CSS reads as cargo-cult.
3. **0003 — Architecture tests as enforcement layer.** Why layer boundaries, dataclass-return rules, and naming conventions live in `tests/test_architecture.py` rather than ruff plugins or docs. Fails in CI with a specific remediation message; lint plugins would need to be custom-written; docs drift.
4. **0004 — `docs/plans/` is read-only history.** `docs/plans/multi-team-files/` is a snapshot of pre-merge design artifacts, kept for audit. It is ruff-excluded (`pyproject.toml:38`) and intentionally diverges from current source. **Agents must not copy patterns from it or edit its contents.** The ADR exists so a future agent discovering the directory has the context to avoid treating it as a reference.
5. **0005 — Agent-harness sizing.** Which ultraplan phases this repo adopts vs skips, and why. Phase 6 (worktree isolation) and Phase 7 (throughput policy) are skipped because this is a single-user single-agent repo. Phase 4 feedback loops are satisfied by `check.sh` + `tests/test_architecture.py` plus the **graph-freshness warning** (non-blocking, in `check.sh`) — the graph is the substrate for `AGENTS.md`'s architecture facts, and keeping it fresh is a Phase 4 concern even though the regeneration itself (`/graphify`) is manual. Phase 5 mechanical enforcement is satisfied by the architecture tests. The ADR spells this out so a future pass — say, after the repo gains multi-agent orchestration or a UI — knows exactly which row of the decision matrix has changed and can be superseded. **Triggers for revisit:** multi-agent orchestration introduced, a UI added, long-lived service deployed, or >1 concurrent contributor.

(Squash-only merge policy is not a separate ADR — it's stated in `CLAUDE.md` and the rationale reduces to "that's how the repo is configured.")

### 5. Branch + commit strategy

- **Branch:** `chore/harness-patterns`
- **Single commit** bundling all deliverables (squash-merge erases per-file commit granularity anyway).
- **Commit subject:** `chore: add agent harness (audit, session continuity, ADRs)`
- **PR:** against `master`, wait for CI (`check` + `smoke-test`) green, squash-merge.
- `bash check.sh` passes locally before push. Pre-commit hooks run normally. If `check.sh` warns about the secrets baseline, run `detect-secrets scan --baseline .secrets.baseline` and `git add .secrets.baseline` before committing (per `CLAUDE.md`). No `--no-verify`.
- **Not doing:** separate PR per phase, direct commits to `master`.

## Risks / constraints

- **`AGENTS.md` line count.** Prepending checklists pushes the file from ~140 to ~160 lines. Still under the ~200 budget the ultraplan suggests. Acceptable.
- **ADR backfill accuracy.** Rationales are derived from current code + commit messages. If a past decision's real rationale differs, ADRs should be corrected before acceptance.
- **None of the new files are loaded at runtime.** All additions are docs or dev-time scripts. No impact on the digest hot path or existing tests.

## Verification

Before PR:

```bash
# 1. Full lint/type/test suite.
bash check.sh

# 2. Warm-repo idempotency — init.sh on the current checkout must be a no-op.
bash init.sh

# 3. Fresh-clone smoke — this is the path init.sh actually exists to serve.
#    Branch must already be pushed for this step to work.
WORK=$(mktemp -d)
git clone -b chore/harness-patterns "$(pwd)" "$WORK/braves"
pushd "$WORK/braves"
bash init.sh                       # must succeed
[ -f .env ] || { echo "init.sh did not create .env"; exit 1; }
[ -d .venv ] || { echo "uv sync did not create .venv"; exit 1; }
bash check.sh                      # must pass in the fresh clone too
popd
rm -rf "$WORK"
```

No new tests required — none of the additions are runtime code.

## Acceptance

Ship when:

1. All files in the deliverables table exist, committed on branch `chore/harness-patterns`.
2. `bash check.sh` passes locally.
3. PR opened against `master`, both CI jobs green.
4. You approve the ADR rationales after reading them.
