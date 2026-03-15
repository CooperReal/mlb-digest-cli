# MLB Digest CLI

[![CI](https://github.com/CooperReal/mlb-digest-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/CooperReal/mlb-digest-cli/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

A personal CLI tool that sends you a daily email digest about your MLB team. It fetches game results, standings, and articles, then uses Claude to write it up in a conversational tone so you can stay connected without watching every game.

Built for the Atlanta Braves by default, but configurable for any team.

## What You Get

**Daily digest email with:**
- Around the League headlines (from RSS articles)
- Last night's game recap with key stats
- Today's game preview with starting pitchers
- Team storylines from RSS articles
- Division standings snapshot with top hitters/pitchers
- Worth Reading links to recent articles

**Catchup mode** adds roster breakdown, season overview, playoff picture, and rivals.

## Quick Start

```bash
# Clone and install
git clone https://github.com/CooperReal/mlb-digest-cli.git
cd mlb-digest-cli
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e ".[dev]"

# Configure (see User Guide below)
cp .env.example .env
# Edit .env with your API keys

# Test it
mlb-digest --no-email        # Print digest to terminal
mlb-digest --catchup --no-email  # Full catchup report
mlb-digest test-email        # Verify Gmail works
mlb-digest                   # Send the daily email
```

## Requirements

- Python 3.11+
- [Anthropic API key](https://console.anthropic.com/) (Claude Sonnet, ~$1/month)
- Gmail account with [App Password](https://myaccount.google.com/apppasswords)

## CLI Usage

```
mlb-digest [OPTIONS]
mlb-digest test-email
```

| Flag | What it does |
|------|-------------|
| `--catchup` | Include roster, season overview, rivals, playoff picture |
| `--no-email` | Print to terminal instead of sending email |
| `--dry-run` | Show raw data without calling Claude or sending email |

| Subcommand | What it does |
|------------|-------------|
| `test-email` | Send a test email to verify your Gmail setup |

## Configuration

### Secrets (`.env`)

```
ANTHROPIC_API_KEY=sk-ant-...
GMAIL_ADDRESS=your@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

### Settings (`config.toml`)

```toml
[team]
id = 144                # MLB team ID (144 = Braves)
name = "Braves"
league_id = 104         # 104 = NL, 103 = AL
colors = { primary = "#13274F", accent = "#CE1141" }

[email]
recipients = ["you@gmail.com"]
subject = "{team_name} Daily - {date}"
subject_catchup = "{team_name} Catchup - {date}"
transport = "gmail_smtp"

[feeds.team]
urls = ["https://www.mlbtraderumors.com/atlanta-braves/feed"]

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

## Development

```bash
# Run tests
pytest tests/ -v

# Lint
ruff check src/ tests/
ruff format src/ tests/

# Type check
mypy src/mlb_digest/
```

CI runs lint, mypy, and tests on every push and PR via GitHub Actions.

## Architecture

```
MLB Stats API  ->  Game data, standings, roster, stats
RSS Feeds      ->  Team + MLB articles
                      |
               Claude Sonnet  ->  Conversational narrative
                      |
               Gmail SMTP  ->  Formatted email (HTML + plain text)
```

Seven modules: `config`, `feeds`, `mlb_api`, `narrator`, `templates`, `emailer`, `cli`.

## License

Personal project. Use however you like.
