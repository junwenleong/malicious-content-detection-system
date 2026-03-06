# Development Workflow

## Check Execution Strategy

This document clarifies when to run quality checks and how to avoid duplication.

**Philosophy**: Pre-commit hooks are a "fast filter" (< 5 seconds) that catch 90% of mistakes in 10% of the time. Heavy checks run in CI/CD or ship.sh.

## Check Types Comparison

### lint.sh (Local Development)

- **Purpose**: Fast local validation before commit (if not using pre-commit hook)
- **Runs**:
  - `ruff check --fix` (linting with auto-fix)
  - `ruff format` (code formatting - replaces black)
  - `mypy` (type checking)
  - `npm run lint` (ESLint for frontend)
- **Note**: Redundant if pre-commit hook is installed

### CI/CD Pipeline (.github/workflows/ci.yml)

- **Purpose**: Comprehensive validation on push/PR
- **Runs**:
  - `ruff check` (linting, no auto-fix)
  - `black --check` (formatting verification)
  - `mypy` (type checking)
  - `pytest` (full test suite with coverage)
  - `npm run lint` (ESLint)
  - `npx tsc --noEmit` (TypeScript type checking)
  - `npm run build` (frontend build)
  - Docker image builds
  - Security scanning (Trivy)

### Pre-commit Hook (Recommended)

- **Purpose**: Automatic validation on every commit (< 5 seconds)
- **Framework**: Industry-standard `pre-commit` framework
- **Runs**: Fast checks only (changed files where possible)
- **Benefit**: Catches issues before they reach CI/CD

**What it checks:**

- Trailing whitespace, end-of-file fixes
- YAML/JSON syntax validation
- Large file detection (>1MB)
- Merge conflict detection
- Secret detection (TruffleHog - replaces detect-private-key)
- Python: ruff (lint check + format check), mypy (changed files only)
- Frontend: Prettier (format check), ESLint (lint), TypeScript (changed files only)
- Fast unit tests only (< 2 seconds, marked with `@pytest.mark.unit` or no marker)

## When to Run What

### 1. Real-Time (During Development)

**IDE/Editor Integration** (Recommended)

- Configure your editor to run linters on save
- VS Code: Install Python, Ruff, ESLint extensions
- PyCharm: Enable Ruff and Mypy inspections
- **Benefit**: Immediate feedback, no manual commands

### 2. Pre-Commit (Automatic)

**Pre-commit Hook** (Recommended Setup)

```bash
# One-time setup
pip install -r requirements-dev.txt
./scripts/setup-hooks.sh

# Now every git commit automatically runs checks
git commit -m "Your changes"
```

**What happens:**

- Runs all quality checks automatically
- Auto-fixes formatting issues
- Blocks commit if critical issues found
- **Benefit**: Never commit broken code

### 3. Manual (When Needed)

**Run lint.sh manually** only in these cases:

- You bypassed pre-commit with `git commit --no-verify`
- You want to check before creating a PR
- You're debugging linting issues
- Pre-commit hook isn't installed yet

```bash
# Run all checks
./lint.sh

# Or run specific checks
ruff check src/
mypy src/
cd frontend && npm run lint
```

### 4. CI/CD (Automatic)

**GitHub Actions** runs on:

- Every push to `main` or `develop`
- Every pull request
- **Benefit**: Comprehensive validation including tests, builds, security scans

## Recommended Workflow

### Initial Setup (One-Time)

```bash
# 1. Install dependencies
pip install -r requirements-dev.txt
cd frontend && npm install && cd ..

# 2. Setup pre-commit hook
./scripts/setup-hooks.sh

# 3. Configure your IDE (optional but recommended)
# - Install linter extensions
# - Enable format-on-save
```

### Daily Development

```bash
# 1. Write code
# 2. Save file (IDE auto-formats if configured)
# 3. Commit
git add .
git commit -m "Add feature X"
# Pre-commit hook runs automatically ✓

# 4. Push
git push
# CI/CD runs automatically ✓
```

### When Pre-Commit Fails

```bash
# Pre-commit found issues and auto-fixed them
git add .  # Stage the auto-fixes
git commit -m "Add feature X"  # Try again

# OR if you need to investigate
./lint.sh  # Run manually to see details
# Fix issues manually
git add .
git commit -m "Add feature X"
```

### When to Skip Pre-Commit

```bash
# Only use --no-verify in emergencies
git commit --no-verify -m "Hotfix: critical bug"

# Then fix linting issues in next commit
./lint.sh  # Run manually
git add .
git commit -m "Fix linting issues"
```

## Anti-Patterns (Don't Do This)

❌ **Running lint.sh before every commit when hook is installed**

```bash
./lint.sh  # Unnecessary
git commit -m "Changes"  # Hook runs lint.sh again (duplicate!)
```

✅ **Just commit - hook handles it**

```bash
git commit -m "Changes"  # Hook runs lint.sh automatically
```

❌ **Bypassing pre-commit regularly**

```bash
git commit --no-verify -m "WIP"  # Bad habit
```

✅ **Let pre-commit catch issues early**

```bash
git commit -m "WIP"  # Hook catches issues before they reach CI/CD
```

❌ **Waiting for CI/CD to find linting issues**

```bash
git push  # CI/CD fails 5 minutes later
```

✅ **Catch issues locally**

```bash
git commit  # Pre-commit catches issues in 5 seconds
```

## Check Execution Matrix

| Check Type      | When       | Duration | Auto-Fix | Blocks Commit | Runs Tests      |
| --------------- | ---------- | -------- | -------- | ------------- | --------------- |
| IDE Linting     | On save    | <1s      | ✓        | ✗             | ✗               |
| Pre-commit Hook | On commit  | <5s      | ✗        | ✓             | Fast only       |
| ship.sh         | Manual     | ~10s     | ✓        | ✓             | Full suite      |
| Manual lint.sh  | On demand  | 5-10s    | ✓        | ✗             | ✗               |
| CI/CD Pipeline  | On push/PR | 2-5min   | ✗        | ✓             | Full + coverage |

**Key Changes:**

- Pre-commit now runs fast unit tests only (< 2s)
- ship.sh runs full test suite before commit
- Only changed files checked where possible (Mypy, TypeScript)

## Troubleshooting

### Pre-commit hook not running

```bash
# Check if hook exists
ls -la .git/hooks/pre-commit

# Reinstall
./scripts/setup-hooks.sh
```

### Linting fails in CI but passes locally

```bash
# Ensure you have latest dependencies
pip install -r requirements-dev.txt
cd frontend && npm install

# Run same checks as CI
ruff check src/ api/ tests/
black --check src/ api/ tests/
mypy src/ api/
pytest tests/
```

### Want to commit despite linting issues (emergency only)

```bash
git commit --no-verify -m "Emergency hotfix"
# Then fix in next commit!
```

## ship.sh Workflow

The `ship.sh` script provides a complete validation and deployment workflow:

```bash
./ship.sh "Your commit message"
```

**What it does:**

1. Runs **full test suite** (pytest tests/)
2. Auto-formats frontend with Prettier
3. Stages all changes (git add .)
4. Commits with GPG signature (git commit -S)
   - Pre-commit hook runs here (fast checks only)
5. Pushes to remote (git push)

**Key insight**: ship.sh runs full tests BEFORE committing, so pre-commit hook only needs fast checks.

## Test Markers

Control when tests run using pytest markers:

```python
import pytest

# Fast unit test - runs in pre-commit
def test_basic():
    assert True

# Slow test - skipped in pre-commit, runs in ship.sh and CI/CD
@pytest.mark.slow
def test_integration():
    time.sleep(2)
    assert True

# Integration test - skipped in pre-commit
@pytest.mark.integration
def test_api():
    response = client.get("/v1/predict")
    assert response.status_code == 200
```

**Run fast tests only** (what pre-commit does):

```bash
pytest -m "not slow and not integration"
```

**Run all tests** (what ship.sh and CI/CD do):

```bash
pytest tests/
```

## TruffleHog Secret Detection

Replaced `detect-private-key` and `detect-secrets` with TruffleHog:

**Installation:**

```bash
brew install trufflesecurity/trufflehog/trufflehog
```

**Benefits:**

- Faster (scans only staged changes)
- More accurate (700+ credential types)
- No infinite loops (no baseline file needed)
- Fewer false positives (--only-verified flag)

**Handling false positives:**

```bash
# Add to ignore file
echo "path/to/file:line_number" >> .trufflehogignore
```

## Summary

**Best Practice**: Install pre-commit hook once, then just write code and commit normally. The hook catches issues automatically, and CI/CD provides comprehensive validation.

**Key Principles:**

1. Pre-commit: Fast filter (< 5s) catches 90% of mistakes
2. ship.sh: Full validation before push
3. CI/CD: Comprehensive validation with coverage and security scans
4. Only check changed files where possible (Mypy, TypeScript)
5. Mark slow tests so they don't block commits
