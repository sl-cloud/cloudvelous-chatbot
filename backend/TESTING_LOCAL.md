# Running Tests Locally (Outside Docker)

## Quick Start

### Option 1: Use the Script (Easiest)

```bash
cd /home/steve/repos/portfolio/cloudvelous-chatbot/backend
./run_tests_local.sh
```

This automatically sets up PYTHONPATH and runs all tests.

### Option 2: Manual Setup

```bash
cd /home/steve/repos/portfolio/cloudvelous-chatbot/backend

# Set Python path to include repo root
export PYTHONPATH="${PYTHONPATH}:$(dirname $(pwd))"

# Run tests
python3 -m pytest
```

## The Problem

When you run `pytest` from `backend/` directory locally, you get:

```
ERROR tests/ingestion/test_github_client.py
ModuleNotFoundError: No module named 'scripts'
```

**Why?** The `scripts/` directory is at the repo root, not in `backend/`, so Python can't find it.

## Solutions

### ✅ Best: Use Docker

**This is what GitHub Actions uses:**

```bash
# From repo root
docker compose exec backend pytest

# Or use the CI simulation script
./scripts/test_like_ci.sh
```

**Pros:**
- ✅ Matches CI environment exactly
- ✅ No PYTHONPATH setup needed
- ✅ All dependencies guaranteed available

**Cons:**
- ⏱️ Slightly slower startup

### ✅ Good: Use the Local Script

```bash
cd backend
./run_tests_local.sh
```

**Pros:**
- ✅ Automatically sets PYTHONPATH
- ✅ Checks for dependencies
- ✅ Faster than Docker

**Cons:**
- ⚠️ Requires local Python environment setup

### ✅ Manual: Set PYTHONPATH

```bash
cd backend

# One-time per shell session
export PYTHONPATH="${PYTHONPATH}:$(dirname $(pwd))"

# Now you can run pytest normally
pytest
pytest tests/unit/
pytest tests/ingestion/
```

**Pros:**
- ✅ Full control
- ✅ Can use pytest directly

**Cons:**
- ⚠️ Must remember to export PYTHONPATH
- ⚠️ Different shell = need to export again

## Running Specific Tests

### All Tests

```bash
# Docker
docker compose exec backend pytest

# Local
./run_tests_local.sh
```

### Unit Tests Only

```bash
# Docker
docker compose exec backend pytest tests/unit/

# Local
./run_tests_local.sh tests/unit/
```

### Ingestion Tests Only

```bash
# Docker
docker compose exec backend pytest tests/ingestion/

# Local
export PYTHONPATH="${PYTHONPATH}:$(dirname $(pwd))"
pytest tests/ingestion/
```

### Single Test File

```bash
# Docker
docker compose exec backend pytest tests/ingestion/test_github_client.py

# Local
./run_tests_local.sh tests/ingestion/test_github_client.py
```

### Single Test Function

```bash
# Docker
docker compose exec backend pytest tests/ingestion/test_github_client.py::TestGitHubClientInitialization::test_init_with_token

# Local
./run_tests_local.sh tests/ingestion/test_github_client.py::TestGitHubClientInitialization::test_init_with_token
```

## Setup Local Environment

If you want to run tests locally (outside Docker), you need:

### 1. Create Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set PYTHONPATH

```bash
# Add to your ~/.bashrc or ~/.zshrc for persistence
export PYTHONPATH="${PYTHONPATH}:/home/steve/repos/portfolio/cloudvelous-chatbot"
```

Or use the script which does this automatically:

```bash
./run_tests_local.sh
```

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'scripts'"

**Solution:** PYTHONPATH not set

```bash
# Docker (recommended)
docker compose exec backend pytest

# Or set PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(dirname $(pwd))"
```

### Error: "ModuleNotFoundError: No module named 'pytest'"

**Solution:** pytest not installed

```bash
pip install -r requirements.txt
```

### Error: "ModuleNotFoundError: No module named 'tenacity'"

**Solution:** tenacity not installed

```bash
pip install tenacity
```

### Error: "Bad credentials" in integration tests

**Solution:** Skip integration tests or set GITHUB_TOKEN

```bash
# Skip integration tests
pytest tests/ingestion/ -m "not integration"

# Or set token
export GITHUB_TOKEN="ghp_your_token"
```

## IDE Configuration (VS Code)

If using VS Code, add to `.vscode/settings.json`:

```json
{
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": [
    "tests"
  ],
  "python.envFile": "${workspaceFolder}/.env",
  "terminal.integrated.env.linux": {
    "PYTHONPATH": "${workspaceFolder}"
  }
}
```

This makes the test discovery work in VS Code.

## IDE Configuration (PyCharm)

1. Go to: Run → Edit Configurations → Tests → pytest
2. Environment variables: Add `PYTHONPATH=/home/steve/repos/portfolio/cloudvelous-chatbot`
3. Working directory: `/home/steve/repos/portfolio/cloudvelous-chatbot/backend`

## Comparison

| Method | Speed | Setup | Matches CI | Recommended |
|--------|-------|-------|------------|-------------|
| Docker | Slower | None | ✅ Yes | ⭐⭐⭐⭐⭐ |
| Local Script | Fast | Easy | ⚠️ Mostly | ⭐⭐⭐⭐ |
| Manual | Fast | Manual | ⚠️ Mostly | ⭐⭐⭐ |

## Recommendations

### For Day-to-Day Development

**Use Docker:**
```bash
docker compose exec backend pytest tests/unit/
```

Fast enough, matches CI exactly.

### For Quick Iteration

**Use local script:**
```bash
./run_tests_local.sh tests/ingestion/test_github_client.py::test_specific_function -v
```

Faster feedback loop when working on a specific test.

### Before Pushing

**Use CI simulation:**
```bash
cd ..  # Go to repo root
./scripts/test_like_ci.sh
```

This runs exactly what GitHub Actions will run.

## Summary

**Problem:** Running `pytest` from `backend/` can't find `scripts/` directory

**Solutions:**
1. ⭐ **Best:** Use Docker - `docker compose exec backend pytest`
2. ⭐ **Easy:** Use script - `./run_tests_local.sh`
3. ⭐ **Manual:** Set PYTHONPATH - `export PYTHONPATH="..."`

**Quick Commands:**
```bash
# From backend/ directory
docker compose exec backend pytest                    # All tests in Docker
./run_tests_local.sh                                  # All tests locally
./run_tests_local.sh tests/ingestion/                # Ingestion tests only

# From repo root
./scripts/test_like_ci.sh                            # CI simulation
```

