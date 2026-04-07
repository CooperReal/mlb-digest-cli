"""
Tests for teams_registry — lookup by name, abbreviation, ID, and error handling.
"""

import pytest

from mlb_digest.teams_registry import (
    ALL_TEAMS,
    DIVISION_ORDER,
    get_team,
    get_team_or_raise,
    list_teams,
)

# ---------------------------------------------------------------------------
# Registry completeness
# ---------------------------------------------------------------------------


def test_registry_has_all_30_teams():
    assert len(ALL_TEAMS) == 30


def test_all_team_ids_are_unique():
    ids = [t.team_id for t in ALL_TEAMS]

    assert len(ids) == len(set(ids))


def test_all_abbreviations_are_unique():
    abbrevs = [t.abbreviation for t in ALL_TEAMS]

    assert len(abbrevs) == len(set(abbrevs))


def test_every_team_has_required_fields():
    for team in ALL_TEAMS:
        assert team.team_id > 0, f"{team.short_name} has invalid team_id"
        assert team.full_name, f"ID {team.team_id} missing full_name"
        assert team.short_name, f"ID {team.team_id} missing short_name"
        assert team.abbreviation, f"ID {team.team_id} missing abbreviation"
        assert team.league_id in (103, 104), f"{team.short_name} has invalid league_id"
        assert team.division in DIVISION_ORDER, f"{team.short_name} has invalid division"
        assert team.primary_color.startswith("#"), f"{team.short_name} bad primary_color"
        assert team.accent_color.startswith("#"), f"{team.short_name} bad accent_color"


def test_every_team_has_at_least_one_feed():
    for team in ALL_TEAMS:
        assert len(team.team_feed_urls) >= 1, f"{team.short_name} has no feeds"


def test_every_team_has_narrator_hint():
    for team in ALL_TEAMS:
        assert team.narrator_hint, f"{team.short_name} missing narrator_hint"


# ---------------------------------------------------------------------------
# Lookup by short name
# ---------------------------------------------------------------------------


def test_lookup_by_short_name():
    team = get_team("Yankees")

    assert team is not None
    assert team.team_id == 147
    assert team.full_name == "New York Yankees"


def test_lookup_by_short_name_case_insensitive():
    team = get_team("yankees")

    assert team is not None
    assert team.team_id == 147


def test_lookup_braves_by_short_name():
    team = get_team("Braves")

    assert team is not None
    assert team.team_id == 144
    assert team.division == "NL East"


# ---------------------------------------------------------------------------
# Lookup by abbreviation
# ---------------------------------------------------------------------------


def test_lookup_by_abbreviation():
    team = get_team("NYY")

    assert team is not None
    assert team.full_name == "New York Yankees"


def test_lookup_by_abbreviation_case_insensitive():
    team = get_team("nyy")

    assert team is not None
    assert team.team_id == 147


def test_lookup_dodgers_by_abbreviation():
    team = get_team("LAD")

    assert team is not None
    assert team.full_name == "Los Angeles Dodgers"


# ---------------------------------------------------------------------------
# Lookup by full name
# ---------------------------------------------------------------------------


def test_lookup_by_full_name():
    team = get_team("New York Yankees")

    assert team is not None
    assert team.team_id == 147


def test_lookup_by_full_name_case_insensitive():
    team = get_team("san francisco giants")

    assert team is not None
    assert team.team_id == 137


# ---------------------------------------------------------------------------
# Lookup by ID
# ---------------------------------------------------------------------------


def test_lookup_by_id():
    team = get_team(147)

    assert team is not None
    assert team.short_name == "Yankees"


def test_lookup_braves_by_id():
    team = get_team(144)

    assert team is not None
    assert team.short_name == "Braves"


# ---------------------------------------------------------------------------
# Not found
# ---------------------------------------------------------------------------


def test_lookup_unknown_name_returns_none():
    assert get_team("Unicorns") is None


def test_lookup_unknown_id_returns_none():
    assert get_team(9999) is None


def test_lookup_empty_string_returns_none():
    assert get_team("") is None


# ---------------------------------------------------------------------------
# get_team_or_raise
# ---------------------------------------------------------------------------


def test_or_raise_returns_team_on_match():
    team = get_team_or_raise("Mets")

    assert team.team_id == 121


def test_or_raise_raises_on_unknown():
    with pytest.raises(ValueError, match="Unknown team"):
        get_team_or_raise("Unicorns")


def test_or_raise_error_lists_available_teams():
    with pytest.raises(ValueError, match="Yankees"):
        get_team_or_raise("NotATeam")


# ---------------------------------------------------------------------------
# list_teams
# ---------------------------------------------------------------------------


def test_list_teams_returns_all_six_divisions():
    grouped = list_teams()

    assert len(grouped) == 6
    assert "AL East" in grouped
    assert "NL West" in grouped


def test_list_teams_has_five_teams_per_division():
    grouped = list_teams()

    for division, teams in grouped.items():
        assert len(teams) == 5, f"{division} has {len(teams)} teams, expected 5"


def test_list_teams_total_is_30():
    grouped = list_teams()
    total = sum(len(teams) for teams in grouped.values())

    assert total == 30


# ---------------------------------------------------------------------------
# Specific team data spot checks
# ---------------------------------------------------------------------------


def test_braves_colors():
    team = get_team("Braves")

    assert team.primary_color == "#13274F"
    assert team.accent_color == "#CE1141"


def test_dodgers_league():
    team = get_team("Dodgers")

    assert team.league_id == 104


def test_astros_division():
    team = get_team("Astros")

    assert team.division == "AL West"


def test_red_sox_feeds_include_mlbtraderumors():
    team = get_team("Red Sox")

    feed_urls = " ".join(team.team_feed_urls)
    assert "mlbtraderumors.com" in feed_urls


def test_white_sox_two_word_name():
    """Ensure multi-word short names work."""
    team = get_team("White Sox")

    assert team is not None
    assert team.abbreviation == "CWS"


def test_blue_jays_two_word_name():
    team = get_team("Blue Jays")

    assert team is not None
    assert team.abbreviation == "TOR"
