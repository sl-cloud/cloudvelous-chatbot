# Cloudvelous Chat Assistant

An intelligent chatbot backend powered by RAG (Retrieval-Augmented Generation) with workflow learning capabilities. Built with FastAPI, PostgreSQL (pgvector), and advanced LLM integration.

## Features

- **RAG Architecture**: Semantic search over GitHub repository documentation using pgvector
- **Multi-LLM Support**: OpenAI and Google Gemini integration
- **Workflow Learning**: Captures and learns from reasoning chains to improve future responses
- **Admin Training Interface**: Review and provide feedback on chatbot responses
- **Self-Improving**: Automatically adjusts retrieval weights based on feedback
- **GitHub Integration**: Automated repository documentation ingestion


📚 **Documentation:**
- [User Manual](USER_MANUAL.md) - A complete guide to using the Cloudvelous Chat Assistant from asking questions to training the AI.

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git
- At least 4GB RAM available for Docker

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd cloudvelous-chatbot
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your API keys:
   - `POSTGRES_PASSWORD`: Set a secure password for PostgreSQL
   - `OPENAI_API_KEY`: Your OpenAI API key (starts with `sk-`)
   - `GEMINI_API_KEY`: Your Google Gemini API key (optional)
   - `GITHUB_TOKEN`: GitHub personal access token for repository access
   - `ADMIN_JWT_SECRET`: Random string (min 32 characters) for JWT signing
   - `ADMIN_API_KEY`: Random string for admin API authentication

   Generate secure secrets:
   ```bash
   openssl rand -hex 32  # ADMIN_JWT_SECRET
   openssl rand -hex 16  # ADMIN_API_KEY
   ```

3. **Start all services**
   ```bash
   docker compose up -d
   ```

4. **Verify services are running**
   ```bash
   docker compose ps
   ```
   
   You should see:
   - `cloudvelous-chatbot-db` (postgres) - healthy
   - `cloudvelous-chatbot-backend` - running

5. **View logs**
   ```bash
   # All services
   docker compose logs -f
   
   # Backend only
   docker compose logs -f backend
   
   # Database only
   docker compose logs -f postgres
   ```

6. **Access the API**
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - Database: localhost:5432

7. **Run initial data ingestion** (after implementation)
   ```bash
   docker compose exec backend python scripts/initial_ingestion.py
   ```

## Project Structure

```
cloudvelous-chatbot/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── config.py            # Configuration management
│   │   ├── routers/             # API endpoints
│   │   ├── services/            # Business logic
│   │   ├── models/              # Database models
│   │   ├── schemas/             # Pydantic schemas
│   │   ├── llm/                 # LLM provider integrations
│   │   ├── training/            # Training & optimization services
│   │   └── middleware/          # Authentication & middleware
│   ├── tests/                   # Unit and integration tests
│   ├── alembic/                 # Database migrations
│   ├── requirements.txt         # Python dependencies
│   ├── Dockerfile               # Backend Docker image
│   └── setup.sh                 # Local dev setup script
├── scripts/
│   ├── init-db.sql              # Database initialization
│   ├── initial_ingestion.py     # Repository data ingestion
│   └── manual_retrain.py        # Manual retraining trigger
├── docker compose.yml           # Docker Compose configuration
├── .env.example                 # Environment template
└── README.md                    # This file
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

- `POST /api/ask` - Ask a question (returns AI-generated answer)
- `POST /api/train` - Submit admin feedback on responses
- `GET /api/embedding-inspector/{session_id}` - Inspect retrieved embeddings
- `GET /api/admin/sessions` - List training sessions
- `GET /api/admin/accuracy-report` - View performance metrics

## Development

### Managing Docker Services

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# Restart a service
docker compose restart backend

# Rebuild after code changes
docker compose up -d --build backend

# View resource usage
docker compose stats

# Clean up (removes volumes too)
docker compose down -v
```

### Database Management

```bash
# Access PostgreSQL shell
docker compose exec postgres psql -U chatbot_user -d cloudvelous_chatbot

# Run migrations
docker compose exec backend alembic upgrade head

# Create new migration
docker compose exec backend alembic revision --autogenerate -m "description"

# Rollback migration
docker compose exec backend alembic downgrade -1
```

### Testing

```bash
# Run all tests
docker compose exec backend pytest

# Run with coverage
docker compose exec backend pytest --cov=app --cov-report=html

# Run specific test file
docker compose exec backend pytest tests/unit/test_embedder.py
```

### Code Quality

```bash
# Format code
docker compose exec backend black app/

# Lint code
docker compose exec backend flake8 app/

# Type checking
docker compose exec backend mypy app/
```

## Configuration

All configuration is managed through environment variables. See `.env.example` for available options.

### Key Configuration Options

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider to use | `openai` |
| `EMBED_MODEL` | Sentence transformer model | `all-MiniLM-L6-v2` |
| `TOP_K_RETRIEVAL` | Number of chunks to retrieve | `5` |
| `WORKFLOW_EMBEDDING_ENABLED` | Enable workflow learning | `true` |
| `FEEDBACK_THRESHOLD_FOR_RETRAIN` | Feedback count to trigger retraining | `50` |

## Monitoring & Logs

```bash
# Follow all logs
docker compose logs -f

# Follow specific service
docker compose logs -f backend

# View last 100 lines
docker compose logs --tail=100 backend

# Export logs to file
docker compose logs > logs.txt
```

## Troubleshooting

### Database Connection Issues

```bash
# Check if PostgreSQL is running
docker compose ps postgres

# Check PostgreSQL logs
docker compose logs postgres

# Restart PostgreSQL
docker compose restart postgres
```

### Backend Won't Start

```bash
# Check backend logs
docker compose logs backend

# Rebuild backend image
docker compose build backend
docker compose up -d backend

# Check if migrations ran
docker compose exec backend alembic current
```

### Port Conflicts

If ports 5432 or 8000 are already in use, edit `docker compose.yml`:

```yaml
ports:
  - "5433:5432"  # Use different host port
```

## Contributing

1. Create a feature branch
2. Make your changes
3. Write/update tests
4. Run tests and linting
5. Submit a pull request

## License

MIT

## Support

For issues and questions, please open an issue on GitHub.
