"""
Preview rendering for the email template.

Writes the rendered email to local HTML files so it can be inspected in a
browser without sending anything. The gmail-dark variant reproduces the DOM
Gmail builds around an email (a <u> element followed by a .body-classed
wrapper) so the ADR-0002 blend-mode defenses activate in a normal browser.
"""

from importlib import resources


def load_sample_digest() -> str:
    """Return the canned sample digest markdown shipped with the package."""
    sample_file = resources.files("mlb_digest").joinpath("sample_digest.md")
    return sample_file.read_text(encoding="utf-8")
