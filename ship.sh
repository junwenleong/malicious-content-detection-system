#!/bin/bash
# ship.sh - Run tests, format, commit, and push
# Usage: ./ship.sh "Your commit message here" [--fast]
# Options:
#   --fast    Skip slow/integration tests

set -eE
trap 'cleanup_on_error' ERR

# --- Helper functions -------------------------------------------------

die() {
    echo -e "❌ $1" >&2
    exit 1
}

cleanup_on_error() {
    echo "❌ ship.sh failed. See error above." >&2
}

# --- Argument parsing -------------------------------------------------

if [ -z "$1" ]; then
    die "Please provide a commit message.\nUsage: ./ship.sh \"feat: your message\" [--fast]"
fi

COMMIT_MSG="$1"
FAST=false
if [[ "$2" == "--fast" ]]; then
    FAST=true
fi

# --- Python detection -------------------------------------------------

if [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    die "No Python 3 found. Install Python 3.11+ or create a venv."
fi

# --- Warn about untracked files ---------------------------------------

untracked=$(git ls-files --others --exclude-standard)
if [ -n "$untracked" ]; then
    echo "⚠️  You have untracked files:"
    echo "$untracked" | sed 's/^/   /'
    read -p "Continue and include them in the commit? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        die "Aborted by user."
    fi
fi

echo "=========================================="
echo "🚀 Shipping code"
echo "📝 Message: $COMMIT_MSG"
echo "=========================================="

# --- Run tests --------------------------------------------------------

echo "🧪 Running tests..."
if [ "$FAST" = true ]; then
    echo "   (Fast mode: skipping slow and integration tests)"
    $PYTHON_CMD -m pytest -m "not slow and not integration" -q --tb=short || die "Tests failed!"
else
    echo "   (Full test suite)"
    $PYTHON_CMD -m pytest -q --tb=short || die "Tests failed!"
fi
echo "✅ Tests passed!"

# --- Format frontend --------------------------------------------------

echo "🎨 Formatting code with Prettier..."
if command -v npx &> /dev/null && [ -d "frontend" ]; then
    (cd frontend && npx prettier --write "**/*.{js,jsx,ts,tsx,json,css,scss,md,yaml,yml}" --ignore-unknown) 2>/dev/null || true
fi

# --- Stage and commit -------------------------------------------------

echo "➕ Adding files..."
git add .

echo "🔏 Committing with GPG signature..."
commit_failed() {
    # Diagnose the actual reason for failure
    echo "❌ Commit failed. Diagnosing..." >&2

    # Check if pre-commit hook blocked it (exit code 1 with hook output)
    if [ -f ".git/hooks/pre-commit" ]; then
        echo "   ↳ Pre-commit hooks may have blocked the commit. Check output above." >&2
    fi

    # Check GPG key configuration
    local signing_key
    signing_key=$(git config user.signingkey 2>/dev/null || true)
    if [ -z "$signing_key" ]; then
        echo "   ↳ No GPG signing key configured. Run: git config user.signingkey <key-id>" >&2
    else
        # Check if the key is actually available in the keyring
        if ! gpg --list-secret-keys "$signing_key" >/dev/null 2>&1; then
            echo "   ↳ GPG key '$signing_key' not found in keyring. Check: gpg --list-secret-keys" >&2
        fi
    fi

    exit 1
}

if ! git commit -S -m "$COMMIT_MSG"; then
    # Pre-commit hooks may have auto-fixed files (they land as unstaged)
    if ! git diff --quiet; then
        echo "⚠️  Pre-commit hooks auto-fixed some files. Re-staging..."
        git add -u
        # Verify there's actually something staged before retrying
        if git diff --cached --quiet; then
            echo "ℹ️  No changes to commit after re-staging (pre-commit hooks produced identical output)."
        else
            echo "✅ Auto-fixes staged. Committing again..."
            git commit -S -m "$COMMIT_MSG" || commit_failed
        fi
    # Nothing to commit (working tree clean after auto-fixes applied everything)
    elif git diff --cached --quiet; then
        echo "ℹ️  No changes to commit (working tree clean after auto-fixes)."
    else
        commit_failed
    fi
fi

CURRENT_BRANCH=$(git branch --show-current)

# --- Sync with remote -------------------------------------------------

echo "🔄 Checking remote status..."
git fetch origin "$CURRENT_BRANCH" 2>/dev/null || true

if git rev-parse --verify origin/"$CURRENT_BRANCH" >/dev/null 2>&1; then
    BEHIND=$(git rev-list --count HEAD..origin/"$CURRENT_BRANCH" 2>/dev/null || echo 0)
    if [ "$BEHIND" -gt 0 ]; then
        echo "ℹ️  Branch is behind origin/$CURRENT_BRANCH by $BEHIND commit(s)."
        echo "⬇️  Attempting fast-forward pull..."
        if git pull --ff-only origin "$CURRENT_BRANCH"; then
            echo "✅ Pull successful. Re-running tests to verify..."
            if [ "$FAST" = true ]; then
                $PYTHON_CMD -m pytest -m "not slow and not integration" -q --tb=short || die "Tests failed after pull!"
            else
                $PYTHON_CMD -m pytest -q --tb=short || die "Tests failed after pull!"
            fi
            echo "✅ Tests still pass."
        else
            die "Fast-forward pull failed. Please rebase manually:\n   git pull --rebase origin $CURRENT_BRANCH"
        fi
    else
        echo "✅ Branch is up to date."
    fi
else
    echo "🆕 No remote branch yet – will be created on push."
fi

# --- Push -------------------------------------------------------------

echo "⬆️  Pushing to remote (branch: $CURRENT_BRANCH)..."
COMMIT_SHA=$(git rev-parse HEAD)

if ! git push origin "$CURRENT_BRANCH"; then
    echo ""
    echo "⚠️  Push failed (pre-push hooks or remote rejection)."
    read -p "Undo the last commit and keep changes staged? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Only revert if HEAD is still the commit we just made
        if [ "$(git rev-parse HEAD)" = "$COMMIT_SHA" ]; then
            git reset --soft HEAD~1
            echo "✅ Commit undone. Changes are still staged. Fix the errors and run ship.sh again."
        else
            echo "⚠️  HEAD has changed since commit — skipping revert to avoid data loss."
            echo "   Manually run: git reset --soft $COMMIT_SHA~1"
        fi
    else
        echo "ℹ️  Commit remains. You can amend it later with 'git commit --amend'."
    fi
    exit 1
fi

echo "✅ Done! GitHub Actions will run the full CI pipeline."
echo "=========================================="
