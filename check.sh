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

echo "=== Architecture ==="
uv run pytest tests/test_architecture.py -v --tb=short

echo "=== Tests ==="
uv run pytest tests/ -v

echo "=== Graph Freshness ==="
# Non-blocking. Surfaces graphify-out staleness so AGENTS.md architecture
# facts don't silently diverge from src/.
if [ -f graphify-out/.last-sha ]; then
    LAST_SHA=$(cat graphify-out/.last-sha)
    STALE=$(git rev-list --count "${LAST_SHA}..HEAD" -- src/ 2>/dev/null || echo 0)
    if [ "${STALE}" -gt 10 ]; then
        echo "⚠ graphify-out is ${STALE} src/ commits stale — run /graphify after your next feature"
    else
        echo "graphify-out is ${STALE} src/ commits old (threshold: 10)"
    fi
else
    echo "no graphify-out/.last-sha — skipping freshness check"
fi

echo "=== All checks passed ==="
