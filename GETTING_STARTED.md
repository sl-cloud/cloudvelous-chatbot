# Getting Started with Cloudvelous Chat Assistant

Welcome! This guide will get you up and running in minutes.

## What You Have Now

Phase 0 (Environment & Infrastructure Setup) is **complete**! You now have:

✅ Docker Compose configuration with PostgreSQL + pgvector  
✅ Backend Dockerfile with Python 3.11 + virtual environment  
✅ Complete project structure with all directories  
✅ Dependencies defined in requirements.txt  
✅ Database initialization scripts  
✅ Environment configuration template  
✅ Local development setup script  
✅ Comprehensive documentation  

## Quick Start (3 Steps)

### 1. Configure Environment

```bash
# Copy the environment template
cp env.example .env

# Generate secure secrets
openssl rand -hex 32  # Copy this for ADMIN_JWT_SECRET
openssl rand -hex 16  # Copy this for ADMIN_API_KEY

# Edit .env and add your API keys
nano .env  # or your preferred editor
```

**Required settings in .env:**
- `POSTGRES_PASSWORD` - Any secure password
- `OPENAI_API_KEY` - Your OpenAI API key
- `GITHUB_TOKEN` - GitHub personal access token
- `ADMIN_JWT_SECRET` - Use generated value above
- `ADMIN_API_KEY` - Use generated value above

### 2. Start Services

```bash
# Start everything
docker compose up -d

# Check status
docker compose ps

# View logs (optional)
docker compose logs -f backend
```

### 3. Verify It's Running

```bash
# Test the health endpoint
curl http://localhost:8000/health

# Open API documentation in browser
# http://localhost:8000/docs
```

That's it! You're running! 🚀

## What Works Right Now

- ✅ FastAPI backend server running on port 8000
- ✅ PostgreSQL database with pgvector extension
- ✅ API documentation at `/docs`
- ✅ Health check endpoint at `/health`
- ✅ Complete infrastructure ready for Phase 1

## What's Next (Phase 1)

The backend is running but has minimal functionality. Phase 1 will add:

1. **Database Models** - Tables for knowledge chunks, questions, feedback
2. **Configuration** - Complete settings management
3. **Authentication** - JWT and API key middleware

Then subsequent phases will add:
- RAG pipeline (retrieval, generation)
- Admin training interface
- Workflow learning
- Background optimization

## Project Structure Overview

```
cloudvelous-chatbot/
├── backend/              # FastAPI application
│   ├── app/             # Application code
│   │   ├── main.py      # Entry point (minimal for now)
│   │   ├── config.py    # Configuration (basic placeholder)
│   │   ├── routers/     # API endpoints (Phase 1+)
│   │   ├── services/    # Business logic (Phase 1+)
│   │   ├── models/      # Database models (Phase 1)
│   │   └── ...
│   ├── tests/           # Unit and integration tests
│   └── alembic/         # Database migrations (Phase 1)
├── scripts/             # Utility scripts
├── docker compose.yml   # Service orchestration
└── .env                 # Your configuration (create this!)
```

## Key Commands

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# View logs
docker compose logs -f

# Access database
docker compose exec postgres psql -U chatbot_user -d cloudvelous_chatbot

# Access backend shell
docker compose exec backend bash

# Restart a service
docker compose restart backend

# Rebuild after changes
docker compose up -d --build backend
```

## Documentation

- **QUICKSTART.md** - Fast 5-minute setup guide
- **README.md** - Complete documentation

## Getting Help

**Services not starting?**
1. Check logs: `docker compose logs -f`
2. Verify .env file exists and has all required values
3. Check that all required environment variables are set in .env

**Port conflicts?**
Edit `docker compose.yml` and change the host ports:
```yaml
ports:
  - "5433:5432"  # PostgreSQL (changed from 5432)
  - "8001:8000"  # Backend (changed from 8000)
```

**Want to develop locally without Docker?**
```bash
cd backend
bash setup.sh
source venv/bin/activate
# Follow README.md for local PostgreSQL setup
```

## Current Status

**Phase 0**: ✅ Complete - Infrastructure ready  
**Phase 1**: ⏳ Pending - Database models and config  
**Phase 2**: ⏳ Pending - Workflow reasoning capture  
**Phase 3**: ⏳ Pending - Admin training interface  
**Phase 4**: ⏳ Pending - Retrieval enhancement  
**Phase 5**: ⏳ Pending - Background optimization  
**Phase 6**: ⏳ Pending - Admin frontend hooks  
**Phase 7**: ⏳ Pending - Testing  

## Next Implementation Steps

When you're ready to continue building:

1. Implement database models in `backend/app/models/`
2. Create Alembic migrations for schema
3. Complete authentication middleware
4. Build RAG pipeline services
5. Create API endpoints

The foundation is solid and ready for development! 🎉

---

Need more details? Check out:
- **README.md** for comprehensive documentation
- **QUICKSTART.md** for minimal setup steps

