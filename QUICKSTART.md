# Quick Start Guide

Get the Cloudvelous Chat Assistant running in 5 minutes!

## Prerequisites

- Docker and Docker Compose installed
- At least 4GB RAM available

## Steps

### 1. Clone and Navigate

```bash
git clone <repository-url>
cd cloudvelous-chatbot
```

### 2. Configure Environment

```bash
# Copy the environment template
cp env.example .env

# Edit .env with your favorite editor
nano .env  # or vim, code, etc.
```

**Required values to set:**
- `POSTGRES_PASSWORD` - Any secure password
- `OPENAI_API_KEY` - Your OpenAI API key
- `GITHUB_TOKEN` - GitHub personal access token
- `ADMIN_JWT_SECRET` - Random 32+ character string
- `ADMIN_API_KEY` - Random string for admin access

**Quick secret generation:**
```bash
# Generate JWT secret
openssl rand -hex 32

# Generate API key
openssl rand -hex 16
```

### 3. Start Services

```bash
docker compose up -d
```

This will:
- Download PostgreSQL with pgvector
- Build the FastAPI backend
- Start both services
- Run database migrations

### 4. Verify

```bash
# Check services are running
docker compose ps

# You should see:
# cloudvelous-chatbot-db       running   healthy
# cloudvelous-chatbot-backend  running

# View logs
docker compose logs -f backend
```

### 5. Access the API

Open your browser:
- **API Documentation**: http://localhost:8000/docs
- **API Health Check**: http://localhost:8000/health

### 6. Test the API (Optional)

```bash
# Health check
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","version":"0.1.0"}
```

## Next Steps

1. **Run Initial Ingestion** (after implementation)
   ```bash
   docker compose exec backend python scripts/initial_ingestion.py
   ```

2. **Access Admin Interface** (after frontend implementation)
   - Navigate to the admin panel
   - Use your ADMIN_API_KEY to authenticate

3. **Monitor Logs**
   ```bash
   docker compose logs -f
   ```

## Common Issues

### Port Already in Use

If port 5432 or 8000 is already in use:

Edit `docker compose.yml` and change the host port:
```yaml
ports:
  - "5433:5432"  # Changed from 5432:5432
```

### Database Connection Failed

```bash
# Restart PostgreSQL
docker compose restart postgres

# Check PostgreSQL logs
docker compose logs postgres
```

### Backend Won't Start

```bash
# Rebuild the backend
docker compose build backend
docker compose up -d backend

# Check logs for errors
docker compose logs backend
```

## Stopping Services

```bash
# Stop services (preserves data)
docker compose down

# Stop and remove all data
docker compose down -v
```

## Development Mode

For local development without Docker:

```bash
cd backend
bash setup.sh
source venv/bin/activate
```

See [README.md](README.md) for full details.

## Getting Help

- Check the [README.md](README.md) for detailed documentation
- Review logs: `docker compose logs -f`
- Check that all environment variables are properly set
- Open an issue on GitHub

Happy chatting! 🚀

