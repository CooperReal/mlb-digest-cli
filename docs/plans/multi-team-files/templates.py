"""
Email template rendering.

Converts Claude's markdown narrative into team-branded HTML and plain text emails.
Every team gets a unique look driven by their color palette from the registry.

The HTML template is a single-file, inline-styled design that works across
Gmail, Apple Mail, Outlook, and mobile clients.
"""

import re

import markdown


def _apply_inline_styles(html: str, primary_color: str, accent_color: str) -> str:
    """Replace tags with inline-styled versions. Email clients strip <style> blocks."""

    # Headings — primary color with accent underline
    html = re.sub(
        r"<h1(.*?)>",
        rf'<h1\1 style="color: {primary_color}; margin-top: 20px;">',
        html,
    )
    html = re.sub(
        r"<h2(.*?)>",
        rf'<h2\1 style="color: {primary_color}; '
        rf"border-bottom: 2px solid {accent_color}; "
        r'padding-bottom: 6px; margin-top: 30px; margin-bottom: 12px;">',
        html,
    )
    html = re.sub(
        r"<h3(.*?)>",
        rf'<h3\1 style="color: {primary_color}; margin-top: 15px;">',
        html,
    )

    # Links — accent color
    html = re.sub(
        r"<a ",
        f'<a style="color: {accent_color}; text-decoration: underline;" ',
        html,
    )

    # Tables — clean, scannable standings
    html = re.sub(
        r"<table(.*?)>",
        r'<table\1 style="border-collapse: collapse; width: 100%; margin: 10px 0;">',
        html,
    )
    html = re.sub(
        r"<th(.*?)>",
        rf'<th\1 style="background-color: {primary_color}; '
        r"color: #ffffff; padding: 10px 12px; "
        r'text-align: left; border: 1px solid #ddd; font-size: 13px; text-transform: uppercase;">',
        html,
    )
    html = re.sub(
        r"<td(.*?)>",
        r'<td\1 style="padding: 10px 12px; border: 1px solid #eee; font-size: 14px;">',
        html,
    )

    # Paragraphs — consistent spacing
    html = re.sub(
        r"<p(.*?)>",
        r'<p\1 style="margin: 0 0 14px 0; line-height: 1.65;">',
        html,
    )

    # Lists — readable spacing
    html = re.sub(
        r"<li(.*?)>",
        r'<li\1 style="margin-bottom: 8px; line-height: 1.5;">',
        html,
    )

    return html


def render_email_html(
    md_content: str,
    team_name: str = "MLB Digest",
    primary_color: str = "#333333",
    accent_color: str = "#cc0000",
    secondary_color: str = "#666666",
    emoji: str = "⚾",
) -> str:
    """
    Render markdown content into a team-branded HTML email.

    The design uses the team's colors for:
    - Header banner background (primary)
    - Section dividers (accent)
    - Links (accent)
    - Table headers (primary)
    - Footer accent line (accent)
    """
    body_html = markdown.markdown(md_content, extensions=["tables"])
    body_html = _apply_inline_styles(body_html, primary_color, accent_color)

    # All styles are inline — email clients strip <style> blocks
    body_style = (
        "margin: 0; padding: 0; "
        "font-family: -apple-system, BlinkMacSystemFont, "
        "'Segoe UI', Roboto, Helvetica, Arial, sans-serif; "
        "background-color: #f5f5f5; "
        "-webkit-font-smoothing: antialiased;"
    )
    wrapper_style = (
        "max-width: 600px; margin: 0 auto; "
        "background-color: #ffffff; "
        "border-radius: 8px; overflow: hidden; "
        "box-shadow: 0 2px 8px rgba(0,0,0,0.08);"
    )

    # Team-colored header banner
    header_style = (
        f"background-color: {primary_color}; "
        "color: #ffffff; "
        "padding: 24px 30px; "
        "text-align: left;"
    )
    title_style = (
        "margin: 0; "
        "font-size: 22px; "
        "font-weight: 700; "
        "color: #ffffff; "
        "letter-spacing: 0.5px;"
    )
    subtitle_style = (
        "margin: 4px 0 0 0; "
        "font-size: 13px; "
        f"color: {accent_color}; "
        "opacity: 0.9; "
        "font-weight: 400;"
    )

    # Content area
    content_style = (
        "padding: 24px 30px 20px; "
        "color: #333333; "
        "line-height: 1.65; "
        "font-size: 15px;"
    )

    # Footer with team accent
    footer_style = (
        f"border-top: 3px solid {accent_color}; "
        "background-color: #fafafa; "
        "padding: 16px 30px; "
        "font-size: 12px; "
        "color: #999999; "
        "line-height: 1.5;"
    )

    return (
        "<!DOCTYPE html>\n"
        "<html>\n"
        '<head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        "</head>\n"
        f'<body style="{body_style}">\n'
        f'  <div style="padding: 20px 10px;">\n'
        f'  <div style="{wrapper_style}">\n'
        # Header
        f'    <div style="{header_style}">\n'
        f'      <div style="{title_style}">{emoji} {team_name}</div>\n'
        f'      <div style="{subtitle_style}">Your Morning Digest</div>\n'
        "    </div>\n"
        # Content
        f'    <div style="{content_style}">\n'
        f"      {body_html}\n"
        "    </div>\n"
        # Footer
        f'    <div style="{footer_style}">\n'
        f"      {emoji} Powered by MLB Stats API &amp; Claude &middot; "
        "Data from RSS feeds<br>\n"
        '      <span style="font-size: 11px; color: #bbbbbb;">'
        "Reply to this email with feedback</span>\n"
        "    </div>\n"
        "  </div>\n"
        "  </div>\n"
        "</body>\n"
        "</html>"
    )


def render_email_text(md_content: str, team_name: str = "MLB Digest") -> str:
    """Render markdown content as plain text email."""
    text = md_content

    # Strip markdown formatting for plain text
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1 (\2)", text)
    text = re.sub(r"^#{1,3} ", "", text, flags=re.MULTILINE)

    text += (
        f"\n\n---\n"
        f"{team_name} Digest\n"
        f"Sources: MLB Stats API, RSS feeds. Narrated by Claude.\n"
    )

    return text.strip()
