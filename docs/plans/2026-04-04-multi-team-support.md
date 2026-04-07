# Multi-Team Support Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform MLB Digest from a hardcoded Braves tool into a configurable newsletter for any of the 30 MLB teams, with team-specific email theming, feeds, and narrator personality.

**Architecture:** A new `teams_registry.py` module (layer 0) becomes the single source of truth for all 30 teams. `config.py` looks up the team by name/abbreviation/ID and merges registry defaults with user overrides. The narrator gets a team-specific personality hint, and the email template gets team-branded colors, name, and emoji. The user only needs `name = "Yankees"` in `config.toml`.

**Tech Stack:** Python dataclasses, tomllib, Click subcommands. No new dependencies.

---

## Task 1: Add `teams_registry.py`

**Files:**
- Create: `src/mlb_digest/teams_registry.py`

The registry is the foundation — every other task depends on it. This is a data-heavy module (~780 lines, mostly team definitions). Copy the complete registry from the spec file at `docs/plans/multi-team-files/teams_registry.py`.

**Step 1: Create the registry module**

Copy `docs/plans/multi-team-files/teams_registry.py` to `src/mlb_digest/teams_registry.py`. The file contains:
- `TeamInfo` frozen dataclass with all team metadata
- 30 team constants (ORIOLES, RED_SOX, ... GIANTS)
- `ALL_TEAMS` tuple and lookup indexes
- `get_team()`, `list_teams()`, `get_team_or_raise()` functions

```bash
cp docs/plans/multi-team-files/teams_registry.py src/mlb_digest/teams_registry.py
```

**Step 2: Verify it imports cleanly**

```bash
uv run python -c "from mlb_digest.teams_registry import get_team, list_teams, ALL_TEAMS; print(f'{len(ALL_TEAMS)} teams loaded')"
```

Expected: `30 teams loaded`

**Step 3: Commit**

```bash
git add src/mlb_digest/teams_registry.py
git commit -m "feat: add teams registry with all 30 MLB teams"
```

---

## Task 2: Update architecture tests for new module

**Files:**
- Modify: `tests/test_architecture.py:29-37` (LAYER dict)
- Modify: `tests/test_architecture.py:85` (MAX_MODULE_LINES)

The registry is ~780 lines — almost all data. The 300-line architecture limit is meant to keep *logic* modules focused. Add `teams_registry` to layer 0 and exempt data-heavy modules from the size check.

**Step 1: Add `teams_registry` to the LAYER dict**

In `tests/test_architecture.py`, update the LAYER dict (line 29-37):

```python
LAYER: dict[str, int] = {
    "teams_registry": 0,
    "config": 0,
    "mlb_api": 1,
    "feeds": 1,
    "narrator": 2,
    "templates": 3,
    "emailer": 4,
    "cli": 5,
}
```

**Step 2: Add size exemption for data-heavy modules**

After `MAX_MODULE_LINES = 300` (line 85), add:

```python
# Data-heavy modules (mostly constants, not logic) are exempt from the size limit
SIZE_EXEMPT: set[str] = {"teams_registry"}
```

Then update `test_module_size_limit` to skip exempt modules:

```python
@pytest.mark.parametrize("module", MODULES)
def test_module_size_limit(module: str) -> None:
    """No single module may exceed 300 lines (data-heavy modules exempt)."""
    if module in SIZE_EXEMPT:
        return
    filepath = SRC_DIR / f"{module}.py"
    line_count = len(filepath.read_text().splitlines())

    assert line_count <= MAX_MODULE_LINES, (
        f"TASTE VIOLATION: '{module}.py' is {line_count} lines "
        f"(max {MAX_MODULE_LINES}).\n"
        f"FIX: Split into focused modules. Each module should do one thing. "
        f"For example, extract roster functions from mlb_api.py into mlb_roster.py."
    )
```

**Step 3: Run architecture tests**

```bash
uv run pytest tests/test_architecture.py -v
```

Expected: ALL PASS (including new `teams_registry` in layer and size checks)

**Step 4: Commit**

```bash
git add tests/test_architecture.py
git commit -m "feat: add teams_registry to architecture layer map and size exemptions"
```

---

## Task 3: Add `test_teams_registry.py`

**Files:**
- Create: `tests/test_teams_registry.py`

Copy from `docs/plans/multi-team-files/test_teams_registry.py` — it already tests registry completeness, all lookup methods, error handling, and spot-checks.

**Step 1: Copy the test file**

```bash
cp docs/plans/multi-team-files/test_teams_registry.py tests/test_teams_registry.py
```

**Step 2: Run the tests**

```bash
uv run pytest tests/test_teams_registry.py -v
```

Expected: ALL PASS (30 teams, unique IDs, unique abbreviations, all lookups work)

**Step 3: Commit**

```bash
git add tests/test_teams_registry.py
git commit -m "test: add teams registry tests for lookup, completeness, and data integrity"
```

---

## Task 4: Rewrite `config.py` to use registry lookup

**Files:**
- Modify: `src/mlb_digest/config.py` (full rewrite)
- Modify: `config.toml` (simplify)

The Config dataclass gains new fields: `full_team_name`, `division`, `team_emoji`, `narrator_hint`. The `load_config()` function looks up the team in the registry and merges defaults with overrides. `format_subject` gains `emoji` and `full_team_name` template variables.

**Step 1: Write failing tests for new config behavior**

Create or update `tests/test_config.py` with these new tests (keep existing tests, update them to match the new minimal toml format):

All existing tests need their toml fixtures updated. The minimal valid config is now:

```toml
[team]
name = "Braves"

[email]
recipients = ["test@example.com"]

[narrator]
model = "claude-sonnet-4-6"
temperature = 0.7
```

Add these new tests:

```python
def test_load_config_resolves_team_from_registry(tmp_path: Path):
    """Just `name = "Yankees"` should resolve all team metadata."""
    toml_content = """
[team]
name = "Yankees"

[email]
recipients = ["test@example.com"]

[narrator]
model = "claude-sonnet-4-6"
temperature = 0.7
"""
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)

    config = load_config(config_path=config_file)

    assert config.team_id == 147
    assert config.team_name == "Yankees"
    assert config.full_team_name == "New York Yankees"
    assert config.league_id == 103
    assert config.division == "AL East"
    assert config.team_colors["primary"] == "#003087"
    assert config.team_emoji == "⚾"
    assert "Bronx" in config.narrator_hint


def test_load_config_resolves_by_abbreviation(tmp_path: Path):
    toml_content = """
[team]
name = "LAD"

[email]
recipients = ["test@example.com"]

[narrator]
model = "claude-sonnet-4-6"
temperature = 0.7
"""
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)

    config = load_config(config_path=config_file)

    assert config.team_id == 119
    assert config.full_team_name == "Los Angeles Dodgers"


def test_load_config_allows_color_override(tmp_path: Path):
    toml_content = """
[team]
name = "Braves"
colors = { accent = "#FFD700" }

[email]
recipients = ["test@example.com"]

[narrator]
model = "claude-sonnet-4-6"
temperature = 0.7
"""
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)

    config = load_config(config_path=config_file)

    assert config.team_colors["accent"] == "#FFD700"
    assert config.team_colors["primary"] == "#13274F"  # registry default kept


def test_load_config_allows_display_name_override(tmp_path: Path):
    toml_content = """
[team]
name = "Cubs"
display_name = "Cubbies"

[email]
recipients = ["test@example.com"]

[narrator]
model = "claude-sonnet-4-6"
temperature = 0.7
"""
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)

    config = load_config(config_path=config_file)

    assert config.team_name == "Cubbies"
    assert config.full_team_name == "Chicago Cubs"


def test_load_config_uses_registry_feeds_when_none_in_toml(tmp_path: Path):
    toml_content = """
[team]
name = "Braves"

[email]
recipients = ["test@example.com"]

[narrator]
model = "claude-sonnet-4-6"
temperature = 0.7
"""
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)

    config = load_config(config_path=config_file)

    assert len(config.team_feed_urls) >= 1
    assert any("mlbtraderumors" in url for url in config.team_feed_urls)


def test_load_config_raises_on_unknown_team(tmp_path: Path):
    toml_content = """
[team]
name = "Unicorns"

[email]
recipients = ["test@example.com"]

[narrator]
model = "claude-sonnet-4-6"
temperature = 0.7
"""
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)

    with pytest.raises(ValueError, match="Unknown team"):
        load_config(config_path=config_file)


def test_format_subject_includes_emoji(tmp_path: Path):
    toml_content = """
[team]
name = "Braves"

[email]
recipients = ["test@example.com"]

[narrator]
model = "claude-sonnet-4-6"
temperature = 0.7
"""
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)

    config = load_config(config_path=config_file)
    subject = config.format_subject(catchup=False)

    assert config.team_emoji in subject
    assert "Braves" in subject
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_config.py -v
```

Expected: New tests FAIL (Config doesn't have `full_team_name`, `division`, etc. yet)

**Step 3: Rewrite `config.py`**

Replace `src/mlb_digest/config.py` with the new version adapted from `docs/plans/multi-team-files/config.py`. Key adaptations from spec to current codebase:

- Keep the same import style
- Use `get_team_or_raise` from the new registry
- Add new Config fields: `full_team_name`, `division`, `team_emoji`, `narrator_hint`
- `format_subject` template gains `{emoji}` and `{full_team_name}` variables
- Default subject templates include emoji: `"{emoji} {team_name} Daily — {date}"`
- Registry feeds as fallback when toml doesn't specify them
- Default MLB feed URLs as fallback

**Step 4: Simplify `config.toml`**

Replace `config.toml` with the minimal version:

```toml
# MLB Digest — Configuration
# Just set your team name below. Everything else has smart defaults.
# Run `mlb-digest list-teams` to see all available teams.

[team]
name = "Braves"

[email]
recipients = ["you@gmail.com"]

[narrator]
model = "claude-sonnet-4-6"
temperature = 0.7
```

**Step 5: Update existing tests in `test_config.py`**

The existing tests (`test_load_config_reads_toml_values`, etc.) use the old verbose toml format with explicit `id`, `league_id`. Update them to use the new minimal format. The test for `test_load_config_raises_on_missing_toml_section` should now expect a `ValueError` (from `get_team_or_raise`) when `[team]` section is missing or has no `name`.

**Step 6: Run all tests**

```bash
uv run pytest tests/test_config.py -v
```

Expected: ALL PASS

**Step 7: Run full test suite to check nothing else broke**

```bash
uv run pytest tests/ -v
```

Expected: ALL PASS. The `test_cli.py` mock config may need `full_team_name`, `division`, `team_emoji`, `narrator_hint` fields added to `_make_mock_config` — if so, fix those too.

**Step 8: Commit**

```bash
git add src/mlb_digest/config.py config.toml tests/test_config.py
git commit -m "feat: config looks up team from registry, simplified config.toml"
```

---

## Task 5: Enhance `narrator.py` with team personality

**Files:**
- Modify: `src/mlb_digest/narrator.py:13-35` (SYSTEM_PROMPT_TEMPLATE)
- Modify: `src/mlb_digest/narrator.py:42-43` (build_system_prompt signature)
- Modify: `tests/test_narrator.py`

**Step 1: Write failing tests**

Add to `tests/test_narrator.py`:

```python
def test_build_system_prompt_includes_personality_and_division():
    prompt = build_system_prompt(
        team_name="Yankees",
        full_team_name="New York Yankees",
        division="AL East",
        narrator_hint="Write like a proud Bronx fan who expects championships.",
    )

    assert "Yankees" in prompt
    assert "AL East" in prompt
    assert "Bronx" in prompt
    assert "PERSONALITY" in prompt
    assert "CRITICAL RULES" in prompt


def test_build_system_prompt_falls_back_without_optional_args():
    prompt = build_system_prompt("Braves")

    assert "Braves" in prompt
    assert "CRITICAL RULES" in prompt
```

**Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_narrator.py::test_build_system_prompt_includes_personality_and_division -v
```

Expected: FAIL (build_system_prompt only takes `team_name`)

**Step 3: Update `narrator.py`**

Update `SYSTEM_PROMPT_TEMPLATE` to include `PERSONALITY` and `TEAM CONTEXT` sections (from `docs/plans/multi-team-files/narrator.py`).

Update `build_system_prompt` signature:

```python
def build_system_prompt(
    team_name: str,
    full_team_name: str = "",
    division: str = "",
    narrator_hint: str = "",
) -> str:
```

With fallback defaults for backward compatibility (empty strings get generic defaults).

**Step 4: Run all narrator tests**

```bash
uv run pytest tests/test_narrator.py -v
```

Expected: ALL PASS

**Step 5: Commit**

```bash
git add src/mlb_digest/narrator.py tests/test_narrator.py
git commit -m "feat: narrator system prompt includes team personality and division"
```

---

## Task 6: Enhance `templates.py` with team branding

**Files:**
- Modify: `src/mlb_digest/templates.py` (both render functions)
- Modify: `tests/test_templates.py`

The email gets a team-branded header (team name + emoji), richer inline styles (paragraphs, lists), secondary color support, and a team-branded footer.

**Step 1: Write failing tests**

Add to `tests/test_templates.py`:

```python
def test_render_email_html_includes_team_name_in_header():
    md = "## Test\n\nContent."

    html = render_email_html(
        md,
        team_name="Atlanta Braves",
        primary_color="#13274F",
        accent_color="#CE1141",
        secondary_color="#CE1141",
        emoji="🪓",
    )

    assert "Atlanta Braves" in html
    assert "🪓" in html


def test_render_email_html_uses_secondary_color():
    md = "## Test\n\nContent."

    html = render_email_html(
        md,
        team_name="Atlanta Braves",
        primary_color="#13274F",
        accent_color="#CE1141",
        secondary_color="#666666",
        emoji="🪓",
    )

    assert "#666666" in html


def test_render_email_text_includes_team_name():
    md = "## Hello\n\nSome content."

    text = render_email_text(md, team_name="Atlanta Braves")

    assert "Atlanta Braves" in text
```

**Step 2: Run to verify they fail**

```bash
uv run pytest tests/test_templates.py -v
```

Expected: FAIL (render_email_html doesn't accept `team_name`, `secondary_color`, `emoji`)

**Step 3: Update `templates.py`**

Update `render_email_html` signature to match the spec:

```python
def render_email_html(
    md_content: str,
    team_name: str = "MLB Digest",
    primary_color: str = "#333333",
    accent_color: str = "#cc0000",
    secondary_color: str = "#666666",
    emoji: str = "⚾",
) -> str:
```

Update the HTML template to include:
- Team-branded header banner with `{emoji} {team_name}` and "Your Morning Digest" subtitle
- Viewport meta tag for mobile
- Paragraph and list inline styles
- Team-branded footer with accent border

Update `render_email_text` signature:

```python
def render_email_text(md_content: str, team_name: str = "MLB Digest") -> str:
```

Update the footer text to include the team name.

**Step 4: Update existing tests**

Existing tests call `render_email_html(md, primary_color=..., accent_color=...)` — these still work because `team_name`, `secondary_color`, and `emoji` have defaults. No changes needed to existing tests.

Existing `test_render_email_text_strips_markdown` calls `render_email_text(md)` — still works with default `team_name`. No changes needed.

**Step 5: Run all template tests**

```bash
uv run pytest tests/test_templates.py -v
```

Expected: ALL PASS

**Step 6: Commit**

```bash
git add src/mlb_digest/templates.py tests/test_templates.py
git commit -m "feat: team-branded email template with name, emoji, and richer styling"
```

---

## Task 7: Update `cli.py` — wire everything together + `list-teams`

**Files:**
- Modify: `src/mlb_digest/cli.py`
- Modify: `tests/test_cli.py`

The CLI needs to:
1. Pass the new config fields through to `build_system_prompt`, `render_email_html`, and `render_email_text`
2. Add a `list-teams` subcommand
3. Include `team` and `division` in `--dry-run` output

**Step 1: Write failing test for list-teams**

Add to `tests/test_cli.py`:

```python
def test_cli_list_teams_shows_all_divisions():
    runner = CliRunner()

    result = runner.invoke(main, ["list-teams"])

    assert result.exit_code == 0
    assert "AL East" in result.output
    assert "NL West" in result.output
    assert "Yankees" in result.output
    assert "Braves" in result.output


def test_cli_list_teams_json_output():
    runner = CliRunner()

    result = runner.invoke(main, ["list-teams", "--json-output"])

    assert result.exit_code == 0
    import json
    data = json.loads(result.output)
    assert "AL East" in data
    assert len(data) == 6
```

**Step 2: Run to verify they fail**

```bash
uv run pytest tests/test_cli.py::test_cli_list_teams_shows_all_divisions -v
```

Expected: FAIL (no `list-teams` subcommand)

**Step 3: Update `cli.py`**

Wire the new config fields into existing calls:

```python
# In main(), update build_system_prompt call:
system_prompt = build_system_prompt(
    team_name=config.team_name,
    full_team_name=config.full_team_name,
    division=config.division,
    narrator_hint=config.narrator_hint,
)

# Update render_email_html call:
html_body = render_email_html(
    narrative,
    team_name=config.full_team_name,
    primary_color=config.team_colors.get("primary", "#333333"),
    accent_color=config.team_colors.get("accent", "#cc0000"),
    secondary_color=config.team_colors.get("secondary", "#666666"),
    emoji=config.team_emoji,
)
text_body = render_email_text(narrative, team_name=config.full_team_name)

# Update dry-run data dict to include team and division:
data = {
    "team": config.full_team_name,
    "division": config.division,
    ...  # rest stays the same
}

# Update test_email to show team name:
html_body=(
    "<html><body>"
    "<h1>Hello from MLB Digest!</h1>"
    f"<p>Your email setup works. Configured for: {config.full_team_name}</p>"
    "</body></html>"
),
text_body=f"Hello from MLB Digest! Your email setup works. Team: {config.full_team_name}",
```

Add the `list-teams` subcommand:

```python
@main.command("list-teams")
@click.option("--json-output", "as_json", is_flag=True, help="Output as JSON.")
def list_teams_cmd(as_json: bool) -> None:
    """Show all 30 available MLB teams."""
    from mlb_digest.teams_registry import list_teams

    grouped = list_teams()

    if as_json:
        output = {}
        for division, teams in grouped.items():
            output[division] = [
                {
                    "abbreviation": t.abbreviation,
                    "short_name": t.short_name,
                    "full_name": t.full_name,
                    "team_id": t.team_id,
                    "primary_color": t.primary_color,
                    "accent_color": t.accent_color,
                }
                for t in teams
            ]
        click.echo(json.dumps(output, indent=2))
        return

    for division, teams in grouped.items():
        click.echo(f"\n  {division}")
        click.echo(f"  {'─' * 50}")
        for t in teams:
            click.echo(f"    {t.abbreviation:<5} {t.full_name:<28} (ID: {t.team_id})")
    click.echo()
```

**Step 4: Update `_make_mock_config` in `test_cli.py`**

Add the new fields:

```python
defaults = {
    "team_id": 144,
    "team_name": "Braves",
    "full_team_name": "Atlanta Braves",
    "league_id": 104,
    "division": "NL East",
    "team_feed_urls": [],
    "mlb_feed_urls": [],
    "anthropic_api_key": "sk-test",  # pragma: allowlist secret
    "narrator_model": "claude-sonnet-4-6",
    "narrator_temperature": 0.7,
    "team_colors": {"primary": "#13274F", "accent": "#CE1141", "secondary": "#CE1141"},
    "team_emoji": "🪓",
    "narrator_hint": "Write like a Braves fan.",
    "email_recipients": ["test@example.com"],
    "email_transport": "gmail_smtp",
    "gmail_address": "test@gmail.com",
    "gmail_app_password": "pw",  # pragma: allowlist secret
}
```

**Step 5: Run all CLI tests**

```bash
uv run pytest tests/test_cli.py -v
```

Expected: ALL PASS

**Step 6: Commit**

```bash
git add src/mlb_digest/cli.py tests/test_cli.py
git commit -m "feat: wire team branding through CLI, add list-teams subcommand"
```

---

## Task 8: Full validation

**Step 1: Run the full test suite**

```bash
uv run pytest tests/ -v
```

Expected: ALL PASS

**Step 2: Run lint and type checks**

```bash
bash check.sh
```

Expected: ALL PASS (ruff, mypy, pytest)

**Step 3: Verify the list-teams command works end-to-end**

```bash
uv run mlb-digest list-teams
```

Expected: Prints all 30 teams grouped by division

**Step 4: Verify dry-run still works**

```bash
uv run mlb-digest --dry-run
```

Expected: JSON output with `team` and `division` fields

**Step 5: Final commit if any fixups needed**

```bash
git add -A
git commit -m "fix: address lint/type issues from multi-team integration"
```

---

## Architecture Notes

### Dependency layers (updated)

```
teams_registry  (layer 0 — pure data, no internal imports)
config          (layer 0 — imports teams_registry)
mlb_api, feeds  (layer 1 — data fetching)
narrator        (layer 2 — transforms data)
templates       (layer 3 — rendering)
emailer         (layer 4 — delivery)
cli             (layer 5 — orchestrator)
```

### Module size

`teams_registry.py` is ~785 lines (almost all data constants). It is exempt from the 300-line limit in the architecture tests. All other modules remain under 300 lines.

### Backward compatibility

The old verbose `config.toml` format (with explicit `id`, `league_id`, `colors`) no longer works — `config.py` now requires the team to exist in the registry. This is intentional: the registry is the single source of truth. Users only need `name = "Braves"`.

### What's NOT in scope

- Multi-team digest (one email covering multiple teams) — future feature
- Custom narrator hints in config.toml — could add later but YAGNI
- Per-team email recipient lists — future feature
