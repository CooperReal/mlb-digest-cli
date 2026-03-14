# MLB Digest CLI — Design

## Overview

A Python CLI tool that helps a casual fan stay connected to their MLB team. Configured for the Atlanta Braves by default, but team-agnostic by design. Two commands:

- **`mlb-digest`** — generates and emails the daily digest. Add `--catchup` to include roster breakdown, rivals, and season overview on top of the regular content.
- **`mlb-digest test-email`** — sends a test email to verify Gmail setup works.

Requires Python >= 3.12.

## Data Flow

```
MLB Stats API  →  Fetch raw data (scores, rosters, standings, schedule)
RSS Feeds      →  Fetch recent team + MLB articles
                        ↓
               Claude Sonnet  →  Turn raw data into conversational narrative
                  (constrained to only reference provided data)
                        ↓
               HTML template  →  Format narrative into email with inline CSS
                        ↓
               Gmail SMTP  →  Send multipart email (HTML + plain text)
```

## MLB Stats API Endpoints

The MLB Stats API is free, public, and requires no API key. No official docs exist — the community wiki at [toddrob99/MLB-StatsAPI](https://github.com/toddrob99/MLB-StatsAPI/wiki/Endpoints) is the best reference.

Required endpoints (team ID is configurable, 144 = Braves):

| Endpoint | Purpose | Used By |
|----------|---------|---------|
| `/api/v1/schedule?teamId={id}&startDate=...&endDate=...&hydrate=probablePitcher,linescore,decisions` | Yesterday's game results, today's schedule | always |
| `/api/v1/standings?leagueId=104` | NL standings (W-L, GB) | always |
| `/api/v1/teams/{id}/roster?rosterType=active` | Active roster | `--catchup` |
| `/api/v1/people/{id}/stats?stats=season&group=hitting` | Season batting stats | always (top players), `--catchup` (full roster) |
| `/api/v1/people/{id}/stats?stats=season&group=pitching` | Season pitching stats | always (top players), `--catchup` (full roster) |
| `/api/v1/schedule?teamId={id}&startDate=...&endDate=...&hydrate=probablePitcher` | Upcoming schedule | `--catchup` |
| `/api/v1/teams/{id}/roster?rosterType=depthChart` | Depth chart for position context | `--catchup` |

**Dependency decision:** Evaluate the `MLB-StatsAPI` Python package (`pip install MLB-StatsAPI`) before writing raw `httpx` calls. It wraps these endpoints with convenience functions for rosters, schedules, standings, and box scores. If it covers the needed endpoints, use it instead of raw HTTP. If using raw `httpx`, add `tenacity` for retry logic with exponential backoff.

## Commands

### `mlb-digest`

The main command. Generates and emails the daily digest. Adapts its content based on flags and context (game day vs. off-day vs. off-season).

Email subject: **"{team_name} Daily — Mar 14, 2026"** (or **"{team_name} Catchup — Mar 14, 2026"** with `--catchup`)

#### Standard Digest Sections

1. **Around the League** — Headlines and storylines sourced directly from MLB-wide RSS feed articles (titles, summaries, links). Sonnet summarizes the article content into a few bullet points — trades, injuries, milestones, controversies. This section is article-driven, not stat-driven. If no MLB articles are available, this section is omitted.
2. **Last Night's Game** (if they played) — Final score, W/L, winning/losing pitcher, innings pitched, key stat lines from the box score (HR, multi-hit games, pitching line). Sonnet narrates these stats conversationally but does not invent plays or moments not reflected in the data.
3. **Today's Game** (if scheduled) — Opponent, time, TV channel (from broadcast field in schedule API), starting pitchers with season stats, head-to-head series record.
4. **Storylines** — Primarily sourced from team RSS feed articles: injuries, roster moves, trade rumors, series context. Supplemented with data-backed facts where available (W/L streak from standings, recent transactions from roster endpoint). The RSS articles drive the narrative; stats fill in the gaps.
5. **Standings Snapshot** — Division standings table (W-L, GB), team's last 10 record, team batting average, team ERA, individual leaders (top 3 hitters by AVG, top 3 pitchers by ERA from the active roster stats).
6. **Worth Reading** — 1-2 team articles + 1-2 MLB articles from RSS feeds, each with title, source, link, and a one-line summary.

**Off-day:** Sections 1, 4, 5, 6 only, plus a "Next Game" preview (date, opponent, probable pitchers).

#### `--catchup` Flag — Additional Sections

When `--catchup` is passed, the digest includes everything above **plus** these sections appended after Standings Snapshot:

- **The {team_name} Roster — Who to Know** — Starting lineup with positions, season stat lines, and role descriptions derived from stats (e.g., "leadoff hitter, leads the team in stolen bases" — not invented scouting notes). Rotation with ERA/record. Key bullpen arms and closer with save counts. Manager name.
- **Season So Far** — Record, division standing, recent results (last 10 games W-L), run differential. Key stat-backed observations (hot/cold streaks visible in the numbers).
- **Playoff Picture & IL Report** — Wild card standings, games back of playoff spot, key injured players with IL status from the roster endpoint. No speculative return dates unless sourced from articles.
- **Rivals to Know** — Division teams with records and GB, head-to-head record vs. configured team, key upcoming series dates.

### `mlb-digest test-email`

Sends a simple "Hello from MLB Digest — your email setup works!" message to verify Gmail configuration. No API calls, no data fetching.

### CLI Flags

- **`--catchup`** — Include roster, season overview, rivals, and playoff picture on top of the regular digest.
- **`--no-email`** — Print the final formatted narrative to stdout instead of sending email.
- **`--dry-run`** — Print the raw data that would be sent to Sonnet, without making the Anthropic API call or sending email. Useful for debugging data fetching.

## Off-Season Behavior (November – March)

The MLB regular season runs April through October. During the off-season:

- **`mlb-digest`** — Detects no scheduled games via the schedule API. Sends a reduced digest: RSS articles only (hot stove/free agency/trade news) + a note: "No games scheduled. The next season begins [date]." If no RSS articles are found either, skips sending entirely and logs "Off-season: no content available."
- **`mlb-digest --catchup`** — Works normally but notes the off-season context. Roster shows the 40-man roster (`rosterType=fortyMan`). Standings reflect final previous-season results.
- The API client must handle off-season data shapes: null probable pitchers, empty schedule responses, different roster types.

## Architecture

### Project Structure

```
mlb-digest-cli/
  src/
    mlb_digest/
      __init__.py
      mlb_api.py      — fetch data from MLB Stats API
      narrator.py     — Claude Sonnet calls to generate narratives
      emailer.py      — pluggable email transport (Gmail SMTP default)
      feeds.py        — RSS feed fetching, parsing, and deduplication
      cli.py          — Click CLI entry points (mlb-digest, test-email)
      config.py       — stable config (team ID, model, subject formats)
      templates.py    — HTML email template with inline CSS
  config.toml         — volatile config (RSS feed URLs, recipient list)
  tests/
    fixtures/         — sample API responses and RSS XML
    test_mlb_api.py
    test_narrator.py
    test_emailer.py
    test_feeds.py
    test_cli.py
    test_integration.py
  .env                — secrets (not committed)
  pyproject.toml
```

### Key Design Decisions

- **No database, no state.** Each run fetches fresh data. Cloud-ready with zero changes.
- **Team config, not hardcoded.** Team ID, team name, division, league, colors — all flow from `config.toml`. The CLI name (`mlb-digest`) and all internal references are team-agnostic. Changing teams is a config edit.
- **Sonnet for narratives, constrained.** See "Narrative Generation" section below for prompt strategy.
- **RSS for articles with deduplication.** See "RSS Feed Strategy" section below.
- **Pluggable email transport.** Gmail SMTP via app password is the default, but the emailer module accepts a transport interface so switching to OAuth 2.0 or SendGrid is a config change. See "Email Transport" section below.
- **Click for CLI.** One main command with `--catchup`, `--no-email`, and `--dry-run` flags. Plus `test-email` subcommand.
- **Multipart email.** HTML (inline CSS, single-column, team-colored headers) + plain text fallback. Sonnet generates markdown; `templates.py` converts to HTML.

## Narrative Generation (narrator.py)

Sonnet turns raw stats into a conversational digest. This is the core of the tool and must be carefully constrained.

### Prompt Strategy

**System prompt:**
```
You are a knowledgeable but casual {team_name} fan writing a morning email
digest for a friend who doesn't have time to watch every game. You are
conversational, not a sports anchor. You reference specific stats and facts
from the data provided.

CRITICAL RULES:
- ONLY reference facts, stats, and events present in the provided data.
- NEVER invent plays, moments, or descriptions not supported by the data.
- For headlines and storylines, use the RSS article titles and summaries
  provided. Summarize what the articles say — do NOT generate storylines
  from imagination.
- If the data shows a player hit 2-4 with a HR and 3 RBI, you can say
  "went 2-for-4 with a homer and 3 ribbies" — but do NOT invent the
  situation (e.g., "a clutch 2-run shot in the 8th") unless inning/situation
  data is in the input.
- For player descriptions in catchup reports, derive from stats only:
  "leads the team in HRs" not "has a smooth swing."
- When in doubt, state the numbers. Never embellish.
```

**Input format:** Structured JSON. Each section's data is passed as a clearly labeled JSON object so Sonnet knows exactly what data is available.

**One API call per run.** The full digest (with or without catchup sections) is generated in a single call. Simpler, cheaper, and produces more cohesive output.

**Temperature:** 0.7 — engaging but not creative with facts.

**Output format:** Sonnet returns markdown. `templates.py` converts to HTML.

### Token Budget Estimates

| Mode | Est. Input Tokens | Est. Output Tokens | Est. Cost/Call |
|------|------------------|--------------------|----------------|
| Game day | 2,000–4,000 | 800–1,500 | $0.01–0.03 |
| Off-day | 1,000–2,000 | 400–800 | $0.005–0.015 |
| With `--catchup` | 5,000–15,000 | 1,500–3,000 | $0.03–0.09 |

**Monthly estimate:** Daily digest (~$0.60/mo) + occasional `--catchup` (~$0.20/mo) = **~$0.80–1.50/month**.

Token usage is logged to stderr on every run so actual costs can be monitored.

## RSS Feed Strategy (feeds.py)

### Feed URLs

Stored in `config.toml` (not `config.py`) so they can be updated without code changes.

**Team-focused (Braves default):**
- `https://www.mlbtraderumors.com/atlanta-braves/feed` — Braves-specific trades, roster moves, injuries, analysis (verified working)

**MLB-wide:**
- `https://www.mlb.com/feeds/news/rss.xml` — Official MLB news (verified working)
- `https://www.espn.com/espn/rss/mlb/news` — Quality reporting + analysis (verified working)
- `https://www.mlbtraderumors.com/feed` — League-wide trades and transactions (verified working)
- `https://blogs.fangraphs.com/feed/` — Deep statistical analysis (verified working)

**Dead feeds (verified 404 as of 2026-03-14):** mlb.com/braves/feeds/news/rss, batterypower.com, talkingchop.com, SB Nation team blogs generally.

### Deduplication

RSS feeds often syndicate the same AP wire stories. `feeds.py` deduplicates by normalized title similarity (case-insensitive, strip punctuation, check for >80% overlap using `difflib.SequenceMatcher`). Deduplicated before passing to Sonnet.

### Selection

From deduplicated results, select the 1-2 most recent team articles and 1-2 most recent MLB articles. Pass title, source, link, and summary/description to Sonnet for the one-line summary. If the RSS description is empty or too short (<50 chars), pass only the title.

## Email Transport (emailer.py)

### Gmail SMTP (Default)

Uses app password via `smtplib`. Simple and free.

**Known risk:** Google has been systematically tightening authentication and could deprecate app passwords. They eliminated "less secure apps" in Sept 2024; app passwords are described as transitional in Google's docs.

### Pluggable Design

`emailer.py` defines a `send_email(subject, html_body, text_body, recipients)` function. The transport is selected by config:

```python
# Transports are swappable via config
TRANSPORT = "gmail_smtp"  # or "oauth2" or "sendgrid" in the future
```

Adding OAuth 2.0 or SendGrid later means adding a new transport function and changing the config value — no changes to `narrator.py`, `cli.py`, or any other module.

### Email Format

- **Multipart:** HTML + plain text fallback.
- **HTML:** Inline CSS (email clients strip `<style>` blocks). Single-column layout. Team primary color headers, team accent color highlights (configurable in `config.toml`). Simple, mobile-friendly.
- **Plain text:** Clean markdown-like formatting for clients that don't render HTML.
- **Sonnet generates markdown** → `templates.py` converts to HTML with the team-themed template.
- **Footer:** "Sources: MLB Stats API, RSS feeds. Narrated by Claude Sonnet."

### Recipients

`config.toml` supports a list of recipients for sharing with family:

```toml
[email]
recipients = ["you@gmail.com", "family@gmail.com"]
```

## Error Handling

**Philosophy: Log errors, send degraded email, never crash silently.**

This tool is designed to run unattended. A partial digest is always better than no digest.

| Component | Failure Mode | Behavior |
|-----------|-------------|----------|
| MLB Stats API | Down / timeout / error response | Log error. Skip sections that depend on this data. Send digest with available sections + note: "MLB data temporarily unavailable." |
| Anthropic API | Down / rate limited / error | Log error. Send raw stat summary (pre-formatted fallback) instead of narrative. Include note: "AI narrative unavailable — here are the raw numbers." |
| Gmail SMTP | Auth failure / timeout / rejected | Log error. Print the digest to stdout so it's captured in cron logs. Exit with non-zero status. |
| RSS Feeds | Down / malformed XML / empty | Log warning. Skip "Worth Reading" section. Rest of digest sends normally. |
| Individual feed | One feed fails, others succeed | Log warning for failed feed. Use articles from remaining feeds. |

**Retry logic:** MLB Stats API and RSS feeds retry up to 3 times with exponential backoff (1s, 2s, 4s) via `tenacity`. Anthropic API respects rate limit headers. Gmail SMTP retries once after 5s on transient errors.

**Exit codes:** 0 = success, 1 = partial failure (some data missing but email sent), 2 = fatal failure (email could not be sent).

**Logging:** All errors logged to stderr with timestamps. Token usage logged per run.

## Configuration

### `.env` (secrets, not committed)

```
ANTHROPIC_API_KEY=sk-...
GMAIL_ADDRESS=your@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

**Security:** `.env` should have restricted file permissions (`chmod 600`). For cloud deployment, use environment variables or a secrets manager instead of a file.

### `config.toml` (volatile config, committed)

```toml
[team]
id = 144
name = "Braves"
league_id = 104  # NL
colors = { primary = "#13274F", accent = "#CE1141" }

[email]
recipients = ["you@gmail.com"]
subject = "{team_name} Daily — {date}"
subject_catchup = "{team_name} Catchup — {date}"  # used when --catchup flag is passed
transport = "gmail_smtp"

[feeds.team]
urls = [
    "https://www.mlbtraderumors.com/atlanta-braves/feed",
]

[feeds.mlb]
urls = [
    "https://www.mlb.com/feeds/news/rss.xml",
    "https://www.espn.com/espn/rss/mlb/news",
    "https://www.mlbtraderumors.com/feed",
    "https://blogs.fangraphs.com/feed/",
]

[narrator]
model = "claude-sonnet-4-6"
temperature = 0.7
```

### `config.py` (stable config, code-level)

- MLB Stats API base URL
- Default retry/timeout settings
- Email template structure
- Loads `.env` and `config.toml`

## Dependencies

### Runtime

- `httpx` — HTTP client (or `MLB-StatsAPI` if it covers needed endpoints)
- `tenacity` — retry logic with backoff
- `anthropic` — Claude SDK for narrative generation
- `feedparser` — RSS feed parsing
- `python-dotenv` — load `.env` secrets
- `click` — CLI framework
- Standard library `tomllib` — parse `config.toml` (3.12+ stdlib)
- Standard library `smtplib` + `email` — Gmail SMTP
- Standard library `difflib` — RSS deduplication

### Dev

- `pytest`
- `ruff`
- `respx` — mock `httpx` requests (if using raw httpx)

### pyproject.toml

```toml
[project]
name = "mlb-digest-cli"
requires-python = ">=3.12"

[project.scripts]
mlb-digest = "mlb_digest.cli:main"
```

## Test Strategy

Every module has corresponding tests. Tests use fixture files, not live APIs.

### Fixtures (`tests/fixtures/`)

- `schedule_game_day.json` — MLB API schedule response for a day with a game
- `schedule_off_day.json` — MLB API schedule response with no game
- `schedule_off_season.json` — MLB API schedule response during off-season
- `standings.json` — MLB API standings response
- `roster.json` — MLB API active roster response
- `player_stats_hitting.json` — MLB API hitting stats response
- `player_stats_pitching.json` — MLB API pitching stats response
- `team_feed.xml` — Sample team RSS feed
- `mlb_feed.xml` — Sample MLB RSS feed
- `empty_feed.xml` — Empty/malformed RSS feed

All fixtures are captured from real API responses during development.

### Test Coverage by Module

| Module | What's Tested | Mocking Strategy |
|--------|--------------|------------------|
| `mlb_api.py` | Data fetching, parsing, off-season handling, error responses | `respx` to mock HTTP responses with fixture JSON |
| `narrator.py` | Prompt construction, response parsing, fallback on API error | Mock `anthropic.Anthropic` client, assert prompt structure contains expected data |
| `emailer.py` | Email construction, multipart format, recipient list, transport selection | Mock `smtplib.SMTP_SSL`, assert email headers and body structure |
| `feeds.py` | Feed parsing, deduplication, empty feed handling, malformed XML | `respx` to serve fixture XML files |
| `cli.py` | Flag handling (`--catchup`, `--no-email`, `--dry-run`), exit codes | Mock all underlying modules, assert correct orchestration |
| `test_integration.py` | Full pipeline: data fetch → narrate → format → "send" | All external calls mocked, assert final email contains all expected sections |

### Test Philosophy

- **Arrange / Act / Assert** structure with blank line separators.
- Test names describe behavior: `test_digest_skips_game_recap_on_off_day`, `test_feeds_deduplicates_ap_wire_stories`.
- No test helpers that hide what's being tested.
- Fixture data lives in files, not inline in tests.

## Scheduling (Future)

Built for manual execution now. No state or scheduling logic in the tool itself. When ready for cloud deployment, wrap in AWS Lambda / cron / Task Scheduler — the tool just runs, generates, sends, and exits. Cloud deployments should use environment variables or a secrets manager instead of `.env` files.
