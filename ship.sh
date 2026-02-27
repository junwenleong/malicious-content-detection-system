#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🚀 Starting ship process...${NC}"

# Check if commit message provided
if [ -z "$1" ]; then
    echo -e "${RED}❌ Error: Commit message required${NC}"
    echo "Usage: ./ship.sh \"Your commit message\""
    exit 1
fi

COMMIT_MSG="$1"

# Step 1: Run tests
echo -e "${YELLOW}🧪 Running tests...${NC}"
pytest tests/ || {
    echo -e "${RED}❌ Tests failed. Fix issues before shipping.${NC}"
    exit 1
}
echo -e "${GREEN}✓ Tests passed${NC}"

# Step 2: Auto-format frontend with Prettier
echo -e "${YELLOW}✨ Auto-formatting frontend files with Prettier...${NC}"
if [ -d "frontend" ]; then
    cd frontend
    if [ -f "package.json" ]; then
        npm run format 2>/dev/null || npx prettier --write "src/**/*.{ts,tsx,js,jsx,json,css}" 2>/dev/null || {
            echo -e "${YELLOW}⚠️  Prettier not configured, skipping frontend formatting${NC}"
        }
    fi
    cd ..
    echo -e "${GREEN}✓ Frontend formatted${NC}"
else
    echo -e "${YELLOW}⚠️  No frontend directory found, skipping formatting${NC}"
fi

# Step 3: Stage all changes (including formatting fixes)
echo -e "${YELLOW}📦 Staging changes...${NC}"
git add .
echo -e "${GREEN}✓ Changes staged${NC}"

# Step 4: Commit with GPG signature
echo -e "${YELLOW}📝 Committing with message: ${COMMIT_MSG}${NC}"
git commit -S -m "$COMMIT_MSG" || {
    echo -e "${RED}❌ Commit failed. Check pre-commit hooks output above.${NC}"
    exit 1
}
echo -e "${GREEN}✓ Committed${NC}"

# Step 5: Push to remote
echo -e "${YELLOW}🚢 Pushing to remote...${NC}"
git push || {
    echo -e "${RED}❌ Push failed. Check your remote configuration.${NC}"
    exit 1
}
echo -e "${GREEN}✓ Pushed${NC}"

echo -e "${GREEN}🎉 Ship complete!${NC}"
