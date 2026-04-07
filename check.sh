#!/usr/bin/env bash
set -e

echo "=== Secrets Baseline ==="
uv run detect-secrets scan --baseline .secrets.baseline
if ! git diff --quiet .secrets.baseline 2>/dev/null; then
    echo "WARNING: .secrets.baseline was out of date — updated. Stage it with: git add .secrets.baseline"
fi

echo "=== Lint ==="
uv run ruff check .

echo "=== Type Check ==="
uv run mypy src/

echo "=== Tests ==="
uv run pytest tests/ -v

echo "=== All checks passed ==="
