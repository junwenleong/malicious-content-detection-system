# Development Workflow

## Check Execution Strategy

This document clarifies when to run quality checks and how to avoid duplication.

## Check Types Comparison

### lint.sh (Local Development)
- **Purpose**: Fast local validation before commit
- **Runs**:
  - `ruff check --fix` (linting with auto-fix)
  - `ruff format` (code formatting)
  - `mypy` (type checking)
  - `npm run lint` (ESLint for frontend)

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
- **Purpose**: Automatic validation on every commit
- **Runs**: Same as `lint.sh` but automatically
- **Benefit**: Catches issues before they reach CI/CD

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
./scripts/setup-pre-commit.sh

# Now every git commit automatically runs lint.sh
git commit -m "Your changes"
```

**What happens:**
- Runs `lint.sh` automatically
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
./scripts/setup-pre-commit.sh

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

| Check Type | When | Duration | Auto-Fix | Blocks Commit | Runs Tests |
|------------|------|----------|----------|---------------|------------|
| IDE Linting | On save | <1s | ✓ | ✗ | ✗ |
| Pre-commit Hook | On commit | 5-10s | ✓ | ✓ | ✗ |
| Manual lint.sh | On demand | 5-10s | ✓ | ✗ | ✗ |
| CI/CD Pipeline | On push/PR | 2-5min | ✗ | ✓ | ✓ |

## Troubleshooting

### Pre-commit hook not running
```bash
# Check if hook exists
ls -la .git/hooks/pre-commit

# Reinstall
./scripts/setup-pre-commit.sh
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

## Summary

**Best Practice**: Install pre-commit hook once, then just write code and commit normally. The hook catches issues automatically, and CI/CD provides comprehensive validation.

**Key Principle**: Run checks once per commit (automatically via pre-commit), not manually before every commit.
