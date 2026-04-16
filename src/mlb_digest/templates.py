# src/mlb_digest/templates.py
"""
Dugout Digest email template — dark-mode design.

Converts Claude's markdown narrative into a dark-themed, team-branded HTML email.
All styles are inline (email clients strip <style> blocks).

Color scheme:
    Page background:  #0d0d1a (near-black)
    Content area:     #1a1a2e (dark navy-purple)
    Card panels:      #2a2a2f (elevated surface)
    Body text:        #c8c8d8 (soft light gray)
    Muted text:       #8b8fa3
    Headings:         accent color (team-specific)
    Links:            #7ea8e8 (blue)
    Table headers:    #1e1e24 (darkest surface)
"""

import re

import markdown

# -- Color constants for the dark theme --
PAGE_BG = "#0d0d1a"
CONTENT_BG = "#1a1a2e"
CARD_BG = "#2a2a2f"
CARD_BORDER = "#333338"
DARK_SURFACE = "#1e1e24"
BODY_TEXT = "#c8c8d8"
MUTED_TEXT = "#8b8fa3"
DIM_TEXT = "#5a5e73"
LINK_COLOR = "#7ea8e8"
HEADING_TEXT = "#e8e8f0"

# -- Font stacks --
SANS = "'Trebuchet MS', Helvetica, Arial, sans-serif"
SERIF = "Georgia, 'Times New Roman', serif"


def _apply_inline_styles(html: str, accent_color: str) -> str:
    """Replace tags with dark-mode inline styles. Email clients strip <style> blocks."""
    # Section headings — accent color with left border
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

    # h3 subheadings
    html = re.sub(
        r"<h3(.*?)>",
        rf'<h3\1 style="font-family: {SANS}; font-size: 15px; font-weight: bold; '
        rf'color: {HEADING_TEXT}; margin: 18px 0 8px 0;">',
        html,
    )

    # Paragraphs — light text on dark
    html = re.sub(
        r"<p(.*?)>",
        rf'<p\1 style="font-family: {SERIF}; font-size: 14px; color: {BODY_TEXT}; '
        r'line-height: 1.65; margin: 0 0 14px 0;">',
        html,
    )

    # Bold text — slightly brighter
    html = re.sub(
        r"<strong(.*?)>",
        rf'<strong\1 style="color: {HEADING_TEXT};">',
        html,
    )

    # List items
    html = re.sub(
        r"<li(.*?)>",
        rf'<li\1 style="font-family: {SERIF}; font-size: 14px; color: {BODY_TEXT}; '
        r'line-height: 1.6; margin-bottom: 10px;">',
        html,
    )

    # Unordered lists
    html = re.sub(
        r"<ul(.*?)>",
        r'<ul\1 style="padding-left: 20px; margin: 8px 0 14px 0;">',
        html,
    )

    # Links — blue on dark
    html = re.sub(
        r"<a ",
        f'<a style="color: {LINK_COLOR}; text-decoration: underline;" ',
        html,
    )

    # Tables — dark themed
    html = re.sub(
        r"<table(.*?)>",
        rf'<table\1 style="border-collapse: collapse; width: 100%; margin: 10px 0; '
        rf'background: {CARD_BG}; border-radius: 8px;">',
        html,
    )
    html = re.sub(
        r"<th(.*?)>",
        rf'<th\1 style="background: {DARK_SURFACE}; color: {MUTED_TEXT}; '
        rf"padding: 12px 14px; text-align: left; font-family: {SANS}; "
        r'font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;">',
        html,
    )
    html = re.sub(
        r"<td(.*?)>",
        rf'<td\1 style="padding: 11px 14px; font-family: {SANS}; font-size: 14px; '
        rf'color: {BODY_TEXT}; border-bottom: 1px solid {CARD_BORDER};">',
        html,
    )

    # Horizontal rules — accent colored
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

    # Extract first letter of team name for the badge (e.g. "A" for Atlanta Braves)
    badge_letter = team_name[0] if team_name else "D"

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>"
        '<meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">'
        # Tell Gmail/Apple Mail to leave our dark colors alone
        '<meta name="color-scheme" content="light dark">'
        '<meta name="supported-color-schemes" content="light dark">'
        "<style>:root{color-scheme:light dark;}</style>"
        "</head>\n"
        # Gmail dark mode prevention: use `background` shorthand instead of
        # `background-color` so Gmail's inversion algorithm skips these elements.
        f'<body style="margin:0; padding:0; background:{PAGE_BG}; '
        f"font-family:{SERIF}; "
        '-webkit-text-size-adjust:100%; -ms-text-size-adjust:100%;">\n'
        # Outer wrapper
        f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        f'width="100%" style="background:{PAGE_BG};">\n'
        "<tr>\n"
        f'<td align="center" style="padding:20px 10px;">\n'
        # Main container
        f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        f'width="600" style="max-width:600px; width:100%; '
        f'background:{primary_color};">\n'
        # Header: accent stripe + branding
        "<tr>\n"
        f'<td style="background:{accent_color}; height:4px; '
        f'font-size:1px; line-height:1px;">&nbsp;</td>\n'
        "</tr>\n"
        "<tr>\n"
        f'<td style="background:{primary_color}; padding:24px 30px 20px 30px;">\n'
        f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        f'width="100%"><tr>\n'
        f'<td style="vertical-align:middle;">\n'
        # Badge + name
        f'<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>\n'
        f'<td style="background:{accent_color}; width:42px; height:42px; '
        f'text-align:center; vertical-align:middle; border-radius:6px;">'
        f'<span style="font-family:{SANS}; font-size:24px; font-weight:bold; '
        f'color:#ffffff; line-height:42px;">{badge_letter}</span></td>\n'
        f'<td style="padding-left:14px; vertical-align:middle;">'
        f'<span style="font-family:{SANS}; font-size:22px; font-weight:bold; '
        f'color:#ffffff; letter-spacing:1px;">DUGOUT DIGEST</span></td>\n'
        "</tr></table>\n"
        "</td>\n"
        f'<td style="text-align:right; vertical-align:middle;">'
        f'<span style="font-family:{SANS}; font-size:13px; '
        f'color:{MUTED_TEXT};">{emoji} {team_name}</span></td>\n'
        "</tr></table>\n"
        "</td>\n"
        "</tr>\n"
        # Content area: dark background
        "<tr>\n"
        f'<td style="background:{CONTENT_BG}; padding:8px 30px 30px 30px;">\n'
        f"{body_html}\n"
        "</td>\n"
        "</tr>\n"
        # Footer
        "<tr>\n"
        f'<td style="background:{accent_color}; height:2px; '
        f'font-size:1px; line-height:1px;">&nbsp;</td>\n'
        "</tr>\n"
        "<tr>\n"
        f'<td style="background:{primary_color}; padding:24px 30px; '
        f'text-align:center;">\n'
        f'<span style="font-family:{SANS}; font-size:14px; font-weight:bold; '
        f'color:#ffffff; letter-spacing:1px;">THE DUGOUT DIGEST</span><br>\n'
        f'<span style="font-family:{SERIF}; font-size:12px; color:{DIM_TEXT}; '
        f'line-height:1.8;">'
        f"Powered by MLB Stats API &amp; Claude<br>"
        f"Questions or feedback? Just reply to this email.</span>\n"
        "</td>\n"
        "</tr>\n"
        # Close main container
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

    # Strip markdown formatting for plain text
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"\*(.+?)\*", r"\1", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r"\1 (\2)", text)
    text = re.sub(r"^#{1,3} ", "", text, flags=re.MULTILINE)

    text += (
        f"\n\n---\nThe Dugout Digest — {team_name}\n"
        f"Sources: MLB Stats API, RSS feeds. Narrated by Claude.\n"
    )

    return text.strip()
