# src/mlb_digest/templates.py
import re

import markdown


def _apply_inline_styles(html: str, primary_color: str, accent_color: str) -> str:
    """Replace tags with inline-styled versions. Email clients strip <style> blocks."""
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
    html = re.sub(
        r"<p(.*?)>",
        r'<p\1 style="margin: 0 0 14px 0; line-height: 1.65;">',
        html,
    )
    html = re.sub(
        r"<li(.*?)>",
        r'<li\1 style="margin-bottom: 8px; line-height: 1.5;">',
        html,
    )
    html = re.sub(
        r"<a ",
        f'<a style="color: {accent_color}; text-decoration: underline;" ',
        html,
    )
    html = re.sub(
        r"<table(.*?)>",
        r'<table\1 style="border-collapse: collapse; width: 100%; margin: 10px 0;">',
        html,
    )
    html = re.sub(
        r"<th(.*?)>",
        rf'<th\1 style="background-color: {primary_color}; '
        r"color: #ffffff; padding: 8px; "
        r"text-align: left; border: 1px solid #ddd; "
        r'font-size: 13px; text-transform: uppercase;">',
        html,
    )
    html = re.sub(
        r"<td(.*?)>",
        r'<td\1 style="padding: 10px 12px; font-size: 14px; border: 1px solid #eee;">',
        html,
    )
    return html


def render_email_html(
    md_content: str,
    team_name: str = "MLB Digest",
    primary_color: str = "#333333",
    accent_color: str = "#cc0000",
    secondary_color: str = "#666666",
    emoji: str = "\u26be",
) -> str:
    body_html = markdown.markdown(md_content, extensions=["tables"])
    body_html = _apply_inline_styles(body_html, primary_color, accent_color)

    body_style = (
        "margin: 0; padding: 0; "
        "font-family: -apple-system, BlinkMacSystemFont, "
        "'Segoe UI', Roboto, sans-serif; "
        "background-color: #f5f5f5;"
    )
    outer_padding_style = "padding: 20px 0;"
    wrapper_style = (
        "max-width: 600px; margin: 0 auto; background-color: #ffffff; "
        "padding: 0; border-radius: 8px; "
        "box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);"
    )
    header_style = (
        f"background-color: {primary_color}; color: #ffffff; "
        "padding: 20px 30px; border-radius: 8px 8px 0 0;"
    )
    h1_style = "margin: 0; font-size: 24px; color: #ffffff;"
    subtitle_style = (
        f"margin: 6px 0 0 0; font-size: 13px; color: {accent_color}; "
        "font-weight: normal; letter-spacing: 0.5px;"
    )
    content_style = (
        f"padding: 24px 30px 20px; color: {secondary_color}; "
        "line-height: 1.6; font-size: 15px;"
    )
    footer_style = (
        f"background-color: #fafafa; padding: 15px 30px; font-size: 12px; "
        f"color: #888888; border-top: 3px solid {accent_color}; "
        "border-radius: 0 0 8px 8px;"
    )

    return (
        "<!DOCTYPE html>\n"
        "<html>\n"
        "<head>"
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        "</head>\n"
        f'<body style="{body_style}">\n'
        f'  <div style="{outer_padding_style}">\n'
        f'    <div style="{wrapper_style}">\n'
        f'      <div style="{header_style}">\n'
        f'        <h1 style="{h1_style}">{emoji} {team_name}</h1>\n'
        f'        <p style="{subtitle_style}">Your Morning Digest</p>\n'
        "      </div>\n"
        f'      <div style="{content_style}">\n'
        f"        {body_html}\n"
        "      </div>\n"
        f'      <div style="{footer_style}">\n'
        f"        {emoji} Powered by MLB Stats API &amp; Claude<br>\n"
        "        Questions or feedback? Just reply to this email.\n"
        "      </div>\n"
        "    </div>\n"
        "  </div>\n"
        "</body>\n"
        "</html>"
    )


def render_email_text(md_content: str, team_name: str = "MLB Digest") -> str:
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
