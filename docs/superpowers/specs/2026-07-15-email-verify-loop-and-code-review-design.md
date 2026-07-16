# Email Verification Loop & Codebase Review — Design

**Date:** 2026-07-15
**Status:** Approved

## Context

The digest email template carries three Gmail dark-mode defenses (linear-gradient
backgrounds, blend-mode text fix, Gmail-scoped CSS — see ADR 0002). But there is no way
to see the rendered email without sending one, dark-mode correctness has zero automated
verification, and the current rendering state is unknown. The digest is read in the
Gmail iOS app (dark mode) and Gmail web.

## Goals

1. A repeatable loop: make a change → render → screenshot → share back in chat.
2. Establish a baseline: confirm how the current email actually renders today.
3. Extensive code review: fix real bugs and rewrite existing code to the project style
   rules (simple, explicit, no/minimal list comprehensions, comments only when needed).
4. Keep everything simple — no new heavy dependencies.

## Non-Goals

- Pixel-perfect emulation of Gmail iOS color inversion.
- CI visual-regression testing (rejected: heavy dependencies, flaky pixel diffs).
- Sending a real email on every iteration (real send is the final check only).

## Design

### 1. `preview` subcommand

`uv run mlb-digest preview` renders the real template from canned sample data and
writes the result to local files. No API calls, no Claude call — works offline.

- Sample data lives at `src/mlb_digest/sample_digest.md` (package data). It contains
  every element the narrator produces: headings, a standings table, links, a score
  line, and the badge.
- Output goes to `preview/` (gitignored):
  - `preview.html` — the email exactly as `render_email_html()` builds it.
  - `preview-gmail-dark.html` — the same HTML wrapped in a harness that mimics
    Gmail's DOM (see below).

### 2. Gmail dark harness

The harness wraps the email HTML with the DOM structure Gmail's apps produce — a
`<u></u>` sibling plus a `.body`-classed wrapper — on a dark Gmail-style page
background. This activates the ADR-0002 blend-mode defenses in Chrome.

**Caveat (accepted):** the harness verifies our defenses fire and text stays legible.
It does not replicate Gmail iOS's exact color transformation. The final real-send
check plus a manual iOS glance covers the gap.

### 3. `test-email` upgrade

`test-email` currently sends throwaway HTML that never exercises the template. It will
instead send the real template rendered from the same sample data, so the final check
tests exactly what production sends.

### 4. `email-check` project skill

`.claude/skills/email-check/SKILL.md` documents the loop so any future session repeats
it:

1. Run `uv run mlb-digest preview`.
2. Open both preview files in Chrome, screenshot, share back in chat.
3. Iterate until correct.
4. Final check: `uv run mlb-digest test-email`, open Gmail web in Chrome, screenshot
   the delivered email, share back. User glances at Gmail iOS when convenient.

### 5. Code review process

- Parallel review subagents sweep all modules (`cli`, `config`, `mlb_api`, `feeds`,
  `narrator`, `emailer`, `templates`) on three lenses: correctness bugs,
  style-vs-rules, dead code/debt.
- Every finding is adversarially verified before it becomes a fix.
- Known debt already queued: dead `_gfix()` in templates.py, unused `secondary_color`
  parameter, no SMTP timeout in emailer.py, `test-email` throwaway body (fixed by §3).

### 6. Style rules made permanent

Added to CLAUDE.md so they bind every future session:

- No/minimal list comprehensions — prefer explicit `for` loops.
- Comments only when needed; code should explain itself.

### 7. Testing

- Every bug fix ships with a test that reproduces the bug first (TDD).
- Style-only rewrites are covered by the existing test suite, which must stay green;
  pure refactors need no new tests.
- Template changes are additionally verified visually through the preview loop.
- `bash check.sh` (lint + mypy + pytest) must pass before every commit.

## Delivery

Before any changes: baseline — find the most recent digest in Gmail web via Chrome,
screenshot it, assess the current state.

Two PRs, squash-merged per repo policy:

1. **PR 1:** `preview` subcommand + sample data + `test-email` upgrade + `email-check`
   skill + this spec. Merged first so the verification loop exists.
2. **PR 2:** review fixes + style cleanup, verified with that loop.

## Success Criteria

- `preview` produces both files offline.
- Screenshots shared in chat show correct colors in both plain and gmail-dark views.
- Delivered test email renders correctly in Gmail web; user confirms iOS looks right.
- `check.sh` passes; queued debt is gone; style rules live in CLAUDE.md.
