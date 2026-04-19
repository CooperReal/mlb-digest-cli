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
