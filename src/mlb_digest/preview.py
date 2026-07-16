"""
Sample data for email previews.

Loads the canned sample digest shipped with the package, wraps the rendered
HTML in a Gmail-like DOM for dark-mode previews, and writes both preview
files to disk. The gmail-dark harness reproduces the DOM Gmail builds around
an email (a <u> element followed by a .body-classed wrapper) so the ADR-0002
blend-mode defenses activate in a normal browser.
"""

import re
from importlib import resources
from pathlib import Path

from mlb_digest.config import Config
from mlb_digest.templates import GMAIL_BLEND_CSS, render_email_html

GMAIL_DARK_PAGE_BG = "#121212"


def load_sample_digest() -> str:
    """Return the canned sample digest markdown shipped with the package."""
    sample_file = resources.files("mlb_digest").joinpath("sample_digest.md")
    return sample_file.read_text(encoding="utf-8")


def wrap_in_gmail_dark_harness(email_html: str) -> str:
    """Rebuild the email inside a Gmail-like DOM so the blend-mode CSS activates."""
    match = re.search(r'<body class="body"(.*?)>(.*)</body>', email_html, flags=re.DOTALL)
    if match is None:
        raise ValueError('email HTML has no <body class="body"> element')

    body_attrs = match.group(1)
    body_content = match.group(2)
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>"
        '<meta charset="utf-8">'
        f"{GMAIL_BLEND_CSS}"
        "</head>\n"
        f'<body style="margin:0; padding:0; background:{GMAIL_DARK_PAGE_BG};">\n'
        "<u></u>\n"
        f'<div class="body"{body_attrs}>\n'
        f"{body_content}\n"
        "</div>\n"
        "</body>\n"
        "</html>"
    )


def write_preview_files(config: Config, output_dir: Path) -> list[Path]:
    """Render the sample digest and write plain + gmail-dark preview files."""
    sample_md = load_sample_digest()
    email_html = render_email_html(
        sample_md,
        team_name=config.full_team_name,
        primary_color=config.team_colors.get("primary", "#333333"),
        accent_color=config.team_colors.get("accent", "#cc0000"),
        emoji=config.team_emoji,
    )
    harness_html = wrap_in_gmail_dark_harness(email_html)

    output_dir.mkdir(parents=True, exist_ok=True)
    plain_path = output_dir / "preview.html"
    dark_path = output_dir / "preview-gmail-dark.html"
    plain_path.write_text(email_html, encoding="utf-8")
    dark_path.write_text(harness_html, encoding="utf-8")
    return [plain_path, dark_path]
