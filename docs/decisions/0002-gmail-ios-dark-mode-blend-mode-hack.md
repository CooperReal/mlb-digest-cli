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
- Commits: `999b629` (initial dark-mode inversion fix, PR #4), `57d296f` (blend-mode for text + linear-gradient backgrounds, PR #5)
