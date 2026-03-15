import json
import logging
from collections import OrderedDict
from dataclasses import asdict

import anthropic

from mlb_digest.feeds import Article
from mlb_digest.mlb_api import DivisionStandings, GameResult, UpcomingGame

logger = logging.getLogger(__name__)

SYSTEM_PROMPT_TEMPLATE = (
    "You are a knowledgeable but casual {team_name} fan writing a morning "
    "email digest for a friend who doesn't have time to watch every game. "
    "You are conversational, not a sports anchor. You reference specific "
    "stats and facts from the data provided.\n"
    "\n"
    "CRITICAL RULES:\n"
    "- ONLY reference facts, stats, and events present in the provided data.\n"
    "- NEVER invent plays, moments, or descriptions not supported by the data.\n"
    "- For headlines and storylines, use the RSS article titles and summaries "
    "provided. Summarize what the articles say - do NOT generate storylines "
    "from imagination.\n"
    "- If the data shows a player hit 2-4 with a HR and 3 RBI, you can say "
    '"went 2-for-4 with a homer and 3 ribbies" - but do NOT invent the '
    'situation (e.g., "a clutch 2-run shot in the 8th") unless '
    "inning/situation data is in the input.\n"
    "- For player descriptions in catchup reports, derive from stats only: "
    '"leads the team in HRs" not "has a smooth swing."\n'
    "- When in doubt, state the numbers. Never embellish.\n"
    "\n"
    "Output format: Return the digest as markdown. Use ## headers for each "
    "section. Output the sections in the order they appear in the input data."
)


class NarratorError(Exception):
    pass


def build_system_prompt(team_name: str) -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(team_name=team_name)


def _articles_to_dicts(articles: list[Article]) -> list[dict]:
    return [
        {"title": a.title, "summary": a.summary, "link": a.link, "source": a.source}
        for a in articles
    ]


def build_prompt(
    team_name: str,
    yesterday_game: GameResult | None,
    today_game: UpcomingGame | None,
    standings: list[DivisionStandings],
    team_articles: list[Article],
    mlb_articles: list[Article],
    top_players: dict | None,
    catchup: bool = False,
    roster_data: list[dict] | None = None,
) -> str:
    # OrderedDict to guarantee section ordering in JSON output
    sections: OrderedDict[str, dict] = OrderedDict()

    if mlb_articles:
        sections["around_the_league"] = {
            "instruction": (
                "Summarize these MLB headlines into a few bullet points. "
                "Use the article titles and summaries - do not invent storylines."
            ),
            "articles": _articles_to_dicts(mlb_articles),
        }

    if yesterday_game:
        sections["last_nights_game"] = {
            "instruction": (
                f"Recap {team_name}'s game from last night. "
                "Narrate the stats conversationally. "
                "Do not invent plays not in the data."
            ),
            "data": asdict(yesterday_game),
        }

    if today_game:
        sections["todays_game"] = {
            "instruction": (
                f"Preview {team_name}'s game today. "
                "Mention the opponent, time, and starting pitchers."
            ),
            "data": asdict(today_game),
        }

    if team_articles:
        sections["storylines"] = {
            "instruction": (
                f"Write {team_name} storylines based on these articles. "
                "Summarize what the articles say. "
                "Supplement with standings data if relevant."
            ),
            "articles": _articles_to_dicts(team_articles),
        }

    if standings:
        standings_section: dict = {
            "instruction": f"Show the division standings. Highlight {team_name}'s position.",
            "data": [asdict(d) for d in standings],
        }
        if top_players:
            standings_section["top_players"] = top_players
            standings_section["instruction"] += (
                f" Include top hitters (by AVG) and top pitchers (by ERA) for {team_name}."
            )
        sections["standings_snapshot"] = standings_section

    if catchup and roster_data:
        sections["roster"] = {
            "instruction": (
                f"Introduce the {team_name} roster. "
                "Describe each player based on their stats - "
                "do not invent scouting descriptions."
            ),
            "data": roster_data,
        }

    if team_articles or mlb_articles:
        all_for_reading = team_articles[:2] + mlb_articles[:2]
        sections["worth_reading"] = {
            "instruction": (
                "List these articles with title, source, link, and a one-line summary each."
            ),
            "articles": _articles_to_dicts(all_for_reading),
        }

    return json.dumps(sections, indent=2)


def generate_narrative(
    prompt: str,
    system_prompt: str,
    api_key: str,
    model: str,
    temperature: float,
) -> str:
    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            temperature=temperature,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as e:
        raise NarratorError(f"Anthropic API call failed: {e}") from e

    if not response.content:
        raise NarratorError("Anthropic returned empty content")

    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    logger.info("Token usage - input: %d, output: %d", input_tokens, output_tokens)

    block = response.content[0]
    if not hasattr(block, "text"):
        raise NarratorError(f"Unexpected response block type: {type(block)}")
    return block.text  # type: ignore[union-attr]
