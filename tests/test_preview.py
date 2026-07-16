import pytest

from mlb_digest.preview import load_sample_digest, wrap_in_gmail_dark_harness
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
