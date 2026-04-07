from unittest.mock import MagicMock

import pytest

from mlb_digest.config import Config


@pytest.fixture
def mock_config() -> MagicMock:
    """Build a mock Config with all required fields. Uses spec=Config to catch field drift."""
    mock = MagicMock(spec=Config)
    mock.team_id = 144
    mock.team_name = "Braves"
    mock.full_team_name = "Atlanta Braves"
    mock.league_id = 104
    mock.division = "NL East"
    mock.team_feed_urls = []
    mock.mlb_feed_urls = []
    mock.anthropic_api_key = "sk-test"  # pragma: allowlist secret
    mock.narrator_model = "claude-sonnet-4-6"
    mock.narrator_temperature = 0.7
    mock.team_colors = {"primary": "#13274F", "accent": "#CE1141", "secondary": "#CE1141"}
    mock.team_emoji = "\U0001fa93"
    mock.narrator_hint = "Write like a Braves fan."
    mock.email_recipients = ["test@example.com"]
    mock.email_transport = "gmail_smtp"
    mock.gmail_address = "test@gmail.com"
    mock.gmail_app_password = "pw"  # pragma: allowlist secret
    mock.format_subject.return_value = "Braves Daily - Mar 14, 2026"
    return mock
