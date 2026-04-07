import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import date, timedelta

import statsapi
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


@dataclass
class GameResult:
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    winning_pitcher: str
    losing_pitcher: str
    save_pitcher: str
    summary: str


@dataclass
class UpcomingGame:
    opponent: str
    game_time: str
    home_pitcher: str
    away_pitcher: str
    is_home: bool


@dataclass
class TeamStanding:
    name: str
    wins: int
    losses: int
    games_back: str
    team_id: int


@dataclass
class DivisionStandings:
    division_name: str
    teams: list[TeamStanding]


@dataclass
class RosterPlayer:
    player_id: int
    name: str
    position: str
    status: str


@dataclass
class PlayerStats:
    player_id: int
    group: str
    stats: dict[str, str | int | float]


@dataclass
class TopPlayers:
    top_hitters: list[dict[str, str | int | float]]
    top_pitchers: list[dict[str, str | int | float]]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4), reraise=True)
def _fetch_schedule(team: int, date_str: str) -> list[dict]:
    return statsapi.schedule(team=team, date=date_str)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=4), reraise=True)
def _fetch_roster(team_id: int, roster_type: str = "active") -> dict:
    result = statsapi.get("team_roster", {"teamId": team_id, "rosterType": roster_type})
    if not isinstance(result, dict):
        raise RuntimeError(f"Unexpected response type from roster API: {type(result)}")
    return result


def get_yesterday_game(team_id: int) -> GameResult | None:
    yesterday = (date.today() - timedelta(days=1)).strftime("%m/%d/%Y")
    try:
        games = _fetch_schedule(team=team_id, date_str=yesterday)
    except Exception:
        logger.warning("Failed to fetch yesterday's schedule", exc_info=True)
        return None

    if not games:
        return None

    game = games[0]
    return GameResult(
        home_team=game.get("home_name", "Unknown"),
        away_team=game.get("away_name", "Unknown"),
        home_score=game.get("home_score", 0),
        away_score=game.get("away_score", 0),
        winning_pitcher=game.get("winning_pitcher", "Unknown"),
        losing_pitcher=game.get("losing_pitcher", "Unknown"),
        save_pitcher=game.get("save_pitcher", ""),
        summary=game.get("summary", ""),
    )


def get_today_game(team_id: int, team_name: str) -> UpcomingGame | None:
    today = date.today().strftime("%m/%d/%Y")
    try:
        games = _fetch_schedule(team=team_id, date_str=today)
    except Exception:
        logger.warning("Failed to fetch today's schedule", exc_info=True)
        return None

    if not games:
        return None

    game = games[0]
    home_name = game.get("home_name", "Unknown")
    away_name = game.get("away_name", "Unknown")
    home_id = game.get("home_id", 0)
    is_home = home_id == team_id
    opponent = away_name if is_home else home_name

    return UpcomingGame(
        opponent=opponent,
        game_time=game.get("game_datetime", ""),
        home_pitcher=game.get("home_probable_pitcher", "TBD"),
        away_pitcher=game.get("away_probable_pitcher", "TBD"),
        is_home=is_home,
    )


def get_standings(league_id: int) -> list[DivisionStandings]:
    try:
        data = statsapi.standings_data(leagueId=league_id)
    except Exception:
        logger.warning("Failed to fetch standings", exc_info=True)
        return []

    divisions = []
    for _div_id, div_data in data.items():
        teams = [
            TeamStanding(
                name=t["name"],
                wins=t["w"],
                losses=t["l"],
                games_back=t["gb"],
                team_id=t["team_id"],
            )
            for t in div_data["teams"]
        ]
        divisions.append(
            DivisionStandings(
                division_name=div_data["div_name"],
                teams=teams,
            )
        )

    return divisions


def get_active_roster(team_id: int) -> list[RosterPlayer]:
    try:
        data = _fetch_roster(team_id)
    except Exception:
        logger.warning("Failed to fetch roster", exc_info=True)
        return []

    players = []
    for entry in data.get("roster", []):
        person = entry.get("person", {})
        position = entry.get("position", {})
        status = entry.get("status", {})
        players.append(
            RosterPlayer(
                player_id=person.get("id", 0),
                name=person.get("fullName", "Unknown"),
                position=position.get("abbreviation", "Unknown"),
                status=status.get("description", "Active"),
            )
        )

    return players


def get_player_stats(player_id: int, group: str = "hitting") -> PlayerStats | None:
    try:
        data = statsapi.player_stat_data(player_id, group=group, type="season")
    except Exception:
        logger.warning("Failed to fetch stats for player %d", player_id, exc_info=True)
        return None

    stats_list = data.get("stats", [])
    if not stats_list:
        return None

    return PlayerStats(
        player_id=player_id,
        group=group,
        stats=stats_list[0].get("stats", {}),
    )


def get_top_players(
    roster: list[RosterPlayer],
    count: int = 3,
) -> TopPlayers:
    hitters: list[dict[str, str | int | float]] = []
    pitchers: list[dict[str, str | int | float]] = []

    def fetch_stats(player: RosterPlayer) -> tuple[str, dict[str, str | int | float] | None]:
        group = "pitching" if player.position == "P" else "hitting"
        stats = get_player_stats(player.player_id, group=group)
        if stats and stats.stats:
            return group, {"name": player.name, **stats.stats}
        return group, None

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_stats, p): p for p in roster}
        for future in as_completed(futures):
            group, result = future.result()
            if result is None:
                continue
            if group == "pitching":
                pitchers.append(result)
            else:
                hitters.append(result)

    hitters.sort(key=lambda h: float(h.get("avg", "0") or "0"), reverse=True)
    pitchers.sort(key=lambda p: float(p.get("era", "99") or "99"))

    return TopPlayers(
        top_hitters=hitters[:count],
        top_pitchers=pitchers[:count],
    )
