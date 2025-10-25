#!/bin/bash
#
# Test runner for ingestion module
# Usage: ./scripts/ingestion/run_tests.sh [unit|integration|all]
#

set -e

MODE="${1:-unit}"

case "$MODE" in
  unit)
    echo "Running unit tests only (mocked, no GitHub token required)..."
    docker compose exec backend pytest tests/ingestion/ \
      -v \
      -m "not integration" \
      -o addopts="" \
      --cov=scripts.ingestion \
      --cov-report=term-missing \
      --cov-report=html:htmlcov/ingestion \
      --cov-fail-under=95
    ;;
  
  integration)
    echo "Running integration tests (requires GITHUB_TOKEN)..."
    if [ -z "$GITHUB_TOKEN" ]; then
      echo "ERROR: GITHUB_TOKEN environment variable not set"
      echo "Export your token: export GITHUB_TOKEN='ghp_your_token'"
      exit 1
    fi
    docker compose exec backend pytest tests/ingestion/ \
      -v \
      -m integration \
      --tb=short
    ;;
  
  all)
    echo "Running all tests..."
    docker compose exec backend pytest tests/ingestion/ \
      -v \
      -o addopts="" \
      --cov=scripts.ingestion \
      --cov-report=term-missing \
      --cov-fail-under=95
    ;;
  
  *)
    echo "Usage: $0 [unit|integration|all]"
    echo ""
    echo "  unit        - Run unit tests only (default)"
    echo "  integration - Run integration tests (requires GITHUB_TOKEN)"
    echo "  all         - Run all tests"
    exit 1
    ;;
esac

echo ""
echo "✅ Tests completed successfully!"

