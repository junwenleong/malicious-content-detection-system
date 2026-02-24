#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Pre-commit Hooks Setup ===${NC}"
echo ""

# Check if .git directory exists
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}Warning: .git directory not found. Are you in the project root?${NC}"
    exit 1
fi

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo -e "${YELLOW}pre-commit not found. Installing...${NC}"
    pip install pre-commit>=3.5.0
fi

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

# Install commit-msg hook (optional, for commit message linting)
pre-commit install --hook-type commit-msg

echo ""
echo -e "${GREEN}✓ Pre-commit hooks installed successfully!${NC}"
echo ""
echo "The hooks will now run automatically on every commit."
echo ""
echo -e "${BLUE}Test the hooks with:${NC}"
echo "  pre-commit run --all-files"
echo ""
echo "To bypass hooks in emergencies:"
echo "  git commit --no-verify -m \"Your message\""
echo ""
echo -e "${BLUE}Update hooks to latest versions:${NC}"
echo "  pre-commit autoupdate"
