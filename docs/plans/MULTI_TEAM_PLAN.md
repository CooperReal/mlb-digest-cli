# Multi-Team Support Plan

## Overview

Transform MLB Digest from a single-team Braves tool into a configurable newsletter
that works for any of the 30 MLB teams, with team-specific email theming, feeds,
and narrator personality.

---

## What Changes

### 1. New File: `teams_registry.py`

A single Python module containing a `TEAMS` dictionary with every MLB team's:

- **MLB Stats API ID** — used for all API calls
- **Full name, short name, abbreviation** — for display and matching
- **League ID** — 103 (AL) or 104 (NL)
- **Division** — for context in the narrator prompt
- **Colors** — primary, secondary, accent — drives the entire email theme
- **RSS feed URLs** — team-specific MLBTradeRumors feed + subreddit
- **Emoji** — for subject lines and social posts
- **Narrator personality hint** — a one-liner that gives Claude the team's vibe

This is the single source of truth. No more hardcoding Braves data anywhere.

### 2. Simplified `config.toml`

The user only needs to set ONE field to switch teams:

```toml
[team]
name = "Yankees"   # That's it. Everything else is looked up.
```

They can still override colors, feeds, or any other field if they want,
but the defaults from the registry cover everything.

### 3. Updated `config.py`

- Looks up the team name/abbreviation in the registry
- Merges registry defaults with any user overrides from `config.toml`
- Validates that the team name actually exists (clear error if not)
- Adds a `--list-teams` CLI flag to print all available teams

### 4. Team-Themed Email Templates

Each team gets a visually distinct email driven by their color palette:

- **Header banner** — team primary color background, white text
- **Section dividers** — accent color underlines
- **Standings highlight** — the user's team row gets the accent background
- **Links** — accent color
- **Footer** — subtle team branding

The template code stays the same — it just receives different colors per team.
No 30 separate HTML files. One template, 30 color schemes.

### 5. Team-Aware Narrator

The system prompt already takes `team_name`, but we enhance it with:

- The team's division context ("NL East rival of the Mets and Phillies")
- A personality hint ("Write like a passionate Bronx fan" vs "laid-back West Coast vibes")
- This makes the digest feel authentically different per team

---

## File-by-File Changes

| File | Change |
|------|--------|
| `teams_registry.py` | **NEW** — all 30 teams, colors, feeds, metadata |
| `config.toml` | Simplified to just `name = "Yankees"` |
| `config.py` | Looks up team in registry, merges overrides |
| `narrator.py` | Uses team personality hint in system prompt |
| `templates.py` | No structural change — already parameterized by color |
| `cli.py` | Adds `--list-teams` subcommand |
| `tests/` | New tests for registry lookup, override merging |

---

## How a User Switches Teams

**Before (current):**
```toml
[team]
id = 144
name = "Braves"
league_id = 104
colors = { primary = "#13274F", accent = "#CE1141" }

[feeds.team]
urls = ["https://www.mlbtraderumors.com/atlanta-braves/feed"]
```

**After (new):**
```toml
[team]
name = "Yankees"
```

That's it. The registry fills in ID 147, league 103, navy/red colors,
Yankees-specific feeds, and the narrator personality. If they want to
override the accent color or add a custom feed, they still can:

```toml
[team]
name = "Yankees"
colors = { accent = "#FFD700" }  # gold instead of red

[feeds.team]
urls = ["https://custom-yankees-blog.com/feed"]  # overrides default
```

---

## CLI Addition

```bash
mlb-digest list-teams          # Print all 30 teams with IDs and abbreviations
mlb-digest list-teams --json   # Machine-readable output
```

Output:
```
AL East
  BAL  Baltimore Orioles      (ID: 110)
  BOS  Boston Red Sox          (ID: 111)
  NYY  New York Yankees        (ID: 147)
  TB   Tampa Bay Rays          (ID: 139)
  TOR  Toronto Blue Jays       (ID: 141)

AL Central
  CWS  Chicago White Sox       (ID: 145)
  CLE  Cleveland Guardians     (ID: 114)
  ...
```

---

## Migration Path

1. Add `teams_registry.py` — no existing code breaks
2. Update `config.py` to check registry first, fall back to manual config
3. Update `config.toml` defaults — old format still works
4. Add `list-teams` CLI command
5. Update narrator system prompt to use personality hints
6. Add tests for all new behavior
7. Update README with new setup instructions

Existing users with the old `config.toml` format keep working.
The registry is only used when `league_id` or `id` are not explicitly set.

---

## Team Data Sources

- **Team IDs**: MLB Stats API (`statsapi.lookup_team()`)
- **Colors**: Official MLB brand guidelines
- **RSS feeds**: MLBTradeRumors team pages + team subreddits
- **League/Division**: MLB Stats API metadata

All 30 teams are defined in `teams_registry.py` (see that file).
