from unittest.mock import MagicMock, patch

import pytest

from mlb_digest.feeds import Article
from mlb_digest.mlb_api import (
    DivisionStandings,
    GameResult,
    TeamStanding,
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
        home_team="Braves",
        away_team="Mets",
        home_score=5,
        away_score=3,
        winning_pitcher="Sale",
        losing_pitcher="Severino",
        save_pitcher="Iglesias",
        summary="",
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
        Article(
            title="Big Trade",
            link="https://x.com/a",
            summary="A big trade happened.",
            source="x.com",
            source_type="team",
        ),
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
    standings = [
        DivisionStandings(
            division_name="NL East",
            teams=[TeamStanding(name="Braves", wins=50, losses=30, games_back="-", team_id=144)],
        )
    ]

    prompt = build_prompt(
        team_name="Braves",
        yesterday_game=None,
        today_game=None,
        standings=standings,
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
        home_team="Braves",
        away_team="Mets",
        home_score=5,
        away_score=3,
        winning_pitcher="Sale",
        losing_pitcher="Severino",
        save_pitcher="",
        summary="",
    )
    mlb_articles = [
        Article(
            title="MLB News",
            link="https://x.com/a",
            summary="news",
            source="x.com",
            source_type="mlb",
        ),
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

    with (
        patch("mlb_digest.narrator.anthropic.Anthropic", return_value=mock_client),
        pytest.raises(NarratorError, match="API down"),
    ):
        generate_narrative(
            prompt="test",
            system_prompt="test",
            api_key="sk-test",
            model="claude-sonnet-4-6",
            temperature=0.7,
        )


def test_generate_narrative_raises_on_empty_content():
    """NOTE: Depends on the new empty-content check being added to narrator.py."""
    mock_response = MagicMock()
    mock_response.content = []
    mock_response.usage.input_tokens = 100
    mock_response.usage.output_tokens = 0

    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_response

    with (
        patch("mlb_digest.narrator.anthropic.Anthropic", return_value=mock_client),
        pytest.raises(NarratorError, match="empty content"),
    ):
        generate_narrative(
            prompt="test prompt",
            system_prompt="test system",
            api_key="sk-test",
            model="claude-sonnet-4-6",
            temperature=0.7,
        )
