#!/bin/bash
#
# Run tests locally (outside Docker)
# This script sets up the Python path correctly
#

set -e

# Get the repo root directory
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Add repo root to PYTHONPATH so scripts.ingestion can be imported
export PYTHONPATH="${PYTHONPATH}:${REPO_ROOT}"

# Change to backend directory
cd "${REPO_ROOT}/backend"

echo "=========================================="
echo "Running tests locally (outside Docker)"
echo "PYTHONPATH: ${PYTHONPATH}"
echo "=========================================="
echo ""

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: Not in a virtual environment"
    echo "Consider running: source venv/bin/activate"
    echo ""
fi

# Check if pytest is available
if ! python3 -c "import pytest" 2>/dev/null; then
    echo "❌ pytest not installed"
    echo "Install dependencies: pip install -r requirements.txt"
    exit 1
fi

# Check if tenacity is available
if ! python3 -c "import tenacity" 2>/dev/null; then
    echo "❌ tenacity not installed"
    echo "Install dependencies: pip install tenacity"
    exit 1
fi

# Run the tests
if [ -z "$1" ]; then
    echo "Running all backend tests..."
    python3 -m pytest tests/ "$@"
else
    echo "Running: pytest $@"
    python3 -m pytest "$@"
fi

