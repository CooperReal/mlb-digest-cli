"""
Sample data for email previews.

Loads the canned sample digest shipped with the package, used for
email previews and test sends. The gmail-dark harness reproduces the DOM
Gmail builds around an email (a <u> element followed by a .body-classed
wrapper) so the ADR-0002 blend-mode defenses activate in a normal browser.
"""

import re
from importlib import resources

from mlb_digest.templates import GMAIL_BLEND_CSS

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
