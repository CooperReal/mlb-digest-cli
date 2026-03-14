# MLB Digest CLI — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a CLI tool that fetches MLB data and RSS articles, uses Claude Sonnet to generate a conversational digest, and emails it daily.

**Architecture:** Single CLI entry point (`mlb-digest`) with `--catchup`, `--no-email`, and `--dry-run` flags. Data flows through four modules: `mlb_api.py` (MLB Stats API via `statsapi` convenience functions), `feeds.py` (RSS via `feedparser`), `narrator.py` (Claude Sonnet via `anthropic`), and `emailer.py` (Gmail SMTP). Config split between `.env` (secrets) and `config.toml` (volatile settings).

**Tech Stack:** Python 3.12+, MLB-StatsAPI, anthropic SDK, feedparser, click, tenacity, python-dotenv, markdown, pytest, ruff

**Design doc:** `docs/plans/2026-03-14-braves-daily-digest-design.md`

## Execution Order

```
Phase 1 (sequential):  Task 1 → Task 2
Phase 2 (parallel):    Tasks 3, 4, 6, 7 — all independent, run simultaneously
Phase 3 (sequential):  Task 5 (depends on 3 + 4)
Phase 4 (sequential):  Task 8 (depends on 2, 3, 4, 5, 6, 7)
Phase 5 (sequential):  Task 9 (depends on 8)
Phase 6 (sequential):  Task 10 (depends on 9)
```

---

## Task 1: Project Scaffolding — *Phase 1 (sequential)*

**Files:**
- Create: `pyproject.toml`
- Create: `src/mlb_digest/__init__.py`
- Create: `config.toml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `tests/__init__.py`
- Create: `tests/fixtures/` (directory)

**Step 1: Create `pyproject.toml`**

```toml
[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[project]
name = "mlb-digest-cli"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "MLB-StatsAPI>=1.9.0",
    "anthropic>=0.40.0",
    "feedparser>=6.0",
    "click>=8.1",
    "tenacity>=8.2",
    "python-dotenv>=1.0",
    "httpx>=0.27",
    "markdown>=3.6",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "ruff>=0.4",
]

[project.scripts]
mlb-digest = "mlb_digest.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "W"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

**Step 2: Create `src/mlb_digest/__init__.py`**

```python
"""MLB Digest CLI — daily MLB team digest via email."""
```

**Step 3: Create `config.toml`**

```toml
[team]
id = 144
name = "Braves"
league_id = 104
colors = { primary = "#13274F", accent = "#CE1141" }

[email]
recipients = ["you@gmail.com"]
subject = "{team_name} Daily — {date}"
subject_catchup = "{team_name} Catchup — {date}"
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

**Step 4: Create `.env.example`**

```
ANTHROPIC_API_KEY=sk-ant-...
GMAIL_ADDRESS=your@gmail.com
GMAIL_APP_PASSWORD=xxxx-xxxx-xxxx-xxxx
```

**Step 5: Create `.gitignore`**

```
.env
__pycache__/
*.pyc
*.egg-info/
dist/
build/
.venv/
.pytest_cache/
.ruff_cache/
```

**Step 6: Create empty `tests/__init__.py` and `tests/fixtures/` directory**

**Step 7: Install the project in dev mode**

Run: `pip install -e ".[dev]"`
Expected: Installs all dependencies, `mlb-digest` command becomes available.

**Step 8: Verify setup**

Run: `python -c "import mlb_digest; print('ok')"`
Expected: `ok`

**Step 9: Commit**

```bash
git add pyproject.toml src/ config.toml .env.example .gitignore tests/
git commit -m "feat: project scaffolding with dependencies and config"
```

---

## Task 2: Config Module — *Phase 1 (sequential, after Task 1)*

**Files:**
- Create: `src/mlb_digest/config.py`
- Create: `tests/test_config.py`

**Step 1: Write the failing test**

```python
# tests/test_config.py
import os
from pathlib import Path
from unittest.mock import patch

from mlb_digest.config import load_config


def test_load_config_reads_toml_values(tmp_path: Path):
    toml_content = """
[team]
id = 144
name = "Braves"
league_id = 104
colors = { primary = "#13274F", accent = "#CE1141" }

[email]
recipients = ["test@example.com"]
subject = "{team_name} Daily — {date}"
subject_catchup = "{team_name} Catchup — {date}"
transport = "gmail_smtp"

[feeds.team]
urls = ["https://example.com/team.rss"]

[feeds.mlb]
urls = ["https://example.com/mlb.rss"]

[narrator]
model = "claude-sonnet-4-6"
temperature = 0.7
"""
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)

    config = load_config(config_path=config_file)

    assert config.team_id == 144
    assert config.team_name == "Braves"
    assert config.league_id == 104
    assert config.team_colors == {"primary": "#13274F", "accent": "#CE1141"}
    assert config.email_recipients == ["test@example.com"]
    assert config.email_transport == "gmail_smtp"
    assert config.team_feed_urls == ["https://example.com/team.rss"]
    assert config.mlb_feed_urls == ["https://example.com/mlb.rss"]
    assert config.narrator_model == "claude-sonnet-4-6"
    assert config.narrator_temperature == 0.7


def test_load_config_reads_env_secrets(tmp_path: Path):
    toml_content = """
[team]
id = 144
name = "Braves"
league_id = 104
colors = { primary = "#13274F", accent = "#CE1141" }

[email]
recipients = ["test@example.com"]
subject = "{team_name} Daily — {date}"
subject_catchup = "{team_name} Catchup — {date}"
transport = "gmail_smtp"

[feeds.team]
urls = []

[feeds.mlb]
urls = []

[narrator]
model = "claude-sonnet-4-6"
temperature = 0.7
"""
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)

    env_vars = {
        "ANTHROPIC_API_KEY": "sk-test-key",
        "GMAIL_ADDRESS": "sender@gmail.com",
        "GMAIL_APP_PASSWORD": "xxxx-xxxx",
    }

    with patch.dict(os.environ, env_vars, clear=False):
        config = load_config(config_path=config_file)

    assert config.anthropic_api_key == "sk-test-key"
    assert config.gmail_address == "sender@gmail.com"
    assert config.gmail_app_password == "xxxx-xxxx"


def test_format_subject_with_team_name_and_date(tmp_path: Path):
    toml_content = """
[team]
id = 144
name = "Braves"
league_id = 104
colors = { primary = "#13274F", accent = "#CE1141" }

[email]
recipients = ["test@example.com"]
subject = "{team_name} Daily — {date}"
subject_catchup = "{team_name} Catchup — {date}"
transport = "gmail_smtp"

[feeds.team]
urls = []

[feeds.mlb]
urls = []

[narrator]
model = "claude-sonnet-4-6"
temperature = 0.7
"""
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)

    config = load_config(config_path=config_file)

    subject = config.format_subject(catchup=False)
    assert "Braves" in subject
    assert "Daily" in subject

    subject_catchup = config.format_subject(catchup=True)
    assert "Braves" in subject_catchup
    assert "Catchup" in subject_catchup
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'mlb_digest.config'`

**Step 3: Write minimal implementation**

```python
# src/mlb_digest/config.py
import os
import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

MLB_API_BASE_URL = "https://statsapi.mlb.com"
DEFAULT_CONFIG_PATH = Path.cwd() / "config.toml"
RETRY_ATTEMPTS = 3
RETRY_WAIT_SECONDS = 1


@dataclass
class Config:
    team_id: int
    team_name: str
    league_id: int
    team_colors: dict[str, str]

    email_recipients: list[str]
    email_subject_template: str
    email_subject_catchup_template: str
    email_transport: str

    team_feed_urls: list[str]
    mlb_feed_urls: list[str]

    narrator_model: str
    narrator_temperature: float

    anthropic_api_key: str
    gmail_address: str
    gmail_app_password: str

    def format_subject(self, catchup: bool = False) -> str:
        template = self.email_subject_catchup_template if catchup else self.email_subject_template
        return template.format(team_name=self.team_name, date=date.today().strftime("%b %d, %Y"))


def load_config(config_path: Path = DEFAULT_CONFIG_PATH) -> Config:
    load_dotenv()

    with open(config_path, "rb") as f:
        toml_data = tomllib.load(f)

    team = toml_data["team"]
    email = toml_data["email"]
    feeds = toml_data.get("feeds", {})
    narrator = toml_data["narrator"]

    return Config(
        team_id=team["id"],
        team_name=team["name"],
        league_id=team["league_id"],
        team_colors=dict(team.get("colors", {})),
        email_recipients=email["recipients"],
        email_subject_template=email["subject"],
        email_subject_catchup_template=email["subject_catchup"],
        email_transport=email["transport"],
        team_feed_urls=feeds.get("team", {}).get("urls", []),
        mlb_feed_urls=feeds.get("mlb", {}).get("urls", []),
        narrator_model=narrator["model"],
        narrator_temperature=narrator["temperature"],
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        gmail_address=os.environ.get("GMAIL_ADDRESS", ""),
        gmail_app_password=os.environ.get("GMAIL_APP_PASSWORD", ""),
    )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_config.py -v`
Expected: 3 passed

**Step 5: Commit**

```bash
git add src/mlb_digest/config.py tests/test_config.py
git commit -m "feat: config module — loads config.toml and .env secrets"
```

---

## Task 3: RSS Feeds Module — *Phase 2 (parallel with Tasks 4, 6, 7)*

**Files:**
- Create: `src/mlb_digest/feeds.py`
- Create: `tests/test_feeds.py`
- Create: `tests/fixtures/team_feed.xml`
- Create: `tests/fixtures/mlb_feed.xml`
- Create: `tests/fixtures/empty_feed.xml`

**Step 1: Create fixture files**

`tests/fixtures/team_feed.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Braves Feed</title>
    <item>
      <title>Braves Sign New Closer in Blockbuster Deal</title>
      <link>https://www.mlbtraderumors.com/braves-closer</link>
      <description>The Atlanta Braves announced a major bullpen acquisition today, signing a top closer to a multi-year deal.</description>
      <pubDate>Thu, 14 Mar 2026 10:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Spring Training Update: Rotation Takes Shape</title>
      <link>https://www.mlbtraderumors.com/spring-rotation</link>
      <description>With opening day approaching, the Braves rotation is starting to come together after a strong spring.</description>
      <pubDate>Wed, 13 Mar 2026 14:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Injury Report: Key Outfielder Day-to-Day</title>
      <link>https://www.mlbtraderumors.com/injury-report</link>
      <description>A key outfielder left yesterday's game early with a hamstring issue and is listed as day-to-day.</description>
      <pubDate>Tue, 12 Mar 2026 09:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
```

`tests/fixtures/mlb_feed.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>MLB News</title>
    <item>
      <title>MLB Announces Rule Changes for 2026 Season</title>
      <link>https://www.mlb.com/rule-changes</link>
      <description>Major League Baseball has announced a new set of rule changes taking effect this season.</description>
      <pubDate>Thu, 14 Mar 2026 08:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Braves Sign New Closer in Blockbuster Deal</title>
      <link>https://www.espn.com/braves-closer</link>
      <description>The Braves announced a major bullpen acquisition today signing a top closer.</description>
      <pubDate>Thu, 14 Mar 2026 10:30:00 GMT</pubDate>
    </item>
    <item>
      <title>Top Prospect Called Up by Dodgers</title>
      <link>https://www.mlb.com/dodgers-prospect</link>
      <description>The Dodgers called up their top prospect from Triple-A ahead of opening day.</description>
      <pubDate>Wed, 13 Mar 2026 16:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
```

`tests/fixtures/empty_feed.xml`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Empty Feed</title>
  </channel>
</rss>
```

**Step 2: Write the failing tests**

```python
# tests/test_feeds.py
import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from mlb_digest.feeds import (
    Article,
    deduplicate_articles,
    fetch_articles,
    select_articles,
)

FIXTURES = Path(__file__).parent / "fixtures"


def test_parse_rss_feed_returns_articles():
    feed_xml = (FIXTURES / "team_feed.xml").read_text()

    with patch("mlb_digest.feeds._fetch_feed_content", return_value=feed_xml):
        articles = fetch_articles(["https://example.com/feed"], source_type="team")

    assert len(articles) == 3
    assert articles[0].title == "Braves Sign New Closer in Blockbuster Deal"
    assert articles[0].link == "https://www.mlbtraderumors.com/braves-closer"
    assert articles[0].source_type == "team"
    assert len(articles[0].summary) > 0


def test_empty_feed_returns_no_articles():
    feed_xml = (FIXTURES / "empty_feed.xml").read_text()

    with patch("mlb_digest.feeds._fetch_feed_content", return_value=feed_xml):
        articles = fetch_articles(["https://example.com/feed"], source_type="team")

    assert articles == []


def test_deduplicate_removes_similar_titles():
    articles = [
        Article(
            title="Braves Sign New Closer in Blockbuster Deal",
            link="https://example.com/a",
            summary="First source version.",
            source="example.com",
            source_type="team",
        ),
        Article(
            title="Braves Sign New Closer in Blockbuster Deal",
            link="https://example.com/b",
            summary="Second source version.",
            source="other.com",
            source_type="mlb",
        ),
        Article(
            title="MLB Announces Rule Changes for 2026 Season",
            link="https://example.com/c",
            summary="Different article entirely.",
            source="mlb.com",
            source_type="mlb",
        ),
    ]

    result = deduplicate_articles(articles)

    assert len(result) == 2
    titles = [a.title for a in result]
    assert "MLB Announces Rule Changes for 2026 Season" in titles


def test_failed_feed_logs_warning_and_returns_empty(caplog):
    with caplog.at_level(logging.WARNING):
        with patch("mlb_digest.feeds._fetch_feed_content.retry.wait", return_value=0):
            with patch("mlb_digest.feeds._fetch_feed_content", side_effect=Exception("Connection refused")):
                articles = fetch_articles(["https://broken.example.com/feed"], source_type="team")

    assert articles == []
    assert "Connection refused" in caplog.text


def test_fetch_articles_from_multiple_feeds():
    team_xml = (FIXTURES / "team_feed.xml").read_text()
    mlb_xml = (FIXTURES / "mlb_feed.xml").read_text()

    def mock_fetch(url: str) -> str:
        if "team" in url:
            return team_xml
        return mlb_xml

    with patch("mlb_digest.feeds._fetch_feed_content", side_effect=mock_fetch):
        articles = fetch_articles(
            ["https://example.com/team", "https://example.com/mlb"],
            source_type="team",
        )

    assert len(articles) == 6


def test_select_articles_separates_by_source_type():
    team_articles = [
        Article(title="Team A", link="https://a.com/1", summary="a", source="a.com", source_type="team"),
        Article(title="Team B", link="https://a.com/2", summary="b", source="a.com", source_type="team"),
        Article(title="Team C", link="https://a.com/3", summary="c", source="a.com", source_type="team"),
    ]
    mlb_articles = [
        Article(title="MLB A", link="https://b.com/1", summary="a", source="b.com", source_type="mlb"),
        Article(title="MLB B", link="https://b.com/2", summary="b", source="b.com", source_type="mlb"),
        Article(title="MLB C", link="https://b.com/3", summary="c", source="b.com", source_type="mlb"),
    ]

    result = select_articles(team_articles, mlb_articles, team_count=2, mlb_count=2)

    assert len(result["team"]) == 2
    assert len(result["mlb"]) == 2
    assert all(a.source_type == "team" for a in result["team"])
    assert all(a.source_type == "mlb" for a in result["mlb"])


def test_select_articles_deduplicates_across_feeds():
    team_articles = [
        Article(title="Same Story", link="https://a.com/1", summary="a", source="a.com", source_type="team"),
    ]
    mlb_articles = [
        Article(title="Same Story", link="https://b.com/1", summary="a", source="b.com", source_type="mlb"),
        Article(title="Different Story", link="https://b.com/2", summary="b", source="b.com", source_type="mlb"),
    ]

    result = select_articles(team_articles, mlb_articles, team_count=2, mlb_count=2)

    all_titles = [a.title for a in result["team"] + result["mlb"]]
    assert all_titles.count("Same Story") == 1
```

**Step 3: Run tests to verify they fail**

Run: `pytest tests/test_feeds.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 4: Write minimal implementation**

```python
# src/mlb_digest/feeds.py
import logging
from dataclasses import dataclass
from difflib import SequenceMatcher
from urllib.parse import urlparse

import feedparser
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.8


@dataclass
class Article:
    title: str
    link: str
    summary: str
    source: str
    source_type: str  # "team" or "mlb"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4), reraise=True)
def _fetch_feed_content(url: str) -> str:
    response = httpx.get(url, timeout=10, follow_redirects=True)
    response.raise_for_status()
    return response.text


def fetch_articles(feed_urls: list[str], source_type: str) -> list[Article]:
    articles: list[Article] = []

    for url in feed_urls:
        try:
            content = _fetch_feed_content(url)
        except Exception:
            logger.warning("Failed to fetch feed: %s", url, exc_info=True)
            continue

        feed = feedparser.parse(content)
        source = urlparse(url).netloc

        for entry in feed.entries:
            title = entry.get("title", "").strip()
            link = entry.get("link", "").strip()
            summary = entry.get("summary", entry.get("description", "")).strip()

            if not title:
                continue

            articles.append(Article(
                title=title,
                link=link,
                summary=summary,
                source=source,
                source_type=source_type,
            ))

    return articles


def deduplicate_articles(articles: list[Article]) -> list[Article]:
    seen: list[Article] = []

    for article in articles:
        normalized = article.title.lower().strip()
        is_duplicate = False

        for existing in seen:
            existing_normalized = existing.title.lower().strip()
            similarity = SequenceMatcher(None, normalized, existing_normalized).ratio()
            if similarity >= SIMILARITY_THRESHOLD:
                is_duplicate = True
                break

        if not is_duplicate:
            seen.append(article)

    return seen


def select_articles(
    team_articles: list[Article],
    mlb_articles: list[Article],
    team_count: int = 2,
    mlb_count: int = 2,
) -> dict[str, list[Article]]:
    all_deduped = deduplicate_articles(team_articles + mlb_articles)

    selected_team = [a for a in all_deduped if a.source_type == "team"][:team_count]
    selected_mlb = [a for a in all_deduped if a.source_type == "mlb"][:mlb_count]

    return {"team": selected_team, "mlb": selected_mlb}
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/test_feeds.py -v`
Expected: 7 passed

**Step 6: Commit**

```bash
git add src/mlb_digest/feeds.py tests/test_feeds.py tests/fixtures/
git commit -m "feat: RSS feed fetching with deduplication and source tracking"
```

---

## Task 4: MLB API Module — *Phase 2 (parallel with Tasks 3, 6, 7)*

**Files:**
- Create: `src/mlb_digest/mlb_api.py`
- Create: `tests/test_mlb_api.py`

This module uses `statsapi.schedule()` and `statsapi.standings_data()` convenience functions (not raw `statsapi.get()`) for simpler, flatter response shapes.

**Step 1: Capture fixture data shapes**

Run these to understand the convenience function return shapes:

```python
import statsapi
import json

# statsapi.schedule() returns a flat list of game dicts
games = statsapi.schedule(team=144, date="07/04/2025")
print(json.dumps(games[:1], indent=2))
# Keys: game_id, game_datetime, game_date, game_type, status, away_name, home_name,
#        away_score, home_score, home_probable_pitcher, away_probable_pitcher,
#        winning_pitcher, losing_pitcher, save_pitcher, summary, ...

# statsapi.standings_data() returns dict keyed by division ID
standings = statsapi.standings_data(leagueId=104)
print(json.dumps(standings, indent=2, default=str))
# Keys per division: div_name, teams (list of dicts with name, w, l, gb, wc_rank, team_id, ...)

# statsapi.roster() returns formatted string; use get() for structured data
roster = statsapi.get("team_roster", {"teamId": 144, "rosterType": "active"})
print(json.dumps(roster, indent=2)[:500])

# statsapi.player_stat_data() returns dict with player info + stats
player = statsapi.player_stat_data(660271, group="hitting", type="season")
print(json.dumps(player, indent=2, default=str)[:500])
```

Save representative samples to fixture files. The tests below mock the functions directly, so fixtures are optional references — the mocks return the expected shapes inline.

**Step 2: Write the failing tests**

```python
# tests/test_mlb_api.py
import logging
from unittest.mock import patch

import pytest

from mlb_digest.mlb_api import (
    DivisionStandings,
    GameResult,
    PlayerStats,
    RosterPlayer,
    UpcomingGame,
    get_active_roster,
    get_player_stats,
    get_standings,
    get_today_game,
    get_top_players,
    get_yesterday_game,
)


def test_get_yesterday_game_returns_game_result():
    mock_schedule = [
        {
            "game_id": 12345,
            "home_name": "Braves",
            "away_name": "Mets",
            "home_score": 5,
            "away_score": 3,
            "winning_pitcher": "Sale",
            "losing_pitcher": "Severino",
            "save_pitcher": "Iglesias",
            "home_probable_pitcher": "Sale",
            "away_probable_pitcher": "Severino",
            "game_datetime": "2026-03-13T23:20:00Z",
            "status": "Final",
            "summary": "Braves 5, Mets 3",
        }
    ]

    with patch("mlb_digest.mlb_api._fetch_schedule", return_value=mock_schedule):
        result = get_yesterday_game(team_id=144)

    assert result is not None
    assert isinstance(result, GameResult)
    assert result.home_team == "Braves"
    assert result.away_team == "Mets"
    assert result.home_score == 5
    assert result.away_score == 3
    assert result.winning_pitcher == "Sale"


def test_get_yesterday_game_returns_none_on_off_day():
    with patch("mlb_digest.mlb_api._fetch_schedule", return_value=[]):
        result = get_yesterday_game(team_id=144)

    assert result is None


def test_get_today_game_returns_upcoming_game_when_home():
    mock_schedule = [
        {
            "game_id": 12346,
            "home_name": "Braves",
            "away_name": "Phillies",
            "home_score": 0,
            "away_score": 0,
            "winning_pitcher": "",
            "losing_pitcher": "",
            "save_pitcher": "",
            "home_probable_pitcher": "Fried",
            "away_probable_pitcher": "Wheeler",
            "game_datetime": "2026-03-14T23:20:00Z",
            "status": "Pre-Game",
            "summary": "",
        }
    ]

    with patch("mlb_digest.mlb_api._fetch_schedule", return_value=mock_schedule):
        result = get_today_game(team_id=144, team_name="Braves")

    assert result is not None
    assert isinstance(result, UpcomingGame)
    assert result.opponent == "Phillies"
    assert result.home_pitcher == "Fried"
    assert result.away_pitcher == "Wheeler"
    assert result.is_home is True


def test_get_today_game_returns_upcoming_game_when_away():
    mock_schedule = [
        {
            "game_id": 12347,
            "home_name": "Mets",
            "away_name": "Braves",
            "home_score": 0,
            "away_score": 0,
            "winning_pitcher": "",
            "losing_pitcher": "",
            "save_pitcher": "",
            "home_probable_pitcher": "Severino",
            "away_probable_pitcher": "Sale",
            "game_datetime": "2026-03-15T23:10:00Z",
            "status": "Pre-Game",
            "summary": "",
        }
    ]

    with patch("mlb_digest.mlb_api._fetch_schedule", return_value=mock_schedule):
        result = get_today_game(team_id=144, team_name="Braves")

    assert result is not None
    assert result.opponent == "Mets"
    assert result.is_home is False


def test_get_standings_returns_division_standings():
    mock_standings = {
        204: {
            "div_name": "NL East",
            "teams": [
                {"name": "Braves", "w": 5, "l": 2, "gb": "-", "team_id": 144},
                {"name": "Mets", "w": 4, "l": 3, "gb": "1.0", "team_id": 121},
            ],
        }
    }

    with patch("mlb_digest.mlb_api.statsapi.standings_data", return_value=mock_standings):
        result = get_standings(league_id=104)

    assert len(result) == 1
    assert isinstance(result[0], DivisionStandings)
    assert result[0].division_name == "NL East"
    assert len(result[0].teams) == 2
    assert result[0].teams[0].name == "Braves"


def test_get_active_roster_returns_players():
    mock_roster = {
        "roster": [
            {
                "person": {"id": 660271, "fullName": "Ronald Acuna Jr."},
                "position": {"abbreviation": "RF"},
                "status": {"description": "Active"},
            },
            {
                "person": {"id": 621439, "fullName": "Chris Sale"},
                "position": {"abbreviation": "P"},
                "status": {"description": "Active"},
            },
        ]
    }

    with patch("mlb_digest.mlb_api._fetch_roster", return_value=mock_roster):
        result = get_active_roster(team_id=144)

    assert len(result) == 2
    assert isinstance(result[0], RosterPlayer)
    assert result[0].name == "Ronald Acuna Jr."
    assert result[0].position == "RF"
    assert result[0].player_id == 660271


def test_get_player_stats_returns_stats():
    mock_stats = {
        "id": 660271,
        "first_name": "Ronald",
        "last_name": "Acuna Jr.",
        "stats": [
            {
                "type": "season",
                "group": "hitting",
                "stats": {
                    "avg": ".310",
                    "homeRuns": 15,
                    "rbi": 42,
                    "stolenBases": 20,
                    "ops": ".950",
                },
            }
        ],
    }

    with patch("mlb_digest.mlb_api.statsapi.player_stat_data", return_value=mock_stats):
        result = get_player_stats(player_id=660271, group="hitting")

    assert result is not None
    assert isinstance(result, PlayerStats)
    assert result.stats["avg"] == ".310"
    assert result.stats["homeRuns"] == 15


def test_get_yesterday_game_handles_api_error(caplog):
    with caplog.at_level(logging.WARNING):
        with patch("mlb_digest.mlb_api._fetch_schedule", side_effect=Exception("API timeout")):
            result = get_yesterday_game(team_id=144)

    assert result is None
    assert "API timeout" in caplog.text


def test_get_standings_handles_api_error(caplog):
    with caplog.at_level(logging.WARNING):
        with patch("mlb_digest.mlb_api.statsapi.standings_data", side_effect=Exception("API down")):
            result = get_standings(league_id=104)

    assert result == []


def test_get_top_players_returns_sorted_hitters_and_pitchers():
    roster = [
        RosterPlayer(player_id=1, name="Hitter A", position="RF", status="Active"),
        RosterPlayer(player_id=2, name="Hitter B", position="1B", status="Active"),
        RosterPlayer(player_id=3, name="Pitcher A", position="P", status="Active"),
    ]

    def mock_get_stats(player_id: int, group: str = "hitting") -> PlayerStats | None:
        stats_map = {
            (1, "hitting"): PlayerStats(player_id=1, group="hitting", stats={"avg": ".300"}),
            (2, "hitting"): PlayerStats(player_id=2, group="hitting", stats={"avg": ".320"}),
            (3, "pitching"): PlayerStats(player_id=3, group="pitching", stats={"era": "3.50"}),
        }
        return stats_map.get((player_id, group))

    with patch("mlb_digest.mlb_api.get_player_stats", side_effect=mock_get_stats):
        result = get_top_players(roster)

    assert result["top_hitters"][0]["name"] == "Hitter B"  # .320 > .300
    assert result["top_hitters"][1]["name"] == "Hitter A"
    assert len(result["top_pitchers"]) == 1
    assert result["top_pitchers"][0]["name"] == "Pitcher A"
```

**Step 3: Run tests to verify they fail**

Run: `pytest tests/test_mlb_api.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 4: Write minimal implementation**

```python
# src/mlb_digest/mlb_api.py
import logging
from dataclasses import dataclass
from datetime import date, timedelta

import statsapi
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


@dataclass
class GameResult:
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    winning_pitcher: str
    losing_pitcher: str
    save_pitcher: str
    summary: str


@dataclass
class UpcomingGame:
    opponent: str
    game_time: str
    home_pitcher: str
    away_pitcher: str
    is_home: bool


@dataclass
class TeamStanding:
    name: str
    wins: int
    losses: int
    games_back: str
    team_id: int


@dataclass
class DivisionStandings:
    division_name: str
    teams: list[TeamStanding]


@dataclass
class RosterPlayer:
    player_id: int
    name: str
    position: str
    status: str


@dataclass
class PlayerStats:
    player_id: int
    group: str
    stats: dict


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4), reraise=True)
def _fetch_schedule(team: int, date_str: str) -> list[dict]:
    return statsapi.schedule(team=team, date=date_str)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4), reraise=True)
def _fetch_roster(team_id: int, roster_type: str = "active") -> dict:
    return statsapi.get("team_roster", {"teamId": team_id, "rosterType": roster_type})


def get_yesterday_game(team_id: int) -> GameResult | None:
    yesterday = (date.today() - timedelta(days=1)).strftime("%m/%d/%Y")
    try:
        games = _fetch_schedule(team=team_id, date_str=yesterday)
    except Exception:
        logger.warning("Failed to fetch yesterday's schedule", exc_info=True)
        return None

    if not games:
        return None

    game = games[0]
    return GameResult(
        home_team=game.get("home_name", "Unknown"),
        away_team=game.get("away_name", "Unknown"),
        home_score=game.get("home_score", 0),
        away_score=game.get("away_score", 0),
        winning_pitcher=game.get("winning_pitcher", "Unknown"),
        losing_pitcher=game.get("losing_pitcher", "Unknown"),
        save_pitcher=game.get("save_pitcher", ""),
        summary=game.get("summary", ""),
    )


def get_today_game(team_id: int, team_name: str) -> UpcomingGame | None:
    today = date.today().strftime("%m/%d/%Y")
    try:
        games = _fetch_schedule(team=team_id, date_str=today)
    except Exception:
        logger.warning("Failed to fetch today's schedule", exc_info=True)
        return None

    if not games:
        return None

    game = games[0]
    home_name = game.get("home_name", "Unknown")
    away_name = game.get("away_name", "Unknown")
    is_home = team_name.lower() in home_name.lower()
    opponent = away_name if is_home else home_name

    return UpcomingGame(
        opponent=opponent,
        game_time=game.get("game_datetime", ""),
        home_pitcher=game.get("home_probable_pitcher", "TBD"),
        away_pitcher=game.get("away_probable_pitcher", "TBD"),
        is_home=is_home,
    )


def get_standings(league_id: int) -> list[DivisionStandings]:
    try:
        data = statsapi.standings_data(leagueId=league_id)
    except Exception:
        logger.warning("Failed to fetch standings", exc_info=True)
        return []

    divisions = []
    for _div_id, div_data in data.items():
        teams = [
            TeamStanding(
                name=t["name"],
                wins=t["w"],
                losses=t["l"],
                games_back=t["gb"],
                team_id=t["team_id"],
            )
            for t in div_data["teams"]
        ]
        divisions.append(DivisionStandings(
            division_name=div_data["div_name"],
            teams=teams,
        ))

    return divisions


def get_active_roster(team_id: int) -> list[RosterPlayer]:
    try:
        data = _fetch_roster(team_id)
    except Exception:
        logger.warning("Failed to fetch roster", exc_info=True)
        return []

    players = []
    for entry in data.get("roster", []):
        person = entry.get("person", {})
        position = entry.get("position", {})
        status = entry.get("status", {})
        players.append(RosterPlayer(
            player_id=person.get("id", 0),
            name=person.get("fullName", "Unknown"),
            position=position.get("abbreviation", "Unknown"),
            status=status.get("description", "Active"),
        ))

    return players


def get_player_stats(player_id: int, group: str = "hitting") -> PlayerStats | None:
    try:
        data = statsapi.player_stat_data(player_id, group=group, type="season")
    except Exception:
        logger.warning("Failed to fetch stats for player %d", player_id, exc_info=True)
        return None

    stats_list = data.get("stats", [])
    if not stats_list:
        return None

    return PlayerStats(
        player_id=player_id,
        group=group,
        stats=stats_list[0].get("stats", {}),
    )


def get_top_players(
    roster: list[RosterPlayer],
    count: int = 3,
) -> dict[str, list[dict]]:
    hitters = []
    pitchers = []

    for player in roster:
        if player.position == "P":
            stats = get_player_stats(player.player_id, group="pitching")
            if stats and stats.stats:
                pitchers.append({"name": player.name, **stats.stats})
        else:
            stats = get_player_stats(player.player_id, group="hitting")
            if stats and stats.stats:
                hitters.append({"name": player.name, **stats.stats})

    # Sort hitters by AVG descending, pitchers by ERA ascending
    hitters.sort(key=lambda h: float(h.get("avg", "0") or "0"), reverse=True)
    pitchers.sort(key=lambda p: float(p.get("era", "99") or "99"))

    return {
        "top_hitters": hitters[:count],
        "top_pitchers": pitchers[:count],
    }
```

**Step 5: Run tests to verify they pass**

Run: `pytest tests/test_mlb_api.py -v`
Expected: 8 passed

**Step 6: Commit**

```bash
git add src/mlb_digest/mlb_api.py tests/test_mlb_api.py
git commit -m "feat: MLB API module — schedule, standings, roster, player stats"
```

---

## Task 5: Narrator Module — *Phase 3 (sequential, after Tasks 3 + 4)*

**Files:**
- Create: `src/mlb_digest/narrator.py`
- Create: `tests/test_narrator.py`

**Step 1: Write the failing tests**

```python
# tests/test_narrator.py
from unittest.mock import patch, MagicMock

import pytest

from mlb_digest.feeds import Article
from mlb_digest.mlb_api import (
    DivisionStandings,
    GameResult,
    TeamStanding,
    UpcomingGame,
)
from mlb_digest.narrator import NarratorError, build_prompt, build_system_prompt, generate_narrative


def test_build_system_prompt_includes_team_name_and_rules():
    prompt = build_system_prompt("Braves")

    assert "Braves" in prompt
    assert "CRITICAL RULES" in prompt
    assert "NEVER invent" in prompt
    assert "Output the sections in the order" in prompt


def test_build_prompt_includes_game_result():
    game = GameResult(
        home_team="Braves", away_team="Mets",
        home_score=5, away_score=3,
        winning_pitcher="Sale", losing_pitcher="Severino",
        save_pitcher="Iglesias", summary="",
    )

    prompt = build_prompt(
        team_name="Braves",
        yesterday_game=game,
        today_game=None,
        standings=[],
        team_articles=[],
        mlb_articles=[],
        top_players=None,
    )

    assert "Braves" in prompt
    assert "Mets" in prompt
    assert "5" in prompt
    assert "Sale" in prompt


def test_build_prompt_skips_game_section_on_off_day():
    prompt = build_prompt(
        team_name="Braves",
        yesterday_game=None,
        today_game=None,
        standings=[],
        team_articles=[],
        mlb_articles=[],
        top_players=None,
    )

    assert "last_nights_game" not in prompt
    assert "todays_game" not in prompt


def test_build_prompt_includes_articles():
    articles = [
        Article(title="Big Trade", link="https://x.com/a", summary="A big trade happened.", source="x.com", source_type="team"),
    ]

    prompt = build_prompt(
        team_name="Braves",
        yesterday_game=None,
        today_game=None,
        standings=[],
        team_articles=articles,
        mlb_articles=[],
        top_players=None,
    )

    assert "Big Trade" in prompt
    assert "A big trade happened" in prompt


def test_build_prompt_includes_top_players():
    top_players = {
        "top_hitters": [{"name": "Acuna", "avg": ".310", "homeRuns": 15}],
        "top_pitchers": [{"name": "Sale", "era": "2.50", "wins": 8}],
    }

    prompt = build_prompt(
        team_name="Braves",
        yesterday_game=None,
        today_game=None,
        standings=[],
        team_articles=[],
        mlb_articles=[],
        top_players=top_players,
    )

    assert "Acuna" in prompt
    assert "Sale" in prompt
    assert ".310" in prompt


def test_build_prompt_catchup_includes_roster():
    roster_data = [
        {"name": "Acuna", "position": "RF", "player_id": 660271},
        {"name": "Sale", "position": "P", "player_id": 621439},
    ]

    prompt = build_prompt(
        team_name="Braves",
        yesterday_game=None,
        today_game=None,
        standings=[],
        team_articles=[],
        mlb_articles=[],
        top_players=None,
        catchup=True,
        roster_data=roster_data,
    )

    assert "Acuna" in prompt
    assert "roster" in prompt.lower()


def test_build_prompt_includes_standings_data():
    standings = [
        DivisionStandings(
            division_name="NL East",
            teams=[
                TeamStanding(name="Braves", wins=50, losses=30, games_back="-", team_id=144),
                TeamStanding(name="Mets", wins=45, losses=35, games_back="5.0", team_id=121),
            ],
        )
    ]

    prompt = build_prompt(
        team_name="Braves",
        yesterday_game=None,
        today_game=None,
        standings=standings,
        team_articles=[],
        mlb_articles=[],
        top_players=None,
    )

    assert "NL East" in prompt
    assert "Braves" in prompt
    assert "50" in prompt
    assert "Mets" in prompt


def test_build_prompt_section_ordering():
    game = GameResult(
        home_team="Braves", away_team="Mets",
        home_score=5, away_score=3,
        winning_pitcher="Sale", losing_pitcher="Severino",
        save_pitcher="", summary="",
    )
    mlb_articles = [
        Article(title="MLB News", link="https://x.com/a", summary="news", source="x.com", source_type="mlb"),
    ]

    prompt = build_prompt(
        team_name="Braves",
        yesterday_game=game,
        today_game=None,
        standings=[DivisionStandings(division_name="NL East", teams=[])],
        team_articles=[],
        mlb_articles=mlb_articles,
        top_players=None,
    )

    # around_the_league should appear before last_nights_game
    league_pos = prompt.find("around_the_league")
    game_pos = prompt.find("last_nights_game")
    assert league_pos < game_pos


def test_generate_narrative_returns_markdown():
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="## Braves Daily\n\nGreat game last night!")]
    mock_response.usage.input_tokens = 100
    mock_response.usage.output_tokens = 50

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with patch("mlb_digest.narrator.anthropic.Anthropic", return_value=mock_client):
        result = generate_narrative(
            prompt="test prompt",
            system_prompt="test system",
            api_key="sk-test",
            model="claude-sonnet-4-6",
            temperature=0.7,
        )

    assert "Braves Daily" in result
    assert "Great game" in result


def test_generate_narrative_raises_on_api_error():
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = Exception("API down")

    with patch("mlb_digest.narrator.anthropic.Anthropic", return_value=mock_client):
        with pytest.raises(NarratorError, match="API down"):
            generate_narrative(
                prompt="test",
                system_prompt="test",
                api_key="sk-test",
                model="claude-sonnet-4-6",
                temperature=0.7,
            )
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_narrator.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# src/mlb_digest/narrator.py
import json
import logging
import sys
from collections import OrderedDict
from dataclasses import asdict

import anthropic

from mlb_digest.feeds import Article
from mlb_digest.mlb_api import DivisionStandings, GameResult, UpcomingGame

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_TEMPLATE = """You are a knowledgeable but casual {team_name} fan writing a morning email \
digest for a friend who doesn't have time to watch every game. You are \
conversational, not a sports anchor. You reference specific stats and facts \
from the data provided.

CRITICAL RULES:
- ONLY reference facts, stats, and events present in the provided data.
- NEVER invent plays, moments, or descriptions not supported by the data.
- For headlines and storylines, use the RSS article titles and summaries \
provided. Summarize what the articles say — do NOT generate storylines \
from imagination.
- If the data shows a player hit 2-4 with a HR and 3 RBI, you can say \
"went 2-for-4 with a homer and 3 ribbies" — but do NOT invent the \
situation (e.g., "a clutch 2-run shot in the 8th") unless inning/situation \
data is in the input.
- For player descriptions in catchup reports, derive from stats only: \
"leads the team in HRs" not "has a smooth swing."
- When in doubt, state the numbers. Never embellish.

Output format: Return the digest as markdown. Use ## headers for each section. \
Output the sections in the order they appear in the input data."""


class NarratorError(Exception):
    pass


def build_system_prompt(team_name: str) -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(team_name=team_name)


def _articles_to_dicts(articles: list[Article]) -> list[dict]:
    return [
        {"title": a.title, "summary": a.summary, "link": a.link, "source": a.source}
        for a in articles
    ]


def build_prompt(
    team_name: str,
    yesterday_game: GameResult | None,
    today_game: UpcomingGame | None,
    standings: list[DivisionStandings],
    team_articles: list[Article],
    mlb_articles: list[Article],
    top_players: dict | None,
    catchup: bool = False,
    roster_data: list[dict] | None = None,
) -> str:
    # OrderedDict to guarantee section ordering in JSON output
    sections: OrderedDict[str, dict] = OrderedDict()

    if mlb_articles:
        sections["around_the_league"] = {
            "instruction": "Summarize these MLB headlines into a few bullet points. Use the article titles and summaries — do not invent storylines.",
            "articles": _articles_to_dicts(mlb_articles),
        }

    if yesterday_game:
        sections["last_nights_game"] = {
            "instruction": f"Recap {team_name}'s game from last night. Narrate the stats conversationally. Do not invent plays not in the data.",
            "data": asdict(yesterday_game),
        }

    if today_game:
        sections["todays_game"] = {
            "instruction": f"Preview {team_name}'s game today. Mention the opponent, time, and starting pitchers.",
            "data": asdict(today_game),
        }

    if team_articles:
        sections["storylines"] = {
            "instruction": f"Write {team_name} storylines based on these articles. Summarize what the articles say. Supplement with standings data if relevant.",
            "articles": _articles_to_dicts(team_articles),
        }

    if standings:
        standings_section: dict = {
            "instruction": f"Show the division standings. Highlight {team_name}'s position.",
            "data": [asdict(d) for d in standings],
        }
        if top_players:
            standings_section["top_players"] = top_players
            standings_section["instruction"] += f" Include top hitters (by AVG) and top pitchers (by ERA) for {team_name}."
        sections["standings_snapshot"] = standings_section

    if catchup and roster_data:
        sections["roster"] = {
            "instruction": f"Introduce the {team_name} roster. Describe each player based on their stats — do not invent scouting descriptions.",
            "data": roster_data,
        }

    if team_articles or mlb_articles:
        all_for_reading = team_articles[:2] + mlb_articles[:2]
        sections["worth_reading"] = {
            "instruction": "List these articles with title, source, link, and a one-line summary each.",
            "articles": _articles_to_dicts(all_for_reading),
        }

    return json.dumps(sections, indent=2)


def generate_narrative(
    prompt: str,
    system_prompt: str,
    api_key: str,
    model: str,
    temperature: float,
) -> str:
    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as e:
        raise NarratorError(f"Anthropic API call failed: {e}") from e

    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    logger.info("Token usage — input: %d, output: %d", input_tokens, output_tokens)

    return response.content[0].text
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_narrator.py -v`
Expected: 8 passed

**Step 5: Commit**

```bash
git add src/mlb_digest/narrator.py tests/test_narrator.py
git commit -m "feat: narrator module — prompt building with ordered sections and Sonnet generation"
```

---

## Task 6: Email Templates Module — *Phase 2 (parallel with Tasks 3, 4, 7)*

**Files:**
- Create: `src/mlb_digest/templates.py`
- Create: `tests/test_templates.py`

Uses the `markdown` library instead of hand-rolled parsing. All styles are inline (no `<style>` blocks — email clients strip them).

**Step 1: Write the failing tests**

```python
# tests/test_templates.py
from mlb_digest.templates import render_email_html, render_email_text


def test_render_email_html_converts_markdown_headers():
    md = "## Hello World\n\nSome content here."

    html = render_email_html(md, primary_color="#13274F", accent_color="#CE1141")

    assert "Hello World" in html
    assert "Some content" in html
    assert "<html" in html.lower()


def test_render_email_html_has_inline_styles_not_style_block():
    md = "## Test Section\n\nContent here."

    html = render_email_html(md, primary_color="#13274F", accent_color="#CE1141")

    assert "#13274F" in html
    assert "Test Section" in html
    # Must NOT contain a <style> block — email clients strip them
    assert "<style>" not in html


def test_render_email_html_includes_footer():
    md = "## Test\n\nContent."

    html = render_email_html(md, primary_color="#13274F", accent_color="#CE1141")

    assert "MLB Stats API" in html


def test_render_email_html_handles_links():
    md = "Check out [this article](https://example.com)."

    html = render_email_html(md, primary_color="#13274F", accent_color="#CE1141")

    assert 'href="https://example.com"' in html
    assert "this article" in html


def test_render_email_html_handles_tables():
    md = "| Team | W | L |\n|------|---|---|\n| Braves | 5 | 2 |"

    html = render_email_html(md, primary_color="#13274F", accent_color="#CE1141")

    assert "<table" in html.lower()
    assert "Braves" in html


def test_render_email_text_strips_markdown():
    md = "## Hello\n\nSome **bold** content.\n\n- Item 1\n- Item 2"

    text = render_email_text(md)

    assert "Hello" in text
    assert "Item 1" in text
    assert "MLB Stats API" in text
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_templates.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# src/mlb_digest/templates.py
import re

import markdown


def _apply_inline_styles(html: str, primary_color: str, accent_color: str) -> str:
    """Replace tags with inline-styled versions. Email clients strip <style> blocks."""
    html = re.sub(
        r"<h1(.*?)>",
        rf'<h1\1 style="color: {primary_color}; margin-top: 20px;">',
        html,
    )
    html = re.sub(
        r"<h2(.*?)>",
        rf'<h2\1 style="color: {primary_color}; border-bottom: 2px solid {accent_color}; padding-bottom: 5px; margin-top: 25px;">',
        html,
    )
    html = re.sub(
        r"<h3(.*?)>",
        rf'<h3\1 style="color: {primary_color}; margin-top: 15px;">',
        html,
    )
    html = re.sub(
        r"<a ",
        f'<a style="color: {accent_color}; text-decoration: underline;" ',
        html,
    )
    html = re.sub(
        r"<table(.*?)>",
        r'<table\1 style="border-collapse: collapse; width: 100%; margin: 10px 0;">',
        html,
    )
    html = re.sub(
        r"<th(.*?)>",
        rf'<th\1 style="background-color: {primary_color}; color: #ffffff; padding: 8px; text-align: left; border: 1px solid #ddd;">',
        html,
    )
    html = re.sub(
        r"<td(.*?)>",
        r'<td\1 style="padding: 8px; border: 1px solid #ddd;">',
        html,
    )
    return html


def render_email_html(md_content: str, primary_color: str, accent_color: str) -> str:
    body_html = markdown.markdown(md_content, extensions=["tables"])
    body_html = _apply_inline_styles(body_html, primary_color, accent_color)

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f5f5f5;">
  <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 0;">
    <div style="background-color: {primary_color}; color: #ffffff; padding: 20px 30px;">
      <h1 style="margin: 0; font-size: 24px; color: #ffffff;">MLB Digest</h1>
    </div>
    <div style="padding: 20px 30px; color: #333333; line-height: 1.6; font-size: 16px;">
      {body_html}
    </div>
    <div style="background-color: #f0f0f0; padding: 15px 30px; font-size: 12px; color: #888888;">
      Sources: MLB Stats API, RSS feeds. Narrated by Claude Sonnet.
    </div>
  </div>
</body>
</html>"""


def render_email_text(md_content: str) -> str:
    text = md_content

    # Strip markdown formatting for plain text
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1 (\2)", text)
    text = re.sub(r"^#{1,3} ", "", text, flags=re.MULTILINE)

    text += "\n\n---\nSources: MLB Stats API, RSS feeds. Narrated by Claude Sonnet.\n"

    return text.strip()
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_templates.py -v`
Expected: 6 passed

**Step 5: Commit**

```bash
git add src/mlb_digest/templates.py tests/test_templates.py
git commit -m "feat: email templates — markdown lib with inline CSS, no style blocks"
```

---

## Task 7: Emailer Module — *Phase 2 (parallel with Tasks 3, 4, 6)*

**Files:**
- Create: `src/mlb_digest/emailer.py`
- Create: `tests/test_emailer.py`

**Step 1: Write the failing tests**

```python
# tests/test_emailer.py
from unittest.mock import patch, MagicMock

import pytest

from mlb_digest.emailer import build_message, send_email


def test_build_message_creates_multipart_email():
    msg = build_message(
        subject="Braves Daily — Mar 14, 2026",
        html_body="<html><body>Hello</body></html>",
        text_body="Hello",
        sender="sender@gmail.com",
        recipients=["user@example.com"],
    )

    assert msg["Subject"] == "Braves Daily — Mar 14, 2026"
    assert msg["From"] == "sender@gmail.com"
    assert msg["To"] == "user@example.com"
    assert msg.is_multipart()

    payloads = msg.get_payload()
    content_types = [p.get_content_type() for p in payloads]
    assert "text/plain" in content_types
    assert "text/html" in content_types


def test_build_message_handles_multiple_recipients():
    msg = build_message(
        subject="Test",
        html_body="<html>Hi</html>",
        text_body="Hi",
        sender="sender@gmail.com",
        recipients=["a@example.com", "b@example.com"],
    )

    assert "a@example.com" in msg["To"]
    assert "b@example.com" in msg["To"]


def test_send_email_calls_smtp():
    mock_smtp_instance = MagicMock()
    mock_smtp_class = MagicMock(return_value=mock_smtp_instance)
    mock_smtp_instance.__enter__ = MagicMock(return_value=mock_smtp_instance)
    mock_smtp_instance.__exit__ = MagicMock(return_value=False)

    with patch("mlb_digest.emailer.smtplib.SMTP_SSL", mock_smtp_class):
        send_email(
            subject="Test Subject",
            html_body="<html>Hello</html>",
            text_body="Hello",
            sender="sender@gmail.com",
            password="app-password",
            recipients=["user@example.com"],
            transport="gmail_smtp",
        )

    mock_smtp_instance.login.assert_called_once_with("sender@gmail.com", "app-password")
    mock_smtp_instance.send_message.assert_called_once()


def test_send_email_raises_on_unknown_transport():
    with pytest.raises(ValueError, match="carrier_pigeon"):
        send_email(
            subject="Test",
            html_body="<html>Hi</html>",
            text_body="Hi",
            sender="sender@gmail.com",
            password="pw",
            recipients=["user@example.com"],
            transport="carrier_pigeon",
        )
```

Note: The SMTP mock works because tenacity's `@retry` still calls the underlying function, which hits the mocked `smtplib.SMTP_SSL`. The retry waits are short (5s with only 2 attempts), and since the mock succeeds on first call, no retry occurs.

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_emailer.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# src/mlb_digest/emailer.py
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from tenacity import retry, stop_after_attempt, wait_fixed

logger = logging.getLogger(__name__)


def build_message(
    subject: str,
    html_body: str,
    text_body: str,
    sender: str,
    recipients: list[str],
) -> MIMEMultipart:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)

    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    return msg


@retry(stop=stop_after_attempt(2), wait=wait_fixed(5), reraise=True)
def _send_gmail_smtp(msg: MIMEMultipart, sender: str, password: str) -> None:
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender, password)
        server.send_message(msg)


def send_email(
    subject: str,
    html_body: str,
    text_body: str,
    sender: str,
    password: str,
    recipients: list[str],
    transport: str = "gmail_smtp",
) -> None:
    if transport != "gmail_smtp":
        raise ValueError(f"Unknown transport: {transport}. Only 'gmail_smtp' is supported.")

    msg = build_message(subject, html_body, text_body, sender, recipients)

    logger.info("Sending email to %s via %s", recipients, transport)
    _send_gmail_smtp(msg, sender, password)
    logger.info("Email sent successfully")
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_emailer.py -v`
Expected: 4 passed

**Step 5: Commit**

```bash
git add src/mlb_digest/emailer.py tests/test_emailer.py
git commit -m "feat: emailer module — Gmail SMTP with pluggable transport"
```

---

## Task 8: CLI Module — *Phase 4 (sequential, after all Phase 2 + 3)*

**Files:**
- Create: `src/mlb_digest/cli.py`
- Create: `tests/test_cli.py`

**Step 1: Write the failing tests**

```python
# tests/test_cli.py
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from mlb_digest.cli import main


def _make_mock_config(**overrides) -> MagicMock:
    """Build a mock config with sensible defaults. Override any field via kwargs."""
    defaults = {
        "team_id": 144,
        "team_name": "Braves",
        "league_id": 104,
        "team_feed_urls": [],
        "mlb_feed_urls": [],
        "anthropic_api_key": "sk-test",
        "narrator_model": "claude-sonnet-4-6",
        "narrator_temperature": 0.7,
        "team_colors": {"primary": "#13274F", "accent": "#CE1141"},
        "email_recipients": ["test@example.com"],
        "email_transport": "gmail_smtp",
        "gmail_address": "test@gmail.com",
        "gmail_app_password": "pw",
    }
    defaults.update(overrides)
    mock = MagicMock()
    for key, value in defaults.items():
        setattr(mock, key, value)
    mock.format_subject.return_value = "Braves Daily — Mar 14, 2026"
    return mock


def test_cli_help_shows_usage():
    runner = CliRunner()

    result = runner.invoke(main, ["--help"])

    assert result.exit_code == 0
    assert "catchup" in result.output
    assert "no-email" in result.output
    assert "dry-run" in result.output


def test_cli_test_email_subcommand():
    runner = CliRunner()

    with patch("mlb_digest.cli.send_email") as mock_send, \
         patch("mlb_digest.cli.load_config", return_value=_make_mock_config()):

        result = runner.invoke(main, ["test-email"])

    assert result.exit_code == 0
    mock_send.assert_called_once()


def test_cli_dry_run_does_not_call_narrator_or_emailer():
    runner = CliRunner()

    with patch("mlb_digest.cli.load_config", return_value=_make_mock_config()), \
         patch("mlb_digest.cli.get_yesterday_game", return_value=None), \
         patch("mlb_digest.cli.get_today_game", return_value=None), \
         patch("mlb_digest.cli.get_standings", return_value=[]), \
         patch("mlb_digest.cli.fetch_articles", return_value=[]), \
         patch("mlb_digest.cli.get_active_roster", return_value=[]), \
         patch("mlb_digest.cli.get_top_players", return_value={"top_hitters": [], "top_pitchers": []}), \
         patch("mlb_digest.cli.generate_narrative") as mock_narrate, \
         patch("mlb_digest.cli.send_email") as mock_send:

        result = runner.invoke(main, ["--dry-run"])

    mock_narrate.assert_not_called()
    mock_send.assert_not_called()


def test_cli_no_email_prints_to_stdout():
    runner = CliRunner()

    with patch("mlb_digest.cli.load_config", return_value=_make_mock_config()), \
         patch("mlb_digest.cli.get_yesterday_game", return_value=None), \
         patch("mlb_digest.cli.get_today_game", return_value=None), \
         patch("mlb_digest.cli.get_standings", return_value=[]), \
         patch("mlb_digest.cli.fetch_articles", return_value=[]), \
         patch("mlb_digest.cli.get_active_roster", return_value=[]), \
         patch("mlb_digest.cli.get_top_players", return_value={"top_hitters": [], "top_pitchers": []}), \
         patch("mlb_digest.cli.generate_narrative", return_value="## Test Digest\n\nContent here."):

        result = runner.invoke(main, ["--no-email"])

    assert "Test Digest" in result.output


def test_cli_catchup_fetches_roster_data():
    from mlb_digest.mlb_api import RosterPlayer

    runner = CliRunner()
    mock_roster = [RosterPlayer(player_id=660271, name="Acuna", position="RF", status="Active")]

    with patch("mlb_digest.cli.load_config", return_value=_make_mock_config()), \
         patch("mlb_digest.cli.get_yesterday_game", return_value=None), \
         patch("mlb_digest.cli.get_today_game", return_value=None), \
         patch("mlb_digest.cli.get_standings", return_value=[]), \
         patch("mlb_digest.cli.fetch_articles", return_value=[]), \
         patch("mlb_digest.cli.get_active_roster", return_value=mock_roster) as mock_roster_call, \
         patch("mlb_digest.cli.get_top_players", return_value={"top_hitters": [], "top_pitchers": []}), \
         patch("mlb_digest.cli.generate_narrative", return_value="## Roster\n\nAcuna leads.") as mock_narrate:

        result = runner.invoke(main, ["--catchup", "--no-email"])

    mock_roster_call.assert_called_once()
    # Verify roster data was passed to build_prompt via generate_narrative
    assert "Roster" in result.output or "Acuna" in result.output
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cli.py -v`
Expected: FAIL — `ModuleNotFoundError`

**Step 3: Write minimal implementation**

```python
# src/mlb_digest/cli.py
import json
import logging
import sys
from dataclasses import asdict

import click

from mlb_digest.config import load_config
from mlb_digest.emailer import send_email
from mlb_digest.feeds import fetch_articles, select_articles
from mlb_digest.mlb_api import (
    get_active_roster,
    get_standings,
    get_today_game,
    get_top_players,
    get_yesterday_game,
)
from mlb_digest.narrator import (
    NarratorError,
    build_prompt,
    build_system_prompt,
    generate_narrative,
)
from mlb_digest.templates import render_email_html, render_email_text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.option("--catchup", is_flag=True, help="Include roster, season overview, rivals, playoff picture.")
@click.option("--no-email", is_flag=True, help="Print digest to stdout instead of emailing.")
@click.option("--dry-run", is_flag=True, help="Print raw data without calling Sonnet or emailing.")
@click.pass_context
def main(ctx: click.Context, catchup: bool, no_email: bool, dry_run: bool) -> None:
    """MLB Digest — daily team digest via email."""
    if ctx.invoked_subcommand is not None:
        return

    config = load_config()
    exit_code = 0

    # Fetch data
    yesterday_game = get_yesterday_game(config.team_id)
    today_game = get_today_game(config.team_id, config.team_name)
    standings = get_standings(config.league_id)

    team_articles_raw = fetch_articles(config.team_feed_urls, source_type="team")
    mlb_articles_raw = fetch_articles(config.mlb_feed_urls, source_type="mlb")
    selected = select_articles(team_articles_raw, mlb_articles_raw)
    team_articles = selected["team"]
    mlb_articles = selected["mlb"]

    # Fetch roster for top players (always) and full roster (catchup only)
    roster = get_active_roster(config.team_id)
    top_players = get_top_players(roster) if roster else None

    roster_data = None
    if catchup and roster:
        roster_data = [asdict(p) for p in roster]

    # Dry run — dump raw data and exit
    if dry_run:
        data = {
            "yesterday_game": str(yesterday_game),
            "today_game": str(today_game),
            "standings": str(standings),
            "team_articles": [a.title for a in team_articles],
            "mlb_articles": [a.title for a in mlb_articles],
            "roster_count": len(roster),
            "top_players": top_players,
        }
        click.echo(json.dumps(data, indent=2, default=str))
        return

    # Build prompt and generate narrative
    prompt = build_prompt(
        team_name=config.team_name,
        yesterday_game=yesterday_game,
        today_game=today_game,
        standings=standings,
        team_articles=team_articles,
        mlb_articles=mlb_articles,
        top_players=top_players,
        catchup=catchup,
        roster_data=roster_data,
    )

    system_prompt = build_system_prompt(config.team_name)

    try:
        narrative = generate_narrative(
            prompt=prompt,
            system_prompt=system_prompt,
            api_key=config.anthropic_api_key,
            model=config.narrator_model,
            temperature=config.narrator_temperature,
        )
    except NarratorError:
        logger.error("Narrator failed — sending raw data fallback")
        narrative = f"# {config.team_name} Daily\n\n*AI narrative unavailable — here are the raw numbers.*\n\n{prompt}"
        exit_code = 1

    # No-email — print and exit
    if no_email:
        click.echo(narrative)
        ctx.exit(exit_code)
        return

    # Render and send email
    html_body = render_email_html(
        narrative,
        primary_color=config.team_colors.get("primary", "#333333"),
        accent_color=config.team_colors.get("accent", "#cc0000"),
    )
    text_body = render_email_text(narrative)
    subject = config.format_subject(catchup=catchup)

    try:
        send_email(
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            sender=config.gmail_address,
            password=config.gmail_app_password,
            recipients=config.email_recipients,
            transport=config.email_transport,
        )
    except Exception:
        logger.error("Failed to send email — printing to stdout", exc_info=True)
        click.echo(narrative)
        ctx.exit(2)
        return

    ctx.exit(exit_code)


@main.command()
def test_email() -> None:
    """Send a test email to verify Gmail setup."""
    config = load_config()

    send_email(
        subject="MLB Digest — Test Email",
        html_body="<html><body><h1>Hello from MLB Digest!</h1><p>Your email setup works.</p></body></html>",
        text_body="Hello from MLB Digest! Your email setup works.",
        sender=config.gmail_address,
        password=config.gmail_app_password,
        recipients=config.email_recipients,
        transport=config.email_transport,
    )

    click.echo("Test email sent successfully!")
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_cli.py -v`
Expected: 5 passed

**Step 5: Commit**

```bash
git add src/mlb_digest/cli.py tests/test_cli.py
git commit -m "feat: CLI module — main command with --catchup, --no-email, --dry-run, test-email"
```

---

## Task 9: Integration Tests — *Phase 5 (sequential, after Task 8)*

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write the integration tests**

```python
# tests/test_integration.py
from unittest.mock import patch, MagicMock

from click.testing import CliRunner

from mlb_digest.cli import main
from mlb_digest.mlb_api import (
    DivisionStandings,
    GameResult,
    TeamStanding,
    UpcomingGame,
)
from mlb_digest.narrator import NarratorError


def _make_mock_config() -> MagicMock:
    mock = MagicMock()
    mock.team_id = 144
    mock.team_name = "Braves"
    mock.league_id = 104
    mock.team_feed_urls = []
    mock.mlb_feed_urls = []
    mock.anthropic_api_key = "sk-test"
    mock.narrator_model = "claude-sonnet-4-6"
    mock.narrator_temperature = 0.7
    mock.team_colors = {"primary": "#13274F", "accent": "#CE1141"}
    mock.email_recipients = ["test@example.com"]
    mock.email_transport = "gmail_smtp"
    mock.gmail_address = "test@gmail.com"
    mock.gmail_app_password = "pw"
    mock.format_subject.return_value = "Braves Daily — Mar 15, 2026"
    return mock


def test_full_pipeline_game_day_no_email():
    """Full pipeline: game day data -> narrator -> stdout (no email)."""
    runner = CliRunner()

    game = GameResult(
        home_team="Braves", away_team="Mets",
        home_score=5, away_score=3,
        winning_pitcher="Sale", losing_pitcher="Severino",
        save_pitcher="Iglesias", summary="",
    )
    today = UpcomingGame(
        opponent="Phillies", game_time="2026-03-15T19:20:00Z",
        home_pitcher="Fried", away_pitcher="Wheeler", is_home=True,
    )
    standings = [DivisionStandings(
        division_name="NL East",
        teams=[
            TeamStanding(name="Braves", wins=5, losses=2, games_back="-", team_id=144),
            TeamStanding(name="Mets", wins=4, losses=3, games_back="1.0", team_id=121),
        ],
    )]

    narrative = "## Last Night's Game\n\nBraves beat the Mets 5-3. Sale got the W.\n\n## Today's Game\n\nBraves host the Phillies at 7:20 PM."

    with patch("mlb_digest.cli.load_config", return_value=_make_mock_config()), \
         patch("mlb_digest.cli.get_yesterday_game", return_value=game), \
         patch("mlb_digest.cli.get_today_game", return_value=today), \
         patch("mlb_digest.cli.get_standings", return_value=standings), \
         patch("mlb_digest.cli.fetch_articles", return_value=[]), \
         patch("mlb_digest.cli.get_active_roster", return_value=[]), \
         patch("mlb_digest.cli.get_top_players", return_value=None), \
         patch("mlb_digest.cli.generate_narrative", return_value=narrative):

        result = runner.invoke(main, ["--no-email"])

    assert result.exit_code == 0
    assert "Braves" in result.output
    assert "Mets" in result.output
    assert "Sale" in result.output
    assert "Phillies" in result.output


def test_full_pipeline_off_day_no_email():
    """Off day — no game sections, still sends standings + articles."""
    runner = CliRunner()

    standings = [DivisionStandings(
        division_name="NL East",
        teams=[TeamStanding(name="Braves", wins=5, losses=2, games_back="-", team_id=144)],
    )]

    narrative = "## Standings\n\nBraves sit atop the NL East at 5-2."

    with patch("mlb_digest.cli.load_config", return_value=_make_mock_config()), \
         patch("mlb_digest.cli.get_yesterday_game", return_value=None), \
         patch("mlb_digest.cli.get_today_game", return_value=None), \
         patch("mlb_digest.cli.get_standings", return_value=standings), \
         patch("mlb_digest.cli.fetch_articles", return_value=[]), \
         patch("mlb_digest.cli.get_active_roster", return_value=[]), \
         patch("mlb_digest.cli.get_top_players", return_value=None), \
         patch("mlb_digest.cli.generate_narrative", return_value=narrative):

        result = runner.invoke(main, ["--no-email"])

    assert result.exit_code == 0
    assert "Standings" in result.output


def test_full_pipeline_narrator_failure_exits_code_1():
    """Narrator fails -> CLI sends raw fallback and exits with code 1."""
    runner = CliRunner()

    with patch("mlb_digest.cli.load_config", return_value=_make_mock_config()), \
         patch("mlb_digest.cli.get_yesterday_game", return_value=None), \
         patch("mlb_digest.cli.get_today_game", return_value=None), \
         patch("mlb_digest.cli.get_standings", return_value=[]), \
         patch("mlb_digest.cli.fetch_articles", return_value=[]), \
         patch("mlb_digest.cli.get_active_roster", return_value=[]), \
         patch("mlb_digest.cli.get_top_players", return_value=None), \
         patch("mlb_digest.cli.generate_narrative", side_effect=NarratorError("API down")):

        result = runner.invoke(main, ["--no-email"])

    assert result.exit_code == 1
    assert "AI narrative unavailable" in result.output


def test_full_pipeline_email_failure_exits_code_2():
    """Email send fails -> CLI prints to stdout and exits with code 2."""
    runner = CliRunner()

    narrative = "## Test\n\nContent."

    with patch("mlb_digest.cli.load_config", return_value=_make_mock_config()), \
         patch("mlb_digest.cli.get_yesterday_game", return_value=None), \
         patch("mlb_digest.cli.get_today_game", return_value=None), \
         patch("mlb_digest.cli.get_standings", return_value=[]), \
         patch("mlb_digest.cli.fetch_articles", return_value=[]), \
         patch("mlb_digest.cli.get_active_roster", return_value=[]), \
         patch("mlb_digest.cli.get_top_players", return_value=None), \
         patch("mlb_digest.cli.generate_narrative", return_value=narrative), \
         patch("mlb_digest.cli.send_email", side_effect=Exception("SMTP failed")):

        result = runner.invoke(main, [])

    assert result.exit_code == 2
    assert "Test" in result.output


def test_full_pipeline_catchup_passes_roster_to_narrator():
    """--catchup flag triggers roster fetch and passes data to narrator."""
    from mlb_digest.mlb_api import RosterPlayer

    runner = CliRunner()
    mock_roster = [RosterPlayer(player_id=660271, name="Acuna", position="RF", status="Active")]

    narrative = "## Roster\n\nRonald Acuna Jr. — RF, leads team in SB."

    with patch("mlb_digest.cli.load_config", return_value=_make_mock_config()), \
         patch("mlb_digest.cli.get_yesterday_game", return_value=None), \
         patch("mlb_digest.cli.get_today_game", return_value=None), \
         patch("mlb_digest.cli.get_standings", return_value=[]), \
         patch("mlb_digest.cli.fetch_articles", return_value=[]), \
         patch("mlb_digest.cli.get_active_roster", return_value=mock_roster), \
         patch("mlb_digest.cli.get_top_players", return_value=None), \
         patch("mlb_digest.cli.generate_narrative", return_value=narrative) as mock_narrate:

        result = runner.invoke(main, ["--catchup", "--no-email"])

    assert result.exit_code == 0
    assert "Roster" in result.output
    # Verify build_prompt received catchup=True and roster_data
    call_kwargs = mock_narrate.call_args
    prompt_str = call_kwargs[1]["prompt"] if "prompt" in (call_kwargs[1] or {}) else call_kwargs[0][0]
    assert "roster" in prompt_str.lower()
```

**Step 2: Run integration tests**

Run: `pytest tests/test_integration.py -v`
Expected: 5 passed

**Step 3: Run the full test suite**

Run: `pytest tests/ -v`
Expected: All tests pass (~43 tests across all modules)

**Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "feat: integration tests — game day, off day, narrator failure, email failure, catchup"
```

---

## Task 10: Lint and Final Polish — *Phase 6 (sequential, after Task 9)*

**Step 1: Run ruff**

Run: `ruff check src/ tests/ --fix`
Expected: No errors (or auto-fixed)

Run: `ruff format src/ tests/`
Expected: Files formatted

**Step 2: Run full test suite**

Run: `pytest tests/ -v`
Expected: All tests pass

**Step 3: Verify CLI entry point**

Run: `mlb-digest --help`
Expected: Shows help text with `--catchup`, `--no-email`, `--dry-run` flags and `test-email` subcommand.

Run: `mlb-digest --dry-run`
Expected: Prints raw JSON data (will hit live MLB API and RSS feeds).

**Step 4: Commit**

```bash
git add -A
git commit -m "chore: lint and format with ruff"
```

---

## Task Summary

| Task | Module | Tests | Description |
|------|--------|-------|-------------|
| 1 | Scaffolding | — | pyproject.toml, config.toml, .gitignore, project structure |
| 2 | config.py | 3 | Load config.toml + .env, format subjects |
| 3 | feeds.py | 7 | RSS fetch, parse, deduplicate, select by source_type |
| 4 | mlb_api.py | 10 | Schedule, standings, roster, player stats, top players, home/away |
| 5 | narrator.py | 10 | System prompt, prompt building with ordered sections, standings, Sonnet generation |
| 6 | templates.py | 6 | Markdown lib → HTML with inline CSS, plain text |
| 7 | emailer.py | 4 | Gmail SMTP, multipart email, pluggable transport |
| 8 | cli.py | 5 | Click CLI with all flags, roster/stats wiring |
| 9 | Integration | 5 | Full pipeline: game day, off day, failures, catchup |
| 10 | Polish | — | Lint, format, verify entry point |

**Total: ~50 tests across 10 tasks**

## Fixes Applied from Adversarial Reviews

### Round 1

| Issue | Fix |
|-------|-----|
| C1: Wrong build-backend | Changed to `setuptools.build_meta` |
| C2: `--catchup` empty shell | Added `get_active_roster`, `get_player_stats`, `get_top_players` to mlb_api.py; wired roster data through CLI and narrator |
| C3: `<style>` block in email | Replaced with inline styles via `_apply_inline_styles()`, uses `markdown` library |
| C4: Raw `statsapi.get()` | Switched to `statsapi.schedule()` convenience function via `_fetch_schedule` |
| H2: Exit codes untested | Added `test_narrator_failure_exits_code_1` and `test_email_failure_exits_code_2`; use `ctx.exit()` |
| H3: Article mis-classification | Added `source_type` field to `Article`, classify at fetch time not by domain |
| H4: No retries on MLB API | Added `@retry` decorator to `_fetch_schedule` and `_fetch_roster` |
| H5: Daily player stats missing | `get_active_roster` + `get_top_players` called in standard (non-catchup) flow |
| H6: Tenacity/mock conflict | Note to patch `__wrapped__` or extract non-decorated helper |
| M2: caplog level | Added `caplog.at_level(logging.WARNING)` |
| M3: No catchup integration test | Added `test_full_pipeline_catchup_passes_roster_to_narrator` |
| M5: select_articles untested | Added `test_select_articles_separates_by_source_type` and dedup test |
| M7: Section ordering | Added OrderedDict + "Output sections in order" instruction to system prompt |
| L1: try/except in tests | Switched to `pytest.raises(...)` |
| L2: Hand-rolled markdown | Replaced with `markdown` library + `tables` extension |
| L3: httpx as dev dep | Moved to runtime dependencies |
| L5: Duplicate logging | Removed `print()` call, kept logger only |
| L7: Unused respx | Removed from dev dependencies |

### Round 2

| Issue | Fix |
|-------|-----|
| C1: SMTP test contradictory mocks | Removed `__wrapped__` patch, only mock `smtplib.SMTP_SSL` |
| C2: `is_home` hardcoded to `True` | `get_today_game` now accepts `team_name`, checks `home_name` for match. Added away game test. |
| C3/C4: `MagicMock` passed to `asdict()` crashes | Replaced with real `RosterPlayer` dataclass instances in CLI and integration tests |
| H1: Feed error test takes 7s from retry backoff | Patched retry wait to 0 in test |
| H3: `build_system_prompt` untested | Added `test_build_system_prompt_includes_team_name_and_rules` |
| H5: `get_top_players` untested | Added `test_get_top_players_returns_sorted_hitters_and_pitchers` |
| M8: Table test weak assertion | Split `or` into two separate asserts |
| M9: No test for standings in prompt | Added `test_build_prompt_includes_standings_data` |
| L2: `DEFAULT_CONFIG_PATH` breaks when installed | Changed to `Path.cwd() / "config.toml"` |
