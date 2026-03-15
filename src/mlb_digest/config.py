import os
import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

DEFAULT_CONFIG_PATH = Path.cwd() / "config.toml"


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
        return template.format(team_name=self.team_name, date=date.today().strftime("%b %d, %Y"))


def _parse_recipients(env_value: str, toml_fallback: list[str]) -> list[str]:
    if env_value:
        return [r.strip() for r in env_value.split(",") if r.strip()]
    return toml_fallback


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
        email_recipients=_parse_recipients(
            os.environ.get("EMAIL_RECIPIENTS", ""),
            email.get("recipients", []),
        ),
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
