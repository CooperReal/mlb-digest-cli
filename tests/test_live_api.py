"""
Live API smoke tests — verify every team ID in the registry returns real data.

These tests hit the real MLB Stats API and are skipped by default.
Run them explicitly with:  uv run pytest -m live -v
"""

import pytest
import statsapi

from mlb_digest.teams_registry import ALL_TEAMS, TeamInfo

TEAM_IDS = [(t.abbreviation, t) for t in ALL_TEAMS]


@pytest.mark.live
class TestScheduleLookup:
    """Every team ID should return a valid schedule response (even if no games)."""

    @pytest.mark.parametrize(("abbrev", "team"), TEAM_IDS, ids=[t[0] for t in TEAM_IDS])
    def test_schedule_returns_without_error(self, abbrev: str, team: TeamInfo) -> None:
        result = statsapi.schedule(team=team.team_id, date="04/03/2026")

        assert isinstance(result, list)


@pytest.mark.live
class TestStandings:
    """Both league IDs (103=AL, 104=NL) should return 3 divisions with 5 teams each."""

    @pytest.mark.parametrize(("league_name", "league_id"), [("AL", 103), ("NL", 104)])
    def test_standings_returns_full_league(self, league_name: str, league_id: int) -> None:
        data = statsapi.standings_data(leagueId=league_id)

        assert len(data) == 3
        total_teams = sum(len(d["teams"]) for d in data.values())
        assert total_teams == 15


@pytest.mark.live
class TestRoster:
    """Every team should have an active roster with at least 1 player."""

    @pytest.mark.parametrize(("abbrev", "team"), TEAM_IDS, ids=[t[0] for t in TEAM_IDS])
    def test_roster_returns_players(self, abbrev: str, team: TeamInfo) -> None:
        data = statsapi.get("team_roster", {"teamId": team.team_id, "rosterType": "active"})

        assert isinstance(data, dict)
        roster = data.get("roster", [])
        assert len(roster) >= 1, f"{team.short_name} returned empty roster"

        # Verify player data structure
        first = roster[0]
        assert "person" in first
        assert "id" in first["person"]
        assert "fullName" in first["person"]
