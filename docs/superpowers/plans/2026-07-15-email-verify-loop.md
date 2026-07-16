# Email Verification Loop & Codebase Review Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a render → screenshot → share verification loop for the digest email, then run an extensive code review and style cleanup verified with that loop.

**Architecture:** A new `preview.py` module (layer 3, beside `templates`) renders the real template from canned sample markdown into two local HTML files — plain, and wrapped in a Gmail-like DOM harness that activates the ADR-0002 blend-mode defenses. The CLI gains a `preview` subcommand; `test-email` is upgraded to send the real template. A project skill documents the loop. Delivered as two squash-merged PRs: tooling first, review fixes second.

**Tech Stack:** Python 3.11+, Click, importlib.resources for package data, pytest, claude-in-chrome for screenshots.

**Spec:** `docs/superpowers/specs/2026-07-15-email-verify-loop-and-code-review-design.md`

---

## File Structure

**Part A (PR 1, branch `email-verify-loop`):**
- Create: `src/mlb_digest/sample_digest.md` — canned narrative exercising every template element
- Create: `src/mlb_digest/preview.py` — sample loading, Gmail-dark harness, preview file writing
- Create: `tests/test_preview.py`
- Create: `.claude/skills/email-check/SKILL.md` — the documented loop
- Modify: `src/mlb_digest/cli.py` — add `preview` command; upgrade `test_email`
- Modify: `tests/test_cli.py` — tests for both
- Modify: `tests/test_architecture.py:29-38` — register `preview` in `LAYER`
- Modify: `pyproject.toml` — package data for the `.md` file
- Modify: `.gitignore` — ignore `preview/`

**Part B (PR 2, branch `code-review-fixes`):**
- Modify: `CLAUDE.md` — permanent style rules
- Modify: `src/mlb_digest/templates.py` — remove dead `_gfix()`, remove `secondary_color`
- Modify: `src/mlb_digest/cli.py` — drop `secondary_color` arg, explicit loops in `list-teams`
- Modify: `src/mlb_digest/emailer.py` — SMTP timeout
- Modify: `src/mlb_digest/config.py` — explicit loop in `_parse_recipients`
- Modify: `tests/test_emailer.py` — timeout test
- Plus fixes for confirmed findings from the review sweep (Task 14)

---

## Part A — PR 1: the verification loop

> **STATUS: Part A landed as PR 1 — do not re-execute these tasks.** Deviations from
> the original steps, applied during review: the `preview/` gitignore line was pulled
> forward from Task 6 into its own commit; the preview.py module docstring was scoped
> to current behavior and grows with each task; the heading assertions in
> test_preview.py are line-anchored (`"\n## "`); the preview CLI test hardens
> `validate_secrets` with a side_effect guard. Task 0 (Gmail baseline screenshot) was
> deferred — Chrome extension unavailable; runs before Part B.

### Task 0: Baseline — screenshot the current email in Gmail web

No code. Establishes ground truth before any changes.

- [ ] **Step 1:** Invoke the `claude-in-chrome` skill, load browser tools via one ToolSearch call.
- [ ] **Step 2:** Get tab context, open a new tab to `https://mail.google.com`, search for `Dugout Digest` (fall back to `Braves Daily`).
- [ ] **Step 3:** Open the most recent digest, screenshot the full email, share it in chat.
- [ ] **Step 4:** Note in chat what looks right/wrong (text legibility, background colors, accent stripe, table rows). Anything broken becomes a finding for Part B.

### Task 1: Sample digest + `preview.py` module with `load_sample_digest()`

**Files:**
- Create: `src/mlb_digest/sample_digest.md`
- Create: `src/mlb_digest/preview.py`
- Create: `tests/test_preview.py`
- Modify: `pyproject.toml` (after line 33)
- Modify: `tests/test_architecture.py:29-38`

- [x] **Step 1: Write the failing test**

Create `tests/test_preview.py`:

```python
from mlb_digest.preview import load_sample_digest


def test_load_sample_digest_contains_all_template_elements():
    sample = load_sample_digest()

    assert "## " in sample
    assert "### " in sample
    assert "**" in sample
    assert "](http" in sample
    assert "| Team |" in sample
    assert "\n- " in sample
    assert "\n---\n" in sample
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_preview.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'mlb_digest.preview'`

- [x] **Step 3: Create the sample markdown**

Create `src/mlb_digest/sample_digest.md`:

```markdown
## GAME RECAP

**Braves 5, Phillies 3** — Atlanta took the series opener behind a dominant start.

The offense woke up in the sixth when [Ronald Acuna Jr.](https://www.mlb.com/player/660670) launched a two-run shot to left. Spencer Strider struck out nine over six innings and the bullpen closed it out without drama.

### Player of the Game

Acuna finished 3-for-4 with a homer, a double, and two runs scored.

## STANDINGS

| Team | W | L | GB |
| --- | --- | --- | --- |
| Phillies | 55 | 38 | — |
| Braves | 52 | 41 | 3.0 |
| Mets | 48 | 45 | 7.0 |

## NEWS & NOTES

- The Braves activated a reliever from the injured list before the game.
- [Trade rumor roundup](https://www.mlbtraderumors.com) — Atlanta linked to bullpen help ahead of the deadline.
- Prospect watch: the system's top arm struck out 11 in Double-A.

---

## ON DECK

Tonight, 7:20 PM ET at Truist Park. Braves send their ace to the mound against the Phillies' lefty.
```

- [x] **Step 4: Create the module**

Create `src/mlb_digest/preview.py`:

```python
"""
Preview rendering for the email template.

Writes the rendered email to local HTML files so it can be inspected in a
browser without sending anything. The gmail-dark variant reproduces the DOM
Gmail builds around an email (a <u> element followed by a .body-classed
wrapper) so the ADR-0002 blend-mode defenses activate in a normal browser.
"""

import re
from importlib import resources
from pathlib import Path

from mlb_digest.config import Config
from mlb_digest.templates import GMAIL_BLEND_CSS, render_email_html

GMAIL_DARK_PAGE_BG = "#121212"


def load_sample_digest() -> str:
    """Return the canned sample digest markdown shipped with the package."""
    sample_file = resources.files("mlb_digest").joinpath("sample_digest.md")
    return sample_file.read_text(encoding="utf-8")
```

- [x] **Step 5: Ship the markdown as package data**

In `pyproject.toml`, after the `[tool.setuptools.packages.find]` block (line 32-33), add:

```toml
[tool.setuptools.package-data]
mlb_digest = ["*.md"]
```

- [x] **Step 6: Register the module in the architecture layers**

In `tests/test_architecture.py`, change the `LAYER` dict (line 29) to include `preview` at layer 3 (it imports `templates`, layer 3, and `config`, layer 0):

```python
LAYER: dict[str, int] = {
    "teams_registry": 0,
    "config": 0,
    "mlb_api": 1,
    "feeds": 1,
    "narrator": 2,
    "templates": 3,
    "preview": 3,
    "emailer": 4,
    "cli": 5,
}
```

- [x] **Step 7: Run tests to verify they pass**

Run: `uv run pytest tests/test_preview.py tests/test_architecture.py -v`
Expected: PASS (architecture tests now include `preview` and find `tests/test_preview.py`)

- [x] **Step 8: Commit**

```bash
bash check.sh && git add -A && git commit -m "feat: add preview module with sample digest data"
```

### Task 2: Gmail dark harness

**Files:**
- Modify: `src/mlb_digest/preview.py`
- Modify: `tests/test_preview.py`

- [x] **Step 1: Write the failing tests**

Update the imports at the top of `tests/test_preview.py` to:

```python
import pytest

from mlb_digest.preview import load_sample_digest, wrap_in_gmail_dark_harness
from mlb_digest.templates import render_email_html
```

Then add:

```python
def test_gmail_dark_harness_wraps_body_in_gmail_dom():
    email_html = render_email_html("## HELLO\n\nWorld.")

    harness = wrap_in_gmail_dark_harness(email_html)

    assert "<u></u>" in harness
    assert '<div class="body"' in harness
    assert "#121212" in harness
    assert "World." in harness


def test_gmail_dark_harness_keeps_blend_mode_css():
    email_html = render_email_html("Hello.")

    harness = wrap_in_gmail_dark_harness(email_html)

    assert "mix-blend-mode:screen" in harness
    assert "mix-blend-mode:difference" in harness


def test_gmail_dark_harness_rejects_html_without_body_class():
    with pytest.raises(ValueError, match="no <body"):
        wrap_in_gmail_dark_harness("<html><body>plain</body></html>")
```

- [x] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_preview.py -v`
Expected: FAIL — `ImportError: cannot import name 'wrap_in_gmail_dark_harness'`

- [x] **Step 3: Implement the harness**

Add to `src/mlb_digest/preview.py`:

```python
def wrap_in_gmail_dark_harness(email_html: str) -> str:
    """Rebuild the email inside a Gmail-like DOM so the blend-mode CSS activates."""
    match = re.search(r'<body class="body"(.*?)>(.*)</body>', email_html, flags=re.DOTALL)
    if match is None:
        raise ValueError('email HTML has no <body class="body"> element')

    body_attrs = match.group(1)
    body_content = match.group(2)
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>"
        '<meta charset="utf-8">'
        f"{GMAIL_BLEND_CSS}"
        "</head>\n"
        f'<body style="margin:0; padding:0; background:{GMAIL_DARK_PAGE_BG};">\n'
        "<u></u>\n"
        f'<div class="body"{body_attrs}>\n'
        f"{body_content}\n"
        "</div>\n"
        "</body>\n"
        "</html>"
    )
```

- [x] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_preview.py -v`
Expected: PASS

- [x] **Step 5: Commit**

```bash
bash check.sh && git add -A && git commit -m "feat: add Gmail dark-mode DOM harness for previews"
```

### Task 3: `write_preview_files()`

**Files:**
- Modify: `src/mlb_digest/preview.py`
- Modify: `tests/test_preview.py`

- [x] **Step 1: Write the failing test**

Add to `tests/test_preview.py` (add `from unittest.mock import MagicMock` and
`from mlb_digest.preview import write_preview_files` to the imports):

```python
def test_write_preview_files_creates_plain_and_dark_files(tmp_path):
    config = MagicMock()
    config.full_team_name = "Atlanta Braves"
    config.team_colors = {"primary": "#13274F", "accent": "#CE1141"}
    config.team_emoji = "⚾"

    written = write_preview_files(config, tmp_path)

    plain_file = tmp_path / "preview.html"
    dark_file = tmp_path / "preview-gmail-dark.html"
    assert written == [plain_file, dark_file]
    assert "Atlanta Braves" in plain_file.read_text(encoding="utf-8")
    assert "<u></u>" in dark_file.read_text(encoding="utf-8")
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_preview.py -v`
Expected: FAIL — `ImportError: cannot import name 'write_preview_files'`

- [x] **Step 3: Implement**

Add to `src/mlb_digest/preview.py`:

```python
def write_preview_files(config: Config, output_dir: Path) -> list[Path]:
    """Render the sample digest and write plain + gmail-dark preview files."""
    sample_md = load_sample_digest()
    email_html = render_email_html(
        sample_md,
        team_name=config.full_team_name,
        primary_color=config.team_colors.get("primary", "#333333"),
        accent_color=config.team_colors.get("accent", "#cc0000"),
        emoji=config.team_emoji,
    )
    harness_html = wrap_in_gmail_dark_harness(email_html)

    output_dir.mkdir(parents=True, exist_ok=True)
    plain_path = output_dir / "preview.html"
    dark_path = output_dir / "preview-gmail-dark.html"
    plain_path.write_text(email_html, encoding="utf-8")
    dark_path.write_text(harness_html, encoding="utf-8")
    return [plain_path, dark_path]
```

- [x] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_preview.py -v`
Expected: PASS

- [x] **Step 5: Commit**

```bash
bash check.sh && git add -A && git commit -m "feat: write plain and gmail-dark preview files"
```

### Task 4: `preview` CLI subcommand

**Files:**
- Modify: `src/mlb_digest/cli.py`
- Modify: `tests/test_cli.py`

- [x] **Step 1: Write the failing test**

Add to `tests/test_cli.py`:

```python
def test_cli_preview_writes_both_html_files(tmp_path):
    runner = CliRunner()

    with patch("mlb_digest.cli.load_config", return_value=_make_mock_config()):
        result = runner.invoke(main, ["preview", "--out", str(tmp_path)])

    assert result.exit_code == 0
    assert (tmp_path / "preview.html").exists()
    assert (tmp_path / "preview-gmail-dark.html").exists()
    assert "preview.html" in result.output
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli.py::test_cli_preview_writes_both_html_files -v`
Expected: FAIL — `Error: No such command 'preview'` (exit_code 2)

- [x] **Step 3: Implement the command**

In `src/mlb_digest/cli.py`: add `from pathlib import Path` to the stdlib imports
and `from mlb_digest.preview import load_sample_digest, write_preview_files` to
the internal imports. Then add after the `test_email` command:

```python
@main.command()
@click.option(
    "--out",
    "out_dir",
    type=click.Path(file_okay=False, path_type=Path),
    default=Path("preview"),
    help="Directory for the preview HTML files.",
)
def preview(out_dir: Path) -> None:
    """Render the email template from sample data into local HTML files."""
    config = load_config()

    written = write_preview_files(config, out_dir)
    for path in written:
        click.echo(str(path))
```

Note: no `validate_secrets()` — preview needs no secrets and must work offline.

- [x] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_cli.py -v`
Expected: PASS (all, including existing tests)

- [x] **Step 5: Commit**

```bash
bash check.sh && git add -A && git commit -m "feat: add preview CLI subcommand"
```

### Task 5: `test-email` sends the real template

**Files:**
- Modify: `src/mlb_digest/cli.py:178-205`
- Modify: `tests/test_cli.py`

- [x] **Step 1: Write the failing test**

Add to `tests/test_cli.py`:

```python
def test_cli_test_email_sends_real_template():
    runner = CliRunner()

    with (
        patch("mlb_digest.cli.send_email") as mock_send,
        patch("mlb_digest.cli.load_config", return_value=_make_mock_config()),
    ):
        result = runner.invoke(main, ["test-email"])

    assert result.exit_code == 0
    html_body = mock_send.call_args[1]["html_body"]
    assert "DUGOUT DIGEST" in html_body
    assert "linear-gradient" in html_body
```

- [x] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_cli.py::test_cli_test_email_sends_real_template -v`
Expected: FAIL — `AssertionError` (current body is `<h1>Hello from MLB Digest!</h1>`)

- [x] **Step 3: Rewrite the command body**

Replace the `test_email` function body in `src/mlb_digest/cli.py` (lines 179-205) with:

```python
@main.command()
def test_email() -> None:
    """Send the sample digest through the real template to verify Gmail setup."""
    config = load_config()
    config.validate_secrets()

    sample_md = load_sample_digest()
    html_body = render_email_html(
        sample_md,
        team_name=config.full_team_name,
        primary_color=config.team_colors.get("primary", "#333333"),
        accent_color=config.team_colors.get("accent", "#cc0000"),
        emoji=config.team_emoji,
    )
    text_body = render_email_text(sample_md, team_name=config.full_team_name)

    try:
        send_email(
            subject="MLB Digest — Test Email (sample data)",
            html_body=html_body,
            text_body=text_body,
            sender=config.gmail_address,
            password=config.gmail_app_password,
            recipients=config.email_recipients,
            transport=config.email_transport,
        )
        click.echo("Test email sent successfully!")
    except Exception as e:
        logger.exception("Test email failed")
        click.echo(f"Test email failed: {e}", err=True)
        raise SystemExit(1) from e
```

- [x] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_cli.py -v`
Expected: PASS (including the pre-existing `test_cli_test_email_subcommand`)

- [x] **Step 5: Commit**

```bash
bash check.sh && git add -A && git commit -m "feat: test-email sends the real template from sample data"
```

### Task 6: gitignore + email-check skill

**Files:**
- Modify: `.gitignore`
- Create: `.claude/skills/email-check/SKILL.md`

- [x] **Step 1: Ignore preview output**

Add to `.gitignore`:

```
preview/
```

- [x] **Step 2: Write the skill**

Create `.claude/skills/email-check/SKILL.md`:

```markdown
---
name: email-check
description: Render the digest email from sample data, screenshot it in Chrome, and share the screenshots back in chat. Use whenever templates.py changes or email rendering/colors need verification.
---

# Email Check Loop

Verify the digest email renders correctly (including the Gmail dark-mode
defenses from ADR 0002) without sending real emails until the final check.

## Fast iteration (no email sent)

1. Run: `uv run mlb-digest preview`
   - Writes `preview/preview.html` (the email as built) and
     `preview/preview-gmail-dark.html` (same HTML inside a Gmail-like DOM:
     `<u></u>` + `.body` wrapper on a dark background, which activates the
     blend-mode CSS).
2. Open both files in Chrome via claude-in-chrome (`file://` URLs) and
   screenshot each.
3. Share the screenshots in chat. Check: white text legible, backgrounds not
   inverted, accent colors correct, table rows readable, badge letter visible.
4. Iterate until correct.

## Final check (sends one real email)

5. Run: `uv run mlb-digest test-email` — sends the sample digest through the
   real template.
6. Open Gmail web in Chrome, find the "MLB Digest — Test Email" message,
   screenshot it, share in chat.
7. Ask the user to glance at Gmail iOS dark mode when convenient.

## Caveat

The gmail-dark harness verifies the blend-mode defenses activate and text
stays legible. It does not replicate Gmail iOS's exact color transformation —
the final check plus the iOS glance covers that gap.
```

- [x] **Step 3: Commit**

```bash
bash check.sh && git add -A && git commit -m "chore: add email-check skill and ignore preview output"
```

### Task 7: Visual verification of the new loop

Run the loop end-to-end on the unchanged template — proves the tooling and re-baselines.

- [x] **Step 1:** Run `uv run mlb-digest preview`. Expected output: two file paths.
- [x] **Step 2:** Open `file:///Users/cooperreal/mlb-digest-cli/preview/preview.html` and `file:///Users/cooperreal/mlb-digest-cli/preview/preview-gmail-dark.html` in Chrome, screenshot both, share in chat.
- [x] **Step 3:** Confirm: dark navy page, white legible text, red accent stripe/labels, readable standings table in both variants. If the harness itself is buggy (not the template), fix it here with a test before proceeding.

### Task 8: PR 1

- [ ] **Step 1:** Run `bash check.sh` — must pass.
- [ ] **Step 2:** Push and open the PR:

```bash
git push -u origin email-verify-loop
gh pr create --title "feat: email preview loop + real-template test-email" --body "$(cat <<'EOF'
Adds the render → screenshot → share verification loop from the approved spec:

- `preview` subcommand renders the real template from canned sample data into
  `preview/preview.html` and `preview/preview-gmail-dark.html` (Gmail-like DOM
  harness that activates the ADR-0002 blend-mode defenses)
- `test-email` now sends the real template instead of throwaway HTML
- `.claude/skills/email-check/` documents the loop
- Spec: docs/superpowers/specs/2026-07-15-email-verify-loop-and-code-review-design.md

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 3:** Wait for `check` and `smoke-test` CI jobs to go green.
- [ ] **Step 4:** Ask the user to approve squash-merge (or merge if pre-authorized): `gh pr merge --squash`. Branch auto-deletes.

---

## Part B — PR 2: code review fixes + style cleanup

Prerequisite: PR 1 merged.

### Task 9: Branch

- [ ] **Step 1:**

```bash
git checkout master && git pull && git checkout -b code-review-fixes
```

### Task 10: Permanent style rules in CLAUDE.md

**Files:**
- Modify: `CLAUDE.md` (section "6. Python & Code Style")

- [ ] **Step 1:** In CLAUDE.md section 6, replace the line:

```markdown
- **Flat is better than nested.** Early returns over nested conditionals. Simple loops over clever comprehensions.
```

with:

```markdown
- **Flat is better than nested.** Early returns over nested conditionals.
- **No/minimal list comprehensions.** Prefer explicit `for` loops. A comprehension is acceptable only as a single trivial transform on one line — no conditionals, no nesting.
- **Comments only when needed.** Code should explain itself; delete comments that restate the code.
```

- [ ] **Step 2: Commit**

```bash
bash check.sh && git add -A && git commit -m "docs: make explicit-loop and minimal-comment style rules permanent"
```

### Task 11: Remove dead `_gfix()`

**Files:**
- Modify: `src/mlb_digest/templates.py:50-52`

- [ ] **Step 1:** Delete the function (never called anywhere):

```python
def _gfix(text: str) -> str:
    """Wrap text in Gmail blend mode fix divs."""
    return f"{GFIX_OPEN}{text}{GFIX_CLOSE}"
```

- [ ] **Step 2:** Run: `uv run pytest tests/ -v` — Expected: all PASS (it was dead code).
- [ ] **Step 3: Commit**

```bash
bash check.sh && git add -A && git commit -m "refactor: remove dead _gfix helper"
```

### Task 12: Remove unused `secondary_color` parameter

**Files:**
- Modify: `src/mlb_digest/templates.py:152-159`
- Modify: `src/mlb_digest/cli.py` (the `render_email_html(...)` call in the main flow)

- [ ] **Step 1:** In `render_email_html`, delete the line `secondary_color: str = "#666666",` from the signature. The parameter is never used in the function body.
- [ ] **Step 2:** In `cli.py`, delete the line `secondary_color=config.team_colors.get("secondary", "#666666"),` from the `render_email_html(...)` call.
- [ ] **Step 3:** Run: `uv run mypy src/ && uv run pytest tests/ -v` — Expected: clean + all PASS.
- [ ] **Step 4: Commit**

```bash
bash check.sh && git add -A && git commit -m "refactor: remove unused secondary_color template parameter"
```

### Task 13: SMTP timeout (TDD)

**Files:**
- Modify: `tests/test_emailer.py`
- Modify: `src/mlb_digest/emailer.py` (the `smtplib.SMTP_SSL(...)` call in `_send_gmail_smtp`)

- [ ] **Step 1: Write the failing test** — add to `tests/test_emailer.py` (match its existing patch style; it already patches `smtplib.SMTP_SSL` — check the exact patch target used by `test_send_email_calls_smtp` and reuse it):

```python
def test_send_email_sets_smtp_timeout():
    with patch("mlb_digest.emailer.smtplib.SMTP_SSL") as mock_smtp:
        send_email(
            subject="s",
            html_body="<p>h</p>",
            text_body="t",
            sender="a@b.c",
            password="pw",  # pragma: allowlist secret
            recipients=["r@x.y"],
        )

    assert mock_smtp.call_args[1]["timeout"] == 30
```

- [ ] **Step 2:** Run: `uv run pytest tests/test_emailer.py::test_send_email_sets_smtp_timeout -v`
Expected: FAIL — `KeyError: 'timeout'`
- [ ] **Step 3: Implement** — in `emailer.py` line 31:

```python
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
```

- [ ] **Step 4:** Run: `uv run pytest tests/test_emailer.py -v` — Expected: PASS.
- [ ] **Step 5: Commit**

```bash
bash check.sh && git add -A && git commit -m "fix: add 30s timeout to SMTP connection"
```

### Task 14: Parallel review sweep

Dispatch three review subagents concurrently (one Agent message, three tool
uses). Each must return findings as a list of `file:line — summary — concrete
failure scenario or rule violated — suggested fix`.

- [ ] **Step 1:** Dispatch subagent A (correctness):

> Review every module in /Users/cooperreal/mlb-digest-cli/src/mlb_digest/ for correctness bugs only: logic errors, unhandled edge cases (empty lists, None, missing dict keys, malformed feed/API data), regex pitfalls in templates.py (greedy matches, nested-tag corruption, unescaped user content flowing into HTML), error-handling gaps, and resource leaks. For each finding give file:line, a one-sentence defect statement, and a concrete input/state → wrong output scenario. Report only defects you can demonstrate with a scenario — no style opinions.

- [ ] **Step 2:** Dispatch subagent B (style rules):

> Review every module in /Users/cooperreal/mlb-digest-cli/src/mlb_digest/ against these rules: explicit `for` loops preferred — a list comprehension is acceptable only as a single trivial one-line transform with no conditionals and no nesting; comments only when needed (flag comments restating the code); no unnecessary indirection; functions do one thing; clear names; flat over nested. For each violation give file:line, the rule broken, and the rewritten code.

- [ ] **Step 3:** Dispatch subagent C (dead code / debt):

> Review /Users/cooperreal/mlb-digest-cli/src/mlb_digest/ and tests/ for: dead or unreachable code, unused parameters/imports/constants, config values loaded but never used, test gaps (public functions with no test exercising them), and inconsistencies between CLAUDE.md/README and actual behavior. file:line + one sentence each.

- [ ] **Step 4:** Adversarially verify each finding by reading the cited code yourself. Discard anything that doesn't hold up. List confirmed findings in chat, ranked by severity.

### Task 15: Fix confirmed findings

For each confirmed finding from Task 14, apply this loop (one commit per finding or per tight group of related findings):

- [ ] **Step 1:** Bug findings: write a failing test that reproduces the defect → run it, confirm FAIL → minimal fix → run full suite, confirm PASS → `bash check.sh` → commit `fix: <finding>`.
- [ ] **Step 2:** Style findings: apply the rewrite → full suite stays green → `bash check.sh` → commit `refactor: <finding>`.
- [ ] **Step 3:** If any finding touches `templates.py` or `preview.py`, run the email-check skill loop (preview → screenshots → share in chat) before committing.

### Task 16: Known comprehension conversions

These two are pre-confirmed violations of the new rule; convert regardless of Task 14 output. Trivial one-line transforms elsewhere (e.g. `[asdict(p) for p in roster]`, `[a.title for a in team_articles]`) stay — they satisfy the rule.

**Files:**
- Modify: `src/mlb_digest/cli.py` (the `--json-output` branch of `list_teams_cmd` — nested, multi-line)
- Modify: `src/mlb_digest/config.py:91-94` (`_parse_recipients` — has a conditional)

- [ ] **Step 1:** Rewrite the `list-teams` JSON branch:

```python
    if as_json:
        output = {}
        for division, teams in grouped.items():
            division_teams = []
            for t in teams:
                division_teams.append(
                    {
                        "abbreviation": t.abbreviation,
                        "short_name": t.short_name,
                        "full_name": t.full_name,
                        "team_id": t.team_id,
                        "primary_color": t.primary_color,
                        "accent_color": t.accent_color,
                    }
                )
            output[division] = division_teams
        click.echo(json.dumps(output, indent=2))
        return
```

- [ ] **Step 2:** Rewrite `_parse_recipients`:

```python
def _parse_recipients(env_value: str, toml_fallback: list[str]) -> list[str]:
    if not env_value:
        return toml_fallback

    recipients = []
    for raw_recipient in env_value.split(","):
        cleaned = raw_recipient.strip()
        if cleaned:
            recipients.append(cleaned)
    return recipients
```

- [ ] **Step 3:** Run: `uv run pytest tests/test_cli.py tests/test_config.py -v` — Expected: PASS (behavior identical).
- [ ] **Step 4: Commit**

```bash
bash check.sh && git add -A && git commit -m "refactor: explicit loops for list-teams JSON and recipient parsing"
```

### Task 17: Visual verification

- [ ] **Step 1:** Run the email-check skill fast loop (preview → Chrome screenshots of both files → share in chat). Template changes in this PR are subtractive (dead code, unused param), so rendering must be pixel-identical in intent — confirm nothing regressed.

### Task 18: PR 2 + final real-send check

- [ ] **Step 1:** `bash check.sh` — must pass.
- [ ] **Step 2:** Push and open the PR:

```bash
git push -u origin code-review-fixes
gh pr create --title "fix: code review findings + explicit-style cleanup" --body "$(cat <<'EOF'
Extensive review sweep (correctness / style / debt) with every finding
adversarially verified before fixing. Includes:

- remove dead `_gfix()` and unused `secondary_color` param
- 30s SMTP timeout
- explicit loops per the new CLAUDE.md style rules
- <verified findings from the sweep — fill in actual list at PR time>

Verified with the email-check preview loop (screenshots in PR thread).

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

(Replace the placeholder line with the real list of landed fixes before submitting.)

- [ ] **Step 3:** CI green → user approves → squash-merge.
- [ ] **Step 4:** Final check from the skill: `uv run mlb-digest test-email`, open Gmail web in Chrome, screenshot the delivered "MLB Digest — Test Email (sample data)" message, share in chat.
- [ ] **Step 5:** Ask the user to glance at the same email in Gmail iOS dark mode when convenient. Their thumbs-up closes the spec's success criteria.
