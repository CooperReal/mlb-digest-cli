# tests/test_templates.py
from mlb_digest.templates import render_email_html, render_email_text


def test_render_email_html_converts_markdown_headers():
    md = "## Hello World\n\nSome content here."

    html = render_email_html(md, primary_color="#13274F", accent_color="#CE1141")

    assert "Hello World" in html
    assert "Some content" in html
    assert "<html" in html.lower()


def test_render_email_html_has_gmail_blend_mode_css():
    md = "## Test Section\n\nContent here."

    html = render_email_html(md, primary_color="#13274F", accent_color="#CE1141")

    assert "gfix-screen" in html
    assert "gfix-diff" in html
    assert "mix-blend-mode" in html
    assert 'class="body"' in html


def test_render_email_html_uses_dark_background():
    md = "## Test\n\nContent."

    html = render_email_html(md, primary_color="#13274F", accent_color="#CE1141")

    assert "#0d0d1a" in html
    assert "#1a1a2e" in html


def test_render_email_html_uses_linear_gradient_backgrounds():
    md = "## Test\n\nContent."

    html = render_email_html(md, primary_color="#13274F", accent_color="#CE1141")

    assert "linear-gradient(#0d0d1a,#0d0d1a)" in html
    assert "linear-gradient(#13274F,#13274F)" in html


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
    assert "#8cb8ff" in html


def test_render_email_html_handles_tables():
    md = "| Team | W | L |\n|------|---|---|\n| Braves | 5 | 2 |"

    html = render_email_html(md, primary_color="#13274F", accent_color="#CE1141")

    assert "<table" in html.lower()
    assert "Braves" in html


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

    assert ">A</span>" in html


def test_render_email_html_blend_wraps_body_text_not_badge():
    md = "## Section\n\nBody text here."

    html = render_email_html(
        md,
        team_name="Atlanta Braves",
        primary_color="#13274F",
        accent_color="#CE1141",
    )

    # Badge letter should NOT be inside blend wrapper
    assert 'line-height:42px;">A</span>' in html
    # Body text SHOULD be inside blend wrapper
    assert "gfix-screen" in html
    assert "gfix-diff" in html


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
