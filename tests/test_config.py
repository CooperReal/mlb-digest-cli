import os
from pathlib import Path
from unittest.mock import patch

import pytest

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
subject = "{team_name} Daily - {date}"
subject_catchup = "{team_name} Catchup - {date}"
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
subject = "{team_name} Daily - {date}"
subject_catchup = "{team_name} Catchup - {date}"
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


def test_load_config_raises_on_missing_file(tmp_path: Path):
    nonexistent = tmp_path / "does_not_exist.toml"

    with pytest.raises(FileNotFoundError):
        load_config(config_path=nonexistent)


def test_load_config_raises_on_missing_toml_section(tmp_path: Path):
    toml_content = """
[email]
recipients = ["test@example.com"]
subject = "Test"
subject_catchup = "Test Catchup"
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

    with pytest.raises(KeyError):
        load_config(config_path=config_file)


def test_validate_secrets_raises_on_empty_api_key(tmp_path: Path):
    """NOTE: Depends on Config.validate_secrets() being added by the other agent."""
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
        "ANTHROPIC_API_KEY": "",
        "GMAIL_ADDRESS": "sender@gmail.com",
        "GMAIL_APP_PASSWORD": "xxxx-xxxx",
    }

    with patch.dict(os.environ, env_vars, clear=False):
        config = load_config(config_path=config_file)

    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        config.validate_secrets()
