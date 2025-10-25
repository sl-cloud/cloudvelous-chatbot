# Cloudvelous Chat Assistant

An intelligent chatbot backend powered by RAG (Retrieval-Augmented Generation) with workflow learning capabilities. Built with FastAPI, PostgreSQL (pgvector), and advanced LLM integration.

## Features

- **RAG Architecture**: Semantic search over documentation using pgvector vector database
- **Multi-LLM Support**: OpenAI GPT-4 and Google Gemini integration with runtime switching
- **Workflow Learning**: Captures and learns from successful reasoning chains to improve future responses
- **Admin Training Interface**: Review sessions, provide feedback, and analyze performance metrics
- **Self-Improving**: Automatically adjusts retrieval accuracy weights based on user feedback
- **Flexible Embedding**: Support for both local (sentence-transformers) and cloud (OpenAI) embeddings
- **GitHub Integration**: Ready for automated repository documentation ingestion

## Architecture

### Tech Stack

- **Backend**: FastAPI (Python 3.11+) with async support
- **Database**: PostgreSQL 16 with pgvector extension for vector similarity search
- **Embeddings**: Sentence Transformers (all-MiniLM-L6-v2, 384-dim) or OpenAI (text-embedding-3-small, 1536-dim)
- **LLM Providers**: OpenAI GPT-4, Google Gemini
- **Deployment**: Docker Compose for local development and production

### Key Components

1. **Embedding Service**: Converts text to vector embeddings for semantic search
2. **Retrieval Service**: Finds relevant knowledge chunks using vector similarity
3. **Generator Service**: Generates responses using retrieved context and LLM
4. **Workflow Learner**: Learns from successful query patterns to boost future retrievals
5. **Training System**: Collects feedback and adjusts accuracy weights

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Git
- At least 4GB RAM available for Docker
- API keys for OpenAI and/or Google Gemini

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd cloudvelous-chatbot
   ```

2. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set required values:
   ```bash
   # Database
   POSTGRES_PASSWORD=your_secure_password

   # LLM Provider (choose one or both)
   OPENAI_API_KEY=sk-your-openai-key
   GEMINI_API_KEY=your-gemini-key
   LLM_PROVIDER=openai  # or gemini

   # GitHub Integration
   GITHUB_TOKEN=ghp_your-github-token

   # Security (generate with: openssl rand -hex 32)
   ADMIN_JWT_SECRET=your-jwt-secret-min-32-chars
   ADMIN_API_KEY=your-api-key
   ```

3. **Start all services**
   ```bash
   docker compose up -d
   ```

4. **Verify services are running**
   ```bash
   docker compose ps
   ```

   Expected output:
   ```
   NAME                          STATUS          PORTS
   cloudvelous-chatbot-backend   Up              0.0.0.0:8000->8000/tcp
   cloudvelous-chatbot-db        Up (healthy)    0.0.0.0:5432->5432/tcp
   cloudvelous-chatbot-postadmin Up              0.0.0.0:5050->80/tcp
   ```

5. **Check API health**
   ```bash
   curl http://localhost:8000/health
   ```

   Expected response:
   ```json
   {"status":"healthy","version":"0.3.0","phase":"3"}
   ```

6. **Access the API documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
   - pgAdmin: http://localhost:5050 (optional)

## Usage

### API Endpoints

#### Ask a Question
```bash
curl -X POST http://localhost:8000/api/ask \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I implement authentication?",
    "llm_provider": "openai",
    "llm_model": "gpt-4"
  }'
```

#### Submit Feedback
```bash
curl -X POST http://localhost:8000/api/train \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": 123,
    "is_correct": true,
    "chunk_feedback": [
      {"chunk_id": 1, "was_useful": true}
    ]
  }'
```

#### View Admin Sessions
```bash
curl -X POST http://localhost:8000/api/admin/sessions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-admin-api-key" \
  -d '{
    "skip": 0,
    "limit": 10,
    "feedback_status": "pending"
  }'
```

#### Get Performance Metrics
```bash
curl -X GET http://localhost:8000/api/admin/stats \
  -H "X-API-Key: your-admin-api-key"
```

### Complete API Documentation

Visit http://localhost:8000/docs for interactive API documentation with:
- All available endpoints
- Request/response schemas
- Try-it-out functionality
- Authentication requirements

## Project Structure

```
cloudvelous-chatbot/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application entry point
│   │   ├── config.py            # Configuration management (env vars)
│   │   ├── database.py          # Database connection & session
│   │   ├── routers/             # API route handlers
│   │   │   ├── chat.py          # /api/ask endpoint
│   │   │   ├── training.py      # /api/train endpoint
│   │   │   ├── admin.py         # /api/admin/* endpoints
│   │   │   └── github.py        # GitHub API client (planned)
│   │   ├── services/            # Business logic layer
│   │   │   ├── embedder.py      # Text embedding generation
│   │   │   ├── retriever.py     # Semantic search & ranking
│   │   │   ├── generator.py     # LLM response generation
│   │   │   ├── workflow_learner.py  # Pattern learning
│   │   │   └── admin_service.py # Admin operations
│   │   ├── models/              # SQLAlchemy ORM models
│   │   │   ├── embeddings.py    # KnowledgeChunk model
│   │   │   ├── training_sessions.py  # TrainingSession model
│   │   │   ├── embedding_links.py    # Chunk-session links
│   │   │   └── workflow_vectors.py   # Workflow embeddings
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── llm/                 # LLM provider implementations
│   │   │   ├── factory.py       # Provider factory pattern
│   │   │   ├── openai_provider.py   # OpenAI integration
│   │   │   └── gemini_provider.py   # Google Gemini integration
│   │   ├── training/            # Training & optimization
│   │   │   └── optimizer.py     # Accuracy weight optimizer
│   │   └── middleware/          # Authentication & middleware
│   │       ├── auth.py          # JWT authentication
│   │       └── rate_limit.py    # Rate limiting
│   ├── tests/                   # Unit and integration tests
│   │   ├── unit/                # Unit tests
│   │   └── integration/         # Integration tests
│   ├── alembic/                 # Database migrations
│   │   └── versions/            # Migration scripts
│   ├── requirements.txt         # Python dependencies
│   ├── Dockerfile               # Backend container image
│   └── setup.sh                 # Local development setup
├── scripts/
│   ├── init-db.sql              # Database initialization SQL
│   ├── initial_ingestion.py     # Data ingestion script (planned)
│   └── manual_retrain.py        # Manual retraining trigger
├── docs/
│   ├── DEBUGGING.md             # Troubleshooting guide
│   ├── implementation-plans/    # GitHub ingestion implementation
│   │   ├── README.md            # Implementation overview
│   │   ├── 01-github-client.md  # GitHub API client
│   │   ├── 02-fetch-files.md    # File fetching
│   │   ├── 03-text-chunking.md  # Text chunking
│   │   ├── 04-embeddings.md     # Embedding generation
│   │   ├── 05-database-storage.md  # Database storage
│   │   ├── 06-orchestration.md  # Pipeline orchestration
│   │   ├── 07-testing.md        # Comprehensive testing
│   │   ├── 08-incremental-updates.md  # SHA-based updates
│   │   └── 09-openai-embeddings.md   # OpenAI integration
│   └── USER_MANUAL.md           # End-user documentation
├── docker-compose.yml           # Docker Compose configuration
├── .env.example                 # Environment variable template
└── README.md                    # This file
```

## Development

### Local Development Setup

```bash
# Install backend dependencies locally (optional)
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run locally without Docker
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Managing Services

```bash
# Start all services
docker compose up -d

# Start specific service
docker compose up -d backend

# Stop all services
docker compose down

# Stop without removing volumes
docker compose stop

# Restart service
docker compose restart backend

# Rebuild after code changes
docker compose up -d --build backend

# View logs
docker compose logs -f backend

# View resource usage
docker compose stats

# Clean up everything (including volumes)
docker compose down -v
```

### Database Operations

```bash
# Access PostgreSQL shell
docker compose exec postgres psql -U chatbot_user -d cloudvelous_chatbot

# Common SQL commands
\dt          # List tables
\d tablename # Describe table
SELECT COUNT(*) FROM knowledge_chunks;  # Count chunks

# Run migrations
docker compose exec backend alembic upgrade head

# Create new migration
docker compose exec backend alembic revision --autogenerate -m "Add new column"

# Rollback last migration
docker compose exec backend alembic downgrade -1

# View migration history
docker compose exec backend alembic history
```

### Testing

```bash
# Run all tests
docker compose exec backend pytest

# Run with coverage report
docker compose exec backend pytest --cov=app --cov-report=html
open htmlcov/index.html  # View coverage report

# Run specific test file
docker compose exec backend pytest tests/unit/test_embedder.py

# Run tests matching pattern
docker compose exec backend pytest -k "test_retrieval"

# Run with verbose output
docker compose exec backend pytest -v
```

### Code Quality

```bash
# Format code with Black
docker compose exec backend black app/

# Lint with Flake8
docker compose exec backend flake8 app/

# Type checking with MyPy
docker compose exec backend mypy app/

# Run all quality checks
docker compose exec backend sh -c "black app/ && flake8 app/ && mypy app/"
```

## Configuration

All configuration is managed through environment variables defined in `.env`.

### Core Settings

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `POSTGRES_PASSWORD` | PostgreSQL password | - | Yes |
| `DATABASE_URL` | Full database connection string | Auto-generated | No |
| `OPENAI_API_KEY` | OpenAI API key | - | If using OpenAI |
| `GEMINI_API_KEY` | Google Gemini API key | - | If using Gemini |
| `LLM_PROVIDER` | Default LLM provider | `openai` | No |
| `LLM_MODEL` | Default LLM model | `gpt-4` | No |

### Retrieval Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `EMBED_MODEL` | Sentence transformer model | `all-MiniLM-L6-v2` |
| `TOP_K_RETRIEVAL` | Number of chunks to retrieve | `5` |
| `WORKFLOW_BOOST_FACTOR` | Boost for workflow matches | `1.2` |
| `CHUNK_WEIGHT_ADJUSTMENT_RATE` | Learning rate for weights | `0.1` |
| `MIN_CHUNK_WEIGHT` | Minimum accuracy weight | `0.5` |
| `MAX_CHUNK_WEIGHT` | Maximum accuracy weight | `2.0` |

### Workflow Learning

| Variable | Description | Default |
|----------|-------------|---------|
| `WORKFLOW_EMBEDDING_ENABLED` | Enable workflow learning | `true` |
| `WORKFLOW_SIMILARITY_WEIGHT` | Weight for workflow similarity | `0.3` |
| `FEEDBACK_THRESHOLD_FOR_RETRAIN` | Feedback count trigger | `50` |

### Security Settings

| Variable | Description | Required |
|----------|-------------|----------|
| `ADMIN_JWT_SECRET` | JWT signing secret (min 32 chars) | Yes |
| `ADMIN_API_KEY` | Admin API authentication key | Yes |
| `JWT_ALGORITHM` | JWT signing algorithm | No (RS256) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry time | No (30) |

## Monitoring & Debugging

### Viewing Logs

```bash
# Follow all logs
docker compose logs -f

# Follow specific service
docker compose logs -f backend

# Last 100 lines
docker compose logs --tail=100 backend

# Export logs to file
docker compose logs > logs.txt

# Search logs for errors
docker compose logs backend | grep -i error
```

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Database connection
docker compose exec backend python -c "
from app.database import SessionLocal
db = SessionLocal()
print('Connected:', db.execute('SELECT 1').scalar())
db.close()
"

# Check embedder
docker compose exec backend python -c "
from app.services.embedder import EmbeddingService
embedder = EmbeddingService()
print('Model loaded:', embedder.model)
"
```

### Performance Monitoring

```bash
# Container resource usage
docker compose stats

# Database stats
docker compose exec postgres psql -U chatbot_user -d cloudvelous_chatbot -c "
SELECT
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"

# API endpoint stats (requires admin API key)
curl -H "X-API-Key: your-admin-api-key" \
  http://localhost:8000/api/admin/stats
```

## Troubleshooting

### Common Issues

**Backend won't start - "ModuleNotFoundError"**
```bash
# Rebuild container
docker compose up -d --build backend
```

**Database connection refused**
```bash
# Check PostgreSQL is running
docker compose ps postgres

# Restart PostgreSQL
docker compose restart postgres

# Wait a few seconds and restart backend
sleep 5
docker compose restart backend
```

**Port already in use**
```bash
# Find what's using the port
lsof -i :8000

# Kill the process or change port in docker-compose.yml
```

**Slow query responses**
```bash
# Check database indices
docker compose exec postgres psql -U chatbot_user -d cloudvelous_chatbot -c "\di"

# Check embedding count
docker compose exec postgres psql -U chatbot_user -d cloudvelous_chatbot -c \
  "SELECT COUNT(*) FROM knowledge_chunks;"
```

For more detailed troubleshooting, see [docs/DEBUGGING.md](docs/DEBUGGING.md).

## GitHub Integration

The system is designed to ingest documentation from GitHub repositories. Implementation plans are available in `docs/implementation-plans/`.

### Planned Features
- Automated repository documentation ingestion
- Incremental updates (SHA-based change detection)
- Support for Markdown, code files, and documentation
- Configurable file filters and chunking strategies

### Implementation
See [docs/implementation-plans/README.md](docs/implementation-plans/README.md) for step-by-step implementation guides.

## Contributing

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes
4. Write/update tests
5. Run tests and linting: `docker compose exec backend pytest && black app/`
6. Commit: `git commit -m "Add your feature"`
7. Push: `git push origin feature/your-feature`
8. Create a Pull Request

### Code Style

- Follow PEP 8 guidelines
- Use type hints for all function parameters
- Write docstrings for public functions
- Keep functions focused and single-purpose
- Add tests for new features

## License

MIT License - See LICENSE file for details

## Support

- **Documentation**: See `docs/` directory
- **User Manual**: [USER_MANUAL.md](USER_MANUAL.md)
- **Debugging Guide**: [docs/DEBUGGING.md](docs/DEBUGGING.md)
- **Issues**: Open an issue on GitHub
- **Questions**: Use GitHub Discussions

## Acknowledgments

- FastAPI for the excellent web framework
- PostgreSQL pgvector for vector similarity search
- Sentence Transformers for embeddings
- OpenAI and Google for LLM APIs
