#!/usr/bin/env bash
# Fresh clone → runnable. Idempotent; safe to re-run.
set -euo pipefail

# Always run from the script's own directory (the repo root).
cd "$(dirname "$0")"

if ! command -v uv >/dev/null 2>&1; then
  echo "uv is not installed. Install: https://docs.astral.sh/uv/getting-started/installation/"
  exit 1
fi

uv sync --all-extras

if [ ! -f .env ]; then
  cp .env.example .env
  echo "Created .env from .env.example. Fill in ANTHROPIC_API_KEY, GMAIL_ADDRESS, GMAIL_APP_PASSWORD, EMAIL_RECIPIENTS before running."
fi

uv run pre-commit install

echo "Ready. Next: fill in .env, then 'bash check.sh' to verify."
