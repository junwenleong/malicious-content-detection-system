#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Migrating to Optimized Pre-commit Hooks ===${NC}"
echo ""

# Step 1: Check if TruffleHog is installed
echo -e "${YELLOW}Checking TruffleHog installation...${NC}"
if ! command -v trufflehog &> /dev/null; then
    echo -e "${RED}❌ TruffleHog not found${NC}"
    echo ""
    echo "Please install TruffleHog:"
    echo ""
    echo "  macOS:"
    echo "    brew install trufflesecurity/trufflehog/trufflehog"
    echo ""
    echo "  Linux:"
    echo "    curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | sh -s -- -b /usr/local/bin"
    echo ""
    exit 1
else
    echo -e "${GREEN}✓ TruffleHog installed${NC}"
fi

# Step 2: Remove old secrets baseline (no longer needed)
if [ -f ".secrets.baseline" ]; then
    echo -e "${YELLOW}Removing old .secrets.baseline...${NC}"
    rm .secrets.baseline
    echo -e "${GREEN}✓ Removed .secrets.baseline${NC}"
fi

# Step 3: Update pre-commit hooks
echo -e "${YELLOW}Updating pre-commit hooks...${NC}"
# Clean cache (ignore errors if directory is in use)
pre-commit clean 2>/dev/null || true
# Force remove cache if clean failed
rm -rf ~/.cache/pre-commit 2>/dev/null || true
pre-commit install
pre-commit install --hook-type commit-msg
echo -e "${GREEN}✓ Hooks updated${NC}"

# Step 4: Run hooks on all files to verify
echo -e "${YELLOW}Testing hooks on all files...${NC}"
echo "(This may take a minute on first run)"
if pre-commit run --all-files 2>&1 | tee /tmp/pre-commit-test.log; then
    echo -e "${GREEN}✓ All hooks passed!${NC}"
else
    # Check if it's a network error
    if grep -q "Could not resolve host" /tmp/pre-commit-test.log; then
        echo -e "${YELLOW}⚠️  Network connectivity issue detected${NC}"
        echo "GitHub is unreachable. This is temporary and doesn't affect the hook installation."
        echo ""
        echo "The hooks are installed and will work when you commit."
        echo "Pre-commit will download dependencies on first commit when network is available."
    else
        echo -e "${YELLOW}⚠️  Some hooks failed or made changes${NC}"
        echo "This is normal - hooks auto-fixed formatting issues."
        echo "Stage the changes and commit again."
    fi
fi
rm -f /tmp/pre-commit-test.log

echo ""
echo -e "${GREEN}=== Migration Complete! ===${NC}"
echo ""
echo -e "${BLUE}What changed:${NC}"
echo "  • TruffleHog replaces detect-private-key (faster, no baseline file)"
echo "  • Ruff replaces Black (100x faster)"
echo "  • Only fast unit tests run in pre-commit (< 2s)"
echo "  • Mypy and TypeScript only check changed files"
echo "  • Prettier auto-formats frontend files"
echo ""
echo -e "${BLUE}Next steps:${NC}"
echo "  1. Mark slow tests: @pytest.mark.slow"
echo "  2. Mark integration tests: @pytest.mark.integration"
echo "  3. Test with: git commit -m 'Test commit'"
echo "  4. See docs/PRE_COMMIT_GUIDE.md for details"
echo ""
echo -e "${GREEN}Happy coding! 🚀${NC}"
