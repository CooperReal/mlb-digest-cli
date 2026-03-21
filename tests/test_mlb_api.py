import logging
from unittest.mock import patch

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
    with (
        caplog.at_level(logging.WARNING),
        patch("mlb_digest.mlb_api._fetch_schedule", side_effect=Exception("API timeout")),
    ):
        result = get_yesterday_game(team_id=144)

    assert result is None
    assert "API timeout" in caplog.text


def test_get_standings_handles_api_error(caplog):
    with (
        caplog.at_level(logging.WARNING),
        patch("mlb_digest.mlb_api.statsapi.standings_data", side_effect=Exception("API down")),
    ):
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


def test_get_today_game_handles_api_error(caplog):
    with (
        caplog.at_level(logging.WARNING),
        patch("mlb_digest.mlb_api._fetch_schedule", side_effect=Exception("API timeout")),
    ):
        result = get_today_game(team_id=144, team_name="Braves")

    assert result is None
    assert "API timeout" in caplog.text


def test_get_active_roster_handles_api_error(caplog):
    with (
        caplog.at_level(logging.WARNING),
        patch("mlb_digest.mlb_api._fetch_roster", side_effect=Exception("Connection refused")),
    ):
        result = get_active_roster(team_id=144)

    assert result == []
    assert "Connection refused" in caplog.text


def test_get_player_stats_returns_none_on_api_error():
    with patch("mlb_digest.mlb_api.statsapi.player_stat_data", side_effect=Exception("Not found")):
        result = get_player_stats(player_id=999999)

    assert result is None


def test_get_player_stats_returns_none_when_no_stats():
    mock_data = {"id": 660271, "first_name": "Ronald", "last_name": "Acuna", "stats": []}

    with patch("mlb_digest.mlb_api.statsapi.player_stat_data", return_value=mock_data):
        result = get_player_stats(player_id=660271, group="hitting")

    assert result is None


def test_get_top_players_with_empty_roster():
    result = get_top_players([])

    assert result == {"top_hitters": [], "top_pitchers": []}
