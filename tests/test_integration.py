from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from mlb_digest.cli import main
from mlb_digest.mlb_api import (
    DivisionStandings,
    GameResult,
    RosterPlayer,
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
    mock.format_subject.return_value = "Braves Daily - Mar 15, 2026"
    return mock


def test_full_pipeline_game_day_no_email():
    """Full pipeline: game day data -> narrator -> stdout (no email)."""
    runner = CliRunner()

    game = GameResult(
        home_team="Braves",
        away_team="Mets",
        home_score=5,
        away_score=3,
        winning_pitcher="Sale",
        losing_pitcher="Severino",
        save_pitcher="Iglesias",
        summary="",
    )
    today = UpcomingGame(
        opponent="Phillies",
        game_time="2026-03-15T19:20:00Z",
        home_pitcher="Fried",
        away_pitcher="Wheeler",
        is_home=True,
    )
    standings = [
        DivisionStandings(
            division_name="NL East",
            teams=[
                TeamStanding(name="Braves", wins=5, losses=2, games_back="-", team_id=144),
                TeamStanding(name="Mets", wins=4, losses=3, games_back="1.0", team_id=121),
            ],
        )
    ]

    narrative = (
        "## Last Night's Game\n\n"
        "Braves beat the Mets 5-3. Sale got the W.\n\n"
        "## Today's Game\n\n"
        "Braves host the Phillies at 7:20 PM."
    )

    with (
        patch("mlb_digest.cli.load_config", return_value=_make_mock_config()),
        patch("mlb_digest.cli.get_yesterday_game", return_value=game),
        patch("mlb_digest.cli.get_today_game", return_value=today),
        patch("mlb_digest.cli.get_standings", return_value=standings),
        patch("mlb_digest.cli.fetch_articles", return_value=[]),
        patch("mlb_digest.cli.get_active_roster", return_value=[]),
        patch("mlb_digest.cli.get_top_players", return_value=None),
        patch("mlb_digest.cli.generate_narrative", return_value=narrative),
    ):
        result = runner.invoke(main, ["--no-email"])

    assert result.exit_code == 0
    assert "Braves" in result.output
    assert "Mets" in result.output
    assert "Sale" in result.output
    assert "Phillies" in result.output


def test_full_pipeline_off_day_no_email():
    """Off day - no game sections, still sends standings."""
    runner = CliRunner()

    standings = [
        DivisionStandings(
            division_name="NL East",
            teams=[
                TeamStanding(name="Braves", wins=5, losses=2, games_back="-", team_id=144),
            ],
        )
    ]

    narrative = "## Standings\n\nBraves sit atop the NL East at 5-2."

    with (
        patch("mlb_digest.cli.load_config", return_value=_make_mock_config()),
        patch("mlb_digest.cli.get_yesterday_game", return_value=None),
        patch("mlb_digest.cli.get_today_game", return_value=None),
        patch("mlb_digest.cli.get_standings", return_value=standings),
        patch("mlb_digest.cli.fetch_articles", return_value=[]),
        patch("mlb_digest.cli.get_active_roster", return_value=[]),
        patch("mlb_digest.cli.get_top_players", return_value=None),
        patch("mlb_digest.cli.generate_narrative", return_value=narrative),
    ):
        result = runner.invoke(main, ["--no-email"])

    assert result.exit_code == 0
    assert "Standings" in result.output


def test_full_pipeline_narrator_failure_exits_code_1():
    """Narrator fails -> CLI sends raw fallback and exits with code 1."""
    runner = CliRunner()

    with (
        patch("mlb_digest.cli.load_config", return_value=_make_mock_config()),
        patch("mlb_digest.cli.get_yesterday_game", return_value=None),
        patch("mlb_digest.cli.get_today_game", return_value=None),
        patch("mlb_digest.cli.get_standings", return_value=[]),
        patch("mlb_digest.cli.fetch_articles", return_value=[]),
        patch("mlb_digest.cli.get_active_roster", return_value=[]),
        patch("mlb_digest.cli.get_top_players", return_value=None),
        patch("mlb_digest.cli.generate_narrative", side_effect=NarratorError("API down")),
    ):
        result = runner.invoke(main, ["--no-email"])

    assert result.exit_code == 1
    assert "AI narrative unavailable" in result.output


def test_full_pipeline_email_failure_exits_code_2():
    """Email send fails -> CLI prints to stdout and exits with code 2."""
    runner = CliRunner()

    narrative = "## Test\n\nContent."

    with (
        patch("mlb_digest.cli.load_config", return_value=_make_mock_config()),
        patch("mlb_digest.cli.get_yesterday_game", return_value=None),
        patch("mlb_digest.cli.get_today_game", return_value=None),
        patch("mlb_digest.cli.get_standings", return_value=[]),
        patch("mlb_digest.cli.fetch_articles", return_value=[]),
        patch("mlb_digest.cli.get_active_roster", return_value=[]),
        patch("mlb_digest.cli.get_top_players", return_value=None),
        patch("mlb_digest.cli.generate_narrative", return_value=narrative),
        patch("mlb_digest.cli.send_email", side_effect=Exception("SMTP failed")),
    ):
        result = runner.invoke(main, [])

    assert result.exit_code == 2
    assert "Test" in result.output


def test_full_pipeline_catchup_passes_roster_to_narrator():
    """--catchup flag triggers roster fetch and passes roster data to narrator."""
    runner = CliRunner()
    mock_roster = [
        RosterPlayer(player_id=660271, name="Acuna", position="RF", status="Active"),
    ]

    narrative = "## Roster\n\nRonald Acuna Jr. - RF, leads team in SB."

    with (
        patch("mlb_digest.cli.load_config", return_value=_make_mock_config()),
        patch("mlb_digest.cli.get_yesterday_game", return_value=None),
        patch("mlb_digest.cli.get_today_game", return_value=None),
        patch("mlb_digest.cli.get_standings", return_value=[]),
        patch("mlb_digest.cli.fetch_articles", return_value=[]),
        patch("mlb_digest.cli.get_active_roster", return_value=mock_roster),
        patch("mlb_digest.cli.get_top_players", return_value=None),
        patch("mlb_digest.cli.generate_narrative", return_value=narrative) as mock_narrate,
    ):
        result = runner.invoke(main, ["--catchup", "--no-email"])

    assert result.exit_code == 0
    assert "Roster" in result.output
    # Verify build_prompt received catchup=True and roster_data
    call_kwargs = mock_narrate.call_args
    kwargs = call_kwargs[1] or {}
    prompt_str = kwargs["prompt"] if "prompt" in kwargs else call_kwargs[0][0]
    assert "roster" in prompt_str.lower()
