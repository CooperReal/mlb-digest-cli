# src/mlb_digest/templates.py
"""
Dugout Digest email template — dark-mode design with Gmail iOS fix.

Converts Claude's markdown narrative into a dark-themed, team-branded HTML email.
Uses two techniques to survive Gmail iOS dark mode:
  1. linear-gradient backgrounds prevent Gmail from inverting bg colors
  2. mix-blend-mode (screen+difference) restores white text Gmail dims

All visual styles are inline (email clients strip <style> blocks).
The only <style> block is for Gmail-targeted blend mode rules.
"""

import re

import markdown

# -- Color constants for the dark theme --
PAGE_BG = "#0d0d1a"
CONTENT_BG = "#1a1a2e"
CARD_BG = "#2a2a2f"
CARD_BORDER = "#333338"
DARK_SURFACE = "#1e1e24"
TEXT_COLOR = "#ffffff"
LINK_COLOR = "#8cb8ff"

# -- Font stacks --
SANS = "'Trebuchet MS', Helvetica, Arial, sans-serif"
SERIF = "Georgia, 'Times New Roman', serif"

# -- Gmail dark mode helpers --
GFIX_OPEN = '<div class="gfix-screen"><div class="gfix-diff">'
GFIX_CLOSE = "</div></div>"

# Gmail-targeted CSS: u + .body only matches inside Gmail (Gmail injects <u> before body)
GMAIL_BLEND_CSS = (
    "<style>"
    ":root{color-scheme:light dark;}"
    "u + .body .gfix-screen{background:#000;mix-blend-mode:screen;}"
    "u + .body .gfix-diff{background:#000;mix-blend-mode:difference;}"
    "</style>"
)


def _dark_bg(color: str) -> str:
    """Gmail-safe dark background: linear-gradient prevents dark mode inversion."""
    return f"background:{color}; background-image:linear-gradient({color},{color})"


def _gfix(text: str) -> str:
    """Wrap text in Gmail blend mode fix divs."""
    return f"{GFIX_OPEN}{text}{GFIX_CLOSE}"


def _apply_inline_styles(html: str, accent_color: str) -> str:
    """Replace tags with dark-mode inline styles. Email clients strip <style> blocks."""
    # Section headings — accent color with left border (NOT blend-wrapped)
    html = re.sub(
        r"<h2(.*?)>(.*?)</h2>",
        rf'<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        rf'width="100%" style="margin: 28px 0 12px 0;"><tr>'
        rf'<td style="border-left: 3px solid {accent_color}; padding-left: 12px;">'
        rf'<span style="font-family: {SANS}; font-size: 13px; font-weight: bold; '
        rf'color: {accent_color}; letter-spacing: 2px; text-transform: uppercase;">'
        r"\2</span></td></tr></table>",
        html,
    )

    # h3 subheadings — blend-wrapped
    html = re.sub(
        r"<h3(.*?)>(.*?)</h3>",
        rf'<h3\1 style="font-family: {SANS}; font-size: 15px; font-weight: bold; '
        rf'color: {TEXT_COLOR}; margin: 18px 0 8px 0;">'
        rf"{GFIX_OPEN}\2{GFIX_CLOSE}</h3>",
        html,
    )

    # Paragraphs — blend-wrapped
    html = re.sub(
        r"<p(.*?)>(.*?)</p>",
        rf'<p\1 style="font-family: {SERIF}; font-size: 14px; color: {TEXT_COLOR}; '
        rf'line-height: 1.65; margin: 0 0 14px 0;">{GFIX_OPEN}\2{GFIX_CLOSE}</p>',
        html,
        flags=re.DOTALL,
    )

    # Bold text
    html = re.sub(
        r"<strong(.*?)>",
        rf'<strong\1 style="color: {TEXT_COLOR};">',
        html,
    )

    # List items — blend-wrapped
    html = re.sub(
        r"<li(.*?)>(.*?)</li>",
        rf'<li\1 style="font-family: {SERIF}; font-size: 14px; color: {TEXT_COLOR}; '
        rf'line-height: 1.6; margin-bottom: 10px;">{GFIX_OPEN}\2{GFIX_CLOSE}</li>',
        html,
        flags=re.DOTALL,
    )

    # Unordered lists
    html = re.sub(
        r"<ul(.*?)>",
        r'<ul\1 style="padding-left: 20px; margin: 8px 0 14px 0;">',
        html,
    )

    # Links
    html = re.sub(
        r"<a ",
        f'<a style="color: {LINK_COLOR}; text-decoration: underline;" ',
        html,
    )

    # Tables — dark themed with linear-gradient backgrounds
    html = re.sub(
        r"<table(.*?)>",
        rf'<table\1 style="border-collapse: collapse; width: 100%; margin: 10px 0; '
        rf'{_dark_bg(CARD_BG)}; border-radius: 8px;">',
        html,
    )
    # Table headers — blend-wrapped text inside
    html = re.sub(
        r"<th(.*?)>(.*?)</th>",
        rf'<th\1 style="{_dark_bg(DARK_SURFACE)}; color: {TEXT_COLOR}; '
        rf"padding: 12px 14px; text-align: left; font-family: {SANS}; "
        rf"font-size: 11px; font-weight: bold; text-transform: uppercase; "
        rf'letter-spacing: 1px;">{GFIX_OPEN}\2{GFIX_CLOSE}</th>',
        html,
    )
    # Table cells — blend-wrapped text inside
    html = re.sub(
        r"<td(.*?)>(.*?)</td>",
        rf'<td\1 style="padding: 11px 14px; font-family: {SANS}; font-size: 14px; '
        rf'color: {TEXT_COLOR}; border-bottom: 1px solid {CARD_BORDER};">'
        rf"{GFIX_OPEN}\2{GFIX_CLOSE}</td>",
        html,
    )

    # Horizontal rules
    html = re.sub(
        r"<hr\s*/?>",
        rf'<hr style="border: none; border-top: 1px solid {CARD_BORDER}; margin: 24px 0;" />',
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
    """
    Render markdown into the Dugout Digest dark-mode HTML email.

    Uses the team's colors for header/footer (primary), section labels and
    accents (accent), and the first letter of team_name for the badge.
    """
    body_html = markdown.markdown(md_content, extensions=["tables"])
    body_html = _apply_inline_styles(body_html, accent_color)

    badge_letter = team_name[0] if team_name else "D"

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>"
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        '<meta name="color-scheme" content="light dark">'
        '<meta name="supported-color-schemes" content="light dark">'
        f"{GMAIL_BLEND_CSS}"
        "</head>\n"
        # class="body" required for Gmail's u + .body selector
        f'<body class="body" style="margin:0; padding:0; {_dark_bg(PAGE_BG)}; '
        f"font-family:{SERIF}; "
        '-webkit-text-size-adjust:100%; -ms-text-size-adjust:100%;">\n'
        # Outer wrapper
        f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        f'width="100%" style="{_dark_bg(PAGE_BG)};">\n'
        "<tr>\n"
        f'<td align="center" style="padding:20px 10px;">\n'
        # Main container
        f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        f'width="600" style="max-width:600px; width:100%; '
        f'{_dark_bg(primary_color)};">\n'
        # Header: accent stripe
        "<tr>\n"
        f'<td style="{_dark_bg(accent_color)}; height:4px; '
        f'font-size:1px; line-height:1px;">&nbsp;</td>\n'
        "</tr>\n"
        # Header: branding
        "<tr>\n"
        f'<td style="{_dark_bg(primary_color)}; padding:24px 30px 20px 30px;">\n'
        f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        f'width="100%"><tr>\n'
        f'<td style="vertical-align:middle;">\n'
        # Badge (NOT blend-wrapped) + DUGOUT DIGEST text (blend-wrapped)
        f'<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>\n'
        f'<td style="{_dark_bg(accent_color)}; width:42px; height:42px; '
        f'text-align:center; vertical-align:middle; border-radius:6px;">'
        f'<span style="font-family:{SANS}; font-size:24px; font-weight:bold; '
        f'color:#ffffff; line-height:42px;">{badge_letter}</span></td>\n'
        f'<td style="padding-left:14px; vertical-align:middle;">'
        f'{GFIX_OPEN}<span style="font-family:{SANS}; font-size:22px; font-weight:bold; '
        f'color:#ffffff; letter-spacing:1px;">DUGOUT DIGEST</span>{GFIX_CLOSE}</td>\n'
        "</tr></table>\n"
        "</td>\n"
        f'<td style="text-align:right; vertical-align:middle;">'
        f'{GFIX_OPEN}<span style="font-family:{SANS}; font-size:13px; '
        f'color:#ffffff;">{emoji} {team_name}</span>{GFIX_CLOSE}</td>\n'
        "</tr></table>\n"
        "</td>\n"
        "</tr>\n"
        # Content area
        "<tr>\n"
        f'<td style="{_dark_bg(CONTENT_BG)}; padding:8px 30px 30px 30px;">\n'
        f"{body_html}\n"
        "</td>\n"
        "</tr>\n"
        # Footer stripe
        "<tr>\n"
        f'<td style="{_dark_bg(accent_color)}; height:2px; '
        f'font-size:1px; line-height:1px;">&nbsp;</td>\n'
        "</tr>\n"
        # Footer
        "<tr>\n"
        f'<td style="{_dark_bg(primary_color)}; padding:24px 30px; '
        f'text-align:center;">\n'
        f'{GFIX_OPEN}<span style="font-family:{SANS}; font-size:14px; font-weight:bold; '
        f'color:#ffffff; letter-spacing:1px;">THE DUGOUT DIGEST</span><br>\n'
        f'<span style="font-family:{SERIF}; font-size:12px; color:#ffffff; '
        f'line-height:1.8;">'
        f"Powered by MLB Stats API &amp; Claude<br>"
        f"Questions or feedback? Just reply to this email.</span>{GFIX_CLOSE}\n"
        "</td>\n"
        "</tr>\n"
        "</table>\n"
        "</td>\n"
        "</tr>\n"
        "</table>\n"
        "</body>\n"
        "</html>"
    )


def render_email_text(md_content: str, team_name: str = "MLB Digest") -> str:
    """Render markdown content as plain text email."""
    text = md_content

    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1 (\2)", text)
    text = re.sub(r"^#{1,3} ", "", text, flags=re.MULTILINE)

    text += (
        f"\n\n---\nThe Dugout Digest \u2014 {team_name}\n"
        f"Sources: MLB Stats API, RSS feeds. Narrated by Claude.\n"
    )

    return text.strip()
