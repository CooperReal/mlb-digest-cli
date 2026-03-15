#!/usr/bin/env bash
set -e

echo "=== Lint ==="
uv run ruff check .

echo "=== Type Check ==="
uv run mypy src/

echo "=== Tests ==="
uv run pytest tests/ -v

echo "=== All checks passed ==="
