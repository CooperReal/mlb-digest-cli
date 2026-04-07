"""
Configuration loader.

Reads config.toml and .env, then looks up the team in the registry.
Users only need to set `name = "Yankees"` — everything else has sensible defaults.

Override priority (highest to lowest):
    1. Environment variables (EMAIL_RECIPIENTS, secrets)
    2. config.toml explicit values
    3. Team registry defaults
"""

import os
import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

from mlb_digest.teams_registry import TeamInfo, get_team_or_raise

DEFAULT_CONFIG_PATH = Path.cwd() / "config.toml"

# Defaults for fields not in the registry
DEFAULT_MLB_FEED_URLS = [
    "https://www.mlb.com/feeds/news/rss.xml",
    "https://www.espn.com/espn/rss/mlb/news",
    "https://www.mlbtraderumors.com/feed",
    "https://blogs.fangraphs.com/feed/",
    "https://www.reddit.com/r/baseball/.rss",
]

DEFAULT_NARRATOR_MODEL = "claude-sonnet-4-6"
DEFAULT_NARRATOR_TEMPERATURE = 0.7
DEFAULT_EMAIL_TRANSPORT = "gmail_smtp"


@dataclass
class Config:
    # Team identity (from registry)
    team_id: int
    team_name: str
    full_team_name: str
    league_id: int
    division: str
    team_colors: dict[str, str]
    team_emoji: str
    narrator_hint: str

    # Email
    email_recipients: list[str]
    email_subject_template: str
    email_subject_catchup_template: str
    email_transport: str

    # Feeds
    team_feed_urls: list[str]
    mlb_feed_urls: list[str]

    # Narrator
    narrator_model: str
    narrator_temperature: float

    # Secrets
    anthropic_api_key: str
    gmail_address: str
    gmail_app_password: str

    def validate_secrets(self) -> None:
        missing = []
        if not self.anthropic_api_key:
            missing.append("ANTHROPIC_API_KEY")
        if not self.gmail_address:
            missing.append("GMAIL_ADDRESS")
        if not self.gmail_app_password:
            missing.append("GMAIL_APP_PASSWORD")
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    def format_subject(self, catchup: bool = False) -> str:
        template = self.email_subject_catchup_template if catchup else self.email_subject_template
        return template.format(
            team_name=self.team_name,
            full_team_name=self.full_team_name,
            emoji=self.team_emoji,
            date=date.today().strftime("%b %d, %Y"),
        )


def _parse_recipients(env_value: str, toml_fallback: list[str]) -> list[str]:
    if env_value:
        return [r.strip() for r in env_value.split(",") if r.strip()]
    return toml_fallback


def _resolve_team(toml_team: dict) -> TeamInfo:
    """
    Find the team in the registry. Accepts name, abbreviation, or ID.

    Examples of valid config.toml [team] sections:

        [team]
        name = "Yankees"

        [team]
        name = "NYY"

        [team]
        id = 147
    """
    # Try name first, then ID
    identifier = toml_team.get("name") or toml_team.get("id")
    if identifier is None:
        raise ValueError(
            "config.toml [team] section must have a 'name' field. "
            "Example: name = \"Yankees\""
        )
    return get_team_or_raise(identifier)


def load_config(config_path: Path = DEFAULT_CONFIG_PATH) -> Config:
    load_dotenv()

    with open(config_path, "rb") as f:
        toml_data = tomllib.load(f)

    toml_team = toml_data.get("team", {})
    toml_email = toml_data.get("email", {})
    toml_feeds = toml_data.get("feeds", {})
    toml_narrator = toml_data.get("narrator", {})

    # Look up team in registry
    team_info = _resolve_team(toml_team)

    # Merge colors: registry defaults + any toml overrides
    colors = {
        "primary": team_info.primary_color,
        "secondary": team_info.secondary_color,
        "accent": team_info.accent_color,
    }
    if "colors" in toml_team:
        colors.update(toml_team["colors"])

    # Team feeds: use toml override if present, otherwise registry defaults
    team_feeds = (
        toml_feeds.get("team", {}).get("urls")
        or list(team_info.team_feed_urls)
    )

    # MLB-wide feeds: use toml override if present, otherwise defaults
    mlb_feeds = (
        toml_feeds.get("mlb", {}).get("urls")
        or DEFAULT_MLB_FEED_URLS
    )

    # Subject line defaults include the emoji
    default_subject = "{emoji} {team_name} Daily — {date}"
    default_subject_catchup = "{emoji} {team_name} Catchup — {date}"

    return Config(
        # Team identity
        team_id=toml_team.get("id", team_info.team_id),
        team_name=toml_team.get("display_name", team_info.short_name),
        full_team_name=team_info.full_name,
        league_id=toml_team.get("league_id", team_info.league_id),
        division=team_info.division,
        team_colors=colors,
        team_emoji=toml_team.get("emoji", team_info.emoji),
        narrator_hint=team_info.narrator_hint,
        # Email
        email_recipients=_parse_recipients(
            os.environ.get("EMAIL_RECIPIENTS", ""),
            toml_email.get("recipients", []),
        ),
        email_subject_template=toml_email.get("subject", default_subject),
        email_subject_catchup_template=toml_email.get("subject_catchup", default_subject_catchup),
        email_transport=toml_email.get("transport", DEFAULT_EMAIL_TRANSPORT),
        # Feeds
        team_feed_urls=team_feeds,
        mlb_feed_urls=mlb_feeds,
        # Narrator
        narrator_model=toml_narrator.get("model", DEFAULT_NARRATOR_MODEL),
        narrator_temperature=toml_narrator.get("temperature", DEFAULT_NARRATOR_TEMPERATURE),
        # Secrets
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        gmail_address=os.environ.get("GMAIL_ADDRESS", ""),
        gmail_app_password=os.environ.get("GMAIL_APP_PASSWORD", ""),
    )
