# Testing Guide for GitHub Ingestion Module

## Quick Start

```bash
# Easiest way - use the test runner script
./scripts/ingestion/run_tests.sh unit
```

## Common Issues and Solutions

### Issue 1: "FAIL Required test coverage of 79% not reached. Total coverage: 50.74%"

**Problem:** This occurs when you run ingestion tests but pytest is configured to measure coverage for the entire `app/` directory (see `pytest.ini`). Since you're only testing the ingestion module, the `app/` coverage is 0%, bringing the total down.

**Solution:** Use the `-o addopts=""` flag to override the default configuration:

```bash
docker compose exec backend pytest tests/ingestion/ \
  -v \
  -m "not integration" \
  -o addopts="" \
  --cov=scripts.ingestion \
  --cov-fail-under=95
```

Or use the provided script:

```bash
./scripts/ingestion/run_tests.sh unit
```

### Issue 2: "ModuleNotFoundError: No module named 'scripts'"

**Problem:** The `scripts/` directory is not in the Python path or not mounted in the container.

**Solution:** Make sure you're running tests inside the Docker container:

```bash
# ✅ Correct
docker compose exec backend pytest tests/ingestion/

# ❌ Wrong
pytest tests/ingestion/
```

The `docker-compose.yml` mounts `./scripts:/app/scripts` so it's available in the container.

### Issue 3: Integration Tests Failing with "Bad credentials"

**Problem:** Integration tests require a valid GitHub token.

**Solution 1:** Skip integration tests (recommended for development):

```bash
pytest tests/ingestion/ -m "not integration"
```

**Solution 2:** Set a valid GITHUB_TOKEN:

```bash
export GITHUB_TOKEN="ghp_your_token_here"
pytest tests/ingestion/ -m integration
```

### Issue 4: "ModuleNotFoundError: No module named 'tenacity'"

**Problem:** The `tenacity` dependency is not installed.

**Solution:** Install dependencies:

```bash
docker compose exec backend pip install tenacity==8.2.3

# Or rebuild the container
docker compose up -d --build backend
```

## Test Organization

### Unit Tests
- **Location:** `backend/tests/ingestion/test_github_client.py`
- **Marker:** Classes without `@pytest.mark.integration`
- **Requirements:** None (all mocked)
- **Run:** `./scripts/ingestion/run_tests.sh unit`
- **Count:** 30 tests

### Integration Tests
- **Location:** `backend/tests/ingestion/test_github_client.py`
- **Marker:** `@pytest.mark.integration`
- **Requirements:** Valid `GITHUB_TOKEN` environment variable
- **Run:** `./scripts/ingestion/run_tests.sh integration`
- **Count:** 3 tests

## Coverage Goals

- **Target:** 95% minimum (100% achieved)
- **Scope:** `scripts.ingestion` module only
- **Report Locations:**
  - Terminal: Shown after tests
  - HTML: `htmlcov/ingestion/index.html`

## CI/CD Considerations

When running in CI/CD pipelines:

```yaml
# GitHub Actions example
- name: Run ingestion tests
  run: |
    docker compose exec -T backend pytest tests/ingestion/ \
      -v \
      -m "not integration" \
      -o addopts="" \
      --cov=scripts.ingestion \
      --cov-report=xml \
      --cov-fail-under=95
```

The key is always using `-o addopts=""` to prevent measuring coverage for unrelated code.

## Development Workflow

### 1. Make Changes to Code

Edit `scripts/ingestion/github_client.py`

### 2. Run Tests

```bash
./scripts/ingestion/run_tests.sh unit
```

### 3. Check Coverage

Look for "Required test coverage of 95% reached" in the output.

If coverage drops below 95%, add more tests to `backend/tests/ingestion/test_github_client.py`.

### 4. Run Integration Tests (Optional)

```bash
export GITHUB_TOKEN="your_token"
./scripts/ingestion/run_tests.sh integration
```

### 5. Commit

```bash
git add scripts/ingestion/ backend/tests/ingestion/
git commit -m "feat: update GitHub client"
```

## Test Runner Script Options

The provided script `scripts/ingestion/run_tests.sh` supports three modes:

### Unit Mode (Default)
```bash
./scripts/ingestion/run_tests.sh unit
# or just
./scripts/ingestion/run_tests.sh
```

- Runs only unit tests (mocked)
- No GitHub token required
- Measures coverage for scripts.ingestion
- Requires 95% coverage

### Integration Mode
```bash
export GITHUB_TOKEN="ghp_your_token"
./scripts/ingestion/run_tests.sh integration
```

- Runs only integration tests
- Requires valid GITHUB_TOKEN
- Makes real API calls to GitHub
- No coverage measurement

### All Mode
```bash
./scripts/ingestion/run_tests.sh all
```

- Runs all tests (unit + integration)
- Requires GITHUB_TOKEN for integration tests
- Measures coverage
- Shows failures from both test types

## Debugging Test Failures

### Verbose Output

```bash
docker compose exec backend pytest tests/ingestion/ -vv --tb=long
```

### Run Single Test

```bash
docker compose exec backend pytest tests/ingestion/test_github_client.py::TestGitHubClientInitialization::test_init_with_token -v
```

### Print Statements

```bash
docker compose exec backend pytest tests/ingestion/ -v -s
```

The `-s` flag shows print statements and logs.

### Interactive Debugging

Add `breakpoint()` in your test or code:

```python
def test_something():
    client = GitHubClient(token="test")
    breakpoint()  # Debugger will stop here
    assert client is not None
```

Then run:

```bash
docker compose exec backend pytest tests/ingestion/ -v --pdb
```

## Quick Reference

| Command | Purpose |
|---------|---------|
| `./scripts/ingestion/run_tests.sh` | Run unit tests (recommended) |
| `./scripts/ingestion/run_tests.sh unit` | Run unit tests explicitly |
| `./scripts/ingestion/run_tests.sh integration` | Run integration tests |
| `./scripts/ingestion/run_tests.sh all` | Run all tests |
| `-o addopts=""` | Override pytest.ini defaults |
| `-m "not integration"` | Skip integration tests |
| `--cov=scripts.ingestion` | Measure coverage for this module |
| `--cov-fail-under=95` | Require 95% coverage |

## Expected Output (Success)

```
Running unit tests only (mocked, no GitHub token required)...
...
====================== 30 passed, 3 deselected in 45.34s =======================

---------- coverage: platform linux, python 3.11.14-final-0 ----------
Name                                 Stmts   Miss  Cover   Missing
------------------------------------------------------------------
scripts/ingestion/__init__.py            1      0   100%
scripts/ingestion/github_client.py      79      0   100%
------------------------------------------------------------------
TOTAL                                   80      0   100%

Required test coverage of 95% reached. Total coverage: 100.00%

✅ Tests completed successfully!
```

## Getting Help

If you encounter issues not covered here:

1. Check `scripts/ingestion/README.md` for usage documentation
2. Review test code in `backend/tests/ingestion/test_github_client.py`
3. Check Docker container logs: `docker compose logs backend`
4. Verify dependencies are installed: `docker compose exec backend pip list | grep -i github`

