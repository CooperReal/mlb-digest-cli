import json
import logging
import sys
from dataclasses import asdict

import click

from mlb_digest.config import load_config
from mlb_digest.emailer import send_email
from mlb_digest.feeds import fetch_articles, select_articles
from mlb_digest.mlb_api import (
    get_active_roster,
    get_standings,
    get_today_game,
    get_top_players,
    get_yesterday_game,
)
from mlb_digest.narrator import (
    NarratorError,
    build_prompt,
    build_system_prompt,
    generate_narrative,
)
from mlb_digest.templates import render_email_html, render_email_text

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.option(
    "--catchup",
    is_flag=True,
    help="Include roster, season overview, rivals, playoff picture.",
)
@click.option("--no-email", is_flag=True, help="Print digest to stdout instead of emailing.")
@click.option("--dry-run", is_flag=True, help="Print raw data without calling Sonnet or emailing.")
@click.option(
    "--smoke-test",
    is_flag=True,
    help="Run full pipeline with minimal tokens (Haiku, 50 max_tokens).",
)
@click.pass_context
def main(
    ctx: click.Context,
    catchup: bool,
    no_email: bool,
    dry_run: bool,
    smoke_test: bool,
) -> None:
    """MLB Digest - daily team digest via email."""
    if ctx.invoked_subcommand is not None:
        return

    config = load_config()
    config.validate_secrets()
    exit_code = 0

    # Fetch data
    yesterday_game = get_yesterday_game(config.team_id)
    today_game = get_today_game(config.team_id, config.team_name)
    standings = get_standings(config.league_id)

    team_articles_raw = fetch_articles(config.team_feed_urls, source_type="team")
    mlb_articles_raw = fetch_articles(config.mlb_feed_urls, source_type="mlb")
    selected = select_articles(team_articles_raw, mlb_articles_raw)
    team_articles = selected.team
    mlb_articles = selected.mlb

    # Fetch roster for top players (always) and full roster (catchup only)
    roster = get_active_roster(config.team_id)
    top_players = get_top_players(roster) if roster else None

    roster_data = None
    if catchup and roster:
        roster_data = [asdict(p) for p in roster]

    # Dry run - dump raw data and exit
    if dry_run:
        data = {
            "team": config.full_team_name,
            "division": config.division,
            "yesterday_game": str(yesterday_game),
            "today_game": str(today_game),
            "standings": str(standings),
            "team_articles": [a.title for a in team_articles],
            "mlb_articles": [a.title for a in mlb_articles],
            "roster_count": len(roster),
            "top_players": top_players,
        }
        click.echo(json.dumps(data, indent=2, default=str))
        return

    # Build prompt and generate narrative
    prompt = build_prompt(
        team_name=config.team_name,
        yesterday_game=yesterday_game,
        today_game=today_game,
        standings=standings,
        team_articles=team_articles,
        mlb_articles=mlb_articles,
        top_players=top_players,
        catchup=catchup,
        roster_data=roster_data,
    )

    system_prompt = build_system_prompt(
        team_name=config.team_name,
        full_team_name=config.full_team_name,
        division=config.division,
        narrator_hint=config.narrator_hint,
    )

    narrator_model = config.narrator_model
    narrator_max_tokens = 4096
    if smoke_test:
        narrator_model = "claude-haiku-4-5-20251001"
        narrator_max_tokens = 50

    try:
        narrative = generate_narrative(
            prompt=prompt,
            system_prompt=system_prompt,
            api_key=config.anthropic_api_key,
            model=narrator_model,
            temperature=config.narrator_temperature,
            max_tokens=narrator_max_tokens,
        )
    except NarratorError:
        logger.error("Narrator failed - sending raw data fallback")
        narrative = (
            f"# {config.team_name} Daily\n\n"
            f"*AI narrative unavailable - here are the raw numbers.*\n\n{prompt}"
        )
        exit_code = 1

    # No-email - print and exit
    if no_email:
        click.echo(narrative)
        ctx.exit(exit_code)
        return

    # Render and send email
    html_body = render_email_html(
        narrative,
        team_name=config.full_team_name,
        primary_color=config.team_colors.get("primary", "#333333"),
        accent_color=config.team_colors.get("accent", "#cc0000"),
        secondary_color=config.team_colors.get("secondary", "#666666"),
        emoji=config.team_emoji,
    )
    text_body = render_email_text(narrative, team_name=config.full_team_name)
    subject = config.format_subject(catchup=catchup)

    try:
        send_email(
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            sender=config.gmail_address,
            password=config.gmail_app_password,
            recipients=config.email_recipients,
            transport=config.email_transport,
        )
    except Exception:
        logger.exception("Failed to send email - printing to stdout")
        click.echo(narrative)
        ctx.exit(2)
        return

    ctx.exit(exit_code)


@main.command()
def test_email() -> None:
    """Send a test email to verify Gmail setup."""
    config = load_config()
    config.validate_secrets()

    try:
        send_email(
            subject="MLB Digest - Test Email",
            html_body=(
                "<html><body>"
                "<h1>Hello from MLB Digest!</h1>"
                f"<p>Your email setup works. Configured for: {config.full_team_name}</p>"
                "</body></html>"
            ),
            text_body=(
                f"Hello from MLB Digest! Your email setup works. Team: {config.full_team_name}"
            ),
            sender=config.gmail_address,
            password=config.gmail_app_password,
            recipients=config.email_recipients,
            transport=config.email_transport,
        )
        click.echo("Test email sent successfully!")
    except Exception as e:
        logger.exception("Test email failed")
        click.echo(f"Test email failed: {e}", err=True)
        raise SystemExit(1) from e


@main.command("list-teams")
@click.option("--json-output", "as_json", is_flag=True, help="Output as JSON.")
def list_teams_cmd(as_json: bool) -> None:
    """Show all 30 available MLB teams."""
    from mlb_digest.teams_registry import list_teams  # lazy: avoid circular + only needed here

    grouped = list_teams()

    if as_json:
        output = {}
        for division, teams in grouped.items():
            output[division] = [
                {
                    "abbreviation": t.abbreviation,
                    "short_name": t.short_name,
                    "full_name": t.full_name,
                    "team_id": t.team_id,
                    "primary_color": t.primary_color,
                    "accent_color": t.accent_color,
                }
                for t in teams
            ]
        click.echo(json.dumps(output, indent=2))
        return

    for division, teams in grouped.items():
        click.echo(f"\n  {division}")
        click.echo(f"  {'─' * 50}")
        for t in teams:
            click.echo(f"    {t.abbreviation:<5} {t.full_name:<28} (ID: {t.team_id})")
    click.echo()
