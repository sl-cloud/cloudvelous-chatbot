-- Initialize database for Cloudvelous Chatbot
-- This script runs automatically when the PostgreSQL container starts for the first time

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extension is installed
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';

-- Log confirmation
DO $$
BEGIN
    RAISE NOTICE 'pgvector extension enabled successfully';
END $$;

