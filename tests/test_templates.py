# tests/test_templates.py
from mlb_digest.templates import render_email_html, render_email_text


def test_render_email_html_converts_markdown_headers():
    md = "## Hello World\n\nSome content here."

    html = render_email_html(md, primary_color="#13274F", accent_color="#CE1141")

    assert "Hello World" in html
    assert "Some content" in html
    assert "<html" in html.lower()


def test_render_email_html_has_inline_styles_not_style_block():
    md = "## Test Section\n\nContent here."

    html = render_email_html(md, primary_color="#13274F", accent_color="#CE1141")

    assert "#13274F" in html
    assert "Test Section" in html
    assert "<style>" not in html


def test_render_email_html_uses_dark_background():
    md = "## Test\n\nContent."

    html = render_email_html(md, primary_color="#13274F", accent_color="#CE1141")

    assert "#0d0d1a" in html  # page background
    assert "#1a1a2e" in html  # content area


def test_render_email_html_includes_dugout_digest_branding():
    md = "## Test\n\nContent."

    html = render_email_html(md, primary_color="#13274F", accent_color="#CE1141")

    assert "DUGOUT DIGEST" in html


def test_render_email_html_includes_footer():
    md = "## Test\n\nContent."

    html = render_email_html(md, primary_color="#13274F", accent_color="#CE1141")

    assert "MLB Stats API" in html


def test_render_email_html_handles_links():
    md = "Check out [this article](https://example.com)."

    html = render_email_html(md, primary_color="#13274F", accent_color="#CE1141")

    assert 'href="https://example.com"' in html
    assert "this article" in html
    assert "#7ea8e8" in html  # link color on dark


def test_render_email_html_handles_tables():
    md = "| Team | W | L |\n|------|---|---|\n| Braves | 5 | 2 |"

    html = render_email_html(md, primary_color="#13274F", accent_color="#CE1141")

    assert "<table" in html.lower()
    assert "Braves" in html


def test_render_email_html_body_text_is_light_on_dark():
    md = "## Section\n\nSome paragraph text here."

    html = render_email_html(md, primary_color="#13274F", accent_color="#CE1141")

    assert "#c8c8d8" in html  # light body text color


def test_render_email_html_includes_team_name_in_header():
    md = "## Test\n\nContent."

    html = render_email_html(
        md,
        team_name="Atlanta Braves",
        primary_color="#13274F",
        accent_color="#CE1141",
        secondary_color="#CE1141",
        emoji="\U0001fa93",
    )

    assert "Atlanta Braves" in html
    assert "\U0001fa93" in html


def test_render_email_html_has_badge_with_first_letter():
    md = "## Test\n\nContent."

    html = render_email_html(
        md,
        team_name="Atlanta Braves",
        primary_color="#13274F",
        accent_color="#CE1141",
    )

    # Badge should contain "A" for Atlanta Braves
    assert ">A</span>" in html


def test_render_email_html_accent_stripe():
    md = "## Test\n\nContent."

    html = render_email_html(md, primary_color="#13274F", accent_color="#CE1141")

    # Accent color used for top stripe and footer stripe
    assert "#CE1141" in html


def test_render_email_text_strips_markdown():
    md = "## Hello\n\nSome **bold** content.\n\n- Item 1\n- Item 2"

    text = render_email_text(md)

    assert "Hello" in text
    assert "Item 1" in text
    assert "MLB Stats API" in text
    assert "Dugout Digest" in text


def test_render_email_text_includes_team_name():
    md = "## Hello\n\nSome content."

    text = render_email_text(md, team_name="Atlanta Braves")

    assert "Atlanta Braves" in text
