import os
from pathlib import Path
from unittest.mock import patch

import pytest

from mlb_digest.config import load_config

# ---------------------------------------------------------------------------
# Old verbose format still works (backward compatibility)
# ---------------------------------------------------------------------------


def test_load_config_reads_toml_values(tmp_path: Path):
    toml_content = """
[team]
id = 144
name = "Braves"
league_id = 104
colors = { primary = "#13274F", accent = "#CE1141" }

[email]
recipients = ["test@example.com"]
subject = "{team_name} Daily - {date}"
subject_catchup = "{team_name} Catchup - {date}"
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

    with patch.dict(os.environ, {"EMAIL_RECIPIENTS": ""}, clear=False):
        config = load_config(config_path=config_file)

    assert config.team_id == 144
    assert config.team_name == "Braves"
    assert config.full_team_name == "Atlanta Braves"
    assert config.league_id == 104
    assert config.division == "NL East"
    assert config.team_colors["primary"] == "#13274F"
    assert config.team_colors["accent"] == "#CE1141"
    assert config.email_recipients == ["test@example.com"]
    assert config.email_transport == "gmail_smtp"
    assert config.team_feed_urls == ["https://example.com/team.rss"]
    assert config.mlb_feed_urls == ["https://example.com/mlb.rss"]
    assert config.narrator_model == "claude-sonnet-4-6"
    assert config.narrator_temperature == 0.7


def test_load_config_reads_env_secrets(tmp_path: Path):
    toml_content = """
[team]
name = "Braves"

[email]
recipients = ["test@example.com"]

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
name = "Braves"

[email]
recipients = ["test@example.com"]
subject = "{team_name} Daily - {date}"
subject_catchup = "{team_name} Catchup - {date}"

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


def test_load_config_raises_on_missing_file(tmp_path: Path):
    nonexistent = tmp_path / "does_not_exist.toml"

    with pytest.raises(FileNotFoundError):
        load_config(config_path=nonexistent)


def test_load_config_raises_on_missing_team_name(tmp_path: Path):
    toml_content = """
[email]
recipients = ["test@example.com"]

[narrator]
model = "claude-sonnet-4-6"
temperature = 0.7
"""
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)

    with pytest.raises(ValueError, match="must have a 'name' field"):
        load_config(config_path=config_file)


def test_validate_secrets_raises_on_empty_api_key(tmp_path: Path):
    toml_content = """
[team]
name = "Braves"

[email]
recipients = ["test@example.com"]

[narrator]
model = "claude-sonnet-4-6"
temperature = 0.7
"""
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)

    env_vars = {
        "ANTHROPIC_API_KEY": "",
        "GMAIL_ADDRESS": "sender@gmail.com",
        "GMAIL_APP_PASSWORD": "xxxx-xxxx",
    }

    with patch.dict(os.environ, env_vars, clear=False):
        config = load_config(config_path=config_file)

    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        config.validate_secrets()


# ---------------------------------------------------------------------------
# New minimal format — registry lookup
# ---------------------------------------------------------------------------


def test_load_config_resolves_team_from_registry(tmp_path: Path):
    """Just `name = "Yankees"` should resolve all team metadata."""
    toml_content = """
[team]
name = "Yankees"

[email]
recipients = ["test@example.com"]

[narrator]
model = "claude-sonnet-4-6"
temperature = 0.7
"""
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)

    config = load_config(config_path=config_file)

    assert config.team_id == 147
    assert config.team_name == "Yankees"
    assert config.full_team_name == "New York Yankees"
    assert config.league_id == 103
    assert config.division == "AL East"
    assert config.team_colors["primary"] == "#003087"
    assert config.team_emoji == "\u26be"
    assert "Bronx" in config.narrator_hint


def test_load_config_resolves_by_abbreviation(tmp_path: Path):
    toml_content = """
[team]
name = "LAD"

[email]
recipients = ["test@example.com"]

[narrator]
model = "claude-sonnet-4-6"
temperature = 0.7
"""
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)

    config = load_config(config_path=config_file)

    assert config.team_id == 119
    assert config.full_team_name == "Los Angeles Dodgers"


def test_load_config_allows_color_override(tmp_path: Path):
    toml_content = """
[team]
name = "Braves"
colors = { accent = "#FFD700" }

[email]
recipients = ["test@example.com"]

[narrator]
model = "claude-sonnet-4-6"
temperature = 0.7
"""
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)

    config = load_config(config_path=config_file)

    assert config.team_colors["accent"] == "#FFD700"
    assert config.team_colors["primary"] == "#13274F"


def test_load_config_allows_display_name_override(tmp_path: Path):
    toml_content = """
[team]
name = "Cubs"
display_name = "Cubbies"

[email]
recipients = ["test@example.com"]

[narrator]
model = "claude-sonnet-4-6"
temperature = 0.7
"""
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)

    config = load_config(config_path=config_file)

    assert config.team_name == "Cubbies"
    assert config.full_team_name == "Chicago Cubs"


def test_load_config_uses_registry_feeds_when_none_in_toml(tmp_path: Path):
    toml_content = """
[team]
name = "Braves"

[email]
recipients = ["test@example.com"]

[narrator]
model = "claude-sonnet-4-6"
temperature = 0.7
"""
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)

    config = load_config(config_path=config_file)

    assert len(config.team_feed_urls) >= 1
    assert any("mlbtraderumors" in url for url in config.team_feed_urls)


def test_load_config_uses_default_mlb_feeds_when_none_in_toml(tmp_path: Path):
    toml_content = """
[team]
name = "Braves"

[email]
recipients = ["test@example.com"]

[narrator]
model = "claude-sonnet-4-6"
temperature = 0.7
"""
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)

    config = load_config(config_path=config_file)

    assert len(config.mlb_feed_urls) >= 1
    assert any("mlb.com" in url for url in config.mlb_feed_urls)


def test_load_config_raises_on_unknown_team(tmp_path: Path):
    toml_content = """
[team]
name = "Unicorns"

[email]
recipients = ["test@example.com"]

[narrator]
model = "claude-sonnet-4-6"
temperature = 0.7
"""
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)

    with pytest.raises(ValueError, match="Unknown team"):
        load_config(config_path=config_file)


def test_env_recipients_override_toml_recipients(tmp_path: Path):
    toml_content = """
[team]
name = "Braves"

[email]
recipients = ["toml@example.com"]

[narrator]
model = "claude-sonnet-4-6"
temperature = 0.7
"""
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)

    with patch.dict(os.environ, {"EMAIL_RECIPIENTS": "env1@example.com, env2@example.com"}):
        config = load_config(config_path=config_file)

    assert config.email_recipients == ["env1@example.com", "env2@example.com"]


def test_format_subject_includes_emoji(tmp_path: Path):
    toml_content = """
[team]
name = "Braves"

[email]
recipients = ["test@example.com"]

[narrator]
model = "claude-sonnet-4-6"
temperature = 0.7
"""
    config_file = tmp_path / "config.toml"
    config_file.write_text(toml_content)

    config = load_config(config_path=config_file)
    subject = config.format_subject(catchup=False)

    assert config.team_emoji in subject
    assert "Braves" in subject
