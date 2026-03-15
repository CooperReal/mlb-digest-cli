# MLB Digest CLI

Daily email digest for Atlanta Braves fans. Fetches game results, standings, news, and roster data from MLB APIs and RSS feeds, generates a narrative via Claude, and emails it.

## Tech Stack

Python 3.11+, Click CLI, Anthropic SDK, MLB-StatsAPI, feedparser, httpx, Markdown, tenacity, python-dotenv. Linting via Ruff, type checking via mypy, tests via pytest.

## Project Structure

```
src/mlb_digest/
  cli.py          — Click CLI entry point (main command + test-email subcommand)
  config.py       — Loads config.toml + env vars into Config dataclass
  mlb_api.py      — MLB Stats API calls (games, standings, roster, player stats)
  feeds.py        — RSS feed fetching, parsing, deduplication
  narrator.py     — Claude API prompt building + narrative generation
  emailer.py      — Gmail SMTP email sending
  templates.py    — HTML/text email rendering from markdown
```

## Commands

```bash
uv run mlb-digest                # Full digest, sent via email
uv run mlb-digest --catchup      # Includes roster, season overview, playoff picture
uv run mlb-digest --no-email     # Print digest to stdout
uv run mlb-digest --dry-run      # Dump raw data, no Claude call
uv run mlb-digest test-email     # Send test email to verify Gmail setup
uv run ruff check .              # Lint
uv run mypy src/                 # Type check
uv run pytest tests/ -v          # Tests
```

## Configuration

- `config.toml` — Team settings, feed URLs, narrator model, email subject templates
- `.env` — Secrets: `ANTHROPIC_API_KEY`, `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `EMAIL_RECIPIENTS`
- `EMAIL_RECIPIENTS` env var overrides `config.toml` recipients (comma-separated)

## Secret Protection

- `.env` is gitignored
- Pre-commit hook via `detect-secrets` scans for leaked secrets before every commit
- `.secrets.baseline` tracks known false positives (fake test passwords) — commit this file

## Pre-Push Checklist (MANDATORY)

Before every commit/push, you MUST run all three and they MUST pass:

```bash
uv run pytest tests/ -v          # All tests pass
uv run ruff check .              # No lint errors
uv run mypy src/                 # No type errors
```

Never bypass pre-commit hooks (`--no-verify` is forbidden). If a hook fails, fix the issue.

## Operating Principles

### 1. Plan First, Code Second
- Always enter Plan Mode before writing code. Outline what changes, why, and what tests are needed.
- No plan is approved without a test strategy.

### 2. Maximize Subagent Usage
- Delegate aggressively. Parallel subagents for exploration, testing, review.
- `subagent_type=Explore` for codebase investigation, `subagent_type=Plan` for architecture.
- Run build/test agents in background when possible.
- Keep main conversation context lean.

### 3. Output Discipline
- Be terse. Lead with answer or action.
- No summaries of what was just done.
- Status updates only at milestones or blockers.
- Subagent results compressed to 1-2 sentences.

### 4. Zero Tech Debt
- No shortcuts. No "fix later." No TODO-as-IOU.
- Every function: clear, tested, typed.
- Flag existing debt — don't propagate it.

### 5. Tests Are Mandatory
- Every code change ships with tests. No exceptions.
- TDD when feasible — tests before implementation.
- Never skip running tests. Always run the full relevant suite.
- Failing tests block all forward progress.
- Hard-to-test code = bad design. Fix the design.

### 6. Python & Code Style
- **Readability is the priority.** If a stranger can't understand the code in 10 seconds, rewrite it.
- **No indirection.** No unnecessary abstractions, wrapper functions, base classes, or design patterns for their own sake.
- **Flat is better than nested.** Early returns over nested conditionals. Simple loops over clever comprehensions.
- **Explicit is better than implicit.** Name things clearly. No single-letter variables outside tight loops. No magic values.
- **Functions do one thing and are short.** If it needs a comment explaining what a block does, that block should be its own function with a clear name instead.
- **Type hints on all function signatures.** No `Any` unless truly unavoidable.
- **No premature abstraction.** Three copies of similar code is fine. Don't DRY it up until you actually have a fourth.
- **Ruff line-length is 100.** Check before committing.

### 7. Test Readability
- Tests are documentation. A test should read like a spec.
- **Arrange / Act / Assert** — always structured this way, with blank lines separating each phase.
- Test names describe behavior: `test_empty_roster_returns_no_starters`, not `test_roster_1`.
- No test helpers that hide what's being tested.
- One assertion per concept. Multiple `assert` calls are fine if they verify the same logical thing.
