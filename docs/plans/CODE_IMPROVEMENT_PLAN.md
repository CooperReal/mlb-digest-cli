# MLB Digest CLI — Code Improvement Plan

A step-by-step implementation plan covering every improvement from the initial
code review. Each section includes what changes, why, which files are touched,
and what tests to write.

---

## Table of Contents

1. Fix the N+1 Player Stats Problem
2. Parallel RSS Feed Fetching
3. Daily File Cache Layer
4. Validate Narrator Output
5. Reusable Anthropic Client
6. Structured Error Handling (Replace bare None returns)
7. Config Validation at Load Time
8. Decouple Prompt Data from Serialization
9. Dynamic Subject Lines with Scores
10. Email Template Redesign
11. X/Twitter Auto-Posting Integration
12. Multi-Team Registry Support

---

## 1. Fix the N+1 Player Stats Problem

### Problem

`get_top_players()` fires one API call per roster player (25-40 individual
calls via `get_player_stats()`). This is the single biggest performance
bottleneck. On a 40-man roster, this takes 15-30 seconds and hammers the
MLB Stats API with redundant requests.

### Solution

Replace the per-player `statsapi.player_stat_data()` calls with a single
bulk endpoint. The MLB Stats API supports fetching team-level stats in one
request via `statsapi.get("team_stats", ...)` or by hitting the
`/api/v1/teams/{id}/stats` endpoint directly.

### Files Changed

| File | Change |
|------|--------|
| `mlb_api.py` | Replace `get_top_players()` internals with bulk fetch |
| `mlb_api.py` | Remove `get_player_stats()` single-player function (or keep for catchup) |
| `tests/test_mlb_api.py` | Update mocks, add test for bulk fetch, test sorting |

### Implementation Steps

1. **Add `_fetch_team_stats()` helper** that calls
   `statsapi.get("team_stats", {"teamId": team_id, ...})` to get all
   hitters and pitchers in two requests (one for hitting, one for pitching)
   instead of N requests.

2. **Update `get_top_players()`** to accept `team_id: int` instead of
   `roster: list[RosterPlayer]`. It calls `_fetch_team_stats()` twice
   (hitting + pitching), parses the response, sorts by AVG/ERA, and
   returns the top 3 of each.

3. **Remove the `ThreadPoolExecutor`** from `get_top_players()` — it's no
   longer needed since we're making 2 calls instead of 40.

4. **Keep `get_player_stats()`** available for the `--catchup` flow where
   individual player detail might be useful, but mark it as optional.

5. **Update `cli.py`** to pass `team_id` instead of `roster` to
   `get_top_players()`.

### Tests

- `test_bulk_stats_returns_top_hitters_sorted_by_avg`
- `test_bulk_stats_returns_top_pitchers_sorted_by_era`
- `test_bulk_stats_handles_empty_response`
- `test_bulk_stats_retries_on_failure`
- `test_top_players_count_parameter`

### Performance Impact

Before: 25-40 API calls, ~20 seconds
After: 2 API calls, ~1 second

---

## 2. Parallel RSS Feed Fetching

### Problem

`fetch_articles()` fetches each RSS feed URL sequentially. With 5-7 feeds
configured, this adds 5-10 seconds of serial I/O waiting.

### Solution

Use `ThreadPoolExecutor` (already imported in `mlb_api.py`) to fetch all
feeds in parallel. The feeds are independent — no ordering dependency.

### Files Changed

| File | Change |
|------|--------|
| `feeds.py` | Add parallel fetching with ThreadPoolExecutor |
| `tests/test_feeds.py` | Add test for concurrent fetch behavior |

### Implementation Steps

1. **Refactor `fetch_articles()`** to submit all URLs to a thread pool
   and collect results as they complete:

   ```python
   def fetch_articles(feed_urls: list[str], source_type: str) -> list[Article]:
       articles: list[Article] = []

       with ThreadPoolExecutor(max_workers=len(feed_urls)) as executor:
           future_to_url = {
               executor.submit(_fetch_and_parse_feed, url, source_type): url
               for url in feed_urls
           }
           for future in as_completed(future_to_url):
               url = future_to_url[future]
               try:
                   articles.extend(future.result())
               except Exception:
                   logger.warning("Failed to fetch feed: %s", url, exc_info=True)

       return articles
   ```

2. **Extract `_fetch_and_parse_feed()`** — move the per-URL fetch + parse
   logic into its own function that returns `list[Article]`.

3. **Cap `max_workers`** at 8 to avoid opening too many connections.

### Tests

- `test_parallel_fetch_returns_articles_from_all_feeds`
- `test_parallel_fetch_continues_when_one_feed_fails`
- `test_parallel_fetch_empty_url_list`

### Performance Impact

Before: ~8 seconds (sequential, 5 feeds × ~1.5s each)
After: ~2 seconds (parallel, limited by slowest feed)

---

## 3. Daily File Cache Layer

### Problem

Every run hits all external APIs from scratch. During development, this
wastes time and API quota. If the narrator fails, you have to re-fetch
everything. There's no way to iterate on the prompt without re-running
the full pipeline.

### Solution

Add a simple file-based cache at `~/.cache/mlb-digest/` keyed by date.
Cache raw API responses for the day. Subsequent runs reuse cached data.

### Files Changed

| File | Change |
|------|--------|
| `cache.py` | **NEW** — read/write JSON cache by date |
| `cli.py` | Wire cache into the pipeline |
| `mlb_api.py` | No change — cache wraps the callers, not the API module |
| `tests/test_cache.py` | **NEW** — cache read/write/expiry tests |

### Implementation Steps

1. **Create `cache.py`** with a `DailyCache` class:

   ```python
   @dataclass
   class DailyCache:
       cache_dir: Path = Path.home() / ".cache" / "mlb-digest"

       def get(self, key: str, date: date | None = None) -> dict | None:
           """Return cached data for today (or given date), or None."""

       def set(self, key: str, data: dict, date: date | None = None) -> None:
           """Write data to cache for today."""

       def clear(self, date: date | None = None) -> None:
           """Delete cache for a given date."""
   ```

2. **Cache keys** map to pipeline stages:
   - `yesterday_game` — GameResult
   - `today_game` — UpcomingGame
   - `standings` — DivisionStandings list
   - `team_articles` — Article list
   - `mlb_articles` — Article list
   - `roster` — RosterPlayer list
   - `top_players` — dict

3. **Cache file format**: `~/.cache/mlb-digest/2026-04-04/standings.json`

4. **CLI integration**: Add `--no-cache` flag to bypass. Cache is on by
   default. Cache auto-expires after 24 hours (next day's run ignores
   yesterday's cache).

5. **Serialization**: All dataclasses already support `asdict()`. For
   deserialization, add `from_dict()` classmethods or simple factory
   functions.

### Tests

- `test_cache_write_and_read_roundtrip`
- `test_cache_miss_returns_none`
- `test_cache_ignores_stale_date`
- `test_cache_clear_removes_files`
- `test_cache_creates_directory_if_missing`
- `test_no_cache_flag_bypasses_cache`

---

## 4. Validate Narrator Output

### Problem

Claude returns markdown, but there's no verification that the output
contains the sections we requested. If Claude hallucinates a different
structure, the email looks broken or incomplete with no warning.

### Solution

After `generate_narrative()` returns, check that the markdown contains
the expected `##` section headers. If validation fails, retry once with
a stricter prompt. If the retry also fails, log a warning and use the
best attempt.

### Files Changed

| File | Change |
|------|--------|
| `narrator.py` | Add `validate_narrative()` function |
| `cli.py` | Call validator after generation, handle retry |
| `tests/test_narrator.py` | Tests for validation logic |

### Implementation Steps

1. **Add `validate_narrative()`** to `narrator.py`:

   ```python
   def validate_narrative(
       narrative: str,
       expected_sections: list[str],
   ) -> tuple[bool, list[str]]:
       """
       Check that the narrative contains the expected section headers.
       Returns (is_valid, missing_sections).
       """
       found_headers = re.findall(r"^## (.+)$", narrative, re.MULTILINE)
       # Fuzzy match against expected sections
       ...
   ```

2. **Expected sections** are derived from the prompt's OrderedDict keys:
   `around_the_league`, `last_nights_game`, `todays_game`, etc. Map these
   to expected header patterns.

3. **Retry logic in `cli.py`**: If validation fails, append a correction
   to the prompt: "Your previous response was missing these sections:
   [list]. Please include all sections." Re-call `generate_narrative()`.

4. **Max retries**: 1 retry. If both attempts fail validation, use the
   better attempt (the one with more matching sections) and log a warning.

### Tests

- `test_valid_narrative_passes_validation`
- `test_missing_section_fails_validation`
- `test_extra_sections_still_passes`
- `test_validation_is_case_insensitive`
- `test_empty_narrative_fails`

---

## 5. Reusable Anthropic Client

### Problem

`generate_narrative()` creates a new `anthropic.Anthropic()` client on
every call. This is wasteful (re-initializes HTTP connection pool) and
makes it harder to add features like token tracking across multiple calls
(e.g., tweet generation + digest generation).

### Solution

Instantiate the client once in `cli.py` and pass it through. This also
sets up the architecture for the X/Twitter tweet generation (Plan 3 from
the original review), which will need its own Claude call.

### Files Changed

| File | Change |
|------|--------|
| `narrator.py` | Accept `client: anthropic.Anthropic` instead of `api_key: str` |
| `cli.py` | Create client once, pass to all narrator calls |
| `tests/test_narrator.py` | Update mocks to use client object |

### Implementation Steps

1. **Update `generate_narrative()` signature**:

   ```python
   def generate_narrative(
       prompt: str,
       system_prompt: str,
       client: anthropic.Anthropic,  # was: api_key: str
       model: str,
       temperature: float,
       max_tokens: int = 4096,
   ) -> str:
   ```

2. **Create client in `cli.py`**:

   ```python
   client = anthropic.Anthropic(api_key=config.anthropic_api_key)
   narrative = generate_narrative(prompt=prompt, client=client, ...)
   ```

3. **Add token tracking**: Store cumulative input/output tokens on the
   client or in a simple counter, log total at the end of the run.

### Tests

- `test_generate_uses_provided_client`
- `test_client_is_not_recreated_per_call`

---

## 6. Structured Error Handling

### Problem

API functions return `None` for both "no data available" (e.g., no game
today) and "API call failed" (e.g., network error). The caller can't
distinguish between these two very different situations. This leads to
silent failures — if the MLB API is down, the digest just skips sections
without telling anyone.

### Solution

Introduce a lightweight result pattern using a union type. Functions
return either the data or a specific error, never bare `None`.

### Files Changed

| File | Change |
|------|--------|
| `mlb_api.py` | Add `FetchError` dataclass, update return types |
| `cli.py` | Handle `FetchError` vs `None` differently |
| `tests/test_mlb_api.py` | Update assertions for new return types |

### Implementation Steps

1. **Add error type**:

   ```python
   @dataclass
   class FetchError:
       source: str      # "yesterday_game", "standings", etc.
       message: str     # Human-readable error
       exception: Exception | None = None
   ```

2. **Update return types**:

   ```python
   def get_yesterday_game(team_id: int) -> GameResult | FetchError | None:
       # Returns GameResult if game found
       # Returns None if no game scheduled
       # Returns FetchError if API call failed
   ```

3. **CLI handles errors explicitly**:

   ```python
   yesterday_game = get_yesterday_game(config.team_id)
   if isinstance(yesterday_game, FetchError):
       logger.warning("Could not fetch yesterday's game: %s", yesterday_game.message)
       # Still continue — just skip this section
   ```

4. **Aggregate errors** and include a warning in the email footer if any
   data source failed: "Note: standings data was unavailable for this
   digest."

### Tests

- `test_api_failure_returns_fetch_error`
- `test_no_game_returns_none`
- `test_successful_fetch_returns_data`
- `test_cli_continues_on_fetch_error`
- `test_fetch_error_included_in_email_footer`

---

## 7. Config Validation at Load Time

### Problem

`load_config()` does zero validation. A missing `[narrator]` section
gives a cryptic `KeyError`. An invalid `temperature` of `"hot"` passes
through silently until the Anthropic API rejects it. A typo in the
transport name (`"gmail_stmp"`) isn't caught until email sending time.

### Solution

Validate all config fields at load time with clear error messages. No
external dependencies needed — use simple checks in the `Config`
dataclass or a post-init validator.

### Files Changed

| File | Change |
|------|--------|
| `config.py` | Add `__post_init__()` validation to `Config` |
| `tests/test_config.py` | Tests for every validation rule |

### Implementation Steps

1. **Add `__post_init__()` to `Config`**:

   ```python
   def __post_init__(self) -> None:
       if self.team_id <= 0:
           raise ValueError(f"Invalid team_id: {self.team_id}")
       if not self.team_name:
           raise ValueError("team_name cannot be empty")
       if self.narrator_temperature < 0 or self.narrator_temperature > 2:
           raise ValueError(f"narrator_temperature must be 0-2, got {self.narrator_temperature}")
       if self.email_transport not in ("gmail_smtp",):
           raise ValueError(f"Unknown email transport: {self.email_transport}")
       if not self.email_recipients:
           raise ValueError("At least one email recipient is required")
   ```

2. **Validate feed URLs**: Check that each URL starts with `http://` or
   `https://`. Don't fetch — just syntax check.

3. **Validate color format**: Check that colors match `#RRGGBB` pattern.

4. **Friendly error messages**: Every validation error should say what's
   wrong AND how to fix it: "narrator_temperature must be between 0 and
   2.0 (got 'hot'). Set it as a number in config.toml: temperature = 0.7"

### Tests

- `test_invalid_team_id_raises`
- `test_empty_team_name_raises`
- `test_bad_temperature_raises`
- `test_unknown_transport_raises`
- `test_no_recipients_raises`
- `test_bad_color_format_raises`
- `test_valid_config_passes_validation`

---

## 8. Decouple Prompt Data from Serialization

### Problem

`build_prompt()` returns a JSON string. The structured data (sections,
game results, articles) is immediately serialized and can't be reused.
If you want to generate a tweet (Plan 3) or validate sections (item 4
above), you have to re-parse the JSON or duplicate the data gathering.

### Solution

Split `build_prompt()` into two functions: one that builds the structured
data, one that serializes it for Claude.

### Files Changed

| File | Change |
|------|--------|
| `narrator.py` | Split into `build_digest_data()` + `serialize_prompt()` |
| `cli.py` | Call both functions, pass data to validator and tweet generator |
| `tests/test_narrator.py` | Update tests for new function signatures |

### Implementation Steps

1. **Add `DigestData` type** (or use the OrderedDict directly):

   ```python
   @dataclass
   class DigestData:
       sections: OrderedDict[str, dict]
       team_name: str
       catchup: bool

       @property
       def section_names(self) -> list[str]:
           return list(self.sections.keys())

       def to_prompt(self) -> str:
           return json.dumps(self.sections, indent=2)
   ```

2. **Rename `build_prompt()` → `build_digest_data()`**: Returns
   `DigestData` instead of `str`.

3. **Usage in `cli.py`**:

   ```python
   digest_data = build_digest_data(...)
   prompt = digest_data.to_prompt()
   narrative = generate_narrative(prompt=prompt, ...)

   # Now we can also use digest_data for:
   is_valid, missing = validate_narrative(narrative, digest_data.section_names)
   tweet = generate_tweet(digest_data, client=client)
   ```

### Tests

- `test_digest_data_section_names_match_keys`
- `test_digest_data_to_prompt_is_valid_json`
- `test_digest_data_without_game_omits_game_section`

---

## 9. Dynamic Subject Lines with Scores

### Problem

The current subject line is static: "Braves Daily — Apr 04, 2026". This
tells the recipient nothing about what happened. Most people decide
whether to open an email based on the subject line alone.

### Solution

Include the game result in the subject line when available:
"🪓 Braves 6, Mets 3 — Daily Digest — Apr 04"

### Files Changed

| File | Change |
|------|--------|
| `config.py` | Update `format_subject()` to accept game data |
| `cli.py` | Pass yesterday's game result to subject formatter |
| `tests/test_config.py` | Tests for subject line formatting |

### Implementation Steps

1. **Update `format_subject()`**:

   ```python
   def format_subject(
       self,
       catchup: bool = False,
       yesterday_game: GameResult | None = None,
   ) -> str:
       template = self.email_subject_catchup_template if catchup else self.email_subject_template

       # Build score string if game data available
       score = ""
       if yesterday_game:
           score = f"{yesterday_game.home_team} {yesterday_game.home_score}, {yesterday_game.away_team} {yesterday_game.away_score}"

       return template.format(
           team_name=self.team_name,
           emoji=self.team_emoji,
           score=score,
           date=date.today().strftime("%b %d"),
       )
   ```

2. **Update default template**:
   ```
   "{emoji} {score} — {team_name} Digest — {date}"
   ```
   Falls back to `"{emoji} {team_name} Digest — {date}"` when no game.

### Tests

- `test_subject_includes_score_when_game_exists`
- `test_subject_omits_score_when_no_game`
- `test_catchup_subject_uses_catchup_template`

---

## 10. Email Template Redesign

### Problem

The current email is a flat wall of markdown-to-HTML with no visual
hierarchy. On mobile, it's hard to scan. There's no score banner, no
styled standings table, and the "Worth Reading" section is just a list.

### Solution

Redesign the HTML template with card-based sections, a score banner,
styled tables, and mobile-optimized spacing. All inline styles (email
clients strip `<style>` blocks).

### Files Changed

| File | Change |
|------|--------|
| `templates.py` | Rewrite `render_email_html()` with new design |
| `templates.py` | Add `_render_score_banner()` helper |
| `tests/test_templates.py` | Tests for new HTML structure |

### Implementation Steps

1. **Score banner at top**: A full-width colored bar showing the final
   score in large text. This is the first thing the reader sees.

2. **Card-based sections**: Each `## Section` becomes a div with
   padding, subtle background, and clear separation from the next
   section.

3. **Styled standings table**: The user's team row gets highlighted
   with the accent color. Headers use the primary color.

4. **"Worth Reading" as mini-cards**: Each article gets a container
   with source label, title link, and one-line summary.

5. **Mobile spacing**: 16px minimum font, 44px minimum link tap
   targets, generous padding.

6. **Footer with branding**: Team emoji, data sources, and a
   subscribe/feedback link.

### Tests

- `test_html_contains_team_colors`
- `test_html_has_viewport_meta_tag`
- `test_html_inline_styles_on_headings`
- `test_plain_text_strips_markdown`

---

## 11. X/Twitter Auto-Posting Integration

### Problem

No way to promote the newsletter or reach new subscribers. The digest
goes to email only, limiting growth.

### Solution

After sending the email, auto-post a teaser tweet to X with the score,
one highlight stat, and a subscribe CTA. Uses the `tweepy` library for
X API v2 integration.

### Files Changed

| File | Change |
|------|--------|
| `social.py` | **NEW** — X API client, tweet generation |
| `cli.py` | Add `--no-social` flag, post after email |
| `config.py` | Add social config fields |
| `config.toml` | Add `[social.x]` section |
| `narrator.py` | Add `generate_tweet()` function |
| `tests/test_social.py` | **NEW** — mock tweet posting |

### Implementation Steps

1. **Create `social.py`** with `post_to_x()`:

   ```python
   def post_to_x(
       tweet_text: str,
       api_key: str,
       api_secret: str,
       access_token: str,
       access_secret: str,
   ) -> str:
       """Post a tweet and return the tweet ID."""
   ```

2. **Add `generate_tweet()` to `narrator.py`**: A separate Claude call
   that takes the DigestData and produces a 280-char tweet.

3. **Tweet styles rotation**: Give Claude 4 styles to choose from
   randomly each day:
   - Score-focused: "Braves 6, Mets 3. Sale: 7 IP, 9 K..."
   - Stat-focused: "Ronald Acuña Jr. is hitting .342 this month..."
   - Storyline: "Trade deadline buzz around the Braves..."
   - Hot take: "This bullpen might be the best in the NL..."

4. **Thread support**: On days with recap + preview, post a 2-tweet
   thread. Tweet 1 = recap teaser. Tweet 2 = preview + subscribe link.

5. **CLI flag**: `--no-social` skips posting. Social failures are logged
   but don't fail the run.

6. **Config**:
   ```toml
   [social.x]
   enabled = true
   cta_link = "https://yoursite.com/subscribe"
   hashtags = ["Braves", "MLB"]
   ```

### Tests

- `test_tweet_under_280_chars`
- `test_tweet_includes_score_when_available`
- `test_tweet_includes_cta_link`
- `test_social_failure_does_not_fail_run`
- `test_no_social_flag_skips_posting`
- `test_thread_created_for_recap_plus_preview`

---

## 12. Multi-Team Registry Support

### Problem

The tool is hardcoded for the Braves. Switching teams requires manually
finding the MLB API team ID, league ID, choosing colors, and finding
RSS feeds. There's no discoverability.

### Solution

A 30-team registry that auto-fills everything from a single team name.
Users just set `name = "Yankees"` in config.toml. Includes team-specific
narrator personality hints so each team's digest has a different voice.

(This is fully detailed in `MULTI_TEAM_PLAN.md` and all implementation
files have already been created — see the files delivered previously.)

### Files Changed

| File | Change |
|------|--------|
| `teams_registry.py` | **NEW** — all 30 teams with metadata |
| `config.py` | Registry lookup with override merging |
| `config.toml` | Simplified to `name = "Yankees"` |
| `narrator.py` | Team personality in system prompt |
| `cli.py` | `list-teams` subcommand |
| `tests/test_teams_registry.py` | **NEW** — 30 tests |

---

## Implementation Order

These items have dependencies. Here's the order that minimizes conflicts
and lets you ship incrementally:

```
Phase 1 — Foundation (no behavior changes, enables everything else)
  ├── 12. Multi-Team Registry     ← already built
  ├──  7. Config Validation
  └──  5. Reusable Anthropic Client

Phase 2 — Performance (biggest user-facing wins)
  ├──  1. Fix N+1 Player Stats
  ├──  2. Parallel RSS Fetching
  └──  3. Daily File Cache

Phase 3 — Quality (better output, better errors)
  ├──  6. Structured Error Handling
  ├──  8. Decouple Prompt Data
  ├──  4. Validate Narrator Output
  └──  9. Dynamic Subject Lines

Phase 4 — Design (visual upgrade)
  └── 10. Email Template Redesign

Phase 5 — Growth (new channel)
  └── 11. X/Twitter Integration
```

Each phase can be shipped as its own PR. Phase 1 items are independent
of each other. Phase 2 items are independent of each other. Phase 3
items should be done in the listed order (6 → 8 → 4 → 9). Phase 4 and
5 are independent.

---

## Testing Strategy

Every item above includes specific test names. The overall approach:

- **Unit tests for every new function** — no exceptions
- **Integration test updates** for the full pipeline
- **Mock all external APIs** — MLB Stats API, RSS feeds, Anthropic, Gmail, X
- **Run `bash check.sh` before every commit** — lint, mypy, pytest
- **CI catches regressions** — the existing GitHub Actions workflow
  already runs everything on push

Target: maintain the current 95%+ coverage after all changes.

---

## Estimated Effort

| Phase | Items | Estimated Time |
|-------|-------|----------------|
| Phase 1 | Registry, config validation, client reuse | 2-3 hours |
| Phase 2 | N+1 fix, parallel feeds, cache | 3-4 hours |
| Phase 3 | Error handling, prompt decoupling, validation, subjects | 3-4 hours |
| Phase 4 | Email redesign | 2-3 hours |
| Phase 5 | X integration | 3-4 hours |
| **Total** | **12 items** | **~15 hours** |

These estimates assume familiarity with the codebase (which you have).
Each phase is independently shippable — you don't have to do all 5 at once.
