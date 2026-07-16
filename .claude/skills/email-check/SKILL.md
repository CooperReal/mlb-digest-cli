---
name: email-check
description: Render the digest email from sample data, screenshot it in Chrome, and share the screenshots back in chat. Use whenever templates.py changes or email rendering/colors need verification.
---

# Email Check Loop

Verify the digest email renders correctly (including the Gmail dark-mode
defenses from ADR 0002) without sending real emails until the final check.

## Fast iteration (no email sent)

1. Run: `uv run mlb-digest preview`
   - Writes `preview/preview.html` (the email as built) and
     `preview/preview-gmail-dark.html` (same HTML inside a Gmail-like DOM:
     `<u></u>` + `.body` wrapper on a dark background, which activates the
     blend-mode CSS).
2. Open both files in Chrome via claude-in-chrome (`file://` URLs) and
   screenshot each.
3. Share the screenshots in chat. Check: white text legible, backgrounds not
   inverted, accent colors correct, table rows readable, badge letter visible.
4. Iterate until correct.

## Final check (sends one real email)

5. Run: `uv run mlb-digest test-email` — sends the sample digest through the
   real template.
6. Open Gmail web in Chrome, find the "MLB Digest — Test Email (sample data)"
   message, screenshot it, share in chat.
7. Ask the user to glance at Gmail iOS dark mode when convenient.

## Caveat

The gmail-dark harness verifies the blend-mode defenses activate and text
stays legible. It does not replicate Gmail iOS's exact color transformation —
the final check plus the iOS glance covers that gap.
