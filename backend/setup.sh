#!/bin/bash
# Setup script for local development outside Docker

set -e

echo "🚀 Setting up Cloudvelous Chatbot Backend - Local Development Environment"
echo "========================================================================="

# Check if Python 3.11+ is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed. Please install Python 3.11 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "✓ Found Python $PYTHON_VERSION"

# Create virtual environment
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Removing old one..."
    rm -rf venv
fi

echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📚 Installing dependencies from requirements.txt..."
pip install -r requirements.txt

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Activate the virtual environment:"
echo "      source venv/bin/activate"
echo ""
echo "   2. Copy and configure environment variables:"
echo "      cp ../.env.example ../.env"
echo "      # Edit .env with your actual credentials"
echo ""
echo "   3. Ensure PostgreSQL with pgvector is running:"
echo "      # Option A: Use Docker Compose from project root:"
echo "      cd .. && docker compose up -d postgres"
echo ""
echo "      # Option B: Install locally (Ubuntu/Debian):"
echo "      sudo apt-get install postgresql-16 postgresql-16-pgvector"
echo ""
echo "   4. Run database migrations:"
echo "      alembic upgrade head"
echo ""
echo "   5. Start the development server:"
echo "      uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "🎉 Happy coding!"

