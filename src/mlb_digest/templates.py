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
        r'padding-bottom: 5px; margin-top: 25px;">',
        html,
    )
    html = re.sub(
        r"<h3(.*?)>",
        rf'<h3\1 style="color: {primary_color}; margin-top: 15px;">',
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
        r'text-align: left; border: 1px solid #ddd;">',
        html,
    )
    html = re.sub(
        r"<td(.*?)>",
        r'<td\1 style="padding: 8px; border: 1px solid #ddd;">',
        html,
    )
    return html


def render_email_html(md_content: str, primary_color: str, accent_color: str) -> str:
    body_html = markdown.markdown(md_content, extensions=["tables"])
    body_html = _apply_inline_styles(body_html, primary_color, accent_color)

    body_style = (
        "margin: 0; padding: 0; "
        "font-family: -apple-system, BlinkMacSystemFont, "
        "'Segoe UI', Roboto, sans-serif; "
        "background-color: #f5f5f5;"
    )
    header_style = f"background-color: {primary_color}; color: #ffffff; padding: 20px 30px;"
    content_style = "padding: 20px 30px; color: #333333; line-height: 1.6; font-size: 16px;"
    footer_style = "background-color: #f0f0f0; padding: 15px 30px; font-size: 12px; color: #888888;"
    wrapper_style = "max-width: 600px; margin: 0 auto; background-color: #ffffff; padding: 0;"
    h1_style = "margin: 0; font-size: 24px; color: #ffffff;"

    return (
        "<!DOCTYPE html>\n"
        "<html>\n"
        '<head><meta charset="utf-8"></head>\n'
        f'<body style="{body_style}">\n'
        f'  <div style="{wrapper_style}">\n'
        f'    <div style="{header_style}">\n'
        f'      <h1 style="{h1_style}">MLB Digest</h1>\n'
        "    </div>\n"
        f'    <div style="{content_style}">\n'
        f"      {body_html}\n"
        "    </div>\n"
        f'    <div style="{footer_style}">\n'
        "      Sources: MLB Stats API, RSS feeds."
        " Narrated by Claude Sonnet.\n"
        "    </div>\n"
        "  </div>\n"
        "</body>\n"
        "</html>"
    )


def render_email_text(md_content: str) -> str:
    text = md_content

    # Strip markdown formatting for plain text
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1 (\2)", text)
    text = re.sub(r"^#{1,3} ", "", text, flags=re.MULTILINE)

    text += "\n\n---\nSources: MLB Stats API, RSS feeds. Narrated by Claude Sonnet.\n"

    return text.strip()
