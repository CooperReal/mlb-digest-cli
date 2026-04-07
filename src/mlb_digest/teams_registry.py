"""
All 30 MLB teams with their metadata, colors, feeds, and narrator personality.

This is the single source of truth for team configuration. Users only need to
set `name = "Yankees"` in config.toml — everything else is looked up here.

Usage:
    from mlb_digest.teams_registry import get_team, list_teams

    team = get_team("Yankees")       # by short name
    team = get_team("NYY")           # by abbreviation
    team = get_team("New York Yankees")  # by full name
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class TeamInfo:
    """Everything we need to know about an MLB team."""

    team_id: int
    full_name: str
    short_name: str
    abbreviation: str
    league_id: int  # 103 = AL, 104 = NL
    division: str  # "AL East", "NL West", etc.

    # Colors — drive the entire email theme
    primary_color: str  # Dark/dominant — header background, headings
    secondary_color: str  # Supporting color — subtle accents
    accent_color: str  # Bright/pop — links, dividers, highlights

    # RSS feeds — team-specific news sources
    team_feed_urls: tuple[str, ...] = field(default_factory=tuple)

    # Emoji for subject lines and social posts
    emoji: str = ""

    # One-liner that shapes the narrator's voice for this team
    narrator_hint: str = ""


# ---------------------------------------------------------------------------
# American League East
# ---------------------------------------------------------------------------

ORIOLES = TeamInfo(
    team_id=110,
    full_name="Baltimore Orioles",
    short_name="Orioles",
    abbreviation="BAL",
    league_id=103,
    division="AL East",
    primary_color="#DF4601",
    secondary_color="#000000",
    accent_color="#DF4601",
    team_feed_urls=(
        "https://www.mlbtraderumors.com/baltimore-orioles/feed",
        "https://www.reddit.com/r/orioles/.rss",
    ),
    emoji="🐦",
    narrator_hint=(
        "Write like a lifelong Baltimore fan who remembers the lean years "
        "and is fired up about the rebuild paying off."
    ),
)

RED_SOX = TeamInfo(
    team_id=111,
    full_name="Boston Red Sox",
    short_name="Red Sox",
    abbreviation="BOS",
    league_id=103,
    division="AL East",
    primary_color="#BD3039",
    secondary_color="#0C2340",
    accent_color="#BD3039",
    team_feed_urls=(
        "https://www.mlbtraderumors.com/boston-red-sox/feed",
        "https://www.reddit.com/r/redsox/.rss",
    ),
    emoji="🧦",
    narrator_hint=(
        "Write like a die-hard Sox fan from Southie who lives and dies with "
        "every pitch and still brings up 2004 at least once a week."
    ),
)

YANKEES = TeamInfo(
    team_id=147,
    full_name="New York Yankees",
    short_name="Yankees",
    abbreviation="NYY",
    league_id=103,
    division="AL East",
    primary_color="#003087",
    secondary_color="#132448",
    accent_color="#C4CED4",
    team_feed_urls=(
        "https://www.mlbtraderumors.com/new-york-yankees/feed",
        "https://www.reddit.com/r/NYYankees/.rss",
    ),
    emoji="⚾",
    narrator_hint=(
        "Write like a proud Bronx fan who expects championships, references "
        "the franchise's history naturally, and has strong opinions on the roster."
    ),
)

RAYS = TeamInfo(
    team_id=139,
    full_name="Tampa Bay Rays",
    short_name="Rays",
    abbreviation="TB",
    league_id=103,
    division="AL East",
    primary_color="#092C5C",
    secondary_color="#8FBCE6",
    accent_color="#8FBCE6",
    team_feed_urls=(
        "https://www.mlbtraderumors.com/tampa-bay-rays/feed",
        "https://www.reddit.com/r/tampabayrays/.rss",
    ),
    emoji="☀️",
    narrator_hint=(
        "Write like a savvy Rays fan who appreciates analytics, creative "
        "roster moves, and punching above the payroll weight class."
    ),
)

BLUE_JAYS = TeamInfo(
    team_id=141,
    full_name="Toronto Blue Jays",
    short_name="Blue Jays",
    abbreviation="TOR",
    league_id=103,
    division="AL East",
    primary_color="#134A8E",
    secondary_color="#1D2D5C",
    accent_color="#E8291C",
    team_feed_urls=(
        "https://www.mlbtraderumors.com/toronto-blue-jays/feed",
        "https://www.reddit.com/r/Torontobluejays/.rss",
    ),
    emoji="🇨🇦",
    narrator_hint=(
        "Write like a passionate Canadian baseball fan who reps the "
        "only MLB team north of the border with national pride."
    ),
)


# ---------------------------------------------------------------------------
# American League Central
# ---------------------------------------------------------------------------

WHITE_SOX = TeamInfo(
    team_id=145,
    full_name="Chicago White Sox",
    short_name="White Sox",
    abbreviation="CWS",
    league_id=103,
    division="AL Central",
    primary_color="#27251F",
    secondary_color="#C4CED4",
    accent_color="#C4CED4",
    team_feed_urls=(
        "https://www.mlbtraderumors.com/chicago-white-sox/feed",
        "https://www.reddit.com/r/whitesox/.rss",
    ),
    emoji="🖤",
    narrator_hint=(
        "Write like a South Side loyalist who's been through the tough "
        "times and keeps showing up. Gallows humor welcome."
    ),
)

GUARDIANS = TeamInfo(
    team_id=114,
    full_name="Cleveland Guardians",
    short_name="Guardians",
    abbreviation="CLE",
    league_id=103,
    division="AL Central",
    primary_color="#00385D",
    secondary_color="#E31937",
    accent_color="#E31937",
    team_feed_urls=(
        "https://www.mlbtraderumors.com/cleveland-guardians/feed",
        "https://www.reddit.com/r/ClevelandGuardians/.rss",
    ),
    emoji="⚔️",
    narrator_hint=(
        "Write like a Cleveland lifer who's seen heartbreak but believes "
        "this core is special. Midwest genuine, no flash."
    ),
)

TIGERS = TeamInfo(
    team_id=116,
    full_name="Detroit Tigers",
    short_name="Tigers",
    abbreviation="DET",
    league_id=103,
    division="AL Central",
    primary_color="#0C2340",
    secondary_color="#FA4616",
    accent_color="#FA4616",
    team_feed_urls=(
        "https://www.mlbtraderumors.com/detroit-tigers/feed",
        "https://www.reddit.com/r/motorcitykitties/.rss",
    ),
    emoji="🐯",
    narrator_hint=(
        "Write like a blue-collar Detroit fan who respects the game's "
        "history and gets fired up about young talent coming through."
    ),
)

ROYALS = TeamInfo(
    team_id=118,
    full_name="Kansas City Royals",
    short_name="Royals",
    abbreviation="KC",
    league_id=103,
    division="AL Central",
    primary_color="#004687",
    secondary_color="#BD9B60",
    accent_color="#BD9B60",
    team_feed_urls=(
        "https://www.mlbtraderumors.com/kansas-city-royals/feed",
        "https://www.reddit.com/r/KCRoyals/.rss",
    ),
    emoji="👑",
    narrator_hint=(
        "Write like a proud KC fan who remembers 2015 fondly and is "
        "hungry to see the Royals back in contention."
    ),
)

TWINS = TeamInfo(
    team_id=142,
    full_name="Minnesota Twins",
    short_name="Twins",
    abbreviation="MIN",
    league_id=103,
    division="AL Central",
    primary_color="#002B5C",
    secondary_color="#D31145",
    accent_color="#D31145",
    team_feed_urls=(
        "https://www.mlbtraderumors.com/minnesota-twins/feed",
        "https://www.reddit.com/r/minnesotatwins/.rss",
    ),
    emoji="🏔️",
    narrator_hint=(
        "Write like a Minnesota nice fan — warm, knowledgeable, maybe a "
        "little self-deprecating about October heartbreak."
    ),
)


# ---------------------------------------------------------------------------
# American League West
# ---------------------------------------------------------------------------

ASTROS = TeamInfo(
    team_id=117,
    full_name="Houston Astros",
    short_name="Astros",
    abbreviation="HOU",
    league_id=103,
    division="AL West",
    primary_color="#002D62",
    secondary_color="#EB6E1F",
    accent_color="#EB6E1F",
    team_feed_urls=(
        "https://www.mlbtraderumors.com/houston-astros/feed",
        "https://www.reddit.com/r/Astros/.rss",
    ),
    emoji="🚀",
    narrator_hint=(
        "Write like a Houston fan who's proud of the dynasty run and "
        "doesn't care what the rest of baseball thinks about it."
    ),
)

ANGELS = TeamInfo(
    team_id=108,
    full_name="Los Angeles Angels",
    short_name="Angels",
    abbreviation="LAA",
    league_id=103,
    division="AL West",
    primary_color="#BA0021",
    secondary_color="#003263",
    accent_color="#003263",
    team_feed_urls=(
        "https://www.mlbtraderumors.com/los-angeles-angels/feed",
        "https://www.reddit.com/r/angelsbaseball/.rss",
    ),
    emoji="😇",
    narrator_hint=(
        "Write like a patient Angels fan who's been through the Trout "
        "years without October success and is ready for a new chapter."
    ),
)

ATHLETICS = TeamInfo(
    team_id=133,
    full_name="Oakland Athletics",
    short_name="Athletics",
    abbreviation="OAK",
    league_id=103,
    division="AL West",
    primary_color="#003831",
    secondary_color="#EFB21E",
    accent_color="#EFB21E",
    team_feed_urls=(
        "https://www.mlbtraderumors.com/oakland-athletics/feed",
        "https://www.reddit.com/r/OaklandAthletics/.rss",
    ),
    emoji="🐘",
    narrator_hint=(
        "Write like a loyal A's fan navigating the relocation era — "
        "passionate about the team, conflicted about ownership."
    ),
)

MARINERS = TeamInfo(
    team_id=136,
    full_name="Seattle Mariners",
    short_name="Mariners",
    abbreviation="SEA",
    league_id=103,
    division="AL West",
    primary_color="#0C2C56",
    secondary_color="#005C5C",
    accent_color="#005C5C",
    team_feed_urls=(
        "https://www.mlbtraderumors.com/seattle-mariners/feed",
        "https://www.reddit.com/r/Mariners/.rss",
    ),
    emoji="🧭",
    narrator_hint=(
        "Write like a PNW baseball fan — chill but deeply invested, "
        "with a dry sense of humor about the drought years."
    ),
)

RANGERS = TeamInfo(
    team_id=140,
    full_name="Texas Rangers",
    short_name="Rangers",
    abbreviation="TEX",
    league_id=103,
    division="AL West",
    primary_color="#003278",
    secondary_color="#C0111F",
    accent_color="#C0111F",
    team_feed_urls=(
        "https://www.mlbtraderumors.com/texas-rangers/feed",
        "https://www.reddit.com/r/TexasRangers/.rss",
    ),
    emoji="🤠",
    narrator_hint=(
        "Write like a Texas fan riding high from the 2023 championship "
        "and expecting the boys to compete every year."
    ),
)


# ---------------------------------------------------------------------------
# National League East
# ---------------------------------------------------------------------------

BRAVES = TeamInfo(
    team_id=144,
    full_name="Atlanta Braves",
    short_name="Braves",
    abbreviation="ATL",
    league_id=104,
    division="NL East",
    primary_color="#13274F",
    secondary_color="#CE1141",
    accent_color="#CE1141",
    team_feed_urls=(
        "https://www.mlbtraderumors.com/atlanta-braves/feed",
        "https://www.reddit.com/r/Braves/.rss",
    ),
    emoji="🪓",
    narrator_hint=(
        "Write like a Braves fan who's been spoiled by the 2021 ring "
        "and a decade of division titles but still wants more."
    ),
)

MARLINS = TeamInfo(
    team_id=146,
    full_name="Miami Marlins",
    short_name="Marlins",
    abbreviation="MIA",
    league_id=104,
    division="NL East",
    primary_color="#00A3E0",
    secondary_color="#EF3340",
    accent_color="#EF3340",
    team_feed_urls=(
        "https://www.mlbtraderumors.com/miami-marlins/feed",
        "https://www.reddit.com/r/letsgofish/.rss",
    ),
    emoji="🐟",
    narrator_hint=(
        "Write like a true Marlins fan — rare, loyal, and waiting "
        "for the front office to stop trading away the good players."
    ),
)

METS = TeamInfo(
    team_id=121,
    full_name="New York Mets",
    short_name="Mets",
    abbreviation="NYM",
    league_id=104,
    division="NL East",
    primary_color="#002D72",
    secondary_color="#FF5910",
    accent_color="#FF5910",
    team_feed_urls=(
        "https://www.mlbtraderumors.com/new-york-mets/feed",
        "https://www.reddit.com/r/NewYorkMets/.rss",
    ),
    emoji="🍎",
    narrator_hint=(
        "Write like a Mets fan who's seen it all — the heartbreak, the "
        "magic, the LOLMets moments — and keeps coming back for more."
    ),
)

PHILLIES = TeamInfo(
    team_id=143,
    full_name="Philadelphia Phillies",
    short_name="Phillies",
    abbreviation="PHI",
    league_id=104,
    division="NL East",
    primary_color="#E81828",
    secondary_color="#002D72",
    accent_color="#002D72",
    team_feed_urls=(
        "https://www.mlbtraderumors.com/philadelphia-phillies/feed",
        "https://www.reddit.com/r/phillies/.rss",
    ),
    emoji="🔔",
    narrator_hint=(
        "Write like a Philly fan — intense, opinionated, loves the "
        "team fiercely, and isn't afraid to call out bad play."
    ),
)

NATIONALS = TeamInfo(
    team_id=120,
    full_name="Washington Nationals",
    short_name="Nationals",
    abbreviation="WSH",
    league_id=104,
    division="NL East",
    primary_color="#AB0003",
    secondary_color="#14225A",
    accent_color="#14225A",
    team_feed_urls=(
        "https://www.mlbtraderumors.com/washington-nationals/feed",
        "https://www.reddit.com/r/Nationals/.rss",
    ),
    emoji="🇺🇸",
    narrator_hint=(
        "Write like a DC fan who cherishes the 2019 title and is "
        "patiently watching the next wave of talent develop."
    ),
)


# ---------------------------------------------------------------------------
# National League Central
# ---------------------------------------------------------------------------

CUBS = TeamInfo(
    team_id=112,
    full_name="Chicago Cubs",
    short_name="Cubs",
    abbreviation="CHC",
    league_id=104,
    division="NL Central",
    primary_color="#0E3386",
    secondary_color="#CC3433",
    accent_color="#CC3433",
    team_feed_urls=(
        "https://www.mlbtraderumors.com/chicago-cubs/feed",
        "https://www.reddit.com/r/CHICubs/.rss",
    ),
    emoji="🐻",
    narrator_hint=(
        "Write like a Wrigley regular who broke the curse in 2016 "
        "and now expects the Cubs to be competitive every year."
    ),
)

REDS = TeamInfo(
    team_id=113,
    full_name="Cincinnati Reds",
    short_name="Reds",
    abbreviation="CIN",
    league_id=104,
    division="NL Central",
    primary_color="#C6011F",
    secondary_color="#000000",
    accent_color="#000000",
    team_feed_urls=(
        "https://www.mlbtraderumors.com/cincinnati-reds/feed",
        "https://www.reddit.com/r/Reds/.rss",
    ),
    emoji="🔴",
    narrator_hint=(
        "Write like a Reds fan who knows the franchise invented "
        "professional baseball and has strong feelings about the payroll."
    ),
)

BREWERS = TeamInfo(
    team_id=158,
    full_name="Milwaukee Brewers",
    short_name="Brewers",
    abbreviation="MIL",
    league_id=104,
    division="NL Central",
    primary_color="#12284B",
    secondary_color="#FFC52F",
    accent_color="#FFC52F",
    team_feed_urls=(
        "https://www.mlbtraderumors.com/milwaukee-brewers/feed",
        "https://www.reddit.com/r/Brewers/.rss",
    ),
    emoji="🍺",
    narrator_hint=(
        "Write like a Wisconsin fan who tailgates at AmFam Field, "
        "appreciates good pitching, and loves an underdog story."
    ),
)

PIRATES = TeamInfo(
    team_id=134,
    full_name="Pittsburgh Pirates",
    short_name="Pirates",
    abbreviation="PIT",
    league_id=104,
    division="NL Central",
    primary_color="#27251F",
    secondary_color="#FDB827",
    accent_color="#FDB827",
    team_feed_urls=(
        "https://www.mlbtraderumors.com/pittsburgh-pirates/feed",
        "https://www.reddit.com/r/buccos/.rss",
    ),
    emoji="🏴‍☠️",
    narrator_hint=(
        "Write like a Pittsburgh fan who loves the city, loves the team, "
        "and is cautiously optimistic about the young talent pipeline."
    ),
)

CARDINALS = TeamInfo(
    team_id=138,
    full_name="St. Louis Cardinals",
    short_name="Cardinals",
    abbreviation="STL",
    league_id=104,
    division="NL Central",
    primary_color="#C41E3A",
    secondary_color="#0C2340",
    accent_color="#0C2340",
    team_feed_urls=(
        "https://www.mlbtraderumors.com/st-louis-cardinals/feed",
        "https://www.reddit.com/r/Cardinals/.rss",
    ),
    emoji="🐦",
    narrator_hint=(
        "Write like a Cardinals fan — knowledgeable, proud of the 'best "
        "fans in baseball' reputation, and expects October every year."
    ),
)


# ---------------------------------------------------------------------------
# National League West
# ---------------------------------------------------------------------------

DIAMONDBACKS = TeamInfo(
    team_id=109,
    full_name="Arizona Diamondbacks",
    short_name="Diamondbacks",
    abbreviation="ARI",
    league_id=104,
    division="NL West",
    primary_color="#A71930",
    secondary_color="#E3D4AD",
    accent_color="#E3D4AD",
    team_feed_urls=(
        "https://www.mlbtraderumors.com/arizona-diamondbacks/feed",
        "https://www.reddit.com/r/azdiamondbacks/.rss",
    ),
    emoji="🐍",
    narrator_hint=(
        "Write like a desert baseball fan who watched the 2023 World "
        "Series run and believes this team is built to compete."
    ),
)

ROCKIES = TeamInfo(
    team_id=115,
    full_name="Colorado Rockies",
    short_name="Rockies",
    abbreviation="COL",
    league_id=104,
    division="NL West",
    primary_color="#33006F",
    secondary_color="#C4CED4",
    accent_color="#C4CED4",
    team_feed_urls=(
        "https://www.mlbtraderumors.com/colorado-rockies/feed",
        "https://www.reddit.com/r/ColoradoRockies/.rss",
    ),
    emoji="⛰️",
    narrator_hint=(
        "Write like a Rockies fan who loves Coors Field, knows the "
        "altitude changes everything, and stays loyal through the rebuild."
    ),
)

DODGERS = TeamInfo(
    team_id=119,
    full_name="Los Angeles Dodgers",
    short_name="Dodgers",
    abbreviation="LAD",
    league_id=104,
    division="NL West",
    primary_color="#005A9C",
    secondary_color="#EF3E42",
    accent_color="#EF3E42",
    team_feed_urls=(
        "https://www.mlbtraderumors.com/los-angeles-dodgers/feed",
        "https://www.reddit.com/r/Dodgers/.rss",
    ),
    emoji="💙",
    narrator_hint=(
        "Write like an LA fan who expects to win it all every year, "
        "has opinions on every trade deadline move, and bleeds Dodger blue."
    ),
)

PADRES = TeamInfo(
    team_id=135,
    full_name="San Diego Padres",
    short_name="Padres",
    abbreviation="SD",
    league_id=104,
    division="NL West",
    primary_color="#2F241D",
    secondary_color="#FFC425",
    accent_color="#FFC425",
    team_feed_urls=(
        "https://www.mlbtraderumors.com/san-diego-padres/feed",
        "https://www.reddit.com/r/Padres/.rss",
    ),
    emoji="🤎",
    narrator_hint=(
        "Write like a San Diego fan who loves the brown-and-gold identity, "
        "the Petco Park vibes, and wants to beat the Dodgers more than anything."
    ),
)

GIANTS = TeamInfo(
    team_id=137,
    full_name="San Francisco Giants",
    short_name="Giants",
    abbreviation="SF",
    league_id=104,
    division="NL West",
    primary_color="#FD5A1E",
    secondary_color="#27251F",
    accent_color="#27251F",
    team_feed_urls=(
        "https://www.mlbtraderumors.com/san-francisco-giants/feed",
        "https://www.reddit.com/r/SFGiants/.rss",
    ),
    emoji="🧡",
    narrator_hint=(
        "Write like a Bay Area fan who watched the dynasty years, "
        "appreciates smart baseball, and has strong feelings about the DH."
    ),
)


# ---------------------------------------------------------------------------
# Registry lookup
# ---------------------------------------------------------------------------

# Master list of all teams — order matches the divisions above
ALL_TEAMS: tuple[TeamInfo, ...] = (
    # AL East
    ORIOLES,
    RED_SOX,
    YANKEES,
    RAYS,
    BLUE_JAYS,
    # AL Central
    WHITE_SOX,
    GUARDIANS,
    TIGERS,
    ROYALS,
    TWINS,
    # AL West
    ASTROS,
    ANGELS,
    ATHLETICS,
    MARINERS,
    RANGERS,
    # NL East
    BRAVES,
    MARLINS,
    METS,
    PHILLIES,
    NATIONALS,
    # NL Central
    CUBS,
    REDS,
    BREWERS,
    PIRATES,
    CARDINALS,
    # NL West
    DIAMONDBACKS,
    ROCKIES,
    DODGERS,
    PADRES,
    GIANTS,
)

# Build lookup indexes — case-insensitive matching
_BY_FULL_NAME: dict[str, TeamInfo] = {t.full_name.lower(): t for t in ALL_TEAMS}
_BY_SHORT_NAME: dict[str, TeamInfo] = {t.short_name.lower(): t for t in ALL_TEAMS}
_BY_ABBREVIATION: dict[str, TeamInfo] = {t.abbreviation.lower(): t for t in ALL_TEAMS}
_BY_ID: dict[int, TeamInfo] = {t.team_id: t for t in ALL_TEAMS}

# Division ordering for display
DIVISION_ORDER = (
    "AL East",
    "AL Central",
    "AL West",
    "NL East",
    "NL Central",
    "NL West",
)


def get_team(identifier: str | int) -> TeamInfo | None:
    """
    Look up a team by name, abbreviation, or ID.

    Accepts any of:
        "Yankees"              -> short name
        "NYY"                  -> abbreviation
        "New York Yankees"     -> full name
        147                    -> MLB Stats API ID

    Returns None if no match found.
    """
    if isinstance(identifier, int):
        return _BY_ID.get(identifier)

    key = identifier.strip().lower()

    # Try each index in order: abbreviation first (fastest), then names
    return _BY_ABBREVIATION.get(key) or _BY_SHORT_NAME.get(key) or _BY_FULL_NAME.get(key)


def list_teams() -> dict[str, list[TeamInfo]]:
    """Return all teams grouped by division, in display order."""
    grouped: dict[str, list[TeamInfo]] = {div: [] for div in DIVISION_ORDER}
    for team in ALL_TEAMS:
        grouped[team.division].append(team)
    return grouped


def get_team_or_raise(identifier: str | int) -> TeamInfo:
    """
    Like get_team(), but raises ValueError with a helpful message if not found.
    """
    team = get_team(identifier)
    if team is not None:
        return team

    # Build a helpful error message with suggestions
    available = ", ".join(t.short_name for t in ALL_TEAMS)
    raise ValueError(
        f"Unknown team: '{identifier}'. "
        f"Available teams: {available}. "
        f"You can use the full name, short name, or abbreviation."
    )
