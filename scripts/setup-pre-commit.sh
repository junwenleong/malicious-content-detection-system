#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Pre-commit Hook Setup ===${NC}"
echo ""

# Check if .git directory exists
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}Warning: .git directory not found. Are you in the project root?${NC}"
    exit 1
fi

# Ensure lint.sh is executable
if [ -f "lint.sh" ]; then
    chmod +x lint.sh
    echo "✓ Made lint.sh executable"
else
    echo -e "${YELLOW}Warning: lint.sh not found${NC}"
fi

# Create hooks directory if it doesn't exist
mkdir -p .git/hooks

# Create pre-commit hook
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Running pre-commit checks...${NC}"
echo ""

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Check if ruff is available
if ! command -v ruff >/dev/null 2>&1; then
    echo -e "${RED}Error: Ruff is not installed.${NC}"
    echo "Please run: pip install -r requirements-dev.txt"
    echo ""
    echo "To bypass this check (emergency only), use:"
    echo "  git commit --no-verify -m \"Your message\""
    exit 1
fi

# Run lint.sh
if [ -f "./lint.sh" ]; then
    ./lint.sh
else
    echo -e "${RED}Error: lint.sh not found${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}✓ Pre-commit checks passed!${NC}"
echo ""
EOF

# Make the hook executable
chmod +x .git/hooks/pre-commit

echo -e "${GREEN}✓ Pre-commit hook installed successfully!${NC}"
echo ""
echo "The hook will now run automatically on every commit."
echo ""
echo "To bypass the hook in emergencies, use:"
echo "  git commit --no-verify -m \"Your message\""
echo ""
echo -e "${BLUE}Test the hook with:${NC}"
echo "  git commit --allow-empty -m \"Test pre-commit hook\""
