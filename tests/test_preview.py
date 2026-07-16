from unittest.mock import MagicMock

import pytest

from mlb_digest.preview import (
    load_sample_digest,
    wrap_in_gmail_dark_harness,
    write_preview_files,
)
from mlb_digest.templates import render_email_html


def test_load_sample_digest_contains_all_template_elements():
    sample = load_sample_digest()

    assert "\n## " in sample
    assert "\n### " in sample
    assert "**" in sample
    assert "](http" in sample
    assert "| Team |" in sample
    assert "\n- " in sample
    assert "\n---\n" in sample


def test_gmail_dark_harness_wraps_body_in_gmail_dom():
    email_html = render_email_html("## HELLO\n\nWorld.")

    harness = wrap_in_gmail_dark_harness(email_html)

    assert "<u></u>" in harness
    assert '<div class="body"' in harness
    assert "#121212" in harness
    assert "World." in harness


def test_gmail_dark_harness_keeps_blend_mode_css():
    email_html = render_email_html("Hello.")

    harness = wrap_in_gmail_dark_harness(email_html)

    assert "mix-blend-mode:screen" in harness
    assert "mix-blend-mode:difference" in harness


def test_gmail_dark_harness_rejects_html_without_body_class():
    with pytest.raises(ValueError, match="no <body"):
        wrap_in_gmail_dark_harness("<html><body>plain</body></html>")


def test_write_preview_files_creates_plain_and_dark_files(tmp_path):
    config = MagicMock()
    config.full_team_name = "Atlanta Braves"
    config.team_colors = {"primary": "#13274F", "accent": "#CE1141"}
    config.team_emoji = "⚾"

    written = write_preview_files(config, tmp_path)

    plain_file = tmp_path / "preview.html"
    dark_file = tmp_path / "preview-gmail-dark.html"
    assert written == [plain_file, dark_file]
    assert "Atlanta Braves" in plain_file.read_text(encoding="utf-8")
    assert "<u></u>" in dark_file.read_text(encoding="utf-8")
