# AGENTS.md — How this repo is wired

For agents working in `mlb-digest-cli`. Project rules (style, commit policy, secrets, pre-push checklist) live in `CLAUDE.md`. This file describes **architecture** — what the code does, how it's connected, and where the load-bearing pieces are.

> Architectural facts here were derived by graphifying the codebase (`graphify-out/GRAPH_REPORT.md`), then verified against source. Known LLM-inferred edge mistakes have been corrected by `graphify-out/postprocess.py` — re-run it after any `/graphify` rebuild.

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

A daily CLI that fetches MLB data + team RSS feeds, asks Claude to narrate it in a team-fan voice, renders the result as a dark-mode HTML email, and sends it via Gmail SMTP. One config file picks the team; everything else is looked up in a 30-team registry.

## The pipeline (single hot path)

```
load_config() ──► Config (team_id, league_id, secrets, narrator settings, colors)
        │
        ▼
get_yesterday_game()        ┐
get_today_game()             ├─► dataclasses (GameResult, UpcomingGame, …)
get_standings()              │
get_active_roster()          │
get_top_players()            ┘
        │
fetch_articles() ─► select_articles() ─► SelectedArticles(team, mlb)
        │
        ▼
build_system_prompt() + build_prompt()  ──►  generate_narrative()  ──►  markdown
        │                                           │
        │                                           └── raises NarratorError on failure
        │                                               (caught only in main(), exits 1
        │                                                with raw-numbers fallback)
        ▼
render_email_html() / render_email_text() / format_subject()
        │
        ▼
send_email()  (Gmail SMTP, retried twice)
```

Every step lives in its own module. `cli.py:main()` is the **only** function that touches the whole pipeline.

## Module layers (enforced by tests)

`tests/test_architecture.py` enforces strict dependency direction. Imports may only flow from a higher layer to a lower one. **Adding a wrong-direction import will fail CI.**

```
layer 0 :  teams_registry, config        (no internal deps)
layer 1 :  mlb_api, feeds                (data fetching, dataclasses only)
layer 2 :  narrator                      (allowed to import feeds + mlb_api types)
layer 3 :  templates                     (pure rendering)
layer 4 :  emailer                       (delivery)
layer 5 :  cli                           (orchestrator — may import anything)
```

Other invariants the architecture tests enforce on `src/mlb_digest/*.py`:

- Every module has a matching `tests/test_<module>.py`
- Public functions in `mlb_api`, `feeds`, `config` must return **dataclasses, not dicts**
- Public function signatures must declare a return type (Click-decorated commands exempt)
- Custom exceptions end in `Error` (e.g. `NarratorError`, never `NarratorException`)
- No wildcard imports
- Logging uses `%`-formatting, not f-strings (lazy + parseable)
- Modules cap at 300 lines (`teams_registry` is exempt — it's data)

If you violate one, the test message tells you exactly how to fix it.

## Bridge nodes — change with care

These are the highest-betweenness nodes. Modifying them affects multiple subsystems:

| Node | File | Why it matters |
|---|---|---|
| `main()` | `cli.py:48` | Wires all six layers together. Order of calls = the user-visible product. |
| `load_config()` | `config.py:117` | Only constructor of `Config`. Resolves team via registry, then layers env > toml > registry defaults. |
| `_resolve_team()` | `config.py:97` | Sole bridge from config → registry. Calls `get_team_or_raise()`. |
| `Config` dataclass | `config.py:39` | Carrier of every downstream input — team identity, colors, feeds, narrator model, secrets. |
| `NarratorError` | `narrator.py:42` | Only raised in `generate_narrative()`. Only caught in `main()` (cli.py:133). Catching it elsewhere is wrong. |

## Where to make common changes

| Want to… | Edit |
|---|---|
| Add a team / change colors / change personality | `src/mlb_digest/teams_registry.py` (single source of truth — 30 teams) |
| Change the email look | `src/mlb_digest/templates.py` (all styles inline; see Gmail-iOS notes below) |
| Change the narrator's voice / prompt | `src/mlb_digest/narrator.py:SYSTEM_PROMPT_TEMPLATE` (line 13) |
| Add a new data fetch | New function in `mlb_api.py` returning a `@dataclass`, then thread through `main()` and `build_prompt()` |
| Add a new RSS source for one team | `team_feed_urls` tuple inside that team's `TeamInfo` |
| Add an MLB-wide feed | `config.toml` `[feeds.mlb]` or `DEFAULT_MLB_FEED_URLS` in `config.py` |
| Add a CLI flag | `@click.option` on `main()` in `cli.py:34`, then thread the flag through `main()` |
| Switch the Claude model | `config.toml` `[narrator] model = "..."` |

## Non-obvious things the graph (and source) reveal

1. **Override priority for config**: env vars > `config.toml` > team registry defaults. The order is documented at `config.py:7` and matters when adding new fields.
2. **Smoke-test mode is a tokens cap, not a code path.** `--smoke-test` swaps to Haiku 4.5 and `max_tokens=50`. The full pipeline still runs (cli.py:120).
3. **Failure modes intentionally degrade rather than crash:**
   - Narrator fails → email sends raw numbers + exit code 1 (cli.py:133)
   - Email send fails → narrative printed to stdout + exit code 2 (cli.py:169)
   - MLB API call fails → that section is silently dropped (`get_*` functions return `None` / `[]`)
4. **Tenacity retries are scoped tight.** `_fetch_schedule`, `_fetch_roster`, `_fetch_feed_content` retry 3× with exponential backoff; `_send_gmail_smtp` retries twice with a fixed 5-second wait. Don't add retries at the outer layer — it'll multiply.
5. **Concurrency lives in two places only:** `get_top_players` (ThreadPoolExecutor over per-player stats) and `_send_gmail_smtp`. Everything else is sync.
6. **Email template Gmail-iOS hack:** `templates.py` uses `linear-gradient` backgrounds and `mix-blend-mode` wrappers (`gfix-screen` / `gfix-diff`) to survive Gmail's dark-mode auto-inversion. The `<style>` block at the top is the only one that survives — Gmail strips others. See module docstring.
7. **CLI subcommands are siblings of `main()`, not children.** `test_email` and `list_teams_cmd` are separate `@main.command()` entries; they don't go through the digest pipeline. They each call `load_config()` independently.
8. **`docs/plans/multi-team-files/` is excluded from ruff** (`pyproject.toml:38`). Old planning artifacts — do not edit, do not propagate patterns from there.

## Trusting the graph

`graphify-out/postprocess.py` corrects the known LLM-inference mistakes after every rebuild. Specifically it:

- Drops the false-positive "every CLI subcommand uses NarratorError" edges — only `main()` actually catches it (cli.py:133)
- Reverses `NarratorError --calls--> generate_narrative` to `generate_narrative --raises--> NarratorError`
- Reverses `_parse_recipients/_resolve_team --calls--> load_config` (load_config calls them, not vice versa)
- Reverses `load_config --calls--> test_*` and relabels as `test_* --tests--> load_config`
- Drops `load_config --calls--> test_format_subject_*` and `test_validate_secrets_*` (those tests target `Config` methods)
- Generally relabels any `test_X --calls--> Y` as `test_X --tests--> Y`

Re-run after `/graphify` or `/graphify --update`:

```bash
py graphify-out/postprocess.py
```

It's idempotent — safe to run repeatedly. AST-extracted edges (`EXTRACTED` confidence) are reliable as-is; only the `INFERRED` ones needed correction.

## Verifying your work

Before declaring done, run from the repo root:

```bash
bash check.sh
```

This runs (in order): detect-secrets baseline scan, ruff, mypy on `src/`, the architecture tests, then the full test suite. **All steps must pass.** No `--no-verify`; if a hook fails, fix the cause. (Full rules: `CLAUDE.md`.)

## Pointers

- **Project rules / commit policy / secret protection / style:** `CLAUDE.md`
- **Daily commands:** `README.md`
- **Knowledge graph (regenerate with `/graphify`):** `graphify-out/GRAPH_REPORT.md`, `graphify-out/graph.html`
- **Architecture tests (the real spec):** `tests/test_architecture.py`
