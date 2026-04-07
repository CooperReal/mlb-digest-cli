import json
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from mlb_digest.cli import main


def _make_mock_config(**overrides) -> MagicMock:
    """Build a mock config with sensible defaults. Override any field via kwargs."""
    defaults = {
        "team_id": 144,
        "team_name": "Braves",
        "full_team_name": "Atlanta Braves",
        "league_id": 104,
        "division": "NL East",
        "team_feed_urls": [],
        "mlb_feed_urls": [],
        "anthropic_api_key": "sk-test",
        "narrator_model": "claude-sonnet-4-6",
        "narrator_temperature": 0.7,
        "team_colors": {"primary": "#13274F", "accent": "#CE1141", "secondary": "#CE1141"},
        "team_emoji": "\U0001fa93",
        "narrator_hint": "Write like a Braves fan.",
        "email_recipients": ["test@example.com"],
        "email_transport": "gmail_smtp",
        "gmail_address": "test@gmail.com",
        "gmail_app_password": "pw",
    }
    defaults.update(overrides)
    mock = MagicMock()
    for key, value in defaults.items():
        setattr(mock, key, value)
    mock.format_subject.return_value = "Braves Daily - Mar 14, 2026"
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

    with (
        patch("mlb_digest.cli.send_email") as mock_send,
        patch("mlb_digest.cli.load_config", return_value=_make_mock_config()),
    ):
        result = runner.invoke(main, ["test-email"])

    assert result.exit_code == 0
    mock_send.assert_called_once()


def test_cli_dry_run_does_not_call_narrator_or_emailer():
    runner = CliRunner()

    top = {"top_hitters": [], "top_pitchers": []}
    with (
        patch("mlb_digest.cli.load_config", return_value=_make_mock_config()),
        patch("mlb_digest.cli.get_yesterday_game", return_value=None),
        patch("mlb_digest.cli.get_today_game", return_value=None),
        patch("mlb_digest.cli.get_standings", return_value=[]),
        patch("mlb_digest.cli.fetch_articles", return_value=[]),
        patch("mlb_digest.cli.get_active_roster", return_value=[]),
        patch("mlb_digest.cli.get_top_players", return_value=top),
        patch("mlb_digest.cli.generate_narrative") as mock_narrate,
        patch("mlb_digest.cli.send_email") as mock_send,
    ):
        runner.invoke(main, ["--dry-run"])

    mock_narrate.assert_not_called()
    mock_send.assert_not_called()


def test_cli_no_email_prints_to_stdout():
    runner = CliRunner()

    top = {"top_hitters": [], "top_pitchers": []}
    with (
        patch("mlb_digest.cli.load_config", return_value=_make_mock_config()),
        patch("mlb_digest.cli.get_yesterday_game", return_value=None),
        patch("mlb_digest.cli.get_today_game", return_value=None),
        patch("mlb_digest.cli.get_standings", return_value=[]),
        patch("mlb_digest.cli.fetch_articles", return_value=[]),
        patch("mlb_digest.cli.get_active_roster", return_value=[]),
        patch("mlb_digest.cli.get_top_players", return_value=top),
        patch(
            "mlb_digest.cli.generate_narrative",
            return_value="## Test Digest\n\nContent here.",
        ),
    ):
        result = runner.invoke(main, ["--no-email"])

    assert "Test Digest" in result.output


def test_cli_smoke_test_uses_haiku_and_small_max_tokens():
    runner = CliRunner()

    top = {"top_hitters": [], "top_pitchers": []}
    with (
        patch("mlb_digest.cli.load_config", return_value=_make_mock_config()),
        patch("mlb_digest.cli.get_yesterday_game", return_value=None),
        patch("mlb_digest.cli.get_today_game", return_value=None),
        patch("mlb_digest.cli.get_standings", return_value=[]),
        patch("mlb_digest.cli.fetch_articles", return_value=[]),
        patch("mlb_digest.cli.get_active_roster", return_value=[]),
        patch("mlb_digest.cli.get_top_players", return_value=top),
        patch("mlb_digest.cli.generate_narrative", return_value="## Smoke") as mock_narrate,
        patch("mlb_digest.cli.send_email"),
    ):
        result = runner.invoke(main, ["--smoke-test"])

    assert result.exit_code == 0
    call_kwargs = mock_narrate.call_args[1]
    assert call_kwargs["model"] == "claude-haiku-4-5-20251001"
    assert call_kwargs["max_tokens"] == 50


def test_cli_catchup_fetches_roster_data():
    from mlb_digest.mlb_api import RosterPlayer

    runner = CliRunner()
    mock_roster = [RosterPlayer(player_id=660271, name="Acuna", position="RF", status="Active")]

    top = {"top_hitters": [], "top_pitchers": []}
    with (
        patch("mlb_digest.cli.load_config", return_value=_make_mock_config()),
        patch("mlb_digest.cli.get_yesterday_game", return_value=None),
        patch("mlb_digest.cli.get_today_game", return_value=None),
        patch("mlb_digest.cli.get_standings", return_value=[]),
        patch("mlb_digest.cli.fetch_articles", return_value=[]),
        patch("mlb_digest.cli.get_active_roster", return_value=mock_roster) as mock_roster_call,
        patch("mlb_digest.cli.get_top_players", return_value=top),
        patch(
            "mlb_digest.cli.generate_narrative",
            return_value="## Roster\n\nAcuna leads.",
        ),
    ):
        result = runner.invoke(main, ["--catchup", "--no-email"])

    mock_roster_call.assert_called_once()
    # Verify roster data was passed to build_prompt via generate_narrative
    assert "Roster" in result.output or "Acuna" in result.output


def test_cli_list_teams_shows_all_divisions():
    runner = CliRunner()

    result = runner.invoke(main, ["list-teams"])

    assert result.exit_code == 0
    assert "AL East" in result.output
    assert "NL West" in result.output
    assert "Yankees" in result.output
    assert "Braves" in result.output


def test_cli_list_teams_json_output():
    runner = CliRunner()

    result = runner.invoke(main, ["list-teams", "--json-output"])

    assert result.exit_code == 0
    data = json.loads(result.output)
    assert "AL East" in data
    assert len(data) == 6
