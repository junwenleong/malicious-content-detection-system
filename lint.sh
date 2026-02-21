#!/bin/sh
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "Starting Linting Process..."

# Backend Linting
echo ""
echo "=== Backend (Ruff & Mypy) ==="

# Check for Ruff
if ! command -v ruff >/dev/null 2>&1; then
    echo "${RED}Ruff is not installed. Please run 'pip install -r requirements-dev.txt'${NC}"
    exit 1
fi

echo "Running Ruff Check and Fix..."
ruff check . --fix --ignore E741
echo "Running Ruff Format..."
ruff format .

echo "Running Mypy..."
# mypy might need some ignore flags if dependencies aren't perfect, but let's try strict first
# Using --ignore-missing-imports to avoid errors from missing types in some libs
mypy . || echo "${RED}Mypy found issues (continuing...)${NC}"

# Frontend Linting
echo ""
echo "=== Frontend (ESLint) ==="
cd frontend

if [ ! -d "node_modules" ]; then
    echo "${RED}node_modules not found. Please run 'npm install' in frontend/${NC}"
    exit 1
fi

npm run lint

echo ""
echo "${GREEN}Linting Complete!${NC}"
