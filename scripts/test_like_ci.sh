#!/bin/bash
#
# Test script that mimics GitHub Actions workflow
# Use this to verify tests pass before pushing to GitHub
#

set -e

echo "=========================================="
echo "Testing like GitHub Actions CI"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Backend app tests
echo "${YELLOW}Step 1: Running backend app tests...${NC}"
echo ""

docker compose exec -T backend pytest tests/unit \
  -o addopts="-v --strict-markers --tb=short" \
  --cov=app \
  --cov-report=term-missing

if [ $? -eq 0 ]; then
  echo ""
  echo "${GREEN}✅ Backend app tests passed!${NC}"
  echo ""
else
  echo ""
  echo "${RED}❌ Backend app tests failed!${NC}"
  exit 1
fi

# Step 2: Ingestion module tests
echo "${YELLOW}Step 2: Running ingestion module tests...${NC}"
echo ""

docker compose exec -T backend pytest tests/ingestion \
  -v \
  -m "not integration" \
  -o addopts="" \
  --cov=scripts.ingestion \
  --cov-report=term-missing \
  --cov-fail-under=95 \
  --tb=short

if [ $? -eq 0 ]; then
  echo ""
  echo "${GREEN}✅ Ingestion module tests passed!${NC}"
  echo ""
else
  echo ""
  echo "${RED}❌ Ingestion module tests failed!${NC}"
  exit 1
fi

# Success!
echo "=========================================="
echo "${GREEN}🎉 All tests passed!${NC}"
echo "${GREEN}Your code is ready for GitHub Actions!${NC}"
echo "=========================================="

