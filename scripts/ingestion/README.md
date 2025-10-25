# GitHub Repository Ingestion

This module provides a robust GitHub API client for fetching repository data, with built-in authentication, rate limiting, retry logic, and comprehensive error handling.

## Features

- **Secure Authentication**: Token-based authentication with automatic masking in logs
- **Context Manager Support**: Automatic resource cleanup via `with` statements
- **Retry Logic**: Configurable exponential backoff for transient failures
- **Rate Limit Handling**: Automatic detection and clear error messages
- **Structured Logging**: Rich context for debugging and monitoring
- **Type Safety**: Full type hints with TypedDict for API responses
- **Timeout Configuration**: Prevent hanging on slow API responses

## Setup

### Prerequisites

1. **GitHub Personal Access Token**: Generate a token with appropriate permissions at [github.com/settings/tokens](https://github.com/settings/tokens)

2. **Environment Configuration**: Set your token in the environment

```bash
export GITHUB_TOKEN="ghp_your_token_here"
```

Alternatively, add to your `.env` file:

```
GITHUB_TOKEN=ghp_your_token_here
```

### Dependencies

Install required packages:

```bash
pip install PyGithub tenacity
```

## Usage

### Basic Usage with Context Manager (Recommended)

```python
from scripts.ingestion.github_client import GitHubClient

# Using context manager ensures automatic cleanup
with GitHubClient() as client:
    # Verify authentication
    client.verify_connection()
    
    # Fetch a repository
    repo = client.get_repository("cloudvelous/aws-sdk")
    print(f"Repository: {repo.full_name}")
    print(f"Stars: {repo.stargazers_count}")
    print(f"Description: {repo.description}")
```

### Manual Resource Management

```python
from scripts.ingestion.github_client import GitHubClient

client = GitHubClient(token="ghp_your_token")
try:
    client.verify_connection()
    repo = client.get_repository("owner/repo")
    # ... process repo
finally:
    client.close()
```

### Custom Configuration

```python
from scripts.ingestion.github_client import GitHubClient

# Configure timeout and retry behaviour
client = GitHubClient(
    token="ghp_your_token",
    timeout=20,        # Request timeout in seconds (default: 10)
    max_retries=5      # Retry attempts for failures (default: 3, 0 to disable)
)
```

### Check Rate Limits

```python
with GitHubClient() as client:
    limits = client.check_rate_limit()
    print(f"Remaining requests: {limits['remaining']}/{limits['limit']}")
    print(f"Resets at: {limits['reset']}")
```

### Error Handling

```python
from scripts.ingestion.github_client import (
    GitHubClient,
    GitHubAuthenticationError,
    GitHubRateLimitError,
    GitHubClientError,
)

try:
    with GitHubClient() as client:
        repo = client.get_repository("owner/repo")
except GitHubAuthenticationError as e:
    print(f"Authentication failed: {e}")
except GitHubRateLimitError as e:
    print(f"Rate limit exceeded: {e}")
except GitHubClientError as e:
    print(f"GitHub API error: {e}")
```

## API Reference

### `GitHubClient`

Main client class for interacting with the GitHub API.

#### Constructor

```python
GitHubClient(
    token: Optional[str] = None,
    timeout: int = 10,
    max_retries: int = 3
)
```

**Parameters:**
- `token`: GitHub personal access token (reads from `GITHUB_TOKEN` env var if not provided)
- `timeout`: Request timeout in seconds
- `max_retries`: Maximum retry attempts for transient failures (set to 0 to disable)

**Raises:**
- `GitHubAuthenticationError`: If no token is provided or found

#### Methods

##### `verify_connection() -> bool`

Verify authentication and check rate limits.

**Returns:** `True` if connection is successful

**Raises:**
- `GitHubAuthenticationError`: If authentication fails
- `GitHubClientError`: If connection fails

##### `get_repository(repo_full_name: str) -> Repository`

Fetch a repository by its full name.

**Parameters:**
- `repo_full_name`: Repository identifier in format "owner/repo"

**Returns:** PyGithub `Repository` object

**Raises:**
- `GitHubClientError`: If repository not found or access denied
- `GitHubRateLimitError`: If rate limit is exceeded

##### `check_rate_limit() -> RateLimitInfo`

Check current API rate limit status.

**Returns:** `RateLimitInfo` TypedDict with:
- `limit` (int): Total requests allowed per hour
- `remaining` (int): Requests remaining
- `reset` (datetime): When limit resets

##### `close() -> None`

Close the GitHub client connection. Called automatically when using context manager.

### Exception Hierarchy

```
GitHubClientError (base)
├── GitHubAuthenticationError (401 errors)
└── GitHubRateLimitError (rate limit exceeded)
```

## Testing

### Quick Start (Recommended)

Use the provided test runner script for the best experience:

```bash
# Run unit tests only (no GitHub token needed)
./scripts/ingestion/run_tests.sh unit

# Run integration tests (requires GITHUB_TOKEN)
export GITHUB_TOKEN="ghp_your_token"
./scripts/ingestion/run_tests.sh integration

# Run all tests
./scripts/ingestion/run_tests.sh all
```

### Manual Testing

If you prefer to run tests manually:

```bash
# Unit tests with coverage (from project root)
docker compose exec backend pytest tests/ingestion/ \
  -v \
  -m "not integration" \
  -o addopts="" \
  --cov=scripts.ingestion \
  --cov-report=term-missing \
  --cov-fail-under=95

# Integration tests (requires GITHUB_TOKEN)
export GITHUB_TOKEN="ghp_your_token"
docker compose exec backend pytest tests/ingestion/ \
  -v \
  -m integration \
  --tb=short

# All tests
docker compose exec backend pytest tests/ingestion/ \
  -v \
  -o addopts="" \
  --cov=scripts.ingestion
```

**Important:** The `-o addopts=""` flag is necessary to override the default pytest configuration which measures coverage for the entire `app/` directory. When running only ingestion tests, you want to measure coverage only for `scripts.ingestion`.

## Best Practices

### 1. Use Context Managers

Always prefer context managers to ensure proper resource cleanup:

```python
# ✅ Good
with GitHubClient() as client:
    repo = client.get_repository("owner/repo")

# ❌ Avoid
client = GitHubClient()
repo = client.get_repository("owner/repo")
# client.close() might not be called if exception occurs
```

### 2. Handle Rate Limits Gracefully

```python
from scripts.ingestion.github_client import GitHubRateLimitError

try:
    with GitHubClient() as client:
        # Check before making many requests
        limits = client.check_rate_limit()
        if limits['remaining'] < 100:
            print(f"Warning: Only {limits['remaining']} requests remaining")
        
        repo = client.get_repository("owner/repo")
except GitHubRateLimitError as e:
    print(f"Rate limited until: {e}")
    # Implement backoff or queue for later
```

### 3. Configure Timeouts for Your Use Case

```python
# For batch processing - use longer timeout
batch_client = GitHubClient(timeout=30, max_retries=5)

# For interactive requests - use shorter timeout
interactive_client = GitHubClient(timeout=5, max_retries=1)
```

### 4. Never Log or Print Raw Tokens

The client automatically masks tokens in logs and repr:

```python
client = GitHubClient(token="ghp_secret_token")
print(repr(client))  # GitHubClient(token=ghp_sec..., ...)
# Token is safely masked
```

### 5. Validate Repository Names

```python
def validate_repo_name(repo_name: str) -> bool:
    """Validate repository name format."""
    parts = repo_name.split("/")
    return len(parts) == 2 and all(p.strip() for p in parts)

repo_name = "owner/repo"
if validate_repo_name(repo_name):
    with GitHubClient() as client:
        repo = client.get_repository(repo_name)
```

## Troubleshooting

### "GitHub token not provided"

**Problem:** No token found in environment or constructor.

**Solution:**
```bash
# Set environment variable
export GITHUB_TOKEN="ghp_your_token"

# Or pass explicitly
client = GitHubClient(token="ghp_your_token")
```

### "Authentication failed: Bad credentials"

**Problem:** Token is invalid or expired.

**Solution:**
1. Generate a new token at [github.com/settings/tokens](https://github.com/settings/tokens)
2. Ensure token has required scopes (typically `repo` for private repos, or public access for public repos)
3. Update your environment variable or `.env` file

### "Rate limit exceeded"

**Problem:** You've made too many requests in the current hour.

**Solution:**
1. Check rate limit before making requests: `client.check_rate_limit()`
2. Wait until the reset time
3. For authenticated requests: 5,000 requests/hour
4. For unauthenticated: 60 requests/hour
5. Consider implementing request batching or caching

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'github'` or `'tenacity'`

**Solution:**
```bash
pip install PyGithub tenacity
```

## Architecture

The client follows these design principles:

- **Separation of Concerns**: Authentication, rate limiting, and retry logic are handled separately
- **Fail-Fast**: Invalid inputs and auth errors are caught early
- **EAFP (Easier to Ask for Forgiveness than Permission)**: Uses try/except rather than extensive pre-checks
- **Structured Logging**: All log messages include contextual information for debugging
- **Type Safety**: Full type hints enable static analysis and IDE support

## Future Enhancements

Planned features:
- [ ] Support for GitHub Apps authentication
- [ ] Automatic pagination for large result sets
- [ ] Caching layer for repeated requests
- [ ] Metrics collection (request counts, latencies)
- [ ] Support for GitHub Enterprise Server

## Contributing

When adding features:
1. Maintain >= 95% test coverage
2. Add both unit and integration tests
3. Update this README with new functionality
4. Follow existing code style (ruff formatting)
5. Add structured logging for observability

## License

Part of the Cloudvelous Chatbot project.

